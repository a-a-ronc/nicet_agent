"""
Command-line interface for the rack selector.

Examples
--------
  # ZIP-based, auto-fetch ASCE 7-22 seismic from USGS
  python -m rack_selector --zip 84101 --pallet-weight 2500 --pallet-height 48 \
      --beam-length 96 --levels 4 --pallets-per-bay 2 --clear-height 384 \
      --commodity "Class IV"

  # lat/long directly, JSON output
  python -m rack_selector --lat 40.76 --lon -111.89 --pallet-weight 2000 \
      --pallet-height 50 --beam-length 108 --levels 5 --json

  # fully offline (skip network): supply seismic params yourself
  python -m rack_selector --offline --sds 1.0 --sd1 0.6 --s1 0.55 --sdc D \
      --lat 40.76 --lon -111.89 --pallet-weight 2000 --pallet-height 50 \
      --beam-length 108 --levels 5
"""

from __future__ import annotations

import argparse
import json
import sys

from .seismic import (SeismicResult, seismic_result_from_usgs, fetch_seismic, compute_cs,
                      R_DOWN_AISLE, R_CROSS_AISLE)
from .geocode import resolve_location
from .selector import recommend, render_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rack_selector",
        description="OneRack-style seismic rack-selection triage tool (nicet_agent).")

    loc = p.add_argument_group("location")
    loc.add_argument("--zip", dest="zip_code", help="US ZIP code")
    loc.add_argument("--address", help="One-line US address")
    loc.add_argument("--lat", type=float, help="Latitude (decimal degrees)")
    loc.add_argument("--lon", type=float, help="Longitude (decimal degrees)")
    loc.add_argument("--risk-category", default=None, choices=["I", "II", "III", "IV"],
                     help="Default II")
    loc.add_argument("--site-class", default=None,
                     choices=["Default", "A", "B", "BC", "C", "CD", "D", "DE", "E", "F"],
                     help="Default 'Default' (F valid for ASCE 7-16 only)")
    loc.add_argument("--ip", type=float, default=1.0,
                     help="Importance factor Ip (1.0 typ., 1.5 if open to public)")
    loc.add_argument("--r-down", type=float, default=R_DOWN_AISLE)
    loc.add_argument("--r-cross", type=float, default=R_CROSS_AISLE)
    loc.add_argument("--code-edition", default=None,
                     choices=["asce7-22", "asce7-16"],
                     help="Seismic reference: asce7-22 (IBC 2024, default) or asce7-16 "
                          "(IBC 2018/2021 — current Utah/SLC permits)")

    off = p.add_argument_group("offline seismic (with --offline)")
    off.add_argument("--offline", action="store_true",
                     help="Skip network; use supplied --sds/--sd1/--s1/--sdc")
    off.add_argument("--sds", type=float)
    off.add_argument("--sd1", type=float)
    off.add_argument("--s1", type=float)
    off.add_argument("--ss", type=float)
    off.add_argument("--sdc")

    prod = p.add_argument_group("product / configuration")
    prod.add_argument("--project", help="Project profile JSON (fills site + load defaults)")
    prod.add_argument("--pallet-weight", type=float, help="lb per pallet (pallet mode)")
    prod.add_argument("--shelf-load", type=float,
                      help="lb per level per bay (hand-stack mode; replaces pallets)")
    prod.add_argument("--pallet-height", "--load-height", dest="pallet_height", type=float,
                      help="in (pallet / case load height)")
    prod.add_argument("--beam-length", type=float, help="in (bay width)")
    prod.add_argument("--levels", type=int, help="number of BEAM levels")
    prod.add_argument("--pallets-per-bay", type=int, default=2)
    prod.add_argument("--in-rack", action="store_true",
                      help="In-rack sprinklers present (12 in. clearance; else 6 in.)")
    prod.add_argument("--no-floor-level", action="store_true",
                      help="Bottom level is NOT floor-supported (all levels on beams)")
    prod.add_argument("--clear-height", type=float,
                      help="Ceiling sprinkler deflector / clear height (in)")
    prod.add_argument("--ceiling-sprinkler", default="standard",
                      choices=["standard", "esfr", "cmsa"],
                      help="Deflector clearance check: 18 in. standard, 36 in. ESFR/CMSA")
    prod.add_argument("--hole-pitch", type=float, help="Round level pitch up (in), e.g. 2")
    prod.add_argument("--commodity", default="", help="Commodity class, e.g. 'Class IV'")
    prod.add_argument("--dead-load-fraction", type=float, default=0.05)

    p.add_argument("--json", action="store_true", help="Emit JSON instead of a report")
    return p


def _apply_project(args) -> None:
    """Fill unset args from a project profile (explicit flags win)."""
    if not args.project:
        args.risk_category = args.risk_category or "II"
        args.site_class = args.site_class or "Default"
        args.code_edition = args.code_edition or "asce7-22"
        return
    from .project import load_project, site_dict
    proj = load_project(args.project)
    site, rack = site_dict(proj), proj.get("rack", {})
    bld, fire = proj.get("building", {}), proj.get("fire", {})
    if args.lat is None and args.lon is None and not args.zip_code and not args.address:
        args.lat, args.lon = site.get("lat"), site.get("lon")
        if args.lat is None:
            args.zip_code, args.address = site.get("zip"), site.get("address")
    args.risk_category = args.risk_category or site.get("risk_category") or "II"
    args.site_class = args.site_class or site.get("site_class") or "Default"
    args.code_edition = args.code_edition or site.get("code_edition") or "asce7-22"
    args.pallet_height = args.pallet_height or rack.get("load_height_in")
    args.beam_length = args.beam_length or rack.get("beam_length_in")
    if args.pallet_weight is None and args.shelf_load is None:
        args.shelf_load = rack.get("shelf_load_lb")
        args.pallet_weight = rack.get("load_weight_lb") if args.shelf_load is None else None
    if args.clear_height is None:
        defl = bld.get("deflector_height_ft") or (
            bld["ceiling_height_ft"] - 1.0 if bld.get("ceiling_height_ft") else None)
        args.clear_height = defl * 12 if defl else None
    if not args.commodity:
        args.commodity = fire.get("commodity", "")
    if rack.get("in_rack_sprinklers") and not args.in_rack:
        args.in_rack = True


def _seismic_from_args(args) -> SeismicResult:
    lat, lon, label = resolve_location(
        zip_code=args.zip_code, address=args.address, lat=args.lat, lon=args.lon)

    ref_doc = "ASCE7-16" if args.code_edition == "asce7-16" else "ASCE7-22"

    if args.offline:
        for name in ("sds", "sd1", "s1", "sdc"):
            if getattr(args, name) is None:
                raise SystemExit(f"--offline requires --{name}")
        res = SeismicResult(
            latitude=lat, longitude=lon, risk_category=args.risk_category,
            site_class=args.site_class, sds=args.sds, sd1=args.sd1, s1=args.s1,
            sdc=args.sdc, ss=args.ss, ie=args.ip,
            source=f"user-supplied (offline, {ref_doc})")
        res.cs_down_aisle = compute_cs(args.sds, args.sd1, args.s1, args.r_down, args.ip)
        res.cs_cross_aisle = compute_cs(args.sds, args.sd1, args.s1, args.r_cross, args.ip)
        res.notes.append(f"Offline seismic ({ref_doc}). R_down={args.r_down}, "
                         f"R_cross={args.r_cross}, Ip={args.ip}. Location: {label}")
        return res

    res = fetch_seismic(lat, lon, risk_category=args.risk_category,
                        site_class=args.site_class, r_down=args.r_down,
                        r_cross=args.r_cross, ie=args.ip, reference_document=ref_doc)
    res.notes.append(f"Location: {label}")
    return res


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    from ._io import safe_stdout
    safe_stdout()
    _apply_project(args)
    missing = [n for n, v in (("--pallet-height/--load-height", args.pallet_height),
                              ("--beam-length", args.beam_length), ("--levels", args.levels))
               if v is None]
    if args.pallet_weight is None and args.shelf_load is None:
        missing.append("--pallet-weight or --shelf-load")
    if missing:
        print(f"ERROR: missing {', '.join(missing)}", file=sys.stderr)
        return 2
    try:
        seismic = _seismic_from_args(args)
    except Exception as exc:  # network / input errors
        print(f"ERROR resolving seismic data: {exc}", file=sys.stderr)
        print("Tip: use --offline with --sds/--sd1/--s1/--sdc if no internet.",
              file=sys.stderr)
        return 2

    rec = recommend(
        seismic,
        pallet_weight_lb=args.pallet_weight, shelf_load_lb=args.shelf_load,
        pallet_height_in=args.pallet_height,
        beam_length_in=args.beam_length, num_beam_levels=args.levels,
        pallets_per_bay=args.pallets_per_bay, in_rack_sprinklers=args.in_rack,
        floor_level=not args.no_floor_level, building_clear_height_in=args.clear_height,
        commodity_class=args.commodity, dead_load_fraction=args.dead_load_fraction,
        ceiling_sprinkler=args.ceiling_sprinkler, hole_pitch_in=args.hole_pitch)

    if args.json:
        print(json.dumps(rec.as_dict(), indent=2))
    else:
        print(render_report(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
