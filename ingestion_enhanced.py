import os
from dotenv import load_dotenv
load_dotenv()
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import requests

import ccxt
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert

from config import EXCHANGES, SYMBOLS, LIQUIDATION_CFG, FUNDING_CFG

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("market_ingest_enhanced")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)

FAILURE_COUNT = defaultdict(int)
CIRCUIT_OPEN = defaultdict(bool)
CIRCUIT_OPENED_AT = {}
CIRCUIT_THRESHOLD = 3
COOLDOWN_SECONDS = 900

# Binance.US API endpoints
BINANCE_US_BASE = "https://api.binance.us"
BINANCE_US_FAPI = "https://fapi.binance.us"  # Futures API (if available)


def get_exchange(name: str):
    """Get CCXT exchange instance."""
    return getattr(ccxt, name)({"enableRateLimit": True})


def fetch_liquidation_data(ex_name: str) -> list:
    """
    Fetch liquidation data from Binance.US.
    Returns list of liquidation records for the last 1 hour.
    """
    try:
        rows = []
        ts = datetime.now(timezone.utc).replace(microsecond=0)
        
        # Try to fetch from Binance.US futures API
        # Note: Liquidations are typically on futures; spot market has no liquidations
        for symbol in SYMBOLS:
            try:
                # Convert to Binance format (BTC/USDT -> BTCUSDT)
                binance_symbol = symbol.replace("/", "")
                
                # Fetch recent liquidation data (if futures are available)
                # This is a best-effort call - Binance.US may have limited futures liquidity
                url = f"{BINANCE_US_FAPI}/v1/forceOrders"
                params = {
                    "symbol": binance_symbol,
                    "limit": 100,  # Last 100 liquidations
                }
                
                # Use requests to avoid CCXT overhead
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                liq_data = response.json()
                if isinstance(liq_data, list):
                    long_liq_total = 0.0
                    short_liq_total = 0.0
                    
                    # Sum up liquidations from the last hour
                    one_hour_ago = int((ts - timedelta(hours=1)).timestamp() * 1000)
                    
                    for liq in liq_data:
                        if int(liq.get("time", 0)) >= one_hour_ago:
                            qty = float(liq.get("origQty", 0))
                            price = float(liq.get("avgPrice", 0))
                            side = liq.get("side", "").upper()
                            
                            liq_usd = qty * price
                            
                            if side == "SELL":  # SELL = long liquidation
                                long_liq_total += liq_usd
                            elif side == "BUY":  # BUY = short liquidation
                                short_liq_total += liq_usd
                    
                    rows.append({
                        "ts": ts,
                        "symbol": symbol,
                        "exchange": ex_name,
                        "long_liq_usd": long_liq_total,
                        "short_liq_usd": short_liq_total,
                    })
                
            except Exception as e:
                log.debug(f"[LIQ] Could not fetch liquidations for {symbol}: {e}")
                # Futures may not be available on Binance.US for all symbols
                pass
        
        return rows
    
    except Exception as e:
        log.warning(f"[LIQ] Liquidation fetch error: {e}")
        return []


def fetch_funding_rates(ex_name: str) -> dict:
    """
    Fetch funding rates from Binance.US (if available).
    Returns dict of symbol -> funding_rate.
    """
    try:
        funding_rates = {}
        
        for symbol in SYMBOLS:
            try:
                binance_symbol = symbol.replace("/", "")
                
                # Try to fetch funding rate from futures API
                url = f"{BINANCE_US_FAPI}/v1/fundingRate"
                params = {
                    "symbol": binance_symbol,
                    "limit": 1,
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    funding_rates[symbol] = float(data[0].get("fundingRate", 0.0))
                
            except Exception as e:
                log.debug(f"[FUND] Could not fetch funding for {symbol}: {e}")
                pass
        
        return funding_rates
    
    except Exception as e:
        log.warning(f"[FUND] Funding rate fetch error: {e}")
        return {}


def fetch_for_exchange(ex_name: str, ts):
    """
    Fetch spot market data, liquidations, and funding rates.
    """
    ex = get_exchange(ex_name)
    rows = []
    
    for symbol in SYMBOLS:
        try:
            # Ticker for price and 24h context
            ticker = ex.fetch_ticker(symbol)
            price = ticker.get("last") or ticker.get("close")
            
            # Compute 1h return using OHLCV
            ret_1h = None
            try:
                ohlcv = ex.fetch_ohlcv(symbol, timeframe="1h", limit=2)
                if ohlcv and len(ohlcv) >= 2:
                    prev_close = float(ohlcv[-2][4])
                    last_close = float(ohlcv[-1][4])
                    if prev_close != 0:
                        ret_1h = (last_close - prev_close) / prev_close
            except Exception:
                pass
            
            # Volume
            vol_quote = ticker.get("quoteVolume")
            if vol_quote is None:
                try:
                    if ohlcv and len(ohlcv) >= 1 and price is not None:
                        base_vol = float(ohlcv[-1][5])
                        vol_quote = base_vol * float(price)
                except Exception:
                    vol_quote = None
            
            rows.append({
                "ts": ts,
                "symbol": symbol,
                "exchange": ex_name,
                "price": price,
                "ret_1h": ret_1h,
                "oi": None,
                "funding": None,
                "long_liq_usd": 0.0,
                "short_liq_usd": 0.0,
                "volume": vol_quote,
            })
        
        except Exception as e:
            log.warning(f"[MKT] Error fetching {symbol}: {e}")
    
    return rows


def upsert_rows(rows):
    """Upsert market metrics to database."""
    if not rows:
        return

    meta = MetaData()
    market_table = Table("market_metrics", meta, autoload_with=engine)

    with engine.begin() as conn:
        for row in rows:
            stmt = insert(market_table).values(**row)
            update_cols = {
                "price": stmt.excluded.price,
                "ret_1h": stmt.excluded.ret_1h,
                "oi": stmt.excluded.oi,
                "funding": stmt.excluded.funding,
                "long_liq_usd": stmt.excluded.long_liq_usd,
                "short_liq_usd": stmt.excluded.short_liq_usd,
                "volume": stmt.excluded.volume,
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=[market_table.c.ts, market_table.c.symbol, market_table.c.exchange],
                set_=update_cols,
            )
            conn.execute(stmt)


def run_ingestion_cycle():
    """Main ingestion cycle: fetch spot data + liquidations + funding rates."""
    ts = datetime.now(timezone.utc).replace(microsecond=0)
    all_rows = []

    for ex_name in EXCHANGES:
        if CIRCUIT_OPEN[ex_name]:
            opened_at = CIRCUIT_OPENED_AT.get(ex_name)
            if opened_at and datetime.now(timezone.utc) - opened_at > timedelta(seconds=COOLDOWN_SECONDS):
                log.info(f"[MKT] {ex_name} circuit cooldown elapsed; attempting to close")
                CIRCUIT_OPEN[ex_name] = False
            else:
                log.warning(f"[MKT] {ex_name} circuit OPEN, skipping this cycle")
                continue

        try:
            # Fetch spot market data
            rows = fetch_for_exchange(ex_name, ts)
            
            # Fetch liquidation data
            liq_rows = fetch_liquidation_data(ex_name)
            
            # Merge liquidation data into rows
            liq_map = {(r["symbol"], r["exchange"]): r for r in liq_rows}
            for row in rows:
                key = (row["symbol"], row["exchange"])
                if key in liq_map:
                    row["long_liq_usd"] = liq_map[key]["long_liq_usd"]
                    row["short_liq_usd"] = liq_map[key]["short_liq_usd"]
            
            # Fetch funding rates
            funding_rates = fetch_funding_rates(ex_name)
            for row in rows:
                if row["symbol"] in funding_rates:
                    row["funding"] = funding_rates[row["symbol"]]
            
            all_rows.extend(rows)
            FAILURE_COUNT[ex_name] = 0
            if ex_name in CIRCUIT_OPENED_AT:
                CIRCUIT_OPENED_AT.pop(ex_name, None)
        
        except Exception as e:
            FAILURE_COUNT[ex_name] += 1
            log.warning(f"[MKT] {ex_name} failure {FAILURE_COUNT[ex_name]}: {e}")
            if FAILURE_COUNT[ex_name] >= CIRCUIT_THRESHOLD:
                CIRCUIT_OPEN[ex_name] = True
                CIRCUIT_OPENED_AT[ex_name] = datetime.now(timezone.utc)
                log.error(f"[CRIT] Circuit breaker OPEN for {ex_name}")

    upsert_rows(all_rows)
    log.info(f"[MKT] {ts} inserted {len(all_rows)} rows")


if __name__ == "__main__":
    while True:
        run_ingestion_cycle()
        time.sleep(3600)  # Run every hour
