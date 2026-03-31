import uuid
from datetime import datetime

from sqlalchemy import Boolean, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StockWatchlist(Base):
    __tablename__ = "stock_watchlist"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_buy_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    position_size: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())
