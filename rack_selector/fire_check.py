"""
fire_check — fire-protection triage for rack / shelf storage ("do we need in-rack?").

Walks the same decision path an FPE would, in order:
  1. Governing authority + ADOPTED editions (jurisdiction table, FM override)
  2. IFC Ch. 32 high-piled trigger (and FM DS 8-9 scope)
  3. Rack row classification (single / double / multiple) from depth + aisle width
  4. Open rack vs. solid shelving (deck open area, flues maintained, shelf area)
  5. Ceiling-only ESFR feasibility (NFPA 13 Ch. 23 envelope, specific-application
     listings, 36 in. deflector clearance, aisle width)
  6. In-rack conclusion + level planning for listed in-rack options

Every number used here is either sourced (see knowledge_base/) or explicitly labeled as a
value to verify. Conventional (K8.0/K11.2 QR) in-rack vertical spacing is NOT encoded —
it comes from the NFPA 13 Ch. 25 figure for the specific arrangement; pass
--conventional-spacing-ft only if you have read it from the adopted edition.

TRIAGE ONLY — not a sprinkler design. FPE review required for any permit or build.

Usage:
  python -m rack_selector.fire_check --commodity "Class IV" --storage-height 30 \
      --ceiling-height 50 --aisle 5.83 --rack-depth 4 --shelving wire --deck-open 50 \
      --flues-blocked --jurisdiction UT
  python -m rack_selector.fire_check --project projects/25-1642_new_balance_slc.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_DATA = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------------------
# Commodity normalization
# ---------------------------------------------------------------------------------------
# Keys: I, II, III, IV, CUP (cartoned unexpanded Group A), CEP (cartoned expanded),
#       EUP (exposed/uncartoned unexpanded), EEP (exposed/uncartoned expanded)
_COMMODITY_ALIASES = {
    "I": "I", "1": "I", "CLASS I": "I", "CLASS 1": "I",
    "II": "II", "2": "II", "CLASS II": "II", "CLASS 2": "II",
    "III": "III", "3": "III", "CLASS III": "III", "CLASS 3": "III",
    "IV": "IV", "4": "IV", "CLASS IV": "IV", "CLASS 4": "IV",
    "CUP": "CUP", "CARTONED UNEXPANDED": "CUP", "CARTONED UNEXPANDED PLASTIC": "CUP",
    "CARTONED UNEXPANDED GROUP A": "CUP", "CARTONED GROUP A": "CUP",
    "CEP": "CEP", "CARTONED EXPANDED": "CEP", "CARTONED EXPANDED PLASTIC": "CEP",
    "EUP": "EUP", "EXPOSED UNEXPANDED": "EUP", "UNCARTONED UNEXPANDED": "EUP",
    "EXPOSED UNEXPANDED PLASTIC": "EUP",
    "EEP": "EEP", "EXPOSED EXPANDED": "EEP", "UNCARTONED EXPANDED": "EEP",
    "EXPOSED EXPANDED PLASTIC": "EEP",
}
_AMBIGUOUS_PLASTIC = {"GROUP A", "GROUP A PLASTIC", "PLASTIC", "PLASTICS", "A PLASTIC"}

COMMODITY_LABEL = {
    "I": "Class I", "II": "Class II", "III": "Class III", "IV": "Class IV",
    "CUP": "Cartoned unexpanded Group A plastic", "CEP": "Cartoned expanded Group A plastic",
    "EUP": "Exposed (uncartoned) unexpanded Group A plastic",
    "EEP": "Exposed (uncartoned) expanded Group A plastic",
}
GROUP_A = {"CUP", "CEP", "EUP", "EEP"}
UNCARTONED = {"EUP", "EEP"}


def normalize_commodity(text: str) -> tuple[str, Optional[str]]:
    """Return (key, warning). Raises ValueError if unrecognized."""
    t = " ".join((text or "").upper().replace("-", " ").split())
    if t in _COMMODITY_ALIASES:
        return _COMMODITY_ALIASES[t], None
    if t in _AMBIGUOUS_PLASTIC:
        return "CUP", ("Commodity given only as 'Group A plastic' — assumed CARTONED UNEXPANDED. "
                       "Exposed or expanded plastic is far more severe; confirm.")
    raise ValueError(f"Unrecognized commodity {text!r}. Use Class I-IV, CUP, CEP, EUP or EEP.")


# ---------------------------------------------------------------------------------------
# Sourced rule data
# ---------------------------------------------------------------------------------------
# NFPA 13 Ch. 23 ESFR ceiling-only envelope (K-25.2 rows). VERIFY the exact row in the
# adopted edition (Table 23.3.1 in 2019+). CEP / EUP intentionally not encoded.
ESFR_ENVELOPE = {
    "I": (40.0, 45.0), "II": (40.0, 45.0), "III": (40.0, 45.0), "IV": (40.0, 45.0),
    "CUP": (40.0, 45.0),
    "EEP": (35.0, 40.0),  # exposed expanded: K-25.2 @ 60 psi + vertical barriers (2016+)
}
ESFR_ENVELOPE_SOURCE = ("NFPA 13 Ch. 23 ESFR table (K-25.2): Class I-IV & CUP to 40 ft storage / "
                        "45 ft ceiling; EEP to 35/40 ft with vertical barriers. Verify the row in "
                        "the adopted edition.")

# Specific-application / FM-approved ceiling-only options that go beyond the NFPA tables.
# Each is a LISTING condition (AHJ/insurer acceptance required), not NFPA table criteria.
SA_OPTIONS = [
    {
        "name": "Reliable P25 (K25.2 specific application, cULus)",
        "commodities": {"I", "II", "III", "IV", "CUP"},
        "row_types": {"single", "double"},
        "max_storage_ft": 40.0, "max_ceiling_ft": 48.0, "min_aisle_ft": 5.0,
        "fm_only": False,
        "note": "Open-frame single/double-row racks; aisles >= 5 ft. Verify current Reliable bulletin.",
    },
    {
        "name": "Viking VK514 (K28 specific application, UL)",
        "commodities": {"I", "II", "III", "IV", "CUP"},
        "row_types": {"single", "double"},
        "max_storage_ft": None, "max_ceiling_ft": 48.0, "min_aisle_ft": None,
        "fm_only": False,
        "note": "Reported to 48 ft ceiling (12 @ 35 psi); aisle/storage limits per Viking data sheet — VERIFY.",
    },
    {
        "name": "FM-approved K28 ESFR (Viking) — FM DS 8-9 sites",
        "commodities": {"I", "II", "III", "IV", "CUP"},
        "row_types": {"single", "double"},
        "max_storage_ft": 50.0, "max_ceiling_ft": 55.0, "min_aisle_ft": 8.0,
        "fm_only": True,
        "note": "9 sprinklers @ 80 psi (~2,250 gpm, likely fire pump); min 8 ft aisles. Verify with FM.",
    },
]

# In-rack options with SOURCED max vertical spacing between in-rack levels (ft).
IN_RACK_OPTIONS = {
    "EC in-rack (K25.2EC pendent, NFPA 13-2019 §25.8.3)": {
        "spacing_ft": {"default": 30.0, "uncartoned": 20.0},
        "note": "Horizontal barriers required at each in-rack level; independent of ceiling "
                "('virtual floor'). Racks up to 15.5 ft deep.",
    },
    "ESFR in-rack (NFPA 13-2019 Ch. 25)": {
        "spacing_ft": {"default": 40.0, "CEP": 30.0, "uncartoned": 30.0},
        "note": "Not balanced with ceiling demand; top in-rack level treated as the 'virtual "
                "floor' when selecting ceiling protection.",
    },
}

ESFR_MIN_CLEARANCE_IN = 36.0      # NFPA 13 §14.2.12 (2019+); §8.12.x in earlier editions
STANDARD_MIN_CLEARANCE_IN = 18.0  # standard-spray deflector to top of storage
OPEN_SHELF_MAX_FT2 = 20.0         # solid shelf <= 20 ft2 is still 'open rack'
OPEN_DECK_MIN_PCT = 50.0          # wire/slatted deck >= 50% open (flues maintained) = open


def load_adopted_codes(path: Optional[str] = None) -> dict:
    with open(path or os.path.join(_DATA, "adopted_codes.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------------------
@dataclass
class FireInputs:
    commodity: str
    storage_height_ft: float
    ceiling_height_ft: float
    aisle_width_ft: float
    storage_method: str = "rack"           # rack | shelf | palletized | solid_pile
    rack_depth_ft: Optional[float] = None  # overall row depth (back-to-back incl. flue)
    row_type: Optional[str] = None         # override: single | double | multiple
    shelving: str = "none"                 # none | wire | slatted | solid
    deck_open_pct: Optional[float] = None
    flues_maintained: bool = True
    shelf_area_ft2: Optional[float] = None
    encapsulated: bool = False
    insurer: str = "NFPA"                  # FM | NFPA | UNKNOWN
    jurisdiction: str = "DEFAULT"
    deflector_height_ft: Optional[float] = None
    beam_elevations_in: Optional[list] = None
    conventional_spacing_ft: Optional[float] = None


@dataclass
class Finding:
    level: str      # REQUIRED | WARN | INFO | OK
    topic: str
    message: str
    cite: str = ""


@dataclass
class FireAssessment:
    inputs: FireInputs
    commodity_key: str
    editions: dict
    row_type: Optional[str]
    open_rack: Optional[bool]
    in_rack_status: str          # REQUIRED | LIKELY | UNRESOLVED | POSSIBLY_AVOIDABLE
    rationale: list
    findings: list = field(default_factory=list)
    sa_options: list = field(default_factory=list)
    in_rack_plans: dict = field(default_factory=dict)
    assumptions: list = field(default_factory=list)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["inputs"] = asdict(self.inputs)
        return d


# ---------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------
def classify_row(aisle_ft: float, depth_ft: Optional[float], override: Optional[str]) -> tuple[str, list]:
    """NFPA 13 definitions: single <= 6 ft deep, double <= 12 ft, aisles >= 3.5 ft."""
    notes = []
    if aisle_ft < 3.5:
        notes.append("Aisles < 3.5 ft: racks are treated as MULTIPLE-ROW (NFPA 13 definitions).")
        return "multiple", notes
    if override:
        return override.lower(), notes
    if depth_ft is None:
        notes.append("Rack depth not given — row type assumed DOUBLE; provide --rack-depth.")
        return "double", notes
    if depth_ft <= 6.0:
        return "single", notes
    if depth_ft <= 12.0:
        return "double", notes
    return "multiple", notes


def plan_in_rack_levels(beam_elevations_in: list, top_of_storage_in: float,
                        max_spacing_ft: float,
                        virtual_floor_min_in: Optional[float] = None) -> tuple[list, Optional[str]]:
    """
    Place in-rack levels at beam elevations (returns 1-based beam level numbers, warning).

    Conventional mode (virtual_floor_min_in is None): greedy from the floor — highest beam
    within max_spacing of the previous level — until the storage above the last level is
    within max_spacing.

    Virtual-floor mode (EC / ESFR in-rack options): levels climb with gaps <= max_spacing
    until the top in-rack level is at or above virtual_floor_min_in, i.e. high enough that
    the ceiling and storage ABOVE it fall inside the ceiling-only envelope. If that minimum
    is <= 0 the ceiling-only envelope is already met and no in-rack level is needed.
    """
    elevs = sorted(float(e) for e in beam_elevations_in)
    s = max_spacing_ft * 12.0
    prev, levels = 0.0, []

    if virtual_floor_min_in is not None:
        if virtual_floor_min_in <= 0:
            return [], None  # ceiling-only envelope already met from the real floor
        target = virtual_floor_min_in
        while prev < target - 1e-6:
            cands = [e for e in elevs if prev < e <= prev + s + 1e-6]
            if not cands:
                return levels, (f"No beam level within {max_spacing_ft:.0f} ft above "
                                f"{prev:.0f} in — cannot reach the required virtual floor "
                                f"({target:.0f} in).")
            reach = [e for e in cands if e >= target - 1e-6]
            nxt = min(reach) if reach else max(cands)
            levels.append(elevs.index(nxt) + 1)
            prev = nxt
            if prev >= target - 1e-6:
                break
        return levels, None

    while top_of_storage_in - prev > s + 1e-6:
        cands = [e for e in elevs if prev < e <= prev + s + 1e-6]
        if not cands:
            return levels, (f"No beam level within {max_spacing_ft:.0f} ft above "
                            f"{prev:.0f} in — tier pitch exceeds the spacing limit.")
        nxt = max(cands)
        levels.append(elevs.index(nxt) + 1)
        prev = nxt
    return levels, None


# ---------------------------------------------------------------------------------------
# Main assessment
# ---------------------------------------------------------------------------------------
def assess(inp: FireInputs, codes: Optional[dict] = None) -> FireAssessment:
    codes = codes or load_adopted_codes()
    jur = (inp.jurisdiction or "DEFAULT").upper()
    ed = codes.get(jur) or codes["DEFAULT"]
    nfpa = f"NFPA 13 ({ed['nfpa13']})"
    ifc = f"IFC ({ed['ifc']})"

    key, cwarn = normalize_commodity(inp.commodity)
    F: list[Finding] = []
    rationale: list[str] = []
    assumptions: list[str] = []
    if cwarn:
        F.append(Finding("WARN", "Commodity", cwarn))

    insurer = (inp.insurer or "NFPA").upper()
    is_fm = insurer == "FM"

    # 1. Authority + editions --------------------------------------------------------
    if jur not in codes:
        F.append(Finding("WARN", "Editions", f"Jurisdiction {jur!r} not in adopted_codes.json — "
                         "using latest published editions as reference only."))
    F.append(Finding("INFO", "Editions",
                     f"{ed['name']}: {nfpa}, {ifc}, IBC ({ed['ibc']}), ASCE {ed['asce7']} "
                     f"[{ed.get('status', '')}].", "rack_selector/data/adopted_codes.json"))
    if is_fm:
        F.append(Finding("WARN", "Authority",
                         "FM Global-insured: FM DS 8-9 governs fire protection. NFPA-based findings "
                         "below are a cross-check only; FM is generally more conservative.",
                         "FM DS 8-9"))
    elif insurer == "UNKNOWN":
        F.append(Finding("WARN", "Authority",
                         "Insurer unknown. If FM Global, DS 8-9 governs and may change every "
                         "conclusion below — confirm before relying on this.", "FM DS 8-9"))

    # 2. IFC high-piled trigger + FM scope ----------------------------------------------
    h = inp.storage_height_ft
    if h > 12.0:
        F.append(Finding("INFO", "IFC Ch. 32",
                         f"High-piled combustible storage (top of storage {h:.1f} ft > 12 ft): "
                         "Table 3206.2 requirements + storage permit/submittal apply.",
                         f"{ifc} §3202 / Table 3206.2"))
    elif key in GROUP_A and h > 6.0:
        F.append(Finding("WARN", "IFC Ch. 32",
                         "Group A plastics are high-hazard commodities: high-piled at > 6 ft "
                         "WHEN REQUIRED by the fire code official.", f"{ifc} §3202 / §3203.6"))
    else:
        F.append(Finding("OK", "IFC Ch. 32", "Not high-piled by height.", f"{ifc} §3202"))
    if is_fm:
        fm_trig = (key in ("I", "II", "III") and h > 10) or (key not in ("I", "II", "III") and h > 5)
        if fm_trig:
            F.append(Finding("INFO", "FM scope", "Within FM DS 8-9 scope (Cl.1-3 > 10 ft; "
                             "Cl.4/plastics > 5 ft; or any height > 200 ft2).", "FM DS 8-9 §1"))

    # Deflector / clearance ---------------------------------------------------------------
    if inp.deflector_height_ft is not None:
        defl = inp.deflector_height_ft
    else:
        defl = inp.ceiling_height_ft - 1.0
        assumptions.append(f"Ceiling deflector assumed 1 ft below ceiling ({defl:.1f} ft); "
                           "provide --deflector-height for the actual elevation.")
    clear_in = (defl - h) * 12.0
    if clear_in < STANDARD_MIN_CLEARANCE_IN:
        F.append(Finding("REQUIRED", "Clearance",
                         f"Only {clear_in:.0f} in. from deflector to top of storage — below the "
                         f"{STANDARD_MIN_CLEARANCE_IN:.0f} in. minimum. Lower storage.", nfpa))
    esfr_clear_ok = clear_in >= ESFR_MIN_CLEARANCE_IN
    if not esfr_clear_ok and clear_in >= STANDARD_MIN_CLEARANCE_IN:
        F.append(Finding("WARN", "Clearance",
                         f"{clear_in:.0f} in. deflector-to-storage meets 18 in. (standard spray) "
                         f"but NOT the 36 in. ESFR/CMSA minimum.", f"{nfpa} §14.2.12 (ESFR)"))
    elif esfr_clear_ok:
        F.append(Finding("OK", "Clearance",
                         f"{clear_in:.0f} in. deflector-to-storage (>= 36 in. ESFR / 18 in. "
                         "standard spray).", f"{nfpa} §14.2.12"))

    # 3. Row classification ---------------------------------------------------------------
    row_type = None
    if inp.storage_method in ("rack", "shelf"):
        row_type, rnotes = classify_row(inp.aisle_width_ft, inp.rack_depth_ft, inp.row_type)
        for n in rnotes:
            F.append(Finding("WARN", "Row type", n, f"{nfpa} Ch. 3 definitions"))
        F.append(Finding("INFO", "Row type", f"Classified as {row_type.upper()}-row rack "
                         f"(aisle {inp.aisle_width_ft:.2f} ft"
                         + (f", depth {inp.rack_depth_ft:.1f} ft)." if inp.rack_depth_ft else ")."),
                         f"{nfpa} Ch. 3 definitions"))
        if 3.5 <= inp.aisle_width_ft < 4.0:
            F.append(Finding("WARN", "Aisle", "Aisles < 4 ft: ceiling criteria for 4 ft aisles "
                             "apply to narrower aisles.", f"{nfpa} Ch. 21"))

    # 4. Open rack vs solid shelving -------------------------------------------------------
    open_rack: Optional[bool] = True
    shelving = (inp.shelving or "none").lower()
    if shelving == "none":
        F.append(Finding("OK", "Shelving", "No shelving — open rack.", f"{nfpa} §3.3 'open rack'"))
    else:
        deck_ok = None
        if shelving in ("wire", "slatted"):
            if inp.deck_open_pct is None:
                deck_ok = None
                F.append(Finding("WARN", "Shelving", "Deck open-area % unknown. Wire/slatted "
                                 "decks count as open only if >= 50% open AND flues are maintained.",
                                 f"{nfpa} §3.3 'open rack'"))
            else:
                deck_ok = inp.deck_open_pct >= OPEN_DECK_MIN_PCT
        if shelving in ("wire", "slatted") and deck_ok is not False and inp.flues_maintained:
            open_rack = True if deck_ok else None
            if deck_ok:
                F.append(Finding("OK", "Shelving", f"{shelving} deck {inp.deck_open_pct:.0f}% open "
                                 "with flues maintained — open rack.", f"{nfpa} §3.3 'open rack'"))
        else:
            # solid deck, under-50% deck, or loads blocking flues -> shelf area governs
            why = ("solid deck" if shelving == "solid" else
                   "loads block the flue spaces" if not inp.flues_maintained else
                   f"deck only {inp.deck_open_pct:.0f}% open")
            if inp.shelf_area_ft2 is not None and inp.shelf_area_ft2 <= OPEN_SHELF_MAX_FT2:
                open_rack = True
                F.append(Finding("OK", "Shelving", f"{why}, but shelf area {inp.shelf_area_ft2:.0f} "
                                 f"ft2 <= 20 ft2 — still open rack.", f"{nfpa} §3.3 'open rack'"))
            else:
                open_rack = False
                area = (f"{inp.shelf_area_ft2:.0f} ft2" if inp.shelf_area_ft2 is not None
                        else "area bounded by actual flues/aisles (> 20 ft2 assumed)")
                F.append(Finding("REQUIRED", "Shelving",
                                 f"SOLID SHELVING ({why}; {area}). In-rack sprinklers are required "
                                 "at each tier beneath solid shelves; the 20-64 ft2 band has "
                                 "specific provisions in recent editions — FPE to confirm.",
                                 f"{nfpa} Ch. 20/25 solid-shelving racks"))

    if inp.encapsulated:
        F.append(Finding("WARN", "Encapsulation", "Encapsulated loads escalate protection; "
                         "confirm the ESFR/CMDA row explicitly covers encapsulation.", nfpa))

    # 5. Ceiling-only feasibility -----------------------------------------------------------
    env = ESFR_ENVELOPE.get(key)
    nfpa_table_ok = False
    if env is None:
        F.append(Finding("WARN", "ESFR", f"No ceiling-only ESFR envelope encoded for "
                         f"{COMMODITY_LABEL[key]} — expect in-rack; FPE to check Ch. 23.",
                         ESFR_ENVELOPE_SOURCE))
    else:
        s_max, c_max = env
        within = h <= s_max and inp.ceiling_height_ft <= c_max
        nfpa_table_ok = within and esfr_clear_ok and row_type != "multiple"
        msg = (f"NFPA ESFR table envelope for {COMMODITY_LABEL[key]}: <= {s_max:.0f} ft storage / "
               f"<= {c_max:.0f} ft ceiling. Project: {h:.1f} ft / {inp.ceiling_height_ft:.1f} ft "
               f"-> {'WITHIN' if within else 'OUTSIDE'}.")
        F.append(Finding("OK" if within else "WARN", "ESFR", msg, ESFR_ENVELOPE_SOURCE))
        if row_type == "multiple":
            F.append(Finding("WARN", "ESFR", "Multiple-row racks: ceiling-only ESFR coverage is "
                             "limited — verify the table row explicitly includes multiple-row.", nfpa))

    sa_hits = []
    for opt in SA_OPTIONS:
        if opt["fm_only"] and not is_fm:
            continue
        reasons = []
        if key not in opt["commodities"]:
            reasons.append("commodity not covered")
        if row_type and row_type not in opt["row_types"]:
            reasons.append(f"{row_type}-row not covered")
        if opt["max_storage_ft"] and h > opt["max_storage_ft"]:
            reasons.append(f"storage > {opt['max_storage_ft']:.0f} ft")
        if opt["max_ceiling_ft"] and inp.ceiling_height_ft > opt["max_ceiling_ft"]:
            reasons.append(f"ceiling > {opt['max_ceiling_ft']:.0f} ft")
        if opt["min_aisle_ft"] and inp.aisle_width_ft < opt["min_aisle_ft"]:
            reasons.append(f"aisle < {opt['min_aisle_ft']:.0f} ft")
        if open_rack is False:
            reasons.append("solid shelving (not open-frame)")
        sa_hits.append({"name": opt["name"], "compatible": not reasons,
                        "blocked_by": reasons, "note": opt["note"]})

    # 6. Conclusion --------------------------------------------------------------------------
    sa_ok = any(o["compatible"] for o in sa_hits)
    if open_rack is False:
        status = "REQUIRED"
        rationale.append("Solid shelving -> in-rack at each tier beneath solid shelves.")
    elif nfpa_table_ok and open_rack:
        status = "POSSIBLY_AVOIDABLE"
        rationale.append("Open rack within the NFPA ESFR ceiling-only envelope with 36 in. "
                         "clearance — ceiling-only ESFR may work (verify exact table row, "
                         "water supply, obstructions).")
    elif sa_ok and open_rack:
        status = "POSSIBLY_AVOIDABLE"
        rationale.append("Outside the NFPA ESFR table but a specific-application listing appears "
                         "compatible — requires AHJ (and insurer) acceptance of the listing.")
    elif open_rack is None:
        status = "UNRESOLVED"
        rationale.append("Open-rack vs. solid-shelving status unresolved (deck open % unknown). "
                         "Resolve that first — it decides whether in-rack is mandatory.")
    else:
        status = "LIKELY"
        rationale.append("Outside ceiling-only envelopes encoded here — plan on in-rack unless the "
                         "FPE finds a listed ceiling-only scheme.")
    if is_fm:
        rationale.append("FM site: conclusion must be re-checked against FM DS 8-9 tables.")
    if inp.ceiling_height_ft > 45.0 and key in ("I", "II", "III", "IV", "CUP"):
        rationale.append("Ceiling > 45 ft: NFPA 13 table ESFR is not available for ceiling-only; "
                         "options are a specific-application listing or in-rack ('virtual floor').")

    # In-rack plans ---------------------------------------------------------------------------
    plans = {}
    if inp.beam_elevations_in:
        top = inp.storage_height_ft * 12.0
        if open_rack is False:
            plans["Solid shelving — every tier"] = {
                "levels": list(range(1, len(inp.beam_elevations_in) + 1)),
                "spacing_ft": None, "warning": None,
                "note": "In-rack beneath each solid shelf level."}
        vf_min = None
        if env is not None:
            s_max, c_max = env
            vf_min = max(inp.ceiling_height_ft - c_max, inp.storage_height_ft - s_max, 0.0) * 12.0
        for name, o in IN_RACK_OPTIONS.items():
            sp = o["spacing_ft"]
            spacing = (sp.get("uncartoned") if key in UNCARTONED and "uncartoned" in sp
                       else sp.get(key, sp["default"]))
            lv, w = plan_in_rack_levels(inp.beam_elevations_in, top, spacing, vf_min)
            note = o["note"]
            if vf_min:
                note += (f" Top in-rack level must be >= {vf_min / 12:.1f} ft so the ceiling/"
                         "storage above it fit the ceiling-only ESFR envelope.")
            plans[name] = {"levels": lv, "spacing_ft": spacing, "warning": w, "note": note,
                           "virtual_floor_min_in": vf_min}
        if inp.conventional_spacing_ft:
            lv, w = plan_in_rack_levels(inp.beam_elevations_in, top, inp.conventional_spacing_ft)
            plans["Conventional QR in-rack (user-supplied spacing)"] = {
                "levels": lv, "spacing_ft": inp.conventional_spacing_ft, "warning": w,
                "note": "Spacing supplied by user from the NFPA 13 Ch. 25 figure."}
        else:
            assumptions.append("Conventional QR (K8.0/K11.2) in-rack level spacing is set by the "
                               "NFPA 13 Ch. 25 figure for the arrangement — not encoded here.")

    return FireAssessment(
        inputs=inp, commodity_key=key, editions=ed, row_type=row_type, open_rack=open_rack,
        in_rack_status=status, rationale=rationale, findings=F, sa_options=sa_hits,
        in_rack_plans=plans, assumptions=assumptions)


# ---------------------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------------------
_ICON = {"REQUIRED": "[!!]", "WARN": "[! ]", "INFO": "[i ]", "OK": "[ok]"}


def render(a: FireAssessment) -> str:
    i = a.inputs
    L = ["=" * 74,
         "  FIRE CHECK — IN-RACK TRIAGE (not a sprinkler design; FPE review required)",
         "=" * 74, ""]
    L.append(f"Commodity: {COMMODITY_LABEL[a.commodity_key]}   Storage {i.storage_height_ft:.1f} ft"
             f" / ceiling {i.ceiling_height_ft:.1f} ft   Aisle {i.aisle_width_ft:.2f} ft")
    L.append(f"Jurisdiction: {a.editions['name']}  (NFPA 13 {a.editions['nfpa13']}, "
             f"IFC {a.editions['ifc']})   Insurer: {i.insurer}")
    L.append("")
    L.append(f"IN-RACK: {a.in_rack_status.replace('_', ' ')}")
    for r in a.rationale:
        L.append(f"  - {r}")
    L.append("")
    L.append("FINDINGS")
    for f in a.findings:
        cite = f"  ({f.cite})" if f.cite else ""
        L.append(f"  {_ICON.get(f.level, '    ')} {f.topic}: {f.message}{cite}")
    if a.sa_options:
        L.append("")
        L.append("SPECIFIC-APPLICATION CEILING-ONLY OPTIONS (listing conditions; AHJ acceptance)")
        for o in a.sa_options:
            st = "compatible" if o["compatible"] else "blocked: " + "; ".join(o["blocked_by"])
            L.append(f"  - {o['name']}: {st}")
    if a.in_rack_plans:
        L.append("")
        L.append("IN-RACK LEVEL PLANNING (beam level numbers from the floor)")
        for name, p in a.in_rack_plans.items():
            sp = f" (max {p['spacing_ft']:.0f} ft vertical)" if p["spacing_ft"] else ""
            lv = ", ".join(str(x) for x in p["levels"]) or "none needed"
            L.append(f"  - {name}{sp}: levels {lv}")
            if p.get("virtual_floor_min_in"):
                L.append(f"      virtual floor must be >= {p['virtual_floor_min_in'] / 12:.1f} ft "
                         "(ceiling above it <= ESFR table ceiling)")
            if p.get("warning"):
                L.append(f"      ! {p['warning']}")
    if a.assumptions:
        L.append("")
        L.append("ASSUMPTIONS")
        for s in a.assumptions:
            L.append(f"  - {s}")
    L.append("")
    L.append("** TRIAGE ONLY — confirm every table row, listing, and level with the FPE. **")
    return "\n".join(L)


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rack_selector.fire_check",
                                description="In-rack sprinkler triage (nicet_agent).")
    p.add_argument("--project", help="Project profile JSON (fills defaults)")
    p.add_argument("--commodity")
    p.add_argument("--storage-height", type=float, help="Top of storage (ft)")
    p.add_argument("--ceiling-height", type=float, help="Ceiling / roof deck (ft)")
    p.add_argument("--deflector-height", type=float, help="Ceiling sprinkler deflector (ft)")
    p.add_argument("--aisle", type=float, help="Aisle width between loads (ft)")
    p.add_argument("--rack-depth", type=float, help="Overall row depth (ft)")
    p.add_argument("--row-type", choices=["single", "double", "multiple"])
    p.add_argument("--storage-method", choices=["rack", "shelf", "palletized", "solid_pile"])
    p.add_argument("--shelving", choices=["none", "wire", "slatted", "solid"])
    p.add_argument("--deck-open", type=float, help="Deck open area %%")
    p.add_argument("--flues-blocked", action="store_true", help="Loads block flue spaces")
    p.add_argument("--shelf-area", type=float, help="Shelf area bounded by flues/aisles (ft2)")
    p.add_argument("--encapsulated", action="store_true")
    p.add_argument("--insurer", choices=["FM", "NFPA", "UNKNOWN"])
    p.add_argument("--jurisdiction", help="e.g. UT, CA, WA")
    p.add_argument("--beam-elevations", help="Comma-separated beam top elevations (in)")
    p.add_argument("--pitch", type=float, help="Uniform level pitch (in) — generates elevations "
                   "with --levels")
    p.add_argument("--levels", type=int, help="Number of beam levels (with --pitch)")
    p.add_argument("--first-beam-top", type=float,
                   help="First beam top elevation (in); default = one pitch")
    p.add_argument("--conventional-spacing-ft", type=float,
                   help="Conventional in-rack vertical spacing read from NFPA 13 Ch. 25 figure")
    p.add_argument("--json", action="store_true")
    return p


def inputs_from_args(args) -> FireInputs:
    base: dict = {}
    if args.project:
        from .project import load_project, fire_inputs_dict
        base = fire_inputs_dict(load_project(args.project))
    over = {
        "commodity": args.commodity, "storage_height_ft": args.storage_height,
        "ceiling_height_ft": args.ceiling_height, "deflector_height_ft": args.deflector_height,
        "aisle_width_ft": args.aisle, "rack_depth_ft": args.rack_depth, "row_type": args.row_type,
        "storage_method": args.storage_method, "shelving": args.shelving,
        "deck_open_pct": args.deck_open, "shelf_area_ft2": args.shelf_area,
        "insurer": args.insurer, "jurisdiction": args.jurisdiction,
        "conventional_spacing_ft": args.conventional_spacing_ft,
    }
    base.update({k: v for k, v in over.items() if v is not None})
    if args.flues_blocked:
        base["flues_maintained"] = False
    if args.encapsulated:
        base["encapsulated"] = True
    if args.beam_elevations:
        base["beam_elevations_in"] = [float(x) for x in args.beam_elevations.split(",") if x.strip()]
    elif args.pitch and args.levels:
        first = args.first_beam_top if args.first_beam_top is not None else args.pitch
        base["beam_elevations_in"] = [first + i * args.pitch for i in range(args.levels)]
    missing = [k for k in ("commodity", "storage_height_ft", "ceiling_height_ft", "aisle_width_ft")
               if base.get(k) is None]
    if missing:
        raise SystemExit(f"Missing required inputs: {', '.join(missing)} (or supply --project)")
    allowed = set(FireInputs.__dataclass_fields__)
    return FireInputs(**{k: v for k, v in base.items() if k in allowed})


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    from ._io import safe_stdout
    safe_stdout()
    try:
        a = assess(inputs_from_args(args))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(a.as_dict(), indent=2, default=str) if args.json else render(a))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
