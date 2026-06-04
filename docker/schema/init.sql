-- Zoro Energy — TimescaleDB Schema
-- Automatically applied on first container start via docker-entrypoint-initdb.d/
-- All statements use IF NOT EXISTS / ADD COLUMN IF NOT EXISTS — safe to re-run.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ── Tenants ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id   TEXT        PRIMARY KEY,
    name        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Buildings ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS buildings (
    building_id TEXT        PRIMARY KEY,
    tenant_id   TEXT        NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name        TEXT        NOT NULL,
    address     TEXT,
    timezone    TEXT        NOT NULL DEFAULT 'UTC',
    tags        TEXT[]      DEFAULT '{}',
    metadata    JSONB       DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_buildings_tenant ON buildings (tenant_id);

-- ── Devices ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    device_id   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id TEXT        NOT NULL,
    tenant_id   TEXT        NOT NULL,
    name        TEXT        NOT NULL,
    type        TEXT        NOT NULL DEFAULT 'gateway',
    protocol    TEXT        NOT NULL DEFAULT 'mqtt',
    status      TEXT        NOT NULL DEFAULT 'offline',
    last_seen   TIMESTAMPTZ,
    config      JSONB       DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_devices_building ON devices (tenant_id, building_id);
CREATE INDEX IF NOT EXISTS idx_devices_status   ON devices (status);

-- ── Datapoints registry ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS datapoints (
    dp_id         TEXT        PRIMARY KEY,
    hash          CHAR(8)     NOT NULL UNIQUE,
    building_id   TEXT        NOT NULL,
    tenant_id     TEXT        NOT NULL,
    brick         TEXT,
    pin           TEXT,
    unit          TEXT        DEFAULT '',
    protocol      TEXT        DEFAULT 'influxdb_csv',
    protocol_meta JSONB       DEFAULT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE datapoints ADD COLUMN IF NOT EXISTS protocol_meta JSONB DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_dp_hash     ON datapoints (hash);
CREATE INDEX IF NOT EXISTS idx_dp_building ON datapoints (tenant_id, building_id);
CREATE INDEX IF NOT EXISTS idx_dp_proto_meta ON datapoints USING GIN (protocol_meta);

-- ── Observations hypertable ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS observations (
    ts          TIMESTAMPTZ         NOT NULL,
    dp_hash     CHAR(8)             NOT NULL REFERENCES datapoints(hash),
    value       DOUBLE PRECISION,
    quality     SMALLINT            DEFAULT 0,
    UNIQUE (ts, dp_hash)
);

SELECT create_hypertable(
    'observations', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists       => TRUE
);

CREATE INDEX IF NOT EXISTS idx_obs_dp_hash_ts
    ON observations (dp_hash, ts DESC);

-- ── Compression ───────────────────────────────────────────────────────────────
ALTER TABLE observations SET (
    timescaledb.compress,
    timescaledb.compress_orderby   = 'ts DESC',
    timescaledb.compress_segmentby = 'dp_hash'
);

SELECT add_compression_policy(
    'observations',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ── Convenience views ─────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW latest_observations AS
SELECT DISTINCT ON (o.dp_hash)
    o.ts,
    o.dp_hash,
    d.dp_id,
    d.building_id,
    d.tenant_id,
    d.brick,
    d.pin,
    d.unit,
    o.value,
    o.quality
FROM observations o
JOIN datapoints d ON d.hash = o.dp_hash
ORDER BY o.dp_hash, o.ts DESC;

CREATE OR REPLACE VIEW building_latest AS
SELECT
    d.tenant_id,
    d.building_id,
    d.dp_id,
    d.hash,
    d.brick,
    d.pin,
    d.unit,
    d.protocol,
    d.protocol_meta,
    lo.ts         AS last_seen,
    lo.value      AS last_value,
    lo.quality
FROM datapoints d
LEFT JOIN latest_observations lo ON lo.dp_hash = d.hash
ORDER BY d.building_id, d.pin;
