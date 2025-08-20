# bond-scraper

Production-ready corporate bond extractor that parses SEC EDGAR filings and returns database-ready rows
using Google's Gemini 2.5 models via the `google-genai` SDK. Organized for maintainability, tested helpers,
and configuration via `config.ini`/`config.secrets.ini` (no env vars required).

## Features
- Gemini-powered structured extraction (fixed, floating, and rate-reset bonds)
- Database-ready normalization (decimals, ISO dates, numeric frequencies/amounts)
- Graceful JSON parsing and cleaning
- SEC-friendly client and simple caching hooks
- Summary statistics utilities
- `uv`-friendly Python project (also ships a `requirements.txt`)

## Install (uv)

```bash
# install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# create a local venv and install
cd bond-scraper-uv
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Alternatively, you can use the `pyproject.toml` directly:

```bash
uv sync
```

## Configure

Copy the provided examples and fill in your values:

```bash
cp config.ini.example config.ini
cp config.secrets.ini.example config.secrets.ini
```

Edit both files. Put the Gemini API key in `config.secrets.ini`. Choose the model in `config.ini`.

## Run the example

```bash
python scripts/run_example.py
```

Results are written to `./output/` as CSV and JSON. See `scripts/run_example.py` for how to pass your own company list.

## Tests

```bash
pytest -q
```

## Notes
- This project reads configuration using the provided `config.py` helper (case-sensitive, no interpolation).
- By default, the example uses `gemini-2.5-flash`. Change the model in `config.ini`.
- Be mindful of SEC rate limits and provide a real email for the `User-Agent` header.
