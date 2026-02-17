# Authentik OIDC Integration Guide

> How to wire a new application to Authentik SSO via OIDC/OAuth2.
> Reference implementation: Immich (`apps/immich/`)

This document captures the exact steps, failure modes, and design decisions encountered when integrating the first application (Immich) with Authentik. Follow it when adding any future application that supports OIDC.

---

## Overview

Authentik acts as the OIDC Identity Provider (IdP). Each application is an OIDC Relying Party (RP) that delegates authentication to Authentik. The result:

- Users log in once at `login.home` and are recognised in all integrated apps
- Access is controlled by Authentik group membership, not per-app user management
- Accounts in integrated apps are created automatically on first login (if the app supports auto-provisioning)

---

## Architecture

```
Browser → App (immich.home)
        → "Login with Authentik" button
        → Redirect to login.home/application/o/<slug>/authorize
        → Authentik authentication flow
        → Redirect back to app with auth code
        → App server fetches token from login.home/application/o/<slug>/token
        → App validates JWT
        → Login complete
```

The app server makes a **server-side** token request to Authentik. This is where the hostname problem below originates.

---

## Prerequisites

- Authentik stack running with a valid `AUTHENTIK_BOOTSTRAP_TOKEN` in `.env`
- Application stack running and reachable via Caddy (`<app>.home`)
- The app supports OIDC/OAuth2 natively (preferred) or via proxy auth

---

## Part 1: Authentik Side

### 1.1 Create Access Groups

Each app gets two groups: `<app>-admin` and `<app>-user`. Additional groups (`<app>-readonly`, `<app>-kids`) are optional.

**Via `scripts/setup-authentik-<app>` (preferred):** the script creates groups idempotently.

**Manual (Authentik UI):**
1. Go to `http://login.home/if/admin/` → Directory → Groups → Create
2. Name: `<app>-admin`, `is_superuser`: off
3. Repeat for `<app>-user`

### 1.2 Create OAuth2/OIDC Provider

**Key settings:**

| Setting | Value | Notes |
|---------|-------|-------|
| Name | `<App>` (e.g., `Immich`) | Used to identify the provider |
| Authorization flow | `default-provider-authorization-implicit-consent` | Pre-existing default flow |
| Authentication flow | `default-authentication-flow` | Pre-existing default flow |
| Client type | `Confidential` | Required for server-side apps |
| Redirect URIs | `http://<app>.home/auth/login` | App-specific — check app docs |
| Signing key | `authentik Self-signed Certificate` | Default self-signed key |
| Sub mode | `Hashed User ID` | Stable opaque identifier |
| Encryption certificate | **None** | See pitfall §3.1 below |
| Issuer mode | `Per provider` | Each app gets its own issuer URL |
| Include claims in ID token | Yes | Avoids extra userinfo request |

**Critical:** Set **Encryption Certificate = None** in Advanced Protocol Settings. If a certificate is set, Authentik returns a JWE-encrypted token. Most applications (including Immich) only support plain RS256-signed JWT and will fail with `JWE decryption is not configured`.

### 1.3 Create Application

1. Go to Applications → Applications → Create
2. Name: `<App>`, Slug: `<app>` (lowercase, matches the URL)
3. Provider: select the provider created above
4. Policy engine mode: `any`

### 1.4 Bind Groups to Application

Add a Policy Binding for each group:
- Policy/Group/User: select the group (`<app>-admin`, `<app>-user`)
- Enabled: yes
- Order: 0

Only members of these groups can authenticate. Users not in any bound group are denied at Authentik before reaching the app.

---

## Part 2: Application Side

### 2.1 OIDC Discovery URL

Every OIDC application requires a discovery URL (also called Issuer URL or Well-Known URL). For Authentik it follows this pattern:

```
http://login.home/application/o/<app-slug>/
```

The discovery endpoint is at:

```
http://login.home/application/o/<app-slug>/.well-known/openid-configuration
```

**Always use `login.home` in the Issuer URL**, never the internal Docker hostname (`authentik-server:9000`). See pitfall §3.2.

### 2.2 Configure the App

Typical OIDC settings to fill in:

| Field | Value |
|-------|-------|
| Issuer URL / Discovery URL | `http://login.home/application/o/<app-slug>/` |
| Client ID | Shown in Authentik provider detail (edit view) |
| Client Secret | Shown in Authentik provider detail (edit view — not the overview) |
| Scope | `openid profile email` |
| Redirect URI | Must match exactly what was set in the provider |

**Client Secret location:** In the Authentik UI, the client secret is only visible in the **edit view** of the provider (click the pencil/edit icon), not on the read-only overview page.

---

## Part 3: Pitfalls and Solutions

### 3.1 JWE Encryption — "JWE decryption is not configured"

**Symptom:** Browser completes the redirect to the app, Authentik shows a successful login, but the app shows "Failed to finish OAuth" or similar.

**Cause:** The Authentik provider has an Encryption Certificate set. Authentik encrypts the ID token as JWE. The application only supports plain RS256 JWT.

**Fix:** In the provider's Advanced Protocol Settings, set **Encryption Certificate = None**. The app will then receive a standard signed JWT.

---

### 3.2 OIDC Discovery From Inside a Container — "TypeError: fetch failed"

**Symptom:** The app shows "Error in OAuth discovery" or fails to fetch the OIDC configuration document. The error originates server-side (in the app container), not in the browser.

**Cause:** The app server makes a server-side HTTP request to the Issuer URL to fetch OIDC metadata. Custom `.home` hostnames only exist in the Mac's `/etc/hosts`. Docker containers have no knowledge of them, so DNS resolution fails inside the container.

**Wrong fix (do not do this):** Use `http://authentik-server:9000/application/o/<slug>/` as the Issuer URL. This resolves inside Docker, but Authentik generates all URLs in the discovery document based on the `Host` header of the incoming request. Using the internal hostname causes Authentik to embed `authentik-server:9000` in the `authorization_endpoint` and `token_endpoint` URLs. The browser then tries to navigate to `authentik-server:9000/...`, which fails.

**Correct fix:** Add `extra_hosts` to the app's `compose.yml` so the container resolves `.home` names through the Docker host (which runs Caddy on port 80):

```yaml
services:
  <app>-server:
    extra_hosts:
      - "login.home:host-gateway"
      - "<app>.home:host-gateway"
```

`host-gateway` is a Docker special value that resolves to the host's internal Docker bridge IP. Traffic to `login.home:80` hits Caddy, which routes to `authentik-server:9000`. Authentik sees `Host: login.home` and generates discovery URLs with `login.home` — the same URLs the browser uses.

**Verify the fix:**

```bash
docker exec <app>-server curl -s http://login.home/application/o/<slug>/.well-known/openid-configuration | python3 -m json.tool | grep issuer
# Should return: "issuer": "http://login.home/application/o/<slug>/"
```

---

### 3.3 Bootstrap Token Not Created — API Returns 403

**Symptom:** `AUTHENTIK_BOOTSTRAP_TOKEN` is set in `.env`, Authentik is restarted, but API calls with the token return 403. The token is not in the database.

**Cause:** Bootstrap tasks (including token creation) run in the **worker**, not the server. If `AUTHENTIK_BOOTSTRAP_TOKEN` is only in the server's environment, the worker never sees it.

**Fix:** Ensure `AUTHENTIK_BOOTSTRAP_TOKEN` (and `AUTHENTIK_BOOTSTRAP_PASSWORD`) are set in **both** `authentik-server` and `authentik-worker` in `compose.yml`:

```yaml
authentik-server:
  environment:
    AUTHENTIK_BOOTSTRAP_PASSWORD: ${AUTHENTIK_BOOTSTRAP_PASSWORD:-}
    AUTHENTIK_BOOTSTRAP_TOKEN: ${AUTHENTIK_BOOTSTRAP_TOKEN:-}

authentik-worker:
  environment:
    AUTHENTIK_BOOTSTRAP_PASSWORD: ${AUTHENTIK_BOOTSTRAP_PASSWORD:-}
    AUTHENTIK_BOOTSTRAP_TOKEN: ${AUTHENTIK_BOOTSTRAP_TOKEN:-}
```

**Second cause:** `AUTHENTIK_BOOTSTRAP_TOKEN` only auto-creates the token on **first boot** (empty database). On an already-running Authentik instance, bootstrap has already completed and will not run again. Create the token manually via the Django shell:

```bash
docker exec authentik-worker python3 manage.py shell -c "
from authentik.core.models import Token, TokenIntents, User
import os
ak_user = User.objects.get(username='akadmin')
token_val = os.environ['AUTHENTIK_BOOTSTRAP_TOKEN']
t, created = Token.objects.get_or_create(
    identifier='bootstrap-api-token',
    defaults={
        'user': ak_user,
        'intent': TokenIntents.INTENT_API,
        'key': token_val,
        'expiring': False,
    }
)
print('Created' if created else 'Already exists')
"
```

Or create a token manually through the Authentik UI: Directory → Tokens → Create → Intent: API Token.

---

### 3.4 Container Lost `caddy-net` After Manual Restart

**Symptom:** A service was working, then its hostname returns 502. Caddy logs show no upstream connection.

**Cause:** Running `docker compose up -d` on a single service (or restarting a container directly) can cause it to lose externally-connected networks like `caddy-net` if the stack was originally started in the wrong order or partially.

**Immediate fix:**

```bash
docker network connect caddy-net <container-name>
```

**Permanent fix:** Always start stacks via `scripts/platform-up`, which starts Caddy first (creating `caddy-net`) then all app stacks in order.

---

## Part 4: Scripted Setup Pattern

For each new application, create a `scripts/setup-authentik-<app>` script following the pattern established in `scripts/setup-authentik-immich`. Key requirements:

1. **Read token from `.env`** — support `AUTHENTIK_TOKEN` env override for flexibility
2. **Pass `Host: login.home` header** — all API calls must include this; Caddy routes via virtual host, not IP
3. **Use temp files for curl responses** — `head -n -1` is not portable on macOS; write body to a temp file, capture http_code via `-w "%{http_code}"`
4. **Avoid nested shell quoting** — do not use `"$(python3 -c "...")"`. Use a heredoc instead:
   ```bash
   BODY=$(python3 - <<PYEOF
   import json
   print(json.dumps({"key": "value"}))
   PYEOF
   )
   ak_api POST "some/endpoint/" "$BODY"
   ```
5. **Make it idempotent** — check if each resource exists before creating; print warnings not errors on duplicates
6. **Print credentials at the end** — Client ID and Secret are generated by Authentik; the script must surface them

---

## Part 5: Checklist for a New Application

- [ ] App's `compose.yml` includes `extra_hosts` with `login.home:host-gateway` (and `<app>.home:host-gateway` if the app makes self-referential requests)
- [ ] App joins `caddy-net` (only the frontend container, not DB/Redis sidecars)
- [ ] Authentik groups created: `<app>-admin`, `<app>-user`
- [ ] Authentik OAuth2/OIDC provider created with **Encryption Certificate = None**
- [ ] Authentik Application created and groups bound
- [ ] Issuer URL in app config uses `login.home` (not `authentik-server:9000`)
- [ ] Auto-register / auto-provision enabled in app if supported
- [ ] Redirect URI in Authentik provider matches exactly what the app expects
- [ ] Script `scripts/setup-authentik-<app>` created and tested (idempotent)
- [ ] Groups and role mapping added to `docs/access-matrix.md`
- [ ] `app-contract.yaml` updated with `auth.mode: oidc` and group names

---

## Reference

| Resource | Location |
|----------|----------|
| Authentik admin UI | `http://login.home/if/admin/` |
| OIDC discovery (Immich) | `http://login.home/application/o/immich/.well-known/openid-configuration` |
| Setup script | `scripts/setup-authentik-immich` |
| App spec | `docs/app-spec.md` §3 |
| Access matrix | `docs/access-matrix.md` |
| Bootstrap guide | `docs/bootstrap.md` §8 |
