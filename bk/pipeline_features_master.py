import logging
from datetime import datetime

from bk.liquidation_cascade import run as run_liq
from bk.funding_anomaly import run as run_funding
from bk.volatility_regime import run as run_vol
from bk.multi_timeframe import run as run_mtf
from bk.correlation_engine import run as run_corr

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bk_pipeline_master")


def run_all_features():
    """Compute all advanced features via bk wrappers (no webhooks)."""
    log.info("[BK-MASTER] Starting feature computation pipeline...")
    start_time = datetime.now()

    results = {
        "timestamp": start_time,
        "features": {},
        "alerts": [],
    }

    # 1. Liquidation cascades
    liq = run_liq()
    results["features"]["liquidation_cascades"] = liq
    for e in liq.get("cascade_events", []):
        results["alerts"].append({"type": "CASCADE", "symbol": e.get("symbol")})

    # 2. Funding anomalies
    fund = run_funding()
    results["features"]["funding_anomalies"] = fund
    for e in fund.get("funding_anomalies", []):
        results["alerts"].append({"type": "FUNDING_ANOMALY", "symbol": e.get("symbol")})
    for e in fund.get("reversal_signals", []):
        results["alerts"].append({"type": "FUNDING_REVERSAL", "symbol": e.get("symbol")})

    # 3. Volatility features
    vol = run_vol()
    results["features"]["volatility_analysis"] = vol

    # 4. Multi-timeframe regimes
    mtf = run_mtf()
    results["features"]["multi_timeframe_regimes"] = mtf
    for r in mtf.get("primary_regimes", []):
        if r.get("confidence_score", 0) > 0.7:
            results["alerts"].append({"type": "REGIME_CONFIRMED", "symbol": r.get("symbol")})

    # 5. Correlation
    corr = run_corr()
    results["features"]["correlation_analysis"] = corr
    for e in corr.get("divergence_events", []):
        results["alerts"].append({"type": "CORRELATION_BREAK", "asset_pair": e.get("asset_pair")})

    elapsed = (datetime.now() - start_time).total_seconds()
    log.info(f"[BK-MASTER] Feature pipeline completed in {elapsed:.1f}s with {len(results['alerts'])} alerts")

    return results


if __name__ == "__main__":
    res = run_all_features()
    print(f"Features computed: {list(res['features'].keys())}")
    print(f"Alerts: {len(res['alerts'])}")
