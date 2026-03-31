"""
Stock Signal scorer.

SHARED between production and backtest — no DB/Redis imports.
All inputs are plain Python dataclasses.
"""
from dataclasses import dataclass

from app.config import settings


@dataclass
class FundamentalInput:
    pe_ratio: float | None
    sector_median_pe: float | None
    roe: float | None
    debt_to_equity: float | None
    promoter_holding_pct: float | None
    promoter_holding_change: float | None  # QoQ change in %


@dataclass
class TechnicalInput:
    rsi_14: float | None
    vs_200dma_pct: float | None  # (price - 200DMA) / 200DMA * 100
    macd_histogram: float | None  # positive = bullish momentum


@dataclass
class EventInput:
    earnings_surprise_pct: float | None  # (actual - estimate) / estimate * 100
    news_sentiment: str  # "positive" | "neutral" | "negative"


@dataclass
class StockScoreInput:
    ticker: str
    current_price: float
    fundamental: FundamentalInput
    technical: TechnicalInput
    event: EventInput


@dataclass
class StockScoreOutput:
    ticker: str
    current_price: float
    fundamental_score: float   # 0–40
    technical_score: float     # 0–40
    event_score: float         # 0–20
    composite_score: float     # 0–100 (rescaled)
    signal_label: str          # strong_buy | buy | hold | sell
    reasoning: str
    rsi: float | None
    vs_200dma_pct: float | None
    macd_signal: str | None    # "bullish" | "bearish" | None


# ── Fundamental Scorer (max 40) ───────────────────────────────────────────────

def _score_pe(pe: float | None, sector_pe: float | None) -> float:
    """Max 15 points."""
    if pe is None:
        return 7.5
    if sector_pe and sector_pe > 0:
        discount = (sector_pe - pe) / sector_pe * 100
        if discount >= 20:
            return 15.0
        elif discount >= 10:
            return 10.0
        elif discount >= 0:
            return 7.0
        else:
            return 3.0
    else:
        if pe < 15:
            return 15.0
        elif pe < 20:
            return 10.0
        elif pe < 25:
            return 6.0
        else:
            return 2.0


def _score_roe(roe: float | None) -> float:
    """Max 10 points. ROE > 15% is the Buffett floor."""
    if roe is None:
        return 5.0
    if roe >= 25:
        return 10.0
    elif roe >= 15:
        return 8.0
    elif roe >= 10:
        return 5.0
    else:
        return 2.0


def _score_debt(de: float | None) -> float:
    """Max 10 points."""
    if de is None:
        return 5.0
    if de <= 0.3:
        return 10.0
    elif de <= 0.7:
        return 7.0
    elif de <= 1.0:
        return 4.0
    else:
        return 1.0


def _score_promoter(holding: float | None, change: float | None) -> float:
    """Max 5 points."""
    if holding is None:
        return 2.5
    score = 0.0
    if holding >= 60:
        score += 3.0
    elif holding >= 40:
        score += 2.0
    else:
        score += 1.0
    if change is not None:
        if change > 0:
            score += 2.0   # promoter buying = strong signal
        elif change < -1:
            score -= 1.0   # significant selling = red flag
        else:
            score += 0.5
    return round(min(score, 5.0), 2)


def compute_fundamental_score(inp: FundamentalInput) -> float:
    return round(
        min(
            _score_pe(inp.pe_ratio, inp.sector_median_pe)
            + _score_roe(inp.roe)
            + _score_debt(inp.debt_to_equity)
            + _score_promoter(inp.promoter_holding_pct, inp.promoter_holding_change),
            40.0,
        ),
        2,
    )


# ── Technical Scorer (max 40) ─────────────────────────────────────────────────

def compute_technical_score(inp: TechnicalInput) -> tuple[float, str | None]:
    """Returns (score, macd_signal_label)."""
    score = 0.0
    macd_signal = None

    # RSI (max 20)
    if inp.rsi_14 is not None:
        rsi = inp.rsi_14
        if rsi < 30:
            score += 20.0  # deeply oversold
        elif rsi < 40:
            score += 15.0
        elif rsi < 50:
            score += 8.0
        elif rsi < 60:
            score += 4.0
        # else: 0 — overbought

    # Distance from 200DMA (max 15)
    if inp.vs_200dma_pct is not None:
        pct = inp.vs_200dma_pct
        if pct < -15:
            score += 15.0  # deeply below 200DMA
        elif pct < -8:
            score += 12.0
        elif pct < 0:
            score += 8.0
        elif pct < 10:
            score += 4.0
        # else: 0 — far above 200DMA, risky entry

    # MACD histogram (max 5)
    if inp.macd_histogram is not None:
        if inp.macd_histogram > 0:
            score += 5.0
            macd_signal = "bullish"
        else:
            macd_signal = "bearish"

    return round(min(score, 40.0), 2), macd_signal


# ── Event Scorer (max 20) ─────────────────────────────────────────────────────

def compute_event_score(inp: EventInput) -> float:
    score = 0.0

    if inp.earnings_surprise_pct is not None:
        surp = inp.earnings_surprise_pct
        if surp >= 10:
            score += 10.0
        elif surp >= 5:
            score += 7.0
        elif surp >= 0:
            score += 4.0
        else:
            score -= 2.0  # earnings miss

    sentiment_map = {"positive": 10.0, "neutral": 5.0, "negative": 0.0}
    score += sentiment_map.get(inp.news_sentiment, 5.0)

    return round(min(max(score, 0.0), 20.0), 2)


# ── Composite + Label ─────────────────────────────────────────────────────────

def _composite_to_label(score: float) -> str:
    """
    Guard: never return buy/strong_buy if fundamental_score is very weak.
    This implements the CLAUDE.md rule: "never show BUY if fundamentals deteriorating."
    """
    threshold = settings.stock_signal_threshold
    if score >= 85:
        return "strong_buy"
    elif score >= threshold:
        return "buy"
    elif score >= 45:
        return "hold"
    else:
        return "sell"


def _build_reasoning(
    ticker: str,
    fund_score: float,
    tech_score: float,
    evt_score: float,
    rsi: float | None,
    vs_200dma: float | None,
    label: str,
) -> str:
    parts = []
    if rsi is not None and rsi < 40:
        parts.append(f"RSI at {rsi:.0f} — oversold territory.")
    if vs_200dma is not None and vs_200dma < 0:
        parts.append(f"Trading {abs(vs_200dma):.1f}% below 200DMA.")
    if fund_score >= 30:
        parts.append("Fundamentals strong.")
    elif fund_score <= 15:
        parts.append("Fundamentals weak — use caution.")
    if evt_score >= 15:
        parts.append("Recent earnings beat or positive news.")
    action = {
        "strong_buy": "High conviction accumulation zone.",
        "buy": "Accumulate on dips.",
        "hold": "Hold existing position. No fresh entry.",
        "sell": "Consider reducing position.",
    }.get(label, "")
    if action:
        parts.append(action)
    return " ".join(parts) or "Insufficient data for detailed reasoning."


# ── Main Entry Point ──────────────────────────────────────────────────────────

def score_stock_signal(inp: StockScoreInput) -> StockScoreOutput:
    """
    Main entry. Called by production daily job and backtest replay engine.
    """
    fund_score = compute_fundamental_score(inp.fundamental)
    tech_score, macd_signal = compute_technical_score(inp.technical)
    evt_score = compute_event_score(inp.event)

    w = settings
    weighted_sum = (
        fund_score * w.stock_fundamental_weight
        + tech_score * w.stock_technical_weight
        + evt_score * w.stock_event_weight
    )
    # Max weighted sum = 40*0.4 + 40*0.4 + 20*0.2 = 36 → rescale to 100
    composite_scaled = round((weighted_sum / 36.0) * 100, 2)

    # Guard: if fundamentals are very weak, cap at hold regardless of technical spike
    if fund_score < 12 and composite_scaled >= settings.stock_signal_threshold:
        composite_scaled = min(composite_scaled, 69.9)  # keep below buy threshold

    label = _composite_to_label(composite_scaled)
    reasoning = _build_reasoning(
        inp.ticker, fund_score, tech_score, evt_score,
        inp.technical.rsi_14, inp.technical.vs_200dma_pct, label,
    )

    return StockScoreOutput(
        ticker=inp.ticker,
        current_price=inp.current_price,
        fundamental_score=fund_score,
        technical_score=tech_score,
        event_score=evt_score,
        composite_score=composite_scaled,
        signal_label=label,
        reasoning=reasoning,
        rsi=inp.technical.rsi_14,
        vs_200dma_pct=inp.technical.vs_200dma_pct,
        macd_signal=macd_signal,
    )
