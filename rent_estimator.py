"""
rent_estimator.py — Extract rental income from Domain listing descriptions.

Handles:
  - Direct weekly:   "$450/week", "$450 per week", "$450pw", "$450 p.w."
  - Direct annual:   "$23,400 p.a.", "$23,400 per annum", "$23,400/year"
  - Multi-unit desc: "2 x 2 bedroom @ $380/wk each" → 2 × $380 = $760/wk
  - Multiple units:  "$380/wk + $420/wk" → $800/wk total
  - Context phrases: "currently rented at $X", "returning $X per week"

Falls back to suburb median rent if description has no rent data.
"""

import re
from suburb_stats import lookup as stats_lookup


# ── Regex patterns ────────────────────────────────────────────────────────────

# Weekly rent: $450/week, $450 per week, $450pw, $450 p.w., 450 per week
_RE_PW = re.compile(
    r'\$\s*([\d,]+)\s*(?:per\s+week|/\s*week|\bpw\b|p\.w\.)'
    r'|(?<!\d)([\d,]+)\s*(?:per\s+week|/\s*week|\bpw\b|p\.w\.)',
    re.IGNORECASE,
)

# Annual rent: $23,400 pa, $23,400 per annum, $23,400/year, $23,400 p.a.
_RE_PA = re.compile(
    r'\$\s*([\d,]+)\s*(?:per\s+(?:annum|year)|/\s*(?:year|annum)|\bpa\b|p\.a\.)'
    r'|(?<!\d)([\d,]+)\s*(?:per\s+(?:annum|year)|/\s*(?:year|annum)|\bpa\b|p\.a\.)',
    re.IGNORECASE,
)

# Word → digit mapping for multi-unit patterns
_WORD_NUMS = {
    'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
}

def _normalise_word_nums(text: str) -> str:
    """Replace written numbers with digits so regex can match them."""
    for word, digit in _WORD_NUMS.items():
        text = re.sub(rf'\b{word}\b', digit, text, flags=re.IGNORECASE)
    return text

# Multi-unit: "2 x 2 bedroom @ $380/week each" or "3 x 2br returning $350pw"
_RE_UNITS = re.compile(
    r'(\d{1,2})\s*[xX×]\s*(\d)\s*(?:bed(?:room)?s?|br)'
    r'[^$\n]{0,60}?\$\s*([\d,]+)\s*(?:per\s+week|/\s*week|\bpw\b|p\.w\.|each)?',
    re.IGNORECASE,
)

# Individual unit amounts for summing: "unit 1: $350pw ... unit 2: $380pw"
_RE_UNIT_INDIVIDUAL = re.compile(
    r'(?:unit|tenancy|dwelling|property)\s*\d*\s*[:\-]?\s*\$\s*([\d,]+)\s*'
    r'(?:per\s+week|/\s*week|\bpw\b|p\.w\.)',
    re.IGNORECASE,
)


def _num(s: str) -> float:
    """Strip commas/$ and parse float."""
    return float(re.sub(r'[,$]', '', str(s))) if s else 0.0


def _pw_amounts(text: str) -> list[float]:
    vals = []
    for m in _RE_PW.finditer(text):
        raw = m.group(1) or m.group(2) or ''
        v   = _num(raw)
        if 80 < v < 10_000:
            vals.append(v)
    return vals


def _pa_amounts(text: str) -> list[float]:
    vals = []
    for m in _RE_PA.finditer(text):
        raw = m.group(1) or m.group(2) or ''
        v   = _num(raw)
        if 4_000 < v < 1_000_000:
            vals.append(v)
    return vals


# ── Main estimator ────────────────────────────────────────────────────────────

def estimate_rent(
    desc: str,
    beds: str = '',
    ptype: str = '',
    suburb: str = '',
    state: str = '',
) -> dict:
    """
    Extract rental income from a listing description.

    Returns dict:
      annual_rent:     int  — total annual rent (0 = unknown)
      weekly_rent:     int  — total weekly rent (0 = unknown)
      assumptions:     str  — human-readable breakdown, e.g. "2 x 2bed @ $380/wk"
      rent_source:     str  — 'description' | 'suburb_median' | 'none'
    """
    text = _normalise_word_nums((desc or '').lower())

    # 1. Multi-unit breakdown: "N x M bed @ $X/wk"
    unit_items = []
    for m in _RE_UNITS.finditer(text):
        count = int(m.group(1))
        beds_ = int(m.group(2))
        rate  = _num(m.group(3))
        if 1 <= count <= 50 and 80 < rate < 10_000:
            unit_items.append((count, beds_, rate))

    if unit_items:
        total_pw  = sum(c * r for c, _, r in unit_items)
        parts_str = ' + '.join(f"{c} x {b}bed @ ${r:.0f}/wk" for c, b, r in unit_items)
        return {
            'annual_rent':  int(total_pw * 52),
            'weekly_rent':  int(total_pw),
            'assumptions':  parts_str,
            'rent_source':  'description',
        }

    # 2. Individual unit amounts listed separately: "Unit 1: $350pw, Unit 2: $380pw"
    indiv = [_num(m.group(1)) for m in _RE_UNIT_INDIVIDUAL.finditer(text)
             if 80 < _num(m.group(1)) < 10_000]
    if len(indiv) > 1:
        total_pw = sum(indiv)
        parts_str = ' + '.join(f'${v:.0f}' for v in sorted(indiv)) + '/wk'
        return {
            'annual_rent':  int(total_pw * 52),
            'weekly_rent':  int(total_pw),
            'assumptions':  parts_str,
            'rent_source':  'description',
        }

    # 3. Annual amount explicit
    pa = _pa_amounts(text)
    if pa:
        annual = int(pa[0])
        beds_n = int(beds) if str(beds).isdigit() else 0
        label  = f"{beds_n}bed " if beds_n else ''
        return {
            'annual_rent':  annual,
            'weekly_rent':  int(annual / 52),
            'assumptions':  f"{label}${annual:,}/yr (desc)",
            'rent_source':  'description',
        }

    # 4. Weekly amounts
    pw = _pw_amounts(text)
    if pw:
        # Multiple distinct values → could be several units; sum them
        unique = sorted(set(round(v) for v in pw))
        if len(unique) > 1:
            total_pw  = sum(unique)
            parts_str = ' + '.join(f'${v}' for v in unique) + '/wk'
        else:
            total_pw  = unique[0]
            beds_n    = int(beds) if str(beds).isdigit() else 0
            label     = f"{beds_n}bed " if beds_n else ''
            parts_str = f"{label}${int(total_pw)}/wk (desc)"
        return {
            'annual_rent':  int(total_pw * 52),
            'weekly_rent':  int(total_pw),
            'assumptions':  parts_str,
            'rent_source':  'description',
        }

    # 5. Fallback to suburb median rent
    if suburb:
        is_house = 'house' in (ptype or '').lower() or 'villa' in (ptype or '').lower()
        stats    = stats_lookup(suburb, state)
        med_pw   = stats.get('rent_house_pw', 0) if is_house else stats.get('rent_unit_pw', 0)
        if not med_pw:
            med_pw = stats.get('rent_house_pw', 0) or stats.get('rent_unit_pw', 0)
        if med_pw:
            kind = 'House' if is_house else 'Unit'
            return {
                'annual_rent':  int(med_pw * 52),
                'weekly_rent':  int(med_pw),
                'assumptions':  f"Est. suburb median ({kind}: ${med_pw}/wk)",
                'rent_source':  'suburb_median',
            }

    return {'annual_rent': 0, 'weekly_rent': 0, 'assumptions': '', 'rent_source': 'none'}
