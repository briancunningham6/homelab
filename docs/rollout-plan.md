# Rollout Plan

> Phased implementation and status tracking | Parent: [DESIGN.md](../DESIGN.md)

---

## Status Key

| Icon | Meaning |
|------|---------|
| :white_circle: | Not started |
| :large_blue_circle: | In progress |
| :green_circle: | Complete |

---

## Phase 1: Foundation

**Goal:** Core platform running with monitoring and documentation.

> Infrastructure files created via agent tasks. Deployment pending on Mac mini.

| Task | Status | Notes |
|------|--------|-------|
| Create `~/homelab` directory structure | :large_blue_circle: | Repo structure and all stack files created |
| Deploy Docker Engine + Compose | :large_blue_circle: | Docker Desktop running on Mac mini |
| Deploy Dockge (stack management) | :large_blue_circle: | `platform/dockge/` created; stack running |
| Deploy Homepage (dashboard) | :large_blue_circle: | `platform/homepage/` created; stack running |
| Deploy Caddy (reverse proxy) | :large_blue_circle: | `platform/caddy/` created; stack running |
| Deploy Tailscale (remote access) | :large_blue_circle: | `platform/tailscale/` created; requires TS_AUTHKEY |
| Deploy Uptime Kuma (monitoring) | :large_blue_circle: | `platform/uptime-kuma/` created; stack running |
| Create `docs/inventory.md` | :large_blue_circle: | Created in `docs/inventory.md` |
| Create `docs/runbook.md` | :large_blue_circle: | Created in `docs/runbook.md` |

---

## Phase 2: Identity

**Goal:** Centralised identity with family accounts and RBAC.

> Infrastructure files created via agent tasks. Deployment pending on Mac mini.

| Task | Status | Notes |
|------|--------|-------|
| Deploy Authentik | :large_blue_circle: | `platform/authentik/` created; 4-container stack running |
| Create family user accounts | :white_circle: | Complete via `http://login.home` after first-run setup |
| Create baseline groups (homelab-admin, parents, kids) | :white_circle: | See `docs/onboarding.md` |
| Apply Authentik branding | :white_circle: | |
| Configure break-glass admin account | :white_circle: | `akadmin` account created on first run |
| Create `docs/access-matrix.md` | :large_blue_circle: | Created in `docs/access-matrix.md` |

---

## Phase 3: Applications

**Goal:** First production app (Immich) deployed with full platform integration.

> Infrastructure files created via agent tasks. Deployment pending on Mac mini.

| Task | Status | Notes |
|------|--------|-------|
| Deploy Immich with pinned image tags | :large_blue_circle: | `apps/immich/` created; stack running on v2.5.6 |
| Wire Immich SSO via Authentik | :white_circle: | Steps documented in `apps/immich/README.md` |
| Map immich-admin / immich-user groups | :white_circle: | Pending Authentik group creation |
| Add Immich to Homepage dashboard | :large_blue_circle: | Added to `platform/homepage/config/services.yaml` |
| Add Immich Uptime Kuma monitor | :white_circle: | Configure via `http://status.home` |
| Configure Immich backup policy | :white_circle: | Scope documented in `apps/immich/app-contract.yaml` |
| Run Immich restore test | :white_circle: | |
| Record in inventory and access-matrix | :white_circle: | Pending `docs/inventory.md` and `docs/access-matrix.md` update |

---

## Phase 4: OpenClaw — Early Agent Rollout

**Goal:** Validate the multi-agent model by giving every family member a working AI agent scoped to their identity and permissions. This is an early bet — if agents prove useful, OpenClaw becomes central to how the family interacts with the platform.

**Prerequisite:** Phases 1–3 complete (platform running, identity configured, at least one app deployed).

See [agent-model.md](agent-model.md) for the full design and [security.md](security.md) § 7 for agent security model.

| Task | Status | Notes |
|------|--------|-------|
| **Runtime selection** | | |
| Evaluate agent runtimes (Open WebUI, custom, etc.) | :white_circle: | Resolve open question from agent-model.md § 7 |
| Deploy chosen runtime via Compose in `ai/openclaw/` | :white_circle: | Follow app-spec conventions |
| Wire runtime to Authentik SSO | :white_circle: | OIDC preferred |
| Add to Caddy (`openclaw.home`) and Homepage | :white_circle: | |
| **Admin agent lane** | | |
| Configure admin agent with platform management tools | :white_circle: | Scoped to `homelab-admin` group |
| Test: agent can run `platform-up`, check health, read logs | :white_circle: | Uses scripts from `scripts/` |
| Test: agent respects confirmation gates for destructive ops | :white_circle: | |
| **User agent lanes** | | |
| Create per-user isolated workspaces and memory stores | :white_circle: | One per family member |
| Scope user agents to Authentik group membership | :white_circle: | `parents` group → user lane |
| Test: user agent can interact with Immich (browse, upload) | :white_circle: | Via app API, not direct DB |
| Test: user agent cannot access admin tools or other users' data | :white_circle: | |
| **Child agent lane** | | |
| Configure child agents with safety restrictions | :white_circle: | `kids` group → child lane |
| Implement parent-approval gate for destructive actions | :white_circle: | Or document as manual for now |
| Test: child agent cannot exceed allowed app/data scope | :white_circle: | |
| **Operational integration** | | |
| Define agent tool registry (what each lane can call) | :white_circle: | |
| Configure per-user credential injection for app access | :white_circle: | Tokens via Authentik, not shared secrets |
| Set up audit logging for all agent actions | :white_circle: | |
| Add Uptime Kuma monitor for agent runtime | :white_circle: | |
| Document agent setup in `docs/runbook.md` | :white_circle: | |
| Update `docs/access-matrix.md` with agent lane mappings | :white_circle: | |
| **Evaluation** | | |
| Each family member tests their agent for 1–2 weeks | :white_circle: | Collect feedback |
| Write evaluation summary: keep / iterate / defer | :white_circle: | Go/no-go for deeper investment |

---

## Phase 5: Storage Expansion

**Goal:** External SSD provides capacity for media-heavy workloads.

| Task | Status | Notes |
|------|--------|-------|
| Attach external SSD | :white_circle: | |
| Configure stable mount paths (`/Volumes/HomelabData/`) | :white_circle: | |
| Migrate Immich media library to external storage | :white_circle: | |
| Migrate backup repositories to external storage | :white_circle: | |
| Update compose files and inventory | :white_circle: | |

---

## Phase 6: DR Hardening

**Goal:** Tested offsite backup with documented recovery procedures.

| Task | Status | Notes |
|------|--------|-------|
| Deploy offsite Raspberry Pi + external HDD | :white_circle: | |
| Join Pi to Tailscale | :white_circle: | |
| Configure Restic encrypted offsite replication | :white_circle: | |
| Optional: configure Backblaze B2 secondary copy | :white_circle: | |
| Run first full restore drill | :white_circle: | |
| Document results in `docs/dr-runbook.md` | :white_circle: | |

---

## Phase 7: Local AI Expansion

**Goal:** Dedicated local inference for family use, expanding beyond OpenClaw's agent layer.

| Task | Status | Notes |
|------|--------|-------|
| Deploy Ollama via Compose | :white_circle: | May already exist if OpenClaw runtime uses it |
| Deploy Open WebUI via Compose | :white_circle: | Standalone chat interface alongside agents |
| Configure model storage on external SSD | :white_circle: | |
| Wire Authentik SSO for Open WebUI | :white_circle: | |
| Map ai-admin / ai-user / ai-kids groups | :white_circle: | |
| Set usage quotas and concurrency limits | :white_circle: | |

---

## Definition of Done (v1)

This platform is considered **active** when all of the following are true:

- [ ] `~/homelab/` structure exists and matches documented layout
- [ ] Core platform services (Phase 1) are running and monitored
- [ ] Authentik is running with family accounts and baseline groups
- [ ] At least one app (Immich) is deployed with monitoring + backup + access mapping
- [ ] Every family member has a working OpenClaw agent scoped to their identity
- [ ] Offsite backup to Pi target is operational
- [ ] A restore drill has been executed and documented

---

## Future Work (not yet phased)

| Area | Description |
|------|-------------|
| OpenClaw deep integration | Advanced agent tooling, automations, and scheduled jobs (builds on Phase 4 evaluation) |
| Multi-node scaling | Adding app/AI/DR nodes (see DESIGN.md §8) |
| Custom app development | Build family/developer apps using the [app spec](app-spec.md) |
| Contributor onboarding | Simplify and document for external contributors |
