# Node Registry

> Hardware nodes in the homelab mesh | Parent: [DESIGN.md](../DESIGN.md)

Last updated: YYYY-MM-DD

## Active Nodes

| Hostname | Role | Hardware | OS | Tailscale IP | Services | Status |
|----------|------|----------|------|-------------|----------|--------|
| homelab-mac-mini | Control | Mac mini | macOS | 100.x.x.x | All platform + apps | Active |
| homelab-pi-dr | DR | Raspberry Pi 4/5 | Raspberry Pi OS | 100.x.x.x | Restic backup target | Planned |

## Node Roles

| Role | Description | Reference |
|------|-------------|-----------|
| Control | Identity, proxy, monitoring, management | DESIGN.md § 8 |
| App | Application hosting | DESIGN.md § 8 |
| AI | LLM inference and model storage | DESIGN.md § 8 |
| DR | Offsite backup and restore staging | DESIGN.md § 8 |

## Adding a New Node

See DESIGN.md § 8 "Adding a new node" for the procedure.
