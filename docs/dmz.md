# DMZ Architecture

> Internet-facing services on isolated infrastructure | Parent: [DESIGN.md](../DESIGN.md)

---

## Overview

The homelab uses a **two-zone architecture** to balance security with the need for certain internet-facing services:

| Zone | Hardware | Exposure | Trust Level | Purpose |
|------|----------|----------|-------------|---------|
| **Internal** | Mac mini | Tailscale-only | High | Family data, identity, backups |
| **DMZ** | Raspberry Pi | Internet-facing | Low | Public services (blog, Matrix) |

This separation ensures that a compromise of internet-exposed services does not grant access to family photos, identity data, or other sensitive information.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ Ports 80, 443, 8448 (Matrix federation)
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DMZ ZONE (Raspberry Pi)                              │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │    Caddy     │  │    Blog      │  │   Conduit    │                       │
│  │ (TLS, Let's  │  │              │  │   (Matrix)   │                       │
│  │  Encrypt)    │  │              │  │              │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
│         │                                   │                                │
│         └───────────── Tailscale ───────────┘                                │
│                           │                                                  │
└───────────────────────────│─────────────────────────────────────────────────┘
                            │
                            │ Encrypted VPN tunnel
                            │
┌───────────────────────────│─────────────────────────────────────────────────┐
│                    INTERNAL ZONE (Mac mini)                                  │
│                           │                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Authentik   │◄─┤  PostgreSQL  │  │    Immich    │  │   Restic     │     │
│  │   (OIDC)     │  │   (shared)   │  │   (photos)   │  │  (backups)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                                              │
│                    NO INTERNET EXPOSURE - Tailscale only                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Security Model

### Zone Isolation Principles

1. **DMZ is expendable** — If compromised, the Pi can be wiped and rebuilt. No family data is stored there.
2. **Internal zone is protected** — The Mac mini has no internet exposure. All remote access is via Tailscale.
3. **Communication is explicit** — DMZ services can only reach specific internal services over Tailscale, never the reverse.
4. **Credentials are scoped** — DMZ services get minimal credentials (OIDC client ID/secret), never admin access.

### Trust Boundaries

| From | To | Allowed | Method | Purpose |
|------|-----|---------|--------|---------|
| Internet | DMZ Pi | Yes | Ports 80, 443, 8448 | Public services |
| Internet | Mac mini | **No** | Blocked | — |
| DMZ Pi | Authentik | Yes | Tailscale | OIDC authentication |
| DMZ Pi | Other Mac mini services | **No** | Blocked | Isolation |
| Mac mini | DMZ Pi | Yes | Tailscale | Backups, management |
| Family devices | DMZ Pi | Yes | Tailscale | Access without internet |

### What DMZ Pi Can Access (via Tailscale)

| Service | Port | Purpose | Credentials |
|---------|------|---------|-------------|
| Authentik | 9000 | OIDC login for Matrix users | Client ID + secret only |

### What DMZ Pi Must NEVER Access

- Docker socket on Mac mini
- Control panel or Dockge
- PostgreSQL (unless explicitly required and documented)
- Immich or other app data
- `.env` files or secrets from Mac mini
- Restic repository passwords

---

## DMZ Pi Hardening

### Base OS Configuration

```bash
# Automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Firewall (ufw)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH (consider restricting to Tailscale IP)
sudo ufw allow 80/tcp    # HTTP (Let's Encrypt + redirect)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8448/tcp  # Matrix federation
sudo ufw enable

# Fail2ban for SSH
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### SSH Hardening

```bash
# /etc/ssh/sshd_config additions
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers pi  # or your username
```

### Container Security

Same principles as Mac mini (see [security.md](security.md)):
- Pinned image tags
- Non-root containers
- No privileged mode
- Resource limits

---

## Services on DMZ Pi

### Current

| Service | Hostname | Purpose | Ports |
|---------|----------|---------|-------|
| Blog | blog.yourdomain.com | Public website | 443 |

### Planned

| Service | Hostname | Purpose | Ports |
|---------|----------|---------|-------|
| Matrix (Conduit) | matrix.yourdomain.com | Federated messaging | 443, 8448 |
| Element Web | element.yourdomain.com | Matrix web client (optional) | 443 |

---

## Networking

### DNS Requirements

For internet-facing services, you need public DNS records:

```
# A records pointing to your home IP (or CNAME to dynamic DNS)
matrix.yourdomain.com    A    <your-public-ip>
blog.yourdomain.com      A    <your-public-ip>

# Matrix federation SRV record (optional but recommended)
_matrix._tcp.yourdomain.com    SRV    10 5 8448 matrix.yourdomain.com
```

### Router Port Forwarding

Forward these ports to the DMZ Pi's LAN IP:

| External Port | Internal Port | Protocol | Service |
|---------------|---------------|----------|---------|
| 80 | 80 | TCP | HTTP (Let's Encrypt, redirects) |
| 443 | 443 | TCP | HTTPS (all services) |
| 8448 | 8448 | TCP | Matrix federation |

**Important:** Only forward to the DMZ Pi. The Mac mini should have **no** port forwards.

### Caddy on DMZ Pi

The DMZ Pi runs its own Caddy instance for TLS termination:

```caddyfile
# /etc/caddy/Caddyfile on DMZ Pi

matrix.yourdomain.com {
    reverse_proxy localhost:6167  # Conduit
}

matrix.yourdomain.com:8448 {
    reverse_proxy localhost:6167  # Federation
}

blog.yourdomain.com {
    # Your blog configuration
}
```

---

## Backup Strategy

DMZ Pi data is backed up to the Mac mini via Tailscale:

```
DMZ Pi (Conduit data)
    → Restic over Tailscale
    → Mac mini backup repository
    → Offsite DR Pi
```

### What to Back Up

| Service | Data Location | Backup Method |
|---------|---------------|---------------|
| Conduit | `/opt/conduit/data/` | Restic to Mac mini |
| Caddy | `/etc/caddy/Caddyfile` | Git or Restic |
| System config | `/etc/` (selected files) | Restic |

### Recovery

If the DMZ Pi is compromised or fails:
1. Wipe and reinstall Raspberry Pi OS
2. Apply hardening configuration
3. Install Docker and Tailscale
4. Restore services from backup
5. Update DNS if IP changed

---

## Disaster Recovery

### Scenario: DMZ Pi Compromised

1. **Immediate:** Disconnect Pi from network (unplug Ethernet)
2. **Assess:** Check what was exposed (Matrix messages are end-to-end encrypted, so content is safe)
3. **Contain:** Revoke OIDC client credentials in Authentik
4. **Recover:** Wipe Pi, reinstall from scratch, restore from backup
5. **Review:** Check Authentik logs for any suspicious logins

### Scenario: DMZ Pi Hardware Failure

1. Acquire replacement Raspberry Pi
2. Install OS and apply hardening
3. Join to Tailscale
4. Restore services from backup
5. Update router port forwarding if IP changed

---

## Future Considerations

### Additional DMZ Services

Other candidates for DMZ hosting:
- Gitea/Forgejo (if public repos needed)
- Nextcloud (if external sharing required)
- Vaultwarden (if external access required)

### Cloudflare Tunnel Alternative

Instead of direct port forwarding, consider Cloudflare Tunnel:
- No ports exposed on home router
- DDoS protection
- Hides home IP address
- Adds latency but improves security

This would be a significant architecture change and should be evaluated separately.

---

## Related Documents

| Document | Relevance |
|----------|-----------|
| [security.md](security.md) | Overall security model, threat actors |
| [networking.md](networking.md) | Internal zone networking |
| [nodes.md](nodes.md) | Node registry including DMZ Pi |
| [ops-standard.md](ops-standard.md) | Backup and DR procedures |
