import pytest

from rack_selector.levels import compare, fit_levels, max_storage_from_deflector, round_up


def test_pitch_and_opening_matrix_for_31_5in_case():
    f5 = fit_levels(31.5, 5.0, False, max_top_of_storage_in=600)
    assert f5.pitch_in == pytest.approx(42.5) and f5.clear_opening_in == pytest.approx(37.5)
    f35_ir = fit_levels(31.5, 3.5, True, max_top_of_storage_in=600)
    assert f35_ir.pitch_in == pytest.approx(47.0) and f35_ir.clear_opening_in == pytest.approx(43.5)


def test_hole_pitch_rounds_up():
    f = fit_levels(31.5, 5.0, False, max_top_of_storage_in=600, hole_pitch_in=2)
    assert f.pitch_in == 44.0
    assert round_up(41.0, 2) == 42.0 and round_up(42.0, 2) == 42.0


def test_level_count_under_limit():
    f = fit_levels(31.5, 5.0, False, max_top_of_storage_in=330)
    assert f.num_beam_levels == 7          # tops 42.5 .. 297.5
    assert f.storage_levels == 8           # + floor
    assert f.top_of_storage_in == pytest.approx(329.0)
    assert f.headroom_in == pytest.approx(1.0)


def test_max_top_beam_limit():
    f = fit_levels(31.5, 5.0, False, max_top_beam_in=170)
    assert f.beam_tops_in[-1] <= 170


def test_deflector_limit():
    assert max_storage_from_deflector(49 * 12, "esfr") == 49 * 12 - 36
    assert max_storage_from_deflector(49 * 12, "standard") == 49 * 12 - 18


def test_compare_shape():
    fits = compare(31.5, [3.5, 5.0], max_top_of_storage_in=552)
    assert len(fits) == 4
    assert [f.in_rack for f in fits] == [False, True, False, True]


def test_errors():
    with pytest.raises(ValueError):
        fit_levels(31.5, 5.0, False)
    with pytest.raises(ValueError):
        fit_levels(31.5, 5.0, False, max_top_of_storage_in=300, floor_level=False)
