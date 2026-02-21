# Update Manager Deployment Guide

This guide walks through deploying the complete update management system: Diun + Update Handler.

## Prerequisites

- Caddy running and configured
- Authentik running with homelab-admin group
- scripts/app-update and scripts/app-backup exist and are executable

## Step 1: Deploy Diun

```bash
cd ~/dev/homelab

# No .env needed for Diun (configuration in config/diun.yml)
docker compose -f platform/diun/compose.yml up -d

# Verify it's running
docker ps | grep diun

# Check logs
docker compose -f platform/diun/compose.yml logs -f
```

Expected log output:
```
Diun v4.28.0
Starting notification providers...
Watching Docker containers...
```

## Step 2: Deploy Update Handler

```bash
# No .env needed (uses defaults)
docker compose -f platform/update-handler/compose.yml up -d

# Verify it's running
docker ps | grep update-handler

# Check logs
docker compose -f platform/update-handler/compose.yml logs -f
```

Expected log output:
```
Initializing database at /app/data/updates.db...
Update Handler listening on port 8080
Dashboard: http://localhost:8080/
Webhook endpoint: http://localhost:8080/webhook
```

## Step 3: Reload Caddy

```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Expected output:
```
Successfully reloaded
```

## Step 4: Verify Access

1. Open http://updates.home in browser
2. Should redirect to Authentik login
3. Log in as homelab-admin
4. Should see Update Manager dashboard (empty initially)

## Step 5: Test with Manual Webhook

```bash
# Send a test webhook to verify the integration works
docker exec -it update-handler curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": {
      "image": "ghcr.io/immich-app/immich-server:v999.99.99",
      "status": "new",
      "created": "2026-02-21T10:00:00Z",
      "digest": "sha256:test123"
    },
    "metadata": {
      "name": "immich-server"
    }
  }'
```

Expected response:
```json
{"status": "received"}
```

Now refresh http://updates.home — you should see a pending update for Immich.

## Step 6: Test Update Approval (Optional)

**WARNING:** Only test with a non-critical service or a fake version that doesn't exist.

If you created a test update in Step 5:

1. Go to http://updates.home
2. Click "Dismiss" on the test update (since v999.99.99 doesn't exist)
3. Verify it disappears from the pending list

## Step 7: Trigger Manual Check

Force Diun to check for updates now (instead of waiting 2 hours):

```bash
docker exec diun diun once
```

Watch the logs:
```bash
docker compose -f platform/diun/compose.yml logs -f
```

You should see:
- Registry queries for each running container
- Webhook POSTs to update-handler (if updates found)

## Step 8: Monitor in Homepage

Reload http://home.home — you should see:
- **Diun** in Platform section (no href, background service)
- **Update Manager** in Platform section with link to http://updates.home

## Verification Checklist

- [ ] Diun container running and healthy
- [ ] Update-handler container running and healthy
- [ ] http://updates.home accessible (requires Authentik login)
- [ ] Dashboard shows "No pending updates" (or detected updates if any exist)
- [ ] Test webhook received successfully
- [ ] Caddy routing works (login redirect, dashboard loads)
- [ ] Homepage shows Update Manager link

## Troubleshooting

### Diun not detecting updates

1. Check Diun is watching containers:
   ```bash
   docker exec diun diun once
   ```

2. Verify containers use explicit version tags (not `latest`)

3. Check logs for errors:
   ```bash
   docker compose -f platform/diun/compose.yml logs
   ```

### Update Handler webhook not received

1. Check both containers on caddy-net:
   ```bash
   docker network inspect caddy-net | grep -E "(diun|update-handler)"
   ```

2. Test webhook manually (see Step 5)

3. Check update-handler logs:
   ```bash
   docker compose -f platform/update-handler/compose.yml logs
   ```

### Dashboard not accessible

1. Check Caddy routing:
   ```bash
   docker exec caddy curl -s http://update-handler:8080/health
   # Expected: OK
   ```

2. Check Authentik is running:
   ```bash
   docker ps | grep authentik
   ```

3. Verify you're logged in as homelab-admin user

### Updates not executing

1. Check scripts/app-update is executable:
   ```bash
   ls -l scripts/app-update
   # Expected: -rwxr-xr-x
   ```

2. Test manual update:
   ```bash
   AUTO_APPROVE=true scripts/app-update immich v1.130.3
   ```

3. Check database for error messages:
   ```bash
   sqlite3 platform/update-handler/data/updates.db \
     "SELECT * FROM updates WHERE status='failed';"
   ```

## Next Steps

### Configure Diun Check Interval

Default is every 2 hours. To change:

1. Edit `platform/diun/config/diun.yml`:
   ```yaml
   watch:
     schedule: "0 */6 * * *"  # Every 6 hours
   ```

2. Restart Diun:
   ```bash
   docker compose -f platform/diun/compose.yml restart
   ```

### Exclude Containers from Monitoring

Add label to container's compose.yml:

```yaml
services:
  myapp:
    image: example/app:v1.0.0
    labels:
      - diun.enable=false
```

### Add to Uptime Kuma

Monitor both services:

1. **Diun**:
   - Type: Docker Container
   - Container: diun

2. **Update Handler**:
   - Type: HTTP(s)
   - URL: http://update-handler:8080/health
   - Expected: 200 OK

## Backup

Both services have minimal persistent state:

- Diun: No state (configuration in git)
- Update Handler: `data/updates.db` (history, optional)

To backup:
```bash
scripts/backup-all --service update-handler
```

## Uninstall

```bash
# Stop and remove containers
docker compose -f platform/update-handler/compose.yml down
docker compose -f platform/diun/compose.yml down

# Remove data (optional)
rm -rf platform/update-handler/data
rm -rf platform/diun/data

# Remove from Caddyfile (manual)
# Remove from Homepage (manual)
```
