from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MFSignalResponse(BaseModel):
    id: str
    computed_at: datetime
    nifty_price: float
    nifty_52w_high: float
    drawdown_pct: float
    nifty_pe: Optional[float]
    nifty_pb: Optional[float]
    drawdown_score: float
    valuation_score: float
    macro_score: float
    composite_score: float
    signal: str  # WAIT | WATCH | CONSIDER | DEPLOY
    recommendation: str
    deploy_pct_hint: float
    fund_allocation_hint: Optional[str]  # JSON string


class MFSignalHistoryItem(BaseModel):
    computed_at: datetime
    composite_score: float
    signal: str
    nifty_price: float
    drawdown_pct: float


class StockSignalResponse(BaseModel):
    id: str
    ticker: str
    company_name: Optional[str]
    computed_at: datetime
    current_price: float
    fundamental_score: float
    technical_score: float
    event_score: float
    composite_score: float
    signal_label: str  # strong_buy | buy | hold | sell
    rsi: Optional[float]
    macd_signal: Optional[str]
    vs_200dma_pct: Optional[float]
    pe_ratio: Optional[float]
    roe: Optional[float]
    reasoning: Optional[str]


class StockSignalSummary(BaseModel):
    ticker: str
    company_name: Optional[str]
    composite_score: float
    signal_label: str
    current_price: float
    rsi: Optional[float]
    vs_200dma_pct: Optional[float]
