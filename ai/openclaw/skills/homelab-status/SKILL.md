---
name: homelab-status
description: Monitor homelab health — container status, resource usage, disk space, uptime, and service availability.
metadata:
  openclaw:
    requires:
      - exec
      - web_fetch
---

# Homelab — Status & Health Monitoring

You can check the health of all homelab services and the host system.

## Quick Health Check

Run this to get a fast overview:

```bash
echo "=== Containers ===" && \
docker ps --format "table {{.Names}}\t{{.Status}}" && \
echo "\n=== Disk ===" && \
df -h / /Volumes/* 2>/dev/null | grep -v "^$" && \
echo "\n=== Memory ===" && \
vm_stat | head -5 && \
echo "\n=== Docker Disk ===" && \
docker system df
```

## Container Status

```bash
# All containers with health status
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.State}}"

# Just unhealthy or exited containers
docker ps -a --filter "status=exited" --filter "health=unhealthy" \
  --format "table {{.Names}}\t{{.Status}}"
```

## Resource Usage

```bash
# CPU and memory per container
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

## Disk Space

```bash
# Host disk usage
df -h /

# Docker disk usage breakdown
docker system df -v

# Largest Docker volumes
docker system df -v 2>/dev/null | grep -A 100 "VOLUME NAME" | head -20
```

## Service Availability

Check each `*.home` endpoint from the host:

```bash
for svc in homepage dockge authentik immich uptime-kuma openclaw; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://${svc}.home" --max-time 3)
  printf "%-15s %s\n" "$svc" "$code"
done
```

Expected: all return `200` or `302` (redirect to login).

## Uptime Kuma Monitoring

Uptime Kuma tracks all services with configurable checks.

- **Dashboard**: `http://uptime-kuma.home`
- **Status page**: `http://uptime-kuma.home/status/homelab`

### Query Uptime Kuma API

```bash
# Get public status page data
curl -s "http://uptime-kuma.home/api/status-page/heartbeat/homelab"
```

### Webhook Integration (Inbound to OpenClaw)

Uptime Kuma can POST to OpenClaw's webhook endpoint when a monitor goes down:

```
POST http://localhost:18789/hooks/agent
Headers:
  Authorization: Bearer $OPENCLAW_HOOKS_TOKEN
  Content-Type: application/json
Body:
  {
    "msg": "🔴 {{monitorJSON.name}} is DOWN — {{msg}}",
    "sessionKey": "hook:uptime-kuma"
  }
```

Configure this in Uptime Kuma → Notifications → Webhook.

## Log Inspection

```bash
# Last 30 lines of a service's logs
docker compose -f ~/homelab/platform/caddy/compose.yml logs --tail 30

# Search logs for errors
docker compose -f ~/homelab/apps/immich/compose.yml logs --tail 200 | grep -i "error\|fatal\|panic"

# Caddy access logs (structured JSON)
docker compose -f ~/homelab/platform/caddy/compose.yml logs caddy --tail 100 | jq -r '.msg' 2>/dev/null || echo "Logs not in JSON format"
```

## macOS Host Health

```bash
# Uptime
uptime

# Top processes by CPU
ps aux --sort=-%cpu | head -10 2>/dev/null || ps aux | sort -nrk 3 | head -10

# Temperature (if iStats installed)
istats cpu temp 2>/dev/null || echo "iStats not installed"

# Network connectivity
ping -c 1 1.1.1.1 > /dev/null 2>&1 && echo "Internet: OK" || echo "Internet: DOWN"
ping -c 1 100.100.100.100 > /dev/null 2>&1 && echo "Tailscale: OK" || echo "Tailscale: DOWN"
```

## Cron-Worthy Checks

These are good candidates for OpenClaw cron jobs:

- **Morning briefing** (daily 07:00): container count, disk usage, any down monitors
- **Backup freshness** (daily 09:00): check last backup timestamp per app
- **Weekly report** (Sunday 10:00): storage trends, update availability, uptime summary

Example cron prompt for the agent:

> Run a quick health check. Report container status, disk usage, and any Uptime Kuma alerts. Keep it to 3-4 lines.

## Guidelines

- Present status in compact tables or bullet lists — don't dump raw command output.
- Highlight anything **unhealthy** or **abnormal** prominently.
- If a service is down, suggest the likely fix (usually `docker compose up -d` in the service directory).
- Report disk usage in human units. Flag if any filesystem is above 80%.
- For the family agent: only report high-level status ("everything is running" or "Immich is down"), never raw Docker output.
