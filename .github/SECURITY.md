# Security Policy

## Supported Scope

This project currently targets a self-hosted, macOS-first homelab environment.
Security reports should focus on vulnerabilities in project-managed scripts,
configurations, and documented deployment patterns.

## Reporting a Vulnerability

Please do not open public GitHub issues for security vulnerabilities.

Report vulnerabilities privately by contacting the maintainer:
- GitHub: <https://github.com/briancunningham6>

When possible, include:
- Vulnerability description and impact
- Affected files/services/components
- Reproduction steps or proof of concept
- Suggested mitigation (if known)

## Response Targets

- Initial acknowledgment: within 72 hours
- Triage and severity assessment: within 7 days
- Status update cadence: at least every 7 days until resolution plan is clear

These are best-effort targets for the current project stage.

## Disclosure Process

1. Report is received and acknowledged.
2. Maintainer validates impact and scope.
3. Fix plan is prepared.
4. Patch is released.
5. Public disclosure is coordinated after a fix is available (or risk is accepted and documented).

## What Qualifies as a Security Issue

Examples include:
- Authentication or authorization bypass
- Secret leakage or credential exposure
- Unsafe default configurations that create material risk
- Remote code execution or command injection in project tooling
- Supply chain trust failures in app ingestion workflows

Non-security bugs should be filed using standard issue templates.

## Recognition

Responsible reporters may be credited in release notes unless they prefer to remain anonymous.
