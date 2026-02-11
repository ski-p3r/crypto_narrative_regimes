import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timezone

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from config import FUNDING_CFG

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("funding_anomaly")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)


def detect_funding_anomalies():
    """
    Detect anomalies in funding rates:
    1. Z-score based anomaly (extreme funding levels)
    2. Reversal signals (funding changing direction sharply)
    3. Divergence between exchange pairs (if applicable)
    """
    try:
        # Fetch last 7 days of funding data
        df = pd.read_sql("""
            SELECT ts, symbol, funding
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '7 days'
            AND funding IS NOT NULL
            ORDER BY symbol, ts
        """, engine)
        
        if df.empty:
            log.debug("[FUND] No funding data available")
            return []
        
        df['ts'] = pd.to_datetime(df['ts'])
        
        anomalies = []
        z_threshold = FUNDING_CFG['anomaly_z_threshold']
        reversal_threshold = FUNDING_CFG['reversal_threshold']
        
        for symbol in df['symbol'].unique():
            sym_data = df[df['symbol'] == symbol].sort_values('ts').copy()
            
            if len(sym_data) < 10:
                continue
            
            # Calculate z-scores
            sym_data['funding_mean'] = sym_data['funding'].rolling(window=24, min_periods=5).mean()
            sym_data['funding_std'] = sym_data['funding'].rolling(window=24, min_periods=5).std()
            
            sym_data['funding_z'] = (sym_data['funding'] - sym_data['funding_mean']) / (sym_data['funding_std'] + 1e-8)
            
            # Calculate funding rate changes
            sym_data['funding_change'] = sym_data['funding'].diff()
            sym_data['abs_funding_change'] = sym_data['funding_change'].abs()
            
            # Detect anomalies
            for idx, row in sym_data.iterrows():
                anomaly_score = 0.0
                anomaly_reasons = []
                
                # Z-score anomaly
                if pd.notna(row['funding_z']) and abs(row['funding_z']) > z_threshold:
                    anomaly_score += abs(row['funding_z']) / z_threshold
                    anomaly_reasons.append(f"Z-score anomaly: {row['funding_z']:.2f}σ")
                
                # Reversal signal
                if pd.notna(row['funding_change']) and abs(row['funding_change']) > reversal_threshold:
                    anomaly_score += 1.0
                    direction = "↑" if row['funding_change'] > 0 else "↓"
                    anomaly_reasons.append(f"Reversal {direction}: {row['funding_change']:.4f}")
                
                # High volatility in funding
                if len(sym_data) >= 24:
                    recent_volatility = sym_data['funding'].tail(24).std()
                    if recent_volatility > 0.02:
                        anomaly_score += 0.5
                        anomaly_reasons.append(f"High volatility: {recent_volatility:.4f}")
                
                # Only flag if there's a real anomaly
                if anomaly_score > 0 and len(anomaly_reasons) > 0:
                    anomalies.append({
                        "ts": row['ts'],
                        "symbol": symbol,
                        "event_type": "FUNDING_ANOMALY",
                        "funding_rate": float(row['funding']),
                        "funding_z_score": float(row['funding_z']) if pd.notna(row['funding_z']) else None,
                        "funding_change": float(row['funding_change']) if pd.notna(row['funding_change']) else None,
                        "anomaly_score": float(anomaly_score),
                        "reasons": anomaly_reasons,
                    })
        
        return anomalies
    
    except Exception as e:
        log.error(f"[FUND] Error detecting anomalies: {e}")
        return []


def detect_reversal_signals():
    """
    Identify potential reversal signals based on funding rate extremes
    and sudden direction changes.
    """
    try:
        df = pd.read_sql("""
            SELECT ts, symbol, funding, price
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '7 days'
            AND funding IS NOT NULL
            AND price IS NOT NULL
            ORDER BY symbol, ts
        """, engine)
        
        if df.empty:
            return []
        
        df['ts'] = pd.to_datetime(df['ts'])
        
        reversals = []
        
        for symbol in df['symbol'].unique():
            sym_data = df[df['symbol'] == symbol].sort_values('ts').copy()
            
            if len(sym_data) < 20:
                continue
            
            # Calculate funding statistics
            sym_data['funding_mean'] = sym_data['funding'].rolling(window=24, min_periods=5).mean()
            sym_data['funding_std'] = sym_data['funding'].rolling(window=24, min_periods=5).std()
            sym_data['funding_pct_change'] = sym_data['funding'].pct_change()
            
            # Recent funding trends
            recent_funding = sym_data['funding'].tail(4).values
            
            for idx, row in sym_data.tail(10).iterrows():
                # Signal: extreme funding followed by reversal
                if len(recent_funding) >= 3:
                    prev_trend = np.sign(recent_funding[-1] - recent_funding[-3])
                    curr_trend = np.sign(row['funding'] - recent_funding[-1])
                    
                    # Trend reversal detected
                    if prev_trend != 0 and curr_trend != 0 and prev_trend != curr_trend:
                        extreme_level = "EXTREMELY_HIGH" if row['funding'] > 0.001 else ("EXTREMELY_LOW" if row['funding'] < -0.001 else "MODERATE")
                        
                        reversals.append({
                            "ts": row['ts'],
                            "symbol": symbol,
                            "event_type": "FUNDING_REVERSAL",
                            "funding_rate": float(row['funding']),
                            "extreme_level": extreme_level,
                            "price": float(row['price']),
                            "reversal_confidence": 0.7,  # Medium confidence for trend reversals
                        })
        
        return reversals
    
    except Exception as e:
        log.error(f"[FUND] Error detecting reversals: {e}")
        return []


def compute_funding_metrics():
    """
    Compute funding rate anomalies and reversal signals.
    """
    log.info("[FUND] Computing funding rate metrics...")
    
    anomalies = detect_funding_anomalies()
    reversals = detect_reversal_signals()
    
    if anomalies:
        log.info(f"[FUND] Detected {len(anomalies)} funding anomalies")
    
    if reversals:
        log.info(f"[FUND] Detected {len(reversals)} reversal signals")
    
    return {
        "funding_anomalies": anomalies,
        "reversal_signals": reversals,
        "timestamp": datetime.now(timezone.utc),
    }


if __name__ == "__main__":
    result = compute_funding_metrics()
    print(f"Anomalies: {len(result['funding_anomalies'])}")
    print(f"Reversals: {len(result['reversal_signals'])}")
