# Uptime Kuma — Health Monitoring

Uptime Kuma monitors service health endpoints and provides uptime statistics, alerting, and status pages. It is the primary observability tool for the homelab platform, watching all services and alerting on failures.

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `louislam/uptime-kuma` |
| Version | `1.23.16` |
| Port (internal) | `3001` |
| Hostname | `status.home` |
| Health endpoint | `/` |
| Data | `./data` (SQLite) |
| Upstream | https://github.com/louislam/uptime-kuma |

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart uptime-kuma

# View logs
docker compose logs -f uptime-kuma

# Update to new version
# 1. Edit compose.yml — update image tag to new version
# 2. docker compose pull
# 3. docker compose up -d
# Rollback: revert compose.yml change and run docker compose up -d
```

## First-Run Setup

On first launch, Uptime Kuma will prompt you to create an admin account:

1. Navigate to `http://status.home`
2. Create an admin username and password
3. Add monitors (see recommended monitors below)

**Note:** Admin credentials are stored in the SQLite database at `./data/kuma.db` — include this in backups.

## Recommended Monitors

Add these monitors after first launch via the web UI:

| Monitor Name | Type | URL | Interval |
|-------------|------|-----|----------|
| Caddy | HTTP | `http://caddy:80` | 60s |
| Dockge | HTTP | `http://dockge:5001` | 60s |
| Homepage | HTTP | `http://homepage:3000` | 60s |
| Authentik | HTTP | `http://authentik-server:9000/-/health/live/` | 60s |
| Immich | HTTP | `http://immich-server:2283/api/server/ping` | 60s |

**Note:** Uptime Kuma is on `caddy-net` and can reach other containers by their container names.

## Backup

Monitor configuration is stored in Kuma's SQLite database:

```bash
# Backup the data directory
cp -r ./data ./data-backup-$(date +%Y%m%d)

# Or via the app-backup script
scripts/app-backup uptime-kuma
```

Include `./data` in the platform backup scope (Restic or local tar).

## Networking

Uptime Kuma joins the `caddy-net` external network to:
1. Be proxied by Caddy at `status.home`
2. Reach other containers directly by name for monitoring

The `caddy-net` network must already exist (created by the Caddy stack).

## Upstream

- [Uptime Kuma GitHub](https://github.com/louislam/uptime-kuma)
- [Uptime Kuma Releases](https://github.com/louislam/uptime-kuma/releases)
