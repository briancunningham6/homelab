# Security Model

> Platform security architecture and operational practices | Parent: [DESIGN.md](../DESIGN.md)

---

## Guiding Principle

This platform stores and manages a family's personal data — photos, files, identity information, and potentially financial data. Security must be strong enough to protect that data from external threats and internal mistakes, but not so burdensome that family members avoid using the system.

**Design for sound architecture first, then layer on best practices.** A system that people circumvent because it's too annoying is less secure than one they actually use.

---

## 1. Threat Model

Understand what we're defending against and what is out of scope.

### 1.1 What We're Protecting

| Asset | Sensitivity | Examples |
|-------|-------------|---------|
| **Personal media** | High | Family photos, videos (Immich) |
| **Identity data** | Critical | Usernames, passwords, MFA seeds, SSO tokens (Authentik) |
| **Shared files** | Medium–High | Documents, uploads (Copyparty) |
| **Financial data** | Critical | Exchange API keys, trade history, portfolio (Trader) |
| **Platform configuration** | High | Compose files, `.env` secrets, backup encryption keys |
| **AI conversations** | Medium | Chat history, prompts, personal context (Open WebUI) |
| **Backup data** | High | Encrypted snapshots containing all of the above |

### 1.2 Threat Actors

| Actor | Likelihood | Capability |
|-------|------------|------------|
| **Opportunistic internet scanner** | High | Automated port scanning, known CVE exploitation |
| **Targeted remote attacker** | Low | Unlikely for a family homelab — but not impossible if financial data present |
| **Compromised app / supply chain** | Medium | Malicious Docker image update, dependency hijack |
| **Credential theft / phishing** | Medium | Password reuse, phishing for SSO credentials |
| **Physical access / theft** | Low–Medium | Someone with physical access to the Mac mini or offsite Pi |
| **Curious family member** | Medium | Child or guest accessing things they shouldn't — not malicious, but must be gated |
| **AI agent misbehaviour** | Medium | OpenClaw agent exceeding intended scope, data leakage between agent lanes |

### 1.3 What Is Out of Scope

- Nation-state adversaries
- Sophisticated targeted attacks on the home network
- Attacks on Tailscale's coordination infrastructure (accepted risk — see [dependencies.md](dependencies.md))
- Vulnerabilities in Apple hardware/firmware

---

## 2. Network Security

### 2.1 Zero Exposure by Default

The single most important security decision in this platform: **no ports are forwarded from the router to any homelab service**. All remote access flows through Tailscale.

| Control | Detail |
|---------|--------|
| No port forwarding | Router firewall blocks all inbound connections to homelab services |
| Tailscale-only remote access | Encrypted WireGuard tunnels, no public IP exposure |
| MagicDNS | Internal-only DNS names; not resolvable from the public internet |
| Caddy local routing | Reverse proxy binds to local/Tailscale interfaces, not `0.0.0.0` |

**Why this matters:** The vast majority of homelab compromises start with an internet-exposed service. By removing that attack surface entirely, we eliminate the highest-probability threat vector.

### 2.2 Internal Network Segmentation

| Control | Detail |
|---------|--------|
| Docker networks | Each Compose stack gets its own Docker bridge network; services only communicate with what they need |
| No `network_mode: host` | Containers don't share the host's network namespace unless absolutely required (document exceptions) |
| Inter-service access | Services speak to each other via internal Docker DNS, not published host ports |
| Admin UI restriction | Dockge, Authentik admin, control panel accessible only via LAN or Tailscale — never from wider network |

### 2.3 DNS & TLS

| Control | Detail |
|---------|--------|
| Local hostnames | Stable names via Caddy (`immich.home`, `login.home`, etc.) |
| TLS on local network | Caddy provides HTTPS with locally-trusted certificates where possible |
| No split-horizon DNS | Avoid complexity; Tailscale MagicDNS handles remote resolution |

---

## 3. Identity & Authentication

Authentik is the security backbone. Every security boundary flows through it.

### 3.1 Authentication Policies

| Control | Detail |
|---------|--------|
| No shared accounts | One account per person — no "family" logins |
| No self-registration | Admin-only account creation via enrollment links ([onboarding.md](onboarding.md)) |
| Strong passwords | Enforce minimum complexity at the Authentik policy level |
| MFA required | Mandatory for `homelab-admin` and `parents` groups; configurable for `kids` |
| MFA method | TOTP (authenticator app) preferred; WebAuthn/passkeys encouraged when supported |
| Session lifetimes | Reasonable expiry — long enough for family use, short enough that stale sessions don't linger (configurable per policy) |
| Brute-force protection | Authentik's built-in rate limiting and reputation scoring on login attempts |

### 3.2 Authorisation Model

| Control | Detail |
|---------|--------|
| Group-based RBAC | Access determined by Authentik group membership, not per-user config |
| Least privilege | Users get minimum groups needed; new apps don't auto-grant access to existing users |
| Role separation | `homelab-admin`, `parents`, `kids` are distinct lanes with different capabilities |
| App-specific groups | Every app has `<app>-admin` and `<app>-user` minimum; mapped to app roles via OIDC/SAML claims |
| Access matrix | All mappings documented in [access-matrix.md](access-matrix.md) |

### 3.3 Break-Glass Access

A "break-glass" account exists for emergency recovery when Authentik is unavailable.

| Control | Detail |
|---------|--------|
| Account | Authentik's `akadmin` bootstrap account |
| Storage | Credentials stored in password manager **and** sealed offline copy (not on the homelab itself) |
| Usage policy | Only for recovery scenarios — all uses logged and reviewed |
| Individual app admin | Each app retains a local emergency admin account, documented securely |

---

## 4. Secrets Management

### 4.1 Where Secrets Live

| Secret Type | Storage Location | Access |
|-------------|------------------|--------|
| App configuration secrets | `.env` files in each app/platform folder | Read by Docker Compose at startup |
| Authentik signing/encryption keys | Authentik database + exported in backup | Managed by Authentik |
| Restic repository passwords | `.env` or dedicated secret file | Used by backup scripts |
| Break-glass credentials | External password manager + offline copy | Admin only |
| Exchange API keys (Trader) | `.env` in Trader app folder | Read by Trader container only |
| Tailscale auth keys | Tailscale admin console | One-time use, expire after setup |

### 4.2 What We Do NOT Do

- **No secrets in source control** — `.env` is in `.gitignore`; only `.env.example` with placeholder values is committed
- **No secrets in container images** — images contain no credentials; all injected at runtime via environment
- **No hardcoded credentials** — every secret is externalised to `.env` or Docker secrets
- **No secrets in logs** — applications should not log secrets; review log output during deployment testing

### 4.3 Secret Rotation

| Secret | Rotation Policy |
|--------|----------------|
| Admin user passwords | Change on suspected compromise; review annually |
| App-specific API keys | Rotate on compromise or personnel change |
| Restic backup passwords | Rotate with extreme care — losing this means losing access to all encrypted backups |
| Authentik secret key | Rotate only during clean reinstall — changes invalidate all sessions |
| Break-glass credentials | Verify quarterly (ops-standard.md § 3); update if admin credentials change |

### 4.4 Future Consideration: Centralised Secrets

The current `.env`-per-app approach is simple and appropriate for the platform's scale. If the platform grows significantly, evaluate:
- **Docker Secrets** (Swarm mode) — adds complexity but improves secret isolation
- **HashiCorp Vault** — full secrets management; overkill at current scale
- **Infisical / SOPS** — encrypted secrets in Git; may improve secrets-in-version-control story

---

## 5. Container Security

### 5.1 Image Supply Chain

| Control | Detail |
|---------|--------|
| Pinned image tags | Every `compose.yml` uses explicit version tags, never `latest` |
| Trusted sources | Prefer official images from Docker Hub, GitHub Container Registry, or project-maintained registries |
| Changelog review | Read release notes before every update — check for security advisories and known vulnerabilities |
| No automatic updates | No Watchtower, Diun auto-pull, or scheduled image pulls |
| Verify image signatures | Where available (e.g., Docker Content Trust, cosign), verify image provenance |

### 5.2 Container Runtime

| Control | Detail |
|---------|--------|
| Non-root containers | Run as non-root user inside containers where feasible |
| Read-only root filesystem | Where supported, mount container root as read-only and use tmpfs for writable paths |
| No `privileged` mode | Never use `--privileged` unless absolutely required (document and justify any exception) |
| Minimal capabilities | Drop all Linux capabilities and add back only what's needed (`cap_drop: [ALL]`, `cap_add: [...]`) |
| No host network mode | Use Docker bridge networks; avoid `network_mode: host` |
| Resource limits | Set memory and CPU limits for resource-heavy containers (Immich ML, Ollama) to prevent runaway processes from affecting the host |

### 5.3 Docker Socket Access

The control panel requires Docker socket (`/var/run/docker.sock`) access, which is effectively root-equivalent on the host.

| Control | Detail |
|---------|--------|
| Acknowledged risk | Docker socket access = root on the host. This is a deliberate trade-off for management capability. |
| Limited exposure | Only the control panel mounts the socket; no other app receives it |
| Admin-only access | Control panel is gated by `homelab-admin` Authentik group |
| Socket proxy (future) | Consider a Docker socket proxy (e.g., Tecnativa docker-socket-proxy) to restrict API calls to read-only or specific endpoints |

---

## 6. Data Protection

### 6.1 Data at Rest

| Control | Detail |
|---------|--------|
| Backup encryption | Restic encrypts all backup data client-side before it leaves the Mac mini |
| Disk encryption | macOS FileVault on internal disk (enabled by default); evaluate LUKS if migrating to Linux |
| External storage | External SSD should use encrypted volume (APFS encrypted or LUKS) |
| Offsite Pi | Restic repository on the Pi is already encrypted — even physical theft of the Pi doesn't expose data |

### 6.2 Data in Transit

| Control | Detail |
|---------|--------|
| Tailscale | WireGuard encryption for all remote connections |
| Caddy HTTPS | TLS for local service-to-browser communication |
| Restic to offsite | Encrypted data over Tailscale (double encrypted: Restic encryption + WireGuard tunnel) |
| No unencrypted services | Every user-facing service should be accessed via HTTPS (Caddy) or Tailscale |

### 6.3 Data Destruction

Covered fully in [teardown.md](teardown.md) — but from a security angle:

- When decommissioning storage, ensure data is actually destroyed (not just files deleted)
- Docker volume removal (`docker volume rm`) does not securely erase — for sensitive data, overwrite or destroy the underlying disk
- Offsite Pi: if decommissioned, securely wipe the external HDD

---

## 7. OpenClaw Agent Security

OpenClaw is the most experimental and least mature part of the security model. This section documents the known risks and the controls that must be in place before agents handle real data.

### 7.1 Accepted Risk

OpenClaw introduces an AI-agent layer that can take actions on behalf of users. This is inherently a broader attack surface than a traditional web application. The decision to include it is deliberate:

- **Why:** The agent layer is central to the platform's vision and differentiation
- **Risk acceptance:** The admin is willing to experiment during this development phase, with the expectation that security matures alongside the implementation
- **Constraint:** OpenClaw must never be the sole path to any critical function — every action it performs must also be possible via direct admin intervention

### 7.2 Agent Isolation Requirements

| Control | Detail |
|---------|--------|
| Per-user scoping | Each agent operates within the permissions of its associated Authentik user |
| Lane enforcement | Agent capabilities derive from group membership — a child agent cannot perform parent or admin actions |
| No cross-user leakage | Agent memory, conversation context, and credentials are isolated per user |
| No privilege escalation | An agent cannot grant itself additional permissions or act outside its lane |
| Credential injection | Agents receive app credentials via controlled injection, not by reading `.env` files directly |

### 7.3 Admin Agent Controls

The admin agent has the highest privilege and therefore the highest risk.

| Control | Detail |
|---------|--------|
| Destructive action confirmation | Delete, teardown, user removal, and data wipe require explicit human confirmation — the agent proposes, the admin approves |
| Audit logging | Every infrastructure action taken by the admin agent is logged with timestamp, action, target, and outcome |
| Scope boundary | Admin agent operates within `~/homelab/**` — no arbitrary host commands without explicit approval |
| Rollback capability | Agent-initiated changes must follow the same reversibility principles as manual operations (pre-backup, pinned tags, documented rollback) |

### 7.4 Data Handling

| Control | Detail |
|---------|--------|
| No cross-user data in context | Agent must not include User A's data in User B's conversation or tool responses |
| Sensitive data minimisation | Agents should not persist API keys, passwords, or financial data in conversation memory |
| Output filtering | Agent responses should not echo back secrets, tokens, or credentials |
| Model data residency | LLMs run locally via Ollama — no family data sent to external cloud AI services |

### 7.5 Maturity Roadmap

OpenClaw security will develop in phases:

| Phase | Security Posture |
|-------|-----------------|
| **Current (design)** | Threat model documented, isolation requirements defined, no running code |
| **Phase 1 (prototype)** | Single admin agent only, no user/child agents, manual review of all actions |
| **Phase 2 (controlled)** | User agents added with read-only app access, admin agent gains more autonomy with audit trail |
| **Phase 3 (production)** | Full lane enforcement, automated scope checking, child lane with parent approval gates |
| **Phase 4 (hardened)** | Formal agent testing (adversarial prompts, scope escape attempts), external security review |

---

## 8. Physical Security

### 8.1 Mac Mini (Primary Host)

| Control | Detail |
|---------|--------|
| Physical location | Inside the home — not in a shared or publicly accessible space |
| FileVault | macOS disk encryption enabled |
| Screen lock | Auto-lock on sleep/screen saver with strong password |
| Firmware password | Consider enabling to prevent boot from external media |
| USB/Thunderbolt | Be aware that physical port access can bypass software security (accept this risk for a home environment) |

### 8.2 Offsite Pi (DR Host)

| Control | Detail |
|---------|--------|
| Physical location | At a relative's house — limited physical security but reasonable for family trust |
| Encrypted data | All backup data is Restic-encrypted — physical access to the Pi/HDD does not expose data without the repository password |
| Tailscale-only access | No other services exposed; the Pi is reachable only via Tailscale |
| Minimal attack surface | Pi runs minimal software — Tailscale, Restic, and the OS. No web UIs, no SSO, no apps |

### 8.3 Network Hardware

| Control | Detail |
|---------|--------|
| Router admin password | Change default credentials; use a strong password |
| Router firmware | Keep router firmware updated |
| Wi-Fi security | WPA3 preferred, WPA2 minimum; strong passphrase |
| Guest network | Isolate guest devices from the homelab VLAN/subnet if the router supports it |

---

## 9. Operational Security Practices

### 9.1 Patch Management

| Control | Detail |
|---------|--------|
| Monthly update window | Review and apply security patches for all container images ([ops-standard.md](ops-standard.md) § 5) |
| Immediate CVE response | Critical vulnerabilities affecting exposed services get patched immediately, outside the monthly cadence |
| macOS updates | Apply macOS security updates promptly; test Docker compatibility before major macOS upgrades |
| Dependency monitoring | Quarterly licence and security review ([dependencies.md](dependencies.md) § 5) |

### 9.2 Monitoring & Alerting

| Control | Detail |
|---------|--------|
| Uptime Kuma | Health checks for every service — alerts on downtime or degraded state |
| Authentik login events | Monitor for failed login attempts, unusual patterns, new device logins |
| Container events | Watch for unexpected container restarts, crashes, or resource exhaustion |
| Backup monitoring | Alert on backup failure or missed schedule ([control-panel.md](control-panel.md) § 6) |
| Disk usage | Warning at 75%, action required at 85% |

### 9.3 Incident Response

This is a family homelab, not a SOC — but having a basic plan prevents panic.

**If you suspect a security incident:**

1. **Contain** — Disconnect the affected service or container. If unsure of scope, disconnect the Mac mini from the network (unplug Ethernet / disable Wi-Fi).
2. **Assess** — Check container logs, Authentik login events, and Docker events. Identify what happened and what was affected.
3. **Recover** — Restore from the last known-good backup if data integrity is in question. Rotate any credentials that may have been exposed.
4. **Review** — Document what happened in `docs/runbook.md`. Identify what control failed and update this security model accordingly.
5. **Notify** — If family members' data was affected, inform them. If financial data (Trader) was potentially exposed, rotate exchange API keys and review trade history.

### 9.4 Security Review Schedule

| Frequency | Activity |
|-----------|----------|
| Monthly | Apply container image security updates |
| Quarterly | Review Authentik login events, group memberships, and unused accounts |
| Quarterly | Verify break-glass credentials work |
| Quarterly | Licence and dependency security review ([dependencies.md](dependencies.md) § 5) |
| Quarterly | Review this security document for accuracy against running platform |
| Annually | Full security posture review — re-evaluate threat model, controls, and accepted risks |

---

## 10. Security Checklist for New Applications

Every new app must pass this security review before production deployment (supplements [app-spec.md](app-spec.md) § 7 and release gates):

- [ ] Runs as non-root user inside container (or exception documented)
- [ ] No `privileged` mode or unnecessary Linux capabilities
- [ ] Secrets in `.env` only — none in image, source, or logs
- [ ] Authentik SSO integrated (OIDC preferred) with correct group mappings
- [ ] Local break-glass admin account documented
- [ ] Health endpoint monitored by Uptime Kuma
- [ ] Network exposure reviewed — only necessary ports published, no `0.0.0.0` binds unless required
- [ ] Backup scope defined and restore test completed
- [ ] Agent scopes defined in `app-contract.yaml` (if OpenClaw applicable)
- [ ] Upstream project security posture reviewed (active maintenance, CVE response history, image signing)

---

## 11. Known Accepted Risks

Every system has trade-offs. These are the risks that are deliberate and documented, not oversights.

| Risk | Why Accepted | Mitigation |
|------|-------------|------------|
| **Docker socket on control panel** | Required for container management — the core value of the control panel | Admin-only access, audit trail, future socket proxy |
| **Tailscale SaaS dependency** | Best UX for family remote access; self-hosted alternative (Headscale) exists but adds operational burden | Headscale documented as fallback ([dependencies.md](dependencies.md)) |
| **Authentik source-available licence** | Best identity solution for the platform's needs; alternatives exist | Pin versions, Keycloak/Authelia as fallback |
| **OpenClaw agent attack surface** | Core to the platform vision; willing to experiment during development | Lane isolation, audit logging, maturity roadmap, human confirmation for destructive actions |
| **Physical access to Mac mini** | It's in a home, not a data centre | FileVault, screen lock, encrypted backups |
| **Physical access to offsite Pi** | At a relative's house — trusted but not controlled | All data Restic-encrypted at rest; Pi has minimal services |
| **macOS as server OS** | Mac mini is the available hardware; Linux migration path documented | Docker abstracts most OS concerns; migration plan in [dependencies.md](dependencies.md) § 3 |
| **Single admin operator** | Only one person manages the platform | Break-glass documented, backup procedures automated, DR procedures written for any competent operator to follow |

---

## Related Documents

| Document | Security Relevance |
|----------|-------------------|
| [ops-standard.md](ops-standard.md) | Backup encryption (§ 1), DR (§ 2), security baseline (§ 3), update procedures (§ 5) |
| [app-spec.md](app-spec.md) | Per-app security requirements (§ 7), release gates |
| [agent-model.md](agent-model.md) | OpenClaw lane isolation, management contract, operational controls |
| [control-panel.md](control-panel.md) | Docker socket risk, admin-only access, destructive action gates |
| [onboarding.md](onboarding.md) | Account creation policy, MFA enforcement, break-glass setup |
| [teardown.md](teardown.md) | Secure data destruction procedures |
| [dependencies.md](dependencies.md) | Supply chain risks, proprietary dependencies, monitoring schedule |
| [access-matrix.md](access-matrix.md) | Who has access to what — the authorisation source of truth |
