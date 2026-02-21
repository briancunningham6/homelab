# Diun — Docker Image Update Notifier

Monitors Docker containers for available image updates and sends notifications when new versions are detected.

## Quick Reference

| Item | Value |
|------|-------|
| Image | `crazymax/diun:4.28.0` |
| Container | `diun` |
| Port | None (background service) |
| Webhook endpoint | `http://update-handler:8080/webhook` |
| Health check | `diun version` |
| Auth | None (internal service) |

## What Diun Does

- **Monitors Docker images** — Checks registries every 2 hours for new versions
- **Sends webhooks** — Notifies update-handler when updates detected
- **Zero action** — Does NOT automatically update containers (notification only)
- **Configurable exclusions** — Can exclude specific containers via labels

## Commands

```bash
# Start
docker compose -f platform/diun/compose.yml up -d

# Stop
docker compose -f platform/diun/compose.yml down

# Logs
docker compose -f platform/diun/compose.yml logs -f

# Restart
docker compose -f platform/diun/compose.yml restart

# Force check now (manual trigger)
docker exec diun diun once

# View current config
docker exec diun cat /diun.yml
```

## Configuration

All configuration is in [config/diun.yml](config/diun.yml).

### Check Schedule

Default: Every 2 hours (`0 */2 * * *`)

To change the schedule, edit `config/diun.yml`:

```yaml
watch:
  schedule: "0 */6 * * *"  # Every 6 hours
```

### Excluding Containers

To exclude a container from monitoring, add a label to its compose.yml:

```yaml
services:
  myapp:
    image: example/app:latest
    labels:
      - diun.enable=false  # Don't monitor this container
```

### Notification Flow

```
Diun (detects new version)
  ↓
Sends webhook to update-handler
  ↓
Update-handler stores in database
  ↓
Admin views in Update Manager UI
  ↓
Admin clicks "Approve & Update"
  ↓
scripts/app-update executes
  ↓
Container updated
```

## How It Works

1. **Every 2 hours**, Diun queries container registries (Docker Hub, GHCR, etc.)
2. Compares image digests: local vs. remote
3. If remote is newer, sends webhook to update-handler
4. Webhook includes:
   - Image name and new tag
   - Digest (SHA256)
   - Container metadata (name, labels)
   - Timestamp

## Monitored Containers

Diun automatically watches **all running containers** in:
- `apps/*/compose.yml`
- `platform/*/compose.yml`
- `ai/*/compose.yml`

Stopped containers are **not monitored** (to avoid noise).

## Troubleshooting

### No updates detected (but I know there's a new version)

1. Check Diun logs:
   ```bash
   docker compose -f platform/diun/compose.yml logs -f
   ```

2. Verify container is being watched:
   ```bash
   docker exec diun diun once
   ```

3. Check if container has `diun.enable=false` label

4. Verify image tag format (must be explicit version, not `latest`)

### Webhook not reaching update-handler

1. Check both containers are on `caddy-net`:
   ```bash
   docker network inspect caddy-net
   ```

2. Test webhook manually:
   ```bash
   curl -X POST http://update-handler:8080/webhook \
     -H "Content-Type: application/json" \
     -d '{"entry":{"image":"test:v1.0.0"}}'
   ```

3. Check update-handler logs:
   ```bash
   docker compose -f platform/update-handler/compose.yml logs -f
   ```

### False positives (detecting updates that aren't real)

This can happen with images that use mutable tags (like `latest` or `stable`). Use pinned versions (e.g., `v1.2.3`) to avoid this.

## Environment Variables

See [.env.example](.env.example) for configuration options.

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `America/New_York` | Timezone for scheduling |
| `LOG_LEVEL` | `info` | Log verbosity (trace, debug, info, warn, error) |
| `LOG_JSON` | `false` | Use JSON logging format |

## Integration with Update Manager

Diun does NOT have a web UI. To view detected updates, use the Update Manager:

1. Open http://updates.home (requires Authentik homelab-admin)
2. View pending updates
3. Click "Approve & Update" to trigger update workflow
4. Or click "Dismiss" to ignore the update

## Backup

No persistent state to backup. Configuration is in git-tracked `config/diun.yml`.

## Monitoring

### In Uptime Kuma

- Type: Docker Container
- Container name: `diun`
- Check: Container running

### Health Check

```bash
docker exec diun diun version
```

Expected output: `Diun v4.28.0`

## Upstream

- Website: https://crazymax.dev/diun/
- Documentation: https://crazymax.dev/diun/config/
- GitHub: https://github.com/crazy-max/diun
- Docker Hub: https://hub.docker.com/r/crazymax/diun
