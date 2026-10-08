"""
Orchestration: turn site seismic + product + configuration into a rack recommendation.

Selection logic (triage level):
  * Required beam-pair capacity = pallets_per_bay x pallet_weight.
  * Required frame axial = pallets_per_bay x pallet_weight x beam_levels (interior frame
    carries one full bay per level; floor-level load goes to the slab, not the frame).
  * Beams/frames are chosen as the lightest sufficient option PER DEALER, then ordered by
    dealer priority (Interlake Mecalux > SpaceRAK > Hannibal/Nucor).
  * Seismic base shear V = Cs x Ws is reported per bay; Cs already contains Ie/Ip.

All numbers are triage estimates — confirm against manufacturer SEISMIC load tables and
have a licensed PE review before procurement or construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .catalog import Catalog, BeamOption, FrameOption
from .clearance import beam_layout, BeamLayout
from .seismic import SeismicResult, seismic_weight, base_shear, sdc_requirements

# Rough ESFR ceiling-only envelope for the in-rack advisory (see knowledge_base/nfpa13.md).
ESFR_MAX_STORAGE_FT = 35.0
ESFR_MAX_CEILING_FT = 40.0
HIGH_HAZARD_CLASSES = {"IV", "CLASS IV", "GROUP A", "A PLASTIC", "PLASTIC"}
DEFAULT_DEAD_LOAD_FRACTION = 0.05  # rack steel as fraction of product load (estimate)


@dataclass
class RackRecommendation:
    seismic: SeismicResult
    layout: BeamLayout
    required_beam_pair_lb: float
    required_frame_axial_lb: float
    recommended_beam: Optional[BeamOption]
    beam_alternatives: list
    recommended_frame: Optional[FrameOption]
    frame_alternatives: list
    seismic_weight_per_bay_lb: float
    base_shear_down_aisle_lb: float
    base_shear_cross_aisle_lb: float
    fire_note: str
    flags: list = field(default_factory=list)
    review_required: str = (
        "TRIAGE ONLY — not a stamped design. Confirm all capacities against manufacturer "
        "SEISMIC load tables and obtain licensed PE/FPE review before procurement or build."
    )

    def as_dict(self) -> dict:
        def beam_d(b):
            return None if b is None else {
                "dealer": b.dealer, "model": b.model_id, "face_in": b.face_in,
                "gauge": b.gauge, "length_in": b.length_in,
                "capacity_pair_lb": b.capacity_pair_lb, "confidence": b.confidence,
            }

        def frame_d(f):
            return None if f is None else {
                "dealer": f.dealer, "model": f.model_id, "column": f.column,
                "depth_in": f.depth_in, "unsupported_length_in": f.unsupported_length_in,
                "capacity_lb": f.capacity_lb, "confidence": f.confidence,
            }

        return {
            "seismic": self.seismic.as_dict(),
            "layout": self.layout.as_dict(),
            "required_beam_pair_lb": round(self.required_beam_pair_lb, 0),
            "required_frame_axial_lb": round(self.required_frame_axial_lb, 0),
            "recommended_beam": beam_d(self.recommended_beam),
            "beam_alternatives": [beam_d(b) for b in self.beam_alternatives],
            "recommended_frame": frame_d(self.recommended_frame),
            "frame_alternatives": [frame_d(f) for f in self.frame_alternatives],
            "seismic_weight_per_bay_lb": round(self.seismic_weight_per_bay_lb, 0),
            "base_shear_down_aisle_lb": round(self.base_shear_down_aisle_lb, 0),
            "base_shear_cross_aisle_lb": round(self.base_shear_cross_aisle_lb, 0),
            "fire_note": self.fire_note,
            "flags": self.flags,
            "review_required": self.review_required,
        }


def _fire_advisory(commodity_class: str, storage_ft: float, ceiling_ft: Optional[float],
                   in_rack: bool) -> str:
    cc = (commodity_class or "").upper().strip()
    high_hazard = any(h in cc for h in HIGH_HAZARD_CLASSES)
    within_esfr = storage_ft <= ESFR_MAX_STORAGE_FT and (
        ceiling_ft is None or ceiling_ft <= ESFR_MAX_CEILING_FT)
    if in_rack:
        return ("In-rack sprinklers assumed PRESENT -> 12 in. clearance applied. Verify "
                "in-rack level placement and piping per NFPA 13 Ch. 20-25 (or FM DS 8-9).")
    if high_hazard and not within_esfr:
        return ("High-hazard commodity above the typical ESFR ceiling-only envelope "
                f"(~{ESFR_MAX_STORAGE_FT:.0f} ft storage / {ESFR_MAX_CEILING_FT:.0f} ft "
                "ceiling). In-rack sprinklers are LIKELY required — re-run with in-rack = "
                "True (12 in. clearance) once the FPE confirms.")
    if not within_esfr:
        return ("Storage/ceiling near or above the typical ESFR envelope — confirm the "
                "ceiling-only ESFR listing or expect in-rack sprinklers.")
    return ("Within the typical ESFR ceiling-only envelope; no in-rack assumed (6 in. "
            "clearance). Confirm the ESFR listing for this commodity/height with the FPE.")


def recommend(seismic: SeismicResult, *, pallet_weight_lb: float, pallet_height_in: float,
              beam_length_in: float, num_beam_levels: int, pallets_per_bay: int = 2,
              in_rack_sprinklers: bool = False, floor_level: bool = True,
              building_clear_height_in: Optional[float] = None,
              commodity_class: str = "", dead_load_fraction: float = DEFAULT_DEAD_LOAD_FRACTION,
              catalog: Optional[Catalog] = None) -> RackRecommendation:
    cat = catalog or Catalog()
    flags: list[str] = []

    # --- beam demand & selection ---
    required_pair = pallets_per_bay * pallet_weight_lb
    beam_best = cat.best_beam_per_dealer(beam_length_in, required_pair)
    beam_ordered = cat.order_by_priority(beam_best)
    rec_beam = beam_ordered[0] if beam_ordered else None
    if rec_beam is None:
        flags.append(
            f"No catalogued beam meets {required_pair:,.0f} lb/pair at {beam_length_in:.0f} in. "
            "Increase beam size/dealer data, reduce pallets/bay, or shorten the bay.")
        beam_height = 5.0  # assume for layout so the rest still computes
    else:
        beam_height = rec_beam.face_in
        if rec_beam.confidence == "representative":
            flags.append(
                f"Recommended beam ({rec_beam.dealer} {rec_beam.model_id}) capacity is "
                "REPRESENTATIVE — confirm against the dealer's published load table.")

    # --- elevation layout ---
    layout = beam_layout(
        pallet_height_in=pallet_height_in, beam_height_in=beam_height,
        num_beam_levels=num_beam_levels, in_rack_sprinklers=in_rack_sprinklers,
        floor_level=floor_level, building_clear_height_in=building_clear_height_in)
    flags.extend(layout.flags)

    # --- frame demand & selection ---
    required_frame = pallets_per_bay * pallet_weight_lb * num_beam_levels
    frame_best = cat.best_frame_per_dealer(
        layout.max_beam_spacing_in, required_frame, layout.required_frame_height_in)
    frame_ordered = cat.order_by_priority(frame_best)
    rec_frame = frame_ordered[0] if frame_ordered else None
    if rec_frame is None:
        flags.append(
            f"No catalogued frame meets {required_frame:,.0f} lb at "
            f"{layout.max_beam_spacing_in:.0f} in unsupported length. Add bracing/rows, "
            "use a heavier column, or extend dealer data.")
    elif rec_frame.confidence == "representative":
        flags.append(
            f"Recommended frame ({rec_frame.dealer} {rec_frame.model_id}) capacity is "
            "REPRESENTATIVE — confirm against the dealer's published load table.")

    if layout.required_frame_height_in > 288.0:
        flags.append(
            f"Required frame height {layout.required_frame_height_in:.0f} in (>24 ft) — "
            "verify column availability and the H:D ratio (<=6:1 single-row).")

    # --- seismic magnitude (per bay) ---
    storage_levels = layout.storage_levels
    product_load = pallets_per_bay * pallet_weight_lb * storage_levels
    dead_load = dead_load_fraction * product_load
    ws = seismic_weight(dead_load, product_load)
    v_down = base_shear(seismic.cs_down_aisle or 0.0, ws)
    v_cross = base_shear(seismic.cs_cross_aisle or 0.0, ws)

    flags.extend(sdc_requirements(seismic.sdc))

    storage_ft = layout.top_of_storage_in / 12.0
    ceiling_ft = (building_clear_height_in / 12.0) if building_clear_height_in else None
    fire_note = _fire_advisory(commodity_class, storage_ft, ceiling_ft, in_rack_sprinklers)

    return RackRecommendation(
        seismic=seismic, layout=layout,
        required_beam_pair_lb=required_pair, required_frame_axial_lb=required_frame,
        recommended_beam=rec_beam, beam_alternatives=beam_ordered[1:],
        recommended_frame=rec_frame, frame_alternatives=frame_ordered[1:],
        seismic_weight_per_bay_lb=ws, base_shear_down_aisle_lb=v_down,
        base_shear_cross_aisle_lb=v_cross, fire_note=fire_note, flags=flags,
    )


def render_report(rec: RackRecommendation) -> str:
    s = rec.seismic
    lay = rec.layout
    L = []
    L.append("=" * 70)
    L.append("  RACK SELECTOR — TRIAGE RECOMMENDATION (not a stamped design)")
    L.append("=" * 70)
    L.append("")
    L.append(f"SITE  {s.latitude:.4f}, {s.longitude:.4f}  | Risk Cat {s.risk_category} "
             f"| Site Class {s.site_class}")
    L.append(f"  SDS={s.sds:.3f}g  SD1={s.sd1:.3f}g  S1={s.s1:.3f}g  -> SDC {s.sdc}")
    L.append(f"  Cs down-aisle (R={6.0}) = {s.cs_down_aisle:.3f}   "
             f"Cs cross-aisle (R={4.0}) = {s.cs_cross_aisle:.3f}")
    L.append("")
    L.append("CONFIGURATION")
    L.append(f"  Beam levels: {lay.num_beam_levels}  (storage levels: {lay.storage_levels}"
             f"{' incl. floor' if lay.floor_level else ''})")
    L.append(f"  Pitch: {lay.pitch_in:.1f} in  | Clearance/level: {lay.clearance_in:.0f} in"
             f"  | Beam height: {lay.beam_height_in:.2f} in")
    L.append(f"  Beam top elevations (in): "
             f"{', '.join(f'{e:.0f}' for e in lay.beam_top_elevations_in)}")
    L.append(f"  Top of storage: {lay.top_of_storage_in:.0f} in "
             f"({lay.top_of_storage_in/12:.1f} ft)  | Frame height >= "
             f"{lay.required_frame_height_in:.0f} in")
    if lay.building_clear_height_in:
        ok = "OK" if lay.nfpa_ok else "FAIL"
        L.append(f"  NFPA 18 in. to deflector vs clear height "
                 f"{lay.building_clear_height_in:.0f} in: {ok}")
    L.append("")
    L.append("DEMAND")
    L.append(f"  Required beam capacity: {rec.required_beam_pair_lb:,.0f} lb/pair "
             f"@ {lay and rec.recommended_beam.length_in if rec.recommended_beam else '?'} in")
    L.append(f"  Required frame axial:   {rec.required_frame_axial_lb:,.0f} lb "
             f"(unsupported len {lay.max_beam_spacing_in:.0f} in)")
    L.append(f"  Seismic weight/bay Ws:  {rec.seismic_weight_per_bay_lb:,.0f} lb")
    L.append(f"  Base shear/bay: down-aisle {rec.base_shear_down_aisle_lb:,.0f} lb | "
             f"cross-aisle {rec.base_shear_cross_aisle_lb:,.0f} lb")
    L.append("")
    L.append("RECOMMENDATION  (dealer priority: Interlake Mecalux > SpaceRAK > Hannibal/Nucor)")
    if rec.recommended_beam:
        b = rec.recommended_beam
        util = rec.required_beam_pair_lb / b.capacity_pair_lb * 100
        L.append(f"  BEAM : {b.dealer} {b.model_id}  {b.face_in}\" face {b.gauge}ga  "
                 f"@ {b.length_in:.0f}\"  cap {b.capacity_pair_lb:,.0f} lb/pair  "
                 f"(util {util:.0f}%, {b.confidence})")
    else:
        L.append("  BEAM : none meets demand — see flags.")
    if rec.recommended_frame:
        f = rec.recommended_frame
        util = rec.required_frame_axial_lb / f.capacity_lb * 100
        L.append(f"  FRAME: {f.dealer} {f.model_id}  {f.column}  depth {f.depth_in} in  "
                 f"cap {f.capacity_lb:,.0f} lb  (util {util:.0f}%, {f.confidence})")
    else:
        L.append("  FRAME: none meets demand — see flags.")
    if rec.beam_alternatives:
        L.append("  Beam alternatives: " +
                 ", ".join(f"{b.dealer} {b.model_id}" for b in rec.beam_alternatives))
    if rec.frame_alternatives:
        L.append("  Frame alternatives: " +
                 ", ".join(f"{f.dealer} {f.model_id}" for f in rec.frame_alternatives))
    L.append("")
    L.append("FIRE PROTECTION")
    L.append("  " + rec.fire_note)
    L.append("")
    L.append("FLAGS / REQUIREMENTS")
    for fl in rec.flags:
        L.append(f"  - {fl}")
    L.append("")
    L.append("** " + rec.review_required + " **")
    return "\n".join(L)
