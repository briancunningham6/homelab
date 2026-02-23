# Contributing Guide

Thanks for your interest in contributing to this project.

This project is currently optimized for a macOS-first homelab setup and a
solo power-user operator model. Contributions that improve clarity, safety,
and repeatability are especially valuable.

## Development Environment Setup

1. Clone the repository.
2. Ensure Docker Desktop is installed and running on macOS.
3. Copy `.env.example` files to `.env` where required and fill values.
4. Validate all compose files before changes:

```bash
HOMELAB_DIR=$(pwd) ./scripts/validate-compose
```

5. For stack-level validation during larger changes:

```bash
./scripts/platform-up
```

## Ways to Contribute

- Fix documentation issues and broken links
- Improve scripts and operational reliability
- Add or refine app integrations that follow `docs/app-spec.md`
- Report bugs with clear reproduction steps
- Propose focused roadmap improvements

## Issue Reporting

Use issue templates and include:

- What you expected
- What happened
- Steps to reproduce
- Environment details (host OS, Docker version, app/service name)
- Relevant logs or command output

If the issue is security-sensitive, do not open a public issue. Use the
private disclosure process in `.github/SECURITY.md`.

## Pull Request Process

1. Create a focused branch for one logical change.
2. Keep PRs small and reviewable where possible.
3. Run relevant validation locally (at minimum `scripts/validate-compose`).
4. Update docs for behavior, workflow, or interface changes.
5. Open a PR using the PR template and complete all checklist items.

## Code Review Expectations

- Be specific, respectful, and solution-oriented.
- Prioritize correctness, security, and operational safety.
- Call out tradeoffs explicitly.
- Prefer incremental improvements over large speculative rewrites.

## Commit Message Convention

Use Conventional Commits style when possible:

- `feat: add app backup preflight checks`
- `fix: handle missing env file in app-up`
- `docs: clarify restore workflow`
- `chore: update script comments`

Recommended types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## What Makes a Good Contribution

- Solves a clear problem
- Matches project scope and current phase
- Includes validation and rollback considerations
- Improves or preserves security posture
- Includes documentation updates where relevant

## Scope Notes

Before implementing large changes, check:

- `manifesto.md` for mission and scope
- `docs/open-source-roadmap.md` for current priorities
- `docs/ops-standard.md` for operational expectations

If your idea is large or directional, open a discussion or issue first.
