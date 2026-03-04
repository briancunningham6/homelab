# Trader — Crypto Trading Platform

Trader is a self-hosted cryptocurrency trading platform built with Elixir and Phoenix LiveView. It connects to the Binance exchange API for real-time price feeds, order placement, and trade history. It includes a naive algorithmic trading strategy, a backtesting engine, and a live dashboard for monitoring positions and streaming data. Built from source via the `trader-homelab` branch of the trader repo.

## Quick Reference

| Property | Value |
|----------|-------|
| Source | `github.com/briancunningham6/trader` (`trader-homelab` branch) |
| Runtime | Elixir 1.18.3-otp-26 / Erlang 26.2.5 |
| Port (internal) | `4000` |
| Hostname | `trader.home` |
| Health endpoint | `/` |
| Database | `trader_prod` on shared platform postgres |
| Logs | `./data/logs/` |
| Upstream | https://github.com/briancunningham6/trader |

## Prerequisites

- `platform/postgres` stack is running
- `platform/caddy` stack is running (the `trader.home` entry is already in the Caddyfile)
- `platform/postgres/init/02-trader.sql` has been updated with the correct `DATABASE_PASSWORD` (see First-Run Setup)
- `TRADER_SOURCE_PATH` in `.env` points to a local checkout of the `trader-homelab` branch

## First-Run Setup

1. Clone the trader repo and check out the homelab branch:
   ```bash
   cd ~/dev
   git clone https://github.com/briancunningham6/trader
   cd trader && git checkout trader-homelab
   ```

2. Copy and configure the environment file:
   ```bash
   cp .env.example .env
   ```

3. Generate secrets and fill in `.env`:
   ```bash
   # DATABASE_PASSWORD
   openssl rand -base64 32

   # SECRET_KEY_BASE
   docker run --rm hexpm/elixir:1.18.3-erlang-26.2.5-debian-bookworm-20250224-slim mix phx.gen.secret

   # RELEASE_COOKIE
   openssl rand -base64 32
   ```

4. Update `platform/postgres/init/02-trader.sql` — replace `CHANGE_ME` with the same `DATABASE_PASSWORD` you set in `.env`. This only takes effect on a fresh postgres data directory.

   If postgres is already running (i.e., the init script has already run), create the user and database manually:
   ```bash
   docker exec -it postgres psql -U postgres
   ```
   ```sql
   CREATE USER trader WITH PASSWORD '<your-password>';
   CREATE DATABASE trader_prod OWNER trader;
   GRANT ALL PRIVILEGES ON DATABASE trader_prod TO trader;
   \q
   ```

5. Build the Docker image (takes a few minutes — compiles Elixir + assets):
   ```bash
   docker compose build
   ```

6. Start the stack:
   ```bash
   docker compose up -d
   ```

7. Watch logs for migration output and startup confirmation:
   ```bash
   docker compose logs -f trader
   # Expect: "Running database migrations..." then "Running Trader..."
   ```

8. Navigate to `http://trader.home` and log in with the app's built-in credentials.

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f trader

# Update (rebuild from latest trader-homelab branch)
cd ${TRADER_SOURCE_PATH:-~/dev/trader} && git pull
cd ~/dev/homelab/apps/trader
docker compose build
docker compose up -d

# Rollback
cd ${TRADER_SOURCE_PATH:-~/dev/trader} && git checkout <previous-commit>
cd ~/dev/homelab/apps/trader
docker compose build
docker compose up -d
```

## Binance Live Trading

Trader can run in read-only / backtest mode without API keys. To enable live trading:

1. Generate an API key at https://www.binance.com/en/my/settings/api-management
2. In Binance API key settings, whitelist your **Tailscale IP** (not your public IP)
3. Set `BINANCE_API_KEY` and `BINANCE_SECRET_KEY` in `.env`
4. Restart: `docker compose up -d`
5. Keep `AUTO_START_TRADING=false` — enable trading per-symbol through the UI at `http://trader.home/streaming-settings`

## Backup

All trading state is in the shared platform postgres under `trader_prod`.

```bash
# Dump trader database
docker exec postgres pg_dump -U trader trader_prod | gzip > trader-db-$(date +%Y%m%d).sql.gz

# Restore
gunzip -c trader-db-YYYYMMDD.sql.gz | docker exec -i postgres psql -U trader trader_prod
```

**Backup scope:**
- `trader_prod` database — all trades, orders, settings, users (critical)
- `./data/logs/` — optional (debug logs, not critical)

**Schedule:** daily (RPO class: daily)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TRADER_SOURCE_PATH` | Yes | Absolute path to local trader repo checkout |
| `DATABASE_NAME` | No | Database name. Default: `trader_prod` |
| `DATABASE_USER` | No | Database user. Default: `trader` |
| `DATABASE_PASSWORD` | Yes | Must match `platform/postgres/init/02-trader.sql` |
| `DATABASE_POOL_SIZE` | No | Connection pool size. Default: `10` |
| `SECRET_KEY_BASE` | Yes | Phoenix secret — 64+ chars. Generate: `mix phx.gen.secret` |
| `RELEASE_COOKIE` | Yes | Erlang distribution cookie. Generate: `openssl rand -base64 32` |
| `BINANCE_API_KEY` | No | Required for live trading only |
| `BINANCE_SECRET_KEY` | No | Required for live trading only |
| `AUTO_START_TRADING` | No | Start trading on boot. Default: `false` |
| `PHX_CHECK_ORIGINS` | No | Comma-separated extra WebSocket origins (e.g., Tailscale hostname) |

See `.env.example` for the full reference.

## Security Checklist

| Check | Status | Notes |
|-------|--------|-------|
| Non-root container user | ✓ | Runs as `trader` (uid 1001) |
| No privileged mode | ✓ | No `privileged` or extra capabilities |
| Secrets in `.env` only | ✓ | `DATABASE_PASSWORD`, `SECRET_KEY_BASE`, `RELEASE_COOKIE` |
| Authentik SSO | Not applicable | App uses built-in auth; OIDC requires upstream changes |
| Health endpoint monitored | Pending | Add Uptime Kuma monitor for `http://trader.home/` |
| Network exposure reviewed | ✓ | No host ports published; access via Caddy only |
| Backup scope defined | ✓ | `trader_prod` database; daily RPO |
| Binance API IP whitelist | Required | Whitelist Tailscale IP before enabling live trading |

## Caddy Integration

The `trader.home` entry is already in `platform/caddy/Caddyfile`:

```
http://trader.home {
    reverse_proxy trader-app:4000
}
```

Caddy handles Phoenix LiveView WebSocket upgrades automatically. No additional configuration needed.

## Upstream

- [Trader GitHub](https://github.com/briancunningham6/trader)
- [Phoenix LiveView docs](https://hexdocs.pm/phoenix_live_view)
- [Binance API docs](https://binance-docs.github.io/apidocs/spot/en/)
