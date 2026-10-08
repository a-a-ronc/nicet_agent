# Structural & Seismic — Storage Rack Design

> Anchored to **high-seismic US (CA / UT / WA)**. Rack structural design is governed by
> **ANSI/RMI MH16.1-2023**, which now aligns its seismic provisions with **ASCE/SEI 7-22**.
> Building seismic design loads come from **ASCE 7-22** as adopted through **IBC 2024**.
> This is the basis for the planned OneRack-style rack-selection tool.

---

## 1. Governing documents
- **ANSI/RMI MH16.1-2023** — *Design, Testing, and Utilization of Industrial Steel
  Storage Racks.* Replaces MH16.1-2021. Minimum requirements for structural design,
  testing, and utilization of steel storage racks.
- **ASCE/SEI 7-22** — *Minimum Design Loads and Associated Criteria.* Source of seismic
  ground-motion parameters, response coefficients, and load combinations.
- **IBC 2024** — adopts ASCE 7-22 and sets when rack seismic design / anchorage is
  required; storage racks are "nonbuilding structures" / can be "structures supported
  by other structures."
- **FM DS 1-2** (FM sites) — adds FM seismic expectations on top of code.

---

## 2. What changed in MH16.1-2023 (seismic-relevant)
- Seismic provisions revised to **align with ASCE/SEI 7-22**, including:
  - Use of **software/online tools** to obtain site seismic data (Ss, S1, etc.).
  - **New methods** to obtain the seismic response coefficients.
- New provisions for **base plate and anchor design** where **seismic overstrength**
  must be considered.
- Added **base-fixity test** and **frame-bracing test** procedures.

---

## 3. Seismic Design Category (SDC) — the master switch (high-seismic region)
- SDC (A–F) is derived from site seismicity (Ss, S1, site class → SDS, SD1) and risk
  category. **CA / UT / WA sites are commonly SDC D, with E/F near major faults.**
- Higher SDC →
  - Heavier members, more bracing, larger base plates.
  - **Anchorage / overstrength** requirements on base connections.
  - Tighter limits on eccentric/heavy loads and on **reduction of design loads**.
  - Often special seismic detailing and inspection.
- Rack seismic demand depends on: **SDC, site class, weight of stored product
  (and how full the rack is assumed), rack geometry/height, importance/risk category,
  and base anchorage condition.**

---

## 4. Inputs needed to design / select rack (seismic)
1. **Site** — state/ZIP (→ Ss, S1, site class → SDS/SD1 → SDC).
2. **Risk / Importance category** (per occupancy; public access raises it).
3. **Commodity / product weight per pallet** and **pallet positions** (defines seismic mass).
4. **Rack configuration** — single/double/multi-row, height, beam levels, depth.
5. **Storage occupancy %** assumption (seismic weight factor for racks).
6. **Anchorage** — slab thickness/condition, base plate, overstrength need.
7. **Seismic separation / interaction** with the building.

---

## 5. Clearance convention for rack selection (Intralog / planned OneRack tool)
When laying out beam elevations and openings, add vertical load-handling clearance
above each load:
- **6 in.** where there are **no in-rack sprinklers**.
- **12 in.** where **in-rack sprinklers are present** (room for IRAS piping + distribution).

This is a **rack-design clearance**, separate from the NFPA 13 **18 in.** top-of-storage
-to-**ceiling**-deflector clearance (`nfpa13.md`). Both must be satisfied.

Worked logic for an opening (per beam level):
```
clear opening height = load height + (12 in. if in-rack sprinklers else 6 in.)
beam top elevation    = bottom-of-load elevation + clear opening height + beam height
```
Then check the **top of top load + 18 in. ≤ ceiling deflector** (NFPA) and confirm the
overall storage height is within the chosen sprinkler scheme's listing.

---

## 6. Interaction with fire protection
- In-rack sprinklers (driven by commodity/height per NFPA 13 / FM DS 8-9) add piping
  inside the rack → use the **12 in.** clearance and coordinate beam levels.
- Flue spaces (6 in. transverse, `nfpa13.md`) must be preserved by the rack layout —
  upright placement and load overhang affect this.
- Seismic bracing / spacers must not block required flue spaces or sprinkler discharge.

---

## 7. Tools (built) — see `rack_selector/README.md`
- `python -m rack_selector` — site → ASCE 7 seismic (use `--code-edition asce7-16` for
  Utah/WA permits) → Cs/base shear → beam elevations (6/12 in.) → frame + beam pick by
  dealer priority. Pallet mode (`--pallet-weight`) or hand-stack mode (`--shelf-load`).
- `python -m rack_selector.levels` — levels-that-fit matrix (beam size × in-rack).
- `python -m rack_selector.fire_check` — in-rack triage.

## 8. Dealer handling clearances (for comparison)
Interlake Mecalux's own selective-rack tables size level pitch as **pallet height + 4 in.
+ beam height, rounded up to the next 2 in.**, with **≥ 8 in.** from the forks to the top
beam. Intralog's convention (**+6 in.**, **+12 in.** with in-rack) is more conservative and
governs our layouts; use `--hole-pitch 2` to snap pitches to the 2 in. teardrop hole
pattern. Source: Interlake Mecalux Selective Pallet Rack Calculation Tables U02 (2014).

## 9. Adopted seismic standard
Seismic design loads follow the **adopted** IBC: IBC 2018/2021 → **ASCE 7-16** (Utah, WA
today); IBC 2024 → ASCE 7-22 (California 2025 CBC). See `adopted_codes_*.md`.

**ASCE 7-16 site-class traps (handled by `rack_selector`):**
- There is **no "Default" site class** in 7-16. With no soils report, §11.4.3 says use
  **Site Class D**, and §11.4.4 then requires **Fa ≥ 1.2**. At the New Balance SLC site
  USGS returns Fa = 1.0 for Site Class D, so the floor raises SDS from 1.045 g to 1.254 g
  (+20%). Swapping "Default" for "D" without the floor understates seismic demand.
- For **Site Class D with S1 ≥ 0.2**, USGS returns **SD1 / Fv / SDC as null** (§11.4.8,
  site-specific study). **Exception 2** waives the study when Cs uses Eq. 12.8-2 for
  T ≤ 1.5Ts and 1.5 × Eq. 12.8-3 above that; the tool's short-period Cs matches that, and
  the SDC is taken from SDS (Table 11.6-1) and S1. The PE confirms.
- USGS moved the services to `/ws/building-codes/asce7-XX/calculate` (old
  `/ws/designmaps/asce7-XX.json` URLs redirect).

## Sources
- [ANSI MH16.1-2023 overview — Apex](https://www.apexwarehousesystems.com/ansi-updates-steel-pallet-racking-standards-apex-answers-your-questions/)
- [ANSI MH16.1-2023 excerpts — Damotech](https://www.damotech.com/blog/ansi-mh-16.1-excerpts)
- [MH16.1 standard — GlobalSpec / MHI](https://standards.globalspec.com/std/14608011/mh16-1)
