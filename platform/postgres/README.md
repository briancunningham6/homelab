# Shared PostgreSQL — Platform Database Service

Central PostgreSQL instance for all platform apps. Uses pgvecto-rs (PostgreSQL 16 + vector extensions) to support AI/ML features like Immich's face recognition and semantic search.

## Quick Reference

| Item | Value |
|------|-------|
| Image | `tensorchord/pgvecto-rs:pg16-v0.2.0` |
| Container | `postgres` |
| Internal port | 5432 |
| Network | `postgres-net` |
| Data directory | `./data/` |
| Init scripts | `./init/*.sql` (run on first start) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     postgres-net (internal)                  │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Immich  │    │  Matrix  │    │ Future   │              │
│  │  Server  │    │ Synapse  │    │   Apps   │              │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘              │
│       │               │               │                     │
│       └───────────────┴───────────────┘                     │
│                       │                                      │
│              ┌────────▼────────┐                            │
│              │    postgres     │                            │
│              │  (pgvecto-rs)   │                            │
│              │                 │                            │
│              │  ┌───────────┐  │                            │
│              │  │  immich   │  │  ← per-app databases      │
│              │  │  matrix   │  │                            │
│              │  │  ...      │  │                            │
│              │  └───────────┘  │                            │
│              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

## First-Run Setup

### Step 1: Populate `.env`

```bash
cp platform/postgres/.env.example platform/postgres/.env

# Generate admin password
echo "POSTGRES_ADMIN_PASSWORD=$(openssl rand -hex 32)" >> platform/postgres/.env
```

### Step 2: Configure app passwords in init scripts

Edit `init/01-immich.sql` and replace `CHANGEME_IMMICH_DB_PASSWORD` with the actual password from `apps/immich/.env` (`DB_PASSWORD`).

Or use the setup script (recommended):

```bash
scripts/setup-shared-postgres
```

### Step 3: Start PostgreSQL

```bash
docker compose -f platform/postgres/compose.yml up -d

# Verify it's healthy
docker compose -f platform/postgres/compose.yml ps
```

### Step 4: Migrate apps

See "Migrating an App" below.

## Adding a New App

1. Create an init script in `init/` (e.g., `02-myapp.sql`):

```sql
CREATE USER myapp WITH PASSWORD 'password-from-app-env';
CREATE DATABASE myapp OWNER myapp;
\c myapp
GRANT ALL PRIVILEGES ON DATABASE myapp TO myapp;
```

2. If PostgreSQL is already running (data directory exists), run the script manually:

```bash
docker exec -i postgres psql -U postgres < platform/postgres/init/02-myapp.sql
```

3. Update the app's compose.yml:
   - Remove its `*-db` service
   - Add `postgres-net` to networks
   - Change `DB_HOSTNAME` to `postgres`

## Migrating an App (e.g., Immich)

### Prerequisites

- Shared PostgreSQL running and healthy
- App database and user created (via init script)
- App is stopped

### Migration Steps

```bash
# 1. Stop the app
docker compose -f apps/immich/compose.yml down

# 2. Export data from old database
docker exec immich-db pg_dump -U immich immich > /tmp/immich-backup.sql

# 3. Import into shared PostgreSQL
docker exec -i postgres psql -U immich -d immich < /tmp/immich-backup.sql

# 4. Update apps/immich/compose.yml:
#    - Remove immich-db service
#    - Add postgres-net to immich-server networks
#    - Change DB_HOSTNAME from immich-db to postgres

# 5. Start the app
docker compose -f apps/immich/compose.yml up -d

# 6. Verify
docker compose -f apps/immich/compose.yml logs -f immich-server
```

### Rollback

If migration fails:

```bash
# Restore old compose.yml (git checkout or backup)
# Start with original immich-db
docker compose -f apps/immich/compose.yml up -d
```

## Backup

### Full backup (all databases)

```bash
docker exec postgres pg_dumpall -U postgres > backups/postgres/all-$(date +%Y%m%d).sql
```

### Per-app backup

```bash
docker exec postgres pg_dump -U postgres -d immich > backups/postgres/immich-$(date +%Y%m%d).sql
docker exec postgres pg_dump -U postgres -d matrix > backups/postgres/matrix-$(date +%Y%m%d).sql
```

### Restore

```bash
# Stop all apps using the database
# Then restore:
docker exec -i postgres psql -U postgres < backups/postgres/all-YYYYMMDD.sql
```

## Maintenance

### Connect to psql

```bash
docker exec -it postgres psql -U postgres
```

### List databases

```bash
docker exec postgres psql -U postgres -c "\l"
```

### List users

```bash
docker exec postgres psql -U postgres -c "\du"
```

### Check database sizes

```bash
docker exec postgres psql -U postgres -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database;"
```

## Vector Extensions

The pgvecto-rs image includes:

- `vectors` — pgvecto.rs extension (used by Immich)
- `vector` — pgvector extension (alternative, compatible)

Enable in a database:

```sql
\c myapp
CREATE EXTENSION IF NOT EXISTS vectors;
-- or
CREATE EXTENSION IF NOT EXISTS vector;
```

## Troubleshooting

### "password authentication failed"

- Verify the password in the app's `.env` matches the one in `init/*.sql`
- If PostgreSQL has already initialized, the init scripts don't re-run. Update passwords manually:

```bash
docker exec -it postgres psql -U postgres -c "ALTER USER immich WITH PASSWORD 'correct-password';"
```

### "database does not exist"

- Init scripts only run on first start (empty data directory)
- Create manually:

```bash
docker exec -it postgres psql -U postgres -c "CREATE DATABASE myapp OWNER myapp;"
```

### App can't connect

- Verify the app is on `postgres-net`:

```bash
docker network inspect postgres-net
```

- Verify `DB_HOSTNAME` in app's `.env` is `postgres` (not `immich-db` or `localhost`)
