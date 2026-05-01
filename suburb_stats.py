"""
suburb_stats.py — Suburb statistics lookup from suburbs_stats_extracted.xlsx

Provides sqm_rating, vacancy rate, median house/unit rent and price.
Data sourced from SQM Research — Oct 2025 figures used where available.

Column index reference (0-based):
  0  Rating_Oct24    1  Rating_Oct25
  2  Vacancy_Oct24   3  Vacancy_Oct25_pct
  4  Rent_House24_pw 5  Rent_House25_pw
  6  Rent_Unit24_pw  7  Rent_Unit25_pw
  8  Yield_House24   9  Yield_House25_pct
  10 Yield_Unit24    11 Yield_Unit25_pct
  12 Median_House18  13 Median_House24  14 Median_House25
  15 Median_Unit18   16 Median_Unit24   17 Median_Unit25
  18 Postcode        19 Suburb          20 State
"""

from pathlib import Path

_STATS_FILE = Path(__file__).parent / "suburbs_stats_extracted.xlsx"
_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache

    if not _STATS_FILE.exists():
        _cache = {}
        return _cache

    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(_STATS_FILE), read_only=True, data_only=True)
        ws = wb.active
    except Exception:
        _cache = {}
        return _cache

    data: dict = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or not row or not row[19]:  # skip header + empty rows
            continue
        suburb_raw = str(row[19]).strip()
        state      = str(row[20] or '').strip().upper()
        postcode   = str(row[18] or '').strip()

        entry = {
            'sqm_rating':      _safe(row[1]),
            'vacancy_pct':     _safe(row[3]),
            'rent_house_pw':   _safe_int(row[5]),
            'rent_unit_pw':    _safe_int(row[7]),
            'yield_house_pct': _safe(row[9]),
            'yield_unit_pct':  _safe(row[11]),
            'median_house':    _safe_int(row[14]),
            'median_unit':     _safe_int(row[17]),
            'postcode':        postcode,
            'state':           state,
        }

        key_full  = (suburb_raw.upper(), state)
        key_alone = suburb_raw.upper()
        data[key_full] = entry
        # Title-case version so "Ipswich" matches "IPSWICH"
        data[(suburb_raw.title(), state)] = entry
        if key_alone not in data:
            data[key_alone] = entry

    _cache = data
    return _cache


def _safe(v) -> float:
    try:
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0


def _safe_int(v) -> int:
    try:
        return int(v) if v is not None else 0
    except Exception:
        return 0


def lookup(suburb: str, state: str = '') -> dict:
    """
    Look up suburb stats by name (case-insensitive).
    Provide state ('QLD', 'NSW', etc.) to disambiguate suburbs that exist in
    multiple states. Returns empty dict if suburb not found.

    Keys returned:
      sqm_rating, vacancy_pct, rent_house_pw, rent_unit_pw,
      yield_house_pct, yield_unit_pct, median_house, median_unit,
      postcode, state
    """
    data  = _load()
    upper = suburb.strip().upper()
    state_up = state.strip().upper()

    if state_up:
        entry = data.get((upper, state_up))
        if entry:
            return entry

    return data.get(upper, {})


def median_rent_pw(suburb: str, is_house: bool, state: str = '') -> int:
    """Return the latest median weekly rent for a house or unit in this suburb."""
    s = lookup(suburb, state)
    if not s:
        return 0
    return s['rent_house_pw'] if is_house else s['rent_unit_pw']


def median_price(suburb: str, is_house: bool, state: str = '') -> int:
    """Return the latest median sale price for a house or unit in this suburb."""
    s = lookup(suburb, state)
    if not s:
        return 0
    return s['median_house'] if is_house else s['median_unit']
