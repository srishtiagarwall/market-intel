"""
Scrapes Nifty P/E and P/B from NSE India.
NSE publishes this daily at:
  https://www.nseindia.com/reports-indices-historical-vix-data

Primary source: NSE JSON API (unofficial but stable).
Falls back to cached value if scrape fails.
"""
import logging

import httpx

logger = logging.getLogger(__name__)

# NSE unofficial API endpoint for index P/E data
_NSE_PE_URL = (
    "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


async def get_nifty_pe_pb() -> tuple[float | None, float | None]:
    """
    Returns (pe, pb) for Nifty 50.
    Both can be None if the scrape fails (caller handles gracefully).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # NSE requires a session cookie — first hit the homepage
            await client.get("https://www.nseindia.com", headers=_HEADERS)
            resp = await client.get(_NSE_PE_URL, headers=_HEADERS)

        if resp.status_code != 200:
            logger.warning(f"NSE PE scrape: HTTP {resp.status_code}")
            return None, None

        data = resp.json()
        # The API returns index metadata; P/E is in data["data"][0]["pe"]
        records = data.get("data", [])
        if not records:
            logger.warning("NSE PE scrape: empty data array")
            return None, None

        # First record is Nifty 50 overall
        nifty_row = records[0]
        pe = _safe_float(nifty_row.get("pe"))
        pb = _safe_float(nifty_row.get("pb"))
        logger.info(f"NSE PE scrape: PE={pe}, PB={pb}")
        return pe, pb

    except Exception as e:
        logger.error(f"NSE PE scrape failed: {e}")
        return None, None


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if f != f else f
    except (TypeError, ValueError):
        return None
