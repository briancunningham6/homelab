# DMZ Blog (Static Site)

Static blog deployment for the DMZ Raspberry Pi.

**Deployment Node:** DMZ Pi (`homelab-pi-dmz`) — NOT the Mac mini

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `nginxinc/nginx-unprivileged` |
| Version | `1.27-alpine` |
| Internal Port | `8080` |
| Host Bind | `127.0.0.1:6180` |
| External Ports | `443` (via DMZ Caddy) |
| Data Path | `./public/` |
| Hostname | `blog.yourdomain.com` |

## Prerequisites

1. DMZ Pi reachable over Tailscale + SSH
2. Caddy running on DMZ Pi for TLS and public routing
3. DNS record for `blog.yourdomain.com` pointing at your public endpoint

## Setup

```bash
cd ~/homelab/dmz/blog
cp .env.example .env
```

Configure DMZ Caddy on the Pi:

```caddyfile
blog.yourdomain.com {
    reverse_proxy localhost:6180
}
```

## Deploy from Mac mini

```bash
scripts/dmz-app up blog
```

This command:
1. Validates `dmz/blog/compose.yml` against DMZ security policy
2. Syncs files to the DMZ Pi
3. Runs `docker compose up -d` on the Pi

## Commands

```bash
# Validate DMZ security policy
scripts/validate-dmz-compose blog

# Sync files only
scripts/dmz-app sync blog

# Start / update
scripts/dmz-app up blog

# Stop
scripts/dmz-app down blog

# Logs
scripts/dmz-app logs blog
```

## Security Notes

- Container runs as non-root (`user: 101:101`)
- Content mount is read-only
- Host port is bound to loopback only
- Public ingress is handled by DMZ reverse proxy
- No Docker socket access, no privileged mode
