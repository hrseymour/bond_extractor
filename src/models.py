
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class SecurityRank(Enum):
    SENIOR_SECURED = "SeniorSecured"
    SENIOR_UNSECURED = "SeniorUnsecured"
    SENIOR_SUBORDINATED = "SeniorSubordinated"
    JUNIOR_SUBORDINATED = "JuniorSubordinated"
    PREFERRED_STOCK = "PreferredStock"

class CouponType(Enum):
    FIXED = "Fixed"
    FLOATING = "Floating"
    ZERO = "Zero"
    RATE_RESET = "RateReset"
    STEP_UP = "StepUp"
    PIK = "PIK"
    OTHER = "Other"

class PaymentFrequency(Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    SEMI_ANNUAL = "SemiAnnual"
    ANNUAL = "Annual"
    ZERO = "Zero"
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

@dataclass
class BondDetails:
    # Identifiers
    cusip: Optional[str] = None
    isin: Optional[str] = None

    # Financial terms
    security_type: Optional[SecurityRank] = None
    principal_amount: Optional[float] = None
    currency: str = "USD"
    face_value: Optional[float] = 1000.0

    # Interest / coupon
    interest_rate: Optional[float] = None
    coupon_type: Optional[CouponType] = None
    payment_frequency: Optional[PaymentFrequency] = None

    # Floating / reset
    rate_benchmark: Optional[RateBenchmark] = None
    rate_spread: Optional[float] = None
    rate_floor: Optional[float] = None
    rate_cap: Optional[float] = None
    reset_frequency: Optional[float] = None
    next_reset_date: Optional[str] = None

    # Dates (ISO)
    issue_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    maturity_date: Optional[str] = None

    # Call
    callable: Optional[bool] = None
    first_call_date: Optional[str] = None
    call_price: Optional[float] = None

    # Put
    puttable: Optional[bool] = None
    first_put_date: Optional[str] = None
    put_price: Optional[float] = None

    # Convertible
    convertible: Optional[bool] = None
    conversion_price: Optional[float] = None
    conversion_ratio: Optional[float] = None

    # Deferral features
    deferral_allowed: Optional[bool] = None
    max_deferral_period: Optional[int] = None
    deferred_interest_cumulative: Optional[bool] = None
