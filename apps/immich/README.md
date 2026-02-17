# Immich — Photo & Video Management

Immich is a self-hosted Google Photos replacement for the homelab. It provides automatic mobile backup, facial recognition, object detection, album sharing, and a polished iOS/Android app. All family media is stored on-premise, encrypted in backups, and accessible locally and over Tailscale.

**Components:** `immich-server` (API + web UI), `immich-ml` (machine learning: face/object recognition), `immich-db` (PostgreSQL with pgvecto.rs extension), `immich-redis` (cache/queue).

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `ghcr.io/immich-app/immich-server` |
| Version | `v2.5.6` |
| Port (internal) | `2283` |
| Hostname | `immich.home` |
| Health endpoint | `/api/server/ping` |
| Upload data | `./data/upload` (Phase A) or `/Volumes/HomelabData/immich-library` (Phase B) |
| Database | `./data/postgres` |
| Admin UI | `http://immich.home` |
| Upstream | https://immich.app/docs |

## First-Run Setup

1. Generate `DB_PASSWORD`:
   ```bash
   openssl rand -base64 32
   # Paste into DB_PASSWORD in .env
   ```

2. Confirm `UPLOAD_LOCATION` in `.env` (defaults to `./data/upload` for Phase A):
   ```bash
   # Phase A (internal disk):
   UPLOAD_LOCATION=./data/upload
   ```

3. Start the stack:
   ```bash
   docker compose up -d
   ```

4. Wait ~30 seconds for the database to initialise, then navigate to `http://immich.home` and create your admin account.

5. Wire Authentik OIDC once the identity stack is verified (see Authentik Integration below).

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart server only
docker compose restart immich-server

# View logs
docker compose logs -f immich-server
docker compose logs -f immich-ml

# Update to new version
# ⚠ Read Immich release notes first: https://github.com/immich-app/immich/releases
# 1. Back up postgres (see Backup section)
# 2. Edit .env — set IMMICH_VERSION to new tag
# 3. Pull and restart:
docker compose pull
docker compose up -d
# Rollback: revert IMMICH_VERSION in .env, restore postgres from backup, docker compose up -d
```

## Authentik OIDC Integration

Immich supports native OIDC login. Complete this after the Authentik stack is fully set up.

**In Authentik (`http://login.home`):**

1. Go to **Applications → Providers → Create** → choose **OAuth2/OpenID Provider**.
2. Configure:
   - Name: `Immich`
   - Client type: `Confidential`
   - Redirect URI: `http://immich.home/auth/login`
   - Scopes: `openid`, `profile`, `email`
3. Note the **Client ID** and **Client Secret**.
4. Go to **Applications → Create** and bind to the provider.
5. Set access to groups `immich-admin` and `immich-user`.

**In Immich (`http://immich.home`):**

1. Go to **Administration → OAuth Settings**.
2. Enable OAuth and fill in:
   - Issuer URL: `http://login.home/application/o/immich/`
   - Client ID: (from Authentik)
   - Client Secret: (from Authentik)
   - Scope: `openid profile email`
   - Button text: `Sign in with Authentik`
3. Test login via SSO.

**Group mapping:**
- `immich-admin` → Immich admin role
- `immich-user` → standard user access

**Break-glass:** the local admin account created during first-run setup remains active. Keep its credentials in a password manager in case Authentik is unavailable.

## Storage Migration (Phase A → Phase B)

When the internal disk fills up or you want to move the library to the external SSD:

1. Stop Immich:
   ```bash
   docker compose down
   ```

2. Move the upload directory:
   ```bash
   mv data/upload /Volumes/HomelabData/immich-library
   ```

3. Update `.env`:
   ```bash
   UPLOAD_LOCATION=/Volumes/HomelabData/immich-library
   ```

4. Start Immich and verify the library is intact:
   ```bash
   docker compose up -d
   # Check http://immich.home — all photos should be visible
   ```

## Backup

Immich state is in two places: the PostgreSQL database and the upload directory.

```bash
# Back up PostgreSQL (run while stack is up)
docker exec immich-db pg_dump -U immich immich | gzip > ./immich-db-$(date +%Y%m%d).sql.gz

# Or via the platform app-backup script (backs up ./data/ directory)
scripts/app-backup immich
```

**Backup scope:**
- `./data/upload/` — all photos and videos (large, must include)
- `./data/postgres/` — database (metadata, albums, faces, users)
- `./data/model-cache/` — **exclude** — reproducible, re-downloaded automatically

**Backup schedule:** daily (RPO class: daily)

## Restore

1. Stop the stack:
   ```bash
   docker compose down
   ```

2. Clear existing data:
   ```bash
   rm -rf ./data/postgres
   ```

3. Start only the database:
   ```bash
   docker compose up -d immich-db
   ```

4. Restore the dump:
   ```bash
   gunzip -c ./immich-db-YYYYMMDD.sql.gz | docker exec -i immich-db psql -U immich immich
   ```

5. Restore upload directory from backup (Restic or tarball).

6. Start the full stack:
   ```bash
   docker compose up -d
   ```

7. Verify at `http://immich.home` — photos should be visible and thumbnails regenerating.

## Resource Notes

The `immich-ml` container runs face detection and object recognition. On the Mac mini (shared with Minecraft), this can spike CPU/RAM during bulk imports.

To disable machine learning:
```bash
# In .env, add:
IMMICH_MACHINE_LEARNING_ENABLED=false
# Then restart:
docker compose up -d
```

Features that rely on ML (face recognition, smart search, CLIP) will be unavailable, but photos remain fully accessible.

## Mobile Apps

iOS and Android apps are available at https://immich.app/docs/features/mobile-app

- **Local access:** `http://immich.home` (requires device on home network)
- **Remote access:** use the Tailscale hostname (e.g., `http://homelab-mac-mini`) — no port forwarding required

## Security Checklist (docs/security.md § 10)

| Check | Status | Notes |
|-------|--------|-------|
| Non-root container user | ✓ | Immich server runs as non-root by default |
| No privileged mode | ✓ | No `privileged` or unnecessary capabilities |
| Secrets in `.env` only | ✓ | `DB_PASSWORD` generated and stored in `.env` |
| Authentik SSO integrated | Pending | Steps documented above; configure post-deployment |
| Break-glass admin documented | ✓ | Local admin created during first-run |
| Health endpoint monitored | Pending | Add Uptime Kuma monitor for `/api/server/ping` |
| Network exposure reviewed | ✓ | No host ports published; access via Caddy only |
| Backup scope defined | ✓ | upload + postgres; model-cache excluded |
| Agent scopes defined | ✓ | Declared in `app-contract.yaml` |
| Upstream security posture | ✓ | Active project, regular releases, image signing available |

## Caddy Integration

The `immich.home` entry is already in `platform/caddy/Caddyfile`:

```
http://immich.home {
    reverse_proxy immich-server:2283 {
        header_up X-Real-IP {remote_host}
    }
}
```

No changes to Caddyfile needed. The `immich-server` container joins `caddy-net` — Caddy routes requests directly to it.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `IMMICH_VERSION` | Yes | Version tag for all Immich images. Must match across all containers. |
| `UPLOAD_LOCATION` | Yes | Host path for photo/video storage. Phase A: `./data/upload`. |
| `DB_DATABASE_NAME` | No | Database name. Default: `immich`. |
| `DB_USERNAME` | No | Database user. Default: `immich`. |
| `DB_PASSWORD` | Yes | PostgreSQL password. Generate: `openssl rand -base64 32`. |

See `.env.example` for the full reference.

## Upstream

- [Immich Documentation](https://immich.app/docs)
- [Immich GitHub](https://github.com/immich-app/immich)
- [Immich Releases](https://github.com/immich-app/immich/releases)
- [Immich Docker Compose reference](https://immich.app/docs/install/docker-compose)
