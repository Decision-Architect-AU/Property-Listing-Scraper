# Property Listing Scraper

## What does this do?

Think of it like a robot that visits Domain.com.au every week, reads every house listing across 50 target suburbs, and tells you which ones are worth looking at — based on your investment strategy.

Instead of spending hours scrolling through listings, it does the legwork and emails you a ranked, colour-coded report with the best picks.

---

## The big picture

```
Domain.com.au  →  raw_listings.txt  →  scored_listings.json  →  SEQ_Listings.xlsx  →  Email
```

1. **Scrape** — visits Domain.com.au for each suburb, collects every house listing (up to ~100 per suburb). Apartments, strata titles, and house-and-land packages are filtered out automatically.

2. **Store** — saves listings to `C:\DomainListingData\raw_listings.txt`. One property per line, details separated by pipes (`|`): suburb, address, price, beds, land size, etc.

3. **Score** — every listing gets rated on three things:
   - 🌿 **Growth** — Is this suburb likely to be rezoned? Big block? In the Fast 50 target list?
   - 💸 **Deals** — Does it look like a motivated seller? Long on market, price drops, deceased estate keywords?
   - 💰 **Cashflow** — Will it rent well? Estimated yield, granny flat potential, bedroom count?

4. **Report** — builds `C:\DomainListingData\SEQ_Listings.xlsx`, a colour-coded spreadsheet with the best picks at the top.

5. **Email** — after all 50 suburbs are done, sends one summary email to `samthemerchant@gmail.com`.

---

## Folder layout

```
Property Listing Scraper/        ← All Python scripts live here (the "brain")
│
├── domain_mcp.py                ← The main engine. Claude talks to this directly via the
│                                   MCP plugin. Handles scraping, scoring, and Excel builds.
│
├── build_excel.py               ← Turns scored data into the colour-coded .xlsx report
├── send_report.py               ← Sends the HTML email report after a full run
├── run_batch.py                 ← Alternative: run the whole pipeline from the command line
├── email_config.json            ← Your Gmail address and app password (keep this private!)
│
├── Domain_Info/                 ← Everything about suburbs and locations
│   ├── regions.py               ← The 50 target suburbs with zoning data, rezone ratings,
│   │                               Fast 50 membership, and cashflow demand flags
│   ├── rent_estimator.py        ← Estimates weekly rent by suburb and bedroom count
│   ├── suburb_stats.py          ← Vacancy rates, median prices by suburb
│   ├── build_suburb_list.py     ← Utility: regenerates Ref_Suburbs.json
│   ├── suburbs.txt              ← Suburb slugs list for the command-line batch runner
│   ├── Ref_Suburbs.json         ← Full reference list of all suburbs with metadata
│   ├── SA3_2021_AUST.xlsx       ← ABS geographic reference data
│   └── suburbs_stats_extracted.xlsx  ← Suburb stats source data
│
└── Strategy_Scoring/            ← The investment scoring logic
    ├── scoring.py               ← The three-pillar scoring engine (Growth / Deals / Cashflow)
    └── score_listings.py        ← Reads raw_listings.txt, scores every row, writes JSON


C:\DomainListingData\            ← Data files only — no scripts here
├── raw_listings.txt             ← Every scraped listing in pipe-delimited format
├── scored_listings.json         ← Same listings after scoring
├── SEQ_Listings.xlsx            ← The final colour-coded Excel report
└── email_log.json               ← Log of sent emails
```

---

## The Fast 50 — which suburbs?

50 Queensland growth suburbs across:

- **Logan / South Brisbane** — Beenleigh, Woodridge, Browns Plains, Berrinba, Crestmead…
- **Ipswich** — Ripley, Springfield, Redbank Plains, Bellbird Park, Collingwood Park…
- **Moreton Bay** — Caboolture, North Lakes, Narangba, Petrie, Bray Park…
- **Toowoomba** — Toowoomba CBD, Rockville, Harristown, Wilsonton, Newtown…
- **Townsville / Mackay** — Bohle Plains, Ooralea, Andergrove, Berserker, Norman Gardens…
- **Bundaberg / Fraser Coast / Rockhampton** — Bargara, Walkervale, Avenell Heights, Park Avenue…

All 50 are pre-loaded with zoning data and rent estimates in `Domain_Info/regions.py`. Adding a new suburb means editing that file — see "Adding a new suburb" below.

---

## How the scoring works

Each listing gets a score out of 10 in three categories. Higher = better.

| Pillar | What scores points |
|---|---|
| 🌿 Growth | In the Fast 50? HIGH/MEDIUM rezone potential? Block over 400m²? Infrastructure keywords in the listing text? |
| 💸 Deals | Days on market over 60? Price reduction mentioned? Keywords: "deceased estate", "mortgagee", "as-is", "auction" |
| 💰 Cashflow | Gross yield over 7%? Granny flat or dual income mentioned? Higher bedroom count relative to suburb demand |

The **Total** column in the Excel report is Growth + Deals + Cashflow. Columns are colour-coded: dark green (strong), amber (okay), grey (weak).

---

## The automated weekly run

Claude runs this on a schedule. Here's what happens each time:

1. Loops through all 50 suburb slugs, calling `full_pipeline()` for each one
2. Each call scrapes Domain, saves listings to `C:\DomainListingData`, and scores everything
3. After all 50 suburbs are done, calls `send_report.py` to send one email

You don't need to do anything — just check your inbox.

---

## Running it manually

**From inside Cowork / Claude** — just ask Claude to run the Fast 50 pipeline, or call `full_pipeline` directly with a suburb slug.

**From the command line:**

```bash
# Build the Excel report from existing scored data
python build_excel.py

# Send the email report
python send_report.py

# Batch scrape all suburbs in Domain_Info\suburbs.txt
python run_batch.py
```

---

## Setup

Install dependencies:

```bash
pip install fastmcp httpx openpyxl
```

`curl` must be on your system PATH — it's built into Windows 10/11 already.

---

## Adding a new suburb

1. Open `Domain_Info/regions.py`
2. Add it to `ZONING` — zone type, council, notes
3. Add it to `REZONE_POTENTIAL` — `"HIGH"`, `"MEDIUM"`, or `"LOW"`
4. Add to `HIGH_REZONE` or `MEDIUM_REZONE` sets if applicable
5. Add to `FAST_50` if it's a target suburb
6. Add to `CASHFLOW_DEMAND_SUBURBS` if rental demand is strong
7. Add the Domain slug to `Domain_Info/suburbs.txt` for batch runs

Without these entries the scoring engine uses `DEFAULT_ZONE` and misses all rezone signals.

**Suburb slug format:** `lowercase-suburb-name-state-postcode`

| Location | Slug |
|---|---|
| Ipswich QLD 4305 | `ipswich-qld-4305` |
| Toowoomba QLD 4350 | `toowoomba-qld-4350` |
| Caboolture QLD 4510 | `caboolture-qld-4510` |
| North Lakes QLD 4509 | `north-lakes-qld-4509` |

---

## Email setup

Edit `email_config.json`:

```json
{
  "gmail_address": "you@gmail.com",
  "gmail_app_password": "xxxx xxxx xxxx xxxx",
  "to": "you@gmail.com"
}
```

The `gmail_app_password` is a 16-character App Password from Google Account → Security → 2-Step Verification → App Passwords. It's not your normal Gmail password.

---

## MCP plugin setup (Cowork / Claude Desktop)

Add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "Domaincomau-Scraper": {
      "command": "python",
      "args": ["C:/Users/Administrator/Documents/Claude/Projects/Property Listing Scraper/domain_mcp.py"]
    }
  }
}
```
