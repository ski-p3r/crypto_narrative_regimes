import os
import sys
import argparse
from typing import List, Dict, Any
from datetime import datetime, timezone

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


def _parse_dt(s: str):
    if not s:
        return None
    s = s.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        try:
            # epoch seconds
            return datetime.utcfromtimestamp(float(s)).replace(tzinfo=timezone.utc)
        except Exception as e:
            raise ValueError(f"Invalid datetime format: {s}") from e


def fetch_rows(
    engine,
    exchanges: List[str] = None,
    symbols: List[str] = None,
    start: str = None,
    end: str = None,
    min_price: float = None,
    max_price: float = None,
    min_ret1h: float = None,
    max_ret1h: float = None,
    min_volume: float = None,
    max_volume: float = None,
    order_by: str = "ts",
    desc: bool = True,
    limit: int = 50,
    offset: int = 0,
):
    sql = (
        "SELECT ts, exchange, symbol, price, ret_1h, oi, funding, "
        "long_liq_usd, short_liq_usd, volume "
        "FROM market_metrics WHERE 1=1 "
    )
    params: Dict[str, Any] = {}

    if exchanges:
        sql += "AND exchange = ANY(:exchanges) "
        params["exchanges"] = exchanges
    if symbols:
        sql += "AND symbol = ANY(:symbols) "
        params["symbols"] = symbols

    if start:
        dt = _parse_dt(start)
        sql += "AND ts >= :start "
        params["start"] = dt
    if end:
        dt = _parse_dt(end)
        sql += "AND ts <= :end "
        params["end"] = dt

    if min_price is not None:
        sql += "AND price >= :min_price "
        params["min_price"] = float(min_price)
    if max_price is not None:
        sql += "AND price <= :max_price "
        params["max_price"] = float(max_price)

    if min_ret1h is not None:
        sql += "AND ret_1h >= :min_ret1h "
        params["min_ret1h"] = float(min_ret1h)
    if max_ret1h is not None:
        sql += "AND ret_1h <= :max_ret1h "
        params["max_ret1h"] = float(max_ret1h)

    if min_volume is not None:
        sql += "AND volume >= :min_volume "
        params["min_volume"] = float(min_volume)
    if max_volume is not None:
        sql += "AND volume <= :max_volume "
        params["max_volume"] = float(max_volume)

    # order by whitelist to avoid SQL injection
    allowed_order = {
        "ts",
        "exchange",
        "symbol",
        "price",
        "ret_1h",
        "volume",
    }
    ob = order_by if order_by in allowed_order else "ts"
    direction = "DESC" if desc else "ASC"
    sql += f"ORDER BY {ob} {direction} LIMIT :limit OFFSET :offset"
    params["limit"] = int(limit)
    params["offset"] = int(offset)

    with engine.connect() as conn:
        result = conn.execute(text(sql), params).mappings().all()
        return [dict(r) for r in result]


def try_tabulate(rows: List[Dict[str, Any]]):
    try:
        from tabulate import tabulate  # optional dependency
        headers = [
            "ts",
            "exchange",
            "symbol",
            "price",
            "ret_1h",
            "oi",
            "funding",
            "long_liq_usd",
            "short_liq_usd",
            "volume",
        ]
        table = [
            [
                str(r.get("ts")),
                r.get("exchange"),
                r.get("symbol"),
                r.get("price"),
                r.get("ret_1h"),
                r.get("oi"),
                r.get("funding"),
                r.get("long_liq_usd"),
                r.get("short_liq_usd"),
                r.get("volume"),
            ]
            for r in rows
        ]
        print(tabulate(table, headers=headers, tablefmt="github"))
        return True
    except Exception:
        return False


def print_table(rows: List[Dict[str, Any]]):
    if not rows:
        print("No rows found.")
        return
    if try_tabulate(rows):
        return
    # Fallback simple table formatter
    headers = [
        "ts",
        "exchange",
        "symbol",
        "price",
        "ret_1h",
        "oi",
        "funding",
        "long_liq_usd",
        "short_liq_usd",
        "volume",
    ]
    # compute column widths
    def _cell(r, k):
        v = r.get(k)
        return "" if v is None else str(v)
    widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            widths[h] = max(widths[h], len(_cell(r, h)))
    # print header
    header_line = " | ".join(h.ljust(widths[h]) for h in headers)
    sep_line = "-+-".join("-" * widths[h] for h in headers)
    print(header_line)
    print(sep_line)
    # print rows
    for r in rows:
        line = " | ".join(_cell(r, h).ljust(widths[h]) for h in headers)
        print(line)


def print_csv(rows: List[Dict[str, Any]]):
    import csv
    headers = [
        "ts",
        "exchange",
        "symbol",
        "price",
        "ret_1h",
        "oi",
        "funding",
        "long_liq_usd",
        "short_liq_usd",
        "volume",
    ]
    w = csv.writer(sys.stdout)
    w.writerow(headers)
    for r in rows:
        w.writerow([
            r.get("ts"),
            r.get("exchange"),
            r.get("symbol"),
            r.get("price"),
            r.get("ret_1h"),
            r.get("oi"),
            r.get("funding"),
            r.get("long_liq_usd"),
            r.get("short_liq_usd"),
            r.get("volume"),
        ])


def main():
    parser = argparse.ArgumentParser(
        description="View rows from market_metrics with rich filters and output formats"
    )
    parser.add_argument(
        "--exchanges",
        help="Comma-separated exchanges (e.g., binance,bybit)",
        default=None,
    )
    parser.add_argument(
        "--symbols",
        help="Comma-separated symbols (e.g., BTC/USDT,ETH/USDT)",
        default=None,
    )
    parser.add_argument("--start", help="Start time (ISO 8601 or epoch)", default=None)
    parser.add_argument("--end", help="End time (ISO 8601 or epoch)", default=None)
    parser.add_argument("--min-price", type=float, default=None)
    parser.add_argument("--max-price", type=float, default=None)
    parser.add_argument("--min-ret1h", type=float, default=None)
    parser.add_argument("--max-ret1h", type=float, default=None)
    parser.add_argument("--min-volume", type=float, default=None)
    parser.add_argument("--max-volume", type=float, default=None)
    parser.add_argument("--order-by", default="ts")
    parser.add_argument("--asc", action="store_true", help="Sort ascending")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument(
        "--output",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format",
    )
    args = parser.parse_args()

    engine = create_engine(compose_db_url(), pool_pre_ping=True)
    exchanges = [x.strip() for x in args.exchanges.split(",") if x.strip()] if args.exchanges else None
    symbols = [x.strip() for x in args.symbols.split(",") if x.strip()] if args.symbols else None
    rows = fetch_rows(
        engine,
        exchanges=exchanges,
        symbols=symbols,
        start=args.start,
        end=args.end,
        min_price=args.min_price,
        max_price=args.max_price,
        min_ret1h=args.min_ret1h,
        max_ret1h=args.max_ret1h,
        min_volume=args.min_volume,
        max_volume=args.max_volume,
        order_by=args.order_by,
        desc=not args.asc,
        limit=args.limit,
        offset=args.offset,
    )
    if args.output == "table":
        print_table(rows)
    elif args.output == "csv":
        print_csv(rows)
    else:
        import json
        print(json.dumps(rows, default=str, indent=2))


if __name__ == "__main__":
    main()
