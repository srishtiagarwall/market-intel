"""
Fetches financial news headlines and classifies macro/stock sentiment.

Uses NewsAPI (free tier: 100 req/day).
Sentiment classification uses a lightweight HuggingFace FinBERT model
(ProsusAI/finbert) on first call — cached in memory after that.
"""
import logging
from functools import lru_cache

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_NEWSAPI_BASE = "https://newsapi.org/v2/everything"
_MACRO_QUERY = "Nifty OR Sensex OR RBI OR Indian stock market OR NSE"
_STOCK_QUERY_TEMPLATE = "{ticker} NSE stock earnings"

# Sentiment label mapping from FinBERT
_LABEL_MAP = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "POSITIVE": "positive",
    "NEGATIVE": "negative",
    "NEUTRAL": "neutral",
}


@lru_cache(maxsize=1)
def _load_sentiment_pipeline():
    """Load FinBERT once and cache. Lazy-loaded on first call."""
    try:
        from transformers import pipeline
        logger.info("Loading FinBERT sentiment model...")
        return pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            top_k=1,
        )
    except Exception as e:
        logger.error(f"Failed to load FinBERT: {e}")
        return None


def _classify_headlines(headlines: list[str]) -> str:
    """
    Returns "positive" | "neutral" | "negative" for a list of headlines.
    Majority vote across all headlines.
    Falls back to "neutral" if model unavailable.
    """
    if not headlines:
        return "neutral"

    pipe = _load_sentiment_pipeline()
    if pipe is None:
        return "neutral"

    try:
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for headline in headlines[:10]:  # cap at 10 to save tokens
            result = pipe(headline[:512])  # FinBERT max 512 tokens
            label = _LABEL_MAP.get(result[0][0]["label"], "neutral")
            counts[label] += 1
        return max(counts, key=lambda k: counts[k])
    except Exception as e:
        logger.error(f"Sentiment classification failed: {e}")
        return "neutral"


async def _fetch_headlines(query: str, page_size: int = 10) -> list[str]:
    if not settings.newsapi_key:
        logger.warning("NEWSAPI_KEY not set — returning empty headlines")
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                _NEWSAPI_BASE,
                params={
                    "q": query,
                    "language": "en",
                    "pageSize": page_size,
                    "sortBy": "publishedAt",
                    "apiKey": settings.newsapi_key,
                },
            )
        if resp.status_code != 200:
            logger.warning(f"NewsAPI: HTTP {resp.status_code}")
            return []
        articles = resp.json().get("articles", [])
        return [a["title"] for a in articles if a.get("title")]
    except Exception as e:
        logger.error(f"NewsAPI fetch failed: {e}")
        return []


async def get_macro_sentiment() -> str:
    """Returns "positive" | "neutral" | "negative" for overall market macro."""
    headlines = await _fetch_headlines(_MACRO_QUERY, page_size=10)
    return _classify_headlines(headlines)


async def get_stock_sentiment(ticker: str) -> tuple[str, float | None]:
    """
    Returns (sentiment, earnings_surprise_pct).
    earnings_surprise_pct is None — we don't parse it from news (Screener provides it).
    """
    query = _STOCK_QUERY_TEMPLATE.format(ticker=ticker)
    headlines = await _fetch_headlines(query, page_size=5)
    sentiment = _classify_headlines(headlines)
    return sentiment, None  # earnings_surprise comes from screener.py
