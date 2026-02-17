# Task 06: Operational Scripts

## Context
Read `CLAUDE.md` for project conventions. Read `docs/ops-standard.md` for the operational procedures these scripts implement. Read `docs/app-spec.md` for the standard app folder layout. These scripts are the CLI interface for day-to-day platform operations.

## Objective
Create all operational scripts in `scripts/`. These are shell scripts that wrap common Docker Compose and Restic operations for consistency and safety.

## Output Files

```
scripts/
├── app-up
├── app-down
├── app-update
├── app-backup
├── app-restore
├── dr-verify
├── platform-up
├── platform-down
└── README.md
```

## Requirements

### General Script Rules
- All scripts are POSIX-compatible shell (`#!/bin/sh`) or bash (`#!/usr/bin/env bash`)
- All scripts must be executable (`chmod +x`)
- All scripts accept the app/service name as the first argument (where applicable)
- All scripts print clear status messages and exit with appropriate codes
- All scripts validate that the target directory exists before operating
- Include colour-coded output: green for success, yellow for warnings, red for errors
- Reference `~/homelab` as the base directory (use `$HOMELAB_DIR` with a default)

### app-up
```
Usage: app-up <app-name>
```
- Resolves the app path: check `apps/<name>`, then `platform/<name>`, then `ai/<name>`
- Runs `docker compose up -d` in the app directory
- Waits briefly and checks container health
- Prints status summary

### app-down
```
Usage: app-down <app-name>
```
- Resolves the app path (same as app-up)
- Runs `docker compose down` in the app directory
- Confirms containers are stopped

### app-update
```
Usage: app-update <app-name> <new-version>
```
- Implements the 7-step update workflow from `docs/ops-standard.md` § 5:
  1. Show current image tag from compose.yml
  2. Prompt for confirmation before proceeding
  3. Run `app-backup` for the app (pre-update safety net)
  4. Update the image tag in `compose.yml` using `sed`
  5. Pull new image and recreate containers
  6. Check container health
  7. Print result and remind to log in `docs/runbook.md`
- If health check fails, prompt to rollback (revert the sed change and restart with old image)

### app-backup
```
Usage: app-backup <app-name>
```
- Resolves the app path
- Checks if Restic is configured (look for `RESTIC_REPOSITORY` and `RESTIC_PASSWORD` in the app's `.env` or a global backup config)
- If Restic is configured: run `restic backup` on the app's `data/` directory
- If Restic is NOT configured: fall back to a local tar archive in `backups/local/<app-name>-<timestamp>.tar.gz`
- Print snapshot ID or archive path on success

### app-restore
```
Usage: app-restore <app-name> [snapshot-id]
```
- Stop the app first (`app-down`)
- If Restic: list snapshots, restore the specified (or latest) snapshot
- If local tar: list available archives, restore the specified (or latest)
- Prompt before overwriting existing data
- Restart the app (`app-up`)

### dr-verify
```
Usage: dr-verify
```
- Run a platform-wide health check:
  1. Check all compose stacks are running (iterate `platform/`, `apps/`, `ai/`)
  2. For each running service with a health endpoint, curl it
  3. Check disk usage and warn if above thresholds (75% warning, 85% critical)
  4. Check if latest backup exists and its age
  5. Print a summary report
- Exit with non-zero if any critical check fails

### platform-up
```
Usage: platform-up
```
- Start platform services in the correct boot order (from `docs/ops-standard.md` § 4):
  1. Tailscale
  2. Caddy
  3. Authentik (if deployed)
  4. Uptime Kuma
  5. Homepage
  6. Dockge
- Wait for each service to be healthy before starting the next
- Then start all app stacks

### platform-down
```
Usage: platform-down
```
- Stop everything in reverse order:
  1. App stacks
  2. Dockge
  3. Homepage
  4. Uptime Kuma
  5. Authentik
  6. Caddy
  7. Tailscale

### README.md
- List all scripts with usage and description
- Note: these scripts are convenience wrappers — the underlying operations are `docker compose` and `restic` commands
- Document the `HOMELAB_DIR` environment variable (default: `~/homelab`)
- Document the boot sequence and why order matters

## Constraints
- Scripts should work on macOS (use `date` flags compatible with BSD date, use `sed -i ''` for macOS, or detect the OS)
- Do NOT hardcode absolute paths — use `$HOMELAB_DIR` or `$HOME/homelab` as default
- Back up operations should be non-destructive by default (never overwrite without prompting)

## Acceptance Criteria
- [ ] All scripts are executable and have shebangs
- [ ] `app-up`, `app-down` resolve app paths correctly across `platform/`, `apps/`, `ai/`
- [ ] `app-update` implements the 7-step workflow with rollback
- [ ] `app-backup` works with or without Restic
- [ ] `platform-up` follows the documented boot sequence
- [ ] `dr-verify` checks health, disk, and backup freshness
- [ ] README documents all scripts
- [ ] Scripts are macOS-compatible
