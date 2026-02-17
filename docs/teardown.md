# Teardown & Clean Reinstall

> Controlled destruction and rebuild procedures | Parent: [DESIGN.md](../DESIGN.md)

This document covers the scenario where the admin intentionally wants to destroy the existing homelab installation — partially or fully — and rebuild from scratch. This is **not** disaster recovery (see [ops-standard.md](ops-standard.md) §2). This is a controlled, planned operation where the admin has full access and wants a clean slate.

---

## When to Use This

- The platform has drifted from spec and a clean start is faster than fixing in place
- A major architecture change makes migration impractical (e.g., changing identity provider, switching OS)
- Testing the full rebuild process as a DR preparedness exercise
- Moving the homelab to new hardware

---

## 1. Pre-Teardown Checklist

**Nothing is destroyed until every item on this checklist is confirmed.**

### 1.1 Backup verification

| Check | Detail | Done |
|-------|--------|------|
| Fresh backup exists | Run a full backup of all services immediately before teardown — do not rely on the last scheduled backup | [ ] |
| Backup is offsite | Confirm the fresh backup has replicated to the offsite target (Pi or B2). Do not rely solely on local backups that will be destroyed | [ ] |
| Backup is restorable | Restore at least one critical dataset (Authentik DB, one app DB) to a temporary location and verify integrity | [ ] |
| Restic repo password available | Confirm you have the repo password accessible **outside** the system being destroyed (password manager, sealed envelope) | [ ] |

### 1.2 Credential and secret inventory

Before teardown, confirm you have access to the following **independent of the homelab**:

| Secret | Where it should be | Verified |
|--------|--------------------|----------|
| Restic repository password(s) | Password manager + sealed offline copy | [ ] |
| `akadmin` break-glass credentials | Password manager + sealed offline copy | [ ] |
| Authentik signing/encryption keys | In backup; verify you can extract them | [ ] |
| Tailscale auth key or account access | Tailscale admin console (cloud) | [ ] |
| GitHub/source repo access | GitHub account / SSH keys | [ ] |
| DNS / domain credentials (if any) | Password manager | [ ] |
| Backblaze B2 keys (if used) | Password manager | [ ] |
| Any app-specific API keys or tokens | Password manager | [ ] |

### 1.3 Data preservation decisions

Explicitly decide what to **keep** vs. **discard**. This prevents regret.

| Data category | Keep or discard | Notes |
|---------------|----------------|-------|
| User media (photos, files) | Usually **keep** | Verified in offsite backup |
| App databases (Immich, etc.) | Usually **keep** | In backup |
| Authentik DB + config | Usually **keep** | Restoring preserves all users, groups, SSO configs |
| Compose files / platform config | **Keep** | In git repo + backup |
| Operational docs | **Keep** | In git repo |
| Container images | **Discard** | Re-pulled on reinstall |
| Container volumes (temp/cache) | **Discard** | Regenerated on startup |
| AI model files | **Discard** | Re-pulled from registries; large, not worth backing up |
| Logs | **Decide** | Archive if needed for audit; usually discard |

### 1.4 Notify affected users

- Inform all family members of planned downtime window.
- Set expectations: services will be unavailable, logins will stop working temporarily.
- If kids use the system, coordinate timing.

---

## 2. Teardown Scope

Choose the scope before proceeding. Each level includes everything above it.

### Level 1: App-only teardown
Destroy and reinstall specific application stacks. Platform and identity remain intact.

**Use when:** A single app is broken or needs a fresh start.

### Level 2: Platform teardown (keep identity)
Destroy all services but preserve the Authentik database and configuration for restore. Users, groups, and SSO mappings survive.

**Use when:** Platform drift or configuration mess, but user accounts and access policies are still correct.

### Level 3: Full teardown
Destroy everything including identity. Complete rebuild from backups or from scratch.

**Use when:** Changing fundamental architecture, moving to new hardware, or intentional fresh start.

---

## 3. Shutdown Sequence

Services must be stopped in **reverse dependency order** to avoid corruption.

### Step 1: Stop applications first
```bash
# Stop each app stack
cd ~/homelab/apps/<app-name> && docker compose down
# Repeat for all apps
```

### Step 2: Stop AI services (if running)
```bash
cd ~/homelab/ai/ollama && docker compose down
cd ~/homelab/ai/open-webui && docker compose down
```

### Step 3: Stop platform services (reverse boot order)
```bash
# Monitoring and dashboard last-to-start = first-to-stop
cd ~/homelab/platform/uptime-kuma && docker compose down
cd ~/homelab/platform/homepage && docker compose down

# Identity
cd ~/homelab/platform/authentik && docker compose down

# Reverse proxy
cd ~/homelab/platform/caddy && docker compose down

# Stack management
cd ~/homelab/platform/dockge && docker compose down

# Tailscale — stop last (you may need remote access during teardown)
cd ~/homelab/platform/tailscale && docker compose down
```

### Step 4: Verify all containers are stopped
```bash
docker ps -a
# Should return empty or only unrelated containers
```

---

## 4. Data Destruction

**Only proceed when the pre-teardown checklist (§1) is fully complete.**

### 4.1 Remove Docker resources

```bash
# Remove all stopped containers
docker container prune -f

# Remove all volumes (THIS DESTROYS APP DATA)
docker volume prune -a -f

# Remove all unused networks
docker network prune -f

# Remove all unused images (frees disk space)
docker image prune -a -f
```

### 4.2 Remove homelab directory (Level 2–3 only)

```bash
# DANGER: This removes all compose files, configs, and local data
# Ensure git repo and backups are confirmed before this step
rm -rf ~/homelab
```

### 4.3 Clean external storage (if applicable)

If external storage (`/Volumes/HomelabData/`) should also be wiped:

```bash
# Only if you want a fully clean external disk
rm -rf /Volumes/HomelabData/immich-library
rm -rf /Volumes/HomelabData/backups    # ONLY if offsite backup is confirmed
rm -rf /Volumes/HomelabData/models
```

> **Warning:** Do not delete `/Volumes/HomelabData/backups` unless you have confirmed the offsite copy is complete and restorable. Destroying both your local and only backup copy is unrecoverable.

### 4.4 Clean macOS system-level config (Level 3 only)

```bash
# Remove launchd agents (startup orchestrator, OpenClaw)
rm ~/Library/LaunchAgents/com.homelab.*.plist

# Unload if currently loaded
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.homelab.*.plist 2>/dev/null
```

---

## 5. External Service Cleanup

These services exist outside the homelab host and may need manual cleanup.

| Service | Cleanup action | How |
|---------|---------------|-----|
| **Tailscale** | Remove the old Mac mini device from your tailnet (or reuse it) | [Tailscale admin console](https://login.tailscale.com/admin/machines) |
| **Tailscale** | If the offsite Pi is being reset too, remove that device | Same admin console |
| **Backblaze B2** | Decide: keep existing backup bucket (for restore) or delete it | B2 dashboard |
| **GitHub** | No action needed — the repo is the source of truth for rebuilding | — |
| **DNS** | If using any custom DNS records, review and clean up | DNS provider dashboard |
| **Docker Hub** | No action needed — images are public | — |

---

## 6. Post-Teardown Verification

Confirm the system is actually clean before rebuilding.

| Check | Command / Action | Expected |
|-------|-----------------|----------|
| No Docker containers | `docker ps -a` | Empty |
| No Docker volumes | `docker volume ls` | Empty (or only unrelated) |
| No homelab directory | `ls ~/homelab` | "No such file or directory" |
| No launchd agents | `ls ~/Library/LaunchAgents/com.homelab.*` | "No such file" |
| External storage clean (if wiped) | `ls /Volumes/HomelabData/` | Empty or not mounted |
| Tailscale devices cleaned | Check admin console | Old devices removed |
| Backups accessible | Test Restic access to offsite repo | `restic snapshots` returns data |

---

## 7. Rebuild Path

After teardown, follow one of these paths:

### Option A: Fresh install from documentation
1. Clone the homelab repo: `git clone <repo-url> ~/homelab`
2. Follow [rollout-plan.md](rollout-plan.md) from Phase 1
3. Set up Authentik fresh with new users/groups (or restore from backup per Option B)
4. Deploy apps per the rollout phases
5. Run a full health check

### Option B: Restore from backup
1. Clone the homelab repo: `git clone <repo-url> ~/homelab`
2. Follow [ops-standard.md](ops-standard.md) §2 (Disaster Recovery) for the recovery dependency order
3. Restore Authentik DB and keys first — this preserves all users, groups, and SSO configs
4. Restore app databases and media
5. Verify user logins and RBAC mappings
6. Run a full health check

### Which option to choose?

| Scenario | Recommended path |
|----------|-----------------|
| Clean slate, don't want old config baggage | Option A |
| Want to preserve users, groups, app data | Option B |
| Moving to new hardware | Option B (restore onto new host) |
| Testing DR readiness | Option B (this IS the drill) |

---

## 8. Teardown Runbook Template

Copy and fill in when performing a teardown. Record in `docs/runbook.md`.

```markdown
### Teardown Record — [DATE]

**Reason:** [why are we tearing down?]
**Scope:** Level [1/2/3]
**Operator:** [name]

#### Pre-teardown
- [ ] Fresh backup completed at [timestamp]
- [ ] Offsite replication confirmed
- [ ] Restore test passed for: [list datasets tested]
- [ ] All credentials verified outside the system
- [ ] Data preservation decisions documented
- [ ] Users notified

#### Teardown
- [ ] Shutdown sequence completed
- [ ] Docker resources removed
- [ ] Homelab directory removed (if Level 2–3)
- [ ] External storage cleaned (if applicable)
- [ ] macOS config cleaned (if Level 3)
- [ ] External services cleaned (Tailscale, B2, etc.)

#### Post-teardown
- [ ] Clean state verified
- [ ] Backup accessibility confirmed from outside the system

#### Rebuild
- [ ] Rebuild path chosen: [A/B]
- [ ] Rebuild completed at [timestamp]
- [ ] Health checks passing
- [ ] User access verified
- [ ] Documented in runbook
```

---

## 9. Partial Teardown: Single App Reset

For Level 1 (app-only), the procedure is simpler:

```bash
# 1. Stop the app
cd ~/homelab/apps/<app-name>
docker compose down

# 2. Backup app data (if not already backed up)
# Use the app-backup script or manual restic snapshot

# 3. Remove app data
rm -rf data/

# 4. Optionally remove and re-pull the image
docker compose pull

# 5. Recreate
docker compose up -d

# 6. Restore data from backup if needed
# Use the app-restore script

# 7. Verify health check and SSO
# 8. Update runbook
```

This does **not** require stopping other services or cleaning up external state.
