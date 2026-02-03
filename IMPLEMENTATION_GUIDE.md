# Crypto Narrative Regimes - Enhanced Feature Implementation Guide

## Overview

This implementation adds five powerful market analysis features to your crypto narrative regime system:

1. **Liquidation Cascade Detection** - Identifies rapid liquidation events and support zones
2. **Funding Rate Anomaly Detection** - Detects extreme funding levels and reversal signals
3. **Multi-Timeframe Regime Confirmation** - Validates regimes across 1h, 4h, 1d, 1w timeframes
4. **Volatility Regime Analysis** - Classifies market into STABLE/HIGH_VOL/EXPLOSIVE states
5. **Cross-Exchange Correlation Engine** - Tracks BTC/ETH/SOL relationships for divergence signals
6. **HTTP Webhook Dispatcher** - Real-time alert system for critical events
7. **Real-Time Dashboard** - Next.js web interface for monitoring all metrics

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Binance.US API                           │
│         (Spot prices, Funding rates, Liquidations)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ingestion_enhanced.py                           │
│    • Fetches spot market data                                │
│    • Queries liquidation & funding data                      │
│    • Upserts to market_metrics table                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌────────────┐ ┌──────────────┐
│ Liquidation  │ │  Funding   │ │  Volatility  │
│  Cascade     │ │  Anomaly   │ │   Regime     │
│ Detection    │ │ Detection  │ │  Analysis    │
└──────────────┘ └────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌────────────┐ ┌──────────────┐
│   Multi-TF   │ │Correlation │ │   Pipeline   │
│   Regimes    │ │  Engine    │ │   Master     │
└──────────────┘ └────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │  Webhook Dispatcher      │
        │  • HTTP POST to webhooks │
        │  • Real-time alerts      │
        └──────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │   Next.js Dashboard      │
        │   • Live metrics         │
        │   • Real-time updates    │
        │   • REST API endpoints   │
        └──────────────────────────┘
```

## File Structure

### Core Feature Modules

- **`features_liquidation_cascade.py`** - Detect cascade events and support zones
  - `detect_cascade_events()` - Compute velocity-based cascades
  - `identify_liquidation_support_zones()` - Find high-liq price levels
  - `compute_liquidation_metrics()` - Main entry point

- **`features_funding_anomaly.py`** - Funding rate analysis
  - `detect_funding_anomalies()` - Z-score based anomalies
  - `detect_reversal_signals()` - Trend reversals
  - `compute_funding_metrics()` - Main entry point

- **`features_volatility_regime.py`** - Volatility classification
  - `compute_volatility_metrics()` - STABLE/HIGH_VOL/EXPLOSIVE
  - `analyze_volatility_persistence()` - Mean reversion potential
  - `compute_volatility_features()` - Main entry point

- **`features_multi_timeframe.py`** - Cross-timeframe regime confirmation
  - `compute_multi_timeframe_regimes()` - 1h/4h/1d/1w analysis
  - Confidence scores based on timeframe agreement

- **`features_correlation_engine.py`** - Asset relationship tracking
  - `compute_pairwise_correlations()` - BTC/ETH/SOL correlations
  - `identify_leading_assets()` - Which asset leads regime shifts
  - Divergence signal detection

### Integration & Delivery

- **`ingestion_enhanced.py`** - Enhanced market data ingestion
  - Fetches liquidation data from Binance.US futures API
  - Queries funding rates
  - Merges with spot price data

- **`pipeline_features_master.py`** - Orchestrates all features
  - Runs all feature modules sequentially
  - Dispatches webhook events for alerts
  - Logs results and metrics

- **`webhook_dispatcher.py`** - HTTP event notification system
  - `WebhookDispatcher` class manages registrations
  - `dispatch_cascade_event()`, `dispatch_funding_anomaly()`, etc.
  - Supports multiple endpoints per event type

### Dashboard (Next.js)

- **`dashboard/app/page.tsx`** - Main dashboard page
- **`dashboard/app/api/features/route.ts`** - Feature data API
- **`dashboard/app/api/cascades/route.ts`** - Cascade events API
- **`dashboard/app/api/volatility/route.ts`** - Volatility API
- **`dashboard/components/`** - React components for UI
  - `header.tsx` - Dashboard header with status
  - `cascade-display.tsx` - Liquidation cascade visualization
  - `regime-display.tsx` - Regime classification display
  - `volatility-display.tsx` - Volatility regime chart

## Setup Instructions

### 1. Install Dependencies

```bash
# Python dependencies
pip install ccxt pandas sqlalchemy requests

# Dashboard dependencies
cd dashboard
npm install
```

### 2. Environment Variables

Create `.env` file or set in your system:

```bash
# Database
export DB_URL="postgresql://user:password@localhost:5432/crypto"

# OpenAI (for narrative system)
export OPENAI_API_KEY="sk-..."

# Webhooks (optional, comma-separated)
export WEBHOOKS_CASCADE="https://webhook.com/cascade1,https://webhook.com/cascade2"
export WEBHOOKS_FUNDING="https://webhook.com/funding"
export WEBHOOKS_VOLATILITY="https://webhook.com/volatility"
export WEBHOOKS_CORRELATION="https://webhook.com/correlation"
export WEBHOOKS_ALL="https://webhook.com/all-events"
```

### 3. Configure Market Ingestion

Update `config.py` if needed:

```python
EXCHANGES = ["binanceus"]  # US market only
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# Thresholds for cascade detection
LIQUIDATION_CFG = {
    "cascade_threshold_usd": 500000,      # Alert threshold
    "velocity_window": 4,                  # hours to measure
    "critical_velocity": 200000,           # USD/hour
}
```

### 4. Start Ingestion Pipeline

```bash
# Enhanced market data ingestion (runs hourly)
python ingestion_enhanced.py

# Feature computation (runs every hour or on-demand)
python pipeline_features_master.py
```

### 5. Start Dashboard

```bash
cd dashboard
npm run dev
# Visit http://localhost:3000
```

## Feature Details

### Liquidation Cascade Detection

**Purpose**: Early warning system for flash crashes and liquidation cascades.

**Algorithm**:
1. Sum liquidations over configurable window (4 hours by default)
2. Calculate velocity: total USD / elapsed hours
3. Flag as CASCADE if velocity > critical threshold AND total > USD threshold
4. Classify as one-sided (LONG/SHORT) or BALANCED

**Events Dispatched**:
```json
{
  "event_type": "LIQUIDATION_CASCADE",
  "symbol": "BTC/USDT",
  "severity": "CRITICAL",
  "data": {
    "total_liquidated_usd": 1500000,
    "velocity_usd_per_hour": 375000,
    "side_bias": "LONG",
    "severity": 1.875
  }
}
```

### Funding Rate Anomaly Detection

**Purpose**: Identify extreme funding levels that often precede reversals.

**Algorithm**:
1. Compute Z-score of funding rate (24h rolling)
2. Detect rapid direction changes
3. Flag anomalies when Z-score > threshold OR change > reversal threshold
4. Track funding volatility

**Events Dispatched**:
```json
{
  "event_type": "FUNDING_ANOMALY",
  "symbol": "BTC/USDT",
  "severity": "WARNING",
  "data": {
    "funding_rate": 0.00125,
    "funding_z_score": 2.3,
    "anomaly_score": 2.8,
    "reasons": ["Z-score anomaly: 2.30σ", "High volatility: 0.00042"]
  }
}
```

### Volatility Regime Classification

**Purpose**: Adapt risk management based on market volatility state.

**Regimes**:
- **STABLE** (vol ≤ 1%): Low volatility, potentially boring, good for mean-reversion strategies
- **HIGH_VOL** (1% < vol ≤ 5%): Elevated volatility, trending potential
- **EXPLOSIVE** (5% < vol ≤ 10%): Extreme volatility, high risk
- **EXTREME** (vol > 10%): Dangerous conditions, reduce size

**Risk Multipliers**:
- STABLE: 0.7x (reduce risk)
- HIGH_VOL: 1.2x (normal risk)
- EXPLOSIVE: 1.8x (increase caution)
- EXTREME: 2.5x (maximum caution)

### Multi-Timeframe Regime Confirmation

**Purpose**: Filter false signals by requiring regime agreement across multiple timeframes.

**Confidence Scoring**:
- Computes regimes at 1h, 4h, 1d, 1w
- Confidence = % of timeframes agreeing
- 100% agreement = highly reliable signal
- < 50% agreement = potentially false signal

**Use Case**: Only take action when primary_regime has >70% confidence.

### Cross-Exchange Correlation Engine

**Purpose**: Identify when normally-correlated assets diverge (pair trading signals).

**Metrics Tracked**:
- BTC/ETH correlation (normally 0.7-0.9)
- ETH/SOL correlation (normally 0.6-0.8)
- BTC/SOL correlation (normally 0.5-0.7)

**Divergence Signals**:
- When correlation drops below -0.5 (negative correlation)
- Typically precedes reversal
- Good for pair trading (long leading asset, short lagging asset)

**Output**:
```json
{
  "event_type": "CORRELATION_BREAK",
  "asset_pair": "BTC/USDT/ETH/USDT",
  "data": {
    "return_correlation": -0.65,
    "divergence_strength": 0.65,
    "signal": "POTENTIAL_PAIR_TRADE"
  }
}
```

## Webhook Integration

### Setting Up Webhooks

1. **Register Endpoints** in environment variables:
   ```bash
   export WEBHOOKS_CASCADE="https://your-server.com/alerts/cascade"
   export WEBHOOKS_ALL="https://your-server.com/alerts/all"
   ```

2. **Receive Events** - Your endpoint receives POST requests:
   ```bash
   POST https://your-server.com/alerts/cascade
   Content-Type: application/json

   {
     "event_type": "LIQUIDATION_CASCADE",
     "timestamp": "2024-02-03T12:34:56.789Z",
     "symbol": "BTC/USDT",
     "severity": "CRITICAL",
     "title": "Liquidation Cascade Detected - BTC/USDT",
     "description": "Large liquidation event with velocity 375000 USD/h",
     "source": "CASCADE",
     "data": { ... }
   }
   ```

3. **Event Types**:
   - `LIQUIDATION_CASCADE` - Large liquidation burst
   - `FUNDING_ANOMALY` - Extreme funding rates
   - `FUNDING_REVERSAL` - Funding trend reversal
   - `VOLATILITY_REGIME_CHANGE` - Volatility state change
   - `CORRELATION_BREAK` - Asset pair divergence
   - `REGIME_CONFIRMED` - Multi-timeframe confirmation

### Example: Discord Integration

```python
import requests
from webhook_dispatcher import WebhookEvent

discord_webhook = "https://discordapp.com/api/webhooks/YOUR_ID/YOUR_TOKEN"

event = WebhookEvent(
    event_type="CASCADE",
    timestamp=datetime.now(timezone.utc),
    symbol="BTC/USDT",
    severity="CRITICAL",
    title="Liquidation Cascade!",
    description="500K liquidated in 1 hour",
    data={"velocity": 500000},
    source="CASCADE"
)

# Discord webhook format
payload = {
    "content": f"🚨 {event.title}\n{event.description}",
    "embeds": [{
        "title": event.title,
        "description": event.description,
        "color": 16711680 if event.severity == "CRITICAL" else 16753920,
    }]
}

requests.post(discord_webhook, json=payload)
```

## Dashboard Usage

### Main Views

1. **Header** - Quick status overview
   - Cascade count (last 24h)
   - Volatility events count
   - Data live status

2. **Cascades Chart** - Time series of liquidation events
   - Stacked bar showing long vs. short liquidations
   - Top 5 events table with severity badges

3. **Volatility Chart** - Bar chart of current volatility levels
   - Color-coded by regime (green=STABLE, orange=HIGH_VOL, red=EXPLOSIVE)
   - Risk multipliers shown

4. **Regimes Panel** - Current regime for each symbol
   - Regime type with emoji indicator
   - Confidence percentage with progress bar
   - Long bias and risk multiplier

### API Endpoints

- `GET /api/features` - Latest market metrics and regimes
- `GET /api/cascades?hours=24` - Liquidation cascade events
- `GET /api/volatility` - Current volatility regimes

## Calibration & Tuning

### Liquidation Thresholds

Adjust in `config.py`:

```python
LIQUIDATION_CFG = {
    "cascade_threshold_usd": 500000,    # Increase if too many false alerts
    "critical_velocity": 200000,        # Decrease for higher sensitivity
}
```

### Funding Rate Sensitivity

```python
FUNDING_CFG = {
    "anomaly_z_threshold": 2.0,         # Higher = fewer alerts
    "reversal_threshold": 0.05,         # Higher = more selective
}
```

### Volatility Regime Boundaries

```python
VOLATILITY_CFG = {
    "stable_threshold": 0.01,           # 1% - adjust based on market
    "high_vol_threshold": 0.05,         # 5%
    "explosive_threshold": 0.10,        # 10%
}
```

## Performance & Monitoring

### Resource Usage

- **Database**: ~500K rows/month for 3 symbols, hourly updates
- **API Calls**: ~100 requests/hour to Binance.US
- **Computation**: <30 seconds for full feature pipeline
- **Memory**: ~200MB Python process, ~400MB Next.js process

### Logging

```bash
# View all logs
tail -f <logfile>

# Monitor ingestion
grep "\[MKT\]" <logfile>

# Monitor features
grep "\[CASCADE\]\|\[FUND\]\|\[VOL\]" <logfile>

# Monitor webhooks
grep "\[WEBHOOK\]" <logfile>
```

## Troubleshooting

### No Liquidation Data

**Issue**: Liquidation cascade module returns empty results

**Solutions**:
1. Verify Binance.US futures API is accessible
2. Check liquidation thresholds aren't too strict
3. Increase `cascade_threshold_usd` in config
4. Look for API rate limiting errors

### Funding Rate Data Missing

**Issue**: Funding module returns None values

**Solutions**:
1. Check if Binance.US futures are available in your region
2. Verify API connectivity
3. Some symbols may not have funding rates available

### Dashboard not connecting to database

**Issue**: API endpoints return 500 error

**Solutions**:
1. Verify `DB_URL` environment variable is set
2. Test database connection: `psql $DB_URL`
3. Check PostgreSQL is running and accessible
4. Ensure `market_metrics` and `regimes` tables exist

## Advanced Customization

### Adding New Symbols

Edit `config.py`:

```python
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ARB/USDT"]  # Add new pair
```

### Custom Regime Logic

Modify `classify_regime()` in `features_multi_timeframe.py`:

```python
def classify_regime_simple(price_z, vol_z, heat=0.5):
    # Add your custom conditions here
    if heat > 0.8 and price_z > 1.5:
        return "SUPER_HOT", 0.95
    # ...
```

### Webhook Event Filtering

Modify `pipeline_features_master.py`:

```python
if event_data.get('severity') == 'CRITICAL':  # Only send critical alerts
    dispatcher.dispatch_cascade_event(...)
```

## Deployment to Production

### Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "pipeline_features_master.py"]
```

### Cloud Deployment

- **Python Backend**: Deploy to AWS Lambda, GCP Cloud Run, or traditional server
- **Dashboard**: Deploy to Vercel (easiest for Next.js)
- **Database**: Use managed PostgreSQL (AWS RDS, Supabase, Neon)

### Monitoring

- Set up uptime monitoring for ingestion process
- Alert on missing data (>2 hour gap)
- Monitor webhook delivery failures
- Track feature computation time

## Support & Debugging

For issues or improvements:

1. Check logs for error messages
2. Verify all environment variables are set
3. Test individual modules in isolation
4. Review data in database directly:
   ```sql
   SELECT * FROM market_metrics WHERE symbol='BTC/USDT' ORDER BY ts DESC LIMIT 10;
   SELECT * FROM regimes WHERE symbol='BTC/USDT' ORDER BY ts DESC LIMIT 10;
   ```

## Future Enhancements

- [ ] Machine learning regime predictor
- [ ] Options implied volatility integration
- [ ] Cross-exchange arbitrage detection
- [ ] Sentiment analysis integration
- [ ] Mobile app for alerts
- [ ] Backtesting engine
- [ ] Strategy simulator based on regimes

---

**Version**: 1.0.0  
**Last Updated**: Feb 2024  
**Compatibility**: Python 3.8+, PostgreSQL 12+, Next.js 16+
