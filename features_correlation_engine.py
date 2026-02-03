import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timezone

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from config import CORRELATION_CFG

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("correlation_engine")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)


def compute_pairwise_correlations():
    """
    Compute pairwise correlations between primary assets (BTC, ETH, SOL).
    Identify when correlations break down (divergence signals).
    """
    try:
        window_hours = CORRELATION_CFG['window']
        primary_assets = CORRELATION_CFG['primary_assets']
        correlation_break_threshold = CORRELATION_CFG['correlation_break_threshold']
        
        # Fetch price data for primary assets
        df = pd.read_sql(f"""
            SELECT ts, symbol, price, ret_1h
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '{window_hours} hours'
            AND symbol = ANY(ARRAY{primary_assets}::text[])
            ORDER BY ts, symbol
        """, engine)
        
        if df.empty:
            log.debug("[CORR] No price data available")
            return {}
        
        df['ts'] = pd.to_datetime(df['ts'])
        
        # Pivot to get one column per asset
        price_pivot = df.pivot(index='ts', columns='symbol', values='price')
        ret_pivot = df.pivot(index='ts', columns='symbol', values='ret_1h')
        
        results = {
            "price_correlation_matrix": {},
            "return_correlation_matrix": {},
            "correlation_changes": [],
            "divergence_events": [],
            "timestamp": datetime.now(timezone.utc),
        }
        
        # Compute correlations
        if not price_pivot.empty and len(price_pivot) >= 10:
            price_corr = price_pivot.corr()
            results["price_correlation_matrix"] = price_corr.to_dict()
            log.info(f"[CORR] Price correlations computed: {price_corr.shape}")
        
        if not ret_pivot.empty and len(ret_pivot) >= 10:
            ret_corr = ret_pivot.corr()
            results["return_correlation_matrix"] = ret_corr.to_dict()
            log.info(f"[CORR] Return correlations computed: {ret_corr.shape}")
        
        # Detect correlation changes (rolling windows)
        if len(price_pivot) >= 48:
            lookback_periods = 24  # 1 day of hourly data
            recent_corr = price_pivot.tail(lookback_periods).corr()
            early_corr = price_pivot.iloc[-48:-24].corr()
            
            # Compare correlations
            corr_change = (recent_corr - early_corr).abs()
            
            for asset_i in primary_assets:
                for asset_j in primary_assets:
                    if asset_i >= asset_j:
                        continue
                    
                    if asset_i in corr_change.index and asset_j in corr_change.columns:
                        change = float(corr_change.loc[asset_i, asset_j])
                        recent = float(recent_corr.loc[asset_i, asset_j]) if not pd.isna(recent_corr.loc[asset_i, asset_j]) else 0.5
                        
                        if abs(change) > 0.2:  # Significant change
                            results["correlation_changes"].append({
                                "asset_pair": f"{asset_i}/{asset_j}",
                                "correlation_change": change,
                                "recent_correlation": recent,
                                "significance": "HIGH" if change > 0.3 else "MEDIUM",
                            })
        
        # Detect divergence events
        if len(ret_pivot) >= 20:
            for asset_i in primary_assets:
                for asset_j in primary_assets:
                    if asset_i >= asset_j:
                        continue
                    
                    if asset_i in ret_pivot.columns and asset_j in ret_pivot.columns:
                        recent_returns_i = ret_pivot[asset_i].tail(24).dropna()
                        recent_returns_j = ret_pivot[asset_j].tail(24).dropna()
                        
                        # Simple divergence: opposite movements
                        if len(recent_returns_i) >= 5 and len(recent_returns_j) >= 5:
                            corr_returns = recent_returns_i.corr(recent_returns_j)
                            
                            # Negative correlation = divergence
                            if corr_returns < -correlation_break_threshold:
                                results["divergence_events"].append({
                                    "ts": datetime.now(timezone.utc),
                                    "asset_pair": f"{asset_i}/{asset_j}",
                                    "event_type": "CORRELATION_BREAK",
                                    "return_correlation": float(corr_returns),
                                    "divergence_strength": abs(float(corr_returns)),
                                    "signal": "POTENTIAL_PAIR_TRADE",
                                })
        
        return results
    
    except Exception as e:
        log.error(f"[CORR] Error computing correlations: {e}")
        return {}


def identify_leading_assets():
    """
    Identify which assets lead regime shifts.
    Usually BTC leads, but sometimes ETH or SOL can lead altseason.
    """
    try:
        window_hours = CORRELATION_CFG['window']
        primary_assets = CORRELATION_CFG['primary_assets']
        
        # Fetch price changes
        df = pd.read_sql(f"""
            SELECT ts, symbol, price, ret_1h
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '{window_hours} hours'
            AND symbol = ANY(ARRAY{primary_assets}::text[])
            ORDER BY ts, symbol
        """, engine)
        
        if df.empty:
            return {}
        
        df['ts'] = pd.to_datetime(df['ts'])
        
        results = {
            "leading_indicators": [],
            "lagging_assets": [],
            "timestamp": datetime.now(timezone.utc),
        }
        
        # For each asset, compute correlation with future 1h returns
        for target_asset in primary_assets:
            target_returns = df[df['symbol'] == target_asset].set_index('ts')['ret_1h'].sort_index()
            
            lead_scores = {}
            
            for source_asset in primary_assets:
                if source_asset == target_asset:
                    continue
                
                source_returns = df[df['symbol'] == source_asset].set_index('ts')['ret_1h'].sort_index()
                
                # Shift source forward (leading indicator)
                source_shifted = source_returns.shift(-1)
                
                # Align dates and compute correlation
                aligned = pd.concat([source_shifted, target_returns], axis=1).dropna()
                
                if len(aligned) >= 20:
                    corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
                    lead_scores[source_asset] = corr if not pd.isna(corr) else 0.0
            
            # Identify if this asset is typically a leader
            if lead_scores:
                avg_lead_score = np.mean(list(lead_scores.values()))
                
                if avg_lead_score > 0.3:
                    results["leading_indicators"].append({
                        "target_asset": target_asset,
                        "leading_assets": lead_scores,
                        "average_lead_correlation": float(avg_lead_score),
                        "role": "LEADER",
                    })
                else:
                    results["lagging_assets"].append({
                        "asset": target_asset,
                        "average_lead_score": float(avg_lead_score),
                        "role": "FOLLOWER",
                    })
        
        return results
    
    except Exception as e:
        log.error(f"[CORR] Error identifying leaders: {e}")
        return {}


def compute_correlation_metrics():
    """
    Compute all correlation-based features.
    """
    log.info("[CORR] Computing correlation metrics...")
    
    pairwise_corr = compute_pairwise_correlations()
    leading_assets = identify_leading_assets()
    
    combined_results = {
        **pairwise_corr,
        "leading_analysis": leading_assets,
    }
    
    if pairwise_corr.get("divergence_events"):
        log.info(f"[CORR] Detected {len(pairwise_corr['divergence_events'])} divergence events")
    
    return combined_results


if __name__ == "__main__":
    result = compute_correlation_metrics()
    print(f"Divergence events: {len(result.get('divergence_events', []))}")
    print(f"Leading indicators: {len(result.get('leading_analysis', {}).get('leading_indicators', []))}")
