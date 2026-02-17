# CLAUDE.md — Project Context for Claude Code

## Project Overview

This is a homelab platform specification and implementation repo. It defines a self-hosted platform running on a Mac mini that replaces cloud services with containerised applications for a family. The platform uses Docker Compose for all services, Authentik for identity/SSO, Caddy for reverse proxy, Tailscale for secure remote access, and Restic for encrypted backups.

## Repository Structure

```
~/homelab/
├── DESIGN.md                    # Core architecture document — read this first
├── CLAUDE.md                    # This file — project context for Claude Code
├── tasks/                       # Agent task definitions for implementation work
├── platform/                    # Platform service stacks (Compose)
│   ├── caddy/
│   ├── dockge/
│   ├── homepage/
│   ├── uptime-kuma/
│   ├── tailscale/
│   ├── authentik/
│   └── control-panel/
├── apps/                        # Application stacks (Compose)
│   └── immich/
├── ai/                          # AI service stacks (future)
├── backups/                     # Backup repositories
├── scripts/                     # Operational scripts
└── docs/                        # All project documentation
```

## Key Documentation (read before implementing)

| Document | What it tells you |
|----------|-------------------|
| `DESIGN.md` | Architecture, principles, component inventory, filesystem layout, networking, storage, identity |
| `docs/app-spec.md` | How every app must be packaged — folder layout, auth, networking, health, backup contract, `app-contract.yaml` |
| `docs/ops-standard.md` | Backup 3-2-1 model, DR, security baseline, boot sequence, update workflow, testing |
| `docs/security.md` | Threat model, network security, secrets management, container hardening, accepted risks |
| `docs/control-panel.md` | Admin UI design — modules, integrations, phasing |
| `docs/onboarding.md` | Admin bootstrap and user management procedures |
| `docs/rollout-plan.md` | Phased implementation plan with task tracking |
| `docs/dependencies.md` | Licensing audit, portability analysis, risk assessment |
| `docs/agent-model.md` | OpenClaw AI agent layer — lanes, isolation, management contract |
| `docs/notes/mac-mini.md` | macOS-specific config: launchd, storage mounts, resource sharing |

## Conventions — All Agents Must Follow

### File naming
- Folder names: lowercase kebab-case (`uptime-kuma/`, not `UptimeKuma/`)
- Compose files: always `compose.yml` (not `docker-compose.yml`)
- Environment: `.env` for secrets, `.env.example` for documented template (committed to git)

### Docker Compose rules
- **Pinned image tags** — never use `latest`. Use explicit versions (e.g., `image: ghcr.io/immich-app/immich-server:v1.130.3`)
- **`restart: unless-stopped`** on all containers
- **Non-root user** inside containers where feasible
- **No `privileged: true`** unless documented and justified
- **No `network_mode: host`** — use Docker bridge networks
- Use Docker named volumes or bind mounts to `./data/` for persistent state
- Secrets via `${VARIABLE}` referencing `.env` — never hardcoded

### Standard app folder layout
Every platform service and app follows this structure:
```
<service-name>/
├── compose.yml
├── .env                    # Actual secrets (gitignored)
├── .env.example            # Template with placeholder values (committed)
├── data/                   # Persistent state (gitignored)
└── README.md               # Start, stop, update, rollback, backup, restore
```

### README template for each service
Each README.md must include:
- What the service does (one paragraph)
- Quick reference table: image, version, ports, hostname, health endpoint
- Commands: start, stop, restart, update (with rollback), backup, restore
- Environment variables reference (from .env.example)
- Authentik integration notes (if applicable)
- Upstream links

### Networking
- Services communicate over internal Docker networks
- Caddy handles all HTTP routing via local hostnames (e.g., `immich.home`, `login.home`)
- Only publish host ports when absolutely necessary
- Admin UIs restricted to LAN/Tailscale

### .gitignore
The following must be gitignored:
- `.env` (secrets)
- `data/` directories (persistent state)
- `backups/` directories
- Any generated credentials or keys

## Platform Services (Phase 1)

| Service | Hostname | Purpose | Default Port |
|---------|----------|---------|-------------|
| Caddy | — (reverse proxy) | Routes all HTTP traffic, TLS termination | 80, 443 |
| Dockge | `dockge.home` | Docker Compose stack management UI | 5001 |
| Homepage | `home.home` | Dashboard / app launcher | 3000 |
| Uptime Kuma | `status.home` | Health monitoring | 3001 |
| Tailscale | — (VPN) | Secure remote access | — |

## Identity (Phase 2)

| Service | Hostname | Purpose | Default Port |
|---------|----------|---------|-------------|
| Authentik | `login.home` | SSO, users, groups, RBAC | 9000 (HTTP), 9443 (HTTPS) |
| PostgreSQL | — (internal) | Authentik database | 5432 |
| Redis | — (internal) | Authentik cache | 6379 |

## Applications (Phase 3)

| Service | Hostname | Purpose | Default Port |
|---------|----------|---------|-------------|
| Immich | `immich.home` | Photo/video management | 2283 |

## Important Constraints

1. **macOS host** — Docker Desktop or Colima required (not native Docker Engine). Auto-start via `launchd`, not `systemd`.
2. **Resource-shared** — Mac mini runs Minecraft too. Use conservative resource limits.
3. **No internet exposure** — all remote access via Tailscale. No port forwarding.
4. **Identity-first** — every service with a UI must integrate with Authentik SSO (OIDC preferred).
5. **Backup contract** — every service must declare its backup scope and have documented restore procedures.

## Task System

Implementation tasks are defined in `tasks/`. Each task file is a self-contained prompt for a Claude Code agent session. Tasks are numbered and can be run in parallel where dependencies allow.

See `tasks/README.md` for the execution plan and dependency map.
