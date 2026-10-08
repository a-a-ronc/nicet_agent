"""
Rack component catalog access + capacity lookup.

Beam capacities are per PAIR, by length. Frame capacities are per single frame, by max
unsupported length. Lookups are CONSERVATIVE: when the requested length is between
tabulated values, the next-longer tabulated entry is used (lower capacity).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

_DEFAULT_CATALOG = os.path.join(os.path.dirname(__file__), "data", "rack_catalog.json")


@dataclass
class BeamOption:
    dealer: str
    family: str
    model_id: str
    face_in: float
    gauge: int
    length_in: float
    capacity_pair_lb: float
    confidence: str
    source: str
    lateral_bracing_over_in: Optional[float] = None
    deck_tie_over_in: Optional[float] = None


@dataclass
class FrameOption:
    dealer: str
    family: str
    model_id: str
    column: str
    depth_in: list
    unsupported_length_in: float
    capacity_lb: float
    confidence: str
    source: str


class Catalog:
    def __init__(self, path: Optional[str] = None):
        self.path = path or _DEFAULT_CATALOG
        with open(self.path, "r", encoding="utf-8") as fh:
            self.data = json.load(fh)
        self.dealer_priority = self.data["_meta"]["dealer_priority"]

    # ---- helpers ---------------------------------------------------------------

    @staticmethod
    def _capacity_at(table: dict, requested: float) -> Optional[tuple[float, float]]:
        """
        Given {length_str: capacity}, return (used_length, capacity) for the smallest
        tabulated length >= requested (conservative). If requested exceeds all tabulated
        lengths, return the longest available (caller should flag). None if empty.
        """
        if not table:
            return None
        pairs = sorted((float(k), float(v)) for k, v in table.items())
        for length, cap in pairs:
            if length >= requested - 1e-6:
                return length, cap
        return pairs[-1]  # requested longer than max tabulated -> flag upstream

    def _dealer_rank(self, dealer: str) -> int:
        try:
            return self.dealer_priority.index(dealer)
        except ValueError:
            return len(self.dealer_priority)

    # ---- beam selection --------------------------------------------------------

    def beams_meeting(self, length_in: float, required_pair_lb: float) -> list[BeamOption]:
        """All beam options (any dealer) whose capacity at length_in >= required."""
        out: list[BeamOption] = []
        for fam in self.data["beams"]:
            for m in fam["models"]:
                res = self._capacity_at(m["capacity_by_length_lb"], length_in)
                if res is None:
                    continue
                used_len, cap = res
                if cap >= required_pair_lb and used_len >= length_in - 1e-6:
                    out.append(BeamOption(
                        dealer=fam["dealer"], family=fam["family"], model_id=m["id"],
                        face_in=m["face_in"], gauge=m["gauge"], length_in=length_in,
                        capacity_pair_lb=cap, confidence=fam["confidence"],
                        source=fam["source"],
                        lateral_bracing_over_in=fam.get("lateral_bracing_over_in"),
                        deck_tie_over_in=fam.get("deck_tie_over_in"),
                    ))
        return out

    def best_beam_per_dealer(self, length_in: float, required_pair_lb: float
                             ) -> dict[str, BeamOption]:
        """Lightest sufficient beam (smallest face, then lowest capacity) per dealer."""
        best: dict[str, BeamOption] = {}
        for opt in self.beams_meeting(length_in, required_pair_lb):
            cur = best.get(opt.dealer)
            if cur is None or (opt.face_in, opt.capacity_pair_lb) < (cur.face_in, cur.capacity_pair_lb):
                best[opt.dealer] = opt
        return best

    # ---- frame selection -------------------------------------------------------

    def frames_meeting(self, unsupported_length_in: float, required_lb: float,
                       required_height_in: float) -> list[FrameOption]:
        out: list[FrameOption] = []
        for fam in self.data["frames"]:
            for m in fam["models"]:
                res = self._capacity_at(m["capacity_by_unsupported_length_lb"],
                                        unsupported_length_in)
                if res is None:
                    continue
                used_len, cap = res
                if cap >= required_lb and used_len >= unsupported_length_in - 1e-6:
                    out.append(FrameOption(
                        dealer=fam["dealer"], family=fam["family"], model_id=m["id"],
                        column=m["column"], depth_in=fam.get("depth_in", []),
                        unsupported_length_in=unsupported_length_in, capacity_lb=cap,
                        confidence=fam["confidence"], source=fam["source"],
                    ))
        return out

    def best_frame_per_dealer(self, unsupported_length_in: float, required_lb: float,
                              required_height_in: float) -> dict[str, FrameOption]:
        best: dict[str, FrameOption] = {}
        for opt in self.frames_meeting(unsupported_length_in, required_lb, required_height_in):
            cur = best.get(opt.dealer)
            if cur is None or opt.capacity_lb < cur.capacity_lb:
                best[opt.dealer] = opt
        return best

    def order_by_priority(self, per_dealer: dict) -> list:
        return [per_dealer[d] for d in sorted(per_dealer, key=self._dealer_rank)]
