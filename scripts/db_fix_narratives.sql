BEGIN;

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Drop the old unique index that violates hypertable constraints
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND indexname = 'narratives_fp_idx'
    ) THEN
        EXECUTE 'DROP INDEX narratives_fp_idx';
    END IF;
END$$;

-- Create hypertable and compliant unique index
SELECT create_hypertable('narratives', 'ts', if_not_exists => TRUE);
CREATE UNIQUE INDEX IF NOT EXISTS narratives_ts_fp_idx ON narratives (ts, narrative_fingerprint);

-- Create missing tables safely and convert to hypertables
CREATE TABLE IF NOT EXISTS narrative_assets (
    ts             TIMESTAMPTZ NOT NULL,
    narrative_id   TEXT        NOT NULL,
    symbol         TEXT        NOT NULL,
    strength       DOUBLE PRECISION,
    direction_bias DOUBLE PRECISION,
    PRIMARY KEY (ts, narrative_id, symbol)
);
SELECT create_hypertable('narrative_assets', 'ts', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS regimes (
    ts         TIMESTAMPTZ NOT NULL,
    symbol     TEXT        NOT NULL,
    regime     TEXT        NOT NULL,
    long_bias  DOUBLE PRECISION,
    risk_mult  DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    meta_json  JSONB,
    PRIMARY KEY (ts, symbol)
);
SELECT create_hypertable('regimes', 'ts', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS regime_thresholds (
    version        INT PRIMARY KEY,
    cfg            JSONB NOT NULL,
    sharpe_oos     DOUBLE PRECISION,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

COMMIT;
