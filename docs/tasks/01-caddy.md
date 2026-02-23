# Task 01: Caddy Reverse Proxy Stack

## Context
Read `CLAUDE.md` for project conventions. Read `docs/adrs/003-caddy-reverse-proxy.md` for the technology decision. Read `DESIGN.md` § 4 for networking and hostname conventions.

## Objective
Create the complete Caddy reverse proxy stack in `platform/caddy/`.

## Output Files

```
platform/caddy/
├── compose.yml
├── .env
├── .env.example
├── Caddyfile
├── data/                   # Created at runtime (gitignored)
└── README.md
```

## Requirements

### compose.yml
- Use official Caddy image with a pinned version tag (check https://hub.docker.com/_/caddy for latest stable)
- `restart: unless-stopped`
- Publish ports 80 and 443 on the host
- Mount `./Caddyfile` as the config file
- Mount `./data/caddy_data` to `/data` (TLS certs and state)
- Mount `./data/caddy_config` to `/config`
- Define a Docker network `caddy-net` (other services will join this network)
- Container name: `caddy`

### Caddyfile
- Create route entries for all known services. Use placeholder upstream addresses that will be updated as services deploy:
  ```
  dockge.home {
      reverse_proxy dockge:5001
  }

  home.home {
      reverse_proxy homepage:3000
  }

  status.home {
      reverse_proxy uptime-kuma:3001
  }

  login.home {
      reverse_proxy authentik-server:9000
  }

  immich.home {
      reverse_proxy immich-server:2283
  }
  ```
- Each block should include appropriate headers (X-Real-IP, X-Forwarded-For, X-Forwarded-Proto)
- Add a comment block at the top explaining how to add new services
- Use internal Docker DNS names (container names on the shared network)

### .env.example
- Minimal — Caddy typically needs no secrets. Include a commented placeholder for any custom domain or email if using public ACME.

### README.md
Follow the template from CLAUDE.md. Include:
- What Caddy does in this platform (reverse proxy, local hostname routing, TLS)
- Quick reference: image, version, ports 80/443, no dedicated hostname (it IS the proxy)
- Commands: start, stop, restart, update with rollback
- How to add a new service route (edit Caddyfile, reload)
- How Caddy reload works (`docker exec caddy caddy reload --config /etc/caddy/Caddyfile`)
- Note: Caddy uses internal Docker networks — services must join `caddy-net`

## Constraints
- Do NOT use Caddy's automatic HTTPS with public CAs — this is local only
- Do NOT use `network_mode: host`
- The Caddyfile must be human-editable (no JSON config, no API-driven config)
- Caddy is a Phase 1 service — it has no dependency on Authentik (forward auth will be added in Phase 2)

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] Caddyfile is syntactically valid
- [ ] All known service hostnames are routed
- [ ] README includes all required sections
- [ ] `.env.example` is committed, `.env` is gitignored
