# Application Ideas

> Candidate apps for the homelab platform | Parent: [DESIGN.md](../DESIGN.md)

Track application ideas here. When an app moves to implementation, create its folder under `~/homelab/apps/<app-name>/` and follow the [app spec](app-spec.md).

---

## How to Add an Idea

Copy this template and fill in what you know. Not every field is required at the idea stage — fill in more as you research.

```markdown
### App Name

| Field | Detail |
|-------|--------|
| **What it replaces** | Cloud service or manual process this replaces |
| **Purpose** | One-line description |
| **Upstream** | Link to project / repo |
| **Docker ready** | Yes / No / Needs custom image |
| **Auth support** | OIDC / SAML / LDAP / Proxy-auth / None |
| **Storage needs** | Light (config only) / Medium (DB) / Heavy (media/files) |
| **Priority** | High / Medium / Low / Someday |
| **Status** | Idea / Researching / Ready to deploy / Deployed |

**Notes:** Any extra context, concerns, or links.
```

---

## Tracked Ideas

### Immich

| Field | Detail |
|-------|--------|
| **What it replaces** | Google Photos, iCloud Photos |
| **Purpose** | Self-hosted photo and video management with mobile app, facial recognition, and sharing |
| **Upstream** | https://github.com/immich-app/immich |
| **Docker ready** | Yes — official Compose stack |
| **Auth support** | OIDC (Authentik compatible) |
| **Storage needs** | Heavy — media library grows continuously; move to external SSD in Phase B |
| **Priority** | High |
| **Status** | Ready to deploy (Phase 3) |

**Notes:** Mobile apps for iOS and Android with automatic backup. Machine learning for face/object recognition can be resource-intensive — may need to tune or disable on Mac mini. Start on internal disk with conservative settings, migrate media to `/Volumes/HomelabData/immich-library` in Phase B.

---

### Copyparty

| Field | Detail |
|-------|--------|
| **What it replaces** | WeTransfer, Google Drive file sharing, manual USB transfers |
| **Purpose** | File sharing server — lets users upload and share large files with each other |
| **Upstream** | https://github.com/9001/copyparty |
| **Docker ready** | Yes — official Docker image available |
| **Auth support** | Built-in user accounts; proxy-auth pattern for Authentik integration |
| **Storage needs** | Medium to Heavy — depends on shared file sizes; external storage recommended for large transfers |
| **Priority** | Medium |
| **Status** | Idea |

**Notes:** Lightweight Python server. Supports resumable uploads, thumbnails, media playback. Useful for sharing videos or large albums with family without cloud services. Investigate Authentik proxy-auth integration since it doesn't have native OIDC. Consider shared vs. per-user upload directories and retention/cleanup policies for temporary shares.

---

### Trader

| Field | Detail |
|-------|--------|
| **What it replaces** | Cloud-hosted or manual crypto trading |
| **Purpose** | Crypto trading application — portfolio management and trade execution |
| **Upstream** | Custom / private |
| **Docker ready** | TBD — may need custom Dockerfile |
| **Auth support** | TBD — will need to conform to platform auth spec |
| **Storage needs** | Medium — trade history database, configuration, API keys |
| **Priority** | Medium |
| **Status** | Idea |

**Notes:** Handles sensitive financial data and exchange API keys — security is critical. Secrets must be in `.env` or Docker secrets, never in source. Consider: does it need outbound internet access to exchanges? If so, this is an exception to the "no direct internet exposure" principle (outbound API calls, not inbound). Needs its own `trader-admin` / `trader-user` groups — likely admin-only initially. Backup scope must include trade database and encrypted API credentials.

---

### Jellyfin

| Field | Detail |
|-------|--------|
| Media streaming service | hosts videos and music|
| **Purpose** | Watching video and streaming music|
| **Upstream** | |
| **Docker ready** | |
| **Auth support** | |
| **Storage needs** | Large |
| **Priority** | Medium |
| **Status** | Idea |

**Notes:** 

<!-- 
### Template — copy this for new ideas

### App Name

| Field | Detail |
|-------|--------|
| **What it replaces** | |
| **Purpose** | |
| **Upstream** | |
| **Docker ready** | |
| **Auth support** | |
| **Storage needs** | |
| **Priority** | |
| **Status** | Idea |

**Notes:** 

-->
