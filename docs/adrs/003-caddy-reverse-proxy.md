# ADR-003: Caddy as Reverse Proxy

## Status

**Accepted**

## Date

2026-02-17

## Context

A reverse proxy is needed to provide stable local hostnames (e.g., `immich.home`, `login.home`) and terminate TLS for internal services. The proxy must be simple to configure, support automatic HTTPS, and integrate with the Docker Compose deployment model.

## Decision

Use **Caddy** as the reverse proxy for all homelab services.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| Traefik | Auto-discovery of Docker containers, powerful routing | Complex label-based config, steeper learning curve, harder to debug | Caddy's Caddyfile is simpler to read and maintain for a small number of services |
| Nginx Proxy Manager | GUI-based, beginner-friendly | Less flexible, UI-driven config harder to version control, extra database dependency | Caddyfile is easier to keep in git and reproduce |
| Nginx (raw) | Battle-tested, very flexible | Manual config, no automatic HTTPS, verbose syntax | Higher maintenance burden for no clear benefit at this scale |

## Consequences

- **Positive:** Caddyfile syntax is minimal — a few lines per service.
- **Positive:** Automatic HTTPS with internal certificates (or Let's Encrypt if ever needed).
- **Positive:** Config file is easily version-controlled alongside the platform stack.
- **Trade-off:** No auto-discovery of Docker containers (unlike Traefik). Manual Caddyfile entries required per service. Acceptable given the small service count.

## References

- [Caddy documentation](https://caddyserver.com/docs/)
- [Caddy Docker proxy plugin](https://github.com/lucaslorentz/caddy-docker-proxy) (optional future enhancement)
