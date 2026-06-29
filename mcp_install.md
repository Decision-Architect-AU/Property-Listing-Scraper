# domain-listings MCP — Install Guide

## 1. Install dependencies

```bash
pip install fastmcp undetected-chromedriver openpyxl requests httpx
pip install ollama  # optional — only needed for classify_listings()
```

Chrome must be installed: https://www.google.com/chrome/

## 2. Add to Claude config

**Cowork / Claude Desktop** — add to `claude_desktop_config.json`:

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

**Claude Code** — add to `~/.claude/settings.json`:

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

## 3. Usage

Once connected, Claude has access to these tools:

### One-shot pipeline
```
full_pipeline(suburb_slug="toowoomba-qld-4350")
```
Scrapes Domain → updates raw_listings.txt → scores → builds Excel.

### Individual steps
```
search_listings("caboolture-qld-4510")          # returns rows
append_listings(rows=rows, suburb="Caboolture") # writes raw_listings.txt
run_scoring()                                    # → scored_listings.json
run_excel_build()                               # → SEQ_Listings.xlsx
send_report()                                   # email the report (once, after all suburbs)
classify_listings()                             # AI deal analysis via Ollama (optional)
```

### Send the report
Always call `send_report` **once**, after all suburbs are done — not per suburb.

## 4. Suburb slug format

`lowercase-suburb-state-postcode`

Examples:
- Tamworth NSW 2340 → `tamworth-nsw-2340`
- Ipswich QLD 4305 → `ipswich-qld-4305`
- Caboolture QLD 4510 → `caboolture-qld-4510`
- Toowoomba QLD 4350 → `toowoomba-qld-4350`

## 5. Before adding a new suburb

Edit `regions.py` (project root) to add the suburb to:
- `ZONING` dict (zone type, council, notes)
- `REZONE_POTENTIAL` dict (growth potential string)
- `REZONE_SUBURBS` or `HIGH_REZONE` sets if applicable
- `FAST_50` set if it's a target suburb

Otherwise it will score using `DEFAULT_ZONE` and miss the rezone signals.

## 6. Troubleshooting ChromeDriver

If Chrome auto-updated and the scraper fails to launch, run:

```bash
python fix_chromedriver.py
```

This clears the cached driver and re-downloads the correct version.
