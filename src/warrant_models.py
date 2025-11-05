from dataclasses import dataclass
from typing import Optional
from enum import Enum

# -----------------------------
# Enums
# -----------------------------

class Exchange(Enum):
    NYSE = "NYSE"
    AMEX = "AMEX"
    NNM = "NNM"
    PINK = "PINK"
    UNK = "UNK"
       
class WarrantType(Enum):
    CALL = "Call"
    PUT = "Put"

class ExerciseType(Enum):
    AMERICAN = "American"
    EUROPEAN = "European"
    BERMUDA = "Bermuda"

class SettlementType(Enum):
    PHYSICAL = "Physical"
    CASH = "Cash"
    NET_SHARE = "NetShare"

class AntiDilutionType(Enum):
    FULL_RATCHET = "FullRatchet"
    WEIGHTED_AVERAGE = "WeightedAverage"
    BROAD_BASED = "BroadBased"
    NARROW_BASED = "NarrowBased"
    OTHER = "Other"

class WarrantClass(Enum):
    PUBLIC = "Public"
    PRIVATE = "Private"
    FOUNDER = "Founder"
    PLACEMENT = "Placement"
    OTHER = "Other"

# -----------------------------
# Dataclass
# -----------------------------

@dataclass
class WarrantDetails:
    # PRIMARY IDENTIFICATION
    symbol: Optional[str] = None
    isin: Optional[str] = None
    exchange: Optional[str] = None
    invalid_symbol: Optional[bool] = None
    parent: Optional[str] = None
    currency: str = "USD"

    # BASIC WARRANT TERMS
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    strike_price: Optional[float] = None
    conversion_ratio: Optional[float] = None
    warrant_type: Optional[WarrantType] = None

    # CURRENT MARKET QUOTE (will be null from SEC filings)
    prev_close: Optional[float] = None
    last_trade: Optional[float] = None
    last_trade_date: Optional[str] = None

    # EXERCISE TERMS
    exercise_type: Optional[ExerciseType] = None
    first_exercise_date: Optional[str] = None
    is_callable: Optional[bool] = None
    is_putable: Optional[bool] = None

    # SETTLEMENT
    settlement_type: Optional[SettlementType] = None
    settlement_days: Optional[int] = None

    # CASHLESS EXERCISE
    allows_cashless_exercise: Optional[bool] = None
    cashless_exercise_formula: Optional[str] = None

    # TRIGGER 1: CALL/REDEMPTION TRIGGER
    has_call_trigger: Optional[bool] = None
    call_trigger_price: Optional[float] = None
    call_trigger_days: Optional[int] = None
    call_trigger_period: Optional[int] = None
    call_trigger_notice_days: Optional[int] = None
    call_redemption_price: Optional[float] = None
    call_trigger_start_date: Optional[str] = None
    call_trigger_end_date: Optional[str] = None
    call_trigger_additional_conditions: Optional[str] = None

    # TRIGGER 2: ACCELERATION TRIGGER
    has_acceleration_trigger: Optional[bool] = None
    accel_trigger_price: Optional[float] = None
    accel_trigger_days: Optional[int] = None
    accel_trigger_period: Optional[int] = None
    accel_trigger_effect: Optional[str] = None

    # ANTI-DILUTION PROVISIONS
    has_anti_dilution: Optional[bool] = None
    anti_dilution_type: Optional[AntiDilutionType] = None
    anti_dilution_details: Optional[str] = None

    # AUTOMATIC ADJUSTMENT EVENTS
    adjusts_for_dividends: Optional[bool] = None
    dividend_threshold: Optional[float] = None
    adjusts_for_stock_splits: Optional[bool] = None
    adjusts_for_mergers: Optional[bool] = None
    adjusts_for_spinoffs: Optional[bool] = None
    adjusts_for_rights_offerings: Optional[bool] = None

    # CHANGE OF CONTROL / M&A PROVISIONS
    fundamental_transaction_provision: Optional[str] = None
    change_of_control_provision: Optional[str] = None

    # TRANSFER AND TRADING
    is_transferable: Optional[bool] = None
    transfer_restrictions: Optional[str] = None
    is_publicly_traded: Optional[bool] = None

    # REGISTRATION RIGHTS
    has_registration_rights: Optional[bool] = None
    registration_details: Optional[str] = None

    # BENEFICIAL OWNERSHIP LIMITATIONS
    has_ownership_limit: Optional[bool] = None
    ownership_limit_pct: Optional[float] = None
    ownership_limit_waiver: Optional[str] = None

    # UNIT STRUCTURE
    is_detachable: Optional[bool] = None
    original_issue_price: Optional[float] = None
    issued_with_security: Optional[str] = None

    # SEC FILINGS & LEGAL DOCUMENTATION
    issuer_cik: Optional[int] = None
    filing_url: Optional[str] = None

    # EXOTIC/RARE FEATURES
    is_extendable: Optional[bool] = None
    extension_conditions: Optional[str] = None
    has_knock_out_provision: Optional[bool] = None
    knock_out_details: Optional[str] = None
    has_knock_in_provision: Optional[bool] = None
    knock_in_details: Optional[str] = None

    # CLASSIFICATION & NOTES
    spac_related: Optional[bool] = None
    warrant_class: Optional[WarrantClass] = None
    vintage: Optional[str] = None
    notes: Optional[str] = None
