import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from datetime import datetime
import pandas as pd

from src.sec_client import SECClient
from src.warrant_scraper import SmartWarrantScraper

from config import config  # reads config.ini + config.secrets.ini

def main():
    name = config['sec']['name']
    email = config['sec']['email']
    model = config['gemini'].get('model', 'gemini-2.0-flash')
    api_key = config['gemini']['api_key']

    outdir = Path("output/warrant_cache")
    outdir.mkdir(parents=True, exist_ok=True)
    
    sec = SECClient(email, name)
    
    # Search for warrant-related filings for IONQ
    print("Searching for DSX warrant filings...")
    df_filings = sec.get_recent_filings(
        company=["DSX"],  # Diana Shipping
        # search_term='Warrants',
        file_types=["8-A12B", "8-A12G"],
        from_date="2020-01-01",
        to_date="2025-11-03",
        max_results=10
    )
    
    fn = str(outdir) + "/" + "filings.csv"
    # df_filings.to_csv(fn, index = False)
    df_filings = pd.read_csv(fn)
    
    scraper = SmartWarrantScraper(sec, model=model, api_key=api_key, filings_dir=str(outdir))
    
    report_file = f"output/Warrants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df = scraper.process_filings(df_filings, report_file, skip_cached=False)
    print(df.head())

if __name__ == "__main__":
    main()
