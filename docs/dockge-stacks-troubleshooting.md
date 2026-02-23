# Dockge Stack Logs/Status Troubleshooting

This note documents a failure mode where Dockge shows stacks but cannot show container status/logs.

## Symptom

In Dockge UI:
- Stacks appear in left sidebar
- But Containers/Logs/Terminal panes are empty or fail

In Dockge container logs:
- `GETSERVICESTATUSLIST ERROR: no configuration file provided: not found`

## Root cause

Dockge was pointed at a flat stacks directory:

- `DOCKGE_STACKS_DIR_HOST=/Users/briancunningham/dev/homelab/.dockge-stacks`

But stack folders were incomplete (missing compose files, or only had `.env`), so Dockge could not run compose operations.

In this environment, Dockge worked reliably when each stack directory contains:
- `compose.yml`
- `compose.yaml` (compatibility copy)
- optional `.env`

## Fix applied

1. Rebuild stack folders under `.dockge-stacks` from canonical repo paths (`apps/*`, `platform/*`).
2. Ensure each stack has `compose.yml`.
3. Create `compose.yaml` copy for each stack.
4. Restart Dockge.

## Recovery script

Run from host:

```bash
python3 - <<'PY'
from pathlib import Path
import shutil

repo=Path('/Users/briancunningham/dev/homelab')
stacks=repo/'.dockge-stacks'
stacks.mkdir(exist_ok=True)

mapping={
  'authentik': repo/'platform/authentik',
  'caddy': repo/'platform/caddy',
  'dockge': repo/'platform/dockge',
  'homepage': repo/'platform/homepage',
  'immich': repo/'apps/immich',
  'jellyfin': repo/'apps/jellyfin',
  'postgres': repo/'platform/postgres',
  'tailscale': repo/'platform/tailscale',
  'uptime-kuma': repo/'platform/uptime-kuma',
  'adguard': repo/'apps/adguard',
  'copyparty': repo/'apps/copyparty',
  'backrest': repo/'apps/backrest',
  'missions': repo/'apps/missions',
}

for name,src in mapping.items():
    if not src.exists():
        continue
    d=stacks/name
    d.mkdir(parents=True, exist_ok=True)

    yml_src=src/'compose.yml'
    if yml_src.exists():
        yml_dst=d/'compose.yml'
        shutil.copy2(yml_src, yml_dst)
        (d/'compose.yaml').write_text(yml_dst.read_text())

    env_src=src/'.env'
    if env_src.exists():
        shutil.copy2(env_src, d/'.env')

print('Dockge stack folders refreshed')
PY

docker restart dockge
```

## Validation

```bash
docker logs --tail=120 dockge
```

You should no longer see repeated:
- `no configuration file provided: not found`

And Dockge should show stack container logs/status normally.
