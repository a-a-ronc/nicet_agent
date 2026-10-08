# rack_selector — OneRack-style seismic rack-selection tool

A triage calculator that turns **site + product + configuration** into a **rack frame/beam
recommendation**, with seismic demand and fire-protection clearance checks. Part of
`nicet_agent`. **Not a stamped design** — confirm against manufacturer load tables and a
licensed PE/FPE.

## What it does
1. Resolves a location (ZIP, address, or lat/long).
2. Auto-fetches **ASCE 7-22** seismic parameters from the **USGS** web service
   (SDS, SD1, S1, SDC).
3. Computes the rack seismic response coefficient **Cs** (down-aisle R=6, cross-aisle R=4)
   and base shear per **ANSI/RMI MH16.1-2023 / ASCE 7-22**.
4. Lays out **beam elevations** using the Intralog clearance convention
   (**6 in.** without in-rack sprinklers, **12 in.** with) and checks the NFPA 13
   **18 in.** top-of-storage-to-deflector rule.
5. Recommends the lightest sufficient **beam** and **frame** per dealer, ordered by
   priority: **Interlake Mecalux > SpaceRAK > Hannibal/Nucor**.
6. Surfaces SDC-driven anchorage/overstrength requirements and a fire-protection
   advisory, plus the mandatory PE/FPE review note.

## Install / run
Pure standard library (no third-party deps to run; `pytest` only for tests).

```bash
# from the nicet_agent/ directory
python -m rack_selector --zip 84101 --pallet-weight 2500 --pallet-height 48 \
    --beam-length 96 --levels 4 --pallets-per-bay 2 --clear-height 384 \
    --commodity "Class IV"

# JSON output
python -m rack_selector --lat 40.76 --lon -111.89 --pallet-weight 2000 \
    --pallet-height 50 --beam-length 108 --levels 5 --json

# fully offline (no internet): supply seismic values yourself
python -m rack_selector --offline --sds 1.0 --sd1 0.6 --s1 0.55 --sdc D \
    --lat 40.76 --lon -111.89 --pallet-weight 2500 --pallet-height 48 \
    --beam-length 96 --levels 4 --clear-height 384 --commodity "Class IV"
```

Key flags: `--in-rack` (12 in. clearance), `--no-floor-level`, `--ip 1.5`
(public-access importance factor), `--site-class`, `--risk-category`,
`--r-down/--r-cross`.

## Tests
```bash
python -m pytest        # 25 tests, offline (network paths are not exercised)
```

## Library use
```python
from rack_selector import recommend
from rack_selector.seismic import fetch_seismic
seismic = fetch_seismic(40.76, -111.89, risk_category="II")
rec = recommend(seismic, pallet_weight_lb=2500, pallet_height_in=48,
                beam_length_in=96, num_beam_levels=4, building_clear_height_in=384,
                commodity_class="Class IV")
print(rec.as_dict())
```

## Files
- `seismic.py` — Cs / base-shear math (pure) + USGS fetch.
- `geocode.py` — ZIP/address → lat-long (Zippopotam.us / US Census).
- `catalog.py` — load catalog, conservative capacity lookup, dealer-priority selection.
- `clearance.py` — beam elevations + 6/12 in. clearance + NFPA 18 in. check.
- `selector.py` — orchestration + text report.
- `cli.py` / `__main__.py` — command line.
- `data/rack_catalog.json` — dealer components (see catalog notes below).
- `methodology.md` — assumptions, equations, and limitations. **Read this.**

## Catalog data confidence
- **SpaceRAK** beams and structural-channel frames are **transcribed from the published
  load charts** (cited in the JSON).
- **Interlake Mecalux** and **Hannibal/Nucor** entries are **representative**, anchored on
  published data points, and flagged in every recommendation. Drop the dealers' full
  published load tables into `data/rack_catalog.json` (same structure) to upgrade them.

## Limitations (see methodology.md)
Cs uses the conservative short-period value (no period reduction). Frame selection is on
gravity axial load; seismic adequacy of the chosen frame must be confirmed against the
manufacturer's **seismic** tables at the computed Cs. Single-deep selective rack assumed.
No anchor/baseplate design, no connection design, no drift check. Triage only.
