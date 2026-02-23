# Documentation Index

Central index for project documentation, organized by audience and task.

## Start Here
- Project quick start: `README.md`
- Project manifesto: `manifesto.md`
- Open source roadmap (executive): `README.md` ("Open Source Roadmap (Executive)")
- Open source roadmap (detailed): `docs/open-source-roadmap.md`

## Reading Paths

### For Users (deploy and use)
1. `README.md`
2. `docs/bootstrap.md`
3. `docs/networking.md`
4. `docs/onboarding.md`
5. `docs/runbook.md`

### For Operators (day-2 operations)
1. `docs/ops-standard.md`
2. `docs/dr-runbook.md`
3. `docs/security.md`
4. `docs/inventory.md`
5. `docs/teardown.md`

### For Contributors (build and extend)
1. `docs/open-source-roadmap.md`
2. `docs/app-spec.md`
3. `docs/adrs/`
4. `docs/tasks/`
5. `CLAUDE.md`

## Quick Task Links
- First install prerequisites: `docs/bootstrap.md`
- Validate all compose files: `scripts/validate-compose`
- Bring up platform stack: `scripts/platform-up`
- Bring up an app: `scripts/app-up`
- Backup and restore workflows: `docs/ops-standard.md`, `docs/dr-runbook.md`
- DMZ/public services planning: `docs/dmz-public-services.md`, `docs/dmz-implementation-plan.md`

## Core Document Inventory

### Project Direction
- `manifesto.md`: Mission, principles, scope, and phased success definition.
- `docs/open-source-roadmap.md`: Detailed open source readiness plan and milestones.
- `docs/rollout-plan.md`: Platform rollout sequencing and execution notes.

### Platform Design and Architecture
- `docs/agent-model.md`: Multi-agent model and responsibilities.
- `docs/control-panel.md`: Control plane UX and management model.
- `docs/dependencies.md`: Dependency map and replacement considerations.
- `docs/networking.md`: Network topology and routing details.
- `docs/mobile-access-architecture.md`: Mobile/remote access architecture.

### Security and Operations
- `docs/security.md`: Threat model, controls, and accepted risks.
- `docs/ops-standard.md`: Standard operating procedures.
- `docs/runbook.md`: Operational runbook and common workflows.
- `docs/dr-runbook.md`: Disaster recovery procedures.
- `docs/teardown.md`: Safe teardown and reset procedures.
- `docs/access-matrix.md`: Access roles and permissions matrix.

### App Ecosystem
- `docs/app-spec.md`: App integration contract and standards.
- `docs/app-ideas.md`: Candidate apps and backlog ideas.
- `docs/authentik-oidc-integration.md`: Identity integration guidance.

### DMZ and Public Services
- `docs/dmz-public-services.md`: Public-facing services architecture.
- `docs/dmz-implementation-plan.md`: DMZ implementation details and phases.

### Onboarding and Learning
- `docs/onboarding.md`: User onboarding and account setup.
- `docs/first-install-lessons.md`: Lessons learned from first deployment.
- `docs/future-considerations.md`: Future improvements and open directions.

### Project Tracking and Tasks
- `docs/inventory.md`: Service and deployment inventory.
- `docs/nodes.md`: Host and node reference.
- `docs/tasks/`: Implementation task breakdowns.
- `docs/notes/`: Working notes and scratch planning.

## Maintenance Notes
- Keep this file updated when adding, renaming, or deprecating docs.
- Prefer linking to canonical docs here instead of duplicating guidance across files.
