# Scripts — Operational Tooling

Convenience scripts for day-to-day homelab operations. These scripts wrap `docker compose` and `restic` commands for consistency and safety.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `HOMELAB_DIR` | `~/homelab` | Root of the homelab repository |
| `LOCAL_BACKUP_DIR` | `$HOMELAB_DIR/backups/local` | Local tar backup destination |

## Scripts

### `app-up <app-name>`
Start a service. Searches `apps/`, `platform/`, and `ai/` directories.

```bash
scripts/app-up caddy
scripts/app-up immich
```

### `app-down <app-name>`
Stop a service.

```bash
scripts/app-down immich
```

### `app-update <app-name> <new-version>`
Update a service to a new image version. Implements a 7-step workflow:
1. Show current image tag
2. Confirm before proceeding
3. Run pre-update backup
4. Update image tag in `compose.yml`
5. Pull new image and recreate containers
6. Check health
7. Confirm success or offer rollback

```bash
scripts/app-update immich v1.131.0
scripts/app-update caddy 2.9.2
```

### `app-backup <app-name>`
Backup an app's `data/` directory.
- If Restic is configured (via `RESTIC_REPOSITORY` + `RESTIC_PASSWORD` in `.env` or `backups/restic.env`): uses Restic
- Otherwise: creates a timestamped tar archive in `backups/local/`

```bash
scripts/app-backup uptime-kuma
scripts/app-backup immich
```

### `app-restore <app-name> [snapshot-id]`
Restore an app from backup. Stops the app, restores, then restarts.

```bash
scripts/app-restore uptime-kuma          # Restore latest
scripts/app-restore uptime-kuma abc12345 # Restore specific Restic snapshot
```

### `dr-verify`
Platform-wide health and DR readiness check:
1. Checks all Compose stacks have running containers
2. Checks HTTP health endpoints
3. Checks disk usage (75% warning, 85% critical)
4. Checks backup freshness (warns if no backup in 24h)

```bash
scripts/dr-verify
```

Exit code 0 = all critical checks passed. Non-zero = failures found.

### `platform-up`
Start all platform services in the correct boot order:
1. Tailscale (VPN)
2. Caddy (proxy)
3. Authentik (identity — if deployed)
4. Uptime Kuma (monitoring)
5. Homepage (dashboard)
6. Dockge (management)
7. All app stacks

```bash
scripts/platform-up
```

### `platform-down`
Stop all services in reverse boot order (apps first, Tailscale last).

```bash
scripts/platform-down
```

## Boot Sequence

Services are started in a specific order because:
- **Tailscale** must be up for remote access during startup
- **Caddy** must be up before any HTTP-proxied services are accessible
- **Authentik** must be up before apps that depend on SSO
- **Apps** start last, after all platform dependencies are ready

Reverse order on shutdown ensures apps cleanly disconnect from platform services before they stop.

## Notes

- Scripts are macOS-compatible (BSD `sed -i ''`, `find -mtime`)
- Scripts are non-destructive by default — restore operations prompt before overwriting
- The underlying operations are standard `docker compose` and `restic` commands
- See `docs/ops-standard.md` for the full operational procedures these scripts implement
