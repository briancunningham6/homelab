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

| Task | Status | Notes |
|------|--------|-------|
| Create `~/homelab` directory structure | :white_circle: | |
| Deploy Docker Engine + Compose | :white_circle: | |
| Deploy Dockge (stack management) | :white_circle: | |
| Deploy Homepage (dashboard) | :white_circle: | |
| Deploy Caddy (reverse proxy) | :white_circle: | |
| Deploy Tailscale (remote access) | :white_circle: | |
| Deploy Uptime Kuma (monitoring) | :white_circle: | |
| Create `docs/inventory.md` | :white_circle: | |
| Create `docs/runbook.md` | :white_circle: | |

---

## Phase 2: Identity

**Goal:** Centralised identity with family accounts and RBAC.

| Task | Status | Notes |
|------|--------|-------|
| Deploy Authentik | :white_circle: | |
| Create family user accounts | :white_circle: | |
| Create baseline groups (homelab-admin, parents, kids) | :white_circle: | |
| Apply Authentik branding | :white_circle: | |
| Configure break-glass admin account | :white_circle: | |
| Create `docs/access-matrix.md` | :white_circle: | |

---

## Phase 3: Applications

**Goal:** First production app (Immich) deployed with full platform integration.

| Task | Status | Notes |
|------|--------|-------|
| Deploy Immich with pinned image tags | :white_circle: | |
| Wire Immich SSO via Authentik | :white_circle: | |
| Map immich-admin / immich-user groups | :white_circle: | |
| Add Immich to Homepage dashboard | :white_circle: | |
| Add Immich Uptime Kuma monitor | :white_circle: | |
| Configure Immich backup policy | :white_circle: | |
| Run Immich restore test | :white_circle: | |
| Record in inventory and access-matrix | :white_circle: | |

---

## Phase 4: Storage Expansion

**Goal:** External SSD provides capacity for media-heavy workloads.

| Task | Status | Notes |
|------|--------|-------|
| Attach external SSD | :white_circle: | |
| Configure stable mount paths (`/Volumes/HomelabData/`) | :white_circle: | |
| Migrate Immich media library to external storage | :white_circle: | |
| Migrate backup repositories to external storage | :white_circle: | |
| Update compose files and inventory | :white_circle: | |

---

## Phase 5: DR Hardening

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

## Phase 6: Local AI

**Goal:** Family-accessible AI running locally with group-based access.

| Task | Status | Notes |
|------|--------|-------|
| Deploy Ollama via Compose | :white_circle: | |
| Deploy Open WebUI via Compose | :white_circle: | |
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
- [ ] Offsite backup to Pi target is operational
- [ ] A restore drill has been executed and documented

---

## Future Work (not yet phased)

| Area | Description |
|------|-------------|
| OpenClaw agents | Multi-user AI agent layer (see [agent-model.md](agent-model.md)) |
| Multi-node scaling | Adding app/AI/DR nodes (see DESIGN.md §8) |
| Custom app development | Build family/developer apps using the [app spec](app-spec.md) |
| Contributor onboarding | Simplify and document for external contributors |
