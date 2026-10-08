import pytest

from rack_selector.clearance import beam_layout, clearance_for


def test_clearance_convention():
    assert clearance_for(False) == 6.0
    assert clearance_for(True) == 12.0


def test_pitch_and_elevations_no_inrack():
    lay = beam_layout(pallet_height_in=48, beam_height_in=5, num_beam_levels=4,
                      in_rack_sprinklers=False, floor_level=True)
    assert lay.clearance_in == 6.0
    assert lay.pitch_in == pytest.approx(59.0)        # 48 + 6 + 5
    assert lay.beam_top_elevations_in == pytest.approx([59, 118, 177, 236])
    assert lay.top_of_storage_in == pytest.approx(284.0)  # 236 + 48
    assert lay.storage_levels == 5                     # 4 beam levels + floor


def test_inrack_uses_12in_clearance():
    lay = beam_layout(pallet_height_in=48, beam_height_in=5, num_beam_levels=3,
                      in_rack_sprinklers=True, floor_level=True)
    assert lay.clearance_in == 12.0
    assert lay.pitch_in == pytest.approx(65.0)         # 48 + 12 + 5


def test_nfpa_18in_pass_and_fail():
    ok = beam_layout(48, 5, 4, in_rack_sprinklers=False, building_clear_height_in=384)
    assert ok.nfpa_ok is True
    assert ok.flags == []

    bad = beam_layout(48, 5, 6, in_rack_sprinklers=False, building_clear_height_in=300)
    assert bad.nfpa_ok is False
    assert any("NFPA 13" in f for f in bad.flags)


def test_invalid_levels():
    with pytest.raises(ValueError):
        beam_layout(48, 5, 0, in_rack_sprinklers=False)
