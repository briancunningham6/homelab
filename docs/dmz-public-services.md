# DMZ for Public Services — Architecture and Implementation

> **Status:** Planned (not yet implemented)
> **Date:** 2026-02-21
> **Approach:** Tailscale Funnel + DMZ Raspberry Pi

---

## Overview

This document describes how to safely expose public-facing services (blog, file share) to the internet while keeping the home network isolated.

### Goals

1. **Isolation** — DMZ cannot access home LAN
2. **No Static IP Required** — Works with dynamic home IP
3. **Secure** — Public services hardened and monitored
4. **Simple** — Leverage Tailscale to avoid port forwarding
5. **Manageable** — Can be administered remotely via Tailscale

---

## Architecture

```
                          Internet
                             │
                             │
                    ┌────────▼─────────┐
                    │  Tailscale       │
                    │  (funnel)        │
                    └────────┬─────────┘
                             │
                             │ HTTPS (Tailscale manages certs)
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    DMZ Network (Pi)                           │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Raspberry Pi 4/5 (DMZ Host)                          │   │
│  │                                                       │   │
│  │  Tailscale:                                          │   │
│  │  - Funnel enabled (public HTTPS)                    │   │
│  │  - Management access                                │   │
│  │                                                       │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Caddy (internal reverse proxy)             │    │   │
│  │  │  - Routes requests to services               │    │   │
│  │  │  - Rate limiting                             │    │   │
│  │  │  - Access logging                            │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │                                                       │   │
│  │  Public Services:                                    │   │
│  │  ┌──────────────┐  ┌─────────────────────────┐      │   │
│  │  │  Blog        │  │  Public File Share      │      │   │
│  │  │  (Ghost)     │  │  (Nginx static)         │      │   │
│  │  └──────────────┘  └─────────────────────────┘      │   │
│  │                                                       │   │
│  │  Security:                                           │   │
│  │  - Fail2ban (ban abusive IPs)                       │   │
│  │  - Automatic security updates                       │   │
│  │  - Minimal installed packages                       │   │
│  │                                                       │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  Firewall Rules (iptables):                                  │
│  ✗ DMZ → Home LAN (192.168.x.x) — DROP ALL                  │
│  ✓ DMZ → Internet — ALLOW (for updates, Tailscale)          │
│  ✓ DMZ → Tailscale network — ALLOW (management only)        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                             │
                             │ Tailscale network only
                             │ (management, content sync)
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    Home LAN Network                           │
│                                                               │
│  Mac mini (homelab platform)                                 │
│  - Immich, Jellyfin, Authentik                               │
│  - All sensitive services                                    │
│  - Content authoring for DMZ                                 │
│                                                               │
│  Family devices                                              │
│                                                               │
│  Firewall Rules:                                             │
│  ✗ Accept connections FROM DMZ — DROP ALL                    │
│  ✓ Initiate connections TO DMZ — ALLOW (for publishing)     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Why Tailscale Funnel?

| Feature | Benefit |
|---------|---------|
| **No port forwarding** | No router configuration needed |
| **No static IP** | Works with dynamic home IP |
| **Automatic HTTPS** | Tailscale manages certificates |
| **DDoS protection** | Tailscale infrastructure absorbs attacks |
| **Simple setup** | One command to enable |
| **Free tier** | Included in Tailscale free plan |

### Limitations

- **Beta feature** — May change or have bugs
- **Custom domains** — Requires paid Tailscale plan (or use `*.ts.net`)
- **Bandwidth** — Subject to Tailscale fair use policy
- **Control** — Less granular than self-hosted reverse proxy

---

## Implementation Plan

### Phase 1: DMZ Pi Setup

**Hardware:**
- Raspberry Pi 4 or 5 (4GB+ RAM)
- MicroSD card (32GB+) or USB SSD boot
- Power supply
- Ethernet cable (preferred over WiFi for stability)

**Network Setup:**

**Option A: Separate Physical Network (Ideal)**
- Connect DMZ Pi to a separate router port/VLAN
- Configure router firewall to block DMZ → LAN

**Option B: Same Physical Network with Firewall (Simpler)**
- Connect DMZ Pi to home network
- Use iptables on Pi to block LAN access
- Verify isolation with testing

**Initial Installation:**

```bash
# 1. Flash Raspberry Pi OS Lite (64-bit) to SD card
# Use Raspberry Pi Imager

# 2. Enable SSH in imager settings
# Set hostname: dmz-pi
# Set username/password

# 3. Boot Pi and SSH in
ssh user@dmz-pi.local

# 4. Update system
sudo apt update && sudo apt upgrade -y

# 5. Install essentials
sudo apt install -y \
  ufw \
  fail2ban \
  unattended-upgrades \
  docker.io \
  docker-compose

# 6. Enable automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

### Phase 2: Tailscale Setup

**Install Tailscale:**

```bash
# On DMZ Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

**Enable Tailscale Funnel:**

```bash
# Enable funnel on port 443
sudo tailscale funnel 443 on

# This exposes https://<machine-name>.ts.net publicly
```

**Verify:**

```bash
# Check funnel status
tailscale funnel status

# Should show:
# https://<machine-name>.ts.net
#   |-- / => http://127.0.0.1:8080
```

---

### Phase 3: Firewall Configuration

**Block DMZ from accessing home LAN:**

```bash
# On DMZ Pi - create firewall rules
sudo tee /etc/iptables/rules.v4 << 'EOF'
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# Allow loopback
-A INPUT -i lo -j ACCEPT
-A OUTPUT -o lo -j ACCEPT

# Allow established connections
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (from Tailscale only)
-A INPUT -i tailscale0 -p tcp --dport 22 -j ACCEPT

# Allow Tailscale
-A INPUT -i tailscale0 -j ACCEPT
-A OUTPUT -o tailscale0 -j ACCEPT

# Block access to home LAN (adjust subnet to your LAN)
-A OUTPUT -d 192.168.0.0/16 -j DROP
-A OUTPUT -d 10.0.0.0/8 -j DROP
-A OUTPUT -d 172.16.0.0/12 -j DROP

# Allow DNS, NTP, HTTP(S) for updates
-A OUTPUT -p udp --dport 53 -j ACCEPT
-A OUTPUT -p tcp --dport 53 -j ACCEPT
-A OUTPUT -p udp --dport 123 -j ACCEPT
-A OUTPUT -p tcp --dport 80 -j ACCEPT
-A OUTPUT -p tcp --dport 443 -j ACCEPT

# Drop everything else
-A INPUT -j DROP
-A OUTPUT -j DROP

COMMIT
EOF

# Apply rules
sudo iptables-restore < /etc/iptables/rules.v4

# Make persistent across reboots
sudo apt install -y iptables-persistent
```

**Test Isolation:**

```bash
# Should FAIL (blocked by firewall)
ping <ROUTER_IP>

# Should SUCCEED (Tailscale management)
ping <mac-mini-tailscale-ip>

# Should SUCCEED (internet access)
ping 8.8.8.8
```

---

### Phase 4: Caddy Reverse Proxy

**Install Caddy on DMZ Pi:**

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

**Configure Caddy:**

```bash
sudo tee /etc/caddy/Caddyfile << 'EOF'
# Internal reverse proxy
# Tailscale Funnel forwards HTTPS to this Caddy instance

:8080 {
    # Rate limiting
    rate_limit {
        zone dmz {
            key {remote_host}
            events 100
            window 1m
        }
    }

    # Logging
    log {
        output file /var/log/caddy/access.log
        format json
    }

    # Route to services
    route /blog* {
        reverse_proxy ghost:2368
    }

    route /files* {
        reverse_proxy nginx:80
    }

    route / {
        respond "DMZ Public Services" 200
    }
}
EOF

# Create log directory
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

# Reload Caddy
sudo systemctl reload caddy
```

**Configure Tailscale Funnel to forward to Caddy:**

```bash
# Forward public HTTPS to Caddy on port 8080
sudo tailscale funnel 443 http://127.0.0.1:8080
```

---

### Phase 5: Deploy Public Services

**Example: Static File Server (Nginx)**

Create `docker-compose.yml` on DMZ Pi:

```yaml
version: '3'

services:
  nginx:
    image: nginx:alpine
    container_name: dmz-files
    restart: unless-stopped
    volumes:
      - ./public:/usr/share/nginx/html:ro
    networks:
      - dmz-net

  ghost:
    image: ghost:5-alpine
    container_name: dmz-blog
    restart: unless-stopped
    environment:
      url: https://dmz-pi.ts.net/blog
      database__client: sqlite3
      database__connection__filename: /var/lib/ghost/content/data/ghost.db
    volumes:
      - ./ghost:/var/lib/ghost/content
    networks:
      - dmz-net

networks:
  dmz-net:
    driver: bridge
```

**Start services:**

```bash
sudo docker-compose up -d
```

---

### Phase 6: Content Publishing Workflow

**From Mac mini to DMZ Pi:**

```bash
# On Mac mini (home LAN)
# Sync static files to DMZ via Tailscale

# Example: Publish blog content
rsync -avz --delete \
  ~/blog/public/ \
  dmz-pi:/home/user/public/

# Or use git for version control
ssh dmz-pi "cd /home/user/blog && git pull"
```

**Security Notes:**
- DMZ cannot pull from LAN (firewall blocks it)
- LAN must push to DMZ
- Use Tailscale for secure transfer (not exposed to internet)

---

### Phase 7: Security Hardening

**Fail2ban for Abuse Prevention:**

```bash
# On DMZ Pi
sudo apt install -y fail2ban

# Create jail for Caddy
sudo tee /etc/fail2ban/jail.d/caddy.conf << 'EOF'
[caddy]
enabled = true
port = http,https
filter = caddy
logpath = /var/log/caddy/access.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

# Create filter
sudo tee /etc/fail2ban/filter.d/caddy.conf << 'EOF'
[Definition]
failregex = ^.*"remote_ip":"<HOST>".*"status":(?:429|403).*$
ignoreregex =
EOF

sudo systemctl restart fail2ban
```

**Automatic Updates:**

```bash
# Already enabled in Phase 1
# Verify configuration
sudo systemctl status unattended-upgrades
```

**Minimal Attack Surface:**

```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# Remove unnecessary packages
sudo apt autoremove -y
```

---

### Phase 8: Monitoring

**Log Aggregation:**

```bash
# View Caddy access logs
sudo tail -f /var/log/caddy/access.log | jq

# View fail2ban bans
sudo fail2ban-client status caddy
```

**Health Monitoring:**

Add DMZ Pi to Uptime Kuma (via Tailscale):

```bash
# On Mac mini (Uptime Kuma)
# Add monitor:
# Type: HTTP(s)
# URL: http://dmz-pi:8080/
# Note: Accessed via Tailscale, not public internet
```

---

## Testing the Setup

### Test 1: Public Access

```bash
# From any device NOT on Tailscale
curl https://<dmz-pi-hostname>.ts.net

# Should return: "DMZ Public Services"
```

### Test 2: Isolation

```bash
# On DMZ Pi - should FAIL
ping <ROUTER_IP>
ssh user@mac-mini.local

# Should SUCCEED
ping <mac-mini-tailscale-ip>
ssh user@<mac-mini-tailscale-ip>
```

### Test 3: Rate Limiting

```bash
# Rapid requests from same IP
for i in {1..150}; do
  curl -s https://dmz-pi.ts.net > /dev/null
done

# Should see 429 (Too Many Requests) after 100 requests
```

### Test 4: Fail2ban

```bash
# After hitting rate limit, check fail2ban
sudo fail2ban-client status caddy

# Should show banned IPs
```

---

## Custom Domain (Optional)

**Requires:** Tailscale paid plan

```bash
# On DMZ Pi
sudo tailscale funnel --set-path=/blog \
  --hostname=blog.yourdomain.com

# Configure DNS CNAME:
# blog.yourdomain.com -> dmz-pi.ts.net
```

---

## Backup and Recovery

### What to Backup

- `/home/user/docker-compose.yml` — Service definitions
- `/home/user/public/` — Static files
- `/home/user/ghost/` — Blog content
- `/etc/caddy/Caddyfile` — Caddy config
- `/etc/iptables/rules.v4` — Firewall rules

### Backup Command

```bash
# On DMZ Pi - push to Mac mini via Tailscale
rsync -avz \
  /home/user/{docker-compose.yml,public,ghost} \
  /etc/caddy/Caddyfile \
  /etc/iptables/rules.v4 \
  mac-mini:/backups/dmz/
```

### Recovery

```bash
# Rebuild DMZ Pi from scratch
# 1. Fresh Raspberry Pi OS install
# 2. Run Phase 1-2 (system setup, Tailscale)
# 3. Restore files from backup
# 4. Run Phase 3-4 (firewall, Caddy)
# 5. Start services
```

**DMZ is designed to be ephemeral** — can be rebuilt quickly from backups.

---

## Maintenance

### Daily
- Automatic security updates (unattended-upgrades)

### Weekly
- Review Caddy access logs for abuse
- Check fail2ban ban list

### Monthly
- Review and update Docker images
- Test backup restore procedure
- Review firewall rules for gaps

### Quarterly
- Rebuild DMZ Pi from scratch (DR drill)
- Update documentation

---

## Security Checklist

- [ ] DMZ Pi cannot ping home LAN IPs
- [ ] DMZ Pi can only SSH via Tailscale
- [ ] Fail2ban is running and configured
- [ ] Automatic updates enabled
- [ ] Rate limiting configured in Caddy
- [ ] Access logs reviewed weekly
- [ ] Minimal packages installed
- [ ] Unnecessary services disabled
- [ ] Backups configured and tested
- [ ] Monitoring in place (Uptime Kuma)

---

## Future Enhancements

1. **DDoS Protection** — Add Cloudflare in front of Tailscale Funnel
2. **WAF (Web Application Firewall)** — Add ModSecurity to Caddy
3. **Intrusion Detection** — Install Snort or Suricata
4. **Log Analysis** — Forward logs to central SIEM
5. **Honeypot** — Deploy decoy service to detect attackers
6. **Geographic Restrictions** — Block traffic from specific countries
7. **Custom Domain** — Use Tailscale custom domain feature

---

## References

- Tailscale Funnel: https://tailscale.com/kb/1223/funnel
- Raspberry Pi Hardening: https://www.raspberrypi.com/documentation/computers/configuration.html#securing-your-raspberry-pi
- Caddy Rate Limiting: https://caddyserver.com/docs/caddyfile/directives/rate_limit
- Fail2ban: https://www.fail2ban.org/
- DMZ Best Practices: https://en.wikipedia.org/wiki/DMZ_(computing)

---

## Support

For questions or issues, see:
- Tailscale Community: https://tailscale.com/contact/support
- Homelab repo: `/docs/` directory
