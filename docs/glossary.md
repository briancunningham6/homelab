# Glossary

## Core Project Terms

### Platform
The shared infrastructure layer in this repository that provides routing,
identity, observability, and operational workflows for deployed services.

### App
A deployable service stack under `apps/` that follows project integration and
operations patterns.

### Stack
A unit of deployment defined by a `compose.yml` file and related configuration.

### Day-2 Operations
Operational tasks after initial install, such as update, backup, restore,
rollback, and troubleshooting.

### Baseline
The officially documented and supported setup for the current project phase.

## Identity and Access Terms

### SSO (Single Sign-On)
A login model where users authenticate once via a central identity provider and
then access multiple apps.

### OIDC (OpenID Connect)
An identity layer built on OAuth 2.0 used for authentication flows between apps
and identity providers.

### IdP (Identity Provider)
The system that authenticates users and issues identity tokens (Authentik in
this project baseline).

### RBAC (Role-Based Access Control)
Permission model where access is granted through roles/groups rather than
direct per-user rules.

## Networking Terms

### Reverse Proxy
A service that receives incoming HTTP(S) traffic and routes it to internal
services (Caddy in this project baseline).

### DMZ Segment
A network boundary for internet-exposed services that should be isolated from
core internal services.

### Internal Service
A service intended for trusted network access only (for example, admin tools
and internal dashboards).

### Public Service
A service intentionally exposed to the internet with additional hardening.

## Operations and Reliability Terms

### Backup
A protected copy of service state and configuration used for disaster recovery.

### Restore
The process of recovering a service from a known backup state.

### RPO (Recovery Point Objective)
Maximum acceptable data loss measured in time.

### RTO (Recovery Time Objective)
Maximum acceptable recovery time after an incident.

### Rollback
Reverting a deployment change to a previous known-good version.

## Security and Supply Chain Terms

### Vulnerability Disclosure
The process for privately reporting and triaging security issues.

### Secret
Sensitive credential material (API keys, passwords, tokens, private keys).

### SBOM (Software Bill of Materials)
Machine-readable inventory of software components used by a system.

### Provenance
Traceable metadata showing where an artifact came from and how it was produced.

### Trust Tier
Classification for app sources (for example: official, verified community,
unverified) used to guide risk-aware installation decisions.
