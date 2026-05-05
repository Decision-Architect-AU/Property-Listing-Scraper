"""
regions.py — Suburb knowledge base
Edit this file to add/update regions, zoning, rezone potential, and Fast 50 lists.
"""

# ── Zoning data ───────────────────────────────────────────────────────────────
ZONING: dict[str, dict] = {
    # Logan City Council
    "Woodridge":         {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",       "notes": "Train station precinct. Centre zone near Woodridge station. High MDR potential."},
    "Kingston":          {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",       "notes": "Urban core of Logan. Centre zone, MDR pockets near transit."},
    "Logan Central":     {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",       "notes": "Logan CBD fringe. Centre zone, high MDR potential."},
    "Slacks Creek":      {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established suburb. Some MDR pockets near main roads."},
    "Marsden":           {"council": "Logan City Council", "zone": "Low Density Res / MDR",               "notes": "Infill suburb. MDR zoning along key corridors."},
    "Loganholme":        {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Growth corridor near Pacific Motorway. Stable LDR."},
    "Springwood":        {"council": "Logan City Council", "zone": "Low Density Res / Mixed Use",         "notes": "Major commercial hub. MDR and mixed use pockets."},
    "Shailer Park":      {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established suburb near Springwood. Stable LDR."},
    "Meadowbrook":       {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Near Logan Hospital and TAFE. Rental demand high."},
    "Logan Reserve":     {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",   "notes": "Outer growth corridor south of Logan. New estates."},
    "Waterford West":    {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established suburb. Stable LDR. Some infill."},
    "Waterford":         {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Near Beenleigh. Some MDR along main roads."},
    "Crestmead":         {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Growth suburb. Industrial fringe. Rental demand."},
    "Rochedale South":   {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Near Rochedale corridor. Stable established suburb."},
    "Cornubia":          {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established suburb. Stable. Some large blocks."},
    "Tanah Merah":       {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established suburb. Stable. Some large blocks."},
    "Daisy Hill":        {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established. Near Springwood. Stable LDR."},
    "Underwood":         {"council": "Logan City Council", "zone": "Low Density Res / Mixed Use",         "notes": "Corridor suburb. Some mixed-use and MDR pockets."},
    "Holmview":          {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",   "notes": "Growth corridor suburb. New estates."},
    "Bethania":          {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Near Beenleigh. Train station suburb. Rental demand."},
    "Edens Landing":     {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Near Holmview. Stable LDR."},
    "Heritage Park":     {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Outer growth suburb. New estates."},
    "Park Ridge":        {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",   "notes": "Growth corridor. Rural-residential transition."},
    "Regents Park":      {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established suburb. Close to train line."},
    "Hillcrest":         {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Established suburb. Stable LDR."},
    "Browns Plains":     {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",       "notes": "Major retail hub. Some MDR along Grand Plaza corridor."},
    "Bannockburn":       {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Outer suburb. Rural-residential."},
    "Beenleigh":         {"council": "Logan City Council", "zone": "Low Density Res / Centre Zone",       "notes": "Major centre zone. Train line. ShapingSEQ growth node. High MDR potential."},
    "Eagleby":           {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Near Beenleigh CBD. Affordable. Rental demand."},
    "Bahrs Scrub":       {"council": "Logan City Council", "zone": "Low Density Res / Growth Corridor",   "notes": "Growth corridor. New estates near Beenleigh."},
    "Greenbank":         {"council": "Logan City Council", "zone": "Low Density Residential",             "notes": "Outer growth corridor. Rural-residential transition."},
    "New Beith":         {"council": "Logan City Council", "zone": "Low Density Res / Rural Residential", "notes": "Rural-residential. Large blocks. Lifestyle buyers."},
    "Jimboomba":         {"council": "Logan City Council", "zone": "Low Density Res / Rural Residential", "notes": "Outer growth town. Rural-residential. Large blocks."},
    "Mundoolun":         {"council": "Logan City Council", "zone": "Rural",                               "notes": "Rural. Large acreage."},
    # Ipswich City Council
    "Ipswich":           {"council": "Ipswich City Council", "zone": "Low Density Res / Inner Urban",        "notes": "MDR / Centre Zone potential near CBD. ShapingSEQ corridor."},
    "Leichhardt":        {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Inner suburb adj to Ipswich CBD. Rezone upside likely."},
    "East Ipswich":      {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Heritage & character precinct. Limited rezone but large blocks."},
    "Raceview":          {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Established suburb. Some infill opportunity."},
    "Brassall":          {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Growth suburb west of CBD. Some MDR pockets."},
    "Bellbird Park":     {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Established suburb near Springfield. Stable LDR."},
    "Gailes":            {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Older suburb near Goodna. Some MDR potential."},
    "Redbank Plains":    {"council": "Ipswich City Council", "zone": "Low Density Res / Emerging Community", "notes": "Fast-growing suburb. Some emerging community zones at fringe."},
    "Ripley":            {"council": "Ipswich City Council", "zone": "Emerging Community / PDA",             "notes": "Ripley Valley Priority Development Area. Greenfield master-planned."},
    "Spring Mountain":   {"council": "Ipswich City Council", "zone": "Low Density Res / Growth Corridor",    "notes": "Part of Springfield Lakes PDA. High-growth greenfield."},
    "Springfield":       {"council": "Ipswich City Council", "zone": "Low Density Res / Mixed Use",          "notes": "Springfield Lakes / Orion corridor. Centre zone near retail hub."},
    "Sadliers Crossing": {"council": "Ipswich City Council", "zone": "Low Density Residential",              "notes": "Adj to Ipswich CBD. Emerging community fringe."},
    # Moreton Bay Regional Council
    "Caboolture":        {"council": "Moreton Bay Regional", "zone": "Low Density Res / Centre Zone",  "notes": "Centre zone near CBD. MDR in inner ring. ShapingSEQ growth node."},
    "Morayfield":        {"council": "Moreton Bay Regional", "zone": "Low Density Res / MDR",          "notes": "Fast 50 suburb. Active MDR & Centre zone pockets. High growth."},
}

# ── Rezone potential ─────────────────────────────────────────────────────────
REZONE_POTENTIAL: dict[str, str] = {
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
    "Ipswich":           "HIGH — Inner city, ShapingSEQ corridor",
    "Leichhardt":        "HIGH — Adj CBD, character precinct",
    "East Ipswich":      "MEDIUM — Large blocks, heritage area",
    "Sadliers Crossing": "HIGH — Fringe CBD, emerging zone",
    "Redbank Plains":    "MEDIUM — Growing, emerging community",
    "Morayfield":        "HIGH — Fast 50, MDR pockets, active growth",
    "Caboolture":        "HIGH — Centre zone, MDR ring, ShapingSEQ node",
}

# ── Scoring sets ─────────────────────────────────────────────────────────────
HIGH_REZONE = {
    "Woodridge", "Kingston", "Logan Central", "Beenleigh",
    "Ipswich", "Leichhardt", "Sadliers Crossing", "Morayfield", "Caboolture",
}

MEDIUM_REZONE = {
    "Browns Plains", "Springwood", "Marsden", "Slacks Creek",
    "Meadowbrook", "Bethania", "Regents Park", "Underwood",
    "East Ipswich", "Redbank Plains", "Brassall",
}

# Suburbs with strong rental demand near hospitals / TAFE / employment hubs
CASHFLOW_DEMAND_SUBURBS = {
    "Meadowbrook", "Logan Central", "Woodridge", "Kingston",
}

FAST_50 = {"Morayfield", "Caboolture"}

DEFAULT_ZONE = {
    "council": "Unknown",
    "zone":    "Low Density Residential",
    "notes":   "No zoning data — scored using defaults.",
}
