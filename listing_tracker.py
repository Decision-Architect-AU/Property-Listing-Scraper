#!/usr/bin/env python3
"""
listing_tracker.py — Tracks listing presence across weekly scrape runs.

For each suburb scrape, compares the freshly scraped listing IDs against
the previously tracked set for that suburb. Any listing that was active
last run but missing from this run is marked "delisted". Any delisted
listing that reappears is reactivated (e.g. contract collapsed).

Storage: listing_status.json  (same folder as this script)

Schema per entry:
  {
    "<listing_id>": {
      "suburb":        "Toowoomba",
      "status":        "active" | "delisted" | "sold",
      "first_seen":    "2026-04-28",
      "last_seen":     "2026-05-05",
      "delisted_date": "2026-05-05"   # only when status = delisted
    }
  }
"""

import json
from datetime import date
from pathlib import Path


TRACKER_FILE = Path(__file__).parent / "listing_status.json"


def _load() -> dict:
    if TRACKER_FILE.exists():
        try:
            return json.loads(TRACKER_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    TRACKER_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def update_suburb(suburb: str, current_ids: list[str]) -> dict:
    """
    Update tracker for a freshly scraped suburb.

    Args:
        suburb:      Suburb name (e.g. "Toowoomba")
        current_ids: List of listing_id strings from the latest scrape

    Returns a summary dict:
        {
          "new":         int,   # first time we've seen these
          "reactivated": int,   # were delisted, now back
          "delisted":    int,   # were active, now missing
          "unchanged":   int,   # still active, seen again
        }
    """
    today      = str(date.today())
    data       = _load()
    current_set = set(current_ids)

    # All previously tracked IDs for this suburb
    prev_active = {
        lid for lid, info in data.items()
        if info.get("suburb", "").lower() == suburb.lower()
        and info.get("status") == "active"
    }

    counts = {"new": 0, "reactivated": 0, "delisted": 0, "unchanged": 0}

    # Process currently scraped listings
    for lid in current_ids:
        if lid not in data:
            # Brand new listing
            data[lid] = {
                "suburb":     suburb,
                "status":     "active",
                "first_seen": today,
                "last_seen":  today,
            }
            counts["new"] += 1
        else:
            existing = data[lid]
            if existing.get("status") == "delisted":
                # Reactivated — contract collapsed or relisted
                existing["status"]       = "active"
                existing["last_seen"]    = today
                existing["suburb"]       = suburb
                existing.pop("delisted_date", None)
                counts["reactivated"] += 1
            else:
                existing["status"]    = "active"
                existing["last_seen"] = today
                existing["suburb"]    = suburb
                counts["unchanged"] += 1

    # Listings that were active last run but missing this run → delist
    missing = prev_active - current_set
    for lid in missing:
        data[lid]["status"]       = "delisted"
        data[lid]["delisted_date"] = today
        counts["delisted"] += 1

    _save(data)
    return counts


def get_status(listing_id: str) -> str:
    """Return status string for a listing_id ('active', 'delisted', 'sold', or 'unknown')."""
    data = _load()
    return data.get(listing_id, {}).get("status", "unknown")


def is_active(listing_id: str) -> bool:
    """Return True if the listing is active (or has never been tracked = assume active)."""
    status = get_status(listing_id)
    return status in ("active", "unknown")


def apply_to_scored(scored: list[dict]) -> list[dict]:
    """
    Stamp each scored listing with tracker status.
    If the tracker says 'delisted', override active=False regardless of scoring.
    """
    data = _load()
    for listing in scored:
        lid    = str(listing.get("listing_id", ""))
        info   = data.get(lid, {})
        status = info.get("status", "unknown")

        if status == "delisted":
            listing["active"]         = False
            listing["status"]         = "delisted"
            listing["delisted_date"]  = info.get("delisted_date", "")
        elif status == "active" and listing.get("status") != "sold":
            listing["active"]  = True
            listing["status"]  = "active"

    return scored


def suburb_summary(suburb: str) -> dict:
    """Return counts of active/delisted/sold for a given suburb."""
    data   = _load()
    suburb = suburb.lower()
    counts = {"active": 0, "delisted": 0, "sold": 0, "total": 0}
    for info in data.values():
        if info.get("suburb", "").lower() == suburb:
            counts["total"] += 1
            s = info.get("status", "active")
            if s in counts:
                counts[s] += 1
    return counts
