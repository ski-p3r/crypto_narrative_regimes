import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timezone, timedelta

import pandas as pd
from sqlalchemy import create_engine

from config import LIQUIDATION_CFG

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("liquidation_cascade")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)


def detect_cascade_events():
    """
    Detect liquidation cascade events based on liquidation velocity.
    A cascade event occurs when:
    1. Total liquidations exceed threshold
    2. Liquidation velocity (USD/hour) exceeds critical threshold
    3. One-sided liquidations (long or short dominate)
    """
    try:
        # Fetch last 24 hours of liquidation data
        df = pd.read_sql("""
            SELECT ts, symbol, long_liq_usd, short_liq_usd
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '24 hours'
            ORDER BY symbol, ts
        """, engine)
        
        if df.empty:
            log.warning("[CASCADE] No liquidation data available")
            return []
        
        df['ts'] = pd.to_datetime(df['ts'])
        df['total_liq'] = df['long_liq_usd'] + df['short_liq_usd']
        df['liq_ratio'] = df['long_liq_usd'] / (df['total_liq'] + 1e-8)  # Ratio of long liq
        
        events = []
        window_hours = LIQUIDATION_CFG['velocity_window']
        critical_velocity = LIQUIDATION_CFG['critical_velocity']
        cascade_threshold = LIQUIDATION_CFG['cascade_threshold_usd']
        
        for symbol in df['symbol'].unique():
            sym_data = df[df['symbol'] == symbol].sort_values('ts')
            
            # Calculate rolling liquidation sums and velocity
            sym_data = sym_data.copy()
            sym_data['time_index'] = range(len(sym_data))
            
            # For each row, look back window_hours
            for idx, row in sym_data.iterrows():
                current_time = row['ts']
                window_start = current_time - timedelta(hours=window_hours)
                
                window_data = sym_data[sym_data['ts'] >= window_start]
                
                if len(window_data) < 2:
                    continue
                
                total_long_liq = window_data['long_liq_usd'].sum()
                total_short_liq = window_data['short_liq_usd'].sum()
                total_liq = total_long_liq + total_short_liq
                
                if total_liq < cascade_threshold:
                    continue
                
                # Calculate velocity (USD per hour)
                time_elapsed = (current_time - window_data['ts'].min()).total_seconds() / 3600
                if time_elapsed < 0.1:
                    continue
                
                velocity = total_liq / time_elapsed
                
                # Determine if this is a cascade event
                if velocity >= critical_velocity:
                    # One-sided cascade?
                    long_ratio = total_long_liq / (total_liq + 1e-8)
                    short_ratio = total_short_liq / (total_liq + 1e-8)
                    
                    side_bias = "LONG" if long_ratio > 0.6 else ("SHORT" if short_ratio > 0.6 else "BALANCED")
                    
                    events.append({
                        "ts": current_time,
                        "symbol": symbol,
                        "event_type": "CASCADE_DETECTED",
                        "total_liquidated_usd": total_liq,
                        "long_liq_usd": total_long_liq,
                        "short_liq_usd": total_short_liq,
                        "velocity_usd_per_hour": velocity,
                        "side_bias": side_bias,
                        "severity": min(velocity / critical_velocity, 5.0),  # 1.0 = threshold, 5.0 = max
                        "window_hours": window_hours,
                    })
        
        return events
    
    except Exception as e:
        log.error(f"[CASCADE] Error detecting cascades: {e}")
        return []


def identify_liquidation_support_zones():
    """
    Identify price levels where liquidations are clustered.
    These are critical support/resistance zones where cascades are likely.
    """
    try:
        # Fetch last 7 days of data with prices and liquidations
        df = pd.read_sql("""
            SELECT ts, symbol, price, long_liq_usd, short_liq_usd
            FROM market_metrics
            WHERE ts > NOW() - INTERVAL '7 days'
            AND price IS NOT NULL
            ORDER BY symbol, ts
        """, engine)
        
        if df.empty:
            return []
        
        zones = []
        
        for symbol in df['symbol'].unique():
            sym_data = df[df['symbol'] == symbol].sort_values('price').copy()
            
            if len(sym_data) < 10:
                continue
            
            # Create price bins (10 bins across price range)
            sym_data['price_bin'] = pd.cut(sym_data['price'], bins=10)
            
            # Sum liquidations per bin
            bin_stats = sym_data.groupby('price_bin', observed=True).agg({
                'long_liq_usd': 'sum',
                'short_liq_usd': 'sum',
                'price': 'mean',
                'ts': 'count'
            }).rename(columns={'ts': 'observations'})
            
            bin_stats['total_liq'] = bin_stats['long_liq_usd'] + bin_stats['short_liq_usd']
            bin_stats = bin_stats.sort_values('total_liq', ascending=False)
            
            # Top 3 zones
            for i, (idx, row) in enumerate(bin_stats.head(3).iterrows()):
                zones.append({
                    "symbol": symbol,
                    "price_level": float(row['price']),
                    "total_liquidations_usd": float(row['total_liq']),
                    "long_liq_usd": float(row['long_liq_usd']),
                    "short_liq_usd": float(row['short_liq_usd']),
                    "risk_rank": i + 1,
                    "zone_strength": min(float(row['total_liq']) / 1000000, 5.0),  # Normalized 0-5
                })
        
        return zones
    
    except Exception as e:
        log.error(f"[CASCADE] Error identifying zones: {e}")
        return []


def compute_liquidation_metrics():
    """
    Compute cascade events and liquidation zones.
    Store results for dashboard/alerts.
    """
    log.info("[CASCADE] Computing liquidation cascade metrics...")
    
    events = detect_cascade_events()
    zones = identify_liquidation_support_zones()
    
    if events:
        log.info(f"[CASCADE] Detected {len(events)} cascade events")
        for event in events:
            log.info(f"  {event['symbol']}: {event['event_type']} "
                   f"velocity={event['velocity_usd_per_hour']:.0f} USD/h, "
                   f"side={event['side_bias']}, severity={event['severity']:.2f}")
    
    if zones:
        log.info(f"[CASCADE] Identified {len(zones)} liquidation zones")
    
    return {
        "cascade_events": events,
        "liquidation_zones": zones,
        "timestamp": datetime.now(timezone.utc),
    }


if __name__ == "__main__":
    result = compute_liquidation_metrics()
    print(f"Events: {len(result['cascade_events'])}")
    print(f"Zones: {len(result['liquidation_zones'])}")
