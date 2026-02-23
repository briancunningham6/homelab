# Support Policy

## Scope

This project is currently maintained as an experimental, macOS-first homelab
platform.

Current supported operator profile:
- Solo power users running the documented baseline architecture.

Family-admin usability is a project direction, but not yet a guaranteed support
target for all workflows.

## Supported Environments

Officially supported baseline:
- Host OS: macOS
- Primary host: Mac mini M4
- Secondary host: Raspberry Pi 5 for backup workflows and DMZ blog hosting

Other environments may work but are best-effort unless explicitly documented as
supported.

## Support Channels

- Bug reports: GitHub Issues (use templates)
- Feature requests: GitHub Issues (use templates)
- Security vulnerabilities: private report path in `.github/SECURITY.md`

## Response Expectations

This is a maintainer-led project; support is best-effort.

Target response windows:
- Initial triage for standard issues: within 7 days
- Security reports: see `.github/SECURITY.md` SLA targets

No guaranteed turnaround times are provided.

## What Maintainers Will Help With

- Reproducible bugs in project scripts and documented workflows
- Documentation corrections and gaps
- Issues in supported baseline environments
- App integrations that follow `docs/app-spec.md`

## What Is Out of Scope for Direct Troubleshooting

- Custom hardware/network topologies outside documented patterns
- Private infrastructure and secrets-specific debugging
- General Linux/macOS administration unrelated to this repository
- Custom forks with significant architectural divergence
- Upstream app bugs unrelated to integration logic in this repo

## Issue Quality Requirements

To receive useful support, include:
- Reproduction steps
- Environment details
- Relevant logs and command output
- What you already tried

Incomplete reports may be closed until more detail is provided.

## Project Boundaries

Support follows project priorities in:
- `manifesto.md`
- `docs/open-source-roadmap.md`
- `docs/ops-standard.md`
