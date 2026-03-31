"""
Backtest entry point.

Usage:
  python run_backtest.py --mode mf
  python run_backtest.py --mode stock --ticker HDFCBANK
  python run_backtest.py --mode all

Output:
  backtest/reports/mf_backtest_report.json
  backtest/reports/stock_backtest_report.json
"""
import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))


def run_mf_backtest() -> None:
    from backtest.engine.signal_replay import replay_mf_signals
    from backtest.evaluators.mf_evaluator import (
        run_threshold_sweep, find_optimal_threshold, save_report
    )

    end = date.today()
    start = end - timedelta(days=2 * 365)

    print(f"Running MF backtest: {start} → {end}")
    rows = replay_mf_signals(start, end)
    print(f"Total trading days replayed: {len(rows)}")

    results = run_threshold_sweep(rows)
    best = find_optimal_threshold(results)

    print("\n── Threshold Sweep Results ──────────────────────")
    print(f"{'Threshold':>10} {'Signals':>8} {'Hit Rate':>10} {'Avg 180d':>10}")
    for r in results:
        print(f"{r.threshold:>10.0f} {r.signals_fired:>8} {r.hit_rate_pct:>9.1f}% {r.avg_return_180d:>9.1f}%")

    print(f"\nOptimal threshold: {best.threshold}")
    print(f"Hit rate at optimal: {best.hit_rate_pct:.1f}%")
    print(f"Avg 180d return: {best.avg_return_180d:.1f}%")

    if best.hit_rate_pct < 55:
        print("\nWARN: Hit rate < 55% — consider rethinking signal design before trusting production")
    elif best.hit_rate_pct < 65:
        print("\nWARN: Hit rate 55–65% — tighten one sub-score rule and re-run")
    else:
        print(f"\nOK: Hit rate > 65% — signal validated. Update MF_SIGNAL_THRESHOLD={best.threshold:.0f} in .env")

    save_report(results, best)


def main() -> None:
    parser = argparse.ArgumentParser(description="Market Intel Backtest Runner")
    parser.add_argument("--mode", choices=["mf", "stock", "all"], default="mf")
    parser.add_argument("--ticker", type=str, default=None, help="Ticker for stock mode")
    args = parser.parse_args()

    if args.mode in ("mf", "all"):
        run_mf_backtest()

    if args.mode in ("stock", "all"):
        print("\nStock backtest — coming in Phase 4 after MF backtest validates signal logic.")


if __name__ == "__main__":
    main()
