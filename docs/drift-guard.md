# Homelab Drift Guard

`platform-drift-guard` is a lightweight checker that catches (and optionally self-heals) common drift issues seen in this homelab:

- Dockge stack path drift (`platform/dockge/.env`)
- Immich DB credential drift (`apps/immich/.env` vs Postgres login)
- Uptime Kuma corruption early signal (oversized `kuma.db-wal`)
- Core container runtime/health for:
  - `dockge`
  - `uptime-kuma`
  - `immich-server`

## Script location

- `scripts/platform-drift-guard`

## Usage

Read-only check (reports issues):

```bash
HOMELAB_DIR=/Users/briancunningham/dev/homelab scripts/platform-drift-guard
```

Light self-heal mode (non-destructive):

```bash
HOMELAB_DIR=/Users/briancunningham/dev/homelab scripts/platform-drift-guard --fix-light
```

## Exit codes

- `0`: healthy
- `1`: drift found (or fixed)
- `2`: runtime/tooling error

## What `--fix-light` can do

- Normalize Dockge stacks path in `platform/dockge/.env`
- Start/restart missing or unhealthy target containers
- Restart Homepage after fixes so status tiles refresh

It intentionally does **not** perform destructive recovery (e.g., wiping Kuma DB).

## LaunchAgent (macOS)

A local LaunchAgent can run it every 30 minutes:

- `~/Library/LaunchAgents/com.homelab.drift-guard.plist`

Configured command:

```bash
HOMELAB_DIR=/Users/briancunningham/dev/homelab /Users/briancunningham/dev/homelab/scripts/platform-drift-guard --fix-light
```

Log file:

- `/tmp/homelab-drift-guard.log`

## Notes

- Keep app credentials in a single source of truth to avoid drift after redeploys.
- For Uptime Kuma, corruption events should be handled with backup/restore, not auto-healed by this guard.
