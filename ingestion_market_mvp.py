import os
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone

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
CIRCUIT_THRESHOLD = 3  # after 3 consecutive failures, open circuit


def get_exchange(name: str):
    return getattr(ccxt, name)({"enableRateLimit": True})


def fetch_for_exchange(ex_name: str, ts):
    ex = get_exchange(ex_name)
    rows = []
    for symbol in SYMBOLS:
        ticker = ex.fetch_ticker(symbol)

        price = ticker.get("last") or ticker.get("close")
        ret_1h = None
        if ticker.get("open"):
            try:
                ret_1h = (price - ticker["open"]) / ticker["open"]
            except ZeroDivisionError:
                ret_1h = None

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
            "volume": ticker.get("quoteVolume"),
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
            stmt = stmt.on_conflict_do_nothing()
            conn.execute(stmt)


def run_ingestion_cycle():
    ts = datetime.now(timezone.utc).replace(microsecond=0)
    all_rows = []

    for ex_name in EXCHANGES:
        if CIRCUIT_OPEN[ex_name]:
            log.warning(f"[MKT] {ex_name} circuit OPEN, skipping this cycle")
            continue

        try:
            rows = fetch_for_exchange(ex_name, ts)
            all_rows.extend(rows)
            FAILURE_COUNT[ex_name] = 0
        except Exception as e:
            FAILURE_COUNT[ex_name] += 1
            log.warning(f"[MKT] {ex_name} failure {FAILURE_COUNT[ex_name]}: {e}")
            if FAILURE_COUNT[ex_name] >= CIRCUIT_THRESHOLD:
                CIRCUIT_OPEN[ex_name] = True
                log.error(f"[CRIT] Circuit breaker OPEN for {ex_name}")

    upsert_rows(all_rows)
    log.info(f"[MKT] {ts} inserted {len(all_rows)} rows")


if __name__ == "__main__":
    while True:
        run_ingestion_cycle()
        time.sleep(3600)  # or 900 for every 15 minutes
