from dataclasses import dataclass
from typing import Optional
from enum import Enum

# -----------------------------
# Enums
# -----------------------------

class SecurityRank(Enum):
    SENIOR_SECURED = "SeniorSecured"
    SENIOR_UNSECURED = "SeniorUnsecured"
    SENIOR_SUBORDINATED = "SeniorSubordinated"
    JUNIOR_SUBORDINATED = "JuniorSubordinated"
    PREFERRED_STOCK = "PreferredStock"

class CouponType(Enum):
    ZERO = "Zero"
    FIXED = "Fixed"
    FLOATER = "Floater"               # Floating for life (e.g., SOFR 3M + spread)
    FIXED_TO_FLOAT = "FixedToFloat"   # Fixed until a switch date, then true floater
    RATE_RESET = "RateReset"          # Fixed-to-fixed resets to term benchmark every few years
    STEP_UP = "StepUp"
    STEP_DOWN = "StepDown"
    OTHER = "Other"

class PaymentFrequency(Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    SEMI_ANNUAL = "SemiAnnual"
    ANNUAL = "Annual"
    ZERO = "Zero"
    OTHER = "Other"

class RateChangeTrigger(Enum):
    DATE_BASED = "DateBased"
    RATING_CHANGE = "RatingChange"
    REGULATORY_EVENT = "RegulatoryEvent"
    DEFERRAL_EVENT = "DeferralEvent"
    OTHER = "Other"

class RateBenchmark(Enum):
    FIXED = "Fixed"
    CAD_3MO = "CAD3Mo"
    CAD_5YR = "CAD5Yr"
    CAD_PRIME = "CADPrime"
    LIBOR_1MO = "Libor1Mo"
    LIBOR_3MO = "Libor3Mo"
    LIBOR_6MO = "Libor6Mo"
    LIBOR_1YR = "Libor1Yr"
    TERM_SOFR = "TermSofr"
    SOFR_1MO = "Sofr1Mo"
    SOFR_3MO = "Sofr3Mo"
    SOFR_6MO = "Sofr6Mo"
    TREAS_1MO = "Treas1Mo"
    TREAS_3MO = "Treas3Mo"
    TREAS_1YR = "Treas1Yr"
    TREAS_2YR = "Treas2Yr"
    TREAS_5YR = "Treas5Yr"
    TREAS_7YR = "Treas7Yr"
    TREAS_10YR = "Treas10Yr"
    TREAS_30YR = "Treas30Yr"
    # Inflation indices (kept simple)
    CPI_U = "CPI_U"   # US CPI-U (headline, typically NSA for linkers)
    CPI = "CPI"       # Generic CPI label
    HICP = "HICP"     # Eurozone HICP
    RPI = "RPI"       # UK RPI
    OTHER = "Other"

# -----------------------------
# Dataclass
# -----------------------------

@dataclass
class BondDetails:
    # Identifiers
    cusip: Optional[str] = None
    isin: Optional[str] = None

    # Financial terms
    security_type: Optional[SecurityRank] = None
    principal_amount: Optional[float] = None
    currency: str = "USD"
    face_value: Optional[float] = None  # par per note (often 1000)

    # Interest / coupon
    interest_rate: Optional[float] = None
    coupon_type: Optional[CouponType] = None
    payment_frequency: Optional[PaymentFrequency] = None

    # Inflation link minimal flags
    inflation_linked: Optional[bool] = None
    inflation_lag_months: Optional[int] = None
    inflation_method: Optional[str] = None

    # Floating / reset / triggers
    rate_benchmark: Optional[RateBenchmark] = None
    rate_spread: Optional[float] = None
    rate_floor: Optional[float] = None
    rate_cap: Optional[float] = None
    reset_frequency: Optional[float] = None
    
    next_trigger_date: Optional[str] = None  # generalized: reset / step / float switch
    rate_change_trigger: Optional[RateChangeTrigger] = None
    trigger_note: Optional[str] = None

    # Dates (ISO)
    issue_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    maturity_date: Optional[str] = None
    perpetual: Optional[bool] = None

    # Call features
    callable: Optional[bool] = None
    first_call_date: Optional[str] = None
    call_price_pct_of_face: Optional[float] = None
    call_note: Optional[str] = None

    # Put features
    puttable: Optional[bool] = None
    first_put_date: Optional[str] = None
    put_price_pct_of_face: Optional[float] = None
    put_note: Optional[str] = None

    # Convertible
    convertible: Optional[bool] = None
    conversion_price: Optional[float] = None
    conversion_ratio: Optional[float] = None
    conversion_note: Optional[str] = None

    # PIK / regulatory hybrid flags
    pik_allowed: Optional[bool] = None
    coco_at1_t2: Optional[bool] = None

    # Deferral features
    deferral_allowed: Optional[bool] = None
    max_deferral_period: Optional[int] = None
    deferred_interest_cumulative: Optional[bool] = None
