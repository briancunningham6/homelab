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
Brought the homelab stack up on the Mac mini from `/Users/briancunningham/dev/homelab` and verified that Immich responds through Caddy.

### Steps taken
1. Ran platform startup using repo path override:
   - `HOMELAB_DIR=/Users/briancunningham/dev/homelab ./scripts/platform-up`
2. Fixed Dockge stack path config:
   - `platform/dockge/.env` updated from `/Users/user/homelab` → `/Users/briancunningham/dev/homelab`
3. Started Dockge directly:
   - `HOMELAB_DIR=/Users/briancunningham/dev/homelab ./scripts/app-up dockge`
4. Started Immich directly:
   - `HOMELAB_DIR=/Users/briancunningham/dev/homelab ./scripts/app-up immich`
5. Added quick LAN access host for experiment to Caddyfile:
   - `http://immich.home, http://192.168.0.199` → `immich-server:2283`
6. Reloaded Caddy and validated Immich ping:
   - `curl http://192.168.0.199/api/server/ping` returned `{"res":"pong"}`

### Result
Core platform and app stacks running; Immich reachable over LAN via Caddy at:
- `http://192.168.0.199`
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

<!-- Add new entries above this line, newest first -->
