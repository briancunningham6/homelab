# DR Runbook — Disaster Recovery Procedures & Drill Results

> Recovery procedures and test history | Parent: [DESIGN.md](../DESIGN.md)

## Recovery Procedure

See [ops-standard.md](ops-standard.md) § 2 for recovery objectives (RPO ≤ 24h, RTO 4–8h) and dependency order.

### Quick Reference: Recovery Order

1. Prepare replacement hardware and OS
2. Install Docker Engine + Compose
3. Restore platform manifests (compose files, configs) from backup or git
4. Restore Tailscale (join to tailnet)
5. Restore Caddy (config + certs)
6. Restore Authentik (database + config + keys) — **critical dependency**
7. Restore monitoring (Uptime Kuma, Homepage)
8. Restore app stacks (Immich, etc.)
9. Validate all services healthy
10. Run `scripts/dr-verify`

## Drill History

### Drill Template

```
## YYYY-MM-DD — DR Drill [Full / Partial]

**Scope:** [What was tested]
**Hardware:** [What hardware was used]
**Backup source:** [Local / Offsite Pi / B2]

### Steps
1. ...

### Result
- RPO achieved: [yes/no — data loss?]
- RTO achieved: [yes/no — how long?]
- Services restored: [list]
- Issues encountered: [list]

### Lessons learned
[What to improve]
```

---

## Drills

<!-- Add new drill records above this line, newest first -->
