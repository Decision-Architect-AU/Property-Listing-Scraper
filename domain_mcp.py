#!/usr/bin/env python3
"""
domain_mcp.py
─────────────
MCP server for the Domain.com.au property listing pipeline.

Tools exposed:
  search_listings(suburb_slug, max_price, max_pages)
      → Scrapes Domain.com.au and returns pipe-delimited listing rows

  append_listings(project_dir, rows, suburb)
      → Merges rows into raw_listings.txt (deduplicates by listing ID)

  run_scoring(project_dir)
      → Runs score_listings.py, returns summary stats

  run_excel_build(project_dir)
      → Runs build_excel.py, returns output file paths

  full_pipeline(suburb_slug, project_dir, state, postcode, max_price, max_pages)
      → Chains all four steps; one call to rule them all

Install deps:
  pip install fastmcp httpx

Run standalone (stdio transport, for Claude Code / Cowork):
  python domain_mcp.py

Configure in claude_desktop_config.json or .claude/settings.json:
  {
    "mcpServers": {
      "domain-listings": {
        "command": "python",
        "args": ["/absolute/path/to/domain_mcp.py"]
      }
    }
  }
"""

import json
import re
import subprocess
import sys
import os
import time
import random
from pathlib import Path
from typing import Optional

import httpx
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
from fastmcp import FastMCP

# ─────────────────────────────────────────────────────────────
# Server
# ─────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="domain-listings",
    instructions=(
        "Tools for scraping Domain.com.au property listings, scoring them against the "
        "three-pillar investment strategy (Growth / Deals / Cashflow), and building "
        "Excel reports. Use full_pipeline() for a complete suburb scrape in one call."
    ),
)

# ─────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────
DOMAIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-AU,en-GB;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Referer": "https://www.google.com/",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


def _parse_land_m2(land_str: str) -> float:
    """Convert land string like '600m²', '1.2ha', '4000sqm' to m²."""
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


def _build_url(suburb_slug: str, max_price: int, page: int) -> str:
    base = (
        f"https://www.domain.com.au/sale/{suburb_slug}/"
        f"?excludeunderoffer=1"
        f"&property-type=house"
        f"&price=0-{max_price}"
    )
    return base if page == 1 else f"{base}&page={page}"


def _extract_rows_from_html(html: str) -> tuple[list[str], int, int]:
    """
    Parse __NEXT_DATA__ from a Domain search page.
    Returns (rows, total_listings, total_pages).
    rows is a list of pipe-delimited strings.
    """
    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
        html,
        re.DOTALL,
    )
    if not m:
        return [], 0, 0

    data = json.loads(m.group(1))
    comp = (
        data.get("props", {})
        .get("pageProps", {})
        .get("componentProps", {})
    )

    lmap = comp.get("listingsMap", {})
    ids  = comp.get("listingSearchResultIds", [])
    total_listings = comp.get("totalListings", 0)
    total_pages    = comp.get("totalPages", 1)

    rows = []
    for lid in ids:
        # Domain sometimes uses int keys, sometimes string keys
        listing = lmap.get(lid) or lmap.get(str(lid))
        if not listing:
            continue

        try:
            # New structure: data lives inside listingModel
            lm = listing.get("listingModel") or {}
            if not isinstance(lm, dict):
                lm = {}

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

            raw_feats = lm.get("features") or listing.get("features") or listing.get("propertyFeatures") or {}

            beds = baths = parking = land = ""
            ptype = ""
            if isinstance(raw_feats, dict):
                beds    = raw_feats.get("beds",    raw_feats.get("bedroomsCount",    raw_feats.get("bedrooms",    "")))
                baths   = raw_feats.get("baths",   raw_feats.get("bathroomsCount",   raw_feats.get("bathrooms",   "")))
                parking = raw_feats.get("parking", raw_feats.get("parkingSpacesCount", raw_feats.get("parkingSpaces", "")))
                # Property type from features (House, Townhouse, Unit etc.)
                ptype   = (raw_feats.get("propertyTypeFormatted") or raw_feats.get("propertyType") or "")
                land_val = raw_feats.get("landSize") or raw_feats.get("land")
                if land_val:
                    raw_unit = str(raw_feats.get("landUnit") or raw_feats.get("landSizeUnit") or "m²")
                    # Fix double-encoded UTF-8 (e.g. "mÂ²" → "m²")
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

            # Fallback property type from listing metadata
            if not ptype:
                ptype = listing.get("listingType") or lm.get("listingType") or ""

            # description = marketing headline from price field; actual price from displaySearchPriceRange
            description = price  # the "price" text is often the headline
            actual_price = lm.get("displaySearchPriceRange") or ""
            # If displaySearchPriceRange looks empty or same as description, keep price as-is
            if not actual_price or actual_price == description:
                actual_price = price

            lid_str = str(listing.get("id") or lid)
            raw_url = lm.get("url") or listing.get("listingSlug") or listing.get("seoUrl") or ""
            url     = "/" + raw_url.lstrip("/") if raw_url else ""

            # Extract the actual property description text
            # Domain search results expose the marketing headline in lm["headline"];
            # full body text (lm["description"]) is usually only on the listing page.
            raw_desc = (
                lm.get("description")
                or listing.get("description")
                or lm.get("propertyDescription")
                or listing.get("propertyDescription")
                or lm.get("headline")
                or listing.get("headline")
                or lm.get("name")
                or listing.get("name")
                or ""
            )
            # Sanitise: flatten whitespace, strip pipe chars (they're our delimiter)
            listing_desc = re.sub(r"[\r\n\t]+", " ", str(raw_desc)).replace("|", " ").strip()
            if len(listing_desc) > 800:
                listing_desc = listing_desc[:800] + "…"

            # Format: suburb|street|price|beds|baths|parking|land|ptype|lid|url|headline|listing_description
            rows.append("|".join(str(x) for x in [
                suburb, street, actual_price, beds, baths, parking, land, ptype, lid_str, url, description, listing_desc
            ]))

        except Exception:
            # Skip malformed listings silently
            continue

    return rows, total_listings, total_pages


def _polite_delay(base_seconds: float = 8.0, jitter: float = 2.0) -> None:
    """
    Sleep for base_seconds ± jitter before the next request.
    The randomness makes the timing look less robotic to the server.
    """
    delay = base_seconds + random.uniform(-jitter, jitter)
    delay = max(delay, base_seconds - jitter)  # never go below floor
    time.sleep(delay)


def _is_strata(address: str) -> bool:
    return bool(re.match(r"^\d+/\d+", address.strip()))


def _should_keep(row: str) -> bool:
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


# ─────────────────────────────────────────────────────────────
# Tool 1 — search_listings
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def search_listings(
    suburb_slug: str,
    max_price: int = 2_000_000,
    max_pages: int = 5,
    page_delay: float = 8.0,
    listing_delay: float = 0,
    debug: bool = False,
) -> dict:
    """
    Scrape Domain.com.au for house listings in a given suburb.

    Args:
        suburb_slug:    Domain suburb slug, e.g. "tamworth-nsw-2340" or "ipswich-qld-4305".
                        Format is: lowercase-suburb-name-state-postcode
        max_price:      Upper price limit in dollars (default 2,000,000)
        max_pages:      Maximum pages to fetch (default 5, Domain shows ~20 per page)
        page_delay:     Seconds to wait between page requests (default 8). A small
                        random jitter of ±2s is added so the timing looks natural.
        listing_delay:  Seconds to wait between individual listing page fetches when
                        retrieving description text (default 0, disabled). Use
                        fetch_descriptions() tool to populate descriptions separately.

    Returns:
        {
          "suburb_slug": str,
          "total_listings": int,
          "total_pages": int,
          "pages_fetched": int,
          "rows_raw": int,        # before filtering
          "rows_kept": int,       # after filtering H&L / strata
          "desc_fetched": int,    # how many listing descriptions were retrieved
          "rows": ["suburb|address|price|...", ...],
          "errors": [str, ...]
        }
    """
    all_rows: list[str] = []
    errors:   list[str] = []
    total_listings = 0
    total_pages    = 1

    # Use a temp cookie jar file so curl persists cookies across requests
    import tempfile
    cookie_file = tempfile.mktemp(suffix=".txt")

    def _curl_get(url: str, timeout: int = 30) -> str:
        """Fetch a URL using system curl (bypasses Python TLS fingerprinting)."""
        cmd = [
            "curl", "-s", "-L",
            "--max-time", str(timeout),
            "--compressed",
            "--cookie", cookie_file,
            "--cookie-jar", cookie_file,
            "-H", f"User-Agent: {DOMAIN_HEADERS['User-Agent']}",
            "-H", f"Accept: {DOMAIN_HEADERS['Accept']}",
            "-H", f"Accept-Language: {DOMAIN_HEADERS['Accept-Language']}",
            "-H", "Cache-Control: max-age=0",
            "-H", "Sec-Fetch-Dest: document",
            "-H", "Sec-Fetch-Mode: navigate",
            "-H", "Sec-Fetch-Site: none",
            "-H", "Sec-Fetch-User: ?1",
            "-H", "Upgrade-Insecure-Requests: 1",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode != 0:
            raise RuntimeError(f"curl exited {result.returncode}: {result.stderr.strip()}")
        return result.stdout

    def _extract_listing_desc(listing_html: str) -> str:
        """
        Pull the description body text from an individual listing page's __NEXT_DATA__.
        Confirmed paths from Domain's listing page JSON (2025).
        """
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
            listing_html, re.DOTALL,
        )
        if not m:
            return ""
        try:
            data = json.loads(m.group(1))
        except Exception:
            return ""

        cp = data.get("props", {}).get("pageProps", {}).get("componentProps", {})

        # Primary: full description text via GraphQL data
        rg = cp.get("rootGraphQuery", {}) or {}
        lbv2 = rg.get("listingByIdV2", {}) or {}
        desc = lbv2.get("description") or ""

        # description may be a list of paragraphs — join them
        if isinstance(desc, list):
            desc = " ".join(str(p) for p in desc if p)

        # Fallback: componentProps.description (also sometimes a list)
        if not desc:
            raw = cp.get("description") or ""
            if isinstance(raw, list):
                desc = " ".join(str(p) for p in raw if p)
            else:
                desc = str(raw)

        # Last resort: marketing headline
        if not desc:
            desc = cp.get("headline") or lbv2.get("headline") or ""

        if not desc:
            return ""

        # Fix double-encoded UTF-8 (e.g. "mÂ²" → "m²")
        try:
            desc = desc.encode("latin-1").decode("utf-8")
        except Exception:
            pass

        # Sanitise: flatten whitespace, strip pipe chars (our delimiter)
        desc = re.sub(r"[\r\n\t]+", " ", str(desc)).replace("|", " ").strip()
        if len(desc) > 800:
            desc = desc[:800] + "…"
        return desc

    try:
        # Warm up: visit homepage first to collect cookies
        try:
            _curl_get("https://www.domain.com.au/", timeout=15)
            time.sleep(random.uniform(2, 4))
        except Exception:
            pass  # non-fatal

        for page in range(1, max_pages + 1):

            # Polite delay before every request except the very first
            if page > 1:
                _polite_delay(base_seconds=page_delay)

            url = _build_url(suburb_slug, max_price, page)
            try:
                html = _curl_get(url)
            except Exception as e:
                errors.append(f"Page {page}: HTTP error — {e}")
                break

            # Debug: dump first listing's JSON structure
            if debug and page == 1:
                try:
                    debug_html = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_page.html")
                    with open(debug_html, "w", encoding="utf-8") as _f:
                        _f.write(html)
                    errors.append(f"DEBUG html saved to: {debug_html}")
                except Exception as _e:
                    errors.append(f"DEBUG html save failed: {_e}")

            rows, tl, tp = _extract_rows_from_html(html)

            if page == 1:
                total_listings = tl
                total_pages    = tp

            if not rows:
                break

            all_rows.extend(rows)

            if page >= total_pages:
                break

        # ── Per-listing description fetch ────────────────────────
        kept = [r for r in all_rows if _should_keep(r)]
        desc_fetched = 0

        if listing_delay > 0:
            for i, row in enumerate(kept):
                parts = row.split("|")
                # Only fetch if description slot is empty
                existing_desc = parts[11].strip() if len(parts) > 11 else ""
                if existing_desc:
                    desc_fetched += 1
                    continue

                url_part = parts[9].strip() if len(parts) > 9 else ""
                if not url_part or not url_part.startswith("/"):
                    continue

                time.sleep(listing_delay + random.uniform(0, 0.3))

                try:
                    listing_html = _curl_get(f"https://www.domain.com.au{url_part}", timeout=20)
                    desc = _extract_listing_desc(listing_html)
                    if desc:
                        # Pad to 12 fields if needed and set field[11]
                        while len(parts) < 12:
                            parts.append("")
                        parts[11] = desc
                        kept[i] = "|".join(parts)
                        desc_fetched += 1
                except Exception as e:
                    errors.append(f"Desc fetch failed for {url_part}: {e}")

    finally:
        # Clean up temp cookie file
        try:
            os.unlink(cookie_file)
        except Exception:
            pass

    return {
        "suburb_slug":    suburb_slug,
        "total_listings": total_listings,
        "total_pages":    total_pages,
        "pages_fetched":  min(max_pages, total_pages),
        "rows_raw":       len(all_rows),
        "rows_kept":      len(kept),
        "desc_fetched":   desc_fetched,
        "rows":           kept,
        "errors":         errors,
    }


# ─────────────────────────────────────────────────────────────
# Tool 2 — append_listings
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def append_listings(
    project_dir: str,
    rows: list[str],
    suburb: Optional[str] = None,
    replace_suburb: bool = True,
) -> dict:
    """
    Write scraped listing rows into raw_listings.txt.

    Args:
        project_dir:    Absolute path to the directory containing raw_listings.txt,
                        score_listings.py, and build_excel.py
        rows:           List of pipe-delimited listing strings from search_listings()
        suburb:         If provided and replace_suburb=True, all existing rows for this
                        suburb are removed before writing (for a clean refresh).
                        If None, rows are simply appended.
        replace_suburb: Whether to remove old rows for this suburb first (default True)

    Returns:
        { "raw_listings_path": str, "rows_written": int,
          "rows_removed": int, "total_rows": int }
    """
    raw_path = Path(project_dir) / "raw_listings.txt"

    existing: list[str] = []
    if raw_path.exists():
        existing = raw_path.read_text(encoding="utf-8").splitlines()

    removed = 0
    if suburb and replace_suburb:
        suburb_lower = suburb.lower()
        before = len(existing)
        existing = [
            line for line in existing
            if line and line.split("|")[0].strip().lower() != suburb_lower
        ]
        removed = before - len(existing)

    # Deduplicate by listing ID (field index 8)
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
    raw_path.write_text("\n".join(line for line in final if line) + "\n", encoding="utf-8")

    return {
        "raw_listings_path": str(raw_path),
        "rows_written":      len(new_rows),
        "rows_removed":      removed,
        "total_rows":        len([l for l in final if l]),
    }


# ─────────────────────────────────────────────────────────────
# Tool 3 — run_scoring
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def run_scoring(project_dir: str) -> dict:
    """
    Run score_listings.py logic inline to produce scored_listings.json.

    Args:
        project_dir: Absolute path containing score_listings.py and raw_listings.txt

    Returns:
        { "success": bool, "scored_json_path": str, "rows_scored": int, "stderr": str }
    """
    import importlib.util, traceback
    script = Path(project_dir) / "score_listings.py"
    raw    = Path(project_dir) / "raw_listings.txt"
    out    = Path(project_dir) / "scored_listings.json"

    if not script.exists():
        return {"success": False, "error": f"score_listings.py not found in {project_dir}"}
    if not raw.exists():
        return {"success": False, "error": f"raw_listings.txt not found in {project_dir}"}

    try:
        spec   = importlib.util.spec_from_file_location("score_listings", str(script))
        mod    = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        lines  = [l.strip() for l in raw.read_text(encoding="utf-8").splitlines() if l.strip()]
        scored = []
        for line in lines:
            parts = line.split("|")
            if len(parts) < 9 or not parts[0].strip():
                continue
            row = {
                "suburb":               parts[0].strip(),
                "street":               parts[1].strip(),
                "price":                parts[2].strip(),
                "beds":                 parts[3].strip(),
                "baths":                parts[4].strip(),
                "parking":              parts[5].strip(),
                "land":                 parts[6].strip(),
                "type":                 parts[7].strip(),
                "listing_id":           parts[8].strip(),
                "url":                  parts[9].strip() if len(parts) > 9 else "",
                "description":          parts[10].strip() if len(parts) > 10 else "",
                "listing_description":  parts[11].strip() if len(parts) > 11 else "",
            }
            scored.append(mod.score_listing(row))

        out.write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "success":          True,
            "scored_json_path": str(out),
            "rows_scored":      len(scored),
            "stdout":           f"Scored {len(scored)} listings → {out}",
            "stderr":           "",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc(), "stdout": "", "stderr": ""}


# ─────────────────────────────────────────────────────────────
# Tool 4 — run_excel_build
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def run_excel_build(project_dir: str) -> dict:
    """
    Run build_excel.py logic inline to produce SEQ_Listings.xlsx.

    Args:
        project_dir: Absolute path containing build_excel.py and scored_listings.json

    Returns:
        { "success": bool, "files": [str, ...], "stdout": str, "stderr": str }
    """
    import importlib.util, traceback
    script = Path(project_dir) / "build_excel.py"
    scored = Path(project_dir) / "scored_listings.json"

    if not script.exists():
        return {"success": False, "error": f"build_excel.py not found in {project_dir}"}
    if not scored.exists():
        return {"success": False, "error": f"scored_listings.json not found — run run_scoring() first"}

    try:
        spec = importlib.util.spec_from_file_location("build_excel", str(script))
        mod  = importlib.util.module_from_spec(spec)
        # Make project_dir available as the script's __file__ so Path(__file__).parent works
        mod.__file__ = str(script)
        sys.path.insert(0, str(project_dir))
        spec.loader.exec_module(mod)
        mod.main()
        sys.path.pop(0)

        out_file = Path(project_dir) / "SEQ_Listings.xlsx"
        files = [str(out_file)] if out_file.exists() else []
        return {
            "success": True,
            "files":   files,
            "stdout":  f"Saved listings: {out_file}",
            "stderr":  "",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc(), "stdout": "", "stderr": ""}


# ─────────────────────────────────────────────────────────────
# Tool 5 — full_pipeline
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def full_pipeline(
    suburb_slug: str,
    project_dir: str,
    max_price: int = 2_000_000,
    max_pages: int = 5,
    replace_suburb: bool = True,
    page_delay: float = 8.0,
) -> dict:
    """
    Run the complete Domain.com.au → Excel pipeline in one call.

    Steps:
      1. Scrape Domain.com.au for listings in the given suburb
      2. Merge rows into raw_listings.txt (replacing old rows for this suburb)
      3. Run score_listings.py → scored_listings.json
      4. Run build_excel.py → SEQ_Listings.xlsx + SEQ_Dashboard.xlsx

    Args:
        suburb_slug:    e.g. "toowoomba-qld-4350" or "tamworth-nsw-2340"
        project_dir:    Absolute path to the folder with score_listings.py and build_excel.py
        max_price:      Upper price limit in dollars (default 2,000,000)
        max_pages:      Max Domain result pages to fetch (default 5)
        replace_suburb: Remove existing rows for this suburb before writing (default True)
        page_delay:     Seconds between page requests during scraping (default 8)

    Returns a summary dict with results from each step.

    Note: If a new suburb is added, you must first update the ZONING and
    REZONE_POTENTIAL dicts in score_listings.py — otherwise scoring will
    use DEFAULT_ZONE and won't have rezone potential data.
    """
    summary: dict = {"suburb_slug": suburb_slug, "steps": {}}

    # Derive suburb name from slug for replace logic (e.g. "tamworth-nsw-2340" → "Tamworth")
    suburb_name = suburb_slug.split("-")[0].title()

    # Step 1: scrape
    scrape = search_listings(suburb_slug, max_price, max_pages, page_delay)
    summary["steps"]["scrape"] = {
        "rows_kept":      scrape["rows_kept"],
        "total_listings": scrape["total_listings"],
        "pages_fetched":  scrape["pages_fetched"],
        "errors":         scrape["errors"],
    }

    if not scrape["rows"]:
        summary["status"]  = "failed"
        summary["message"] = f"No listings found for {suburb_slug}. Check the slug format."
        return summary

    # Step 2: append
    append = append_listings(
        project_dir,
        scrape["rows"],
        suburb=suburb_name,
        replace_suburb=replace_suburb,
    )
    summary["steps"]["append"] = {
        "rows_written": append["rows_written"],
        "rows_removed": append["rows_removed"],
        "total_rows":   append["total_rows"],
    }

    # Step 3: score
    score = run_scoring(project_dir)
    summary["steps"]["score"] = {
        "success": score["success"],
        "output":  score.get("stdout", ""),
        "errors":  score.get("stderr", "") or score.get("error", ""),
    }

    if not score["success"]:
        summary["status"]  = "failed_at_scoring"
        summary["message"] = score.get("stderr") or score.get("error", "Unknown error")
        return summary

    # Step 4: build Excel
    excel = run_excel_build(project_dir)
    summary["steps"]["excel"] = {
        "success": excel["success"],
        "files":   excel.get("files", []),
        "errors":  excel.get("stderr", ""),
    }

    if not excel["success"]:
        summary["status"]  = "failed_at_excel"
        summary["message"] = excel.get("error", "Excel build failed")
        return summary

    # Step 5: email report (optional — skipped if email_config.json is absent)
    email_result = {"success": False, "message": "email_config.json not found — skipping email"}
    try:
        import importlib.util
        send_script = Path(project_dir) / "send_report.py"
        if send_script.exists() and (Path(project_dir) / "email_config.json").exists():
            spec = importlib.util.spec_from_file_location("send_report", str(send_script))
            mod  = importlib.util.module_from_spec(spec)
            mod.__file__ = str(send_script)
            spec.loader.exec_module(mod)
            email_result = mod.send_report(suburb_filter=suburb_name)
    except Exception as e:
        email_result = {"success": False, "message": f"Email step error: {e}"}

    summary["steps"]["email"] = email_result
    summary["status"]         = "success"
    summary["output_files"]   = excel.get("files", [])
    summary["message"]        = (
        f"Pipeline complete — {append['total_rows']} total listings, "
        f"{scrape['rows_kept']} new from {suburb_slug}. "
        f"Email: {email_result['message']}"
    )
    return summary


# ─────────────────────────────────────────────────────────────
# Tool 6 — fetch_descriptions
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def fetch_descriptions(
    project_dir: str,
    batch_size: int = 40,
    listing_delay: float = 0.5,
    suburb: Optional[str] = None,
    smart_filter: bool = True,
) -> dict:
    """
    Fetch listing description text for rows in raw_listings.txt that don't have one yet.
    Reads field[11] — if empty, fetches the individual Domain listing page and extracts
    the description. Writes results back to raw_listings.txt in-place.

    Run this after search_listings / append_listings to populate the description column.
    Call repeatedly until rows_remaining == 0.

    Args:
        project_dir:    Path containing raw_listings.txt
        batch_size:     Max listings to process per call (default 40, ~25s at 0.5s delay)
        listing_delay:  Seconds between individual page fetches (default 0.5)
        suburb:         If set, only process rows for this suburb
        smart_filter:   If True (default), skip description fetch for listings that are
                        clearly uninteresting: price > dataset median AND land < 500m²
                        AND beds <= 3. Unknown prices (Contact Agent, EOI, Auction) are
                        always fetched regardless.

    Returns:
        { "rows_updated": int, "rows_remaining": int, "rows_skipped": int,
          "rows_failed": int, "median_price": int, "errors": [] }
    """
    import tempfile

    raw_path = Path(project_dir) / "raw_listings.txt"
    if not raw_path.exists():
        return {"success": False, "error": f"raw_listings.txt not found in {project_dir}"}

    lines = raw_path.read_text(encoding="utf-8").splitlines()
    cookie_file = tempfile.mktemp(suffix=".txt")

    def _curl_get(url: str, timeout: int = 20) -> str:
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

    def _extract_desc(html: str) -> str:
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
            html, re.DOTALL,
        )
        if not m:
            return ""
        try:
            data = json.loads(m.group(1))
        except Exception:
            return ""
        cp = data.get("props", {}).get("pageProps", {}).get("componentProps", {})
        rg = cp.get("rootGraphQuery", {}) or {}
        lbv2 = rg.get("listingByIdV2", {}) or {}
        desc = lbv2.get("description") or ""
        if isinstance(desc, list):
            desc = " ".join(str(p) for p in desc if p)
        if not desc:
            raw = cp.get("description") or ""
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

    rows_updated   = 0
    rows_failed    = 0
    rows_skipped   = 0
    rows_remaining = 0
    errors: list[str] = []

    # ── Compute median price for smart filtering ──────────────
    median_price = 0
    if smart_filter:
        known_prices = []
        for line in lines:
            if not line.strip():
                continue
            parts = line.split("|")
            price_s = parts[2].strip() if len(parts) > 2 else ""
            # Strip common prefixes and take the first number
            clean = price_s.replace(",", "").replace("$", "").lower()
            # Skip unknown-price strings
            if any(x in clean for x in ("contact", "auction", "eoi", "expression", "guide", "call")) \
                    or ("offer" in clean and not re.search(r"\d{6,}", clean)):
                continue
            m = re.search(r"(\d{6,})", clean)
            if m:
                val = float(m.group(1))
                # Normalise shorthand: "$1.2m" → 1200000
                if val < 100:
                    val *= 1_000_000
                elif val < 10_000:
                    val *= 1_000
                if 100_000 < val < 10_000_000:
                    known_prices.append(val)
        if known_prices:
            known_prices.sort()
            mid = len(known_prices) // 2
            median_price = int(known_prices[mid])

    def _is_uninteresting(parts: list[str]) -> bool:
        """Return True if this listing is a clear owner-occ / overpriced skip."""
        if not smart_filter or median_price == 0:
            return False
        price_s = parts[2].strip() if len(parts) > 2 else ""
        # Unknown price → always interesting (might be a deal or have dual income)
        clean = price_s.replace(",", "").replace("$", "").lower()
        if any(x in clean for x in ("contact", "auction", "eoi", "expression", "guide", "call", "for sale")) \
                or ("offer" in clean and not re.search(r"\d{6,}", clean)):
            return False
        # Parse price
        pm = re.search(r"(\d{6,})", clean)
        if not pm:
            return False
        val = float(pm.group(1))
        if val < 100:
            val *= 1_000_000
        elif val < 10_000:
            val *= 1_000
        if val <= median_price:
            return False  # At or below median → keep
        # Over median — check land and beds
        land_s = parts[6].strip() if len(parts) > 6 else ""
        beds_s = parts[3].strip() if len(parts) > 3 else ""
        land_m2 = _parse_land_m2(land_s)
        try:
            beds = int(beds_s)
        except ValueError:
            beds = 0
        # Skip only if: over-median price AND small block AND average bed count
        return land_m2 > 0 and land_m2 < 500 and beds <= 3

    # ── Find rows that need descriptions ──────────────────────
    todo_indices = []
    suburb_lower = suburb.lower() if suburb else None
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) < 10:
            continue
        if suburb_lower and parts[0].strip().lower() != suburb_lower:
            continue
        existing = parts[11].strip() if len(parts) > 11 else ""
        url_part = parts[9].strip() if len(parts) > 9 else ""
        if existing or not url_part.startswith("/"):
            continue
        if _is_uninteresting(parts):
            rows_skipped += 1
            continue
        todo_indices.append(idx)

    rows_remaining = max(0, len(todo_indices) - batch_size)

    try:
        # Warm up cookies
        _curl_get("https://www.domain.com.au/", timeout=10)
        time.sleep(1)

        for idx in todo_indices[:batch_size]:
            parts = lines[idx].split("|")
            url_part = parts[9].strip()
            time.sleep(listing_delay + random.uniform(0, 0.3))
            try:
                html = _curl_get(f"https://www.domain.com.au{url_part}")
                desc = _extract_desc(html)
                while len(parts) < 12:
                    parts.append("")
                parts[11] = desc
                lines[idx] = "|".join(parts)
                if desc:
                    rows_updated += 1
                else:
                    rows_failed += 1
            except Exception as e:
                rows_failed += 1
                errors.append(f"{url_part}: {e}")
    finally:
        try:
            os.unlink(cookie_file)
        except Exception:
            pass

    raw_path.write_text("\n".join(l for l in lines if l) + "\n", encoding="utf-8")

    return {
        "rows_updated":   rows_updated,
        "rows_remaining": rows_remaining,
        "rows_skipped":   rows_skipped,
        "rows_failed":    rows_failed,
        "median_price":   median_price,
        "errors":         errors[:10],
    }


# ─────────────────────────────────────────────────────────────
# Tool 7 — debug_listing_page (diagnostic only)
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def debug_listing_page(listing_url: str) -> dict:
    """
    Fetch a single Domain listing page and dump its __NEXT_DATA__ JSON structure.
    Use this to find the correct JSON path for description text.

    Args:
        listing_url: Full URL, e.g. "https://www.domain.com.au/1-cedar-street-raceview-qld-4305-2020775400"

    Returns:
        { "found_next_data": bool, "props_path_keys": dict, "description_candidates": dict }
    """
    import tempfile, subprocess as _sp

    cookie_file = tempfile.mktemp(suffix=".txt")

    def _curl(url: str) -> str:
        cmd = [
            "curl", "-s", "-L", "--max-time", "20", "--compressed",
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
        r = _sp.run(cmd, capture_output=True, text=True, timeout=25)
        return r.stdout

    try:
        # Warm cookies
        _curl("https://www.domain.com.au/")
        time.sleep(2)

        html = _curl(listing_url)

        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
            html, re.DOTALL,
        )
        if not m:
            return {"found_next_data": False, "html_length": len(html), "html_snippet": html[:500]}

        data = json.loads(m.group(1))
        pp = data.get("props", {}).get("pageProps", {})
        cp = pp.get("componentProps", {})

        def _keys_summary(d, depth=0):
            """Recursively summarise dict keys up to depth 3."""
            if not isinstance(d, dict) or depth > 3:
                return type(d).__name__
            return {k: _keys_summary(v, depth + 1) for k, v in list(d.items())[:30]}

        # Hunt for anything called 'description' anywhere in pageProps
        candidates = {}
        def _hunt(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    full = f"{path}.{k}" if path else k
                    if "description" in k.lower() or "headline" in k.lower():
                        candidates[full] = str(v)[:200] if not isinstance(v, (dict, list)) else f"[{type(v).__name__}]"
                    _hunt(v, full)
            elif isinstance(obj, list):
                for i, v in enumerate(obj[:3]):
                    _hunt(v, f"{path}[{i}]")

        _hunt(pp)

        return {
            "found_next_data": True,
            "pageProps_keys": list(pp.keys()),
            "componentProps_keys": list(cp.keys()),
            "description_candidates": candidates,
            "pp_structure": _keys_summary(pp),
        }
    finally:
        try:
            os.unlink(cookie_file)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# Tool 8 — send_email_report
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def send_email_report(
    project_dir: str,
    suburb: Optional[str] = None,
) -> dict:
    """
    Send the scored listings report to the email address configured in email_config.json.
    Attaches SEQ_Listings.xlsx and includes a colour-coded HTML summary table.

    Args:
        project_dir: Absolute path containing scored_listings.json, SEQ_Listings.xlsx,
                     send_report.py, and email_config.json
        suburb:      Optional suburb name to filter the report (e.g. "Bendigo").
                     If omitted, all suburbs are included.

    Returns:
        { "success": bool, "message": str }
    """
    import importlib.util, traceback
    send_script = Path(project_dir) / "send_report.py"
    if not send_script.exists():
        return {"success": False, "message": f"send_report.py not found in {project_dir}"}

    try:
        spec = importlib.util.spec_from_file_location("send_report", str(send_script))
        mod  = importlib.util.module_from_spec(spec)
        mod.__file__ = str(send_script)
        spec.loader.exec_module(mod)
        return mod.send_report(suburb_filter=suburb)
    except Exception as e:
        return {"success": False, "message": f"Error: {e}", "traceback": traceback.format_exc()}


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
