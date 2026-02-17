# Dockge — Docker Compose Stack Management

Dockge is a browser-based UI for managing Docker Compose stacks. It lets the admin view, start, stop, update, and edit Compose stacks without using the command line. In this platform, Dockge is the primary interface for stack lifecycle management.

**Note:** Dockge is a management interface — the source of truth for all Compose files is the git repository (`~/homelab`). Do not use Dockge to create new stacks; use it to view and control stacks that are already in git.

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `louislam/dockge` |
| Version | `1.4.2` |
| Port (internal) | `5001` |
| Hostname | `dockge.home` |
| Upstream | https://github.com/louislam/dockge |

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart dockge

# View logs
docker compose logs -f dockge

# Update to new version
# 1. Edit compose.yml — update image tag to new version
# 2. docker compose pull
# 3. docker compose up -d
# Rollback: revert compose.yml change and run docker compose up -d
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCKGE_STACKS_DIR` | `/opt/stacks` | Host path mapped into Dockge for stack management. Set to `~/homelab` to manage all homelab stacks. |

## Security Note: Docker Socket Access

Dockge requires access to the Docker socket (`/var/run/docker.sock`). This grants Dockge — and any user with Dockge access — root-equivalent control over the Docker daemon and the host system.

**Accepted risk:** Dockge is an admin-only tool, accessible only on the LAN/Tailscale network, protected by Authentik SSO. The risk is documented in `docs/security.md`.

The socket is mounted read-write (required — Dockge must start/stop containers). Do not expose Dockge to the internet.

## Stacks Directory

The `DOCKGE_STACKS_DIR` variable maps a host directory into Dockge so it can discover and manage Compose stacks. Set this to `~/homelab` (or the absolute path to the homelab repo) to manage all platform and app stacks from the Dockge UI.

## Networking

Dockge joins the `caddy-net` external network so Caddy can proxy it at `dockge.home`. The `caddy-net` network must already exist (created by the Caddy stack).

## Authentik Integration

Dockge does not natively support OIDC. Access is restricted to admin users via network-level controls (LAN/Tailscale only). A local Dockge account is created on first launch.

## Upstream

- [Dockge GitHub](https://github.com/louislam/dockge)
- [Dockge Releases](https://github.com/louislam/dockge/releases)
