import uuid
from datetime import datetime

from sqlalchemy import Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MFSignal(Base):
    __tablename__ = "mf_signals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    nifty_price: Mapped[float] = mapped_column(Numeric(10, 2))
    nifty_52w_high: Mapped[float] = mapped_column(Numeric(10, 2))
    drawdown_pct: Mapped[float] = mapped_column(Numeric(5, 2))
    nifty_pe: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    nifty_pb: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    drawdown_score: Mapped[float] = mapped_column(Numeric(5, 2))
    valuation_score: Mapped[float] = mapped_column(Numeric(5, 2))
    macro_score: Mapped[float] = mapped_column(Numeric(5, 2))
    composite_score: Mapped[float] = mapped_column(Numeric(5, 2))
    signal: Mapped[str] = mapped_column(String(20))  # WAIT | WATCH | CONSIDER | DEPLOY
    recommendation: Mapped[str] = mapped_column(Text)
    deploy_pct_hint: Mapped[float] = mapped_column(Numeric(5, 2))
    fund_allocation_hint: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
