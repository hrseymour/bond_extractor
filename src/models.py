from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class BondType(Enum):
    SENIOR = "Senior"
    SUBORDINATED = "Subordinated"
    CONVERTIBLE = "Convertible"
    MEZZANINE = "Mezzanine"
    SECURED = "Secured"
    UNSECURED = "Unsecured"
    OTHER = "Other"


class CouponType(Enum):
    FIXED = "Fixed"
    FLOATING = "Floating"
    ZERO = "Zero"
    RATE_RESET = "RateReset"
    STEP_UP = "StepUp"
    PIK = "PIK"
    OTHER = "Other"


class RateBenchmark(Enum):
    SOFR = "SOFR"
    LIBOR = "LIBOR"
    PRIME = "Prime"
    TREASURY = "Treasury"
    EURIBOR = "EURIBOR"
    SONIA = "SONIA"
    FIXED = "Fixed"
    OTHER = "Other"


@dataclass
class BondDetails:
    # Identifiers
    cusip: Optional[str] = None
    isin: Optional[str] = None
    bond_identifier: Optional[str] = None

    # Basic info
    bond_type: Optional[str] = None
    bond_subtype: Optional[str] = None
    series_name: Optional[str] = None
    tranche: Optional[str] = None

    # Financial terms
    principal_amount: Optional[float] = None
    currency: str = "USD"
    issue_price: Optional[float] = None
    minimum_denomination: Optional[float] = None

    # Interest / coupon
    interest_rate: Optional[float] = None
    coupon_type: Optional[str] = None
    payment_frequency: Optional[float] = None
    day_count_convention: Optional[str] = None

    # Floating / reset
    rate_benchmark: Optional[str] = None
    rate_spread: Optional[float] = None
    rate_floor: Optional[float] = None
    rate_cap: Optional[float] = None
    reset_frequency: Optional[float] = None
    next_reset_date: Optional[str] = None
    reset_lookback_days: Optional[int] = None

    # Dates (ISO)
    issue_date: Optional[str] = None
    dated_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    maturity_date: Optional[str] = None

    # Call
    callable: Optional[bool] = None
    first_call_date: Optional[str] = None
    call_price: Optional[float] = None
    make_whole_provision: Optional[bool] = None
    make_whole_spread: Optional[float] = None

    # Put
    puttable: Optional[bool] = None
    put_dates: Optional[List[str]] = None
    put_price: Optional[float] = None

    # Convertible
    convertible: Optional[bool] = None
    conversion_price: Optional[float] = None
    conversion_ratio: Optional[float] = None
    conversion_start_date: Optional[str] = None
    conversion_end_date: Optional[str] = None

    # Ratings & listing
    credit_rating_sp: Optional[str] = None
    credit_rating_moodys: Optional[str] = None
    credit_rating_fitch: Optional[str] = None
    listing_exchange: Optional[str] = None

    # Transaction details
    use_of_proceeds: Optional[str] = None
    lead_underwriter: Optional[str] = None
    underwriters: Optional[List[str]] = None
    trustee: Optional[str] = None

    # Covenants
    covenants_summary: Optional[str] = None

    # Metadata
    filing_extracted_from: Optional[str] = None
    extraction_confidence: Optional[float] = None
    extraction_timestamp: Optional[str] = None
