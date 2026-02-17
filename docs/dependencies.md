# Dependencies & Licensing

> Software dependencies, licensing risks, and platform portability | Parent: [DESIGN.md](../DESIGN.md)

---

## 1. Component Licence Summary

Every component in the platform and its licence, with risk notes where relevant.

### Core platform

| Component | Licence | Risk | Notes |
|-----------|---------|------|-------|
| **Docker Engine** | Apache 2.0 | :green_circle: Low | Open source. The Engine itself is free. |
| **Docker Desktop** (macOS) | Docker Subscription Service Agreement | :red_circle: **High** | **Proprietary.** Free for personal use, but licence terms can change. Required on macOS because Docker Engine doesn't run natively. See §3 for alternatives. |
| **Docker Compose** | Apache 2.0 | :green_circle: Low | Open source, ships with Docker Engine. |
| **Dockge** | MIT | :green_circle: Low | Open source. |
| **Homepage** | GPL-3.0 | :green_circle: Low | Open source. Copyleft applies if you modify and distribute it. |
| **Caddy** | Apache 2.0 | :green_circle: Low | Open source. Commercial support available but not required. |
| **Tailscale** (client) | BSD-3-Clause | :yellow_circle: Medium | Client is open source. **Coordination server is proprietary SaaS** — see §2. |
| **Uptime Kuma** | MIT | :green_circle: Low | Open source. |

### Identity

| Component | Licence | Risk | Notes |
|-----------|---------|------|-------|
| **Authentik** | Source Available (custom) | :yellow_circle: Medium | Not a standard OSI-approved open source licence. Free to self-host. Enterprise features require a paid licence. See §2. |
| **PostgreSQL** (Authentik dep) | PostgreSQL Licence (permissive) | :green_circle: Low | Open source. |
| **Redis** (Authentik dep) | BSD-3-Clause / SSPL for Redis Ltd modules | :yellow_circle: Medium | Core Redis is BSD. Some Redis Ltd modules are SSPL (not OSI-approved). Authentik uses core Redis features — currently low risk but monitor. |

### Data protection

| Component | Licence | Risk | Notes |
|-----------|---------|------|-------|
| **Restic** | BSD-2-Clause | :green_circle: Low | Open source. |
| **Backblaze B2** | Proprietary SaaS | :yellow_circle: Medium | Cloud storage with usage-based pricing. No data lock-in — Restic uses S3-compatible API, portable to any S3 provider. |

### Applications

| Component | Licence | Risk | Notes |
|-----------|---------|------|-------|
| **Immich** | AGPL-3.0 | :green_circle: Low | Open source. Strong copyleft — if you modify the server and expose it to users, you must share source. Fine for personal/family use as-is. |
| **Copyparty** | MIT | :green_circle: Low | Open source. |
| **Trader** | Private / Custom | :yellow_circle: Medium | Your own app — no external licence dependency, but you control the terms. Ensure any libraries it uses are licence-compatible. |

### AI

| Component | Licence | Risk | Notes |
|-----------|---------|------|-------|
| **Ollama** | MIT | :green_circle: Low | Open source. |
| **Open WebUI** | MIT | :green_circle: Low | Open source. |
| **LLM model weights** | Varies per model | :yellow_circle: Medium | Each model has its own licence (Llama: Meta Community Licence, Mistral: Apache 2.0, etc.). Some restrict commercial use. Review individual model licences before deploying. |

### Host operating system

| Component | Licence | Risk | Notes |
|-----------|---------|------|-------|
| **macOS** | Proprietary (Apple EULA) | :red_circle: **High** | Tied to Apple hardware. Cannot run on non-Apple machines. Major platform lock-in — see §3. |
| **Homebrew** | BSD-2-Clause | :green_circle: Low | Open source package manager. macOS and Linux. |

---

## 2. Key Licensing Risks in Detail

### Docker Desktop on macOS

Docker Engine (the actual container runtime) is open source, but it requires a Linux kernel. On macOS, you need a wrapper that provides a Linux VM:

- **Docker Desktop** is the default option. It is **proprietary** with a subscription-based licence. Currently free for personal use and small businesses (<250 employees, <$10M revenue), but Docker Inc. has changed these terms before (notably in 2021) and could do so again.
- **Impact if terms change:** You'd need to switch to an alternative (see Colima below) or move to Linux.

**Mitigation:** See §3 — Colima is a drop-in replacement that eliminates Docker Desktop dependency entirely.

### Tailscale coordination server

The Tailscale **client** is open source (BSD-3), but the **coordination server** (login, key exchange, ACLs, MagicDNS) is proprietary SaaS operated by Tailscale Inc.:

- Free tier: up to 100 devices, 3 users. Sufficient for family use currently.
- **Risk:** If Tailscale changes pricing, removes the free tier, or shuts down, the coordination server is gone. Your mesh network stops working.
- **Mitigation:** [Headscale](https://github.com/juanfont/headscale) is a BSD-3 licensed, self-hosted alternative coordination server. It's compatible with official Tailscale clients. Migration is possible but requires re-keying devices. Evaluate Headscale if Tailscale dependency becomes a concern.

### Authentik licensing

Authentik uses a **custom source-available licence** (not OSI-approved "open source"):

- Free to self-host for any use.
- Source code is publicly available.
- Enterprise features (e.g., enterprise SSO, support, advanced outpost features) require a paid licence.
- **Risk:** The maintainers could change the licence for future versions (this has happened with other "source available" projects — Redis, Elasticsearch, HashiCorp). You are not guaranteed the same terms in perpetuity.
- **Mitigation:** Current features needed for this homelab are all in the free tier. If terms change, alternatives exist (Keycloak under Apache 2.0, Authelia under Apache 2.0 — though both have trade-offs documented in [ADR-002](adrs/002-authentik-identity.md)). Pin to a known-good version before evaluating migration if needed.

### Redis licensing (SSPL concern)

In 2024, Redis Ltd re-licenced Redis server modules under the Server Side Public License (SSPL), which is **not** OSI-approved and restricts offering Redis as a service. The core server remains BSD-3, but the boundary between "core" and "modules" is controlled by Redis Ltd.

- **Current risk:** Low — Authentik uses core Redis features.
- **Future risk:** If Redis Ltd moves more functionality behind SSPL, alternatives like [Valkey](https://github.com/valkey-io/valkey) (BSD-3, Linux Foundation fork) or [KeyDB](https://github.com/Snapchat/KeyDB) can replace Redis with minimal config changes.

---

## 3. macOS vs. Linux — Platform Portability

### Current macOS dependencies

The design currently assumes macOS on a Mac mini. The macOS-specific touchpoints are:

| Dependency | macOS-specific | Linux equivalent |
|------------|---------------|-----------------|
| Docker runtime | Docker Desktop or Colima (VM-based) | Docker Engine (native, no VM needed) |
| Auto-start | `launchd` plist files in `~/Library/LaunchAgents/` | `systemd` unit files |
| External storage paths | `/Volumes/HomelabData/` | `/mnt/homelab-data/` or similar |
| Filesystem | APFS (default) | ext4 / XFS / ZFS |
| Package manager | Homebrew | apt / dnf / pacman |

### Can this run on Linux?

**Yes — the architecture is almost entirely portable.** Every containerised service runs identically on Linux. The only work required is:

| Migration task | Effort |
|----------------|--------|
| Replace Docker Desktop / Colima with native Docker Engine | Trivial — Docker Engine is simpler and faster on Linux |
| Convert `launchd` plists to `systemd` services | Low — one-time rewrite of 2–3 service files |
| Update storage mount paths in Compose files and docs | Low — find/replace `/Volumes/HomelabData/` → `/mnt/homelab-data/` |
| Update `scripts/` for any macOS-specific commands | Low — mostly path changes |
| Verify Tailscale client config | Trivial — Tailscale works natively on Linux |

**Estimated total migration effort:** A few hours for an experienced operator. No application changes required — only host-level configuration.

### Advantages of moving to Linux

| Benefit | Detail |
|---------|--------|
| No Docker Desktop dependency | Docker Engine runs natively — no VM layer, better performance, no licence risk |
| Wider hardware support | Not tied to Apple hardware; run on any x86/ARM machine |
| Lower cost | Used enterprise hardware (Dell micro PCs, Intel NUCs) is cheap and powerful |
| Better container ecosystem | Most self-hosted projects target Linux first; fewer edge cases |
| ZFS support | Native ZFS for snapshots, compression, and data integrity (not available on macOS without workarounds) |
| systemd integration | More robust service management than launchd for server workloads |

### Recommendation

Design all Compose files, scripts, and documentation to be **OS-agnostic where possible**. The macOS-specific items should be isolated to:
- [docs/notes/mac-mini.md](notes/mac-mini.md) — macOS-specific config
- `launchd` plist files (keep in a `platform/launchd/` directory)
- Storage mount paths (use a variable or `.env` reference rather than hardcoding `/Volumes/`)

This way, adding a Linux node (or migrating entirely) requires only host-level changes, not application changes.

---

## 4. Proprietary SaaS Dependencies

Services that depend on external proprietary infrastructure:

| Service | What's proprietary | Self-hosted alternative | Migration effort |
|---------|--------------------|------------------------|------------------|
| **Tailscale** coordination | Login, key exchange, ACL management | Headscale (BSD-3) | Medium — re-key all devices |
| **Backblaze B2** | Cloud object storage | Any S3-compatible storage (MinIO, Wasabi, or just the offsite Pi) | Low — change Restic backend config |
| **Docker Desktop** | macOS container runtime | Colima (MIT) — uses Lima VMs + Docker Engine | Low — drop-in replacement |
| **Apple macOS** | Host operating system | Any Linux distribution | Medium — see §3 migration table |
| **GitHub** | Git hosting, CI/CD (future) | Gitea (MIT), Forgejo (MIT) | Low for hosting; higher if using GitHub Actions |

### Fully self-hostable alternative stack

If the goal were to eliminate **all** proprietary dependencies, the substitutions would be:

| Current | Replacement | Licence |
|---------|-------------|---------|
| macOS | Ubuntu Server / Debian | GPL / DFSG |
| Docker Desktop | Docker Engine (native on Linux) | Apache 2.0 |
| Tailscale | Headscale + Tailscale clients | BSD-3 |
| Backblaze B2 | Offsite Pi only (already planned) | N/A |
| GitHub | Forgejo (self-hosted) | MIT |
| Authentik | Authentik (self-hosted, current terms) or Keycloak (Apache 2.0) | — |

This is achievable today with moderate effort. The design does not have any hard dependency that prevents full self-hosting.

---

## 5. Dependency Monitoring

Track licence changes for high and medium risk components:

| Component | Watch for | How to monitor |
|-----------|-----------|---------------|
| Docker Desktop | Licence term changes | Docker blog, release notes |
| Tailscale | Free tier changes, service terms | Tailscale blog, pricing page |
| Authentik | Licence model changes, feature gating | GitHub releases, blog |
| Redis | SSPL scope expansion | Redis blog, Valkey project |
| LLM models | Per-model licence changes | Model cards on Hugging Face / Ollama library |

**Review frequency:** Quarterly, aligned with the security exposure review in [ops-standard.md](ops-standard.md) §3.
