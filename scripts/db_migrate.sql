BEGIN;

-- Ensure TimescaleDB is available
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1) Market microstructure
CREATE TABLE IF NOT EXISTS market_metrics (
    ts           TIMESTAMPTZ NOT NULL,
    symbol       TEXT        NOT NULL,
    exchange     TEXT        NOT NULL,
    price        DOUBLE PRECISION,
    ret_1h       DOUBLE PRECISION,
    oi           DOUBLE PRECISION,
    funding      DOUBLE PRECISION,
    long_liq_usd DOUBLE PRECISION,
    short_liq_usd DOUBLE PRECISION,
    volume       DOUBLE PRECISION,
    PRIMARY KEY (ts, symbol, exchange)
);
SELECT create_hypertable('market_metrics', 'ts', if_not_exists => TRUE);

-- 2) Narratives (global per snapshot)
CREATE TABLE IF NOT EXISTS narratives (
    ts                    TIMESTAMPTZ NOT NULL,
    narrative_id          TEXT        NOT NULL,
    heat_score            DOUBLE PRECISION,
    sentiment_score       DOUBLE PRECISION,
    novelty_score         DOUBLE PRECISION,
    coherence_score       DOUBLE PRECISION,
    narrative_fingerprint CHAR(32),
    PRIMARY KEY (ts, narrative_id)
);
SELECT create_hypertable('narratives', 'ts', if_not_exists => TRUE);
CREATE UNIQUE INDEX IF NOT EXISTS narratives_ts_fp_idx
    ON narratives (ts, narrative_fingerprint);

-- 3) Narrative–asset links
CREATE TABLE IF NOT EXISTS narrative_assets (
    ts             TIMESTAMPTZ NOT NULL,
    narrative_id   TEXT        NOT NULL,
    symbol         TEXT        NOT NULL,
    strength       DOUBLE PRECISION,
    direction_bias DOUBLE PRECISION,
    PRIMARY KEY (ts, narrative_id, symbol)
);
SELECT create_hypertable('narrative_assets', 'ts', if_not_exists => TRUE);

-- 4) Regimes per symbol
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

-- 5) Regime threshold versions
CREATE TABLE IF NOT EXISTS regime_thresholds (
    version        INT PRIMARY KEY,
    cfg            JSONB NOT NULL,
    sharpe_oos     DOUBLE PRECISION,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

COMMIT;
