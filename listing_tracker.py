"""
listing_tracker.py — Slowly Changing Dimension (SCD) tracker for Domain listings.

Compares raw_listings.txt against the stored listing_history.json, records
price and description changes, and enriches listing rows with their full
change history before scoring.

History schema per listing_id:
  listing_id          str
  suburb / street     str
  first_seen          YYYY-MM-DD
  last_seen           YYYY-MM-DD
  original_price      str   — price text on first_seen
  original_price_n    float — parsed dollar amount on first_seen
  current_price       str
  current_price_n     float
  price_changes       int   — number of price change events
  price_reduction_n   float — total $ drop from original (0 if gone up)
  price_reduction_pct float — % drop from original
  desc_changes        int   — number of description changes
  snapshots           list  — [{date, price, price_n, listing_description, change}]
"""

import json
import re
from datetime import date
from pathlib import Path


# ── Price parsing ─────────────────────────────────────────────────────────────

def _parse_price_n(price_str: str) -> float:
    """Extract first numeric dollar value from a price string, or 0."""
    if not price_str:
        return 0.0
    s = price_str.replace(",", "").replace("$", "")
    m = re.search(r"(\d{5,})", s)   # must be at least 5 digits (≥$10,000)
    return float(m.group(1)) if m else 0.0


def _price_is_known(price_n: float) -> bool:
    return price_n >= 50_000


# ── History I/O ───────────────────────────────────────────────────────────────

def load_history(history_path: str) -> dict:
    """Load listing_history.json. Returns empty dict if file doesn't exist."""
    p = Path(history_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_history(history: dict, history_path: str):
    Path(history_path).write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── Core update ───────────────────────────────────────────────────────────────

def update_history(raw_listings_path: str, history_path: str) -> dict:
    """
    Read raw_listings.txt and update listing_history.json with any changes.

    Detects:
      - New listings (first_seen recorded)
      - Price drops / increases
      - Description changes (triggers re-score signal)

    Returns stats dict:
      {new, price_dropped, price_increased, desc_changed, unchanged, total}
    """
    today    = str(date.today())
    history  = load_history(history_path)

    # Parse current listings into a dict keyed by listing_id
    current: dict[str, dict] = {}
    raw_path = Path(raw_listings_path)
    if not raw_path.exists():
        return {"new": 0, "price_dropped": 0, "price_increased": 0,
                "desc_changed": 0, "unchanged": 0, "total": 0}

    for line in raw_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 9:
            continue
        lid = parts[8].strip()
        if not lid:
            continue
        current[lid] = {
            "suburb":              parts[0].strip(),
            "street":              parts[1].strip(),
            "price":               parts[2].strip(),
            "price_n":             _parse_price_n(parts[2].strip()),
            "listing_id":          lid,
            "listing_description": parts[11].strip() if len(parts) > 11 else "",
        }

    stats = {"new": 0, "price_dropped": 0, "price_increased": 0,
             "desc_changed": 0, "unchanged": 0, "total": len(current)}

    for lid, cur in current.items():
        cur_price_n = cur["price_n"]
        cur_desc    = cur["listing_description"]

        if lid not in history:
            # ── New listing ──────────────────────────────────────────────────
            history[lid] = {
                "listing_id":          lid,
                "suburb":              cur["suburb"],
                "street":              cur["street"],
                "first_seen":          today,
                "last_seen":           today,
                "original_price":      cur["price"],
                "original_price_n":    cur_price_n,
                "current_price":       cur["price"],
                "current_price_n":     cur_price_n,
                "price_changes":       0,
                "price_reduction_n":   0.0,
                "price_reduction_pct": 0.0,
                "desc_changes":        0,
                "snapshots": [{
                    "date":               today,
                    "price":              cur["price"],
                    "price_n":            cur_price_n,
                    "listing_description": cur_desc,
                    "change":             "first_seen",
                }],
            }
            stats["new"] += 1
            continue

        # ── Existing listing — check for changes ─────────────────────────────
        h           = history[lid]
        h["last_seen"] = today
        prev_price_n   = h.get("current_price_n", 0)
        prev_desc      = (h["snapshots"][-1].get("listing_description", "")
                         if h.get("snapshots") else "")
        changed        = False
        snapshot_change = None

        # Price change?
        if (_price_is_known(cur_price_n) and _price_is_known(prev_price_n)
                and cur_price_n != prev_price_n
                and cur["price"] != h.get("current_price", "")):

            h["price_changes"]  = h.get("price_changes", 0) + 1
            h["current_price"]  = cur["price"]
            h["current_price_n"] = cur_price_n

            orig = h.get("original_price_n", cur_price_n) or cur_price_n
            drop = orig - cur_price_n
            h["price_reduction_n"]   = max(0.0, drop)
            h["price_reduction_pct"] = round(max(0.0, drop / orig * 100), 1) if orig else 0.0

            if cur_price_n < prev_price_n:
                snapshot_change = "price_drop"
                stats["price_dropped"] += 1
            else:
                snapshot_change = "price_increase"
                stats["price_increased"] += 1
            changed = True

        # Description change?
        if cur_desc and cur_desc != prev_desc:
            h["desc_changes"] = h.get("desc_changes", 0) + 1
            if not snapshot_change:
                snapshot_change = "desc_changed"
                stats["desc_changed"] += 1
            changed = True

        if changed and snapshot_change:
            h.setdefault("snapshots", []).append({
                "date":               today,
                "price":              cur["price"],
                "price_n":            cur_price_n,
                "listing_description": cur_desc,
                "change":             snapshot_change,
            })
        elif not changed:
            stats["unchanged"] += 1

    save_history(history, history_path)
    return stats


# ── Row enrichment ────────────────────────────────────────────────────────────

def enrich_row(row: dict, history: dict) -> dict:
    """
    Add history-derived fields to a listing row dict before scoring.

    Fields added:
      price_changes       int   — number of price change events
      price_reduction_pct float — % reduction from original ask
      price_reduction_n   float — $ reduction from original ask
      desc_changes        int   — number of description relaunches
      first_seen          str   — date first scraped (YYYY-MM-DD)
      history_dom         int   — days on market from our first_seen date
    """
    lid = row.get("listing_id", "")
    h   = history.get(lid, {})

    first_seen = h.get("first_seen", "")
    history_dom = 0
    if first_seen:
        try:
            from datetime import date as _date
            history_dom = max(0, (_date.today() - _date.fromisoformat(first_seen)).days)
        except Exception:
            pass

    row["price_changes"]       = h.get("price_changes", 0)
    row["price_reduction_pct"] = h.get("price_reduction_pct", 0.0)
    row["price_reduction_n"]   = h.get("price_reduction_n", 0.0)
    row["desc_changes"]        = h.get("desc_changes", 0)
    row["first_seen"]          = first_seen
    row["history_dom"]         = history_dom   # our own DOM, more reliable than listing date

    return row
