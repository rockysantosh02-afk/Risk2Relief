-- Risk2Relief PostgreSQL Database Initialization Script
-- Executed on container startup by /docker-entrypoint-initdb.d/

-- Enable cryptographic UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for secure hashing if needed
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant privileges to the default user
GRANT ALL PRIVILEGES ON DATABASE risk2relief_db TO risk2relief_user;

-- Create an internal health verification table
CREATE TABLE IF NOT EXISTS system_heartbeat (
    id SERIAL PRIMARY KEY,
    component VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'healthy',
    last_ping TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO system_heartbeat (component, status) 
VALUES ('database_core', 'initialized')
ON CONFLICT DO NOTHING;
