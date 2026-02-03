# How It All Works - Complete System Integration Guide

Visual walkthrough of the complete crypto narrative regime system.

## System Overview Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     CRYPTO NARRATIVE REGIME SYSTEM                │
└──────────────────────────────────────────────────────────────────┘

                          ┌─────────────────┐
                          │  Binance.US API │
                          │   (Market Data) │
                          └────────┬────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │ Market Data Ingestion    │
                    │ (ingestion_enhanced.py)  │
                    ├──────────────────────────┤
                    │ • OHLCV Candles (1h/4h) │
                    │ • Liquidation Events     │
                    │ • Funding Rates          │
                    └────────┬─────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌─────────────────────────┐  ┌──────────────────────┐
    │ Feature Pipeline        │  │ Dashboard Frontend   │
    │ (Python backend)        │  │ (Next.js React)      │
    │                         │  │                      │
    │ Runs Hourly:            │  │ Real-Time (10s):     │
    │ ┌───────────────────┐   │  │ ┌──────────────────┐ │
    │ │ 1. Cascade Det.   │   │  │ │ Fetches latest   │ │
    │ │ 2. Funding Anomal │   │  │ │ metrics from API │ │
    │ │ 3. Volatility Cls │   │  │ │ Updates displays │ │
    │ │ 4. Multi-Timeframe│   │  │ │ Refreshes charts │ │
    │ │ 5. Correlation   │   │  │ └──────────────────┘ │
    │ └───────────────────┘   │  │                      │
    │         │               │  └──────────────────────┘
    │         ▼               │           ▲
    │    Combine Results      │           │
    │         │               │           │
    └─────────┼───────────────┘           │
              │                           │
        ┌─────┴──────────┬─────────┬──────┴────┐
        ▼                ▼         ▼           ▼
    ┌────────┐    ┌──────────┐ ┌──────┐  ┌────────┐
    │Database│    │ Webhooks │ │ Logs │  │API Routes
    │ Store  │    │ (Discord,│ │      │  │/api/*
    │ Events │    │ Telegram)│ │Audit │  └────────┘
    └────────┘    └──────────┘ └──────┘
        │              │
        │              ▼
        │          ┌──────────────────┐
        │          │ External Systems │
        │          ├──────────────────┤
        │          │ • Discord        │
        │          │ • Telegram       │
        │          │ • Custom HTTP    │
        │          │ • Trading Bot    │
        │          │ • Mobile Alerts  │
        │          └──────────────────┘
        │
        └─────────► Analytics & Reporting
```

---

## Data Flow - Step by Step

### Step 1: Data Ingestion (Every Hour at :00)

```
Time: 2024-02-03 15:00:00 UTC

ACTION: Fetch market data
├─ Call: Binance.US /api/v3/klines?symbol=BTCUSDT&interval=1h
├─ Call: Binance.US /fapi/v1/fundingRate?symbol=BTCUSDT
├─ Call: Liquidation API for last 24 hours
└─ Call: SOL, ETH data (same pattern)

RESULT:
├─ 100 BTC 1-hour candles
├─ 50 BTC 4-hour candles
├─ 10 BTC daily candles
├─ 2 BTC weekly candles
├─ 1,200 liquidation events (last 24h)
├─ Current funding rates: BTC 0.00125%, ETH 0.0085%, SOL 0.001%
└─ Data stored in memory for feature computation

DATA STORED:
{
  "symbol": "BTC/USDT",
  "timestamp": "2024-02-03T15:00:00Z",
  "ohlcv": [...50 candles...],
  "liquidations": [...1200 events...],
  "funding_current": 0.00125,
  "funding_history": [...720 rates...]
}
```

---

### Step 2: Feature Computation (Parallel Processing)

```
Time: 2024-02-03 15:00:05 UTC (5 seconds after ingestion start)

FEATURE 1: Liquidation Cascade Detection
├─ Input: 1,200 liquidation events (last 24h)
├─ Process:
│  ├─ Sum USD liquidated: 2,400,000 USD total
│  ├─ Calculate velocity: 2,400,000 USD ÷ 24 hours = 100,000 USD/hour
│  ├─ Check cascade threshold: 2,400,000 > 500,000 ✓ CASCADE DETECTED
│  ├─ Classify severity: 100K USD/hour = Severity 2/5
│  └─ Identify support: Order book shows support at 45,000
└─ Output:
   {
     "total_liquidation_usd": 2400000,
     "velocity_usd_per_hour": 100000,
     "severity": 2,
     "support_levels": [45000, 44500],
     "cascade_detected": true
   }

FEATURE 2: Funding Anomaly Detection
├─ Input: Funding history (last 30 days)
├─ Process:
│  ├─ Calculate mean: 0.0008%
│  ├─ Calculate std dev: 0.0003%
│  ├─ Current: 0.00125%
│  ├─ Z-score: (0.00125 - 0.0008) / 0.0003 = 1.67
│  └─ Check threshold: 1.67 < 2.0 → NOT ANOMALY
└─ Output:
   {
     "is_anomaly": false,
     "z_score": 1.67,
     "funding_rate": 0.00125,
     "percentile": 85
   }

FEATURE 3: Volatility Regime Classification
├─ Input: 100 BTC 1-hour candles
├─ Process:
│  ├─ Calculate 24h volatility: 2.1%
│  ├─ Calculate baseline (30-day mean): 1.8%
│  ├─ Ratio: 2.1% ÷ 1.8% = 1.17x
│  ├─ Compare to thresholds:
│  │  ├─ < 1.0x = STABLE
│  │  ├─ 1.0-1.5x = HIGH_VOL ✓ (1.17x matches)
│  │  ├─ 1.5-2.5x = EXPLOSIVE
│  │  └─ > 2.5x = EXTREME
│  └─ Clustering score: 78% (high predictability)
└─ Output:
   {
     "vol_regime": "HIGH_VOL",
     "volatility_24h": 0.021,
     "clustering_probability": 0.78,
     "risk_multiplier": 1.2
   }

FEATURE 4: Multi-Timeframe Regime Analysis
├─ Input: 50 1h, 10 4h, 2 1d, 1 1w candles
├─ Process for each timeframe:
│  ├─ 1h Regime Analysis:
│  │  ├─ Heat score: 0.72 (high)
│  │  ├─ Price Z-score: 1.2 (positive direction)
│  │  ├─ Volume Z-score: 1.8 (elevated)
│  │  └─ Classification: SPOT_IGNITION (uptrend)
│  │
│  ├─ 4h Regime Analysis:
│  │  └─ Classification: SPOT_IGNITION (uptrend)
│  │
│  ├─ 1d Regime Analysis:
│  │  └─ Classification: SPOT_COOLING (downtrend)
│  │
│  └─ 1w Regime Analysis:
│     └─ Classification: SPOT_NEUTRAL (no direction)
├─ Calculate agreement: 2 of 4 timeframes = IGNITION
├─ Confidence: 2/4 = 50% agreement
└─ Output:
   {
     "1h_regime": "SPOT_IGNITION",
     "4h_regime": "SPOT_IGNITION",
     "1d_regime": "SPOT_COOLING",
     "1w_regime": "SPOT_NEUTRAL",
     "primary_regime": "SPOT_IGNITION",
     "confidence": 0.50,
     "agreement_count": 2
   }

FEATURE 5: Correlation Engine
├─ Input: Returns for BTC, ETH, SOL (last 7 days)
├─ Process:
│  ├─ Correlation Matrix (current hour):
│  │  ├─ BTC/ETH: 0.82
│  │  ├─ BTC/SOL: 0.68
│  │  └─ ETH/SOL: 0.75
│  │
│  ├─ Normal Correlations (30-day average):
│  │  ├─ BTC/ETH: 0.87
│  │  ├─ BTC/SOL: 0.72
│  │  └─ ETH/SOL: 0.78
│  │
│  ├─ Changes:
│  │  ├─ BTC/ETH down 5% (0.87 → 0.82) = NORMAL
│  │  ├─ BTC/SOL down 5% (0.72 → 0.68) = NORMAL
│  │  └─ ETH/SOL down 3% (0.78 → 0.75) = NORMAL
│  │
│  └─ Leadership:
│     └─ BTC leading (moved first, others following)
└─ Output:
   {
     "current_correlations": {"BTC/ETH": 0.82, "BTC/SOL": 0.68, ...},
     "correlation_breaks": [],
     "leading_asset": "BTC/USDT",
     "lagging_assets": ["ETH/USDT", "SOL/USDT"]
   }
```

---

### Step 3: Feature Combination (Pipeline Orchestration)

```
Time: 2024-02-03 15:00:08 UTC (8 seconds after start)

ACTION: Combine all 5 feature outputs

INPUT: Individual feature results
OUTPUT: Combined Feature Package

{
  "timestamp": "2024-02-03T15:00:00Z",
  "symbol": "BTC/USDT",
  
  "cascades": {
    "total_liquidation_usd": 2400000,
    "velocity_usd_per_hour": 100000,
    "severity": 2,
    "support_levels": [45000, 44500]
  },
  
  "funding": {
    "is_anomaly": false,
    "z_score": 1.67,
    "funding_rate": 0.00125
  },
  
  "volatility": {
    "vol_regime": "HIGH_VOL",
    "volatility_24h": 0.021,
    "clustering_probability": 0.78,
    "risk_multiplier": 1.2
  },
  
  "regimes": {
    "1h_regime": "SPOT_IGNITION",
    "4h_regime": "SPOT_IGNITION",
    "1d_regime": "SPOT_COOLING",
    "1w_regime": "SPOT_NEUTRAL",
    "primary_regime": "SPOT_IGNITION",
    "confidence": 0.50
  },
  
  "correlations": {
    "current": {"BTC/ETH": 0.82, "BTC/SOL": 0.68, "ETH/SOL": 0.75},
    "breaks": [],
    "leading_asset": "BTC/USDT"
  }
}
```

---

### Step 4: Webhook Dispatch

```
Time: 2024-02-03 15:00:09 UTC (9 seconds after start)

ACTION: Determine which webhooks to fire

EVALUATION:
├─ Cascade severity 2: NOT CRITICAL (threshold is 3+) → NO ALERT
├─ Funding anomaly: FALSE → NO ALERT
├─ Volatility: HIGH_VOL (normal) → NO ALERT
├─ Regimes: Confidence 50% (threshold 70%+) → NO ALERT
└─ Correlations: No breaks → NO ALERT

RESULT: No webhooks fired this hour (all conditions below thresholds)
└─ System working normally, no anomalies to report

---

Next Hour (15:01:00 UTC) - Different Scenario:

ACTION: New data shows CRITICAL CASCADE

EVALUATION:
├─ Cascade Event:
│  ├─ Total liquidation: 5,000,000 USD (> 500K threshold) ✓
│  ├─ Velocity: 500,000 USD/hour (> 200K threshold) ✓
│  └─ Severity: 5/5 (CRITICAL)
│
├─ Send to WEBHOOKS_CASCADE:
│  ├─ POST https://discord.webhook.com/...
│  ├─ Headers: Content-Type: application/json
│  └─ Body: {...full event JSON...}
│
├─ Retry Logic:
│  ├─ First attempt: TIMEOUT
│  ├─ Retry 1 (5s later): SUCCESS (200 OK)
│  └─ Logged: "Cascade alert sent to Discord"
│
└─ Also send to WEBHOOKS_ALL:
   ├─ POST https://custom.webhook.com/events
   ├─ Custom endpoint receives same JSON
   └─ Logged: "Event dispatched to custom webhook"

DATABASE STORAGE:
├─ Table: market_events
│  ├─ ID: 12345
│  ├─ event_type: "LIQUIDATION_CASCADE"
│  ├─ symbol: "BTC/USDT"
│  ├─ severity: "CRITICAL"
│  ├─ data: {full event JSON}
│  └─ timestamp: 2024-02-03 15:01:00
│
└─ Table: webhook_logs
   ├─ ID: 98765
   ├─ webhook_url: "https://discord.webhook.com/..."
   ├─ event_id: 12345
   ├─ success: true
   ├─ response_code: 200
   └─ timestamp: 2024-02-03 15:01:05
```

---

### Step 5: Dashboard Real-Time Updates

```
Time: 2024-02-03 15:01:30 UTC (30 seconds after cascade event)

USER BROWSER: Dashboard at http://localhost:3000

ACTION: SWR polling fetches latest data

┌─────────────────────────────────────────────┐
│ GET /api/features                           │
│ Response (200 OK, 45ms):                    │
│ {all combined features}                     │
│                                             │
│ GET /api/cascades?hours=24                  │
│ Response (200 OK, 38ms):                    │
│ {                                           │
│   "cascades": [                             │
│     {cascade from 15:00:00},                │
│     {cascade from 15:01:00} ← NEW ONE       │
│   ]                                         │
│ }                                           │
│                                             │
│ GET /api/volatility                         │
│ Response (200 OK, 42ms):                    │
│ {volatility metrics}                        │
│                                             │
│ GET /api/correlation                        │
│ Response (200 OK, 51ms):                    │
│ {correlation data}                          │
└─────────────────────────────────────────────┘

DASHBOARD UPDATES:
├─ Cascade card shows: "1 event" (was 0)
├─ Cascade detail shows: CRITICAL cascade
│  ├─ 5M USD liquidated
│  ├─ 500K USD/hour velocity
│  └─ Red severity indicator
├─ Event stream shows: "CRITICAL: BTC Cascade"
└─ Alert banner displays: "Critical event detected!"

USER SEES:
┌──────────────────────────────────────────┐
│ Crypto Narrative Regime Dashboard        │
│                                          │
│ CASCADES  │  VOLATILITY  │  CORRELATION │
│    1      │     HIGH     │      0       │
│                                          │
│ Cascade Details:                         │
│ • Event: LIQUIDATION CASCADE             │
│ • Severity: CRITICAL (5/5)               │
│ • Volume: 5,000,000 USD                  │
│ • Velocity: 500,000 USD/hour             │
│ • Support Zone: 45,000                   │
│                                          │
│ Recent Events:                           │
│ > CRITICAL: BTC Cascade - 5M USD         │
│   (15:01:00)                             │
└──────────────────────────────────────────┘
```

---

### Step 6: External System Reaction

```
Time: 2024-02-03 15:01:10 UTC (10 seconds after dispatch)

DISCORD RECEIVES:
┌─────────────────────────────────────────┐
│ #market-alerts                          │
│                                         │
│ 🚨 CRITICAL: BTC Liquidation Cascade    │
│                                         │
│ Symbol: BTC/USDT                        │
│ Severity: CRITICAL                      │
│ Total Liquidated: 5,000,000 USD         │
│ Velocity: 500,000 USD/hour              │
│ Duration: 10 hours                      │
│ Support Zone: 44,500 - 45,000           │
│ Timestamp: 2024-02-03 15:01:00 UTC      │
│                                         │
│ Action: Review market and adjust        │
│ positions if necessary.                 │
└─────────────────────────────────────────┘

TELEGRAM BOT SENDS:
┌─────────────────────────────────────────┐
│ ⚠️ BTC Liquidation Alert                │
│                                         │
│ 🔴 CRITICAL CASCADE                     │
│ Amount: 5.0M USD liquidated             │
│ Velocity: 500K USD/h                    │
│ Support: 45K                            │
│ Time: 2024-02-03 15:01:00               │
│                                         │
│ [View on Dashboard] [More Info]         │
└─────────────────────────────────────────┘

CUSTOM HTTP WEBHOOK RECEIVES:
POST /events
{
  "event_type": "LIQUIDATION_CASCADE",
  "timestamp": "2024-02-03T15:01:00Z",
  "symbol": "BTC/USDT",
  "severity": "CRITICAL",
  "title": "Liquidation Cascade Detected",
  "description": "Large liquidation event: 5M USD at 500K USD/h velocity",
  "source": "CASCADE",
  "data": {
    "total_liquidation_usd": 5000000,
    "velocity_usd_per_hour": 500000,
    "severity": 5,
    ...more data...
  }
}

RESPONSE: 200 OK
{"status": "received", "event_id": 12345}
```

---

## Complete Timeline Example

```
15:00:00 ─ Data Ingestion Starts
15:00:01 │  ├─ Fetch Binance API
15:00:02 │  ├─ Fetch liquidation data
15:00:03 │  └─ Fetch funding rates
         │
15:00:05 ─ Feature Computation Starts
15:00:06 │  ├─ Run cascade detector
15:00:06 │  ├─ Run funding detector
15:00:06 │  ├─ Run volatility analyzer (parallel)
15:00:06 │  ├─ Run multi-timeframe analyzer
15:00:07 │  └─ Run correlation engine
         │
15:00:08 ─ Pipeline Combination
15:00:08 │  └─ Combine all results
         │
15:00:09 ─ Webhook Dispatch
15:00:09 │  ├─ Evaluate alert conditions
15:00:09 │  ├─ Fire CASCADE webhook (if applicable)
15:00:09 │  ├─ Fire FUNDING webhook (if applicable)
15:00:09 │  ├─ Fire VOLATILITY webhook (if applicable)
15:00:09 │  ├─ Fire CORRELATION webhook (if applicable)
15:00:09 │  ├─ Fire REGIME webhook (if applicable)
15:00:09 │  └─ Store results in database
         │
15:00:10 ─ Webhooks Delivered
15:00:10 │  ├─ Discord receives notification
15:00:10 │  ├─ Telegram receives message
15:00:10 │  ├─ Custom HTTP receives event
15:00:10 │  └─ Trading bot receives signal
         │
15:00:30 ─ Dashboard Updates
15:00:30 │  ├─ Browser polls /api/features
15:00:30 │  ├─ Browser polls /api/cascades
15:00:30 │  ├─ Browser polls /api/volatility
15:00:30 │  ├─ Browser polls /api/correlation
15:00:30 │  └─ Dashboard refreshes with new data
         │
15:00:31 ─ User Sees Results
15:00:31 │  ├─ Cascade metrics updated
15:00:31 │  ├─ Event stream shows new event
15:00:31 │  ├─ Alert banner displays
15:00:31 │  └─ Charts refresh with latest data
         │
15:01:00 ─ NEXT HOUR CYCLE BEGINS
         └─ Repeat
```

---

## Feature Decision Trees

### When is a CASCADE Alert Sent?

```
Cascade Event Detected
    │
    ├─ Is total > 500,000 USD? 
    │   NO → Skip
    │   YES ↓
    │
    ├─ Is velocity > 200K USD/hour?
    │   NO → Low severity (1-2)
    │   YES ↓
    │
    ├─ Classify Severity
    │   ├─ 100K-200K USD/h = Severity 2
    │   ├─ 200K-400K USD/h = Severity 3
    │   ├─ 400K-600K USD/h = Severity 4
    │   └─ >600K USD/h = Severity 5 (CRITICAL)
    │
    ├─ Send Webhook?
    │   ├─ Only if Severity >= 3
    │   └─ Send to: WEBHOOKS_CASCADE + WEBHOOKS_ALL
    │
    └─ Store in Database
        └─ Log for analytics & audit trail
```

### When is a FUNDING Alert Sent?

```
Funding Data Analyzed
    │
    ├─ Calculate Z-Score
    │   ├─ Z = (current - mean) / std_dev
    │   │
    │   ├─ If |Z| < 1.0: Normal (no alert)
    │   ├─ If 1.0 < |Z| < 2.0: Watch (no alert)
    │   └─ If |Z| >= 2.0: Anomaly (ALERT!)
    │
    ├─ Send Webhook?
    │   ├─ YES if anomaly detected
    │   └─ Send to: WEBHOOKS_FUNDING + WEBHOOKS_ALL
    │
    └─ Store Event
        └─ Track for reversal signals
```

### When is a VOLATILITY Alert Sent?

```
Volatility Calculated
    │
    ├─ Compare to Baseline
    │   ├─ If ratio < 1.0x: STABLE (no alert)
    │   ├─ If 1.0-1.5x: HIGH_VOL (watch)
    │   ├─ If 1.5-2.5x: EXPLOSIVE (ALERT!)
    │   └─ If > 2.5x: EXTREME (CRITICAL ALERT!)
    │
    ├─ Send Webhook?
    │   ├─ YES if regime changes AND is HIGH_VOL+
    │   └─ Send to: WEBHOOKS_VOLATILITY + WEBHOOKS_ALL
    │
    └─ Store Event
        └─ Track regime transitions
```

---

## System States

### Normal Operation
```
All features computing normally
✓ Data fetching: Success
✓ Cascade detector: No cascades
✓ Funding detector: No anomalies  
✓ Volatility: STABLE regime
✓ Regimes: Clear multi-timeframe agreement
✓ Correlations: Normal
→ No webhooks fired
→ Dashboard shows green indicators
```

### Active Market
```
Multiple features triggering
✓ Data fetching: Success
✓ Cascade detector: Moderate cascade detected
✓ Funding detector: Slight anomaly
! Volatility: HIGH_VOL regime (elevated)
! Regimes: Disagreement between timeframes
⚠ Correlations: Minor divergence
→ Multiple webhooks fired
→ Dashboard shows yellow/orange indicators
```

### Crisis Mode
```
Multiple critical events
✓ Data fetching: Success
✗ Cascade detector: CRITICAL cascade (5M+ USD)
✗ Funding detector: Extreme anomaly (Z > 3)
✗ Volatility: EXPLOSIVE regime
✗ Regimes: Major disagreement, low confidence
✗ Correlations: Major breaks detected
→ Critical webhooks fired repeatedly
→ Dashboard flashing red alerts
→ All external systems notified
```

---

## Configuration Impact

### Sensitivity Tuning

```
Configuration: LIQUIDATION_CFG["cascade_threshold_usd"]

High Value (1,000,000):
  → Only massive cascades trigger alerts
  → Few false positives, may miss events
  → Good for: Production stability

Medium Value (500,000):
  → Moderate cascades trigger alerts
  → Balanced sensitivity/specificity
  → Good for: Normal trading

Low Value (100,000):
  → Small cascades trigger alerts
  → Many alerts, some false positives
  → Good for: Research/analysis mode
```

### Feature Behavior by Configuration

```
FUNDING_CFG["anomaly_z_threshold"] = 2.0

If changed to 1.5:
  → More alerts (even small anomalies trigger)
  → Higher sensitivity
  → More noise but fewer missed events

If changed to 3.0:
  → Fewer alerts (only extreme anomalies trigger)
  → Lower sensitivity
  → Less noise but may miss events
```

---

## Scaling the System

### Low Volume (Local Development)
```
Data: 3 symbols, hourly intervals
Ingestion: ~1 second
Computation: ~2 seconds
Total Runtime: 3 seconds every hour
Storage: SQLite (enough for 1GB+ events)
```

### Medium Volume (Staging)
```
Data: 10 symbols, hourly intervals + multiple timeframes
Ingestion: ~3 seconds
Computation: ~5 seconds
Total Runtime: 8 seconds every hour
Storage: PostgreSQL (handles millions of events)
Webhooks: Sent to 5-10 endpoints
Dashboard: 10-50 concurrent users
```

### High Volume (Production)
```
Data: 50+ symbols, multiple intervals, real-time updates
Ingestion: Parallel API calls (~2-3 seconds)
Computation: Distributed across workers
Total Runtime: ~10-15 seconds for all symbols
Storage: PostgreSQL with replication
Webhooks: Sent to 20+ endpoints with queuing
Dashboard: 100+ concurrent users with caching
```

---

## Error Handling & Recovery

### API Connection Lost

```
Attempt 1: Try API call
  → Timeout/Error → Wait 1 second
Attempt 2: Retry
  → Timeout/Error → Wait 2 seconds
Attempt 3: Retry
  → Timeout/Error → Wait 4 seconds
Attempt 4: Retry
  → Still Failed → Use cached data from last hour
  → Log error: "API connection failed 4 times"
  → Continue with cached data
  → Notify admin if critical
```

### Webhook Delivery Failed

```
Send to https://webhook.com/events
  → Timeout (5s) → Retry once
  → Still fails → Log failure
  → Store for retry later
  → Continue (don't block pipeline)
  → Try again next hour
```

### Database Connection Lost

```
Attempt to connect
  → Connection failed → Reconnect
  → Queue events in memory
  → Once connected: Flush queued events
  → If still down after 30 min: Alert admin
  → Continue with in-memory storage
```

---

## Success Indicators

### System is Working Well When:
- ✓ All services start without errors
- ✓ Dashboard loads and updates every 10 seconds
- ✓ API responses < 100ms
- ✓ No gaps in event timestamps
- ✓ Webhooks deliver successfully
- ✓ Database has new events every hour
- ✓ Logs show normal INFO level messages

### Investigate When:
- ⚠ API response times > 500ms
- ⚠ Dashboard updates take >30 seconds
- ⚠ Webhooks show timeout errors
- ⚠ Logs show WARNING or ERROR
- ⚠ No new events in database for 2+ hours
- ⚠ High CPU or memory usage

### Critical Issues (Need Immediate Action):
- 🚨 Services won't start
- 🚨 Database connection failed
- 🚨 All webhooks failing
- 🚨 Dashboard completely unresponsive
- 🚨 Continuous ERROR logs

---

## Conclusion

The system operates on a simple but powerful cycle:

1. **Fetch** real-time market data from Binance
2. **Analyze** with 5 independent feature modules
3. **Combine** results into comprehensive picture
4. **Alert** external systems via webhooks
5. **Display** on real-time dashboard
6. **Store** everything for analytics

Repeat every hour, with dashboard updates every 10 seconds for live monitoring.

All components work together seamlessly to provide complete market intelligence.

---

**For more details, see:**
- Architecture: `SYSTEM_ARCHITECTURE_AND_INTEGRATION.md`
- Quick Start: `QUICK_START.md`
- Production: `PRODUCTION_DEPLOYMENT.md`
