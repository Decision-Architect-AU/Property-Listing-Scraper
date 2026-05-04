#!/usr/bin/env python3
"""
run_batch.py — Batch scraper orchestrator for Domain.com.au
════════════════════════════════════════════════════════════
Each run saves output to runs/YYYY-MM-DD/ containing:
  raw_listings.txt       — pipe-delimited working file (internal)
  raw_listings.json      — JSON snapshot after scraping, before descriptions
  enriched_listings.json — after descriptions + suburb stats
  scored_listings.json   — after three-pillar scoring
  Listings.xlsx          — formatted Excel report
  batch_progress.json    — resume state
  batch_run.log          — full run log

Usage:
    python run_batch.py                          # scrape all pending suburbs
    python run_batch.py --refresh                # re-scrape already-done suburbs
    python run_batch.py --skip-descs             # skip description fetching
    python run_batch.py --no-excel               # skip Excel build
    python run_batch.py --suburbs mylist.txt     # custom suburbs file
    python run_batch.py --max-pages 3            # fewer pages per suburb
    python run_batch.py --date 2026-04-30        # write to a specific run folder
"""

import argparse
import json
import os
import random
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper import curl_get, warm_cookies, build_search_url, parse_listings_page, extract_listing_desc, parse_land_m2
from scoring import score_listing
from suburb_stats import lookup as stats_lookup

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_DIR  = Path(__file__).parent
SUBURBS_FILE = PROJECT_DIR / "suburbs.txt"
MAX_PRICE    = 2_000_000
MAX_PAGES    = 5
PAGE_DELAY   = 8.0
DESC_DELAY   = 0.5
SUBURB_PAUSE = 5.0

# Run-specific paths — set by setup_run_dir()
RUN_DIR       = PROJECT_DIR
RAW_FILE      = RUN_DIR / "raw_listings.txt"
SCORED_FILE   = RUN_DIR / "scored_listings.json"
PROGRESS_FILE = RUN_DIR / "batch_progress.json"
LOG_FILE      = RUN_DIR / "batch_run.log"


def setup_run_dir(date_str: str = None) -> Path:
    """Create and set the dated run folder. Call before any other function."""
    global RUN_DIR, RAW_FILE, SCORED_FILE, PROGRESS_FILE, LOG_FILE
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    RUN_DIR       = PROJECT_DIR / "runs" / date_str
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    RAW_FILE      = RUN_DIR / "raw_listings.txt"
    SCORED_FILE   = RUN_DIR / "scored_listings.json"
    PROGRESS_FILE = RUN_DIR / "batch_progress.json"
    LOG_FILE      = RUN_DIR / "batch_run.log"
    return RUN_DIR


# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── Listing filtering ─────────────────────────────────────────────────────────
def _is_strata(address: str) -> bool:
    return bool(re.match(r"^\d+/\d+", address.strip()))


def should_keep(row: str) -> bool:
    parts = row.split("|")
    if len(parts) < 8:
        return False
    ptype   = parts[7].lower()
    address = parts[1]
    if ("new house" in ptype and "land" in ptype) or "new home design" in ptype:
        return False
    if _is_strata(address):
        return False
    return True


def scrape_suburb(slug: str, cookie_file: str, max_price: int, max_pages: int) -> list[str]:
    all_rows    = []
    total_pages = 1
    for page in range(1, max_pages + 1):
        if page > 1:
            time.sleep(max(PAGE_DELAY + random.uniform(-2, 2), 4))
        url = build_search_url(slug, max_price, page)
        try:
            html = curl_get(url, cookie_file)
        except Exception as e:
            log(f"  Page {page} fetch failed: {e}", "WARN")
            break
        rows, tl, tp = parse_listings_page(html)
        if page == 1:
            total_pages = tp
            log(f"  {tl} total listings across {tp} pages — fetching up to {min(max_pages, tp)}")
        if not rows:
            break
        all_rows.extend(rows)
        if page >= total_pages:
            break
    return [r for r in all_rows if should_keep(r)]


# ── raw_listings.txt management ───────────────────────────────────────────────
def append_rows(rows: list[str]) -> tuple[int, int]:
    """Deduplicate by listing ID (field[8]) and append new rows."""
    existing: list[str] = []
    if RAW_FILE.exists():
        existing = [l for l in RAW_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    seen: set[str] = set()
    for line in existing:
        parts = line.split("|")
        if len(parts) > 8:
            seen.add(parts[8].strip())
    new_rows = []
    for row in rows:
        parts = row.split("|")
        lid   = parts[8].strip() if len(parts) > 8 else ""
        if lid and lid not in seen:
            new_rows.append(row)
            seen.add(lid)
    final = existing + new_rows
    RAW_FILE.write_text("\n".join(final) + "\n", encoding="utf-8")
    return len(new_rows), len(final)


# ── JSON stage exports ────────────────────────────────────────────────────────
def _pipe_to_dict(line: str) -> dict:
    parts = line.split("|")
    def f(i): return parts[i].strip() if len(parts) > i else ""
    return {
        "suburb": f(0), "street": f(1), "price": f(2),
        "beds": f(3), "baths": f(4), "parking": f(5),
        "land": f(6), "type": f(7), "listing_id": f(8),
        "url": f(9), "headline": f(10), "date_listed": f(11),
        "listing_description": f(12),
    }


def save_raw_json():
    """Snapshot raw scraped data as JSON (no descriptions yet)."""
    lines   = [l.strip() for l in RAW_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    records = [_pipe_to_dict(l) for l in lines]
    (RUN_DIR / "raw_listings.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log(f"raw_listings.json saved ({len(records)} rows)")


def save_enriched_json():
    """Snapshot pipe-delimited data (with descriptions) as JSON, adding suburb stats."""
    lines   = [l.strip() for l in RAW_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    records = []
    for line in lines:
        rec      = _pipe_to_dict(line)
        is_house = 'house' in rec['type'].lower() or 'villa' in rec['type'].lower()
        stats    = stats_lookup(rec['suburb'])
        rec.update({
            "sub_median_rent_pw": stats.get("rent_house_pw" if is_house else "rent_unit_pw", 0),
            "sub_median_price":   stats.get("median_house"  if is_house else "median_unit",  0),
            "vacancy_pct":        stats.get("vacancy_pct", 0),
            "sqm_rating":         stats.get("sqm_rating", 0),
        })
        records.append(rec)
    (RUN_DIR / "enriched_listings.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log(f"enriched_listings.json saved ({len(records)} rows)")


# ── Description fetching ──────────────────────────────────────────────────────
def _compute_median_price() -> int:
    lines  = RAW_FILE.read_text(encoding="utf-8").splitlines() if RAW_FILE.exists() else []
    prices = []
    for line in lines:
        parts = line.strip().split("|")
        if len(parts) < 3:
            continue
        clean = parts[2].replace(",", "").replace("$", "").lower()
        pm    = re.search(r"(\d{6,})", clean)
        if pm:
            val = float(pm.group(1))
            if 100_000 < val < 10_000_000:
                prices.append(val)
    if not prices:
        return 0
    prices.sort()
    return int(prices[len(prices) // 2])


def _is_boring(parts: list[str], median: int) -> bool:
    if median == 0:
        return False
    clean = parts[2].replace(",", "").replace("$", "").lower() if len(parts) > 2 else ""
    pm    = re.search(r"(\d{6,})", clean)
    if not pm:
        return False
    val = float(pm.group(1))
    if val <= median:
        return False
    land_m2 = parse_land_m2(parts[6].strip() if len(parts) > 6 else "")
    try:
        beds = int(parts[3].strip() if len(parts) > 3 else "0")
    except ValueError:
        beds = 0
    return land_m2 > 0 and land_m2 < 500 and beds <= 3


def fetch_all_descriptions(skip_boring: bool = True) -> dict:
    lines  = RAW_FILE.read_text(encoding="utf-8").splitlines() if RAW_FILE.exists() else []
    median = _compute_median_price() if skip_boring else 0
    log(f"  Median price: ${median:,}" if median else "  Median price: unknown")
    todo, skipped = [], 0
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        parts    = line.split("|")
        if len(parts) < 10:
            continue
        existing = parts[12].strip() if len(parts) > 12 else ""
        url_part = parts[9].strip()
        if existing or not url_part.startswith("/"):
            continue
        if skip_boring and _is_boring(parts, median):
            skipped += 1
            continue
        todo.append(idx)

    total_needed = len(todo)
    log(f"  Descriptions needed: {total_needed}  skipped (boring): {skipped}")
    if not todo:
        return {"updated": 0, "skipped": skipped, "failed": 0}

    cookie_file = tempfile.mktemp(suffix=".txt")
    updated = failed = 0
    try:
        warm_cookies(cookie_file)
        for i, idx in enumerate(todo):
            parts    = lines[idx].split("|")
            url_part = parts[9].strip()
            time.sleep(DESC_DELAY + random.uniform(0, 0.3))
            try:
                html = curl_get(f"https://www.domain.com.au{url_part}", cookie_file, timeout=20)
                desc = extract_listing_desc(html)
                while len(parts) < 13:
                    parts.append("")
                parts[12]  = desc
                lines[idx] = "|".join(parts)
                updated += 1 if desc else 0
                failed  += 0 if desc else 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    log(f"  Desc fetch failed {url_part}: {e}", "WARN")
            if (i + 1) % 50 == 0:
                log(f"  Descriptions: {i+1}/{total_needed} ({(i+1)/total_needed*100:.0f}%)  updated={updated}  failed={failed}")
    finally:
        try:
            os.unlink(cookie_file)
        except Exception:
            pass
    RAW_FILE.write_text("\n".join(l for l in lines if l) + "\n", encoding="utf-8")
    return {"updated": updated, "skipped": skipped, "failed": failed}


# ── Scoring ───────────────────────────────────────────────────────────────────
def run_scoring():
    lines  = [l.strip() for l in RAW_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 9 or not parts[0].strip():
            continue
        def f(i): return parts[i].strip() if len(parts) > i else ""
        row = {
            "suburb": f(0), "street": f(1), "price": f(2),
            "beds":   f(3), "baths":  f(4), "parking": f(5),
            "land":   f(6), "type":   f(7), "listing_id": f(8),
            "url":    f(9), "description": f(10),
            "date_listed": f(11), "listing_description": f(12),
        }
        scored.append(score_listing(row))
    SCORED_FILE.write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"scored_listings.json saved ({len(scored)} rows)")
    return len(scored)


# ── Excel ─────────────────────────────────────────────────────────────────────
def run_excel():
    import importlib.util
    script = PROJECT_DIR / "build_excel.py"
    spec   = importlib.util.spec_from_file_location("build_excel", str(script))
    mod    = importlib.util.module_from_spec(spec)
    mod.__file__ = str(script)
    spec.loader.exec_module(mod)
    mod.main(scored_path=SCORED_FILE, out_path=RUN_DIR / "Listings.xlsx")
    log("Listings.xlsx saved")


# ── Progress ──────────────────────────────────────────────────────────────────
def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"completed": {}, "started": str(datetime.now())}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Batch Domain.com.au scraper")
    parser.add_argument("--suburbs",    default=str(SUBURBS_FILE))
    parser.add_argument("--refresh",    action="store_true", help="Re-scrape already-completed suburbs")
    parser.add_argument("--skip-descs", action="store_true", help="Skip description fetching")
    parser.add_argument("--no-excel",   action="store_true", help="Skip Excel build at end")
    parser.add_argument("--max-pages",  type=int, default=MAX_PAGES)
    parser.add_argument("--max-price",  type=int, default=MAX_PRICE)
    parser.add_argument("--date",       default=None, help="Run folder date override (YYYY-MM-DD)")
    args = parser.parse_args()

    run_dir = setup_run_dir(args.date)
    log(f"Run folder: {run_dir}")

    suburbs_path = Path(args.suburbs)
    if not suburbs_path.exists():
        print(f"ERROR: suburbs file not found: {suburbs_path}")
        sys.exit(1)

    slugs = [l.strip() for l in suburbs_path.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.strip().startswith("#")]
    if not slugs:
        print("ERROR: No suburb slugs found.")
        sys.exit(1)

    progress  = load_progress()
    completed = progress.get("completed", {})

    log("=" * 60)
    log(f"Batch scrape — {len(slugs)} suburbs  max-pages={args.max_pages}  max-price=${args.max_price:,}")
    log(f"Already completed: {len(completed)}  Refresh: {args.refresh}")
    log("=" * 60)

    cookie_file = tempfile.mktemp(suffix=".txt")
    total_added = 0

    try:
        warm_cookies(cookie_file)
        for i, slug in enumerate(slugs):
            if not args.refresh and slug in completed:
                log(f"[{i+1}/{len(slugs)}] SKIP {slug}")
                continue
            log(f"[{i+1}/{len(slugs)}] Scraping: {slug}")
            try:
                rows = scrape_suburb(slug, cookie_file, args.max_price, args.max_pages)
                log(f"  Scraped {len(rows)} listings")
            except KeyboardInterrupt:
                log("Interrupted — saving progress", "WARN")
                save_progress(progress)
                sys.exit(0)
            except Exception as e:
                log(f"  FAILED: {e}", "ERROR")
                progress["completed"][slug] = {"status": "error", "error": str(e), "ts": str(datetime.now())}
                save_progress(progress)
                continue
            added, total = append_rows(rows)
            total_added += added
            log(f"  New: {added}  Total in file: {total}")
            progress["completed"][slug] = {"status": "done", "scraped": len(rows), "added": added, "ts": str(datetime.now())}
            save_progress(progress)
            if i < len(slugs) - 1:
                time.sleep(SUBURB_PAUSE + random.uniform(0, 3))
    finally:
        try:
            os.unlink(cookie_file)
        except Exception:
            pass

    log(f"\nScraping complete — {total_added} new listings added")
    save_raw_json()

    if not args.skip_descs:
        log("\nFetching listing descriptions…")
        result = fetch_all_descriptions(skip_boring=True)
        log(f"  Updated: {result['updated']}  Skipped: {result['skipped']}  Failed: {result['failed']}")

    log("\nSaving enriched_listings.json…")
    save_enriched_json()

    log("\nScoring listings…")
    run_scoring()

    if not args.no_excel:
        log("Building Excel…")
        run_excel()

    log(f"\n✅ Done. Output: {run_dir}")


if __name__ == "__main__":
    main()
