# Shared configuration and thresholds

EXCHANGES = ["binance", "bybit"]

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# Minimum number of observations per symbol for meaningful stats
MIN_OBS = 10

# Regime thresholds (MVP – tune via backtests)
REGIME_CFG = {
    "OVERHEATED": {
        "heat_min": 0.85,
        "oi_z_min": 1.5,
        "funding_z_min": 1.0,
    },
    "IGNITION": {
        "heat_min": 0.6,
        "oi_z_min": 0.5,
        "funding_z_min": 0.2,
        "liq_intensity_max": 1.0,
    },
    "FUNDING_RESET_IGNITION": {
        "heat_min": 0.4,
        "heat_delta_min": 0.1,
        "oi_z_min": -0.5,
        "oi_z_max": 1.0,
        "funding_max": 0.0,  # negative or zero
    },
    "PANIC": {
        "liq_bias_max": -0.6,
        "liq_intensity_min": 1.5,
        "oi_z_max": -0.5,
    },
    "COILED": {
        "heat_max": 0.3,
        "oi_z_min": 0.5,
        "funding_z_abs_max": 0.3,
        "liq_intensity_max": 0.5,
    },
}
