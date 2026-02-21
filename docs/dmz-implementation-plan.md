# DMZ Implementation Plan — Raspberry Pi 5 Public Services

> **Status:** Ready for Implementation
> **Hardware:** Raspberry Pi 5
> **Services:** Static blog (Hugo), protected file share
> **Public URL:** `<hostname>.ts.net` (custom domain later)

---

## Overview

Deploy a secure DMZ on Raspberry Pi 5 to host public-facing content:
- **Static blog** — Hugo-generated HTML pushed from Mac mini
- **Protected file share** — Password/invite-protected downloads
- **Full homelab integration** — Monitoring, backup, content sync

### Architecture

```
                          Internet
                             │
                             │ HTTPS (Tailscale Funnel)
                             ▼
┌────────────────────────────────────────────────────────────────┐
│  DMZ: Raspberry Pi 5                                            │
│  Hostname: dmz-pi5                                              │
│  Tailscale: dmz-pi5.tail*****.ts.net (public via Funnel)       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Docker Compose Stack                                    │  │
│  │                                                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │   Caddy     │  │   Nginx     │  │   FileBrowser   │  │  │
│  │  │   (proxy)   │─▶│   (blog)    │  │   (protected)   │  │  │
│  │  │   :8080     │  │   :80       │  │   :8081         │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Security Layer:                                                │
│  - iptables: Block outbound to 192.168.x.x (LAN)               │
│  - fail2ban: Ban abusive IPs                                   │
│  - unattended-upgrades: Auto security patches                  │
│                                                                 │
│  Firewall Rules:                                                │
│  ✗ DMZ → Home LAN (192.168.0.0/16) — DROP                      │
│  ✓ DMZ → Internet — ALLOW (updates, Tailscale)                 │
│  ✓ DMZ → Tailscale network — ALLOW (management)                │
│  ✓ LAN → DMZ (via Tailscale) — ALLOW (content push)            │
└────────────────────────────────────────────────────────────────┘
                             │
                             │ Tailscale (private network)
                             │
┌────────────────────────────▼───────────────────────────────────┐
│  Home LAN: Mac mini (homelab platform)                          │
│                                                                 │
│  Content Workflow:                                              │
│  1. Author content locally (Hugo blog, files)                  │
│  2. Build static site: hugo build                              │
│  3. Push to DMZ: scripts/dmz-publish                           │
│                                                                 │
│  Monitoring:                                                    │
│  - Uptime Kuma monitors dmz-pi5 via Tailscale                  │
│                                                                 │
│  Backup:                                                        │
│  - DMZ pushes backups to Mac mini via Tailscale                │
│  - Or: Mac mini pulls from DMZ                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Pi 5 Hardware Setup

**Hardware Required:**
- Raspberry Pi 5 (4GB or 8GB)
- USB-C power supply (27W official recommended)
- MicroSD card (32GB+) OR NVMe SSD with HAT (recommended for performance)
- Ethernet cable (preferred over WiFi)
- Active cooler (recommended for sustained load)

**Initial OS Installation:**

1. Download Raspberry Pi Imager
2. Select: **Raspberry Pi OS Lite (64-bit)** — no desktop needed
3. Configure in Imager settings:
   - Hostname: `dmz-pi5`
   - Username: `dmz` (not default `pi`)
   - Password: Strong unique password
   - SSH: Enable with password auth (will switch to key-only later)
   - WiFi: Skip (use Ethernet)
   - Locale: Your timezone

4. Flash to SD card or NVMe
5. Boot Pi 5 and connect Ethernet

**First Boot Configuration:**

```bash
# SSH into Pi (from Mac mini or any device on LAN)
ssh dmz@dmz-pi5.local

# Update system
sudo apt update && sudo apt full-upgrade -y

# Set timezone
sudo timedatectl set-timezone America/New_York

# Disable swap (SSD longevity)
sudo dphys-swapfile swapoff
sudo systemctl disable dphys-swapfile

# Reboot
sudo reboot
```

**Estimated time:** 30-45 minutes

---

### Phase 2: Security Baseline

**SSH Hardening:**

```bash
# Generate SSH key on Mac mini (if not already exists)
# On Mac mini:
ssh-keygen -t ed25519 -C "homelab-dmz"
ssh-copy-id -i ~/.ssh/id_ed25519.pub dmz@dmz-pi5.local

# Disable password auth on Pi
# On dmz-pi5:
sudo tee /etc/ssh/sshd_config.d/hardening.conf << 'EOF'
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

sudo systemctl restart sshd

# Test SSH key login (from Mac mini)
ssh dmz@dmz-pi5.local
# Should connect without password prompt
```

**Automatic Security Updates:**

```bash
sudo apt install -y unattended-upgrades apt-listchanges

# Enable automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades

# Verify configuration
cat /etc/apt/apt.conf.d/20auto-upgrades
# Should show:
# APT::Periodic::Update-Package-Lists "1";
# APT::Periodic::Unattended-Upgrade "1";
```

**Fail2ban Installation:**

```bash
sudo apt install -y fail2ban

# Create SSH jail
sudo tee /etc/fail2ban/jail.d/ssh.conf << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Verify
sudo fail2ban-client status sshd
```

**Disable Unnecessary Services:**

```bash
# Disable Bluetooth
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# Disable Avahi (mDNS)
sudo systemctl disable avahi-daemon
sudo systemctl stop avahi-daemon

# Remove unnecessary packages
sudo apt autoremove -y
```

**Estimated time:** 20 minutes

---

### Phase 3: Tailscale Installation

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (will show a URL to visit)
sudo tailscale up

# Verify connection
tailscale status

# Note the Tailscale hostname (e.g., dmz-pi5.tail12345.ts.net)
tailscale status --self
```

**Enable Tailscale Funnel:**

```bash
# Enable Funnel on port 443
# This exposes https://dmz-pi5.tail*****.ts.net to the public internet
sudo tailscale funnel 443

# Verify Funnel status
tailscale funnel status

# Expected output:
# Funnel on:
#   - https://dmz-pi5.tail*****.ts.net
```

**Test Public Access:**

From a device NOT on your Tailscale network (e.g., phone on cellular):
```
curl https://dmz-pi5.tail*****.ts.net
# Should show Tailscale's default "connection refused" (no service yet)
```

**Estimated time:** 10 minutes

---

### Phase 4: Network Isolation (iptables)

This is the **critical security layer** — blocks DMZ from accessing home LAN.

```bash
# Install iptables-persistent for rules to survive reboot
sudo apt install -y iptables-persistent

# Create firewall rules
sudo tee /etc/iptables/rules.v4 << 'EOF'
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT DROP [0:0]

# ===== INPUT RULES =====

# Allow loopback
-A INPUT -i lo -j ACCEPT

# Allow established/related connections
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH only from Tailscale interface
-A INPUT -i tailscale0 -p tcp --dport 22 -j ACCEPT

# Allow all Tailscale traffic (management, content push)
-A INPUT -i tailscale0 -j ACCEPT

# Allow HTTP from Tailscale Funnel (internal proxy)
-A INPUT -i tailscale0 -p tcp --dport 8080 -j ACCEPT

# ===== OUTPUT RULES =====

# Allow loopback
-A OUTPUT -o lo -j ACCEPT

# Allow established/related connections
-A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow all Tailscale traffic
-A OUTPUT -o tailscale0 -j ACCEPT

# BLOCK access to private networks (LAN isolation)
# This is the critical DMZ isolation rule
-A OUTPUT -d 192.168.0.0/16 -j DROP
-A OUTPUT -d 10.0.0.0/8 -j DROP
-A OUTPUT -d 172.16.0.0/12 -j DROP

# Allow DNS (for package updates)
-A OUTPUT -p udp --dport 53 -j ACCEPT
-A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow NTP (time sync)
-A OUTPUT -p udp --dport 123 -j ACCEPT

# Allow HTTP/HTTPS (for apt updates, Docker pulls)
-A OUTPUT -p tcp --dport 80 -j ACCEPT
-A OUTPUT -p tcp --dport 443 -j ACCEPT

# Log dropped packets (optional, for debugging)
-A INPUT -j LOG --log-prefix "iptables-INPUT-DROP: " --log-level 4
-A OUTPUT -j LOG --log-prefix "iptables-OUTPUT-DROP: " --log-level 4

# Drop everything else (default policy enforced)

COMMIT
EOF

# Apply rules
sudo iptables-restore < /etc/iptables/rules.v4

# Save for persistence
sudo netfilter-persistent save
```

**Test Isolation:**

```bash
# Should FAIL (blocked by firewall)
ping -c 1 192.168.1.1
# Expected: 100% packet loss or "Operation not permitted"

# Should SUCCEED (Tailscale management)
ping -c 1 $(tailscale ip -4)
# Expected: Reply from Tailscale IP

# Should SUCCEED (Internet access for updates)
ping -c 1 8.8.8.8
# Expected: Reply from Google DNS

# Should SUCCEED (DNS resolution)
nslookup google.com
# Expected: Address returned
```

**Verify from Mac mini:**

```bash
# SSH via Tailscale should work
ssh dmz@dmz-pi5  # Uses Tailscale DNS

# SSH via LAN should work (for now - Pi can receive, just can't initiate)
ssh dmz@dmz-pi5.local
```

**Estimated time:** 15 minutes

---

### Phase 5: Docker Installation

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker dmz

# Log out and back in for group membership
exit
ssh dmz@dmz-pi5

# Verify Docker
docker --version
docker run hello-world

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verify
docker compose version
```

**Estimated time:** 10 minutes

---

### Phase 6: DMZ Services Deployment

**Create directory structure:**

```bash
mkdir -p ~/dmz/{caddy,blog,files,data}
cd ~/dmz
```

**Create Docker Compose stack:**

```bash
cat > ~/dmz/docker-compose.yml << 'EOF'
services:
  # Caddy reverse proxy - receives Funnel traffic on :8080
  caddy:
    image: caddy:2.8-alpine
    container_name: dmz-caddy
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - ./caddy/data:/data
      - ./caddy/config:/config
      - ./caddy/logs:/var/log/caddy
    networks:
      - dmz-net
    healthcheck:
      test: ["CMD", "caddy", "version"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx serves static blog content
  blog:
    image: nginx:alpine
    container_name: dmz-blog
    restart: unless-stopped
    volumes:
      - ./blog/public:/usr/share/nginx/html:ro
      - ./blog/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - dmz-net
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # FileBrowser for protected file sharing
  filebrowser:
    image: filebrowser/filebrowser:v2-alpine
    container_name: dmz-files
    restart: unless-stopped
    environment:
      - FB_NOAUTH=false
      - FB_DATABASE=/database/filebrowser.db
    volumes:
      - ./files/public:/srv:ro       # Read-only public files
      - ./files/database:/database   # FileBrowser database
      - ./files/config:/config       # FileBrowser config
    networks:
      - dmz-net
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  dmz-net:
    driver: bridge
EOF
```

**Create Caddy configuration:**

```bash
cat > ~/dmz/caddy/Caddyfile << 'EOF'
# DMZ Reverse Proxy
# Receives traffic from Tailscale Funnel on :8080

{
    # Disable HTTPS (Tailscale Funnel handles TLS)
    auto_https off

    # Logging
    log {
        output file /var/log/caddy/access.log {
            roll_size 10mb
            roll_keep 5
        }
        format json
    }
}

:8080 {
    # Rate limiting - 100 requests per minute per IP
    # Uncomment when rate_limit module is available
    # rate_limit {
    #     zone dmz {
    #         key {remote_host}
    #         events 100
    #         window 1m
    #     }
    # }

    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }

    # Blog - public, no auth
    handle /blog* {
        uri strip_prefix /blog
        reverse_proxy blog:80
    }

    # Files - protected with FileBrowser auth
    handle /files* {
        uri strip_prefix /files
        reverse_proxy filebrowser:80
    }

    # Root - redirect to blog
    handle / {
        redir /blog permanent
    }

    # Health check endpoint (internal)
    handle /health {
        respond "OK" 200
    }

    # Catch-all - 404
    handle {
        respond "Not Found" 404
    }
}
EOF
```

**Create Nginx configuration for blog:**

```bash
cat > ~/dmz/blog/nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Static file serving
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
    }
}
EOF
```

**Create placeholder blog content:**

```bash
mkdir -p ~/dmz/blog/public
cat > ~/dmz/blog/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DMZ Blog</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: #333; }
        .placeholder {
            background: #f5f5f5;
            padding: 40px;
            border-radius: 8px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="placeholder">
        <h1>Blog Coming Soon</h1>
        <p>This is a placeholder. Hugo-generated content will be published here.</p>
    </div>
</body>
</html>
EOF
```

**Create directories for FileBrowser:**

```bash
mkdir -p ~/dmz/files/{public,database,config}
```

**Configure Tailscale Funnel to forward to Caddy:**

```bash
# Forward public HTTPS to Caddy on port 8080
sudo tailscale funnel --bg 443 http://127.0.0.1:8080
```

**Start services:**

```bash
cd ~/dmz
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Test locally:**

```bash
# On dmz-pi5
curl http://localhost:8080/health
# Expected: OK

curl http://localhost:8080/blog/
# Expected: HTML content

curl http://localhost:8080/files/
# Expected: FileBrowser login page
```

**Test publicly:**

From phone on cellular (not on WiFi/Tailscale):
```
https://dmz-pi5.tail*****.ts.net/blog/
# Expected: Placeholder blog page

https://dmz-pi5.tail*****.ts.net/files/
# Expected: FileBrowser login
```

**Estimated time:** 30 minutes

---

### Phase 7: FileBrowser User Setup

```bash
# Access FileBrowser CLI inside container
docker exec -it dmz-files /filebrowser users add admin <password> --perm.admin

# Or access web UI and create users:
# 1. Visit https://dmz-pi5.tail*****.ts.net/files/
# 2. Default login: admin / admin
# 3. Change password immediately
# 4. Create invite-only users as needed
```

**Estimated time:** 5 minutes

---

### Phase 8: Mac Mini Integration

**Create content publishing script:**

On Mac mini, create `scripts/dmz-publish`:

```bash
#!/usr/bin/env bash
# dmz-publish — Push blog content to DMZ Pi
# Usage: dmz-publish [blog|files|all]

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DMZ_HOST="dmz-pi5"  # Tailscale hostname
DMZ_USER="dmz"
DMZ_PATH="/home/dmz/dmz"

BLOG_SOURCE="${HOMELAB_DIR:-$HOME/homelab}/content/blog/public"
FILES_SOURCE="${HOMELAB_DIR:-$HOME/homelab}/content/files"

info()  { echo -e "${GREEN}[dmz-publish]${NC} $*"; }
warn()  { echo -e "${YELLOW}[dmz-publish]${NC} $*"; }
error() { echo -e "${RED}[dmz-publish]${NC} $*" >&2; }

publish_blog() {
    info "Publishing blog content to DMZ..."

    if [ ! -d "$BLOG_SOURCE" ]; then
        error "Blog source not found: $BLOG_SOURCE"
        error "Run 'hugo build' first to generate static content"
        return 1
    fi

    rsync -avz --delete \
        "$BLOG_SOURCE/" \
        "${DMZ_USER}@${DMZ_HOST}:${DMZ_PATH}/blog/public/"

    info "Blog published successfully"
}

publish_files() {
    info "Publishing files to DMZ..."

    if [ ! -d "$FILES_SOURCE" ]; then
        warn "Files source not found: $FILES_SOURCE"
        warn "Create the directory and add files to share"
        return 0
    fi

    rsync -avz --delete \
        "$FILES_SOURCE/" \
        "${DMZ_USER}@${DMZ_HOST}:${DMZ_PATH}/files/public/"

    info "Files published successfully"
}

case "${1:-all}" in
    blog)
        publish_blog
        ;;
    files)
        publish_files
        ;;
    all)
        publish_blog
        publish_files
        ;;
    *)
        echo "Usage: dmz-publish [blog|files|all]"
        exit 1
        ;;
esac

info "DMZ content updated!"
info "Public URL: https://dmz-pi5.tail*****.ts.net"
```

**Make executable:**

```bash
chmod +x scripts/dmz-publish
```

**Create content directories on Mac mini:**

```bash
mkdir -p content/blog
mkdir -p content/files
```

**Set up Hugo (optional, for blog authoring):**

```bash
# Install Hugo on Mac mini
brew install hugo

# Create new blog site
cd content/blog
hugo new site .

# Add a theme (example: PaperMod)
git clone https://github.com/adityatelange/hugo-PaperMod themes/PaperMod
echo "theme = 'PaperMod'" >> hugo.toml

# Create first post
hugo new posts/hello-world.md

# Build static site
hugo build

# Publish to DMZ
scripts/dmz-publish blog
```

**Estimated time:** 20 minutes

---

### Phase 9: Monitoring Integration

**Add DMZ to Uptime Kuma:**

On Mac mini (via Uptime Kuma web UI or API):

1. **Blog Monitor:**
   - Name: `DMZ Blog`
   - Type: HTTP(s)
   - URL: `http://dmz-pi5:8080/blog/` (via Tailscale)
   - Interval: 60 seconds

2. **Files Monitor:**
   - Name: `DMZ Files`
   - Type: HTTP(s)
   - URL: `http://dmz-pi5:8080/files/` (via Tailscale)
   - Interval: 60 seconds

3. **Caddy Health:**
   - Name: `DMZ Caddy`
   - Type: HTTP(s)
   - URL: `http://dmz-pi5:8080/health`
   - Interval: 30 seconds

4. **SSH Connectivity:**
   - Name: `DMZ SSH`
   - Type: TCP Port
   - Host: `dmz-pi5`
   - Port: `22`
   - Interval: 60 seconds

**Estimated time:** 10 minutes

---

### Phase 10: Backup Integration

**Create backup script on DMZ Pi:**

```bash
cat > ~/dmz/backup.sh << 'EOF'
#!/usr/bin/env bash
# DMZ backup - push to Mac mini via Tailscale
set -euo pipefail

BACKUP_HOST="mac-mini"  # Tailscale hostname
BACKUP_PATH="/Users/user/homelab/backups/dmz"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "[$(date)] Starting DMZ backup..."

# Backup critical files
tar -czf "/tmp/dmz-backup-${TIMESTAMP}.tar.gz" \
    -C /home/dmz/dmz \
    docker-compose.yml \
    caddy/Caddyfile \
    files/database \
    files/config

# Transfer to Mac mini
rsync -avz "/tmp/dmz-backup-${TIMESTAMP}.tar.gz" \
    "${BACKUP_HOST}:${BACKUP_PATH}/"

# Cleanup local temp
rm -f "/tmp/dmz-backup-${TIMESTAMP}.tar.gz"

# Keep only last 7 backups on Mac mini
ssh "${BACKUP_HOST}" "cd ${BACKUP_PATH} && ls -t dmz-backup-*.tar.gz | tail -n +8 | xargs -r rm"

echo "[$(date)] DMZ backup complete"
EOF

chmod +x ~/dmz/backup.sh
```

**Schedule daily backup:**

```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "0 4 * * * /home/dmz/dmz/backup.sh >> /home/dmz/dmz/backup.log 2>&1") | crontab -
```

**Create backup directory on Mac mini:**

```bash
mkdir -p ~/homelab/backups/dmz
```

**Estimated time:** 10 minutes

---

### Phase 11: Fail2ban for Web Traffic

```bash
# Create Caddy jail
sudo tee /etc/fail2ban/jail.d/caddy.conf << 'EOF'
[caddy]
enabled = true
port = http,https,8080
filter = caddy
logpath = /home/dmz/dmz/caddy/logs/access.log
maxretry = 10
bantime = 3600
findtime = 600
action = iptables-multiport[name=caddy, port="http,https,8080", protocol=tcp]
EOF

# Create Caddy filter (for JSON logs)
sudo tee /etc/fail2ban/filter.d/caddy.conf << 'EOF'
[Definition]
failregex = ^.*"remote_ip":"<HOST>".*"status":(429|403|401).*$
            ^.*"remote_ip":"<HOST>".*"status":404.*"uri":"/(wp-admin|phpmyadmin|\.env|\.git).*$
ignoreregex =
EOF

# Restart fail2ban
sudo systemctl restart fail2ban

# Verify
sudo fail2ban-client status caddy
```

**Estimated time:** 10 minutes

---

## Post-Deployment Verification

### Security Checklist

```bash
# Run on DMZ Pi

# 1. Test LAN isolation
ping -c 1 192.168.1.1
# Expected: FAIL (blocked)

# 2. Test Tailscale access
tailscale ping mac-mini
# Expected: SUCCESS

# 3. Test internet access
ping -c 1 8.8.8.8
# Expected: SUCCESS

# 4. Check fail2ban
sudo fail2ban-client status
# Expected: sshd and caddy jails active

# 5. Check auto-updates
sudo systemctl status unattended-upgrades
# Expected: Active

# 6. Check Docker containers
docker compose ps
# Expected: All containers healthy

# 7. Check firewall rules
sudo iptables -L -n
# Expected: DROP rules for private networks
```

### Functional Checklist

- [ ] Blog accessible at `https://dmz-pi5.tail*****.ts.net/blog/`
- [ ] Files accessible at `https://dmz-pi5.tail*****.ts.net/files/` (with login)
- [ ] SSH only works via Tailscale (not from internet)
- [ ] `dmz-publish` successfully pushes content from Mac mini
- [ ] Uptime Kuma shows all DMZ monitors as UP
- [ ] Daily backups appearing in `~/homelab/backups/dmz/`
- [ ] Fail2ban banning abusive IPs

---

## Operations

### Content Publishing Workflow

```bash
# On Mac mini

# 1. Create/edit blog post
cd content/blog
hugo new posts/my-new-post.md
# Edit content/blog/content/posts/my-new-post.md

# 2. Build static site
cd content/blog
hugo build

# 3. Publish to DMZ
scripts/dmz-publish blog

# 4. Verify
open https://dmz-pi5.tail*****.ts.net/blog/
```

### Adding Files to Share

```bash
# On Mac mini

# 1. Add files to content/files/
cp ~/Documents/shared-file.pdf content/files/

# 2. Publish
scripts/dmz-publish files

# 3. Users access via FileBrowser login
```

### Updating DMZ Services

```bash
# SSH to DMZ
ssh dmz@dmz-pi5

# Pull new images
cd ~/dmz
docker compose pull

# Restart with new images
docker compose up -d

# Verify
docker compose ps
```

### Emergency: Rebuild DMZ from Scratch

```bash
# 1. Flash new Raspberry Pi OS to SD/NVMe
# 2. Follow Phase 1-6 of this document
# 3. Restore from backup:
scp mac-mini:~/homelab/backups/dmz/dmz-backup-*.tar.gz /tmp/
cd ~/dmz
tar -xzf /tmp/dmz-backup-*.tar.gz
# 4. Restart services
docker compose up -d
```

---

## Future Enhancements

1. **Custom domain** — Upgrade Tailscale plan, configure DNS CNAME
2. **Analytics** — Add GoAccess or Plausible for visitor stats
3. **Comments** — Add Giscus (GitHub-based) or Cusdis for blog comments
4. **CDN** — Put Cloudflare in front for DDoS protection
5. **More services** — Portfolio site, API endpoints, etc.
6. **VLAN isolation** — Move to router-level isolation for stronger security

---

## Files Created

| File | Purpose |
|------|---------|
| `~/dmz/docker-compose.yml` | Service definitions |
| `~/dmz/caddy/Caddyfile` | Reverse proxy config |
| `~/dmz/blog/nginx.conf` | Blog server config |
| `~/dmz/blog/public/` | Hugo-generated static files |
| `~/dmz/files/public/` | Shared files |
| `~/dmz/backup.sh` | Daily backup script |
| `/etc/iptables/rules.v4` | Firewall rules |
| `/etc/fail2ban/jail.d/` | Fail2ban jails |
| `scripts/dmz-publish` (Mac mini) | Content push script |
| `content/blog/` (Mac mini) | Hugo blog source |
| `content/files/` (Mac mini) | Files to share |

---

## Summary

| Component | Status | Location |
|-----------|--------|----------|
| **Hardware** | Pi 5, Ethernet, SSD boot | Physical |
| **OS** | Raspberry Pi OS Lite 64-bit | dmz-pi5 |
| **Network** | Tailscale Funnel (public HTTPS) | dmz-pi5 |
| **Isolation** | iptables (blocks LAN access) | dmz-pi5 |
| **Security** | fail2ban, auto-updates, key-only SSH | dmz-pi5 |
| **Blog** | Nginx serving Hugo static files | dmz-pi5 |
| **Files** | FileBrowser with password auth | dmz-pi5 |
| **Proxy** | Caddy with security headers | dmz-pi5 |
| **Authoring** | Hugo on Mac mini | Mac mini |
| **Publishing** | rsync via Tailscale | Mac mini → dmz-pi5 |
| **Monitoring** | Uptime Kuma via Tailscale | Mac mini |
| **Backup** | Daily tar to Mac mini | dmz-pi5 → Mac mini |

**Public URL:** `https://dmz-pi5.tail*****.ts.net/`

This design provides strong security (isolated from LAN, key-only SSH, auto-updates, fail2ban) while remaining simple to operate (content push from Mac mini, full homelab integration).
