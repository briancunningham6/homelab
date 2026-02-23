# Task 09: Immich Photo Management

## Context
Read `CLAUDE.md` for project conventions. Read `docs/app-spec.md` for the application specification standard. Read `docs/app-ideas.md` — Immich entry for platform-specific notes. Read `docs/security.md` § 10 for the new app security checklist.

**This task depends on Task 01 (Caddy) and Task 08 (Authentik) being complete.**

## Objective
Create the complete Immich stack in `apps/immich/` as the first production application, fully conforming to the app spec.

## Output Files

```
apps/immich/
├── compose.yml
├── .env
├── .env.example
├── app-contract.yaml
├── data/                   # Created at runtime (gitignored)
└── README.md
```

## Requirements

### compose.yml
Immich is a multi-container application. Reference the official Compose file but adapt to platform conventions.

**Services:**

1. **immich-server**
   - Image: `ghcr.io/immich-app/immich-server` with pinned version tag (check https://github.com/immich-app/immich/releases for latest stable)
   - Expose port 2283 internally
   - Environment from `.env`
   - Depends on: `immich-db`, `immich-redis`
   - Mount `${UPLOAD_LOCATION}` to `/usr/src/app/upload` (photo/video storage)
   - `restart: unless-stopped`
   - Container name: `immich-server`

2. **immich-machine-learning**
   - Image: `ghcr.io/immich-app/immich-machine-learning` with same version tag
   - Mount `./data/model-cache` to `/cache`
   - `restart: unless-stopped`
   - Container name: `immich-ml`
   - Note in README: this can be resource-intensive on Mac mini — may need memory limits or disabling

3. **immich-db**
   - Image: `docker.io/tensorchord/pgvecto-rs:pg16-v0.2.0` (Immich requires pgvecto.rs extension)
   - Note: check Immich docs for the exact required Postgres image — it's NOT standard postgres
   - Environment: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_INITDB_ARGS=--data-checksums`
   - Mount `./data/postgres` to `/var/lib/postgresql/data`
   - `restart: unless-stopped`
   - Container name: `immich-db`
   - Health check: `pg_isready -U ${DB_USERNAME} -d ${DB_DATABASE_NAME}`

4. **immich-redis**
   - Image: `docker.io/library/redis:7-alpine`
   - `restart: unless-stopped`
   - Container name: `immich-redis`
   - Health check: `redis-cli ping`

**Networks:**
- Internal network for Immich components
- Join `caddy-net` external network (so Caddy reaches immich-server)

### .env.example
```
# Immich Configuration
# Check https://immich.app/docs/install/environment-variables for full reference

# Upload location — where photos/videos are stored
# Phase A: internal disk
UPLOAD_LOCATION=./data/upload
# Phase B: external SSD (uncomment when ready)
# UPLOAD_LOCATION=/Volumes/HomelabData/immich-library

# Database
DB_DATABASE_NAME=immich
DB_USERNAME=immich
DB_PASSWORD=

# Immich version — keep all services on the same version
IMMICH_VERSION=v1.130.3

# Machine learning
# Set to false to disable ML (saves resources on Mac mini)
# IMMICH_MACHINE_LEARNING_ENABLED=true

# Optional: Authentik OIDC (configure after Authentik is running)
# See README for Authentik integration steps
```

### app-contract.yaml
```yaml
name: immich
version: 1.0.0

auth:
  mode: oidc
  provider: authentik
  groups:
    admin: immich-admin
    user: immich-user

network:
  hostname: immich.home
  internalPort: 2283

data:
  paths:
    - ./data/upload
    - ./data/postgres

backup:
  includes:
    - data/upload
    - data/postgres
  rpoClass: daily
  restoreTest: documented

agentScopes:
  user: [read, write]
  child: [read]
  admin: [read, write, delete, configure]

health:
  endpoint: /api/server/ping
```

### README.md
Follow the template from CLAUDE.md. Include:
- What Immich does (self-hosted photo/video management, Google Photos replacement)
- Quick reference: image, version, internal port 2283, hostname `immich.home`, health endpoint `/api/server/ping`
- Commands: start, stop, restart, update with rollback
- **First-run setup:**
  1. Generate `DB_PASSWORD` with `openssl rand -base64 32`
  2. Set `UPLOAD_LOCATION` (Phase A: `./data/upload`)
  3. Start stack
  4. Navigate to `http://immich.home` and create admin account
  5. Configure Authentik OIDC once identity stack is ready
- **Authentik OIDC integration steps:**
  1. In Authentik: create OAuth2/OpenID Provider for Immich
  2. Set client ID and secret
  3. Redirect URI: `http://immich.home/auth/login`
  4. Create Application in Authentik, bind to provider
  5. Map `immich-admin` and `immich-user` groups
  6. In Immich: Administration → OAuth Settings → configure OIDC
  7. Test login with SSO
- **Storage migration** (Phase A → Phase B):
  1. Stop Immich
  2. Move `data/upload/` to `/Volumes/HomelabData/immich-library/`
  3. Update `UPLOAD_LOCATION` in `.env`
  4. Start Immich and verify
- **Backup:** PostgreSQL (`pg_dump`) + upload directory. Document both.
- **Resource notes:** ML container may use significant CPU/RAM. Disable with `IMMICH_MACHINE_LEARNING_ENABLED=false` if Mac mini is under pressure.
- **Mobile apps:** iOS and Android apps available — configure server URL to Tailscale hostname for remote access.
- Upstream: https://immich.app/docs

## Constraints
- Immich requires a specific Postgres image with pgvecto.rs — do NOT use standard postgres
- All Immich containers must use the same version tag
- Upload location must be configurable via `.env` (for Phase A → B storage migration)
- Immich's PostgreSQL and Redis are Immich-specific — do NOT share with Authentik's
- Security checklist from `docs/security.md` § 10 must be addressed in README

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] All four services defined (server, ML, postgres, redis)
- [ ] Health checks on postgres and redis containers
- [ ] `.env.example` has all required variables with generation instructions
- [ ] `app-contract.yaml` follows the format from app-spec.md
- [ ] Upload location is configurable via environment variable
- [ ] README includes Authentik OIDC integration steps
- [ ] README includes storage migration procedure
- [ ] README includes backup and restore procedures
- [ ] Joins `caddy-net` for external access
