"""
Fetch 2-year Nifty 50 daily OHLCV + PE/PB history for backtesting.
Run once: python -m backtest.data.fetch_nifty_history
Saves to: backtest/data/nifty_ohlcv.csv
PE/PB:     backtest/data/pe_history.csv (manual download from NSE)
"""
import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent

sys_path_parent = Path(__file__).parents[3]  # market-intel/backend
import sys
sys.path.insert(0, str(sys_path_parent))

from app.fetchers.yahoo_finance import get_nifty_history


def fetch_and_save(years: int = 2) -> None:
    print(f"Fetching {years}-year Nifty history...")
    df = get_nifty_history(years=years)
    if df is None:
        print("ERROR: Could not fetch Nifty history")
        return

    out_path = DATA_DIR / "nifty_ohlcv.csv"
    df.to_csv(out_path)
    print(f"Saved {len(df)} rows to {out_path}")
    print("\nNOTE: Download PE/PB history manually from NSE:")
    print("  https://www.nseindia.com/reports-indices-historical-index-data")
    print(f"  Save as: {DATA_DIR}/pe_history.csv")
    print("  Expected columns: Date, PE, PB, Div_Yield")


if __name__ == "__main__":
    fetch_and_save()
