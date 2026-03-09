# ntfy

Push notification service for the homelab. Missions (and other apps) send alerts here; you receive them on your phone via the ntfy app.

## Quick reference

| Item | Value |
|------|-------|
| Image | `binwiederhier/ntfy:v2.11.0` |
| Hostname | `ntfy.home` |
| Internal port | 80 |
| Health endpoint | `http://ntfy.home/healthz` |

## Setup

### 1. Deploy ntfy

```bash
cd ~/homelab/platform/ntfy
cp .env.example .env
docker compose up -d
```

### 2. Install ntfy on your phone

- iOS / Android: search **ntfy** in the App Store / Play Store (free, by binwiederhier)
- Open the app → **Subscribe to topic**
- Server URL: `http://ntfy.home` (on LAN) or your Tailscale IP, e.g. `http://100.x.x.x`
- Topic: `missions`

> **Tip for remote access**: set the server URL to your Tailscale machine address so notifications arrive wherever you are.

### 3. Test

In the Missions app, open any mission and tap the 🔔 bell button in the header. You should receive a notification within a few seconds.

Or via curl:

```bash
curl -H "Title: Test" -d "Hello from homelab" http://ntfy.home/missions
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `America/New_York` | Timezone |
| `NTFY_BASE_URL` | `http://ntfy.home` | Public base URL (used in notification links) |

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f ntfy

# Update
docker compose pull && docker compose up -d
```

## How Missions uses ntfy

The Missions backend sends a notification after every **autonomous check** (hourly/daily/weekly):

- If new suggested actions were created → **high** priority with a lightbulb tag and a deep-link to the mission
- If the check completed with no new suggestions → **low** priority

Notifications are sent to the topic configured in `NTFY_TOPIC` (default: `missions`).

## Backup

ntfy stores a cache database in `./data/cache/` and auth state in `./data/lib/`. These are lightweight and regenerated on restart — no backup required.
