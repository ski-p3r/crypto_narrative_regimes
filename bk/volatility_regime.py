from features_volatility_regime import compute_volatility_features


def run():
    return compute_volatility_features()


if __name__ == "__main__":
    result = run()
    print(f"Volatility regimes: {len(result.get('volatility_regimes', []))}")
    print(f"Clustering events: {len(result.get('volatility_clustering', []))}")
    print(f"Persistence data: {len(result.get('volatility_persistence', []))}")
