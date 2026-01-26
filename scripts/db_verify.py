import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv, find_dotenv


def get_db_url() -> str:
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url
    user = os.getenv("POSTGRES_USER", "crypto_admin")
    password = os.getenv("POSTGRES_PASSWORD", "change_me_please")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "crypto")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def main() -> int:
    # Load .env without requiring global exports
    load_dotenv(find_dotenv())
    db_url = get_db_url()
    print(f"Connecting to: {db_url}")
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names(schema="public")
            print("Tables:", tables)
            required = [
                "market_metrics",
                "narratives",
                "narrative_assets",
                "regimes",
                "regime_thresholds",
            ]
            missing = [t for t in required if t not in tables]
            if missing:
                print("Missing tables:", missing)
                return 2
            print("DB connectivity OK and schema present.")
            return 0
    except Exception as e:
        print("Connection failed:", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
