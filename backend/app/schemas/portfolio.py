from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.portfolio import FundType


class AddHoldingRequest(BaseModel):
    fund_name: str = Field(..., min_length=1, max_length=100)
    fund_type: FundType
    isin: Optional[str] = None
    invested_amount: float = Field(..., gt=0)
    units_held: float = Field(..., gt=0)
    purchase_nav: float = Field(..., gt=0)
    purchase_date: date
    target_pct: float = Field(default=0.0, ge=0, le=100)


class HoldingResponse(BaseModel):
    id: str
    fund_name: str
    fund_type: str
    isin: Optional[str]
    invested_amount: float
    units_held: float
    purchase_nav: float
    purchase_date: str
    target_pct: float
    current_nav: Optional[float]
    current_value: Optional[float]
    gain_loss_pct: Optional[float]


class CashStateRequest(BaseModel):
    total_available: float = Field(..., ge=0)
    deployed_amount: float = Field(..., ge=0)
    emergency_fund: float = Field(..., ge=0)
    notes: Optional[str] = None


class AllocationEntry(BaseModel):
    current_pct: float
    target_pct: float
    drift: float
    current_value: float


class PortfolioHealthResponse(BaseModel):
    total_invested: float
    current_value: float
    overall_gain_loss_pct: float
    cash_available: float
    cash_deployed_pct: float
    allocation: dict[str, AllocationEntry]
    drift_alerts: list[str]
