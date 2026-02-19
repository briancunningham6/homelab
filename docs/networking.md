# Networking & Remote Access

> URL routing, DNS, and Tailscale access model | Parent: [DESIGN.md](../DESIGN.md)

---

## Overview

All services are exposed via `.home` local hostnames routed by Caddy. These are **not real DNS names** — they require a DNS resolver or `/etc/hosts` entries to work. The approach differs depending on whether you are on the local LAN or accessing remotely.

---

## How `.home` hostnames work

Caddy listens on port 80 on the Mac mini and routes requests based on the `Host` header:

```
http://immich.home  →  Caddy  →  immich-server:2283 (Docker internal)
http://login.home   →  Caddy  →  authentik-server:9000
http://copyparty.home → Caddy → (Authentik auth) → copyparty:3923
... etc.
```

For a client to reach `immich.home`, it must:
1. Resolve `immich.home` to the Mac mini's IP address.
2. Have network connectivity to the Mac mini on port 80.

Neither of these is automatic — they require DNS or hosts-file configuration.

---

## Access contexts

### 1. Developer machine (current setup — hosts file)

Your dev machine has `/etc/hosts` entries pointing `.home` names to `127.0.0.1` (local loopback or the Mac mini's LAN IP). This is how the homelab works during development on the same machine.

This approach does **not** scale to other devices or remote access.

---

### 2. Remote access via Tailscale

When you are outside the home network, the Mac mini is reachable via Tailscale at:
- **Tailscale IP:** `100.x.x.x` (find with `tailscale ip -4` on the Mac mini)
- **MagicDNS hostname:** `macmini` (or `macmini.<tailnet-name>.ts.net`)

However, `.home` hostnames still won't resolve unless something maps them to the Mac mini's Tailscale IP. There are two ways to handle this:

---

## Option A: `/etc/hosts` on each client (immediate workaround)

Add entries to your laptop's `/etc/hosts` pointing `.home` names to the Mac mini's **Tailscale IP** (not `127.0.0.1`):

```
# /etc/hosts — replace 100.x.x.x with the Mac mini's Tailscale IP
# Run `tailscale ip -4` on the Mac mini to find it

100.x.x.x   home.home
100.x.x.x   login.home
100.x.x.x   status.home
100.x.x.x   dockge.home
100.x.x.x   immich.home
100.x.x.x   copyparty.home
100.x.x.x   openclaw.home
```

**How it works:**
- When on Tailscale, traffic routes through the VPN to the Mac mini.
- When off Tailscale, the names resolve but connections time out — services are unreachable without the VPN. This is the correct security behaviour.

**Limitation:** Every new device (family phone, tablet) needs its own hosts file update. Not practical for non-technical family members.

---

## Option B: Tailscale Split DNS (recommended end state)

Tailscale's **Split DNS** feature tells all devices on your Tailscale network: *"for the `.home` domain, ask this specific DNS server."* Combined with a lightweight DNS server on the Mac mini, all Tailscale-connected devices resolve `.home` names automatically — no per-device configuration needed.

### Setup steps

#### Step 1: Deploy a DNS resolver on the Mac mini

AdGuard Home is the recommended option — it doubles as an ad blocker and has a clean UI.

> AdGuard Home deployment is tracked as a future platform addition. Until then, use Option A.

Alternatively, `dnsmasq` can be run as a lightweight Docker container.

#### Step 2: Configure the DNS resolver

Add a wildcard rewrite in AdGuard Home (or equivalent):

```
*.home  →  <Mac mini Tailscale IP>
```

This means any `.home` name resolves to the Mac mini, where Caddy handles routing.

#### Step 3: Configure Tailscale Split DNS

In the **Tailscale admin console** (admin.tailscale.com):

1. Go to **DNS** tab.
2. Under **Nameservers**, click **Add nameserver → Custom**.
3. Enter the Mac mini's Tailscale IP as the nameserver.
4. Set the **Restricted to domain**: `.home`
5. Save.

All Tailscale-connected devices will now resolve `*.home` via the Mac mini's DNS — no `/etc/hosts` changes needed on phones, tablets, or family laptops.

### Result

```
Your laptop (on Tailscale, anywhere in the world)
    │
    │  browser: http://immich.home
    │
    ▼
Tailscale Split DNS → Mac mini DNS resolver → resolves immich.home → 100.x.x.x
    │
    ▼
Caddy on Mac mini (port 80)
    │
    ▼
immich-server:2283 (internal Docker)
```

---

## Caddy must listen on the Tailscale interface

By default Caddy binds to `0.0.0.0:80` — it will accept connections on the Tailscale interface automatically. No extra configuration needed.

Verify with:
```bash
docker exec caddy netstat -tlnp 2>/dev/null | grep :80
# or
curl -H "Host: home.home" http://100.x.x.x/
```

---

## Service hostname reference

| Service | Hostname | Port | Notes |
|---------|----------|------|-------|
| Homepage dashboard | `home.home` | 80 | |
| Authentik SSO | `login.home` | 80 | Identity provider |
| Uptime Kuma | `status.home` | 80 | |
| Dockge | `dockge.home` | 80 | Admin only |
| Immich | `immich.home` | 80 | |
| Copyparty | `copyparty.home` | 80 | Authentik forward-auth |
| OpenClaw | `openclaw.home` | 80 | Native host process |

All traffic on these hostnames goes through Caddy on port 80. No services are directly exposed to the network on their native ports (except where explicitly required).

---

## Security properties

- **No internet exposure.** The Mac mini has no router port forwarding. All remote access is via Tailscale only.
- **Tailscale as the network perimeter.** Anyone without a Tailscale device on your tailnet cannot reach any service, even if they know the `.home` hostnames.
- **LAN access.** Devices on the home LAN can reach services if they have DNS resolution (via hosts file or Split DNS pointed at the LAN IP). This is acceptable — LAN devices are trusted.
- **Authentik as the application perimeter.** Even if a device can reach a `.home` hostname via Tailscale, apps that require Authentik login (Copyparty, Immich) will redirect to `login.home` for authentication.

---

## Finding the Mac mini's Tailscale IP

```bash
# Run on the Mac mini
tailscale ip -4
```

Or visit the **Tailscale admin console** → Machines → find `macmini`.

---

## Future: per-app subdomains on a real TLS domain (optional)

If you ever want `immich.yourdomain.com` with a real TLS certificate accessible over the internet (not Tailscale-only), that requires:
- A registered domain name
- Cloudflare Tunnel or nginx/Caddy with ACME DNS challenge
- Deliberate firewall and auth hardening

This is explicitly **out of scope** for the current platform. Remote access via Tailscale is the designed model. Do not add internet exposure without a documented threat model review.
