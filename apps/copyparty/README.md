# Copyparty

Copyparty is a self-hosted file server with resumable uploads, media browsing, per-user private storage, and a shared family folder. It runs as a single Docker container behind Caddy, authenticated via Authentik using reverse-proxy header injection — users log in with their existing homelab Authentik account and are taken directly to their personal file space.

---

## Quick Reference

| | |
|-|-|
| Image | `copyparty/ac:1.20.7` |
| Internal port | `3923` |
| Hostname | `http://copyparty.home` |
| Health check | `GET /` (200 = healthy) |
| Config file | `config/copyparty.conf` |
| File storage | `./data/library/` |
| Index/cache | `./data/db/` |

---

## Commands

```bash
# Start
docker compose -f apps/copyparty/compose.yml up -d

# Stop
docker compose -f apps/copyparty/compose.yml down

# Restart
docker compose -f apps/copyparty/compose.yml restart

# View logs
docker logs -f copyparty

# Update (with rollback)
# 1. Read upstream release notes at https://github.com/9001/copyparty/releases
# 2. Edit compose.yml — update the image tag
docker compose -f apps/copyparty/compose.yml pull
docker compose -f apps/copyparty/compose.yml up -d
# Rollback: revert image tag in compose.yml, then up -d again
```

---

## First-Run Setup

### 1. Generate the shared secret

This secret is sent by Caddy as a header to prove the Authentik auth headers are legitimate — it prevents clients from spoofing their username.

```bash
# Generate secret
openssl rand -hex 32

# Add to both:
#   apps/copyparty/.env      → CP_SECRET=<generated>
#   platform/caddy/.env      → CP_SECRET=<same value>
```

### 2. Create the Authentik proxy provider

```bash
HOMELAB_DIR=~/dev/homelab scripts/setup-authentik-copyparty
```

This creates the Authentik proxy provider, application, groups, and group bindings. No Client ID/Secret is produced — auth happens at the Caddy layer, not via OIDC.

### 3. Reload Caddy

The Caddyfile already includes the `copyparty.home` block with forward-auth. After setting `CP_SECRET` in Caddy's env:

```bash
docker compose -f platform/caddy/compose.yml up -d
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### 4. Start Copyparty

```bash
docker compose -f apps/copyparty/compose.yml up -d
```

### 5. Verify

```bash
# Should redirect to Authentik login (302)
curl -s -o /dev/null -w "%{http_code}" http://copyparty.home/

# After logging in via browser, you should land on the Copyparty UI
# Your personal folder appears at /u/<your-username>/
```

---

## Authentik Integration

### How it works

Copyparty uses **reverse-proxy header authentication** — not OIDC. The flow is:

```
Browser → Caddy → Authentik (forward_auth check)
                       ↓ authenticated
              Caddy injects headers:
                X-authentik-username: alice
                X-authentik-groups: parents,copyparty-user
                X-CP-Secret: <shared secret>
                       ↓
                  Copyparty reads headers,
                  grants access to /u/alice/
```

This is different from Immich (which uses OIDC/OAuth2). Copyparty doesn't redirect to Authentik itself — Caddy handles the auth gate entirely.

### Groups

| Authentik Group | Access |
|----------------|--------|
| `copyparty-admin` | Full admin — all volumes, config management |
| `copyparty-user` | Standard access — own folder + shared + media |
| `parents` | Write access to `/shared/` in addition to standard |

**To grant a user access:**
1. Go to `http://login.home/if/admin/` → Directory → Groups
2. Add them to `copyparty-user` (or `copyparty-admin`)
3. Optionally add to `parents` for shared folder write access

**To remove access:** Remove from all `copyparty-*` groups. They will be denied at the Authentik gate on next request.

---

## Volume Structure

| Path | Contents | Permissions |
|------|----------|------------|
| `/` | Root listing | Read: all authenticated users |
| `/shared/` | Family shared folder | Read: all; Write: `parents` group + admins |
| `/u/<username>/` | Per-user home | Read+Write+Delete: owner; Read: admins |
| `/u/<username>/priv/` | Private area | Owner + admins only |
| `/media/` | Read-only media library | Read: all authenticated users |

Per-user folders (`/u/<username>/`) are created automatically on first login — no config changes required. Files go in `./data/library/users/<username>/` on disk.

---

## User Provisioning Limitation

Copyparty does not auto-create accounts (unlike Immich). Here is what happens automatically vs what requires manual action:

**Automatic (no action needed):**
- Per-user folder `/u/<username>/` is created on first login via `${u}` substitution
- Group-based permissions (e.g., `parents` write access to `/shared/`) work immediately

**Requires manual config edit (`config/copyparty.conf`):**
- Granting one user access to another user's folder
- Changing a specific user's permissions beyond the group defaults
- Custom per-user volume definitions

**Removing a user:** Remove them from all `copyparty-*` groups in Authentik. Their folder on disk is not deleted — files are preserved.

### Future automation target

A script to sync Authentik group memberships with `copyparty.conf` overrides would remove the manual step for custom permissions. Track in `tasks/`.

---

## Backup & Restore

Data to back up: `apps/copyparty/data/library/` — all user files.

```bash
scripts/app-backup copyparty
```

The index and thumbnail cache (`data/db/`) is excluded — it is regeneratable and can be large.

Restore:

```bash
scripts/app-restore copyparty
```

RPO: Daily. After restore, Copyparty will rebuild its index on startup (may take a few minutes depending on library size).

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CP_SECRET` | Yes | Shared secret header value. Must match `CP_SECRET` in `platform/caddy/.env`. Generate with `openssl rand -hex 32`. |

---

## Upstream Links

- [Copyparty GitHub](https://github.com/9001/copyparty)
- [Copyparty Releases](https://github.com/9001/copyparty/releases)
- [Copyparty IdP Auth Docs](https://github.com/9001/copyparty/blob/hovudstraum/docs/idp.md)
- [Authentik Proxy Provider Docs](https://docs.goauthentik.io/add-secure-apps/providers/proxy/)
