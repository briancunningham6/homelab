# Compatibility Matrix

This document defines what environments are currently supported, best-effort,
or out of scope for this project phase.

## Current Phase Support Targets

| Category | Target | Status | Notes |
|----------|--------|--------|-------|
| Primary host OS | macOS | Supported | Current baseline and primary development target |
| Primary host hardware | Mac mini M4 | Supported | Main platform host profile |
| Secondary host hardware | Raspberry Pi 5 | Supported (limited role) | Backup workflows + DMZ blog hosting role |
| Container runtime | Docker Desktop (macOS) | Supported | Required for documented setup |
| Remote access | Tailscale | Supported | Current transitional dependency |

## Best-Effort / Experimental Targets

| Category | Target | Status | Notes |
|----------|--------|--------|-------|
| Linux host parity | Ubuntu/Debian-class hosts | Experimental | Planned via roadmap; not fully validated |
| Alternate ARM hosts | Other ARM SBCs/NAS devices | Best effort | No guarantee of docs parity or support |
| Self-hosted WireGuard access path | Non-Tailscale remote access | Experimental | Planned replacement track |

## Not Currently Supported

| Category | Target | Status | Notes |
|----------|--------|--------|-------|
| Non-Docker runtimes | Podman, Kubernetes, Nomad | Not supported | Out of current scope |
| Windows host baseline | Native Windows host setup | Not supported | No official setup path yet |
| Public-cloud-only reference architecture | Managed cloud as primary target | Not supported | Project is home/self-host first |

## Compatibility Rules

- "Supported" means documented setup + maintainer troubleshooting within normal
  project boundaries.
- "Best effort/Experimental" means community contributions are welcome, but
  breakage risk and support variability are expected.
- New support targets should be proposed via issue and aligned to
  `docs/open-source-roadmap.md`.
