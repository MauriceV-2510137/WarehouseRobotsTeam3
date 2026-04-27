from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class AisleLocation:
    aisle_pos:   tuple[float, float]
    segment_pos: tuple[float, float]

_AISLE_Y: dict[int, float] = {
    1:  4.0,
    2:  2.0,
    3:  0.0,
    4: -2.0,
    5: -4.0,
}

_SHELF_X: dict[int, float] = {
    1: 4.5,
    2: 5.5,
    3: 6.5,
}

_AISLE_ENTRY_X: float = 3.0

_MAP: dict[tuple[int, int], AisleLocation] = {
    (aisle, shelf): AisleLocation(
        aisle_pos=(_AISLE_ENTRY_X, aisle_y),
        segment_pos=(shelf_x, aisle_y),
    )
    for aisle, aisle_y in _AISLE_Y.items()
    for shelf, shelf_x in _SHELF_X.items()
}

class WarehouseMap:
    AISLE_RANGE = range(1, 6) # 1...5
    SHELF_RANGE = range(1, 4) # 1...3

    def resolve(self, aisle: int, shelf: int) -> AisleLocation:
        if aisle not in self.AISLE_RANGE:
            raise ValueError(f"Invalid aisle '{aisle}'. Must be in {list(self.AISLE_RANGE)}.")
        if shelf not in self.SHELF_RANGE:
            raise ValueError(f"Invalid shelf '{shelf}'. Must be in {list(self.SHELF_RANGE)}.")

        location = _MAP.get((aisle, shelf))
        if location is None:
            raise KeyError(f"No location found for aisle={aisle}, shelf={shelf}.")

        return location