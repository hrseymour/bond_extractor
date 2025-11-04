# Warrant Extractor

A comprehensive tool for scraping and extracting stock warrant specifications from SEC Edgar filings using LLM-based parsing.

## Overview

This system extracts detailed warrant information from SEC filings (8-A, 424B series) and structures it according to the `Warrant` table schema. It uses Google's Gemini model to parse complex legal documents and extract ~60+ fields covering:

- Basic warrant terms (strike price, expiration, conversion ratio)
- Call/redemption triggers (the most critical feature)
- Exercise and settlement terms
- Anti-dilution provisions
- Ownership limits and restrictions
- Registration rights
- SEC filing URLs

## Project Structure

```
.
├── config.py                          # Configuration loader
├── config.ini                         # Main config (SEC identity)
├── config.secrets.ini                 # Secrets (Gemini API key)
├── src/
│   ├── sec_client.py                  # SEC Edgar API client
│   ├── utils.py                       # Shared utilities
│   ├── warrant_models.py              # Warrant data models (NEW)
│   ├── warrant_extractor.py           # LLM warrant extraction (NEW)
│   └── warrant_scraper.py             # Orchestration layer (NEW)
├── scripts/
│   ├── run_warrant_example.py         # Example: Extract DSX warrants (NEW)
│   └── run_example.py                 # Original: Extract rate reset bonds
└── output/
    ├── warrant_cache/                 # Cached SEC filings
    └── Warrants_YYYYMMDD_HHMMSS.csv  # Extraction results
```

## Setup

### 1. Configuration Files

Create `config.ini`:
```ini
[sec]
name = Your Name
email = your@email.com

[gemini]
model = gemini-2.0-flash
```

Create `config.secrets.ini`:
```ini
[gemini]
api_key = your_gemini_api_key_here
```

### 2. Dependencies

```bash
pip install google-genai pandas requests edgar-tool beautifulsoup4
```

### 3. Run Setup Script (Optional)

```bash
./setup_warrant_extractor.sh
```

## Usage

### Basic Example: Extract DSX Warrants

```bash
python scripts/run_warrant_example.py
```

This will:
1. Search SEC Edgar for warrant-related filings from DSX (Diana Shipping)
2. Download filings (8-A, 424B2/3/5 types)
3. Extract warrant specifications using Gemini
4. Save results to `output/Warrants_YYYYMMDD_HHMMSS.csv`

### Custom Extraction

```python
from src.sec_client import SECClient
from src.warrant_scraper import SmartWarrantScraper
from config import config

# Initialize
sec = SECClient(config['sec']['email'], config['sec']['name'])
scraper = SmartWarrantScraper(
    sec,
    model=config['gemini']['model'],
    api_key=config['gemini']['api_key'],
    filings_dir="output/warrant_cache"
)

# Search for filings
df_filings = sec.get_recent_filings(
    company=["DSX", "IONQ"],  # Multiple tickers
    search_term='warrant',
    file_types=["8-A", "424B2", "424B5"],
    from_date="2020-01-01",
    to_date="2025-11-03"
)

# Extract warrants
df_warrants = scraper.process_filings(
    df_filings,
    report_file="output/my_warrants.csv",
    skip_cached=False
)
```

## Output Format

The CSV output contains all fields from the `Warrant` table schema:

### Core Fields
- `symbol`, `parent`, `exchange`, `currency`
- `strike_price`, `expiration_date`, `conversion_ratio`
- `issue_date`, `warrant_type`

### Exercise & Settlement
- `exercise_type` (American/European/Bermuda)
- `settlement_type` (Physical/Cash/NetShare)
- `allows_cashless_exercise`, `cashless_exercise_formula`

### Call Triggers (CRITICAL)
- `has_call_trigger`
- `call_trigger_price` (e.g., $18.00)
- `call_trigger_days` (e.g., 20 days)
- `call_trigger_period` (e.g., 30 consecutive days)
- `call_redemption_price` (e.g., $0.01)
- `call_trigger_notice_days`

### Anti-Dilution & Adjustments
- `has_anti_dilution`, `anti_dilution_type`
- `adjusts_for_stock_splits`, `adjusts_for_dividends`, etc.

### Ownership & Transfer
- `has_ownership_limit`, `ownership_limit_pct` (e.g., 4.99%)
- `is_transferable`, `is_publicly_traded`

### Classification
- `spac_related`, `warrant_class` (Public/Private/Founder)
- `notes` (free-form for unusual terms)

Columns with all null values are automatically dropped from the output.

## Key Features

### 1. Intelligent Filing Search
- Uses SEC Edgar full-text search API
- Filters by form type (8-A, 424B series)
- Supports multiple companies in batch
- Pagination for large result sets

### 2. LLM-Based Extraction
- Uses Gemini 2.0 Flash (or 2.5 Pro) for parsing
- Extracts structured JSON from legal documents
- Handles multiple warrant classes per filing
- Normalizes dates, percentages, and enums

### 3. Caching
- Downloaded filings cached by ticker and accession number
- Avoids redundant SEC requests
- Speeds up re-runs during development

### 4. Incremental Output
- CSV saved after each warrant extracted
- Safe to interrupt and resume
- Progress tracking

## Comparison to Bond Extractor

This warrant extractor follows the same architecture as the rate reset bond extractor:

| Component | Bond Extractor | Warrant Extractor |
|-----------|---------------|-------------------|
| Models | `src/models.py` | `src/warrant_models.py` |
| Extractor | `src/extractor.py` | `src/warrant_extractor.py` |
| Scraper | `src/scraper.py` | `src/warrant_scraper.py` |
| Example | `scripts/run_example.py` | `scripts/run_warrant_example.py` |
| Output | `Bonds_YYYYMMDD.csv` | `Warrants_YYYYMMDD_HHMMSS.csv` |

Both use:
- Same `SECClient` for filing discovery and download
- Same `utils.py` for normalization
- Same Gemini model and prompting strategy
- Same incremental CSV output pattern

## Tips for Best Results

### 1. Filing Type Selection
- **8-A**: Primary warrant registration documents
- **424B2/B5**: Prospectus supplements with warrant terms
- **6-K**: For foreign issuers (use if needed)

### 2. Search Terms
- `'warrant'` - broad, good starting point
- `'warrant agreement'` - more specific
- `'exercise price'` or `'redemption'` - narrow to key terms

### 3. Call Triggers
- These are THE most important feature for investors
- Pattern: "may redeem if stock trades at/above $X for Y out of Z days"
- Often in Section 6 or "Redemption" sections
- LLM is good at finding these even when buried

### 4. SPAC Warrants
- Very common and standardized
- Typical terms: $11.50 strike, 5 year expiration, $18 call trigger
- Often have both Public and Private warrant classes

### 5. Handling Exotic Features
- Most warrants DON'T have knock-in/knock-out provisions
- If found, they'll appear in the extraction
- Unusual terms can be noted in the `notes` field

## Troubleshooting

### No Filings Found
- Check that the ticker symbol is correct
- Verify the date range includes warrant issuance
- Try broader search terms (just `'warrant'`)
- Check if company uses different filing types

### Extraction Errors
- Review the raw filing text (cached in `output/warrant_cache/`)
- Check if filing is actually a warrant document
- Some filings mention warrants but don't contain full terms

### API Rate Limits
- SEC Edgar: ~10 requests/second limit
- Gemini: Check your quota
- Use caching to avoid redundant requests

## Future Enhancements

Potential improvements:
1. Add support for warrant amendments (track term changes)
2. Build warrant symbol discovery (find all warrants automatically)
3. Add market data integration (current prices, volumes)
4. Support for international warrants (non-US exchanges)
5. Database insertion (directly populate SQL Server)

## License

Internal tool for financial analysis.

## Contact

Questions? Check the handoff documentation in `Handoff.md`.
