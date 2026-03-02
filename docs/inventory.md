# Service Inventory

> All deployed services, ports, hostnames, and backup targets | Parent: [DESIGN.md](../DESIGN.md)

Last updated: 2026-02-28

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

## DMZ Services (homelab-pi-dmz)

| Service | Hostname | Container | Ports (internal) | Ports (host) | Image | Version | Backup Scope | Owner |
|---------|----------|-----------|-----------------|-------------|-------|---------|-------------|-------|
| Blog (Static) | blog.yourdomain.com | dmz-blog | 8080 | 6180 (localhost) | nginxinc/nginx-unprivileged | 1.27-alpine | ./public + nginx.conf | Brian |
| Matrix (Conduit) | matrix.yourdomain.com | conduit | 6167 | 6167 (localhost) | matrixconduit/matrix-conduit | v0.8.0 | ./data/conduit | Brian |

**Note:** DMZ services are internet-facing. Ports shown are internal to the Pi; Caddy on the DMZ Pi handles external 443/8448. See [dmz.md](dmz.md) for architecture.

## Notes

- "Ports (host)" = published to the host. Blank means internal only (proxied via Caddy).
- Update this document after every deployment, update, or removal.
- Version should match the pinned image tag in compose.yml.
