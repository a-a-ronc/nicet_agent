# NFPA 13 (2025 Edition) — Sprinkler Design for Storage

> Standard for the Installation of Sprinkler Systems. Governs fire-sprinkler design
> on non-FM-insured sites (alongside the locally adopted IFC). On FM Global-insured
> sites, **FM DS 8-9 governs** — see `fm_global.md`.
> Storage protection lives mainly in **Chapters 20–25**; clearances/flue in Ch. 20–25
> and obstruction rules in Ch. 10–14.
> **Adopted edition:** permits are reviewed against the locally adopted edition (e.g.
> Utah = **NFPA 13 2019**) — see `adopted_codes_utah.md` and
> `rack_selector/data/adopted_codes.json`. Content below applies to 2019+ unless noted.

---

## 1. Commodity classification (the first thing to establish)

Classification drives everything downstream (density, sprinkler type, in-rack need).

| Class | What it is | Typical examples |
|-------|-----------|------------------|
| **Class I** | Essentially noncombustible product, on combustible (wood / non-expanded PE) pallet, in single-layer corrugated carton or paper wrap | Metal parts, glass bottles, canned food, ceramic tile |
| **Class II** | Class I products in slatted wood crates, solid wood boxes, or multi-thickness paperboard | Same goods, heavier packaging |
| **Class III** | Wood, paper, natural-fiber cloth, or **Group C plastic**; up to **5%** Group A/B plastic by weight/volume | Furniture, paper products, wood items, natural-fiber textiles |
| **Class IV** | Class I–III products that contain Group A plastic in cartons, or with Group A packaging; also Group B plastics and free-flowing Group A plastics | Mixed goods with appreciable plastic content |

### Plastics groups
- **Group A** — highest heat of combustion / burn rate. ABS, acrylic, PE, PP, PS,
  PUR, PVC (rigid only in some cases), nylon, FRP. **Drives the most demanding protection.**
- **Group B** — intermediate. Chloroprene, fluoroplastics in some forms, silicone.
- **Group C** — burns like ordinary combustibles. PVC (flexible), PVDC, PVDF, PTFE,
  melamine, phenolic, urea formaldehyde.

### Plastic sub-conditions that escalate hazard
- **Cartoned vs. exposed** — exposed plastic is far more severe than cartoned.
- **Expanded vs. unexpanded** — expanded (foamed: EPS, foam rubber) is most severe.
- **Encapsulated** — plastic film over the top/sides of a load traps heat/water → escalates.
- **Free-flowing** Group A (e.g., small pellets/powder that smother) can de-escalate.

> Cartoned Unexpanded plastic, Cartoned Expanded, Exposed Unexpanded, Exposed Expanded
> form an increasing-hazard ladder, each typically requiring more water / higher pressure.

---

## 2. Storage arrangement (second input)

- **Palletized** — loads on pallets, stacked, no rack.
- **Solid-piled** — stacked without pallets/spaces.
- **Bin box / shelf storage** — shelves ≤ 30 in. deep (shelf) / 30–60 in. (defined separately).
- **Rack** — the warehouse case:
  - **Single-row rack** — one pallet deep, aisles both sides.
  - **Double-row rack** — two single rows back-to-back (most common selective rack).
  - **Multiple-row rack** — > 2 rows deep (drive-in, flow, push-back, deep reach).
- Open vs. solid shelving in racks changes water penetration and in-rack rules.

Storage height and ceiling height are required for every protection lookup.

---

## 3. The three protection approaches

| Approach | What it is | When used |
|----------|-----------|-----------|
| **CMDA** — Control Mode Density/Area | Traditional. Pick a **density (gpm/ft²)** over a **design area (ft²)** from the curves for the commodity/height. Controls (not suppresses) the fire. | Lower hazard, lower heights, retrofit, where ESFR isn't feasible (high ceilings, obstructions). |
| **CMSA** — Control Mode Specific Application | Large-drop / specific listed sprinklers; design by **number of sprinklers at a pressure** instead of density/area. | Higher-challenge storage where listed for it. |
| **ESFR** — Early Suppression Fast Response | High-K, fast-response sprinklers intended to **suppress** the fire; design by **number of sprinklers operating at a minimum pressure**. Usually allows ceiling-only (no in-rack) within limits. | The default for modern high-bay warehouses when ceiling/storage heights fit the listing. |

### ESFR essentials & limits
- Design = a set number of sprinklers (commonly 12) at a **minimum operating pressure**.
- Common K-factors: K-14.0, K-16.8, K-22.4, K-25.2 (360). Higher K → lower pressure for
  same flow; high-K heads enable taller storage / ceiling-only protection.
- **ESFR is height-limited by listing.** Example from the standard for **exposed expanded
  Group A plastic** in rack: **max storage 35 ft, max ceiling 40 ft** at K-25.2,
  intermediate-temp pendent, **60 psi** minimum. (Different commodities/heights have
  their own rows — always read the governing table.)
- ESFR is sensitive to **obstructions** and requires controlled ceiling slope, smooth
  ceilings, and adequate water supply (high flow + pressure).
- When storage/ceiling exceeds the ESFR listing, you fall back to CMDA/CMSA **plus
  in-rack sprinklers.**

> Exact densities, design areas, K-factors, pressures, and height limits come from the
> Chapter 20–25 tables/figures for the specific commodity, arrangement and height.
> Read the controlling table — do not rely on a recalled number.

### ESFR ceiling-only envelope and what happens above it
- **NFPA 13 ESFR table (K-25.2): Class I–IV and cartoned unexpanded Group A plastic to
  40 ft storage / 45 ft ceiling.** Exposed expanded plastic: 35 ft / 40 ft with vertical
  barriers. For NFPA 13, **45 ft is the ceiling-only maximum** for these commodities.
- **Above a 45 ft ceiling** the options are:
  - **Specific-application listings** (AHJ acceptance required, listing conditions are
    binding): Reliable **P25** (K25.2, cULus) — single/double-row open-frame racks, ≤ 40 ft
    storage, **≤ 48 ft ceiling, aisles ≥ 5 ft**; Viking **VK514** (K28, UL) — reported to
    48 ft ceiling, verify data sheet.
  - **FM sites:** FM-approved **K28 ESFR** to **55 ft ceiling / 50 ft storage**, single/
    double-row, Class I–IV & CUP, **9 heads @ 80 psi (~2,250 gpm, fire pump likely), min
    8 ft aisles**. (FM DS 8-9 otherwise caps K25.2 at 45 ft for CUP.)
  - **In-rack sprinklers** (independent EC or ESFR in-rack options, §6) — the top in-rack
    level acts as a **"virtual floor"**; ceiling protection is then selected using the
    ceiling height *above* that level.
- Ceiling-only ESFR also assumes **open racks** (see §6a) and adequate water supply.

---

## 4. Clearances

- **Standard spray:** **18 in. minimum** between the **top of storage** and the **ceiling
  sprinkler deflector**.
- **ESFR (and CMSA): 36 in. minimum** deflector-to-top-of-storage (NFPA 13 §14.2.12 in
  2019+; §8.12.x in earlier editions — section number varies, verify in the adopted
  edition). In a high-bay ESFR warehouse **36 in. is the number that governs**, not 18 in.
- Also honor the sprinkler's listing/cut sheet clearances and ESFR obstruction rules.
- Top of storage must not impede sprinkler discharge; signage/AHJ may enforce a marked
  max storage line.
- **Intralog convention** for rack opening sizing: add **6 in.** load-handling
  clearance where there are no in-rack sprinklers, **12 in.** where in-rack sprinklers
  are present (room for in-rack piping/distribution). This is separate from the 18 in.
  deflector rule. See `CLAUDE.md`.

---

## 5. Flue spaces (rack storage)

Flue spaces let heat reach ceiling sprinklers and let water reach the seat of the fire.

- **Transverse flue** (perpendicular to aisle, between loads / at uprights):
  **nominal 6 in.** required in all rack types.
- **Longitudinal flue** (parallel to aisle, between back-to-back rows in double/multi-row):
  NFPA target **6 in.**; in double-/multi-row open racks no longitudinal clearance is
  strictly required between loads, but where used it should be kept clear.
- **2025 update:** in multiple-row racks, longitudinal flue is **not required** when
  nominal **6 in. transverse flues at ≤ 5 ft intervals** are provided, **rack depth ≤ 20 ft**,
  and **minimum aisle width ≥ 3.5 ft**.

Aisle width interacts with protection: narrower aisles can require more demanding
protection or in-rack sprinklers.

---

## 6. In-rack sprinklers (IRAS)

Required when ceiling-only protection can't handle the commodity/height, when shelving
is solid (§6a), or to enable storage/ceilings above ESFR/CMDA listings.

- Example: for **Class I–IV stored up to 25 ft** with **ESFR at the ceiling**, in-rack
  sprinklers go at the **first tier level or above half the storage height**, using
  **K-8.0 or K-11.2 quick-response** heads.
- **Independent in-rack options (NFPA 13-2019 Ch. 25)** — sourced maximum vertical spacing
  between in-rack levels:

  | Option | Class I–IV & cartoned unexpanded plastic | Cartoned expanded | Uncartoned plastics |
  |--------|------------------------------------------|-------------------|---------------------|
  | **EC in-rack** (K25.2EC pendent, §25.8.3) | **30 ft** | 30 ft | **20 ft** |
  | **ESFR in-rack** | **40 ft** | 30 ft | 30 ft |

  EC in-rack requires **horizontal barriers at each in-rack level**; both options are not
  balanced with ceiling demand and use the **top in-rack level as a "virtual floor."**
- **Conventional QR in-rack (K8.0/K11.2):** level placement comes from the NFPA 13 Ch. 25
  **figure** for the commodity/arrangement/height. *Correction:* an earlier chat answer
  gave a rule of thumb (≈ every 3rd tier for Class I–IV, every other for plastics) —
  that could **not** be verified against a source; do not use it. Read the figure.
- In-rack sprinklers add piping inside the rack — coordinate with rack design and the
  12 in. Intralog clearance convention (needed at the levels carrying branch lines).

---

## 6a. Open rack vs. solid shelving (decides whether in-rack is mandatory)

NFPA 13 definitions (Ch. 3):
- **Open rack** = no shelving; or solid shelves with area **≤ 20 ft²**; or wire mesh /
  slatted / other shelves with **≥ 50% open area AND flue spaces maintained**.
- The area of a solid shelf is bounded by aisles/flues on all four sides **or by loads
  that block the openings that would otherwise be the required flue spaces.** So a ≥50%
  open wire deck becomes "solid shelving" if hand-stacked cartons close off the flues.
- **Solid-shelving racks → in-rack sprinklers at every tier level** beneath the solid
  shelves (shielding). The 20–64 ft² band has specific provisions in recent editions —
  FPE to confirm.
- Practical: hand-stack pick modules on wire decks are the classic case where operations
  (filled decks, no flues) silently convert an open rack into solid shelving.

Tool: `python -m rack_selector.fire_check` walks §3–§6a and reports REQUIRED / LIKELY /
UNRESOLVED / POSSIBLY_AVOIDABLE with the reasons.

---

## 7. Other factors that shift the design
- **Idle pallet storage** (esp. plastic pallets) is treated as a high hazard and has its
  own rules — wood vs. plastic pallets can bump the effective commodity class.
- **Open-top containers / solid shelves** reduce water penetration → more demand.
- **Encapsulation** → escalate.
- **Mixed commodities** → design to the most severe present (unless segregated/limited).

---

## 8. 2025 edition notes relevant to storage/warehouses
- Chapter 4 split miscellaneous vs. low-piled storage into separate sections.
- Chapter 18 load tables/seismic coefficients updated to align with **ASCE/SEI 7**.
- Various sprinkler placement / allowable-omission revisions.

## Sources
- [NFPA 13 2025 product page](https://www.nfpa.org/product/nfpa-13-standard-for-the-installation-of-sprinkler-systems/p0013code)
- [Changes in the 2025 Edition of NFPA 13 — NFSA TechNotes](https://nfsa.org/2024/07/23/changes-in-the-2025-edition-of-nfpa-13-technotes/)
- [Notable Changes to the 2025 Edition of NFPA 13 — Risk Logic](https://risklogic.com/notable-changes-to-2025-edition-of-nfpa-13)
- [Commodity Classifications in NFPA 13 — NFPA](https://www.nfpa.org/news-blogs-and-articles/blogs/2022/01/18/commodity-classifications-in-nfpa-13)
- [Flue Spaces in Racks — NFPA 13 vs FM DS 8-9 — Risk Logic](https://risklogic.com/flue-spaces-in-racks-nfpa-13-vs-fm-global-data-sheet-8-9/)
- [In-Rack Requirements for ESFR up to 25 ft — UpCodes](https://up.codes/s/in-rack-sprinkler-requirements-for-rack-storage-of-class-i-through-class-iv-comm)
- [Storage clearance from nearest sprinkler (ESFR 36 in.) — MeyerFire](https://www.meyerfire.com/daily/storage-clearance-from-nearest-fire-sprinkler)
- [K25.2 above 45 ft? NFPA vs FM DS 8-9 vs K28 listings — MeyerFire forum](https://www.meyerfire.com/daily/use-k252-sprinklers-up-to-50-ft-roof-height)
- [New In-rack Design Criteria in NFPA 13 & FM DS 8-9 — Reliable/ANRACI](https://anraci.org/wp-content/uploads/2018/11/ANRACI-2018-New-In-rack-Storage-Criteria.pdf)
- [Solid shelving & open-rack thresholds — FPI](https://www.the-fpi.com/single-post/2017/01/20/solid-shelving-part-2)
- [Rack storage with solid shelving — Sprinkler Age](https://www.sprinklerage.com/rack-storage-solid-shelving/)
