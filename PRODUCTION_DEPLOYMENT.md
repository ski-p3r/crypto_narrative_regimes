# Production Deployment Guide

Complete guide to deploying the crypto narrative regime system to production.

## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Environment variables configured
- [ ] Database backed up
- [ ] Monitoring set up
- [ ] Alerting configured
- [ ] Disaster recovery plan ready
- [ ] Load tested

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Binance.US API                       │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Market Data Ingestion Server               │
│           (ingestion_enhanced.py + scheduler)           │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Feature Computation Pipeline               │
│  - Liquidation Cascades                                │
│  - Funding Anomalies                                   │
│  - Volatility Regime                                   │
│  - Multi-Timeframe Analysis                            │
│  - Correlation Engine                                  │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│  Database       │   │  Webhook         │
│  (PostgreSQL)   │   │  Dispatcher      │
└─────────────────┘   └──────────────────┘
        ▲                     │
        │                     ▼
        │            ┌──────────────────┐
        │            │  Webhook         │
        │            │  Receivers       │
        │            │  (Discord, etc)  │
        │            └──────────────────┘
        │
        └────────────────────┐
                             ▼
                    ┌──────────────────┐
                    │  Next.js         │
                    │  Dashboard       │
                    │  (localhost:3000)│
                    └──────────────────┘
```

## Step 1: Infrastructure Setup

### Option A: AWS EC2 Deployment

```bash
# Launch EC2 instance
# - AMI: Ubuntu 22.04 LTS
# - Type: t3.medium (2 vCPU, 4GB RAM)
# - Storage: 100GB gp3
# - Security Group: Allow ports 22, 80, 443, 3000

# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install -y python3.10 python3.10-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Supervisor (for process management)
sudo apt install -y supervisor

# Install Nginx (for reverse proxy)
sudo apt install -y nginx
```

### Option B: Heroku Deployment

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create your-app-name

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### Option C: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 5000 3000

# Run both services
CMD ["./start.sh"]
```

Create `start.sh`:

```bash
#!/bin/bash
python pipeline_features_master.py &
cd dashboard && npm run build && npm start
```

Build and push:

```bash
docker build -t my-crypto-app .
docker tag my-crypto-app:latest myregistry.azurecr.io/my-crypto-app:latest
docker push myregistry.azurecr.io/my-crypto-app:latest
```

## Step 2: Database Setup

### PostgreSQL Configuration

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE crypto_regimes;
CREATE USER crypto_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE crypto_regimes TO crypto_user;

# Exit psql
\q
```

Create database schema:

```python
# db_init.py
import psycopg2
from psycopg2 import sql

conn = psycopg2.connect(
    dbname="crypto_regimes",
    user="crypto_user",
    password="strong_password_here",
    host="localhost"
)

cur = conn.cursor()

# Create tables
cur.execute('''
    CREATE TABLE IF NOT EXISTS market_events (
        id SERIAL PRIMARY KEY,
        event_type VARCHAR(50),
        symbol VARCHAR(20),
        severity VARCHAR(20),
        data JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS webhook_logs (
        id SERIAL PRIMARY KEY,
        webhook_url VARCHAR(500),
        event_id INTEGER,
        success BOOLEAN,
        response_code INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
cur.close()
conn.close()
```

Run:
```bash
python db_init.py
```

## Step 3: Environment Configuration

Create `.env.production`:

```bash
# API Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret

# Database
DB_URL=postgresql://crypto_user:password@localhost:5432/crypto_regimes

# Webhooks
WEBHOOKS_CASCADE=https://your-webhook-1.com/cascade,https://your-webhook-2.com/cascade
WEBHOOKS_FUNDING=https://your-webhook.com/funding
WEBHOOKS_VOLATILITY=https://your-webhook.com/volatility
WEBHOOKS_CORRELATION=https://your-webhook.com/correlation
WEBHOOKS_REGIME=https://your-webhook.com/regime

# OpenAI (for narrative analysis)
OPENAI_API_KEY=sk-your-key-here

# Dashboard
NEXT_PUBLIC_API_URL=https://your-domain.com/api
NEXT_PUBLIC_DASHBOARD_URL=https://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/crypto_regimes.log

# Server
PORT=5000
NODE_ENV=production
```

## Step 4: Process Management with Supervisor

Create `/etc/supervisor/conf.d/crypto-regimes.conf`:

```ini
[program:crypto-market-data]
command=/home/ubuntu/.venv/bin/python /app/ingestion_enhanced.py
directory=/app
autostart=true
autorestart=true
stderr_logfile=/var/log/crypto_market_data.err
stdout_logfile=/var/log/crypto_market_data.out
environment=PATH="/home/ubuntu/.venv/bin"

[program:crypto-features]
command=/home/ubuntu/.venv/bin/python /app/pipeline_features_master.py
directory=/app
autostart=true
autorestart=true
stderr_logfile=/var/log/crypto_features.err
stdout_logfile=/var/log/crypto_features.out
environment=PATH="/home/ubuntu/.venv/bin"

[program:crypto-dashboard]
command=/usr/bin/npm start
directory=/app/dashboard
autostart=true
autorestart=true
stderr_logfile=/var/log/crypto_dashboard.err
stdout_logfile=/var/log/crypto_dashboard.out

[group:crypto-regimes]
programs=crypto-market-data,crypto-features,crypto-dashboard
priority=999
```

Enable and start:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start crypto-regimes:*
```

## Step 5: Reverse Proxy with Nginx

Create `/etc/nginx/sites-available/crypto-regimes`:

```nginx
upstream backend {
    server 127.0.0.1:5000;
}

upstream dashboard {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 20M;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    client_max_body_size 20M;

    # SSL certificates (get free ones from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # API routes to backend
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Dashboard routes
    location / {
        proxy_pass http://dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/crypto-regimes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Get SSL certificate:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

## Step 6: Monitoring & Logging

### Configure Logging

Create `logging_config.py`:

```python
import logging
import logging.handlers
import os

def setup_logging():
    """Setup centralized logging"""
    
    log_dir = "/var/log/crypto_regimes"
    os.makedirs(log_dir, exist_ok=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler (daily rotation)
    handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/app.log",
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

### Monitoring with Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'crypto-regimes'
    static_configs:
      - targets: ['localhost:8000']
```

Add metrics to app:

```python
from prometheus_client import Counter, Gauge, start_http_server

# Metrics
cascade_events = Counter('cascade_events_total', 'Total cascade events')
funding_anomalies = Counter('funding_anomalies_total', 'Total funding anomalies')
active_connections = Gauge('active_connections', 'Active WebSocket connections')

# Start metrics server on port 8000
start_http_server(8000)

# Use metrics
cascade_events.inc()
active_connections.set(42)
```

### Alerting with Grafana

```bash
# Install Grafana
sudo apt install -y grafana-server
sudo systemctl start grafana-server

# Access at http://localhost:3001
# Add Prometheus data source
# Import dashboards for crypto metrics
```

## Step 7: Backup & Recovery

### Automated Database Backups

Create `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups/crypto_regimes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="crypto_regimes"
DB_USER="crypto_user"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
```

Schedule with cron:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /app/backup.sh
```

### Restore from Backup

```bash
# Decompress
gunzip backup_20240203_020000.sql.gz

# Restore
psql -U crypto_user crypto_regimes < backup_20240203_020000.sql
```

## Step 8: Security Hardening

### Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS only
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Check rules
sudo ufw status
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/events')
@limiter.limit("100 per hour")
def get_events():
    return {"events": []}
```

### Secret Management

Use environment variables, not hardcoded secrets:

```bash
# Store secrets in ~/.bashrc or /etc/environment
export BINANCE_API_KEY="actual-key-here"
export DB_PASSWORD="actual-password-here"
```

Or use AWS Secrets Manager:

```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

binance_key = get_secret('crypto-regimes/binance-key')
```

## Step 9: Performance Optimization

### Caching

```python
from redis import Redis
from functools import wraps

redis_client = Redis(host='localhost', port=6379, db=0)

def cache_result(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Compute and cache
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=600)
def compute_features():
    # Expensive computation
    pass
```

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_events_timestamp ON market_events(timestamp);
CREATE INDEX idx_events_symbol ON market_events(symbol);
CREATE INDEX idx_events_type ON market_events(event_type);

-- Optimize for cascades
CREATE INDEX idx_cascades_vol_hour ON market_events
WHERE event_type = 'CASCADE' AND timestamp > NOW() - INTERVAL '24 hours';
```

## Step 10: Monitoring Checklist

After deployment, monitor:

```bash
# System resources
top
free -h
df -h

# Service status
sudo supervisorctl status

# Logs
tail -f /var/log/crypto_regimes.log
tail -f /var/log/crypto_market_data.err

# Network
netstat -tuln | grep LISTEN

# Database
psql -U crypto_user -d crypto_regimes -c "SELECT COUNT(*) FROM market_events;"
```

## Production Runbook

### Daily Checks

```bash
# 1. Verify all services running
sudo supervisorctl status

# 2. Check logs for errors
grep ERROR /var/log/crypto_regimes.log

# 3. Test webhook delivery
curl https://your-domain.com/health

# 4. Monitor disk space
df -h

# 5. Check API response times
time curl https://your-domain.com/api/features
```

### Incident Response

**Service Down:**
1. Check service status: `sudo supervisorctl status`
2. Restart service: `sudo supervisorctl restart crypto-regimes:*`
3. Check logs: `tail -100 /var/log/crypto_regimes.log`
4. Contact support if issue persists

**High Memory Usage:**
1. Check what's consuming memory: `top`
2. Restart affected service
3. Scale up instance size if persistent

**Webhook Failures:**
1. Check webhook URLs in config
2. Test webhook endpoint: `curl -X POST https://webhook-url/test`
3. Check firewall/network rules
4. Retry manual webhook dispatch

## Scaling to Production

For high-traffic production:

1. **Horizontal Scaling:**
   - Run multiple pipeline instances with load balancer
   - Use database connection pooling
   - Implement queue-based architecture (Celery)

2. **Database Scaling:**
   - Use PostgreSQL read replicas
   - Implement sharding for large datasets
   - Archive old data to separate storage

3. **Monitoring at Scale:**
   - Use APM tools (DataDog, New Relic)
   - Set up distributed tracing
   - Monitor all critical paths

## Support & Troubleshooting

See TROUBLESHOOTING_GUIDE.md for detailed issue resolution.
