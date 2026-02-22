# Homelab Documentation

This directory contains comprehensive documentation for the homelab platform.

## Quick Links

### Core Documentation

| Document | Description | When to Read |
|----------|-------------|--------------|
| [DESIGN.md](../DESIGN.md) | Platform architecture and design principles | Before making any changes |
| [app-spec.md](app-spec.md) | Application packaging standards | Before adding new services |
| [ops-standard.md](ops-standard.md) | Operational procedures and standards | For day-to-day operations |

### Setup Guides

| Document | Description | When to Use |
|----------|-------------|-------------|
| [iphone-access-setup.md](iphone-access-setup.md) | Quick setup for mobile access | Setting up new mobile device |
| [mobile-access-architecture.md](mobile-access-architecture.md) | Detailed explanation of DNS/VPN setup | Understanding how mobile access works |
| [onboarding.md](onboarding.md) | Admin and user onboarding | Adding new users to the platform |

### Integration Guides

| Document | Description | When to Use |
|----------|-------------|-------------|
| [authentik-oidc-integration.md](authentik-oidc-integration.md) | Integrating services with Authentik SSO | Adding SSO to new services |
| [control-panel.md](control-panel.md) | Admin control panel design | Working on admin UI |

### Reference

| Document | Description | When to Use |
|----------|-------------|-------------|
| [security.md](security.md) | Security model and threat analysis | Security-related decisions |
| [dependencies.md](dependencies.md) | License audit and portability | Legal or migration questions |
| [agent-model.md](agent-model.md) | AI agent architecture | Working with AI features |
| [rollout-plan.md](rollout-plan.md) | Phased implementation plan | Project planning |

### Platform-Specific

| Document | Description | When to Use |
|----------|-------------|-------------|
| [notes/mac-mini.md](notes/mac-mini.md) | macOS-specific configuration | macOS host setup |

## Documentation by Topic

### Mobile Access

Mobile access to homelab services is accomplished through the combination of Tailscale VPN and AdGuard Home DNS:

1. Start here: [iPhone Access Setup Guide](iphone-access-setup.md) - Quick setup steps
2. Deep dive: [Mobile Access Architecture](mobile-access-architecture.md) - How it all works

**Key concepts**:
- Tailscale provides secure VPN connectivity
- AdGuard Home resolves `.home` domains to homelab IP
- Caddy routes requests to appropriate services
- Works on iPhone, iPad, Android, and any Tailscale-capable device

### Adding New Services

To add a new service to the homelab:

1. Follow structure in: [app-spec.md](app-spec.md)
2. Add Caddy route to: `platform/caddy/Caddyfile`
3. If using individual DNS entries (not wildcard): Add DNS rewrite in AdGuard Home
4. If requiring authentication: Follow [authentik-oidc-integration.md](authentik-oidc-integration.md)
5. Update Homepage: Add to `platform/homepage/config/services.yaml`

### Authentication & Security

**SSO Setup**:
- Read: [authentik-oidc-integration.md](authentik-oidc-integration.md)
- Security model: [security.md](security.md)
- User management: [onboarding.md](onboarding.md)

**Security checklist**:
1. All external access via Tailscale (no open ports)
2. Services protected by Authentik SSO
3. Secrets encrypted (see [security.md](security.md))
4. Regular backups (see [ops-standard.md](ops-standard.md))

### Backup & Recovery

**Backup strategy**:
- 3-2-1 rule (see [ops-standard.md](ops-standard.md))
- Automated daily backups with Restic
- Offsite backup to cloud storage
- Regular restore testing

**Recovery procedures**:
- Service failure: Check `apps/<service>/README.md`
- Data corruption: Restore from Restic backup
- Complete disaster: Follow disaster recovery plan in [ops-standard.md](ops-standard.md)

### Monitoring & Maintenance

**Health monitoring**:
- Uptime Kuma: Service availability
- Homepage: Quick status dashboard
- Docker health checks: Container status
- AdGuard Home: DNS query logs

**Regular maintenance**:
- Weekly: Review Uptime Kuma alerts
- Monthly: Update Docker images
- Quarterly: Test backup restores
- Yearly: Review security audit

## Common Tasks

### I want to...

**Access services from my iPhone**
→ [iPhone Access Setup Guide](iphone-access-setup.md)

**Add a new service to the homelab**
→ [App Specification](app-spec.md)

**Integrate SSO with a new service**
→ [Authentik OIDC Integration](authentik-oidc-integration.md)

**Understand the overall architecture**
→ [DESIGN.md](../DESIGN.md)

**Add a new user**
→ [Onboarding Guide](onboarding.md)

**Troubleshoot DNS issues**
→ [Mobile Access Architecture](mobile-access-architecture.md#troubleshooting)

**Set up backups for a new service**
→ [Ops Standard](ops-standard.md)

**Review security model**
→ [Security Documentation](security.md)

**Understand the AI agent system**
→ [Agent Model](agent-model.md)

## Contributing to Documentation

When adding new documentation:

1. **Choose the right location**:
   - Core architecture: Root level (like `DESIGN.md`)
   - Guides and procedures: `docs/` directory
   - Service-specific: Service README (`apps/<service>/README.md`)

2. **Follow the template**:
   - Start with overview/purpose
   - Include prerequisites
   - Step-by-step instructions
   - Troubleshooting section
   - Reference material

3. **Link to related docs**:
   - Cross-reference other documentation
   - Update this README when adding new docs
   - Keep links relative (not absolute)

4. **Keep it current**:
   - Update docs when changing systems
   - Mark deprecated information clearly
   - Include last updated date if relevant

## Documentation Standards

### Formatting

- Use Markdown (`.md` extension)
- Include table of contents for long documents
- Use code blocks with language hints (```bash, ```yaml, etc.)
- Include examples and command outputs
- Use tables for reference material

### Structure

```markdown
# Document Title

Brief overview paragraph.

## Table of Contents
- [Section 1](#section-1)
- [Section 2](#section-2)

## Section 1
Content...

## Section 2
Content...

## Reference
Tables, commands, etc.
```

### Screenshots

- Place in `docs/images/` directory
- Use descriptive filenames
- Keep file sizes reasonable (<500KB)
- Reference with relative paths

### Updates

When a system changes:
1. Update affected documentation
2. Update "last modified" date if present
3. Update cross-references
4. Test any commands/procedures
5. Commit with clear message: "docs: update X for Y change"

## Getting Help

If documentation is unclear or missing:

1. Check service README: `apps/<service>/README.md`
2. Search this directory: All documentation is here
3. Check CLAUDE.md: Context for AI assistants
4. Review git history: `git log -- docs/`
5. Create an issue: Document what's missing

## Maintenance

**Review schedule**:
- After major changes: Update affected docs immediately
- Monthly: Review for accuracy
- Quarterly: Update examples and screenshots
- Yearly: Full documentation audit

**Deprecation process**:
1. Mark document as deprecated at top
2. Link to replacement documentation
3. Keep for one version/6 months
4. Move to `docs/archive/` before deletion
