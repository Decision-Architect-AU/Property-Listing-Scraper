"""
regions.py — Suburb knowledge base
Edit this file to add/update regions, zoning, rezone potential, and Fast 50 lists.

Fast 50 covers ~50 high-growth QLD suburbs spanning SEQ corridors (Logan, Ipswich,
Moreton Bay, Brisbane CC) and regional hubs (Toowoomba, Rockhampton, Bundaberg,
Wide Bay, Sunshine Coast, North QLD, Gladstone). Sources: SPI Fast 50 2025/2026,
REIQ, OpenAgent, and research on ShapingSEQ growth nodes.
"""

# ── Zoning data ───────────────────────────────────────────────────────────────
ZONING: dict[str, dict] = {

    # ── Logan City Council ────────────────────────────────────────────────────
    "Woodridge":         {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",        "notes": "Train station precinct. Centre zone near Woodridge station. High MDR potential. Fast 50."},
    "Kingston":          {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",        "notes": "Urban core of Logan. Centre zone, MDR pockets near transit. Fast 50."},
    "Logan Central":     {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",        "notes": "Logan CBD fringe. Centre zone, high MDR potential. SPI Fast 50 2026."},
    "Slacks Creek":      {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Some MDR pockets near main roads."},
    "Marsden":           {"council": "Logan City Council", "zone": "Low Density Res / MDR",                "notes": "Infill suburb. MDR zoning along key corridors. Fast 50."},
    "Loganholme":        {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Growth corridor near Pacific Motorway. Stable LDR."},
    "Springwood":        {"council": "Logan City Council", "zone": "Low Density Res / Mixed Use",          "notes": "Major commercial hub. MDR and mixed use pockets."},
    "Shailer Park":      {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established suburb near Springwood. Stable LDR."},
    "Meadowbrook":       {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Near Logan Hospital and TAFE. Rental demand high."},
    "Logan Reserve":     {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",    "notes": "Outer growth corridor south of Logan. New estates."},
    "Waterford West":    {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Stable LDR. Some infill."},
    "Waterford":         {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Near Beenleigh. Some MDR along main roads."},
    "Crestmead":         {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Growth suburb. Industrial fringe. Rental demand."},
    "Rochedale South":   {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Near Rochedale corridor. Stable established suburb."},
    "Cornubia":          {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Stable. Some large blocks."},
    "Tanah Merah":       {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Stable. Some large blocks."},
    "Daisy Hill":        {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established. Near Springwood. Stable LDR."},
    "Underwood":         {"council": "Logan City Council", "zone": "Low Density Res / Mixed Use",          "notes": "Corridor suburb. Some mixed-use and MDR pockets."},
    "Holmview":          {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",    "notes": "Growth corridor suburb. New estates."},
    "Bethania":          {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Near Beenleigh. Train station suburb. Rental demand."},
    "Edens Landing":     {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Near Holmview. Stable LDR."},
    "Heritage Park":     {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Outer growth suburb. New estates."},
    "Park Ridge":        {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",    "notes": "Growth corridor. Rural-residential transition."},
    "Regents Park":      {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Close to train line."},
    "Hillcrest":         {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Stable LDR."},
    "Browns Plains":     {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",        "notes": "Major retail hub. Some MDR along Grand Plaza corridor. Fast 50."},
    "Bannockburn":       {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Outer suburb. Rural-residential."},
    "Beenleigh":         {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",        "notes": "Major centre zone. Train line. ShapingSEQ growth node. High MDR potential. Fast 50."},
    "Eagleby":           {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Near Beenleigh CBD. Affordable. Rental demand."},
    "Bahrs Scrub":       {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",    "notes": "Growth corridor. New estates near Beenleigh."},
    "Greenbank":         {"council": "Logan City Council", "zone": "Low Density Residential",              "notes": "Outer growth corridor. Rural-residential transition."},
    "New Beith":         {"council": "Logan City Council", "zone": "Low Density Res / Rural Residential",  "notes": "Rural-residential. Large blocks. Lifestyle buyers."},
    "Jimboomba":         {"council": "Logan City Council", "zone": "Low Density Res / Rural Residential",  "notes": "Outer growth town. Rural-residential. Large blocks."},
    "Mundoolun":         {"council": "Logan City Council", "zone": "Rural",                                "notes": "Rural. Large acreage."},

    # ── Ipswich City Council ──────────────────────────────────────────────────
    "Ipswich":           {"council": "Ipswich City Council", "zone": "Low Density Res / Inner Urban",         "notes": "MDR / Centre Zone potential near CBD. ShapingSEQ corridor. Fast 50."},
    "Leichhardt":        {"council": "Ipswich City Council", "zone": "Low Density Residential",               "notes": "Inner suburb adj to Ipswich CBD. Rezone upside likely. SPI Fast 50 2025. Near Wulkuraka Station."},
    "East Ipswich":      {"council": "Ipswich City Council", "zone": "Low Density Residential",               "notes": "Heritage & character precinct. Limited rezone but large blocks."},
    "Raceview":          {"council": "Ipswich City Council", "zone": "Low Density Residential",               "notes": "Established suburb. Some infill opportunity."},
    "Brassall":          {"council": "Ipswich City Council", "zone": "Low Density Residential",               "notes": "Growth suburb west of CBD. Some MDR pockets."},
    "Bellbird Park":     {"council": "Ipswich City Council", "zone": "Low Density Residential",               "notes": "Established suburb near Springfield. Stable LDR."},
    "Gailes":            {"council": "Ipswich City Council", "zone": "Low Density Residential",               "notes": "Older suburb near Goodna. Some MDR potential."},
    "Redbank Plains":    {"council": "Ipswich City Council", "zone": "Low Density Res / Emerging Community",  "notes": "Fast-growing suburb. Emerging community zones at fringe. SPI Fast 50. Strong demand."},
    "Ripley":            {"council": "Ipswich City Council", "zone": "Emerging Community / PDA",              "notes": "Ripley Valley Priority Development Area. Greenfield master-planned. Fast 50."},
    "Spring Mountain":   {"council": "Ipswich City Council", "zone": "Low Density Res / Growth Corridor",     "notes": "Part of Springfield Lakes PDA. High-growth greenfield."},
    "Springfield":       {"council": "Ipswich City Council", "zone": "Low Density Res / Mixed Use",           "notes": "Springfield Lakes / Orion corridor. Centre zone near retail hub. Fast 50."},
    "Sadliers Crossing": {"council": "Ipswich City Council", "zone": "Low Density Residential",               "notes": "Adj to Ipswich CBD. Emerging community fringe."},

    # ── Moreton Bay Regional Council ──────────────────────────────────────────
    "Caboolture":        {"council": "Moreton Bay Regional", "zone": "Low Density Res / Centre Zone",    "notes": "Centre zone near CBD. MDR in inner ring. ShapingSEQ growth node. SPI Fast 50."},
    "Morayfield":        {"council": "Moreton Bay Regional", "zone": "Low Density Res / MDR",            "notes": "Active MDR & Centre zone pockets. High growth. SPI Fast 50."},
    "Bray Park":         {"council": "Moreton Bay Regional", "zone": "Low Density Res / Centre Zone",    "notes": "Established suburb near Strathpine. Centre zone corridors. SPI Fast 50 2026."},
    "Griffin":           {"council": "Moreton Bay Regional", "zone": "Low Density Res / Growth Corridor","notes": "New master-planned suburb. Rail access via Petrie. Fast-growing. SPI Fast 50 2026."},
    "Petrie":            {"council": "Moreton Bay Regional", "zone": "Low Density Res / Centre Zone",    "notes": "Train station suburb. University campus (UniSC). Centre zone. SPI Fast 50 2026."},
    "Burpengary":        {"council": "Moreton Bay Regional", "zone": "Low Density Res / Growth Corridor","notes": "Fast-growing corridor north of Brisbane. Affordable. Strong capital growth."},
    "Narangba":          {"council": "Moreton Bay Regional", "zone": "Low Density Residential",          "notes": "Train station. Commuter belt suburb. Affordable LDR. Growing rental demand."},
    "Kallangur":         {"council": "Moreton Bay Regional", "zone": "Low Density Res / MDR",            "notes": "Close to Petrie. Train access. MDR pockets. Growth corridor affordability."},
    "North Lakes":       {"council": "Moreton Bay Regional", "zone": "Low Density Res / Mixed Use",      "notes": "Established master-planned community. Major commercial hub. Strong rental demand."},
    "Mango Hill":        {"council": "Moreton Bay Regional", "zone": "Low Density Residential",          "notes": "Near North Lakes. Fast-growing estates. Good rental demand and infrastructure."},

    # ── Brisbane City Council ─────────────────────────────────────────────────
    "Wavell Heights":    {"council": "Brisbane City Council", "zone": "Low Density Res / Neighbourhood Plan","notes": "Established north Brisbane suburb. SPI Fast 50 2026. Character housing, near Chermside hub."},
    "Herston":           {"council": "Brisbane City Council", "zone": "Low Density Res / Inner Urban",       "notes": "Adjacent to Royal Brisbane Hospital precinct. SPI Fast 50 2026. Strong medical rental demand."},
    "Yeronga":           {"council": "Brisbane City Council", "zone": "Low Density Res / Inner Urban",       "notes": "South Brisbane riverfront suburb. SPI Fast 50 2026. Established, near UQ. MDR corridors."},
    "Oxley":             {"council": "Brisbane City Council", "zone": "Low Density Residential",             "notes": "Train station suburb south Brisbane. Established. Affordable entry. Infill potential."},
    "Acacia Ridge":      {"council": "Brisbane City Council", "zone": "Low Density Res / Industrial Fringe", "notes": "Affordable south Brisbane. Near industrial employment hubs. Rental demand."},
    "Rocklea":           {"council": "Brisbane City Council", "zone": "Low Density Res / Mixed Use",         "notes": "South Brisbane near markets and industrial belt. Affordable. Some MDR potential."},
    "Zillmere":          {"council": "Brisbane City Council", "zone": "Low Density Res / Centre Zone",       "notes": "North Brisbane. Train station. Affordable entry. Centre zone. Good rental yield."},
    "Chermside":         {"council": "Brisbane City Council", "zone": "Low Density Res / Centre Zone",       "notes": "Major north Brisbane hub near Westfield. MDR and mixed use. Strong rental demand."},

    # ── Toowoomba / Somerset / Lockyer Valley ─────────────────────────────────
    "Highfields":        {"council": "Toowoomba Regional Council", "zone": "Low Density Res / Growth Corridor","notes": "North Toowoomba growth corridor. SPI Fast 50 2026. New estates, strong population growth."},
    "Toowoomba":         {"council": "Toowoomba Regional Council", "zone": "Low Density Res / Centre Zone",   "notes": "Darling Downs regional city. MDR/Centre zone in CBD fringe. Strong employment base."},
    "Lowood":            {"council": "Somerset Regional Council",  "zone": "Low Density Residential",         "notes": "Somerset LGA. SPI Fast 50 2026. Affordable commuter town on Brisbane Valley Hwy. Growth."},
    "Plainland":         {"council": "Lockyer Valley Regional Council", "zone": "Low Density Res / Growth Corridor","notes": "Lockyer Valley. SPI Fast 50 2026. Rapid growth, Warrego Hwy access, affordable entry."},

    # ── Rockhampton Regional Council ──────────────────────────────────────────
    "Park Avenue":       {"council": "Rockhampton Regional Council", "zone": "Low Density Residential",        "notes": "North Rockhampton. SPI Fast 50 2026. +29% annual growth. Established, affordable."},
    "Koongal":           {"council": "Rockhampton Regional Council", "zone": "Low Density Residential",        "notes": "North Rockhampton. SPI Fast 50 2026. +34% annual growth. Strong rental demand."},
    "Frenchville":       {"council": "Rockhampton Regional Council", "zone": "Low Density Residential",        "notes": "Rockhampton suburb. SPI Fast 50 2025/2026. Median $529K, +15% annual growth."},
    "Gracemere":         {"council": "Rockhampton Regional Council", "zone": "Low Density Res / Growth Corridor","notes": "Rockhampton satellite town. Industrial/agribusiness employment nearby. Growth corridor."},
    "Norman Gardens":    {"council": "Rockhampton Regional Council", "zone": "Low Density Residential",        "notes": "Popular Rockhampton suburb. Established. Strong rental demand near CBD."},

    # ── Bundaberg Regional Council ────────────────────────────────────────────
    "Kepnock":           {"council": "Bundaberg Regional Council", "zone": "Low Density Residential",   "notes": "Bundaberg suburb. SPI Fast 50 2025/2026. Median $500K, +11.7% annual growth. Affordable."},
    "Avenell Heights":   {"council": "Bundaberg Regional Council", "zone": "Low Density Residential",   "notes": "Bundaberg established suburb. Good rental yield. Near CBD and services."},
    "Walkervale":        {"council": "Bundaberg Regional Council", "zone": "Low Density Residential",   "notes": "Bundaberg. Affordable investment suburb. Near employment and schools."},

    # ── Wide Bay / Fraser Coast / South Burnett ───────────────────────────────
    "Kingaroy":          {"council": "South Burnett Regional Council", "zone": "Low Density Res / Centre Zone","notes": "South Burnett commercial hub. SPI Fast 50. +27.3% annual growth, +94.7% five-year. Centre zone."},
    "Maryborough":       {"council": "Fraser Coast Regional Council", "zone": "Low Density Res / Centre Zone", "notes": "Fraser Coast regional centre. Heritage city. Growing investment interest. Affordable."},
    "Hervey Bay":        {"council": "Fraser Coast Regional Council", "zone": "Low Density Res / Coastal",     "notes": "Fast-growing coastal city. Retiree and tourist demand. Affordable entry. Strong rental yield."},

    # ── Sunshine Coast Regional Council ───────────────────────────────────────
    "Nambour":           {"council": "Sunshine Coast Regional Council", "zone": "Low Density Res / Centre Zone","notes": "Sunshine Coast hinterland hub. Affordable entry. Gentrifying. Strong growth potential."},
    "Caloundra":         {"council": "Sunshine Coast Regional Council", "zone": "Low Density Res / Coastal",   "notes": "Southern Sunshine Coast. Coastal lifestyle suburb. Strong rental demand. Solid growth."},

    # ── Townsville / Mackay ───────────────────────────────────────────────────
    "Townsville":        {"council": "Townsville City Council",  "zone": "Low Density Res / Centre Zone",  "notes": "NQ regional capital. Defence, healthcare employment. Centre zone near CBD. High yield."},
    "Bohle Plains":      {"council": "Townsville City Council",  "zone": "Low Density Res / Growth Corridor","notes": "North Townsville growth corridor. New estates. Affordable. Strong rental demand."},
    "Mackay":            {"council": "Mackay Regional Council",  "zone": "Low Density Res / Centre Zone",  "notes": "Central QLD resources hub. Mining cycle employment. High rental yield potential."},
    "Ooralea":           {"council": "Mackay Regional Council",  "zone": "Low Density Residential",        "notes": "Mackay suburb. Established. Affordable. Good yield near employment hubs."},

    # ── Gladstone Regional Council ────────────────────────────────────────────
    "Gladstone":         {"council": "Gladstone Regional Council", "zone": "Low Density Res / Centre Zone","notes": "Industrial port city. LNG/resources employment. High rental demand and yield potential."},
}


# ── Rezone potential ──────────────────────────────────────────────────────────
REZONE_POTENTIAL: dict[str, str] = {
    # Logan
    "Woodridge":         "HIGH — Centre zone, MDR ring, transit precinct",
    "Kingston":          "HIGH — Urban core, centre zone, MDR pockets",
    "Logan Central":     "HIGH — Logan CBD fringe, centre zone",
    "Beenleigh":         "HIGH — Centre zone, train line, ShapingSEQ growth node",
    "Browns Plains":     "MEDIUM-HIGH — Centre zone near Grand Plaza",
    "Springwood":        "MEDIUM-HIGH — Mixed use, MDR pockets, commercial hub",
    "Marsden":           "MEDIUM — MDR corridors, infill opportunity",
    "Slacks Creek":      "MEDIUM — MDR pockets along main roads",
    "Meadowbrook":       "MEDIUM — Near Logan Hospital, rental demand",
    "Bethania":          "MEDIUM — Train station suburb, rental demand",
    "Regents Park":      "MEDIUM — Close to train line, infill",
    "Underwood":         "MEDIUM — Mixed use and MDR pockets",
    "Loganholme":        "LOW-MEDIUM — Growth corridor, stable LDR",
    "Shailer Park":      "LOW-MEDIUM — Established, near Springwood",
    "Logan Reserve":     "LOW-MEDIUM — Growth corridor, new estates",
    "Waterford West":    "LOW-MEDIUM — Established, some infill",
    "Crestmead":         "LOW-MEDIUM — Growth suburb, rental demand",
    "Rochedale South":   "LOW — Established, stable",
    "Greenbank":         "LOW — Outer rural-res",
    "New Beith":         "LOW — Rural-residential, lifestyle",
    "Jimboomba":         "LOW — Outer rural-res, large blocks",
    "Eagleby":           "LOW-MEDIUM — Near Beenleigh, affordable",
    "Bahrs Scrub":       "LOW-MEDIUM — Growth corridor near Beenleigh",
    "Park Ridge":        "LOW-MEDIUM — Growth corridor",
    # Ipswich
    "Ipswich":           "HIGH — Inner city, ShapingSEQ corridor",
    "Leichhardt":        "HIGH — Adj CBD, character precinct, SPI Fast 50",
    "East Ipswich":      "MEDIUM — Large blocks, heritage area",
    "Sadliers Crossing": "HIGH — Fringe CBD, emerging zone",
    "Redbank Plains":    "MEDIUM — Growing, emerging community",
    "Brassall":          "MEDIUM — MDR pockets, growing suburb",
    "Springfield":       "MEDIUM-HIGH — Mixed use, centre zone, fast growth corridor",
    "Ripley":            "MEDIUM — PDA greenfield, strong long-term potential",
    # Moreton Bay
    "Morayfield":        "HIGH — Fast 50, MDR pockets, active growth",
    "Caboolture":        "HIGH — Centre zone, MDR ring, ShapingSEQ node",
    "Bray Park":         "HIGH — Centre zone corridors, established, transit precinct",
    "Petrie":            "HIGH — University precinct, centre zone, train station, MDR",
    "Burpengary":        "MEDIUM-HIGH — Fast growth corridor, MDR pockets forming",
    "Kallangur":         "MEDIUM — MDR pockets, train access, growth corridor",
    "Griffin":           "MEDIUM — Growth corridor, new master-planned estate",
    "Narangba":          "MEDIUM — Train station, commuter belt, infill potential",
    "North Lakes":       "MEDIUM — Mixed use pockets, commercial hub",
    "Mango Hill":        "LOW-MEDIUM — Established estates, growth area",
    # Brisbane CC
    "Wavell Heights":    "MEDIUM-HIGH — Neighbourhood plan, inner north, character housing ripe for infill",
    "Herston":           "HIGH — Inner Brisbane, hospital precinct, strong MDR potential",
    "Yeronga":           "HIGH — Inner Brisbane south, riverfront, MDR/mixed use corridors",
    "Zillmere":          "HIGH — Centre zone, train station, affordable inner north",
    "Chermside":         "HIGH — Centre zone, Westfield precinct, MDR and mixed use",
    "Oxley":             "MEDIUM — Train station suburb, infill potential south Brisbane",
    "Acacia Ridge":      "LOW-MEDIUM — Affordable, industrial fringe, some MDR pockets",
    "Rocklea":           "MEDIUM — Mixed use near markets, some MDR potential",
    # Toowoomba / Lockyer / Somerset
    "Highfields":        "MEDIUM-HIGH — Growth corridor north Toowoomba, fast expanding",
    "Toowoomba":         "HIGH — Regional city centre zone, MDR corridors, strong employment base",
    "Plainland":         "MEDIUM-HIGH — Lockyer Valley fast growth, freeway access, rezone trajectory",
    "Lowood":            "MEDIUM — Somerset growth town, commuter belt, affordable",
    # Rockhampton
    "Park Avenue":       "MEDIUM — SPI Fast 50, established suburb, strong growth momentum",
    "Koongal":           "MEDIUM — SPI Fast 50, strong annual growth, established suburb",
    "Frenchville":       "MEDIUM — SPI Fast 50, established Rockhampton suburb",
    "Gracemere":         "MEDIUM-HIGH — Growth corridor, industrial employment nearby, satellite town",
    "Norman Gardens":    "MEDIUM — Established, strong rental demand, near Rockhampton CBD",
    # Bundaberg
    "Kepnock":           "MEDIUM — SPI Fast 50, affordable family homes, growing demand",
    "Avenell Heights":   "LOW-MEDIUM — Bundaberg established, good yield potential",
    "Walkervale":        "LOW-MEDIUM — Bundaberg affordable, investment grade",
    # Wide Bay / South Burnett
    "Kingaroy":          "HIGH — SPI Fast 50, +27% growth, commercial centre, strong momentum",
    "Maryborough":       "MEDIUM — Regional centre, heritage city, growing investment interest",
    "Hervey Bay":        "MEDIUM-HIGH — Coastal growth city, strong rental demand, affordable entry",
    # Sunshine Coast
    "Nambour":           "MEDIUM-HIGH — Affordable hinterland hub, gentrifying, centre zone",
    "Caloundra":         "MEDIUM — Coastal lifestyle, stable, strong rental demand",
    # North QLD
    "Townsville":        "HIGH — Regional capital centre zone, defence, healthcare, high yield",
    "Bohle Plains":      "MEDIUM — North Townsville growth, new estates, affordable",
    "Mackay":            "HIGH — Resources town centre zone, mining cycle, high yield potential",
    "Ooralea":           "MEDIUM — Mackay suburb, established, good yield near employment",
    # Gladstone
    "Gladstone":         "HIGH — Industrial port city, LNG resources, high rental yield, centre zone",
}


# ── Scoring sets ──────────────────────────────────────────────────────────────

HIGH_REZONE = {
    # Logan
    "Woodridge", "Kingston", "Logan Central", "Beenleigh",
    # Ipswich
    "Ipswich", "Leichhardt", "Sadliers Crossing",
    # Moreton Bay
    "Morayfield", "Caboolture", "Bray Park", "Petrie",
    # Brisbane CC
    "Herston", "Yeronga", "Zillmere", "Chermside",
    # Regional
    "Toowoomba", "Kingaroy", "Townsville", "Mackay", "Gladstone",
}

MEDIUM_REZONE = {
    # Logan
    "Browns Plains", "Springwood", "Marsden", "Slacks Creek",
    "Meadowbrook", "Bethania", "Regents Park", "Underwood",
    # Ipswich
    "East Ipswich", "Redbank Plains", "Brassall", "Springfield", "Ripley",
    # Moreton Bay
    "Burpengary", "Kallangur", "Griffin", "Narangba", "North Lakes",
    # Brisbane CC
    "Wavell Heights", "Oxley", "Rocklea",
    # Toowoomba region
    "Highfields", "Plainland", "Lowood",
    # Rockhampton
    "Gracemere", "Park Avenue", "Koongal", "Frenchville",
    # Wide Bay / Bundaberg
    "Hervey Bay", "Nambour", "Kepnock", "Maryborough",
    # North QLD
    "Bohle Plains",
}

# Suburbs with strong rental demand near hospitals / TAFE / employment hubs
CASHFLOW_DEMAND_SUBURBS = {
    # SEQ
    "Meadowbrook", "Logan Central", "Woodridge", "Kingston",
    "Herston",       # Royal Brisbane Hospital precinct
    "Petrie",        # UniSC campus
    "Springfield",   # Orion retail + hospital
    # Regional
    "Townsville",    # Defence + hospital employment
    "Mackay",        # Resources employment
    "Gladstone",     # LNG / industrial employment
    "Kingaroy",      # Commercial hub employment
}

# ── Fast 50 — 50 high-growth QLD investment suburbs ──────────────────────────
# Sources: SPI Fast 50 2025/2026, ShapingSEQ growth nodes, REIQ hotspots.
# Used in scoring: Fast 50 flag adds +1 to growth score.
FAST_50 = {
    # Moreton Bay (SEQ North)
    "Caboolture", "Morayfield", "Bray Park", "Griffin",
    "Petrie", "Burpengary", "Narangba", "Kallangur",
    "North Lakes", "Mango Hill",
    # Logan (SEQ South)
    "Woodridge", "Kingston", "Logan Central", "Beenleigh",
    "Browns Plains", "Marsden",
    # Ipswich
    "Ipswich", "Leichhardt", "Redbank Plains", "Springfield", "Ripley",
    # Brisbane CC
    "Wavell Heights", "Herston", "Yeronga", "Oxley",
    "Acacia Ridge", "Zillmere", "Chermside",
    # Toowoomba / Lockyer / Somerset
    "Highfields", "Toowoomba", "Lowood", "Plainland",
    # Rockhampton
    "Park Avenue", "Koongal", "Frenchville", "Gracemere", "Norman Gardens",
    # Bundaberg
    "Kepnock", "Avenell Heights", "Walkervale",
    # Wide Bay / South Burnett
    "Kingaroy", "Maryborough", "Hervey Bay",
    # Sunshine Coast
    "Nambour", "Caloundra",
    # North QLD
    "Townsville", "Bohle Plains", "Mackay", "Ooralea",
    # Gladstone
    "Gladstone",
}

DEFAULT_ZONE = {
    "council": "Unknown",
    "zone":    "Low Density Residential",
    "notes":   "No zoning data — scored using defaults.",
}
