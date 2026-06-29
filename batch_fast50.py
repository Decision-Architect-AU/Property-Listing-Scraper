#!/usr/bin/env python3
"""
batch_fast50.py — Weekly Fast 50 suburb scraper.

Opens ONE Chrome session, scrapes all suburbs in fast50_suburbs.txt,
appends to C:\\DomainListingData, then scores + builds Excel + emails report.

Run every Tuesday night via Windows Task Scheduler:
    python "C:\\Users\\Glenn\\Documents\\Claude\\Projects\\Property Listing Scraper\\batch_fast50.py"

Logs are written to C:\\DomainListingData\\batch_YYYYMMDD_HHMM.log
"""

import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_DIR  = Path(r"C:\Users\Glenn\Documents\Claude\Projects\Property Listing Scraper")
DATA_DIR     = Path(r"C:\DomainListingData")
SUBURBS_FILE = PROJECT_DIR / "fast50_suburbs.txt"

# Scraping config
MAX_PRICE   = 2_000_000
MAX_PAGES   = 5
PAGE_DELAY  = 8.0   # seconds between pages within a suburb
SUB_DELAY   = 12.0  # seconds between suburbs (polite pause)

sys.path.insert(0, str(PROJECT_DIR))

# Import browser + parsing helpers from domain_mcp (avoids duplicating code)
from domain_mcp import (
    _uc_session,
    _uc_fetch,
    _build_url,
    _extract_rows_from_html,
    _polite_delay,
    _should_keep,
)


# ─── Logging ──────────────────────────────────────────────────────────────────
_log_path: Path | None = None

def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"{ts}  {msg}"
    print(line, flush=True)
    if _log_path:
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# ─── Suburb list ──────────────────────────────────────────────────────────────
def load_suburbs() -> list[str]:
    if not SUBURBS_FILE.exists():
        raise FileNotFoundError(f"Suburbs file not found: {SUBURBS_FILE}")
    lines = SUBURBS_FILE.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


# ─── Scrape one suburb (reusing existing driver) ──────────────────────────────
def scrape_suburb(driver, slug: str) -> tuple[list[str], int, list[str]]:
    """
    Scrape up to MAX_PAGES of listings for a suburb slug.
    Returns (kept_rows, total_available, errors).
    """
    all_rows: list[str] = []
    errors:   list[str] = []
    total_listings = 0
    total_pages    = 1

    for page_num in range(1, MAX_PAGES + 1):
        if page_num > 1:
            time.sleep(PAGE_DELAY + random.uniform(-1, 2))

        url = _build_url(slug, MAX_PRICE, page_num)
        try:
            html = _uc_fetch(driver, url, settle=1.0)
        except Exception as e:
            errors.append(f"Page {page_num}: {e}")
            break

        rows, tl, tp = _extract_rows_from_html(html)

        if page_num == 1:
            total_listings = tl
            total_pages    = tp

            # Detect Akamai block
            if tl == 0 and "Access Denied" in html:
                errors.append("Akamai block detected — Chrome session may need refresh")
                break

        if not rows:
            break

        all_rows.extend(rows)

        if page_num >= total_pages:
            break

    kept = [r for r in all_rows if _should_keep(r)]
    return kept, total_listings, errors


# ─── Append rows to raw_listings.txt ──────────────────────────────────────────
def append_to_data(rows: list[str], suburb_name: str) -> dict:
    """Merge rows into DATA_DIR/raw_listings.txt, replacing old rows for this suburb."""
    raw_path = DATA_DIR / "raw_listings.txt"
    existing: list[str] = []
    if raw_path.exists():
        existing = raw_path.read_text(encoding="utf-8").splitlines()

    # Remove old rows for this suburb
    suburb_lower = suburb_name.lower()
    before   = len(existing)
    existing = [l for l in existing if l and l.split("|")[0].strip().lower() != suburb_lower]
    removed  = before - len(existing)

    # Deduplicate by listing_id
    seen_ids: set[str] = set()
    for line in existing:
        parts = line.split("|")
        if len(parts) > 8:
            seen_ids.add(parts[8].strip())

    new_rows: list[str] = []
    for row in rows:
        parts = row.split("|")
        lid = parts[8].strip() if len(parts) > 8 else ""
        if lid and lid not in seen_ids:
            new_rows.append(row)
            seen_ids.add(lid)

    final = existing + new_rows
    raw_path.write_text("\n".join(l for l in final if l) + "\n", encoding="utf-8")
    return {"rows_written": len(new_rows), "rows_removed": removed, "total_rows": len([l for l in final if l])}


# ─── Score listings ────────────────────────────────────────────────────────────
def score_all() -> int:
    """Run score_listings.py against DATA_DIR/raw_listings.txt → scored_listings.json."""
    import importlib.util

    script   = PROJECT_DIR / "score_listings.py"
    raw_path = DATA_DIR / "raw_listings.txt"
    out_path = DATA_DIR / "scored_listings.json"

    spec = importlib.util.spec_from_file_location("score_listings", str(script))
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    lines  = [l.strip() for l in raw_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 9 or not parts[0].strip():
            continue
        row = {
            "suburb":              parts[0].strip(),
            "street":              parts[1].strip(),
            "price":               parts[2].strip(),
            "beds":                parts[3].strip(),
            "baths":               parts[4].strip(),
            "parking":             parts[5].strip(),
            "land":                parts[6].strip(),
            "type":                parts[7].strip(),
            "listing_id":          parts[8].strip(),
            "url":                 parts[9].strip()  if len(parts) > 9  else "",
            "description":         parts[10].strip() if len(parts) > 10 else "",
            "listing_description": parts[11].strip() if len(parts) > 11 else "",
        }
        scored.append(mod.score_listing(row))

    out_path.write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(scored)


# ─── Build Excel ───────────────────────────────────────────────────────────────
def build_excel() -> Path:
    """Run build_excel.py, writing SEQ_Listings.xlsx to DATA_DIR."""
    import importlib.util

    script     = PROJECT_DIR / "build_excel.py"
    scored     = DATA_DIR / "scored_listings.json"
    out_xlsx   = DATA_DIR / "SEQ_Listings.xlsx"

    spec = importlib.util.spec_from_file_location("build_excel", str(script))
    mod  = importlib.util.module_from_spec(spec)
    mod.__file__ = str(script)
    sys.path.insert(0, str(PROJECT_DIR))
    spec.loader.exec_module(mod)
    mod.main(scored_path=scored, out_path=out_xlsx)
    sys.path.pop(0)
    return out_xlsx


# ─── Send report ───────────────────────────────────────────────────────────────
def send_email_report() -> str:
    """Load send_report.py and email the Fast 50 report."""
    import importlib.util

    script = PROJECT_DIR / "send_report.py"
    spec   = importlib.util.spec_from_file_location("send_report", str(script))
    mod    = importlib.util.module_from_spec(spec)
    mod.__file__ = str(script)
    spec.loader.exec_module(mod)
    result = mod.send_report()
    return result.get("message", "Unknown result")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    global _log_path

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _log_path = DATA_DIR / f"batch_{datetime.now().strftime('%Y%m%d_%H%M')}.log"

    suburbs = load_suburbs()
    start   = datetime.now()
    _log(f"{'='*60}")
    _log(f"Fast 50 Batch  —  {start.strftime('%A %d %b %Y %H:%M')}")
    _log(f"Suburbs: {len(suburbs)}  |  Data → {DATA_DIR}")
    _log(f"{'='*60}")

    success_count = 0
    fail_count    = 0
    total_written = 0

    with _uc_session() as driver:
        for i, slug in enumerate(suburbs, 1):
            suburb_name = slug.split("-")[0].title()
            _log(f"\n[{i:02d}/{len(suburbs)}] {suburb_name}  ({slug})")

            try:
                rows, total_avail, errors = scrape_suburb(driver, slug)

                if errors:
                    for e in errors:
                        _log(f"  ⚠  {e}")

                if rows:
                    result = append_to_data(rows, suburb_name)
                    _log(f"  ✓  {result['rows_written']} written  |  {result['rows_removed']} replaced  |  {result['total_rows']} total in file")
                    total_written += result["rows_written"]
                    success_count += 1
                else:
                    _log(f"  —  No listings kept (total available on site: {total_avail})")
                    if not errors:
                        success_count += 1  # suburb processed, just no results

            except Exception as e:
                _log(f"  ✗  ERROR: {e}")
                fail_count += 1

            # Polite pause between suburbs (skip after last one)
            if i < len(suburbs):
                time.sleep(SUB_DELAY + random.uniform(-2, 4))

    _log(f"\n{'='*60}")
    _log(f"Scraping done  —  {success_count} ok  |  {fail_count} failed  |  {total_written} new rows")

    # ── Score ──────────────────────────────────────────────────────────────────
    _log("\nScoring listings…")
    try:
        n = score_all()
        _log(f"  ✓  Scored {n} listings → {DATA_DIR / 'scored_listings.json'}")
    except Exception as e:
        _log(f"  ✗  Scoring failed: {e}")
        sys.exit(1)

    # ── Excel ──────────────────────────────────────────────────────────────────
    _log("\nBuilding Excel…")
    try:
        xlsx = build_excel()
        _log(f"  ✓  {xlsx}")
    except Exception as e:
        _log(f"  ✗  Excel build failed: {e}")

    # ── Email ──────────────────────────────────────────────────────────────────
    _log("\nSending report…")
    try:
        msg = send_email_report()
        _log(f"  ✓  {msg}")
    except Exception as e:
        _log(f"  ✗  Email failed: {e}")

    elapsed = datetime.now() - start
    _log(f"\n{'='*60}")
    _log(f"Batch complete in {int(elapsed.total_seconds() // 60)}m {int(elapsed.total_seconds() % 60)}s")
    _log(f"Log: {_log_path}")


if __name__ == "__main__":
    main()
