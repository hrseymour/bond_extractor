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
    
    # Search for warrant-related filings for DSX (Diana Shipping)
    print("Searching for DSX warrant filings...")
    df_filings = sec.get_recent_filings(
        company=["DSX"],  # Diana Shipping
        search_term='warrant',
        file_types=["8-A", "424B2", "424B3", "424B5"],
        from_date="2020-01-01",
        to_date="2025-11-03",
        max_results=100
    )
    
    print(f"Found {len(df_filings)} filings")
    if len(df_filings) > 0:
        print("\nFilings found:")
        print(df_filings[['ticker', 'form', 'filing_date', 'company_name']].to_string(index=False))
    
    # Save the filings list
    filings_file = str(outdir) + "/warrant_filings.csv"
    df_filings.to_csv(filings_file, index=False)
    print(f"\nSaved filings list to: {filings_file}")
    
    # Process the filings with the warrant scraper
    scraper = SmartWarrantScraper(sec, model=model, api_key=api_key, filings_dir=str(outdir))
    
    report_file = f"output/Warrants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"\nProcessing filings and extracting warrants...")
    print(f"Results will be saved to: {report_file}")
    
    df_warrants = scraper.process_filings(df_filings, report_file, skip_cached=False)
    
    print(f"\n{'='*60}")
    print(f"Extraction complete!")
    print(f"Found {len(df_warrants)} warrant records")
    print(f"Results saved to: {report_file}")
    print(f"{'='*60}")
    
    if len(df_warrants) > 0:
        print("\nWarrant summary:")
        summary_cols = ['symbol', 'parent', 'strike_price', 'expiration_date', 
                       'conversion_ratio', 'has_call_trigger', 'call_trigger_price']
        available_cols = [c for c in summary_cols if c in df_warrants.columns]
        print(df_warrants[available_cols].to_string(index=False))

if __name__ == "__main__":
    main()
