#!/usr/bin/env python3
"""
domain_mcp.py
─────────────
MCP server for the Domain.com.au property listing pipeline.
Uses undetected-chromedriver (real patched Chrome) to bypass Akamai bot detection.

Tools exposed:
  search_listings      – scrape Domain search results for a suburb
  append_listings      – merge rows into raw_listings.txt
  run_scoring          – run score_listings.py → scored_listings.json
  run_excel_build      – run build_excel.py → SEQ_Listings.xlsx
  full_pipeline        – chains all four steps in one call
  fetch_descriptions   – back-fill listing description text
  debug_listing_page   – dump __NEXT_DATA__ structure for a listing URL
  send_report          – email the scored listings as an HTML report
  classify_listings    – use local Ollama LLM to classify deals

Install deps:
  pip install fastmcp undetected-chromedriver ollama
  (Chrome must be installed — https://www.google.com/chrome/)

Run standalone (stdio transport):
  python domain_mcp.py
"""

import json
import re
import sys
import os
import time
import random
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

try:
    import httpx as _httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

from fastmcp import FastMCP

# ─────────────────────────────────────────────────────────────
# Data directory — all output files go here
# ─────────────────────────────────────────────────────────────
DEFAULT_DATA_DIR = r"C:\DomainListingData"

def _ddir(data_dir: str) -> Path:
    """Resolve the data directory, creating it if needed."""
    d = Path(data_dir) if data_dir else Path(DEFAULT_DATA_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─────────────────────────────────────────────────────────────
# Server
# ─────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="domain-listings",
    instructions=(
        "Tools for scraping Domain.com.au property listings, scoring them against the "
        "three-pillar investment strategy (Growth / Deals / Cashflow), and building "
        "Excel reports. Use full_pipeline() for a complete suburb scrape in one call. "
        "Use classify_listings() after scoring to get AI-powered deal analysis via Ollama."
    ),
)

# ─────────────────────────────────────────────────────────────
# Chrome session helper (undetected-chromedriver)
# ─────────────────────────────────────────────────────────────
def _detect_chrome_major_version() -> int | None:
    """Return the installed Chrome major version, or None if undetectable.
    On Windows, reads from the registry (most reliable). Falls back to
    checking common exe paths via --version flag.
    """
    # 1. Windows registry (fastest, works without launching Chrome)
    try:
        import winreg
        reg_paths = [
            (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon"),
        ]
        for hive, key_path in reg_paths:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    version, _ = winreg.QueryValueEx(key, "version")
                    return int(str(version).split(".")[0])
            except Exception:
                continue
    except ImportError:
        pass  # Not on Windows

    # 2. Fallback: launch Chrome with --version
    import subprocess, shutil
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\Glenn\AppData\Local\Google\Chrome\Application\chrome.exe",
        "google-chrome", "google-chrome-stable", "chromium-browser", "chromium",
    ]
    for exe in candidates:
        path = shutil.which(exe) or (exe if os.path.isfile(exe) else None)
        if not path:
            continue
        try:
            out = subprocess.check_output(
                [path, "--version"], timeout=5, stderr=subprocess.DEVNULL
            ).decode().strip()
            m = re.search(r"(\d+)\.\d+\.\d+", out)
            if m:
                return int(m.group(1))
        except Exception:
            continue

    return None


@contextmanager
def _uc_session():
    """
    Context manager: launches an undetected Chrome instance, warms up with a
    Domain homepage visit to acquire cookies, then yields the driver.
    Caller fetches pages with driver.get(url). Cleans up on exit.
    """
    import undetected_chromedriver as uc

    options = uc.ChromeOptions()
    options.add_argument("--lang=en-AU")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    chrome_ver = _detect_chrome_major_version()
    driver = uc.Chrome(
        headless=False,
        options=options,
        use_subprocess=True,
        **({"version_main": chrome_ver} if chrome_ver else {}),
    )
    try:
        driver.set_page_load_timeout(30)
        # Warm up: homepage visit seeds session cookies
        try:
            driver.get("https://www.domain.com.au/")
            time.sleep(1)
        except Exception:
            pass
        yield driver
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def _uc_fetch(driver, url: str, settle: float = 1.0) -> str:
    """Navigate to url, wait for page to settle, return full page HTML."""
    driver.get(url)
    time.sleep(settle + random.uniform(0, 0.3))
    return driver.page_source


# ─────────────────────────────────────────────────────────────
# Parsing helpers
# ─────────────────────────────────────────────────────────────
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

    # Guard: ids must be a list of IDs (ints or long strings).
    # If Domain changed the structure so ids is a dict or short-key iterable,
    # fall back to iterating lmap keys directly.
    if not isinstance(ids, list) or (ids and len(str(ids[0])) < 4):
        ids = list(lmap.keys())

    rows = []
    for lid in ids:
        listing = lmap.get(lid) or lmap.get(str(lid))
        if not listing:
            continue

        try:
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
                ptype   = (raw_feats.get("propertyTypeFormatted") or raw_feats.get("propertyType") or "")
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

            description = price
            actual_price = lm.get("displaySearchPriceRange") or ""
            if not actual_price or actual_price == description:
                actual_price = price

            lid_str = str(listing.get("id") or lid)
            raw_url = lm.get("url") or listing.get("listingSlug") or listing.get("seoUrl") or ""
            url     = "/" + raw_url.lstrip("/") if raw_url else ""

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
            listing_desc = re.sub(r"[\r\n\t]+", " ", str(raw_desc)).replace("|", " ").strip()
            if len(listing_desc) > 800:
                listing_desc = listing_desc[:800] + "…"

            # Strip pipe chars from free-text fields so the row stays pipe-delimited
            def _clean(v): return str(v).replace("|", " / ").strip()
            rows.append("|".join(_clean(x) for x in [
                suburb, street, actual_price, beds, baths, parking, land, ptype, lid_str, url, description, listing_desc
            ]))

        except Exception:
            continue

    return rows, total_listings, total_pages


def _polite_delay(base_seconds: float = 8.0, jitter: float = 2.0) -> None:
    delay = base_seconds + random.uniform(-jitter, jitter)
    delay = max(delay, base_seconds - jitter)
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


def _extract_listing_desc_from_html(html: str) -> str:
    """Extract the description body text from an individual Domain listing page."""
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

    cp   = data.get("props", {}).get("pageProps", {}).get("componentProps", {})
    rg   = cp.get("rootGraphQuery", {}) or {}
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
        max_pages:      Maximum pages to fetch (default 5, ~20 listings/page)
        page_delay:     Seconds to wait between page requests (default 8)
        listing_delay:  Seconds between individual listing page fetches for descriptions
                        (default 0, disabled — use fetch_descriptions() instead)

    Returns:
        {suburb_slug, total_listings, total_pages, pages_fetched,
         rows_raw, rows_kept, desc_fetched, rows, errors}
    """
    all_rows: list[str] = []
    errors:   list[str] = []
    total_listings = 0
    total_pages    = 1
    desc_fetched   = 0

    with _uc_session() as driver:
        for page_num in range(1, max_pages + 1):
            if page_num > 1:
                _polite_delay(base_seconds=page_delay)

            url = _build_url(suburb_slug, max_price, page_num)
            try:
                html = _uc_fetch(driver, url)
            except Exception as e:
                errors.append(f"Page {page_num}: {e}")
                break

            if debug and page_num == 1:
                try:
                    debug_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "debug_page.html"
                    )
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    errors.append(f"DEBUG html saved to: {debug_path}")
                except Exception as e:
                    errors.append(f"DEBUG save failed: {e}")

            rows, tl, tp = _extract_rows_from_html(html)

            if page_num == 1:
                total_listings = tl
                total_pages    = tp

            if not rows:
                break

            all_rows.extend(rows)

            if page_num >= total_pages:
                break

        kept = [r for r in all_rows if _should_keep(r)]

        if listing_delay > 0:
            for i, row in enumerate(kept):
                parts = row.split("|")
                existing_desc = parts[11].strip() if len(parts) > 11 else ""
                if existing_desc:
                    desc_fetched += 1
                    continue
                url_part = parts[9].strip() if len(parts) > 9 else ""
                if not url_part.startswith("/"):
                    continue
                time.sleep(listing_delay + random.uniform(0, 0.3))
                try:
                    listing_html = _uc_fetch(driver, f"https://www.domain.com.au{url_part}", settle=1.0)
                    desc = _extract_listing_desc_from_html(listing_html)
                    if desc:
                        while len(parts) < 12:
                            parts.append("")
                        parts[11] = desc
                        kept[i] = "|".join(parts)
                        desc_fetched += 1
                except Exception as e:
                    errors.append(f"Desc fetch failed for {url_part}: {e}")

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
    rows: list[str],
    suburb: Optional[str] = None,
    replace_suburb: bool = True,
    data_dir: str = "",
    project_dir: str = "",   # kept for backwards compat — ignored when data_dir is set
) -> dict:
    """
    Write scraped listing rows into raw_listings.txt.

    Args:
        rows:           List of pipe-delimited listing strings from search_listings()
        suburb:         If provided and replace_suburb=True, existing rows for this
                        suburb are removed before writing (clean refresh).
        replace_suburb: Whether to remove old rows for this suburb first (default True)
        data_dir:       Directory where raw_listings.txt is stored
                        (default: C:\\DomainListingData)

    Returns:
        { "raw_listings_path": str, "rows_written": int,
          "rows_removed": int, "total_rows": int }
    """
    raw_path = _ddir(data_dir or project_dir) / "raw_listings.txt"

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
def run_scoring(project_dir: str, data_dir: str = "") -> dict:
    """
    Run score_listings.py logic inline to produce scored_listings.json.

    Args:
        project_dir: Absolute path containing score_listings.py (scripts folder)
        data_dir:    Directory containing raw_listings.txt and where scored_listings.json
                     will be written (default: C:\\DomainListingData)

    Returns:
        { "success": bool, "scored_json_path": str, "rows_scored": int, "stderr": str }
    """
    import importlib.util, traceback
    dd     = _ddir(data_dir or "")
    script = Path(project_dir) / "score_listings.py"
    raw    = dd / "raw_listings.txt"
    out    = dd / "scored_listings.json"

    if not script.exists():
        return {"success": False, "error": f"score_listings.py not found in {project_dir}"}
    if not raw.exists():
        return {"success": False, "error": f"raw_listings.txt not found in {dd}"}

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
def run_excel_build(project_dir: str, data_dir: str = "") -> dict:
    """
    Run build_excel.py logic inline to produce SEQ_Listings.xlsx.

    Args:
        project_dir: Absolute path containing build_excel.py (scripts folder)
        data_dir:    Directory containing scored_listings.json and where the xlsx
                     will be written (default: C:\\DomainListingData)

    Returns:
        { "success": bool, "files": [str, ...], "stdout": str, "stderr": str }
    """
    import importlib.util, traceback
    dd     = _ddir(data_dir or "")
    script = Path(project_dir) / "build_excel.py"
    scored = dd / "scored_listings.json"

    if not script.exists():
        return {"success": False, "error": f"build_excel.py not found in {project_dir}"}
    if not scored.exists():
        return {"success": False, "error": f"scored_listings.json not found in {dd} — run run_scoring() first"}

    try:
        spec = importlib.util.spec_from_file_location("build_excel", str(script))
        mod  = importlib.util.module_from_spec(spec)
        mod.__file__ = str(script)
        sys.path.insert(0, str(project_dir))
        spec.loader.exec_module(mod)
        mod.main(scored_path=scored, out_path=dd / "SEQ_Listings.xlsx")
        sys.path.pop(0)

        out_file = dd / "SEQ_Listings.xlsx"
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
    data_dir: str = "",
) -> dict:
    """
    Run the complete Domain.com.au → Excel pipeline in one call.

    Steps:
      1. Scrape Domain.com.au for listings in the given suburb
      2. Merge rows into raw_listings.txt
      3. Run score_listings.py → scored_listings.json
      4. Run build_excel.py → SEQ_Listings.xlsx

    Args:
        suburb_slug:    e.g. "loganholme-qld-4129" or "ipswich-qld-4305"
        project_dir:    Absolute path to the folder with score_listings.py and build_excel.py
        max_price:      Upper price limit in dollars (default 2,000,000)
        max_pages:      Max Domain result pages to fetch (default 5)
        replace_suburb: Remove existing rows for this suburb before writing (default True)
        page_delay:     Seconds between page requests during scraping (default 8)
        data_dir:       Where to store data files (default: C:\\DomainListingData)
    """
    summary: dict = {"suburb_slug": suburb_slug, "steps": {}}
    suburb_name = suburb_slug.split("-")[0].title()

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

    append = append_listings(rows=scrape["rows"], suburb=suburb_name,
                             replace_suburb=replace_suburb, data_dir=data_dir)
    summary["steps"]["append"] = {
        "rows_written": append["rows_written"],
        "rows_removed": append["rows_removed"],
        "total_rows":   append["total_rows"],
    }

    score = run_scoring(project_dir, data_dir=data_dir)
    summary["steps"]["score"] = {
        "success": score["success"],
        "output":  score.get("stdout", ""),
        "errors":  score.get("stderr", "") or score.get("error", ""),
    }

    if not score["success"]:
        summary["status"]  = "failed_at_scoring"
        summary["message"] = score.get("stderr") or score.get("error", "Unknown error")
        return summary

    excel = run_excel_build(project_dir, data_dir=data_dir)
    summary["steps"]["excel"] = {
        "success": excel["success"],
        "files":   excel.get("files", []),
        "errors":  excel.get("stderr", ""),
    }

    if not excel["success"]:
        summary["status"]  = "failed_at_excel"
        summary["message"] = excel.get("error", "Excel build failed")
        return summary

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
    data_dir: str = "",
) -> dict:
    """
    Fetch listing description text for rows in raw_listings.txt that don't have one yet.
    Call repeatedly until rows_remaining == 0.

    Args:
        project_dir:    Script directory (not used for data — kept for compat)
        batch_size:     Max listings to process per call (default 40)
        listing_delay:  Seconds between individual page fetches (default 0.5)
        suburb:         If set, only process rows for this suburb
        smart_filter:   Skip clearly uninteresting listings (over median price,
                        small block, low bed count)
        data_dir:       Directory containing raw_listings.txt (default: C:\\DomainListingData)

    Returns:
        { "rows_updated": int, "rows_remaining": int, "rows_skipped": int,
          "rows_failed": int, "median_price": int, "errors": [] }
    """
    raw_path = _ddir(data_dir or "") / "raw_listings.txt"
    if not raw_path.exists():
        return {"success": False, "error": f"raw_listings.txt not found in {project_dir}"}

    lines = raw_path.read_text(encoding="utf-8").splitlines()

    rows_updated   = 0
    rows_failed    = 0
    rows_skipped   = 0
    errors: list[str] = []

    median_price = 0
    if smart_filter:
        known_prices = []
        for line in lines:
            if not line.strip():
                continue
            parts = line.split("|")
            price_s = parts[2].strip() if len(parts) > 2 else ""
            clean = price_s.replace(",", "").replace("$", "").lower()
            if any(x in clean for x in ("contact", "auction", "eoi", "expression", "guide", "call")) \
                    or ("offer" in clean and not re.search(r"\d{6,}", clean)):
                continue
            m = re.search(r"(\d{6,})", clean)
            if m:
                val = float(m.group(1))
                if val < 100:   val *= 1_000_000
                elif val < 10_000: val *= 1_000
                if 100_000 < val < 10_000_000:
                    known_prices.append(val)
        if known_prices:
            known_prices.sort()
            median_price = int(known_prices[len(known_prices) // 2])

    def _is_uninteresting(parts: list[str]) -> bool:
        if not smart_filter or median_price == 0:
            return False
        price_s = parts[2].strip() if len(parts) > 2 else ""
        clean = price_s.replace(",", "").replace("$", "").lower()
        if any(x in clean for x in ("contact", "auction", "eoi", "expression", "guide", "call", "for sale")) \
                or ("offer" in clean and not re.search(r"\d{6,}", clean)):
            return False
        pm = re.search(r"(\d{6,})", clean)
        if not pm:
            return False
        val = float(pm.group(1))
        if val < 100:   val *= 1_000_000
        elif val < 10_000: val *= 1_000
        if val <= median_price:
            return False
        land_m2 = _parse_land_m2(parts[6].strip() if len(parts) > 6 else "")
        try:
            beds = int(parts[3].strip() if len(parts) > 3 else "0")
        except ValueError:
            beds = 0
        return land_m2 > 0 and land_m2 < 500 and beds <= 3

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

    with _uc_session() as driver:
        for idx in todo_indices[:batch_size]:
            parts = lines[idx].split("|")
            url_part = parts[9].strip()
            time.sleep(listing_delay + random.uniform(0, 0.3))
            try:
                html = _uc_fetch(driver, f"https://www.domain.com.au{url_part}", settle=1.0)
                desc = _extract_listing_desc_from_html(html)
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
# Tool 7 — debug_listing_page
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def debug_listing_page(listing_url: str) -> dict:
    """
    Fetch a single Domain listing page and dump its __NEXT_DATA__ JSON structure.
    Use this to diagnose parsing issues or verify bot detection is bypassed.

    Args:
        listing_url: Full URL, e.g. "https://www.domain.com.au/1-cedar-street-raceview-qld-4305-2020775400"

    Returns:
        { "found_next_data": bool, "pageProps_keys": list, "description_candidates": dict }
    """
    with _uc_session() as driver:
        try:
            html = _uc_fetch(driver, listing_url)
        except Exception as e:
            return {"found_next_data": False, "error": str(e)}

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
        if not isinstance(d, dict) or depth > 3:
            return type(d).__name__
        return {k: _keys_summary(v, depth + 1) for k, v in list(d.items())[:30]}

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
        "found_next_data":        True,
        "pageProps_keys":         list(pp.keys()),
        "componentProps_keys":    list(cp.keys()),
        "description_candidates": candidates,
        "pp_structure":           _keys_summary(pp),
    }


# ─────────────────────────────────────────────────────────────
# Tool 8 — send_report
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def send_report(project_dir: str, suburb_filter: str = "") -> dict:
    """
    Email the scored listings as an HTML report via Gmail SMTP.

    IMPORTANT: Call EXACTLY ONCE after ALL suburbs are processed.

    Args:
        project_dir:    Absolute path to the project folder (where send_report.py lives).
        suburb_filter:  Limit report to one suburb name (e.g. "Ipswich"). Empty = all.

    Returns:
        { "success": bool, "message": str }
    """
    import importlib.util

    script = Path(project_dir) / "send_report.py"
    if not script.exists():
        return {"success": False, "message": f"send_report.py not found at {script}"}

    spec = importlib.util.spec_from_file_location("send_report", str(script))
    mod  = importlib.util.module_from_spec(spec)
    mod.__file__ = str(script)
    spec.loader.exec_module(mod)

    return mod.send_report(suburb_filter=suburb_filter or None)


# ─────────────────────────────────────────────────────────────
# Tool 9 — classify_listings (Ollama LLM)
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def classify_listings(
    project_dir: str,
    model: str = "qwen2.5:14b",
    ollama_url: str = "http://localhost:11434",
    batch_size: int = 20,
    min_score: float = 0.0,
    force_reclassify: bool = False,
    data_dir: str = "",
) -> dict:
    """
    Use a local Ollama LLM to classify scored listings and identify deals.

    Reads scored_listings.json, analyses each listing's description and metrics,
    and adds AI classification fields. Writes results to classified_listings.json.

    Requires Ollama to be running locally:
      ollama serve
      ollama pull qwen2.5:14b

    Args:
        project_dir:       Script directory (kept for compat)
        model:             Ollama model name (default: qwen2.5:14b)
        ollama_url:        Ollama API base URL (default: http://localhost:11434)
        batch_size:        Max listings to classify per call (default 20)
        min_score:         Only classify listings with total_score >= this (default 0 = all)
        force_reclassify:  Re-classify listings that already have AI classification
        data_dir:          Directory containing scored_listings.json (default: C:\\DomainListingData)

    Returns:
        { "success": bool, "classified": int, "skipped": int,
          "remaining": int, "output_path": str, "errors": [] }
    """
    import urllib.request, urllib.error

    dd          = _ddir(data_dir or "")
    scored_path = dd / "scored_listings.json"
    out_path    = dd / "classified_listings.json"

    if not scored_path.exists():
        return {"success": False, "error": "scored_listings.json not found — run run_scoring() first"}

    listings = json.loads(scored_path.read_text(encoding="utf-8"))

    # Load existing classified output if present
    existing: dict[str, dict] = {}
    if out_path.exists():
        try:
            for item in json.loads(out_path.read_text(encoding="utf-8")):
                lid = item.get("listing_id", "")
                if lid:
                    existing[lid] = item
        except Exception:
            pass

    def _ollama_classify(listing: dict) -> dict:
        """Send one listing to Ollama and return structured classification."""
        desc = listing.get("listing_description") or listing.get("description") or ""
        prompt = f"""You are an Australian property investment analyst. Analyse this residential listing and respond ONLY with a JSON object — no explanation, no markdown, just the JSON.

Listing:
- Address: {listing.get("street", "")}, {listing.get("suburb", "")}
- Price: {listing.get("price", "Unknown")}
- Beds/Baths/Parking: {listing.get("beds", "?")}/{listing.get("baths", "?")}/{listing.get("parking", "?")}
- Land: {listing.get("land", "Unknown")}
- Type: {listing.get("type", "House")}
- Investment Score: {listing.get("total_score", 0)}/100
- Description: {desc[:600] if desc else "No description available"}

Respond with exactly this JSON structure:
{{
  "deal_type": "cashflow|growth|development|flip|none",
  "deal_flags": ["short flag 1", "short flag 2"],
  "red_flags": ["concern 1"],
  "confidence": "high|medium|low",
  "ai_summary": "1-2 sentence investment take"
}}"""

        payload = json.dumps({
            "model":  model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{ollama_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        raw = result.get("response", "{}")
        # Extract JSON from response (model might wrap it in markdown)
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            classification = json.loads(json_match.group())
        else:
            classification = json.loads(raw)

        return classification

    classified_count = 0
    skipped_count    = 0
    errors: list[str] = []
    todo = []

    for listing in listings:
        lid = listing.get("listing_id", "")
        score = listing.get("total_score", 0) or 0
        if score < min_score:
            skipped_count += 1
            continue
        if not force_reclassify and lid in existing and existing[lid].get("ai_classification"):
            skipped_count += 1
            continue
        todo.append(listing)

    remaining = max(0, len(todo) - batch_size)

    for listing in todo[:batch_size]:
        lid = listing.get("listing_id", "")
        try:
            classification = _ollama_classify(listing)
            enriched = {**listing, "ai_classification": classification}
            existing[lid] = enriched
            classified_count += 1
        except Exception as e:
            errors.append(f"{listing.get('street', lid)}: {e}")
            existing[lid] = {**listing, "ai_classification": None}

    # Merge: preserve all listings, with classifications where available
    output = []
    lid_order = {l.get("listing_id"): i for i, l in enumerate(listings)}
    for lid, item in sorted(existing.items(), key=lambda x: lid_order.get(x[0], 9999)):
        output.append(item)

    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "success":      True,
        "classified":   classified_count,
        "skipped":      skipped_count,
        "remaining":    remaining,
        "output_path":  str(out_path),
        "errors":       errors[:10],
    }


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
