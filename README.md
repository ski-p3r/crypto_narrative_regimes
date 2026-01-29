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

## Setup Instructions (DigitalOcean Droplet)

### 1. System Access & Dependencies
SSH into your droplet and confirm sudo:
```bash
ssh <user>@<droplet_ip>
sudo -v
```

Install system packages:
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip postgresql postgresql-contrib
```

### 2. Database Setup
#### Create the database and user (Plain Postgres OK)
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
-- Optional: Enable TimescaleDB if installed
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
Create project directory and unzip the repo into it:
```bash
mkdir -p ~/sentiment && cd ~/sentiment
unzip /path/to/crypto_narrative_regimes.zip -d crypto_narrative_regimes
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

Export env vars for current shell (MVP):
```bash
export DB_URL=postgresql://crypto_admin:change_me_please@localhost:5432/crypto
export OPENAI_API_KEY=sk-...  # replace with your key
```

Verify Python deps import cleanly:
```bash
python -c "import ccxt, pandas, sqlalchemy, apscheduler, openai; print('ok')"
```

## Running the Pipeline

### Individual Scripts
You can run each stage manually for testing:

1. **Market Ingestion** (Spot-only via `binanceus`):
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
Recommendation: Run this in a `tmux` session or as a systemd service to keep it running in the background.

Quick tmux example:
```bash
tmux new -s crypto
source venv/bin/activate
export DB_URL=postgresql://crypto_admin:change_me_please@localhost:5432/crypto
export OPENAI_API_KEY=sk-...
python scheduler_mvp.py
# detach with Ctrl+b then d
```

Systemd unit (example):
Create `/etc/systemd/system/crypto-narrative.service` with:
```
[Unit]
Description=Crypto Narrative Pipeline
After=network-online.target postgresql.service

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i/sentiment/crypto_narrative_regimes
Environment=DB_URL=postgresql://crypto_admin:change_me_please@localhost:5432/crypto
Environment=OPENAI_API_KEY=sk-...
ExecStart=/home/%i/sentiment/crypto_narrative_regimes/venv/bin/python /home/%i/sentiment/crypto_narrative_regimes/scheduler_mvp.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
Reload and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-narrative.service
sudo systemctl start crypto-narrative.service
sudo journalctl -u crypto-narrative.service -f
```

## Caveats & Notes
- **US Market Only**: Currently configured to use `coinbase` (Coinbase Pro) and `binanceus` (if available) due to US restrictions.
- **Exchange Config**: Default `config.py` uses `EXCHANGES=["binanceus"]`. Add others only if region-compliant. Coinbase may use `USD` pairs rather than `USDT`.
- **Spot Regimes**: Regime classification is adapted for spot-only data (Price/Volume) as Futures data (OI/Funding) is often unavailable in the US.
- **Rate Limits**: The ingestion script respects rate limits, but if you run it too frequently, you might get 429s.
- **Logs**: Logs are printed to stdout/stderr. Redirect them to a file if needed (e.g., `python3 scheduler_mvp.py > pipeline.log 2>&1`).
