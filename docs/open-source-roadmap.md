# Open Source Readiness Roadmap

This document outlines what needs to happen before the homelab project can become a viable open source project that others can use and contribute to.

This is the detailed operational roadmap. For a concise executive summary, see `README.md` ("Open Source Roadmap (Executive)").

**Last updated**: 2026-02-23

---

## Current State Assessment

### Strengths

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Documentation** | Excellent | 27+ markdown docs, 15+ service READMEs, clear cross-referencing |
| **Architecture Decisions** | Strong | 5 ADRs documenting key technology choices |
| **Operational Scripts** | Strong | 26 scripts covering lifecycle, backup, restore, validation |
| **Security Documentation** | Strong | 22K security.md with threat model, controls, accepted risks |
| **Deployment Patterns** | Excellent | Consistent Docker Compose structure across all services |
| **Code Examples** | Strong | 7+ complete app deployments as reference implementations |

### Gaps

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Legal/Governance** | Partial | LICENSE exists (MIT); CODE_OF_CONDUCT, CONTRIBUTING, and contributor workflow docs still missing |
| **Testing** | Weak | No automated tests, no CI/CD pipeline |
| **Onboarding** | Partial | Good docs but no interactive setup wizard |
| **App Management** | Manual | No unified UI for deploying community apps |

---

## Open Source Launch Gate (Go/No-Go)

Public launch should happen only when all of the following are true:

- Legal baseline is complete: `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, issue templates, PR template.
- Security baseline is complete: `.github/SECURITY.md`, disclosure SLA, documented secrets handling, and threat model updated for public contributions.
- CI baseline is enforced on pull requests: compose validation, YAML/shell/markdown linting, link checking, and security scans.
- Support boundaries are documented: target operator profile, compatibility matrix, and support policy.
- Release process exists: `CHANGELOG.md`, versioning policy, release checklist, and rollback notes for breaking changes.

---

## Priority Execution Order

Execution order for open-source readiness:

1. Legal & Governance
2. Security Baseline
3. CI and Testing Baseline
4. Documentation Coherence and Support Policy
5. Interactive Onboarding
6. App Ecosystem
7. Community Growth

This order intentionally prioritizes trust, safety, and maintainability before UX expansion.

---

## Priority 1: Legal & Governance (Blocking)

These are **required** before any public release.

### 1.1 LICENSE File

**Status**: Completed (`MIT License` present at repository root).

**Options**:
| License | Best For | Considerations |
|---------|----------|----------------|
| **MIT** | Maximum adoption | Permissive, allows proprietary use |
| **Apache 2.0** | Enterprise adoption | Includes patent grant, contributor agreement |
| **AGPL-3.0** | Ensuring openness | Requires derivative works to be open source |

**Recommendation**: MIT or Apache 2.0 for broad adoption. AGPL if you want to ensure all modifications remain open.

**Action**: Keep MIT unless project goals materially change.

### 1.2 Code of Conduct

**Why**: Sets expectations for community behavior. Required for healthy open source communities.

**Recommendation**: Adopt the [Contributor Covenant](https://www.contributor-covenant.org/), the industry standard.

**Action**: Add `CODE_OF_CONDUCT.md` to repository root.

### 1.3 Contributing Guidelines

**Why**: Without clear contribution guidelines, potential contributors don't know how to help.

**Must include**:
- How to set up a development environment
- How to submit issues (bug reports, feature requests)
- How to submit pull requests
- Code review expectations
- Commit message conventions
- What makes a good contribution

**Action**: Add `CONTRIBUTING.md` to repository root.

### 1.4 Issue & PR Templates

**Why**: Structured templates ensure contributors provide necessary information.

**Action**: Create `.github/` directory with:
```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   ├── feature_request.md
│   └── app_request.md
├── PULL_REQUEST_TEMPLATE.md
└── SECURITY.md          # Vulnerability disclosure policy
```

---

## Priority 2: Security Baseline Review

The security documentation is comprehensive but needs additions for open source.

### 2.1 Vulnerability Disclosure Policy

Create `.github/SECURITY.md` with:
- How to report security vulnerabilities
- Expected response timeline
- What constitutes a security issue
- Recognition/credit policy

### 2.2 Security Checklist

Add to docs/security.md:
- Pre-deployment security checklist
- Post-deployment hardening steps
- Regular security maintenance tasks
- Known limitations and accepted risks (already partially present)

### 2.3 Threat Model Updates

Review and update threat model for:
- Multi-user deployments (not just single family)
- Hostile network environments
- Compromised upstream images
- Supply chain attacks

### 2.4 Secrets Management

Document:
- How secrets are generated
- How secrets are rotated
- What to do if secrets are leaked
- Backup encryption key management

### 2.5 Audit Logging

Define:
- What events should be logged
- Where logs are stored
- Log retention policy
- How to review logs for security incidents

---

## Priority 3: Testing Infrastructure

Currently there are no automated tests. This is a significant gap for open source.

### 3.1 CI/CD Pipeline

Create `.github/workflows/validate.yml` with baseline quality checks and security checks:

```yaml
name: Validate
on: [push, pull_request]

jobs:
  compose-validation:
    # Validate all compose.yml files

  yaml-lint:
    # Lint YAML files

  shell-lint:
    # Lint shell scripts with shellcheck

  markdown-lint:
    # Check markdown formatting

  link-check:
    # Verify documentation links work

  secret-scan:
    # Detect leaked credentials in commits and repository files

  dependency-scan:
    # Run CVE scanning against dependencies and lockfiles

  image-scan:
    # Scan referenced container images for known vulnerabilities

  sbom:
    # Generate Software Bill of Materials artifact for release traceability
```

### 3.2 Script Testing

Add tests for critical scripts using [bats](https://github.com/bats-core/bats-core):

```bash
tests/
├── test_helper.bash
├── app-up.bats
├── app-backup.bats
├── validate-compose.bats
└── dr-verify.bats
```

### 3.3 Integration Tests

Create integration test suite that:
- Spins up minimal platform in CI
- Verifies services start correctly
- Tests health endpoints
- Tests backup/restore cycle
- Tears down cleanly

**Challenge**: Requires Docker-in-Docker or self-hosted runner with Docker.

### 3.4 Restore Testing

Automate the backup/restore verification:
- Create test data
- Run backup
- Destroy service
- Restore from backup
- Verify test data intact

### 3.5 Required PR Gates

Public contributions should require all CI checks to pass before merge, including security jobs.

---

## Priority 4: Documentation Coherence & Support Policy

Documentation is already strong but can be improved for open source consumption.

### 4.1 Reading Paths

Add guided reading paths for different audiences:

**For Users** (want to deploy and use):
1. README.md (overview)
2. docs/bootstrap.md (prerequisites)
3. Setup wizard (interactive, when available)
4. docs/onboarding.md (add family members)

**For Contributors** (want to add features):
1. CONTRIBUTING.md (how to contribute)
2. CLAUDE.md (conventions and patterns)
3. docs/app-spec.md (how to add apps)
4. docs/adrs/ (understand past decisions)

**For Operators** (want to maintain):
1. docs/ops-standard.md (day-2 operations)
2. docs/dr-runbook.md (disaster recovery)
3. docs/security.md (security model)

### 4.2 Documentation Index

Create `docs/index.md` with:
- Complete document inventory
- Reading paths by audience
- Document status (current, needs-update, draft)
- Quick links to common tasks

### 4.3 Glossary

Create `docs/glossary.md` defining:
- Technical terms (OIDC, SSO, reverse proxy)
- Project-specific terms (platform, app, stack)
- Service names and their purposes

### 4.4 FAQ

Create `docs/faq.md` covering:
- Common installation issues
- Networking troubleshooting
- Authentik integration problems
- Backup/restore questions
- Performance tuning

### 4.5 Support Policy

Create `SUPPORT.md` documenting:
- Supported audience for this phase: solo power users
- Expected response times for issues
- Best-effort vs supported areas
- What maintainers will not troubleshoot

### 4.6 Compatibility Matrix

Document officially supported environments:
- Host OS: macOS (current primary target)
- Main host profile: Mac mini M4
- Secondary profile: Raspberry Pi 5 (backup + DMZ blog)
- Experimental/unsupported targets clearly marked

---

## Priority 5: Interactive Onboarding

Currently, getting started requires reading multiple documents and manually executing commands. An interactive setup process would lower the barrier to entry.

### 5.1 Setup Wizard CLI

**Vision**: A single command that guides users through initial setup.

```bash
./scripts/setup-wizard
```

**Features**:
- Check prerequisites (Docker, disk space, network)
- Generate `.env` files interactively (prompt for passwords, domains)
- Validate configuration before starting
- Start services in correct order with progress feedback
- Verify health of all services
- Create initial admin accounts
- Display dashboard URL and next steps

**Implementation approach**:
- Bash script with `dialog` or `whiptail` for TUI
- Or: Node.js CLI with `inquirer` for richer prompts
- Or: Go binary for cross-platform distribution

### 5.2 First-Run Experience

**Features**:
- Detect first run (no `.env` files exist)
- Prompt user before any destructive operations
- Provide rollback instructions at each step
- Generate a "setup report" documenting what was configured

### 5.3 Quick Start Modes

Support different deployment profiles:

| Mode | Services | Use Case |
|------|----------|----------|
| **Minimal** | Caddy, Homepage | Just reverse proxy and dashboard |
| **Standard** | + Authentik, Dockge, Uptime Kuma | Full platform with SSO |
| **Full** | + Apps (Immich, Jellyfin, etc.) | Complete homelab |

```bash
./scripts/setup-wizard --mode minimal
./scripts/setup-wizard --mode standard
./scripts/setup-wizard --mode full
```

---

## Priority 6: App Marketplace / External Repos

Currently, adding a new app requires manually creating folders and files. A unified system for discovering and deploying community apps would be valuable.

### 6.1 App Registry

Create a registry of available apps:

```yaml
# apps/registry.yml
apps:
  - name: immich
    description: Self-hosted photo and video management
    repo: https://github.com/immich-app/immich
    homelab_config: apps/immich/
    category: media
    maturity: stable

  - name: jellyfin
    description: Media server for movies, TV, music
    repo: https://github.com/jellyfin/jellyfin
    homelab_config: apps/jellyfin/
    category: media
    maturity: stable
```

### 6.2 App Template Generator

Create a scaffold tool:

```bash
./scripts/app-new myapp

# Creates:
# apps/myapp/
# ├── compose.yml (template)
# ├── .env.example (template)
# ├── README.md (template)
# └── app-contract.yaml (template)
```

### 6.3 Supply Chain Controls (Required Before External Repos)

Before enabling arbitrary external app repositories:
- Require pinned commit SHA or signed release tag (no floating branch refs).
- Validate app bundles against `docs/app-spec.md` and a strict schema.
- Block privileged compose defaults (host networking, broad host mounts, privileged mode) unless explicitly approved.
- Generate a provenance report at install time: source URL, commit, digest, scan result.
- Maintain allowlist/trust tiers for app sources (official, verified community, unverified).
- Run image vulnerability scan before deploy and surface risk level to users.

### 6.4 External App Repos

Support pulling app configurations from external git repositories:

```bash
./scripts/app-add https://github.com/someone/homelab-app-nextcloud

# Clones repo to apps/nextcloud/
# Validates against app-spec
# Prompts for configuration
# Integrates with platform
```

### 6.5 App Management UI

Long-term vision: A web UI for managing apps.

**Features**:
- Browse available apps from registry
- One-click deploy with configuration wizard
- Update management with rollback
- Health monitoring dashboard
- Backup status and controls

**Options**:
- Extend Dockge with custom functionality
- Build standalone control panel (docs/control-panel.md exists)
- Use Portainer with custom templates

---

## Priority 7: Community Infrastructure

### 7.1 GitHub Discussions

Enable GitHub Discussions for:
- Q&A (support questions)
- Ideas (feature proposals)
- Show and Tell (community deployments)
- Announcements (releases, breaking changes)

### 7.2 Roadmap

Create `ROADMAP.md` with:
- Current version and status
- Planned features by milestone
- Long-term vision
- How to propose new features

### 7.3 Changelog

Create `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/):
- Document all notable changes
- Categorize by Added, Changed, Deprecated, Removed, Fixed, Security
- Tag releases in git

### 7.4 Release Process

Define release process:
- Version numbering (SemVer recommended)
- Release checklist
- How to cut a release
- How to announce releases
- Required green checks and security scans before release tags
- How to publish SBOM/provenance artifacts with release assets

---

## Implementation Milestones

### Milestone A: Legal and Governance Baseline

| Task | Owner | Status |
|------|-------|--------|
| Confirm existing MIT LICENSE remains project choice | | Done |
| Add CODE_OF_CONDUCT.md | | Not started |
| Create CONTRIBUTING.md | | Not started |
| Add issue templates | | Not started |
| Add PR template | | Not started |
| Add SECURITY.md (disclosure policy) | | Not started |

**Exit criteria**:
- All governance files exist at repository root or `.github/`.
- Templates and contribution flow are usable by first-time contributors.

### Milestone B: Security and CI Baseline

| Task | Owner | Status |
|------|-------|--------|
| Create CI/CD workflow | | Not started |
| Add compose validation to CI | | Not started |
| Add markdown link checking | | Not started |
| Add shell script linting | | Not started |
| Add YAML linting | | Not started |
| Add secret scanning | | Not started |
| Add dependency/image vulnerability scans | | Not started |
| Add SBOM artifact generation | | Not started |

**Exit criteria**:
- CI runs on every pull request.
- Branch protection requires passing checks.
- Security disclosure path is public and tested.

### Milestone C: Documentation and Support Boundaries

| Task | Owner | Status |
|------|-------|--------|
| Create docs/index.md with reading paths | | Not started |
| Create docs/glossary.md | | Not started |
| Create docs/faq.md | | Not started |
| Create SUPPORT.md | | Not started |
| Publish compatibility matrix (macOS-first) | | Not started |

**Exit criteria**:
- New users can identify supported environments and support expectations in under 5 minutes.
- Core docs links and navigation are coherent.

### Milestone D: Testing and Recovery Confidence

| Task | Owner | Status |
|------|-------|--------|
| Set up bats testing framework | | Not started |
| Write tests for core scripts | | Not started |
| Create integration test suite | | Not started |
| Automate restore testing | | Not started |

**Exit criteria**:
- Critical lifecycle scripts have automated test coverage.
- Restore validation runs repeatedly without manual intervention.

### Milestone E: Onboarding and App Ecosystem

| Task | Owner | Status |
|------|-------|--------|
| Design setup wizard flow | | Not started |
| Implement setup wizard | | Not started |
| Create deployment profiles | | Not started |
| Add first-run detection | | Not started |
| Create app registry format | | Not started |
| Build app template generator | | Not started |
| Implement supply chain controls | | Not started |
| Support external app repos | | Not started |
| Design app management UI | | Not started |

**Exit criteria**:
- First-run setup is materially simpler than manual doc-only flow.
- External app ingestion is controlled by defined trust and validation rules.

### Milestone F: Community Launch

| Task | Owner | Status |
|------|-------|--------|
| Enable GitHub Discussions | | Not started |
| Create ROADMAP.md | | Not started |
| Create CHANGELOG.md | | Not started |
| Write announcement post | | Not started |
| Reach out to homelab communities | | Not started |

**Exit criteria**:
- Launch gate criteria are all met.
- Initial contributor feedback loop is active and sustainable.

---

## Success Metrics

### Adoption Metrics
- GitHub stars and forks (secondary signal)
- Clones per week
- Returning users (issues/discussions from repeat operators)

### Contribution Metrics
- Pull requests submitted
- Pull requests merged
- Unique contributors
- Time to first response on issues
- Median time to first merged external PR

### Quality Metrics
- CI pass rate
- Open bug count
- Time to close issues
- Documentation coverage
- Restore verification pass rate
- Regression rate after releases

### Operator Outcome Metrics
- Successful first install rate (self-reported or telemetry-free survey)
- Median time-to-working baseline deployment
- Backup/restore success in user testing
- Time-to-recover for common failure scenarios

### Community Metrics
- Discussion activity
- Discord/Matrix members (if created)
- Blog posts / videos by community

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Scope creep** | Delayed release | Focus on Milestones A-B first, release early |
| **Maintainer burnout** | Abandoned project | Set boundaries, find co-maintainers |
| **Security vulnerability** | Reputation damage | Disclosure policy, security audit |
| **Breaking changes** | User frustration | SemVer, migration guides, deprecation warnings |
| **Low adoption** | Wasted effort | Validate need with community before building |

---

## Open Questions

Resolved in manifesto:
1. **Primary operator**: Solo power user in current phase; path to family-admin usability later.
2. **Current platform target**: macOS-first.
3. **Priority workloads**: photo management, AI-assisted coding applications, media server services.
4. **Current hardware baseline**: Mac mini M4 primary host, Raspberry Pi 5 secondary backup/DMZ blog role.

Still open:
1. **Monetization**: Pure open source? Paid support tier? SaaS offering?
2. **Governance**: BDFL? Committee? Foundation?
3. **Branding**: Keep "homelab" name or create unique brand?

---

## References

- [Open Source Guides](https://opensource.guide/) - GitHub's guide to open source
- [Contributor Covenant](https://www.contributor-covenant.org/) - Code of conduct template
- [Keep a Changelog](https://keepachangelog.com/) - Changelog format
- [Semantic Versioning](https://semver.org/) - Version numbering
- [Choose a License](https://choosealicense.com/) - License selection guide
