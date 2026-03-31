"""
Portfolio business logic.
- Holdings with current NAV and gain/loss
- XIRR calculation
- Allocation drift vs targets
- Cash state management
"""
import logging
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio, FundType
from app.models.cash_state import CashState
from app.fetchers.mfapi import get_latest_nav

logger = logging.getLogger(__name__)


async def get_holdings_with_performance(db: AsyncSession) -> list[dict]:
    """Returns all holdings enriched with current NAV and gain/loss."""
    result = await db.execute(select(Portfolio).order_by(Portfolio.purchase_date))
    holdings = result.scalars().all()

    enriched = []
    for h in holdings:
        current_nav = None
        current_value = None
        gain_loss_pct = None

        if h.isin:
            # MFAPI lookup by ISIN — search by fund name if ISIN lookup unavailable
            current_nav = await get_latest_nav(_isin_to_scheme_code(h.isin))

        if current_nav and h.units_held:
            current_value = round(float(h.units_held) * current_nav, 2)
            invested = float(h.invested_amount)
            gain_loss_pct = round(((current_value - invested) / invested) * 100, 2)

        enriched.append({
            "id": str(h.id),
            "fund_name": h.fund_name,
            "fund_type": h.fund_type.value,
            "isin": h.isin,
            "invested_amount": float(h.invested_amount),
            "units_held": float(h.units_held),
            "purchase_nav": float(h.purchase_nav),
            "purchase_date": h.purchase_date.isoformat(),
            "target_pct": float(h.target_pct),
            "current_nav": current_nav,
            "current_value": current_value,
            "gain_loss_pct": gain_loss_pct,
        })

    return enriched


def _isin_to_scheme_code(isin: str) -> int:
    """
    Placeholder: in production, maintain an ISIN → MFAPI scheme code mapping table.
    For now returns 0 (invalid) — MFAPI lookup will return None.
    """
    # TODO: populate this mapping from MFAPI search results
    _ISIN_MAP: dict[str, int] = {
        "INF879O01019": 122639,  # Parag Parikh Flexi Cap — Direct Growth
        "INF769K01EW7": 118834,  # Mirae Asset Large & Midcap — Direct Growth
        "INF205K01DN1": 120595,  # Canara Robeco Small Cap — Direct Growth
        "INF204KB1JE1": 118365,  # Nippon India Large Cap — Direct Growth
    }
    return _ISIN_MAP.get(isin, 0)


async def get_portfolio_health(db: AsyncSession) -> dict[str, Any]:
    """
    Returns allocation drift, total value, cash deployed %.
    Compares current allocation against target_pct per fund.
    """
    holdings = await get_holdings_with_performance(db)
    cash_result = await db.execute(select(CashState).limit(1))
    cash = cash_result.scalar_one_or_none()

    total_invested = sum(h["invested_amount"] for h in holdings)
    total_current = sum(h["current_value"] or h["invested_amount"] for h in holdings)
    total_gain_loss_pct = (
        round(((total_current - total_invested) / total_invested) * 100, 2)
        if total_invested > 0
        else 0.0
    )

    # Aggregate by fund_type
    allocation: dict[str, dict] = {}
    target_map: dict[str, float] = {}
    for h in holdings:
        ft = h["fund_type"]
        val = h["current_value"] or h["invested_amount"]
        allocation[ft] = allocation.get(ft, 0.0) + val
        target_map[ft] = h["target_pct"]  # last one wins (same fund type)

    drift_alerts = []
    allocation_summary = {}
    for ft, val in allocation.items():
        current_pct = round((val / total_current) * 100, 2) if total_current > 0 else 0.0
        target_pct = target_map.get(ft, 0.0)
        drift = round(current_pct - target_pct, 2)
        allocation_summary[ft] = {
            "current_pct": current_pct,
            "target_pct": target_pct,
            "drift": drift,
            "current_value": round(val, 2),
        }
        if abs(drift) >= 3:
            direction = "over" if drift > 0 else "under"
            drift_alerts.append(f"{ft} is {abs(drift):.1f}% {direction} target")

    cash_available = float(cash.total_available) if cash else 0.0
    cash_deployed_pct = (
        round((float(cash.deployed_amount) / (cash_available + float(cash.deployed_amount))) * 100, 2)
        if cash and (cash_available + float(cash.deployed_amount)) > 0
        else 0.0
    )

    return {
        "total_invested": round(total_invested, 2),
        "current_value": round(total_current, 2),
        "overall_gain_loss_pct": total_gain_loss_pct,
        "cash_available": cash_available,
        "cash_deployed_pct": cash_deployed_pct,
        "allocation": allocation_summary,
        "drift_alerts": drift_alerts,
    }


async def update_cash_state(
    db: AsyncSession,
    total_available: float,
    deployed_amount: float,
    emergency_fund: float,
    notes: str | None = None,
) -> CashState:
    result = await db.execute(select(CashState).limit(1))
    cash = result.scalar_one_or_none()

    if cash is None:
        cash = CashState(
            total_available=total_available,
            deployed_amount=deployed_amount,
            emergency_fund=emergency_fund,
            notes=notes,
        )
        db.add(cash)
    else:
        cash.total_available = total_available
        cash.deployed_amount = deployed_amount
        cash.emergency_fund = emergency_fund
        if notes is not None:
            cash.notes = notes

    await db.flush()
    return cash
