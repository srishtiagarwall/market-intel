"""
Fetches MF NAV history from MFAPI.in (free, reliable Indian MF API).
API docs: https://www.mfapi.in/

Usage:
  - get_latest_nav(scheme_code) → current NAV
  - get_nav_history(scheme_code, days) → list of (date, nav) for XIRR computation
"""
import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://api.mfapi.in/mf"


@dataclass
class NAVRecord:
    date: datetime
    nav: float


async def get_latest_nav(scheme_code: int) -> float | None:
    """Returns current NAV for a scheme. scheme_code from MFAPI."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{_BASE}/{scheme_code}")
        if resp.status_code != 200:
            logger.warning(f"MFAPI {scheme_code}: HTTP {resp.status_code}")
            return None
        data = resp.json()
        nav_data = data.get("data", [])
        if not nav_data:
            return None
        return float(nav_data[0]["nav"])
    except Exception as e:
        logger.error(f"MFAPI latest NAV failed for {scheme_code}: {e}")
        return None


async def get_nav_history(scheme_code: int, days: int = 365) -> list[NAVRecord]:
    """
    Returns NAV history for XIRR computation.
    Most recent first (as returned by MFAPI).
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{_BASE}/{scheme_code}")
        if resp.status_code != 200:
            return []
        data = resp.json()
        nav_data = data.get("data", [])

        records = []
        for row in nav_data[:days]:
            try:
                date = datetime.strptime(row["date"], "%d-%m-%Y")
                nav = float(row["nav"])
                records.append(NAVRecord(date=date, nav=nav))
            except (ValueError, KeyError):
                continue
        return records
    except Exception as e:
        logger.error(f"MFAPI history failed for {scheme_code}: {e}")
        return []


async def search_scheme(fund_name: str) -> list[dict]:
    """
    Search for a scheme code by fund name.
    Returns list of {schemeCode, schemeName} dicts.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{_BASE}/search?q={fund_name}")
        if resp.status_code != 200:
            return []
        return resp.json()
    except Exception as e:
        logger.error(f"MFAPI search failed for '{fund_name}': {e}")
        return []
