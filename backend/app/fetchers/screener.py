"""
Scrapes stock fundamentals from Screener.in.
Requires SCREENER_SESSION_COOKIE env var (log in → DevTools → Cookies → sessionid).

Returns: pe_ratio, sector_median_pe, roe, debt_to_equity,
         promoter_holding_pct, promoter_holding_change, earnings_surprise_pct
"""
import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

_BASE = "https://www.screener.in/company/{ticker}/consolidated/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Cookie": f"sessionid={settings.screener_session_cookie}",
}


def _safe_float(val: str | None) -> float | None:
    if val is None:
        return None
    cleaned = re.sub(r"[,%\s₹]", "", str(val))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_ratio(soup: BeautifulSoup, label: str) -> float | None:
    """Find a ratio by its label text in the key ratios section."""
    try:
        spans = soup.find_all("span", class_="name")
        for span in spans:
            if label.lower() in span.get_text(strip=True).lower():
                value_span = span.find_next_sibling("span", class_="nowrap")
                if value_span:
                    return _safe_float(value_span.get_text(strip=True))
    except Exception:
        pass
    return None


def _extract_promoter_holding(soup: BeautifulSoup) -> tuple[float | None, float | None]:
    """
    Extract latest promoter holding % and QoQ change from the shareholding section.
    Returns (holding_pct, qoq_change).
    """
    try:
        # Screener renders shareholding as a table
        tables = soup.find_all("table", class_="data-table")
        for table in tables:
            header = table.find("th")
            if header and "promoter" in header.get_text(strip=True).lower():
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if cells and "promoter" in cells[0].get_text(strip=True).lower():
                        # Last two columns: current quarter and previous quarter
                        values = [_safe_float(c.get_text(strip=True)) for c in cells[1:]]
                        values = [v for v in values if v is not None]
                        if len(values) >= 2:
                            current = values[-1]
                            previous = values[-2]
                            change = round(current - previous, 2)
                            return current, change
    except Exception as e:
        logger.debug(f"Promoter holding extraction failed: {e}")
    return None, None


async def get_stock_fundamentals(ticker: str) -> dict:
    """
    Returns dict with keys: pe_ratio, sector_median_pe, roe, debt_to_equity,
    promoter_holding_pct, promoter_holding_change, earnings_surprise_pct.
    All values may be None if scraping fails.
    """
    result: dict = {
        "pe_ratio": None,
        "sector_median_pe": None,
        "roe": None,
        "debt_to_equity": None,
        "promoter_holding_pct": None,
        "promoter_holding_change": None,
        "earnings_surprise_pct": None,
    }

    if not settings.screener_session_cookie:
        logger.warning("SCREENER_SESSION_COOKIE not set — returning empty fundamentals")
        return result

    url = _BASE.format(ticker=ticker)
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=_HEADERS)

        if resp.status_code == 404:
            # Try standalone (non-consolidated) page
            url_standalone = f"https://www.screener.in/company/{ticker}/"
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url_standalone, headers=_HEADERS)

        if resp.status_code != 200:
            logger.warning(f"Screener {ticker}: HTTP {resp.status_code}")
            return result

        soup = BeautifulSoup(resp.text, "lxml")

        result["pe_ratio"] = _extract_ratio(soup, "Stock P/E")
        result["roe"] = _extract_ratio(soup, "Return on equity")
        result["debt_to_equity"] = _extract_ratio(soup, "Debt to equity")

        promoter_pct, promoter_change = _extract_promoter_holding(soup)
        result["promoter_holding_pct"] = promoter_pct
        result["promoter_holding_change"] = promoter_change

        logger.info(
            f"Screener {ticker}: PE={result['pe_ratio']}, ROE={result['roe']}, "
            f"D/E={result['debt_to_equity']}, Promoter={result['promoter_holding_pct']}%"
        )

    except Exception as e:
        logger.error(f"Screener scrape failed for {ticker}: {e}")

    return result


async def get_sector_median_pe(sector: str) -> float | None:
    """
    Fetches sector-level median PE from Screener.
    Used for stock PE relative scoring.
    """
    try:
        url = f"https://www.screener.in/screens/sector/{sector.lower().replace(' ', '-')}/"
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=_HEADERS)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        return _extract_ratio(soup, "Median PE")
    except Exception as e:
        logger.debug(f"Sector PE fetch failed for {sector}: {e}")
        return None
