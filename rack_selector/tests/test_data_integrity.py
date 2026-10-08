"""Data integrity: dealer catalog, adopted-code table, project profiles, and KB documents."""

import glob
import json
import os
import re

import pytest

from rack_selector.fire_check import FireInputs, assess
from rack_selector.project import fire_inputs_dict, load_project

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "rack_selector", "data")


def _json(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return json.load(fh)


CATALOG = _json("rack_selector", "data", "rack_catalog.json")
CODES = _json("rack_selector", "data", "adopted_codes.json")


# --- dealer catalog -----------------------------------------------------------------------
FAMILIES = [("beams", f, "capacity_by_length_lb") for f in CATALOG["beams"]] + \
           [("frames", f, "capacity_by_unsupported_length_lb") for f in CATALOG["frames"]]


def test_catalog_dealers_match_priority():
    dealers = {f["dealer"] for _, f, _ in FAMILIES}
    assert dealers == set(CATALOG["_meta"]["dealer_priority"])


@pytest.mark.parametrize("kind, fam, key", FAMILIES,
                         ids=[f"{k}:{f['dealer']}:{f['family']}" for k, f, _ in FAMILIES])
def test_catalog_family_is_well_formed(kind, fam, key):
    assert fam["confidence"] in CATALOG["_meta"]["confidence_levels"]
    assert fam["source"].strip()
    if fam["confidence"] == "published":
        assert "http" in fam["source"], "published data must cite a URL"
    ids = [m["id"] for m in fam["models"]]
    assert len(ids) == len(set(ids)), "duplicate model ids"
    for m in fam["models"]:
        table = m[key]
        assert table, f"{m['id']} has no capacities"
        lengths = sorted(float(k) for k in table)
        assert all(float(k) > 0 for k in table)
        caps = [table[k] for k in sorted(table, key=float)]
        assert all(isinstance(c, int) and c > 0 for c in caps)
        # capacity must never INCREASE as span / unsupported length grows
        assert all(a >= b for a, b in zip(caps, caps[1:])), f"{m['id']} not monotonic"
        assert lengths == sorted(lengths)
        if kind == "beams":
            assert m["face_in"] > 0


def test_heavier_beam_is_stronger_at_same_length():
    """Within a family, a deeper face never carries less at a shared length."""
    for fam in CATALOG["beams"]:
        models = sorted(fam["models"], key=lambda m: (m["face_in"], m.get("gauge") or 99))
        for a, b in zip(models, models[1:]):
            for L in set(a["capacity_by_length_lb"]) & set(b["capacity_by_length_lb"]):
                if b["face_in"] > a["face_in"]:
                    assert b["capacity_by_length_lb"][L] >= a["capacity_by_length_lb"][L], \
                        f"{fam['dealer']} {b['id']} < {a['id']} at {L} in"


# --- adopted codes --------------------------------------------------------------------------
def test_adopted_codes_schema_and_seismic_consistency():
    assert {"DEFAULT", "UT", "CA", "WA"} <= set(CODES)
    for key, ed in CODES.items():
        if key.startswith("_"):
            continue
        for field in ("name", "nfpa13", "ifc", "ibc", "asce7", "status"):
            assert ed.get(field), f"{key}.{field} missing"
        assert ed["asce7"] in {"7-16", "7-22"}
        # IBC 2024 references ASCE 7-22; IBC 2018/2021 reference ASCE 7-16
        expected = "7-22" if ed["ibc"].startswith("2024") else "7-16"
        assert ed["asce7"] == expected, f"{key}: IBC {ed['ibc']} vs ASCE {ed['asce7']}"
        if key != "DEFAULT":
            assert ed["sources"], f"{key} has no sources"


def test_utah_is_the_confirmed_governing_set():
    ut = CODES["UT"]
    assert (ut["nfpa13"], ut["ifc"], ut["asce7"], ut["status"]) == ("2019", "2021", "7-16",
                                                                     "confirmed")


# --- project profiles --------------------------------------------------------------------
PROFILES = sorted(glob.glob(os.path.join(ROOT, "projects", "*.json")))


@pytest.mark.parametrize("path", PROFILES, ids=[os.path.basename(p) for p in PROFILES])
def test_project_profile_schema(path):
    proj = load_project(path)
    for key in ("project_id", "name", "site", "building", "insurer", "fire", "rack",
                "open_questions", "history"):
        assert key in proj, f"{os.path.basename(path)} missing {key}"
    if os.path.basename(path).startswith("_"):
        return
    jur = proj["site"]["jurisdiction"]
    assert jur in CODES, f"unknown jurisdiction {jur}"
    assert proj["site"]["code_edition"] == "asce" + CODES[jur]["asce7"], \
        "site.code_edition must match the jurisdiction's adopted ASCE 7"
    assert proj["insurer"] in {"FM", "NFPA", "UNKNOWN"}


@pytest.mark.parametrize("path", [p for p in PROFILES if not os.path.basename(p).startswith("_")])
def test_project_profile_runs_through_fire_check(path):
    allowed = set(FireInputs.__dataclass_fields__)
    inputs = {k: v for k, v in fire_inputs_dict(load_project(path)).items() if k in allowed}
    a = assess(FireInputs(**inputs))
    assert a.in_rack_status in {"REQUIRED", "LIKELY", "UNRESOLVED", "POSSIBLY_AVOIDABLE"}


# --- knowledge base documents ---------------------------------------------------------------
KB_FILES = sorted(glob.glob(os.path.join(ROOT, "knowledge_base", "*.md")))
ALL_MD = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)}


@pytest.mark.parametrize("path", KB_FILES, ids=[os.path.basename(p) for p in KB_FILES])
def test_kb_file_has_title_and_resolvable_references(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    assert text.lstrip().startswith("# "), "KB file must start with an H1 title"
    for ref in set(re.findall(r"`?([A-Za-z0-9_\-]+\.md)`?", text)):
        if "*" in ref:
            continue
        assert ref in ALL_MD, f"{os.path.basename(path)} references missing file {ref}"


def test_index_router_lists_every_kb_file():
    with open(os.path.join(ROOT, "knowledge_base", "00_INDEX.md"), encoding="utf-8") as fh:
        index = fh.read()
    for p in KB_FILES:
        name = os.path.basename(p)
        if name != "00_INDEX.md":
            assert name in index, f"00_INDEX.md does not route to {name}"
