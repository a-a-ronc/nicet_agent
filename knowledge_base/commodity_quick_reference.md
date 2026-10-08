# Commodity & Configuration Quick Reference (cheat sheet)

Cross-cutting cheat sheet. For full detail and citations see `nfpa13.md`, `fm_global.md`,
`ibc_ifc.md`, `seismic_rack_design.md`. **Verify exact design values against the
controlling table/edition — this is a triage aid, not a stamped design.**

## Commodity class at a glance (NFPA 13)
| Class | One-line test | IBC occupancy | IFC high-pile trigger height |
|-------|---------------|---------------|------------------------------|
| I | Noncombustible product, minimal packaging, wood pallet | S-2 (often) | > 12 ft |
| II | Class I in heavier wood/paperboard packaging | S-1/S-2 | > 12 ft |
| III | Wood/paper/natural fiber/Group C; ≤ 5% Group A/B plastic | S-1 | > 12 ft |
| IV | Group A plastic content in cartons / packaging; Group B; free-flow Group A | S-1 | > 12 ft (Class IV is **not** IFC high-hazard) |
| Group A plastic (cartoned→exposed, unexpanded→expanded) | Appreciable/predominant Group A plastic | S-1 | > 12 ft; **> 6 ft when required by the fire code official** (high-hazard) |

Hazard escalates: **Class I → IV → Cartoned Unexpanded → Cartoned Expanded → Exposed
Unexpanded → Exposed Expanded plastic.** Encapsulation and plastic/idle pallets escalate.

## Numbers worth memorizing
| Item | Value | Source |
|------|-------|--------|
| Clearance, top of storage → **ceiling** deflector, standard spray | **≥ 18 in.** | NFPA 13 |
| Clearance, top of storage → **ESFR / CMSA** deflector | **≥ 36 in.** | NFPA 13 §14.2.12 (2019+) |
| ESFR ceiling-only, Class I–IV & cartoned unexpanded plastic | ≤ **40 ft storage / 45 ft ceiling** (K-25.2) | NFPA 13 Ch. 23 |
| Open rack: solid shelf area / wire-deck open area | **≤ 20 ft²** / **≥ 50% open + flues maintained** | NFPA 13 Ch. 3 |
| EC in-rack max vertical spacing (I–IV & cartoned / uncartoned) | **30 ft / 20 ft** | NFPA 13-2019 §25.8.3 |
| ESFR in-rack max vertical spacing (I–IV & CUP / CEP & uncartoned) | **40 ft / 30 ft** | NFPA 13-2019 Ch. 25 |
| **Transverse** flue space (all racks) | nominal **6 in.** | NFPA 13 |
| Longitudinal flue (where required) | **6 in.** | NFPA 13 |
| Intralog rack opening clearance — no in-rack | **+6 in.** | Intralog convention |
| Intralog rack opening clearance — with in-rack | **+12 in.** | Intralog convention |
| High-piled storage trigger (ordinary) | top of storage **> 12 ft** | IFC Ch. 32 |
| High-piled storage trigger (high-hazard: Group A plastics, tires, idle pallets…) | **> 6 ft when required by the fire code official** | IFC §3202 / §3203.6 |
| Sprinkler height increase (building) | **+20 ft / +1 story** | IBC §504 |
| ESFR ex. — exposed expanded Group A, rack | max storage **35 ft** / ceiling **40 ft**, K-25.2, 60 psi | NFPA 13 |
| FM DS 8-9 scope | Cl.1-3 > 10 ft, Cl.4/plastic > 5 ft, or any height > 200 ft² | FM DS 8-9 |
| Seismic Design Category, CA/UT/WA | commonly **D** (E/F near faults) | ASCE 7-22 |

## Protection-approach picker (non-FM site, rough triage)
- **Modern high-bay, fits ESFR listing, smooth ceiling, good water supply** → ESFR
  ceiling-only (preferred). Confirm storage/ceiling height within the listing.
- **Exceeds ESFR height, heavy plastic, obstructed/sloped ceiling, weak water supply**
  → CMDA/CMSA **+ in-rack sprinklers**.
- **FM-insured** → ignore the above default; design per **FM DS 8-9** (more conservative).

## Decision order for any project
1. Insurer? (FM → FM DS 8-9; else NFPA 13 + IFC)
2. Commodity class (NFPA Ch. 20-25 / FM DS 8-1)
3. Storage method + storage height + ceiling height + aisle width
4. Open rack or solid shelving? (deck ≥ 50% open + flues held, or shelf ≤ 20 ft²) — solid → in-rack every tier
4b. Ceiling-only ESFR feasible (≤ 40 ft storage / ≤ 45 ft ceiling, 36 in. clearance, or a
    specific-application listing)? else in-rack — `python -m rack_selector.fire_check`
5. IFC Ch. 32 admin items (vents, FD access, pile limits, permit submittal)
6. IBC occupancy/height/area + construction type
7. Seismic: site → SDC → MH16.1-2023 rack design + anchorage
8. State citations + flag FPE/PE review.
