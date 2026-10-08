# Adopted Code Editions — California and Washington

> Machine-readable source of truth: `rack_selector/data/adopted_codes.json` (used by
> `fire_check`). These two states are **partially verified** — the base I-Code editions
> and effective dates are confirmed; the NFPA 13 edition is inferred from referenced-
> standards tables and must be confirmed per project. Utah is in `adopted_codes_utah.md`.

## California (Title 24, 2025 cycle)
| Item | Edition | Status |
|------|---------|--------|
| California Fire Code (Part 9) | 2025 CFC, based on **2024 IFC** | Confirmed — effective **Jan 1, 2026** |
| California Building Code | 2025 CBC, based on **2024 IBC** → **ASCE 7-22** | Base confirmed |
| NFPA 13 | **2022** (California amended) per CFC referenced-standards table | **VERIFY** in CFC Ch. 80 + local ordinance |

- California historically lags NFPA editions (it skipped NFPA 13-2019 in the 2019 cycle).
- Projects permitted under the 2022 CFC (2021 IFC basis) stay on that edition.
- Local fire authorities (e.g. Ontario Fire) often amend Chapter 32 / sprinkler rules —
  check the city ordinance.

## Washington (State Building Code Council)
| Item | Edition | Status |
|------|---------|--------|
| International Fire Code (WAC 51-54A) | **2021 IFC** | Confirmed — effective **Mar 15, 2024** |
| International Building Code (WAC 51-50) | **2021 IBC** → **ASCE 7-16** | Confirmed |
| NFPA 13 | **2019** (inferred from 2021 IFC referenced standards) | **VERIFY** WAC 51-54A amendments |

- The 2024 I-Code adoption was estimated for **Nov 1, 2026** in a 2024 filing — check
  current SBCC status; if in effect, WA moves to 2024 IFC/IBC (ASCE 7-22).
- Seattle and other cities publish local amendments (e.g. Seattle Fire Code Ch. 32).

## Sources
- [California Fire Code — referenced standards (gocodebook)](https://gocodebook.com/library/us/ca/ca-fire-code/chapter-80-referenced-standards/section-j102-referenced-standards)
- [WA SBCC — State Codes, Regulations & Guidelines](https://sbcc.wa.gov/node/60)
- [WSR 23-20-027 (WA effective date March 15, 2024)](https://lawfilesext.leg.wa.gov/law/wsr/2023/20/23-20-027.htm)
