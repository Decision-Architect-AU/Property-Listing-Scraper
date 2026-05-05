"""
regions.py — Suburb knowledge base for the Fast 50 target list.
Edit this file to add suburbs, update zoning, or adjust scoring sets.

To add a new suburb:
  1. Add to ZONING with council, zone, and notes
  2. Add to REZONE_POTENTIAL with rating string
  3. Add to HIGH_REZONE or MEDIUM_REZONE if applicable
  4. Add to FAST_50 if it's a target suburb
  5. Add to CASHFLOW_DEMAND_SUBURBS if near hospital/TAFE/employment hub
"""

# ── Zoning data ───────────────────────────────────────────────────────────────
ZONING: dict[str, dict] = {

    # ── Logan City Council ────────────────────────────────────────────────────
    "Woodridge":       {"council": "Logan City Council",   "zone": "Low Density Res / Centre Zone",      "notes": "Train station precinct. Centre zone near station. High MDR potential."},
    "Kingston":        {"council": "Logan City Council",   "zone": "Low Density Res / Centre Zone",      "notes": "Urban core of Logan. Centre zone, MDR pockets near transit."},
    "Logan Central":   {"council": "Logan City Council",   "zone": "Low Density Res / Centre Zone",      "notes": "Logan CBD fringe. Centre zone, high MDR potential."},
    "Marsden":         {"council": "Logan City Council",   "zone": "Low Density Res / MDR",              "notes": "Infill suburb. MDR zoning along key corridors."},
    "Browns Plains":   {"council": "Logan City Council",   "zone": "Low Density Res / Centre Zone",      "notes": "Major retail hub. MDR along Grand Plaza corridor."},
    "Beenleigh":       {"council": "Logan City Council",   "zone": "Low Density Res / Centre Zone",      "notes": "Major centre zone. Train line. ShapingSEQ growth node. High MDR potential."},
    "Eagleby":         {"council": "Logan City Council",   "zone": "Low Density Residential",            "notes": "Near Beenleigh CBD. Affordable. Rental demand."},
    "Bethania":        {"council": "Logan City Council",   "zone": "Low Density Residential",            "notes": "Near Beenleigh. Train station suburb. Rental demand."},
    "Berrinba":        {"council": "Logan City Council",   "zone": "Low Density Res / Industry Fringe",  "notes": "Growth suburb near Rochedale industrial. Rental demand."},
    "Crestmead":       {"council": "Logan City Council",   "zone": "Low Density Residential",            "notes": "Growth suburb. Industrial fringe. Strong rental demand."},
    "Slacks Creek":    {"council": "Logan City Council",   "zone": "Low Density Residential",            "notes": "Established suburb. MDR pockets along main roads."},
    "Springwood":      {"council": "Logan City Council",   "zone": "Low Density Res / Mixed Use",        "notes": "Major commercial hub. MDR and mixed use pockets."},
    "Meadowbrook":     {"council": "Logan City Council",   "zone": "Low Density Residential",            "notes": "Near Logan Hospital and TAFE. Rental demand high."},
    "Regents Park":    {"council": "Logan City Council",   "zone": "Low Density Residential",            "notes": "Established suburb. Close to train line."},
    "Underwood":       {"council": "Logan City Council",   "zone": "Low Density Res / Mixed Use",        "notes": "Corridor suburb. Mixed-use and MDR pockets."},
    "Bahrs Scrub":     {"council": "Logan City Council",   "zone": "Low Density Res / Growth Corridor",  "notes": "Growth corridor near Beenleigh."},

    # ── Ipswich City Council ──────────────────────────────────────────────────
    "Ipswich":           {"council": "Ipswich City Council", "zone": "Low Density Res / Inner Urban",        "notes": "MDR / Centre Zone potential near CBD. ShapingSEQ corridor."},
    "Leichhardt":        {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Inner suburb adj to Ipswich CBD. Rezone upside likely."},
    "East Ipswich":      {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Heritage precinct. Large blocks."},
    "Brassall":          {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Growth suburb west of CBD. MDR pockets."},
    "Bellbird Park":     {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Established suburb near Springfield. Stable LDR."},
    "Collingwood Park":  {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Good value. Near Springfield corridor."},
    "Redbank Plains":    {"council": "Ipswich City Council", "zone": "Low Density Res / Emerging Community", "notes": "Fast-growing suburb. Emerging community zones at fringe."},
    "Ripley":            {"council": "Ipswich City Council", "zone": "Emerging Community / PDA",             "notes": "Ripley Valley Priority Development Area. Greenfield master-planned."},
    "Augustine Heights": {"council": "Ipswich City Council", "zone": "Low Density Res / Growth Corridor",   "notes": "Part of Springfield PDA corridor. High-growth greenfield."},
    "Springfield":       {"council": "Ipswich City Council", "zone": "Low Density Res / Mixed Use",          "notes": "Springfield Lakes / Orion corridor. Centre zone near retail hub."},
    "Basin Pocket":      {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Inner Ipswich suburb. Near CBD. Rezone upside."},
    "Barellan Point":    {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Rural-residential fringe. Large blocks near Ipswich."},
    "Plainland":         {"council": "Ipswich City Council", "zone": "Low Density Res / Growth Corridor",   "notes": "Growth area west of Ipswich on Warrego Hwy."},
    "Blackstone":        {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Older suburb near Ipswich CBD. Affordable."},

    # ── Moreton Bay Regional Council ─────────────────────────────────────────
    "Caboolture":      {"council": "Moreton Bay Regional", "zone": "Low Density Res / Centre Zone",  "notes": "Centre zone near CBD. MDR inner ring. ShapingSEQ growth node."},
    "Morayfield":      {"council": "Moreton Bay Regional", "zone": "Low Density Res / MDR",          "notes": "Active MDR and Centre zone pockets. High growth."},
    "Narangba":        {"council": "Moreton Bay Regional", "zone": "Low Density Residential",        "notes": "Growth suburb. Commuter belt. Strong rental demand."},
    "North Lakes":     {"council": "Moreton Bay Regional", "zone": "Low Density Res / Mixed Use",    "notes": "Major PDA. Established master-planned community. Strong demand."},
    "Petrie":          {"council": "Moreton Bay Regional", "zone": "Low Density Res / Centre Zone",  "notes": "Train station precinct. Centre zone. University campus nearby."},
    "Bray Park":       {"council": "Moreton Bay Regional", "zone": "Low Density Residential",        "notes": "Established suburb near Petrie. Train line access."},
    "Deception Bay":   {"council": "Moreton Bay Regional", "zone": "Low Density Residential",        "notes": "Affordable coastal suburb. Strong rental demand."},
    "Banksia Beach":   {"council": "Moreton Bay Regional", "zone": "Low Density Residential",        "notes": "Bribie Island. Coastal lifestyle suburb."},
    "Beachmere":       {"council": "Moreton Bay Regional", "zone": "Low Density Residential",        "notes": "Coastal growth suburb. Near Caboolture."},
    "Bellmere":        {"council": "Moreton Bay Regional", "zone": "Low Density Residential",        "notes": "Near Caboolture. Growth fringe suburb."},

    # ── Brisbane City Council ─────────────────────────────────────────────────
    "Acacia Ridge":    {"council": "Brisbane City Council", "zone": "Low Density Res / Industry Fringe", "notes": "Near industrial corridor. Affordable. Rental demand."},
    "Archerfield":     {"council": "Brisbane City Council", "zone": "Low Density Res / Industry Fringe", "notes": "Near Archerfield Airport and industrial. Affordable."},
    "Oxley":           {"council": "Brisbane City Council", "zone": "Low Density Residential",           "notes": "Established western suburb. Train line. Good value."},
    "Yeronga":         {"council": "Brisbane City Council", "zone": "Low Density Res / MDR",             "notes": "Inner south. Close to city. MDR pockets. High demand."},
    "Wavell Heights":  {"council": "Brisbane City Council", "zone": "Low Density Residential",           "notes": "Established north Brisbane. Good schools. Stable growth."},
    "Zillmere":        {"council": "Brisbane City Council", "zone": "Low Density Res / Centre Zone",     "notes": "Train line. Centre zone pockets. Urban infill opportunity."},
    "Aspley":          {"council": "Brisbane City Council", "zone": "Low Density Residential",           "notes": "Established north suburb. Good value. Train nearby."},
    "Bald Hills":      {"council": "Brisbane City Council", "zone": "Low Density Residential",           "notes": "Near train line. Growth corridor to Moreton Bay."},

    # ── Sunshine Coast Regional Council ──────────────────────────────────────
    "Nambour":         {"council": "Sunshine Coast Regional", "zone": "Low Density Res / Centre Zone",  "notes": "Sunshine Coast hinterland hub. Centre zone. Affordable entry."},
    "Bli Bli":         {"council": "Sunshine Coast Regional", "zone": "Low Density Residential",        "notes": "Growth suburb near Maroochydore. Family demand."},

    # ── Toowoomba Regional Council ────────────────────────────────────────────
    "Toowoomba":       {"council": "Toowoomba Regional", "zone": "Low Density Res / Centre Zone",  "notes": "Major inland city. Diverse economy. ShapingSEQ node."},
    "Harristown":      {"council": "Toowoomba Regional", "zone": "Low Density Residential",        "notes": "Established Toowoomba suburb. Near hospital. Rental demand."},
    "Rockville":       {"council": "Toowoomba Regional", "zone": "Low Density Residential",        "notes": "Established Toowoomba suburb. Affordable. Rental demand."},
    "Wilsonton":       {"council": "Toowoomba Regional", "zone": "Low Density Residential",        "notes": "Toowoomba north-west. Established. Affordable."},
    "Newtown":         {"council": "Toowoomba Regional", "zone": "Low Density Residential",        "notes": "Inner Toowoomba. Character housing. Good rental demand."},
    "Drayton":         {"council": "Toowoomba Regional", "zone": "Low Density Residential",        "notes": "Outer Toowoomba suburb. Affordable entry price."},
    "Rangeville":      {"council": "Toowoomba Regional", "zone": "Low Density Residential",        "notes": "Toowoomba south-east. Good schools. Family demand."},

    # ── Townsville City Council ───────────────────────────────────────────────
    "Townsville":      {"council": "Townsville City Council", "zone": "Low Density Res / Centre Zone",  "notes": "Major regional city. Military, port, hospital employment base."},
    "Bohle Plains":    {"council": "Townsville City Council", "zone": "Low Density Residential",        "notes": "Growth suburb north Townsville. Strong rental demand."},
    "Cranbrook":       {"council": "Townsville City Council", "zone": "Low Density Residential",        "notes": "Established Townsville suburb. Affordable. Rental demand."},
    "Kelso":           {"council": "Townsville City Council", "zone": "Low Density Residential",        "notes": "Townsville western growth. Family suburb."},
    "Rasmussen":       {"council": "Townsville City Council", "zone": "Low Density Residential",        "notes": "Near Townsville CBD fringe. Affordable entry."},

    # ── Mackay Regional Council ───────────────────────────────────────────────
    "Ooralea":         {"council": "Mackay Regional", "zone": "Low Density Residential",  "notes": "Growth suburb near Mackay. Strong FIFO rental demand."},
    "Andergrove":      {"council": "Mackay Regional", "zone": "Low Density Residential",  "notes": "Established Mackay suburb. Near hospital. Rental demand."},
    "Blacks Beach":    {"council": "Mackay Regional", "zone": "Low Density Residential",  "notes": "Coastal Mackay suburb. Lifestyle and rental demand."},
    "Beaconsfield":    {"council": "Mackay Regional", "zone": "Low Density Residential",  "notes": "Established Mackay suburb. Affordable. Good yield."},
    "Rural View":      {"council": "Mackay Regional", "zone": "Low Density Residential",  "notes": "Growth area north of Mackay. Family demand."},

    # ── Rockhampton Regional Council ──────────────────────────────────────────
    "Berserker":         {"council": "Rockhampton Regional", "zone": "Low Density Residential",  "notes": "Established Rocky suburb. Near hospital. Rental demand."},
    "Norman Gardens":    {"council": "Rockhampton Regional", "zone": "Low Density Residential",  "notes": "Growth suburb near Rockhampton. Family demand."},
    "Park Avenue":       {"council": "Rockhampton Regional", "zone": "Low Density Residential",  "notes": "Near CQUniversity and hospital. Strong rental demand."},
    "Allenstown":        {"council": "Rockhampton Regional", "zone": "Low Density Residential",  "notes": "Near Rockhampton CBD. Affordable. Rental demand."},

    # ── Bundaberg Regional Council ────────────────────────────────────────────
    "Bargara":           {"council": "Bundaberg Regional", "zone": "Low Density Residential",  "notes": "Coastal Bundaberg suburb. Lifestyle and retirement demand."},
    "Walkervale":        {"council": "Bundaberg Regional", "zone": "Low Density Residential",  "notes": "Established Bundaberg suburb. Affordable. Rental demand."},
    "Avenell Heights":   {"council": "Bundaberg Regional", "zone": "Low Density Residential",  "notes": "Near hospital and TAFE. Strong rental demand."},
    "Avoca":             {"council": "Bundaberg Regional", "zone": "Low Density Residential",  "notes": "Outer Bundaberg suburb. Affordable entry price."},
    "Norville":          {"council": "Bundaberg Regional", "zone": "Low Density Residential",  "notes": "Established Bundaberg suburb. Good yield potential."},

    # ── Gladstone Regional Council ────────────────────────────────────────────
    "Clinton":           {"council": "Gladstone Regional", "zone": "Low Density Residential",  "notes": "Major Gladstone suburb. Port/industry employment base. Strong yield."},
    "Barney Point":      {"council": "Gladstone Regional", "zone": "Low Density Residential",  "notes": "Gladstone harbour suburb. Affordable. Rental demand."},
    "Beecher":           {"council": "Gladstone Regional", "zone": "Low Density Residential",  "notes": "Outer Gladstone. Industrial fringe. Affordable."},
    "Kin Kora":          {"council": "Gladstone Regional", "zone": "Low Density Residential",  "notes": "Established Gladstone suburb. Good value."},
}

# ── Rezone potential ──────────────────────────────────────────────────────────
REZONE_POTENTIAL: dict[str, str] = {
    # Logan
    "Woodridge":       "HIGH — Centre zone, MDR ring, transit precinct",
    "Kingston":        "HIGH — Urban core, centre zone, MDR pockets",
    "Logan Central":   "HIGH — Logan CBD fringe, centre zone",
    "Beenleigh":       "HIGH — Centre zone, train line, ShapingSEQ growth node",
    "Browns Plains":   "MEDIUM — Centre zone near Grand Plaza",
    "Springwood":      "MEDIUM — Mixed use, MDR pockets, commercial hub",
    "Marsden":         "MEDIUM — MDR corridors, infill opportunity",
    "Slacks Creek":    "MEDIUM — MDR pockets along main roads",
    "Meadowbrook":     "MEDIUM — Near Logan Hospital, rental demand",
    "Bethania":        "MEDIUM — Train station suburb, rental demand",
    "Regents Park":    "MEDIUM — Close to train line, infill",
    "Underwood":       "MEDIUM — Mixed use and MDR pockets",
    "Berrinba":        "MEDIUM — Industry fringe, growth suburb",
    "Crestmead":       "LOW-MEDIUM — Growth suburb, rental demand",
    "Eagleby":         "LOW-MEDIUM — Near Beenleigh, affordable",
    "Bahrs Scrub":     "LOW-MEDIUM — Growth corridor near Beenleigh",
    # Ipswich
    "Ipswich":           "HIGH — Inner city, ShapingSEQ corridor",
    "Leichhardt":        "HIGH — Adj CBD, character precinct",
    "Basin Pocket":      "HIGH — Inner Ipswich, rezone upside",
    "East Ipswich":      "MEDIUM — Large blocks, heritage area",
    "Redbank Plains":    "MEDIUM — Growing, emerging community",
    "Brassall":          "MEDIUM — MDR pockets, growth suburb",
    "Collingwood Park":  "MEDIUM — Near Springfield, established",
    "Ripley":            "HIGH — PDA greenfield, major growth corridor",
    "Augustine Heights": "HIGH — Springfield PDA, high-growth",
    "Springfield":       "MEDIUM — Mixed use, centre zone near Orion",
    "Plainland":         "LOW-MEDIUM — Growth corridor, Warrego Hwy",
    "Bellbird Park":     "LOW-MEDIUM — Established, near Springfield",
    "Blackstone":        "LOW-MEDIUM — Inner Ipswich, affordable",
    # Moreton Bay
    "Caboolture":      "HIGH — Centre zone, MDR ring, ShapingSEQ node",
    "Morayfield":      "HIGH — Active MDR and centre zone pockets",
    "North Lakes":     "MEDIUM — Established PDA, strong demand",
    "Petrie":          "MEDIUM — Train station, centre zone, university",
    "Narangba":        "MEDIUM — Growth suburb, commuter belt",
    "Bray Park":       "LOW-MEDIUM — Established, train access",
    "Deception Bay":   "LOW-MEDIUM — Affordable coastal, rental demand",
    # Brisbane
    "Acacia Ridge":    "MEDIUM — Industry fringe, affordable",
    "Archerfield":     "MEDIUM — Near airport/industrial, affordable",
    "Zillmere":        "MEDIUM — Train line, centre zone pockets",
    "Yeronga":         "MEDIUM — Inner south, MDR pockets",
    "Oxley":           "LOW-MEDIUM — Established, train line",
    "Wavell Heights":  "LOW-MEDIUM — Established, stable growth",
    # Sunshine Coast
    "Nambour":         "MEDIUM — Centre zone, affordable entry",
    "Bli Bli":         "LOW-MEDIUM — Growth suburb",
    # Toowoomba
    "Toowoomba":       "MEDIUM — Major city, diverse economy",
    "Harristown":      "MEDIUM — Near hospital, rental demand",
    "Newtown":         "MEDIUM — Inner Toowoomba, character housing",
    "Rockville":       "LOW-MEDIUM — Established, affordable",
    "Wilsonton":       "LOW-MEDIUM — Affordable entry",
    # Townsville
    "Townsville":      "MEDIUM — Major regional, employment base",
    "Bohle Plains":    "MEDIUM — Growth suburb, strong rental demand",
    "Cranbrook":       "LOW-MEDIUM — Established, affordable",
    # Mackay
    "Ooralea":         "MEDIUM — Growth suburb, FIFO demand",
    "Andergrove":      "MEDIUM — Near hospital, rental demand",
    "Beaconsfield":    "LOW-MEDIUM — Established, good yield",
    # Rockhampton
    "Berserker":       "MEDIUM — Near hospital, rental demand",
    "Norman Gardens":  "MEDIUM — Growth suburb, family demand",
    "Park Avenue":     "MEDIUM — Near uni/hospital, rental demand",
    "Allenstown":      "LOW-MEDIUM — Near CBD, affordable",
    # Bundaberg
    "Bargara":         "LOW-MEDIUM — Coastal lifestyle",
    "Walkervale":      "LOW-MEDIUM — Affordable, rental demand",
    "Avenell Heights": "MEDIUM — Near hospital/TAFE, rental demand",
    # Gladstone
    "Clinton":         "MEDIUM — Port/industry employment base",
    "Barney Point":    "LOW-MEDIUM — Harbour suburb, affordable",
}

# ── Scoring sets ──────────────────────────────────────────────────────────────
HIGH_REZONE = {
    # Logan
    "Woodridge", "Kingston", "Logan Central", "Beenleigh",
    # Ipswich
    "Ipswich", "Leichhardt", "Basin Pocket", "Ripley", "Augustine Heights",
    # Moreton Bay
    "Caboolture", "Morayfield",
}

MEDIUM_REZONE = {
    # Logan
    "Browns Plains", "Springwood", "Marsden", "Slacks Creek",
    "Meadowbrook", "Bethania", "Regents Park", "Underwood", "Berrinba",
    # Ipswich
    "East Ipswich", "Redbank Plains", "Brassall", "Collingwood Park", "Springfield",
    # Moreton Bay
    "North Lakes", "Petrie", "Narangba",
    # Brisbane
    "Acacia Ridge", "Archerfield", "Zillmere", "Yeronga",
    # Sunshine Coast
    "Nambour",
    # Toowoomba
    "Toowoomba", "Harristown", "Newtown",
    # Townsville
    "Townsville", "Bohle Plains",
    # Mackay
    "Ooralea", "Andergrove",
    # Rockhampton
    "Berserker", "Norman Gardens", "Park Avenue",
    # Bundaberg
    "Avenell Heights",
    # Gladstone
    "Clinton",
}

# Suburbs with strong rental demand near hospitals / TAFE / employment hubs
CASHFLOW_DEMAND_SUBURBS = {
    # Logan
    "Meadowbrook", "Logan Central", "Woodridge", "Kingston",
    # Ipswich
    "Ipswich", "Basin Pocket",
    # Moreton Bay
    "Petrie",
    # Toowoomba
    "Harristown", "Newtown",
    # Townsville
    "Townsville", "Bohle Plains", "Cranbrook",
    # Mackay
    "Andergrove", "Ooralea",
    # Rockhampton
    "Berserker", "Park Avenue", "Norman Gardens",
    # Bundaberg
    "Avenell Heights", "Walkervale",
    # Gladstone
    "Clinton", "Barney Point",
}

# The 50 target suburbs for the weekly automated run
FAST_50 = {
    # Logan / South Brisbane
    "Beenleigh", "Woodridge", "Browns Plains", "Berrinba", "Crestmead",
    "Marsden", "Eagleby", "Bethania", "Slacks Creek", "Bahrs Scrub",
    # Ipswich
    "Ipswich", "Ripley", "Springfield", "Redbank Plains", "Bellbird Park",
    "Collingwood Park", "Augustine Heights", "Brassall", "Plainland", "Blackstone",
    # Moreton Bay
    "Caboolture", "Morayfield", "North Lakes", "Narangba", "Petrie",
    "Bray Park", "Deception Bay", "Banksia Beach", "Beachmere", "Bellmere",
    # Brisbane
    "Acacia Ridge", "Archerfield", "Oxley", "Yeronga",
    "Wavell Heights", "Zillmere",
    # Sunshine Coast
    "Nambour", "Bli Bli",
    # Toowoomba
    "Toowoomba", "Harristown",
    # Townsville
    "Townsville", "Bohle Plains",
    # Mackay
    "Ooralea", "Andergrove",
    # Rockhampton
    "Berserker", "Norman Gardens", "Park Avenue", "Allenstown",
    # Bundaberg / Fraser Coast / Gladstone
    "Bargara", "Walkervale", "Avenell Heights", "Clinton",
}

DEFAULT_ZONE = {
    "council": "Unknown",
    "zone":    "Low Density Residential",
    "notes":   "No zoning data — scored using defaults.",
}
