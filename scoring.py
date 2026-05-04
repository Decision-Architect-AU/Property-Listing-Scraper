"""
scoring.py — Three-Pillar Investment Scoring Engine
Edit this file to tune scores, add/remove signals, or adjust DOM thresholds.

Imports suburb knowledge from regions.py.
"""

import re
from datetime import date

from regions import (
    ZONING, REZONE_POTENTIAL, HIGH_REZONE, MEDIUM_REZONE,
    FAST_50, DEFAULT_ZONE, CASHFLOW_DEMAND_SUBURBS,
)
from rent_estimator import estimate_rent
from suburb_stats import lookup as stats_lookup

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_land_m2(land_str: str) -> float:
    """Convert '600m²', '1.2ha', '4000sqm' → m²."""
    if not land_str:
        return 0.0
    s = land_str.lower().replace(",", "").strip()
    if "ha" in s:
        m = re.search(r"([\d.]+)\s*ha", s)
        return float(m.group(1)) * 10000 if m else 0.0
    if "acre" in s:
        m = re.search(r"([\d.]+)\s*acre", s)
        return float(m.group(1)) * 4046.86 if m else 0.0
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else 0.0


def parse_price(price_str: str) -> float:
    """Extract first numeric value from a price display string."""
    if not price_str:
        return 0.0
    s = price_str.replace(",", "").replace("$", "")
    m = re.search(r"(\d+)", s)
    return float(m.group(1)) if m else 0.0


def keyword(text: str, *words: str) -> bool:
    t = text.lower()
    return any(w.lower() in t for w in words)


def days_on_market(date_listed: str) -> int:
    """Return days since listing date, or 0 if unknown/unparseable."""
    if not date_listed:
        return 0
    try:
        listed = date.fromisoformat(str(date_listed)[:10])
        return max(0, (date.today() - listed).days)
    except Exception:
        return 0


# ── Scoring engine ────────────────────────────────────────────────────────────

def score_listing(row: dict) -> dict:
    suburb       = row.get("suburb", "").strip()
    street       = row.get("street", "").strip()
    price_s      = row.get("price", "").strip()
    desc         = row.get("description", "").strip()
    listing_desc = row.get("listing_description", "").strip()
    beds         = str(row.get("beds", "")).strip()
    baths        = str(row.get("baths", "")).strip()
    land_s       = row.get("land", "").strip()
    ptype        = row.get("type", "").strip().lower()
    url_raw      = row.get("url", "").strip()
    date_listed  = row.get("date_listed", "").strip()
    state        = row.get("state", "").strip()

    all_text = f"{price_s} {desc} {listing_desc} {street}".lower()

    zone_info  = ZONING.get(suburb, DEFAULT_ZONE)
    rezone_pot = REZONE_POTENTIAL.get(suburb, "UNKNOWN")
    fast50     = suburb in FAST_50
    land_m2    = parse_land_m2(land_s)
    price_n    = parse_price(price_s)
    beds_n     = int(beds) if beds.isdigit() else 0
    dom        = days_on_market(date_listed)

    # History-derived fields (populated by listing_tracker.enrich_row)
    price_changes       = int(row.get("price_changes", 0) or 0)
    price_reduction_pct = float(row.get("price_reduction_pct", 0.0) or 0.0)
    price_reduction_n   = float(row.get("price_reduction_n", 0.0) or 0.0)
    desc_changes        = int(row.get("desc_changes", 0) or 0)
    history_dom         = int(row.get("history_dom", 0) or 0)

    # Use history DOM when listing date is missing / unreliable
    effective_dom = history_dom if history_dom > dom else dom

    # ── Growth ────────────────────────────────────────────────
    g_score, g_signals = 0, []

    if suburb in HIGH_REZONE:
        g_score += 4;  g_signals.append("High rezone suburb")
    elif suburb in MEDIUM_REZONE:
        g_score += 2;  g_signals.append("Rezone corridor")

    if land_m2 >= 800:
        g_score += 3;  g_signals.append("800m²+ block")
    elif land_m2 >= 600:
        g_score += 2;  g_signals.append("600m²+ block")
    elif land_m2 >= 400:
        g_score += 1;  g_signals.append("400m²+ block")

    if "house" in ptype and "new" not in ptype:
        g_score += 1;  g_signals.append("Established house")

    full_addr = f"{street} {suburb}".lower()
    if re.search(r"\bcorner\b|\bcnr\b", full_addr):
        g_score += 1;  g_signals.append("Corner block")

    if keyword(all_text, "subdivision", "stca", "dual occ", "subdivide"):
        g_score += 1;  g_signals.append("Subdivision/STCA (description)")

    if fast50:
        g_score += 1;  g_signals.append("Fast 50 suburb")

    g_score = min(g_score, 10)

    # ── Deals ─────────────────────────────────────────────────
    d_score, d_signals = 0, []

    if price_n > 0:
        if price_n < 500_000:
            d_score += 2;  d_signals.append("Entry <$500K")
        elif price_n < 650_000:
            d_score += 2;  d_signals.append("Entry <$650K")
        elif price_n < 750_000:
            d_score += 1;  d_signals.append("Entry <$750K")

    if keyword(all_text,
               "motivated seller", "motivated vendor", "must sell",
               "price reduced", "reduced to sell", "below market", "below valuation",
               "urgent sale", "urgently selling", "owner must sell", "relocating",
               "overseas", "deceased estate", "mortgagee", "financial difficulty"):
        d_score += 1;  d_signals.append("Motivated vendor")

    if keyword(all_text, "contact agent", "contact the agent", "call agent",
               "expression of interest", "eoi"):
        d_score += 1;  d_signals.append("Contact agent / EOI")

    if keyword(all_text, "as is", "as-is", "as is where is"):
        d_score += 1;  d_signals.append("Sold as-is")

    if keyword(all_text, "divorce", "estate", "mortgagee", "deceased"):
        d_score += 2;  d_signals.append("Distressed sale")

    if keyword(all_text, "auction"):
        d_score += 1;  d_signals.append("Auction — price discovery")

    # Days on market signals — use the better of listing date vs history DOM
    if effective_dom >= 180:
        d_score += 3;  d_signals.append(f"Very stale listing ({effective_dom}d on market)")
    elif effective_dom >= 90:
        d_score += 2;  d_signals.append(f"Long-listed ({effective_dom}d on market)")
    elif effective_dom >= 60:
        d_score += 1;  d_signals.append(f"Stale listing ({effective_dom}d on market)")

    # Price cut history signals
    if price_reduction_pct >= 10.0:
        d_score += 3
        d_signals.append(f"Price cut {price_reduction_pct:.1f}% (${price_reduction_n:,.0f} off ask)")
    elif price_reduction_pct >= 5.0:
        d_score += 2
        d_signals.append(f"Price cut {price_reduction_pct:.1f}% (${price_reduction_n:,.0f} off)")
    elif price_changes >= 2:
        d_score += 2
        d_signals.append(f"Multiple price drops ({price_changes}x reductions)")
    elif price_changes == 1:
        d_score += 1
        d_signals.append(f"Price reduced once (${price_reduction_n:,.0f} off)")

    # Description relaunch — vendor refreshing a stale campaign
    if desc_changes >= 2:
        d_score += 2;  d_signals.append(f"Listing relaunched {desc_changes}x — vendor motivated")
    elif desc_changes == 1:
        d_score += 1;  d_signals.append("Description updated — campaign refresh")

    d_score = min(d_score, 10)

    # ── Cashflow ──────────────────────────────────────────────
    c_score, c_signals = 0, []

    if beds_n >= 5:
        c_score += 3;  c_signals.append("NDIS/SDA — premium rental yield")
    elif beds_n >= 4:
        c_score += 1;  c_signals.append("4-bed — strong rental demand")

    if land_m2 >= 600 and beds_n >= 3:
        c_score += 2;  c_signals.append("Granny flat potential (600m²+)")
    elif land_m2 >= 450:
        c_score += 1;  c_signals.append("Granny flat possible (450m²+)")

    if keyword(all_text, "dual key", "dual income", "dual occ", "duplex"):
        c_score += 2;  c_signals.append("Dual income / duplex")
    if keyword(all_text, "invest", "tenant", "tenanted", "rental income"):
        c_score += 1;  c_signals.append("Investment / tenanted")
    if keyword(all_text, "ndis", "sda", "specialist disability"):
        c_score += 2;  c_signals.append("NDIS/SDA confirmed")
    if keyword(all_text, "granny flat", "secondary dwelling", "studio"):
        c_score += 2;  c_signals.append("Granny flat / secondary dwelling")

    if suburb in CASHFLOW_DEMAND_SUBURBS:
        c_score += 1;  c_signals.append("Near hospital/TAFE — rental demand")

    # Negative: premium owner-occupier language → poor cashflow fit
    if keyword(all_text,
               "elegant family home", "luxury family home", "executive family home",
               "stunning family home", "perfect family home", "prestige family home",
               "dream family home"):
        c_score = max(0, c_score - 2)
        c_signals.append("⚠️ Premium family home — cashflow discount")

    c_score = min(c_score, 10)

    # ── Delinquent flags ──────────────────────────────────────
    delinquent        = False
    delinquent_signal = "—"
    if keyword(all_text, "fire damage", "flood damage", "uninhabitable", "demo only", "demolish"):
        delinquent        = True
        delinquent_signal = "🔥 Uninhabitable — fire/flood/demo"
    elif keyword(all_text, "as is where is", "as-is") and keyword(all_text, "fire", "damage", "destroyed"):
        delinquent        = True
        delinquent_signal = "Damage — sold as-is"

    url = f"https://www.domain.com.au{url_raw}" if url_raw.startswith("/") else url_raw

    # ── Rent & yield enrichment ───────────────────────────────
    rent_info = estimate_rent(listing_desc, beds, ptype, suburb, state)
    annual_rent      = rent_info['annual_rent']
    weekly_rent      = rent_info['weekly_rent']
    rent_assumptions = rent_info['assumptions']

    is_house    = 'house' in ptype or 'villa' in ptype
    stats       = stats_lookup(suburb, state)

    # Suburb stats
    sub_rent_pw = stats.get('rent_house_pw', 0) if is_house else stats.get('rent_unit_pw', 0)
    sub_median  = stats.get('median_house', 0)  if is_house else stats.get('median_unit', 0)
    vacancy_pct = stats.get('vacancy_pct', 0)
    sqm_rating  = stats.get('sqm_rating', 0)

    # Gross yield — use listing price where known; substitute suburb median when price is missing
    gross_yield = 0.0
    if annual_rent:
        if price_n >= 10_000:
            gross_yield = round(annual_rent / price_n * 100, 2)
        elif sub_median >= 10_000:
            # Price unknown (Contact Agent / Auction) — fall back to suburb median price
            gross_yield = round(annual_rent / sub_median * 100, 2)
            median_note = f"suburb median price ${sub_median:,} used (listing price unknown)"
            rent_assumptions = (f"{rent_assumptions}; {median_note}"
                                if rent_assumptions else median_note)

    # ── Yield-based cashflow score ────────────────────────────
    # <5% = average (no bonus), 5–6% = ok, 6–7% = above avg,
    # 7–8% = good, 8–9% = high, 9%+ = excellent
    if gross_yield >= 9.0:
        c_score += 5; c_signals.append(f"Yield {gross_yield:.1f}% — excellent cashflow")
    elif gross_yield >= 8.0:
        c_score += 4; c_signals.append(f"Yield {gross_yield:.1f}% — high cashflow")
    elif gross_yield >= 7.0:
        c_score += 3; c_signals.append(f"Yield {gross_yield:.1f}% — good cashflow")
    elif gross_yield >= 6.0:
        c_score += 2; c_signals.append(f"Yield {gross_yield:.1f}% — above average cashflow")
    elif gross_yield >= 5.0:
        c_score += 1; c_signals.append(f"Yield {gross_yield:.1f}% — average cashflow")
    # <5% adds nothing
    c_score = min(c_score, 10)

    # Cashflow score boost for strong-yield indicators from stats
    if sqm_rating >= 3.5 and vacancy_pct <= 1.0:
        c_score = min(10, c_score + 1)
        c_signals.append(f"Low vacancy ({vacancy_pct}%) — strong rental demand")

    return {
        "suburb":              suburb,
        "address":             f"{street} {suburb}".strip(),
        "price":               price_s,
        "description":         desc,
        "listing_description": listing_desc,
        "beds":                beds,
        "baths":               baths,
        "parking":             row.get("parking", ""),
        "land":                land_s,
        "type":                row.get("type", ""),
        "listing_id":          row.get("listing_id", ""),
        "url":                 url,
        "fast_50":             fast50,
        "growth_score":        g_score,
        "growth_signals":      "; ".join(g_signals) if g_signals else "—",
        "deals_score":         d_score,
        "deals_signals":       "; ".join(d_signals) if d_signals else "—",
        "cashflow_score":      c_score,
        "cashflow_signals":    "; ".join(c_signals) if c_signals else "—",
        "delinquent":          delinquent,
        "delinquent_signal":   delinquent_signal,
        "zone":                zone_info.get("zone", ""),
        "council":             zone_info.get("council", ""),
        "zone_notes":          zone_info.get("notes", ""),
        "rezone_potential":    rezone_pot,
        "date_listed":         date_listed,
        "days_on_market":      effective_dom if effective_dom > 0 else "",
        "scraped_date":        str(date.today()),
        # History / SCD fields
        "price_changes":       price_changes,
        "price_reduction_pct": price_reduction_pct,
        "price_reduction_n":   price_reduction_n,
        "desc_changes":        desc_changes,
        "first_seen":          row.get("first_seen", ""),
        "history_dom":         history_dom,
        # Rent & yield
        "annual_rent":         annual_rent,
        "weekly_rent":         weekly_rent,
        "rent_assumptions":    rent_assumptions,
        "gross_yield_pct":     gross_yield,
        "rent_source":         rent_info['rent_source'],
        # Suburb stats
        "sub_median_rent_pw":  sub_rent_pw,
        "sub_median_price":    sub_median,
        "vacancy_pct":         vacancy_pct,
        "sqm_rating":          sqm_rating,
    }
