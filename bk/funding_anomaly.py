from features_funding_anomaly import compute_funding_metrics


def run():
    return compute_funding_metrics()


if __name__ == "__main__":
    result = run()
    print(f"Anomalies: {len(result.get('funding_anomalies', []))}")
    print(f"Reversals: {len(result.get('reversal_signals', []))}")
