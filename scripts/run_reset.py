import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from datetime import datetime
import pandas as pd

from src.sec_client import SECClient
from src.reset_scraper import SmartBondScraper

from config import config  # reads config.ini + config.secrets.ini

def main():
    name = config['sec']['name']
    email = config['sec']['email']
    model = config['gemini'].get('model', 'gemini-2.0-flash')
    api_key = config['gemini']['api_key']

    outdir = Path("output/reset_cache")
    outdir.mkdir(exist_ok=True)
    
    sec = SECClient(email, name)
    df_filings = sec.get_recent_filings(
        # company=["AES", "FMC"],
        # search_term='"Fixed-to-Fixed Reset Rate" OR "Fixed-to-Floating Rate"',
        search_term='"Fixed-to-Floating Rate" AND CUSIP',
        # file_types=["424B1","424B2","424B3","424B4","424B5","424B7","424B8","FWP"],
        file_types=["FWP"],
        from_date="2020-01-01",
        to_date="2025-09-01",
        skip_ciks = ["0000019617", "0000895421"]  # + ["0001666268", "0000083246"]
    )
    
    fn = str(outdir) + "/" + "filings.csv"
    # df_filings.to_csv(fn, index = False)
    df_filings = pd.read_csv(fn)

    scraper = SmartBondScraper(sec, model=model, api_key=api_key, filings_dir=str(outdir))
    
    report_file = f"output/Bonds_{datetime.now().strftime('%Y%m%d')}.csv"
    df = scraper.process_filings(df_filings, report_file, skip_cached = False)

if __name__ == "__main__":
    main()
