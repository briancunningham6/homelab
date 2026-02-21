# Update Handler — Container Update Management

Web-based dashboard for approving and executing container updates detected by Diun.

## Quick Reference

| Item | Value |
|------|-------|
| Image | `python:3.12-slim` |
| Container | `update-handler` |
| Port | 8080 (internal) |
| Hostname | `updates.home` |
| Health check | `GET /health → 200` |
| Auth | Authentik (admin only) |

## What Update Handler Does

- **Receives webhooks** from Diun when updates detected
- **Stores pending updates** in SQLite database
- **Provides web UI** to view, approve, or dismiss updates
- **Executes updates** via `scripts/app-update` when approved
- **Tracks history** of completed and failed updates

## Commands

```bash
# Start
docker compose -f platform/update-handler/compose.yml up -d

# Stop
docker compose -f platform/update-handler/compose.yml down

# Logs
docker compose -f platform/update-handler/compose.yml logs -f

# Restart
docker compose -f platform/update-handler/compose.yml restart

# View database
sqlite3 platform/update-handler/data/updates.db "SELECT * FROM updates;"

# Clear all pending updates
sqlite3 platform/update-handler/data/updates.db "DELETE FROM updates WHERE status='pending';"
```

## Access

Open http://updates.home in your browser.

**Authentication:** Requires Authentik login (homelab-admin group only)

## Dashboard UI

The dashboard shows:

- **Pending updates** — Detected by Diun, awaiting approval
- **Current version** — What's currently running
- **New version** — What's available
- **Detected time** — How long ago the update was found
- **Actions**:
  - **Approve & Update** — Trigger automatic update workflow
  - **Dismiss** — Mark as "won't update" (removes from pending list)

### Example

```
┌─────────────────────────────────────────────────────┐
│  Pending Updates                                    │
├─────────────────────────────────────────────────────┤
│  Immich                                             │
│  immich-server                                      │
│  v1.130.3 → v1.131.0                               │
│  Detected: 2 hours ago                              │
│  [Approve & Update]  [Dismiss]                      │
└─────────────────────────────────────────────────────┘
```

## Update Workflow

When you click **"Approve & Update"**, the following happens:

### Step 1: Pre-update Backup
- `scripts/app-backup <app>` runs
- Creates Restic backup or local tar archive
- Stored in `backups/` directory

### Step 2: Update Compose File
- `compose.yml` image tag updated
- Old: `image: ghcr.io/immich-app/immich-server:v1.130.3`
- New: `image: ghcr.io/immich-app/immich-server:v1.131.0`

### Step 3: Pull New Image
- `docker compose pull` downloads new version
- Verifies image integrity

### Step 4: Restart Containers
- `docker compose up -d` recreates containers
- Old containers stopped and removed
- New containers started

### Step 5: Health Check
- Waits 5 seconds for startup
- Checks container status
- If unhealthy: **automatic rollback** to previous version

### Step 6: Log Result
- Update marked as `completed` or `failed` in database
- Output stored for troubleshooting

### Step 7: Notification
- Dashboard updated with result
- Success: Update removed from pending list
- Failure: Error message displayed

## How It Works

### Webhook Endpoint

**POST `/webhook`**

Receives JSON from Diun:

```json
{
  "entry": {
    "image": "ghcr.io/immich-app/immich-server:v1.131.0",
    "status": "new",
    "created": "2026-02-21T10:00:00Z",
    "digest": "sha256:abc123..."
  },
  "metadata": {
    "name": "immich-server",
    "compose_project": "immich"
  }
}
```

### Database Schema

SQLite database at `data/updates.db`:

```sql
CREATE TABLE updates (
    id INTEGER PRIMARY KEY,
    app_name TEXT NOT NULL,
    container_name TEXT NOT NULL,
    current_image TEXT NOT NULL,
    new_image TEXT NOT NULL,
    new_tag TEXT NOT NULL,
    digest TEXT,
    detected_at TEXT NOT NULL,
    status TEXT NOT NULL,  -- pending, approved, completed, failed, dismissed
    approved_at TEXT,
    completed_at TEXT,
    result TEXT
);
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/dashboard` | GET | Dashboard UI (alias) |
| `/health` | GET | Health check (returns `OK`) |
| `/webhook` | POST | Receive Diun notifications |
| `/approve/<id>` | GET | Approve and execute update |
| `/dismiss/<id>` | GET | Dismiss update notification |

## Integration with Diun

This service **requires Diun** to function. The workflow is:

```
Diun (monitors registries)
  ↓
Detects new version
  ↓
POST /webhook → Update Handler
  ↓
Store in database
  ↓
Admin approves in UI
  ↓
Execute scripts/app-update
```

## Manual Update Workflow (Without Diun)

If you want to bypass Diun and manually trigger an update:

```bash
# Direct script execution
AUTO_APPROVE=true scripts/app-update immich v1.131.0

# Or via UI: manually insert into database
sqlite3 platform/update-handler/data/updates.db <<EOF
INSERT INTO updates (app_name, container_name, current_image, new_image, new_tag, detected_at, status)
VALUES ('immich', 'immich-server', 'ghcr.io/immich-app/immich-server:v1.130.3',
        'ghcr.io/immich-app/immich-server:v1.131.0', 'v1.131.0', datetime('now'), 'pending');
EOF
```

Then refresh http://updates.home and approve.

## Troubleshooting

### Webhook not received

1. Check Diun logs:
   ```bash
   docker compose -f platform/diun/compose.yml logs -f
   ```

2. Verify both containers on same network:
   ```bash
   docker network inspect caddy-net | grep -E "(diun|update-handler)"
   ```

3. Test webhook manually:
   ```bash
   curl -X POST http://update-handler:8080/webhook \
     -H "Content-Type: application/json" \
     -d '{"entry":{"image":"test:v1.0.0","status":"new"},"metadata":{"name":"test"}}'
   ```

### Update failed

1. View update logs in database:
   ```bash
   sqlite3 platform/update-handler/data/updates.db \
     "SELECT app_name, status, result FROM updates WHERE status='failed' ORDER BY id DESC LIMIT 5;"
   ```

2. Check app-update script logs (output stored in database `result` column)

3. Verify `scripts/app-update` is executable:
   ```bash
   ls -l scripts/app-update
   ```

4. Test update manually:
   ```bash
   AUTO_APPROVE=true scripts/app-update <app> <version>
   ```

### Dashboard not loading

1. Check container health:
   ```bash
   docker ps | grep update-handler
   ```

2. Check Caddy routing:
   ```bash
   docker exec caddy curl -s http://update-handler:8080/health
   ```

3. Check Authentik forward-auth (must be logged in as homelab-admin)

### Permission errors

Update handler needs access to:
- `/var/run/docker.sock` (to inspect containers)
- `scripts/app-update` (must be executable)
- `data/` directory (must be writable)

Check permissions:
```bash
ls -l /var/run/docker.sock
ls -l scripts/app-update
ls -ld platform/update-handler/data/
```

## Security Considerations

### Admin-Only Access

- Web UI protected by Authentik forward-auth
- Only homelab-admin group can approve updates
- Webhook endpoint is internal-only (not exposed via Caddy)

### Automatic Updates

- Updates are **NOT automatic** — admin approval required
- `AUTO_APPROVE=true` only used when triggered via UI
- Rollback happens automatically on health check failure

### Secrets

- No secrets stored in database
- No credentials required for operation
- Inherits Docker socket access from host

## Backup

### What to Backup

- `data/updates.db` — Update history (optional, regeneratable)

### Backup Command

```bash
# Included in platform backup
scripts/backup-all --service update-handler

# Manual backup
cp platform/update-handler/data/updates.db backups/update-handler-$(date +%Y%m%d).db
```

### Restore

```bash
# Restore from backup
cp backups/update-handler-YYYYMMDD.db platform/update-handler/data/updates.db

# Or start fresh (database auto-created on startup)
rm platform/update-handler/data/updates.db
docker compose -f platform/update-handler/compose.yml restart
```

## Monitoring

### In Uptime Kuma

- Type: HTTP(s)
- URL: `http://update-handler:8080/health`
- Expected: 200 OK

### Health Check

```bash
curl http://updates.home/health
# Expected: OK
```

## Future Enhancements

Potential improvements (not yet implemented):

1. **Email notifications** — Send email when updates detected
2. **Changelog integration** — Fetch release notes from GitHub
3. **Scheduled updates** — Auto-approve at specific times
4. **Update groups** — Batch update related services
5. **Rollback UI** — One-click rollback to previous version
6. **Audit log** — Track who approved which updates

## Upstream

This is a custom service built specifically for this homelab platform.

**Dependencies:**
- Python 3.12
- SQLite3
- Docker CLI (via socket mount)

**Related:**
- Diun: https://crazymax.dev/diun/
- scripts/app-update: [../../scripts/app-update](../../scripts/app-update)
- scripts/app-backup: [../../scripts/app-backup](../../scripts/app-backup)
