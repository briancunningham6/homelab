# FAQ

## General

### What is this project?
A self-hosted homelab platform focused on user control, repeatable operations,
and progressive reduction of third-party dependencies.

### Who is this for right now?
Primary target is a solo power user. Family-admin usability is a planned
direction, but current support assumes moderate technical comfort.

### Is this production-ready?
Not yet. The project is aspirational and experimental. Current focus is fast
iteration and learning with a clear path toward stronger reliability and
security.

## Installation and Setup

### What environment is currently supported?
macOS-first baseline on a Mac mini M4, with a Raspberry Pi 5 in secondary roles
(backup workflows and DMZ blog hosting).

### How do I validate my compose files before starting?
Run:

```bash
HOMELAB_DIR=$(pwd) ./scripts/validate-compose
```

### I started services but something is not reachable. What should I check first?
1. `docker compose ps` in the affected stack directory
2. service logs via `docker compose logs --tail=50`
3. reverse proxy and identity stack health
4. hostname/routing entries documented in platform/app README files

## Identity and Access

### How is authentication handled?
Centralized identity through Authentik with OIDC integrations for apps that
support SSO.

### Do all apps support SSO out of the box?
No. Some require app-specific integration work. Check app docs and
`docs/authentik-oidc-integration.md`.

## Backups and Recovery

### Are backups optional?
No. Backup/restore capability is a core part of the platform operating model.

### How do I verify restores actually work?
Follow the disaster recovery process in `docs/dr-runbook.md` and perform restore
drills, not just backup creation.

## Security

### How do I report a security vulnerability?
Use the private process in `.github/SECURITY.md`. Do not post security issues
publicly.

### Are there accepted security limitations today?
Yes. See `docs/security.md` for current controls, known limitations, and risk
tradeoffs.

## Open Source and Contribution

### How can I contribute?
Start with `CONTRIBUTING.md`, then open an issue/PR using the provided
templates.

### Why are some roadmap items marked complete while others are still manual?
The roadmap is phased. Governance and CI foundations are prioritized before
onboarding UX and marketplace features.
