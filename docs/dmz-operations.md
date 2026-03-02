# DMZ Operations

> Deploy and manage DMZ services from the Mac mini control plane

## Purpose

The Mac mini remains the control plane. The DMZ Raspberry Pi is the execution plane for internet-facing workloads.

All DMZ app changes are:
1. validated locally against DMZ security policy
2. synced over SSH/Tailscale
3. executed remotely with `docker compose`

## One-Time Setup

1. Create a dedicated deploy account on the DMZ Pi (example: `dmz` or `dmz-deploy`)
2. Configure key-only SSH for that account
3. Ensure account can run Docker (`docker` group membership)
4. Keep management access on Tailscale only

## DMZ App Layout

DMZ apps must live in:

```text
dmz/<app>/
├── compose.yml
├── .env.example
├── README.md
└── app-contract.yaml
```

## Security Gate

Run before deployment:

```bash
scripts/validate-dmz-compose all
```

Policy checks:
- no `privileged: true`
- no Docker socket mounts
- no `network_mode: host` unless allowlisted
- explicit non-root `user:` per service
- explicit `healthcheck:` per service
- loopback-only host port binds
- DMZ zone label (`com.homelab.zone=dmz`)

## Deploy Commands

```bash
# Validate only
scripts/dmz-app validate all

# Deploy a single app
scripts/dmz-app up matrix
scripts/dmz-app up blog

# Deploy all DMZ apps
scripts/dmz-app up all

# Check remote status
scripts/dmz-app ps all

# Tail logs
scripts/dmz-app logs matrix
```

### Optional Environment Overrides

```bash
export DMZ_HOST=dmz-pi5
export DMZ_USER=dmz
export DMZ_REMOTE_DIR=/home/dmz/homelab/dmz
```

## Homepage Integration

Homepage includes a `DMZ` category in `platform/homepage/config/services.yaml` with:
- SSH shortcut to the DMZ Pi
- DMZ deployment guide
- Public Matrix and Blog URLs

This gives operators one place (`home.home`) to jump into DMZ operations and services.

## Operational Notes

- Keep DMZ app manifests in git and review changes before deployment.
- Record DMZ deployments and incidents in `docs/runbook.md`.
- Keep the DMZ Pi disposable: if compromised, rebuild and restore from backup.
