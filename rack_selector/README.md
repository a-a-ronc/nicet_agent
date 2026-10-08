# rack_selector — rack selection + fire-protection triage tools

Three command-line tools for Intralog rack projects. Pure standard library to run
(`pytest` only for tests). **Triage only — not a stamped design.** Confirm against
manufacturer load/seismic tables and a licensed PE/FPE.

| Tool | Answers |
|------|---------|
| `python -m rack_selector.ask "question"` | Where in the KB is this answered, and which tool gives the number? |
| `python -m rack_selector.fire_check` | Do we need in-rack sprinklers — and why? |
| `python -m rack_selector.levels` | How many levels fit (beam size × in-rack, under the sprinklers)? |
| `python -m rack_selector` | Which frame/beam, what seismic Cs, what elevations? |

All three accept `--project projects/<job>.json` to pre-fill inputs (explicit flags win).

## fire_check — in-rack triage
```bash
python -m rack_selector.fire_check --project projects/25-1642_new_balance_slc.json \
    --pitch 44 --levels 6 --deck-open 60
python -m rack_selector.fire_check --commodity "Class IV" --storage-height 30 \
    --ceiling-height 50 --aisle 5.83 --rack-depth 4 --shelving wire --deck-open 60 \
    --jurisdiction UT --insurer NFPA
```
Walks: adopted editions (UT/CA/WA table) → FM override → IFC Ch. 32 trigger → row type
(single/double/multiple from depth + aisle; < 3.5 ft aisle = multiple) → **open rack vs.
solid shelving** (≤ 20 ft² or ≥ 50% open deck with flues held; loads blocking flues =
solid) → ESFR ceiling-only envelope (≤ 40 ft storage / ≤ 45 ft ceiling, 36 in.
clearance) → specific-application listings above 45 ft (Reliable P25, Viking VK514, FM
K28) → in-rack level planning. Output status: **REQUIRED / LIKELY / UNRESOLVED /
POSSIBLY_AVOIDABLE** with every finding cited.

In-rack planning uses only sourced spacings — EC in-rack 30 ft (20 ft uncartoned), ESFR
in-rack 40 ft (30 ft CEP/uncartoned) — with the top in-rack level placed high enough to act
as a **virtual floor** (ceiling above it ≤ 45 ft). Conventional K8/K11.2 spacing is **not**
encoded; pass `--conventional-spacing-ft` only if read from the NFPA 13 Ch. 25 figure.

## levels — how many levels fit
```bash
python -m rack_selector.levels --load-height 31.5 --beams 3.5,5 \
    --deflector-height-ft 49 --ceiling-sprinkler esfr --hole-pitch 2
python -m rack_selector.levels --load-height 31.5 --beams 3.5,5 --max-top-beam-ft 26.5
```
Pitch = load + 6 in. (12 in. with in-rack) + beam, rounded up to the hole pitch;
max top of storage = deflector − 36 in. (ESFR) / 18 in. (standard). Flags rows above the
40 ft ceiling-only ESFR storage limit.

## rack selector — frames, beams, seismic
```bash
# Utah permit (ASCE 7-16), hand-stack 1,800 lb per level per bay
python -m rack_selector --project projects/25-1642_new_balance_slc.json \
    --levels 6 --shelf-load 1800 --ceiling-sprinkler esfr --hole-pitch 2
# pallets
python -m rack_selector --zip 84101 --code-edition asce7-16 --pallet-weight 2500 \
    --pallet-height 48 --beam-length 96 --levels 4 --clear-height 384
# offline seismic
python -m rack_selector --offline --sds 1.0 --sd1 0.6 --s1 0.55 --sdc D --lat 40.76 \
    --lon -111.89 --pallet-weight 2500 --pallet-height 48 --beam-length 96 --levels 4
```
Site → USGS ASCE 7-16/7-22 → Cs (R 6 down / 4 cross) and base shear per bay (MH16.1) →
elevations (6/12 in. clearance, 18/36 in. deflector check) → lightest sufficient beam and
frame per dealer, ordered **Interlake Mecalux > SpaceRAK > Hannibal/Nucor**, with
manufacturer flags (Interlake beams > 126 in need lateral bracing; > 90 in with decks
need crossbar ties).

## Catalog data (`data/rack_catalog.json`)
| Dealer | Beams | Frames | Status |
|--------|-------|--------|--------|
| Interlake Mecalux | Step beams 27E–65Q, 48–168 in | Welded teardrop IK025F–IK099F; bolted 3B77–5B122 | **Published** (Calc. Tables U02, 2014; MH16.1-2012) |
| SpaceRAK | Roll-formed 306M–602M | Structural channel 335B–454B | **Published** (2018/2019 charts) |
| Hannibal/Nucor | Teardrop (4 sizes) | Roll-formed (3) | **Representative** — no public chart; request from Hannibal |

Gravity load tables only. The Interlake bolted 3B82T (pick-module frame) column mapping
was inferred from PDF text extraction — verify against the printed table.

## Other files
`ask.py` (query index over KB + project profiles + catalog) · `_io.py` (Windows-safe
console output) · `seismic.py` (Cs math + USGS fetch) · `geocode.py` · `catalog.py` · `clearance.py` ·
`selector.py` · `levels.py` · `fire_check.py` · `project.py` · `data/adopted_codes.json`
· `methodology.md` (**read this**) · `tests/` (`python -m pytest`).
