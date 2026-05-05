# Property Listing Scraper

A Domain.com.au scraping and investment analysis pipeline that scores property listings against a three-pillar strategy (Growth, Deals, Cashflow) and produces Excel reports.

---

## How it works

1. **Scrape** — `domain_mcp.py` (the MCP server) fetches listing pages from Domain.com.au using `curl` with human-like request timing and cookie handling.
2. **Store** — listings are written to `raw_listings.txt` (pipe-delimited), deduplicated by listing ID.
3. **Enrich** — `fetch_descriptions` visits individual listing pages to pull full marketing text.
4. **Score** — `scoring.py` runs each listing through the three-pillar engine using suburb zoning data from `regions.py` and rent estimates from `rent_estimator.py`.
5. **Report** — `build_excel.py` writes `SEQ_Listings.xlsx` with colour-coded score columns.

---

## File overview

| File | Purpose |
|---|---|
| `domain_mcp.py` | MCP server — all tools live here |
| `scoring.py` | Three-pillar scoring engine |
| `score_listings.py` | CLI wrapper: `raw_listings.txt` → `scored_listings.json` |
| `build_excel.py` | Excel report builder: `scored_listings.json` → `SEQ_Listings.xlsx` |
| `regions.py` | Suburb zoning, rezone potential, Fast 50 sets |
| `rent_estimator.py` | Rent yield estimator by suburb / bed count |
| `suburb_stats.py` | Suburb statistics lookup |
| `run_batch.py` | Batch-scrape multiple suburbs in sequence |
| `build_suburb_list.py` | Utility to build `suburbs.txt` / `master_suburbs.json` |
| `raw_listings.txt` | Live pipe-delimited listing data (scraper output) |
| `scored_listings.json` | Scored listings (scoring engine output) |
| `SEQ_Listings.xlsx` | Final Excel report (build_excel output) |
| `SEQ_Dashboard.xlsx` | Dashboard view |
| `master_suburbs.json` | Full suburb slug list |
| `suburbs.txt` | Active suburb list for batch runs |
| `mcp_install.md` | MCP server install guide |

---

## Install

```bash
pip install fastmcp httpx openpyxl
```

`curl` must be available on the system PATH (it is on macOS/Linux by default; on Windows use WSL or install curl).

---

## MCP server setup

The pipeline runs as an MCP server inside Claude (Cowork or Claude Code). Add it to your config:

**Cowork / Claude Desktop** — `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "Domaincomau-Scraper": {
      "command": "python",
      "args": ["C:/absolute/path/to/domain_mcp.py"]
    }
  }
}
```

**Claude Code** — `.claude/settings.json` or `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "Domaincomau-Scraper": {
      "command": "python",
      "args": ["/absolute/path/to/domain_mcp.py"]
    }
  }
}
```

---

## MCP tools

### `full_pipeline` — one-call end-to-end run

```
full_pipeline(
  suburb_slug = "toowoomba-qld-4350",
  project_dir = "C:/Users/.../Property Listing Scraper",
  max_price   = 2000000,   # optional, default $2M
  max_pages   = 5          # optional, ~20 listings per page
)
```

Scrapes Domain → updates `raw_listings.txt` → scores → builds Excel. Returns a summary dict with results from each step.

---

### Individual tools

```python
# 1. Scrape a suburb
search_listings("ipswich-qld-4305", max_pages=3)

# 2. Merge rows into raw_listings.txt
append_listings(project_dir, rows, suburb="Ipswich")

# 3. Fetch full description text from individual listing pages
fetch_descriptions(project_dir, batch_size=40)

# 4. Score all listings
run_scoring(project_dir)

# 5. Build Excel report
run_excel_build(project_dir)

# 6. Debug a single listing page (diagnostic)
debug_listing_page("https://www.domain.com.au/1-cedar-street-raceview-qld-4305-2020775400")
```

---

## Suburb slug format

`lowercase-suburb-name-state-postcode`

| Location | Slug |
|---|---|
| Ipswich QLD 4305 | `ipswich-qld-4305` |
| Toowoomba QLD 4350 | `toowoomba-qld-4350` |
| Caboolture QLD 4510 | `caboolture-qld-4510` |
| Tamworth NSW 2340 | `tamworth-nsw-2340` |

---

## Adding a new suburb

Before running the pipeline on a new suburb, update `regions.py`:

1. Add the suburb to `ZONING` — include zone type, council, and any notes.
2. Add the suburb to `REZONE_POTENTIAL` — use `"HIGH"`, `"MEDIUM"`, or `"LOW"`.
3. Add to `HIGH_REZONE` or `MEDIUM_REZONE` sets if applicable.
4. Optionally add to `FAST_50` if it's a high-growth target suburb.
5. Add to `CASHFLOW_DEMAND_SUBURBS` if it has strong rental demand.

Without these entries the scoring engine will fall back to `DEFAULT_ZONE` and miss all rezone signals.

---

## Scoring — three pillars

Each listing is scored across three dimensions:

**Growth** — rezone potential, block size (400m²+), Fast 50 suburb membership, infrastructure keywords in listing text.

**Deals** — days on market, price reductions, motivated-seller keywords ("deceased estate", "mortgagee", "as-is"), auction/EOI flags.

**Cashflow** — estimated gross yield (from `rent_estimator.py`), dual-income / granny flat signals, bedroom count relative to suburb demand.

Scores are written to `scored_listings.json` and colour-coded in `SEQ_Listings.xlsx`.

---

## Data files

`raw_listings.txt` — pipe-delimited, one listing per line:

```
suburb | street | price | beds | baths | parking | land | type | listing_id | url | headline | listing_description
```

Listings are filtered on scrape: strata (e.g. `12/34 Smith St`) and new house-and-land packages are excluded automatically.

---

## Running the pipeline from the command line

```bash
# Score only (after raw_listings.txt is populated)
python score_listings.py --raw raw_listings.txt --out scored_listings.json

# Build Excel only (after scored_listings.json exists)
python build_excel.py

# Batch scrape all suburbs in suburbs.txt
python run_batch.py
```
