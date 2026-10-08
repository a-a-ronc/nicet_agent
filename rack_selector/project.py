"""
Project profiles — one JSON file per job under projects/, holding the context an FPE would
ask for (site, building, insurer, commodity, rack schema, open questions). The fire_check,
levels and rack-selector CLIs accept --project to pre-fill their inputs; explicit flags
override the profile.

See projects/_TEMPLATE.json for the schema.
"""

from __future__ import annotations

import json
import os
from typing import Optional


def load_project(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        proj = json.load(fh)
    if "project_id" not in proj:
        raise ValueError(f"{path}: missing 'project_id'")
    return proj


def _get(d: dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def fire_inputs_dict(proj: dict) -> dict:
    """Map a project profile to rack_selector.fire_check.FireInputs fields (None = unset)."""
    fire = proj.get("fire", {})
    out = {
        "commodity": fire.get("commodity"),
        "storage_height_ft": fire.get("storage_height_ft"),
        "ceiling_height_ft": _get(proj, "building", "ceiling_height_ft"),
        "deflector_height_ft": _get(proj, "building", "deflector_height_ft"),
        "aisle_width_ft": fire.get("aisle_width_ft"),
        "rack_depth_ft": fire.get("rack_depth_ft"),
        "row_type": fire.get("row_type"),
        "storage_method": fire.get("storage_method"),
        "shelving": fire.get("shelving"),
        "deck_open_pct": fire.get("deck_open_pct"),
        "flues_maintained": fire.get("flues_maintained"),
        "shelf_area_ft2": fire.get("shelf_area_ft2"),
        "encapsulated": fire.get("encapsulated"),
        "insurer": proj.get("insurer"),
        "jurisdiction": _get(proj, "site", "jurisdiction"),
        "beam_elevations_in": fire.get("beam_elevations_in"),
    }
    return {k: v for k, v in out.items() if v is not None}


def site_dict(proj: dict) -> dict:
    """Location / seismic settings for the rack selector."""
    s = proj.get("site", {})
    return {k: s.get(k) for k in ("lat", "lon", "zip", "address", "risk_category",
                                  "site_class", "code_edition", "jurisdiction")
            if s.get(k) is not None}


def open_questions(proj: dict) -> list:
    return list(proj.get("open_questions", []))


def summarize(proj: dict) -> str:
    lines = [f"{proj['project_id']} — {proj.get('name', '')}"]
    b = proj.get("building", {})
    if b.get("ceiling_height_ft") is not None:
        conf = "" if b.get("ceiling_height_confirmed") else " (UNCONFIRMED)"
        lines.append(f"  Ceiling: {b['ceiling_height_ft']} ft{conf}")
    f = proj.get("fire", {})
    if f.get("commodity"):
        conf = "" if f.get("commodity_confirmed") else " (UNCONFIRMED)"
        lines.append(f"  Commodity: {f['commodity']}{conf}")
    lines.append(f"  Insurer: {proj.get('insurer', 'UNKNOWN')}")
    qs = open_questions(proj)
    if qs:
        lines.append("  Open questions:")
        lines += [f"    - {q}" for q in qs]
    return "\n".join(lines)
