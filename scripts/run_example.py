import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from datetime import datetime
import pandas as pd

from src.sec_client import SECClient
from src.scraper import SmartBondScraper

from config import config  # reads config.ini + config.secrets.ini

def main():
    name = config['sec']['name']
    email = config['sec']['email']
    model = config['gemini'].get('model', 'gemini-2.0-flash')
    api_key = config['gemini']['api_key']

    outdir = Path("output")
    outdir.mkdir(exist_ok=True)
    
    sec = SECClient(email, name)
    df_filings = sec.get_recent_filings(
        company=["AES"],  # , "FMC"
        # search_term='"Fixed-to-Fixed Reset Rate" OR "Fixed-to-Floating Rate"',
        # file_types=["424B1","424B2","424B3","424B4","424B5","424B7","424B8","FWP"],
        file_types=["FWP"],
        from_date="2024-01-01",
        to_date="2025-09-01"
    )

    scraper = SmartBondScraper(sec, model=model, api_key=api_key, outdir=str(outdir))
    df = scraper.process_filings(df_filings)
    
    if not df.empty:
        # pd.concat(all_dfs, ignore_index=True)
        fname = outdir / f"Bonds_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(fname, index=False)
        print(f"Saved {len(df)} rows to {fname}")

if __name__ == "__main__":
    main()
