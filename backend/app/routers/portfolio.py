import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.portfolio import Portfolio
from app.schemas.portfolio import (
    AddHoldingRequest,
    HoldingResponse,
    CashStateRequest,
    PortfolioHealthResponse,
)
from app.services.portfolio_service import (
    get_holdings_with_performance,
    get_portfolio_health,
    update_cash_state,
)
from app.services.cams_parser import parse_cams_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/holdings", response_model=list[HoldingResponse])
async def list_holdings(db: DB):
    return await get_holdings_with_performance(db)


@router.post("/holdings", response_model=HoldingResponse, status_code=201)
async def add_holding(body: AddHoldingRequest, db: DB):
    holding = Portfolio(
        fund_name=body.fund_name,
        fund_type=body.fund_type,
        isin=body.isin,
        invested_amount=body.invested_amount,
        units_held=body.units_held,
        purchase_nav=body.purchase_nav,
        purchase_date=body.purchase_date,
        target_pct=body.target_pct,
    )
    db.add(holding)
    await db.commit()
    await db.refresh(holding)
    return {
        "id": str(holding.id),
        "fund_name": holding.fund_name,
        "fund_type": holding.fund_type.value,
        "isin": holding.isin,
        "invested_amount": float(holding.invested_amount),
        "units_held": float(holding.units_held),
        "purchase_nav": float(holding.purchase_nav),
        "purchase_date": holding.purchase_date.isoformat(),
        "target_pct": float(holding.target_pct),
        "current_nav": None,
        "current_value": None,
        "gain_loss_pct": None,
    }


@router.post("/cash")
async def update_cash(body: CashStateRequest, db: DB):
    cash = await update_cash_state(
        db,
        total_available=body.total_available,
        deployed_amount=body.deployed_amount,
        emergency_fund=body.emergency_fund,
        notes=body.notes,
    )
    await db.commit()
    return {
        "total_available": float(cash.total_available),
        "deployed_amount": float(cash.deployed_amount),
        "emergency_fund": float(cash.emergency_fund),
        "notes": cash.notes,
    }


@router.get("/health", response_model=PortfolioHealthResponse)
async def portfolio_health(db: DB):
    return await get_portfolio_health(db)


@router.post("/import/cams")
async def import_cams(db: DB, file: UploadFile = File(...)):
    """Upload CAMS PDF and upsert holdings."""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    pdf_bytes = await file.read()
    holdings = parse_cams_pdf(pdf_bytes)

    if not holdings:
        raise HTTPException(status_code=422, detail="No holdings found in PDF. Check format.")

    upserted = 0
    for h in holdings:
        # Check if this exact lot already exists (same fund_name + purchase_date + units)
        result = await db.execute(
            select(Portfolio).where(
                Portfolio.isin == h["isin"],
                Portfolio.purchase_date == h["purchase_date"],
                Portfolio.units_held == h["units_held"],
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            row = Portfolio(**{
                "fund_name": h["fund_name"],
                "isin": h["isin"],
                "fund_type": h["fund_type"],
                "units_held": h["units_held"],
                "purchase_nav": h["purchase_nav"],
                "invested_amount": h["invested_amount"],
                "purchase_date": h["purchase_date"],
                "target_pct": 0.0,
            })
            db.add(row)
            upserted += 1

    await db.commit()
    return {"imported": upserted, "total_found": len(holdings)}
