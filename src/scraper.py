import time
from typing import Dict, List, Any, Optional
import pandas as pd

from .sec_client import SECClient
from .extractor import LLMBondExtractor

class SmartBondScraper:
    def __init__(self, sec: SECClient, model: str, api_key: str, outdir: Optional[str] = None):
        self.sec = sec
        self.extractor = LLMBondExtractor(api_key=api_key, model=model)
        self.outdir = outdir

    def process_filings(self, df_filings: pd.DataFrame) -> pd.DataFrame:
        all_bonds: List[Dict[str, Any]] = []
        for _, filing in df_filings.iterrows():
            content = self.sec.download_filing(filing['ticker'], filing['accession_no'], self.outdir)
            if not content:
                continue
            
            print(filing['form'])
            bonds = self.extractor.extract_bonds_from_text(content, filing['form'])
            for bd in bonds:
                bd.update({
                    'company_name': filing['company_name'],
                    'ticker': filing['ticker'],
                    'cik': filing['cik'],
                    'form': filing['form'],
                    'filing_date': filing['filing_date'],
                    'accession_no': filing['accession_no'],
                    'filing_url': filing['filing_url']
                })
                all_bonds.append(bd)
            
        if not all_bonds:
            return pd.DataFrame()

        df = pd.DataFrame(all_bonds)
        first_cols = ['ticker','company_name','form','filing_date']
        other_cols = [c for c in df.columns if c not in first_cols]
        return df[first_cols + other_cols]
