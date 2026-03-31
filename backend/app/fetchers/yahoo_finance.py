"""
All yfinance calls go through this module.
Returns plain Python dataclasses — no pandas leaking out.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
import pandas_ta as ta

logger = logging.getLogger(__name__)

_NSE = ".NS"
_NIFTY_TICKER = "^NSEI"


@dataclass
class NiftySnapshot:
    price: float
    high_52w: float
    low_52w: float
    drawdown_from_52w_high_pct: float
    as_of: datetime


@dataclass
class StockTechnicals:
    ticker: str
    current_price: float
    rsi_14: float | None
    macd_histogram: float | None  # positive = bullish
    sma_200: float | None
    vs_200dma_pct: float | None   # (price - 200DMA) / 200DMA * 100
    as_of: datetime


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if f != f else f  # NaN check
    except (TypeError, ValueError):
        return None


def get_nifty_snapshot() -> NiftySnapshot | None:
    try:
        ticker = yf.Ticker(_NIFTY_TICKER)
        info = ticker.fast_info

        price = _safe_float(info.last_price)
        # yfinance renamed fifty_two_week_high → year_high in newer versions
        high_52w = _safe_float(getattr(info, "year_high", None)) or \
                   _safe_float(getattr(info, "fifty_two_week_high", None))
        low_52w  = _safe_float(getattr(info, "year_low", None)) or \
                   _safe_float(getattr(info, "fifty_two_week_low", None)) or 0.0

        if price is None or high_52w is None:
            logger.warning("Nifty snapshot: missing price or 52w high")
            return None

        drawdown = ((high_52w - price) / high_52w) * 100 if high_52w > 0 else 0.0

        return NiftySnapshot(
            price=round(price, 2),
            high_52w=round(high_52w, 2),
            low_52w=round(low_52w, 2),
            drawdown_from_52w_high_pct=round(drawdown, 2),
            as_of=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Failed to fetch Nifty snapshot: {e}")
        return None


def get_nifty_history(years: int = 2) -> pd.DataFrame | None:
    """Returns daily OHLCV DataFrame for backtesting."""
    try:
        end = datetime.today()
        start = end - timedelta(days=365 * years)
        df = yf.download(_NIFTY_TICKER, start=start, end=end, progress=False)
        if df.empty:
            logger.warning("Empty Nifty history returned")
            return None
        return df
    except Exception as e:
        logger.error(f"Failed to fetch Nifty history: {e}")
        return None


def get_stock_technicals(ticker: str) -> StockTechnicals | None:
    """
    Fetch RSI(14), MACD, and 200DMA for a single NSE stock.
    ticker: e.g. "HDFCBANK" (without .NS)
    """
    yf_ticker = ticker if ticker.endswith(_NSE) else f"{ticker}{_NSE}"
    try:
        end = datetime.today()
        start = end - timedelta(days=300)  # Need 300 days for stable 200DMA
        df = yf.download(yf_ticker, start=start, end=end, progress=False, auto_adjust=True)

        if df.empty or len(df) < 50:
            logger.warning(f"{ticker}: insufficient price history ({len(df)} rows)")
            return None

        close = df["Close"].dropna()
        if hasattr(close, 'squeeze'):
            close = close.squeeze()
        current_price = float(close.iloc[-1])

        # RSI(14)
        rsi_series = ta.rsi(close, length=14)
        rsi = _safe_float(rsi_series.iloc[-1]) if rsi_series is not None else None

        # MACD (12, 26, 9)
        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        macd_hist = None
        if macd_df is not None and not macd_df.empty:
            hist_col = [c for c in macd_df.columns if "MACDh" in str(c)]
            if hist_col:
                macd_hist = _safe_float(macd_df[hist_col[0]].iloc[-1])

        # 200DMA
        sma200_series = ta.sma(close, length=200)
        sma200 = _safe_float(sma200_series.iloc[-1]) if sma200_series is not None else None
        vs_200dma = None
        if sma200 and sma200 > 0:
            vs_200dma = round(((current_price - sma200) / sma200) * 100, 2)

        return StockTechnicals(
            ticker=ticker,
            current_price=round(current_price, 2),
            rsi_14=round(rsi, 2) if rsi is not None else None,
            macd_histogram=round(macd_hist, 4) if macd_hist is not None else None,
            sma_200=round(sma200, 2) if sma200 is not None else None,
            vs_200dma_pct=vs_200dma,
            as_of=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Failed to fetch technicals for {ticker}: {e}")
        return None


def get_stock_history(ticker: str, years: int = 2) -> pd.DataFrame | None:
    """For backtesting. Returns daily OHLCV DataFrame."""
    yf_ticker = ticker if ticker.endswith(_NSE) else f"{ticker}{_NSE}"
    try:
        end = datetime.today()
        start = end - timedelta(days=365 * years)
        df = yf.download(yf_ticker, start=start, end=end, progress=False, auto_adjust=True)
        return df if not df.empty else None
    except Exception as e:
        logger.error(f"Failed to fetch history for {ticker}: {e}")
        return None
