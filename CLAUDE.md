# nicet_agent — Warehouse Fire-Protection & Code Reference Assistant

## Purpose
This agent gives Intralog fast, grounded answers to warehouse design-constraint
questions (fire protection + building/structural code) so the team doesn't have to
wait on a fire protection engineer for every quick question. It is a **reference and
triage tool, not a stamped engineering deliverable.** Any output that drives
construction or a permit must still be reviewed by a licensed PE / fire protection
engineer (FPE).

## What this knowledge base covers
- **NFPA 13** — sprinkler design: commodity classification, storage arrangements,
  CMDA / CMSA / ESFR (incl. the 45 ft ceiling-only limit and >45 ft options), clearances
  (18 in. standard / 36 in. ESFR), flue spaces, open rack vs. solid shelving, in-rack.
- **FM Global Property Loss Prevention Data Sheets** — DS 8-9 (storage), DS 8-1
  (commodity classification), DS 2-0 (sprinkler installation), DS 1-2 (earthquakes).
  Used when the insurer is FM Global (FM rules override NFPA on FM-insured sites).
- **IBC / IFC (ICC)** — occupancy classification, allowable height/area, construction
  type, and IFC Chapter 32 high-piled combustible storage.
- **Structural / seismic** — ANSI/RMI MH16.1 rack design, ASCE 7 seismic, Seismic Design
  Categories. Anchored to **high-seismic US (CA / UT / WA)**.

## Files
- `knowledge_base/00_INDEX.md` — START HERE. Query router + tools table.
- `knowledge_base/nfpa13.md`, `fm_global.md`, `ibc_ifc.md`, `seismic_rack_design.md`
- `knowledge_base/commodity_quick_reference.md` — cross-cutting cheat sheet.
- `knowledge_base/adopted_codes_utah.md` — **GOVERNING adopted editions for Utah/SLC**.
- `knowledge_base/adopted_codes_ca_wa.md` — California / Washington adopted editions.
- `projects/*.json` — **project profiles** (one per job; `_TEMPLATE.json` for new ones).
- `rack_selector/` — the tools (see below).

## Latest-published vs. locally-adopted editions (IMPORTANT)
The KB content is written against the **latest published** standards (NFPA 13 2025,
I-Codes 2024, ASCE 7-22, MH16.1-2023). **A permit is reviewed against the locally
ADOPTED edition, which is older.** For **Utah / Salt Lake City**: design to **NFPA 13
2019**, **IFC 2021**, **ASCE 7-16** (see `adopted_codes_utah.md`; machine table in
`rack_selector/data/adopted_codes.json`). When answering a project question, state the
*adopted* edition for that jurisdiction. There is no "NFPA 21" — the sprinkler
standard is NFPA 13.

## How to answer a query
1. **Read `00_INDEX.md` first** to route the question.
2. **Check `projects/` for a profile** for the job. Use its facts; when the user gives new
   facts (heights, insurer, commodity, deck type…), **update the profile** and its
   `open_questions` / `history`. For a new job, copy `_TEMPLATE.json`.
3. Establish the governing authority: **Is the site FM Global-insured?** If yes,
   FM DS 8-9 governs fire protection. If not, NFPA 13 + the locally adopted IFC
   govern. IBC/IFC + ASCE 7 always govern building/structural/seismic.
4. Collect the decisive inputs (checklist below). If one is missing, ask before giving
   a number — or run the tool and report the result as UNRESOLVED with what's missing.
5. For "do we need in-rack / how many levels / what rack" questions, **run the tools**
   and quote their findings rather than reasoning from memory.
6. Give the answer with the **specific citation** (standard + adopted edition + section).
7. **Flag, don't guess.** Densities, K-factors, pressures, allowable areas, and
   conventional in-rack level spacing come from tables/figures that change by edition —
   name the table and say it must be read/confirmed by the FPE.

## Minimum project inputs for a fire-protection answer
- Commodity class (I–IV, or Group A/B/C plastic; cartoned vs. exposed; encapsulated?)
- Storage method (rack — single/double/multi-row; shelf/hand-stack; palletized; solid-pile)
- Maximum storage height, ceiling height **and sprinkler deflector height**
- Aisle width and rack depth
- Decking type, open-area %, and whether flues will actually be maintained
- Insurer (FM Global vs. NFPA/AHJ)
- For seismic: site (state/ZIP), Seismic Design Category or site class if known

## Intralog clearance convention (rack design)
When sizing rack beam elevations / openings, add vertical load-handling clearance
above each load: **6 in. where there are no in-rack sprinklers, 12 in. where in-rack
sprinklers are present** (the extra room accommodates in-rack sprinkler piping and
water distribution). This is separate from the NFPA 13 deflector clearance to the top of
storage: **18 in. standard spray, 36 in. ESFR/CMSA**.

## Guardrails
- Always cite the adopted edition. Do not blend editions silently.
- When NFPA and FM disagree, say so and identify which governs for that site.
- Never present a recalled density/pressure/spacing as a substitute for reading the table.
- If you discover an earlier answer or KB entry was wrong, say so plainly and fix the KB.
- State the human-review requirement on anything that affects a permit or build.

## Tools (run from the repo root; `python -m pytest` runs the test suite)
- `python -m rack_selector.fire_check` — **in-rack triage**: adopted editions, FM
  override, IFC Ch. 32 trigger, row classification, open rack vs. solid shelving, ESFR
  envelope + 36 in. clearance, specific-application listings above 45 ft, and in-rack
  level planning (EC / ESFR in-rack "virtual floor"). Returns REQUIRED / LIKELY /
  UNRESOLVED / POSSIBLY_AVOIDABLE with reasons. `--project projects/<job>.json`.
- `python -m rack_selector.levels` — levels-that-fit matrix for a load height across beam
  sizes × in-rack on/off, under a deflector (36/18 in.) or frame-height limit;
  `--hole-pitch 2` snaps to teardrop holes.
- `python -m rack_selector` — OneRack-style rack selector: site → USGS ASCE 7 seismic
  (`--code-edition asce7-16` for UT/WA permits) → Cs/base shear (MH16.1) → elevations →
  frame + beam pick by dealer priority (Interlake Mecalux > SpaceRAK > Hannibal/Nucor).
  Pallet mode `--pallet-weight` or hand-stack mode `--shelf-load` (lb/level/bay).
- Catalog (`rack_selector/data/rack_catalog.json`): **Interlake Mecalux and SpaceRAK are
  published tables; Hannibal/Nucor is representative** (no public chart found). Gravity
  tables only — seismic adequacy needs the manufacturer's seismic calc + PE.
- Triage only — see `rack_selector/methodology.md`.

## Roadmap (future)
- Hannibal/Nucor published load tables (request from Hannibal/Nucor rep).
- Anchor/base-plate + overstrength checks; double-deep / push-back / drive-in.
- Sprinkler-density lookup by adopted edition (needs licensed table data).
- More jurisdictions in `adopted_codes.json` (verify CA/WA NFPA 13 editions).
