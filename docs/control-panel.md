# Homelab Control Panel

> Central web interface for platform administration | Parent: [DESIGN.md](../DESIGN.md)

**Status:** Design outline — not yet implemented

## Purpose

A single web application that gives the homelab administrator unified management of the entire platform. Instead of logging into Dockge, Authentik, Uptime Kuma, and individual app UIs separately, the control panel aggregates these functions into one interface with a consistent experience.

This is the primary tool the admin uses day-to-day. Every operational procedure documented elsewhere in this repo (updates, onboarding, teardown, backups) should eventually be executable from this panel.

---

## Scope

The control panel is an **admin-only** application. It is not a user-facing dashboard (that role belongs to Homepage). Access is gated to the `homelab-admin` Authentik group.

### What it is

- Unified management interface for the homelab operator
- Orchestration layer that calls existing platform APIs (Docker, Authentik, filesystem)
- Single place to monitor, deploy, update, and troubleshoot

### What it is NOT

- A replacement for individual app UIs (Immich, Open WebUI, etc.)
- A user-facing portal (Homepage serves that purpose)
- A container orchestrator (Docker Compose remains the deployment method)

---

## 1. Application Management

### 1.1 Application Inventory

- List all deployed applications with current status (running / stopped / error / updating)
- Show container health, uptime, image tag, and resource usage per app
- Link to each app's web UI and its `app-contract.yaml` metadata
- Surface Uptime Kuma health check status inline

### 1.2 Install / Deploy

- Browse candidate apps from `docs/app-ideas.md` (or a structured registry)
- Guided deployment workflow:
  1. Select app template or provide Compose file
  2. Configure `.env` values via form (pre-populated from `.env.example`)
  3. Validate Compose syntax (pre-flight check)
  4. Pull images and start containers
  5. Wire SSO in Authentik (create provider, application, group mappings)
  6. Register health check in Uptime Kuma
  7. Add dashboard entry in Homepage
  8. Record in `docs/inventory.md`
- Follow the [app spec](app-spec.md) release gates as a checklist the operator confirms

### 1.3 Start / Stop / Restart

- Per-app controls: start, stop, restart, recreate
- Bulk actions with dependency awareness (e.g., warn before stopping Authentik while apps depend on it)
- Respect the boot sequence defined in [ops-standard.md](ops-standard.md) § 4

### 1.4 Update

- Show available image updates (compare running tag to upstream latest/stable)
- Execute the 7-step update workflow from [ops-standard.md](ops-standard.md) § 5:
  1. Display changelog / release notes
  2. Record current state
  3. Trigger pre-update backup
  4. Edit image tag
  5. Pull new image and restart
  6. Run health verification
  7. Log result to runbook
- One-click rollback: revert tag, restore backup, restart

### 1.5 Remove / Uninstall

- Stop containers, remove volumes (with confirmation), prune images
- Clean up Authentik provider/application entries
- Remove Uptime Kuma check and Homepage entry
- Archive or delete app folder
- Follow [teardown.md](teardown.md) § 9 (single app reset)

---

## 2. User Management

All user operations wrap the Authentik Admin API — the control panel is a purpose-built UI, not a replacement for Authentik's data model.

### 2.1 User List

- View all users with status (active / inactive), groups, MFA enrolment, last login
- Quick filters: by group, by status, by app access

### 2.2 Create User

- Form: username, display name, email
- Assign to groups (multi-select from baseline + app-specific groups)
- Generate enrollment link (invite-only, per [onboarding.md](onboarding.md) § 2)
- Optionally send invite via email or copy link

### 2.3 Manage User

- Edit group memberships (add/remove access to apps)
- View active sessions and revoke if needed
- Toggle MFA requirement
- Disable user (preserves data, blocks login)
- Delete user (with data cleanup confirmation)

### 2.4 Groups & Roles

- View all Authentik groups and their members
- Create new groups (following `<app>-admin` / `<app>-user` naming convention)
- Map groups to app roles (visual representation of [access-matrix.md](access-matrix.md))

---

## 3. System Performance

### 3.1 Host Overview

- CPU usage (current, 1h/24h trend)
- Memory usage and available
- Disk usage per volume with Phase A thresholds (warning at 75%, action at 85%)
- Network throughput
- Host uptime and last reboot

### 3.2 Per-Container Resources

- CPU and memory per running container
- Disk I/O and network per container
- Identify resource-heavy containers (useful for Mac mini shared use — see [mac-mini.md](notes/mac-mini.md))

### 3.3 Storage

- Breakdown by category: platform, apps, media, backups, AI models
- External SSD status and mount health (Phase B)
- Backup repository size and growth trend
- Alerts when approaching capacity thresholds

### 3.4 Service Health

- Aggregate Uptime Kuma status for all monitored endpoints
- Highlight services that are down or degraded
- Link out to Uptime Kuma for detailed history

---

## 4. Logs

### 4.1 Container Logs

- Unified log viewer across all containers (filterable by service, severity, time range)
- Per-container log view with tail / search
- Stream live logs (equivalent to `docker compose logs -f`)

### 4.2 System Events

- Platform-level events: container start/stop/crash, image pulls, volume changes
- Docker daemon events

### 4.3 Authentication Events

- Login attempts (success / failure) from Authentik
- MFA challenges
- Group membership changes
- Enrollment completions
- Session creation and expiry

### 4.4 Operational Log

- Update history (which apps were updated, when, by whom, result)
- Backup execution results (success / failure, duration, snapshot size)
- Restore test results
- Structured view of entries from `docs/runbook.md`

---

## 5. System Reset

Expose the teardown procedures from [teardown.md](teardown.md) as guided workflows with safety gates.

### 5.1 Single App Reset

- Select app → confirm → execute [teardown.md](teardown.md) § 9 steps
- Preserves platform and all other apps

### 5.2 Platform Reset (Level 1–3)

- Guided wizard matching the three teardown scopes:
  - **Level 1 — Apps only:** Remove all app containers/data, keep platform
  - **Level 2 — Platform:** Remove platform services, keep identity backup for restore
  - **Level 3 — Full teardown:** Wipe everything, clean external services
- **Enforced pre-flight checks** before any destructive action:
  - [ ] Backup exists and is verified
  - [ ] Backup is replicated offsite
  - [ ] Credentials are recorded outside the system
  - [ ] Data preservation decisions confirmed
  - [ ] Users notified (if applicable)
- Confirmation gate: admin must type the scope level to proceed (no accidental clicks)

### 5.3 Backup Verification

- Trigger on-demand backup before reset
- Verify latest backup integrity (Restic check)
- Show last successful offsite replication timestamp
- Block teardown if backup verification fails (override requires explicit acknowledgement)

---

## 6. Offsite Backup Management

Monitor and configure the offsite backup system (Raspberry Pi + external HDD at the DR site) from the control panel. This section is an **initial outline** — capabilities will expand as the DR infrastructure matures.

### 6.1 Offsite Node Status

- **Online / offline indicator** — ping the offsite Pi via Tailscale and show connection state with last-seen timestamp
- Tailscale device status (connected, last handshake, IP address)
- Pi system health when reachable: CPU, memory, disk usage, uptime, temperature
- External HDD mount status — confirm the backup target volume is attached and writable
- Alert if the offsite node has been unreachable for more than a configurable threshold (default: 24 hours)

### 6.2 Backup Status Dashboard

- **Last successful backup** — timestamp, duration, snapshot size, and repository the snapshot was written to
- **Last offsite replication** — when data was last synced to the Pi (distinct from local backup)
- Snapshot inventory: list recent Restic snapshots across all repositories (local, offsite, B2 if configured)
- Repository health: last `restic check` result and when it was run
- Visual timeline or table of backup history (success / failure / skipped) over the past 30 days

### 6.3 Backup Configuration

- View and edit backup targets (local path, offsite Pi SFTP/Restic endpoint, optional B2 bucket)
- Configure backup schedule (daily incremental, weekly checkpoint, monthly snapshot — per [ops-standard.md](ops-standard.md) § 1)
- Set retention policy (snapshots to keep: daily / weekly / monthly / yearly)
- Manage Restic repository credentials (reference only — actual secrets stored in `.env`, not in the panel)
- Enable or disable individual backup targets without removing their configuration

### 6.4 On-Demand Actions

- **Trigger backup now** — run an immediate Restic backup for a selected app or the full platform
- **Trigger offsite sync** — force replication to the Pi outside the normal schedule
- **Verify backup integrity** — run `restic check` against a selected repository and display results
- **Test restore** — initiate a restore-to-temp-directory for a selected snapshot to confirm recoverability (does not affect production data)

### 6.5 Alerts & Notifications

- Offsite node offline for > threshold
- Backup job failed or skipped
- No successful offsite replication in > 48 hours
- Repository approaching disk capacity on the Pi (warning at 75%, critical at 90%)
- `restic check` returned errors
- Notification delivery: surface in control panel dashboard; future expansion to email/push/webhook

### 6.6 Future Expansion

- **B2 cloud tier management** — enable/disable optional Backblaze B2 backup, monitor usage and cost
- **Multi-node backup routing** — when additional nodes exist, show per-node backup status and configure replication targets per node
- **Restore wizard** — guided point-in-time restore from any backup target (local, offsite, B2) integrated with the system reset workflow (§ 5)
- **Backup scheduling calendar** — visual schedule of all backup jobs across the platform
- **Bandwidth throttling** — configure offsite sync bandwidth limits to avoid saturating the home network

---

## Technical Decisions (to be made)

These will become ADRs as the control panel moves to implementation.

| Decision | Options to Evaluate | Notes |
|----------|---------------------|-------|
| **Runtime / framework** | Go + htmx, Python + FastAPI, Node + React, Elixir + Phoenix | Must run as a Docker Compose service alongside the platform |
| **API integration** | Docker Engine API (socket), Authentik REST API, Uptime Kuma API, filesystem | Determine which operations can use APIs vs. exec/CLI |
| **Authentication** | Authentik OIDC (SSO with the platform) | Non-negotiable — must eat its own dog food |
| **Data storage** | SQLite (lightweight) vs. PostgreSQL (shared with Authentik) | Prefer SQLite to avoid coupling |
| **Real-time updates** | WebSocket / SSE for log streaming and status changes | Essential for live log tailing and deploy progress |
| **Hosting** | `platform/control-panel/` in the homelab repo | Follows standard platform service layout |

---

## Integration Points

```text
┌──────────────────────────────┐
│      Control Panel UI        │
│   (admin.home / panel.home)  │
└──────────┬───────────────────┘
           │
     ┌─────┼──────────────────────────────────────────┐
     │     │                                           │
     ▼     ▼           ▼          ▼           ▼        ▼
  Docker   Authentik   Uptime     Filesystem  Restic   Offsite Pi
  Engine   Admin API   Kuma API   (compose,   CLI      (Tailscale
  API                             .env, data)           + SSH/SFTP)
```

| Integration | Method | Purpose |
|-------------|--------|---------|
| Docker Engine | Unix socket (`/var/run/docker.sock`) | Container lifecycle, logs, stats, image management |
| Authentik | REST API (`/api/v3/`) | User CRUD, group management, provider/application setup |
| Uptime Kuma | API / push monitors | Health check status, create/delete monitors |
| Homepage | Config file (`services.yaml`) | Add/remove dashboard entries |
| Restic | CLI wrapper | Trigger backups, check integrity, list snapshots |
| Offsite Pi | Tailscale + SSH/SFTP | Node health, replication status, disk usage, remote commands |
| Filesystem | Direct read/write | Compose files, `.env` files, `app-contract.yaml`, docs |

---

## Security Considerations

- **Admin-only access** — gated by `homelab-admin` Authentik group; no user-facing features
- **Docker socket access** — the control panel container needs `/var/run/docker.sock` mounted; this is effectively root-equivalent — accept and document this risk
- **Destructive action gates** — multi-step confirmation for teardown, user deletion, data removal
- **Audit trail** — all actions logged with timestamp, operator identity, and outcome
- **No credential storage** — secrets are in `.env` files and Authentik; the panel reads but does not independently store credentials
- **Session management** — short-lived sessions via Authentik OIDC, no persistent API tokens stored in browser

---

## Phasing

This application does not need to ship fully-featured on day one. Build incrementally:

| Phase | Capabilities | Depends On |
|-------|-------------|------------|
| **Phase A** | Read-only dashboard: container status, host metrics, log viewer | Docker socket access only |
| **Phase B** | App lifecycle: start/stop/restart, log streaming, basic health | Docker socket + Authentik OIDC |
| **Phase C** | User management: list/create/disable users, manage groups | Authentik API integration |
| **Phase D** | App deployment: guided install, update workflow, rollback | Docker + Authentik + filesystem |
| **Phase E** | System reset: teardown wizard, backup verification | Restic CLI + full API integration |
| **Phase F** | Offsite backup management: node status, replication monitoring, on-demand actions | Tailscale + SSH to offsite Pi + Restic |

---

## Open Questions

- Should the control panel replace Dockge entirely, or complement it for advanced Compose editing?
- How much of the update workflow can be safely automated vs. requiring manual confirmation at each step?
- Should the panel manage its own state (SQLite) or remain stateless (derive everything from Docker/Authentik/filesystem)?
- Is there value in a mobile-responsive layout for quick checks from a phone, or is this strictly desktop?
- Can the panel generate and manage `app-contract.yaml` files during the install workflow?

---

## Related Documents

| Document | Relevance |
|----------|-----------|
| [ops-standard.md](ops-standard.md) | Update workflow (§ 5), testing procedures (§ 6), restart/recovery (§ 4) |
| [app-spec.md](app-spec.md) | App contract, release gates — the panel enforces these |
| [onboarding.md](onboarding.md) | User creation and enrollment flow — the panel automates these |
| [teardown.md](teardown.md) | Reset procedures — the panel exposes these as guided workflows |
| [agent-model.md](agent-model.md) | Admin agent lane — the control panel may become the agent's primary interface |
| [access-matrix.md](access-matrix.md) | Group-to-role mappings visualised in user management |
| [dependencies.md](dependencies.md) | Licensing constraints on chosen framework |
