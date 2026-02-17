# Task 11: OpenClaw — Early Agent Rollout

## Context
Read `CLAUDE.md` for project conventions. Read `docs/agent-model.md` for the full OpenClaw design (lanes, isolation, identity integration, management contract, open questions). Read `docs/security.md` § 7 for agent security requirements. Read `docs/rollout-plan.md` Phase 4 for the task list this implements.

**This task depends on Phases 1–3 being complete** — platform running, Authentik configured with family accounts, at least one app (Immich) deployed.

## Objective
Deploy the OpenClaw agent runtime and configure per-user agent lanes so every family member has a working AI agent scoped to their identity and permissions. This is an early validation — the goal is to prove the model works, not to build the final system.

## Output Files

```
ai/openclaw/
├── compose.yml
├── .env
├── .env.example
├── app-contract.yaml
├── data/                       # Created at runtime (gitignored)
└── README.md

docs/openclaw-eval-template.md  # Evaluation template for the family trial
```

## Requirements

### Part 1: Runtime Selection & Deployment

The agent runtime is an open question (see `docs/agent-model.md` § 7). The agent executing this task should evaluate options and pick one. Key criteria:

| Requirement | Why |
|-------------|-----|
| Multi-user support | Each family member gets their own session/workspace |
| OIDC/SSO integration | Must authenticate via Authentik — no separate credentials |
| Tool/function calling | Agents need to call platform scripts and app APIs |
| Per-user isolation | Conversation context and memory must not leak between users |
| Local LLM backend | Must connect to Ollama or similar for local inference |
| Docker Compose deployment | Must follow platform conventions |

**Strong candidates to evaluate:**
- **Open WebUI** — mature, multi-user, OIDC support, tool calling, Ollama integration. May need custom tooling for lane enforcement.
- **AnythingLLM** — workspace-based isolation, API tools, Docker support. Check SSO support.
- **Custom lightweight agent** — if existing tools don't support lane enforcement natively, a thin orchestration layer may be needed on top of the LLM backend.

**Decision process:**
1. Check which candidates support OIDC login via Authentik
2. Check which support per-user workspace isolation
3. Check which support function/tool calling with scoped permissions
4. Pick the best fit — document the decision and reasoning in the README
5. If no single tool meets all requirements, deploy the closest match and document what needs custom work

### compose.yml
- Deploy the chosen runtime with a pinned version tag
- Deploy Ollama as the local LLM backend (if not already deployed elsewhere)
  - Image: `ollama/ollama` with pinned tag
  - Mount `./data/ollama` to `/root/.ollama` for model storage
  - Consider GPU passthrough notes for macOS (Metal is not available in Docker — document this limitation)
- `restart: unless-stopped` on all containers
- Join `caddy-net` external network
- Internal network for runtime ↔ Ollama communication
- Container names: `openclaw`, `openclaw-ollama` (or similar)

### .env.example
```
# OpenClaw Configuration

# Ollama
OLLAMA_HOST=http://openclaw-ollama:11434

# Authentik OIDC (configure after creating the provider in Authentik)
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_ISSUER_URL=http://login.home/application/o/openclaw/
OIDC_REDIRECT_URI=http://openclaw.home/oauth/callback

# Default model to pull on first start
DEFAULT_MODEL=llama3.2:3b

# Admin settings
# ENABLE_SIGNUP=false  # Disable self-registration — users come from Authentik
```

### app-contract.yaml
```yaml
name: openclaw
version: 0.1.0

auth:
  mode: oidc
  provider: authentik
  groups:
    admin: homelab-admin
    user: parents
    child: kids

network:
  hostname: openclaw.home
  internalPort: 8080  # Adjust based on chosen runtime

data:
  paths:
    - ./data/ollama
    - ./data/runtime

backup:
  includes:
    - data/runtime
  excludes:
    - data/ollama  # Models can be re-downloaded
  rpoClass: daily
  restoreTest: documented

agentScopes:
  user: [chat, read-apps, write-apps]
  child: [chat, read-apps]
  admin: [chat, read-apps, write-apps, platform-manage, configure]

health:
  endpoint: /health  # Adjust based on chosen runtime
```

### README.md
Follow the template from CLAUDE.md. Include:

- What OpenClaw does (AI agent layer — every family member gets a personal agent scoped to their identity)
- Runtime decision: which tool was chosen and why
- Quick reference: image, version, internal port, hostname `openclaw.home`, health endpoint
- Commands: start, stop, restart, update with rollback
- **First-run setup:**
  1. Start Ollama, pull default model (`docker exec openclaw-ollama ollama pull llama3.2:3b`)
  2. Create Authentik OIDC provider for OpenClaw
  3. Set OIDC env vars in `.env`
  4. Start the runtime
  5. Log in via `http://openclaw.home` with Authentik SSO
  6. Verify per-user workspace isolation
- **Authentik integration:**
  - Create OAuth2/OpenID Provider in Authentik for OpenClaw
  - Redirect URI: `http://openclaw.home/oauth/callback` (adjust per runtime)
  - Create Application in Authentik, bind to provider
  - Map groups: `homelab-admin` → admin role, `parents` → user role, `kids` → restricted role
  - Disable self-registration — all users flow through Authentik
- **Agent lanes — how they map:**

  | Authentik Group | Agent Lane | Capabilities |
  |-----------------|-----------|--------------|
  | `homelab-admin` | Admin | Full platform management, all tools |
  | `parents` | User | App interaction (Immich, etc.), no infra tools |
  | `kids` | Child | Chat + read-only app access, content safety |

- **Tool registry** (initial set):

  | Tool | Admin | User | Child | Description |
  |------|-------|------|-------|-------------|
  | `platform-up` | ✓ | — | — | Start all platform services |
  | `platform-down` | ✓ | — | — | Stop all platform services |
  | `app-up` | ✓ | — | — | Start an app |
  | `app-down` | ✓ | — | — | Stop an app |
  | `app-backup` | ✓ | — | — | Backup an app |
  | `dr-verify` | ✓ | — | — | Run health check |
  | `immich-browse` | ✓ | ✓ | ✓ | Browse photos |
  | `immich-upload` | ✓ | ✓ | — | Upload photos |

- **macOS / Docker limitation:** Ollama in Docker on macOS cannot access Metal GPU acceleration. Models run on CPU only. For better performance, Ollama can be installed natively (`brew install ollama`) and the runtime pointed at `host.docker.internal:11434`. Document both paths.
- **Backup scope:** Runtime data (user workspaces, conversation history). Models excluded (re-downloadable).
- Upstream links for chosen runtime

---

### Part 2: Authentik Configuration Guide

Document (in the README) the exact steps to create the OpenClaw OIDC provider in Authentik:

1. Navigate to `http://login.home/if/admin/`
2. Providers → Create → OAuth2/OpenID Provider
3. Name: `OpenClaw`
4. Authorization flow: default
5. Client ID: auto-generated (copy to `.env`)
6. Client Secret: auto-generated (copy to `.env`)
7. Redirect URI: `http://openclaw.home/oauth/callback`
8. Scopes: `openid`, `profile`, `email`
9. Create Application → name `OpenClaw`, bind to provider
10. Test: log in as each family member and verify correct group membership flows through

---

### Part 3: Lane Enforcement

Document (in the README or a separate `docs/openclaw-lanes.md` if it gets long) how lane enforcement works in the chosen runtime:

**If the runtime supports role-based tool access natively:**
- Map Authentik groups to runtime roles
- Assign tool permissions per role
- Document the mapping

**If the runtime does NOT support role-based tool access natively:**
- Document what's enforced by the runtime vs what needs manual discipline
- Create a plan for adding enforcement (middleware, custom wrapper, etc.)
- For the evaluation period, rely on Authentik group-gated access + audit logging as interim controls

---

### Part 4: Caddy & Homepage Integration

**Caddyfile entry** (add to `platform/caddy/Caddyfile`):
```
openclaw.home {
    reverse_proxy openclaw:8080
}
```

**Homepage entry** (add to `platform/homepage/config/services.yaml`):
```yaml
- AI:
    - OpenClaw:
        href: http://openclaw.home
        description: AI Agent
        icon: openai  # or a custom icon
        server: my-docker
        container: openclaw
```

---

### Part 5: Evaluation Template

Create `docs/openclaw-eval-template.md`:

```markdown
# OpenClaw Evaluation — [User Name]

> Family member feedback on the OpenClaw agent trial

## Period
Start: YYYY-MM-DD
End: YYYY-MM-DD

## User Profile
- **Name:**
- **Agent lane:** Admin / User / Child
- **Primary use cases tested:**

## What worked well
-

## What didn't work / was frustrating
-

## Feature requests
-

## Trust level
How comfortable are you letting the agent act on your behalf? (1–5)

## Would you use this regularly? (yes / sometimes / no)

## Other notes
-
```

Also create a summary template at the end of the eval period:

```markdown
# OpenClaw Evaluation Summary

> Aggregate results from family trial | Date: YYYY-MM-DD

## Participants
| Name | Lane | Used regularly? | Trust (1–5) | Top feedback |
|------|------|----------------|-------------|-------------|
| | | | | |

## Decision
- [ ] **Keep and invest** — OpenClaw adds clear value, proceed to deeper integration
- [ ] **Iterate** — Promising but needs specific improvements before expanding
- [ ] **Defer** — Not ready yet, revisit after [specific milestone]

## Key findings
-

## Action items
-
```

---

## Constraints
- **No cloud AI** — all inference runs locally via Ollama. No family data leaves the network.
- **Authentik is the only identity source** — no separate user accounts in the agent runtime
- **Ollama GPU limitation on macOS Docker** — document the CPU-only constraint and native install alternative
- **This is a validation phase** — don't over-engineer. Get it working, get feedback, iterate.
- **Lane enforcement may be partial** — document what's enforced technically vs what relies on trust during the trial
- **Models are large** — a 3B parameter model is ~2GB. Budget disk space and note in README.

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] Ollama container starts and can pull a model
- [ ] Runtime container starts and connects to Ollama
- [ ] Authentik OIDC login works — each family member can sign in
- [ ] Per-user session isolation verified (User A cannot see User B's conversations)
- [ ] Admin agent can execute at least one platform script (`dr-verify` or `app-up`)
- [ ] User agent can interact with Immich (browse photos via API)
- [ ] Child agent has reduced capabilities vs user agent
- [ ] `openclaw.home` resolves via Caddy
- [ ] Service appears on Homepage dashboard
- [ ] Uptime Kuma monitor added
- [ ] README documents runtime decision, setup, lanes, tools, and limitations
- [ ] Evaluation templates created for family trial
- [ ] `docs/access-matrix.md` updated with OpenClaw lane mappings
