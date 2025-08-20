import json
import re
from datetime import datetime
from typing import Any, Optional

def normalize_date(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return str(date_str)

def parse_frequency(freq: Any) -> Optional[float]:
    if isinstance(freq, (int, float)):
        return float(freq)
    if isinstance(freq, str):
        f = freq.lower()
        if "semi" in f:
            return 2.0
        if "quarter" in f:
            return 4.0
        if "month" in f:
            return 12.0
        if "annual" in f or "year" in f:
            return 1.0
    return None

def has_bond_content(text: str) -> bool:
    indicators = [
        "notes", "bonds", "debentures", "indenture", "principal amount",
        "interest rate", "maturity", "senior", "subordinated", "convertible",
        "sofr", "libor", "floating rate", "rate reset",
    ]
    t = text.lower()
    return any(x in t for x in indicators)

def safe_json_loads(s: str) -> dict:
    """Accepts a string and tries to load JSON even if the model added stray text.
    - Finds the first {...} or [...]
    - Falls back to '{}' if nothing valid is found
    """
    s = s.strip()
    # Quick happy path
    try:
        return json.loads(s)
    except Exception:
        pass
    # Try to extract a JSON block
    m = re.search(r"(\{.*\}|\[.*\])", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return {}
