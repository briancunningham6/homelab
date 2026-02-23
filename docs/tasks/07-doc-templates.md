# Task 07: Documentation Templates

## Context
Read `CLAUDE.md` for project conventions. Several documents are referenced across the project but don't exist yet. This task creates the templates so they're ready when the platform goes live.

## Objective
Create template/skeleton versions of the operational documents that will be populated during deployment.

## Output Files

```
docs/
├── inventory.md
├── access-matrix.md
├── nodes.md
├── runbook.md
└── dr-runbook.md
```

## Requirements

### docs/inventory.md
Service inventory tracking all deployed services.

```markdown
# Service Inventory

> All deployed services, ports, hostnames, and backup targets | Parent: [DESIGN.md](../DESIGN.md)

Last updated: YYYY-MM-DD

## Platform Services

| Service | Hostname | Container | Ports (internal) | Ports (host) | Image | Version | Backup Scope | Owner |
|---------|----------|-----------|-----------------|-------------|-------|---------|-------------|-------|
| Caddy | — | caddy | 80, 443 | 80, 443 | caddy | x.x.x | Config only | Brian |
| Dockge | dockge.home | dockge | 5001 | — | louislam/dockge | x.x.x | ./data (SQLite) | Brian |
| Homepage | home.home | homepage | 3000 | — | ghcr.io/gethomepage/homepage | x.x.x | ./config | Brian |
| Uptime Kuma | status.home | uptime-kuma | 3001 | — | louislam/uptime-kuma | x.x.x | ./data (SQLite) | Brian |
| Tailscale | — | tailscale | — | — | tailscale/tailscale | x.x.x | ./data | Brian |
| Authentik | login.home | authentik-server | 9000, 9443 | — | ghcr.io/goauthentik/server | x.x.x | PostgreSQL + config | Brian |

## Application Services

| Service | Hostname | Container | Ports (internal) | Ports (host) | Image | Version | Backup Scope | Owner |
|---------|----------|-----------|-----------------|-------------|-------|---------|-------------|-------|
| Immich | immich.home | immich-server | 2283 | — | ghcr.io/immich-app/immich-server | x.x.x | PostgreSQL + media library | Brian |

## Notes
- "Ports (host)" = published to the host. Blank means internal only (proxied via Caddy).
- Update this document after every deployment, update, or removal.
- Version should match the pinned image tag in compose.yml.
```

### docs/access-matrix.md
User/group to app role mappings.

```markdown
# Access Matrix

> User and group to application role mappings | Parent: [DESIGN.md](../DESIGN.md)

Last updated: YYYY-MM-DD

## Group Definitions

| Group | Description | Members |
|-------|-------------|---------|
| `homelab-admin` | Full platform administration | Brian |
| `parents` | Parent-level access across apps | Brian, [partner] |
| `kids` | Child-level access with safety restrictions | [child names] |

## Application Access

| Application | Admin Group | User Group | Read-only Group | Auth Mode |
|-------------|------------|-----------|----------------|-----------|
| Dockge | homelab-admin | — | — | Local account (no SSO) |
| Homepage | — (public to LAN) | — | — | None |
| Uptime Kuma | homelab-admin | — | — | Local account |
| Authentik | homelab-admin | — | — | Built-in admin |
| Immich | immich-admin | immich-user | — | OIDC |

## Agent Lane Mapping

| Agent Lane | Authentik Groups | Capabilities |
|------------|-----------------|-------------|
| Admin | homelab-admin | Full platform + app management |
| User (parent) | parents + app-specific user groups | Standard app access |
| Child | kids + app-specific restricted groups | Restricted access with safety policy |

## Notes
- Update this document when adding new users, groups, or applications.
- See [docs/onboarding.md](onboarding.md) for the user creation workflow.
- See [docs/agent-model.md](agent-model.md) for agent lane definitions.
```

### docs/nodes.md
Node registry for multi-node deployments.

```markdown
# Node Registry

> Hardware nodes in the homelab mesh | Parent: [DESIGN.md](../DESIGN.md)

Last updated: YYYY-MM-DD

## Active Nodes

| Hostname | Role | Hardware | OS | Tailscale IP | Services | Status |
|----------|------|----------|------|-------------|----------|--------|
| homelab-mac-mini | Control | Mac mini | macOS | 100.x.x.x | All platform + apps | Active |
| homelab-pi-dr | DR | Raspberry Pi 4/5 | Raspberry Pi OS | 100.x.x.x | Restic backup target | Planned |

## Node Roles

| Role | Description | Reference |
|------|-------------|-----------|
| Control | Identity, proxy, monitoring, management | DESIGN.md § 8 |
| App | Application hosting | DESIGN.md § 8 |
| AI | LLM inference and model storage | DESIGN.md § 8 |
| DR | Offsite backup and restore staging | DESIGN.md § 8 |

## Adding a New Node
See DESIGN.md § 8 "Adding a new node" for the procedure.
```

### docs/runbook.md
Operational change log.

```markdown
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

<!-- Add new entries above this line, newest first -->
```

### docs/dr-runbook.md
Disaster recovery procedures and drill results.

```markdown
# DR Runbook — Disaster Recovery Procedures & Drill Results

> Recovery procedures and test history | Parent: [DESIGN.md](../DESIGN.md)

## Recovery Procedure

See [ops-standard.md](ops-standard.md) § 2 for recovery objectives (RPO ≤ 24h, RTO 4–8h) and dependency order.

### Quick Reference: Recovery Order

1. Prepare replacement hardware and OS
2. Install Docker Engine + Compose
3. Restore platform manifests (compose files, configs) from backup or git
4. Restore Tailscale (join to tailnet)
5. Restore Caddy (config + certs)
6. Restore Authentik (database + config + keys) — **critical dependency**
7. Restore monitoring (Uptime Kuma, Homepage)
8. Restore app stacks (Immich, etc.)
9. Validate all services healthy
10. Run `scripts/dr-verify`

## Drill History

### Drill Template

```
## YYYY-MM-DD — DR Drill [Full / Partial]

**Scope:** [What was tested]
**Hardware:** [What hardware was used]
**Backup source:** [Local / Offsite Pi / B2]

### Steps
1. ...

### Result
- RPO achieved: [yes/no — data loss?]
- RTO achieved: [yes/no — how long?]
- Services restored: [list]
- Issues encountered: [list]

### Lessons learned
[What to improve]
```

---

## Drills

<!-- Add new drill records above this line, newest first -->
```

## Constraints
- Templates must be immediately usable — copy the entry template and fill in
- Do NOT invent fake log entries — leave the log sections empty
- Use placeholder values (YYYY-MM-DD, x.x.x, [name]) where actual values depend on deployment

## Acceptance Criteria
- [ ] All five documents created with correct structure
- [ ] `inventory.md` has pre-populated rows for all Phase 1–3 services
- [ ] `access-matrix.md` has baseline groups and all known app mappings
- [ ] `runbook.md` and `dr-runbook.md` have copy-paste entry templates
- [ ] All documents link back to parent DESIGN.md
