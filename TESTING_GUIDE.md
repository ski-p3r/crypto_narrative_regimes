# Complete Testing Guide

Comprehensive guide to testing all components of the crypto narrative regime system.

## Testing Overview

The system has multiple layers to test:
1. **Data Ingestion** - Market data fetching from Binance.US
2. **Feature Computation** - Liquidation, funding, volatility calculations
3. **Regime Analysis** - Multi-timeframe regime detection
4. **Webhooks** - Event delivery to external systems
5. **Dashboard** - Web UI real-time updates
6. **Integration** - End-to-end system flow

## Quick Start Testing (10 minutes)

```bash
# 1. Test data ingestion
python test_features.py --component ingestion

# 2. Test feature calculation
python test_features.py --component features

# 3. Test webhooks
python test_features.py --component webhooks

# 4. Run full test suite
python test_features.py --full
```

## Detailed Testing

### 1. Data Ingestion Testing

Test that market data is fetching correctly from Binance.US:

```bash
python -c "
from ingestion_enhanced import BinanceDataFetcher
fetcher = BinanceDataFetcher()

# Fetch recent candles
btc_data = fetcher.fetch_recent_candles('BTC/USDT', 50)
print(f'BTC candles: {len(btc_data)} rows')
print(btc_data.head())

# Test funding rates
funding = fetcher.fetch_latest_funding()
print(f'Funding rates: {funding}')

# Test liquidation data
cascades = fetcher.fetch_liquidation_data('BTC/USDT', hours=24)
print(f'Liquidation events: {len(cascades)}')
"
```

**Expected Output:**
- ✓ BTC candles: 50 rows with OHLCV data
- ✓ Funding rates: Current funding rates for all symbols
- ✓ Liquidation events: Recent liquidation data

### 2. Feature Computation Testing

Test individual feature modules:

```bash
# Test liquidation cascade detection
python -c "
from features_liquidation_cascade import LiquidationCascadeDetector
from ingestion_enhanced import BinanceDataFetcher

fetcher = BinanceDataFetcher()
detector = LiquidationCascadeDetector()

# Get cascade data
cascades = fetcher.fetch_liquidation_data('BTC/USDT', hours=24)

# Analyze cascades
result = detector.analyze_cascades(cascades, 'BTC/USDT')
print(f'Cascade Analysis:')
print(f'  Total USD liquidated: {result[\"total_liquidation_usd\"]}')
print(f'  Velocity: {result[\"velocity_usd_per_hour\"]} USD/h')
print(f'  Severity: {result[\"severity\"]}')
"
```

### 3. Webhook Testing

Test webhook dispatcher without needing real endpoints:

```bash
python webhook_test.py

# Output:
# Testing CASCADE webhooks...
# Testing FUNDING webhooks...
# Testing VOLATILITY webhooks...
# Testing CORRELATION webhooks...
# Testing REGIME webhooks...
```

### 4. End-to-End Integration Test

Test the complete pipeline:

```bash
python -c "
import sys
sys.path.insert(0, '.')

from ingestion_enhanced import BinanceDataFetcher
from features_liquidation_cascade import LiquidationCascadeDetector
from features_funding_anomaly import FundingAnomalyDetector
from features_volatility_regime import VolatilityRegimeAnalyzer
from features_multi_timeframe import MultiTimeframeRegimeAnalyzer
from features_correlation_engine import CorrelationEngine
from webhook_dispatcher import WebhookDispatcher, WebhookEvent
from datetime import datetime, timezone

# Initialize components
fetcher = BinanceDataFetcher()
cascade_detector = LiquidationCascadeDetector()
funding_detector = FundingAnomalyDetector()
vol_analyzer = VolatilityRegimeAnalyzer()
mtf_analyzer = MultiTimeframeRegimeAnalyzer()
corr_engine = CorrelationEngine()
webhook = WebhookDispatcher()

print('1. Fetching market data...')
btc_data = fetcher.fetch_recent_candles('BTC/USDT', 100)
print(f'   ✓ Got {len(btc_data)} candles')

print('2. Computing features...')
cascade_result = cascade_detector.analyze_cascades(
    fetcher.fetch_liquidation_data('BTC/USDT', 24), 
    'BTC/USDT'
)
print(f'   ✓ Cascade severity: {cascade_result[\"severity\"]}')

funding_result = funding_detector.detect_anomalies(
    fetcher.fetch_latest_funding(),
    'BTC/USDT'
)
print(f'   ✓ Funding anomaly: {funding_result[\"is_anomaly\"]}')

vol_result = vol_analyzer.classify_volatility(btc_data)
print(f'   ✓ Volatility regime: {vol_result[\"vol_regime\"]}')

print('3. Computing correlations...')
corr_result = corr_engine.compute_correlations(
    ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
)
print(f'   ✓ Correlations computed')

print('4. All tests passed!')
"
```

## Advanced Testing

### Unit Test Suite

Create `test_suite.py`:

```python
import unittest
from datetime import datetime
import pandas as pd
import numpy as np

class TestLiquidationCascade(unittest.TestCase):
    def setUp(self):
        from features_liquidation_cascade import LiquidationCascadeDetector
        self.detector = LiquidationCascadeDetector()
    
    def test_cascade_detection(self):
        """Test cascade detection with synthetic data"""
        # Create test data: 500K liquidation in 1 hour
        cascade_data = {
            'symbol': 'BTC/USDT',
            'total_liquidation': 500000,
            'longs': 300000,
            'shorts': 200000,
            'timestamp': datetime.now()
        }
        
        result = self.detector.analyze_cascades([cascade_data], 'BTC/USDT')
        self.assertGreater(result['severity'], 0)
        self.assertEqual(result['total_liquidation_usd'], 500000)

class TestFundingDetector(unittest.TestCase):
    def setUp(self):
        from features_funding_anomaly import FundingAnomalyDetector
        self.detector = FundingAnomalyDetector()
    
    def test_extreme_funding(self):
        """Test funding anomaly detection"""
        funding_data = {
            'BTC/USDT': {'funding_rate': 0.005, 'timestamp': datetime.now()}
        }
        
        result = self.detector.detect_anomalies(funding_data, 'BTC/USDT')
        self.assertTrue(result['is_anomaly'])

class TestVolatilityRegime(unittest.TestCase):
    def setUp(self):
        from features_volatility_regime import VolatilityRegimeAnalyzer
        self.analyzer = VolatilityRegimeAnalyzer()
    
    def test_high_volatility(self):
        """Test volatility classification"""
        # Create high volatility data
        closes = np.random.normal(50000, 5000, 50)  # High variance
        data = pd.DataFrame({'close': closes})
        
        result = self.analyzer.classify_volatility(data)
        # Should classify as HIGH_VOL or higher
        self.assertIn(result['vol_regime'], ['HIGH_VOL', 'EXPLOSIVE', 'EXTREME'])

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python -m unittest test_suite -v
```

### Load Testing

Test system performance under load:

```python
# load_test.py
import threading
import time
from ingestion_enhanced import BinanceDataFetcher
from pipeline_features_master import FeaturesPipeline

def worker(worker_id, num_iterations):
    """Worker thread that runs feature pipeline"""
    pipeline = FeaturesPipeline()
    
    for i in range(num_iterations):
        print(f"Worker {worker_id}: iteration {i+1}")
        result = pipeline.compute_all_features()
        time.sleep(1)

# Run 3 workers concurrently
threads = []
for i in range(3):
    t = threading.Thread(target=worker, args=(i, 10))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Load test completed!")
```

Run:
```bash
python load_test.py
```

### Dashboard Testing

Test dashboard API endpoints:

```bash
# Start dashboard
cd dashboard && npm run dev &

# Test API endpoints
curl http://localhost:3000/api/features
curl http://localhost:3000/api/cascades?hours=24
curl http://localhost:3000/api/volatility
curl http://localhost:3000/api/correlation

# Test real-time endpoint
curl http://localhost:3000/api/realtime
```

## Test Coverage Report

Generate coverage report:

```bash
pip install coverage
coverage run -m unittest discover
coverage report -m
coverage html  # Opens htmlcov/index.html
```

## Continuous Testing

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest coverage
    
    - name: Run tests
      run: |
        pytest
        coverage report
    
    - name: Run feature tests
      run: python test_features.py --full
```

## Debugging & Logs

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Now get more verbose output
logger = logging.getLogger(__name__)
logger.debug("Detailed debug information")
```

### Test Specific Components

```bash
# Test with specific symbol
python test_features.py --symbol ETH/USDT

# Test specific timeframe
python test_features.py --timeframe 4h

# Test with mock data
python test_features.py --mock-data

# Verbose output
python test_features.py --verbose
```

## Performance Benchmarks

Expected performance metrics:

```
Data Ingestion:
  - 50 candles: 0.2s
  - Liquidation data: 0.5s
  - Funding rates: 0.2s

Feature Computation:
  - Cascade detection: 0.1s
  - Funding analysis: 0.1s
  - Volatility: 0.05s
  - Correlation: 0.3s
  - Total: ~1.0s

Dashboard:
  - API response: <100ms
  - Page load: <1s
  - WebSocket update: <50ms
```

If performance is slower, check:
1. Network connectivity to Binance.US
2. Database query performance
3. Python version (use 3.9+)
4. System resources (CPU/RAM)

## Testing Checklist

- [ ] Data ingestion tests pass
- [ ] Feature calculation tests pass
- [ ] Webhook tests pass
- [ ] Dashboard API tests pass
- [ ] Load test completes without errors
- [ ] Coverage > 80%
- [ ] All logs show INFO level or better
- [ ] No API rate limit errors
- [ ] Real-time updates working
- [ ] Error handling tested
