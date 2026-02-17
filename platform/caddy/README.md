# Caddy Reverse Proxy

Caddy is the reverse proxy for the homelab platform. It routes all HTTP traffic from local hostnames (e.g., `dockge.home`, `home.home`) to the appropriate backend containers using internal Docker DNS. It handles TLS termination internally — no public certificate authority is required for this local-only setup.

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `caddy` |
| Version | `2.9.1` |
| Ports (host) | `80`, `443` |
| Hostname | — (Caddy IS the proxy) |
| Health endpoint | `http://localhost:80` |
| Config file | `./Caddyfile` |

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart caddy

# View logs
docker compose logs -f caddy

# Reload config without restart (zero downtime)
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# Update to new version
# 1. Edit compose.yml — update image tag
# 2. docker compose pull
# 3. docker compose up -d
# Rollback: revert compose.yml change and run docker compose up -d
```

## Adding a New Service Route

1. Edit `Caddyfile` and add a new block:
   ```
   myapp.home {
       reverse_proxy myapp-container:8080
       header_up X-Real-IP {remote_host}
       header_up X-Forwarded-For {remote_host}
       header_up X-Forwarded-Proto {scheme}
   }
   ```
2. Ensure the target container joins `caddy-net` (add `caddy-net` to its `networks:`)
3. Reload Caddy (no restart needed):
   ```bash
   docker exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```
4. Add the hostname to `/etc/hosts` or your local DNS resolver.

## Networking

Caddy operates on the `caddy-net` Docker bridge network. All services that need to be proxied must join this network. Services communicate over internal Docker DNS using container names as hostnames.

Only ports 80 and 443 are published to the host. All other services are internal only.

## Environment Variables

See `.env.example`. No secrets are required for local-only deployments.

## Upstream

- [Caddy Documentation](https://caddyserver.com/docs/)
- [Caddy Docker Hub](https://hub.docker.com/_/caddy)
