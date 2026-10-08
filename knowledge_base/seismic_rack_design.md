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

## 7. Roadmap — OneRack-style tool (not yet built)
Goal: given commodity + configuration + site, compute seismic demand (ASCE 7-22 →
MH16.1-2023) and recommend a rack type/section, applying the 6"/12" clearance
convention and respecting NFPA 13 / FM flue + clearance rules. Tracked for a later
phase; current phase is reference Q&A only.

## Sources
- [ANSI MH16.1-2023 overview — Apex](https://www.apexwarehousesystems.com/ansi-updates-steel-pallet-racking-standards-apex-answers-your-questions/)
- [ANSI MH16.1-2023 excerpts — Damotech](https://www.damotech.com/blog/ansi-mh-16.1-excerpts)
- [MH16.1 standard — GlobalSpec / MHI](https://standards.globalspec.com/std/14608011/mh16-1)
