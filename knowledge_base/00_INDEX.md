# 00 — INDEX & Query Router (START HERE)

This knowledge base lets the agent answer warehouse design-constraint questions fast,
across fire protection (NFPA 13 / FM Global) and building/structural code (IBC/IFC,
ANSI/RMI, ASCE 7). Read this file first, route the question, then open the file(s) below.

## Files
| File | Use it for |
|------|-----------|
| `nfpa13.md` | Sprinkler design (non-FM sites): commodity class, ESFR/CMDA/CMSA, clearances, flue spaces, in-rack |
| `fm_global.md` | FM-insured sites: DS 8-9 storage, 8-1 classification, 2-0 install, 1-2 earthquake |
| `ibc_ifc.md` | Occupancy (S-1/S-2/H), allowable height/area, IFC Ch. 32 high-piled storage |
| `seismic_rack_design.md` | Rack structural/seismic: ANSI/RMI MH16.1-2023, ASCE 7-22, SDC, 6"/12" clearance |
| `commodity_quick_reference.md` | Cross-cutting cheat sheet + numbers worth memorizing |
| `adopted_codes_utah.md` | **GOVERNING editions for Utah/SLC permits** (NFPA 13 2019, IFC 2021, ASCE 7-16) |

## Editions: latest-published vs. locally-adopted
This KB is written against the **latest published** standards — NFPA 13 **2025** ·
IBC/IFC **2024** · ANSI/RMI **MH16.1-2023** · ASCE/SEI **7-22** · FM Global
**DS 8-9 / 8-1 / 2-0 / 1-2** — for forward-looking reference.

**A permit is reviewed against the locally ADOPTED edition, which is older.** For
**Utah / Salt Lake City** (this project's jurisdiction): **NFPA 13 2019**, **IFC 2021**,
IBC 2018/2021, **ASCE 7-16** — see `adopted_codes_utah.md`. Quote the adopted edition for
real project work; never blend editions; confirm amendments. FM-insured sites: FM Data
Sheets govern regardless.

## Route the question
| If the question is about… | Go to |
|---------------------------|-------|
| "What class is this commodity?" | `nfpa13.md` §1 (or `fm_global.md` DS 8-1 if FM) + cheat sheet |
| "ESFR or in-rack? what density/pressure?" | `nfpa13.md` §3, §6 (FM: `fm_global.md`) |
| "How much clearance / flue space?" | `nfpa13.md` §4–5 + cheat sheet |
| "Do I trigger high-piled storage rules?" | `ibc_ifc.md` §3 (IFC Ch. 32) |
| "What occupancy / how tall / how big can the building be?" | `ibc_ifc.md` §1–2 |
| "Is this site FM or NFPA?" | `fm_global.md` (NFPA-vs-FM rule) |
| "What rack / seismic anchorage do I need?" | `seismic_rack_design.md` |
| "Beam elevations / opening sizing / 6\" vs 12\"" | `seismic_rack_design.md` §5 + `CLAUDE.md` |

## Always ask for (if not provided)
Commodity (class / plastic group, cartoned vs exposed, encapsulated?) · storage method
(rack type / palletized / solid-pile) · max storage height · ceiling height · aisle
width · **insurer (FM vs NFPA/AHJ)** · site (state/ZIP) for seismic.

## Answer format
1. State the **governing authority** (FM vs NFPA/IFC) and **edition**.
2. Give the answer with a **specific citation** (standard + edition + section/table).
3. If a number comes from a table that changes by edition, **name the table and say it
   must be read/confirmed** rather than recalling a possibly-stale value.
4. End with the **FPE/PE review** caveat for anything affecting a permit or build.

## Scope & limits
Reference/triage tool only. Not a stamped design. The OneRack-style seismic
rack-selection tool is **roadmap, not built** (see `seismic_rack_design.md` §7).
