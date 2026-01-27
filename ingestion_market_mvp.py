import os
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone

import requests
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
    try:
        import ccxt  # lazy import to avoid hard dependency when unused
    except ImportError as e:
        raise RuntimeError(
            "ccxt is not installed. Install it or use Binance/CoinGecko paths"
        ) from e
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


def _get_active_exchanges() -> list:
    """Return exchanges to run, optionally filtered via EXCHANGES_ONLY env.

    EXCHANGES_ONLY can be a comma-separated list (e.g., "binance,bybit").
    Matching is case-insensitive and compared to configured EXCHANGES.
    """
    only = os.getenv("EXCHANGES_ONLY")
    if not only:
        return EXCHANGES
    wanted = {x.strip().lower() for x in only.split(",") if x.strip()}
    active = [ex for ex in EXCHANGES if ex.lower() in wanted]
    log.info(f"[CFG] Active exchanges: {active} (from EXCHANGES_ONLY)")
    return active


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
    # Mock mode: bypass live exchange calls if env flag set
    if os.getenv("INGEST_MOCK") in {"1", "true", "True"}:
        rows = []
        # Deterministic mock values per symbol/exchange
        base_prices = {"BTC/USDT": 42000.0, "ETH/USDT": 2200.0, "SOL/USDT": 95.0}
        vol_mult = {"binance": 1.0, "bybit": 0.8}
        for symbol in SYMBOLS:
            p = base_prices.get(symbol, 100.0)
            rows.append({
                "ts": ts,
                "symbol": symbol,
                "exchange": ex_name,
                "price": p,
                "ret_1h": 0.001,
                "oi": 1_000_000.0 * vol_mult.get(ex_name, 0.5),
                "funding": 0.0001,
                "long_liq_usd": 0.0,
                "short_liq_usd": 0.0,
                "volume": 10_000_000.0 * vol_mult.get(ex_name, 0.5),
            })
        log.info(f"[MKT] {ex_name} mock fetched {len(rows)} symbols")
        return rows

    # Use Binance Vision public data API (no proxies/VPN) to bypass geoblocks
    if ex_name.lower() == "binance":
        rows = []
        headers = {
            "Accept": "*/*",
            "User-Agent": "CryptoNarrative/1.0",
        }

        def _bn_sym(sym_ccxt: str) -> str:
            return sym_ccxt.replace("/", "").upper()

        for symbol in SYMBOLS:
            bn_symbol = _bn_sym(symbol)
            price = None
            volume_quote = None
            ret_1h = None
            try:
                r = requests.get(
                    "https://data-api.binance.vision/api/v3/ticker/price",
                    params={"symbol": bn_symbol},
                    headers=headers,
                    timeout=10,
                )
                if r.ok:
                    price = float(r.json().get("price"))
            except Exception as e:
                log.debug(f"[BINANCE] ticker price failed {bn_symbol}: {e}")

            try:
                r = requests.get(
                    "https://data-api.binance.vision/api/v3/klines",
                    params={"symbol": bn_symbol, "interval": "1h", "limit": 2},
                    headers=headers,
                    timeout=10,
                )
                if r.ok:
                    kl = r.json()
                    if kl and len(kl) >= 2:
                        prev_close = float(kl[-2][4])
                        last_close = float(kl[-1][4])
                        volume_quote = float(kl[-1][7]) if len(kl[-1]) > 7 else None
                        if prev_close:
                            ret_1h = (last_close - prev_close) / prev_close
                        # If ticker price missing, use last_close
                        if price is None:
                            price = last_close
            except Exception as e:
                log.debug(f"[BINANCE] klines failed {bn_symbol}: {e}")

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
                "volume": volume_quote,
            })
        log.info(f"[MKT] {ex_name} (vision) fetched {len(rows)} symbols")
        return rows

    # Replace Bybit with CoinGecko public API to avoid geoblocks
    if ex_name.lower() in {"bybit", "coingecko"}:
        rows = []
        headers = {
            "Accept": "*/*",
            "User-Agent": "CryptoNarrative/1.0",
        }

        def _cg_id(base: str) -> str:
            m = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            }
            return m.get(base.upper())

        # Build bulk request to CoinGecko for all supported symbols.
        # Group symbols by mapped vs currency: stable coins → usd for reliability.
        groups = {}
        for symbol in SYMBOLS:
            try:
                base, quote = symbol.split("/")
            except ValueError:
                log.debug(f"[CG] Invalid symbol format {symbol}")
                continue
            cid = _cg_id(base)
            if not cid:
                log.debug(f"[CG] Unsupported base {base} for {symbol}")
                continue
            vs = quote.lower()
            if vs in {"usdt", "usd", "busd", "usdc"}:
                vs = "usd"
            groups.setdefault(vs, []).append((symbol, cid))

        for quote, items in groups.items():
            ids = ",".join(cid for _, cid in items)
            try:
                r = requests.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": ids,
                        "vs_currencies": quote,
                        "include_24hr_vol": "true",
                        "include_24hr_change": "true",
                    },
                    headers=headers,
                    timeout=10,
                )
                data = r.json() if r.ok else {}
            except Exception as e:
                log.debug(f"[CG] request failed for {ids}/{quote}: {e}")
                data = {}

            for symbol, cid in items:
                entry = data.get(cid) or {}
                price = entry.get(quote)
                # Use 24h quote volume as a proxy for activity; ret_1h not available
                vol_key = f"{quote}_24h_vol"
                volume_quote = entry.get(vol_key)
                # Compute 1h return via market_chart RANGE using last 2h window
                ret_1h = None
                try:
                    to_epoch = int(ts.timestamp())
                    from_epoch = to_epoch - 7200
                    r2 = requests.get(
                        f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart/range",
                        params={
                            "vs_currency": quote,
                            "from": from_epoch,
                            "to": to_epoch,
                        },
                        headers=headers,
                        timeout=10,
                    )
                    if r2.ok:
                        mc = r2.json() or {}
                        prices = mc.get("prices") or []
                        # filter out nulls and require at least two points
                        prices = [p for p in prices if p and p[1] is not None]
                        if len(prices) >= 2:
                            prev_close = float(prices[-2][1])
                            last_close = float(prices[-1][1])
                            if prev_close:
                                ret_1h = (last_close - prev_close) / prev_close
                except Exception as e:
                    log.debug(f"[CG] market_chart range failed for {cid}/{quote}: {e}")
                rows.append({
                    "ts": ts,
                    "symbol": symbol,
                    "exchange": ex_name,
                    "price": float(price) if price is not None else None,
                    "ret_1h": ret_1h,
                    "oi": None,
                    "funding": None,
                    "long_liq_usd": 0.0,
                    "short_liq_usd": 0.0,
                    "volume": float(volume_quote) if volume_quote is not None else None,
                })

        log.info(f"[MKT] {ex_name} (coingecko) fetched {len(rows)} symbols")
        return rows

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

    for ex_name in _get_active_exchanges():
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
