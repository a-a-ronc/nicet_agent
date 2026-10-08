# nicet_agent

A warehouse fire-protection & code reference assistant for Intralog. Ask it quick
questions about the factors that drive warehouse design constraints — commodity
classification, sprinkler protection, clearances, building/fire code, and rack seismic —
instead of waiting on a fire protection engineer for every quick answer.

It is a **reference and triage tool, not a stamped engineering deliverable.** Anything
that drives a permit or construction must still be reviewed by a licensed FPE/PE.

## Knowledge base
Start at [`knowledge_base/00_INDEX.md`](knowledge_base/00_INDEX.md), which routes a
question to the right file:
- `nfpa13.md` — NFPA 13 sprinkler design for storage (ESFR envelope, 36 in. clearance,
  open rack vs. solid shelving, in-rack options)
- `fm_global.md` — FM Global Data Sheets (8-9, 8-1, 2-0, 1-2) for FM-insured sites
- `ibc_ifc.md` — IBC/IFC occupancy, height/area, high-piled storage
- `seismic_rack_design.md` — ANSI/RMI MH16.1, ASCE 7 rack seismic, clearances
- `commodity_quick_reference.md` — cross-cutting cheat sheet
- `adopted_codes_utah.md`, `adopted_codes_ca_wa.md` — **the editions a permit is
  actually reviewed against** (Utah: NFPA 13 2019, IFC 2021, ASCE 7-16)

## Tools (`rack_selector/`)
```bash
python -m rack_selector.fire_check --project projects/25-1642_new_balance_slc.json   # in-rack triage
python -m rack_selector.levels --load-height 31.5 --beams 3.5,5 --deflector-height-ft 49 --hole-pitch 2
python -m rack_selector --project projects/25-1642_new_balance_slc.json --levels 6 --shelf-load 1800
python -m pytest                                                                     # test suite
```
See [`rack_selector/README.md`](rack_selector/README.md) and `methodology.md`.

## Projects
One JSON profile per job in `projects/` (copy `_TEMPLATE.json`): site, jurisdiction,
building heights, insurer, commodity, rack schema, and open questions. The tools read it
with `--project`, and the agent updates it as the team supplies new facts.

## How to ask a good question
Include: commodity (class / plastic group, cartoned vs exposed), storage method &
heights (incl. sprinkler deflector height), aisle width, decking type, **insurer (FM vs
NFPA)**, and site (state/ZIP) — or just name the project.
