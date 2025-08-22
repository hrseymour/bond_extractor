import json
from bs4 import BeautifulSoup
import html
import re
from enum import Enum
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

def json_default(o):
    if isinstance(o, Enum):
        return o.value
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

def html_to_structured_text_re(raw: str) -> str:
    if not raw:
        return ""

    s = html.unescape(raw)

    # Normalize newlines up front
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # Drop scripts/styles
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)

    # <br> → hard line break
    s = re.sub(r"(?is)<br\s*/?>", "\n", s)

    # Lists
    s = re.sub(r"(?is)</li\s*>", "\n", s)          # end of bullet = newline
    s = re.sub(r"(?is)<li\b[^>]*>", "\n- ", s)     # bullet prefix
    s = re.sub(r"(?is)</?(ul|ol)\b[^>]*>", "\n", s)

    # Tables → light Markdown
    s = re.sub(r"(?is)</t[dh]\s*>", " | ", s)      # cell separators
    s = re.sub(r"(?is)</tr\s*>", "\n", s)          # row break
    s = re.sub(r"(?is)<t(?:able|head|body|r|d|h)\b[^>]*>", " ", s)

    # Paragraphs & headings: open = \n, close = \n\n (avoids double insertion)
    s = re.sub(r"(?is)<(p|h[1-6])\b[^>]*>", "\n", s)
    s = re.sub(r"(?is)</(p|h[1-6])\s*>", "\n\n", s)

    # Divs are layout wrappers → space (prevents mid-sentence hard breaks)
    s = re.sub(r"(?is)</?div\b[^>]*>", " ", s)

    # Strip any remaining tags
    s = re.sub(r"(?is)<[^>]+>", " ", s)

    # Unicode niceties
    s = s.replace("\u00A0", " ")                    # nbsp
    s = s.replace("\u2013", "-").replace("\u2014", "-")

    # Clean up table pipes at EOL
    s = re.sub(r"[ \t]*\|\s*(?=\n|$)", "", s)

    # Trim spaces around line breaks, then collapse runs
    s = re.sub(r"[ \t]*\n[ \t]*", "\n", s)          # trim around \n
    s = re.sub(r"\n{3,}", "\n\n", s)                # max one blank line
    s = re.sub(r"[ \t]{2,}", " ", s)                # collapse spaces
    s = re.sub(r"\n\n- ", "\n- ", s)                # no blank line before bullets

    # Put "Item X" section headers on their own line (light-touch)
    s = re.sub(r"(?mi)\s*(Item\s+\d+(?:\.\d+)*\s*[:\-–—]?)\s*", r"\n\1\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)                # re-collapse after Item rule

    return s.strip()

def html_to_structured_text_bs4(raw: str) -> str:
    """BeautifulSoup-based HTML→text: preserves useful structure for LLMs."""
    if not raw:
        return ""

    s = html.unescape(raw)

    # Use lxml if available (faster, more robust), otherwise builtin parser
    soup = BeautifulSoup(s, "lxml") if hasattr(BeautifulSoup, "builder") else BeautifulSoup(s, "html.parser")

    # Remove scripts/styles
    for t in soup(["script", "style"]):
        t.decompose()

    # <br> → newline
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # Lists: prefix bullets; replace <li> with text so we avoid nested formatting later
    for li in soup.find_all("li"):
        # get_text(" ", strip=True) keeps inline spacing sane
        li.replace_with("\n- " + li.get_text(" ", strip=True))

    # Tables → simple pipe-separated rows
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(" | ".join(cells))
        table_text = ("\n".join(rows)).strip()
        table.replace_with("\n" + table_text + "\n")

    # Headings / paragraphs → paragraph breaks
    for tag in soup.find_all(["p", "h1","h2","h3","h4","h5","h6", "section", "article"]):
        # Surround each with paragraph breaks; inner text keeps inline spacing
        tag.insert_before("\n")
        tag.insert_after("\n")

    # <div> often wraps flow text; treat it lightly: just a space between blocks
    for div in soup.find_all("div"):
        # If the div has block children, we already added breaks above.
        # Replace leftover simple divs with their text + a space separator.
        if not div.find(["p","h1","h2","h3","h4","h5","h6","section","article","table","ul","ol"]):
            div.insert_after(" ")
            div.unwrap()

    # At this point, soup contains mostly text and newlines.
    text = soup.get_text(" ", strip=False)

    # Normalize unicode and spacing
    text = text.replace("\u00A0", " ")
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    # Normalize newlines and spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)  # trim spaces around newlines
    text = re.sub(r"\n{3,}", "\n\n", text)        # max one blank line
    text = re.sub(r"[ \t]{2,}", " ", text)        # collapse runs of spaces

    # Tidy bullet spacing (avoid blank line before '- ')
    text = re.sub(r"\n\n- ", "\n- ", text)

    # Put "Item X" headers on their own line, then re-collapse
    text = re.sub(r"(?mi)\s*(Item\s+\d+(?:\.\d+)*\s*[:\-–—]?)\s*", r"\n\1\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
