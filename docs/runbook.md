# Runbook — Operational Change Log

> Record of all operational changes, updates, and incidents | Parent: [DESIGN.md](../DESIGN.md)

## How to Use

Log every significant operational event: deployments, updates, configuration changes, incidents, maintenance.

### Entry Template

```
## YYYY-MM-DD — [Summary]

**Type:** deployment | update | configuration | incident | maintenance | teardown
**Operator:** [name]
**Services affected:** [list]

### What changed
[Description]

### Steps taken
1. ...

### Result
[Success / partial / rolled back]

### Follow-up
[Any remaining work or observations]
```

---

## Log

## 2026-02-20 — Initial Mac mini bring-up (experimental)

**Type:** deployment  
**Operator:** OpenClaw + Brian  
**Services affected:** tailscale, caddy, authentik, uptime-kuma, homepage, dockge, copyparty, immich

### What changed
Brought the homelab stack up on the Mac mini from `/Users/<username>/dev/homelab` and verified that Immich responds through Caddy.

### Steps taken
1. Ran platform startup using repo path override:
   - `HOMELAB_DIR=/Users/<username>/dev/homelab ./scripts/platform-up`
2. Fixed Dockge stack path config:
   - `platform/dockge/.env` updated from `/Users/<username>/homelab` → `/Users/<username>/dev/homelab`
3. Started Dockge directly:
   - `HOMELAB_DIR=/Users/<username>/dev/homelab ./scripts/app-up dockge`
4. Started Immich directly:
   - `HOMELAB_DIR=/Users/<username>/dev/homelab ./scripts/app-up immich`
5. Added quick LAN access host for experiment to Caddyfile:
   - `http://immich.home, http://<LAN_IP>` → `immich-server:2283`
6. Reloaded Caddy and validated Immich ping:
   - `curl http://<LAN_IP>/api/server/ping` returned `{"res":"pong"}`

### Result
Core platform and app stacks running; Immich reachable over LAN via Caddy at:
- `http://<LAN_IP>`
- `http://immich.home` (when hostname resolves)

### Follow-up
- `scripts/dr-verify` shows a false-negative for Immich due to HTTP parsing in the script; endpoint itself is healthy.
- Configure Authentik OIDC for Immich login flow as next step.
- Optional cleanup: run `caddy fmt --overwrite platform/caddy/Caddyfile`.

## 2026-02-20 — Authentik→Immich OIDC wiring (partial automation fixed)

**Type:** configuration  
**Operator:** OpenClaw + Brian  
**Services affected:** authentik, immich

### What changed
Configured Authentik side of Immich OIDC and fixed setup script compatibility with Authentik 2024.12 API.

### Steps taken
1. Ran `scripts/setup-authentik-immich` and identified API schema mismatch:
   - required `invalidation_flow`
   - `redirect_uris` now expects list of objects, not string
2. Created/verified Authentik objects via API:
   - groups: `immich-admin`, `immich-user`
   - OAuth provider: `Immich`
   - application slug: `immich`
   - policy bindings from groups to app
3. Added user `brian` to `immich-admin` and `immich-user` groups.
4. Patched `scripts/setup-authentik-immich` for new API schema.

### Result
Authentik side is ready. Immich OAuth settings still need to be enabled in Immich admin UI using generated client credentials.

### Follow-up
- In Immich admin settings, enable OAuth and set Issuer/Client ID/Secret.
- Test login via "Login with Authentik" and confirm first SSO user provisioning.

## 2026-02-20 — Immich migration to shared PostgreSQL

**Type:** migration  
**Operator:** OpenClaw + Brian  
**Services affected:** postgres (shared), immich

### What changed
Migrated Immich from dedicated `immich-db` container to shared `platform/postgres` database service.

### Steps taken
1. Pulled latest `main` (commit `dbb7f9e`) with new shared-postgres scripts.
2. Ran `scripts/setup-shared-postgres` successfully.
3. Ran `scripts/migrate-immich-to-shared-postgres`:
   - exported old DB to `/tmp/immich-migration-20260220-140444.sql`
   - imported into shared PostgreSQL
   - rewrote `apps/immich/compose.yml` (backup kept)
   - removed old `immich-db` container
4. Post-migration fix: Immich initially failed due DB role/schema permissions and extension ownership assumptions.
5. Applied DB fix on shared postgres:
   - reset `immich` role password to match `apps/immich/.env`
   - ensured extensions and grants: `vectors`, `cube`, `earthdistance`
   - granted `USAGE,CREATE` on `vectors` and `public` schemas to `immich`
6. Restarted `immich-server` and re-verified health endpoint.

### Result
Immich is running against shared PostgreSQL and healthy:
- `curl -H 'Host: immich.home' http://127.0.0.1/api/server/ping` → `{"res":"pong"}`

### Follow-up
- Improve migration script to include post-import grants/extensions and role password sync.
- Validate login and core photo workflows from web + iOS clients.

## 2026-02-20 — Backrest deployment for remote backup management

**Type:** deployment/config  
**Operator:** OpenClaw + Brian  
**Services affected:** backrest, caddy, homepage, authentik

### What changed
Pulled latest `main` with Backrest app and backup platform scripts, launched Backrest, and wired access.

### Steps taken
1. Pulled latest repo (commit `a3ffb26`) with `apps/backrest`, backup scripts, Caddy + Homepage updates.
2. Started Backrest: `scripts/app-up backrest`.
3. Reloaded Caddy and restarted Homepage to ensure routes/links were active.
4. Added `brian` user to Authentik `homelab-admin` group.
5. Found Authentik forward-auth endpoint `/outpost.goauthentik.io/auth/caddy` returning 404 (outpost not configured yet).
6. Applied temporary experimental unblock for `backup.home` by bypassing forward-auth in Caddy, relying on Backrest’s own internal admin login.

### Result
- Backrest container is running and healthy.
- `http://backup.home` returns HTTP 200 and is reachable.
- Homepage config includes Backrest link (`http://backup.home`).
- `brian` now has `homelab-admin` group membership in Authentik.

### Follow-up
- Configure Authentik proxy outpost and re-enable forward-auth for `backup.home`.
- Create Backrest initial admin account as `brian` in first-run UI.

## 2026-02-20 — Re-enabled strict Authentik forward-auth for Backrest

**Type:** security hardening  
**Operator:** OpenClaw + Brian  
**Services affected:** authentik, caddy, backrest

### What changed
Configured Authentik proxy provider/outpost wiring correctly for `backup.home` and re-enabled strict `forward_auth` in Caddy.

### Steps taken
1. Created/verified Authentik proxy provider + app for Backrest (`external_host=http://backup.home`).
2. Ensured `homelab-admin` group is bound to Backrest application.
3. Attached provider to `authentik Embedded Outpost`.
4. Restored Caddy `forward_auth` block for `backup.home`.
5. Reloaded Caddy and validated auth flow through route.

### Validation
`curl -I -H 'Host: backup.home' http://127.0.0.1/` returns **302** redirect to Authentik authorization endpoint (expected behavior for unauthenticated client).

### Notes
- Direct requests to `/outpost.goauthentik.io/auth/caddy` without forward-auth headers can return configuration errors; validate via Caddy route instead.

## 2026-02-20 — Backup target configured on Tailscale Pi (`<backup-user>@<backup-host>`)

**Type:** backup setup  
**Operator:** OpenClaw + Brian  
**Services affected:** backup repository, backrest prerequisites

### What changed
Configured Raspberry Pi (`<backup-user>@<backup-host>`) as Restic backup target over Tailscale and initialized repository.

### Steps taken
1. Ran setup script: `HOMELAB_DIR=/Users/<username>/dev/homelab ./scripts/setup-backup-pi <backup-user>@<backup-host>`
2. Accepted proof-of-concept local disk path on Pi (no external drive detected):
   - `/home/<backup-user>/homelab-backups`
3. Installed Restic on Pi (Debian package).
4. Generated SSH key on Mac mini and copied to Pi for key-based auth.
5. Initialized Restic repository over SFTP:
   - `sftp:<backup-user>@<backup-host>:/home/<backup-user>/homelab-backups`
6. Saved backup config to:
   - `platform/backup/.env`
7. Ran and verified test backup (snapshot created successfully).

### Result
- Pi is now reachable as an offsite-style backup target over Tailscale.
- Repository initialized and usable by `backup-all` / Backrest.

### Follow-up
- In Backrest UI (`backup.home`), add repository using:
  - URI: `sftp:<backup-user>@<backup-host>:/home/<backup-user>/homelab-backups`
  - Password: from `platform/backup/.env` (`RESTIC_PASSWORD`)
- For production, migrate backup path to external drive on Pi.

## 2026-02-20 — Scheduled daily backup set to 00:00 (launchd)

**Type:** automation  
**Operator:** OpenClaw + Brian  
**Services affected:** backup scheduling

### What changed
Configured `com.homelab.backup` launchd job to run nightly at **00:00**.

### Implementation details
- Wrote/updated: `~/Library/LaunchAgents/com.homelab.backup.plist`
- Command uses Homebrew Bash for script compatibility:
  - `/opt/homebrew/bin/bash -c '... scripts/backup-all ...'`
- Reloaded launch agent and verified it is loaded.

### Result
`launchctl list | grep com.homelab.backup` shows job present.

## 2026-02-20 — Uptime Kuma monitor baseline documented for deployment

**Type:** documentation/process  
**Operator:** OpenClaw + Brian  
**Services affected:** uptime-kuma, platform-up workflow

### What changed
Added a baseline monitor checklist script and wired it into deployment documentation.

### Changes
- Added script: `scripts/setup-kuma-baseline`
  - prints required monitor set for Kuma
  - performs endpoint reachability checks
- Updated `platform/uptime-kuma/README.md`
  - first-run now includes running the baseline helper
- Updated `scripts/platform-up`
  - end-of-run warning now reminds operator to configure Kuma monitors

### Why
Uptime Kuma showed all zeros because monitors are not auto-created by default. This makes the required step explicit and repeatable.

<!-- Add new entries above this line, newest first -->
