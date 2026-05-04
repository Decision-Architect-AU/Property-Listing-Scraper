# Property Listing Scraper

A Domain.com.au scraping and investment analysis pipeline that scores property listings against a three-pillar strategy (Growth, Deals, Cashflow) and produces Excel reports and email summaries.

---

## How it works

1. **Scrape** — `domain_mcp.py` (the MCP server) fetches listing pages from Domain.com.au using `curl` with human-like request timing and cookie handling.
2. **Store** — listings are written to `raw_listings.txt` (pipe-delimited), deduplicated by listing ID.
3. **Enrich** — `fetch_descriptions` visits individual listing pages to pull full marketing text.
4. **Score** — `Strategy_Scoring/scoring.py` runs each listing through the three-pillar engine using suburb zoning data from `Domain_Info/regions.py` and rent estimates from `Strategy_Scoring/rent_estimator.py`.
5. **Report** — `build_excel.py` writes `SEQ_Listings.xlsx` with colour-coded score columns; `send_report.py` emails a single HTML summary.

---

## Project structure

```
Property Listing Scraper/
│
├── domain_mcp.py          MCP server — all pipeline tools
├── run_batch.py           Batch-scrape multiple suburbs in sequence
├── scraper.py             Low-level Domain.com.au HTTP + HTML parsing
├── listing_tracker.py     Tracks listing history across runs
├── build_excel.py         Excel report builder (scored_listings.json → SEQ_Listings.xlsx)
├── send_report.py         Sends single HTML email report via Gmail SMTP
├── email_config.json      Gmail credentials (not committed to git)
│
├── Domain_Info/           Suburb reference data and builders
│   ├── build_suburb_list.py   Builds Ref_Suburbs.json and suburbs.txt from stats file
│   ├── regions.py             Suburb zoning, rezone potential, Fast 50 membership
│   ├── suburb_stats.py        SQM Research stats lookup (vacancy, yield, median price)
│   ├── suburbs.txt            Active suburb slug list for batch runs
│   ├── Ref_Suburbs.json       Full enriched suburb record for every suburb in the stats file
│   ├── SA3_2021_AUST.xlsx     ABS SA3 reference data
│   └── suburbs_stats_extracted.xlsx   SQM Research extracted stats
│
├── Strategy_Scoring/      Scoring strategy and logic
│   ├── scoring.py             Three-pillar scoring engine (edit here to tune scores)
│   ├── score_listings.py      CLI: raw_listings.txt → scored_listings.json
│   └── rent_estimator.py      Gross yield estimator by suburb / bed count
│
└── C:\DomainListingData\  Central data store (data files only — no scripts)
    ├── raw_listings.txt       Live pipe-delimited listing data (scraper output)
    ├── scored_listings.json   Scored listings (scoring engine output)
    ├── SEQ_Listings.xlsx      Latest Excel report
    └── email_log.json         Log of sent email reports
```

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
      "args": ["C:/Users/.../Property Listing Scraper/domain_mcp.py"]
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
  suburb_slug   = "toowoomba-qld",
  project_dir   = "C:/Users/.../Property Listing Scraper",
  max_price     = 800000,   # optional, default $2M
  max_pages     = 3,        # optional, ~20 listings per page
  replace_suburb = true     # replace this suburb's existing listings
)
```

Scrapes Domain → updates `raw_listings.txt` → scores → builds Excel. Does **not** send email — call `send_report.py` separately after all suburbs are done.

---

### Individual tools

```python
# 1. Scrape a suburb
search_listings("ipswich-qld", max_pages=3)

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

## Scheduled task — Fast 50 weekly run

A scheduled task (`weekly-property-scrape`) runs every Tuesday night. It:

1. Calls `full_pipeline` for each of the 50 Fast 50 suburbs, one at a time.
2. After all 50 are complete, calls `send_report.py` **once** to send a single HTML email summary.

No email is sent between suburbs — only one consolidated report at the end.

---

## Suburb slug format

`lowercase-suburb-name-state`

| Location | Slug |
|---|---|
| Ipswich QLD | `ipswich-qld` |
| Toowoomba QLD | `toowoomba-qld` |
| Caboolture QLD | `caboolture-qld` |
| Tamworth NSW | `tamworth-nsw` |

---

## Adding a new suburb

Before running the pipeline on a new suburb, update `Domain_Info/regions.py`:

1. Add the suburb to `ZONING` — include zone type, council, and any notes.
2. Add the suburb to `REZONE_POTENTIAL` — use `"HIGH"`, `"MEDIUM"`, or `"LOW"`.
3. Add to `HIGH_REZONE` or `MEDIUM_REZONE` sets if applicable.
4. Optionally add to `FAST_50` if it's a high-growth target suburb.
5. Add to `CASHFLOW_DEMAND_SUBURBS` if it has strong rental demand.

Without these entries the scoring engine will fall back to `DEFAULT_ZONE` and miss all rezone signals.

To rebuild the suburb reference file after changes:

```bash
python Domain_Info/build_suburb_list.py --state QLD --fast50
# Outputs: Domain_Info/Ref_Suburbs.json, Domain_Info/suburbs.txt
```

---

## Scoring — three pillars

Each listing is scored across three dimensions:

**Growth** — rezone potential, block size (400m²+), Fast 50 suburb membership, infrastructure keywords in listing text.

**Deals** — days on market, price reductions, motivated-seller keywords ("deceased estate", "mortgagee", "as-is"), auction/EOI flags.

**Cashflow** — estimated gross yield (from `rent_estimator.py`), dual-income / granny flat signals, bedroom count relative to suburb demand.

Scores are written to `scored_listings.json` and colour-coded in `SEQ_Listings.xlsx`.

To tune scoring weights or add new signals, edit `Strategy_Scoring/scoring.py`.

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
python Strategy_Scoring/score_listings.py --raw raw_listings.txt --out scored_listings.json

# Build Excel only (after scored_listings.json exists)
python build_excel.py

# Send email report (after scored_listings.json exists)
python send_report.py

# Batch scrape all suburbs in Domain_Info/suburbs.txt
python run_batch.py

# Rebuild suburb reference data
python Domain_Info/build_suburb_list.py --state QLD --fast50
```
