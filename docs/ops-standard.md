# Operational Standards

> Backup, disaster recovery, security, and restart/recovery | Parent: [DESIGN.md](../DESIGN.md)

---

## 1. Backup Standard (3-2-1 Model)

### Strategy
- **3** copies of data
- **2** locations/media types (local + offsite)
- **1** offsite copy minimum

### Targets

| Target | Location | Purpose |
|--------|----------|---------|
| Local | Mac mini | Fast restore |
| Offsite primary | Relative's Pi + external HDD (via Tailscale) | Geographic separation |
| Offsite secondary | Backblaze B2 (optional) | Cloud redundancy |

### Tooling
Restic with client-side encryption before transfer.

### Minimum backup scope

| Category | What's included |
|----------|----------------|
| Platform manifests | All `compose.yml`, `.env`, reverse proxy configs, dashboard/monitoring configs |
| Identity core | Authentik database, configuration exports, signing/encryption keys |
| App state | App databases (Immich/Postgres, etc.), media/content libraries, app config folders |
| Operations docs | `inventory.md`, `nodes.md`, `access-matrix.md`, `runbook.md`, `dr-runbook.md` |
| Secrets | Backup repo keys/passwords, API tokens, break-glass credentials (stored outside primary site) |
| AI | Workflows and configs (model weights optional — can re-pull) |

### Schedule

| Frequency | Type | Retention |
|-----------|------|-----------|
| Daily | Incremental | 14 snapshots |
| Weekly | Checkpoint | 8 snapshots |
| Monthly | Full snapshot | 6 snapshots |
| Yearly | Archive | 1 snapshot |

---

## 2. Disaster Recovery

### Recovery objectives

| Metric | Target |
|--------|--------|
| **RPO** | ≤ 24 hours |
| **RTO** | Core platform same day (4–8 hours); full media restore may take longer |

### Recovery dependency order

Recovery **must** follow this sequence:

1. Prepare replacement hardware and OS.
2. Restore baseline connectivity (network + Tailscale).
3. Restore homelab manifests and secrets.
4. Restore identity plane first (Authentik + required keys).
5. Restore control plane (Caddy, Homepage, Uptime Kuma, OpenClaw).
6. Restore application databases and persistent data.
7. Start app stacks and run health checks.
8. Validate user logins, RBAC/group mappings, and critical user workflows.

### Rebuild readiness requirements
- Backups are encrypted and replicated offsite.
- Restore instructions are versioned and current.
- Required credentials are available via emergency access process.
- Restore process is executable by a second trusted operator, not only the owner.

### DR testing (non-negotiable)
- **Quarterly** bare-metal restore drills (or equivalent staged simulation).
- Record pass/fail, elapsed time, data loss observed, and blockers in `docs/dr-runbook.md`.
- Any failed drill creates mandatory remediation tasks before the next cycle.

---

## 3. Security Baseline

| # | Control |
|---|---------|
| 1 | Strong unique credentials stored in a password manager |
| 2 | MFA enabled for admin and parent accounts |
| 3 | Tailscale-only remote administration |
| 4 | No anonymous public shares by default |
| 5 | Monthly patch/update window for macOS + containers |
| 6 | Quarterly exposure review (ports, apps, stale accounts, old tokens) |
| 7 | Backup key escrow process (owner + emergency sealed copy) |

---

## 4. Restart & Recovery Standard

**Goal:** After host restart, services return online automatically with no routine manual intervention.

### Auto-start layers

| Layer | Mechanism |
|-------|-----------|
| Host (macOS) | `launchd` with `RunAtLoad` + `KeepAlive` for OpenClaw and startup orchestrator |
| Containers | All services use `restart: unless-stopped` |

### Deterministic boot sequence

A startup orchestrator script runs on boot in this order:

1. Wait for network readiness.
2. Wait for required mounts (especially external storage paths).
3. Start platform core: Tailscale → Caddy → Authentik → monitoring/dashboard.
4. Start application stacks (Immich, custom apps).
5. Execute health checks and record status.

### External storage guardrails
- If an app depends on an external mount and the mount is missing, **do not start that app in write mode**.
- Raise an alert and mark the service degraded rather than risking data corruption.

### Post-boot health policy
- Run health checks for every platform and app service endpoint.
- If unhealthy: retry start, then targeted restart.
- If still unhealthy after retries: alert user with clear remediation notes.

### Recovery targets

| Metric | Target |
|--------|--------|
| Reboot recovery time | ~2–5 minutes |
| User experience | Dashboard shows service state without CLI |

### Reliability validation
- Planned reboot recovery test at least **monthly**.
- Log startup outcomes and incidents in `docs/runbook.md`.
- Maintain a one-command recovery helper in `scripts/` for common failures.
