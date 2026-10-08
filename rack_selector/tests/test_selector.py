import pytest

from rack_selector.seismic import SeismicResult, compute_cs
from rack_selector.selector import recommend, render_report


def make_seismic(sds=1.0, sd1=0.6, s1=0.55, sdc="D"):
    res = SeismicResult(latitude=40.76, longitude=-111.89, risk_category="II",
                        site_class="Default", sds=sds, sd1=sd1, s1=s1, sdc=sdc, ss=1.5)
    res.cs_down_aisle = compute_cs(sds, sd1, s1, 6.0, 1.0)
    res.cs_cross_aisle = compute_cs(sds, sd1, s1, 4.0, 1.0)
    return res


def test_recommend_end_to_end_interlake_priority():
    rec = recommend(make_seismic(), pallet_weight_lb=2500, pallet_height_in=48,
                    beam_length_in=96, num_beam_levels=4, pallets_per_bay=2,
                    in_rack_sprinklers=False, building_clear_height_in=384,
                    commodity_class="Class IV")
    # demand
    assert rec.required_beam_pair_lb == 5000
    assert rec.required_frame_axial_lb == 20000
    # dealer priority honored, capacity sufficient
    assert rec.recommended_beam.dealer == "Interlake Mecalux"
    assert rec.recommended_beam.capacity_pair_lb >= 5000
    assert rec.recommended_frame.dealer == "Interlake Mecalux"
    assert rec.recommended_frame.capacity_lb >= 20000
    # clearance + nfpa
    assert rec.layout.clearance_in == 6.0
    assert rec.layout.nfpa_ok is True
    # seismic magnitude computed
    assert rec.seismic_weight_per_bay_lb > 0
    assert rec.base_shear_down_aisle_lb > 0
    assert rec.base_shear_cross_aisle_lb > rec.base_shear_down_aisle_lb
    # SDC D requirements surfaced
    assert any("overstrength" in f.lower() for f in rec.flags)


def test_inrack_changes_clearance_and_note():
    rec = recommend(make_seismic(), pallet_weight_lb=2000, pallet_height_in=50,
                    beam_length_in=108, num_beam_levels=3, in_rack_sprinklers=True)
    assert rec.layout.clearance_in == 12.0
    assert "12 in" in rec.fire_note


def test_high_hazard_above_esfr_envelope_advises_inrack():
    # storage well above ~35 ft -> advisory should suggest in-rack likely
    rec = recommend(make_seismic(), pallet_weight_lb=1500, pallet_height_in=60,
                    beam_length_in=96, num_beam_levels=8, in_rack_sprinklers=False,
                    commodity_class="Group A plastic")
    assert "in-rack" in rec.fire_note.lower()


def test_overheight_storage_flags_nfpa():
    rec = recommend(make_seismic(), pallet_weight_lb=2000, pallet_height_in=55,
                    beam_length_in=96, num_beam_levels=7, in_rack_sprinklers=False,
                    building_clear_height_in=300)
    assert rec.layout.nfpa_ok is False
    assert any("NFPA 13" in f for f in rec.flags)


def test_no_beam_meets_demand_flagged():
    rec = recommend(make_seismic(), pallet_weight_lb=20000, pallet_height_in=48,
                    beam_length_in=144, num_beam_levels=3, pallets_per_bay=3)
    # 60,000 lb/pair at 144in exceeds the catalog -> flagged, no beam
    assert rec.recommended_beam is None
    assert any("beam" in f.lower() for f in rec.flags)


def test_render_report_runs():
    rec = recommend(make_seismic(), pallet_weight_lb=2500, pallet_height_in=48,
                    beam_length_in=96, num_beam_levels=4, building_clear_height_in=384,
                    commodity_class="Class IV")
    text = render_report(rec)
    assert "RACK SELECTOR" in text
    assert "RECOMMENDATION" in text
    assert "PE/FPE review" in text or "PE" in text
