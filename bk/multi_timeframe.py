from features_multi_timeframe import compute_multi_timeframe_regimes


def run():
    return compute_multi_timeframe_regimes()


if __name__ == "__main__":
    result = run()
    print(f"Primary regimes: {len(result.get('primary_regimes', []))}")
    print(f"Agreement scores: {len(result.get('agreement_scores', {}))}")
