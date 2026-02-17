# Mac mini — Hardware-Specific Notes

> Node-specific considerations for the primary Mac mini | Parent: [DESIGN.md](../../DESIGN.md)

---

## Resource Sharing

This Mac mini is shared with other uses (notably Minecraft). Platform operations must account for this:

- **Scheduling:** Run heavy jobs (media indexing, backup transfers, AI inference) outside peak gaming hours.
- **Resource limits:** Prefer conservative CPU/memory defaults in Compose configs. Scale up only after usage proves value.
- **Disk awareness:** Internal disk is limited. Monitor usage and migrate to external SSD (Phase B) when thresholds are reached (warning at 75%, action at 85%).

## macOS Considerations

- Docker Desktop (or Colima) is required for container runtime on macOS.
- `launchd` is used for auto-start (not systemd). Plist files live in `~/Library/LaunchAgents/`.
- External storage mounts may not be available immediately at boot — the startup orchestrator must wait for mounts before starting dependent services.
- macOS updates should be scheduled during maintenance windows and tested for Docker compatibility.

## Storage Mount Convention

When external SSD is attached:

```text
/Volumes/HomelabData/
├── immich-library/
├── backups/
└── models/
```

These paths are referenced in Compose files. If the volume is not mounted, storage guardrails prevent apps from starting in write mode (see [ops-standard.md](../ops-standard.md)).

## Portability

The macOS-specific touchpoints in this platform are documented in [dependencies.md](../dependencies.md) §3. The architecture is designed to be portable to Linux — the only macOS-specific items are Docker Desktop/Colima, launchd plists, and storage mount paths. All containerised services run identically on both platforms.
