import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.signals import StockSignalResponse, StockSignalSummary

logger = logging.getLogger(__name__)
router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[StockSignalSummary])
async def list_stock_signals(db: DB):
    """Return the latest signal for each active watchlist ticker, ranked by score."""
    from app.models.stock_signal import StockSignal
    from app.models.stock_watchlist import StockWatchlist
    from sqlalchemy.orm import aliased

    # Get all active tickers
    wl_result = await db.execute(
        select(StockWatchlist).where(StockWatchlist.is_active == True)
    )
    watchlist = wl_result.scalars().all()

    summaries = []
    for item in watchlist:
        sig_result = await db.execute(
            select(StockSignal)
            .where(StockSignal.watchlist_id == item.id)
            .order_by(desc(StockSignal.computed_at))
            .limit(1)
        )
        signal = sig_result.scalar_one_or_none()
        if signal:
            summaries.append({
                "ticker": item.ticker,
                "company_name": item.company_name,
                "composite_score": float(signal.composite_score),
                "signal_label": signal.signal_label.value,
                "current_price": float(signal.current_price),
                "rsi": float(signal.rsi) if signal.rsi else None,
                "vs_200dma_pct": float(signal.vs_200dma_pct) if signal.vs_200dma_pct else None,
            })

    # Sort by score descending
    summaries.sort(key=lambda x: x["composite_score"], reverse=True)
    return summaries


@router.get("/{ticker}", response_model=StockSignalResponse)
async def get_stock_signal(ticker: str, db: DB):
    """Return full breakdown for a single ticker."""
    from app.models.stock_signal import StockSignal
    from app.models.stock_watchlist import StockWatchlist

    ticker = ticker.upper()

    wl_result = await db.execute(
        select(StockWatchlist).where(StockWatchlist.ticker == ticker)
    )
    wl_item = wl_result.scalar_one_or_none()
    if wl_item is None:
        raise HTTPException(status_code=404, detail=f"{ticker} not in watchlist")

    sig_result = await db.execute(
        select(StockSignal)
        .where(StockSignal.watchlist_id == wl_item.id)
        .order_by(desc(StockSignal.computed_at))
        .limit(1)
    )
    signal = sig_result.scalar_one_or_none()
    if signal is None:
        raise HTTPException(status_code=404, detail=f"No signal yet for {ticker}")

    return {
        "id": str(signal.id),
        "ticker": wl_item.ticker,
        "company_name": wl_item.company_name,
        "computed_at": signal.computed_at,
        "current_price": float(signal.current_price),
        "fundamental_score": float(signal.fundamental_score),
        "technical_score": float(signal.technical_score),
        "event_score": float(signal.event_score),
        "composite_score": float(signal.composite_score),
        "signal_label": signal.signal_label.value,
        "rsi": float(signal.rsi) if signal.rsi else None,
        "macd_signal": signal.macd_signal,
        "vs_200dma_pct": float(signal.vs_200dma_pct) if signal.vs_200dma_pct else None,
        "pe_ratio": float(signal.pe_ratio) if signal.pe_ratio else None,
        "roe": float(signal.roe) if signal.roe else None,
        "reasoning": signal.reasoning,
    }
