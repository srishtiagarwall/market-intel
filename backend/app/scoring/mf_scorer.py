"""
MF Timing Signal scorer.

SHARED between production signal engine and backtest — no DB/Redis imports.
Inputs/outputs are plain Python dataclasses only.
"""
from dataclasses import dataclass

from app.config import settings


@dataclass
class MFScoreInput:
    nifty_price: float
    nifty_52w_high: float
    nifty_pe: float | None
    nifty_pb: float | None
    macro_sentiment: str  # "positive" | "neutral" | "negative"


@dataclass
class MFScoreOutput:
    drawdown_pct: float
    drawdown_score: float
    valuation_score: float
    macro_score: float
    composite_score: float
    signal: str  # WAIT | WATCH | CONSIDER | DEPLOY
    deploy_pct_hint: float  # 0–100: % of idle cash to deploy
    fund_allocation_hint: dict[str, float]  # fund_type → suggested deploy %
    recommendation: str


def compute_drawdown_score(nifty_price: float, nifty_52w_high: float) -> tuple[float, float]:
    """Returns (drawdown_pct, score). Score out of mf_drawdown_max (40)."""
    if nifty_52w_high <= 0:
        return 0.0, 0.0

    drawdown_pct = ((nifty_52w_high - nifty_price) / nifty_52w_high) * 100
    max_score = settings.mf_drawdown_max

    if drawdown_pct >= 15:
        score = max_score           # 40 — strong buy zone
    elif drawdown_pct >= 10:
        score = max_score * 0.75    # 30
    elif drawdown_pct >= 5:
        score = max_score * 0.50    # 20
    else:
        score = 0.0

    return round(drawdown_pct, 2), round(score, 2)


def compute_valuation_score(pe: float | None, pb: float | None) -> float:
    """Score out of mf_valuation_max (40). Uses PE primary, PB fallback."""
    max_score = settings.mf_valuation_max

    if pe is not None:
        if pe < 18:
            return round(max_score, 2)           # 40 — historically cheap
        elif pe < 20:
            return round(max_score * 0.75, 2)   # 30
        elif pe < 22:
            return round(max_score * 0.50, 2)   # 20 — fair value
        elif pe < 24:
            return round(max_score * 0.25, 2)   # 10
        else:
            return 0.0                           # expensive

    if pb is not None:
        if pb < 3.0:
            return round(max_score * 0.75, 2)
        elif pb < 3.5:
            return round(max_score * 0.50, 2)
        else:
            return 0.0

    # No valuation data — neutral half-score
    return round(max_score * 0.50, 2)


def compute_macro_score(sentiment: str) -> float:
    """Score out of mf_macro_max (20)."""
    max_score = settings.mf_macro_max
    mapping = {
        "positive": max_score,
        "neutral": max_score * 0.50,
        "negative": 0.0,
    }
    return round(mapping.get(sentiment, max_score * 0.50), 2)


def _score_to_signal(score: float) -> tuple[str, float]:
    """Returns (signal_label, deploy_pct_hint)."""
    if score >= 80:
        return "DEPLOY", 50.0
    elif score >= settings.mf_signal_threshold:
        return "CONSIDER", 30.0
    elif score >= 40:
        return "WATCH", 0.0
    else:
        return "WAIT", 0.0


def _build_fund_allocation_hint(signal: str, drawdown_pct: float) -> dict[str, float]:
    """
    Priority order per CLAUDE.md: Large Cap → Flexi Cap → Large & Mid → Small Cap.
    Small Cap excluded when drawdown < 10%.
    """
    if signal == "WAIT":
        return {}
    if signal == "WATCH":
        return {}

    if drawdown_pct >= 10:
        # Full 4-fund deployment
        return {
            "large_cap": 40.0,
            "flexi_cap": 25.0,
            "large_mid": 20.0,
            "small_cap": 15.0,
        }
    else:
        # Drawdown 5–10%: exclude small cap
        return {
            "large_cap": 45.0,
            "flexi_cap": 30.0,
            "large_mid": 25.0,
        }


def _build_recommendation(out: "MFScoreOutput", pe: float | None) -> str:
    lines = []

    if out.drawdown_pct >= 10:
        lines.append(f"Nifty is {out.drawdown_pct:.1f}% below its 52-week high.")
    elif out.drawdown_pct >= 5:
        lines.append(f"Nifty has pulled back {out.drawdown_pct:.1f}% from peak.")
    else:
        lines.append("Nifty is near its 52-week high — limited margin of safety.")

    if pe:
        if pe < 18:
            lines.append(f"Valuation attractive: P/E at {pe:.1f} (below historical avg of 20–22).")
        elif pe < 22:
            lines.append(f"Valuation fair: P/E at {pe:.1f}.")
        else:
            lines.append(f"Valuation stretched: P/E at {pe:.1f} — be cautious.")

    if out.signal == "DEPLOY":
        lines.append(
            f"Signal: DEPLOY — consider investing ~{out.deploy_pct_hint:.0f}% of available "
            "capital. Prioritise Large Cap and Flexi Cap first."
        )
    elif out.signal == "CONSIDER":
        lines.append(
            f"Signal: CONSIDER — a measured deployment of ~{out.deploy_pct_hint:.0f}% "
            "of idle capital is reasonable. Stagger over 2–3 weeks."
        )
    elif out.signal == "WATCH":
        lines.append("Signal: WATCH — conditions improving but not yet compelling. Hold cash.")
    else:
        lines.append("Signal: WAIT — market expensive or macro unfavourable. Stay in cash.")

    return " ".join(lines)


def score_mf_signal(inp: MFScoreInput) -> MFScoreOutput:
    """
    Main entry point. Called by both production job and backtest replay engine.
    """
    drawdown_pct, drawdown_score = compute_drawdown_score(inp.nifty_price, inp.nifty_52w_high)
    valuation_score = compute_valuation_score(inp.nifty_pe, inp.nifty_pb)
    macro_score = compute_macro_score(inp.macro_sentiment)

    composite = round(drawdown_score + valuation_score + macro_score, 2)
    signal, deploy_pct_hint = _score_to_signal(composite)
    fund_allocation_hint = _build_fund_allocation_hint(signal, drawdown_pct)

    result = MFScoreOutput(
        drawdown_pct=drawdown_pct,
        drawdown_score=drawdown_score,
        valuation_score=valuation_score,
        macro_score=macro_score,
        composite_score=composite,
        signal=signal,
        deploy_pct_hint=deploy_pct_hint,
        fund_allocation_hint=fund_allocation_hint,
        recommendation="",
    )
    result.recommendation = _build_recommendation(result, inp.nifty_pe)
    return result
