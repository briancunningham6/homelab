# ADR-001: Docker Compose as the Single Deployment Method

## Status

**Accepted**

## Date

2026-02-17

## Context

The homelab needs a consistent way to deploy and manage all services. Options range from bare-metal installs to full orchestration platforms (Kubernetes, Nomad) to lighter container tools. The platform is operated by one person on a single Mac mini, so operational simplicity is paramount.

## Decision

Use **Docker Compose** as the single deployment method for all self-hosted services. Every service is defined in a `compose.yml` file within its own folder.

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| Bare-metal / Homebrew | Simple for single apps | No isolation, hard to reproduce, messy upgrades | Doesn't scale to many services cleanly |
| Kubernetes (k3s/k8s) | Industry standard, self-healing, declarative | Massive operational overhead for a single node, steep learning curve | Overkill for home use with one operator |
| Podman Compose | Rootless by default, Docker-compatible | Smaller ecosystem, macOS support less mature | Docker has better tooling and community support on macOS |
| Nix / NixOS | Reproducible, declarative | Very steep learning curve, poor Docker integration | Too high a barrier for contributors |

## Consequences

- **Positive:** One tool to learn, well-documented, huge community, works with Dockge for UI management.
- **Positive:** Easy backup — compose files + env + data volumes capture the full state.
- **Trade-off:** No built-in clustering or self-healing. Acceptable for single-node; multi-node scaling (future) will use Compose per node with Tailscale networking, not a cluster orchestrator.
- **Trade-off:** Relies on Docker Desktop or Docker Engine on macOS, which requires monitoring for updates and licensing.

## References

- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Dockge](https://github.com/louislam/dockge) — Compose stack management UI
