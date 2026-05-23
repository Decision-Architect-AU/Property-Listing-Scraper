# Property Listing Scraper

Automated pipeline that scrapes Domain.com.au daily, scores every listing against a three-pillar investment strategy, and emails a ranked HTML report with an Excel attachment.

---

## What it does

```
Domain.com.au  →  raw_listings.txt  →  scored_listings.json  →  SEQ_Listings.xlsx  →  Email
   (scrape)          (pipe-delimited)      (ranked + signals)       (Excel report)
```

1. **Scrape** — fetches listings from Domain.com.au for each target suburb
2. **Score** — ranks every listing on Growth, Deals, and Cashflow (0–10 each)
3. **Report** — builds a colour-coded Excel workbook
4. **Email** — sends one HTML dashboard email with the Excel attached

---

## File locations

Scripts and data are kept separate:

```
Scripts:  C:\Users\Administrator\Documents\Claude\Projects\Property Listing Scraper\
Data:     C:\DomainListingData\
```

**Data files (C:\DomainListingData\):**
| File | Contents |
|---|---|
| `raw_listings.txt` | Every scraped listing, pipe-delimited, one per line |
| `scored_listings.json` | All listings with three-pillar scores and signals |
| `SEQ_Listings.xlsx` | Final formatted Excel report |

**Script files:**
| File | Role |
|---|---|
| `domain_mcp.py` | MCP server — exposes all pipeline tools to Claude |
| `score_listings.py` | CLI: `raw_listings.txt` → `scored_listings.json` |
| `scoring.py` | Scoring engine (three-pillar logic) |
| `build_excel.py` | `scored_listings.json` → `SEQ_Listings.xlsx` |
| `send_report.py` | Emails the report via Gmail SMTP |
| `run_batch.py` | Batch-scrapes all suburbs in a suburbs file |
| `fast50_suburbs.txt` | Canonical slug list for the Fast 50 target suburbs |
| `email_config.json` | Gmail credentials (not committed) |
| `suburbs_stats_extracted.xlsx` | SQM Research suburb stats (read-only reference) |

**Subdirectories:**
| Path | Contents |
|---|---|
| `Domain_Info/` | `regions.py` (Fast 50, zoning), `suburb_stats.py`, `rent_estimator.py` |
| `Strategy_Scoring/` | Canonical `scoring.py` and `score_listings.py` |

---

## The three scores

Every listing gets three scores from 0 to 10:

| Pillar | Question | Key signals |
|---|---|---|
| **Growth** | Will this suburb appreciate? | Rezone potential, block ≥ 400m², Fast 50 suburb, corner block, subdivision/STCA keywords |
| **Deals** | Is there genuine seller pressure? | Mortgagee/deceased estate/divorce (+3), motivated vendor/price reduced (+2), relocating/overseas (+1), days on market 60/90/180+ (+1/2/3) |
| **Cashflow** | Will rent cover the costs? | Estimated gross yield, granny flat/dual income signals, bedroom count, NDIS/SDA keywords, low vacancy rate |

Scores are summed for a **total score** used to rank and sort the report.

**What does NOT score as a Deal:**
- Entry price alone (cheap is not the same as a deal)
- Auction listing (price discovery is not seller distress)
- "Contact agent" / EOI (standard listing practice)

---

## Fast 50 suburbs

50 target suburbs across Queensland with the best mix of affordability, growth signals, and rental demand:

| Region | Suburbs |
|---|---|
| Logan / South Brisbane | Beenleigh, Woodridge, Browns Plains, Berrinba, Crestmead, Marsden, Eagleby, Bethania, Slacks Creek, Bahrs Scrub |
| Ipswich corridor | Ipswich, Ripley, Springfield, Redbank Plains, Bellbird Park, Collingwood Park, Augustine Heights, Brassall, Plainland, Blackstone |
| Moreton Bay | Caboolture, Morayfield, North Lakes, Narangba, Petrie, Bray Park, Deception Bay, Banksia Beach, Beachmere, Bellmere |
| Brisbane inner | Acacia Ridge, Archerfield, Oxley, Yeronga, Wavell Heights, Zillmere |
| Sunshine Coast | Nambour, Bli Bli |
| Toowoomba | Toowoomba, Harristown |
| Townsville | Townsville, Bohle Plains |
| Mackay | Ooralea, Andergrove |
| Rockhampton | Berserker, Norman Gardens, Park Avenue, Allenstown |
| Bundaberg / Gladstone | Bargara, Walkervale, Avenell Heights, Clinton |

---

## Running the pipeline

### Automated (scheduled via Cowork)

The `domain-scraper` skill runs on a schedule. It:
1. Calls `full_pipeline()` for each Fast 50 suburb
2. Calls `send_report()` **once** after all suburbs are done

The MCP server (`C:\MCP_Servers\DomainScaper\domain_mcp.py`) must be running. It is registered in Claude's config and starts automatically.

### Manual — rescore and email existing data

```bash
python score_listings.py --raw C:\DomainListingData\raw_listings.txt --out C:\DomainListingData\scored_listings.json
python build_excel.py
python send_report.py
```

### Manual — full batch scrape then email

```bash
python run_batch.py --suburbs fast50_suburbs.txt --max-pages 3
python send_report.py
```

### Manual — single suburb via MCP tool

```python
full_pipeline(
    suburb_slug="ipswich-qld-4305",
    project_dir=r"C:\Users\Administrator\Documents\Claude\Projects\Property Listing Scraper"
)
```

### Sending the report email

Always call `send_report` **once**, after all suburbs are processed. Never call it per suburb or per region group — this is what causes multiple emails.

```python
# MCP tool (preferred):
send_report(project_dir=r"C:\Users\Administrator\Documents\Claude\Projects\Property Listing Scraper")

# CLI:
python send_report.py
```

The HTML dashboard is in the email body; `SEQ_Listings.xlsx` is attached with a dated filename.

---

## Adding a new suburb

1. Add to `Domain_Info/regions.py`:
   ```python
   # In ZONING dict:
   "Suburb Name": {"zone": "Low Density Residential", "council": "Council Name", "notes": "..."},

   # In REZONE_POTENTIAL dict:
   "Suburb Name": "MEDIUM",  # HIGH, MEDIUM, or LOW

   # Optionally add to FAST_50 set
   ```

2. Add the slug to `fast50_suburbs.txt`

3. Run `full_pipeline()` for the new suburb

**Suburb slug format:** `suburb-state-postcode` — e.g. `ipswich-qld-4305`, `caboolture-qld-4510`

---

## Email configuration

Create `email_config.json` in the project folder (not committed to git):

```json
{
  "gmail_address": "you@gmail.com",
  "gmail_app_password": "xxxx xxxx xxxx xxxx",
  "to": "you@gmail.com"
}
```

Use a [Gmail App Password](https://support.google.com/accounts/answer/185833), not your account password. Enable 2FA first.

---

## Install

```bash
pip install fastmcp httpx openpyxl requests
```

The MCP server is registered in `claude_desktop_config.json` (Claude's config file):

```json
{
  "mcpServers": {
    "Domaincomau-Scraper": {
      "command": "python",
      "args": ["C:\\MCP_Servers\\DomainScaper\\domain_mcp.py"]
    }
  }
}
```
