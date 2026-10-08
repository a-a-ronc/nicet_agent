import json
import math
import os

import pytest

from rack_selector.seismic import (compute_cs, seismic_weight, base_shear,
                                    sdc_requirements, seismic_result_from_usgs,
                                    endpoint_for)

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "usgs_asce7_22_saltlake.json")


def test_compute_cs_short_period_value():
    # Cs = SDS / (R/Ie); SDS=1.0, R=6, Ie=1 -> 0.1667
    assert compute_cs(1.0, 0.6, 0.55, r=6.0, ie=1.0) == pytest.approx(1.0 / 6.0, rel=1e-6)


def test_compute_cs_high_s1_minimum_controls():
    # Low SDS but S1>=0.6 forces Eq 12.8-6 minimum = 0.5*S1/(R/Ie)
    cs = compute_cs(sds=0.05, sd1=0.05, s1=0.75, r=6.0, ie=1.0)
    assert cs == pytest.approx(0.5 * 0.75 / 6.0, rel=1e-6)


def test_compute_cs_absolute_floor():
    cs = compute_cs(sds=0.05, sd1=0.02, s1=0.1, r=6.0, ie=1.0)
    # floor = max(0.044*SDS*Ie, 0.01) = max(0.0022, 0.01) = 0.01
    assert cs == pytest.approx(0.01, rel=1e-6)


def test_compute_cs_period_cap_reduces():
    no_cap = compute_cs(1.0, 0.6, 0.55, r=6.0, ie=1.0)
    with_cap = compute_cs(1.0, 0.6, 0.55, r=6.0, ie=1.0, t=2.0)  # long period -> lower
    assert with_cap < no_cap


def test_importance_factor_increases_cs():
    base = compute_cs(1.0, 0.6, 0.3, r=6.0, ie=1.0)
    public = compute_cs(1.0, 0.6, 0.3, r=6.0, ie=1.5)
    assert public > base


def test_invalid_inputs():
    with pytest.raises(ValueError):
        compute_cs(1.0, 0.6, 0.3, r=0.0)
    with pytest.raises(ValueError):
        seismic_weight(100, 1000, prf=0.0)


def test_seismic_weight_and_base_shear():
    ws = seismic_weight(dead_load_lb=100, product_load_lb=1000, prf=0.67)
    assert ws == pytest.approx(770.0)
    assert base_shear(0.2, ws) == pytest.approx(154.0)


def test_sdc_requirements_mention_overstrength_for_D():
    reqs = " ".join(sdc_requirements("D")).lower()
    assert "overstrength" in reqs
    assert "anchor" in reqs


def test_endpoint_selection():
    assert endpoint_for("ASCE7-22").endswith("asce7-22.json")
    assert endpoint_for("ASCE7-16").endswith("asce7-16.json")
    assert endpoint_for("asce 7-16").endswith("asce7-16.json")  # tolerant of formatting
    with pytest.raises(ValueError):
        endpoint_for("ASCE7-10")


def test_result_from_usgs_fixture():
    with open(FIX) as fh:
        data = json.load(fh)
    res = seismic_result_from_usgs(data, 40.76, -111.89, "II", "Default")
    assert res.sdc == "D"
    assert res.cs_down_aisle == pytest.approx(1.0 / 6.0, rel=1e-6)
    assert res.cs_cross_aisle == pytest.approx(1.0 / 4.0, rel=1e-6)
    # cross-aisle (lower R) must demand more than down-aisle
    assert res.cs_cross_aisle > res.cs_down_aisle
