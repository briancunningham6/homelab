---
name: homelab-ops
description: Operate the homelab platform — start/stop services, backups, updates, disaster-recovery, and Docker management.
metadata:
  openclaw:
    requires:
      - exec
---

# Homelab — Platform Operations

You can manage the homelab platform through shell scripts and Docker commands.

## Repository Layout

The homelab repo lives at `~/homelab` on the Mac mini. Key paths:

| Path                       | Purpose                                        |
| -------------------------- | ---------------------------------------------- |
| `scripts/platform-up`      | Start all platform services (Caddy, Authentik…) |
| `scripts/app-up <app>`     | Start a single app (e.g., `immich`)            |
| `scripts/app-backup <app>` | Snapshot an app's volumes to backup dir         |
| `scripts/app-update <app>` | Pull latest images and recreate an app          |
| `scripts/dr-verify`        | Verify disaster-recovery readiness              |
| `platform/`                | Platform service compose files                  |
| `apps/`                    | App compose files (immich, etc.)                |
| `DESIGN.md`                | Architecture reference                          |
| `docs/`                    | Operational procedures, runbooks, ADRs          |

## Docker Compose Commands

All services use Docker Compose. Compose files live in their respective directories.

```bash
# List running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Restart a specific service
cd ~/homelab/platform/caddy && docker compose restart

# View logs (last 50 lines, follow)
docker compose -f ~/homelab/apps/immich/compose.yml logs --tail 50 -f

# Pull latest images for an app
cd ~/homelab/apps/immich && docker compose pull && docker compose up -d

# Check resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Platform Scripts

Always use the provided scripts when they exist — they handle ordering, health checks, and logging.

### Start the entire platform

```bash
~/homelab/scripts/platform-up
```

Starts services in dependency order: networking → Caddy → Authentik → Homepage → Dockge → Uptime Kuma.

### Backup an application

```bash
~/homelab/scripts/app-backup immich
```

Creates a timestamped snapshot of all named volumes for the app. Backups go to the configured backup directory.

### Update an application

```bash
~/homelab/scripts/app-update immich
```

Pulls latest images, recreates containers, verifies health.

### Verify disaster recovery

```bash
~/homelab/scripts/dr-verify
```

Checks backup freshness, volume integrity, and restore readiness.

## Service Quick Reference

| Service      | Directory                       | Network     | Key Ports     |
| ------------ | ------------------------------- | ----------- | ------------- |
| Caddy        | `platform/caddy`                | caddy-net   | 80, 443       |
| Authentik    | `platform/authentik`            | caddy-net   | 9000, 9443    |
| PostgreSQL   | `platform/authentik` (bundled)  | authentik   | 5432          |
| Redis        | `platform/authentik` (bundled)  | authentik   | 6379          |
| Homepage     | `platform/homepage`             | caddy-net   | 3000          |
| Dockge       | `platform/dockge`               | caddy-net   | 5001          |
| Uptime Kuma  | `platform/uptime-kuma`          | caddy-net   | 3001          |
| Immich       | `apps/immich`                   | caddy-net + immich-internal | 2283 |

## Guidelines

- **Never run destructive commands** (`docker system prune`, `docker volume rm`) without explicit confirmation and a fresh backup.
- Prefer the platform scripts over raw `docker compose` commands — they handle dependency ordering.
- When updating, always check `docker ps` after to verify containers are healthy.
- The Caddy reverse proxy resolves `*.home` hostnames. If a service is unreachable, check Caddy first.
- All compose files use `restart: unless-stopped`. Manual `docker stop` persists across reboots.
