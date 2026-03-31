import uuid
from datetime import datetime

from sqlalchemy import Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CashState(Base):
    __tablename__ = "cash_state"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    total_available: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    deployed_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    emergency_fund: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
