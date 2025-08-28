import hashlib
import json
from pprint import pprint
from dataclasses import asdict, fields as dataclass_fields
from typing import List, Dict, Any
from google import genai
from google.genai.types import GenerateContentConfig

from src.models import (
    BondDetails,
    SecurityRank,
    CouponType,
    PaymentFrequency,
    RateBenchmark,
    RateChangeTrigger,
)
import src.utils as utils

# ---------------------------------------
# LLM Bond Extractor
# ---------------------------------------

class LLMBondExtractor:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    # ---------- Prompt building ----------

    def _allowed_enums(self) -> Dict[str, List[str]]:
        return {
            "SecurityRank": [e.value for e in SecurityRank],
            "CouponType": [e.value for e in CouponType],
            "PaymentFrequency": [e.value for e in PaymentFrequency],
            "RateBenchmark": [e.value for e in RateBenchmark],
            "RateChangeTrigger": [e.value for e in RateChangeTrigger],
        }

    def _schema_block(self) -> str:
        enums = self._allowed_enums()
        # Compact JSON-like template with comments describing each field.
        return f"""REQUIRED STRUCTURE (every field must appear; use null when unknown):
{{
  "bonds": [
    {{
      "cusip": null,                       /* string (9-char CUSIP) or null */
      "isin": null,                        /* string (12-char ISIN) or null */

      "security_type": null,               /* one of {enums['SecurityRank']} */
      "principal_amount": null,            /* number (e.g., 500000000 for $500M) */
      "currency": "USD",                   /* 3-letter code (default USD) */
      "face_value": null,                  /* number or null (par per note, most often 100, sometimes 25 for preferred) */

      "interest_rate": null,               /* decimal (e.g., 5.25% -> 0.0525) */
      "coupon_type": null,                 /* one of {enums['CouponType']} */
      "payment_frequency": null,           /* one of {enums['PaymentFrequency']} */

      "inflation_linked": null,            /* true/false or null */
      "inflation_lag_months": null,        /* integer months or null */
      "inflation_method": null,            /* short text, e.g., interpolation method */

      "rate_benchmark": null,              /* one of {enums['RateBenchmark']} or null */
      "rate_spread": null,                 /* decimal (e.g., 215 bps -> 0.0215) */
      "rate_floor": null,                  /* decimal or null */
      "rate_cap": null,                    /* decimal or null */
      "reset_frequency": null,             /* integer number of months (e.g., 3, 6, 12, 60) */
      
      "next_trigger_date": null,           /* YYYY-MM-DD or null (reset/step/switch date) */
      "rate_change_trigger": null,         /* one of {enums['RateChangeTrigger']} or null */
      "trigger_note": null,                /* short text (e.g., rating-based step-up) */

      "issue_date": null,                  /* YYYY-MM-DD or null */
      "first_payment_date": null,          /* YYYY-MM-DD or null */
      "maturity_date": null,               /* YYYY-MM-DD or null */
      "perpetual": null,                   /* true/false or null */

      "callable": null,                    /* true/false or null */
      "first_call_date": null,             /* YYYY-MM-DD or null */
      "call_price": null,                  /* number or null (e.g. 100 for at par) */
      "call_note": null,                   /* short text (e.g., overview of call terms) */

      "puttable": null,                    /* true/false or null */
      "first_put_date": null,              /* YYYY-MM-DD or null */
      "put_price": null,                   /* number or null (e.g. 103.5 for 3.5% premium over par) */
      "put_note": null,                    /* short text (e.g., overview of put terms, e.g. change of control) */

      "convertible": null,                 /* true/false or null */
      "conversion_price": null,            /* number or null */
      "conversion_ratio": null,            /* number or null */
      "conversion_note": null,             /* short text (e.g., overview of conversion terms) */

      "pik_allowed": null,                 /* true/false or null */
      "coco_at1_t2": null,                 /* true/false or null */

      "deferral_allowed": null,             /* true/false or null */
      "max_deferral_period": null,          /* integer number of months or null */
      "deferred_interest_cumulative": null  /* true/false or null */
    }}
  ]
}}"""

    def _rules_block(self) -> str:
        return (
            "RULES:\n"
            "- Output MUST be valid JSON matching the structure above.\n"
            "- Use ONLY the keys listed; do NOT invent new keys.\n"
            "- If data is not present, include the key with null.\n"
            "- Convert percentages to decimals (e.g., 6.95% -> 0.0695).\n"
            "- Convert basis points to decimals (e.g., 289 bps -> 0.0289).\n"
            "- Convert millions/billions to absolute numbers ($500M -> 500000000).\n"
            "- Express time intervals in MONTHS (e.g., 5 years -> 60).\n"
            "- All dates must be YYYY-MM-DD.\n"
            f"- For enums use EXACT values from: SecurityRank, CouponType, PaymentFrequency, RateBenchmark, RateChangeTrigger."
        )

    def _prompt(self, text: str) -> str:
        return (
            "You are an expert financial analyst specializing in bond markets and SEC filings.\n"
            "Extract ALL bond information from this SEC filing.\n"
            + self._schema_block() + "\n\n"
            + self._rules_block() + "\n\n"
            + "TEXT TO ANALYZE (truncated to 100k chars):\n"
            + text[:100000] + "\n\n"
            + "Only return JSON, no extra commentary."
        )

    # ---------- Normalization / coercion ----------

    def _clean_bond_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Rates -> decimals if accidentally given as percent-like numbers
        for k in ["interest_rate", "rate_spread", "rate_floor", "rate_cap",
                  "call_price_pct_of_face", "put_price_pct_of_face"
                  ]:
            data[k] = utils.from_percent(data.get(k))

        # Time spans -> ints
        for k in ["reset_frequency", "max_deferral_period"]:
            data[k] = utils.to_int(data.get(k))

        # Booleans
        for k in ["inflation_linked", "perpetual", "callable", "puttable",
                  "convertible", "pik_allowed", "coco_at1_t2"
                  "deferral_allowed", "deferred_interest_cumulative"
                  ]:
            data[k] = utils.to_bool(data.get(k))

        # Dates -> ISO
        for k in [
            "next_trigger_date", "issue_date", "first_payment_date", "maturity_date",
            "first_call_date", "first_put_date"
        ]:
            data[k] = utils.normalize_date(data[k])

        # Currency and face value defaults
        if not data.get("currency"):
            data["currency"] = "USD"
        if not data.get("face_value"):
            data["face_value"] = 1000.0

        return data

    def _coerce_enums(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["security_type"] = utils.coerce_enum(SecurityRank, data.get("security_type"))
        data["coupon_type"] = utils.coerce_enum(CouponType, data.get("coupon_type"))
        data["payment_frequency"] = utils.coerce_enum(PaymentFrequency, data.get("payment_frequency"))
        data["rate_benchmark"] = utils.coerce_enum(RateBenchmark, data.get("rate_benchmark"))
        data["rate_change_trigger"] = utils.coerce_enum(RateChangeTrigger, data.get("rate_change_trigger"))
        return data

    def _normalize_and_validate(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure only fields defined on BondDetails are passed and every field exists
        expected = {f.name for f in dataclass_fields(BondDetails)}
        clean: Dict[str, Any] = {k: raw.get(k, None) for k in expected}
        clean = self._clean_bond_data(clean)
        clean = self._coerce_enums(clean)
        return clean

    # ---------- Public API ----------

    def extract_bonds_from_text(self, text: str, filing_type: str) -> List[Dict[str, Any]]:
        key = hashlib.md5(text.encode()).hexdigest()
        if key in self._cache:
            return self._cache[key]

        # Gemini
        resp = self.client.models.generate_content(
            model=self.model,
            contents=self._prompt(text),
            config=GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                max_output_tokens=8192,
            ),
        )

        payload = utils.safe_json_loads(getattr(resp, "text", "") or "") or {}
        bonds_json = payload.get("bonds", [])
        if not isinstance(bonds_json, list):
            bonds_json = []

        bonds: List[Dict[str, Any]] = []
        for raw in bonds_json:
            if not isinstance(raw, dict):
                continue
            clean = self._normalize_and_validate(raw)
            try:
                bd = BondDetails(**clean)
            except TypeError:
                # As a final safety, drop any unexpected keys and retry
                expected = {f.name for f in dataclass_fields(BondDetails)}
                minimal = {k: v for k, v in clean.items() if k in expected}
                bd = BondDetails(**minimal)
                
            js = json.loads(json.dumps(asdict(bd), default= utils.json_default))
            pprint(js)
            bonds.append(js)

        self._cache[key] = bonds
        return bonds
