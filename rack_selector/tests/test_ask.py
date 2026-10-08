import pytest

from rack_selector import ask


@pytest.fixture(scope="module")
def idx():
    return ask.build_index(write=False)


def top(idx, q, n=1):
    return ask.query(q, top=n, index=idx)


def test_index_covers_kb(idx):
    files = {d["section"]["file"] for d in idx["docs"]}
    for f in ("knowledge_base/nfpa13.md", "knowledge_base/ibc_ifc.md",
              "knowledge_base/adopted_codes_utah.md", "knowledge_base/fm_global.md",
              "rack_selector/methodology.md"):
        assert f in files
    assert idx["n"] > 40


def test_sources_sections_not_indexed(idx):
    assert not any(d["section"]["heading"].endswith("Sources") for d in idx["docs"])


def test_tokenize_splits_hyphenated_terms():
    toks = ask.tokenize("In-rack sprinklers for the K-25.2 ESFR")
    assert "in-rack" in toks and "rack" in toks and "k-25.2" in toks
    assert "the" not in toks


@pytest.mark.parametrize("question, file, heading_part", [
    ("what clearance do ESFR sprinklers need to the top of storage",
     "knowledge_base/nfpa13.md", "Clearances"),
    ("does Class IV trigger high-piled storage at 6 ft",
     "knowledge_base/ibc_ifc.md", "High-Piled"),
    ("which NFPA 13 edition applies in Salt Lake City",
     "knowledge_base/adopted_codes_utah.md", "Adopted Code Editions"),
    ("can we avoid in-rack sprinklers with wire decks and hand-stack cartons",
     "knowledge_base/nfpa13.md", "solid shelving"),
    ("FM global insured site which data sheet governs",
     "knowledge_base/fm_global.md", "FM Global"),
    ("seismic design category anchorage overstrength",
     "knowledge_base/seismic_rack_design.md", "Seismic Design Category"),
])
def test_sample_queries_hit_expected_section(idx, question, file, heading_part):
    h = top(idx, question)[0]
    assert h.file == file
    assert heading_part.lower() in h.heading.lower()
    assert h.snippet and h.snippet_line >= h.line


def test_routes():
    assert any("fire_check" in r["tool"] for r in ask.route("can we skip in-rack sprinklers?"))
    assert any("levels" in r["tool"] for r in ask.route("how many levels fit with 3.5 beams"))
    assert any(r["tool"].startswith("python -m rack_selector --")
               for r in ask.route("which upright frame and seismic Cs"))
    assert ask.route("what is commodity class III") == []


def test_no_match_returns_empty(idx):
    assert top(idx, "zzzz qqqq") == []


def test_stale_index_rebuilds(tmp_path, monkeypatch):
    kb = tmp_path / "knowledge_base"
    kb.mkdir()
    (kb / "a.md").write_text("# Alpha\nESFR clearance is 36 in.\n", encoding="utf-8")
    monkeypatch.setattr(ask, "KB_DIR", str(kb))
    monkeypatch.setattr(ask, "ROOT", str(tmp_path))
    monkeypatch.setattr(ask, "EXTRA_SOURCES", [])
    monkeypatch.setattr(ask, "INDEX_PATH", str(kb / "_index.json"))
    first = ask.load_index()
    assert first["n"] == 1
    (kb / "b.md").write_text("# Beta\nFlue spaces are 6 in.\n", encoding="utf-8")
    second = ask.load_index()
    assert second["n"] == 2 and second["fingerprint"] != first["fingerprint"]


def test_cli_runs(capsys):
    assert ask.main(["ESFR", "clearance"]) == 0
    assert "nfpa13.md" in capsys.readouterr().out
