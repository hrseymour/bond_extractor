import hashlib
from datetime import datetime
from typing import List, Dict, Any
from google import genai
from google.genai.types import GenerateContentConfig

from src.models import BondDetails
from src.utils import normalize_date, safe_json_loads

class GeminiBondExtractor:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._cache: Dict[str, List[BondDetails]] = {}

    def _prompt(self, text: str) -> str:
        return f"""You are an expert financial analyst specializing in bond markets and SEC filings.
Extract ALL bond information from this SEC filing. Return a JSON object with a top-level 'bonds' array.
Follow these normalization rules strictly.

REQUIRED STRUCTURE:
{{"bonds": [{{ /* fields omitted in prompt for brevity; see code */ }}]}}

RULES:
- Percentages to decimals: 5.25% -> 0.0525
- Bps to decimals: 215 bps -> 0.0215
- Millions/billions to numbers: $500M -> 500000000
- Time spans and intervals measured in months
- Dates must be YYYY-MM-DD
- Include extraction_confidence (0-1)

TEXT TO ANALYZE (truncated to 100k chars):
{text[:100000]}

Only return JSON, no extra commentary."""

    def _clean_bond_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Rates should be decimals
        for k in ["interest_rate", "rate_spread", "rate_floor", "rate_cap"]:
            v = data.get(k)
            if v is None:
                continue
            try:
                if isinstance(v, (int, float)) and v > 1:
                    data[k] = v / 100.0
            except Exception:
                pass

        # Dates -> ISO
        for k in [
            "next_reset_date","issue_date","dated_date","first_payment_date","maturity_date",
            "first_call_date", "first_put_date"           
        ]:
            if data.get(k):
                data[k] = normalize_date(data[k])

        return data

    def extract_bonds_from_text(self, text: str, filing_type: str) -> List[BondDetails]:
        key = hashlib.md5(text.encode()).hexdigest()
        if key in self._cache:
            return self._cache[key]

        resp = self.client.models.generate_content(
            model=self.model,
            contents=self._prompt(text),
            config=GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                max_output_tokens=8192,
            ),
        )

        payload = safe_json_loads(getattr(resp, "text", "") or "")
        bonds: List[BondDetails] = []
        for raw in payload.get("bonds", []):
            clean = self._clean_bond_data(dict(raw))
            # Filter to BondDetails fields
            bd = BondDetails(**{k: v for k, v in clean.items() if hasattr(BondDetails, k)})
            bd.filing_extracted_from = filing_type
            bd.extraction_timestamp = datetime.now().isoformat()
            bonds.append(bd)

        self._cache[key] = bonds
        return bonds
