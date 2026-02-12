import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bk_paper_trader")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)

CONF_LONG_REGIME = os.getenv("PAPER_LONG_REGIME", "SPOT_IGNITION")
CONF_SHORT_REGIME = os.getenv("PAPER_SHORT_REGIME", "SPOT_COOLING")
CONF_THRESHOLD = float(os.getenv("PAPER_CONF_THRESHOLD", "0.7"))
TRADE_SIZE = float(os.getenv("PAPER_TRADE_SIZE", "1.0"))


def _latest_regimes() -> pd.DataFrame:
    q = text(
        """
        SELECT DISTINCT ON (symbol)
               ts, symbol, regime, confidence
        FROM regimes
        ORDER BY symbol, ts DESC
        """
    )
    with engine.begin() as conn:
        df = pd.read_sql(q, conn)
    return df


def _latest_prices() -> pd.DataFrame:
    q = text(
        """
        SELECT DISTINCT ON (symbol)
               ts, symbol, price
        FROM market_metrics
        WHERE price IS NOT NULL
        ORDER BY symbol, ts DESC
        """
    )
    with engine.begin() as conn:
        df = pd.read_sql(q, conn)
    return df


def _open_trade(symbol: str, side: str, price: float, regime: str, confidence: float):
    ts = datetime.now(timezone.utc).replace(microsecond=0)
    row = {
        "ts": ts,
        "symbol": symbol,
        "side": side,
        "size": TRADE_SIZE,
        "entry_price": price,
        "exit_price": None,
        "pnl": None,
        "status": "OPEN",
        "reason": f"regime={regime}",
        "regime": regime,
        "confidence": confidence,
    }
    with engine.begin() as conn:
        cols = ", ".join(row.keys())
        vals = ", ".join([":" + k for k in row.keys()])
        conn.execute(text(f"INSERT INTO paper_trades ({cols}) VALUES ({vals})"), row)
    log.info(f"[PAPER] OPEN {side} {symbol} @ {price:.4f} (conf={confidence:.2f})")


def _close_trade(open_row: dict, exit_price: float, reason: str):
    pnl = None
    if open_row["side"] == "LONG" and open_row.get("entry_price") is not None:
        pnl = (exit_price - open_row["entry_price"]) * open_row.get("size", TRADE_SIZE)
    elif open_row["side"] == "SHORT" and open_row.get("entry_price") is not None:
        pnl = (open_row["entry_price"] - exit_price) * open_row.get("size", TRADE_SIZE)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE paper_trades
                   SET exit_price = :exit_price,
                       pnl = :pnl,
                       status = 'CLOSED',
                       reason = :reason
                 WHERE id = :id
                """
            ),
            {
                "exit_price": exit_price,
                "pnl": pnl,
                "reason": reason,
                "id": open_row["id"],
            },
        )
    log.info(f"[PAPER] CLOSE {open_row['side']} {open_row['symbol']} @ {exit_price:.4f} (pnl={pnl if pnl is not None else 'NA'})")


def _get_open_trade(symbol: str) -> dict | None:
    with engine.begin() as conn:
        res = conn.execute(
            text(
                """
                SELECT * FROM paper_trades
                 WHERE symbol = :symbol AND status = 'OPEN'
                 ORDER BY ts DESC
                 LIMIT 1
                """
            ),
            {"symbol": symbol},
        ).mappings().fetchone()
    return dict(res) if res else None


def run():
    reg = _latest_regimes()
    if reg.empty:
        log.info("[PAPER] No regimes available")
        return {"opened": [], "closed": []}

    prices = _latest_prices()
    price_map = {r["symbol"]: float(r["price"]) for _, r in prices.iterrows()}

    opened = []
    closed = []

    for _, r in reg.iterrows():
        symbol = r["symbol"]
        regime = str(r["regime"]) if r["regime"] is not None else ""
        confidence = float(r["confidence"]) if r["confidence"] is not None else 0.0
        price = price_map.get(symbol)
        if price is None:
            continue

        open_trade = _get_open_trade(symbol)

        # Decide open/close based on regime
        want_long = regime == CONF_LONG_REGIME and confidence >= CONF_THRESHOLD
        want_short = regime == CONF_SHORT_REGIME and confidence >= CONF_THRESHOLD

        if open_trade is None:
            if want_long:
                _open_trade(symbol, "LONG", price, regime, confidence)
                opened.append({"symbol": symbol, "side": "LONG", "price": price})
            elif want_short:
                _open_trade(symbol, "SHORT", price, regime, confidence)
                opened.append({"symbol": symbol, "side": "SHORT", "price": price})
        else:
            # Close if opposite signal or low confidence
            if open_trade["side"] == "LONG" and (want_short or not want_long):
                _close_trade(open_trade, price, reason=f"signal_change regime={regime}")
                closed.append({"symbol": symbol, "side": "LONG", "price": price})
            elif open_trade["side"] == "SHORT" and (want_long or not want_short):
                _close_trade(open_trade, price, reason=f"signal_change regime={regime}")
                closed.append({"symbol": symbol, "side": "SHORT", "price": price})

    return {"opened": opened, "closed": closed}


if __name__ == "__main__":
    result = run()
    print(result)
