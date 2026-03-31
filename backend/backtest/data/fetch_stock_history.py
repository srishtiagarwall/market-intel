"""
Fetch 2-year daily OHLCV for each ticker in the watchlist.
Run once: python -m backtest.data.fetch_stock_history
Saves to: backtest/data/stocks/{TICKER}.csv
"""
from pathlib import Path
import sys

DATA_DIR = Path(__file__).parent
STOCKS_DIR = DATA_DIR / "stocks"
STOCKS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(Path(__file__).parents[3]))

from app.fetchers.yahoo_finance import get_stock_history

WATCHLIST = [
    "HDFCBANK", "ICICIBANK", "INFY", "TCS",
    "RELIANCE", "BAJFINANCE", "LTIM", "PIDILITIND",
]


def fetch_all(years: int = 2) -> None:
    for ticker in WATCHLIST:
        print(f"Fetching {ticker}...")
        df = get_stock_history(ticker, years=years)
        if df is None:
            print(f"  WARN: No data for {ticker}")
            continue
        out = STOCKS_DIR / f"{ticker}.csv"
        df.to_csv(out)
        print(f"  Saved {len(df)} rows → {out}")


if __name__ == "__main__":
    fetch_all()
