import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SignalLabel(str, enum.Enum):
    strong_buy = "strong_buy"
    buy = "buy"
    hold = "hold"
    sell = "sell"


class StockSignal(Base):
    __tablename__ = "stock_signals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stock_watchlist.id"), nullable=False, index=True
    )
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    current_price: Mapped[float] = mapped_column(Numeric(10, 2))
    fundamental_score: Mapped[float] = mapped_column(Numeric(5, 2))
    technical_score: Mapped[float] = mapped_column(Numeric(5, 2))
    event_score: Mapped[float] = mapped_column(Numeric(5, 2))
    composite_score: Mapped[float] = mapped_column(Numeric(5, 2))
    signal_label: Mapped[SignalLabel] = mapped_column(Enum(SignalLabel), nullable=False)
    rsi: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    macd_signal: Mapped[str | None] = mapped_column(String(10), nullable=True)  # bullish | bearish
    vs_200dma_pct: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    pe_ratio: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    roe: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    reasoning: Mapped[str | None] = mapped_column(String(500), nullable=True)

    watchlist: Mapped["StockWatchlist"] = relationship(  # type: ignore[name-defined]
        "StockWatchlist", lazy="select"
    )
