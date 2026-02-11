# bk (Backup/Experimental)

This folder contains backup or experimental modules that can run alongside the existing pipeline without changing the current scheduler.

## Modules

- `gpt_feed.py`: A parameterized GPT-based narrative feed that writes to the same tables as the main pipeline (`narratives`, `narrative_assets`). It fits into the algorithm by producing heat/coherence signals consumed by `regimes_mvp.py`.

## Usage

```bash
# Activate environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: choose model
export GPT_MODEL=gpt-4o-mini
export OPENAI_API_KEY=sk-REPLACE
export DB_URL=postgresql://user:pass@localhost:5432/crypto

# Run the bk GPT feed
python bk/gpt_feed.py
```

The resulting rows appear in `narratives` and `narrative_assets`. The existing scheduler (`scheduler_mvp.py`) already runs `narrative_stream_openai_v4.py` → `regimes_mvp.py` → features; you can swap or schedule `bk/gpt_feed.py` if desired.

## Enable bk features in the scheduler

To have the scheduler run bk feature wrappers instead of the main pipeline, set:

```bash
export USE_BK_FEATURES=1
python scheduler_mvp.py
```

This will run `bk/pipeline_features_master.py` which calls all bk feature wrappers (`bk/liquidation_cascade.py`, `bk/funding_anomaly.py`, `bk/volatility_regime.py`, `bk/multi_timeframe.py`, `bk/correlation_engine.py`).

## Data sources and storage

- Spot data: fetched via `ccxt` for configured `EXCHANGES`/`SYMBOLS`.
- Liquidations/funding: best-effort queries to Binance.US futures endpoints; no API keys required. If futures are unavailable (US spot-only), liquidation totals remain `0` and funding is `None`.
- Storage: data is upserted into the existing `market_metrics` table. Feature outputs are returned by modules and consumed by the pipeline; regimes are written to the `regimes` table.

If you prefer persisting feature alerts, we can add an optional `feature_alerts` table and a sink in the bk pipeline.
