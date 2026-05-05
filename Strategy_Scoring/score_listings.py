#!/usr/bin/env python3
"""
score_listings.py -- CLI wrapper
Reads raw_listings.txt (pipe-delimited) -> scored_listings.json

Field layout (pipe-delimited):
  0  suburb          6  land
  1  street          7  type
  2  price           8  listing_id
  3  beds            9  url
  4  baths          10  headline / short description
  5  parking        11  listing_description (full text, populated by fetch_descriptions)

Usage:
    python score_listings.py --raw raw_listings.txt --out scored_listings.json
"""

import argparse
import importlib
import json
import sys
from pathlib import Path

# Force reload of scoring module so any changes to scoring.py are picked up
# even when this module is loaded via importlib in a long-running process.
if "scoring" in sys.modules:
    importlib.reload(sys.modules["scoring"])

from scoring import score_listing


def parse_row(parts):
    def f(i): return parts[i].strip() if len(parts) > i else ""
    return {
        "suburb":              f(0),
        "street":              f(1),
        "price":               f(2),
        "beds":                f(3),
        "baths":               f(4),
        "parking":             f(5),
        "land":                f(6),
        "type":                f(7),
        "listing_id":          f(8),
        "url":                 f(9),
        "description":         f(10),
        "listing_description": f(11),
        "date_listed":         "",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    raw_path = Path(args.raw)
    out_path = Path(args.out)

    if not raw_path.exists():
        print("ERROR: {} not found".format(raw_path), file=sys.stderr)
        sys.exit(1)

    lines   = [l.strip() for l in raw_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored  = []
    skipped = 0

    for line in lines:
        parts = line.split("|")
        if len(parts) < 9:
            skipped += 1
            continue
        row = parse_row(parts)
        if not row["suburb"]:
            skipped += 1
            continue
        result = score_listing(row)
        if result is None:
            skipped += 1
            continue
        scored.append(result)

    out_path.write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Scored {} listings -> {}  (skipped {})".format(len(scored), out_path, skipped))


if __name__ == "__main__":
    main()
