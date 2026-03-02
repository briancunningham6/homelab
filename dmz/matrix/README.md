# Matrix (Conduit)

Lightweight Matrix homeserver for secure, federated messaging.

**Deployment Node:** DMZ Pi (`homelab-pi-dmz`) — NOT the Mac mini

## Quick Reference

| Property | Value |
|----------|-------|
| Image | `matrixconduit/matrix-conduit` |
| Version | v0.8.0 |
| Internal Port | 6167 |
| External Ports | 443 (HTTPS), 8448 (federation) |
| Health Endpoint | `/_matrix/client/versions` |
| Data Directory | `./data/conduit/` |
| Hostname | `matrix.yourdomain.com` (public DNS) |

## What is Matrix?

Matrix is an open protocol for secure, decentralized, real-time communication. Conduit is a lightweight Matrix homeserver written in Rust that runs efficiently on Raspberry Pi hardware.

### Why Conduit over Synapse?

| Factor | Synapse | Conduit |
|--------|---------|---------|
| Language | Python | Rust |
| Memory | 500MB-2GB+ | ~50-100MB |
| Pi Performance | Sluggish | Excellent |
| Maturity | Reference implementation | Newer, actively developed |

## Prerequisites

Before deploying Matrix:

1. **Domain name** with DNS pointing to your home IP
2. **Router port forwarding** configured:
   - Port 80 → DMZ Pi (for Let's Encrypt)
   - Port 443 → DMZ Pi (HTTPS)
   - Port 8448 → DMZ Pi (Matrix federation)
3. **Caddy installed** on DMZ Pi for TLS termination
4. **Tailscale configured** on DMZ Pi for backups and optional Authentik access

## Installation

### 1. Configure Environment

```bash
cd ~/homelab/dmz/matrix
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# REQUIRED: Your public Matrix domain
CONDUIT_SERVER_NAME=matrix.yourdomain.com

# Enable registration to create first user (disable after)
CONDUIT_ALLOW_REGISTRATION=true

# Enable federation for public Matrix network
CONDUIT_ALLOW_FEDERATION=true
```

Edit `config/conduit.toml` and set your real public domain:

```toml
server_name = "matrix.yourdomain.com"
```

### 2. Configure Caddy on DMZ Pi

Add to `/etc/caddy/Caddyfile` on the DMZ Pi:

```caddyfile
matrix.yourdomain.com {
    reverse_proxy localhost:6167
}

matrix.yourdomain.com:8448 {
    reverse_proxy localhost:6167
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

### 3. Create Data Directory

```bash
mkdir -p ./data/conduit
sudo chown 1000:1000 ./data/conduit
```

### 4. Start Conduit

```bash
docker compose up -d
```

### 5. Create Admin User

The **first user registered becomes the admin**. Register immediately:

```bash
# Using Element or another Matrix client, register at:
# https://matrix.yourdomain.com

# Or via command line:
docker exec -it conduit /usr/local/bin/conduit-admin register <username> <password>
```

### 6. Disable Registration

After creating your accounts, disable public registration:

```bash
# Edit .env
CONDUIT_ALLOW_REGISTRATION=false

# Restart
docker compose restart conduit
```

## Deploy from Mac mini (Recommended)

Use DMZ deployment tooling from the control-plane repo:

```bash
# Validate DMZ policy
scripts/validate-dmz-compose matrix

# Sync + deploy Matrix on DMZ Pi
scripts/dmz-app up matrix

# View status/logs
scripts/dmz-app ps matrix
scripts/dmz-app logs matrix conduit
```

## Commands

### Start
```bash
docker compose up -d
```

### Stop
```bash
docker compose down
```

### Restart
```bash
docker compose restart conduit
```

### View Logs
```bash
docker compose logs -f conduit
```

### Check Health
```bash
curl -s http://localhost:6167/_matrix/client/versions | jq
```

## Update Procedure

1. **Check release notes** at https://conduit.rs/changelog

2. **Update version** in `.env`:
   ```bash
   CONDUIT_VERSION=v0.9.0  # new version
   ```

3. **Pull and restart**:
   ```bash
   docker compose pull
   docker compose up -d
   ```

4. **Verify health**:
   ```bash
   curl -s http://localhost:6167/_matrix/client/versions
   ```

### Rollback

If issues occur after update:

```bash
# Revert version in .env
CONDUIT_VERSION=v0.8.0

# Pull old version and restart
docker compose pull
docker compose up -d
```

## Backup

Matrix data is backed up to the Mac mini via Restic over Tailscale.

### What's Backed Up

| Data | Location | Criticality |
|------|----------|-------------|
| Database | `./data/conduit/` | Critical |
| Encryption keys | `./data/conduit/` | Critical |
| Media cache | `./data/conduit/` | Medium |

### Manual Backup

```bash
# From DMZ Pi, backup to Mac mini
restic -r sftp:user@<mac-mini-tailscale-ip>:backups/dmz/matrix backup ./data/conduit
```

### Restore

```bash
# Stop Conduit
docker compose down

# Clear existing data (if corrupted)
rm -rf ./data/conduit/*

# Restore from backup
restic -r sftp:user@<mac-mini-tailscale-ip>:backups/dmz/matrix restore latest --target ./

# Fix permissions
sudo chown -R 1000:1000 ./data/conduit

# Start Conduit
docker compose up -d
```

## DNS Configuration

### Required Records

```
# A record pointing to your home IP
matrix.yourdomain.com    A    <your-public-ip>

# Matrix federation SRV record (optional but recommended)
_matrix._tcp.yourdomain.com    SRV    10 5 8448 matrix.yourdomain.com
```

### Testing Federation

Use the Matrix Federation Tester:
https://federationtester.matrix.org/

Enter your server name and verify all checks pass.

## Authentik Integration (Optional)

Conduit can use Authentik for SSO instead of local passwords.

### 1. Create Application in Authentik

On the Mac mini (accessible via Tailscale):

1. Go to `https://login.home/if/admin/`
2. Create new Application:
   - Name: `Matrix`
   - Slug: `matrix`
   - Provider: Create new OIDC provider
3. Configure OIDC Provider:
   - Client ID: `matrix`
   - Client Secret: (generate)
   - Redirect URIs: `https://matrix.yourdomain.com/_matrix/client/r0/login/sso/redirect`

### 2. Create Groups

Create in Authentik:
- `matrix-admin` — Server administrators
- `matrix-user` — Standard users

### 3. Configure Conduit

Add to `.env`:

```bash
CONDUIT_OIDC_ENABLED=true
CONDUIT_OIDC_ISSUER=https://login.home/application/o/matrix/
CONDUIT_OIDC_CLIENT_ID=matrix
CONDUIT_OIDC_CLIENT_SECRET=<your-client-secret>
```

Restart Conduit:
```bash
docker compose restart conduit
```

**Note:** The DMZ Pi must be able to reach `login.home` via Tailscale.

## Client Setup

### Element (Recommended)

1. Download Element from https://element.io/download
2. Choose "Sign in"
3. Enter homeserver: `https://matrix.yourdomain.com`
4. Sign in with your credentials

### Mobile Apps

| Platform | App | Link |
|----------|-----|------|
| iOS | Element | App Store |
| Android | Element | Play Store / F-Droid |

## Voice/Video Calls (Optional)

Matrix voice and video calls require a TURN server. Without one, calls will fail when users are behind NAT.

### Option 1: Self-host Coturn

Add to `compose.yml`:

```yaml
  coturn:
    image: coturn/coturn:4.6.2-alpine
    container_name: coturn
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config/turnserver.conf:/etc/turnserver.conf:ro
```

### Option 2: Use External TURN Service

Services like Twilio offer TURN servers. Configure in `.env`:

```bash
CONDUIT_TURN_URIS=["turn:global.turn.twilio.com:3478?transport=udp"]
CONDUIT_TURN_SECRET=<twilio-auth-token>
```

## Security Considerations

### This is an Internet-Facing Service

Matrix is deployed on the DMZ Pi specifically because it requires internet access for federation. Key security properties:

| Property | Status |
|----------|--------|
| End-to-end encryption | Messages are E2EE by default |
| Server compromise | Cannot read encrypted messages |
| DMZ isolation | Compromise does not affect Mac mini |
| Rebuildable | Can wipe and restore from backup |

### Hardening Checklist

- [ ] Registration disabled after creating accounts
- [ ] Fail2ban monitoring Matrix/Caddy logs
- [ ] Rate limiting configured in Caddy
- [ ] Regular backups to Mac mini
- [ ] Automatic security updates on Pi OS

## Troubleshooting

### Federation Not Working

1. Check DNS records resolve correctly:
   ```bash
   dig matrix.yourdomain.com
   dig _matrix._tcp.yourdomain.com SRV
   ```

2. Test federation: https://federationtester.matrix.org/

3. Check port 8448 is forwarded and open:
   ```bash
   curl -I https://matrix.yourdomain.com:8448/_matrix/federation/v1/version
   ```

### Users Can't Register

Check if registration is enabled:
```bash
grep CONDUIT_ALLOW_REGISTRATION .env
```

Check Conduit logs:
```bash
docker compose logs conduit | grep -i registration
```

### High Memory Usage

Conduit is designed for low memory, but if issues occur:

1. Check current usage:
   ```bash
   docker stats conduit
   ```

2. Limit in `compose.yml`:
   ```yaml
   services:
     conduit:
       deploy:
         resources:
           limits:
             memory: 256M
   ```

## Upstream Links

- Conduit Documentation: https://docs.conduit.rs/
- Conduit Source: https://gitlab.com/famedly/conduit
- Matrix Specification: https://spec.matrix.org/
- Element Client: https://element.io/
- Federation Tester: https://federationtester.matrix.org/
