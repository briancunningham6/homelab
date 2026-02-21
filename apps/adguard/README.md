# AdGuard Home — Network DNS & Ad Blocking

Network-wide ad and tracker blocking DNS server. Blocks ads for all devices on your network without per-device configuration.

## Quick Reference

| Item | Value |
|------|-------|
| Image | `adguard/adguardhome:v0.107.54` |
| Container | `adguard` |
| Web UI port | 3000 (internal) |
| DNS port | 53 (exposed to host) |
| Hostname | `adguard.home` |
| Health check | `GET /` → 200 |
| Auth | Authentik (admin only) + AdGuard login |

## What AdGuard Home Does

- **Network-wide ad blocking** — Blocks ads on all devices (phones, TVs, IoT)
- **Tracker blocking** — Privacy protection across the network
- **Custom DNS** — Resolve `*.home` domains to local services
- **Parental controls** — Block adult content, enforce safe search
- **Query logging** — See what domains devices are querying
- **Per-client rules** — Different filtering for different devices

## Commands

```bash
# Start
docker compose -f apps/adguard/compose.yml up -d

# Stop
docker compose -f apps/adguard/compose.yml down

# Logs
docker compose -f apps/adguard/compose.yml logs -f

# Restart
docker compose -f apps/adguard/compose.yml restart

# Update
docker compose -f apps/adguard/compose.yml pull
docker compose -f apps/adguard/compose.yml up -d
```

## First-Run Setup

### Step 1: Start AdGuard Home

```bash
# No .env file needed for basic setup
docker compose -f apps/adguard/compose.yml up -d
```

### Step 2: Complete Initial Setup

1. Open http://adguard.home
2. Authenticate via Authentik (homelab-admin group)
3. You'll see AdGuard's setup wizard
4. **Admin Interface Settings:**
   - Listen interface: All interfaces
   - Port: 3000 (already configured)
5. **DNS Server Settings:**
   - Listen interface: All interfaces
   - Port: 53 (already configured)
6. Create admin username and password
   - This is AdGuard's internal auth (second layer after Authentik)
7. Finish setup

### Step 3: Configure DNS Rewrites

AdGuard needs to resolve `*.home` domains to your Mac mini's IP.

1. Go to **Filters → DNS rewrites**
2. Add rewrites for each service:

| Domain | Answer (Mac mini IP) |
|--------|----------------------|
| `*.home` | `192.168.x.x` (your Mac mini LAN IP) |

Or add individual rewrites:

```
home.home       → 192.168.x.x
login.home      → 192.168.x.x
immich.home     → 192.168.x.x
jellyfin.home   → 192.168.x.x
copyparty.home  → 192.168.x.x
adguard.home    → 192.168.x.x
backup.home     → 192.168.x.x
status.home     → 192.168.x.x
dockge.home     → 192.168.x.x
openclaw.home   → 192.168.x.x
```

Wildcard is simpler but individual entries give more control.

### Step 4: Configure Upstream DNS

1. Go to **Settings → DNS settings**
2. **Upstream DNS servers** — add these (one per line):

```
https://dns.cloudflare.com/dns-query
https://dns.quad9.net/dns-query
tls://1.1.1.1
```

3. **Bootstrap DNS servers** (for resolving DoH/DoT):

```
1.1.1.1
9.9.9.9
```

4. Enable **DNSSEC**
5. Save

### Step 5: Test with One Device

Before changing network-wide DNS, test with a single device:

**On macOS:**
```bash
# System Settings → Network → Wi-Fi/Ethernet → Details → DNS
# Add: 192.168.x.x (Mac mini IP running AdGuard)
```

**Test DNS resolution:**
```bash
# Should resolve to Mac mini IP
nslookup immich.home

# Should resolve normally
nslookup google.com

# Should be blocked (ad domain)
nslookup ads.example.com
```

**Browse the web** — ads should be blocked across all sites.

**Check AdGuard dashboard** — you should see queries appearing.

### Step 6: Enable Network-Wide DNS

Once verified, configure your router to use AdGuard as the DNS server:

1. Access your router admin panel (usually `192.168.1.1` or `192.168.0.1`)
2. Find **DHCP settings**
3. Set **Primary DNS** to Mac mini IP (`192.168.x.x`)
4. Set **Secondary DNS** to `1.1.1.1` (fallback if AdGuard is down)
5. Save and reboot router (or wait for DHCP lease renewal)

**All devices will now use AdGuard for DNS.**

---

## DNS Resolution Flow

```
Device → AdGuard Home → [Filters/Rewrites] → Upstream DNS
   │           │                │                    │
   │           └─ Check blocklists                  │
   │           └─ Check DNS rewrites                │
   │                                                 │
   └─ If *.home → Return Mac mini IP                │
   └─ If blocked → Return NXDOMAIN                  │
   └─ If allowed → Forward to upstream ─────────────┘
```

**Example queries:**

| Query | AdGuard Action | Result |
|-------|----------------|--------|
| `immich.home` | DNS rewrite match | `192.168.x.x` |
| `ads.doubleclick.net` | Blocklist match | Blocked (NXDOMAIN) |
| `google.com` | No match | Forward to Cloudflare → `142.250.x.x` |

---

## Blocklists

AdGuard comes with default blocklists. Add more for enhanced blocking:

### Recommended Blocklists

1. **Settings → Filters → DNS blocklists → Add blocklist**

| List | URL |
|------|-----|
| OISD Big | `https://big.oisd.nl` |
| Steven Black | `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts` |
| 1Hosts Pro | `https://o0.pages.dev/Pro/hosts.txt` |

2. Save and update filters

**Note:** Too many blocklists can slow DNS resolution. Start with defaults + OISD Big.

---

## Per-Client Settings

Control filtering for specific devices:

1. **Settings → Clients**
2. Add client (by IP, MAC, or name)
3. Configure:
   - Custom blocklists (stricter or looser)
   - Parental controls
   - Safe browsing
   - Disable filtering entirely (for a specific device)

**Example use cases:**
- Children's devices → Enable parental controls
- Smart TV → Stricter ad/tracker blocking
- Developer laptop → Disable filtering (for testing)

---

## Parental Controls

1. **Settings → General settings → Parental control**
2. Enable **SafeSearch** (forces safe mode on search engines)
3. Enable **Safe browsing** (blocks malware/phishing)
4. Apply to specific clients or network-wide

---

## Query Logs

View DNS queries from all devices:

1. **Query log** tab
2. Filter by:
   - Client (device)
   - Domain
   - Response type (blocked, allowed, etc.)

**Privacy considerations:**
- Query logs show browsing patterns
- Only homelab admins can access (Authentik protected)
- Configure retention in **Settings → DNS settings → Query log**
- Recommended: 7 days

---

## Statistics Dashboard

**Dashboard** shows:
- Queries blocked (%)
- Top blocked domains
- Top clients
- Query types
- Upstream servers used

Use this to tune your blocklists and identify noisy devices.

---

## Troubleshooting

### DNS not working after enabling AdGuard

1. Check AdGuard is running:
   ```bash
   docker ps | grep adguard
   ```

2. Check DNS is listening on port 53:
   ```bash
   sudo lsof -i :53
   ```

3. Test DNS directly:
   ```bash
   dig @192.168.x.x google.com
   ```

4. Check router DHCP is configured correctly

5. Flush DNS cache on client devices:
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

   # Windows
   ipconfig /flushdns
   ```

### *.home domains not resolving

1. Verify DNS rewrite in AdGuard: **Filters → DNS rewrites**
2. Check Mac mini IP is correct
3. Test specific domain:
   ```bash
   dig @192.168.x.x immich.home
   ```

### Too much blocked / too little blocked

1. **Too much** — Check query log, allowlist specific domains:
   - **Filters → Custom filtering rules → Allowlist**
   - Add: `@@||example.com^`

2. **Too little** — Add more blocklists or create custom rules

### Web UI inaccessible

1. Verify Caddy is running and routing to AdGuard
2. Check Authentik is running (required for forward-auth)
3. Access directly via IP: `http://192.168.x.x:3000`

---

## Advanced Features

### DNS over HTTPS (DoH)

Clients can query AdGuard via HTTPS:

```
https://adguard.home/dns-query
```

Configure in browser or system settings for encrypted DNS.

### DNS over TLS (DoT)

```
tls://adguard.home:853
```

### Custom Filtering Rules

1. **Filters → Custom filtering rules**
2. Syntax: AdBlock-style

**Block domain:**
```
||ads.example.com^
```

**Allowlist domain:**
```
@@||safe-domain.com^
```

**Block subdomain but not main:**
```
||tracker.example.com^
@@||example.com^
```

---

## Backup and Restore

### What to Backup

- `data/conf/` — All configuration (blocklists, rewrites, settings)

### Backup Command

```bash
scripts/backup-all --service adguard
```

### Manual Export

1. **Settings → General settings → Export**
2. Downloads `AdGuardHome.yaml`
3. Store securely with other backups

### Restore

```bash
scripts/dr-restore --service adguard
```

Or import manually:
1. **Settings → General settings → Import**
2. Upload `AdGuardHome.yaml`

---

## Monitoring

### In AdGuard

- **Dashboard** — Real-time stats
- **Query log** — All DNS queries
- **Settings → DNS settings** — Test upstream DNS

### In Uptime Kuma

AdGuard is automatically monitored if you add it to Uptime Kuma:

- Type: HTTP(s)
- URL: `http://adguard:3000/`

---

## Network Impact

| Scenario | Impact |
|----------|--------|
| **AdGuard running** | Normal DNS resolution, ads blocked |
| **AdGuard down** | Devices fall back to secondary DNS (1.1.1.1) — ads not blocked |
| **Mac mini offline** | Network DNS fails (devices use secondary if configured) |

**Recommendation:** Set secondary DNS in router DHCP as a fallback.

---

## Privacy Considerations

- **Query logs** contain DNS queries from all household devices
- Shows which websites/services each device accesses
- Only homelab admins can view (Authentik protected)
- Configure retention period based on your privacy preferences
- Consider anonymous logging or disable logging entirely

**Settings → DNS settings → Query log:**
- Enable anonymization (anonymizes client IPs)
- Reduce retention (default 24h, recommend 7 days max)

---

## Performance

**DNS query latency:**
- Cached queries: < 1ms
- Blocked domains: < 1ms (no upstream query)
- Allowed domains: 10-50ms (depends on upstream)

**Resource usage:**
- RAM: ~50-100MB
- CPU: Minimal (< 1%)
- Disk: Query logs grow over time (limit via retention)

---

## Migration from Existing DNS

### From Router's Default DNS

Most routers use ISP DNS by default. AdGuard replaces this:

**Before:**
```
Device → Router DHCP → ISP DNS
```

**After:**
```
Device → Router DHCP → AdGuard Home → Upstream DNS (Cloudflare/Quad9)
```

### From Pi-hole

If migrating from Pi-hole:

1. Export Pi-hole settings
2. Import blocklists manually to AdGuard
3. Recreate DNS rewrites
4. Update router DHCP to point to AdGuard
5. Decommission Pi-hole

---

## Environment Variables

None required for basic setup. All configuration via web UI.

---

## Upstream

- Website: https://adguard.com/adguard-home.html
- Documentation: https://github.com/AdguardTeam/AdGuardHome/wiki
- GitHub: https://github.com/AdguardTeam/AdGuardHome
- Community: https://github.com/AdguardTeam/AdGuardHome/discussions
