#!/usr/bin/env python3
"""
Warrant Extractor CLI

Usage:
    python scripts/extract_warrants.py DSX
    python scripts/extract_warrants.py DSX IONQ SPCE
    python scripts/extract_warrants.py --from-file tickers.txt
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

from src.sec_client import SECClient
from src.warrant_scraper import SmartWarrantScraper
from config import config

def load_tickers_from_file(filepath: str) -> list:
    """Load ticker symbols from a text file (one per line)."""
    with open(filepath, 'r') as f:
        tickers = [line.strip().upper() for line in f if line.strip() and not line.startswith('#')]
    return tickers

def main():
    parser = argparse.ArgumentParser(description='Extract warrant specifications from SEC filings')
    parser.add_argument('tickers', nargs='*', help='Ticker symbols (e.g., DSX IONQ)')
    parser.add_argument('--from-file', help='Read tickers from file (one per line)')
    parser.add_argument('--from-date', default='2020-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', default=datetime.now().strftime('%Y-%m-%d'), help='End date (YYYY-MM-DD)')
    parser.add_argument('--forms', default='8-A,424B2,424B3,424B5', help='Comma-separated form types')
    parser.add_argument('--search', default='warrant', help='Search term')
    parser.add_argument('--output', help='Output CSV file (default: output/Warrants_YYYYMMDD_HHMMSS.csv)')
    parser.add_argument('--cache-dir', default='output/warrant_cache', help='Cache directory')
    parser.add_argument('--skip-cached', action='store_true', help='Skip cached filings')
    parser.add_argument('--max-results', type=int, default=100, help='Max filings per ticker')
    
    args = parser.parse_args()
    
    # Get tickers
    tickers = []
    if args.from_file:
        tickers = load_tickers_from_file(args.from_file)
    elif args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        parser.error('Provide either ticker symbols or --from-file')
    
    if not tickers:
        print("ERROR: No tickers provided")
        return 1
    
    print(f"{'='*60}")
    print(f"Warrant Extractor")
    print(f"{'='*60}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Date range: {args.from_date} to {args.to_date}")
    print(f"Forms: {args.forms}")
    print(f"Search: '{args.search}'")
    print(f"{'='*60}\n")
    
    # Setup
    name = config['sec']['name']
    email = config['sec']['email']
    model = config['gemini'].get('model', 'gemini-2.0-flash')
    api_key = config['gemini']['api_key']
    
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    sec = SECClient(email, name)
    
    # Search for filings
    print(f"Searching SEC Edgar for warrant filings...")
    form_types = [f.strip() for f in args.forms.split(',')]
    
    df_filings = sec.get_recent_filings(
        company=tickers,
        search_term=args.search,
        file_types=form_types,
        from_date=args.from_date,
        to_date=args.to_date,
        max_results=args.max_results
    )
    
    print(f"\n{'='*60}")
    print(f"Found {len(df_filings)} filings across {len(tickers)} ticker(s)")
    print(f"{'='*60}\n")
    
    if len(df_filings) == 0:
        print("No filings found. Try:")
        print("  - Broader date range")
        print("  - Different search terms")
        print("  - Check if ticker symbols are correct")
        return 0
    
    # Show summary by ticker
    if len(df_filings) > 0:
        summary = df_filings.groupby(['ticker', 'form']).size().reset_index(name='count')
        print("Filings by ticker and form:")
        print(summary.to_string(index=False))
        print()
    
    # Save filings list
    filings_file = str(cache_dir) + "/warrant_filings.csv"
    df_filings.to_csv(filings_file, index=False)
    print(f"Saved filings list to: {filings_file}\n")
    
    # Process with scraper
    scraper = SmartWarrantScraper(sec, model=model, api_key=api_key, filings_dir=str(cache_dir))
    
    if args.output:
        report_file = args.output
    else:
        report_file = f"output/Warrants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    print(f"{'='*60}")
    print(f"Extracting warrant specifications...")
    print(f"Output: {report_file}")
    print(f"{'='*60}\n")
    
    df_warrants = scraper.process_filings(df_filings, report_file, skip_cached=args.skip_cached)
    
    print(f"\n{'='*60}")
    print(f"Extraction Complete!")
    print(f"{'='*60}")
    print(f"Warrants found: {len(df_warrants)}")
    print(f"Results saved to: {report_file}")
    print(f"{'='*60}\n")
    
    if len(df_warrants) > 0:
        # Show summary
        print("Warrant Summary:")
        summary_cols = ['symbol', 'parent', 'strike_price', 'expiration_date', 
                       'conversion_ratio', 'has_call_trigger', 'call_trigger_price',
                       'spac_related', 'warrant_class']
        available_cols = [c for c in summary_cols if c in df_warrants.columns]
        print(df_warrants[available_cols].to_string(index=False))
        print()
        
        # Show call trigger details if present
        if 'has_call_trigger' in df_warrants.columns:
            callable_warrants = df_warrants[df_warrants['has_call_trigger'] == True]
            if len(callable_warrants) > 0:
                print(f"\n{len(callable_warrants)} warrant(s) have call triggers:")
                trigger_cols = ['symbol', 'call_trigger_price', 'call_trigger_days', 
                              'call_trigger_period', 'call_redemption_price']
                trigger_cols = [c for c in trigger_cols if c in callable_warrants.columns]
                print(callable_warrants[trigger_cols].to_string(index=False))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
