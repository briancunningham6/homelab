# Task 03: Homepage Dashboard

## Context
Read `CLAUDE.md` for project conventions. Homepage is a dashboard that shows all homelab services with health status and quick links. It's the family-facing landing page.

## Objective
Create the complete Homepage stack in `platform/homepage/`.

## Output Files

```
platform/homepage/
├── compose.yml
├── .env
├── .env.example
├── config/
│   ├── services.yaml
│   ├── settings.yaml
│   ├── bookmarks.yaml
│   └── widgets.yaml
├── data/                   # Created at runtime (gitignored)
└── README.md
```

## Requirements

### compose.yml
- Use `ghcr.io/gethomepage/homepage` with a pinned version tag (check https://github.com/gethomepage/homepage/releases)
- `restart: unless-stopped`
- Expose port 3000 internally (Caddy will proxy it)
- Mount `./config` to `/app/config`
- Mount Docker socket (read-only) for container status widgets: `/var/run/docker.sock:/var/run/docker.sock:ro`
- Join the `caddy-net` external network
- Container name: `homepage`

### config/services.yaml
Pre-populate with all Phase 1–3 services:
```yaml
- Platform:
    - Dockge:
        href: http://dockge.home
        description: Stack Management
        icon: dockge
        server: my-docker
        container: dockge
    - Uptime Kuma:
        href: http://status.home
        description: Health Monitoring
        icon: uptime-kuma
        server: my-docker
        container: uptime-kuma
    - Caddy:
        description: Reverse Proxy
        icon: caddy
        server: my-docker
        container: caddy
    - Authentik:
        href: http://login.home
        description: Identity & SSO
        icon: authentik
        server: my-docker
        container: authentik-server

- Applications:
    - Immich:
        href: http://immich.home
        description: Photos & Videos
        icon: immich
        server: my-docker
        container: immich-server
```

### config/settings.yaml
```yaml
title: Homelab
favicon: https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/home-assistant.png
theme: dark
color: slate
headerStyle: clean
layout:
  Platform:
    style: row
    columns: 4
  Applications:
    style: row
    columns: 3
```

### config/bookmarks.yaml
```yaml
- Documentation:
    - Design:
        - href: https://github.com/briancunningham6/homelab
          icon: github
    - Rollout Plan:
        - href: https://github.com/briancunningham6/homelab/blob/main/docs/rollout-plan.md
          icon: markdown
```

### config/widgets.yaml
```yaml
- search:
    provider: google
    target: _blank
- datetime:
    text_size: xl
    format:
      dateStyle: long
      timeStyle: short
```

### .env.example
```
# Homepage — typically no secrets needed
# HOMEPAGE_VAR_TITLE=Homelab
```

### README.md
Follow the template from CLAUDE.md. Include:
- What Homepage does (family-facing dashboard, service status, quick links)
- Quick reference: image, version, internal port 3000, hostname `home.home`
- Commands: start, stop, restart, update with rollback
- How to add a new service (edit `config/services.yaml`)
- How Docker integration works (socket for container status)
- Note: this is the user-facing dashboard; the control panel (future) is the admin interface
- Upstream: https://github.com/gethomepage/homepage

## Constraints
- Docker socket is mounted read-only — document this
- Config files are in `config/` (not `data/`) because they are part of the managed configuration, not runtime state
- Do NOT hardcode service URLs with IP addresses — use hostnames

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] `services.yaml` lists all Phase 1–3 services
- [ ] `settings.yaml` configures dark theme and layout
- [ ] Joins `caddy-net` external network
- [ ] README includes all required sections
