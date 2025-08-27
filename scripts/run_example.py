import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from datetime import datetime
import pandas as pd

from src.scraper import SmartBondScraper

from config import config  # reads config.ini + config.secrets.ini

def main():
    email = config['sec']['email']
    api_key = config['gemini']['api_key']
    model = config['gemini'].get('model', 'gemini-2.0-flash')

    days_back = 5 * 365
    max_filings = 200
    outdir = Path("output")
    outdir.mkdir(exist_ok=True)

    scraper = SmartBondScraper(email=email, api_key=api_key, model=model, outdir=str(outdir))

    companies = [
        {'Symbol': 'AES', 'FullName': 'The AES Corporation', 'Exchange': 'NYSE', 'Currency': 'USD'}
        # {'Symbol': 'F', 'FullName': 'Ford Motor Company', 'Exchange': 'NYSE', 'Currency': 'USD'},
        # {'Symbol': 'T', 'FullName': 'AT&T Inc.', 'Exchange': 'NYSE', 'Currency': 'USD'},
    ]

    all_dfs = []
    for c in companies:
        df = scraper.process_company(c, days_back=days_back, max_filings=max_filings)
        if df.empty:
            continue
        all_dfs.append(df)
        fname = outdir / f"{c['Symbol']}_bonds_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(fname, index=False)
        print(f"Saved {len(df)} rows to {fname}")

    if not all_dfs:
        print("No data.")
        return

    final = pd.concat(all_dfs, ignore_index=True)
    final_file = outdir / f"all_bonds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    final.to_csv(final_file, index=False)
    print(f"Combined written to {final_file}")

if __name__ == "__main__":
    main()
