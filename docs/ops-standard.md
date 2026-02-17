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
---

## 5. Application Update Standard

**Goal:** Update applications safely with minimal downtime and a clear rollback path.

### Principles

- **Never run `latest`** — all images use pinned version tags (e.g., `immich:v1.95.0`).
- **Every update is reversible** — the previous image tag and a pre-update backup make rollback straightforward.
- **Updates are deliberate, not automatic** — no watchtower or auto-pull. The admin decides when to update.
- **One app at a time** — never batch-update multiple apps in a single session.

### Update workflow

Follow this sequence for every app update:

#### Step 1: Check for updates

Review what's available and what changed:

```bash
# Check upstream release notes / changelog before updating
# For off-the-shelf apps, check the project's GitHub releases page
```

Read the changelog. Look for:
- Breaking changes or required migration steps
- Database schema changes
- Config file format changes
- Minimum dependency version bumps (Postgres, Redis, etc.)

#### Step 2: Record current state

Before touching anything, note what's running:

```bash
cd ~/homelab/apps/<app-name>

# Record current image tag from compose.yml
grep 'image:' compose.yml

# Confirm the app is healthy
curl -s http://localhost:<port>/health
```

#### Step 3: Pre-update backup

Run a backup of the app's data **immediately before the update** — do not rely on the last scheduled backup:

```bash
# Use the app-backup script or manual restic snapshot
./scripts/app-backup <app-name>
```

Verify the backup completed successfully before continuing.

#### Step 4: Update the image tag

Edit `compose.yml` to set the new version:

```yaml
# Before
image: ghcr.io/immich-app/immich-server:v1.95.0

# After
image: ghcr.io/immich-app/immich-server:v1.96.0
```

#### Step 5: Pull, stop, and restart

```bash
# Pull the new image first (reduces downtime)
docker compose pull

# Stop and recreate with the new image
docker compose up -d
```

#### Step 6: Verify

```bash
# Check containers are running
docker compose ps

# Check health endpoint
curl -s http://localhost:<port>/health

# Check logs for errors
docker compose logs --tail=50

# Verify in Uptime Kuma — monitor should return to green
```

Test key user workflows (login via SSO, core app functions).

#### Step 7: Record the update

Log the update in `docs/runbook.md`:

```markdown
### Update — <app-name> — [DATE]
- **From:** v1.95.0
- **To:** v1.96.0
- **Reason:** Security patch / new features / bug fix
- **Backup:** Completed at [timestamp]
- **Result:** Healthy / Issues noted
- **Notes:** Any migration steps performed or observations
```

### Rollback procedure

If the update causes problems, roll back immediately:

```bash
cd ~/homelab/apps/<app-name>

# 1. Stop the broken version
docker compose down

# 2. Revert compose.yml to the previous image tag
# Edit image: line back to the old version

# 3. Restore data from the pre-update backup (if schema changed)
./scripts/app-restore <app-name>

# 4. Start the previous version
docker compose up -d

# 5. Verify health
docker compose ps
curl -s http://localhost:<port>/health
```

Record the rollback and the reason in `docs/runbook.md`.

### Platform services

Platform components (Caddy, Authentik, Uptime Kuma, Homepage, Dockge) follow the same workflow but with extra caution:

| Service | Extra considerations |
|---------|---------------------|
| **Authentik** | Critical path — if Authentik breaks, SSO is down for all apps. Update during low-usage window. Test login flow immediately after. |
| **Caddy** | Routing affects all services. Validate all `*.home` hostnames resolve after update. |
| **Uptime Kuma** | If monitoring is down during update, you lose visibility. Update quickly and verify. |
| **Dockge** | UI-only — low risk, but verify stack management works after. |

### Scheduling

| Window | What to update |
|--------|----------------|
| **Monthly** | Security patches and minor version bumps for all apps and platform services |
| **As needed** | Critical security fixes (CVEs) — apply immediately, don't wait for the window |
| **Quarterly** | Major version upgrades (review breaking changes carefully) |

Schedule updates outside peak usage times. For the Mac mini, avoid times when Minecraft or heavy family use is expected (see [mac-mini notes](notes/mac-mini.md)).

### Dependency updates

Some apps depend on shared services (e.g., PostgreSQL, Redis). When updating these:

1. Check **all apps** that use the shared service for compatibility with the new version.
2. Back up **all dependent apps** before updating the shared service.
3. Update the shared service first, then verify each dependent app.
4. If any app is incompatible, roll back the shared service and defer the update.

### What NOT to do

- Do not run `docker compose pull && docker compose up -d` without checking the changelog first.
- Do not enable automatic image updates (Watchtower, Diun auto-pull, etc.).
- Do not update multiple apps at once — if something breaks, you won't know which update caused it.
- Do not skip the pre-update backup — "it's just a minor version" is how data gets lost.
- Do not update Authentik and an app in the same session — update and verify Authentik separately.

---

## 6. Testing and Validation Standard

**Goal:** Validate that applications deploy correctly, integrate with the platform, and remain healthy under production load — before they affect users.

### Test environment setup

#### Option A: Dedicated test host (preferred, when hardware available)

A separate machine (Linux VM, spare hardware, or future app node) that mirrors the production homelab stack:

```text
Test environment setup:

1. Clone the main homelab repo to the test node
2. Stand up parallel compose stacks:
   - platform-test/ (Caddy, Authentik, Uptime Kuma, etc.)
   - apps/test-<app-name>/
3. Use test subdomains (e.g., test-<app>.local, login-test.local)
4. Isolate network from production (separate Docker network or VLAN)
5. Use test data, not production backups
```

**Advantages:**
- No risk to production
- Can test multiple deployments in parallel
- Can test hardware/failover scenarios
- Can leave it running continuously for smoke testing

**Disadvantages:**
- Requires extra hardware or VM capacity
- Ongoing maintenance burden

#### Option B: Parallel compose stacks on production host (lighter alternative)

Run test stacks alongside production on the same host, isolated by Docker networks:

```bash
# Production stacks use default bridge network
cd ~/homelab/platform/authentik && docker compose up -d

# Test stacks use isolated networks
cd ~/homelab/platform-test/authentik && docker compose -p test up -d

# Separate ports to avoid conflicts
# prod: localhost:9000, test: localhost:9001
```

**Advantages:**
- No extra hardware needed
- Quick to spin up and tear down
- Can run before production deployments

**Disadvantages:**
- Shares resources with production (disk, memory)
- Requires disciplined cleanup to avoid clutter

### Application deployment testing workflow

For every new or updated application, follow this testing sequence **before** deploying to production:

#### Step 1: Test compose file syntax

```bash
cd ~/homelab/apps/test-<app-name>
docker compose config > /dev/null && echo "Compose file valid"
```

Catches YAML errors early.

#### Step 2: Build or pull image

```bash
docker compose pull
# Or if custom Dockerfile:
docker compose build
```

Verify the image exists and downloads/builds without error.

#### Step 3: Start in test environment

```bash
docker compose up -d
sleep 10  # Wait for service to initialize
docker compose logs --tail=50  # Check for startup errors
```

Monitor for:
- Container starts and stays running
- No crash loops (exit code 0 in logs)
- Secrets and env vars properly injected

#### Step 4: Health check validation

```bash
# Check the app's health endpoint
curl -v http://localhost:<test-port>/health

# Check Uptime Kuma integration (if applicable)
# Monitor the test health check in Uptime Kuma for pass/fail
```

Expected: HTTP 200 or equivalent healthy response.

#### Step 5: SSO integration test

If the app uses Authentik:

```bash
# 1. Visit the test app URL (e.g., http://test-immich.local/)
# 2. Redirected to test Authentik login
# 3. Log in with test user in appropriate group
# 4. Redirected back to app with authenticated session
# 5. Verify user's group membership appears in app role/permissions
```

Test at least:
- Admin user login and access
- Standard user login and access
- Child user (if applicable) login with restrictions

#### Step 6: Backup/restore test (for data-bearing apps)

```bash
# 1. Create initial test data (upload a file, create a user, etc.)
# 2. Run a backup of the test app
# 3. Simulate failure: delete or corrupt test data
# 4. Restore from the backup
# 5. Verify all test data returned to the state before corruption
```

Catches backup incompleteness before you need it in production.

#### Step 7: Load/stress test (optional, for resource-heavy apps)

For apps expected to handle concurrent users or heavy operations (Immich with large photo library, AI inference):

```bash
# Light load test (example: Immich photo re-indexing)
# Monitor CPU, RAM, disk I/O during the test
# Verify the app completes without crashing or hanging

# Tools: Apache JMeter (load testing), Docker stats (resource monitoring)
docker stats <container-id>
```

Helps identify resource limits before production surprise.

#### Step 8: Teardown and cleanup

```bash
cd ~/homelab/apps/test-<app-name>
docker compose down
docker volume rm test-<app-name>_<volume-name>  # Clean up test data volumes
```

Complete cleanup prevents leftover test containers/volumes from accumulating.

### Validation checklist

Copy and fill in for each deployment. Record in `docs/runbook.md`:

```markdown
### Deployment Test — <app-name> — [DATE]

**App version tested:** [version]
**Deployment target:** Test environment [A/B]

- [ ] 1. Compose syntax valid
- [ ] 2. Image pulled/built successfully
- [ ] 3. Container starts and stays running
- [ ] 4. Health endpoint responds 200 OK
- [ ] 5. Authentik SSO flow works (admin user login)
- [ ] 6. Authentik SSO flow works (standard user login)
- [ ] 7. Group-based role mapping verified
- [ ] 8. Backup created and restore test passed
- [ ] 9. Load test passed (if applicable) — notes: [resource usage]
- [ ] 10. All test data cleaned up

**Result:** Ready for production / BLOCKED with issues:
- [If blocked: describe the issue and blocker]

**Approval:** [your name/date]
```

### Automated testing via CI/CD

For future (when the platform matures), consider automating tests:

| Tool | Purpose |
|------|---------|
| **GitHub Actions** (or Gitea CI) | Run tests on pull requests — validate Compose files, build Docker images, run linters |
| **Shell script test harness** | Local wrapper script that runs the full 8-step test sequence, reports pass/fail |
| **Compose extension hooks** | Use Docker Compose hooks (when available) to run health checks automatically after compose up |

**Starter CI workflow:** On each PR to main, run `docker compose config`, lint YAML, build custom images, and validate app-contract.yaml.

### Test data management

Test environments should never use production data:

| Scenario | Data source |
|----------|-------------|
| **New app** | Synthetic test data (sample files, dummy user accounts) |
| **Major app version upgrade** | Restore from a backup (that's NOT the current production backup) — ideally a 1-week-old backup to test migration without current production state |
| **DR drill simulator** | Use a copy of production backup, but in a completely isolated test environment |

**Retention:** Test backups older than 7 days can be deleted. Keep 1–2 weeks of test snapshots to simulate real restore scenarios.

### Post-deployment validation (production smoke test)

After deploying an app to production:

1. **Health monitoring:** Let Uptime Kuma monitor for 24 hours. Check for any intermittent failures.
2. **User acceptance:** Have a family member test the app's key workflows.
3. **Log review:** Check app logs daily for 3–5 days. Look for errors or warnings.
4. **Dashboard visibility:** Verify the app appears healthy on the Homepage dashboard.

If any issue surfaces, execute the rollback procedure from [§5: Application Update Standard](#5-application-update-standard).

### What to test before each major rollout

| Scenario | Test frequency |
|----------|----------------|
| **New app deployment** | Full 8-step sequence, before production |
| **app version update** | Full 8-step sequence + backup/restore, before production |
| **Platform service update** (Authentik, Caddy) | Full sequence + cross-app SSO verification, before production |
| **Major OS or Docker version change** | All platform services deployed in test env, verify boot sequence and recovery |
| **Disaster recovery drill** | Quarterly — full 8-step sequence plus multi-app restore from offsite backup |

---

## Testing environment best practices

| Practice | Why |
|----------|-----|
| **Isolate test from production** | A test container failure should never affect production services |
| **Use disposable test data** | Never restore actual user data to test — use synthetic or dummy data |
| **Automate repetitive checks** | Write a shell script for the 8-step sequence; run it every deployment |
| **Document failures and fixes** | If a test fails, record why and how you fixed it — informs future tests |
| **Clean up after every test** | Lingering test containers/volumes make the next test less reliable |
| **Test in an order** | Identity → Platform → Applications (dependent services first) |
