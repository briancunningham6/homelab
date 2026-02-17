# ADR-002: Authentik for Identity and Access Management

## Status

**Accepted**

## Date

2026-02-17

## Context

The platform needs centralised identity management for a family of users with different access levels (admin, parent, child). Apps should use SSO rather than per-app credentials. The solution must support OIDC at minimum, with SAML and LDAP as fallbacks for apps that don't support OIDC.

## Decision

Use **Authentik** as the central identity provider for all homelab services.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| Authelia | Lightweight, simple config, low resource usage | Limited to proxy-auth and basic OIDC; no full IdP features (SAML, LDAP, user self-service) | Insufficient for the multi-protocol, multi-group model needed |
| Keycloak | Enterprise-grade, full protocol support | Heavy resource usage (Java), complex administration, overkill for family scale | Too resource-intensive for a shared Mac mini |
| No centralised identity | Zero overhead | Per-app passwords, no SSO, no RBAC, poor UX | Defeats the identity-first principle |

## Consequences

- **Positive:** Full OIDC, SAML, and LDAP support covers virtually all self-hosted apps.
- **Positive:** Built-in user self-service (password reset, profile management) improves family UX.
- **Positive:** Group-based policies map cleanly to the RBAC model (homelab-admin, parents, kids, app-specific groups).
- **Positive:** Customisable branding makes it feel like a family platform, not a corporate login.
- **Trade-off:** Authentik is more resource-intensive than Authelia (Python + PostgreSQL + Redis). Acceptable given the Mac mini's specs.
- **Trade-off:** Authentik becomes a critical dependency — if it's down, SSO-dependent apps are inaccessible. Mitigated by break-glass admin accounts per app.

## References

- [Authentik documentation](https://goauthentik.io/docs/)
- [Authentik vs Authelia comparison](https://goauthentik.io/docs/)
