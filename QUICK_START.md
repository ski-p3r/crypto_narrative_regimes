# Quick Start Guide - Crypto Narrative Regimes Enhanced

Get up and running in 15 minutes.

## 1. Install Dependencies (2 min)

```bash
# Python packages
pip install ccxt pandas sqlalchemy requests python-dotenv

# Dashboard (Node.js required)
cd dashboard
npm install
cd ..
```

## 2. Set Up Environment (2 min)

Create `.env` file in project root:

```bash
DB_URL=postgresql://user:password@localhost:5432/crypto
OPENAI_API_KEY=sk-your-key-here
WEBHOOKS_CASCADE=https://webhook.example.com/cascade
```

Or export as environment variables:
```bash
export DB_URL="postgresql://user:password@localhost:5432/crypto"
export OPENAI_API_KEY="sk-..."
```

## 3. Verify Database (2 min)

Ensure PostgreSQL has the required tables:

```sql
-- If missing, run these commands:
CREATE TABLE IF NOT EXISTS market_metrics (
    ts TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    price DECIMAL,
    ret_1h DECIMAL,
    oi DECIMAL,
    funding DECIMAL,
    long_liq_usd DECIMAL DEFAULT 0,
    short_liq_usd DECIMAL DEFAULT 0,
    volume DECIMAL,
    PRIMARY KEY (ts, symbol, exchange)
);

CREATE TABLE IF NOT EXISTS regimes (
    ts TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    regime VARCHAR(50),
    confidence DECIMAL,
    long_bias DECIMAL,
    risk_mult DECIMAL,
    meta_json JSONB
);

CREATE INDEX ON market_metrics(ts DESC);
CREATE INDEX ON market_metrics(symbol, ts DESC);
CREATE INDEX ON regimes(ts DESC, symbol);
```

## 4. Run Tests (1 min)

```bash
python test_features.py
```

Expected output: `TOTAL: 9/9 tests passed`

## 5. Start the Stack (3 min)

### Terminal 1: Market Ingestion
```bash
python ingestion_enhanced.py
# Runs hourly, fetches Binance.US data
```

### Terminal 2: Feature Computation
```bash
# Run once to test
python pipeline_features_master.py

# Or run periodically (add to cron):
# 0 * * * * cd /path/to/project && python pipeline_features_master.py
```

### Terminal 3: Dashboard
```bash
cd dashboard
npm run dev
# Visit http://localhost:3000
```

## 6. Verify It Works (2 min)

1. **Check Dashboard**: http://localhost:3000
   - Should see header with status
   - Cards showing cascade count, volatility events, data status

2. **Check Database**:
   ```bash
   psql $DB_URL -c "SELECT COUNT(*) as records FROM market_metrics"
   psql $DB_URL -c "SELECT * FROM market_metrics LIMIT 5"
   ```

3. **Check Logs**:
   - Look for success messages in terminal output
   - Should see `[MKT]`, `[CASCADE]`, `[FUND]`, `[VOL]` log entries

## Configuration Adjustments

### For Testing (Be Aggressive)
```python
# In config.py - Lower thresholds to generate alerts
LIQUIDATION_CFG["cascade_threshold_usd"] = 100000  # From 500K
FUNDING_CFG["anomaly_z_threshold"] = 1.5            # From 2.0
VOLATILITY_CFG["stable_threshold"] = 0.001          # From 1%
```

### For Production (Be Conservative)
```python
# Higher thresholds = fewer false alarms
LIQUIDATION_CFG["cascade_threshold_usd"] = 1000000
FUNDING_CFG["anomaly_z_threshold"] = 2.5
VOLATILITY_CFG["stable_threshold"] = 0.02
```

## Key Files

| File | Purpose | Frequency |
|------|---------|-----------|
| `ingestion_enhanced.py` | Fetch market data | Every 1 hour |
| `pipeline_features_master.py` | Compute all features | Every 1 hour |
| `webhook_dispatcher.py` | Send alerts | On-demand |
| `dashboard/` | Web UI | Real-time |

## Features Overview

### 🔥 Liquidation Cascades
```python
from features_liquidation_cascade import compute_liquidation_metrics
result = compute_liquidation_metrics()
# Returns: cascade_events, liquidation_zones
```

### 📊 Funding Anomalies
```python
from features_funding_anomaly import compute_funding_metrics
result = compute_funding_metrics()
# Returns: funding_anomalies, reversal_signals
```

### 📈 Volatility Regimes
```python
from features_volatility_regime import compute_volatility_features
result = compute_volatility_features()
# Returns: STABLE, HIGH_VOL, EXPLOSIVE, EXTREME
```

### ⏱️ Multi-Timeframe
```python
from features_multi_timeframe import compute_multi_timeframe_regimes
result = compute_multi_timeframe_regimes()
# Returns: primary_regimes with confidence scores
```

### 🔗 Correlations
```python
from features_correlation_engine import compute_correlation_metrics
result = compute_correlation_metrics()
# Returns: divergence_events for pair trading
```

## Webhook Integration

### Receive Alerts

Your webhook receives POST requests:

```bash
POST https://your-endpoint.com/alerts
Content-Type: application/json

{
  "event_type": "LIQUIDATION_CASCADE",
  "timestamp": "2024-02-03T12:34:56Z",
  "symbol": "BTC/USDT",
  "severity": "CRITICAL",
  "title": "Liquidation Cascade Detected",
  "data": {
    "total_liquidated_usd": 1500000,
    "velocity_usd_per_hour": 375000,
    "side_bias": "LONG"
  }
}
```

### Test Webhook

```bash
# Simple webhook receiver for testing
python -m http.server 8000 --bind localhost
# In another terminal:
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"event":"test"}'
```

## Dashboard API

Access the data programmatically:

```bash
# Get latest features
curl http://localhost:3000/api/features

# Get cascades (last 24h)
curl http://localhost:3000/api/cascades?hours=24

# Get volatility data
curl http://localhost:3000/api/volatility
```

## Common Commands

```bash
# Restart dashboard
cd dashboard
npm run dev

# Test single feature module
python -c "from features_liquidation_cascade import compute_liquidation_metrics; print(compute_liquidation_metrics())"

# Check database size
psql $DB_URL -c "SELECT pg_size_pretty(pg_total_relation_size('market_metrics'))"

# View latest data
psql $DB_URL -c "SELECT ts, symbol, regime FROM regimes WHERE ts > NOW() - INTERVAL '1 day' ORDER BY ts DESC LIMIT 10"
```

## Troubleshooting

### "DB connection failed"
```bash
# Check connection string
echo $DB_URL
psql $DB_URL -c "SELECT 1"  # Should return 1

# If fails, verify:
# 1. PostgreSQL is running
# 2. Database exists
# 3. User/password correct
```

### "No liquidation data"
```bash
# Check Binance.US API
python -c "import ccxt; ex = ccxt.binanceus(); print(ex.fetch_ticker('BTC/USDT'))"

# If fails, may need lower thresholds or check API rate limits
```

### "Dashboard shows empty"
```bash
# Check if data exists
psql $DB_URL -c "SELECT COUNT(*) FROM market_metrics"

# If 0, run ingestion once:
python ingestion_enhanced.py

# Then run features:
python pipeline_features_master.py

# Wait 30s then refresh dashboard
```

## Next Steps

1. ✅ Run tests: `python test_features.py`
2. ✅ Start services in 3 terminals
3. ✅ Check http://localhost:3000
4. ✅ Set up webhooks for alerts
5. ✅ Configure for your market conditions
6. ✅ Deploy to production (see DEPLOYMENT_CHECKLIST.md)

## Learn More

- **Deep Dive**: Read `IMPLEMENTATION_GUIDE.md`
- **Deployment**: See `DEPLOYMENT_CHECKLIST.md`
- **Code**: Check individual module docstrings
- **Config**: Edit thresholds in `config.py`

## Support

- Check logs for errors: Look for `[ERROR]` or `[CRIT]`
- Run tests: `python test_features.py`
- Verify database: `psql $DB_URL -c "SELECT 1"`
- Check API: `python -c "import ccxt; ccxt.binanceus()"`

---

**Ready to start?** Run the 3 terminals above and navigate to http://localhost:3000! 🚀
