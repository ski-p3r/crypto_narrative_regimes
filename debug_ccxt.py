import ccxt
import logging

logging.basicConfig(level=logging.INFO)

try:
    ex = ccxt.binanceus({"enableRateLimit": True})
    print("Exchange loaded:", ex.id)
    ticker = ex.fetch_ticker("BTC/USDT")
    print("Ticker fetched:", ticker)
except Exception as e:
    print("Error:", e)
