import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine

from config import TIMEFRAMES, REGIME_CFG, MIN_OBS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("multi_timeframe")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)


def add_features_for_timeframe(g: pd.DataFrame, window=None) -> pd.DataFrame:
    """Add technical features for a given timeframe."""
    g = g.sort_values("ts").copy()
    
    if len(g) < MIN_OBS:
        return g
    
    if window is None:
        window = 24  # Default to 24 periods
    
    # Process volume and price
    cols_to_process = ["volume", "price"]
    
    for col in cols_to_process:
        if col not in g.columns:
            continue
        if g[col].notna().sum() < MIN_OBS:
            continue
        
        roll = g[col].rolling(window=window, min_periods=MIN_OBS)
        mean_roll = roll.mean().shift(1)
        std_roll = roll.std().shift(1)
        
        # EWM fallback
        ewm_span = max(window // 4, 6)
        ewm_mean = g[col].ewm(span=ewm_span, adjust=False).mean().shift(1)
        ewm_std = g[col].ewm(span=ewm_span, adjust=False).std().shift(1)
        
        g[f"{col}_mean"] = mean_roll.fillna(ewm_mean)
        g[f"{col}_std"] = std_roll.fillna(ewm_std)
        
        std_safe = g[f"{col}_std"].where(g[f"{col}_std"] > 1e-8)
        g[f"{col}_z"] = (g[col] - g[f"{col}_mean"]) / std_safe
    
    return g


def classify_regime_simple(price_z, vol_z, heat=0.5):
    """Simple regime classification."""
    price_z = price_z or 0.0
    vol_z = vol_z or 0.0
    heat = heat or 0.5
    
    if price_z > 0.8 and vol_z > 0.8:
        return "IGNITION", 0.75
    elif price_z < -0.5 and vol_z < 0.5:
        return "COOLING", 0.65
    elif abs(price_z) < 0.3 and vol_z < 1.0:
        return "CHOP", 0.60
    else:
        return "NEUTRAL", 0.50


def compute_multi_timeframe_regimes():
    """
    Compute regimes across multiple timeframes (1h, 4h, 1d, 1w).
    Provide confidence scores based on alignment across timeframes.
    """
    log.info("[MTF] Computing multi-timeframe regimes...")
    
    timeframe_windows = {
        "1h": 24,
        "4h": 24,
        "1d": 30,
        "1w": 12,
    }
    
    results = {
        "primary_regimes": [],
        "timeframe_regimes": {},
        "agreement_scores": {},
        "timestamp": datetime.now(timezone.utc),
    }
    
    try:
        # Fetch data for different timeframes
        for tf in TIMEFRAMES:
            try:
                # Map CCXT timeframes to hours
                if tf == "1h":
                    hours_back = 24 * 30  # Last 30 days for hourly
                elif tf == "4h":
                    hours_back = 24 * 60  # Last 60 days for 4h
                elif tf == "1d":
                    hours_back = 24 * 180  # Last 180 days for daily
                else:  # 1w
                    hours_back = 24 * 365  # Last year for weekly
                
                # Aggregate market data to timeframe
                df = pd.read_sql(f"""
                    SELECT 
                        DATE_TRUNC('{tf}', ts)::timestamp as ts_period,
                        symbol,
                        exchange,
                        LAST(price, ts) as price,
                        MAX(volume) as volume,
                        SUM(COALESCE(long_liq_usd, 0) + COALESCE(short_liq_usd, 0)) as liquidations
                    FROM market_metrics
                    WHERE ts > NOW() - INTERVAL '{hours_back} hours'
                    GROUP BY ts_period, symbol, exchange
                    ORDER BY symbol, ts_period
                """, engine)
                
                if df.empty:
                    log.debug(f"[MTF] No data for timeframe {tf}")
                    continue
                
                df = df.rename(columns={'ts_period': 'ts'})
                
                # Add features
                df = df.groupby(['symbol', 'exchange'], group_keys=False).apply(
                    lambda g: add_features_for_timeframe(g, window=timeframe_windows.get(tf, 24))
                )
                
                tf_regimes = []
                
                # Classify regimes per symbol
                latest_ts = df['ts'].max()
                latest = df[df['ts'] == latest_ts]
                
                for _, row in latest.iterrows():
                    regime, confidence = classify_regime_simple(
                        row.get('price_z'),
                        row.get('volume_z'),
                        heat=0.5
                    )
                    
                    tf_regimes.append({
                        "timeframe": tf,
                        "symbol": row['symbol'],
                        "regime": regime,
                        "confidence": confidence,
                        "price": row.get('price'),
                        "volume_z": row.get('volume_z'),
                        "price_z": row.get('price_z'),
                    })
                
                results["timeframe_regimes"][tf] = tf_regimes
                log.info(f"[MTF] {tf}: {len(tf_regimes)} regimes computed")
            
            except Exception as e:
                log.warning(f"[MTF] Error processing timeframe {tf}: {e}")
        
        # Compute agreement scores between timeframes
        if len(results["timeframe_regimes"]) >= 2:
            symbols = set()
            for tf_data in results["timeframe_regimes"].values():
                symbols.update([r['symbol'] for r in tf_data])
            
            for symbol in symbols:
                regimes_for_symbol = {}
                
                for tf, tf_data in results["timeframe_regimes"].items():
                    for regime_row in tf_data:
                        if regime_row['symbol'] == symbol:
                            regimes_for_symbol[tf] = regime_row['regime']
                
                # Count agreements
                if len(regimes_for_symbol) >= 2:
                    most_common = max(set(regimes_for_symbol.values()), 
                                    key=list(regimes_for_symbol.values()).count)
                    agreement_count = list(regimes_for_symbol.values()).count(most_common)
                    agreement_pct = agreement_count / len(regimes_for_symbol)
                    
                    results["agreement_scores"][symbol] = {
                        "primary_regime": most_common,
                        "agreement_percentage": agreement_pct,
                        "regimes_by_timeframe": regimes_for_symbol,
                        "timeframe_count": len(regimes_for_symbol),
                    }
                    
                    results["primary_regimes"].append({
                        "symbol": symbol,
                        "primary_regime": most_common,
                        "confidence_score": agreement_pct,
                        "supporting_timeframes": regimes_for_symbol,
                    })
        
        log.info(f"[MTF] Computed agreement scores for {len(results['agreement_scores'])} symbols")
        
        return results
    
    except Exception as e:
        log.error(f"[MTF] Error computing multi-timeframe regimes: {e}")
        return results


if __name__ == "__main__":
    result = compute_multi_timeframe_regimes()
    print(f"Primary regimes: {len(result['primary_regimes'])}")
    print(f"Timeframe coverage: {list(result['timeframe_regimes'].keys())}")
    print(f"Agreement scores: {len(result['agreement_scores'])}")
