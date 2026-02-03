import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timezone

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from config import VOLATILITY_CFG

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("volatility_regime")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)


def compute_volatility_metrics():
    """
    Compute multi-faceted volatility analysis:
    1. Realized volatility (returns-based)
    2. Volatility clustering (GARCH-inspired)
    3. Volatility regimes (STABLE/HIGH_VOL/EXPLOSIVE)
    4. IV spread (if available)
    """
    try:
        log.info("[VOL] Computing volatility metrics...")
        
        # Fetch last 7 days of returns data
        df = pd.read_sql("""
            SELECT ts, symbol, ret_1h, price
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '7 days'
            AND ret_1h IS NOT NULL
            AND price IS NOT NULL
            ORDER BY symbol, ts
        """, engine)
        
        if df.empty:
            log.warning("[VOL] No return data available")
            return {}
        
        df['ts'] = pd.to_datetime(df['ts'])
        
        window = VOLATILITY_CFG['window']
        stable_threshold = VOLATILITY_CFG['stable_threshold']
        high_vol_threshold = VOLATILITY_CFG['high_vol_threshold']
        explosive_threshold = VOLATILITY_CFG['explosive_threshold']
        
        results = {
            "volatility_regimes": [],
            "volatility_clustering": [],
            "vol_term_structure": [],
            "timestamp": datetime.now(timezone.utc),
        }
        
        for symbol in df['symbol'].unique():
            sym_data = df[df['symbol'] == symbol].sort_values('ts').copy()
            
            if len(sym_data) < 10:
                continue
            
            # Realized volatility (rolling std of returns)
            sym_data['realized_vol'] = sym_data['ret_1h'].rolling(window=window, min_periods=5).std()
            
            # Volatility of volatility (clustering indicator)
            sym_data['vol_of_vol'] = sym_data['realized_vol'].rolling(window=12, min_periods=3).std()
            
            # Squared returns (for GARCH-like analysis)
            sym_data['ret_squared'] = sym_data['ret_1h'] ** 2
            sym_data['avg_ret_squared'] = sym_data['ret_squared'].rolling(window=window, min_periods=5).mean()
            
            # Latest values
            latest_row = sym_data.iloc[-1]
            
            if pd.notna(latest_row['realized_vol']):
                realized_vol = latest_row['realized_vol']
                
                # Classify regime
                if realized_vol <= stable_threshold:
                    regime = "STABLE"
                    risk_mult = 0.7
                elif realized_vol <= high_vol_threshold:
                    regime = "HIGH_VOL"
                    risk_mult = 1.2
                elif realized_vol <= explosive_threshold:
                    regime = "EXPLOSIVE"
                    risk_mult = 1.8
                else:
                    regime = "EXTREME"
                    risk_mult = 2.5
                
                # Clustering score (high clustering = more predictable)
                clustering_score = 1.0 - min(latest_row['vol_of_vol'] / (realized_vol + 1e-8), 1.0)
                
                results["volatility_regimes"].append({
                    "symbol": symbol,
                    "ts": latest_row['ts'],
                    "regime": regime,
                    "realized_volatility": float(realized_vol),
                    "price": float(latest_row['price']),
                    "risk_multiplier": risk_mult,
                    "clustering_score": float(clustering_score),
                })
                
                # Detect volatility clustering patterns
                if pd.notna(latest_row['vol_of_vol']) and latest_row['vol_of_vol'] > realized_vol * 0.3:
                    results["volatility_clustering"].append({
                        "symbol": symbol,
                        "ts": latest_row['ts'],
                        "clustering_type": "HIGH_CLUSTERING",
                        "vol_of_vol": float(latest_row['vol_of_vol']),
                        "realized_vol": float(realized_vol),
                        "predictability": "MODERATE",  # Clustering makes future vol somewhat predictable
                    })
        
        # Term structure: volatility at different horizons
        for symbol in df['symbol'].unique():
            sym_data = df[df['symbol'] == symbol].sort_values('ts').copy()
            
            term_struct = {
                "symbol": symbol,
                "ts": datetime.now(timezone.utc),
                "horizons": {}
            }
            
            for hours in [1, 4, 24]:
                if len(sym_data) >= hours:
                    vol_at_horizon = sym_data['ret_1h'].tail(hours).std()
                    # Annualize (approximate: hourly -> daily via sqrt)
                    annualized = vol_at_horizon * np.sqrt(24 * 365)
                    term_struct["horizons"][f"{hours}h"] = float(annualized)
            
            if term_struct["horizons"]:
                results["vol_term_structure"].append(term_struct)
        
        log.info(f"[VOL] Classified {len(results['volatility_regimes'])} symbols")
        log.info(f"[VOL] Detected {len(results['volatility_clustering'])} clustering events")
        
        return results
    
    except Exception as e:
        log.error(f"[VOL] Error computing volatility: {e}")
        return {}


def analyze_volatility_persistence():
    """
    Analyze how volatility persists over time.
    High persistence = trades benefit from vol mean reversion.
    Low persistence = vol regime changes quickly.
    """
    try:
        df = pd.read_sql("""
            SELECT ts, symbol, ret_1h
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '14 days'
            AND ret_1h IS NOT NULL
            ORDER BY symbol, ts
        """, engine)
        
        if df.empty:
            return {}
        
        df['ts'] = pd.to_datetime(df['ts'])
        
        results = []
        
        for symbol in df['symbol'].unique():
            sym_data = df[df['symbol'] == symbol].sort_values('ts').copy()
            
            if len(sym_data) < 50:
                continue
            
            # Compute rolling 24h volatility
            sym_data['vol_24h'] = sym_data['ret_1h'].rolling(window=24, min_periods=10).std()
            
            # Autocorrelation of volatility (persistence measure)
            vol_series = sym_data['vol_24h'].dropna()
            
            if len(vol_series) >= 30:
                # Simple autocorrelation at lag 24
                lag_24_autocorr = vol_series.autocorr(lag=24)
                
                # Half-life of volatility persistence (approximate)
                if lag_24_autocorr > 0:
                    half_life_days = 24 / (-np.log(lag_24_autocorr) / np.log(2)) if lag_24_autocorr < 1 else float('inf')
                else:
                    half_life_days = 1.0
                
                persistence = "HIGH" if lag_24_autocorr > 0.5 else ("MEDIUM" if lag_24_autocorr > 0.2 else "LOW")
                
                results.append({
                    "symbol": symbol,
                    "autocorr_lag24": float(lag_24_autocorr),
                    "persistence": persistence,
                    "estimated_half_life_days": float(min(half_life_days, 30)),  # Cap at 30
                    "mean_reversion_potential": "HIGH" if persistence == "HIGH" else "LOW",
                })
        
        return {
            "volatility_persistence": results,
            "timestamp": datetime.now(timezone.utc),
        }
    
    except Exception as e:
        log.error(f"[VOL] Error analyzing persistence: {e}")
        return {}


def compute_volatility_features():
    """
    Compute all volatility-based features.
    """
    log.info("[VOL] Computing all volatility features...")
    
    regimes = compute_volatility_metrics()
    persistence = analyze_volatility_persistence()
    
    combined = {
        **regimes,
        **persistence,
    }
    
    return combined


if __name__ == "__main__":
    result = compute_volatility_features()
    print(f"Volatility regimes: {len(result.get('volatility_regimes', []))}")
    print(f"Clustering events: {len(result.get('volatility_clustering', []))}")
    print(f"Persistence data: {len(result.get('volatility_persistence', []))}")
