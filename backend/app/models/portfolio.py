import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

import enum


class FundType(str, enum.Enum):
    large_cap = "large_cap"
    large_mid = "large_mid"
    mid_cap = "mid_cap"
    small_cap = "small_cap"
    flexi_cap = "flexi_cap"
    index = "index"


class Portfolio(Base):
    __tablename__ = "users_portfolio"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fund_name: Mapped[str] = mapped_column(String(100), nullable=False)
    fund_type: Mapped[FundType] = mapped_column(Enum(FundType), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    invested_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    units_held: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    purchase_nav: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    target_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
