# Bootstrap — New Machine Setup

> How to go from a brand-new Mac mini to a fully running homelab platform.

This document covers everything needed to reproduce the platform from scratch: dependencies, code, secrets, startup, health verification, and application integration.

---

## 1. Dependencies

Install these on the Mac mini before doing anything else.

### Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Git

```bash
brew install git
```

### Docker Desktop

Download from https://www.docker.com/products/docker-desktop/ and install the Apple Silicon build.

After installation:
1. Open Docker Desktop and complete the setup wizard
2. Go to **Settings → Resources** and configure:
   - CPUs: leave at least 4 cores for macOS/Minecraft
   - Memory: 8–12 GB (leave remainder for the host)
   - Disk: 60+ GB
3. Go to **Settings → General** → enable **"Start Docker Desktop when you log in"**
4. Verify: `docker version` and `docker compose version`

### Restic (for backups)

```bash
brew install restic
```

---

## 2. Get the Code

```bash
git clone <your-repo-url> ~/dev/homelab
cd ~/dev/homelab
```

Set `HOMELAB_DIR` permanently so all scripts find the repo:

```bash
echo 'export HOMELAB_DIR="$HOME/dev/homelab"' >> ~/.zshrc
source ~/.zshrc
```

---

## 3. Create Secrets

Each stack needs a `.env` file with generated secrets. Run these from the repo root.

### Caddy

Caddy has no secrets — the `.env` file is optional:

```bash
cp platform/caddy/.env.example platform/caddy/.env
```

### Dockge

```bash
cp platform/dockge/.env.example platform/dockge/.env
```

### Homepage

```bash
cp platform/homepage/.env.example platform/homepage/.env
```

### Uptime Kuma

```bash
cp platform/uptime-kuma/.env.example platform/uptime-kuma/.env
```

### Tailscale

```bash
cp platform/tailscale/.env.example platform/tailscale/.env
# Edit and set TS_AUTHKEY — generate at https://login.tailscale.com/admin/settings/keys
# Use a reusable, non-expiring auth key
```

### Authentik

```bash
cp platform/authentik/.env.example platform/authentik/.env

# Generate secrets
SECRET_KEY=$(openssl rand -base64 60)
POSTGRES_PASS=$(openssl rand -base64 32)
BOOTSTRAP_TOKEN=$(openssl rand -hex 32)

# Write them into .env
cat > platform/authentik/.env << EOF
AUTHENTIK_SECRET_KEY=${SECRET_KEY}
POSTGRES_DB=authentik
POSTGRES_USER=authentik
POSTGRES_PASSWORD=${POSTGRES_PASS}
AUTHENTIK_POSTGRESQL__HOST=authentik-db
AUTHENTIK_POSTGRESQL__PORT=5432
AUTHENTIK_POSTGRESQL__NAME=authentik
AUTHENTIK_POSTGRESQL__USER=authentik
AUTHENTIK_POSTGRESQL__PASSWORD=${POSTGRES_PASS}
AUTHENTIK_REDIS__HOST=authentik-redis
AUTHENTIK_REDIS__PORT=6379
AUTHENTIK_BOOTSTRAP_PASSWORD=changeme
AUTHENTIK_BOOTSTRAP_TOKEN=${BOOTSTRAP_TOKEN}
EOF
```

> After first-run setup is complete, comment out `AUTHENTIK_BOOTSTRAP_PASSWORD` and `AUTHENTIK_BOOTSTRAP_TOKEN` and restart Authentik.

### Immich

```bash
cp apps/immich/.env.example apps/immich/.env

DB_PASS=$(openssl rand -base64 32)
cat > apps/immich/.env << EOF
IMMICH_VERSION=v2.5.6
UPLOAD_LOCATION=./data/upload
DB_DATABASE_NAME=immich
DB_USERNAME=immich
DB_PASSWORD=${DB_PASS}
EOF
```

---

## 4. Configure /etc/hosts

All `.home` hostnames are resolved via `/etc/hosts`. Add these entries:

```bash
sudo tee -a /etc/hosts << 'EOF'

# Homelab platform
127.0.0.1 home.home
127.0.0.1 status.home
127.0.0.1 login.home
127.0.0.1 dockge.home
127.0.0.1 immich.home
EOF
```

---

## 5. Start the Platform

```bash
scripts/platform-up
```

This starts all services in the correct boot order:
1. Tailscale
2. Caddy (creates `caddy-net`)
3. Authentik (waits for DB and Redis health checks)
4. Uptime Kuma
5. Homepage
6. Dockge
7. All stacks in `apps/`

The first run will pull all Docker images — this takes several minutes.

**Authentik first run** takes ~60 seconds for database migrations. Watch progress:

```bash
docker compose -f platform/authentik/compose.yml logs -f authentik-server
# Wait for: "Starting server" or "Nest application successfully started"
```

---

## 6. Verify Health

```bash
scripts/dr-verify
```

Expected output on a clean first run:

```
✓ platform/authentik: 4/4 containers running
✓ platform/caddy: 1/1 containers running
✓ platform/dockge: 1/1 containers running
✓ platform/homepage: 1/1 containers running
✓ platform/tailscale: 1/1 containers running
✓ platform/uptime-kuma: 1/1 containers running
✓ apps/immich: 4/4 containers running

✓ Caddy: HTTP 200
✓ Homepage: HTTP 200 (via caddy)
✓ Uptime Kuma: HTTP 200 (via caddy)
✓ Authentik: HTTP 200 (via caddy)
✓ Immich: HTTP 200 (via caddy)

⚠ No backup found in the last 26h   ← expected on fresh install
```

If any containers show 0/N, check logs:

```bash
docker logs <container-name> 2>&1 | tail -30
```

---

## 7. Authentik First-Run Setup

### Create your admin account

1. Navigate to `http://login.home/if/flow/initial-setup/`
2. Log in with `akadmin` and the `AUTHENTIK_BOOTSTRAP_PASSWORD` you set
3. Follow `docs/onboarding.md` to:
   - Create your personal admin account
   - Create groups: `homelab-admin`, `parents`, `kids`
   - Add yourself to `homelab-admin`
   - Disable or restrict `akadmin`

---

## 8. Wire Immich to Authentik (Automated)

The `scripts/setup-authentik-immich` script uses the Authentik API to create the OIDC provider, application, and group bindings automatically.

**Run it:**

```bash
scripts/setup-authentik-immich
```

The script will print the Client ID and Client Secret it created.

**Then configure Immich:**

1. Go to `http://immich.home` → log in with your local admin account
2. Go to **Administration → Settings → OAuth**
3. Enable OAuth and fill in:
   - **Issuer URL:** `http://login.home/application/o/immich/`
   - **Client ID:** (printed by script)
   - **Client Secret:** (printed by script)
   - **Scope:** `openid profile email`
   - **Button text:** `Login with Authentik`
   - Enable **Auto-register new users**
4. Save and test — click "Login with Authentik" on the login page

> The Issuer URL must use `login.home` (not `authentik-server:9000`). The `immich-server` container resolves `login.home` via `host-gateway` (configured in `apps/immich/compose.yml`), which routes through Caddy to Authentik and ensures browser-facing URLs in the OIDC discovery document are correct.

**After setup is complete**, comment out the bootstrap credentials so they aren't active on subsequent restarts:

```bash
sed -i '' 's/^AUTHENTIK_BOOTSTRAP_PASSWORD=/#AUTHENTIK_BOOTSTRAP_PASSWORD=/' platform/authentik/.env
sed -i '' 's/^AUTHENTIK_BOOTSTRAP_TOKEN=/#AUTHENTIK_BOOTSTRAP_TOKEN=/' platform/authentik/.env
docker compose -f platform/authentik/compose.yml up -d
```

---

## 9. Adding Users

Once Authentik and Immich are wired:

1. Go to `http://login.home/if/admin/` → **Directory → Users → Create**
2. Fill in username, name, email, and set a password
3. Go to **Directory → Groups → immich-user** → add the user
4. The user logs in at `http://immich.home` → "Login with Authentik" → their Immich account is created automatically on first sign-in

See `docs/onboarding.md` for the full user lifecycle (invitations, access changes, offboarding).

---

## 10. Auto-Start on Boot (macOS)

Docker Desktop handles its own auto-start. To ensure platform services start after Docker Desktop launches on login, create a launchd agent:

```bash
cat > ~/Library/LaunchAgents/com.homelab.platform-up.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.homelab.platform-up</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>sleep 30 &amp;&amp; HOMELAB_DIR=$HOME/dev/homelab $HOME/dev/homelab/scripts/platform-up</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/homelab-platform-up.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/homelab-platform-up.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.homelab.platform-up.plist
```

The `sleep 30` gives Docker Desktop time to start its daemon before the script runs.

Check logs after reboot:

```bash
cat /tmp/homelab-platform-up.log
```

---

## Quick Reference

| URL | Service |
|-----|---------|
| `http://home.home` | Homepage dashboard |
| `http://status.home` | Uptime Kuma monitoring |
| `http://login.home` | Authentik SSO |
| `http://dockge.home` | Dockge stack manager |
| `http://immich.home` | Immich photo library |

| Script | Purpose |
|--------|---------|
| `scripts/platform-up` | Start all services in correct order |
| `scripts/platform-down` | Stop all services |
| `scripts/dr-verify` | Health check and DR readiness |
| `scripts/validate-compose` | Validate all compose files |
| `scripts/setup-authentik-immich` | Wire Immich OIDC via API |
| `scripts/app-backup <name>` | Back up a single app's data |

---

## Troubleshooting

**Caddy returns 502 for a service**
The service container may have lost its `caddy-net` connection. Fix:
```bash
docker network connect caddy-net <container-name>
```

**"caddy-net not found" when starting an app stack**
Start Caddy first — it creates the network:
```bash
docker compose -f platform/caddy/compose.yml up -d
```

**Immich OAuth discovery error**
`login.home` not resolving inside the `immich-server` container. Check:
```bash
docker exec immich-server curl -s http://login.home/api/v3/ -o /dev/null -w "%{http_code}"
# Should return 200. If not, restart the Immich stack:
docker compose -f apps/immich/compose.yml up -d
```

**Authentik API returns 403 on setup script**
The bootstrap token may not have been picked up. Verify it's in `.env` and restart:
```bash
grep AUTHENTIK_BOOTSTRAP_TOKEN platform/authentik/.env
docker compose -f platform/authentik/compose.yml up -d
```
