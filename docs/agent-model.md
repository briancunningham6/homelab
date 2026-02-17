# OpenClaw — Multi-Agent Access Model

> Agent architecture and management contract | Parent: [DESIGN.md](../DESIGN.md)

---

## Overview

OpenClaw is the AI agent layer for the homelab platform. Every person gets an agent scoped to their identity and permissions. Administrators get a separate privileged agent for platform operations.

**Current status:** Conceptual design. No implementation exists yet.

---

## 1. Agent Lanes

### User Agent Lane (default)

The standard lane for adult family members.

| Aspect | Policy |
|--------|--------|
| Workspace | Per-user isolated workspace and memory scope |
| Credentials | Per-user scoped app credentials/tokens |
| App access | Only apps/data allowed by Authentik group membership |
| System access | No unrestricted host or system administration |

### Child Agent Lane

Same isolation as user lane with additional safety restrictions.

| Aspect | Policy |
|--------|--------|
| Tools | Limited tools and external actions by default |
| Data access | Restricted to child-owned or explicitly shared resources |
| Safety | Stricter content and action safety policy |
| Approval gates | Optional parent-approval required for: share, export, delete |

### Admin Agent Lane

Full platform management scope.

| Aspect | Policy |
|--------|--------|
| Scope | Install, update, configure, backup, DR operations |
| Tools | Access to infrastructure tools and system operations |
| Safeguard | Explicit confirmation required for destructive actions |

---

## 2. Separation Requirements

Each user gets isolated:
- Workspace and file storage
- Memory / conversation context
- Credentials and API tokens
- Scheduled jobs and automations
- Activity logs

**Principles:**
- Enforce least privilege in every lane.
- No cross-user data access unless explicitly shared by policy.
- Agent capabilities are derived from Authentik group membership.

---

## 3. Identity & Policy Integration

Authentik is the single source of truth for users, groups, and therefore agent capabilities.

### Group → Lane mapping

| Group | Agent Lane | Capabilities |
|-------|-----------|-------------|
| `homelab-admin` | Admin | Full platform management |
| `parents` | User | Standard app access |
| `kids` | Child | Restricted access with safety policy |
| App-specific groups (e.g., `immich-user`) | — | Grants access to specific apps within the user's lane |

---

## 4. App Integration Requirements

Every new app must include agent-related configuration:

1. **Auth mapping** — OIDC/SAML/LDAP or proxy-auth fallback.
2. **Role-to-group mapping** — documented in `docs/access-matrix.md`.
3. **Data scope rules** — what each lane (user/child/admin) can access.
4. **Agent scopes** — defined in `app-contract.yaml` (see [app-spec.md](app-spec.md)).

Example from `app-contract.yaml`:
```yaml
agentScopes:
  user: [read, write]
  child: [read]
  admin: [read, write, delete, configure]
```

---

## 5. OpenClaw Management Contract

When operating against the homelab, OpenClaw agents must:

1. Operate primarily within `~/homelab/**`.
2. **Ask before destructive actions** — delete, reset, migration.
3. Follow the update workflow: pre-check → backup → update → verify → report.
4. Log operational changes in `docs/runbook.md`.
5. Log DR/restore outcomes in `docs/dr-runbook.md`.

---

## 6. Operational Controls

| Control | Detail |
|---------|--------|
| Audit logging | All admin-lane infrastructure actions are logged |
| Break-glass | Emergency admin account maintained and documented securely |
| Revocation | Access revocation is immediate via Authentik group/user disable |
| Scope enforcement | Agents cannot escalate beyond their lane's permissions |

---

## 7. Open Questions

These will be resolved as OpenClaw moves from concept to implementation:

- [ ] Agent runtime — what framework/runtime hosts the agents?
- [ ] Memory model — how is per-user conversation context stored and isolated?
- [ ] Tool registry — how are tools/actions registered and scoped per lane?
- [ ] Parent approval flow — how do child-lane approval gates work in practice?
- [ ] Credential injection — how do per-user app tokens flow to agents securely?
- [ ] Multi-node agent routing — how do agents talk to apps on different nodes?
