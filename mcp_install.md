# domain-listings MCP — Install Guide

## 1. Install dependencies

```bash
pip install fastmcp httpx
```

## 2. Add to Claude config

**Claude Code** — add to `~/.claude/settings.json` (or `.claude/settings.json` in your project):

```json
{
  "mcpServers": {
    "domain-listings": {
      "command": "python",
      "args": ["/absolute/path/to/domain_mcp.py"]
    }
  }
}
```

**Cowork / Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "domain-listings": {
      "command": "python",
      "args": ["/absolute/path/to/domain_mcp.py"]
    }
  }
}
```

Replace `/absolute/path/to/domain_mcp.py` with the actual path to the file.

## 3. Usage

Once connected, Claude has access to these tools:

### One-shot pipeline
```
full_pipeline(
  suburb_slug = "toowoomba-qld-4350",
  project_dir = "/path/to/your/project"
)
```
Scrapes Domain → updates raw_listings.txt → scores → builds both Excel files.

### Individual steps
```
search_listings("caboolture-qld-4510")          # returns rows
append_listings(project_dir, rows, "Caboolture") # writes raw_listings.txt
run_scoring(project_dir)                          # → scored_listings.json
run_excel_build(project_dir)                      # → Excel files
```

## 4. Suburb slug format

`lowercase-suburb-state-postcode`

Examples:
- Tamworth NSW 2340 → `tamworth-nsw-2340`
- Ipswich QLD 4305 → `ipswich-qld-4305`
- Caboolture QLD 4510 → `caboolture-qld-4510`
- Toowoomba QLD 4350 → `toowoomba-qld-4350`

## 5. Before adding a new suburb

Edit `score_listings.py` to add the suburb to:
- `ZONING` dict (zone type, council, notes)
- `REZONE_POTENTIAL` dict (growth potential string)
- `REZONE_SUBURBS` or `HIGH_REZONE` sets if applicable

Otherwise it will score using `DEFAULT_ZONE` and miss the rezone signals.
