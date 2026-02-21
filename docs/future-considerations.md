# Future Considerations

Items identified but deferred for future implementation.

---

## HTTPS/TLS Implementation

**Status:** Deferred
**Priority:** Medium
**Date Added:** 2026-02-21

### Current State

All services run over HTTP. Access is secured via:
- LAN isolation (local network only)
- Tailscale WireGuard encryption (for remote access)

### Why HTTPS May Be Needed

1. **App Requirements:**
   - Immich mobile app may require HTTPS
   - Authentik OAuth flows work better with HTTPS
   - Jellyfin Chromecast requires HTTPS
   - Matrix federation requires HTTPS
   - PWA/Service Worker features require HTTPS

2. **Browser Warnings:**
   - Modern browsers flag HTTP sites as "Not Secure"
   - Some features (camera access, geolocation) require HTTPS

3. **Best Practice:**
   - End-to-end encryption even on trusted networks
   - Protects against LAN-based attacks

### Implementation Options

#### Option 1: Local CA with Caddy (Recommended)
Create a local Certificate Authority and have Caddy serve HTTPS with local certs.

**Pros:**
- Keeps `.home` hostnames
- Works for LAN and Tailscale
- Full control

**Cons:**
- Requires installing CA cert on each family device
- Manual cert management

**Implementation:**
- Generate CA with `mkcert` or similar
- Configure Caddy to use local certs
- Distribute CA cert to devices

#### Option 2: Tailscale HTTPS
Use Tailscale's built-in HTTPS with `*.ts.net` hostnames.

**Pros:**
- Automatic certificate management
- Zero configuration

**Cons:**
- Changes hostnames from `*.home` to `*.ts.net`
- Only works for Tailscale clients
- No LAN-only access

#### Option 3: Split DNS with Real Domain
Register a domain, use Let's Encrypt, configure split DNS.

**Pros:**
- Proper certificates everywhere
- No trust issues

**Cons:**
- Requires domain registration
- DNS configuration complexity
- Split DNS can be fragile

### Recommendation When Implementing

Start with **Option 1 (Local CA)**:
1. Generate CA with `mkcert`
2. Update Caddyfile to use `https://` blocks
3. Install CA cert on family devices
4. Test all services

### References

- ADR to be created when implemented
- Related: `docs/security.md` § 2.2 (TLS)
- Caddy docs: https://caddyserver.com/docs/caddyfile/options#local-certs

---

## Additional Future Items

*(Add new items here as they're identified)*
