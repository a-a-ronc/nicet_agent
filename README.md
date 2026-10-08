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
- `nfpa13.md` — NFPA 13 (2025) sprinkler design for storage
- `fm_global.md` — FM Global Data Sheets (8-9, 8-1, 2-0, 1-2) for FM-insured sites
- `ibc_ifc.md` — IBC/IFC 2024 occupancy, height/area, high-piled storage
- `seismic_rack_design.md` — ANSI/RMI MH16.1-2023, ASCE 7-22 rack seismic
- `commodity_quick_reference.md` — cross-cutting cheat sheet

Editions: NFPA 13 2025 · IBC/IFC 2024 · ANSI/RMI MH16.1-2023 · ASCE 7-22.
Jurisdiction anchor: high-seismic US (CA/UT/WA).

## How to ask a good question
Include: commodity (class / plastic group, cartoned vs exposed), storage method &
heights, aisle width, **insurer (FM vs NFPA)**, and site (state/ZIP) for seismic.

## Roadmap
A OneRack-style tool that uses seismic engineering to recommend rack type for a given
commodity + configuration (applying the 6" / 12" clearance convention) is planned for a
later phase. See `seismic_rack_design.md` §7.
