# Warrant Extractor - Quick Start Guide

## Installation (One-Time Setup)

1. **Copy files to your project directory:**
   ```bash
   # Copy the warrant extractor files alongside your existing bond extractor
   cp -r src/warrant_*.py /path/to/your/project/src/
   cp scripts/extract_warrants.py /path/to/your/project/scripts/
   cp scripts/run_warrant_example.py /path/to/your/project/scripts/
   ```

2. **Verify your config files have the required sections:**
   
   `config.ini`:
   ```ini
   [sec]
   name = Your Name
   email = your@email.com
   
   [gemini]
   model = gemini-2.5-pro  # or gemini-2.0-flash
   ```
   
   `config.secrets.ini`:
   ```ini
   [gemini]
   api_key = your_gemini_api_key
   ```

3. **No new dependencies needed!** The warrant extractor uses the same packages as your bond extractor.

## Usage Examples

### Example 1: Single Ticker (DSX)
```bash
python scripts/extract_warrants.py DSX
```

### Example 2: Multiple Tickers
```bash
python scripts/extract_warrants.py DSX IONQ SPCE
```

### Example 3: From a File
Create `tickers.txt`:
```
DSX
IONQ
SPCE
# You can add comments with #
```

Then run:
```bash
python scripts/extract_warrants.py --from-file tickers.txt
```

### Example 4: Custom Date Range
```bash
python scripts/extract_warrants.py DSX --from-date 2022-01-01 --to-date 2024-12-31
```

### Example 5: Run the Test Script
```bash
python scripts/run_warrant_example.py
```

## Output

Results are saved to `output/Warrants_YYYYMMDD_HHMMSS.csv` with columns like:
- `symbol`, `parent`, `strike_price`, `expiration_date`
- `has_call_trigger`, `call_trigger_price`, `call_trigger_days`
- `conversion_ratio`, `exercise_type`, `settlement_type`
- And ~50 more fields (empty columns are dropped)

## Command Line Options

```bash
python scripts/extract_warrants.py --help
```

Key options:
- `--from-date YYYY-MM-DD` - Start date (default: 2020-01-01)
- `--to-date YYYY-MM-DD` - End date (default: today)
- `--forms 8-A,424B2` - Form types to search (default: 8-A,424B2,424B3,424B5)
- `--search "warrant"` - Search term (default: "warrant")
- `--output file.csv` - Output file (default: auto-generated)
- `--skip-cached` - Skip cached filings
- `--max-results 100` - Max filings per ticker (default: 100)

## What Gets Extracted

### Core Terms (Always Present)
- Strike price (exercise price)
- Expiration date
- Conversion ratio (shares per warrant)
- Issue date
- Parent ticker (underlying stock)

### Call Triggers (Most Important!)
- Call trigger price (e.g., $18.00)
- Call trigger pattern (e.g., "20 out of 30 days")
- Redemption price (what issuer pays if called)
- Notice period (days of notice required)

### Exercise & Settlement
- Exercise type (American/European/Bermuda)
- Settlement type (Physical/Cash/Net Share)
- Cashless exercise availability

### Adjustments
- Stock split adjustments
- Dividend adjustments
- Anti-dilution provisions
- Merger/spinoff handling

### Restrictions
- Ownership limits (e.g., 4.99% blocker)
- Transfer restrictions
- Registration rights

### Classification
- SPAC-related flag
- Warrant class (Public/Private/Founder)
- Notes for unusual terms

## Troubleshooting

**No filings found?**
- Verify ticker symbol is correct
- Try broader date range
- Check if company is US-listed (6-K forms for foreign)

**API errors?**
- Check Gemini API key in `config.secrets.ini`
- Verify rate limits aren't exceeded
- Check internet connection

**Extraction looks wrong?**
- Review cached filing: `output/warrant_cache/{TICKER}/{TICKER}.{accession}.txt`
- Check if filing actually contains warrant terms
- Some filings mention warrants but lack full specifications

## Next Steps

1. **Test with DSX** (known good example):
   ```bash
   python scripts/extract_warrants.py DSX
   ```

2. **Review output CSV** to verify fields extracted correctly

3. **Scale up** by adding more tickers to `tickers.txt`

4. **Import to SQL Server** using pandas:
   ```python
   import pandas as pd
   import pyodbc
   
   df = pd.read_csv('output/Warrants_20251103_120000.csv')
   
   conn = pyodbc.connect('DRIVER={SQL Server};SERVER=...;DATABASE=QTFIL;...')
   df.to_sql('Warrant', conn, if_exists='append', index=False)
   ```

## File Structure

After copying files, your project should look like:

```
your_project/
├── config.py
├── config.ini
├── config.secrets.ini
├── src/
│   ├── sec_client.py          (existing)
│   ├── utils.py                (existing)
│   ├── models.py               (existing - bonds)
│   ├── extractor.py            (existing - bonds)
│   ├── scraper.py              (existing - bonds)
│   ├── warrant_models.py       (NEW)
│   ├── warrant_extractor.py    (NEW)
│   └── warrant_scraper.py      (NEW)
├── scripts/
│   ├── run_example.py          (existing - bonds)
│   ├── run_warrant_example.py  (NEW)
│   └── extract_warrants.py     (NEW)
└── output/
    ├── warrant_cache/          (NEW - created automatically)
    └── Warrants_*.csv          (NEW - output files)
```

## Support

For detailed information, see `README_WARRANT.md`.

For questions about the warrant table schema, see `Warrant.sql` and `Handoff.md`.
