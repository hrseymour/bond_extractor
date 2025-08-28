import json
from bs4 import BeautifulSoup
import html
import re
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional

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

# ---------- Normalization / coercion ----------

def from_percent(v: Any):
    # Rates -> decimals if accidentally given as percent-like numbers
    if v is None:
        return v
    try:
        if isinstance(v, str) and v.endswith("%"):
            # e.g., "6.95%"
            num = float(v.strip().strip("%"))
            return num / 100.0
        if isinstance(v, (int, float)) and v > 1.0:
            # Treat as percent only if clearly > 1
            return v / 100.0
    except Exception:
        pass
    
    return v

def to_int(v: Any):
    # Time spans -> ints
    if v is None:
        return v
    try:
        return int(float(v))
    except Exception:
        return None

def to_bool(v: Any) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in {"true", "t", "yes", "y"}:
        return True
    if s in {"false", "f", "no", "n"}:
        return False
    return None

def coerce_enum(enum_cls, v: Any):
    if v is None or isinstance(v, enum_cls):
        return v
    # accept exact value, case-insensitive value, and some common aliases
    s = str(v).strip()
    # try exact value match
    for e in enum_cls:
        if s == e.value:
            return e
    # try case-insensitive
    for e in enum_cls:
        if s.lower() == e.value.lower():
            return e
    # common alias normalizations
    alias = s.replace("-", "").replace(" ", "").replace("_", "")
    for e in enum_cls:
        if alias.lower() == e.value.replace("-", "").replace(" ", "").replace("_", "").lower():
            return e
    return None

def safe_json_loads(s: str) -> Dict[str, Any]:
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

def json_default(o):
    if isinstance(o, Enum):
        return o.value
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
