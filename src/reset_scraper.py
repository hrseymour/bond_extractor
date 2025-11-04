import time
from typing import Dict, List, Any, Optional
import pandas as pd

from .sec_client import SECClient
from .reset_extractor import LLMBondExtractor

class SmartBondScraper:
    def __init__(self, sec: SECClient, model: str, api_key: str, filings_dir: str = None):
        self.sec = sec
        self.extractor = LLMBondExtractor(api_key=api_key, model=model)
        self.filings_dir = filings_dir

    def _to_df(self, all_bonds: List[Dict[str, Any]], report_file: str = None) -> pd.DataFrame:
        if not all_bonds:
            return pd.DataFrame()

        df = pd.DataFrame(all_bonds)
        first_cols = ['ticker','company_name','form','filing_date']
        other_cols = [c for c in df.columns if c not in first_cols]
        df = df[first_cols + other_cols]
        
        if report_file:
             df.to_csv(report_file, index=False)        
        return df

    def process_filings(self, df_filings: pd.DataFrame, report_file: str = None, skip_cached: bool = True) -> pd.DataFrame:
        all_bonds: List[Dict[str, Any]] = []
        for _, filing in df_filings.iterrows():
            content, is_cached = self.sec.download_filing(filing['ticker'], filing['accession_no'], self.filings_dir)
            if not content or (skip_cached and is_cached):
                continue
            
            print(filing['ticker'], filing['form'])
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
                df = self._to_df(all_bonds, report_file)
                
        return df
