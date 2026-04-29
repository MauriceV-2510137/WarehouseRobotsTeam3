"""
WarehouseMap – coordinate resolution tests.

Verifies that aisle/shelf coordinates are resolved correctly and that
invalid inputs are rejected.
"""
import pytest
from server.core.warehouse.warehouse_map import WarehouseMap

MAP = WarehouseMap()

AISLE_ENTRY_X = 3.0
SHELF_X = {1: 4.5, 2: 5.5, 3: 6.5}
AISLE_Y = {1: 4.0, 2: 2.0, 3: 0.0, 4: -2.0, 5: -4.0}


# ── Valid coordinates ────────────────────────────────────────────────────────

@pytest.mark.parametrize("aisle,shelf", [
    (a, s) for a in range(1, 6) for s in range(1, 4)
])
def test_all_valid_combinations_resolve(aisle, shelf):
    loc = MAP.resolve(aisle, shelf)
    assert loc is not None


def test_aisle_entry_x_is_correct():
    for aisle in range(1, 6):
        loc = MAP.resolve(aisle, 1)
        assert loc.aisle_pos[0] == pytest.approx(AISLE_ENTRY_X)


def test_shelf_x_coordinates():
    for shelf, expected_x in SHELF_X.items():
        loc = MAP.resolve(1, shelf)
        assert loc.segment_pos[0] == pytest.approx(expected_x)


def test_aisle_y_coordinates():
    for aisle, expected_y in AISLE_Y.items():
        loc = MAP.resolve(aisle, 1)
        assert loc.aisle_pos[1] == pytest.approx(expected_y)
        assert loc.segment_pos[1] == pytest.approx(expected_y)


# ── Invalid inputs ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("aisle", [0, 6, -1, 100])
def test_invalid_aisle_raises(aisle):
    with pytest.raises(ValueError):
        MAP.resolve(aisle, 1)


@pytest.mark.parametrize("shelf", [0, 4, -1, 100])
def test_invalid_shelf_raises(shelf):
    with pytest.raises(ValueError):
        MAP.resolve(1, shelf)
