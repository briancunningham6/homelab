# Homelab Platform Manifesto

## Mission
Build a practical, self-hosted platform that gives people real control over their digital lives: their data, their applications, their automation, and their online identity.

This project exists to make personal digital sovereignty achievable for people with moderate technical skill, without requiring full-time operations work.
The current primary operator is a solo power user, with a planned path toward family-admin usability over time.

## Why This Project Exists
Most modern digital services are optimized for advertising, data extraction, engagement, and lock-in. Those incentives often conflict with user goals: privacy, focus, trust, and long-term ownership.

The alternative has historically been difficult self-hosting. Running services at home has required deep systems knowledge, constant maintenance, and high tolerance for risk and breakage.

That tradeoff is changing. Hardware is better, broadband is better, open-source infrastructure is stronger, and LLMs can now act as on-demand operators and tutors. It is now realistic to build a home platform that is both user-controlled and usable.

## Thesis
People should be able to run the core parts of their digital life on infrastructure they control, while still getting software quality comparable to mainstream hosted products.

This project is an opinionated operating layer for that outcome:
- A consistent way to deploy, secure, update, observe, and recover apps.
- A stable identity and access model across services.
- A path from convenience-first dependencies today to self-reliant operation over time.

## Principles
1. User sovereignty first
Data ownership, portability, and local administrative control are default requirements.

2. Practicality over purity
Use transitional dependencies when they materially reduce complexity, then replace them intentionally.

3. Secure-by-default baseline
Reasonable defaults for auth, network exposure, secrets, and updates are mandatory.

4. Recoverability is a feature
Backup, restore, and rollback are core platform capabilities, not optional add-ons.

5. Observable operations
Health, logs, and failure states must be visible and actionable by non-expert operators.

6. Composable architecture
Apps should follow repeatable patterns so users can add, remove, or replace services safely.

7. Documentation as product
Runbooks and standards are part of the platform, not separate from it.

## Scope
In scope:
- Self-hosted platform infrastructure for home or small-team environments.
- Application lifecycle workflows (install, update, backup, restore, rollback).
- Identity and access integration across apps.
- Remote access and secure operations for real-world use.
- AI-assisted administration and app development workflows.
- Initial priority workloads: photo management, AI-assisted coding applications, and media server services.

Out of scope for now:
- Building a general-purpose public cloud competitor.
- Zero-touch setup for non-technical users.
- Perfect elimination of all third-party dependencies in v1.
- Hardware productization beyond validated reference builds.

## Current Phase
This project is aspirational and experimental. The current phase optimizes for speed of learning and rapid iteration. Long-term hardening, full portability, and deep dependency removal are explicit follow-on phases.
The platform remains macOS-first in this phase.

## Definition of Success (Phased)
### Phase 1: Working Platform Baseline
- A user with moderate IT skills can install and configure the platform on supported hardware.
- Core services and at least one major app can be deployed and operated with documented workflows.
- Routine day-2 actions (update, backup, restore, restart) are scriptable and repeatable.
- Major failure modes are documented with recovery steps.

### Phase 2: Operational Reliability and Safety
- Default configuration includes strong auth, TLS, and least-privilege patterns.
- Backups are tested with successful restore drills.
- Core services recover predictably from reboot and common host/network interruptions.
- Monitoring surfaces service health and regressions early.

### Phase 3: Progressive Self-Reliance
- Third-party dependencies are reduced where practical and replaced with self-hosted alternatives.
- Platform portability improves across host OS and hardware profiles.
- Users can package and share apps with safe install and upgrade patterns.
- Local-first AI workflows become viable as home inference capabilities mature.

## Transitional Dependencies and Exit Intent
Current dependencies are accepted to accelerate learning and delivery. Each dependency should have an explicit replacement trigger and migration path.

- Proprietary LLM models
  - Why now: high quality and lower setup burden.
  - Exit intent: move to open-weight/local inference when quality and hardware economics are sufficient.

- Tailscale
  - Why now: reliable remote access with low operational complexity.
  - Exit intent: evaluate self-hosted WireGuard-based access when maintainability and security posture are comparable.

- macOS host
  - Why now: available hardware and stable local workflow.
  - Exit intent: add Linux parity and migration paths as platform tooling hardens.

- Open-source ecosystem dependencies
  - Why now: leverage proven components rather than reinventing infrastructure primitives.
  - Exit intent: keep dependency graph auditable, minimize unnecessary coupling, and prefer replaceable integrations.

## Current Hardware Baseline
- Main host: Mac mini M4.
- Secondary host: Raspberry Pi 5 for backup workflows and internet-exposed blog hosting (DMZ segment).

## Governance and Decision Rule
When tradeoffs are unclear, choose the option that best improves:
1. User control
2. Operational safety
3. Recoverability
4. Simplicity of ongoing maintenance

If these conflict, document the compromise and revisit it in the next phase review.

## Commitment
This project is not promising instant perfection. It is committing to a clear direction: from experimental self-hosting toward dependable personal infrastructure that users can understand, trust, and control.
