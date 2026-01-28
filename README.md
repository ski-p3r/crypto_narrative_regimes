# Crypto Narrative & Regime Analysis Pipeline

This project implements an automated pipeline to:
1. Ingest crypto market data (Spot only for US market).
2. Generate AI-driven narratives using OpenAI.
3. Classify market regimes (e.g., SPOT_IGNITION, SPOT_COOLING).

## Prerequisites
- Ubuntu 20.04+ (or similar Linux environment)
- Python 3.10+
- PostgreSQL 14+ (TimescaleDB recommended but optional)
- OpenAI API Key

## Setup Instructions

### 1. System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip postgresql postgresql-contrib
```

### 2. Database Setup
#### Option A: Using Docker (Recommended for Testing)
If you have Docker installed, you can spin up the database easily:
```bash
# Start Postgres
docker-compose up -d

# The schema.sql is automatically applied on the first run.
# If you need to re-apply it manually:
# docker exec -i crypto_db psql -U crypto_admin -d crypto < schema.sql
```

#### Option B: Manual Setup
Create the database and user:
```bash
sudo -u postgres psql
```
Inside the `psql` shell:
```sql
CREATE DATABASE crypto;
CREATE USER crypto_admin WITH ENCRYPTED PASSWORD 'change_me_please';
GRANT ALL PRIVILEGES ON DATABASE crypto TO crypto_admin;
\c crypto
-- Enable TimescaleDB if installed, otherwise skip
-- CREATE EXTENSION IF NOT EXISTS timescaledb;
```
Exit `psql` (`\q`).

Initialize the schema:
```bash
# Set DB_URL temporarily for the schema script if needed, or just use psql
export DB_URL="postgresql://crypto_admin:change_me_please@localhost:5432/crypto"
psql $DB_URL -f schema.sql
```

### 3. Project Setup
Clone/Unzip the repo and enter the directory:
```bash
cd crypto_narrative_regimes
```

Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Edit `.env` and set your credentials:
```bash
nano .env
```
Content:
```ini
DB_URL=postgresql://myuser:mypassword@localhost:5432/crypto
OPENAI_API_KEY=sk-proj-...
```

## Running the Pipeline

### Individual Scripts
You can run each stage manually for testing:

1. **Market Ingestion** (Fetches data from Coinbase/Binance.US):
   ```bash
   python3 ingestion_market_mvp.py
   ```
   *Check logs for `[MKT]` messages.*

2. **Narrative Generation** (Calls OpenAI):
   ```bash
   python3 narrative_stream_openai_v4.py
   ```
   *Check logs for `[NARR]` messages.*

3. **Regime Classification** (Computes features and regimes):
   ```bash
   python3 regimes_mvp.py
   ```
   *Check logs for `[REG]` messages.*

### Scheduler (Production)
To run the full pipeline continuously (every hour):
```bash
python3 scheduler_mvp.py
```
*Recommendation: Run this in a `tmux` session or as a systemd service to keep it running in the background.*

## Caveats & Notes
- **US Market Only**: Currently configured to use `coinbase` (Coinbase Pro) and `binanceus` (if available) due to US restrictions.
- **Spot Regimes**: Regime classification is adapted for spot-only data (Price/Volume) as Futures data (OI/Funding) is unavailable in the US.
- **Rate Limits**: The ingestion script respects rate limits, but if you run it too frequently, you might get 429s.
- **Logs**: Logs are printed to stdout/stderr. Redirect them to a file if needed (e.g., `python3 scheduler_mvp.py > pipeline.log 2>&1`).
