import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv, find_dotenv


def check_openai_env() -> bool:
    # Load .env if present (no global export required)
    load_dotenv(find_dotenv())
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Missing OPENAI_API_KEY in environment/.env")
        return False
    # Verify library import without making network calls
    try:
        from openai import OpenAI  # type: ignore
        _ = OpenAI()
        print("OpenAI client initialized.")
        return True
    except Exception as e:
        print("OpenAI library initialization failed:", e)
        return False


def check_config() -> bool:
    try:
        # Ensure project root (parent of scripts/) is in sys.path
        project_root = Path(__file__).resolve().parents[1]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        import config  # local module at project root
    except Exception as e:
        print("Importing config.py failed:", e)
        return False

    print("EXCHANGES:", config.EXCHANGES)
    print("SYMBOLS:", config.SYMBOLS)

    # Validate exchanges and symbols
    expected_exchanges = {"binance", "bybit"}
    if set(x.lower() for x in config.EXCHANGES) != expected_exchanges:
        print("Unexpected EXCHANGES; expected Binance, Bybit")
        return False

    expected_symbols = {"BTC/USDT", "ETH/USDT", "SOL/USDT"}
    if set(config.SYMBOLS) != expected_symbols:
        print("Unexpected SYMBOLS; expected BTC/USDT, ETH/USDT, SOL/USDT")
        return False

    # Basic regime config checks
    required_regimes = {
        "OVERHEATED",
        "IGNITION",
        "FUNDING_RESET_IGNITION",
        "PANIC",
        "COILED",
    }
    if not required_regimes.issubset(set(config.REGIME_CFG.keys())):
        print("Missing regime keys in REGIME_CFG")
        return False

    print("config.py loaded and validated.")
    return True


def main() -> int:
    ok_config = check_config()
    ok_openai = check_openai_env()
    if ok_config and ok_openai:
        print("Configuration and secrets verified.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
