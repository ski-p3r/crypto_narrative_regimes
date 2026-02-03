# Webhook Setup Guide

Complete guide to configuring and testing webhooks for the crypto narrative regime system.

## Overview

Webhooks allow you to receive real-time event notifications when market events occur:
- **Liquidation Cascades** - Large rapid liquidations detected
- **Funding Rate Anomalies** - Extreme funding levels detected
- **Volatility Regime Changes** - Market volatility state transitions
- **Correlation Breaks** - Asset pairs diverging from normal patterns
- **Regime Confirmations** - Multi-timeframe confirmation signals

## Quick Setup (5 minutes)

### 1. Choose Your Webhook Receiver

**Option A: Webhook.site (No Setup Required)**
```bash
# Go to https://webhook.site
# Copy your unique webhook URL
# It will be something like: https://webhook.site/your-unique-id
```

**Option B: Discord Webhook**
```bash
# 1. Create a Discord Server or use existing one
# 2. Create a Channel (e.g., #market-alerts)
# 3. Right-click channel → Edit Channel → Integrations → Create Webhook
# 4. Copy the webhook URL
# Example: https://discordapp.com/api/webhooks/...
```

**Option C: Custom HTTP Endpoint**
```bash
# Set up your own server to receive POST requests
# See "Building Your Own Webhook Receiver" below
```

### 2. Configure Environment Variables

Create or update your `.env` file:

```bash
# Single webhook for all events
WEBHOOKS_ALL=https://webhook.site/your-unique-id

# Or configure specific event types
WEBHOOKS_CASCADE=https://webhook.site/cascade-receiver
WEBHOOKS_FUNDING=https://webhook.site/funding-receiver
WEBHOOKS_VOLATILITY=https://webhook.site/volatility-receiver
WEBHOOKS_CORRELATION=https://webhook.site/correlation-receiver
WEBHOOKS_REGIME=https://webhook.site/regime-receiver

# Multiple webhooks per event (comma-separated)
WEBHOOKS_CASCADE=https://webhook.site/cascade-1,https://webhook.site/cascade-2
```

### 3. Test Your Setup

```bash
# Run the webhook test
python webhook_test.py

# Or test individual event types
python webhook_test.py --type cascade
python webhook_test.py --type funding
python webhook_test.py --type volatility
```

## Event Payload Format

All webhook events follow this JSON structure:

```json
{
  "event_type": "LIQUIDATION_CASCADE",
  "timestamp": "2024-02-03T15:30:45.123456+00:00",
  "symbol": "BTC/USDT",
  "severity": "CRITICAL|WARNING|INFO",
  "title": "Liquidation Cascade Detected - BTC/USDT",
  "description": "Large liquidation event with velocity 1,234,567 USD/h",
  "source": "CASCADE|FUNDING|VOLATILITY|CORRELATION|REGIME",
  "data": {
    "velocity_usd_per_hour": 1234567,
    "long_liquidations_usd": 800000,
    "short_liquidations_usd": 434567,
    "total_liquidation_usd": 1234567,
    "severity": 2,
    "risk_level": "HIGH"
  }
}
```

## Event Types Reference

### CASCADE Events
```json
{
  "event_type": "LIQUIDATION_CASCADE",
  "severity": "CRITICAL|WARNING",
  "data": {
    "velocity_usd_per_hour": 1500000,
    "long_liquidations_usd": 900000,
    "short_liquidations_usd": 600000,
    "support_levels": [45000, 44500],
    "resistance_levels": [47000, 47500]
  }
}
```

### FUNDING Events
```json
{
  "event_type": "FUNDING_ANOMALY|FUNDING_REVERSAL",
  "severity": "WARNING|INFO",
  "data": {
    "funding_rate": 0.00125,
    "z_score": 2.5,
    "extreme_level": "HIGH",
    "persistence_score": 0.75
  }
}
```

### VOLATILITY Events
```json
{
  "event_type": "VOLATILITY_REGIME_CHANGE",
  "severity": "WARNING|INFO",
  "data": {
    "old_regime": "STABLE",
    "new_regime": "HIGH_VOL",
    "volatility_24h": 0.032,
    "clustering_probability": 0.85
  }
}
```

### CORRELATION Events
```json
{
  "event_type": "CORRELATION_BREAK",
  "severity": "WARNING",
  "data": {
    "asset_pair": "BTC/ETH",
    "normal_correlation": 0.87,
    "return_correlation": 0.32,
    "divergence_severity": "HIGH"
  }
}
```

### REGIME Events
```json
{
  "event_type": "REGIME_CONFIRMED",
  "severity": "INFO",
  "data": {
    "primary_regime": "SPOT_IGNITION",
    "1h_regime": "SPOT_IGNITION",
    "4h_regime": "SPOT_IGNITION",
    "1d_regime": "SPOT_COOLING",
    "confidence_score": 0.92
  }
}
```

## Discord Webhook Integration

### Setup

1. Get your Discord webhook URL from Discord channel settings
2. Add to `.env`:
```bash
WEBHOOKS_ALL=https://discordapp.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
```

### Custom Discord Formatting

Convert generic webhooks to Discord embeds:

```python
def format_for_discord(event):
    """Convert WebhookEvent to Discord embed format"""
    color_map = {
        "CRITICAL": 15158332,  # Red
        "WARNING": 15105570,   # Orange
        "INFO": 3447003        # Green
    }
    
    return {
        "embeds": [{
            "title": event.title,
            "description": event.description,
            "color": color_map.get(event.severity, 9807270),
            "fields": [
                {"name": "Symbol", "value": event.symbol, "inline": True},
                {"name": "Severity", "value": event.severity, "inline": True},
                {"name": "Source", "value": event.source, "inline": True},
                {"name": "Data", "value": f"```json\n{json.dumps(event.data)}\n```"}
            ],
            "timestamp": event.timestamp.isoformat()
        }]
    }
```

## Building Your Own Webhook Receiver

### Simple Flask Example

```python
from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhooks/market-events', methods=['POST'])
def handle_webhook():
    event = request.get_json()
    
    # Log the event
    print(f"Received {event['event_type']} for {event['symbol']}")
    
    # Process based on severity
    if event['severity'] == 'CRITICAL':
        send_alert_to_admin(event)
    
    # Store in database
    store_event(event)
    
    # Send to trading system
    if event['source'] == 'CASCADE':
        execute_cascade_trade(event)
    
    return {"status": "received"}, 200

def send_alert_to_admin(event):
    """Send critical alerts to your notification service"""
    pass

def store_event(event):
    """Store event in database for analytics"""
    pass

def execute_cascade_trade(event):
    """Execute automatic trading logic"""
    pass

if __name__ == '__main__':
    app.run(port=5000)
```

### Deploy on Heroku

```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create requirements.txt
pip freeze > requirements.txt

# Deploy
heroku create my-webhook-receiver
git push heroku main
heroku logs --tail

# Get public URL
heroku open
```

## Testing Webhooks

### Manual Test with cURL

```bash
# Test single event
curl -X POST https://webhook.site/your-unique-id \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "LIQUIDATION_CASCADE",
    "timestamp": "2024-02-03T15:30:45Z",
    "symbol": "BTC/USDT",
    "severity": "CRITICAL",
    "title": "Test Cascade Event",
    "description": "Testing cascade alert",
    "source": "CASCADE",
    "data": {"velocity_usd_per_hour": 1500000}
  }'
```

### Python Test Script

```python
import requests
import json
from datetime import datetime, timezone

def test_webhook(webhook_url, event_type):
    """Test webhook with sample event"""
    
    events = {
        "cascade": {
            "event_type": "LIQUIDATION_CASCADE",
            "symbol": "BTC/USDT",
            "severity": "CRITICAL",
            "title": "Test Cascade Event",
            "description": "Large liquidation velocity detected",
            "source": "CASCADE",
            "data": {"velocity_usd_per_hour": 2000000}
        },
        "funding": {
            "event_type": "FUNDING_ANOMALY",
            "symbol": "ETH/USDT",
            "severity": "WARNING",
            "title": "Test Funding Anomaly",
            "description": "Extreme funding detected",
            "source": "FUNDING",
            "data": {"funding_rate": 0.002, "z_score": 3.2}
        }
    }
    
    payload = events[event_type]
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    response = requests.post(webhook_url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
```

## Production Considerations

### Retry Logic

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_robust_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
```

### Webhook Verification

Add authentication to your webhook receivers:

```python
import hmac
import hashlib

SECRET_KEY = os.getenv("WEBHOOK_SECRET")

def verify_webhook_signature(request, secret):
    """Verify webhook came from legitimate source"""
    signature = request.headers.get('X-Webhook-Signature')
    
    body = request.get_data()
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

### Rate Limiting

Protect your webhooks from abuse:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/webhooks/events', methods=['POST'])
@limiter.limit("100 per hour")
def handle_event():
    return {"status": "ok"}
```

## Monitoring Webhooks

### Log All Events

```python
import logging

logging.basicConfig(
    filename='webhooks.log',
    level=logging.INFO,
    format='%(asctime)s - %(event_type)s - %(symbol)s - %(severity)s'
)

def dispatch_event(event):
    # ... existing code ...
    logging.info(f"Event: {event.event_type} Symbol: {event.symbol} Severity: {event.severity}")
```

### Webhook Status Dashboard

Track webhook health:

```python
import sqlite3
from datetime import datetime, timedelta

def log_webhook_attempt(url, success, response_code):
    """Log webhook delivery attempt"""
    conn = sqlite3.connect('webhook_stats.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO webhook_log 
        (url, timestamp, success, response_code) 
        VALUES (?, ?, ?, ?)
    ''', (url, datetime.now(), success, response_code))
    
    conn.commit()
    conn.close()

def get_webhook_stats(hours=24):
    """Get webhook delivery statistics"""
    conn = sqlite3.connect('webhook_stats.db')
    cursor = conn.cursor()
    
    cutoff = datetime.now() - timedelta(hours=hours)
    cursor.execute('''
        SELECT url, COUNT(*) as total, SUM(success) as delivered
        FROM webhook_log
        WHERE timestamp > ?
        GROUP BY url
    ''', (cutoff,))
    
    return cursor.fetchall()
```

## Troubleshooting

### Webhooks Not Firing

1. Check environment variables:
   ```bash
   echo $WEBHOOKS_ALL
   echo $WEBHOOKS_CASCADE
   ```

2. Verify webhook dispatcher is loaded:
   ```python
   from webhook_dispatcher import get_dispatcher
   dispatcher = get_dispatcher()
   print(dispatcher.webhooks)
   ```

3. Check logs for errors:
   ```bash
   tail -f /var/log/market_regime.log | grep WEBHOOK
   ```

### Webhook Not Receiving Data

1. Test endpoint is accessible:
   ```bash
   curl -v https://webhook.site/your-url
   ```

2. Check firewall/network rules

3. Verify Content-Type header is set to application/json

4. Check webhook receiver logs for errors

### High Latency

1. Reduce event frequency in `config.py`
2. Implement webhook queuing (see Production Guide)
3. Use async dispatch to non-blocking thread pool

## Security Best Practices

1. **Use HTTPS only** for webhook URLs
2. **Add authentication** (API keys, signatures)
3. **Validate SSL certificates** in production
4. **Rate limit** webhook endpoints
5. **Encrypt** sensitive data in payloads
6. **Monitor** webhook delivery statistics
7. **Use secrets management** for credentials
8. **Implement retry logic** with exponential backoff
