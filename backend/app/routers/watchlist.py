import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.stock_watchlist import StockWatchlist
from app.schemas.watchlist import AddWatchlistRequest, WatchlistItemResponse

logger = logging.getLogger(__name__)
router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]

# Seed tickers from CLAUDE.md user profile
_SEED_TICKERS = [
    {"ticker": "HDFCBANK", "company_name": "HDFC Bank Ltd", "sector": "Banking"},
    {"ticker": "ICICIBANK", "company_name": "ICICI Bank Ltd", "sector": "Banking"},
    {"ticker": "INFY", "company_name": "Infosys Ltd", "sector": "IT"},
    {"ticker": "TCS", "company_name": "Tata Consultancy Services", "sector": "IT"},
    {"ticker": "RELIANCE", "company_name": "Reliance Industries Ltd", "sector": "Conglomerate"},
    {"ticker": "BAJFINANCE", "company_name": "Bajaj Finance Ltd", "sector": "NBFC"},
    {"ticker": "LTIM", "company_name": "LTIMindtree Ltd", "sector": "IT"},
    {"ticker": "PIDILITIND", "company_name": "Pidilite Industries Ltd", "sector": "Consumer"},
]


@router.get("", response_model=list[WatchlistItemResponse])
async def list_watchlist(db: DB):
    result = await db.execute(
        select(StockWatchlist).where(StockWatchlist.is_active == True)
    )
    items = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "ticker": i.ticker,
            "company_name": i.company_name,
            "sector": i.sector,
            "target_buy_price": float(i.target_buy_price) if i.target_buy_price else None,
            "position_size": float(i.position_size) if i.position_size else None,
            "is_active": i.is_active,
            "added_at": i.added_at.isoformat(),
        }
        for i in items
    ]


@router.post("/add", response_model=WatchlistItemResponse, status_code=201)
async def add_to_watchlist(body: AddWatchlistRequest, db: DB):
    ticker = body.ticker.upper()

    existing = await db.execute(
        select(StockWatchlist).where(StockWatchlist.ticker == ticker)
    )
    item = existing.scalar_one_or_none()

    if item:
        if not item.is_active:
            item.is_active = True  # re-activate if previously removed
            await db.commit()
        return {
            "id": str(item.id),
            "ticker": item.ticker,
            "company_name": item.company_name,
            "sector": item.sector,
            "target_buy_price": float(item.target_buy_price) if item.target_buy_price else None,
            "position_size": float(item.position_size) if item.position_size else None,
            "is_active": item.is_active,
            "added_at": item.added_at.isoformat(),
        }

    new_item = StockWatchlist(
        ticker=ticker,
        company_name=body.company_name,
        sector=body.sector,
        target_buy_price=body.target_buy_price,
        position_size=body.position_size,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    return {
        "id": str(new_item.id),
        "ticker": new_item.ticker,
        "company_name": new_item.company_name,
        "sector": new_item.sector,
        "target_buy_price": float(new_item.target_buy_price) if new_item.target_buy_price else None,
        "position_size": float(new_item.position_size) if new_item.position_size else None,
        "is_active": new_item.is_active,
        "added_at": new_item.added_at.isoformat(),
    }


@router.delete("/{ticker}", status_code=204)
async def remove_from_watchlist(ticker: str, db: DB):
    ticker = ticker.upper()
    result = await db.execute(
        select(StockWatchlist).where(StockWatchlist.ticker == ticker)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"{ticker} not in watchlist")

    item.is_active = False  # soft delete
    await db.commit()


@router.post("/seed", status_code=201)
async def seed_watchlist(db: DB):
    """Seed the default watchlist from CLAUDE.md user profile. Safe to call multiple times."""
    added = []
    for seed in _SEED_TICKERS:
        existing = await db.execute(
            select(StockWatchlist).where(StockWatchlist.ticker == seed["ticker"])
        )
        if existing.scalar_one_or_none() is None:
            item = StockWatchlist(**seed)
            db.add(item)
            added.append(seed["ticker"])
    await db.commit()
    return {"seeded": added}
