import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AlertType(str, enum.Enum):
    mf_signal = "mf_signal"
    stock_signal = "stock_signal"


class AlertChannel(str, enum.Enum):
    telegram = "telegram"
    email = "email"


class AlertStatus(str, enum.Enum):
    sent = "sent"
    failed = "failed"


class AlertLog(Base):
    __tablename__ = "alert_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), nullable=False, index=True)
    ref_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # FK to signal row
    channel: Mapped[AlertChannel] = mapped_column(Enum(AlertChannel), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), nullable=False)
