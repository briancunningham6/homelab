# Task 02: Dockge Stack Management

## Context
Read `CLAUDE.md` for project conventions. Dockge is a Docker Compose stack management UI that lets the admin view, start, stop, and edit Compose stacks from a browser.

## Objective
Create the complete Dockge stack in `platform/dockge/`.

## Output Files

```
platform/dockge/
├── compose.yml
├── .env
├── .env.example
├── data/                   # Created at runtime (gitignored)
└── README.md
```

## Requirements

### compose.yml
- Use `louislam/dockge` with a pinned version tag (check https://github.com/louislam/dockge/releases for latest stable)
- `restart: unless-stopped`
- Expose port 5001 internally (Caddy will proxy it)
- Mount Docker socket: `/var/run/docker.sock:/var/run/docker.sock`
- Mount `./data` to `/app/data` (Dockge's state)
- Mount the homelab stacks directory so Dockge can manage them: `~/homelab:/opt/stacks` (or use the DOCKGE_STACKS_DIR env var)
- Join the `caddy-net` external network
- Container name: `dockge`

### .env.example
```
# Dockge Configuration
DOCKGE_STACKS_DIR=/opt/stacks
```

### README.md
Follow the template from CLAUDE.md. Include:
- What Dockge does (Compose stack management UI)
- Quick reference: image, version, internal port 5001, hostname `dockge.home`
- Commands: start, stop, restart, update with rollback
- Note on Docker socket access: this gives Dockge root-equivalent access to the host (accepted risk, documented in `docs/security.md`)
- How stacks directory mapping works
- Upstream: https://github.com/louislam/dockge

## Constraints
- Docker socket mount is required — document the security implication
- Dockge should manage stacks but NOT be the source of truth — all Compose files are in the git repo
- Do NOT use `privileged: true`

## Acceptance Criteria
- [ ] `docker compose config` passes without errors
- [ ] Docker socket is mounted (read-only if possible, otherwise document)
- [ ] Stacks directory is mapped correctly
- [ ] Joins `caddy-net` external network
- [ ] README includes all required sections
