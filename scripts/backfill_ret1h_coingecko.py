import os
import time
import argparse
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text


def compose_db_url() -> str:
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


ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
}


def symbol_to_id(symbol: str):
    try:
        base, quote = symbol.split("/")
    except ValueError:
        return None, None
    cid = ID_MAP.get(base.upper())
    vs = quote.lower()
    if vs in {"usdt", "usd", "busd", "usdc"}:
        vs = "usd"
    return cid, vs


def compute_ret1h_range(cid: str, vs: str, ts: datetime, session: requests.Session = None):
    if not cid or not vs:
        return None
    s = session or requests.Session()
    headers = {"Accept": "*/*", "User-Agent": "CryptoNarrative/1.0"}
    to_epoch = int(ts.timestamp())
    from_epoch = to_epoch - 7200
    try:
        r = s.get(
            f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart/range",
            params={"vs_currency": vs, "from": from_epoch, "to": to_epoch},
            headers=headers,
            timeout=10,
        )
        if not r.ok:
            return None
        mc = r.json() or {}
        prices = mc.get("prices") or []
        prices = [p for p in prices if p and p[1] is not None]
        if len(prices) < 2:
            return None
        prev_close = float(prices[-2][1])
        last_close = float(prices[-1][1])
        if prev_close:
            return (last_close - prev_close) / prev_close
        return None
    except Exception:
        return None


def backfill(engine, hours: int, exchanges: list, symbols: list, delay: float):
    start_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    params = {"start": start_dt, "ex": exchanges}
    sym_clause = ""
    if symbols:
        params["symbols"] = symbols
        sym_clause = "AND symbol = ANY(:symbols)"

    select_sql = text(
        f"""
        SELECT ts, exchange, symbol
        FROM market_metrics
        WHERE exchange = ANY(:ex)
          AND ret_1h IS NULL
          AND ts >= :start
          {sym_clause}
        ORDER BY ts DESC
        """
    )

    update_sql = text(
        """
        UPDATE market_metrics
        SET ret_1h = :ret1h
        WHERE ts = :ts AND exchange = :exchange AND symbol = :symbol
        """
    )

    s = requests.Session()
    with engine.begin() as conn:
        rows = conn.execute(select_sql, params).mappings().all()
        print(f"[BACKFILL] Found {len(rows)} rows to update")
        for r in rows:
            ts = r["ts"]
            exchange = r["exchange"]
            symbol = r["symbol"]
            cid, vs = symbol_to_id(symbol)
            ret1h = compute_ret1h_range(cid, vs, ts, session=s)
            if ret1h is None:
                continue
            conn.execute(
                update_sql,
                {"ret1h": float(ret1h), "ts": ts, "exchange": exchange, "symbol": symbol},
            )
            time.sleep(delay)
    print("[BACKFILL] Done")


def main():
    parser = argparse.ArgumentParser(description="Backfill ret_1h for Bybit/CoinGecko rows")
    parser.add_argument("--hours", type=int, default=12, help="Look back this many hours")
    parser.add_argument("--exchanges", default="bybit", help="Comma-separated exchanges to backfill")
    parser.add_argument("--symbols", default=None, help="Comma-separated symbols to restrict")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between API calls (seconds)")
    args = parser.parse_args()

    exchanges = [x.strip() for x in args.exchanges.split(",") if x.strip()]
    symbols = [x.strip() for x in args.symbols.split(",") if x and x.strip()] if args.symbols else None

    engine = create_engine(compose_db_url(), pool_pre_ping=True)
    backfill(engine, hours=args.hours, exchanges=exchanges, symbols=symbols, delay=args.delay)


if __name__ == "__main__":
    main()
