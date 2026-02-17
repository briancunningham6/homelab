# Homelab Standard v1.1 (Mac mini)

I want to develop a homelab that hosts and runs various applications for myself and my family. The focus is on running the applications from hardware in my home. I want a robust but managable system that replaces multiple cloud based solutions that I use today. Initially I want containerised instances of existing software to run on this. I also want to define a specification for applications that can be custom built to run on this platform so that vibecoded applications can run on it. A standardised way of managing users and RBAC is implemented to handle user access. OpenClaw agents are provided to the users to interact with their applications while keeping access to their data secure. Since this will be all managed at home we need disaster recoverey and simplicity at the fore. 
 
Owner: Brian  
Host (primary): Mac mini (home services node)  
DR host (offsite): Relative’s house (Raspberry Pi-class device + external HDD)  
Primary goals: standardized installs, clean management, family access control, secure remote access, and tested disaster recovery.

---

## 1) Principles

1. **One install method for self-hosted services:** Docker Compose.
2. **One app = one folder** (`compose.yml`, `.env`, `data/`, `README.md`, `backups/`).
3. **No direct internet exposure by default.** Use Tailscale for remote access.
4. **Identity-first access model:** centralized users/groups via Authentik where app support allows.
5. **Backups are mandatory; restore tests are mandatory.**
6. **Changes are reversible** (pinned image tags + rollback path).
7. **Resource-aware defaults** (Mac mini is fast but disk-limited and shared with Minecraft use).

---

## 2) Platform Architecture (what we run)

## Core platform
- Docker Engine + Docker Compose
- Dockge (stack management)
- Homepage (dashboard)
- Caddy (reverse proxy)
- Tailscale (secure private remote access)
- Uptime Kuma (monitoring)

## Identity & access
- Authentik (central users, groups, SSO)

## Data protection
- Restic (encrypted backups)
- Offsite target A: Raspberry Pi + external HDD (via Tailscale)
- Offsite target B: Backblaze B2 (optional secondary/fallback)

## AI tier (future-ready)
- Ollama (or vLLM, hardware-dependent)
- Open WebUI (family AI frontend)
- Model storage on external SSD/NVMe

---

## 3) Standard Filesystem Layout

```text
~/homelab/
  apps/
    <app-name>/
      compose.yml
      .env
      data/
      backups/
      README.md
  platform/
    dockge/
    homepage/
    caddy/
    uptime-kuma/
    authentik/
    tailscale/
  ai/
    ollama/
    open-webui/
    models/                 # preferably external storage mount later
  backups/
    local/
    manifests/
    restore-tests/
  scripts/
    app-up
    app-down
    app-update
    app-backup
    app-restore
    dr-verify
  docs/
    inventory.md
    access-matrix.md
    runbook.md
    dr-runbook.md
```

Rules:
- Folder names are lowercase kebab-case.
- Persistent app data must live under that app folder (or approved external mount path).
- All exposed ports, domains, owners, and backup targets must be recorded in `docs/inventory.md`.

---

## 4) Networking & Remote Access Standard

## Local access
- Stable local hostnames through Caddy, e.g.:
  - `immich.home`
  - `login.home` (Authentik)
  - `status.home` (Kuma)

## Remote access
- Tailscale-only by default (MagicDNS preferred).
- Avoid router port forwarding unless explicitly approved.

## Port policy
- Prefer internal Docker networks.
- Publish host ports only when needed.
- Admin UIs restricted to LAN/Tailscale.

---

## 5) Storage Strategy (Mac mini limited disk)

## Phase A (start on internal disk)
- Run platform services on internal storage.
- Keep media-heavy apps constrained initially.
- Trigger thresholds:
  - Warning at 75% disk used
  - Action required at 85% disk used

## Phase B (external storage expansion)
- Add external SSD for large-state workloads.
- Move first:
  - Immich media/library
  - backup repositories and snapshots
  - AI model files
- Keep configs/lightweight DBs on internal disk unless needed.
- Use stable mount path convention, e.g.:
  - `/Volumes/HomelabData/immich-library`
  - `/Volumes/HomelabData/backups`
  - `/Volumes/HomelabData/models`

---

## 6) Identity & Family User Management Standard

## Identity provider
- Authentik hosted on Mac mini (critical service).

## User policy
- One account per person (no shared family password).
- Group-based access control (RBAC), not one-off per-user app tweaks.

## Baseline groups
- `homelab-admin`
- `parents`
- `kids`
- `immich-admin`
- `immich-user`
- `ai-admin`
- `ai-user`
- `ai-kids`

## App integration pattern
1. Create app in Authentik.
2. Configure OIDC/SAML/LDAP as supported.
3. Map Authentik groups to app roles.
4. Keep a local emergency admin account (“break-glass”), documented securely.

## UX customization
- Authentik branding customization allowed (logo/colors/domain/text).
- Avoid deep custom UI forks that increase upgrade fragility.

---

## 7) App Deployment Standard (example: Immich)

For each app:
1. Create app folder + template files.
2. Deploy with pinned image tags.
3. Add to Homepage + Uptime Kuma.
4. Wire Authentik SSO when supported.
5. Add backup policy + restore test entry.
6. Record in `inventory.md` and `access-matrix.md`.

Immich-specific:
- Start with conservative settings while on internal disk.
- Move media library to external storage in Phase B.
- Map `immich-admin` and `immich-user` groups through Authentik integration.

---

## 8) Backup & Disaster Recovery Standard (Hybrid Offsite)

## Backup model (3-2-1)
- 3 copies of data
- 2 locations/media (local + offsite)
- 1 offsite copy minimum

## Targets
- Local backup: Mac mini (fast restore)
- Offsite primary: Relative’s Pi + external HDD (over Tailscale)
- Offsite optional secondary: Backblaze B2

## Tooling
- Restic with client-side encryption before transfer.

## Scope (minimum)
- Compose files, `.env`, configs
- Authentik DB + secrets
- App DBs (Immich/Postgres, etc.)
- User content/media
- AI workflows/configs (model weights optional; can re-pull)

## Schedule (starter)
- Daily incremental
- Weekly checkpoint
- Monthly retained snapshot
- Suggested retention: 14 daily / 8 weekly / 6 monthly / 1 yearly

## DR testing
- Quarterly restore drill required.
- Document measured RPO/RTO in `dr-runbook.md`.

---

## 9) Security Baseline

1. Strong unique credentials in password manager.
2. MFA for admin/parent accounts.
3. Tailscale-only remote administration.
4. No anonymous public shares by default.
5. Monthly patch/update window for macOS + containers.
6. Quarterly exposure review (ports, apps, stale accounts, old tokens).
7. Backup key escrow process (owner + emergency sealed copy).

---

## 10) Local AI Integration Standard (future hardware path)

## Deployment model
- `ollama` + `open-webui` via Compose first.
- External storage for model files.

## Access model
- Authentik groups gate AI access (`ai-admin`, `ai-user`, `ai-kids`).
- Restrict tools/internet connectors by group.

## Operations
- Monitor CPU/RAM/disk and request latency.
- Set usage quotas/concurrency limits.
- Keep cloud fallback optional, not default.

---

## 11) OpenClaw Management Contract

OpenClaw should:
1. Operate primarily within `~/homelab/**`.
2. Ask before destructive actions (delete/reset/migration).
3. For updates: pre-check → backup → update → verify → report.
4. Keep change log in `docs/runbook.md`.
5. Keep DR/restore outcomes in `docs/dr-runbook.md`.

---

## 12) Restart & Recovery Standard (Minimal User Input)

Goal: after host restart, services return online automatically with no routine manual intervention.

## Auto-start layers
1. **Host layer (launchd):** OpenClaw and startup orchestrator must run with `RunAtLoad` + `KeepAlive`.
2. **Container layer (Compose):** all services use `restart: unless-stopped`.

## Deterministic boot sequence
A startup orchestrator script must run on boot and follow this order:
1. Wait for network readiness.
2. Wait for required mounts (especially external storage paths).
3. Start platform core first: Tailscale → Caddy → Authentik → monitoring/dashboard.
4. Start application stacks (Immich and other apps).
5. Execute health checks and record status.

## External storage guardrails
- If an app depends on external storage and mount is missing, do not start that app in write mode.
- Raise alert and mark service degraded rather than risking data corruption.

## Post-boot health policy
- Run health checks for every platform/app service endpoint.
- If unhealthy: retry start, then targeted restart.
- If still unhealthy after retries: alert user with clear remediation notes.

## User experience target
- Typical reboot recovery should complete in ~2–5 minutes.
- User should be able to open dashboard and see service state without CLI steps.

## Reliability validation
- Perform a planned reboot recovery test at least monthly.
- Log startup outcomes and incidents in `docs/runbook.md`.
- Maintain a one-command recovery helper in `scripts/` for common failures.

---

## 13) Multi-Agent Access Model (User / Child / Admin)

Goal: every person gets an agent aware of their own context with limited permissions; administrators get a separate privileged agent for platform operations.

## Agent lanes
1. **User Agent Lane (default):**
   - per-user isolated workspace and memory scope
   - per-user scoped app credentials/tokens
   - access only to apps/data allowed by Authentik groups
   - no unrestricted host/system administration

2. **Child Agent Lane:**
   - same isolation as user lane, with stricter safety policy
   - limited tools and external actions by default
   - app/data access restricted to child-owned or explicitly shared resources
   - optional parent-approval gates for sensitive actions (share/export/delete)

3. **Admin Agent Lane:**
   - full homelab management scope (install/update/configure/backup/DR)
   - access to infrastructure tools and system operations
   - explicit confirmation required for destructive actions

## Separation requirements
- Isolate per-user: workspace, memory files, credentials, schedules/jobs, and logs.
- Enforce least privilege in every lane.
- Do not allow cross-user data access unless explicitly shared by policy.

## Identity & policy integration
- Authentik is source of truth for users/groups.
- Groups define both app access and agent capability level.
- Suggested baseline groups:
  - `homelab-admin`
  - `parents`
  - `kids`
  - app-specific role groups (e.g., `immich-admin`, `immich-user`, `ai-user`, `ai-kids`)

## App rollout requirement
Every new app must include:
1. Auth mapping (OIDC/SAML/LDAP or proxy-auth fallback)
2. Role-to-group mapping documented in `docs/access-matrix.md`
3. Data scope rules for user/child/admin lanes
4. Audit and backup coverage before production use

## Operational controls
- All admin-lane infrastructure actions are logged.
- Break-glass admin account maintained and documented securely.
- Access revocation must be immediate via Authentik group/user disable.

---

## 14) Multi-Node Scaling Architecture (Extendable Home Cluster)

Goal: scale beyond one Mac mini by adding specialized nodes without changing user experience, identity model, or operational standards.

## Node roles
1. **Control Node (primary Mac mini):**
   - Authentik, Caddy, Homepage, Uptime Kuma, OpenClaw admin control plane
2. **App Node(s):**
   - application stacks (Immich, custom family/developer apps)
3. **AI Node (dedicated GPU machine):**
   - Ollama/vLLM inference services and model storage
4. **DR Node (offsite Pi + external drive):**
   - encrypted backup target and restore staging

## Placement policy
- Assign services by role and resource profile (CPU, RAM, disk, GPU).
- Keep identity and routing stable while moving app workloads between nodes.
- Record placement decisions in `docs/inventory.md` and `docs/nodes.md`.

## Unified routing model
- Keep stable service URLs regardless of host node (e.g., `immich.home`, `ai.home`, `login.home`).
- Caddy/front-door routes traffic to the correct backend node over trusted network paths.
- Tailscale + internal DNS/MagicDNS provide secure reachability across nodes.

## Identity continuity
- Single Authentik authority for all nodes/apps.
- App access remains group-driven, independent of where app is hosted.

## Multi-node data strategy
- Default: app data stays local to the hosting node.
- Replicate via backup/restore and explicit migration workflows (not ad-hoc shared mounts).
- Keep heavy media/model datasets on external SSD/NVMe attached to the service node.

## Capacity expansion runbook
When adding a new machine:
1. Join node to Tailscale.
2. Apply node baseline (Docker, monitoring hooks, backup hooks).
3. Register node in `docs/nodes.md` and inventory.
4. Deploy assigned stacks from templates.
5. Add health checks and dashboard entries.
6. Run restart and recovery validation.

## Failure isolation
- Issues on AI node should not impact core identity/control plane.
- App node failure should be recoverable by redeploying stack on another node using same templates and backups.

---

## 15) Rollout Plan

## Phase 1: Foundation
- Create `~/homelab` structure
- Deploy Dockge, Homepage, Caddy, Tailscale, Uptime Kuma
- Create docs: `inventory.md`, `runbook.md`

## Phase 2: Identity
- Deploy Authentik
- Create family users/groups
- Apply branding and policy baseline

## Phase 3: Apps
- Deploy Immich with SSO + monitoring + backup
- Optional Copyparty migration into Compose standard

## Phase 4: Storage expansion
- Attach external SSD
- Migrate media/backups/models to external mount paths

## Phase 5: DR hardening
- Deploy offsite Pi backup receiver + drive
- Enable encrypted offsite replication
- Add optional Backblaze B2 secondary copy
- Run first full restore drill

## Phase 6: Local AI
- Deploy Ollama + Open WebUI
- Apply group-based access and safety defaults

---

## 16) Catastrophic Rebuild From Backups (Bare-Metal Recovery)

Goal: if primary systems are lost/destroyed, rebuild a working homelab from backups and documented procedures alone.

## Mandatory backup scope for full rebuild
1. **Platform manifests/config:** all `compose.yml`, `.env`, reverse proxy configs, dashboard and monitoring configs.
2. **Identity core:** Authentik database, configuration exports, and signing/encryption keys.
3. **Application state:** app databases, media/content libraries, and app-specific config folders.
4. **Operations docs:** `inventory.md`, `nodes.md`, `access-matrix.md`, `runbook.md`, `dr-runbook.md`.
5. **Secrets and recovery credentials:** backup repository keys/passwords, API tokens, break-glass credentials (stored securely outside primary site).

## Recovery dependency order (must follow)
1. Prepare replacement hardware/OS.
2. Restore baseline connectivity (network + Tailscale).
3. Restore homelab manifests and secrets.
4. Restore identity plane first (Authentik + required keys).
5. Restore control plane (Caddy, Homepage, Uptime Kuma, OpenClaw).
6. Restore application databases and persistent data.
7. Start app stacks and run health checks.
8. Validate user logins, RBAC/group mappings, and critical user workflows.

## Rebuild readiness requirements
- Backups are encrypted and replicated offsite (Pi target; optional B2 secondary).
- Restore instructions are versioned and current.
- Required credentials are available via emergency access process.
- Restore process is executable by a second trusted operator, not only one person.

## Recovery objectives
- Initial target **RPO**: ≤24 hours.
- Initial target **RTO**: core platform restored same day (4–8 hours typical), full media restore may take longer.

## Verification policy (non-negotiable)
- Perform quarterly bare-metal restore drills (or equivalent staged simulation).
- Record pass/fail, elapsed time, data loss observed, and blockers in `docs/dr-runbook.md`.
- Any failed drill creates mandatory remediation tasks before next cycle.

---

## 17) Definition of Done (v1.1)

This standard is considered active when:
- `~/homelab/` structure exists and is documented
- Core platform and Authentik are running
- At least one app (Immich) is deployed with monitoring + backup + access mapping
- Offsite backup to Pi target is operational (B2 optional configured if desired)
- Restore drill has been executed and documented

---

## 18) Notes for this specific Mac mini

- Keep background resource use moderate due to shared Minecraft usage.
- Schedule heavy jobs (indexing/backups) outside peak gaming times.
- Prefer conservative defaults first, then scale after usage proves value.

---

Version: **v1.1-draft**  
Date: 2026-02-16  
Owner: Brian + OpenClaw
