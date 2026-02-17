# Service Inventory

> All deployed services, ports, hostnames, and backup targets | Parent: [DESIGN.md](../DESIGN.md)

Last updated: YYYY-MM-DD

## Platform Services

| Service | Hostname | Container | Ports (internal) | Ports (host) | Image | Version | Backup Scope | Owner |
|---------|----------|-----------|-----------------|-------------|-------|---------|-------------|-------|
| Caddy | — | caddy | 80, 443 | 80, 443 | caddy | x.x.x | Config only | Brian |
| Dockge | dockge.home | dockge | 5001 | — | louislam/dockge | x.x.x | ./data (SQLite) | Brian |
| Homepage | home.home | homepage | 3000 | — | ghcr.io/gethomepage/homepage | x.x.x | ./config | Brian |
| Uptime Kuma | status.home | uptime-kuma | 3001 | — | louislam/uptime-kuma | x.x.x | ./data (SQLite) | Brian |
| Tailscale | — | tailscale | — | — | tailscale/tailscale | x.x.x | ./data | Brian |
| Authentik | login.home | authentik-server | 9000, 9443 | — | ghcr.io/goauthentik/server | x.x.x | PostgreSQL + config | Brian |

## Application Services

| Service | Hostname | Container | Ports (internal) | Ports (host) | Image | Version | Backup Scope | Owner |
|---------|----------|-----------|-----------------|-------------|-------|---------|-------------|-------|
| Immich | immich.home | immich-server | 2283 | — | ghcr.io/immich-app/immich-server | x.x.x | PostgreSQL + media library | Brian |

## Notes

- "Ports (host)" = published to the host. Blank means internal only (proxied via Caddy).
- Update this document after every deployment, update, or removal.
- Version should match the pinned image tag in compose.yml.
