# Crypto Narrative Regimes (Droplet Runbook)

End-to-end hourly pipeline on a DigitalOcean droplet (US-only):
- Ingest spot data from `binanceus` for `BTC/USDT`, `ETH/USDT`, `SOL/USDT`
- Generate narratives via OpenAI and store narrative heat
- Classify regimes from market + narrative features
- Store everything in Postgres

**.env (auto-loaded by scripts)**
```
DB_URL=postgresql://crypto_admin:change_me_please@localhost:5432/crypto
OPENAI_API_KEY=sk-REPLACE_ME
```

**Initialize DB**
```zsh
sudo -u postgres psql <<'SQL'
CREATE DATABASE crypto;
CREATE USER crypto_admin WITH ENCRYPTED PASSWORD 'change_me_please';
GRANT ALL PRIVILEGES ON DATABASE crypto TO crypto_admin;
SQL
psql "postgresql://crypto_admin:change_me_please@localhost:5432/crypto" -f schema.sql
```

**Local Runs (venv)**
```zsh
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# One-offs
python ingestion_market_mvp.py
python narrative_stream_openai_v4.py
python regimes_mvp.py
# Hourly scheduler
python scheduler_mvp.py
```

**Verify Inserts**
```zsh
DB_URL="$(awk -F= '/^DB_URL=/ {print $2}' .env)"
psql "$DB_URL" -c "SELECT ts, symbol, exchange, price, ret_1h, volume FROM market_metrics ORDER BY ts DESC LIMIT 20;"
psql "$DB_URL" -c "SELECT ts, narrative_id, heat_score, narrative_fingerprint FROM narratives ORDER BY ts DESC LIMIT 10;"
psql "$DB_URL" -c "SELECT ts, narrative_id, symbol, strength, direction_bias FROM narrative_assets ORDER BY ts DESC LIMIT 10;"
psql "$DB_URL" -c "SELECT ts, symbol, regime, long_bias, risk_mult, confidence FROM regimes ORDER BY ts DESC LIMIT 20;"
```

**Docker (optional)**
```zsh
export OPENAI_API_KEY=sk-REPLACE_ME
docker compose build
docker compose up -d db
docker compose up -d app
docker compose logs -f app
# psql in db container
docker compose exec db psql -U crypto_admin -d crypto -c "SELECT COUNT(*) FROM market_metrics;"
```

**Keep Alive**
- tmux:
```zsh
tmux new -s crypto
source venv/bin/activate
python scheduler_mvp.py
# detach: Ctrl+b then d
```
- systemd template:
```zsh
sudo tee /etc/systemd/system/crypto-narrative@.service >/dev/null <<'UNIT'
[Unit]
Description=Crypto Narrative Pipeline (%i)
After=network-online.target postgresql.service

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i/sentiment/crypto_narrative_regimes
ExecStart=/home/%i/sentiment/crypto_narrative_regimes/venv/bin/python /home/%i/sentiment/crypto_narrative_regimes/scheduler_mvp.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable crypto-narrative@$(whoami).service
sudo systemctl start crypto-narrative@$(whoami).service
sudo journalctl -u crypto-narrative@$(whoami).service -f
```

**Notes**
- Region constraints: Bybit excluded; use `binanceus`. Futures fields (OI/funding/liqs) omitted.
- 1h returns via OHLCV; narratives fingerprinted by snapshot to dedupe.
- `schema.sql` is Timescale-safe on plain Postgres (conditional hypertables).
- `.env` is ignored by git; keep real keys only on the server.
