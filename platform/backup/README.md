# Backup System — Encrypted Offsite Backups

Restic-based backup system implementing 3-2-1 strategy: 3 copies of data, on 2 different media, with 1 offsite.

## Quick Reference

| Item | Value |
|------|-------|
| Tool | Restic (client-side encryption) |
| Primary target | Raspberry Pi via Tailscale (SFTP) |
| Secondary target | Backblaze B2 (optional) |
| Schedule | Daily at 3:00 AM |
| RPO | ≤ 24 hours |
| RTO | Core platform 4–8 hours |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Mac mini (Primary)                            │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Authentik  │  │  PostgreSQL │  │   Immich    │  │   Matrix    │   │
│  │   (SSO)     │  │  (Shared)   │  │  (Photos)   │  │   (Chat)    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         └────────────────┴────────────────┴────────────────┘           │
│                                    │                                    │
│                          ┌─────────▼─────────┐                         │
│                          │   backup-all      │                         │
│                          │   (Restic)        │                         │
│                          └─────────┬─────────┘                         │
│                                    │ Encrypted                         │
└────────────────────────────────────┼───────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │         Tailscale VPN          │
                    └────────────────┬────────────────┘
                                     │
┌────────────────────────────────────▼───────────────────────────────────┐
│                     Raspberry Pi (Offsite)                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    External HDD                                  │   │
│  │                                                                  │   │
│  │  /backups/homelab/                                              │   │
│  │  ├── config     (repository configuration)                      │   │
│  │  ├── data/      (deduplicated, encrypted chunks)               │   │
│  │  ├── index/     (chunk index)                                   │   │
│  │  ├── keys/      (encrypted repository keys)                     │   │
│  │  ├── locks/     (concurrent access locks)                       │   │
│  │  └── snapshots/ (snapshot metadata)                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## First-Time Setup

### Step 1: Set up the Raspberry Pi

Prerequisites:
- Raspberry Pi with Raspberry Pi OS
- External HDD/SSD attached and mounted (e.g., `/mnt/backup-drive`)
- Pi joined to Tailscale: `sudo tailscale up`

Get the Pi's Tailscale IP:
```bash
tailscale ip -4
# Example: 100.x.y.z
```

### Step 2: Run the setup script

From the Mac mini:
```bash
scripts/setup-backup-pi 100.x.y.z
```

This script:
1. Installs Restic on the Pi
2. Creates the backup directory
3. Sets up SSH key authentication
4. Generates a repository password
5. Initializes the Restic repository
6. Saves configuration to `platform/backup/.env`

### Step 3: Store the password securely

**CRITICAL**: The repository password in `.env` is the only way to decrypt your backups.

Store it in:
- Password manager (1Password, Bitwarden)
- Offline sealed envelope in a safe
- Trusted family member's password manager

### Step 4: Enable scheduled backups

```bash
scripts/setup-backup-schedule
```

This creates a launchd job that runs daily at 3 AM.

## Commands

### Run a backup

```bash
# Full backup of all services
scripts/backup-all

# Backup a single service
scripts/backup-all --service immich

# Backup only manifests (compose files, docs)
scripts/backup-all --manifests-only

# Dry run (show what would be backed up)
scripts/backup-all --dry-run
```

### Check backup status

```bash
# Load backup environment
source platform/backup/.env

# List all snapshots
restic snapshots

# List snapshots for a specific service
restic snapshots --tag immich

# Check repository integrity
restic check

# Show repository size
restic stats
```

### Restore from backup

```bash
# Interactive full restore
scripts/dr-restore

# List available snapshots
scripts/dr-restore --list

# Restore a single service
scripts/dr-restore --service immich

# Restore from specific snapshot
scripts/dr-restore --snapshot abc123

# Dry run
scripts/dr-restore --dry-run
```

### Manage scheduled backups

```bash
# Check if backup job is running
launchctl list | grep com.homelab.backup

# View backup logs
tail -100 platform/backup/logs/scheduled-backup.log

# Disable scheduled backups
scripts/setup-backup-schedule --remove
```

## Backup Scope

### What's backed up

| Service | Data | Pre-backup hook |
|---------|------|-----------------|
| **Authentik** | `data/` (excluding Redis cache) | PostgreSQL dump |
| **PostgreSQL** | `data/` | pg_dumpall for consistency |
| **Caddy** | `data/`, `Caddyfile` | — |
| **Uptime Kuma** | `data/` (excluding WAL files) | — |
| **Homepage** | `config/` (excluding logs) | — |
| **Immich** | `data/upload/` | — |
| **Copyparty** | `data/library/` | — |
| **Matrix** | `data/` | PostgreSQL dump |
| **Manifests** | All `compose.yml`, `.env`, `docs/`, `scripts/` | — |

### What's excluded

- Redis caches (regenerated)
- SQLite WAL/SHM files (transient)
- ML model caches (re-downloaded)
- Log files
- Git directories
- Node modules / Python cache

## Retention Policy

| Period | Snapshots kept |
|--------|----------------|
| Daily | 14 |
| Weekly | 8 |
| Monthly | 6 |
| Yearly | 1 |

Modify in `platform/backup/.env`:
```bash
RETENTION_DAILY=14
RETENTION_WEEKLY=8
RETENTION_MONTHLY=6
RETENTION_YEARLY=1
```

## Disaster Recovery

### Full platform restore

If the Mac mini dies and you're starting fresh:

1. **Prepare new hardware**
   - Install macOS
   - Install Docker Desktop or Colima
   - Install Homebrew, Restic, Git
   - Clone the homelab repo

2. **Join Tailscale**
   ```bash
   brew install tailscale
   sudo tailscale up
   ```

3. **Configure backup access**
   Create `platform/backup/.env` with:
   ```bash
   RESTIC_REPOSITORY=sftp:pi@<tailscale-ip>:/backups/homelab
   RESTIC_PASSWORD=<your-password>
   ```

4. **Run the restore**
   ```bash
   scripts/dr-restore
   ```

5. **Verify services**
   - Check Authentik: http://login.home
   - Check Homepage: http://home.home
   - Test SSO for each app

### Single service restore

If one service has a problem:

```bash
# Stop the service
docker compose -f apps/immich/compose.yml down

# Restore from backup
scripts/dr-restore --service immich

# Verify
docker compose -f apps/immich/compose.yml logs
```

### Point-in-time restore

To restore from a specific date:

```bash
# List snapshots to find the one you want
scripts/dr-restore --list

# Restore from that snapshot
scripts/dr-restore --service immich --snapshot abc123
```

## Monitoring

### Healthchecks.io integration

Add to `platform/backup/.env`:
```bash
HEALTHCHECK_URL=https://hc-ping.com/<your-uuid>
```

The backup script will:
- Ping `/start` when backup begins
- Ping success URL when backup completes
- Ping `/fail` if backup fails

### Uptime Kuma integration

Add a monitor in Uptime Kuma:
- Type: Push
- Heartbeat Interval: 86400 (24h)
- Grace Period: 3600 (1h)

Then add to `platform/backup/.env`:
```bash
HEALTHCHECK_URL=https://status.home/api/push/<token>
```

## Security

### Encryption

- All data is encrypted client-side before leaving the Mac mini
- Uses AES-256-CTR for data, Poly1305-AES for authentication
- Repository password never leaves the primary machine
- Backup target (Pi) only sees encrypted blobs

### Network security

- Backups travel over Tailscale (WireGuard encrypted)
- No ports exposed to the internet
- SSH key authentication (no passwords)

### Access control

- Only the Mac mini has the repository password
- Pi has read/write access to encrypted blobs only
- Emergency access requires the offline password copy

## Troubleshooting

### "repository does not exist"

Repository not initialized. Run:
```bash
source platform/backup/.env
restic init
```

### "wrong password"

Check `.env` file has correct `RESTIC_PASSWORD`. If lost, backups cannot be recovered.

### "connection refused" to Pi

1. Check Pi is online: `ping <pi-ip>`
2. Check Tailscale status: `tailscale status`
3. Check SSH access: `ssh pi@<pi-ip>`
4. Check Pi's disk space: `ssh pi@<pi-ip> df -h`

### Backup is slow

- Check network speed to Pi: `iperf3 -c <pi-ip>`
- First backup is always slow (full upload)
- Subsequent backups only transfer changes
- Consider excluding large regeneratable data

### Restore fails

1. Check service is stopped before restore
2. Verify snapshot exists: `restic snapshots --tag <service>`
3. Check disk space on Mac mini
4. Review logs: `platform/backup/logs/restore-*.log`

## DR Testing

Conduct quarterly restore drills. Record results in `docs/dr-runbook.md`:

```markdown
### DR Drill — [DATE]

**Scope:** Full platform restore to test hardware

**Steps completed:**
- [ ] Prepared test machine with fresh macOS
- [ ] Installed prerequisites (Docker, Restic, Tailscale)
- [ ] Retrieved backup password from offline storage
- [ ] Configured backup environment
- [ ] Ran full restore
- [ ] Verified Authentik login
- [ ] Verified each application
- [ ] Tested SSO flow end-to-end

**Duration:** X hours
**Data loss observed:** None / X hours
**Issues encountered:** [describe]
**Remediation:** [actions taken]
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RESTIC_REPOSITORY` | Yes | Backup target (sftp:user@host:/path) |
| `RESTIC_PASSWORD` | Yes | Repository encryption password |
| `BACKUP_PI_HOST` | No | Pi hostname/IP for reference |
| `BACKUP_PI_USER` | No | SSH user for Pi |
| `BACKUP_PI_PATH` | No | Path on Pi |
| `RETENTION_DAILY` | No | Days to keep (default: 14) |
| `RETENTION_WEEKLY` | No | Weeks to keep (default: 8) |
| `RETENTION_MONTHLY` | No | Months to keep (default: 6) |
| `RETENTION_YEARLY` | No | Years to keep (default: 1) |
| `HEALTHCHECK_URL` | No | Monitoring ping URL |
