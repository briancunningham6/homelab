# Implementation Tasks

> Agent task definitions for Claude Code | Parent: [DESIGN.md](../DESIGN.md)

## How to Use

Each `.md` file in this directory is a self-contained task prompt. To run a task in Claude Code:

1. Open Claude Code in the `~/homelab` repo
2. Start a new session or use `/agents`
3. Paste the contents of the task file (or reference it)
4. The agent will read project context from `CLAUDE.md` and referenced docs automatically

## Dependency Map

```
Task 01 (Caddy)          ─┐
Task 02 (Dockge)          │
Task 03 (Homepage)        ├─► All independent, run in parallel
Task 04 (Uptime Kuma)     │
Task 05 (Tailscale)      ─┘
                           │
Task 06 (Operational Scripts) ─► Can run in parallel with 01–05
Task 07 (Doc Templates)       ─► Can run in parallel with 01–05
                           │
                           ▼
Task 08 (Authentik)       ─► Depends on: 01 (Caddy config entries)
                           │
                           ▼
Task 09 (Immich)          ─► Depends on: 01 (Caddy), 08 (Authentik)
                           │
                           ▼
Task 10 (Integration)     ─► Depends on: all above (wires everything together)
                           │
                           ▼
Task 11 (OpenClaw)        ─► Depends on: 10 (full platform running + Authentik + Immich)
```

## Parallel Execution Plan

### Wave 1 (all independent — run simultaneously)
| Task | Agent | Output |
|------|-------|--------|
| `01-caddy.md` | Agent 1 | `platform/caddy/` stack |
| `02-dockge.md` | Agent 2 | `platform/dockge/` stack |
| `03-homepage.md` | Agent 3 | `platform/homepage/` stack |
| `04-uptime-kuma.md` | Agent 4 | `platform/uptime-kuma/` stack |
| `05-tailscale.md` | Agent 5 | `platform/tailscale/` stack |
| `06-scripts.md` | Agent 6 | `scripts/*` operational tooling |
| `07-doc-templates.md` | Agent 7 | `docs/inventory.md`, `docs/runbook.md`, etc. |

### Wave 2 (depends on Wave 1)
| Task | Agent | Output |
|------|-------|--------|
| `08-authentik.md` | Agent 8 | `platform/authentik/` stack |

### Wave 3 (depends on Wave 2)
| Task | Agent | Output |
|------|-------|--------|
| `09-immich.md` | Agent 9 | `apps/immich/` stack |

### Wave 4 (integration — depends on all above)
| Task | Agent | Output |
|------|-------|--------|
| `10-integration.md` | Agent 10 | Caddyfile assembly, Homepage config, validation |

### Wave 5 (OpenClaw — depends on full platform)
| Task | Agent | Output |
|------|-------|--------|
| `11-openclaw.md` | Agent 11 | `ai/openclaw/` stack, Ollama, lane config, eval templates |

## Estimated Cost

| Wave | Tasks | Token Estimate | Cost (Opus) | Cost (Sonnet) |
|------|-------|---------------|-------------|---------------|
| Wave 1 | 7 parallel agents | ~600K | ~$12 | ~$3 |
| Wave 2 | 1 agent | ~120K | ~$2.50 | ~$0.60 |
| Wave 3 | 1 agent | ~100K | ~$2.00 | ~$0.50 |
| Wave 4 | 1 agent | ~150K | ~$3.00 | ~$0.75 |
| Wave 5 | 1 agent | ~150K | ~$3.00 | ~$0.75 |
| **Total** | **11 agents** | **~1.12M** | **~$22.50** | **~$5.60** |

Add 50–100% for iteration and debugging → **realistic range: $30–45 (Opus) or $8–12 (Sonnet)**.

## Post-Execution Checklist

After all tasks complete:

- [ ] All `compose.yml` files pass `docker compose config` validation
- [ ] All `.env.example` files have placeholder values for every required variable
- [ ] All READMEs follow the template from CLAUDE.md
- [ ] Caddyfile routes all services to correct hostnames
- [ ] Homepage `services.yaml` lists all deployed services
- [ ] `docs/inventory.md` is populated with all services
- [ ] `.gitignore` covers `.env`, `data/`, `backups/`
- [ ] Rollout plan updated with task completion status
- [ ] OpenClaw runtime deployed with Authentik SSO
- [ ] Per-user agent lanes verified (admin/user/child)
- [ ] Evaluation templates ready for family trial
