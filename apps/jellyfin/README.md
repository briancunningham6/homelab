# Jellyfin — Media Streaming Server

Stream movies, TV shows, music, and photos to any device. Self-hosted, no tracking, no cloud dependency.

## Quick Reference

| Item | Value |
|------|-------|
| Image | `jellyfin/jellyfin:10.10.6` |
| Container | `jellyfin` |
| Internal port | 8096 |
| Hostname | `jellyfin.home` |
| Health check | `GET /health` → 200 |
| Auth | Authentik SSO via plugin |

## Features

- Movies and TV shows with automatic metadata
- Music streaming with playlist support
- Live TV and DVR (with tuner)
- Multi-user with parental controls
- SyncPlay for synchronized remote viewing
- Mobile, TV, and desktop apps

## Commands

```bash
# Start
docker compose -f apps/jellyfin/compose.yml up -d

# Stop
docker compose -f apps/jellyfin/compose.yml down

# Logs
docker compose -f apps/jellyfin/compose.yml logs -f

# Restart
docker compose -f apps/jellyfin/compose.yml restart

# Update
# 1. Edit compose.yml with new version
# 2. Pull and restart
docker compose -f apps/jellyfin/compose.yml pull
docker compose -f apps/jellyfin/compose.yml up -d
```

## First-Run Setup

### Step 1: Configure Environment

```bash
cp apps/jellyfin/.env.example apps/jellyfin/.env
```

Edit `.env` with your media paths:
```bash
# Your media library locations
MOVIES_PATH=/path/to/movies
TV_PATH=/path/to/tv
MUSIC_PATH=/path/to/music

# User/group IDs (run 'id' to find yours)
PUID=1000
PGID=1000

# Timezone
TZ=America/New_York
```

### Step 2: Start Jellyfin

```bash
docker compose -f apps/jellyfin/compose.yml up -d
```

### Step 3: Complete Initial Setup

1. Open http://jellyfin.home
2. Select language
3. Create admin account (username and password)
4. Add media libraries:
   - Movies → `/media/movies`
   - TV Shows → `/media/tv`
   - Music → `/media/music`
5. Configure metadata language
6. Allow remote connections
7. Finish setup

### Step 4: Setup Authentik SSO (Optional)

**Important:** Create a second admin account before linking SSO to your main admin.

```bash
# Create OIDC provider and groups in Authentik
scripts/setup-authentik-jellyfin
```

Then install the SSO plugin:

1. Dashboard → Plugins → Repositories
2. Add: `https://raw.githubusercontent.com/9p4/jellyfin-plugin-sso/manifest-release/manifest.json`
3. Catalog → SSO-Auth → Install
4. Restart Jellyfin:
   ```bash
   docker compose -f apps/jellyfin/compose.yml restart
   ```

Configure the plugin:

1. Dashboard → Plugins → SSO-Auth → Settings
2. Add provider "Authentik" with values from the setup script
3. Configure role mapping:
   - Role Claim: `groups`
   - Admin Roles: `jellyfin-admin`
   - Roles: `jellyfin-user,jellyfin-admin`

Add login button (optional):

1. Dashboard → General → Branding → Login disclaimer
2. Add:
   ```html
   <form action="/sso/OID/start/Authentik">
     <button type="submit">Login with Authentik</button>
   </form>
   ```

## Media Organization

Jellyfin works best with properly organized media:

### Movies
```
/Movies/
├── Movie Name (2024)/
│   ├── Movie Name (2024).mkv
│   └── Movie Name (2024).srt
└── Another Movie (2023)/
    └── Another Movie (2023).mp4
```

### TV Shows
```
/TV/
├── Show Name/
│   ├── Season 01/
│   │   ├── Show Name - S01E01 - Episode Title.mkv
│   │   └── Show Name - S01E02 - Episode Title.mkv
│   └── Season 02/
│       └── Show Name - S02E01 - Episode Title.mkv
```

### Music
```
/Music/
├── Artist Name/
│   ├── Album Name (2024)/
│   │   ├── 01 - Track One.flac
│   │   └── 02 - Track Two.flac
│   └── Another Album/
```

## Transcoding

### Docker on macOS Limitation

Docker on macOS **cannot** use VideoToolbox (hardware transcoding). This deployment uses software transcoding, which:

- Works for 1-2 concurrent streams
- Uses CPU (may impact other services)
- Can be slow for 4K content

### Recommendations

1. **Use Direct Play** — Configure clients to prefer original quality
2. **Optimize media** — Pre-transcode to widely compatible formats (H.264, AAC)
3. **Native install** — For heavy transcoding, install Jellyfin natively on macOS

### Client Compatibility (Direct Play)

Most modern devices can direct play common formats:

| Client | H.264 | HEVC | Audio |
|--------|-------|------|-------|
| Apple TV 4K | ✓ | ✓ | ✓ |
| Fire TV Stick 4K | ✓ | ✓ | ✓ |
| iOS/Android | ✓ | ✓ | ✓ |
| Smart TVs | ✓ | Varies | ✓ |
| Web browser | ✓ | Chrome only | ✓ |

## User Management

### With Authentik SSO

Users are managed in Authentik:
- Add to `jellyfin-user` group for standard access
- Add to `jellyfin-admin` group for admin access
- First SSO login creates the Jellyfin account

### Without SSO (Local Users)

Manage users in Jellyfin:
- Dashboard → Users → Add User
- Set password and permissions
- Configure parental controls if needed

## Parental Controls

1. Dashboard → Users → Select user
2. Set content access:
   - Maximum parental rating
   - Block specific content
   - Restrict library access
3. Set feature access:
   - Disable live TV
   - Restrict downloads
   - Limit playback quality

## Clients

### Official Apps

| Platform | App |
|----------|-----|
| iOS | Jellyfin (App Store) |
| Android | Jellyfin (Play Store) |
| Apple TV | Jellyfin (App Store) |
| Fire TV | Jellyfin (Amazon Appstore) |
| Android TV | Jellyfin (Play Store) |
| Roku | Jellyfin (Channel Store) |
| Web | Built-in at jellyfin.home |

### Third-Party

- **Kodi** — Jellyfin for Kodi addon
- **Infuse** — iOS/tvOS (paid, excellent player)
- **Finamp** — Music-focused client

## Plugins

Popular plugins available in Jellyfin:

| Plugin | Purpose |
|--------|---------|
| SSO-Auth | Authentik/OIDC integration |
| Intro Skipper | Auto-skip TV intros |
| Open Subtitles | Automatic subtitle downloads |
| Trakt | Sync watch history |
| TMDb Box Sets | Collection management |

Install via Dashboard → Plugins → Catalog.

## Remote Access

### Via Tailscale

Jellyfin works over Tailscale without additional configuration:
- Access via `http://jellyfin.home` from any Tailscale device
- Mobile apps need manual server entry

### Mobile App Setup

1. Open Jellyfin app
2. Add server manually
3. Enter: `http://jellyfin.home` or Tailscale IP
4. Login with your credentials

## Troubleshooting

### Media not appearing

1. Check library path mapping in compose.yml
2. Verify file permissions (PUID/PGID)
3. Trigger manual library scan: Dashboard → Libraries → Scan

### Playback buffering

1. Check network speed between client and server
2. Try lower quality setting in client
3. Check if transcoding is occurring (Dashboard → Playback)
4. For 4K, ensure client supports direct play

### SSO not working

1. Verify Authentik is accessible: http://login.home
2. Check plugin is installed and enabled
3. Verify redirect URI matches in Authentik provider
4. Check Jellyfin logs for errors

### Plugin installation fails

1. Check network connectivity
2. Verify repository URL is correct
3. Try restarting Jellyfin after adding repository

## Backup and Restore

### What to Backup

- `data/config/` — User accounts, settings, plugins, metadata
- Media libraries are NOT included (back up separately)

### Backup Command

```bash
scripts/backup-all --service jellyfin
```

### Restore

```bash
scripts/dr-restore --service jellyfin
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PUID` | `1000` | User ID for file permissions |
| `PGID` | `1000` | Group ID for file permissions |
| `TZ` | `UTC` | Timezone |
| `MOVIES_PATH` | `./media/movies` | Movies library path |
| `TV_PATH` | `./media/tv` | TV shows library path |
| `MUSIC_PATH` | `./media/music` | Music library path |

## Upstream

- Website: https://jellyfin.org
- Documentation: https://jellyfin.org/docs
- GitHub: https://github.com/jellyfin/jellyfin
- SSO Plugin: https://github.com/9p4/jellyfin-plugin-sso
