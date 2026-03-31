# Import all models so Alembic can detect them
from app.models.portfolio import Portfolio
from app.models.cash_state import CashState
from app.models.mf_signal import MFSignal
from app.models.stock_watchlist import StockWatchlist
from app.models.stock_signal import StockSignal, SignalLabel
from app.models.alert_log import AlertLog, AlertType, AlertChannel, AlertStatus

__all__ = [
    "Portfolio",
    "CashState",
    "MFSignal",
    "StockWatchlist",
    "StockSignal",
    "SignalLabel",
    "AlertLog",
    "AlertType",
    "AlertChannel",
    "AlertStatus",
]
