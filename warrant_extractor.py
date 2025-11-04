import hashlib
import json
from pprint import pprint
from dataclasses import asdict, fields as dataclass_fields
from typing import List, Dict, Any
from google import genai
from google.genai.types import GenerateContentConfig

from src.warrant_models import (
    WarrantDetails,
    WarrantType,
    ExerciseType,
    SettlementType,
    AntiDilutionType,
    WarrantClass,
)
import src.utils as utils

# ---------------------------------------
# LLM Warrant Extractor
# ---------------------------------------

class LLMWarrantExtractor:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    # ---------- Prompt building ----------

    def _allowed_enums(self) -> Dict[str, List[str]]:
        return {
            "WarrantType": [e.value for e in WarrantType],
            "ExerciseType": [e.value for e in ExerciseType],
            "SettlementType": [e.value for e in SettlementType],
            "AntiDilutionType": [e.value for e in AntiDilutionType],
            "WarrantClass": [e.value for e in WarrantClass],
        }

    def _schema_block(self) -> str:
        enums = self._allowed_enums()
        return f"""REQUIRED STRUCTURE (every field must appear; use null when unknown):
{{
  "warrants": [
    {{
      "symbol": null,                       /* string (e.g., 'DSX WS') or null */
      "isin": null,                         /* string (12-char ISIN) or null */
      "exchange": null,                     /* string (e.g., 'NYSE', 'NASDAQ') or null */
      "invalid_symbol": null,               /* true/false or null */
      "parent": null,                       /* string (underlying stock symbol, e.g., 'DSX') */
      "currency": "USD",                    /* 3-letter code (default USD) */

      "issue_date": null,                   /* YYYY-MM-DD or null */
      "expiration_date": null,              /* YYYY-MM-DD or null (use '2199-12-31' for perpetual) */
      "strike_price": null,                 /* decimal (exercise price per warrant) */
      "conversion_ratio": null,             /* decimal (shares per warrant, default 1.0) */
      "warrant_type": null,                 /* one of {enums['WarrantType']} */

      "prev_close": null,                   /* decimal or null (market quote - usually null from SEC) */
      "last_trade": null,                   /* decimal or null */
      "last_trade_date": null,              /* YYYY-MM-DD or null */

      "exercise_type": null,                /* one of {enums['ExerciseType']} */
      "first_exercise_date": null,          /* YYYY-MM-DD or null */
      "is_callable": null,                  /* true/false or null */
      "is_putable": null,                   /* true/false or null */

      "settlement_type": null,              /* one of {enums['SettlementType']} */
      "settlement_days": null,              /* integer or null (typically 3) */

      "allows_cashless_exercise": null,     /* true/false or null */
      "cashless_exercise_formula": null,    /* short text or null */

      "has_call_trigger": null,             /* true/false or null */
      "call_trigger_price": null,           /* decimal or null */
      "call_trigger_days": null,            /* integer or null (e.g., 20 days) */
      "call_trigger_period": null,          /* integer or null (e.g., 30 days) */
      "call_trigger_notice_days": null,     /* integer or null */
      "call_redemption_price": null,        /* decimal or null (e.g., 0.01) */
      "call_trigger_start_date": null,      /* YYYY-MM-DD or null */
      "call_trigger_end_date": null,        /* YYYY-MM-DD or null */
      "call_trigger_additional_conditions": null, /* short text or null */

      "has_acceleration_trigger": null,     /* true/false or null */
      "accel_trigger_price": null,          /* decimal or null */
      "accel_trigger_days": null,           /* integer or null */
      "accel_trigger_period": null,         /* integer or null */
      "accel_trigger_effect": null,         /* short text or null */

      "has_anti_dilution": null,            /* true/false or null */
      "anti_dilution_type": null,           /* one of {enums['AntiDilutionType']} or null */
      "anti_dilution_details": null,        /* short text or null */

      "adjusts_for_dividends": null,        /* true/false or null */
      "dividend_threshold": null,           /* decimal or null */
      "adjusts_for_stock_splits": null,     /* true/false or null */
      "adjusts_for_mergers": null,          /* true/false or null */
      "adjusts_for_spinoffs": null,         /* true/false or null */
      "adjusts_for_rights_offerings": null, /* true/false or null */

      "fundamental_transaction_provision": null, /* short text or null */
      "change_of_control_provision": null,       /* short text or null */

      "is_transferable": null,              /* true/false or null */
      "transfer_restrictions": null,        /* short text or null */
      "is_publicly_traded": null,           /* true/false or null */

      "has_registration_rights": null,      /* true/false or null */
      "registration_details": null,         /* short text or null */

      "has_ownership_limit": null,          /* true/false or null */
      "ownership_limit_pct": null,          /* decimal (e.g., 4.99 or 9.99) or null */
      "ownership_limit_waiver": null,       /* short text or null */

      "is_detachable": null,                /* true/false or null */
      "original_issue_price": null,         /* decimal or null */
      "issued_with_security": null,         /* short text (e.g., 'Common Stock', 'Bond') or null */

      "issuer_cik": null,                   /* string (10-digit CIK) or null */
      "warrant_agreement_url": null,        /* URL string or null */
      "prospectus_supplement_url": null,    /* URL string or null */

      "is_extendable": null,                /* true/false or null */
      "extension_conditions": null,         /* short text or null */
      "has_knock_out_provision": null,      /* true/false or null */
      "knock_out_details": null,            /* short text or null */
      "has_knock_in_provision": null,       /* true/false or null */
      "knock_in_details": null,             /* short text or null */

      "spac_related": null,                 /* true/false or null */
      "warrant_class": null,                /* one of {enums['WarrantClass']} or null */
      "vintage": null,                      /* short text (e.g., '2023 SPAC') or null */
      "notes": null                         /* free-form text for anything that doesn't fit */
    }}
  ]
}}"""

    def _rules_block(self) -> str:
        return (
            "RULES:\n"
            "- Output MUST be valid JSON matching the structure above.\n"
            "- Use ONLY the keys listed; do NOT invent new keys.\n"
            "- If data is not present, include the key with null.\n"
            "- Convert percentages to decimals (e.g., 4.99% -> 0.0499).\n"
            "- Convert dollars to decimals (e.g., $11.50 -> 11.50).\n"
            "- Express conversion_ratio as decimal (e.g., 1.66585 shares per warrant).\n"
            "- All dates must be YYYY-MM-DD.\n"
            "- For call triggers, extract the pattern: 'X out of Y days above $Z'.\n"
            "- If warrant agreement describes multiple warrant classes (Public/Private/Founder), create separate entries.\n"
            f"- For enums use EXACT values from: WarrantType, ExerciseType, SettlementType, AntiDilutionType, WarrantClass.\n"
            "- Pay special attention to redemption/call provisions - these are critical.\n"
            "- If you find terms that don't fit the schema, put them in 'notes'."
        )

    def _prompt(self, text: str, parent_ticker: str) -> str:
        return (
            "You are an expert financial analyst specializing in equity warrants and SEC filings.\n"
            "Extract ALL warrant information from this SEC filing.\n"
            f"The underlying stock (parent) ticker is: {parent_ticker}\n\n"
            "CRITICAL WARRANT FEATURES TO LOOK FOR:\n"
            "1. CALL/REDEMPTION TRIGGERS: Look for phrases like 'may redeem if stock trades at or above $X for Y out of Z days'\n"
            "2. STRIKE PRICE: The exercise price (often $11.50 for SPACs)\n"
            "3. EXPIRATION: When warrants expire (often 5 years from issuance for SPACs)\n"
            "4. CONVERSION RATIO: How many shares per warrant (usually 1.0, but can vary)\n"
            "5. ANTI-DILUTION: Adjustments for stock splits, dividends, etc.\n"
            "6. CASHLESS EXERCISE: Can holders exercise without paying cash?\n\n"
            + self._schema_block() + "\n\n"
            + self._rules_block() + "\n\n"
            + "TEXT TO ANALYZE (truncated to 64k chars):\n"
            + text[:65536] + "\n\n"
            + "Only return JSON, no extra commentary."
        )

    # ---------- Normalization / coercion ----------

    def _clean_warrant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Prices -> decimals
        for k in ["strike_price", "call_trigger_price", "accel_trigger_price",
                  "call_redemption_price", "dividend_threshold", "ownership_limit_pct",
                  "original_issue_price", "prev_close", "last_trade", "conversion_ratio",
                  "call_price", "put_price", "conversion_price", "conversion_ratio"]:
            data[k] = utils.from_percent(data.get(k))

        # Integers
        for k in ["settlement_days", "call_trigger_days", "call_trigger_period",
                  "call_trigger_notice_days", "accel_trigger_days", "accel_trigger_period"]:
            data[k] = utils.to_int(data.get(k))

        # Booleans
        for k in ["invalid_symbol", "is_callable", "is_putable", "allows_cashless_exercise",
                  "has_call_trigger", "has_acceleration_trigger", "has_anti_dilution",
                  "adjusts_for_dividends", "adjusts_for_stock_splits", "adjusts_for_mergers",
                  "adjusts_for_spinoffs", "adjusts_for_rights_offerings", "is_transferable",
                  "is_publicly_traded", "has_registration_rights", "has_ownership_limit",
                  "is_detachable", "is_extendable", "has_knock_out_provision",
                  "has_knock_in_provision", "spac_related"]:
            data[k] = utils.to_bool(data.get(k))

        # Dates -> ISO
        for k in ["issue_date", "expiration_date", "last_trade_date", "first_exercise_date",
                  "call_trigger_start_date", "call_trigger_end_date"]:
            data[k] = utils.normalize_date(data.get(k))

        # Defaults
        if not data.get("currency"):
            data["currency"] = "USD"
        if not data.get("conversion_ratio"):
            data["conversion_ratio"] = 1.0

        return data

    def _coerce_enums(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["warrant_type"] = utils.coerce_enum(WarrantType, data.get("warrant_type"))
        data["exercise_type"] = utils.coerce_enum(ExerciseType, data.get("exercise_type"))
        data["settlement_type"] = utils.coerce_enum(SettlementType, data.get("settlement_type"))
        data["anti_dilution_type"] = utils.coerce_enum(AntiDilutionType, data.get("anti_dilution_type"))
        data["warrant_class"] = utils.coerce_enum(WarrantClass, data.get("warrant_class"))
        return data

    def _normalize_and_validate(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure only fields defined on WarrantDetails are passed
        expected = {f.name for f in dataclass_fields(WarrantDetails)}
        clean: Dict[str, Any] = {k: raw.get(k, None) for k in expected}
        clean = self._clean_warrant_data(clean)
        clean = self._coerce_enums(clean)
        return clean

    # ---------- Public API ----------

    def extract_warrants_from_text(self, text: str, filing_type: str, parent_ticker: str) -> List[Dict[str, Any]]:
        key = hashlib.md5((text + parent_ticker).encode()).hexdigest()
        if key in self._cache:
            return self._cache[key]

        # Gemini
        resp = self.client.models.generate_content(
            model=self.model,
            contents=self._prompt(text, parent_ticker),
            config=GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                max_output_tokens=8192,
            ),
        )

        payload = utils.safe_json_loads(getattr(resp, "text", "") or "") or {}
        if isinstance(payload, list):
            payload = payload[0]
        
        warrants_json = payload.get("warrants", [])
        if not isinstance(warrants_json, list):
            warrants_json = []

        warrants: List[Dict[str, Any]] = []
        for raw in warrants_json:
            if not isinstance(raw, dict):
                continue
            clean = self._normalize_and_validate(raw)
            try:
                wd = WarrantDetails(**clean)
            except TypeError:
                # Final safety: drop unexpected keys and retry
                expected = {f.name for f in dataclass_fields(WarrantDetails)}
                minimal = {k: v for k, v in clean.items() if k in expected}
                wd = WarrantDetails(**minimal)
                
            js = json.loads(json.dumps(asdict(wd), default=utils.json_default))
            pprint(js)
            warrants.append(js)

        self._cache[key] = warrants
        return warrants
