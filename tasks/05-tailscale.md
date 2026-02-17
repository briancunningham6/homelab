# Task 05: Tailscale Secure Remote Access

## Context
Read `CLAUDE.md` for project conventions. Read `docs/adrs/004-tailscale-remote-access.md` for the technology decision. Read `docs/security.md` § 2 for the zero-exposure network model. Tailscale provides WireGuard-based VPN mesh for secure remote access without port forwarding.

## Objective
Create the complete Tailscale stack in `platform/tailscale/`.

## Output Files

```
platform/tailscale/
├── compose.yml
├── .env
├── .env.example
├── data/                   # Created at runtime (gitignored)
└── README.md
```

## Requirements

### compose.yml
- Use `tailscale/tailscale` with a pinned version tag (check https://hub.docker.com/r/tailscale/tailscale/tags for latest stable)
- `restart: unless-stopped`
- Mount `./data` to `/var/lib/tailscale` for persistent state
- Mount `/dev/net/tun` as a device (required for Tailscale)
- Set `cap_add: [NET_ADMIN, NET_RAW]` (required for Tailscale networking)
- Environment variables from `.env`:
  - `TS_AUTHKEY` — Tailscale auth key for automated setup
  - `TS_HOSTNAME` — device hostname in the tailnet (e.g., `homelab-mac-mini`)
  - `TS_STATE_DIR=/var/lib/tailscale`
  - `TS_EXTRA_ARGS` — optional additional flags
- Network mode: `host` is commonly used for Tailscale containers — **this is an exception to the no-host-network rule**. Document this clearly in the README with justification (Tailscale needs to manage the host's network routing).
- Alternatively, if subnet routing is not needed, use a standard bridge network and document the trade-off.
- Container name: `tailscale`

### .env.example
```
# Tailscale Configuration
# Generate an auth key at https://login.tailscale.com/admin/settings/keys
TS_AUTHKEY=tskey-auth-XXXXXXXXXXXX
TS_HOSTNAME=homelab-mac-mini
TS_STATE_DIR=/var/lib/tailscale
TS_EXTRA_ARGS=
```

### README.md
Follow the template from CLAUDE.md. Include:
- What Tailscale does (WireGuard VPN mesh, secure remote access, MagicDNS)
- Quick reference: image, version, no HTTP port (VPN-level access), no hostname (it provides the network)
- Commands: start, stop, restart, update with rollback
- Setup procedure:
  1. Generate an auth key at https://login.tailscale.com/admin/settings/keys
  2. Set `TS_AUTHKEY` in `.env`
  3. Start the container
  4. Verify device appears in Tailscale admin console
  5. Enable MagicDNS if not already enabled in tailnet settings
- Why `network_mode: host` (or `cap_add`) is needed — Tailscale manages routing
- Security note: Tailscale is the ONLY remote access method. No router port forwarding.
- Backup: state is in `./data/` — include in platform backup scope
- Upstream: https://tailscale.com/kb/1282/docker

## Constraints
- `network_mode: host` is justified here — Tailscale must manage host networking. This is the documented exception per `docs/security.md`.
- Auth key is sensitive — must be in `.env`, never committed
- On macOS with Docker Desktop/Colima, Tailscale in a container has limitations. The README should note that Tailscale may alternatively be installed natively on macOS (via `brew install tailscale` or the App Store) with the container approach as an option for Linux hosts. Document both paths.

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] Auth key is in `.env.example` with placeholder
- [ ] `network_mode: host` or equivalent is documented and justified
- [ ] macOS native vs container trade-off is documented in README
- [ ] README includes all required sections
