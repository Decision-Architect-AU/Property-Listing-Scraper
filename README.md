# Property Listing Scraper 🏠

Think of this like a robot that goes to Domain.com.au every day, reads thousands of property listings, and hands you back a shortlist of the best investment opportunities — already ranked and colour-coded in Excel.

No manual searching. No spreadsheets to fill in yourself. You tell it which suburbs to watch, and it does the rest.

---

## What does it actually do?

Here's the flow from start to finish:

```
Domain.com.au  →  raw_listings.txt  →  scored_listings.json  →  SEQ_Listings.xlsx
   (website)        (all listings)        (ranked listings)         (your report)
```

**Step 1 — Scrape:** The robot visits Domain.com.au and collects every property for sale in your target suburbs. It grabs the address, price, beds/baths, land size, and listing URL.

**Step 2 — Describe:** It then visits each listing's own page to grab the full description text (things like "development potential", "granny flat", "motivated seller").

**Step 3 — Score:** Every listing gets three scores — Growth, Deals, and Cashflow — based on suburb data, zoning maps, and what the listing description says.

**Step 4 — Report:** It writes everything to an Excel file with colour-coded columns so you can instantly see the winners.

---

## Where do files live?

Scripts (the code) live in this project folder. Data (the actual listing files) are saved separately so they don't clutter the code:

```
C:\Users\...\Property Listing Scraper\    ← scripts live here
│
├── domain_mcp.py          ← the brain — all the main tools
├── run_batch.py           ← runs all suburbs one by one
├── build_excel.py         ← turns scored data into Excel
├── send_report.py         ← emails you the report
├── email_config.json      ← your Gmail details for sending reports
│
├── Domain_Info\           ← suburb knowledge lives here
│   ├── regions.py         ← which suburbs to target, zoning, rezone potential
│   ├── suburb_stats.py    ← median prices, rents, vacancy rates per suburb
│   ├── rent_estimator.py  ← figures out rental income from listing text
│   └── build_suburb_list.py  ← generates the suburbs.txt target list
│
└── Strategy_Scoring\      ← scoring logic lives here
    ├── scoring.py         ← the actual scoring engine (Growth / Deals / Cashflow)
    └── score_listings.py  ← runs the scorer on all listings in raw_listings.txt

C:\DomainListingData\                     ← data files live here (separate!)
├── raw_listings.txt       ← every listing scraped so far (pipe-delimited)
├── scored_listings.json   ← listings with their scores attached
└── SEQ_Listings.xlsx      ← your final Excel report
```

---

## The three scores explained

Every property gets scored on three things. Think of them as three questions:

| Score | Question it answers | What it looks at |
|---|---|---|
| **Growth** | Will this suburb go up in value? | Rezone potential, block size (400m²+), Fast 50 suburb list, infrastructure keywords |
| **Deals** | Is this a bargain? | Days on market, price drops, keywords like "deceased estate", "mortgagee", "as-is" |
| **Cashflow** | Will it pay for itself from rent? | Estimated weekly rent, gross yield %, granny flat / dual income signals |

The scores are combined into a total score. Higher = better opportunity.

---

## The Fast 50 suburbs

These are the 50 target suburbs across Queensland that have the best combination of affordability, growth signals, and rental demand:

**Logan / South Brisbane:** Beenleigh, Woodridge, Browns Plains, Berrinba, Crestmead, Marsden, Eagleby, Bethania, Slacks Creek, Bahrs Scrub

**Ipswich corridor:** Ipswich, Ripley, Springfield, Redbank Plains, Bellbird Park, Collingwood Park, Augustine Heights, Brassall, Plainland, Blackstone

**Moreton Bay:** Caboolture, Morayfield, North Lakes, Narangba, Petrie, Bray Park, Deception Bay, Banksia Beach, Beachmere, Bellmere

**Brisbane inner:** Acacia Ridge, Archerfield, Oxley, Yeronga, Wavell Heights, Zillmere

**Sunshine Coast:** Nambour, Bli Bli

**Toowoomba:** Toowoomba, Harristown

**Townsville:** Townsville, Bohle Plains

**Mackay:** Ooralea, Andergrove

**Rockhampton:** Berserker, Norman Gardens, Park Avenue, Allenstown

**Bundaberg / Gladstone:** Bargara, Walkervale, Avenell Heights, Clinton

---

## Running it automatically

The scraper runs as a scheduled task inside Claude (Cowork). When it fires:

1. It loops through all suburbs in `Domain_Info/suburbs.txt`
2. Scrapes Domain.com.au for each one
3. Scores everything
4. Builds the Excel report
5. Emails the report to you

You don't need to touch anything — just open the Excel file when it arrives.

---

## Running it manually (command line)

If you want to run a single suburb right now:

```bash
# Scrape one suburb and get a full report
python domain_mcp.py full_pipeline --suburb ipswich-qld-4305

# Just rebuild the Excel from existing data
python build_excel.py

# Just re-score existing listings
python Strategy_Scoring/score_listings.py --raw C:\DomainListingData\raw_listings.txt --out C:\DomainListingData\scored_listings.json
```

---

## Suburb slug format

Domain.com.au uses URL slugs like `suburb-state-postcode`. Examples:

| Suburb | Slug |
|---|---|
| Ipswich QLD 4305 | `ipswich-qld-4305` |
| Toowoomba QLD 4350 | `toowoomba-qld-4350` |
| Caboolture QLD 4510 | `caboolture-qld-4510` |
| Beenleigh QLD 4207 | `beenleigh-qld-4207` |

---

## Adding a new suburb

1. Open `Domain_Info/regions.py`
2. Add the suburb to `ZONING` (include the zone type and council)
3. Add it to `REZONE_POTENTIAL` — use `"HIGH"`, `"MEDIUM"`, or `"LOW"`
4. Add to `FAST_50` if it's a high-growth target
5. Add to `CASHFLOW_DEMAND_SUBURBS` if it has strong rental demand

Without these entries the scoring engine still works, but it won't pick up rezone or demand signals for that suburb.

---

## Install / setup

```bash
pip install fastmcp httpx openpyxl
```

The MCP server (`domain_mcp.py`) is registered in Claude's config file so it loads automatically when you open Cowork.
