# rack_selector — Methodology, Assumptions & Limitations

**This tool is a triage aid, not a stamped engineering deliverable.** Every output must be
confirmed against manufacturer load tables and reviewed by a licensed PE/FPE before it is
used for procurement, permitting, or construction.

## 1. Seismic parameters (ASCE 7-22)
Site parameters come from the **USGS ASCE7-22 web service**
(`earthquake.usgs.gov/ws/designmaps/asce7-22.json`), which returns SDS, SD1, S1, SS, SDC,
and the multi-period spectra for a given latitude/longitude, Risk Category, and Site
Class. Location is resolved from a ZIP (Zippopotam.us), an address (US Census geocoder),
or direct lat/long.

## 2. Seismic response coefficient Cs (ASCE 7-22 §12.8, ANSI/RMI MH16.1-2023)
```
Cs = SDS / (R / Ie)                      (Eq. 12.8-2, short-period / governing upper)
Cs_min = max(0.044 · SDS · Ie, 0.01)     (Eq. 12.8-5)
if S1 >= 0.6g:  Cs_min = max(Cs_min, 0.5 · S1 / (R/Ie))   (Eq. 12.8-6)
```
- **R**: down-aisle = **6** (steel ordinary moment frame), cross-aisle = **4** (steel
  ordinary concentrically braced frame). RMI defaults; overridable (`--r-down/--r-cross`).
- **Ie / Ip**: importance factor, **1.0** default, **1.5** if open to the public.
- **Period cap** (Eq. 12.8-3/4), which *lowers* Cs, is **intentionally not applied** in the
  default path — no reliable rack period is computed, so the short-period value is used as
  a **conservative** upper bound. (The `compute_cs` function accepts a period `t` if you
  want the reduction.)

## 3. Seismic weight & base shear (ANSI/RMI MH16.1)
```
Ws = Dead Load + PRF · Product Load        (PRF = product reduction factor, default 0.67)
V  = Cs · Ws                               (Ie/Ip already inside Cs)
```
- Dead load is estimated as a fraction of product load (default **5%**, `--dead-load-fraction`).
- Reported **per bay**, for both axes. This is a magnitude indicator for triage — not the
  full equivalent-lateral-force distribution.

## 4. Beam elevations & clearance (Intralog convention + NFPA 13)
```
clearance per level = 12 in. (in-rack sprinklers present) else 6 in.
pitch = pallet_height + clearance + beam_height
beam_top[i] = first_beam_top + i · pitch
top_of_storage = top beam + pallet_height
```
- `first_beam_top` defaults to one full pitch above the slab when the bottom level is
  floor-supported (`floor_level = True`).
- **NFPA 13 check:** `top_of_storage + 18 in. <= building_clear_height` (the 18 in.
  top-of-storage-to-**ceiling-deflector** minimum; clear height approximates the deflector
  elevation). The 6/12 in. value is a **rack-design** clearance, separate from this.

## 5. Component selection (triage)
- **Required beam-pair capacity** = `pallets_per_bay × pallet_weight`. Beam capacities are
  per pair and already include impact (per RMI tables).
- **Required frame axial** = `pallets_per_bay × pallet_weight × beam_levels`. An interior
  upright frame carries one full bay per beam level (two adjacent half-bays). The
  floor-supported level loads the slab, not the frame, so it is excluded from frame axial.
- **Conservative lookups:** when the requested beam length or frame unsupported length
  falls between tabulated values, the **next-larger** tabulated entry is used (→ lower
  capacity).
- **Frame unsupported length** = max(floor-to-first-beam, pitch), per the manufacturers'
  chart definition; frame capacity is read at that length.
- **Selection rule:** lightest sufficient option **per dealer** (smallest beam face / lowest
  frame capacity that still meets demand), then ordered by dealer priority
  (**Interlake Mecalux > SpaceRAK > Hannibal/Nucor**). The top-priority sufficient option is
  recommended; the rest are listed as alternatives.

## 6. What this tool does NOT do
- No anchor / base-plate design, no seismic **overstrength (Ω₀)** member check, no beam-to-
  column connection design, no story-drift / stability (P-Δ) check, no overturning.
- Does **not** confirm the frame against the manufacturer's **seismic** capacity tables at
  the computed Cs — it selects on gravity axial load and then **flags** that the seismic
  check is required.
- Assumes **single-deep selective** rack. Double-deep, push-back, drive-in, pallet-flow,
  and cantilever are out of scope.
- Fire-protection output is an **advisory** pointing to NFPA 13 / FM DS 8-9; it does not
  size sprinklers, set densities, or place in-rack levels.
- Representative (non-published) catalog capacities are estimates — every recommendation
  that uses one says so.

## 7. Standards referenced
ASCE/SEI 7-22 · ANSI/RMI MH16.1-2023 · NFPA 13 (2025) · IFC 2024 Ch. 32 · FM Global
DS 8-9. See the `knowledge_base/` files for the fire-protection and code basis.
