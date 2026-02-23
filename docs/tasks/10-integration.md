# Task 10: Integration — Wire Everything Together

## Context
Read `CLAUDE.md` for project conventions. This task runs AFTER all other tasks (01–09) are complete. It validates, connects, and finalises the full platform configuration.

**This task depends on ALL previous tasks being complete.**

## Objective
Wire all stacks together: finalise the Caddyfile with all routes, ensure Homepage shows all services, verify Docker networks connect properly, update the rollout plan, and create the root `.gitignore`.

## Output Files

```
.gitignore                          # Root gitignore
platform/caddy/Caddyfile            # Updated with all routes + forward auth
platform/homepage/config/services.yaml  # Updated if needed
docs/rollout-plan.md                # Updated task statuses
```

## Requirements

### 1. Root .gitignore

Create `~/homelab/.gitignore`:

```gitignore
# Secrets — never commit
**/.env
!**/.env.example

# Persistent data — too large and runtime-specific
**/data/
**/backups/

# macOS
.DS_Store
**/.DS_Store

# Docker
**/docker-compose.override.yml
```

### 2. Verify Caddyfile completeness

Open `platform/caddy/Caddyfile` and ensure it has entries for ALL services:

```
# Homelab Platform — Caddy Reverse Proxy Configuration
#
# Each service gets a local hostname routed to its internal Docker address.
# Services must be on the caddy-net Docker network to be reachable.
#
# To add a new service:
# 1. Add a block below with the service hostname
# 2. Set reverse_proxy to the container name and port
# 3. Reload Caddy: docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# --- Platform Services ---

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

# --- Applications ---

immich.home {
    reverse_proxy immich-server:2283
}

# --- Authentik Forward Auth (for apps that need SSO protection) ---
# Uncomment and import in app blocks that need Authentik gating:
#
# (authentik) {
#     forward_auth authentik-server:9000 {
#         uri /outpost.goauthentik.io/auth/caddy
#         copy_headers X-Authentik-Username X-Authentik-Groups X-Authentik-Email X-Authentik-Name X-Authentik-Uid
#         trusted_proxies private_ranges
#     }
# }
```

### 3. Verify Docker network consistency

Check that every Compose file that needs external connectivity has:
```yaml
networks:
  caddy-net:
    external: true
```

The following services MUST join `caddy-net`:
- `platform/caddy/` (defines the network)
- `platform/dockge/`
- `platform/homepage/`
- `platform/uptime-kuma/`
- `platform/authentik/` (the server container)
- `apps/immich/` (the server container)

The following do NOT need `caddy-net`:
- `platform/tailscale/` (host networking)
- Internal-only containers (postgres, redis within their own stacks)

### 4. Verify Homepage services.yaml

Ensure `platform/homepage/config/services.yaml` includes entries for all deployed services with correct hostnames and container references.

### 5. Update rollout plan

Update `docs/rollout-plan.md` — change the Phase 1 task statuses to indicate that infrastructure files have been created (but not yet deployed). Use a note like:

> Infrastructure files created via agent tasks. Deployment pending on Mac mini.

Do NOT mark tasks as complete (green) — they are "in progress" (blue) because the files exist but haven't been deployed and validated on real hardware.

### 6. Verify .env.example completeness

Check every `.env.example` across all stacks and confirm:
- All required variables are present
- Placeholder values or generation instructions are provided
- No actual secrets are present

### 7. Create platform-wide docker compose validation script

Create a simple validation script at `scripts/validate-compose`:

```bash
#!/usr/bin/env bash
# Validate all compose.yml files in the homelab repo

set -euo pipefail

HOMELAB_DIR="${HOMELAB_DIR:-$HOME/homelab}"
ERRORS=0

echo "Validating all compose.yml files..."
echo ""

for compose_file in $(find "$HOMELAB_DIR" -name "compose.yml" -not -path "*/data/*" -not -path "*/.git/*"); do
    dir=$(dirname "$compose_file")
    service=$(basename "$dir")
    
    if (cd "$dir" && docker compose config > /dev/null 2>&1); then
        echo "  ✓ $service"
    else
        echo "  ✗ $service — FAILED"
        (cd "$dir" && docker compose config 2>&1 | head -5)
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "All compose files valid."
else
    echo "$ERRORS compose file(s) failed validation."
    exit 1
fi
```

Make it executable.

## Constraints
- Do NOT modify service-specific compose files unless fixing a bug found during validation
- Do NOT mark rollout tasks as complete — only "in progress"
- The `.gitignore` must protect secrets (`.env`) and data directories globally

## Acceptance Criteria
- [ ] Root `.gitignore` exists and covers `.env`, `data/`, `backups/`, `.DS_Store`
- [ ] Caddyfile has entries for all 5 HTTP services (dockge, homepage, uptime-kuma, authentik, immich)
- [ ] All HTTP-serving containers join `caddy-net`
- [ ] Homepage `services.yaml` lists all services
- [ ] All `.env.example` files are complete with no real secrets
- [ ] `scripts/validate-compose` exists and is executable
- [ ] `docs/rollout-plan.md` Phase 1 tasks are updated to in-progress
- [ ] `git add -A && git status` shows no `.env` files staged (gitignore working)
