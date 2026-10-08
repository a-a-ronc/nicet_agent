"""
Beam-elevation / clearance layout using the Intralog convention:
  +6 in. load-handling clearance per level where there are NO in-rack sprinklers,
  +12 in. where in-rack sprinklers are present (room for IRAS piping/distribution).

Also checks the NFPA 13 rule: top of storage + 18 in. <= ceiling sprinkler deflector
(approximated here as building clear height; the deflector sits at/just below it).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

NFPA_DEFLECTOR_CLEARANCE_IN = 18.0


def clearance_for(in_rack_sprinklers: bool) -> float:
    """Intralog vertical load-handling clearance per level (inches)."""
    return 12.0 if in_rack_sprinklers else 6.0


@dataclass
class BeamLayout:
    pallet_height_in: float
    beam_height_in: float
    clearance_in: float
    num_beam_levels: int
    floor_level: bool
    first_beam_top_in: float
    pitch_in: float
    beam_top_elevations_in: list
    top_of_storage_in: float
    required_frame_height_in: float
    max_beam_spacing_in: float
    storage_levels: int
    building_clear_height_in: Optional[float] = None
    nfpa_ok: Optional[bool] = None
    flags: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "pallet_height_in": self.pallet_height_in,
            "beam_height_in": self.beam_height_in,
            "clearance_in": self.clearance_in,
            "num_beam_levels": self.num_beam_levels,
            "floor_level": self.floor_level,
            "storage_levels": self.storage_levels,
            "first_beam_top_in": round(self.first_beam_top_in, 1),
            "pitch_in": round(self.pitch_in, 1),
            "beam_top_elevations_in": [round(e, 1) for e in self.beam_top_elevations_in],
            "top_of_storage_in": round(self.top_of_storage_in, 1),
            "required_frame_height_in": round(self.required_frame_height_in, 1),
            "max_beam_spacing_in": round(self.max_beam_spacing_in, 1),
            "building_clear_height_in": self.building_clear_height_in,
            "nfpa_18in_deflector_ok": self.nfpa_ok,
            "flags": self.flags,
        }


def beam_layout(pallet_height_in: float, beam_height_in: float, num_beam_levels: int,
                in_rack_sprinklers: bool, floor_level: bool = True,
                first_beam_top_in: Optional[float] = None,
                building_clear_height_in: Optional[float] = None) -> BeamLayout:
    """
    Compute beam top elevations and clearance checks.

    floor_level       : True if the bottom storage level sits on the slab (no beam).
    first_beam_top_in : top elevation of the lowest BEAM. Defaults to one full
                        load+clearance+beam pitch above the floor when floor_level,
                        else to one (pallet_height) when the first level is a beam at grade.
    """
    if num_beam_levels < 1:
        raise ValueError("num_beam_levels must be >= 1")

    clearance = clearance_for(in_rack_sprinklers)
    pitch = pallet_height_in + clearance + beam_height_in

    if first_beam_top_in is None:
        # Lowest beam sits one pitch above the floor (above the floor-supported load),
        # or at one pallet_height + clearance + beam if the first level is a beam at grade.
        first_beam_top_in = pitch if floor_level else (pallet_height_in + clearance + beam_height_in)

    beam_tops = [first_beam_top_in + i * pitch for i in range(num_beam_levels)]
    top_beam = beam_tops[-1]
    top_of_storage = top_beam + pallet_height_in
    required_frame_height = top_beam  # frame must reach the top beam connection

    # Max beam spacing governs frame capacity (floor-to-first-beam, or pitch).
    max_beam_spacing = max(first_beam_top_in, pitch)
    storage_levels = num_beam_levels + (1 if floor_level else 0)

    flags: list[str] = []
    nfpa_ok: Optional[bool] = None
    if building_clear_height_in is not None:
        nfpa_ok = (top_of_storage + NFPA_DEFLECTOR_CLEARANCE_IN) <= building_clear_height_in + 1e-6
        if not nfpa_ok:
            need = top_of_storage + NFPA_DEFLECTOR_CLEARANCE_IN
            flags.append(
                f"NFPA 13: top of storage ({top_of_storage:.1f} in) + 18 in = {need:.1f} in "
                f"exceeds building clear height ({building_clear_height_in:.1f} in). "
                f"Lower storage, raise ceiling, or reduce levels."
            )
        if required_frame_height > building_clear_height_in + 1e-6:
            flags.append(
                f"Top beam ({required_frame_height:.1f} in) is above building clear height "
                f"({building_clear_height_in:.1f} in)."
            )

    return BeamLayout(
        pallet_height_in=pallet_height_in, beam_height_in=beam_height_in,
        clearance_in=clearance, num_beam_levels=num_beam_levels, floor_level=floor_level,
        first_beam_top_in=first_beam_top_in, pitch_in=pitch,
        beam_top_elevations_in=beam_tops, top_of_storage_in=top_of_storage,
        required_frame_height_in=required_frame_height, max_beam_spacing_in=max_beam_spacing,
        storage_levels=storage_levels, building_clear_height_in=building_clear_height_in,
        nfpa_ok=nfpa_ok, flags=flags,
    )
