"""
CAMS PDF statement parser.

CAMS sends a consolidated account statement (CAS) PDF monthly.
This parser extracts fund name, ISIN, units, NAV, invested amount, and purchase date.

Usage:
  holdings = parse_cams_pdf(pdf_bytes)
  # Returns list of dicts ready to upsert into users_portfolio
"""
import logging
import re
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

_DATE_FORMATS = ["%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y"]


def _parse_date(date_str: str) -> datetime | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _clean_amount(val: str) -> float | None:
    cleaned = re.sub(r"[₹,\s]", "", val)
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_cams_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Parse CAMS CAS PDF and extract fund transactions.

    Returns list of dicts with keys:
      fund_name, isin, units_held, purchase_nav, invested_amount,
      purchase_date, fund_type (inferred)

    Returns empty list if parsing fails.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber not installed — cannot parse CAMS PDF")
        return []

    holdings = []

    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        # CAMS PDF structure varies but typically has blocks like:
        # Fund Name (ISIN: INFxxxxxxxx)
        # Date | Units | NAV | Amount | ...

        # Extract ISIN blocks
        isin_pattern = re.compile(
            r"([\w\s&\-,()]+?)\s*\(ISIN[:\s]*(INF\w{10})\)",
            re.IGNORECASE,
        )

        # Transaction line pattern: date, description, units, nav, amount
        txn_pattern = re.compile(
            r"(\d{2}[-/]\w{2,3}[-/]\d{4})\s+"  # date
            r"[\w\s]+?\s+"                         # description (Purchase, etc.)
            r"([\d,]+\.\d+)\s+"                   # units
            r"([\d,]+\.\d+)\s+"                   # NAV
            r"([\d,]+\.\d+)"                       # amount
        )

        # Find all fund blocks
        fund_blocks = isin_pattern.finditer(full_text)
        for match in fund_blocks:
            fund_name = match.group(1).strip()
            isin = match.group(2).strip()

            # Get text after this ISIN until the next one
            start = match.end()
            next_match = isin_pattern.search(full_text, start)
            block_end = next_match.start() if next_match else len(full_text)
            block = full_text[start:block_end]

            # Find purchase transactions in this block
            for txn in txn_pattern.finditer(block):
                purchase_date = _parse_date(txn.group(1))
                if purchase_date is None:
                    continue
                units = _clean_amount(txn.group(2))
                nav = _clean_amount(txn.group(3))
                amount = _clean_amount(txn.group(4))

                if units is None or nav is None or amount is None:
                    continue

                holdings.append({
                    "fund_name": fund_name,
                    "isin": isin,
                    "units_held": units,
                    "purchase_nav": nav,
                    "invested_amount": amount,
                    "purchase_date": purchase_date.date(),
                    "fund_type": _infer_fund_type(fund_name),
                })

        logger.info(f"CAMS PDF: extracted {len(holdings)} transaction(s)")

    except Exception as e:
        logger.error(f"CAMS PDF parse failed: {e}")

    return holdings


def _infer_fund_type(fund_name: str) -> str:
    """Infer fund_type enum value from fund name string."""
    name_lower = fund_name.lower()
    if "small cap" in name_lower:
        return "small_cap"
    elif "mid cap" in name_lower or "midcap" in name_lower:
        return "mid_cap"
    elif "large & mid" in name_lower or "large and mid" in name_lower:
        return "large_mid"
    elif "flexi" in name_lower or "multi cap" in name_lower:
        return "flexi_cap"
    elif "index" in name_lower or "nifty" in name_lower or "sensex" in name_lower:
        return "index"
    else:
        return "large_cap"  # default
