# Complete System Architecture & Integration Guide

Comprehensive documentation explaining how all components of the crypto narrative regime system work together.

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Integration Points](#integration-points)
5. [How Everything Works Together](#how-everything-works-together)
6. [Extension Guide](#extension-guide)

## System Overview

The crypto narrative regime system is a real-time market analysis platform that:

1. **Ingests** market data from Binance.US
2. **Computes** advanced features (cascades, funding, volatility, correlations)
3. **Classifies** market regimes across multiple timeframes
4. **Generates** real-time alerts via webhooks
5. **Visualizes** metrics on a live dashboard

### What Problems Does It Solve?

- **Liquidation Cascade Detection:** Identify rapid cascade events before they propagate
- **Funding Anomalies:** Catch extreme funding rates that precede reversals
- **Volatility Regimes:** Adapt strategy to market volatility state (stable vs. explosive)
- **Multi-Timeframe Confirmation:** Filter false signals with cross-timeframe validation
- **Asset Correlations:** Detect pairs diverging from normal relationships
- **Real-Time Monitoring:** Live dashboard for market conditions

## Component Architecture

### Layer 1: Data Ingestion

**Files:** `ingestion_enhanced.py`, `config.py`

```
Binance.US API
     │
     ▼
BinanceDataFetcher
├─ fetch_recent_candles(symbol, limit)
├─ fetch_liquidation_data(symbol, hours)
├─ fetch_latest_funding()
└─ fetch_historical_data(symbol, timeframe)
     │
     ▼
Raw Data Store
(DataFrame/Database)
```

**Responsibilities:**
- Connect to Binance.US REST API
- Fetch OHLCV candles (1h, 4h, 1d, 1w)
- Fetch liquidation cascade data
- Fetch funding rate history
- Handle API rate limits & retries
- Cache data locally

**Key Methods:**
```python
# Fetch hourly candles
df = fetcher.fetch_recent_candles('BTC/USDT', limit=100)

# Fetch liquidations in last 24 hours
cascades = fetcher.fetch_liquidation_data('BTC/USDT', hours=24)

# Get current funding rates
funding = fetcher.fetch_latest_funding()
```

### Layer 2: Feature Computation

Five independent feature modules compute market metrics:

#### 2.1 Liquidation Cascade Detector
**File:** `features_liquidation_cascade.py`

```python
LiquidationCascadeDetector
├─ analyze_cascades(data, symbol)
│  ├─ Calculate total liquidation USD
│  ├─ Calculate velocity (USD/hour)
│  ├─ Classify severity (1-5)
│  ├─ Identify support/resistance zones
│  └─ Detect long vs short domination
└─ Output: {
    "total_liquidation_usd": 2500000,
    "velocity_usd_per_hour": 500000,
    "severity": 3,
    "long_liquidations_usd": 1500000,
    "short_liquidations_usd": 1000000,
    "support_levels": [45000, 44500],
    "resistance_levels": [47000, 47500]
   }
```

**Algorithm:**
1. Fetch liquidation events from Binance.US
2. Aggregate by time window (hourly)
3. Calculate velocity = total_usd / hours_elapsed
4. Classify severity: Low (1), Medium (2), High (3), Critical (4), Extreme (5)
5. Detect support/resistance from orderbook
6. Classify as LONG cascade, SHORT cascade, or BALANCED

#### 2.2 Funding Rate Anomaly Detector
**File:** `features_funding_anomaly.py`

```python
FundingAnomalyDetector
├─ detect_anomalies(funding_data, symbol)
│  ├─ Calculate Z-score against historical
│  ├─ Detect extreme levels (>2 std dev)
│  ├─ Calculate persistence score
│  └─ Generate reversal signals
└─ Output: {
    "is_anomaly": True,
    "funding_rate": 0.00125,
    "z_score": 2.8,
    "extreme_level": "HIGH",
    "persistence_score": 0.65,
    "reversal_probability": 0.72
   }
```

**Algorithm:**
1. Fetch funding rate history (last 30 days)
2. Calculate mean and std deviation
3. Z-score = (current - mean) / std_dev
4. If |Z-score| > 2.0: mark as ANOMALY
5. Track funding direction changes (reversals)
6. Calculate persistence = % of hours at extreme level

#### 2.3 Volatility Regime Analyzer
**File:** `features_volatility_regime.py`

```python
VolatilityRegimeAnalyzer
├─ classify_volatility(data)
│  ├─ Calculate 24h historical volatility
│  ├─ Compare vs rolling mean
│  ├─ Classify regime (STABLE/HIGH_VOL/EXPLOSIVE/EXTREME)
│  ├─ Calculate clustering probability
│  └─ Estimate predictability
└─ Output: {
    "vol_regime": "HIGH_VOL",
    "volatility_24h": 0.032,
    "volatility_mean": 0.015,
    "vol_ratio": 2.13,
    "clustering_probability": 0.78,
    "predictability": "MEDIUM",
    "risk_multiplier": 1.8
   }
```

**Regimes:**
- **STABLE:** vol < 1x baseline (0.7x multiplier)
- **HIGH_VOL:** 1-1.5x baseline (1.2x multiplier)
- **EXPLOSIVE:** 1.5-2.5x baseline (1.8x multiplier)
- **EXTREME:** >2.5x baseline (2.5x multiplier)

#### 2.4 Multi-Timeframe Regime Analyzer
**File:** `features_multi_timeframe.py`

```python
MultiTimeframeRegimeAnalyzer
├─ compute_multiframe_regimes(symbol)
│  ├─ Classify regime on 1h candles
│  ├─ Classify regime on 4h candles
│  ├─ Classify regime on 1d candles
│  ├─ Classify regime on 1w candles
│  ├─ Calculate agreement score
│  └─ Generate confidence rating
└─ Output: {
    "1h_regime": "SPOT_IGNITION",
    "4h_regime": "SPOT_IGNITION",
    "1d_regime": "SPOT_COOLING",
    "1w_regime": "SPOT_NEUTRAL",
    "primary_regime": "SPOT_IGNITION",
    "confidence": 0.92,
    "agreement_count": 3,
    "total_timeframes": 4
   }
```

**Regime Definitions (from original system):**
- **SPOT_IGNITION:** Strong uptrend (high heat, positive price Z-score, high volume)
- **SPOT_COOLING:** Downtrend (low heat, negative price Z-score, moderate volume)
- **SPOT_CHOP:** Ranging (moderate heat, low price movement, variable volume)
- **SPOT_NEUTRAL:** No clear direction

#### 2.5 Correlation Engine
**File:** `features_correlation_engine.py`

```python
CorrelationEngine
├─ compute_correlations(symbols, timeframe='1h')
│  ├─ Fetch returns for all symbols
│  ├─ Calculate rolling correlation matrix
│  ├─ Detect correlation breaks
│  ├─ Identify leading/lagging assets
│  └─ Generate pair trade signals
└─ Output: {
    "correlations": {
      "BTC/ETH": 0.87,
      "BTC/SOL": 0.65,
      "ETH/SOL": 0.72
    },
    "correlation_breaks": [
      {"pair": "BTC/ETH", "break_severity": "HIGH", "duration_hours": 8}
    ],
    "leading_asset": "BTC/USDT",
    "lagging_assets": ["ETH/USDT", "SOL/USDT"]
   }
```

**Algorithm:**
1. Fetch hourly returns for all symbols (last 7 days)
2. Calculate correlation matrix
3. Compare vs 30-day normal correlations
4. If correlation drops >50%: mark as BREAK
5. Identify which asset moved first (leader)

### Layer 3: Feature Orchestration

**File:** `pipeline_features_master.py`

Orchestrates all features and combines into single output:

```python
FeaturesPipeline
├─ compute_all_features()
│  ├─ Get market data
│  ├─ Run cascades detector
│  ├─ Run funding detector
│  ├─ Run volatility analyzer
│  ├─ Run multi-timeframe analyzer
│  ├─ Run correlation engine
│  └─ Return combined: {
│       "timestamp": "2024-02-03T15:30:45Z",
│       "cascades": {...},
│       "funding": {...},
│       "volatility": {...},
│       "regimes": {...},
│       "correlations": {...}
│      }
└─ Run on schedule (hourly)
```

**Execution Flow:**
1. Runs hourly (configurable in scheduler)
2. Fetches fresh market data
3. Runs all 5 feature modules in parallel
4. Combines results
5. Stores in database
6. Sends webhook events
7. Logs metrics

### Layer 4: Webhook Dispatcher

**File:** `webhook_dispatcher.py`

Sends events to external systems:

```python
WebhookDispatcher
├─ dispatch_event(event)
│  ├─ Get target webhook URLs
│  ├─ Format JSON payload
│  ├─ POST to each webhook
│  ├─ Retry on failure
│  └─ Log results
├─ dispatch_cascade_event(symbol, data)
├─ dispatch_funding_anomaly(symbol, data)
├─ dispatch_volatility_regime_change(symbol, data)
├─ dispatch_correlation_break(pair, data)
└─ dispatch_regime_confirmation(symbol, data)
```

**Webhook Event Types:**
- `LIQUIDATION_CASCADE` - Large cascade detected
- `FUNDING_ANOMALY` - Extreme funding detected
- `FUNDING_REVERSAL` - Funding trend reversal
- `VOLATILITY_REGIME_CHANGE` - Volatility state change
- `CORRELATION_BREAK` - Asset pair divergence
- `REGIME_CONFIRMED` - Multi-timeframe confirmation

### Layer 5: Dashboard

**Files:** `/dashboard/` directory

Real-time web UI showing metrics:

```
Next.js Dashboard (React)
├─ App Layout (layout.tsx)
├─ Main Page (page.tsx)
│  ├─ Header (components/header.tsx)
│  ├─ Metrics Panel (components/metrics-panel.tsx)
│  ├─ Cascade Display (components/cascade-display.tsx)
│  ├─ Regime Display (components/regime-display.tsx)
│  ├─ Volatility Display (components/volatility-display.tsx)
│  └─ Correlation Display (components/correlation-display.tsx)
├─ RealTime Page (app/realtime/page.tsx)
└─ API Routes
   ├─ /api/features
   ├─ /api/cascades
   ├─ /api/volatility
   └─ /api/correlation
```

## Data Flow

### Complete Request Flow

```
1. Market Event Occurs
   (e.g., large liquidation cascade)
           │
           ▼
2. Ingestion Module Fetches Data (hourly)
   - OHLCV candles
   - Liquidation events
   - Funding rates
           │
           ▼
3. Feature Modules Process
   ├─ Cascade: "Severity 4 cascade detected"
   ├─ Funding: "Funding at extreme high"
   ├─ Volatility: "Regime changed to HIGH_VOL"
   ├─ Regimes: "SPOT_IGNITION confirmed on 1h/4h"
   └─ Correlation: "BTC/ETH correlation dropped"
           │
           ▼
4. Orchestration Pipeline Combines
   {
     "cascades": {...},
     "funding": {...},
     "volatility": {...},
     "regimes": {...},
     "correlations": {...}
   }
           │
           ├──────────────┬─────────────────┬──────────────┐
           ▼              ▼                 ▼              ▼
5. Dispatch to:
   ├─ Database     ├─ Webhooks      ├─ Dashboard    ├─ Logs
   │   (store)     │   (external)    │   (display)    │   (audit)
   │               │                 │                │
   │               ▼                 ▼                ▼
   │           Discord         Real-time UI      /var/log/
   │           Email            WebSocket        app.log
   │           Telegram         Update
   │           Custom HTTP
           │
           ▼
6. User/System Reacts
   - Receive alert notification
   - View dashboard update
   - Execute trade logic
   - Log event for audit
```

## Integration Points

### Integration 1: Binance.US API

**How it's used:**
- Fetch OHLCV data for technical analysis
- Fetch liquidation cascade data
- Fetch funding rates for futures contracts

**Configuration:**
```python
# ingestion_enhanced.py
BINANCE_API_BASE = "https://api.binance.us"
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
```

**Error Handling:**
- Retry with exponential backoff
- Circuit breaker on repeated failures
- Fallback to cached data

### Integration 2: Database (PostgreSQL)

**What's stored:**
- Market events (cascades, funding, regime changes)
- Webhook delivery logs
- Historical metrics for analytics

**Schema:**
```sql
market_events:
  - id (PK)
  - event_type (CASCADE, FUNDING, VOLATILITY, etc.)
  - symbol (BTC/USDT, ETH/USDT, etc.)
  - severity (INFO, WARNING, CRITICAL)
  - data (JSONB with full event details)
  - timestamp

webhook_logs:
  - id (PK)
  - webhook_url
  - event_id (FK)
  - success (boolean)
  - response_code
  - timestamp
```

### Integration 3: Webhook System

**Supports:**
- Discord webhooks
- Telegram bot API
- Custom HTTP endpoints
- Email (via HTTP gateway)
- Slack (via HTTP webhooks)
- Any system with HTTP POST endpoint

**Example: Discord Integration**

```python
# .env
WEBHOOKS_CASCADE=https://discordapp.com/api/webhooks/YOUR_ID/YOUR_TOKEN

# Code automatically formats and sends
event = WebhookEvent(
    event_type="LIQUIDATION_CASCADE",
    title="BTC Cascade Detected",
    description="2.5M USD liquidated in 1 hour",
    severity="CRITICAL",
    ...
)
dispatcher.dispatch_cascade_event("BTC/USDT", event_data)

# Discord receives formatted message with colors, fields, etc.
```

### Integration 4: Dashboard (Next.js Frontend)

**Architecture:**
- React components with real-time updates (SWR)
- REST API endpoints serving data from pipeline
- WebSocket-ready (can be upgraded)
- Responsive design for mobile/desktop
- Dark theme optimized for trading

**Real-Time Update Flow:**
```
Dashboard (Browser)
      │
      ├─ SWR Polling
      │  (10 second intervals)
      │
      ├─ GET /api/features
      │
      ├─ GET /api/cascades
      │
      ├─ GET /api/volatility
      │
      └─ GET /api/correlation
            │
            ▼
      Feature Pipeline
      (Python backend)
            │
            ▼
      Display Updates
      (React re-render)
```

## How Everything Works Together

### Example Scenario: BTC Cascade Event

```
Time: 2024-02-03 15:30:00 UTC

Step 1: Market Event
  - Binance liquidations spike
  - 500+ longs liquidated in 15 minutes
  - Total: $2.5M USD liquidated

Step 2: Ingestion (15:30)
  - ingestion_enhanced.py fetches data
  - Sees 2,400 liquidations in last hour
  - Detects cascade pattern

Step 3: Feature Computation (15:30)
  ├─ Cascade Detector:
  │  └─ Severity 4 (high velocity)
  │     Velocity: 2.4M USD/hour
  │     Support zone: $45,000
  │
  ├─ Funding Detector:
  │  └─ Funding rate at 0.00125 (3 std dev)
  │     Extreme high funding
  │
  ├─ Volatility Analyzer:
  │  └─ Volatility spiked to 6% (4x baseline)
  │     Regime: EXPLOSIVE
  │
  ├─ Multi-Timeframe:
  │  └─ 1h: SPOT_IGNITION (after cascade reversal)
  │     4h: SPOT_COOLING
  │     Confidence: 0.85 (good agreement)
  │
  └─ Correlation Engine:
     └─ BTC/ETH correlation dropped 0.45 → 0.15
        BTC leading the market down

Step 4: Orchestration (15:30)
  Combined output:
  {
    "timestamp": "2024-02-03T15:30:00Z",
    "cascades": {"severity": 4, "velocity": 2400000, ...},
    "funding": {"anomaly": true, "z_score": 3.0, ...},
    "volatility": {"regime": "EXPLOSIVE", "vol_ratio": 4.2, ...},
    "regimes": {"primary": "SPOT_IGNITION", "confidence": 0.85, ...},
    "correlations": {"BTC/ETH": 0.15, "break_detected": true, ...}
  }

Step 5: Webhook Dispatch (15:30)
  ├─ Discord:
  │  "CRITICAL: BTC Liquidation Cascade - 2.5M USD, Velocity 2.4M/h"
  │
  ├─ Custom Webhook:
  │  POST to trading.example.com/events
  │  {full event data}
  │
  └─ Telegram:
  │  "⚠️ BTC Cascade: $2.5M liquidated in high velocity event"

Step 6: Dashboard Update (15:31)
  ├─ User browses dashboard
  ├─ Dashboard polls /api/cascades
  ├─ Shows:
  │  - "Cascade Events: 1" with severity indicator
  │  - "Volatility: EXPLOSIVE" in red
  │  - Chart shows correlation break
  │  - Regime shows "SPOT_IGNITION (85% confidence)"
  └─ User sees real-time market state

Step 7: Data Storage (15:30)
  Database records:
  - Event ID: 42
  - Type: LIQUIDATION_CASCADE
  - Symbol: BTC/USDT
  - Severity: CRITICAL
  - Data: {full event JSON}
  - Timestamp: 2024-02-03 15:30:00
  
  Plus webhook logs:
  - Discord: SUCCESS (200)
  - Custom: SUCCESS (200)
  - Telegram: RETRY (timeout)

Step 8: User Action
  - Gets alert on Discord
  - Checks dashboard for details
  - Sees multi-timeframe confirmation
  - Executes trading decision
  - Logs trade in CRM
```

## Extension Guide

### Adding a New Feature

To add a new market analysis feature:

1. **Create feature module:**
   ```python
   # features_new_indicator.py
   class MyNewIndicator:
       def analyze(self, data, symbol):
           """Analyze market data"""
           return {
               "indicator_value": value,
               "signal": "BUY|SELL|NEUTRAL",
               "confidence": 0.75
           }
   ```

2. **Integrate into pipeline:**
   ```python
   # pipeline_features_master.py
   from features_new_indicator import MyNewIndicator
   
   indicator = MyNewIndicator()
   result = indicator.analyze(market_data, symbol)
   combined_output['new_feature'] = result
   ```

3. **Add webhook event:**
   ```python
   # webhook_dispatcher.py
   def dispatch_new_feature_signal(self, symbol, event_data):
       event = WebhookEvent(
           event_type="NEW_FEATURE_SIGNAL",
           source="NEW_FEATURE",
           ...
       )
       return self.dispatch_event(event)
   ```

4. **Add dashboard display:**
   ```tsx
   // dashboard/components/new-feature-display.tsx
   export function NewFeatureDisplay({ data }) {
       return (
           <div className="card">
               <h2>New Feature</h2>
               <p>Signal: {data.signal}</p>
               <p>Confidence: {data.confidence}</p>
           </div>
       )
   }
   ```

5. **Add API route:**
   ```typescript
   // dashboard/app/api/new-feature/route.ts
   export async function GET() {
       const data = await fetch('http://python-backend/api/new-feature');
       return Response.json(data);
   }
   ```

### Adding New Data Sources

To integrate additional data sources beyond Binance.US:

```python
# ingestion_enhanced.py - Add new exchange
class KrakenDataFetcher:
    def fetch_candles(self, symbol, limit):
        """Fetch from Kraken API"""
        # Implementation
        pass

# config.py - Add configuration
EXCHANGES = ["binanceus", "kraken"]
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY")
```

### Adding New Webhook Providers

```python
# webhook_dispatcher.py
def send_to_slack(self, event):
    """Send to Slack channel"""
    webhook_url = os.getenv("SLACK_WEBHOOK")
    requests.post(webhook_url, json={
        "text": event.title,
        "blocks": [...]
    })

def send_to_database(self, event):
    """Send to time-series database (InfluxDB)"""
    # Send to your InfluxDB instance
    pass
```

## Summary

The system is modular and extensible:

1. **Ingestion Layer** - Gets raw data from exchanges
2. **Feature Layer** - Computes 5 independent market metrics
3. **Orchestration Layer** - Combines features and manages flow
4. **Dispatch Layer** - Routes alerts to webhooks
5. **Dashboard Layer** - Real-time visualization

Each component is independent and can be:
- Updated without affecting others
- Tested in isolation
- Scaled separately
- Extended with new features

The integration points (Binance API, webhooks, database, dashboard) are clearly defined and can be easily modified or extended.
