# Backrest — Backup Management UI

Web interface for managing Restic backups. Configure backup targets, schedule backups, monitor health, and browse/restore snapshots.

## Quick Reference

| Item | Value |
|------|-------|
| Image | `ghcr.io/garethgeorge/backrest:v1.11.2` |
| Container | `backrest` |
| Internal port | 9898 |
| Hostname | `backup.home` |
| Health check | `GET /` → 200 |
| Access | Admin only (Authentik + Backrest auth) |

## What Backrest Provides

- **Repository Management** — Configure backup targets (Pi, B2, local)
- **Scheduling** — Cron-based backup schedules with retention policies
- **Monitoring** — Health status, connectivity checks, operation history
- **Snapshot Browser** — List backups by date, service, size
- **Restore UI** — Browse and restore files from any snapshot
- **Alerts** — Notifications for backup failures

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Homelab                                  │
│                                                                  │
│  ┌──────────┐  forward   ┌──────────┐        ┌──────────┐      │
│  │  Caddy   │───auth────►│ Authentik│        │ Backrest │      │
│  │          │◄───────────│  (SSO)   │        │  :9898   │      │
│  └────┬─────┘            └──────────┘        └────┬─────┘      │
│       │                                           │             │
│       │  backup.home                              │             │
│       └──────────────────────────────────────────►│             │
│                                                   │             │
│  ┌────────────────────────────────────────────────┼───────────┐│
│  │ Mounted Volumes (read-only)                    │           ││
│  │                                                ▼           ││
│  │  /sources/platform/authentik/data ◄────── Backrest        ││
│  │  /sources/platform/postgres/data              │            ││
│  │  /sources/apps/immich/data                    │            ││
│  │  /sources/apps/copyparty/data                 │            ││
│  │  ...                                          │            ││
│  └───────────────────────────────────────────────┼────────────┘│
│                                                   │             │
└───────────────────────────────────────────────────┼─────────────┘
                                                    │
                              Tailscale VPN         │
                                                    ▼
                          ┌─────────────────────────────────────┐
                          │      Raspberry Pi (Offsite)         │
                          │                                     │
                          │   /backups/homelab/                 │
                          │   └── Restic Repository             │
                          └─────────────────────────────────────┘
```

## Commands

```bash
# Start
docker compose -f apps/backrest/compose.yml up -d

# Stop
docker compose -f apps/backrest/compose.yml down

# Logs
docker compose -f apps/backrest/compose.yml logs -f

# Restart
docker compose -f apps/backrest/compose.yml restart

# Update
# 1. Edit compose.yml with new version
# 2. Pull and restart
docker compose -f apps/backrest/compose.yml pull
docker compose -f apps/backrest/compose.yml up -d
```

## First-Run Setup

### Prerequisites

1. Raspberry Pi configured as backup target (see `platform/backup/README.md`)
2. SSH key access to Pi working: `ssh pi@<pi-ip>`
3. Authentik running with `homelab-admin` group

### Step 1: Start Backrest

```bash
cp apps/backrest/.env.example apps/backrest/.env
# Edit .env with your timezone

docker compose -f apps/backrest/compose.yml up -d
```

### Step 2: Create Backrest Admin Account

1. Open http://backup.home (authenticate via Authentik first)
2. On first access, create a Backrest username and password
3. This is Backrest's internal auth (second layer after Authentik)

### Step 3: Add Repository

1. Click **Add Repository**
2. Configure:
   - **Name:** `homelab-offsite`
   - **Type:** SFTP
   - **URI:** `sftp:pi@<pi-tailscale-ip>:/backups/homelab`
   - **Password:** Your Restic repository password
3. Click **Test Connection** to verify
4. Save

### Step 4: Create Backup Plans

Create a plan for each service tier:

**Plan: Platform Critical**
- Paths: `/sources/platform/authentik/data`, `/sources/platform/postgres/data`
- Schedule: Daily at 2:00 AM
- Retention: 14 daily, 8 weekly, 6 monthly

**Plan: Platform Services**
- Paths: `/sources/platform/caddy/data`, `/sources/platform/uptime-kuma/data`, etc.
- Schedule: Daily at 2:30 AM
- Retention: 14 daily, 4 weekly

**Plan: Applications**
- Paths: `/sources/apps/immich/data`, `/sources/apps/copyparty/data`, etc.
- Schedule: Daily at 3:00 AM
- Retention: 14 daily, 8 weekly, 6 monthly

**Plan: Manifests**
- Paths: `/sources/manifests`
- Excludes: `.git`, `**/data`, `**/node_modules`
- Schedule: Daily at 3:30 AM
- Retention: 30 daily

### Step 5: Test Backup

1. Select a plan
2. Click **Run Now**
3. Monitor the operation in the Activity tab
4. Verify snapshot appears in the Snapshots tab

## Backup Paths

Backrest mounts homelab directories under `/sources/`:

| Container Path | Host Path | Contents |
|----------------|-----------|----------|
| `/sources/platform/authentik/data` | `platform/authentik/data` | SSO database, config |
| `/sources/platform/postgres/data` | `platform/postgres/data` | Shared PostgreSQL |
| `/sources/platform/caddy/data` | `platform/caddy/data` | TLS certs, config |
| `/sources/platform/uptime-kuma/data` | `platform/uptime-kuma/data` | Monitors |
| `/sources/platform/homepage/config` | `platform/homepage/config` | Dashboard config |
| `/sources/apps/immich/data` | `apps/immich/data` | Photos, videos |
| `/sources/apps/copyparty/data` | `apps/copyparty/data` | Shared files |
| `/sources/apps/matrix/data` | `apps/matrix/data` | Chat history |
| `/sources/manifests` | Repository root | Compose files, docs |

All paths are mounted **read-only** — Backrest cannot modify your data.

## Monitoring

### Health Check

Backrest shows repository health on the main dashboard:
- **Connected** — Repository accessible
- **Last Backup** — Time since last successful backup
- **Snapshots** — Total count and size

### Alerts

Configure notifications in Settings → Notifications:
- **Email** — SMTP configuration
- **Discord/Slack** — Webhook URL
- **Healthchecks.io** — Ping on success/failure

### Uptime Kuma Integration

Add a monitor in Uptime Kuma:
- Type: HTTP(s)
- URL: `http://backrest:9898/`
- Expected status: 200

## Restore Operations

### Browse and Restore Files

1. Go to **Snapshots** tab
2. Select a snapshot (by date/service)
3. Click **Browse**
4. Navigate to the file/folder
5. Click **Restore** and choose destination

### Full Service Restore

For full disaster recovery, use the CLI scripts which handle:
- Service stop/start ordering
- Database dump restoration
- Post-restore hooks

```bash
scripts/dr-restore --service immich
```

Backrest is best for:
- Browsing what's in backups
- Restoring individual files
- Verifying backup contents

## Relationship to CLI Scripts

| Task | Use Backrest | Use CLI Scripts |
|------|--------------|-----------------|
| Configure repositories | ✓ | |
| Schedule backups | ✓ | |
| Monitor backup health | ✓ | |
| Browse snapshots | ✓ | |
| Restore individual files | ✓ | |
| Full DR restore | | ✓ `dr-restore` |
| Ad-hoc service backup | Either | ✓ `backup-all --service` |
| Automated daily backup | ✓ (Backrest scheduler) | ✓ (launchd) |

**Recommendation:** Use Backrest's scheduler instead of launchd for daily backups. Backrest provides better visibility into backup operations.

To disable the launchd schedule (if using Backrest):
```bash
scripts/setup-backup-schedule --remove
```

## Security

### Two-Layer Authentication

1. **Authentik** — Must be in `homelab-admin` group to access `backup.home`
2. **Backrest** — Username/password created on first run

### Data Access

- Backrest has **read-only** access to all service data
- Cannot modify or delete source data
- Can only write to its own config/data directories

### Repository Password

- Stored in Backrest's encrypted configuration
- Also store offline in password manager (for DR scenarios)
- If lost, backups cannot be decrypted

## Troubleshooting

### "Connection refused" to Pi

1. Check Tailscale: `tailscale status`
2. Verify SSH works: `ssh pi@<pi-ip>`
3. Check Pi is online and disk is mounted

### Backrest can't find data

Verify volume mounts in compose.yml match your actual paths:
```bash
docker compose -f apps/backrest/compose.yml config | grep -A5 volumes
```

### Backup fails with permission error

Ensure source paths are mounted read-only (`:ro`) and exist:
```bash
ls -la platform/authentik/data
```

### Can't access backup.home

1. Check Caddy is running: `docker ps | grep caddy`
2. Check Authentik is running: `docker ps | grep authentik`
3. Verify you're in `homelab-admin` group in Authentik
4. Check Caddy logs: `docker logs caddy`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `UTC` | Timezone for scheduling |
| `BACKREST_PORT` | `0.0.0.0:9898` | Listen address (set in compose) |
| `BACKREST_CONFIG` | `/config/config.json` | Config file path |
| `BACKREST_DATA` | `/data` | Data directory |

## Upstream

- GitHub: https://github.com/garethgeorge/backrest
- Documentation: https://garethgeorge.github.io/backrest/
- Releases: https://github.com/garethgeorge/backrest/releases
