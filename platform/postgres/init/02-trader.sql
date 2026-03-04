-- Create trader database and user
-- This runs automatically on first PostgreSQL start (empty data directory).
--
-- IMPORTANT: Replace CHANGE_ME with the same DATABASE_PASSWORD set in
-- apps/trader/.env before starting postgres for the first time.
--
-- If postgres is already running, create the user manually instead:
--   docker exec -it postgres psql -U postgres
--   CREATE USER trader WITH PASSWORD '<password>';
--   CREATE DATABASE trader_prod OWNER trader;
--   GRANT ALL PRIVILEGES ON DATABASE trader_prod TO trader;
--
-- Do NOT commit a real password here.

CREATE USER trader WITH PASSWORD 'CHANGE_ME';

CREATE DATABASE trader_prod OWNER trader;

\c trader_prod

GRANT ALL PRIVILEGES ON DATABASE trader_prod TO trader;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trader;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO trader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO trader;
