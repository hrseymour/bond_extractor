# bond-scraper

Production-ready corporate bond extractor that parses SEC EDGAR filings and returns database-ready rows
using Google's Gemini 2.5 models via the `google-genai` SDK. Organized for maintainability, tested helpers,
and configuration via `config.ini`/`config.secrets.ini` (no env vars required).

## Install (uv)

```bash
# install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# create a local venv and install
cd bond-scraper-uv
uv venv .venv
source .venv/bin/activate
```

# install/upgrade dependencies from pyproject.toml

uv sync --upgrade

## Configure

Create `config.secrets.ini` with your Google Gemini API Key:

```text
[gemini]
api_key = YOUR_GOOGLE_GEMINI_API_KEY
```

Edit `config.ini` to input your email address and select your desired Gemini model.

## Run the example

```bash
cd scripts
python run_example.py
```

Results are written to `./output/` as CSV and JSON. See `scripts/run_example.py` for how to pass your own company list.
