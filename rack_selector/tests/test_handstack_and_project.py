import os

import pytest

from rack_selector import cli as rack_cli
from rack_selector import fire_check, levels
from rack_selector.clearance import beam_layout
from rack_selector.fire_check import FireInputs, assess
from rack_selector.project import fire_inputs_dict, load_project, summarize
from rack_selector.seismic import SeismicResult, compute_cs
from rack_selector.selector import recommend

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NB = os.path.join(ROOT, "projects", "25-1642_new_balance_slc.json")


def seismic():
    r = SeismicResult(40.8254, -111.9547, "II", "Default", 0.95, 0.42, 0.40, "D")
    r.cs_down_aisle = compute_cs(0.95, 0.42, 0.40, 6.0)
    r.cs_cross_aisle = compute_cs(0.95, 0.42, 0.40, 4.0)
    return r


# --- hand-stack mode -------------------------------------------------------------------
def test_handstack_shelf_load_drives_selection():
    rec = recommend(seismic(), shelf_load_lb=1800, pallet_height_in=31.5,
                    beam_length_in=144, num_beam_levels=6)
    assert rec.required_beam_pair_lb == 1800
    assert rec.required_frame_axial_lb == 1800 * 6
    assert rec.recommended_beam.dealer == "Interlake Mecalux"
    assert rec.recommended_beam.model_id == "36E"           # 2,000 lb/pair @ 144 in
    assert any("Hand-stack" in f for f in rec.flags)
    assert any("lateral bracing" in f for f in rec.flags)    # > 126 in (Interlake)
    assert any("tied together" in f for f in rec.flags)      # > 90 in with decking


def test_requires_some_load():
    with pytest.raises(ValueError):
        recommend(seismic(), pallet_height_in=31.5, beam_length_in=96, num_beam_levels=3)


def test_esfr_deflector_clearance_36in():
    std = beam_layout(48, 5, 4, False, building_clear_height_in=310)
    esfr = beam_layout(48, 5, 4, False, building_clear_height_in=310, ceiling_sprinkler="esfr")
    assert std.nfpa_ok is True        # 284 + 18 = 302 <= 310
    assert esfr.nfpa_ok is False      # 284 + 36 = 320 > 310


def test_beam_layout_hole_pitch():
    assert beam_layout(48, 5, 2, False, hole_pitch_in=2).pitch_in == 60.0


# --- project profile -------------------------------------------------------------------
def test_load_new_balance_profile():
    proj = load_project(NB)
    d = fire_inputs_dict(proj)
    assert d["jurisdiction"] == "UT" and d["ceiling_height_ft"] == 50.0
    assert d["commodity"] == "Class IV"
    assert "Open questions" in summarize(proj)


def test_new_balance_assessment_unresolved_and_flags_45ft():
    allowed = set(FireInputs.__dataclass_fields__)
    a = assess(FireInputs(**{k: v for k, v in fire_inputs_dict(load_project(NB)).items()
                             if k in allowed}))
    assert a.in_rack_status == "UNRESOLVED"          # deck open % still unknown
    assert any("45 ft" in r for r in a.rationale)
    assert a.editions["nfpa13"] == "2019"


def test_clis_run_from_project(capsys):
    assert fire_check.main(["--project", NB]) == 0
    assert levels.main(["--project", NB, "--hole-pitch", "2"]) == 0
    assert rack_cli.main(["--project", NB, "--offline", "--sds", "0.95", "--sd1", "0.42",
                          "--s1", "0.40", "--sdc", "D", "--levels", "6",
                          "--shelf-load", "1800", "--ceiling-sprinkler", "esfr"]) == 0
    out = capsys.readouterr().out
    assert "FIRE CHECK" in out and "LEVEL FIT" in out and "RACK SELECTOR" in out
