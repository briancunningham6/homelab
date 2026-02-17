# ADR-004: Tailscale for Secure Remote Access

## Status

**Accepted**

## Date

2026-02-17

## Context

Family members need secure remote access to homelab services from outside the home network. The solution must be simple to set up on client devices, avoid exposing the home network to the public internet, and support the offsite DR target (Raspberry Pi at a relative's house).

## Decision

Use **Tailscale** as the only remote access method. No router port forwarding by default.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| WireGuard (self-hosted) | Open source, no third-party dependency | Manual key management, manual DNS, no NAT traversal help, harder client setup for family | Too much operational overhead for non-technical family members |
| Cloudflare Tunnel | Free tier, no port forwarding, DDoS protection | Routes traffic through Cloudflare (privacy concern), requires domain, more complex for internal-only services | Exposes services to the internet by design; conflicts with "no direct exposure" principle |
| ZeroTier | Similar mesh VPN model to Tailscale | Smaller community, less polished client apps, fewer integrations | Tailscale has better UX and MagicDNS |
| Port forwarding + VPN | Works with any VPN | Exposes router, requires DDNS, fragile | Violates the zero-exposure principle |

## Consequences

- **Positive:** Zero exposed ports on the home router.
- **Positive:** MagicDNS provides stable hostnames across the mesh.
- **Positive:** Simple client setup for family (install app, authenticate, done).
- **Positive:** Enables secure Restic backups to the offsite Pi over encrypted tunnel.
- **Trade-off:** Dependency on Tailscale's coordination servers for connection setup (data still flows peer-to-peer). Acceptable given Tailscale's reliability and the option to self-host Headscale if needed in the future.
- **Trade-off:** Free tier has device limits. Currently sufficient for family use.

## References

- [Tailscale documentation](https://tailscale.com/kb/)
- [Headscale](https://github.com/juanfont/headscale) — self-hosted alternative coordination server
