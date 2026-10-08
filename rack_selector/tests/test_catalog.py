import pytest

from rack_selector.catalog import Catalog


@pytest.fixture(scope="module")
def cat():
    return Catalog()


def test_dealer_priority_loaded(cat):
    assert cat.dealer_priority[0] == "Interlake Mecalux"
    assert "SpaceRAK" in cat.dealer_priority
    assert "Hannibal/Nucor" in cat.dealer_priority


def test_conservative_length_lookup_rounds_up(cat):
    # SpaceRAK 506M: 96in=7020, 108in=6344. Requesting 100in must use the 108in value.
    table = None
    for fam in cat.data["beams"]:
        if fam["dealer"] == "SpaceRAK":
            for m in fam["models"]:
                if m["id"] == "506M":
                    table = m["capacity_by_length_lb"]
    used_len, cap = Catalog._capacity_at(table, 100)
    assert used_len == 108
    assert cap == 6344


def test_best_beam_per_dealer_returns_sufficient(cat):
    best = cat.best_beam_per_dealer(length_in=96, required_pair_lb=5000)
    assert "Interlake Mecalux" in best
    for opt in best.values():
        assert opt.capacity_pair_lb >= 5000


def test_order_by_priority_puts_interlake_first(cat):
    best = cat.best_beam_per_dealer(length_in=96, required_pair_lb=5000)
    ordered = cat.order_by_priority(best)
    assert ordered[0].dealer == "Interlake Mecalux"


def test_best_frame_per_dealer(cat):
    best = cat.best_frame_per_dealer(unsupported_length_in=60, required_lb=20000,
                                     required_height_in=236)
    assert best  # at least one dealer qualifies
    for opt in best.values():
        assert opt.capacity_lb >= 20000
