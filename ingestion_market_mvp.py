import os
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone

import ccxt
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv, find_dotenv

from config import EXCHANGES, SYMBOLS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("market_ingest")


def _compose_db_url() -> str:
    load_dotenv(find_dotenv())
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url
    user = os.getenv("POSTGRES_USER", "crypto_admin")
    password = os.getenv("POSTGRES_PASSWORD", "change_me_please")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "crypto")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(_compose_db_url(), pool_pre_ping=True)

FAILURE_COUNT = defaultdict(int)
CIRCUIT_OPEN = defaultdict(bool)
CIRCUIT_THRESHOLD = 3  # after 3 consecutive failures, open circuit


def get_exchange(name: str):
    cfg = {"enableRateLimit": True, "options": {"defaultType": "spot"}}
    # Use HTTP(S) proxies if provided via environment variables
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY")
    if http_proxy or https_proxy:
        cfg["proxies"] = {
            "http": http_proxy or https_proxy,
            "https": https_proxy or http_proxy,
        }
        log.info(f"[NET] Using proxies for {name}")
    return getattr(ccxt, name)(cfg)


def _safe_fetch_ohlcv_return_1h(ex, symbol, price):
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe="1h", limit=2)
        if ohlcv and len(ohlcv) >= 2:
            prev_close = ohlcv[-2][4]
            last_close = ohlcv[-1][4]
            if prev_close:
                return (last_close - prev_close) / prev_close
    except Exception as e:
        log.debug(f"[RET1H] {ex.id} {symbol} ohlcv failed: {e}")
    # fallback: ticker-based open (may be 24h)
    try:
        return None if price is None else None
    except Exception:
        return None


def _safe_fetch_funding_rate(ex, symbol):
    try:
        if getattr(ex, "has", {}).get("fetchFundingRate"):
            fr = ex.fetch_funding_rate(symbol)
            return fr.get("fundingRate")
    except Exception as e:
        log.debug(f"[FUND] {ex.id} {symbol} funding failed: {e}")
    return None


def _safe_fetch_open_interest(ex, symbol):
    try:
        if getattr(ex, "has", {}).get("fetchOpenInterest"):
            oi = ex.fetch_open_interest(symbol)
            # ccxt returns various fields depending on exchange
            return (
                oi.get("openInterestAmount")
                or oi.get("openInterestValue")
                or oi.get("openInterest")
            )
    except Exception as e:
        log.debug(f"[OI] {ex.id} {symbol} OI failed: {e}")
    return None


def fetch_for_exchange(ex_name: str, ts):
    ex = get_exchange(ex_name)
    rows = []
    for symbol in SYMBOLS:
        ticker = ex.fetch_ticker(symbol)

        price = ticker.get("last") or ticker.get("close")
        volume = ticker.get("quoteVolume") or ticker.get("baseVolume")
        ret_1h = _safe_fetch_ohlcv_return_1h(ex, symbol, price)
        funding = _safe_fetch_funding_rate(ex, symbol)
        oi = _safe_fetch_open_interest(ex, symbol)

        rows.append({
            "ts": ts,
            "symbol": symbol,
            "exchange": ex_name,
            "price": price,
            "ret_1h": ret_1h,
            "oi": oi,
            "funding": funding,
            "long_liq_usd": 0.0,
            "short_liq_usd": 0.0,
            "volume": volume,
        })
    log.info(f"[MKT] {ex_name} fetched {len(rows)} symbols")
    return rows


def upsert_rows(rows):
    if not rows:
        return

    meta = MetaData()
    market_table = Table("market_metrics", meta, autoload_with=engine)

    with engine.begin() as conn:
        for row in rows:
            stmt = insert(market_table).values(**row)
            update_fields = {k: row[k] for k in row.keys() if k not in ("ts", "symbol", "exchange")}
            stmt = stmt.on_conflict_do_update(
                index_elements=["ts", "symbol", "exchange"],
                set_=update_fields,
            )
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
            log.info(f"[MKT] {ex_name} success")
        except Exception as e:
            FAILURE_COUNT[ex_name] += 1
            log.warning(f"[MKT] {ex_name} failure {FAILURE_COUNT[ex_name]}: {e}")
            if FAILURE_COUNT[ex_name] >= CIRCUIT_THRESHOLD:
                CIRCUIT_OPEN[ex_name] = True
                log.error(f"[CRIT] Circuit breaker OPEN for {ex_name}")

    upsert_rows(all_rows)
    log.info(f"[MKT] {ts} upserted {len(all_rows)} rows")


if __name__ == "__main__":
    # Single cycle run for MVP; use scheduler_mvp.py for periodic runs
    run_ingestion_cycle()
