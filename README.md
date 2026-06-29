# Property Listing Scraper

Automated pipeline that scrapes Domain.com.au, scores every listing against a three-pillar investment strategy, and emails a ranked HTML report with an Excel attachment.

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

```
Scripts:  C:\Users\Glenn\Documents\Claude\Projects\Property Listing Scraper\
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
| `batch_fast50.py` | **Primary batch runner** — single Chrome session, all Fast 50 suburbs, then score + Excel + email |
| `scoring.py` | Scoring engine (three-pillar logic) |
| `score_listings.py` | CLI: `raw_listings.txt` → `scored_listings.json` |
| `build_excel.py` | `scored_listings.json` → `SEQ_Listings.xlsx` |
| `send_report.py` | Emails the report via Gmail SMTP |
| `run_batch.py` | Legacy batch runner (superseded by `batch_fast50.py`) |
| `regions.py` | Fast 50 suburb list, zoning info, rezone potential |
| `rent_estimator.py` | Gross yield / rent estimation helpers |
| `suburb_stats.py` | Vacancy rate and suburb stat lookups |
| `build_suburb_list.py` | Utility to rebuild the master suburb list |
| `fix_chromedriver.py` | Maintenance: clears cached drivers and re-downloads for current Chrome version |
| `fast50_suburbs.txt` | Canonical slug list for Fast 50 target suburbs |
| `email_config.json` | Gmail credentials (not committed) |
| `suburbs_stats_extracted.xlsx` | SQM Research suburb stats (read-only reference) |
| `domain-scraper.skill` | Cowork skill definition |

**Run logs:** `C:\DomainListingData\batch_YYYYMMDD_HHMM.log`

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

### Scheduled (Windows Task Scheduler — Tuesday nights)

`batch_fast50.py` is the primary runner. It opens one Chrome session, scrapes all suburbs in `fast50_suburbs.txt`, then scores, builds Excel, and emails the report.

```
python "C:\Users\Glenn\Documents\Claude\Projects\Property Listing Scraper\batch_fast50.py"
```

Logs are written to `C:\DomainListingData\batch_YYYYMMDD_HHMM.log`.

### Via Claude / MCP (on demand)

The MCP server must be running (registered in `claude_desktop_config.json` — starts automatically with Claude).

Run a full pipeline for one suburb:
```python
full_pipeline(suburb_slug="ipswich-qld-4305")
```

Send the report after all suburbs are processed:
```python
send_report()
```

**Always call `send_report` once, after all suburbs are done.** Never call it per suburb — this causes multiple emails.

### Manual CLI

Rescore existing data and email:
```bash
python score_listings.py --raw C:\DomainListingData\raw_listings.txt --out C:\DomainListingData\scored_listings.json
python build_excel.py
python send_report.py
```

---

## Adding a new suburb

1. Edit `regions.py`:
   ```python
   # ZONING dict:
   "Suburb Name": {"zone": "Low Density Residential", "council": "Council Name", "notes": "..."},

   # REZONE_POTENTIAL dict:
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

## Troubleshooting

### ChromeDriver version mismatch

If Chrome auto-updated and the scraper fails to launch:

```bash
python fix_chromedriver.py
```

This clears the cached driver and re-downloads the correct version for your installed Chrome.

---

## Install

```bash
pip install fastmcp undetected-chromedriver openpyxl requests httpx
pip install ollama  # optional — only needed for classify_listings()
```

Chrome must be installed: https://www.google.com/chrome/

The MCP server is registered in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "Domaincomau-Scraper": {
      "command": "python",
      "args": ["C:\\Users\\Glenn\\Documents\\Claude\\Projects\\Property Listing Scraper\\domain_mcp.py"]
    }
  }
}
```
