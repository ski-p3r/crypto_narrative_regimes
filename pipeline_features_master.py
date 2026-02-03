import os
from dotenv import load_dotenv
load_dotenv()
import logging
import time
from datetime import datetime, timezone

from features_liquidation_cascade import compute_liquidation_metrics
from features_funding_anomaly import compute_funding_metrics
from features_volatility_regime import compute_volatility_features
from features_multi_timeframe import compute_multi_timeframe_regimes
from features_correlation_engine import compute_correlation_metrics
from webhook_dispatcher import get_dispatcher, WebhookEvent

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pipeline_master")


def run_all_features(dispatch_events=True):
    """
    Compute all advanced features and optionally dispatch webhook events.
    """
    log.info("[MASTER] Starting feature computation pipeline...")
    start_time = datetime.now()
    
    results = {
        "timestamp": start_time,
        "features": {},
        "alerts": [],
    }
    
    try:
        # 1. Liquidation Cascade Detection
        log.info("[MASTER] Computing liquidation cascades...")
        cascade_result = compute_liquidation_metrics()
        results["features"]["liquidation_cascades"] = cascade_result
        
        if dispatch_events and cascade_result.get("cascade_events"):
            dispatcher = get_dispatcher()
            for event_data in cascade_result["cascade_events"]:
                dispatcher.dispatch_cascade_event(
                    symbol=event_data["symbol"],
                    event_data=event_data,
                )
                results["alerts"].append({
                    "type": "CASCADE",
                    "symbol": event_data["symbol"],
                })
        
        # 2. Funding Rate Anomalies
        log.info("[MASTER] Computing funding anomalies...")
        funding_result = compute_funding_metrics()
        results["features"]["funding_anomalies"] = funding_result
        
        if dispatch_events and funding_result.get("funding_anomalies"):
            dispatcher = get_dispatcher()
            for event_data in funding_result["funding_anomalies"]:
                dispatcher.dispatch_funding_anomaly(
                    symbol=event_data["symbol"],
                    event_data=event_data,
                )
                results["alerts"].append({
                    "type": "FUNDING_ANOMALY",
                    "symbol": event_data["symbol"],
                })
        
        if dispatch_events and funding_result.get("reversal_signals"):
            dispatcher = get_dispatcher()
            for event_data in funding_result["reversal_signals"]:
                dispatcher.dispatch_reversal_signal(
                    symbol=event_data["symbol"],
                    event_data=event_data,
                )
                results["alerts"].append({
                    "type": "FUNDING_REVERSAL",
                    "symbol": event_data["symbol"],
                })
        
        # 3. Volatility Regime Analysis
        log.info("[MASTER] Computing volatility regimes...")
        volatility_result = compute_volatility_features()
        results["features"]["volatility_analysis"] = volatility_result
        
        # 4. Multi-Timeframe Regimes
        log.info("[MASTER] Computing multi-timeframe regimes...")
        mtf_result = compute_multi_timeframe_regimes()
        results["features"]["multi_timeframe_regimes"] = mtf_result
        
        if dispatch_events and mtf_result.get("primary_regimes"):
            dispatcher = get_dispatcher()
            for regime_data in mtf_result["primary_regimes"]:
                if regime_data.get("confidence_score", 0) > 0.7:  # Only high-confidence
                    dispatcher.dispatch_regime_confirmation(
                        symbol=regime_data["symbol"],
                        event_data=regime_data,
                    )
                    results["alerts"].append({
                        "type": "REGIME_CONFIRMED",
                        "symbol": regime_data["symbol"],
                    })
        
        # 5. Correlation Analysis
        log.info("[MASTER] Computing correlations...")
        correlation_result = compute_correlation_metrics()
        results["features"]["correlation_analysis"] = correlation_result
        
        if dispatch_events and correlation_result.get("divergence_events"):
            dispatcher = get_dispatcher()
            for event_data in correlation_result["divergence_events"]:
                pair = event_data.get("asset_pair", "UNKNOWN")
                dispatcher.dispatch_correlation_break(
                    asset_pair=pair,
                    event_data=event_data,
                )
                results["alerts"].append({
                    "type": "CORRELATION_BREAK",
                    "asset_pair": pair,
                })
        
        elapsed = (datetime.now() - start_time).total_seconds()
        log.info(f"[MASTER] Feature pipeline completed in {elapsed:.1f}s")
        log.info(f"[MASTER] Generated {len(results['alerts'])} alerts")
        
    except Exception as e:
        log.error(f"[MASTER] Error in feature pipeline: {e}", exc_info=True)
    
    return results


def run_periodic_pipeline(interval_minutes=60):
    """
    Run the feature pipeline periodically.
    """
    log.info(f"[MASTER] Starting periodic pipeline every {interval_minutes} minutes...")
    
    while True:
        try:
            result = run_all_features(dispatch_events=True)
            
            # Log summary
            num_features = len(result.get("features", {}))
            num_alerts = len(result.get("alerts", []))
            log.info(f"[MASTER] Cycle complete: {num_features} features computed, {num_alerts} alerts sent")
        
        except Exception as e:
            log.error(f"[MASTER] Error in periodic run: {e}")
        
        # Sleep
        log.info(f"[MASTER] Sleeping for {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    # One-time run
    result = run_all_features(dispatch_events=False)
    print(f"\nFeatures computed: {list(result['features'].keys())}")
    print(f"Alerts: {len(result['alerts'])}")
    
    # Uncomment to run periodically:
    # run_periodic_pipeline(interval_minutes=1)
