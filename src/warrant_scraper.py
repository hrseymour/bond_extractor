import time
from typing import Dict, List, Any, Optional
import pandas as pd

from .sec_client import SECClient
from .warrant_extractor import LLMWarrantExtractor

class SmartWarrantScraper:
    def __init__(self, sec: SECClient, model: str, api_key: str, filings_dir: str = None):
        self.sec = sec
        self.extractor = LLMWarrantExtractor(api_key=api_key, model=model)
        self.filings_dir = filings_dir

    def _to_df(self, all_warrants: List[Dict[str, Any]], report_file: str = None) -> pd.DataFrame:
        if not all_warrants:
            return pd.DataFrame()

        df = pd.DataFrame(all_warrants)
        
        # Reorder columns: metadata first, then warrant details
        first_cols = ['ticker', 'company_name', 'form', 'filing_date']
        warrant_cols = ['symbol', 'parent', 'strike_price', 'expiration_date', 'conversion_ratio']
        other_cols = [c for c in df.columns if c not in first_cols + warrant_cols]
        
        # Build final column order
        final_cols = first_cols + warrant_cols + other_cols
        final_cols = [c for c in final_cols if c in df.columns]
        df = df[final_cols]
        
        # Drop columns that are all null
        df = df.dropna(axis=1, how='all')
        
        if report_file:
            df.to_csv(report_file, index=False)
        
        return df

    def process_filings(self, df_filings: pd.DataFrame, report_file: str = None, skip_cached: bool = True) -> pd.DataFrame:
        all_warrants: List[Dict[str, Any]] = []
        
        for _, filing in df_filings.iterrows():
            content, is_cached = self.sec.download_filing(filing['ticker'], filing['accession_no'], self.filings_dir)
            if not content or (skip_cached and is_cached):
                continue
            
            print(f"Processing: {filing['ticker']} {filing['form']} {filing['filing_date']}")
            
            # Extract warrants from the filing
            warrants = self.extractor.extract_warrants_from_text(
                content, 
                filing['form'],
                filing['ticker']  # parent ticker
            )
            
            # Add filing metadata to each warrant
            for wd in warrants:
                wd.update({
                    'company_name': filing['company_name'],
                    'ticker': filing['ticker'],
                    'cik': filing['cik'],
                    'form': filing['form'],
                    'filing_date': filing['filing_date'],
                    'accession_no': filing['accession_no'],
                    'filing_url': filing['filing_url']
                })
                all_warrants.append(wd)
                
                # Save incrementally after each warrant
                df = self._to_df(all_warrants, report_file)
        
        return df
