# Homelab Platform (Experimental)

Self-hosted personal infrastructure focused on user control, repeatable operations, and progressive independence from third-party services.

## Dashboard

![Homelab dashboard](docs/assets/homepage-dashboard.png)

## Current Baseline

- Primary host: Mac mini M4 (macOS + Docker Desktop)
- Secondary host: Raspberry Pi 5 (backup workflows + DMZ blog role)
- Primary operator profile: solo power user
- Priority workloads: photo management, AI-assisted coding applications, media services

## What This Repo Includes

- `platform/`: Core services (Caddy, Authentik, Homepage, Dockge, Tailscale, Uptime Kuma, etc.)
- `apps/`: Application stacks (Immich, Copyparty, Jellyfin, and others)
- `scripts/`: Operational scripts for deploy/update/backup/restore/DR verification
- `docs/`: Design, architecture, runbooks, security, roadmap, and onboarding docs
- `tests/`: Bats script and integration tests

## Getting Started

### 1. Prerequisites

1. macOS host with Docker Desktop installed and running
2. Git installed
3. At least 40 GB free disk space recommended
4. Optional: Tailscale auth key for remote access workflows

### 2. Clone the repo

```bash
git clone https://github.com/briancunningham6/homelab.git
cd homelab
```

### 3. Prepare environment files

- Copy each `.env.example` to `.env` where needed
- Fill required values (passwords, secrets, host/domain settings)

### 4. Validate compose files

```bash
HOMELAB_DIR=$(pwd) ./scripts/validate-compose
```

### 5. Start the platform

```bash
./scripts/platform-up
```

### 6. Verify core services

- Caddy routing
- Authentik login
- Homepage dashboard
- Uptime Kuma health panel

### 7. Deploy your first app

```bash
./scripts/app-up immich
```

### 8. Run day-2 operations

```bash
# Stop an app
./scripts/app-down <app>

# Update an app
./scripts/app-update <app> <new-version>

# Backup an app
./scripts/app-backup <app>

# Restore an app
./scripts/app-restore <app>

# DR readiness check
./scripts/dr-verify
```

## Running Tests

Install Bats (macOS):

```bash
brew install bats-core
```

Run all tests:

```bash
bats -r tests
```

## Open Source Status

Completed foundations:

- `LICENSE` (MIT)
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- `.github` issue/PR/security templates
- CI validation workflow (`.github/workflows/validate.yml`)
- Initial Bats test suite for critical scripts and restore cycle

Roadmap details: `docs/open-source-roadmap.md`

## Documentation Map

- Docs index: `docs/index.md`
- Manifesto: `manifesto.md`
- Bootstrap: `docs/bootstrap.md`
- Operations standard: `docs/ops-standard.md`
- DR runbook: `docs/dr-runbook.md`
- Security model: `docs/security.md`
- Support policy: `SUPPORT.md`
- Compatibility matrix: `docs/compatibility-matrix.md`

## Notes

- Keep secrets out of git; use `.env.example` templates only.
- This project is still experimental; optimize for a working vertical slice first.
