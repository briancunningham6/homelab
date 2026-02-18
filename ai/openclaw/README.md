# OpenClaw — AI Agent Gateway

> Chat-first AI assistant for the homelab, powered by [OpenClaw](https://openclaw.ai).

OpenClaw is a **native Gateway process** that bridges messaging apps (WhatsApp, Telegram, Discord) to AI agents (Anthropic Claude, OpenAI GPT). It runs directly on the Mac mini — not in a Docker container.

## Architecture

```
WhatsApp / Telegram ──┐
                      ├── OpenClaw Gateway (localhost:18789) ──┬── brian agent (full access)
Control UI ───────────┘       │                                └── family agent (sandboxed)
                              │
                    Skills: homelab-immich, homelab-ops, homelab-status
                              │
                    Platform: Docker, Caddy, Authentik, Immich, ...
```

## Quick Reference

| Item            | Value                                  |
| --------------- | -------------------------------------- |
| Runtime         | Node.js ≥ 22 (native, not Docker)     |
| Gateway         | `http://localhost:18789`               |
| Tailscale       | `https://mac-mini.tail*.ts.net` (Serve)|
| Config          | `~/.openclaw/openclaw.json`            |
| Daemon          | `launchd` (macOS)                      |
| LLM             | Anthropic Claude Sonnet 4.5            |
| Channels        | WhatsApp (primary), Telegram (optional)|
| Agents          | `brian` (admin), `family` (sandboxed)  |
| Repo config     | `ai/openclaw/config/openclaw.json`     |

## Prerequisites

- **Node.js ≥ 22**: `brew install node@22`
- **Anthropic API key** or Claude Pro/Max subscription
- **WhatsApp** on your phone (for pairing)
- Platform services running (`scripts/platform-up`)

## Installation

```bash
# Install OpenClaw
curl -fsSL https://get.openclaw.ai | sh
# — or —
npm install -g openclaw@latest

# Onboard (interactive setup — connects WhatsApp, sets API key)
openclaw onboard

# Install as launchd daemon (auto-start on boot)
openclaw onboard --install-daemon
```

## Configuration

The repo contains the config template at `ai/openclaw/config/openclaw.json`.

```bash
# Copy config to OpenClaw's config directory
cp ~/homelab/ai/openclaw/config/openclaw.json ~/.openclaw/openclaw.json

# Copy environment variables
cp ~/homelab/ai/openclaw/.env.example ~/.openclaw/.env
# Edit ~/.openclaw/.env with your actual keys
```

### Environment Variables

Create `~/.openclaw/.env` (or export directly):

```bash
ANTHROPIC_API_KEY=sk-ant-...          # Required: Anthropic API key
IMMICH_API_KEY=...                     # For homelab-immich skill
OPENCLAW_HOOKS_TOKEN=...              # Webhook auth token
OPENCLAW_GATEWAY_TOKEN=...            # Control UI auth token
```

## Agent Setup

### Brian (Admin Agent)

Full access to all platform tools. Workspace files:

```bash
# Copy workspace files
cp -r ~/homelab/ai/openclaw/workspace-brian/ ~/.openclaw/workspace-brian/
```

### Family (Sandboxed Agent)

Read-only access, no destructive commands. Runs in Docker sandbox.

```bash
cp -r ~/homelab/ai/openclaw/workspace-family/ ~/.openclaw/workspace-family/
```

## Skills

Skills teach agents about specific platform capabilities. They live in `ai/openclaw/skills/` and are loaded via the `skills.load.extraDirs` config option.

| Skill              | Purpose                                        |
| ------------------ | ---------------------------------------------- |
| `homelab-immich`   | Photo search, albums, statistics via Immich API |
| `homelab-ops`      | Platform scripts, Docker management, updates    |
| `homelab-status`   | Health monitoring, disk/CPU, log inspection     |

Skills are Markdown files with YAML frontmatter — edit them directly to teach the agent new patterns.

## Webhook Integration

### Uptime Kuma → OpenClaw

Configure Uptime Kuma to send alerts when services go down:

1. Open Uptime Kuma → Settings → Notifications
2. Add Webhook notification:
   - **URL**: `http://localhost:18789/hooks/agent`
   - **Header**: `Authorization: Bearer <OPENCLAW_HOOKS_TOKEN>`
   - **Body**: `{"msg": "🔴 {{monitorJSON.name}} is DOWN — {{msg}}", "sessionKey": "hook:uptime-kuma"}`

## Scheduled Tasks (Cron)

Set up via the OpenClaw Control UI or agent conversation:

| Schedule       | Task                                    |
| -------------- | --------------------------------------- |
| Daily 07:00    | Morning briefing (status + weather)     |
| Daily 09:00    | Backup freshness check                  |
| Sunday 10:00   | Weekly platform report                  |

## Operations

```bash
# Check Gateway status
openclaw status

# View logs
openclaw logs --tail 50

# Restart daemon
openclaw daemon restart

# Update OpenClaw
npm update -g openclaw@latest
openclaw daemon restart
```

## Caddy Integration

The Caddyfile proxies `openclaw.home` to the native Gateway:

```
http://openclaw.home {
    reverse_proxy 127.0.0.1:18789
}
```

This gives LAN access to the Control UI dashboard.

## Data & Backup

OpenClaw state lives in `~/.openclaw/`:

```
~/.openclaw/
├── openclaw.json          # Gateway config
├── workspace-brian/       # Admin agent workspace + memory
├── workspace-family/      # Family agent workspace + memory
├── agents/                # Agent runtime state
├── sessions/              # Conversation history
└── skills/                # Global skills (if any)
```

Back up `~/.openclaw/` alongside the homelab repo. Sessions and memory are the most important — config and skills are in the repo.

## Differences from Previous Design

This replaces the earlier Open WebUI-based design. Key changes:

| Aspect       | Old (Open WebUI)               | New (OpenClaw)                  |
| ------------ | ------------------------------ | ------------------------------- |
| Runtime      | Docker container               | Native Node.js process          |
| Interface    | Web UI                         | WhatsApp / Telegram / Discord   |
| Auth         | Authentik OIDC SSO             | Channel identity (phone number) |
| LLM          | OpenAI API / local Ollama      | Anthropic Claude (cloud)        |
| Multi-user   | User accounts in Open WebUI    | Multi-agent routing by binding  |
| Tools        | Open WebUI tool plugins        | exec, browser, cron, webhooks   |
