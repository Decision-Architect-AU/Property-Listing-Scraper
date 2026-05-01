#!/usr/bin/env python3
"""
score_listings.py — CLI wrapper
Reads raw_listings.txt (pipe-delimited) → scored_listings.json

Field layout (pipe-delimited):
  0  suburb          6  land
  1  street          7  type
  2  price           8  listing_id
  3  beds            9  url
  4  baths          10  headline
  5  parking        11  date_listed
                   12  listing_description

Usage:
    python score_listings.py --raw raw_listings.txt --out scored_listings.json
"""

import argparse
import json
import sys
from pathlib import Path

from scoring import score_listing


def parse_row(parts: list[str]) -> dict:
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
        "date_listed":         f(11),
        "listing_description": f(12),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    raw_path = Path(args.raw)
    out_path = Path(args.out)

    if not raw_path.exists():
        print(f"ERROR: {raw_path} not found", file=sys.stderr)
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
        scored.append(score_listing(row))

    out_path.write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Scored {len(scored)} listings → {out_path}  (skipped {skipped})")


if __name__ == "__main__":
    main()
