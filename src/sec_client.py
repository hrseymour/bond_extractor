import re
import time
from datetime import datetime, timedelta
from typing import Optional
import requests
import pandas as pd

class SECClient:
    def __init__(self, email: str):
        self.email = email
        self.headers = {'User-Agent': f'{email} SmartBondScraper/3.1', 'Accept-Encoding': 'gzip, deflate'}

    def get_cik(self, ticker: str) -> Optional[str]:
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            r = requests.get(url, headers=self.headers, timeout=10)
            r.raise_for_status()
            for item in r.json().values():
                if item['ticker'].upper() == ticker.upper():
                    return str(item['cik_str']).zfill(10)
        except Exception:
            return None
        return None

    def get_recent_filings(self, cik: str, days_back: int = 365) -> pd.DataFrame:
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            r = requests.get(url, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            recent = data['filings']['recent']
            df = pd.DataFrame({
                'accessionNumber': recent['accessionNumber'],
                'filingDate': recent['filingDate'],
                'form': recent['form'],
                'primaryDocument': recent['primaryDocument'],
                'primaryDocDescription': recent['primaryDocDescription'],
            })
            df['filingDate'] = pd.to_datetime(df['filingDate'])
            cutoff = datetime.now() - timedelta(days=days_back)
            bond_forms = [
                '424B1','424B2','424B3','424B4','424B5','424B7',
                'S-3','S-3/A','S-3ASR','S-3MEF',
                'F-3','F-3/A','F-3ASR','F-3MEF',
                'FWP','8-K','SUPPL','POS AM'
            ]
            df = df[(df['filingDate'] >= cutoff) & (df['form'].str.upper().isin([f.upper() for f in bond_forms]))]
            return df.sort_values('filingDate', ascending=False)
        except Exception:
            return pd.DataFrame()

    def download_filing(self, cik: str, accession: str, document: str) -> Optional[str]:
        try:
            acc_clean = accession.replace('-', '')
            url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_clean}/{document}"
            r = requests.get(url, headers=self.headers, timeout=30)
            r.raise_for_status()
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text)
            return text
        except Exception:
            return None
