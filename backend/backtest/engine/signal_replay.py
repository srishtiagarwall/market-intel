"""
Signal Replay Engine — the core of the backtest.

Iterates over historical dates and computes signals using ONLY data available
at market close on each day T. No lookahead bias.

Critical rule:
  On day T, you may use: Nifty close[T], PE[T], news[T]
  You MUST NOT use: price[T+1], price[T+30], etc. as inputs.
  Future prices are used ONLY as outcome labels (measured after the fact).
"""
from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

# Add backend root to path so we can import from app.scoring
sys.path.insert(0, str(Path(__file__).parents[3]))

from app.scoring.mf_scorer import score_mf_signal, MFScoreInput, MFScoreOutput
from app.scoring.stock_scorer import (
    score_stock_signal, StockScoreInput, StockScoreOutput,
    FundamentalInput, TechnicalInput, EventInput,
)

DATA_DIR = Path(__file__).parents[1] / "data"


@dataclass
class MFReplayRow:
    date: date
    nifty_price: float
    nifty_pe: float | None
    score_output: MFScoreOutput
    # Outcomes (filled by evaluator, not scorer)
    nifty_30d: float | None = None
    nifty_90d: float | None = None
    nifty_180d: float | None = None
    nifty_365d: float | None = None


def replay_mf_signals(start_date: date, end_date: date) -> list[MFReplayRow]:
    """
    Compute MF signal for every trading day in [start_date, end_date].
    Returns list of MFReplayRow — outcomes are not filled here (evaluator does that).
    """
    # Load price history
    ohlcv_path = DATA_DIR / "nifty_ohlcv.csv"
    if not ohlcv_path.exists():
        raise FileNotFoundError(
            f"{ohlcv_path} not found. Run: python -m backtest.data.fetch_nifty_history"
        )
    prices = pd.read_csv(ohlcv_path, index_col=0, parse_dates=True)
    prices.index = pd.to_datetime(prices.index).date

    # Load PE history (manual CSV from NSE)
    pe_path = DATA_DIR / "pe_history.csv"
    pe_data: dict[date, tuple[float | None, float | None]] = {}
    if pe_path.exists():
        pe_df = pd.read_csv(pe_path, parse_dates=["Date"])
        for _, row in pe_df.iterrows():
            d = row["Date"].date()
            pe_data[d] = (
                float(row["PE"]) if pd.notna(row.get("PE")) else None,
                float(row["PB"]) if pd.notna(row.get("PB")) else None,
            )

    rows = []
    all_dates = sorted([d for d in prices.index if start_date <= d <= end_date])

    for i, current_date in enumerate(all_dates):
        close_prices = prices.loc[:current_date, "Close"]
        if len(close_prices) < 2:
            continue

        nifty_price = float(close_prices.iloc[-1])
        # 52W high: use prices up to and including current_date only (no lookahead)
        lookback_start = current_date - timedelta(days=365)
        window = close_prices[close_prices.index >= lookback_start]
        high_52w = float(window.max())

        pe, pb = pe_data.get(current_date, (None, None))
        # Fallback: use closest prior PE if today's not available
        if pe is None:
            for back in range(1, 8):
                fallback_date = current_date - timedelta(days=back)
                if fallback_date in pe_data:
                    pe, pb = pe_data[fallback_date]
                    break

        inp = MFScoreInput(
            nifty_price=nifty_price,
            nifty_52w_high=high_52w,
            nifty_pe=pe,
            nifty_pb=pb,
            macro_sentiment="neutral",  # news NLP not available historically; use neutral
        )
        output = score_mf_signal(inp)

        rows.append(MFReplayRow(
            date=current_date,
            nifty_price=nifty_price,
            nifty_pe=pe,
            score_output=output,
        ))

    # Fill outcomes (future prices — used as labels only, not inputs)
    price_map = {d: float(prices.loc[d, "Close"]) for d in prices.index}
    for row in rows:
        for horizon_days, attr in [(30, "nifty_30d"), (90, "nifty_90d"), (180, "nifty_180d"), (365, "nifty_365d")]:
            target_date = row.date + timedelta(days=horizon_days)
            # Find nearest trading day after target
            for offset in range(0, 10):
                check = target_date + timedelta(days=offset)
                if check in price_map:
                    setattr(row, attr, price_map[check])
                    break

    return rows
