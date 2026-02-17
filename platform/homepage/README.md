# Homepage — Family Dashboard

Homepage is the family-facing dashboard for the homelab platform. It displays all homelab services with live health status, quick-access links, and a search bar. It is the default landing page for all users on the home network.

**Note:** Homepage is the user-facing dashboard. The admin control panel (future) is a separate interface for platform management.

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `ghcr.io/gethomepage/homepage` |
| Version | `v0.10.9` |
| Port (internal) | `3000` |
| Hostname | `home.home` |
| Config directory | `./config/` |
| Upstream | https://github.com/gethomepage/homepage |

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart homepage

# View logs
docker compose logs -f homepage

# Update to new version
# 1. Edit compose.yml — update image tag to new version
# 2. docker compose pull
# 3. docker compose up -d
# Rollback: revert compose.yml change and run docker compose up -d
```

## Adding a New Service

Edit `config/services.yaml` and add a new entry under the appropriate group:

```yaml
- Platform:
    - My New Service:
        href: http://myservice.home
        description: What it does
        icon: myservice
        server: my-docker
        container: myservice-container-name
```

Homepage picks up config changes automatically — no restart needed.

## Docker Integration

Homepage mounts the Docker socket read-only (`/var/run/docker.sock:ro`) to display live container status for each service. This is lower-risk than read-write socket access but still provides visibility into all running containers. The socket is mounted read-only — Homepage cannot start, stop, or modify containers.

## Configuration Files

| File | Purpose |
|------|---------|
| `config/services.yaml` | Service cards and links shown on the dashboard |
| `config/settings.yaml` | Theme, layout, and title |
| `config/bookmarks.yaml` | Bookmark links (documentation, external) |
| `config/widgets.yaml` | Top-bar widgets (search, clock) |

Config files are in `config/` (not `data/`) because they are managed configuration, not runtime state. They are committed to git.

## Environment Variables

See `.env.example`. No secrets are required.

## Networking

Homepage joins the `caddy-net` external network so Caddy can proxy it at `home.home`. The `caddy-net` network must already exist (created by the Caddy stack).

## Upstream

- [Homepage GitHub](https://github.com/gethomepage/homepage)
- [Homepage Docs](https://gethomepage.dev/latest/)
