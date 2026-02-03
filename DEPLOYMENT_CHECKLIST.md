# Deployment Checklist - Crypto Narrative Regimes Enhanced Features

## Project Summary

Successfully implemented 5 advanced market analysis features + real-time dashboard for your crypto narrative regime system.

## What Was Implemented

### 1. ✅ Enhanced Market Data Ingestion (`ingestion_enhanced.py`)
- Fetches spot prices from Binance.US
- Queries liquidation data from Binance.US futures API
- Retrieves funding rates
- Automatically merges and upserts to PostgreSQL

**Configuration**: 
- Uses `binanceus` exchange for US market only
- Symbols: BTC/USDT, ETH/USDT, SOL/USDT (configurable)
- Runs hourly, can be adjusted

### 2. ✅ Liquidation Cascade Detection (`features_liquidation_cascade.py`)
- **detect_cascade_events()**: Identifies rapid liquidation bursts
  - Measures velocity (USD/hour)
  - Detects one-sided cascades (LONG/SHORT/BALANCED)
  - Configurable thresholds: $500K cascade threshold, $200K/hr velocity critical

- **identify_liquidation_support_zones()**: Maps price levels with high liquidations
  - Useful for identifying support/resistance that will cascade when broken

### 3. ✅ Funding Rate Anomalies (`features_funding_anomaly.py`)
- **detect_funding_anomalies()**: Z-score based anomaly detection
  - Flags extreme funding levels
  - Identifies volatility spikes in funding
  - Anomaly score indicates severity

- **detect_reversal_signals()**: Funding trend reversal detection
  - Extreme funding followed by direction reversal = reversal signal
  - Strong historical predictor of directional moves

### 4. ✅ Volatility Regime Analysis (`features_volatility_regime.py`)
- Classifies market into 4 states: STABLE, HIGH_VOL, EXPLOSIVE, EXTREME
- Computes volatility clustering (high clustering = predictable)
- Analyzes volatility persistence (mean reversion potential)
- Provides risk multipliers (0.7x to 2.5x) per regime

### 5. ✅ Multi-Timeframe Regime Confirmation (`features_multi_timeframe.py`)
- Computes regimes at 1h, 4h, 1d, 1w timeframes
- Calculates confidence score (0-100%) based on timeframe agreement
- Filters false signals when timeframes disagree
- High-confidence signals ideal for trading decisions

### 6. ✅ Cross-Exchange Correlation Engine (`features_correlation_engine.py`)
- Tracks BTC/ETH/SOL pairwise correlations
- Identifies leading assets (which leads regime shifts)
- Detects divergence events (negative correlation = pair trade signals)
- Analyzes correlation persistence and changes

### 7. ✅ HTTP Webhook Dispatcher (`webhook_dispatcher.py`)
- Supports multiple webhook endpoints per event type
- Event types: CASCADE, FUNDING, VOLATILITY, CORRELATION, REGIME
- Timeout handling, retry logic, batch dispatch
- Easily extensible for new event types

**Configuration**:
```bash
export WEBHOOKS_CASCADE="https://webhook1.com,https://webhook2.com"
export WEBHOOKS_ALL="https://catch-all.com"
```

### 8. ✅ Master Pipeline (`pipeline_features_master.py`)
- Orchestrates all feature modules
- Runs sequentially for consistent ordering
- Dispatches webhook events for significant findings
- Logging at each step
- Can run on-demand or periodically

### 9. ✅ Real-Time Dashboard (`dashboard/`)
Complete Next.js web application with:

**Components**:
- Header with live status and event counts
- Liquidation Cascade display with time-series chart
- Volatility Regime cards with risk metrics
- Market Regimes panel with multi-timeframe data

**API Endpoints**:
- `GET /api/features` - Latest market metrics
- `GET /api/cascades?hours=24` - Liquidation events
- `GET /api/volatility` - Volatility regimes

**UI Features**:
- Real-time updates via SWR (stale-while-revalidate)
- Color-coded severity badges
- Responsive design (mobile-friendly)
- Dark theme optimized for 24/7 monitoring

### 10. ✅ Test Suite (`test_features.py`)
Comprehensive test script covering:
- Configuration loading
- All 6 feature modules
- Webhook dispatcher
- Master pipeline
- Enhanced ingestion

Run: `python test_features.py`

## File Structure

```
/
├── config.py                          # Updated with new feature configs
├── ingestion_enhanced.py              # Enhanced market data ingestion
├── ingestion_market_mvp.py            # Original (still functional)
├── features_liquidation_cascade.py    # Liquidation analysis
├── features_funding_anomaly.py        # Funding rate analysis
├── features_volatility_regime.py      # Volatility classification
├── features_multi_timeframe.py        # Multi-timeframe confirmation
├── features_correlation_engine.py     # Asset correlation tracking
├── pipeline_features_master.py        # Master orchestration
├── webhook_dispatcher.py              # HTTP webhook delivery
├── test_features.py                   # Test suite
├── IMPLEMENTATION_GUIDE.md            # Detailed technical guide
├── DEPLOYMENT_CHECKLIST.md            # This file
└── dashboard/                         # Next.js web application
    ├── app/
    │   ├── page.tsx                   # Main dashboard page
    │   ├── layout.tsx                 # Root layout
    │   ├── globals.css                # Styling
    │   └── api/
    │       ├── features/route.ts      # Features API
    │       ├── cascades/route.ts      # Cascades API
    │       └── volatility/route.ts    # Volatility API
    ├── components/
    │   ├── header.tsx                 # Header component
    │   ├── cascade-display.tsx        # Cascade visualization
    │   ├── regime-display.tsx         # Regime display
    │   └── volatility-display.tsx     # Volatility display
    ├── package.json
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── next.config.mjs
    └── postcss.config.js
```

## Pre-Deployment Checklist

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed (for dashboard)
- [ ] PostgreSQL 12+ running
- [ ] `.env` file created with required variables:
  ```bash
  DB_URL=postgresql://user:pass@host:5432/dbname
  OPENAI_API_KEY=sk-...
  WEBHOOKS_CASCADE=https://your-webhook.com (optional)
  ```

### Database Setup
- [ ] PostgreSQL database created
- [ ] `market_metrics` table exists with columns:
  - ts, symbol, exchange, price, ret_1h, oi, funding, long_liq_usd, short_liq_usd, volume
- [ ] `regimes` table exists with columns:
  - ts, symbol, regime, confidence, long_bias, risk_mult, meta_json
- [ ] Tables indexed on (ts, symbol, exchange) for performance

### Python Environment
- [ ] Dependencies installed: `pip install ccxt pandas sqlalchemy requests python-dotenv`
- [ ] All feature modules importable:
  ```bash
  python -c "from features_liquidation_cascade import compute_liquidation_metrics; print('OK')"
  ```
- [ ] Test suite passes: `python test_features.py`

### Dashboard Setup
- [ ] Dependencies installed: `cd dashboard && npm install`
- [ ] Build succeeds: `npm run build`
- [ ] Dev server starts: `npm run dev` → http://localhost:3000

### API Connectivity
- [ ] Can connect to Binance.US: `python -c "import ccxt; ccxt.binanceus()"`
- [ ] PostgreSQL connection works: `psql $DB_URL -c "SELECT 1"`
- [ ] Database tables accessible from Python

## Deployment Steps

### Option 1: Local Development

```bash
# Terminal 1: Start market ingestion (hourly)
python ingestion_enhanced.py

# Terminal 2: Run feature pipeline (hourly or on-demand)
python pipeline_features_master.py

# Terminal 3: Start dashboard
cd dashboard
npm run dev
# Navigate to http://localhost:3000
```

### Option 2: Production Deployment

#### Backend (Python Services)
```bash
# Using systemd service files

# 1. Create ingestion service
sudo systemctl enable crypto-ingest
sudo systemctl start crypto-ingest

# 2. Create features service (cron-based for hourly)
0 * * * * /usr/bin/python3 /path/to/pipeline_features_master.py

# 3. Monitor logs
tail -f /var/log/crypto-ingest.log
```

#### Frontend (Dashboard)
```bash
# Deploy to Vercel (recommended for Next.js)
cd dashboard
npm install -g vercel
vercel

# Or deploy to AWS Amplify, Netlify, etc.
# Set environment variable in deployment:
# NEXT_PUBLIC_DB_URL or DB_URL
```

#### Database
```bash
# Backup before going live
pg_dump -h hostname -U username -d dbname > backup.sql

# Monitor size and performance
psql -c "SELECT pg_size_pretty(pg_total_relation_size('market_metrics'));"
```

## Configuration Tuning

### For "Awful Markets" - Increase Sensitivity

```python
# config.py - Detect more cascades
LIQUIDATION_CFG = {
    "cascade_threshold_usd": 250000,    # Lower from 500K
    "critical_velocity": 100000,        # Lower from 200K
}

# Detect more volatility events
VOLATILITY_CFG = {
    "stable_threshold": 0.005,          # Lower from 1%
    "high_vol_threshold": 0.03,         # Lower from 5%
}

# Detect smaller funding anomalies
FUNDING_CFG = {
    "anomaly_z_threshold": 1.5,         # Lower from 2.0
    "reversal_threshold": 0.02,         # Lower from 5%
}
```

### For Stability - Reduce False Alerts

```python
# Increase thresholds
LIQUIDATION_CFG["cascade_threshold_usd"] = 1000000
FUNDING_CFG["anomaly_z_threshold"] = 2.5

# Only alert on high-confidence signals
# In pipeline_features_master.py:
if regime_data.get("confidence_score", 0) > 0.85:  # Stricter
    dispatcher.dispatch_regime_confirmation(...)
```

## Monitoring & Alerts

### Key Metrics to Track

1. **Ingestion Health**
   - Data freshness (should update hourly)
   - Binance.US API response time
   - Database write latency

2. **Feature Quality**
   - Number of cascades detected (vs. known events)
   - Funding anomaly false positive rate
   - Regime confirmation accuracy

3. **Dashboard Performance**
   - API response time (should be <1s)
   - Frontend load time (should be <3s)
   - Webhook delivery success rate

### Alert Setup

```bash
# Monitor ingestion (alert if no data for 2+ hours)
* * * * * check_latest_data.sh || send_alert "Ingestion down"

# Monitor dashboard uptime
0 * * * * curl -f http://localhost:3000 || send_alert "Dashboard down"

# Monitor database growth
0 0 * * * check_db_size.sh
```

## Performance Benchmarks

| Metric | Expected | Limit |
|--------|----------|-------|
| Ingestion cycle | 2-5 min | <10 min |
| Feature pipeline | 20-30 sec | <60 sec |
| Cascade detection | 5 sec | <15 sec |
| Dashboard API response | 100-500ms | <2s |
| Webhook delivery | 100-200ms | <5s |
| DB query (latest data) | 10-50ms | <100ms |

## Scaling Notes

For more symbols or higher frequency:

1. **More Symbols**: Add to `SYMBOLS` in config.py
   - Each symbol ≈ 1KB/hour of data
   - 100 symbols ≈ 100KB/hour ≈ 2.4MB/day

2. **Faster Updates**: Change ingestion interval in `ingestion_enhanced.py`
   - Hourly to 30-min: 2x data volume
   - Hourly to 15-min: 4x data volume
   - Monitor API rate limits

3. **More Features**: Add new analysis modules
   - Follow pattern in existing feature modules
   - Integrate into `pipeline_features_master.py`
   - Test with `test_features.py`

## Support & Troubleshooting

### Common Issues

**No liquidation data:**
- Check Binance.US futures API availability
- Verify network access to API
- Lower `cascade_threshold_usd` for testing

**Dashboard shows "no data":**
- Verify DB_URL environment variable
- Check PostgreSQL is running: `psql $DB_URL -c "SELECT 1"`
- Run test query: `SELECT COUNT(*) FROM market_metrics`

**Webhooks not firing:**
- Check webhook URLs in environment
- Verify endpoint accepts POST requests
- Check firewall/network access
- Monitor `/var/log/webhook_dispatcher.log`

**High memory usage:**
- Reduce data lookback windows
- Add `LIMIT` to SQL queries
- Consider partitioning by date
- Scale Python process resources

## Next Steps

1. **Verify Setup**: Run `python test_features.py` ✅
2. **Start Ingestion**: Run ingestion process hourly
3. **Configure Webhooks**: Set WEBHOOKS_* env vars
4. **Deploy Dashboard**: Start Next.js server
5. **Monitor**: Check logs and alerts
6. **Optimize**: Tune thresholds based on real data
7. **Integrate**: Connect to trading system via webhooks

## Documentation

- **Technical Details**: See `IMPLEMENTATION_GUIDE.md`
- **Feature API**: See individual module docstrings
- **Dashboard Code**: Well-commented React components
- **Configuration**: See `config.py` with inline documentation

## Support

For issues:
1. Check logs: `grep "[FEATURE]" logfile`
2. Run tests: `python test_features.py`
3. Review data: `psql $DB_URL -c "SELECT * FROM market_metrics LIMIT 5"`
4. Check environment: `env | grep -E "DB_URL|OPENAI|WEBHOOKS"`

---

**Status**: ✅ Implementation Complete  
**Version**: 1.0.0  
**Date**: Feb 2024  
**Ready for Deployment**: Yes
