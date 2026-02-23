# Homelab Platform (Experimental) — Quick Start

## Goal
- Build a self-hosted home platform on a Mac mini using Docker Compose.
- Run core services (routing, identity, dashboard, monitoring).
- Deploy applications (starting with Immich/Copyparty) with consistent patterns.
- Enable OpenClaw to manage and interact with the platform/apps.

## Project Intent (for this phase)
- Prioritize speed of iteration and learning.
- Keep setup simple and practical.
- Reliability and long-term hardening are secondary for now.

## Open Source Roadmap (Executive)
Current direction for preparing this project for open source:

1. Legal and governance baseline
2. Security and CI baseline
3. Documentation and support boundaries
4. Testing and recovery confidence
5. Onboarding and app ecosystem
6. Community launch

Launch criteria before public release:
- Governance docs in place (`LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, issue/PR templates).
- Security disclosure policy and baseline threat-model updates are published.
- CI checks and security scans are required on pull requests.
- Support policy and compatibility matrix are explicit.

Detailed operational roadmap: `docs/open-source-roadmap.md`

## What this repo provides
- `platform/`: Core infrastructure stacks (Caddy, Authentik, Homepage, Dockge, Tailscale, Uptime Kuma)
- `apps/`: Application stacks (Immich, Copyparty, etc.)
- `scripts/`: Helper scripts for start/stop/update/backup flows
- `docs/`: Design, rollout plan, ops standards, agent model

## Prerequisites
1. macOS host with Docker Desktop installed and running
2. GitHub repo cloned locally
3. Enough free disk space (recommended **>= 40GB free**)
4. Optional: Tailscale auth key for remote access stack

## Recommended first-run order
1. **Clone and enter repo**
   ```bash
   git clone https://github.com/briancunningham6/homelab.git
   cd homelab
   ```

2. **Prepare env files from examples**
   - Copy each `.env.example` to `.env` where needed
   - Fill required values (passwords, secrets, domain/host values)

3. **Validate all compose files**
   ```bash
   HOMELAB_DIR=$(pwd) ./scripts/validate-compose
   ```

4. **Start platform core (in order)**
   ```bash
   ./scripts/platform-up
   ```

5. **Verify core services**
   - Caddy routing
   - Authentik login page
   - Homepage dashboard
   - Uptime Kuma health panel

6. **Deploy first app (Immich)**
   ```bash
   ./scripts/app-up immich
   ```

7. **Configure identity integration**
   - Create groups/users in Authentik
   - Wire app SSO (OIDC) as documented

8. **Add monitoring + dashboard entries**
   - Ensure app appears in Homepage and Uptime Kuma

9. **Record what was done**
   - Update `docs/inventory.md` and `docs/runbook.md`

## Quick day-2 operations
```bash
# Stop an app
./scripts/app-down <app>

# Update an app
./scripts/app-update <app>

# Backup an app
./scripts/app-backup <app>

# Restore an app
./scripts/app-restore <app>
```

## Notes
- If disk space gets tight, prune Docker and move heavy app data to external storage.
- Keep secrets out of git; use `.env.example` for templates only.
- This is an experiment: optimize for a working vertical slice first.
