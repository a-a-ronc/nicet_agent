"""
levels — how many storage levels fit for a given load height, beam size and sprinkler choice.

Answers questions like: "31.5 in. cases, 3.5 vs 5 in. beams, with and without in-rack —
what pitch, what clear opening, and how many levels fit under the sprinklers?"

  pitch          = load height + clearance (6 in. no in-rack / 12 in. in-rack) + beam height,
                   optionally rounded UP to the upright hole pitch (2 in. teardrop typical)
  clear opening  = pitch - beam height
  top of storage = top beam + load height  <= max top of storage
  max top of storage = deflector elevation - 36 in. (ESFR/CMSA) or 18 in. (standard spray)

Usage:
  python -m rack_selector.levels --load-height 31.5 --beams 3.5,5 --deflector-height-ft 49 \
      --ceiling-sprinkler esfr --hole-pitch 2
  python -m rack_selector.levels --project projects/25-1642_new_balance_slc.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from typing import Optional

from .clearance import clearance_for

DEFLECTOR_CLEARANCE_IN = {"esfr": 36.0, "cmsa": 36.0, "standard": 18.0}
ESFR_TABLE_MAX_STORAGE_IN = 40.0 * 12  # NFPA 13 Ch. 23 K-25.2, Class I-IV / CUP


def round_up(x: float, inc: Optional[float]) -> float:
    if not inc:
        return x
    return math.ceil(x / inc - 1e-9) * inc


def max_storage_from_deflector(deflector_in: float, ceiling_sprinkler: str = "esfr") -> float:
    return deflector_in - DEFLECTOR_CLEARANCE_IN[ceiling_sprinkler.lower()]


def ft_in(x: float) -> str:
    ft = int(x // 12)
    inch = x - ft * 12
    return f"{ft}'-{inch:g}\""


@dataclass
class LevelFit:
    load_height_in: float
    beam_height_in: float
    in_rack: bool
    clearance_in: float
    pitch_in: float
    clear_opening_in: float
    first_beam_top_in: float
    beam_tops_in: list
    num_beam_levels: int
    storage_levels: int
    top_of_storage_in: Optional[float]
    limit_in: float
    headroom_in: Optional[float]


def fit_levels(load_height_in: float, beam_height_in: float, in_rack: bool,
               max_top_of_storage_in: Optional[float] = None,
               max_top_beam_in: Optional[float] = None,
               floor_level: bool = True, first_beam_top_in: Optional[float] = None,
               hole_pitch_in: Optional[float] = None) -> LevelFit:
    if max_top_of_storage_in is None and max_top_beam_in is None:
        raise ValueError("Provide max_top_of_storage_in and/or max_top_beam_in")
    clearance = clearance_for(in_rack)
    pitch = round_up(load_height_in + clearance + beam_height_in, hole_pitch_in)

    if first_beam_top_in is None:
        if not floor_level:
            raise ValueError("first_beam_top_in is required when the bottom level is on beams")
        first_beam_top_in = pitch  # floor-supported load + clearance + beam
    first_beam_top_in = round_up(first_beam_top_in, hole_pitch_in)

    # Binding limit expressed as max top-beam elevation.
    limits = []
    if max_top_of_storage_in is not None:
        limits.append(max_top_of_storage_in - load_height_in)
    if max_top_beam_in is not None:
        limits.append(max_top_beam_in)
    top_beam_limit = min(limits)

    tops = []
    e = first_beam_top_in
    while e <= top_beam_limit + 1e-6:
        tops.append(e)
        e += pitch
    n = len(tops)
    tos = (tops[-1] + load_height_in) if tops else (load_height_in if floor_level else None)
    limit_tos = top_beam_limit + load_height_in
    return LevelFit(
        load_height_in=load_height_in, beam_height_in=beam_height_in, in_rack=in_rack,
        clearance_in=clearance, pitch_in=pitch, clear_opening_in=pitch - beam_height_in,
        first_beam_top_in=first_beam_top_in, beam_tops_in=tops, num_beam_levels=n,
        storage_levels=n + (1 if floor_level else 0), top_of_storage_in=tos,
        limit_in=limit_tos, headroom_in=(limit_tos - tos) if tos is not None else None)


def compare(load_height_in: float, beams_in: list, **kw) -> list:
    """Matrix of fits for each beam height x (no in-rack, in-rack)."""
    out = []
    for b in beams_in:
        for ir in (False, True):
            out.append(fit_levels(load_height_in, b, ir, **kw))
    return out


def render(fits: list, limit_label: str) -> str:
    L = [f"LEVEL FIT — {limit_label}", "",
         f"{'beam':>6} {'in-rack':>8} {'clear':>6} {'pitch':>10} {'opening':>9} "
         f"{'beam lvls':>9} {'stor lvls':>9} {'top of stor':>12} {'headroom':>9}"]
    for f in fits:
        tos = ft_in(f.top_of_storage_in) if f.top_of_storage_in is not None else "-"
        hr = f"{f.headroom_in:.1f}\"" if f.headroom_in is not None else "-"
        L.append(f"{f.beam_height_in:>5g}\" {('yes' if f.in_rack else 'no'):>8} "
                 f"{f.clearance_in:>5g}\" {ft_in(f.pitch_in):>10} {f.clear_opening_in:>8g}\" "
                 f"{f.num_beam_levels:>9} {f.storage_levels:>9} {tos:>12} {hr:>9}")
    L.append("")
    if any(f.top_of_storage_in and f.top_of_storage_in > ESFR_TABLE_MAX_STORAGE_IN for f in fits):
        L.append("NOTE: some rows exceed 40 ft top of storage — beyond the NFPA 13 ceiling-only "
                 "ESFR table limit for Class I-IV / cartoned plastics. Cap with "
                 "--max-top-of-storage-ft 40 or plan in-rack; run rack_selector.fire_check.")
    L.append("clear = Intralog load-handling clearance (6 in. / 12 in. with in-rack). "
             "Storage levels include the floor level.")
    L.append("Beam elevations should also respect any fixed in-rack branch-line levels and "
             "the manufacturer's hole pitch. Triage only.")
    return "\n".join(L)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rack_selector.levels",
                                description="How many levels fit (nicet_agent).")
    p.add_argument("--project")
    p.add_argument("--load-height", type=float, help="Load / case height (in)")
    p.add_argument("--beams", help="Comma-separated beam heights (in), e.g. 3.5,5")
    p.add_argument("--max-top-of-storage-ft", type=float)
    p.add_argument("--max-top-beam-ft", type=float, help="e.g. frame height limit")
    p.add_argument("--deflector-height-ft", type=float)
    p.add_argument("--ceiling-sprinkler", default="esfr", choices=["esfr", "cmsa", "standard"])
    p.add_argument("--hole-pitch", type=float, default=None, help="Round pitch up (in), e.g. 2")
    p.add_argument("--no-floor-level", action="store_true")
    p.add_argument("--first-beam-top", type=float)
    p.add_argument("--json", action="store_true")
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    load_h, beams, defl_ft = a.load_height, None, a.deflector_height_ft
    if a.beams:
        beams = [float(x) for x in a.beams.split(",") if x.strip()]
    if a.project:
        from .project import load_project
        proj = load_project(a.project)
        rack, bld = proj.get("rack", {}), proj.get("building", {})
        load_h = load_h or rack.get("load_height_in")
        beams = beams or rack.get("beam_options_in") or None
        if defl_ft is None and a.max_top_of_storage_ft is None:
            defl_ft = bld.get("deflector_height_ft")
            if defl_ft is None and bld.get("ceiling_height_ft"):
                defl_ft = bld["ceiling_height_ft"] - 1.0
                print(f"(deflector assumed 1 ft below the {bld['ceiling_height_ft']} ft ceiling)",
                      file=sys.stderr)
    if not load_h or not beams:
        print("ERROR: need --load-height and --beams (or a --project with them)", file=sys.stderr)
        return 2

    max_tos = a.max_top_of_storage_ft * 12 if a.max_top_of_storage_ft else None
    label = []
    if defl_ft is not None and max_tos is None:
        max_tos = max_storage_from_deflector(defl_ft * 12, a.ceiling_sprinkler)
        label.append(f"deflector {defl_ft:g} ft - {DEFLECTOR_CLEARANCE_IN[a.ceiling_sprinkler]:g} in. "
                     f"({a.ceiling_sprinkler.upper()}) -> max top of storage {ft_in(max_tos)}")
    elif max_tos is not None:
        label.append(f"max top of storage {ft_in(max_tos)}")
    max_tb = a.max_top_beam_ft * 12 if a.max_top_beam_ft else None
    if max_tb:
        label.append(f"max top beam {ft_in(max_tb)}")
    if max_tos is None and max_tb is None:
        print("ERROR: give --deflector-height-ft, --max-top-of-storage-ft or --max-top-beam-ft",
              file=sys.stderr)
        return 2

    fits = compare(load_h, beams, max_top_of_storage_in=max_tos, max_top_beam_in=max_tb,
                   floor_level=not a.no_floor_level, first_beam_top_in=a.first_beam_top,
                   hole_pitch_in=a.hole_pitch)
    if a.json:
        print(json.dumps([asdict(f) for f in fits], indent=2))
    else:
        print(render(fits, "; ".join(label)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
