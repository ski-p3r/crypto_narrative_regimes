# Shared configuration and thresholds

EXCHANGES = ["binanceus"]

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# Minimum number of observations per symbol for meaningful stats
MIN_OBS = 10

# Regime thresholds (Spot-only for US Market)
REGIME_CFG = {
    "SPOT_IGNITION": {
        "heat_min": 0.6,
        "price_z_min": 1.0,
        "vol_z_min": 1.5,
    },
    "SPOT_COOLING": {
        "heat_max": 0.4,
        "price_z_max": -0.5,
        "vol_z_max": 0.5,
    },
    "SPOT_CHOP": {
        "heat_max": 0.5,
        "price_z_abs_max": 0.5,
        "vol_z_max": 1.0,
    },
    "SPOT_NEUTRAL": {
        # Fallback if no other condition met
    }
}

# Liquidation Cascade Detection thresholds
LIQUIDATION_CFG = {
    "cascade_threshold_usd": 500000,  # USD threshold to trigger cascade detection
    "velocity_window": 4,  # number of hours to calculate liquidation velocity
    "critical_velocity": 200000,  # USD per hour velocity threshold
}

# Funding Rate Anomaly thresholds
FUNDING_CFG = {
    "anomaly_z_threshold": 2.0,  # Z-score threshold for anomaly detection
    "reversal_threshold": 0.05,  # 5% funding rate reversal signal
}

# Volatility Regime thresholds
VOLATILITY_CFG = {
    "stable_threshold": 0.01,  # 1% volatility threshold for STABLE regime
    "high_vol_threshold": 0.05,  # 5% volatility threshold for HIGH_VOL regime
    "explosive_threshold": 0.10,  # 10% volatility threshold for EXPLOSIVE regime
    "window": 24,  # hours
}

# Multi-timeframe regime parameters
TIMEFRAMES = ["1h", "4h", "1d", "1w"]

# Correlation engine thresholds
CORRELATION_CFG = {
    "window": 24 * 7,  # 7 days in hours
    "correlation_break_threshold": 0.5,  # significant deviation from normal correlation
    "primary_assets": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
}
