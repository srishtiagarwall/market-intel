"""
Daily 4PM IST signal computation pipeline.

Flow:
  1. Fetch Nifty snapshot + PE/PB from NSE
  2. Fetch macro news → NLP sentiment
  3. Compute MF signal → persist → check alert threshold
  4. For each active watchlist ticker:
       Fetch technicals + fundamentals + news
       Compute stock signal → persist → check alert threshold
  5. Send Telegram alerts if thresholds crossed and not already alerted today
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionFactory
from app.fetchers.yahoo_finance import get_nifty_snapshot, get_stock_technicals
from app.fetchers.nse_scraper import get_nifty_pe_pb
from app.fetchers.news_fetcher import get_macro_sentiment, get_stock_sentiment
from app.fetchers.screener import get_stock_fundamentals
from app.scoring.mf_scorer import score_mf_signal, MFScoreInput
from app.scoring.stock_scorer import (
    score_stock_signal,
    StockScoreInput,
    FundamentalInput,
    TechnicalInput,
    EventInput,
)
from app.models.mf_signal import MFSignal
from app.models.stock_signal import StockSignal, SignalLabel
from app.models.stock_watchlist import StockWatchlist
from app.services.alert_service import maybe_send_mf_alert, maybe_send_stock_alert
from app.config import settings

logger = logging.getLogger(__name__)


async def run_daily_signal_job() -> None:
    logger.info(f"[DailySignalJob] Starting at {datetime.now(timezone.utc).isoformat()}")

    async with AsyncSessionFactory() as db:
        try:
            await _compute_mf_signal(db)
            await _compute_stock_signals(db)
            await db.commit()
        except Exception as e:
            logger.error(f"[DailySignalJob] Failed: {e}", exc_info=True)
            await db.rollback()

    logger.info("[DailySignalJob] Complete.")


async def _compute_mf_signal(db) -> None:
    logger.info("[MFSignal] Fetching data...")

    nifty = get_nifty_snapshot()
    if nifty is None:
        logger.error("[MFSignal] Could not fetch Nifty snapshot. Skipping MF signal.")
        return

    pe, pb = await get_nifty_pe_pb()
    sentiment = await get_macro_sentiment()

    inp = MFScoreInput(
        nifty_price=nifty.price,
        nifty_52w_high=nifty.high_52w,
        nifty_pe=pe,
        nifty_pb=pb,
        macro_sentiment=sentiment,
    )
    result = score_mf_signal(inp)

    signal_row = MFSignal(
        nifty_price=nifty.price,
        nifty_52w_high=nifty.high_52w,
        drawdown_pct=result.drawdown_pct,
        nifty_pe=pe,
        nifty_pb=pb,
        drawdown_score=result.drawdown_score,
        valuation_score=result.valuation_score,
        macro_score=result.macro_score,
        composite_score=result.composite_score,
        signal=result.signal,
        recommendation=result.recommendation,
        deploy_pct_hint=result.deploy_pct_hint,
        fund_allocation_hint=json.dumps(result.fund_allocation_hint) if result.fund_allocation_hint else None,
    )
    db.add(signal_row)
    await db.flush()

    logger.info(
        f"[MFSignal] Score={result.composite_score} Signal={result.signal} "
        f"Drawdown={result.drawdown_pct}% PE={pe}"
    )

    await maybe_send_mf_alert(db, signal_row, settings.mf_signal_threshold)


async def _compute_stock_signals(db) -> None:
    result = await db.execute(
        select(StockWatchlist).where(StockWatchlist.is_active == True)
    )
    watchlist = result.scalars().all()

    if not watchlist:
        logger.info("[StockSignal] Watchlist is empty. Skipping.")
        return

    logger.info(f"[StockSignal] Processing {len(watchlist)} tickers...")

    for item in watchlist:
        try:
            await _compute_single_stock_signal(db, item)
        except Exception as e:
            logger.error(f"[StockSignal] Failed for {item.ticker}: {e}", exc_info=True)
            continue


async def _compute_single_stock_signal(db, item: StockWatchlist) -> None:
    ticker = item.ticker

    technicals = get_stock_technicals(ticker)
    if technicals is None:
        logger.warning(f"[StockSignal] No technicals for {ticker}. Skipping.")
        return

    fund_data = await get_stock_fundamentals(ticker)
    news_sentiment, earnings_surprise = await get_stock_sentiment(ticker)

    inp = StockScoreInput(
        ticker=ticker,
        current_price=technicals.current_price,
        fundamental=FundamentalInput(
            pe_ratio=fund_data.get("pe_ratio"),
            sector_median_pe=fund_data.get("sector_median_pe"),
            roe=fund_data.get("roe"),
            debt_to_equity=fund_data.get("debt_to_equity"),
            promoter_holding_pct=fund_data.get("promoter_holding_pct"),
            promoter_holding_change=fund_data.get("promoter_holding_change"),
        ),
        technical=TechnicalInput(
            rsi_14=technicals.rsi_14,
            vs_200dma_pct=technicals.vs_200dma_pct,
            macd_histogram=technicals.macd_histogram,
        ),
        event=EventInput(
            earnings_surprise_pct=earnings_surprise,
            news_sentiment=news_sentiment,
        ),
    )
    result = score_stock_signal(inp)

    signal_row = StockSignal(
        watchlist_id=item.id,
        current_price=result.current_price,
        fundamental_score=result.fundamental_score,
        technical_score=result.technical_score,
        event_score=result.event_score,
        composite_score=result.composite_score,
        signal_label=SignalLabel(result.signal_label),
        rsi=result.rsi,
        macd_signal=result.macd_signal,
        vs_200dma_pct=result.vs_200dma_pct,
        pe_ratio=fund_data.get("pe_ratio"),
        roe=fund_data.get("roe"),
        reasoning=result.reasoning,
    )
    db.add(signal_row)
    await db.flush()

    logger.info(
        f"[StockSignal] {ticker}: score={result.composite_score} label={result.signal_label}"
    )

    await maybe_send_stock_alert(db, item, signal_row, settings.stock_signal_threshold)
