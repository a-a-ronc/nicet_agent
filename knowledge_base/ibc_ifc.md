# IBC 2024 / IFC 2024 (ICC) — Building & Fire Code Constraints

> The **IBC** governs how the *building* may be built (occupancy, construction type,
> allowable height/area, fire resistance). The **IFC** governs *operations and storage*,
> including **Chapter 32 high-piled combustible storage**. Both are adopted (often with
> amendments) by the local AHJ — always confirm the **locally adopted edition** and
> amendments.

---

## 1. Occupancy classification (IBC Chapter 3)

Most warehouses are **Group S (Storage)**:

| Group | Meaning | Typical warehouse fit |
|-------|---------|----------------------|
| **S-1** | Moderate-hazard storage — combustible goods not classified S-2 | General distribution, most mixed commodities, plastics |
| **S-2** | Low-hazard storage — noncombustible goods (incl. noncombustible product on wood pallets / in paper cartons / paper wrap) | Metal, canned goods, masonry, appliances |
| **H** (H-1…H-5) | High-hazard — hazardous materials **above** the Maximum Allowable Quantity per control area (IBC Table 307.1) | Flammable liquids, aerosols, oxidizers, etc. over MAQ |

- A warehouse becomes **Group H** only when hazmat exceeds MAQ per control area. Below
  MAQ it stays S-1/S-2 with control-area limits.
- **Aerosols, flammable/combustible liquids, lithium batteries**, etc. have their own
  IFC chapters that can override the general storage rules.

---

## 2. Allowable height & area (IBC Chapter 5)

Driven by **occupancy group + construction type** (Type I–V), then modified by
sprinklers and frontage.

- **Sprinkler increase (IBC §504):** automatic sprinklers add **+20 ft and +1 story**
  to the tabular height limit (NS → S values), with exceptions for Group H.
- **Area increase (IBC §506):** sprinklered single-story ≈ **4×** the unsprinklered
  base area; sprinklered multi-story ≈ **3×**; plus frontage increase.
- Specific allowable numbers come from **IBC Tables 504.3 (height in feet),
  504.4 (stories), and 506.2 (area)** for the exact group + construction type.
  Read those tables — don't recall the value.
- Big-box DCs are typically **Type II-B** (noncombustible, unprotected) and rely on the
  sprinkler increases + unlimited-area building provisions (**IBC §507**, e.g.
  one-story sprinklered noncombustible buildings can be unlimited area when set back).

---

## 3. IFC Chapter 32 — High-Piled Combustible Storage

**Trigger ("high-piled combustible storage"):** storage of combustible material in
piles / on pallets / in racks / on shelves where the **top of storage > 12 ft**, OR
**> 6 ft for high-hazard commodities** (high-hazard = Class IV and Group A plastics,
and other listed high-challenge commodities).

**What Chapter 32 controls (via Table 3206.2, indexed by commodity class + pile area):**
- Automatic sprinklers and whether **in-rack** sprinklers are required.
- **Smoke and heat removal** (vents) and **draft curtains**.
- **Fire department access doors** and **aisle width** (commonly **min 44 in.** for
  access aisles; wider where used as exit access).
- **Hose connections / standpipes**, building access roads.
- **Maximum pile dimensions / pile volume** and clearance to sprinklers.
- Housekeeping, commodity identification, and permit requirements.

**Submittal package (IFC Ch. 32) — what the AHJ wants at permit:**
floor plan showing high-piled areas with dimensions; usable storage height per area;
number of tiers per rack; **commodity clearance between top of storage and sprinkler
deflector** per arrangement; max pile volume for palletized/solid-pile arrays;
location + classification of commodities; FD access door locations; and locations of
valves controlling ceiling and in-rack sprinkler water supply.

---

## 4. How IBC/IFC interacts with NFPA 13 / FM
- IFC **points to NFPA 13** (or the FM scheme on FM sites) for the *sprinkler design
  itself*; IFC Ch. 32 sets *when* protection/vents/access are required and the
  *administrative* envelope.
- Commodity class used for IFC Ch. 32 should be consistent with the NFPA/FM class used
  for the sprinkler design.
- The **most restrictive** of building code, fire code, and insurer requirements governs.

## Sources
- [IFC 2024 Chapter 32 High-Piled Combustible Storage — ICC](https://codes.iccsafe.org/content/IFC2024P1/chapter-32-high-piled-combustible-storage)
- [IBC 2024 Chapter 3 Occupancy Classification — ICC](https://codes.iccsafe.org/content/IBC2024P1/chapter-3-occupancy-classification-and-use)
- [Storage Occupancy S-1, S-2, Group H — LegalClarity](https://legalclarity.org/storage-occupancy-classification-s-1-s-2-and-group-h/)
- [IBC Height & Area Limits, Tables 504.3 / 506.2 — meltplan](https://www.meltplan.com/buildingcodes/ibc/building-height-area-limits)
- [Occupancy Classifications in the IBC — NFSA](https://nfsa.org/2024/01/08/occupancy-classifications-in-the-ibc/)
