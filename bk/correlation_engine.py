from features_correlation_engine import compute_correlation_metrics


def run():
    return compute_correlation_metrics()


if __name__ == "__main__":
    result = run()
    print(f"Divergence events: {len(result.get('divergence_events', []))}")
    print(f"Leading indicators: {len(result.get('leading_analysis', {}).get('leading_indicators', []))}")
