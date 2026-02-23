# Task 11: OpenClaw — Deploy AI Agent Gateway

## Context

Read `CLAUDE.md` for project conventions. Read `ai/openclaw/README.md` for the full deployment guide. Read `ai/openclaw/config/openclaw.json` for the Gateway configuration.

**This task depends on Phases 1–3 being complete** — platform running, Authentik configured, at least one app (Immich) deployed.

**Important:** OpenClaw is a **native Node.js Gateway process** running on the Mac mini host — NOT a Docker container. It bridges messaging apps (WhatsApp, Telegram) to AI agents (Anthropic Claude). Authentication is via channel identity (phone numbers), not Authentik SSO.

- **Project:** https://openclaw.ai | https://github.com/openclaw/openclaw
- **Docs:** https://docs.openclaw.ai

## Objective

Install and configure the OpenClaw Gateway on the Mac mini with two agents:
- **brian** — full admin access to all platform tools
- **family** — sandboxed, read-only access for family members via group chat

## Existing Files (already in repo)

All config templates and skill files are drafted and ready to deploy:

```
ai/openclaw/
├── config/openclaw.json           # Gateway config — multi-agent routing, tools, hooks
├── skills/
│   ├── homelab-immich/SKILL.md    # Immich REST API skill
│   ├── homelab-ops/SKILL.md       # Platform operations skill
│   └── homelab-status/SKILL.md    # Health monitoring skill
├── workspace-brian/
│   ├── AGENTS.md                  # Admin agent persona
│   └── SOUL.md                    # Admin agent personality
├── workspace-family/
│   ├── AGENTS.md                  # Family agent persona (sandboxed)
│   └── SOUL.md                    # Family agent personality
├── .env.example                   # Environment variable template
├── app-contract.yaml              # Operational contract
└── README.md                      # Deployment guide
```

Platform files already updated:
- `platform/caddy/Caddyfile` — `openclaw.home` proxies to `127.0.0.1:18789`
- `platform/homepage/config/services.yaml` — OpenClaw entry (no Docker container ref)

## Requirements

### Part 1: Install OpenClaw

```bash
# Prerequisite: Node.js >= 22
brew install node@22
node --version  # Verify >= 22

# Install OpenClaw
curl -fsSL https://get.openclaw.ai | sh
# — or —
npm install -g openclaw@latest

# Verify
openclaw --version
```

### Part 2: Onboard & Pair WhatsApp

```bash
# Interactive onboard — sets up API key, pairs WhatsApp via QR code
openclaw onboard
```

During onboard:
1. Enter your Anthropic API key (or sign in with Claude Pro/Max)
2. Scan the WhatsApp QR code with your phone
3. Verify the test message arrives

### Part 3: Deploy Configuration

```bash
# Copy the repo config template to OpenClaw's config directory
cp ~/homelab/ai/openclaw/config/openclaw.json ~/.openclaw/openclaw.json

# Create .env from template
cp ~/homelab/ai/openclaw/.env.example ~/.openclaw/.env
# Edit ~/.openclaw/.env with real values:
#   ANTHROPIC_API_KEY=sk-ant-...
#   IMMICH_API_KEY=...  (generate at http://immich.home → User Settings → API Keys)
#   OPENCLAW_GATEWAY_TOKEN=...  (generate: openssl rand -hex 32)
#   OPENCLAW_HOOKS_TOKEN=...  (generate: openssl rand -hex 32)

# Copy agent workspace files
cp -r ~/homelab/ai/openclaw/workspace-brian/ ~/.openclaw/workspace-brian/
cp -r ~/homelab/ai/openclaw/workspace-family/ ~/.openclaw/workspace-family/
```

### Part 4: Edit Config Placeholders

Open `~/.openclaw/openclaw.json` and replace placeholder values:

| Placeholder | Replace with |
|-------------|-------------|
| `+1BRIAN_PHONE` | Your WhatsApp phone number (E.164 format) |
| `FAMILY_GROUP_ID@g.us` | Your family WhatsApp group ID |
| `+1PARTNER_PHONE` | Partner's phone (in `channels.whatsapp.allowFrom`) |

To find a WhatsApp group ID: send a message in the group after pairing, then check `openclaw logs` — the group peer ID appears in the log output.

### Part 5: Install as launchd Daemon

```bash
# Install daemon — OpenClaw starts on boot, restarts on crash
openclaw onboard --install-daemon

# Verify it's running
openclaw status
curl -s http://127.0.0.1:18789/  # Should return the Control UI
```

The Gateway runs as a `launchd` service at `~/Library/LaunchAgents/ai.openclaw.gateway.plist`.

### Part 6: Verify Caddy Proxy

After the Gateway is running, verify the Caddy proxy works:

```bash
# Reload Caddy with the updated Caddyfile
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# Test
curl -s -o /dev/null -w "%{http_code}" http://openclaw.home
# Expected: 200 or 302
```

### Part 7: Configure Uptime Kuma

Add a monitor in Uptime Kuma for the OpenClaw Gateway:

1. Open `http://status.home`
2. Add new monitor:
   - **Type:** HTTP(s)
   - **URL:** `http://127.0.0.1:18789/`
   - **Name:** OpenClaw Gateway
   - **Interval:** 60s

Then configure the webhook notification (so OpenClaw gets alerted when services go down):

1. Settings → Notifications → Add
2. **Type:** Webhook
3. **URL:** `http://127.0.0.1:18789/hooks/agent`
4. **Header:** `Authorization: Bearer <OPENCLAW_HOOKS_TOKEN>`
5. **Body:** `{"msg": "🔴 {{monitorJSON.name}} is DOWN — {{msg}}", "sessionKey": "hook:uptime-kuma"}`

### Part 8: Test the Agents

**Brian agent (WhatsApp DM):**
```
You: what containers are running?
→ Agent should use `exec` tool to run `docker ps` and return results

You: how much disk space is left?
→ Agent should run `df -h /` and summarise

You: search immich for beach photos
→ Agent should use the homelab-immich skill to call the Immich API
```

**Family agent (WhatsApp group, mention @homelab):**
```
@homelab is everything running?
→ Agent should report high-level status, no raw Docker output

@homelab find photos from Christmas
→ Agent should search Immich and describe results naturally
```

### Part 9: Set Up Cron Jobs

Via the Control UI (`http://openclaw.home`) or by messaging the brian agent:

```
You: set up a daily cron at 7am — run a quick health check and tell me container status, disk usage, and any alerts. Keep it brief.

You: set up a weekly cron on Sunday at 10am — give me a platform report: storage trends, any services that restarted this week, backup status.
```

---

## Constraints

- **Anthropic API key required** — obtain at console.anthropic.com or use Claude Pro/Max subscription ($20-200/mo). Never commit keys.
- **Conversation content sent to Anthropic's API** — chat text leaves the network, but files and photos stay local. The homelab-immich skill queries the local Immich API; only text descriptions are sent to the LLM.
- **No Authentik integration** — OpenClaw uses channel identity (phone numbers), not OIDC. This is fundamentally different from other platform apps.
- **Native process, not Docker** — OpenClaw runs on the host via `launchd`. It accesses Docker via the socket to manage containers and run the family agent sandbox.
- **WhatsApp pairing is per-device** — the Gateway links to one phone number. Multi-device is handled by WhatsApp's linked devices feature.
- **Family sandbox uses Docker** — the `family` agent runs commands inside a sandboxed container (no network, read-only workspace, memory-limited). Docker must be running for this to work.

## Acceptance Criteria

- [ ] `openclaw --version` runs successfully (Node.js >= 22, OpenClaw installed)
- [ ] `openclaw status` shows the Gateway is running
- [ ] `curl http://127.0.0.1:18789/` returns the Control UI
- [ ] `curl http://openclaw.home` returns the Control UI (Caddy proxy working)
- [ ] WhatsApp pairing complete — test message arrives
- [ ] Brian agent responds to WhatsApp DM with platform commands (docker ps, df, etc.)
- [ ] Brian agent can query Immich API via the homelab-immich skill
- [ ] Family agent responds in group chat when mentioned
- [ ] Family agent is sandboxed — cannot run destructive commands
- [ ] Gateway survives reboot (launchd daemon installed)
- [ ] Uptime Kuma monitor shows OpenClaw as UP
- [ ] Webhook from Uptime Kuma triggers an OpenClaw session (test by pausing a monitor)
- [ ] At least one cron job configured (morning health check)
- [ ] Homepage dashboard shows OpenClaw entry
- [ ] Skills loaded — verify via Control UI or `openclaw status`
