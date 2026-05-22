# CLAUDE.md — Project Architecture & Decision Log

Read this at the start of every session before touching any code.
When a decision is made or a bug is fixed, record it here so it doesn't get undone.

---

## File locations — CRITICAL

Scripts live in the project folder. Data files live in a **separate** data directory.

```
Scripts:  C:\Users\Administrator\Documents\Claude\Projects\Property Listing Scraper\
Data:     C:\DomainListingData\
```

**`C:\DomainListingData\` contains:**
- `raw_listings.txt` — all scraped listings (pipe-delimited)
- `scored_listings.json` — listings with scores
- `SEQ_Listings.xlsx` — final Excel report

**Do NOT read or write these files from the project folder.** They used to live there but were moved. Any code that still references `Path(project_dir) / "raw_listings.txt"` etc. is wrong and needs updating.

Files that ARE correctly in the project folder:
- `email_config.json` — Gmail credentials (stays with scripts, not data)
- `suburbs_stats_extracted.xlsx` — SQM Research suburb stats (reference data, not output)
- `suburbs.txt` — target suburb slugs for batch runs

---

## DATA_DIR constant — where it's defined

`domain_mcp.py` defines:
```python
DATA_DIR = Path(r"C:\DomainListingData")
DATA_DIR.mkdir(parents=True, exist_ok=True)
```

`send_report.py` defines:
```python
DATA_DIR    = Path(r"C:\DomainListingData")
SCORED_JSON = DATA_DIR / "scored_listings.json"
```

Both files should use this constant for all data file I/O. Do not change these back to `project_dir` paths.

---

## Folder structure

```
Property Listing Scraper\
├── CLAUDE.md                ← this file
├── README.md
├── domain_mcp.py            ← MCP server, all pipeline tools
├── build_excel.py           ← scored_listings.json → SEQ_Listings.xlsx
├── send_report.py           ← emails the Excel report
├── run_batch.py             ← batch-scrapes suburbs.txt
├── email_config.json        ← Gmail credentials
├── suburbs_stats_extracted.xlsx  ← SQM Research data (read-only reference)
│
├── Domain_Info\             ← suburb knowledge
│   ├── regions.py           ← Fast 50, zoning, rezone potential sets
│   ├── suburb_stats.py      ← SQM stats lookup (reads suburbs_stats_extracted.xlsx)
│   ├── rent_estimator.py    ← extracts/estimates rental income from listing text
│   └── build_suburb_list.py ← generates suburbs.txt from stats file
│
└── Strategy_Scoring\        ← scoring engine
    ├── scoring.py           ← three-pillar score_listing() function
    └── score_listings.py    ← CLI wrapper: raw_listings.txt → scored_listings.json
```

**Note:** Duplicate copies of `regions.py`, `scoring.py`, `suburb_stats.py`, `rent_estimator.py`, `score_listings.py` exist in the project root from before the restructure. The canonical versions are in `Domain_Info/` and `Strategy_Scoring/`. The root copies are legacy — do not update them, do not delete them without checking nothing depends on them.

`domain_mcp.py` `run_scoring` looks for `Strategy_Scoring/score_listings.py` first, then falls back to the root.

---

## Email — one email per full run, NOT per suburb or region

`full_pipeline()` does NOT send email. It was changed deliberately to avoid sending 50 emails when running all Fast 50 suburbs.

### The rule

**Call `send_report` EXACTLY ONCE — after the very last suburb in the batch has been processed.**

- ❌ Do NOT call it after each suburb
- ❌ Do NOT call it after each region group (Logan, Ipswich corridor, Moreton Bay, etc.)
- ✅ Call it once, only after ALL suburbs are done

### How to send it

Use the `send_report` MCP tool (Tool 8 in `domain_mcp.py`):
```python
send_report(project_dir="C:\\Users\\Administrator\\Documents\\Claude\\Projects\\Property Listing Scraper")
```

Do NOT call `python send_report.py` via Bash — use the MCP tool so the call is explicit and controlled.

**Do not add email back into `full_pipeline()`.**

---

## Scoring — three pillars

Every listing gets scored on:
- **Growth** — rezone potential, block size ≥ 400m², Fast 50 membership, infrastructure keywords
- **Deals** — days on market, price reductions, motivated-seller keywords
- **Cashflow** — estimated gross yield, dual-income/granny flat signals, bedroom count

Scoring logic: `Strategy_Scoring/scoring.py` → `score_listing(row) -> dict | None`
Returns `None` for listings that should be excluded (e.g. strata, H&L packages).

---

## Rent estimator — sanity cap on suburb median

`Domain_Info/rent_estimator.py` has `_MAX_SANE_RENT_PW = 2_000`.

**Why it exists:** The `suburbs_stats_extracted.xlsx` file has a corrupt row for Clinton SA (postcode 5570) where the median sale price (~$297,500) landed in the `rent_house_pw` column. Without a cap, any listing that falls back to suburb median rent gets an annual rent of ~$15,000,000.

The cap treats any suburb median rent above $2,000/week as invalid data and falls back to `rent_source = 'none'` instead.

**Do not remove this cap.**

---

## build_excel.py — accepts explicit paths

`build_excel.main()` signature:
```python
def main(scored_path: Path = None, out_path: Path = None)
```

When called from `domain_mcp.py`, always pass explicit paths:
```python
mod.main(scored_path=DATA_DIR / "scored_listings.json", out_path=DATA_DIR / "SEQ_Listings.xlsx")
```

Do not call `mod.main()` with no args — it will default to writing in the project dir.

---

## run_scoring — sys.path setup

`domain_mcp.py` `run_scoring()` inserts three paths before importing:
```python
for p in [str(project_dir),
          str(Path(project_dir) / "Strategy_Scoring"),
          str(Path(project_dir) / "Domain_Info")]:
    if p not in sys.path:
        sys.path.insert(0, p)
```

This lets `scoring.py` import from `rent_estimator`, `suburb_stats`, and `regions` regardless of which copy it finds first.

---

## Bash vs Write tool — IMPORTANT

**Bash shell writes do NOT persist to the Windows filesystem between sessions.**

The Linux sandbox mounts Windows folders read-write, but changes only survive within the same session's overlay. If you use `cp`, `cat >`, or any bash write command to create files in the project folder, those files will be gone next session.

**Rule: always use the Write or Edit tool to create or modify files that must persist.**

Only use bash for: reading files, running scripts, git status/diff checks, py_compile checks.

---

## Git — commit after every working chunk

The project is a git repo at `C:\Users\Administrator\Documents\Claude\Projects\Property Listing Scraper`.

Subdirectories `Domain_Info/` and `Strategy_Scoring/` are now tracked (files physically exist on disk).

Commit message convention: describe what changed and why, e.g.
- `"Route data files to C:\DomainListingData via DATA_DIR"`
- `"Add rent sanity cap — fix Clinton SA corrupt stats row"`

---

## Known issues / things to watch

- `run_batch.py` and `build_suburb_list.py` in the project root are older versions that still do some path lookups relative to `project_dir`. If they're used directly, they may write data files to the wrong place. Prefer triggering runs through `domain_mcp.py` tools.
- `suburbs.txt` in the project root currently contains ALL suburbs from the stats file. The Fast 50 target list used by the scheduled task is set inside the scheduled task config, not in this file.
- `master_suburbs.json` in the root is generated by the old `build_suburb_list.py`. The new version generates `Ref_Suburbs.json` in `Domain_Info/`.
