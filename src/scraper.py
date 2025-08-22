import time
from dataclasses import asdict
from typing import Dict, List
import pandas as pd

from .sec_client import SECClient
from .extractor import LLMBondExtractor

class SmartBondScraper:
    def __init__(self, email: str, api_key: str, model: str):
        self.sec = SECClient(email=email)
        self.extractor = LLMBondExtractor(api_key=api_key, model=model)

    def process_company(self, company_spec: Dict, days_back: int = 365, max_filings: int = 20) -> pd.DataFrame:
        ticker = company_spec['Symbol']
        company_name = company_spec['FullName']

        cik = self.sec.get_cik(ticker)
        if not cik:
            return pd.DataFrame()

        filings = self.sec.get_recent_filings(cik, days_back)
        if filings.empty:
            return pd.DataFrame()

        all_bonds: List[dict] = []
        for _, filing in filings.head(max_filings).iterrows():
            content = self.sec.download_filing(cik, filing['accessionNumber'], filing['primaryDocument'])
            if not content:
                continue
            
            print(filing['form'])
            bonds = self.extractor.extract_bonds_from_text(content, filing['form'])
            for b in bonds:
                bd = asdict(b)
                bd.update({
                    'ticker': ticker,
                    'company_name': company_name,
                    'cik': cik,
                    'filing_date': filing['filingDate'].strftime('%Y-%m-%d'),
                    'filing_type': filing['form'],
                    'accession_number': filing['accessionNumber'],
                    'filing_url': f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{filing['accessionNumber'].replace('-', '')}/{filing['primaryDocument']}",
                })
                all_bonds.append(bd)
            time.sleep(0.5)

        if not all_bonds:
            return pd.DataFrame()

        df = pd.DataFrame(all_bonds)
        first_cols = ['ticker','company_name','filing_date','bond_type','series_name','principal_amount','interest_rate','coupon_type','maturity_date']
        other_cols = [c for c in df.columns if c not in first_cols]
        return df[first_cols + other_cols]

    @staticmethod
    def create_summary_stats(df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        stats = {
            'total_bonds': len(df),
            'total_principal': float(df.get('principal_amount', pd.Series(dtype=float)).fillna(0).sum()),
            'unique_companies': int(df.get('ticker', pd.Series(dtype=object)).nunique()),
            'avg_interest_rate': float((df.get('interest_rate', pd.Series(dtype=float)).mean() or 0) * 100),
            'bond_types': df.get('bond_type', pd.Series(dtype=object)).value_counts().to_dict(),
            'coupon_types': df.get('coupon_type', pd.Series(dtype=object)).value_counts().to_dict(),
        }
        if 'rate_benchmark' in df.columns:
            floating = df[df['rate_benchmark'].notna()]
            if not floating.empty:
                stats['floating_rate_bonds'] = {
                    'count': int(len(floating)),
                    'benchmarks': floating['rate_benchmark'].value_counts().to_dict(),
                    'avg_spread_bps': float((floating.get('rate_spread', pd.Series(dtype=float)).mean() or 0) * 10000),
                }
        if 'convertible' in df.columns:
            convertibles = df[df['convertible'] == True]
            if not convertibles.empty:
                stats['convertible_bonds'] = {
                    'count': int(len(convertibles)),
                    'total_principal': float(convertibles['principal_amount'].fillna(0).sum()),
                }
        return stats
