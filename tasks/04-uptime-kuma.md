# Task 04: Uptime Kuma Health Monitoring

## Context
Read `CLAUDE.md` for project conventions. Uptime Kuma monitors service health endpoints and alerts when services go down. It's a core observability tool for the platform.

## Objective
Create the complete Uptime Kuma stack in `platform/uptime-kuma/`.

## Output Files

```
platform/uptime-kuma/
├── compose.yml
├── .env
├── .env.example
├── data/                   # Created at runtime (gitignored)
└── README.md
```

## Requirements

### compose.yml
- Use `louislam/uptime-kuma` with a pinned version tag (check https://github.com/louislam/uptime-kuma/releases)
- `restart: unless-stopped`
- Expose port 3001 internally (Caddy will proxy it)
- Mount `./data` to `/app/data` for persistent state (SQLite database)
- Join the `caddy-net` external network
- Container name: `uptime-kuma`

### .env.example
```
# Uptime Kuma — no required secrets
# Monitors are configured via the web UI after first launch
```

### README.md
Follow the template from CLAUDE.md. Include:
- What Uptime Kuma does (health monitoring, uptime alerts)
- Quick reference: image, version, internal port 3001, hostname `status.home`, health endpoint `/`
- Commands: start, stop, restart, update with rollback
- First-run setup: create admin account via web UI on first launch
- Recommended monitors to add after deployment:
  | Monitor | Type | URL | Interval |
  |---------|------|-----|----------|
  | Caddy | HTTP | http://caddy:80 | 60s |
  | Dockge | HTTP | http://dockge:5001 | 60s |
  | Homepage | HTTP | http://homepage:3000 | 60s |
  | Authentik | HTTP | http://authentik-server:9000/-/health/live/ | 60s |
  | Immich | HTTP | http://immich-server:2283/api/server/ping | 60s |
- How to backup Kuma (the SQLite DB in `data/`)
- Upstream: https://github.com/louislam/uptime-kuma

## Constraints
- No Docker socket access needed (Kuma monitors HTTP endpoints, not container state)
- First-run admin account is created via the UI — document this in README
- Monitor configuration is stored in Kuma's SQLite DB — include in backup scope

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] Persistent storage mapped to `./data`
- [ ] Joins `caddy-net` external network
- [ ] README includes recommended monitors table
- [ ] README includes all required sections
