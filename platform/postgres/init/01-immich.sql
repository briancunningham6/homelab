-- Create Immich database and user
-- This runs automatically on first PostgreSQL start (empty data directory).
--
-- Credentials must match apps/immich/.env:
--   DB_DATABASE_NAME, DB_USERNAME, DB_PASSWORD
--
-- The password here is a placeholder — it will be replaced by the setup script
-- or you can edit this file before first run.

-- Create user (password set via environment or manually)
-- Note: DO NOT put real passwords in this committed file.
-- Use the setup script or replace CHANGEME before first run.
CREATE USER immich WITH PASSWORD 'YKhSnXcNcVYwapaxSOSG8jhdnOWtRL8Ao\+rwDEP0ipY\=';

-- Create database owned by the user
CREATE DATABASE immich OWNER immich;

-- Connect to the immich database and enable extensions
\c immich

-- Enable pgvecto.rs extension (required for Immich ML features)
CREATE EXTENSION IF NOT EXISTS vectors;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE immich TO immich;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO immich;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO immich;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO immich;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO immich;
