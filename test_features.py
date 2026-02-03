#!/usr/bin/env python3
"""
Test script to verify all feature modules are working correctly.
Run this to validate the implementation before deploying.
"""

import os
from dotenv import load_dotenv
load_dotenv()

import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
log = logging.getLogger("test_features")

def test_config():
    """Test configuration is loaded correctly."""
    log.info("Testing config module...")
    try:
        from config import (
            EXCHANGES, SYMBOLS, REGIME_CFG,
            LIQUIDATION_CFG, FUNDING_CFG, VOLATILITY_CFG,
            TIMEFRAMES, CORRELATION_CFG
        )
        
        assert EXCHANGES == ["binanceus"], "Exchanges should be binanceus"
        assert len(SYMBOLS) >= 3, "Should have at least 3 symbols"
        assert "SPOT_IGNITION" in REGIME_CFG, "Missing SPOT_IGNITION regime"
        assert "cascade_threshold_usd" in LIQUIDATION_CFG, "Missing liquidation config"
        assert "anomaly_z_threshold" in FUNDING_CFG, "Missing funding config"
        assert "stable_threshold" in VOLATILITY_CFG, "Missing volatility config"
        
        log.info("✅ Config test passed")
        return True
    except Exception as e:
        log.error(f"❌ Config test failed: {e}")
        return False


def test_liquidation_module():
    """Test liquidation cascade detection module."""
    log.info("Testing liquidation cascade module...")
    try:
        from features_liquidation_cascade import (
            detect_cascade_events,
            identify_liquidation_support_zones,
            compute_liquidation_metrics
        )
        
        # Test imports
        result = compute_liquidation_metrics()
        assert "cascade_events" in result, "Missing cascade_events in result"
        assert "liquidation_zones" in result, "Missing liquidation_zones in result"
        
        log.info(f"✅ Liquidation test passed (found {len(result['cascade_events'])} cascades)")
        return True
    except Exception as e:
        log.error(f"❌ Liquidation test failed: {e}")
        return False


def test_funding_module():
    """Test funding rate anomaly detection module."""
    log.info("Testing funding anomaly module...")
    try:
        from features_funding_anomaly import (
            detect_funding_anomalies,
            detect_reversal_signals,
            compute_funding_metrics
        )
        
        result = compute_funding_metrics()
        assert "funding_anomalies" in result, "Missing funding_anomalies in result"
        assert "reversal_signals" in result, "Missing reversal_signals in result"
        
        log.info(f"✅ Funding test passed (found {len(result['funding_anomalies'])} anomalies)")
        return True
    except Exception as e:
        log.error(f"❌ Funding test failed: {e}")
        return False


def test_volatility_module():
    """Test volatility regime module."""
    log.info("Testing volatility regime module...")
    try:
        from features_volatility_regime import (
            compute_volatility_metrics,
            analyze_volatility_persistence,
            compute_volatility_features
        )
        
        result = compute_volatility_features()
        assert "volatility_regimes" in result, "Missing volatility_regimes in result"
        assert "volatility_persistence" in result, "Missing volatility_persistence in result"
        
        log.info(f"✅ Volatility test passed (found {len(result['volatility_regimes'])} regimes)")
        return True
    except Exception as e:
        log.error(f"❌ Volatility test failed: {e}")
        return False


def test_multi_timeframe_module():
    """Test multi-timeframe regime analysis."""
    log.info("Testing multi-timeframe regime module...")
    try:
        from features_multi_timeframe import compute_multi_timeframe_regimes
        
        result = compute_multi_timeframe_regimes()
        assert "primary_regimes" in result, "Missing primary_regimes in result"
        assert "timeframe_regimes" in result, "Missing timeframe_regimes in result"
        assert "agreement_scores" in result, "Missing agreement_scores in result"
        
        log.info(f"✅ Multi-timeframe test passed (found {len(result['primary_regimes'])} primary regimes)")
        return True
    except Exception as e:
        log.error(f"❌ Multi-timeframe test failed: {e}")
        return False


def test_correlation_module():
    """Test correlation engine."""
    log.info("Testing correlation engine...")
    try:
        from features_correlation_engine import compute_correlation_metrics
        
        result = compute_correlation_metrics()
        assert "price_correlation_matrix" in result or "divergence_events" in result, "Missing correlation data"
        
        log.info(f"✅ Correlation test passed (found {len(result.get('divergence_events', []))} divergence events)")
        return True
    except Exception as e:
        log.error(f"❌ Correlation test failed: {e}")
        return False


def test_webhook_dispatcher():
    """Test webhook dispatcher."""
    log.info("Testing webhook dispatcher...")
    try:
        from webhook_dispatcher import (
            WebhookDispatcher,
            WebhookEvent,
            get_dispatcher
        )
        
        dispatcher = get_dispatcher()
        
        # Test creating an event
        test_event = WebhookEvent(
            event_type="TEST_EVENT",
            timestamp=datetime.now(timezone.utc),
            symbol="BTC/USDT",
            severity="INFO",
            title="Test Event",
            description="This is a test event",
            data={"test": True},
            source="TEST",
        )
        
        assert test_event.event_type == "TEST_EVENT", "Event type mismatch"
        assert test_event.symbol == "BTC/USDT", "Symbol mismatch"
        
        log.info("✅ Webhook dispatcher test passed")
        return True
    except Exception as e:
        log.error(f"❌ Webhook dispatcher test failed: {e}")
        return False


def test_pipeline_master():
    """Test master pipeline."""
    log.info("Testing master pipeline...")
    try:
        from pipeline_features_master import run_all_features
        
        # Run without dispatching webhooks
        result = run_all_features(dispatch_events=False)
        assert "timestamp" in result, "Missing timestamp in result"
        assert "features" in result, "Missing features in result"
        assert "alerts" in result, "Missing alerts in result"
        
        num_features = len(result['features'])
        num_alerts = len(result['alerts'])
        
        log.info(f"✅ Pipeline test passed ({num_features} features, {num_alerts} alerts)")
        return True
    except Exception as e:
        log.error(f"❌ Pipeline test failed: {e}")
        return False


def test_ingestion_enhanced():
    """Test enhanced ingestion module."""
    log.info("Testing enhanced ingestion module...")
    try:
        from ingestion_enhanced import (
            fetch_for_exchange,
            fetch_liquidation_data,
            fetch_funding_rates
        )
        
        # Test that functions are callable
        assert callable(fetch_for_exchange), "fetch_for_exchange not callable"
        assert callable(fetch_liquidation_data), "fetch_liquidation_data not callable"
        assert callable(fetch_funding_rates), "fetch_funding_rates not callable"
        
        log.info("✅ Enhanced ingestion test passed")
        return True
    except Exception as e:
        log.error(f"❌ Enhanced ingestion test failed: {e}")
        return False


def main():
    """Run all tests."""
    log.info("=" * 60)
    log.info("CRYPTO NARRATIVE REGIMES - FEATURE TEST SUITE")
    log.info("=" * 60)
    
    tests = [
        ("Config Module", test_config),
        ("Liquidation Module", test_liquidation_module),
        ("Funding Module", test_funding_module),
        ("Volatility Module", test_volatility_module),
        ("Multi-Timeframe Module", test_multi_timeframe_module),
        ("Correlation Engine", test_correlation_module),
        ("Webhook Dispatcher", test_webhook_dispatcher),
        ("Enhanced Ingestion", test_ingestion_enhanced),
        ("Master Pipeline", test_pipeline_master),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            log.error(f"Unexpected error in {name}: {e}")
            results.append((name, False))
        
        log.info("")
    
    # Summary
    log.info("=" * 60)
    log.info("TEST SUMMARY")
    log.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        log.info(f"{status} - {name}")
    
    log.info("=" * 60)
    log.info(f"TOTAL: {passed}/{total} tests passed")
    log.info("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
