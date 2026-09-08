import os
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Union, List, Iterable, Tuple
import requests
import pandas as pd
import edgar as edgar

# EDGAR Full-Text Search (same backend the web UI hits)
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"

class SECClient:
    def __init__(self, email: str, name: str = "John Doe"):
        # SEC asks for a descriptive UA with contact info
        self.headers = {
            "User-Agent": f"EdgarQueryTool/1.0 ({email})",
            "Accept-Encoding": "gzip, deflate",
        }

        edgar.set_identity(f"{name} {email}")

    # --- tiny helpers ---------------------------------------------------------
    def _parse_date(self, d: Optional[str]) -> Optional[datetime]:
        if not d:
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(d, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(d.split("T")[0])
        except Exception:
            return None

    def _get_cik(self, ident: str) -> Optional[str]:
        """Return 10-digit CIK for a ticker or numeric CIK."""
        s = (ident or "").strip()
        if not s:
            return None
        if s.isdigit():
            return s.zfill(10)
        
        co = edgar.Company(s.upper())
        return None if co.cik < 1 else co.cik

    def _ensure_ciks(self, companies: Union[str, Iterable[str], None]) -> List[str]:
        if companies is None:
            return []
        if isinstance(companies, str):
            companies = [c.strip() for c in companies.split(",")] if "," in companies else [companies]
        out: List[str] = []
        for c in companies:
            cik10 = self._get_cik(str(c))
            if cik10:
                out.append(str(cik10).zfill(10))

        # de-dupe, preserve order
        seen = set(); uniq = []
        for c in out:
            if c not in seen:
                seen.add(c); uniq.append(c)
        return uniq

    def _parse_company_string(self, company_string: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse strings like:
        "AES CORP  (AES)  (CIK 0000874761)"  -> ("AES CORP", "AES", "0000874761")
        "AES CORP  (CIK 0000874761)"         -> ("AES CORP", None,  "0000874761")
        """
        if not company_string or not isinstance(company_string, str):
            return (None, None, None)

        s = company_string.strip()

        # 1) Extract CIK at the end (case-insensitive for 'CIK')
        m_cik = re.search(r'\((?i:CIK)\s*(\d+)\)\s*$', s)
        if not m_cik:
            return (None, None, None)

        cik = m_cik.group(1).strip()
        before_cik = s[:m_cik.start()].rstrip()

        # 2) Optionally extract a trailing "(TICKER)" just before CIK
        m_ticker = re.search(r'\(([^()]+)\)\s*$', before_cik)
        if m_ticker:
            ticker = m_ticker.group(1).strip()
            company_name = before_cik[:m_ticker.start()].rstrip()
        else:
            ticker = None
            company_name = before_cik

        company_name = company_name if company_name else None
        return (company_name, ticker, cik)
            
    def _fetch_filings_batch(self, params: dict, from_offset: int = 0, size: int = 100,
                             max_retries: int = 3) -> tuple[List[dict], Optional[int]]:
        """Fetch a single batch of filings with pagination.

        EFTS full-text phrase queries are heavy (often >1s) and the server
        sheds load with transient 500s. Retry those (and connection/timeout
        errors) with exponential backoff so a blip doesn't silently drop the
        CUSIP/full-text path -- the one that finds finance-sub bonds. Client
        errors (4xx) fail fast. After all retries, degrade to "no hits" so the
        caller returns nothing rather than crashing.
        """
        batch_params = params.copy()
        batch_params.update({
            "from": from_offset,
            "size": size
        })

        data = None
        backoff = 1.0
        for attempt in range(max_retries):
            try:
                r = requests.get(EFTS_URL, headers=self.headers,
                                 params=batch_params, timeout=30)
                if 500 <= r.status_code < 600:
                    raise requests.HTTPError(
                        f"{r.status_code} Server Error", response=r)
                r.raise_for_status()
                data = r.json()
                break
            except requests.RequestException as e:
                status = getattr(getattr(e, "response", None), "status_code", None)
                if status is not None and 400 <= status < 500:
                    print(f"EFTS request failed ({from_offset=}): {e}")
                    return [], None  # client error -- retrying won't help
                if attempt + 1 >= max_retries:
                    print(f"EFTS request failed after {max_retries} tries "
                          f"({from_offset=}): {e}")
                    return [], None
                time.sleep(backoff)
                backoff *= 2

        hits = []
        total_hits = None
        
        if isinstance(data.get("hits"), dict):
            # Extract total count from first call
            if "total" in data["hits"] and isinstance(data["hits"]["total"], dict):
                total_hits = data["hits"]["total"].get("value")
            
            # Extract the actual hits
            if isinstance(data["hits"].get("hits"), list):
                for h in data["hits"]["hits"]:
                    src = h.get("_source", {})
                    src["score"] = h.get("_score")
                    src["primary_document"] = h.get("_id", ":").split(":")[1]
                    hits.append(src)
        elif isinstance(data.get("hits"), list):
            hits.extend(data["hits"])

        return hits, total_hits

    # --- single-call recent filings ------------------------------------------
    def get_recent_filings(
        self,
        company: Union[str, List[str]] = None,
        search_term: str = None,
        file_types: Union[str, List[str]] = None,
        from_date: str = None,
        to_date: str = None,
        skip_ciks: List[str] = [],
        max_results: int = 5000,
    ) -> pd.DataFrame:
        """Query the EDGAR search index with pagination support.
        Args match the web UI:
          - company: tickers and/or CIKs (list or comma-separated str)
          - search_term: full-text query (e.g., '"Fixed-to-Fixed" OR "Fixed-to-Floating"')
          - file_types: list/CSV of form types (e.g., ['424B2','FWP'])
          - from_date/to_date: YYYY-MM-DD; defaults to last 5 years ending today if omitted.
          - skip_ciks: list of entities to skip based in their CIKs
          - max_results: maximum number of results to fetch (default 1000)
        Returns a tidy pandas DataFrame with one row per filing, duplicates removed.
        """
        # Defaults: to_date=today; from_date=5y before to_date
        to_dt = self._parse_date(to_date) or datetime.now()
        from_dt = self._parse_date(from_date) or (to_dt - timedelta(days=365*5))

        # Normalize inputs
        ciks = self._ensure_ciks(company)
        forms = None
        if file_types:
            if isinstance(file_types, str):
                forms = ",".join([s.strip().upper() for s in file_types.split(",")])
            else:
                forms = ",".join([str(s).strip().upper() for s in file_types])

        base_params = {
            **({"q": search_term} if search_term else {}),
            **({"ciks": ",".join(ciks)} if ciks else {}),
            **({"forms": forms} if forms else {}),
            "dateRange": "custom",
            "startdt": from_dt.strftime("%Y-%m-%d"),
            "enddt": to_dt.strftime("%Y-%m-%d"),
        }

        # Fetch all results with pagination
        all_hits = []
        from_offset = 0
        batch_size = 100
        total_available = None
        
        # First call to get total count
        hits, total_available = self._fetch_filings_batch(base_params, from_offset, batch_size)
        all_hits.extend(hits)
        from_offset += batch_size
        
        # Continue fetching if there are more results
        if total_available is not None:
            print(f"Total filings available: {total_available}")
            
            # Calculate how many more we need to fetch
            remaining_to_fetch = min(max_results - len(all_hits), total_available - len(all_hits))
            
            while remaining_to_fetch > 0 and from_offset < total_available:
                current_batch_size = min(batch_size, remaining_to_fetch)
                
                hits, _ = self._fetch_filings_batch(base_params, from_offset, current_batch_size)
                
                if not hits:
                    # No more results available
                    break
                    
                all_hits.extend(hits)
                from_offset += current_batch_size
                remaining_to_fetch = min(max_results - len(all_hits), total_available - len(all_hits))
        
        print(f"Fetched {len(all_hits)} filings")

        if not all_hits:
            return pd.DataFrame(columns=[
                "company_name","cik","form","filing_date","adsh","primary_document","score"
            ])

        rows = []
        for s in all_hits:
            # Clean the company name
            raw_name = (s.get("display_names") or [""])[0]
            company_name, ticker, cik = self._parse_company_string(raw_name)
            cik = (s.get("ciks") or [""])[0]
            if cik in skip_ciks:
                continue
            
            rows.append({
                "company_name": company_name,
                "ticker": ticker or "PRIVATE",
                "cik": cik,
                "form": s.get("form"),
                "filing_date": s.get("file_date"),
                "accession_no": s.get("adsh"),
                # "primary_document": s.get("primary_document"),
                # "score": s.get("score"),
                "filing_url": f'https://www.sec.gov/Archives/edgar/data/{cik.lstrip("0")}/{s.get("adsh").replace("-", "")}/{s.get("primary_document")}'
            })
            
        df = pd.DataFrame(rows)
        
        # Remove duplicates based on adsh (accession number)
        df = df.drop_duplicates(subset=['accession_no'], keep='first')
        
        if "filing_date" in df.columns:
            # df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")  # leave as str
            df = df.sort_values("filing_date", ascending=False)
            
        return df.reset_index(drop=True)

    def download_filing(self, ticker: str, accession_no: str, outdir: Optional[str] = None) -> Tuple[Optional[str], bool]:
        try:
            # If caching is enabled
            if outdir is not None:
                # Create cache directory for this ticker
                cache_dir = os.path.join(outdir, ticker)
                os.makedirs(cache_dir, exist_ok=True)
                
                # Cache file path
                cache_file = os.path.join(cache_dir, f"{ticker}.{accession_no}.txt")
                
                # Check if cached file exists
                if os.path.exists(cache_file):
                    # Read from cache
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_text = f.read()
                    text = cached_text
                    return text, True
            
            filing = edgar.find(accession_no)
            if filing.cik < 1:
                return None, False

            text = filing.text()
            
            # If caching is enabled, save to cache
            if outdir is not None:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(text)
            
            # Process and return the text
            return text, False
            
        except Exception:
            return None, False


if __name__ == "__main__":
    client = SECClient(email="hrseymour@gmail.com")
    
    # text = client.download_filing("AES", "0000874761")
    
    df = client.get_recent_filings(
        company=["AES"],  # , "FMC"
        # search_term='"Fixed-to-Fixed Reset Rate" OR "Fixed-to-Floating Rate"',
        # file_types=["424B1","424B2","424B3","424B4","424B5","424B7","424B8","FWP"],
        file_types=["FWP"],
        from_date="2020-08-26",
        to_date="2025-08-26"
    )
    print(f"Found {len(df)} unique filings")
    print(df.head(10).to_string(index=False))