"""Query index (rack_selector.ask): completeness, retrieval quality, freshness, CLI."""

import os

import pytest

from rack_selector import ask


@pytest.fixture(scope="module")
def idx():
    return ask.build_index(write=False)


def top(idx, q, n=3):
    return ask.query(q, top=n, index=idx)


# --- completeness ---------------------------------------------------------------------
def test_index_covers_every_source(idx):
    files = {d["section"]["file"] for d in idx["docs"]}
    for p in ask._sources():
        assert os.path.relpath(p, ask.ROOT).replace("\\", "/") in files
    assert "projects/25-1642_new_balance_slc.json" in files
    assert "rack_selector/data/rack_catalog.json" in files


def test_every_heading_is_indexed(idx):
    """Every markdown heading (except 'Sources') must exist as a section."""
    keys = {(d["section"]["file"], d["section"]["line"]) for d in idx["docs"]}
    missing = []
    for p in ask._sources():
        rel = os.path.relpath(p, ask.ROOT).replace("\\", "/")
        with open(p, encoding="utf-8") as fh:
            for i, line in enumerate(fh.read().splitlines(), 1):
                m = ask._HEADING.match(line)
                if m and m.group(2).strip().lower() not in ask.SKIP_HEADINGS:
                    if (rel, i) not in keys:
                        missing.append((rel, i, line))
    assert not missing


def test_sources_sections_not_indexed(idx):
    assert not any(d["section"]["heading"].endswith("Sources") for d in idx["docs"])


def test_no_empty_sections(idx):
    assert all(d["len"] > 0 for d in idx["docs"])


def test_project_and_catalog_sections(idx):
    heads = [d["section"]["heading"] for d in idx["docs"]]
    assert any(h.endswith("> Open questions") and "25-1642" in h for h in heads)
    assert any(h.endswith("> History") and "25-1642" in h for h in heads)
    for dealer in ("Interlake Mecalux", "SpaceRAK", "Hannibal/Nucor"):
        assert any(h.startswith("Rack catalog > Beams > " + dealer) for h in heads)
        assert any(h.startswith("Rack catalog > Frames > " + dealer) for h in heads)


def test_self_retrieval(idx):
    """Each section should come back in the top 3 when queried by its own heading."""
    docs = idx["docs"]
    hits = 0
    for d in docs:
        leaf = d["section"]["heading"].split(" > ")[-1]
        if any(h.file == d["section"]["file"] and h.line == d["section"]["line"]
               for h in top(idx, leaf)):
            hits += 1
    assert hits / len(docs) >= 0.95, f"self-retrieval {hits}/{len(docs)}"


# --- tokenizer ------------------------------------------------------------------------
def test_tokenize_hyphen_dot_stopwords_and_plurals():
    toks = ask.tokenize("In-rack sprinklers for the K-25.2 ESFR via rack_selector.levels")
    assert "in-rack" in toks and "rack" in toks and "k-25.2" in toks
    assert "sprinkler" in toks and "level" in toks          # plural folded
    assert "the" not in toks and "via" not in toks


@pytest.mark.parametrize("word, expected", [
    ("racks", "rack"), ("flues", "flue"), ("boxes", "box"), ("categories", "category"),
    ("class", "class"), ("status", "status"), ("ft", "ft"), ("k-25.2", "k-25.2"),
])
def test_stem(word, expected):
    assert ask.stem(word) == expected


# --- retrieval quality: realistic questions --------------------------------------------
BATTERY = [
    ("what clearance do ESFR sprinklers need to the top of storage", "nfpa13.md", "Clearances"),
    ("does Class IV trigger high-piled storage at 6 ft", "ibc_ifc.md", "High-Piled"),
    ("which NFPA 13 edition applies in Salt Lake City", "adopted_codes_utah.md", "Adopted"),
    ("can we avoid in-rack sprinklers with wire decks and hand-stack cartons", "nfpa13.md",
     "solid shelving"),
    ("FM global insured site which data sheet governs", "fm_global.md", ""),
    ("seismic design category anchorage overstrength", "seismic_rack_design.md",
     "Seismic Design Category"),
    ("what's still open on the new balance job", "25-1642_new_balance_slc.json", "Open questions"),
    ("what did we decide about the aisles at new balance", "25-1642_new_balance_slc.json", ""),
    ("how wide does the flue space need to be between pallets", "nfpa13.md", "Flue"),
    ("what makes a warehouse S-1 vs S-2", "ibc_ifc.md", "Occupancy"),
    ("how tall can a sprinklered type IIB building be", "ibc_ifc.md", "height"),
    ("is footwear class 4 or group A plastic", "nfpa13.md", ""),
    ("what is the max ceiling height for ESFR without in-rack", "nfpa13.md", "ESFR"),
    ("do we need horizontal barriers with extended coverage in-rack", "nfpa13.md", "In-rack"),
    ("what R value do racks use for seismic", "methodology.md", "Cs"),
    ("how do I run the levels tool", "README.md", ""),
    ("what does FM require for commodity classification", "fm_global.md", "8-1"),
    ("interlake beam capacity 144 inch", "rack_catalog.json", "Interlake"),
    ("spacerak 506M capacity", "rack_catalog.json", "SpaceRAK"),
    ("what welded interlake frames are there", "rack_catalog.json", "Welded"),
    ("what's the clearance convention when we add in rack", "seismic_rack_design.md",
     "Clearance convention"),
    ("washington state adopted fire code", "adopted_codes_ca_wa.md", "Washington"),
    ("california fire code edition 2026", "adopted_codes_ca_wa.md", "California"),
    ("idle plastic pallets", "nfpa13.md", ""),
    ("base shear formula Cs Ws", "methodology.md", "base shear"),
    ("can single row racks tied across the aisle avoid in-rack",
     "25-1642_new_balance_slc.json", ""),
    ("what clear height is the new balance building", "25-1642_new_balance_slc.json", ""),
    ("ESFR above 45 ft specific application listing", "nfpa13.md", "ESFR"),
    ("EC in-rack vertical spacing", "nfpa13.md", "In-rack"),
    ("open rack definition 50 percent open wire deck", "nfpa13.md", "solid shelving"),
]


def _rank(idx, q, f, hp):
    for i, h in enumerate(top(idx, q)):
        if h.file.endswith(f) and hp.lower() in h.heading.lower():
            return i
    return None


@pytest.mark.parametrize("question, file, heading_part", BATTERY)
def test_battery_top3(idx, question, file, heading_part):
    assert _rank(idx, question, file, heading_part) is not None


def test_battery_top1_rate(idx):
    first = sum(_rank(idx, q, f, hp) == 0 for q, f, hp in BATTERY)
    assert first / len(BATTERY) >= 0.85, f"top-1 {first}/{len(BATTERY)}"


def test_hits_carry_snippet_and_line(idx):
    h = top(idx, "ESFR clearance top of storage", 1)[0]
    assert h.snippet and h.snippet_line >= h.line and h.score > 0


# --- routing ---------------------------------------------------------------------------
def test_routes():
    assert any("fire_check" in r["tool"] for r in ask.route("can we skip in-rack sprinklers?"))
    assert any("levels" in r["tool"] for r in ask.route("how many levels fit with 3.5 beams"))
    assert any(r["tool"].startswith("python -m rack_selector --")
               for r in ask.route("which upright frame and seismic Cs"))
    assert ask.route("what is commodity class III") == []


def test_no_match_returns_empty(idx):
    assert top(idx, "zzzz qqqq") == []
    assert top(idx, "the and of") == []          # stopwords only


# --- freshness --------------------------------------------------------------------------
@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    kb = tmp_path / "knowledge_base"
    kb.mkdir()
    (kb / "a.md").write_text("# Alpha\nESFR clearance is 36 in.\n", encoding="utf-8")
    monkeypatch.setattr(ask, "KB_DIR", str(kb))
    monkeypatch.setattr(ask, "ROOT", str(tmp_path))
    monkeypatch.setattr(ask, "EXTRA_SOURCES", [])
    monkeypatch.setattr(ask, "PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setattr(ask, "CATALOG_PATH", str(tmp_path / "none.json"))
    monkeypatch.setattr(ask, "INDEX_PATH", str(kb / "_index.json"))
    return tmp_path


def test_index_is_cached_then_rebuilt_when_stale(sandbox):
    first = ask.load_index()
    assert first["n"] == 1 and os.path.exists(ask.INDEX_PATH)
    assert ask.load_index()["fingerprint"] == first["fingerprint"]          # cache hit
    (sandbox / "knowledge_base" / "b.md").write_text("# Beta\nFlue 6 in.\n", encoding="utf-8")
    second = ask.load_index()
    assert second["n"] == 2 and second["fingerprint"] != first["fingerprint"]


def test_new_project_profile_triggers_rebuild(sandbox):
    ask.load_index()
    (sandbox / "projects").mkdir()
    (sandbox / "projects" / "99-0001_demo.json").write_text(
        '{"project_id": "99-0001", "name": "Demo", "open_questions": ["Insurer?"]}',
        encoding="utf-8")
    (sandbox / "projects" / "_TEMPLATE.json").write_text('{"project_id": "x"}', encoding="utf-8")
    heads = [d["section"]["heading"] for d in ask.load_index()["docs"]]
    assert any("99-0001" in h and h.endswith("Open questions") for h in heads)
    assert not any("Project x" in h for h in heads)                       # templates skipped


def test_corrupt_cache_is_rebuilt(sandbox):
    with open(ask.INDEX_PATH, "w", encoding="utf-8") as fh:
        fh.write("{not json")
    assert ask.load_index()["n"] == 1


# --- CLI --------------------------------------------------------------------------------
def test_cli_text_json_and_status(capsys):
    assert ask.main(["ESFR", "clearance"]) == 0
    assert "nfpa13.md" in capsys.readouterr().out
    assert ask.main(["ESFR", "clearance", "--json", "--top", "2"]) == 0
    out = capsys.readouterr().out
    assert '"hits"' in out and '"routes"' in out
    assert ask.main([]) == 0
    assert "sections from" in capsys.readouterr().out
