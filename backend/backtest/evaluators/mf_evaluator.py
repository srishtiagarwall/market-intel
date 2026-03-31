"""
MF Timing Signal Evaluator.

For each day where composite_score > threshold:
  - Record entry date + Nifty level
  - Measure Nifty return at 30/90/180/365 days
  - Mark GOOD if 180d return > 8%, BAD if 180d return < 0%
  - Output: hit rate, avg return, best threshold
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Sequence

sys.path.insert(0, str(Path(__file__).parents[3]))
from backtest.engine.signal_replay import MFReplayRow

REPORTS_DIR = Path(__file__).parents[1] / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


@dataclass
class MFBacktestResult:
    threshold: float
    signals_fired: int
    good_signals: int       # 180d return > 8%
    bad_signals: int        # 180d return < 0%
    hit_rate_pct: float     # good / signals_with_outcome
    avg_return_180d: float
    avg_return_90d: float
    false_positive_rate: float


def evaluate_mf(rows: list[MFReplayRow], threshold: float = 60.0) -> MFBacktestResult:
    signals = [r for r in rows if r.score_output.composite_score >= threshold]
    signals_with_180d = [r for r in signals if r.nifty_180d is not None]

    if not signals_with_180d:
        return MFBacktestResult(
            threshold=threshold,
            signals_fired=len(signals),
            good_signals=0, bad_signals=0,
            hit_rate_pct=0.0,
            avg_return_180d=0.0, avg_return_90d=0.0,
            false_positive_rate=0.0,
        )

    returns_180d = [
        (r.nifty_180d - r.nifty_price) / r.nifty_price * 100
        for r in signals_with_180d
    ]
    returns_90d = [
        ((r.nifty_90d - r.nifty_price) / r.nifty_price * 100)
        for r in signals_with_180d if r.nifty_90d
    ]

    good = sum(1 for r in returns_180d if r > 8.0)
    bad = sum(1 for r in returns_180d if r < 0.0)
    hit_rate = good / len(returns_180d) * 100
    false_positive_rate = bad / len(returns_180d) * 100

    return MFBacktestResult(
        threshold=threshold,
        signals_fired=len(signals),
        good_signals=good,
        bad_signals=bad,
        hit_rate_pct=round(hit_rate, 2),
        avg_return_180d=round(sum(returns_180d) / len(returns_180d), 2),
        avg_return_90d=round(sum(returns_90d) / len(returns_90d), 2) if returns_90d else 0.0,
        false_positive_rate=round(false_positive_rate, 2),
    )


def run_threshold_sweep(rows: list[MFReplayRow]) -> list[MFBacktestResult]:
    """Sweep thresholds 40–80 in steps of 5."""
    results = []
    for t in range(40, 85, 5):
        results.append(evaluate_mf(rows, threshold=float(t)))
    return results


def save_report(results: list[MFBacktestResult], best: MFBacktestResult) -> None:
    report = {
        "best_threshold": best.threshold,
        "best_hit_rate": best.hit_rate_pct,
        "best_avg_return_180d": best.avg_return_180d,
        "vs_baseline_nifty_buyhold": "TODO: compute Nifty CAGR for same period",
        "threshold_sweep": [asdict(r) for r in results],
    }
    out = REPORTS_DIR / "mf_backtest_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"Report saved to {out}")


def find_optimal_threshold(results: list[MFBacktestResult]) -> MFBacktestResult:
    """Maximize hit_rate * avg_return_180d — avoids both too-sensitive and too-loose."""
    return max(
        (r for r in results if r.signals_fired > 0),
        key=lambda r: r.hit_rate_pct * max(r.avg_return_180d, 0),
        default=results[0],
    )
