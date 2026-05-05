#!/usr/bin/env python3
"""
build_suburb_list.py — Generate a filtered Domain.com.au suburb slug list
from the suburbs_stats_extracted.xlsx data file.

Merges SQM Research stats, Fast 50 membership, and auto-generated Domain
search slugs into a master JSON, then outputs a filtered suburbs.txt.

Usage:
    # All defaults — write all suburbs to Ref_Suburbs.json, suburbs.txt
    python build_suburb_list.py

    # Filter to QLD only, Fast 50 only, high SQM rating
    python build_suburb_list.py --state QLD --fast50 --min-rating 3.5

    # Low vacancy, affordable markets, NSW only
    python build_suburb_list.py --state NSW --max-vacancy 1.5 --max-price 900000

    # Write to a custom file
    python build_suburb_list.py --output my_suburbs.txt

Output files:
    Ref_Suburbs.json  — full enriched record for every suburb in the stats file
    suburbs.txt (or --output) — one Domain slug per line for run_batch.py
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── Fast 50 set ───────────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from regions import FAST_50
except ImportError:
    FAST_50 = set()

PROJECT_DIR  = Path(__file__).parent
STATS_FILE   = PROJECT_DIR / "suburbs_stats_extracted.xlsx"
MASTER_JSON  = PROJECT_DIR / "Ref_Suburbs.json"
DEFAULT_OUT  = PROJECT_DIR / "suburbs.txt"


# ── Domain slug generator ─────────────────────────────────────────────────────

_STATE_SLUG = {
    "QLD": "qld", "NSW": "nsw", "VIC": "vic", "SA": "sa",
    "WA": "wa", "TAS": "tas", "ACT": "act", "NT": "nt",
}


def _to_slug(suburb: str, state: str) -> str:
    slug_state = _STATE_SLUG.get(state.upper(), state.lower())
    name_part  = re.sub(r"[^a-z0-9]+", "-", suburb.strip().lower()).strip("-")
    return f"{name_part}-{slug_state}"


def _to_slug_with_postcode(suburb: str, state: str, postcode: str) -> str:
    base = _to_slug(suburb, state)
    if postcode and re.match(r"^\d{4}$", str(postcode)):
        return f"{base}-{postcode}"
    return base


# ── Stats loader ──────────────────────────────────────────────────────────────

def load_stats() -> list[dict]:
    if not STATS_FILE.exists():
        print(f"ERROR: {STATS_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    try:
        import openpyxl
    except ImportError:
        print("ERROR: openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    wb = openpyxl.load_workbook(str(STATS_FILE), read_only=True, data_only=True)
    ws = wb.active

    def _f(v):
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0

    def _i(v):
        try:
            return int(v) if v is not None else 0
        except Exception:
            return 0

    records = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or not row or not row[19]:
            continue

        suburb   = str(row[19]).strip()
        state    = str(row[20] or "").strip().upper()
        postcode = str(row[18] or "").strip()

        rec = {
            "suburb":          suburb,
            "state":           state,
            "postcode":        postcode,
            "sqm_rating":      _f(row[1]),
            "vacancy_pct":     _f(row[3]),
            "rent_house_pw":   _i(row[5]),
            "rent_unit_pw":    _i(row[7]),
            "yield_house_pct": _f(row[9]),
            "yield_unit_pct":  _f(row[11]),
            "median_house":    _i(row[14]),
            "median_unit":     _i(row[17]),
            "fast_50":         suburb in FAST_50,
            "domain_slug":     _to_slug_with_postcode(suburb, state, postcode),
        }
        records.append(rec)

    wb.close()
    return records


# ── Filters ───────────────────────────────────────────────────────────────────

def apply_filters(records, state=None, fast50_only=False, min_rating=0.0,
                  max_vacancy=100.0, max_price=0, region=None):
    out = records
    if state:
        out = [r for r in out if r["state"].upper() == state.upper()]
    if fast50_only:
        out = [r for r in out if r["fast_50"]]
    if min_rating > 0:
        out = [r for r in out if r["sqm_rating"] >= min_rating]
    if max_vacancy < 100.0:
        out = [r for r in out if 0 < r["vacancy_pct"] <= max_vacancy]
    if max_price > 0:
        out = [r for r in out if (
            (r["median_house"] > 0 and r["median_house"] <= max_price) or
            (r["median_unit"]  > 0 and r["median_unit"]  <= max_price)
        )]
    if region:
        out = [r for r in out if region.lower() in r["suburb"].lower()]
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build Domain.com.au suburb slug list from SQM stats file"
    )
    parser.add_argument("--state",       default=None)
    parser.add_argument("--fast50",      action="store_true")
    parser.add_argument("--min-rating",  type=float, default=0.0)
    parser.add_argument("--max-vacancy", type=float, default=100.0)
    parser.add_argument("--max-price",   type=int,   default=0)
    parser.add_argument("--region",      default=None)
    parser.add_argument("--output",      default=str(DEFAULT_OUT))
    parser.add_argument("--no-master",   action="store_true")
    args = parser.parse_args()

    records = load_stats()
    print(f"Loaded {len(records)} suburbs")

    if not args.no_master:
        MASTER_JSON.write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Ref_Suburbs.json saved ({len(records)} records)")

    filtered = apply_filters(
        records,
        state       = args.state,
        fast50_only = args.fast50,
        min_rating  = args.min_rating,
        max_vacancy = args.max_vacancy,
        max_price   = args.max_price,
        region      = args.region,
    )
    print(f"After filters: {len(filtered)} suburbs")

    if not filtered:
        print("WARNING: No suburbs matched — suburbs.txt not written.")
        return

    seen_slugs, slugs = set(), []
    for r in sorted(filtered, key=lambda x: (x["state"], x["suburb"])):
        slug = r["domain_slug"]
        if slug not in seen_slugs:
            slugs.append(f"{slug}  # {r['suburb']} {r['state']} | rating={r['sqm_rating']} vac={r['vacancy_pct']}%")
            seen_slugs.add(slug)

    out_path = Path(args.output)
    out_path.write_text("\n".join(slugs) + "\n", encoding="utf-8")
    print(f"Written {len(slugs)} slugs -> {out_path}")


if __name__ == "__main__":
    main()
