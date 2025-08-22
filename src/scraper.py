import time
from typing import Dict, List, Any, Optional
import pandas as pd

from .sec_client import SECClient
from .extractor import LLMBondExtractor

class SmartBondScraper:
    def __init__(self, email: str, api_key: str, model: str, outdir: Optional[str] = None):
        self.sec = SECClient(email=email)
        self.extractor = LLMBondExtractor(api_key=api_key, model=model)
        self.outdir = outdir

    def process_company(self, company_spec: Dict, days_back: int = 365, max_filings: int = 20) -> pd.DataFrame:
        ticker = company_spec['Symbol']
        company_name = company_spec['FullName']

        cik = self.sec.get_cik(ticker)
        if not cik:
            return pd.DataFrame()

        filings = self.sec.get_recent_filings(cik, days_back)
        if filings.empty:
            return pd.DataFrame()

        all_bonds: List[Dict[str, Any]] = []
        for _, filing in filings.head(max_filings).iterrows():
            content = self.sec.download_filing(ticker, cik, filing['accessionNumber'], filing['primaryDocument'], self.outdir)
            if not content:
                continue
            
            print(filing['form'])
            bonds = self.extractor.extract_bonds_from_text(content, filing['form'])
            for bd in bonds:
                bd.update({
                    'ticker': ticker,
                    'company_name': company_name,
                    'cik': cik,
                    'filing_date': filing['filingDate'].strftime('%Y-%m-%d'),
                    'sec_filing_type': filing['form'],
                    'accession_number': filing['accessionNumber'],
                    'filing_url': f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{filing['accessionNumber'].replace('-', '')}/{filing['primaryDocument']}",
                })
                all_bonds.append(bd)
            time.sleep(0.5)

        if not all_bonds:
            return pd.DataFrame()

        df = pd.DataFrame(all_bonds)
        first_cols = ['ticker','company_name','sec_filing_type','filing_date']
        other_cols = [c for c in df.columns if c not in first_cols]
        return df[first_cols + other_cols]
