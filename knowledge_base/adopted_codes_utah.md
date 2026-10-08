# Adopted Code Editions — Utah / Salt Lake City (GOVERNING for this jurisdiction)

> **Read this before quoting an edition for a Utah project.** The knowledge base is
> anchored to the *latest published* standards (NFPA 13 **2025**, I-Codes **2024**,
> ASCE 7-**22**, ANSI/RMI MH16.1-**2023**) for forward-looking reference. **What a
> Salt Lake City permit is actually reviewed against is the edition the State of Utah
> has adopted — which is older.** Design and stamp to the *adopted* edition unless the
> site is FM Global-insured (then FM Data Sheets govern) or the AHJ accepts a newer one.

Salt Lake City follows the building and fire codes adopted and amended by the **State of
Utah** (Utah Code Title 15A, State Construction and Fire Codes Act). There is no
"NFPA 21" — the sprinkler installation standard is **NFPA 13**.

## Adopted editions (Utah State Fire Marshal, effective July 1, 2023)
| Subject | Standard / Code | Adopted edition |
|---------|-----------------|-----------------|
| Fire code (incl. high-piled storage, IFC Ch. 32) | International Fire Code (IFC) | **2021** |
| Building code | International Building Code (IBC) | **2018** per the State Fire Marshal's current code list — *some sources cite 2021; confirm the exact edition on the design documents per Utah Code 15A-2-103* |
| **Sprinklers** | **NFPA 13, 13R, 13D** | **2019** |
| Standpipes / pumps | NFPA 14, NFPA 20 | 2019 |
| Water spray | NFPA 15 | 2017 |
| Private fire service mains | NFPA 24 | 2019 |
| Inspection/testing/maintenance | NFPA 25 | 2020 |
| Fire alarm | NFPA 72 | 2019 |
| Portable extinguishers | NFPA 10 | 2021 |

## Seismic — the one that bites
- IBC **2018 and 2021** both reference **ASCE/SEI 7-16** for seismic design loads —
  **NOT ASCE 7-22.** A Utah permit today is designed to **ASCE 7-16**.
- ASCE 7-16 and 7-22 differ (7-22 introduced multi-period response spectra and revised
  site-class definitions), so the seismic parameters and Cs can differ for the same site.
- **Rack tool note:** `rack_selector` can fetch either — pass `--code-edition asce7-16`
  for a Utah permit (default is `asce7-22`). The USGS service has both endpoints.
- ANSI/RMI **MH16.1** edition should track the adopted code (MH16.1-2012 era under
  IBC 2018; later editions are commonly accepted by AHJ/PE). Confirm with the PE.

## Practical rules for Utah work
1. **Quote NFPA 13 (2019) and IFC (2021)** as the governing fire-protection editions for
   a Salt Lake City permit — not the 2025/2024 editions in the rest of this KB.
2. The specific adopted editions **must be listed on the design documents**
   (Utah Code 15A-2-103 construction / 15A-5-103 fire).
3. **SLC timing policy:** the codes in effect on the date the **plan submission is
   accepted** for review apply (SLC Code 18.20.050 / IBC 105.3.2). If a new edition is
   adopted mid-project, submit before it takes effect to lock the current edition.
4. **FM Global override:** if New Balance / the site is FM-insured, **FM DS 8-9 governs**
   fire protection regardless of the adopted NFPA edition (see `fm_global.md`).
5. **Don't blend editions.** State which edition each number came from.

## Does the older edition change our prior analysis?
Mostly no, in structure. NFPA 13 **2019** already reorganized storage into **Chapters
20–25** (general / CMDA / CMSA / ESFR / alternatives / in-rack) and already contains the
ESFR-in-rack and EC-in-rack criteria, the flue-space rules, and the solid-shelf vs.
open-rack provisions used in the flue/clearance/in-rack answers for this project. So the
*concepts* (transverse/longitudinal flue, 18" deflector clearance, solid-shelf → in-rack,
aisle reclassification) carry over. **But the exact densities, K-factors, pressures,
height limits, and table cells must be read from the NFPA 13 2019 edition** — do not
substitute a 2025 value. The 2022/2025 editions made incremental changes that the Utah
AHJ has not adopted.

## Sources
- [Utah State Fire Marshal — Current Code Books (adopted July 1, 2023)](https://firemarshal.utah.gov/applications-and-forms/current-code-books/)
- [Salt Lake City — Current Building Codes](https://www.slc.gov/buildingservices/current-building-codes/)
- [Utah Code 15A-5-103 (Fire Code editions)](https://le.utah.gov/xcode/Title15A/Chapter5/15A-5-S103.html)
- [Utah Code 15A-2-103 (Construction Code editions)](https://le.utah.gov/xcode/Title15A/Chapter2/15A-2-S103.html)
- [Utah Fire Code 2021 (IFC 2021 basis) — UpCodes](https://up.codes/viewer/utah/ifc-2021)
