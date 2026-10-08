# FM Global Property Loss Prevention Data Sheets — Storage

> FM Global Data Sheets are the **governing fire-protection criteria on FM-insured
> sites.** They are generally **more conservative than NFPA 13** and FM will hold the
> insured to them. **Always confirm the insurer first** — if the site is FM-insured,
> use these sheets, not NFPA 13. Cross-check edition/revision on FM's portal
> (`www.fm.com` → resources) because FM revises sheets frequently.

Key sheets for warehouse rack/storage work:

| DS | Title | Use |
|----|-------|-----|
| **8-1** | Commodity Classification | Determine the FM commodity class before protection lookup |
| **8-9** | Storage of Class 1, 2, 3, 4 and Plastic Commodities | The main storage-protection sheet |
| **2-0** | Installation Guidelines for Automatic Sprinklers | Sprinkler install/obstruction/spacing rules |
| **1-2** | Earthquakes (and seismic-related sheets) | Seismic protection of sprinkler systems & buildings |

---

## DS 8-9 — Storage of Class 1, 2, 3, 4 and Plastic Commodities

**When it applies (scope thresholds):**
- Class 1, 2 or 3 stored **higher than 10 ft**, OR
- Class 4 or plastic stored **higher than 5 ft**, OR
- Storage of **any height** occupying an area **> 200 ft²**.

**Commodity grouping in DS 8-9:** FM organizes the eight commodity hazards into
protection classes, grouping **Class 1/2/3** together and **Class 4 + cartoned
unexpanded plastic** together, then escalating through cartoned expanded and
uncartoned (exposed) expanded plastics. Protection guidance lives in **Tables 2–11**
covering solid-piled/palletized and rack arrangements for each group.

**How FM design differs from NFPA 13:**
- FM leans on **ceiling-only ESFR / specific-application schemes** with defined
  K-factor + minimum pressure + number of sprinklers, indexed to **commodity, storage
  height, ceiling height, and ESFR sprinkler listing.**
- FM **flue-space and clearance** rules can differ from NFPA — verify against the
  current sheet (see Risk Logic comparison in sources).
- FM publishes **approved/Listed (FM Approved)** sprinkler requirements; substitution
  of non-FM-Approved equipment can void coverage.
- FM frequently requires **larger water supply / longer duration** than the equivalent
  NFPA design for the same storage.

**Inputs FM needs (same as NFPA, plus FM specifics):**
commodity class (per DS 8-1), storage arrangement, storage height, ceiling height,
aisle width, sprinkler K-factor/temperature, and whether in-rack sprinklers are used.

> Exact densities, K-factors, pressures, sprinkler counts, and height limits come from
> the current DS 8-9 tables. Read the controlling table — values change between
> revisions and differ from NFPA.

---

## DS 8-1 — Commodity Classification
FM's classification scheme parallels but is not identical to NFPA's. Classify per
DS 8-1 for an FM site rather than assuming the NFPA class carries over. Pay attention
to plastic content thresholds, packaging, and pallet type.

## DS 2-0 — Installation Guidelines for Automatic Sprinklers
Governs sprinkler positioning, obstruction rules, spacing, and hydraulics on FM sites.
Use together with 8-9 for layout/obstruction questions.

## DS 1-2 — Earthquakes
Seismic protection of the building and the sprinkler system on FM sites. Coordinates
with ASCE 7 / building-code seismic but adds FM-specific bracing and anchorage
expectations. For **rack** seismic design see `seismic_rack_design.md` (ANSI/RMI + ASCE 7).

---

## NFPA vs. FM — quick rule
- **FM-insured site →** FM Data Sheets govern fire protection. (Most conservative.)
- **Not FM-insured →** NFPA 13 + locally adopted IFC govern.
- If a client wants both, design to the **more demanding** of the two.

## Sources
- [Recent Changes to FM DS 8-9 — Risk Logic](https://risklogic.com/recent-changes-to-fm-global-property-loss-prevention-data-sheet-8-9-storage-of-class-1-2-3-4-and-plastic-commodities)
- [FM DS 8-9 (reference copy)](https://fireprotectionsupport.nl/wp-content/uploads/2019/05/FMDS0809-2018-07-Storage-of-Class-1-2-3-4-and-Plastic-Commodities-8-9.pdf)
- [FM Data Sheet 8-9 overview — phcppros](https://www.phcppros.com/articles/2119-fm-data-sheet-8-9)
- [Flue Spaces — NFPA 13 vs FM DS 8-9 — Risk Logic](https://risklogic.com/flue-spaces-in-racks-nfpa-13-vs-fm-global-data-sheet-8-9/)
- [FM DS 8-1 Commodity Classification](https://www.fm.com/FMAApi/data/ApprovalStandardsDownload?itemId=%7B0CE2C1A8-DF22-48D4-B539-9844401B371B%7D)
