from features_liquidation_cascade import compute_liquidation_metrics


def run():
    return compute_liquidation_metrics()


if __name__ == "__main__":
    result = run()
    print(f"Events: {len(result.get('cascade_events', []))}")
    print(f"Zones: {len(result.get('liquidation_zones', []))}")
