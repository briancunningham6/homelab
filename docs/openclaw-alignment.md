# OpenClaw Host Alignment Guide

> How this homelab platform and its applications align with an OpenClaw instance running on the same host machine.

Parent references:
- [DESIGN.md](../DESIGN.md)
- [agent-model.md](agent-model.md)
- [app-spec.md](app-spec.md)
- [ops-standard.md](ops-standard.md)

---

## 1) Objective

Enable a single host (initially Mac mini) to run:
1. Platform services (Caddy, Authentik, Homepage, Uptime Kuma, etc.)
2. Family/developer applications
3. OpenClaw as the local control and automation layer

…while preserving security boundaries, per-user context isolation, and operational reliability.

---

## 2) Current Project Fit (quick review)

The current repo is already well-aligned with OpenClaw:

- Strong platform decomposition (`platform/`, `apps/`, `docs/`, `scripts/`)
- Agent model already defined ([agent-model.md](agent-model.md))
- App contract and onboarding standards already defined ([app-spec.md](app-spec.md), [onboarding.md](onboarding.md))
- DR/restart standards documented ([ops-standard.md](ops-standard.md))
- Compose validation tooling exists (`scripts/validate-compose`)

### Immediate gaps to resolve for safe OpenClaw operations

1. Tracked `.env` files currently exist in git history/state.
2. OpenClaw runtime implementation is still conceptual (Phase 4 not yet delivered).
3. No CI gate yet enforcing app contract + compose validation + secret checks.

---

## 3) Target Integration Model

## 3.1 Control-plane model

OpenClaw runs on the same host as the platform, in an **admin control lane**:

- Uses local scripts in `scripts/` for deterministic operations
- Reads/writes operational docs (`docs/runbook.md`, `docs/dr-runbook.md`)
- Executes change workflows with confirmation gates for destructive actions

## 3.2 User-plane model

User interactions happen through per-user agent lanes:

- Identity source of truth: Authentik
- Per-user context: isolated memory/workspace/session scope
- App/API access: group-derived scopes only
- No unrestricted host tooling for non-admin lanes

## 3.3 Child safety model

Child lanes inherit user isolation plus restrictions:

- reduced tool surface
- stricter content/action policies
- optional parent-approval gates for share/export/delete

---

## 4) Host Co-location Design (same machine)

## 4.1 Process/service boundaries

- OpenClaw service managed by host init (launchd on macOS)
- Platform and apps managed by Docker Compose
- Use one OpenClaw gateway per machine unless a second instance is explicitly isolated

## 4.2 Network boundaries

- OpenClaw talks to apps over local trusted routes (`*.home` via Caddy)
- Remote access remains Tailscale-first
- No direct internet exposure for internal admin surfaces by default

## 4.3 Storage boundaries

- OpenClaw state remains separate from app data volumes
- App data follows app folder standard (`apps/<app>/data`)
- Heavy datasets (media/models/backups) migrate to external SSD in Phase 5

---

## 5) Application Alignment Contract (OpenClaw-ready app)

An app is considered OpenClaw-ready when all are true:

1. Conforms to [app-spec.md](app-spec.md) structure
2. Supports central auth (OIDC preferred)
3. Provides a health endpoint
4. Has backup + restore instructions
5. Declares agent scope in `app-contract.yaml`
6. Is added to inventory and access matrix

### Required app-control interface

Each app should expose at least one of:

- API endpoints (preferred)
- deterministic CLI task wrappers
- admin actions scripted in `scripts/` with idempotent behavior

OpenClaw should call wrappers/scripts rather than ad-hoc shell logic where possible.

---

## 6) Recommended OpenClaw Operating Pattern

For all admin-lane tasks:

1. **Preflight:** service health + dependency checks
2. **Protect:** backup/snapshot if state will change
3. **Apply:** execute one scoped change
4. **Verify:** health + functional check
5. **Record:** append change log entry to runbook

This pattern should be the default for installs, upgrades, migrations, and configuration changes.

---

## 7) Minimum Technical Controls

## 7.1 Identity and authorization
- Authentik is required for user identity lifecycle
- Group-to-role mapping required per app
- Immediate revocation by disabling user/group membership

## 7.2 Secrets handling
- Never commit runtime `.env` files
- Use `.env.example` in repo, real secrets outside git history
- Rotate any previously committed secrets and clean repository history

## 7.3 Reliability controls
- Host restart auto-recovery sequence from [ops-standard.md](ops-standard.md)
- Service health checks and alerting via Uptime Kuma
- Monthly reboot recovery validation

## 7.4 DR controls
- Encrypted offsite backups (Pi target, optional B2 secondary)
- Quarterly restore drill with documented pass/fail

---

## 8) CI/CD and Governance (required before wider rollout)

Add repository gates so every contribution remains OpenClaw-compatible:

1. Compose validation in CI (`scripts/validate-compose`)
2. Secret scanning (gitleaks/trufflehog)
3. App contract validation (`app-contract.yaml` schema check)
4. Documentation checks (required files present)
5. Optional: policy checks that reject public port exposure unless tagged/approved

---

## 9) Same-Host Resource Strategy (Mac mini)

To keep co-located OpenClaw + apps stable:

- Keep internal disk below ~70% target usage
- Trigger warnings at 75%, action at 85%
- Schedule heavy jobs outside peak local usage windows
- Defer heavy AI workloads or move to dedicated GPU node when needed

---

## 10) Phased Implementation for OpenClaw Alignment

## Phase A — Secure baseline
- Remove committed secrets and rotate credentials
- Ensure one stable OpenClaw gateway service
- Confirm restart/sleep policy keeps host available

## Phase B — Admin lane first
- Implement admin lane scripts/workflows only
- Validate update/backup/restore workflows end-to-end
- Record all operations in runbook

## Phase C — First user lane
- Enable one non-admin user lane
- Connect one app (Immich) through Authentik + scoped permissions
- Validate cross-user isolation and revocation

## Phase D — Family rollout
- Add remaining user/child lanes
- Enforce app contract for all new apps
- Add CI governance and periodic policy audits

---

## 11) Definition of “Aligned with OpenClaw”

This platform is considered OpenClaw-aligned when:

- OpenClaw can manage platform lifecycle safely using scripted/idempotent actions
- User/child/admin lanes are technically separated and policy-enforced
- All deployed apps expose an OpenClaw-compatible control interface
- Secrets, backups, and restore drills are operationalized
- CI gates prevent regressions in compose/security/app contract compliance

---

## 12) Immediate Next Actions (recommended)

1. Remove tracked `.env` files from git and rotate affected credentials.
2. Add CI workflow for compose validation + secret scanning.
3. Implement and document the first admin-lane operation set (install/update/backup/restore).
4. Execute one golden path: Authentik + Immich + one user lane + runbook evidence.
