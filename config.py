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
