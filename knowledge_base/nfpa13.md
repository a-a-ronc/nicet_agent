# NFPA 13 (2025 Edition) — Sprinkler Design for Storage

> Standard for the Installation of Sprinkler Systems. Governs fire-sprinkler design
> on non-FM-insured sites (alongside the locally adopted IFC). On FM Global-insured
> sites, **FM DS 8-9 governs** — see `fm_global.md`.
> Storage protection lives mainly in **Chapters 20–25**; clearances/flue in Ch. 20–25
> and obstruction rules in Ch. 10–14.

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

---

## 4. Clearances

- **18 in. minimum** clearance between the **top of storage** and **ceiling sprinkler
  deflectors** (standard rule; greater for some high-pile/special cases).
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

Required when ceiling-only protection can't handle the commodity/height, or to enable
storage above ESFR/CMDA listings.

- Example (2025): for **Class I–IV stored up to 25 ft** with **ESFR at the ceiling**,
  in-rack sprinklers go at the **first tier level or above half the storage height**,
  using **K-8.0 or K-11.2 quick-response** heads.
- Higher / plastic storage drives more in-rack levels and face/transverse-flue placement.
- In-rack sprinklers add piping inside the rack — coordinate with rack design and the
  12 in. Intralog clearance convention.

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
