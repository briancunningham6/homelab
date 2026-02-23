# Platform Auto-Start on macOS (LaunchAgent)

This guide explains how to automatically start the homelab stack after a Mac reboot/login using a `launchd` LaunchAgent.

## Why this is needed

- `scripts/platform-up` starts services in the correct dependency order.
- Docker may restart individual containers, but not always in the desired order.
- A LaunchAgent ensures consistent startup after login.

## Prerequisites

- Repo path exists: `/Users/<username>/dev/homelab`
- Startup script is executable: `scripts/platform-up`
- Docker Desktop is installed and configured to start at login (recommended)

## 1) Create LaunchAgent plist

Create this file:

`~/Library/LaunchAgents/com.homelab.platform-up.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.homelab.platform-up</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/zsh</string>
        <string>-lc</string>
        <string>sleep 30 &amp;&amp; HOMELAB_DIR=/Users/<username>/dev/homelab /Users/<username>/dev/homelab/scripts/platform-up</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/homelab-platform-up.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/homelab-platform-up.log</string>
</dict>
</plist>
```

## 2) Load and enable it

```bash
chmod 644 ~/Library/LaunchAgents/com.homelab.platform-up.plist
launchctl bootout "gui/$(id -u)/com.homelab.platform-up" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.homelab.platform-up.plist
launchctl enable "gui/$(id -u)/com.homelab.platform-up"
launchctl kickstart -k "gui/$(id -u)/com.homelab.platform-up"
```

## 3) Verify

```bash
launchctl print "gui/$(id -u)/com.homelab.platform-up" | head -40
tail -n 50 /tmp/homelab-platform-up.log
```

Expected log pattern:

- `Starting tailscale`
- `Starting caddy`
- `Starting postgres`
- etc., following `scripts/platform-up` order.

## 4) Test reboot behavior

1. Reboot the Mac mini.
2. Log in.
3. Check:

```bash
docker ps
cat /tmp/homelab-platform-up.log
```

## Troubleshooting

### LaunchAgent loaded but services don’t start

- Confirm Docker is running before `platform-up` executes.
- Increase delay from `sleep 30` to `sleep 60` in the plist.

### Wrong repo path

- Update both `HOMELAB_DIR=...` and script path in `ProgramArguments`.

### Service status check

```bash
launchctl print "gui/$(id -u)/com.homelab.platform-up"
```

## Remove/disable auto-start

```bash
launchctl bootout "gui/$(id -u)/com.homelab.platform-up"
rm -f ~/Library/LaunchAgents/com.homelab.platform-up.plist
```
