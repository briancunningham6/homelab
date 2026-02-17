# Tailscale — Secure Remote Access

Tailscale provides WireGuard-based VPN mesh networking for the homelab. It enables secure remote access to all homelab services from anywhere without port forwarding or exposing services to the internet. All remote access goes through Tailscale — there is no router port forwarding in this platform.

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `tailscale/tailscale` |
| Version | `v1.94.2` |
| Port | — (VPN-level, no HTTP port) |
| Hostname | — (Tailscale provides the network layer) |
| Data | `./data` (Tailscale state and keys) |
| Upstream | https://tailscale.com/kb/1282/docker |

## macOS: Native vs Container

**Recommendation for macOS:** Install Tailscale natively on macOS rather than using the container approach.

| Approach | Pros | Cons |
|----------|------|------|
| **Native macOS (recommended)** | Full OS integration, MagicDNS works reliably, no Docker dependency | Must be managed separately from Docker stacks |
| **Container (this stack)** | Managed with other stacks | Limited on macOS — Docker Desktop/Colima runs in a VM, breaking host networking |

On macOS with Docker Desktop or Colima, `network_mode: host` does not give the container access to the macOS host network — it gives access to the Linux VM's network. This means the container approach has significant limitations for subnet routing and MagicDNS on macOS.

**Native macOS installation:**
```bash
brew install tailscale
# Or download the App Store version: https://apps.apple.com/app/tailscale/id1475387142
sudo tailscale up --authkey=tskey-auth-XXXXXXXXXXXX --hostname=homelab-mac-mini
```

The container stack in this directory is provided for documentation and potential future Linux host use.

## Commands (Container)

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Check Tailscale status
docker exec tailscale tailscale status

# View logs
docker compose logs -f tailscale

# Update to new version
# 1. Edit compose.yml — update image tag to new version
# 2. docker compose pull
# 3. docker compose up -d
# Rollback: revert compose.yml change and run docker compose up -d
```

## Setup Procedure

1. Generate an auth key at https://login.tailscale.com/admin/settings/keys
   - Use a **reusable, non-expiring** key for automated setup
2. Copy `.env.example` to `.env` and set `TS_AUTHKEY`
3. Start the container: `docker compose up -d`
4. Verify the device appears in the [Tailscale admin console](https://login.tailscale.com/admin/machines)
5. Enable MagicDNS in tailnet settings if not already enabled

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TS_AUTHKEY` | — | **Required.** Auth key from Tailscale admin. Never commit. |
| `TS_HOSTNAME` | `homelab-mac-mini` | Device name shown in Tailscale admin console |
| `TS_STATE_DIR` | `/var/lib/tailscale` | Where Tailscale stores state inside the container |
| `TS_EXTRA_ARGS` | — | Optional extra flags passed to `tailscale up` |

## Why `network_mode: host`

Tailscale must manage network routing at the OS level. It creates a TUN device (`/dev/net/tun`) and modifies routing tables to route traffic through the WireGuard tunnel. This requires:

- `network_mode: host` — to access and modify the host's network stack
- `cap_add: [NET_ADMIN, NET_RAW]` — for network administration capabilities
- `/dev/net/tun` device — for the WireGuard tunnel interface

This is the documented exception to the no-host-network rule (see `docs/security.md`). The alternative (`cap_add` without host networking) works for basic VPN but limits subnet routing capabilities.

## Security

- `TS_AUTHKEY` is sensitive — never commit `.env` to git
- Tailscale is the **only** remote access method. No router port forwarding is configured.
- All traffic between devices is end-to-end encrypted by WireGuard
- Access control is managed via Tailscale ACLs in the admin console

## Backup

Tailscale state is stored in `./data/`. Include this in the platform backup scope.

```bash
scripts/app-backup tailscale
```

On restore, the device may need to re-authenticate if the state is lost.

## Upstream

- [Tailscale Docker docs](https://tailscale.com/kb/1282/docker)
- [Tailscale admin console](https://login.tailscale.com/admin)
- [Tailscale GitHub](https://github.com/tailscale/tailscale)
