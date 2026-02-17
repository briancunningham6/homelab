# Developer Application Specification

> Platform Conformance v1 | Parent: [DESIGN.md](../DESIGN.md)

Goal: enable developers (including AI coding-agent workflows) to build apps that integrate cleanly with the homelab platform's identity, access, operations, backup, and multi-agent controls.

---

## 1. Packaging & Runtime

| Requirement | Detail |
|-------------|--------|
| Runtime | Docker (container only) |
| Required files | `Dockerfile` (or pinned upstream image), `compose.yml`, `.env.example`, `README.md` |
| User | Non-root container user where feasible |
| Restart policy | `unless-stopped` |
| Image tags | Pinned versions, never `latest` in production |

---

## 2. Standard App Folder Layout

```text
~/homelab/apps/<app-name>/
├── compose.yml
├── .env
├── .env.example
├── data/
├── backups/
├── app-contract.yaml
└── README.md
```

- App name is lowercase kebab-case.
- Persistent state must live under `data/` (or an approved external mount path).
- `.env.example` documents all required and optional environment variables.

---

## 3. Identity & Access Integration

| Priority | Auth mode |
|----------|-----------|
| Preferred | OIDC with Authentik |
| Fallback 1 | SAML or LDAP |
| Fallback 2 | Proxy-auth pattern (Caddy + Authentik forward auth) |

**Requirements:**
1. Role groups at minimum: `<app>-admin`, `<app>-user`.
2. Optional additional groups: `<app>-readonly`, `<app>-kids`.
3. No shared or hardcoded credentials.
4. Document group-to-role mapping in `docs/access-matrix.md`.

---

## 4. Networking & Exposure

1. **Private by default** — LAN and Tailscale only.
2. No direct public exposure without explicit approval and documentation.
3. Stable hostname via Caddy routing (e.g., `<app>.home`).
4. All ports and protocols documented in `docs/inventory.md`.

---

## 5. Health, Observability & Operations

| Requirement | Detail |
|-------------|--------|
| Health endpoint | `/health` or equivalent returning HTTP 200 when healthy |
| Logging | stdout/stderr (no internal-only log files) |
| Documentation | README must include: start, stop, update, rollback, backup, restore commands |
| Monitoring | Uptime Kuma monitor defined before production use |

---

## 6. Backup & Recovery Contract

1. App must declare its critical data scope (database, config, user content).
2. Backup and restore procedures must be documented in the app README.
3. App must be fully restorable on new hardware from backups + manifests + secrets.
4. Expected RPO/RTO class must be specified in the app contract.

---

## 7. Security Baseline

1. Secrets via `.env` or Docker secret files only — never hardcoded in source.
2. Least-privilege defaults for app and service roles.
3. Pinned dependency and image versions with documented update path.
4. Input validation and sensible auth/session defaults.

---

## 8. Multi-Agent Compatibility

Apps must define allowed actions per agent lane (see [agent-model.md](agent-model.md)):

| Lane | Description |
|------|-------------|
| **User** | Standard user operations |
| **Child** | Restricted subset with safety policy |
| **Admin** | Full app management |

At minimum, classify permissions across: `read`, `write`, `share/export`, `delete`, `configure`.

---

## 9. App Contract Manifest

Each app includes `app-contract.yaml`. Example:

```yaml
name: example-app
version: 1.0.0

auth:
  mode: oidc
  provider: authentik
  groups:
    admin: example-app-admin
    user: example-app-user

network:
  hostname: example-app.home
  internalPort: 8080

data:
  paths:
    - ./data

backup:
  includes:
    - data
  rpoClass: daily        # daily | hourly | best-effort
  restoreTest: documented

agentScopes:
  user: [read, write]
  child: [read]
  admin: [read, write, delete, configure]

health:
  endpoint: /health
```

---

## 10. Deployment Checklist

For each new app deployment:

1. [ ] Create app folder with all required files.
2. [ ] Deploy with pinned image tags.
3. [ ] Add to Homepage dashboard.
4. [ ] Add Uptime Kuma monitor.
5. [ ] Wire Authentik SSO (or document fallback auth mode).
6. [ ] Add backup policy and run restore test.
7. [ ] Record in `docs/inventory.md` and `docs/access-matrix.md`.
8. [ ] Security checklist reviewed.

---

## 11. Release Gates

All gates must pass before an app is considered production-ready:

1. **Build + run** via Compose passes cleanly.
2. **Authentik integration** works and group mapping verified.
3. **Health checks** green in Uptime Kuma.
4. **Backup and restore** test completed and documented.
5. **Dashboard, inventory, and access-matrix** updated.
6. **Security checklist** reviewed and signed off.
