# iPhone Access Setup Guide

This guide explains how to access homelab services from your iPhone using Tailscale and AdGuard Home DNS.

**For detailed architecture and troubleshooting**, see [Mobile Access Architecture](mobile-access-architecture.md).

This is a quick-start guide. The architecture document explains how everything works under the hood.

## Your Configuration

- **Mac mini LAN IP**: 192.168.0.199
- **Mac mini Tailscale IP**: 100.73.223.8
- **DNS Server**: AdGuard Home (running in Docker)

## Quick Setup

### 1. Configure AdGuard Home DNS Rewrites

**Access AdGuard Home:**
- Local: http://adguard.home
- Direct: http://localhost:3000

**Add DNS Rewrites** (Filters → DNS rewrites):

**Option A - Individual entries:**
```
home.home       → 192.168.0.199
dockge.home     → 192.168.0.199
status.home     → 192.168.0.199
login.home      → 192.168.0.199
immich.home     → 192.168.0.199
missions.home   → 192.168.0.199
adguard.home    → 192.168.0.199
```

**Option B - Wildcard (recommended):**
```
*.home          → 192.168.0.199
```

### 2. Configure Tailscale DNS

**Go to**: https://login.tailscale.com/admin/dns

**Add Global Nameserver:**
1. Click "Add nameserver"
2. Enter: `100.73.223.8`
3. Save

**Add Split DNS (recommended):**
1. Click "Add split DNS nameserver"
2. Nameserver: `100.73.223.8`
3. Restrict to domain: `home`
4. Save

**Enable Override Local DNS:**
- Ensure "Override local DNS" is checked
- This makes sure Tailscale uses your DNS even on other networks

### 3. Test from iPhone

**Prerequisites:**
- iPhone has Tailscale app installed
- Tailscale is connected

**Test URLs:**
- http://home.home → Homepage dashboard
- http://missions.home → Missions app
- http://immich.home → Immich
- http://adguard.home → AdGuard Home admin

## Troubleshooting

### DNS not resolving

**Check AdGuard Home is running:**
```bash
docker ps | grep adguard
```

**Test DNS resolution from Mac:**
```bash
# Should return 192.168.0.199
nslookup missions.home 100.73.223.8
```

**Check Tailscale DNS settings:**
```bash
tailscale status --json | jq '.MagicDNSSuffix'
```

### Can't access from iPhone

1. **Verify Tailscale is connected** on iPhone
2. **Check Tailscale DNS settings** are saved
3. **Try toggling Tailscale off/on** on iPhone
4. **Check if services are running**:
   ```bash
   docker ps
   ```

### Services accessible on LAN but not via Tailscale

1. **Verify AdGuard Home is listening on Tailscale interface:**
   ```bash
   sudo lsof -i :53
   ```

2. **Check firewall** (macOS):
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   ```

3. **Verify Tailscale subnet routing** (if needed):
   ```bash
   tailscale status
   ```

## How It Works

```
iPhone (on cellular/WiFi)
    ↓
Tailscale VPN (100.x.x.x network)
    ↓
DNS Query for missions.home
    ↓
AdGuard Home on Mac mini (100.73.223.8:53)
    ↓
DNS Rewrite: missions.home → 192.168.0.199
    ↓
HTTP Request to 192.168.0.199:80
    ↓
Caddy reverse proxy on Mac mini
    ↓
Routes to appropriate container
    ↓
missions-frontend container
```

## Adding New Services

When you add a new service with a `.home` domain:

**If using wildcard DNS:**
- No action needed! `*.home` already points to Mac mini

**If using individual entries:**
1. Open AdGuard Home UI
2. Go to Filters → DNS rewrites
3. Add: `newservice.home → 192.168.0.199`
4. Save

## Alternative: Direct IP Access

If DNS isn't working, you can always use direct IPs:

**Via Tailscale:**
```
http://100.73.223.8:3000    # Homepage
http://100.73.223.8:2283    # Immich
http://100.73.223.8:5173    # Missions (in dev mode)
```

**Note:** This requires knowing the ports and bypasses Caddy's routing.

## Security Notes

- All traffic over Tailscale is encrypted end-to-end
- AdGuard Home only responds to Tailscale network (100.x.x.x)
- No ports exposed to the internet
- Authentik SSO protects services that require authentication

## Useful Commands

**Check Mac mini IPs:**
```bash
# LAN IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Tailscale IP
tailscale ip -4
```

**Restart AdGuard Home:**
```bash
docker compose -f apps/adguard/compose.yml restart
```

**View AdGuard Home logs:**
```bash
docker compose -f apps/adguard/compose.yml logs -f
```

**Test DNS resolution:**
```bash
# From Mac (using AdGuard Home DNS)
nslookup missions.home 100.73.223.8

# From iPhone (in Safari address bar)
missions.home
```
