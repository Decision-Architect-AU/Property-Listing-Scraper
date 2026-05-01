"""
scraper.py — Domain.com.au HTTP fetching and listing page parsing
Edit this file when Domain changes their JSON structure or search URL format.

Used by both run_batch.py and domain_mcp.py.
"""

import json
import random
import re
import subprocess
import time

# ── Request headers ───────────────────────────────────────────────────────────
DOMAIN_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}


# ── HTTP ──────────────────────────────────────────────────────────────────────

def curl_get(url: str, cookie_file: str, timeout: int = 20) -> str:
    cmd = [
        "curl", "-s", "-L", "--max-time", str(timeout), "--compressed",
        "--cookie", cookie_file, "--cookie-jar", cookie_file,
        "-H", f"User-Agent: {DOMAIN_HEADERS['User-Agent']}",
        "-H", f"Accept: {DOMAIN_HEADERS['Accept']}",
        "-H", f"Accept-Language: {DOMAIN_HEADERS['Accept-Language']}",
        "-H", "Cache-Control: max-age=0",
        "-H", "Sec-Fetch-Dest: document",
        "-H", "Sec-Fetch-Mode: navigate",
        "-H", "Sec-Fetch-Site: none",
        "-H", "Upgrade-Insecure-Requests: 1",
        url,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    return r.stdout


def warm_cookies(cookie_file: str):
    """Hit the Domain homepage to seed session cookies."""
    try:
        curl_get("https://www.domain.com.au/", cookie_file, timeout=15)
        time.sleep(random.uniform(2, 4))
    except Exception:
        pass


# ── URL builder ───────────────────────────────────────────────────────────────

def build_search_url(slug: str, max_price: int, page: int = 1) -> str:
    base = (
        f"https://www.domain.com.au/sale/{slug}/"
        f"?excludeunderoffer=1&property-type=house&price=0-{max_price}"
    )
    return f"{base}&page={page}" if page > 1 else base


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_land_m2(land_str: str) -> float:
    """Convert '600m²', '1.2ha', '4000sqm' → float m²."""
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


def _extract_next_data(html: str) -> dict:
    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
        html, re.DOTALL,
    )
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}


# ── Search results parser ─────────────────────────────────────────────────────

def parse_listings_page(html: str) -> tuple[list[str], int, int]:
    """
    Parse a Domain search results page.
    Returns (rows, total_listings, total_pages)
    rows are pipe-delimited strings:
      suburb|street|price|beds|baths|parking|land|type|listing_id|url|headline|date_listed|
    (field[12] = listing_description, left empty here — filled by fetch_descriptions)
    """
    data = _extract_next_data(html)
    if not data:
        return [], 0, 0

    props     = data.get("props", {}).get("pageProps", {})
    component = props.get("componentProps", props)

    listings = (
        component.get("listingsMap")
        or component.get("listings")
        or props.get("listings")
        or data.get("listings")
        or []
    )
    if isinstance(listings, dict):
        listings = list(listings.values())

    pagination = (
        component.get("pagination")
        or props.get("pagination")
        or {}
    )
    total_listings = int(pagination.get("totalResults", len(listings)) or len(listings))
    total_pages    = int(pagination.get("totalPages", 1) or 1)

    rows = []
    for listing in listings:
        lid = listing.get("id", "")
        if not lid:
            continue
        try:
            lm       = listing.get("listingModel") or {}
            raw_addr = lm.get("address") or listing.get("address") or {}
            addr     = raw_addr if isinstance(raw_addr, dict) else {}
            suburb   = addr.get("suburb", "") or ""
            street   = (addr.get("street", "")
                        or (raw_addr if isinstance(raw_addr, str) else "")
                        or lm.get("displayAddress", "")
                        or listing.get("displayAddress", "")
                        or "")

            raw_price = lm.get("price") or listing.get("price") or {}
            price_obj = raw_price if isinstance(raw_price, dict) else {}
            price = (
                price_obj.get("displayPrice", "")
                or price_obj.get("display", "")
                or (raw_price if isinstance(raw_price, str) else "")
                or lm.get("displaySearchPriceRange", "")
                or listing.get("displayPrice", "")
                or ""
            )

            raw_feats = (lm.get("features")
                         or listing.get("features")
                         or listing.get("propertyFeatures")
                         or {})
            beds = baths = parking = land = ptype = ""
            if isinstance(raw_feats, dict):
                beds    = raw_feats.get("beds",    raw_feats.get("bedroomsCount",    raw_feats.get("bedrooms", "")))
                baths   = raw_feats.get("baths",   raw_feats.get("bathroomsCount",   raw_feats.get("bathrooms", "")))
                parking = raw_feats.get("parking", raw_feats.get("parkingSpacesCount", raw_feats.get("parkingSpaces", "")))
                ptype   = raw_feats.get("propertyTypeFormatted") or raw_feats.get("propertyType") or ""
                land_val = raw_feats.get("landSize") or raw_feats.get("land")
                if land_val:
                    raw_unit = str(raw_feats.get("landUnit") or raw_feats.get("landSizeUnit") or "m²")
                    try:
                        raw_unit = raw_unit.encode("latin-1").decode("utf-8")
                    except Exception:
                        pass
                    unit = raw_unit.replace("sqm", "m²").replace("square metres", "m²")
                    land = f"{land_val}{unit}"
            elif isinstance(raw_feats, list):
                for item in raw_feats:
                    s = str(item).lower().strip()
                    fm = re.match(r"(\d+)\s*(bed|bath|park|garage|car)", s)
                    if fm:
                        n = fm.group(1)
                        if "bed" in s:    beds    = n
                        elif "bath" in s: baths   = n
                        else:             parking = n
                    lm2 = re.match(r"([\d,]+\.?\d*)\s*(m²|sqm|ha|acre)", s)
                    if lm2:
                        land = f"{lm2.group(1)}{lm2.group(2).replace('sqm','m²')}"

            if not ptype:
                ptype = listing.get("listingType") or lm.get("listingType") or ""

            actual_price = lm.get("displaySearchPriceRange") or price
            lid_str      = str(listing.get("id") or lid)
            raw_url      = lm.get("url") or listing.get("listingSlug") or listing.get("seoUrl") or ""
            url          = "/" + raw_url.lstrip("/") if raw_url else ""

            # Listing date
            raw_date = (
                lm.get("dateListed") or lm.get("listedDate")
                or lm.get("dateFirstListed") or lm.get("dateCreated")
                or listing.get("dateListed") or listing.get("listedDate")
                or listing.get("dateCreated") or ""
            )
            date_listed = ""
            if raw_date:
                dm = re.match(r"(\d{4}-\d{2}-\d{2})", str(raw_date))
                date_listed = dm.group(1) if dm else str(raw_date)[:10]

            headline = price  # shown in Domain listings as the price/headline text

            rows.append("|".join(str(x) for x in [
                suburb, street, actual_price, beds, baths, parking, land,
                ptype, lid_str, url, headline, date_listed, ""
                # fields: 0-suburb 1-street 2-price 3-beds 4-baths 5-parking
                #         6-land 7-type 8-lid 9-url 10-headline 11-date_listed
                #         12-listing_description (empty, filled by fetch step)
            ]))
        except Exception:
            continue

    return rows, total_listings, total_pages


# ── Per-listing description fetcher ──────────────────────────────────────────

def extract_listing_desc(html: str) -> str:
    """Extract description text from an individual Domain listing page."""
    data = _extract_next_data(html)
    if not data:
        return ""
    cp   = data.get("props", {}).get("pageProps", {}).get("componentProps", {})
    rg   = cp.get("rootGraphQuery", {}) or {}
    lbv2 = rg.get("listingByIdV2", {}) or {}

    desc = lbv2.get("description") or ""
    if isinstance(desc, list):
        desc = " ".join(str(p) for p in desc if p)
    if not desc:
        raw  = cp.get("description") or ""
        desc = " ".join(str(p) for p in raw if p) if isinstance(raw, list) else str(raw)
    if not desc:
        desc = cp.get("headline") or lbv2.get("headline") or ""
    if not desc:
        return ""

    try:
        desc = desc.encode("latin-1").decode("utf-8")
    except Exception:
        pass

    desc = re.sub(r"[\r\n\t]+", " ", str(desc)).replace("|", " ").strip()
    return desc[:800] + "…" if len(desc) > 800 else desc
