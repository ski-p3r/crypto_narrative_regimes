# START HERE - Complete Crypto Narrative Regime System

Welcome! This document guides you through the entire system and all its components.

## What You Have

A **complete, production-ready crypto market analysis system** with:
- 5 real-time market analysis features
- Live web dashboard
- Webhook alerting system
- Production deployment ready
- Comprehensive testing
- Full documentation

## Quick Navigation

### First Time? Start Here (15 minutes)

1. **Read this:** `EXECUTIVE_SUMMARY.md` (5 min)
   - What was built
   - How it works
   - Quick start

2. **Setup locally:** Run Quick Start Commands below (5 min)
   - Install dependencies
   - Configure environment
   - Start services

3. **Test it:** Run `python test_features.py --full` (5 min)
   - Verify everything works
   - Check API responses

### Setup in 5 Minutes

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd dashboard && npm install && cd ..

# 2. Create .env file
cat > .env << 'EOF'
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET=your_binance_secret
OPENAI_API_KEY=sk-your-key
DB_URL=sqlite:///local.db
WEBHOOKS_ALL=https://webhook.site/your-id
EOF

# 3. Test all components
python test_features.py --full

# 4. Run the system (3 terminals)
# Terminal 1:
python ingestion_enhanced.py

# Terminal 2:
python pipeline_features_master.py

# Terminal 3:
cd dashboard && npm run dev
# Visit http://localhost:3000
```

## System Overview

```
┌─ Ingestion ──┐
│ (Binance API)│
└──────┬───────┘
       │ (Market data)
       ▼
┌─────────────────────────────────────┐
│    Feature Computation (hourly)     │
├─────────────────────────────────────┤
│ • Liquidation Cascades              │
│ • Funding Anomalies                 │
│ • Volatility Regimes                │
│ • Multi-Timeframe Analysis          │
│ • Correlation Engine                │
└─────────┬───────────────────────────┘
          │ (Events)
    ┌─────┴─────┬──────────┐
    ▼           ▼          ▼
  Webhooks   Database  Dashboard
 (Alerts)   (Logging) (Live UI)
```

## Documentation Map

### For Different Roles

**I'm a Trader/Investor**
- Start: `EXECUTIVE_SUMMARY.md`
- Then: `QUICK_START.md`
- Setup: `WEBHOOK_SETUP.md` (get alerts)
- Monitor: `DASHBOARD_ENHANCEMENTS.md` (live dashboard)

**I'm a Developer**
- Start: `SYSTEM_ARCHITECTURE_AND_INTEGRATION.md`
- Code: `IMPLEMENTATION_GUIDE.md`
- Test: `TESTING_GUIDE.md`
- Extend: Look at feature modules, add your own

**I'm DevOps/Operations**
- Deploy: `PRODUCTION_DEPLOYMENT.md`
- Maintain: `DEPLOYMENT_CHECKLIST.md`
- Monitor: See production deployment section
- Backup: Database backup procedures section

### By Purpose

**Getting Started (Quick)**
- `EXECUTIVE_SUMMARY.md` - What was built
- `QUICK_START.md` - 15-minute setup
- `DASHBOARD_ENHANCEMENTS.md` - Live dashboard features

**Understanding the System (Deep)**
- `SYSTEM_ARCHITECTURE_AND_INTEGRATION.md` - Complete architecture
- `IMPLEMENTATION_GUIDE.md` - Technical details
- Read source code in `/features_*.py` files

**Setting Up Production (Comprehensive)**
- `PRODUCTION_DEPLOYMENT.md` - Complete deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Pre-deployment checks
- `WEBHOOK_SETUP.md` - Webhook configuration

**Testing & Quality Assurance**
- `TESTING_GUIDE.md` - Complete testing procedures
- `test_features.py` - Test script
- See "Unit Test Suite" section in TESTING_GUIDE.md

**Webhook Integration (External Systems)**
- `WEBHOOK_SETUP.md` - Complete webhook guide
- Event types and payloads
- Discord, Telegram, custom HTTP examples

## Core Components

### 1. Data Ingestion
**File:** `ingestion_enhanced.py`

Fetches real-time market data from Binance.US:
- OHLCV candles (1h, 4h, 1d, 1w)
- Liquidation cascade data
- Funding rates

```python
from ingestion_enhanced import BinanceDataFetcher
fetcher = BinanceDataFetcher()
btc_data = fetcher.fetch_recent_candles('BTC/USDT', 100)
```

### 2. Feature Modules (5 Independent Modules)

#### Liquidation Cascade Detector
**File:** `features_liquidation_cascade.py`
- Detects rapid liquidation bursts
- Calculates velocity (USD/hour)
- Classifies severity (1-5)
- Identifies support/resistance zones

#### Funding Rate Anomaly Detector
**File:** `features_funding_anomaly.py`
- Detects extreme funding rates
- Identifies mean-reversion signals
- Calculates persistence scores

#### Volatility Regime Analyzer
**File:** `features_volatility_regime.py`
- Classifies market volatility (STABLE/HIGH_VOL/EXPLOSIVE/EXTREME)
- Calculates clustering probability
- Provides risk multipliers

#### Multi-Timeframe Analyzer
**File:** `features_multi_timeframe.py`
- Analyzes regimes on 1h, 4h, 1d, 1w
- Calculates agreement score
- Provides confidence ratings

#### Correlation Engine
**File:** `features_correlation_engine.py`
- Monitors BTC/ETH/SOL correlations
- Detects divergences
- Identifies leading/lagging assets

### 3. Pipeline Orchestration
**File:** `pipeline_features_master.py`

Runs all features and combines results:
```python
from pipeline_features_master import FeaturesPipeline
pipeline = FeaturesPipeline()
result = pipeline.compute_all_features()
# Returns all features combined
```

### 4. Webhook System
**File:** `webhook_dispatcher.py`

Sends events to external systems:
```python
from webhook_dispatcher import get_dispatcher
dispatcher = get_dispatcher()
dispatcher.dispatch_cascade_event('BTC/USDT', cascade_data)
```

Supports:
- Discord (formatted embeds)
- Telegram (bot messages)
- Custom HTTP endpoints
- Email (via HTTP gateway)
- Any system with HTTP POST

### 5. Dashboard (Real-Time Web UI)
**Location:** `/dashboard`

Next.js React app showing:
- Real-time metrics
- Liquidation cascades
- Volatility regimes
- Multi-timeframe regimes
- Asset correlations
- Live event stream

**Access:** `http://localhost:3000` (default)

## Configuration

All settings in `config.py`:

```python
# Symbols to monitor
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# Liquidation thresholds
LIQUIDATION_CFG = {
    "cascade_threshold_usd": 500000,      # Minimum cascade size
    "critical_velocity": 200000,           # USD/hour threshold
}

# Funding anomaly sensitivity
FUNDING_CFG = {
    "anomaly_z_threshold": 2.0,           # Standard deviations
}

# Volatility classification
VOLATILITY_CFG = {
    "stable_threshold": 0.01,             # 1%
    "high_vol_threshold": 0.05,           # 5%
}

# Timeframes for analysis
TIMEFRAMES = ["1h", "4h", "1d", "1w"]
```

**Lower values = more sensitive (more alerts)**
**Higher values = less sensitive (fewer alerts)**

## Environment Variables

Create `.env` file:

```bash
# Required: Binance API
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret

# Optional: Database
DB_URL=postgresql://user:pass@localhost/crypto_db

# Optional: Webhooks (comma-separated for multiple)
WEBHOOKS_CASCADE=https://webhook.site/url1,https://webhook.site/url2
WEBHOOKS_FUNDING=https://webhook.site/funding
WEBHOOKS_VOLATILITY=https://webhook.site/volatility
WEBHOOKS_CORRELATION=https://webhook.site/correlation
WEBHOOKS_REGIME=https://webhook.site/regime

# Optional: OpenAI (for narrative analysis)
OPENAI_API_KEY=sk-your-key

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/crypto_regimes.log
```

## Running

### Local Development (3 terminals)

```bash
# Terminal 1: Market Data Ingestion
python ingestion_enhanced.py

# Terminal 2: Feature Pipeline
python pipeline_features_master.py

# Terminal 3: Web Dashboard
cd dashboard && npm run dev
```

Then visit: `http://localhost:3000`

### Testing Everything

```bash
# Test all components
python test_features.py --full

# Test specific component
python test_features.py --component cascades

# Test with verbose output
python test_features.py --verbose
```

### Production Deployment

See `PRODUCTION_DEPLOYMENT.md` for:
- AWS EC2 setup
- Heroku deployment
- Docker containerization
- Nginx reverse proxy
- SSL/HTTPS setup
- Process management
- Database backup
- Monitoring setup

## Features Explained

### Feature 1: Liquidation Cascade Detection

**What it does:** Detects rapid liquidation events

**Example:**
```
Event: 2M USD liquidated in 1 hour
Severity: 4/5 (CRITICAL)
Velocity: 2,000,000 USD/hour
Webhook Alert: "CRITICAL: BTC Cascade - 2M USD liquidated"
```

### Feature 2: Funding Rate Anomaly Detection

**What it does:** Catches extreme funding rates

**Example:**
```
Event: BTC funding rate at 0.002 (very high)
Z-Score: 3.2 (extreme outlier)
Signal: "Funding Reversal Alert - High probability of mean reversion"
```

### Feature 3: Volatility Regime Classification

**What it does:** Classifies market volatility state

**Regimes:**
- STABLE (low vol, 0.7x multiplier)
- HIGH_VOL (elevated, 1.2x multiplier)
- EXPLOSIVE (very high, 1.8x multiplier)
- EXTREME (extreme, 2.5x multiplier)

**Example:**
```
Volatility: 5.2% (4.3x baseline)
Regime: EXPLOSIVE
Risk Multiplier: 1.8
Predictability: MEDIUM (clustering detected)
```

### Feature 4: Multi-Timeframe Regime Analysis

**What it does:** Validates regime signals across timeframes

**Example:**
```
1h Regime: SPOT_IGNITION (uptrend)
4h Regime: SPOT_IGNITION (uptrend)
1d Regime: SPOT_COOLING (downtrend)
1w Regime: SPOT_NEUTRAL

Primary Regime: SPOT_IGNITION
Confidence: 85% (3 of 4 timeframes agree)
```

### Feature 5: Correlation Engine

**What it does:** Monitors asset relationships

**Example:**
```
BTC/ETH Normal Correlation: 0.87
BTC/ETH Current Correlation: 0.15
Status: CORRELATION BREAK DETECTED
Signal: BTC leading market downward, ETH decoupled
```

## Testing

### Quick Test
```bash
python test_features.py --full
```

### Webhook Test
```bash
python webhook_test.py
# Tests all event types with mock data
```

### Manual API Test
```bash
curl http://localhost:3000/api/features
curl http://localhost:3000/api/cascades?hours=24
curl http://localhost:3000/api/volatility
```

### Load Testing
```bash
python load_test.py
# Simulates multiple concurrent feature computations
```

See `TESTING_GUIDE.md` for comprehensive testing procedures.

## Webhooks (External Alerts)

### Quick Setup (5 minutes)

1. **Get webhook URL** (pick one)
   - Free: https://webhook.site (generates unique URL instantly)
   - Discord: Create channel webhook in settings
   - Telegram: Use bot API endpoint

2. **Add to .env**
   ```bash
   WEBHOOKS_ALL=https://webhook.site/your-unique-id
   ```

3. **Test**
   ```bash
   python webhook_test.py
   ```

You're done! Webhooks are now sending alerts.

### Event Format

All webhooks receive this JSON:
```json
{
  "event_type": "LIQUIDATION_CASCADE",
  "timestamp": "2024-02-03T15:30:45Z",
  "symbol": "BTC/USDT",
  "severity": "CRITICAL",
  "title": "Event title",
  "description": "Event description",
  "source": "CASCADE",
  "data": {
    "velocity_usd_per_hour": 2000000,
    "support_levels": [45000, 44500],
    ...
  }
}
```

See `WEBHOOK_SETUP.md` for advanced configuration, custom receivers, Discord formatting, etc.

## Dashboard Features

### Main Dashboard (`/`)
- Real-time metric cards
- Liquidation cascade display
- Volatility regime chart
- Multi-timeframe regime analysis
- Asset correlation matrix
- Live event stream
- Configurable update frequency (5s to 1m)

### Real-Time Monitoring (`/realtime`)
- Ultra-fast polling (1-10 seconds)
- Per-symbol live feed
- Pause/resume controls
- Manual refresh button
- Dedicated monitoring interface

### Update Frequencies
- 5 seconds: Ultra-aggressive (API intensive)
- 10 seconds: Default (recommended)
- 30 seconds: Balanced
- 1 minute: Conservative (low resource usage)

See `DASHBOARD_ENHANCEMENTS.md` for full feature documentation.

## Troubleshooting

### Data Not Fetching
1. Check Binance API key is valid
2. Check network connectivity: `ping api.binance.us`
3. Review logs: `tail -f /var/log/crypto_regimes.log`

### Webhooks Not Working
1. Test webhook URL is accessible: `curl https://webhook-url`
2. Verify in .env: `echo $WEBHOOKS_ALL`
3. Check firewall rules
4. Run: `python webhook_test.py` for debugging

### Dashboard Not Loading
1. Verify backend service is running: `ps aux | grep pipeline`
2. Test API: `curl http://localhost:3000/api/features`
3. Check browser console for errors (F12)
4. Review dashboard logs: `npm run dev` output

### Performance Issues
1. Reduce update frequency in dashboard
2. Check system resources: `top`
3. Optimize database queries
4. Scale to larger instance

See `TESTING_GUIDE.md` and `PRODUCTION_DEPLOYMENT.md` for detailed troubleshooting.

## Production Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database backups enabled
- [ ] Webhooks tested
- [ ] SSL/HTTPS configured
- [ ] Monitoring enabled
- [ ] Error alerting configured
- [ ] Backup/recovery tested

See `PRODUCTION_DEPLOYMENT.md` for complete setup.

## File Structure

```
/
├── config.py                         # Configuration & thresholds
├── ingestion_enhanced.py             # Market data fetching
├── features_liquidation_cascade.py   # Cascade detection
├── features_funding_anomaly.py       # Funding analysis
├── features_volatility_regime.py     # Volatility classification
├── features_multi_timeframe.py       # Multi-timeframe analysis
├── features_correlation_engine.py    # Correlation tracking
├── pipeline_features_master.py       # Feature orchestration
├── webhook_dispatcher.py             # Webhook sending
├── test_features.py                  # Test suite
│
├── dashboard/                        # Next.js web UI
│   ├── app/
│   │   ├── page.tsx                 # Main dashboard
│   │   ├── realtime/page.tsx        # Real-time monitor
│   │   ├── api/                     # REST API routes
│   │   └── layout.tsx
│   └── components/                  # React components
│
├── START_HERE.md                    # This file
├── EXECUTIVE_SUMMARY.md             # What was built
├── QUICK_START.md                   # 15-minute setup
├── WEBHOOK_SETUP.md                 # Webhook configuration
├── TESTING_GUIDE.md                 # Testing procedures
├── PRODUCTION_DEPLOYMENT.md         # Production deployment
├── SYSTEM_ARCHITECTURE_AND_INTEGRATION.md  # Architecture
├── IMPLEMENTATION_GUIDE.md          # Technical details
├── DEPLOYMENT_CHECKLIST.md          # Pre-deployment checks
└── DASHBOARD_ENHANCEMENTS.md        # Dashboard features
```

## Key Metrics & Thresholds

### Liquidation Cascades
- **Threshold:** 500K USD minimum
- **Critical Velocity:** 200K USD/hour
- **Severity Scale:** 1-5

### Funding Anomalies
- **Z-Score Threshold:** 2.0 (2 standard deviations)
- **Reversal Detection:** When funding direction changes
- **Persistence:** % of time at extreme level

### Volatility Regimes
- **Stable:** <1% volatility (0.7x multiplier)
- **High Vol:** 1-5% volatility (1.2x multiplier)
- **Explosive:** 5-10% volatility (1.8x multiplier)
- **Extreme:** >10% volatility (2.5x multiplier)

Adjust in `config.py` based on market conditions.

## Support

### Documentation
- Architecture: `SYSTEM_ARCHITECTURE_AND_INTEGRATION.md`
- Setup: `QUICK_START.md`, `WEBHOOK_SETUP.md`
- Production: `PRODUCTION_DEPLOYMENT.md`
- Testing: `TESTING_GUIDE.md`
- Code: Docstrings in all Python files

### Common Issues
1. **No data:** Check Binance API key
2. **No webhooks:** Check environment variables
3. **Dashboard not updating:** Check backend running
4. **High CPU:** Reduce update frequency

### Getting Help
1. Read relevant documentation section
2. Check `TESTING_GUIDE.md` for debugging
3. Run `python test_features.py --full` to verify setup
4. Check logs for detailed error messages

## What's Next?

1. **Read:** `EXECUTIVE_SUMMARY.md` (5 min) - Understand what was built
2. **Setup:** Follow Quick Start above (5 min) - Get it running locally
3. **Test:** Run `python test_features.py --full` (2 min) - Verify everything works
4. **Configure:** Setup webhooks - Get alerts in Discord/Telegram
5. **Monitor:** Open dashboard - Watch live market events
6. **Deploy:** Follow `PRODUCTION_DEPLOYMENT.md` - Deploy to production

## License

Production-ready system suitable for:
- Personal trading
- Small fund operations
- Enterprise deployment
- B2B integration

---

**Ready?** Start with Step 2 above or read `EXECUTIVE_SUMMARY.md` first.
