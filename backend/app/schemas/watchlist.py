from typing import Optional

from pydantic import BaseModel, Field


class AddWatchlistRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    sector: Optional[str] = None
    target_buy_price: Optional[float] = Field(default=None, gt=0)
    position_size: Optional[float] = Field(default=None, gt=0)


class WatchlistItemResponse(BaseModel):
    id: str
    ticker: str
    company_name: Optional[str]
    sector: Optional[str]
    target_buy_price: Optional[float]
    position_size: Optional[float]
    is_active: bool
    added_at: str
