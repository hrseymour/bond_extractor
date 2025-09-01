import pandas as pd
import re
from edgar import set_identity, Company
from edgar.xbrl import XBRL

# --- Concepts we'll accept for the table (regex OR) ---
DEBT_CONCEPT_REGEX = r'(' + '|'.join([
    r'DebtInstrumentFaceAmount',
    r'DebtInstrumentCarryingAmount',
    r'DebtLongtermAndShorttermCombinedAmount',
    r'LongTermDebt(?!.*FairValue)',
    r'LongTermDebtCurrent',
    r'LongTermDebtNoncurrent',
    r'DebtSecuritiesCarryingValue',
    r'DebtInstrumentUnamortized.*(Discount|Premium|Issue)Cost.*',
    r'DebtInstrumentEffectiveInterestRate',
    r'DebtInstrumentInterestRateStatedPercentage',
    r'DebtInstrumentMaturityDate',
    r'LongTermDebtFairValue',
    r'DebtFairValue',
    r'DebtInstrumentConversionPrice.*',
    r'DebtInstrumentConversionRate.*'
]) + r')'

# Map concepts -> friendly columns
COL_PATTERNS = {
    'FaceAmount'      : r'DebtInstrumentFaceAmount|DebtLongtermAndShorttermCombinedAmount|LongTermDebt(?!.*FairValue)',
    'CarryingAmount'  : r'DebtInstrumentCarryingAmount|DebtSecuritiesCarryingValue|LongTermDebt(?!.*FairValue)',
    'UnamortizedCosts': r'DebtInstrumentUnamortized.*(Discount|Premium|Issue)Cost.*',
    'EffectiveRatePct': r'DebtInstrumentEffectiveInterestRate',
    'StatedRatePct'   : r'DebtInstrumentInterestRateStatedPercentage|InterestRateStatedPercentage',
    'MaturityDate'    : r'DebtInstrumentMaturityDate',
    'FairValue'       : r'LongTermDebtFairValue|DebtFairValue',
    'ConversionPrice' : r'DebtInstrumentConversionPrice.*',
    'ConversionRate'  : r'DebtInstrumentConversionRate.*',
}

# Axis name hints (case-insensitive)
AXIS_HINT_RE = re.compile(r'(Debt|Note|Instrument|Convertible|Financ|Credit|Loan|Facility|Senior).*Axis$', re.I)

class EdgarDebt:
    def __init__(self, email: str, name: str = "John Doe"):
        set_identity(f"{name} {email}")
        self.co = None
        self.filing = None
        self.xbrl = None

    def get_filing(self, ticker: str, form: str = "10-Q"):
        self.co = Company(ticker)
        self.filing = self.co.latest(form)
        self.xbrl = XBRL.from_filing(self.filing)
        return self.xbrl

    # Quick probe (unchanged behavior, but keep it handy)
    def keyword_report(self, keyword: str = "debt") -> pd.DataFrame:
        return (self.xbrl.query()
                    .by_label(keyword, exact=False)
                    .sort_by('concept')
                    .limit(200)
                    .to_dataframe('concept','label')
                    .drop_duplicates())

    # ---- helpers ----
    def _latest_instant_key(self):
        df = (self.xbrl.query()
                        .by_period_type("instant")
                        .sort_by("period_end", ascending=False)
                        .limit(1)
                        .to_dataframe('period_key'))
        return None if df.empty else df.iloc[0,0]

    def _fallback_latest_any_period_key(self):
        df = (self.xbrl.query()
                        .sort_by("period_end", ascending=False)
                        .limit(1)
                        .to_dataframe('period_key'))
        return None if df.empty else df.iloc[0,0]

    def _normalize_concept(self, concept):
        for nice, pat in COL_PATTERNS.items():
            if re.search(pat, concept, re.I):
                return nice
        return None

    def _candidate_axes(self, period_key: str) -> list[str]:
        # Look at all facts for that period and harvest dimension names that look like an Axis
        df = (self.xbrl.query()
                        .by_period_keys([period_key])
                        .to_dataframe('dimension'))
        if df.empty or 'dimension' not in df.columns:
            return []
        dims = df['dimension'].dropna().unique().tolist()
        # Prefer likely debt-related axes
        likely = [d for d in dims if AXIS_HINT_RE.search(d or "")]
        return likely or dims  # if nothing matched hints, try any axis

    def debt_by_instrument_table(self) -> pd.DataFrame:
        # 1) Prefer instant balance-sheet date; if absent, use latest of any type.
        period_key = self._latest_instant_key() or self._fallback_latest_any_period_key()
        if not period_key:
            return pd.DataFrame()

        # 2) Find the most promising axis (don’t rely on 'Debt' appearing in labels)
        axes = self._candidate_axes(period_key)
        # Try axes in order; stop at the first that yields rows after concept filtering
        for axis in axes:
            df = (self.xbrl.query()
                          .by_dimension(axis)                              # instrument axis
                          .by_period_keys([period_key])
                          .by_concept(DEBT_CONCEPT_REGEX)                  # concept-driven filter
                          .to_dataframe('dimension','dimension_value','concept',
                                        'label','value','units','period_end'))
            if df.empty:
                continue

            # Normalize concepts to friendly columns and pivot
            df['column'] = df['concept'].apply(self._normalize_concept)
            df = df.dropna(subset=['column'])
            if df.empty:
                continue

            wide = (df.sort_values(['dimension_value','column'])
                     .drop_duplicates(subset=['dimension_value','column'])
                     .pivot_table(index='dimension_value',
                                  columns='column',
                                  values='value',
                                  aggfunc='last')
                     .reset_index()
                     .rename(columns={'dimension_value':'Instrument'}))

            # Cosmetic column order
            preferred = ['Instrument','FaceAmount','CarryingAmount','UnamortizedCosts',
                         'StatedRatePct','EffectiveRatePct','MaturityDate','FairValue',
                         'ConversionPrice','ConversionRate']
            cols = [c for c in preferred if c in wide.columns] + [c for c in wide.columns if c not in preferred]
            return wide[cols]

        # 3) Fallback: no axis worked → return undimensioned roll-ups for the period
        base = (self.xbrl.query()
                        .by_period_keys([period_key])
                        .by_concept(DEBT_CONCEPT_REGEX)
                        .by_dimension(None)                                   # explicitly undimensioned
                        .to_dataframe('concept','label','value','units','period_end'))
        if base.empty:
            return base
        base['column'] = base['concept'].apply(self._normalize_concept)
        base = base.dropna(subset=['column']).drop_duplicates(subset=['column'])
        return (base.pivot_table(index=None, columns='column', values='value', aggfunc='last')
                    .reset_index(drop=True))

    
if __name__ == "__main__":
    client = EdgarDebt(email="hrseymour@gmail.com", name="Harlan Seymour")
    
    client.get_filing("MSTR", "10-K")
    df1 = client.xbrl.query().by_label("debt", exact=False).limit(200).to_dataframe().head()
    df2 = client.keyword_report()
    debt_tbl = client.debt_by_instrument_table()
    print(debt_tbl)