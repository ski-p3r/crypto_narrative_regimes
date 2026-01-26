# Crypto Narrative Regimes – Database Setup (Docker)

This repo includes a Docker-only Postgres (TimescaleDB) setup accessible via both localhost and the droplet IP.

## Prerequisites
- Ubuntu/Debian on droplet
- `sudo` privileges
- Docker Engine and Compose plugin

### Install Docker & Compose
```sh
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
docker compose version
```

Optional firewall rule to allow external access:
```sh
sudo ufw allow 5432/tcp
```

## Configure DB credentials
Create your `.env` from the example and set a strong `POSTGRES_PASSWORD`:
```env
cp .env.example .env
# then edit .env and change POSTGRES_PASSWORD
```

Example values (edit these in `.env`):
```env
POSTGRES_DB=crypto
POSTGRES_USER=crypto_admin
POSTGRES_PASSWORD=<STRONG_PASSWORD>
```

## Configure OpenAI API key
Set your OpenAI key via `.env` (preferred):
```sh
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...
```
Or per-run without global export:
```sh
OPENAI_API_KEY=sk-... python scripts/config_verify.py
```

Verify configuration and secrets:
```sh
python scripts/config_verify.py
```
The script imports `config.py`, validates exchanges/symbols/regimes, and checks that `OPENAI_API_KEY` is present.

## Start the database
From the repo root:
```sh
docker compose up -d
docker compose ps
```
On first start, `schema.sql` runs in the `crypto` DB and creates all tables.

## Set DB_URL
Export the connection string for apps and scripts:
```sh
export DB_URL="postgresql+psycopg2://crypto_admin:<STRONG_PASSWORD>@127.0.0.1:5432/crypto"
```
Use the droplet IP instead of `127.0.0.1` when connecting remotely.

## Verify connectivity from Python
Create and activate your venv (see Task 1), then:
```sh
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/db_verify.py
```
Expected output includes the list of tables and the message `DB connectivity OK and schema present.`

### Verify without exporting DB_URL globally
`scripts/db_verify.py` automatically loads `.env` using python-dotenv and constructs the connection string if `DB_URL` is not set. Simply run:
```sh
python scripts/db_verify.py
```
To override host/port per-invocation without a global export:
```sh
DB_HOST=127.0.0.1 DB_PORT=5432 python scripts/db_verify.py
```

## Troubleshooting Connectivity

If the Python script or your app can’t connect to the database, try these checks:

1) Check container health and logs
```sh
docker compose ps
docker compose logs -f db
```

2) Test connectivity with `psql` from the host
```sh
# Install client if missing
sudo apt install -y postgresql-client

# List tables
psql -h 127.0.0.1 -U crypto_admin -d crypto -c '\dt'
```

3) Confirm credentials match `.env`
- Ensure `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in `.env` are correct.
- If you change `POSTGRES_PASSWORD` after first run, recreate the container:
```sh
docker compose down
docker compose up -d
```
Note: `docker compose down -v` will also delete data; only use `-v` if you intend to reset the database.

4) Verify port and firewall
```sh
# Port listening on 0.0.0.0:5432
ss -ltnp | grep 5432

# UFW allows inbound 5432/tcp
sudo ufw status
sudo ufw allow 5432/tcp
```
For remote clients, connect using the droplet IP (e.g., `psql -h <droplet_ip> ...`) and ensure cloud firewall/security group allows 5432/tcp.

5) Run the verification with explicit envs (no global export)
```sh
POSTGRES_USER=crypto_admin POSTGRES_PASSWORD=<STRONG_PASSWORD> DB_HOST=127.0.0.1 DB_PORT=5432 POSTGRES_DB=crypto \
python scripts/db_verify.py
```

6) Ensure schema applied and hypertables exist
```sh
# List tables from inside the container
docker compose exec -T db psql -U crypto_admin -d crypto -c '\dt'

# If some tables are missing, apply the fix script
docker compose exec -T db psql -U crypto_admin -d crypto -v ON_ERROR_STOP=1 -f /dev/stdin < scripts/db_fix_narratives.sql
```
The fix script adjusts the `narratives` unique index to include `ts` and creates missing hypertables.

## Migrate Schema (one-liner)
Run this anytime to ensure the schema is applied/updated (idempotent):
```sh
docker compose exec -T db psql -U crypto_admin -d crypto -v ON_ERROR_STOP=1 -f /dev/stdin < scripts/db_migrate.sql
```
This script creates extensions, tables, compliant indexes, and hypertables with `IF NOT EXISTS`, so it’s safe to re-run.

## Run Market Ingestion (Task 4)
Run a single ingestion cycle to write rows into `market_metrics`:
```sh
source .venv/bin/activate
python ingestion_market_mvp.py
```
What it does:
- Initializes ccxt clients for each exchange in `config.EXCHANGES` (Binance, Bybit).
- For each symbol in `config.SYMBOLS` (BTC/USDT, ETH/USDT, SOL/USDT), fetches:
	- Current price (`ticker.last`/`close`)
	- Hourly return (from 1h OHLCV)
	- Funding rate (if supported by the exchange)
	- Open interest (if supported)
	- Volume (quote/base volume)
	- Liquidations default to 0.0 (not widely available via ccxt)
- Normalizes to the `market_metrics` schema and upserts on `(ts, symbol, exchange)`.

Check results:
```sh
docker compose exec -T db psql -U crypto_admin -d crypto -c "SELECT ts, symbol, exchange, price, ret_1h, volume FROM market_metrics ORDER BY ts DESC LIMIT 9;"
```

If you need periodic ingestion, use:
```sh
source .venv/bin/activate
python scheduler_mvp.py
```
This runs hourly and includes narratives and regimes steps too.

### If you see 451/403 geo-block errors
Some exchanges (Binance, Bybit) restrict access by country/region. Route requests via an allowed region using HTTP(S) proxies.

Set per-run (no global export):
```sh
HTTP_PROXY=http://<proxy_host>:<port> \
HTTPS_PROXY=http://<proxy_host>:<port> \
python ingestion_market_mvp.py
```
Or add to `.env`:
```env
# .env
HTTP_PROXY=http://<proxy_host>:<port>
HTTPS_PROXY=http://<proxy_host>:<port>
```
The script auto-loads `.env` and configures ccxt with these proxies.

### Alternatively: mock mode (no network)
If you only need to verify the pipeline writes rows, enable mock mode:
```sh
echo "INGEST_MOCK=1" >> .env
source .venv/bin/activate
python ingestion_market_mvp.py
```
This inserts deterministic rows for BTC/USDT, ETH/USDT, and SOL/USDT across Binance and Bybit without calling exchanges.




