# ADR-005: Restic for Encrypted Backups

## Status

**Accepted**

## Date

2026-02-17

## Context

The homelab must implement a 3-2-1 backup strategy with encrypted offsite copies. Backups need to work over Tailscale to a Raspberry Pi at a relative's house, and optionally to Backblaze B2. The solution must handle incremental backups efficiently and encrypt data before it leaves the primary host.

## Decision

Use **Restic** for all backup operations with client-side encryption.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| BorgBackup | Efficient deduplication, encryption, mature | No native cloud backend support (needs rclone wrapper), restore UX less polished | Restic's native multi-backend support (local, SFTP, S3/B2) is a better fit for the hybrid offsite model |
| Duplicati | GUI, many cloud backends, free | Written in Mono/.NET (resource heavy on macOS), reliability issues reported at scale | Reliability concerns and resource overhead |
| rsync + encryption wrapper | Minimal, well-understood | No deduplication, no snapshot management, manual encryption setup | Too manual for scheduled, versioned backups with retention policies |
| Kopia | Modern, performant, built-in UI | Newer/less proven, smaller community | Less battle-tested than Restic; may revisit in the future |

## Consequences

- **Positive:** Client-side encryption means neither the offsite Pi nor B2 ever sees unencrypted data.
- **Positive:** Efficient deduplication and incremental backups minimise transfer over Tailscale.
- **Positive:** Native support for local, SFTP, and S3-compatible backends covers all three targets.
- **Positive:** Snapshot-based model with flexible retention policies matches the backup schedule.
- **Trade-off:** Restic's deduplication is slightly less efficient than Borg's. Acceptable given the multi-backend advantage.
- **Trade-off:** Repository password management is critical — losing it means losing all backups. Mitigated by key escrow process documented in security baseline.

## References

- [Restic documentation](https://restic.readthedocs.io/)
- [Restic Backblaze B2 backend](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#backblaze-b2)
