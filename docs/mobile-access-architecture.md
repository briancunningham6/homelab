# Mobile Access Architecture

This document explains how mobile devices (iPhones, iPads, etc.) access homelab services securely over Tailscale using custom DNS resolution.

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Components](#components)
- [How It Works](#how-it-works)
- [Setup Guide](#setup-guide)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Overview

### The Problem

Homelab services use custom `.home` domain names (e.g., `missions.home`, `immich.home`) that work great on the local network but don't resolve on mobile devices because:

1. Mobile devices don't have access to `/etc/hosts` for DNS overrides
2. `.home` domains aren't registered in public DNS
3. Services are only accessible on the local network or via VPN

### The Solution

Combine **Tailscale VPN** + **AdGuard Home DNS** to provide:
- Secure remote access (Tailscale)
- Custom DNS resolution (AdGuard Home)
- Clean, memorable URLs (`missions.home` instead of `100.73.223.8:5173`)
- Works on any device (iPhone, iPad, Android, laptops)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Mobile Device                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Tailscale Client                       │  │
│  │  - Connected to Tailscale network (100.x.x.x)            │  │
│  │  - DNS configured to use 100.73.223.8                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    DNS Query: missions.home
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Tailscale Network (VPN)                       │
│                    Encrypted WireGuard Tunnel                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Mac Mini (Homelab)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AdGuard Home (DNS Server)                   │  │
│  │  - Listens on port 53 (DNS)                             │  │
│  │  - Tailscale IP: 100.73.223.8                           │  │
│  │  - DNS Rewrite: *.home → 192.168.0.199                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│              Returns: 192.168.0.199 (Mac mini LAN IP)           │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Caddy (Reverse Proxy)                      │  │
│  │  - Listens on port 80 (HTTP)                            │  │
│  │  - Routes based on hostname                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Docker Containers (Services)                  │  │
│  │  - missions-frontend (missions.home)                    │  │
│  │  - immich (immich.home)                                 │  │
│  │  - homepage (home.home)                                 │  │
│  │  - etc.                                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Tailscale VPN

**Purpose**: Provides secure, encrypted access to the homelab from anywhere.

**How it works**:
- Creates a private mesh network (100.x.x.x address space)
- Each device gets a stable IP address
- Peer-to-peer connections when possible (NAT traversal)
- All traffic encrypted with WireGuard protocol

**Key features for this setup**:
- Custom nameserver configuration (points to AdGuard Home)
- Split DNS support (only `.home` queries go to homelab DNS)
- Override local DNS (ensures consistent DNS resolution)

**Configuration**:
```
Nameserver: 100.73.223.8 (Mac mini's Tailscale IP)
Split DNS: home domain → 100.73.223.8
Override local DNS: Enabled
```

### 2. AdGuard Home (DNS Server)

**Purpose**: Resolves `.home` domains to the Mac mini's IP address.

**How it works**:
- Listens on port 53 (standard DNS port)
- Receives DNS queries from Tailscale devices
- Checks DNS rewrite rules
- Returns custom IP addresses for `.home` domains
- Forwards other queries to upstream DNS (1.1.1.1, 8.8.8.8)

**Configuration location**:
- Docker: `apps/adguard/compose.yml`
- Data: `apps/adguard/data/`
- Web UI: `http://adguard.home`

**DNS Rewrite Rule**:
```
Domain Pattern: *.home
Answer: 192.168.0.199
```

This single rule handles all `.home` subdomains:
- `missions.home` → `192.168.0.199`
- `immich.home` → `192.168.0.199`
- `anyservice.home` → `192.168.0.199`

### 3. Caddy (Reverse Proxy)

**Purpose**: Routes HTTP requests to the correct container based on hostname.

**How it works**:
- Listens on port 80 (HTTP)
- Inspects `Host` header in HTTP request
- Matches hostname to configured route
- Forwards request to appropriate container

**Configuration location**: `platform/caddy/Caddyfile`

**Example routes**:
```
http://missions.home {
    reverse_proxy missions-frontend:5173
}

http://immich.home {
    reverse_proxy immich-server:2283
}
```

### 4. Docker Network

**Purpose**: Allows containers to communicate using DNS names.

**How it works**:
- All services connected to `caddy-net` network
- Docker's internal DNS resolves container names
- Caddy can reach containers by name (e.g., `missions-frontend`)

**Configuration**:
```yaml
networks:
  caddy-net:
    external: true
```

---

## How It Works

### Step-by-Step Flow

Let's trace what happens when you visit `http://missions.home` from your iPhone:

#### 1. DNS Resolution Phase

```
iPhone Safari: "What is the IP address of missions.home?"
    ↓
iPhone Tailscale Client: "Use 100.73.223.8 for .home domains"
    ↓
DNS Query sent to 100.73.223.8:53 over Tailscale VPN
    ↓
AdGuard Home receives query on Mac mini
    ↓
AdGuard Home checks DNS rewrite rules
    ↓
Match found: *.home → 192.168.0.199
    ↓
AdGuard Home responds: "missions.home is at 192.168.0.199"
    ↓
iPhone receives response: 192.168.0.199
```

#### 2. HTTP Connection Phase

```
iPhone Safari: "Connect to 192.168.0.199:80"
    ↓
Connection routed through Tailscale VPN tunnel
    ↓
Reaches Mac mini's Tailscale interface
    ↓
Forwarded to Mac mini's LAN interface (192.168.0.199)
    ↓
Caddy listening on port 80 receives HTTP request
    ↓
Caddy reads Host header: "missions.home"
    ↓
Caddy matches route: missions.home → missions-frontend:5173
    ↓
Caddy forwards request to missions-frontend container
    ↓
Container responds with web page
    ↓
Caddy sends response back to iPhone
    ↓
Page loads in Safari
```

### Network Address Translation

The system uses three different IP address spaces:

1. **LAN IP**: `192.168.0.199`
   - Mac mini's address on local network
   - Where Caddy and services actually run
   - Not directly accessible from outside the network

2. **Tailscale IP**: `100.73.223.8`
   - Mac mini's address on Tailscale VPN
   - Accessible from any device on the Tailscale network
   - DNS server (AdGuard Home) listens here

3. **Container IPs**: `172.x.x.x` (Docker network)
   - Internal to Docker
   - Not exposed to outside
   - Containers communicate using DNS names

### Why Use LAN IP in DNS Rewrites?

You might wonder: "Why do DNS rewrites point to `192.168.0.199` (LAN IP) instead of `100.73.223.8` (Tailscale IP)?"

**Answer**: Tailscale routing optimization.

When a device on Tailscale queries for `missions.home`:
1. DNS returns `192.168.0.199`
2. Tailscale client sees this is a "local" IP
3. Tailscale routes the connection through the VPN to the Mac mini
4. Mac mini's network stack routes to its own LAN interface
5. Connection arrives at Caddy

This works because:
- Tailscale knows `192.168.0.199` is on the Mac mini
- The connection stays secure (still goes through VPN tunnel)
- It's slightly more efficient than using the Tailscale IP

---

## Setup Guide

### Prerequisites

- Mac mini running macOS
- Homelab services running in Docker
- Tailscale installed on Mac mini and mobile devices
- AdGuard Home deployed (see `apps/adguard/`)

### Initial Setup

#### Step 1: Get IP Addresses

```bash
# Mac mini LAN IP
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example output: inet 192.168.0.199

# Mac mini Tailscale IP
tailscale ip -4
# Example output: 100.73.223.8
```

Record these values - you'll need them for configuration.

#### Step 2: Configure AdGuard Home DNS Rewrites

1. Open AdGuard Home UI: `http://adguard.home`
2. Navigate to: **Filters → DNS rewrites**
3. Click: **Add DNS rewrite**
4. Configure:
   - Domain: `*.home`
   - Answer: `192.168.0.199` (your Mac mini LAN IP)
5. Click: **Save**

**What this does**: Tells AdGuard Home to respond to any `*.home` query with your Mac mini's IP address.

**Alternative - Individual entries**:

If wildcard doesn't work, add each service individually:

```
home.home       → 192.168.0.199
dockge.home     → 192.168.0.199
status.home     → 192.168.0.199
login.home      → 192.168.0.199
immich.home     → 192.168.0.199
missions.home   → 192.168.0.199
adguard.home    → 192.168.0.199
```

#### Step 3: Configure Tailscale DNS

1. Open: https://login.tailscale.com/admin/dns
2. Click: **Add nameserver**
3. Enter: `100.73.223.8` (your Mac mini Tailscale IP)
4. Click: **Save**

**Optional but recommended - Split DNS**:

5. Click: **Add split DNS nameserver**
6. Configure:
   - Nameserver: `100.73.223.8`
   - Restrict to domain: `home`
7. Click: **Save**

**What this does**:
- Global nameserver: All DNS queries from Tailscale devices go to your AdGuard Home
- Split DNS: Only `.home` queries go to AdGuard Home, everything else uses default DNS

**Enable Override Local DNS**:

8. Ensure **"Override local DNS"** is checked

**What this does**: Forces Tailscale to use your custom DNS even when devices are on other networks (cellular, coffee shop WiFi, etc.)

#### Step 4: Test from Mac Mini

Before testing on mobile, verify DNS works from the Mac:

```bash
# Test DNS resolution using AdGuard Home
nslookup missions.home 100.73.223.8

# Expected output:
# Server:    100.73.223.8
# Address:   100.73.223.8#53
#
# Name:      missions.home
# Address:   192.168.0.199
```

If this works, mobile devices will work too.

#### Step 5: Test from Mobile Device

1. **Connect** to Tailscale on your iPhone/iPad
2. **Open** Safari
3. **Navigate** to: `http://home.home`
4. **Verify** Homepage dashboard loads

Try other services:
- `http://missions.home` - Missions app
- `http://immich.home` - Immich photo management
- `http://adguard.home` - AdGuard Home admin

### Adding New Services

When you add a new service to your homelab:

#### If Using Wildcard DNS (`*.home`):

✅ No action needed! The wildcard already covers new services.

Just add the Caddy route:

```
http://newservice.home {
    reverse_proxy newservice-container:port
}
```

#### If Using Individual DNS Entries:

1. **Add DNS rewrite** in AdGuard Home:
   - Domain: `newservice.home`
   - Answer: `192.168.0.199`

2. **Add Caddy route**:
   ```
   http://newservice.home {
       reverse_proxy newservice-container:port
   }
   ```

3. **Reload Caddy**:
   ```bash
   docker exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```

---

## Troubleshooting

### DNS Not Resolving

**Symptom**: `missions.home` doesn't resolve, shows "can't find server" error.

**Check 1 - AdGuard Home is running**:
```bash
docker ps | grep adguard
# Should show: Up X hours (healthy)
```

**Check 2 - DNS rewrites are saved**:
1. Open `http://adguard.home`
2. Go to Filters → DNS rewrites
3. Verify `*.home → 192.168.0.199` exists

**Check 3 - Tailscale DNS settings**:
1. Go to https://login.tailscale.com/admin/dns
2. Verify nameserver `100.73.223.8` is listed
3. Verify "Override local DNS" is enabled

**Check 4 - Test DNS directly**:
```bash
# From Mac
nslookup missions.home 100.73.223.8

# Should return 192.168.0.199
```

**Fix**: If DNS query fails, restart AdGuard Home:
```bash
docker compose -f apps/adguard/compose.yml restart
```

### Can Access on LAN but Not via Tailscale

**Symptom**: Services work at home but not when away from home.

**Check 1 - Tailscale is connected**:
- On mobile device, open Tailscale app
- Verify status shows "Connected"
- Verify Mac mini shows as "Online"

**Check 2 - DNS resolution via Tailscale**:

From mobile device, try using the Tailscale IP directly:
```
http://100.73.223.8:80
```

If this works but `missions.home` doesn't, it's a DNS issue.

**Check 3 - Tailscale DNS settings propagated**:
- Toggle Tailscale off/on on mobile device
- Wait 30 seconds
- Try again

**Fix**:
1. Disable Tailscale on mobile
2. Wait 10 seconds
3. Enable Tailscale
4. Wait 30 seconds for DNS to propagate
5. Try accessing services

### Services Return 404 or Wrong Page

**Symptom**: DNS resolves correctly but service doesn't load.

**Check 1 - Caddy routing**:
```bash
# View Caddy config
cat platform/caddy/Caddyfile | grep -A 3 "missions.home"
```

**Check 2 - Service is running**:
```bash
docker ps | grep missions
# Should show both frontend and backend
```

**Check 3 - Test Caddy**:
```bash
# From Mac, test with Host header
curl -H "Host: missions.home" http://localhost:80
```

**Fix**: Reload Caddy configuration:
```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### AdGuard Home Unhealthy

**Symptom**: `docker ps` shows AdGuard as `unhealthy`.

**Check logs**:
```bash
docker compose -f apps/adguard/compose.yml logs --tail=50
```

**Common causes**:
1. Configuration file corruption
2. Port 53 conflict with another service
3. DNS upstream servers unreachable

**Fix 1 - Restart**:
```bash
docker compose -f apps/adguard/compose.yml restart
```

**Fix 2 - Check port conflict**:
```bash
sudo lsof -i :53
# Should only show AdGuard Home process
```

**Fix 3 - Rebuild if needed**:
```bash
docker compose -f apps/adguard/compose.yml down
docker compose -f apps/adguard/compose.yml up -d
```

### Mobile Device Using Wrong DNS

**Symptom**: iPhone still using cellular provider's DNS instead of AdGuard Home.

**Check**:
1. Open Tailscale app on iPhone
2. Go to Settings
3. Check "DNS" section
4. Should show your Mac mini IP

**Fix**:
1. In Tailscale admin console: https://login.tailscale.com/admin/dns
2. Ensure "Override local DNS" is checked
3. Remove device from Tailscale
4. Re-add device
5. DNS settings should apply correctly

---

## Advanced Configuration

### Split DNS for Multiple Domains

If you have services on multiple domains:

```
Nameserver: 100.73.223.8
Split DNS 1: .home → 100.73.223.8
Split DNS 2: .lab → 100.73.223.8
Split DNS 3: .homelab → 100.73.223.8
```

Add corresponding DNS rewrites in AdGuard Home.

### Using MagicDNS Alongside Custom DNS

Tailscale's MagicDNS gives each device a hostname like `mac-mini.tailnet-name.ts.net`.

You can use both:
- Custom DNS for `.home` services
- MagicDNS for accessing devices

Enable in Tailscale admin → DNS → MagicDNS

### DNS-over-HTTPS (DoH) for AdGuard Home

AdGuard Home supports DoH for encrypted DNS queries:

1. In AdGuard Home UI → Settings → Encryption
2. Enable HTTPS for DNS
3. Configure Tailscale to use: `https://100.73.223.8/dns-query`

**Note**: This adds encryption redundancy (DNS already encrypted by Tailscale VPN).

### Firewall Rules

AdGuard Home should only accept DNS queries from Tailscale network:

**macOS Firewall**:
```bash
# Allow DNS from Tailscale interface only
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/adguard
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /path/to/adguard
```

**Better approach**: Use Docker network isolation (already configured in compose.yml).

### Monitoring DNS Queries

AdGuard Home logs all DNS queries:

1. Open: `http://adguard.home`
2. Go to: Query Log
3. Filter by client IP (your iPhone's Tailscale IP)
4. See what domains are being resolved

Useful for debugging:
- Verify queries reaching AdGuard Home
- Check if rewrites applying correctly
- Monitor unusual DNS activity

---

## Security Considerations

### Why This Setup Is Secure

1. **End-to-End Encryption**: All Tailscale traffic encrypted with WireGuard
2. **No Open Ports**: No firewall ports opened on Mac mini
3. **Private Network**: 100.x.x.x addresses only accessible to your Tailscale network
4. **DNS Privacy**: DNS queries encrypted in VPN tunnel
5. **Zero Trust**: Each device must authenticate to Tailscale

### What's NOT Secure

1. **HTTP (not HTTPS)**: Services use `http://` not `https://`
   - Acceptable: Traffic already encrypted by Tailscale VPN
   - Optional improvement: Add TLS certificates for defense-in-depth

2. **Shared Secret**: All devices on Tailscale can access services
   - Mitigation: Use Authentik SSO for authentication
   - Mitigation: Use Tailscale ACLs to restrict access

3. **DNS Spoofing**: AdGuard Home trusts all queries from Tailscale
   - Acceptable: Tailscale network is private and authenticated
   - Mitigation: Use Tailscale ACLs to control who can query DNS

### Recommended: Add Tailscale ACLs

Restrict which devices can access which services:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:mobile"],
      "dst": ["100.73.223.8:53", "100.73.223.8:80"]
    }
  ]
}
```

This allows only mobile devices to access DNS and HTTP services.

---

## Performance Considerations

### DNS Caching

AdGuard Home caches DNS responses:
- First query: ~50ms (query + rewrite)
- Cached query: ~5ms (local cache)

Mobile devices also cache DNS:
- iPhone DNS cache TTL: ~30 seconds
- Subsequent requests: instant (no DNS query)

### Connection Latency

Typical latency over Tailscale:
- Same WiFi network: ~2-5ms (direct peer connection)
- Cellular to home: ~30-100ms (relayed through Tailscale DERP servers)
- International: ~100-300ms (depends on DERP server location)

Services feel fast because:
- DNS cached after first query
- Tailscale maintains persistent connections
- WireGuard protocol is very efficient

### Bandwidth

Tailscale adds minimal overhead:
- WireGuard encryption: ~1-2% overhead
- DERP relay (worst case): ~2x bandwidth (upload + download)
- Direct peer connection: no extra bandwidth

Streaming large files (photos, videos):
- Uses direct peer-to-peer when possible
- Falls back to relay if NAT traversal fails
- AdGuard Home not involved (only DNS, not data)

---

## Alternative Approaches

### Option 1: Tailscale Serve (Not Used)

Tailscale has built-in HTTPS serving:

```bash
tailscale serve https / http://localhost:80
```

Access: `https://mac-mini.tailnet-name.ts.net`

**Why we didn't use this**:
- Loses custom domain names
- Have to remember long Tailscale hostnames
- Less flexible than DNS approach

**When to use**:
- Quick demos
- Single service exposure
- Don't want to run DNS server

### Option 2: VPN Port Forwarding (Not Used)

Use Tailscale funnel to expose services:

```bash
tailscale funnel 80
```

**Why we didn't use this**:
- Exposes services to public internet (security risk)
- Defeats purpose of private homelab
- Still doesn't give custom domains

**When to use**:
- Sharing specific service with non-Tailscale users
- Public-facing services
- Temporary access

### Option 3: Split-Horizon DNS (More Complex)

Run different DNS for internal vs external:
- Internal: resolves to LAN IPs
- External: resolves to Tailscale IPs

**Why we didn't use this**:
- More complex setup
- Current approach works for both
- No significant benefit

**When to use**:
- Large multi-site deployments
- Need different IPs for internal/external
- Advanced network segmentation

---

## Reference

### IP Address Summary

| Component | LAN IP | Tailscale IP | Purpose |
|-----------|--------|--------------|---------|
| Mac mini | 192.168.0.199 | 100.73.223.8 | Homelab host |
| AdGuard Home | - | 100.73.223.8:53 | DNS server |
| Caddy | 192.168.0.199:80 | - | Reverse proxy |
| Services | 172.x.x.x | - | Docker containers |

### Port Reference

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| 53 | AdGuard Home | UDP/TCP | DNS queries |
| 80 | Caddy | HTTP | Web services |
| 443 | Tailscale | HTTPS | VPN control plane |
| 41641 | Tailscale | UDP | WireGuard VPN |

### Configuration Files

| File | Purpose |
|------|---------|
| `apps/adguard/compose.yml` | AdGuard Home container definition |
| `apps/adguard/data/conf/AdGuardHome.yaml` | AdGuard Home config |
| `platform/caddy/Caddyfile` | Reverse proxy routes |
| Tailscale admin console | DNS nameserver settings |

### Useful Commands

```bash
# Check AdGuard Home status
docker ps | grep adguard

# View AdGuard Home logs
docker compose -f apps/adguard/compose.yml logs -f

# Test DNS resolution
nslookup missions.home 100.73.223.8

# Get Mac mini IPs
ifconfig | grep "inet " | grep -v 127.0.0.1
tailscale ip -4

# Restart AdGuard Home
docker compose -f apps/adguard/compose.yml restart

# Reload Caddy config
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# Check Tailscale status
tailscale status
```

---

## Conclusion

This DNS-based approach provides:
- ✅ Clean, memorable URLs
- ✅ Works on all devices
- ✅ Secure (VPN encrypted)
- ✅ Easy to maintain
- ✅ Scales to new services

The key insight: **Combine VPN for connectivity + Custom DNS for naming**.

Tailscale handles the "how to connect" problem, AdGuard Home handles the "what to call it" problem, and Caddy handles the "where to route it" problem.

Together, they create a seamless experience that feels like services are local, even when you're thousands of miles away.
