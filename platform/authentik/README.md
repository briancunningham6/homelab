# Authentik — Identity & SSO

Authentik is the identity provider for the homelab platform. It provides single sign-on (SSO), user and group management, OIDC/OAuth2/SAML/LDAP protocols, and fine-grained RBAC. Every service with a web UI integrates with Authentik — it is the most critical platform component after Caddy.

**Components:** `authentik-server` (UI + API), `authentik-worker` (background tasks), `authentik-db` (PostgreSQL), `authentik-redis` (cache/queue).

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `ghcr.io/goauthentik/server` |
| Version | `2024.12.3` |
| Ports (internal) | `9000` (HTTP), `9443` (HTTPS) |
| Hostname | `login.home` |
| Health endpoint | `http://authentik-server:9000/-/health/live/` |
| Admin UI | `http://login.home/if/admin/` |
| Data | `./data/postgres`, `./data/redis` |
| Upstream | https://goauthentik.io/docs |

## First-Run Bootstrap

**Do this before starting for the first time:**

1. Generate the secret key:
   ```bash
   openssl rand -base64 60
   # Paste output into AUTHENTIK_SECRET_KEY in .env
   ```

2. Generate the PostgreSQL password:
   ```bash
   openssl rand -base64 32
   # Paste into POSTGRES_PASSWORD and AUTHENTIK_POSTGRESQL__PASSWORD in .env
   ```

3. Set a bootstrap password for the initial `akadmin` account:
   ```bash
   # In .env, set AUTHENTIK_BOOTSTRAP_PASSWORD to a strong password
   ```

4. Start the stack:
   ```bash
   docker compose up -d
   ```

5. Wait ~60 seconds for database migrations to complete:
   ```bash
   docker compose logs -f authentik-server
   # Wait until you see "Starting server" or similar
   ```

6. Complete setup via the web UI:
   - Navigate to `http://login.home/if/flow/initial-setup/`
   - Log in with username `akadmin` and the bootstrap password you set

7. Follow `docs/onboarding.md` for:
   - Branding customisation
   - Group creation (`homelab-admin`, `parents`, `kids`)
   - Creating your personal admin account
   - Disabling or limiting the `akadmin` account

8. **After completing setup**, comment out `AUTHENTIK_BOOTSTRAP_PASSWORD` in `.env` and reload:
   ```bash
   docker compose up -d
   ```

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart (server only, zero-downtime for workers)
docker compose restart authentik-server

# View server logs
docker compose logs -f authentik-server

# View worker logs
docker compose logs -f authentik-worker

# Update to new version
# ⚠ See UPDATE WARNING below before proceeding
# 1. Read the Authentik release notes for the target version
# 2. Back up PostgreSQL (see Backup section)
# 3. Edit compose.yml — update BOTH server and worker image tags to the same version
# 4. docker compose pull
# 5. docker compose up -d
# Rollback: revert compose.yml and restore from PostgreSQL backup
```

## Update Warning

Authentik is a **critical dependency** — all SSO-protected services lose authentication if it fails.

Before updating:
- Read the [Authentik release notes](https://goauthentik.io/docs/releases) for breaking changes
- Take a full PostgreSQL backup (see Backup section)
- Never update Authentik and an application in the same maintenance session
- Never run the server and worker on different versions — they must match
- After update, verify login at `http://login.home` before declaring success

## Caddy Integration

The `login.home` entry in the Caddyfile (already configured in `platform/caddy/Caddyfile`):

```
login.home {
    reverse_proxy authentik-server:9000
    header_up X-Real-IP {remote_host}
    header_up X-Forwarded-For {remote_host}
    header_up X-Forwarded-Proto {scheme}
}
```

**Forward auth snippet** — add this to any app that needs Authentik SSO protection:

```
# Authentik forward auth (add to app Caddyfile blocks):
# (authentik) {
#     forward_auth authentik-server:9000 {
#         uri /outpost.goauthentik.io/auth/caddy
#         copy_headers X-Authentik-Username X-Authentik-Groups X-Authentik-Email X-Authentik-Name X-Authentik-Uid
#         trusted_proxies private_ranges
#     }
# }
#
# Then in each protected app block, add: import authentik
```

## Networking

- `authentik-internal` is an **isolated internal bridge network** — only Authentik components can communicate on it. PostgreSQL and Redis are never exposed outside this network.
- `caddy-net` allows Caddy to reach `authentik-server` for proxying and forward auth.
- The `authentik-worker` does **not** join `caddy-net` — it only needs the internal network.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AUTHENTIK_SECRET_KEY` | Yes | Cryptographic secret. Generate: `openssl rand -base64 60`. Never change after first run. |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password. Generate: `openssl rand -base64 32`. |
| `AUTHENTIK_POSTGRESQL__PASSWORD` | Yes | Must match `POSTGRES_PASSWORD`. |
| `AUTHENTIK_BOOTSTRAP_PASSWORD` | First run | Sets `akadmin` password. Comment out after setup. |
| `POSTGRES_DB` | No | Database name. Default: `authentik`. |
| `POSTGRES_USER` | No | Database user. Default: `authentik`. |

See `.env.example` for the full list including optional email settings.

## Backup

Authentik state lives in PostgreSQL. Back up before updates and on the daily backup schedule.

```bash
# Dump PostgreSQL (run while stack is up)
docker exec authentik-db pg_dump -U authentik authentik | gzip > ./authentik-$(date +%Y%m%d).sql.gz

# Or via the app-backup script (backs up ./data/ directory)
scripts/app-backup authentik
```

**Include in backup scope:**
- `./data/postgres/` — full database state
- `./data/redis/` — queue and cache (less critical, can be lost)

## Restore

1. Stop the stack:
   ```bash
   docker compose down
   ```
2. Clear the existing data directory:
   ```bash
   rm -rf ./data/postgres ./data/redis
   ```
3. Start only the database:
   ```bash
   docker compose up -d authentik-db
   ```
4. Restore the dump:
   ```bash
   gunzip -c ./authentik-YYYYMMDD.sql.gz | docker exec -i authentik-db psql -U authentik authentik
   ```
5. Start the full stack:
   ```bash
   docker compose up -d
   ```
6. Verify login at `http://login.home`

## Upstream

- [Authentik Documentation](https://goauthentik.io/docs)
- [Authentik GitHub](https://github.com/goauthentik/authentik)
- [Authentik Releases](https://github.com/goauthentik/authentik/releases)
- [Authentik Docker Compose reference](https://goauthentik.io/docs/installation/docker-compose)
