"""
Telegram alert service with deduplication.

Rule (from CLAUDE.md): never fire more than one alert per asset class per day.
Before sending, checks alert_log for a sent alert of the same type today.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot
from telegram.error import TelegramError

from app.config import settings
from app.models.alert_log import AlertLog, AlertType, AlertChannel, AlertStatus
from app.models.mf_signal import MFSignal
from app.models.stock_signal import StockSignal
from app.models.stock_watchlist import StockWatchlist

logger = logging.getLogger(__name__)


def _get_bot() -> Bot | None:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — alerts disabled")
        return None
    return Bot(token=settings.telegram_bot_token)


async def _already_alerted_today(db: AsyncSession, alert_type: AlertType) -> bool:
    """Returns True if we already sent an alert of this type today (IST day)."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(AlertLog.id)).where(
            AlertLog.alert_type == alert_type,
            AlertLog.status == AlertStatus.sent,
            AlertLog.sent_at >= today_start,
        )
    )
    count = result.scalar_one()
    return count > 0


async def _send_telegram(message: str) -> bool:
    """Sends a Telegram message. Returns True on success."""
    bot = _get_bot()
    if bot is None:
        return False
    try:
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return True
    except TelegramError as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def _log_alert(
    db: AsyncSession,
    alert_type: AlertType,
    ref_id,
    message: str,
    status: AlertStatus,
) -> None:
    log = AlertLog(
        alert_type=alert_type,
        ref_id=ref_id,
        channel=AlertChannel.telegram,
        message=message,
        status=status,
    )
    db.add(log)


async def maybe_send_mf_alert(
    db: AsyncSession,
    signal: MFSignal,
    threshold: float,
) -> None:
    """Send Telegram alert if MF score crosses threshold and not already alerted today."""
    if signal.composite_score < threshold:
        return

    if await _already_alerted_today(db, AlertType.mf_signal):
        logger.info("[AlertService] MF alert already sent today — skipping")
        return

    message = (
        f"*Market Intel — MF Signal*\n\n"
        f"Signal: `{signal.signal}`\n"
        f"Score: `{signal.composite_score:.1f}/100`\n"
        f"Nifty: ₹{signal.nifty_price:,.2f} "
        f"({signal.drawdown_pct:.1f}% below 52W high)\n"
        f"P/E: {signal.nifty_pe or 'N/A'}\n\n"
        f"_{signal.recommendation}_"
    )

    success = await _send_telegram(message)
    status = AlertStatus.sent if success else AlertStatus.failed
    await _log_alert(db, AlertType.mf_signal, signal.id, message, status)
    logger.info(f"[AlertService] MF alert {'sent' if success else 'failed'}")


async def maybe_send_stock_alert(
    db: AsyncSession,
    watchlist_item: StockWatchlist,
    signal: StockSignal,
    threshold: float,
) -> None:
    """Send Telegram alert if stock score crosses threshold and not already alerted today."""
    if signal.composite_score < threshold:
        return

    # Dedup: check if we already sent a stock_signal alert today for this ticker
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(AlertLog.id)).where(
            AlertLog.alert_type == AlertType.stock_signal,
            AlertLog.ref_id == watchlist_item.id,
            AlertLog.status == AlertStatus.sent,
            AlertLog.sent_at >= today_start,
        )
    )
    if result.scalar_one() > 0:
        logger.info(f"[AlertService] Stock alert for {watchlist_item.ticker} already sent today")
        return

    message = (
        f"*Market Intel — Stock Signal*\n\n"
        f"Ticker: `{watchlist_item.ticker}`"
        + (f" ({watchlist_item.company_name})" if watchlist_item.company_name else "")
        + f"\nSignal: `{signal.signal_label.value.upper()}`\n"
        f"Score: `{signal.composite_score:.1f}/100`\n"
        f"Price: ₹{signal.current_price:,.2f}\n"
        + (f"RSI: {signal.rsi:.0f}\n" if signal.rsi else "")
        + (f"vs 200DMA: {signal.vs_200dma_pct:.1f}%\n" if signal.vs_200dma_pct else "")
        + f"\n_{signal.reasoning}_"
    )

    success = await _send_telegram(message)
    status = AlertStatus.sent if success else AlertStatus.failed
    await _log_alert(db, AlertType.stock_signal, watchlist_item.id, message, status)
    logger.info(
        f"[AlertService] Stock alert for {watchlist_item.ticker} {'sent' if success else 'failed'}"
    )
