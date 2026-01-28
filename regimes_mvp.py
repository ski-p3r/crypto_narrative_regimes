import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine

from config import REGIME_CFG, MIN_OBS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("regimes")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)


def add_features_for_symbol(g: pd.DataFrame, window=24*7) -> pd.DataFrame:
    g = g.sort_values("ts").copy()
    if len(g) < MIN_OBS:
        return g

    # Only compute features for columns that have data
    # For spot-only, we care about price (for returns/z-score) and volume
    
    # Price z-score (using price itself is non-stationary, better to use returns or deviation from MA)
    # Here we'll use price z-score relative to moving average for simplicity in this MVP, 
    # or better: z-score of 1h returns? 
    # The prompt suggested "Price return (1h / 24h) -> z-score".
    # Let's compute z-score of price relative to its rolling mean (deviation) OR z-score of returns.
    # Existing code used z-score of raw values. Let's stick to that pattern for 'volume' and add 'price'.
    
    cols_to_process = ["volume", "price"] # Added price
    
    for col in cols_to_process:
        if col not in g.columns:
            continue
        # If column is all None/NaN, skip
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


def classify_regime(heat, heat_prev, price_z, vol_z):
    # Defaults
    regime = "SPOT_NEUTRAL"
    long_bias = 0.0
    risk_mult = 1.0
    confidence = 0.5

    heat = heat or 0.0
    heat_prev = heat_prev if heat_prev is not None else heat
    # heat_delta = heat - heat_prev # Unused for now
    price_z = price_z or 0.0
    vol_z = vol_z or 0.0

    cfg = REGIME_CFG

    # SPOT_IGNITION
    c = cfg["SPOT_IGNITION"]
    if heat >= c["heat_min"] and price_z >= c["price_z_min"] and vol_z >= c["vol_z_min"]:
        regime = "SPOT_IGNITION"
        long_bias = 0.6
        risk_mult = 1.3
        confidence = 0.7

    # SPOT_COOLING
    c = cfg["SPOT_COOLING"]
    if heat <= c["heat_max"] and price_z <= c["price_z_max"] and vol_z <= c["vol_z_max"]:
        regime = "SPOT_COOLING"
        long_bias = -0.2
        risk_mult = 0.8
        confidence = 0.6

    # SPOT_CHOP
    c = cfg["SPOT_CHOP"]
    if heat <= c["heat_max"] and abs(price_z) <= c["price_z_abs_max"] and vol_z <= c["vol_z_max"]:
        regime = "SPOT_CHOP"
        long_bias = 0.0
        risk_mult = 0.5
        confidence = 0.6

    return regime, long_bias, risk_mult, confidence


def compute_features_and_classify_regimes():
    # 1) Load last 7 days of metrics
    df = pd.read_sql("""
        SELECT *
        FROM market_metrics
        WHERE ts > NOW() - INTERVAL '7 days'
        ORDER BY symbol, ts
    """, engine)

    if df.empty:
        log.warning("[REG] No market data in last 7 days")
        return

    # 2) Add features per symbol
    df = df.groupby("symbol", group_keys=False).apply(
        lambda g: add_features_for_symbol(g, window=24*7)
    )

    if df.empty:
        log.warning("[REG] No rows after feature computation (likely too few obs)")
        return

    # 3) Load latest narrative links + narrative snapshot (last 24h)
    na = pd.read_sql("""
        SELECT DISTINCT ON (narrative_id, symbol) *
        FROM narrative_assets
        WHERE ts > NOW() - INTERVAL '1 day'
        ORDER BY narrative_id, symbol, ts DESC
    """, engine)

    narr = pd.read_sql("""
        SELECT DISTINCT ON (narrative_id) *
        FROM narratives
        WHERE ts > NOW() - INTERVAL '1 day'
        ORDER BY narrative_id, ts DESC
    """, engine)

    symbol_heat = {}
    symbol_coh = {}
    for _, row in na.iterrows():
        nid = row["narrative_id"]
        sym = row["symbol"]
        nar_row = narr[narr["narrative_id"] == nid]
        if nar_row.empty:
            continue
        heat = float(nar_row["heat_score"].iloc[0] or 0.0)
        coherence = float(nar_row["coherence_score"].iloc[0] or 0.0)
        prev = symbol_heat.get(sym, 0.0)
        if heat > prev:
            symbol_heat[sym] = heat
            symbol_coh[sym] = coherence

    latest_ts = df["ts"].max()
    last_rows = df[df["ts"] == latest_ts]

    out = []
    for _, row in last_rows.iterrows():
        sym = row["symbol"]
        heat = symbol_heat.get(sym, 0.0)
        coherence = symbol_coh.get(sym, 1.0)  # assume okay if missing

        if coherence < 0.3:
            regime, lb, rm, conf = "DATA_SUSPECT", 0.0, 0.0, 0.0
        else:
            regime, lb, rm, conf = classify_regime(
                heat=heat,
                heat_prev=None,
                price_z=row.get("price_z"),
                vol_z=row.get("volume_z"),
            )

        out.append({
            "ts": latest_ts,
            "symbol": sym,
            "regime": regime,
            "long_bias": lb,
            "risk_mult": rm,
            "confidence": conf,
            "meta_json": None,
        })

    if out:
        pd.DataFrame(out).to_sql(
            "regimes", engine, if_exists="append", index=False
        )
        log.info(f"[REG] {latest_ts} wrote {len(out)} regime rows")
    else:
        log.warning(f"[REG] {latest_ts} no regimes written")


if __name__ == "__main__":
    compute_features_and_classify_regimes()
