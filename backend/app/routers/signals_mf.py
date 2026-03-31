import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.signals import MFSignalResponse, MFSignalHistoryItem

logger = logging.getLogger(__name__)
router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/latest", response_model=MFSignalResponse)
async def latest_mf_signal(db: DB):
    from app.models.mf_signal import MFSignal

    result = await db.execute(
        select(MFSignal).order_by(desc(MFSignal.computed_at)).limit(1)
    )
    signal = result.scalar_one_or_none()
    if signal is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No MF signal computed yet. Run the job first.")

    return {
        "id": str(signal.id),
        "computed_at": signal.computed_at,
        "nifty_price": float(signal.nifty_price),
        "nifty_52w_high": float(signal.nifty_52w_high),
        "drawdown_pct": float(signal.drawdown_pct),
        "nifty_pe": float(signal.nifty_pe) if signal.nifty_pe else None,
        "nifty_pb": float(signal.nifty_pb) if signal.nifty_pb else None,
        "drawdown_score": float(signal.drawdown_score),
        "valuation_score": float(signal.valuation_score),
        "macro_score": float(signal.macro_score),
        "composite_score": float(signal.composite_score),
        "signal": signal.signal,
        "recommendation": signal.recommendation,
        "deploy_pct_hint": float(signal.deploy_pct_hint),
        "fund_allocation_hint": signal.fund_allocation_hint,
    }


@router.get("/history", response_model=list[MFSignalHistoryItem])
async def mf_signal_history(
    db: DB,
    days: int = Query(default=30, ge=1, le=365),
):
    from app.models.mf_signal import MFSignal
    from datetime import datetime, timedelta

    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(MFSignal)
        .where(MFSignal.computed_at >= since)
        .order_by(desc(MFSignal.computed_at))
    )
    signals = result.scalars().all()

    return [
        {
            "computed_at": s.computed_at,
            "composite_score": float(s.composite_score),
            "signal": s.signal,
            "nifty_price": float(s.nifty_price),
            "drawdown_pct": float(s.drawdown_pct),
        }
        for s in signals
    ]


@router.post("/trigger")
async def trigger_mf_signal(db: DB):
    """Manually trigger signal recompute. For testing/admin use."""
    from app.scheduler.daily_signal_job import run_daily_signal_job
    import asyncio

    asyncio.create_task(run_daily_signal_job())
    return {"status": "job_queued", "message": "Signal recomputation triggered in background."}
