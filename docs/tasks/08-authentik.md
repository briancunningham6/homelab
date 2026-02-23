# Task 08: Authentik Identity Stack

## Context
Read `CLAUDE.md` for project conventions. Read `docs/adrs/002-authentik-identity.md` for the technology decision. Read `docs/onboarding.md` for the admin bootstrap procedure. Read `docs/security.md` § 3 for authentication and authorisation requirements. Read `DESIGN.md` § 6 for the identity and access management model.

**This task depends on Task 01 (Caddy) being complete** — Authentik needs a Caddyfile entry for `login.home`.

## Objective
Create the complete Authentik stack in `platform/authentik/`.

## Output Files

```
platform/authentik/
├── compose.yml
├── .env
├── .env.example
├── data/                   # Created at runtime (gitignored)
└── README.md
```

## Requirements

### compose.yml
Authentik requires three containers: the server, the worker, and supporting services (PostgreSQL + Redis).

**Services:**

1. **authentik-server**
   - Image: `ghcr.io/goauthentik/server` with pinned version tag (check https://github.com/goauthentik/authentik/releases for latest stable — use LTS if available)
   - Command: `server`
   - Expose port 9000 (HTTP) and 9443 (HTTPS) internally
   - Environment from `.env`
   - Depends on: `authentik-db`, `authentik-redis`
   - `restart: unless-stopped`
   - Container name: `authentik-server`

2. **authentik-worker**
   - Same image and version as server
   - Command: `worker`
   - Environment from `.env`
   - Depends on: `authentik-db`, `authentik-redis`
   - `restart: unless-stopped`
   - Container name: `authentik-worker`

3. **authentik-db**
   - Image: `docker.io/library/postgres:16-alpine` (pinned minor version)
   - Environment: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` from `.env`
   - Mount `./data/postgres` to `/var/lib/postgresql/data`
   - `restart: unless-stopped`
   - Container name: `authentik-db`
   - Health check: `pg_isready -U ${POSTGRES_USER}`

4. **authentik-redis**
   - Image: `docker.io/library/redis:7-alpine` (pinned minor version)
   - Command: `--save 60 1 --loglevel warning`
   - Mount `./data/redis` to `/data`
   - `restart: unless-stopped`
   - Container name: `authentik-redis`
   - Health check: `redis-cli ping`

**Networks:**
- Internal network for Authentik components (server ↔ worker ↔ db ↔ redis)
- Join `caddy-net` external network (so Caddy can reach authentik-server)

**Volumes:**
- Use bind mounts to `./data/postgres` and `./data/redis` for persistence

### .env.example
```
# Authentik Configuration
# Generate a secret key: openssl rand -base64 60
AUTHENTIK_SECRET_KEY=

# PostgreSQL
POSTGRES_DB=authentik
POSTGRES_USER=authentik
POSTGRES_PASSWORD=

# Authentik database connection
AUTHENTIK_POSTGRESQL__HOST=authentik-db
AUTHENTIK_POSTGRESQL__PORT=5432
AUTHENTIK_POSTGRESQL__NAME=authentik
AUTHENTIK_POSTGRESQL__USER=authentik
AUTHENTIK_POSTGRESQL__PASSWORD=

# Redis
AUTHENTIK_REDIS__HOST=authentik-redis
AUTHENTIK_REDIS__PORT=6379

# Bootstrap password for initial akadmin account
# Set this on FIRST RUN ONLY, then remove or comment out
AUTHENTIK_BOOTSTRAP_PASSWORD=

# Optional: email configuration for notifications
# AUTHENTIK_EMAIL__HOST=
# AUTHENTIK_EMAIL__PORT=587
# AUTHENTIK_EMAIL__USERNAME=
# AUTHENTIK_EMAIL__PASSWORD=
# AUTHENTIK_EMAIL__USE_TLS=true
# AUTHENTIK_EMAIL__FROM=homelab@example.com
```

### README.md
Follow the template from CLAUDE.md. Include:
- What Authentik does (SSO, users, groups, OIDC/SAML/LDAP, RBAC)
- Quick reference: image, version, ports 9000/9443, hostname `login.home`, health endpoint `/-/health/live/`
- **First-run bootstrap procedure** (reference `docs/onboarding.md` but summarise key steps):
  1. Generate `AUTHENTIK_SECRET_KEY` with `openssl rand -base64 60`
  2. Set `AUTHENTIK_BOOTSTRAP_PASSWORD` for initial `akadmin` account
  3. Set `POSTGRES_PASSWORD` (use `openssl rand -base64 32`)
  4. Copy `POSTGRES_PASSWORD` to `AUTHENTIK_POSTGRESQL__PASSWORD`
  5. Start the stack
  6. Navigate to `http://login.home/if/flow/initial-setup/`
  7. Log in with `akadmin` / bootstrap password
  8. Follow onboarding.md for branding, group creation, personal admin account
  9. Comment out `AUTHENTIK_BOOTSTRAP_PASSWORD` from `.env`
- Commands: start, stop, restart, update with rollback
- **Update warning:** Authentik is a critical service. Read release notes carefully. Back up PostgreSQL before updating. Never update Authentik and an application in the same session.
- Backup scope: PostgreSQL database (use `pg_dump`), media uploads, `./data/` directory
- Restore procedure: restore PostgreSQL, start stack, verify
- Upstream: https://goauthentik.io/docs

### Caddy integration note
The README should include the Caddyfile snippet needed for Authentik:
```
login.home {
    reverse_proxy authentik-server:9000
}
```

And the forward-auth snippet that other apps will use:
```
# Add to any app that needs Authentik forward auth:
# (authentik) {
#     forward_auth authentik-server:9000 {
#         uri /outpost.goauthentik.io/auth/caddy
#         copy_headers X-Authentik-Username X-Authentik-Groups X-Authentik-Email X-Authentik-Name X-Authentik-Uid
#         trusted_proxies private_ranges
#     }
# }
```

## Constraints
- Authentik is the **most critical** platform service — treat it accordingly
- The `AUTHENTIK_SECRET_KEY` must never be in git
- `POSTGRES_PASSWORD` and `AUTHENTIK_POSTGRESQL__PASSWORD` must match
- PostgreSQL and Redis are Authentik-specific — do NOT share them with other services
- Pin Authentik to a specific version, not `latest`

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] All four services defined (server, worker, postgres, redis)
- [ ] Health checks on postgres and redis
- [ ] `.env.example` has all required variables with generation instructions
- [ ] Internal network isolates Authentik components
- [ ] Joins `caddy-net` for external access
- [ ] README includes first-run bootstrap summary
- [ ] README includes Caddy forward-auth snippet for future app integration
- [ ] README includes backup/restore procedures for PostgreSQL
