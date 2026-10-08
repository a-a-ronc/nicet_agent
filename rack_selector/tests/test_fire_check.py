import pytest

from rack_selector.fire_check import (FireInputs, assess, classify_row, normalize_commodity,
                                      plan_in_rack_levels, render)


def base(**kw):
    d = dict(commodity="Class IV", storage_height_ft=30.0, ceiling_height_ft=40.0,
             aisle_width_ft=6.0, rack_depth_ft=4.0, shelving="wire", deck_open_pct=60.0,
             flues_maintained=True, jurisdiction="UT", insurer="NFPA")
    d.update(kw)
    return FireInputs(**d)


# --- normalization / classification ---------------------------------------------------
def test_normalize_commodity():
    assert normalize_commodity("Class IV") == ("IV", None)
    assert normalize_commodity("cartoned unexpanded plastic")[0] == "CUP"
    key, warn = normalize_commodity("Group A plastic")
    assert key == "CUP" and "assumed" in warn.lower()
    with pytest.raises(ValueError):
        normalize_commodity("shoes")


def test_classify_row():
    assert classify_row(3.0, 4.0, None)[0] == "multiple"      # aisle < 3.5 ft
    assert classify_row(6.0, 4.0, None)[0] == "single"
    assert classify_row(6.0, 10.0, None)[0] == "double"
    assert classify_row(6.0, 14.0, None)[0] == "multiple"
    rt, notes = classify_row(6.0, None, None)
    assert rt == "double" and notes


# --- in-rack level planning -----------------------------------------------------------
def test_plan_levels_every_third_at_10ft():
    elevs = [39 * k for k in range(1, 9)]          # 39 .. 312 in
    levels, warn = plan_in_rack_levels(elevs, 343.5, 10.0)
    assert levels == [3, 6] and warn is None


def test_plan_levels_none_needed_when_spacing_large():
    elevs = [39 * k for k in range(1, 9)]
    assert plan_in_rack_levels(elevs, 343.5, 30.0) == ([], None)


def test_plan_levels_warns_when_pitch_too_big():
    levels, warn = plan_in_rack_levels([100, 300], 400, 5.0)
    assert levels == [] and "exceeds" in warn


# --- assessments ----------------------------------------------------------------------
def test_solid_shelving_requires_in_rack():
    a = assess(base(flues_maintained=False))
    assert a.open_rack is False
    assert a.in_rack_status == "REQUIRED"


def test_small_solid_shelf_is_open_rack():
    a = assess(base(shelving="solid", shelf_area_ft2=18.0))
    assert a.open_rack is True


def test_open_rack_within_esfr_envelope_possibly_avoidable():
    a = assess(base())
    assert a.open_rack is True
    assert a.in_rack_status == "POSSIBLY_AVOIDABLE"


def test_unknown_deck_is_unresolved():
    a = assess(base(deck_open_pct=None))
    assert a.open_rack is None
    assert a.in_rack_status == "UNRESOLVED"


def test_50ft_ceiling_outside_nfpa_and_sa_listings():
    a = assess(base(ceiling_height_ft=50.0, storage_height_ft=29.0, aisle_width_ft=5.83,
                    row_type="single"))
    assert a.in_rack_status == "LIKELY"
    assert any("45 ft" in r for r in a.rationale)
    assert not any(o["compatible"] for o in a.sa_options)


def test_47ft_ceiling_specific_application_listing_compatible():
    a = assess(base(ceiling_height_ft=47.0, storage_height_ft=29.0, aisle_width_ft=5.83,
                    row_type="single"))
    p25 = next(o for o in a.sa_options if o["name"].startswith("Reliable P25"))
    assert p25["compatible"]
    assert a.in_rack_status == "POSSIBLY_AVOIDABLE"


def test_fm_k28_blocked_by_narrow_aisle():
    a = assess(base(ceiling_height_ft=50.0, storage_height_ft=29.0, aisle_width_ft=5.83,
                    insurer="FM", row_type="single"))
    fm = next(o for o in a.sa_options if o["name"].startswith("FM-approved"))
    assert not fm["compatible"] and any("aisle" in b for b in fm["blocked_by"])


def test_esfr_36in_clearance_flagged():
    a = assess(base(storage_height_ft=42.0, ceiling_height_ft=45.0))  # deflector 44 -> 24 in
    assert any(f.topic == "Clearance" and "36 in" in f.message for f in a.findings)


def test_utah_editions_reported():
    a = assess(base())
    assert a.editions["nfpa13"] == "2019"
    assert any("NFPA 13 (2019)" in f.message for f in a.findings)


def test_ifc_trigger_class_iv_vs_group_a():
    low_iv = assess(base(storage_height_ft=10.0, ceiling_height_ft=30.0))
    assert any(f.topic == "IFC Ch. 32" and f.level == "OK" for f in low_iv.findings)
    low_cup = assess(base(commodity="CUP", storage_height_ft=8.0, ceiling_height_ft=30.0))
    assert any(f.topic == "IFC Ch. 32" and f.level == "WARN" for f in low_cup.findings)


def test_in_rack_plans_with_elevations():
    elevs = [39.0 * k for k in range(1, 9)]
    a = assess(base(beam_elevations_in=elevs, storage_height_ft=343.5 / 12,
                    ceiling_height_ft=50.0, conventional_spacing_ft=10.0))
    conv = a.in_rack_plans["Conventional QR in-rack (user-supplied spacing)"]
    assert conv["levels"] == [3, 6]
    ec = a.in_rack_plans["EC in-rack (K25.2EC pendent, NFPA 13-2019 §25.8.3)"]
    # 50 ft ceiling - 45 ft ESFR table ceiling = virtual floor >= 5 ft -> first beam >= 60 in
    assert ec["virtual_floor_min_in"] == pytest.approx(60.0)
    assert ec["levels"] == [2]                       # beam 2 at 78 in


def test_virtual_floor_not_needed_inside_envelope():
    elevs = [39.0 * k for k in range(1, 9)]
    assert plan_in_rack_levels(elevs, 343.5, 30.0, virtual_floor_min_in=0.0) == ([], None)


def test_virtual_floor_climbs_in_spacing_steps():
    elevs = [48.0 * k for k in range(1, 11)]          # 48 .. 480 in
    levels, warn = plan_in_rack_levels(elevs, 520, 20.0, virtual_floor_min_in=300.0)
    assert warn is None
    assert elevs[levels[-1] - 1] >= 300.0
    gaps = [elevs[levels[0] - 1]] + [elevs[b - 1] - elevs[a - 1] for a, b in zip(levels, levels[1:])]
    assert all(g <= 240.0 for g in gaps)


def test_render_runs():
    text = render(assess(base()))
    assert "IN-RACK:" in text and "FPE" in text
