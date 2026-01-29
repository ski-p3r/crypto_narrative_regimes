import os
from dotenv import load_dotenv
load_dotenv()
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import ccxt
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert

from config import EXCHANGES, SYMBOLS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("market_ingest")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)

FAILURE_COUNT = defaultdict(int)
CIRCUIT_OPEN = defaultdict(bool)
CIRCUIT_OPENED_AT = {}
CIRCUIT_THRESHOLD = 3  # after 3 consecutive failures, open circuit
COOLDOWN_SECONDS = 900  # try to auto-close circuit after 15 minutes


def get_exchange(name: str):
    return getattr(ccxt, name)({"enableRateLimit": True})


def fetch_for_exchange(ex_name: str, ts):
    ex = get_exchange(ex_name)
    rows = []
    for symbol in SYMBOLS:
        # Ticker for price and 24h context
        ticker = ex.fetch_ticker(symbol)

        # Price
        price = ticker.get("last") or ticker.get("close")

        # Compute 1h return using OHLCV last two 1h candles if available
        ret_1h = None
        try:
            ohlcv = ex.fetch_ohlcv(symbol, timeframe="1h", limit=2)
            if ohlcv and len(ohlcv) >= 2:
                prev_close = float(ohlcv[-2][4])
                last_close = float(ohlcv[-1][4])
                if prev_close != 0:
                    ret_1h = (last_close - prev_close) / prev_close
        except Exception:
            # Keep ret_1h as None on OHLCV errors
            pass

        # Volume approximation: prefer ticker quoteVolume if present; otherwise base_vol * price
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
    return rows


def upsert_rows(rows):
    if not rows:
        return

    meta = MetaData()
    market_table = Table("market_metrics", meta, autoload_with=engine)

    with engine.begin() as conn:
        for row in rows:
            stmt = insert(market_table).values(**row)
            # Upsert by primary key (ts, symbol, exchange)
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
            rows = fetch_for_exchange(ex_name, ts)
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
        time.sleep(3600)  # or 900 for every 15 minutes
