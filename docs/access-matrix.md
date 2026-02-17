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
