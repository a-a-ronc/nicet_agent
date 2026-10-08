"""
ask — query index over the knowledge base.

Builds a section-level index of knowledge_base/*.md (plus rack_selector/methodology.md),
scores sections against a plain-English question with BM25 + domain synonyms, and
returns the best sections with file:line references, the most relevant line, and which
tool to run for a numeric answer.

  python -m rack_selector.ask "do we need in-rack sprinklers with wire decks?"
  python -m rack_selector.ask "ESFR clearance to top of storage" --top 3
  python -m rack_selector.ask --rebuild          # force a rebuild of the index

The index is cached in knowledge_base/_index.json and rebuilt automatically whenever a
source file changes. Stdlib only. This finds where the KB answers a question — the
answer still has to cite the adopted edition and carry the FPE/PE review caveat.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(ROOT, "knowledge_base")
EXTRA_SOURCES = [os.path.join(ROOT, "rack_selector", "methodology.md"),
                 os.path.join(ROOT, "rack_selector", "README.md")]
PROJECTS_DIR = os.path.join(ROOT, "projects")
INDEX_PATH = os.path.join(KB_DIR, "_index.json")
INDEX_VERSION = 5
HEADING_BOOST = 1.0
CATALOG_PATH = os.path.join(ROOT, "rack_selector", "data", "rack_catalog.json")
SKIP_HEADINGS = {"sources"}
# Routing/navigation files rank below substantive sections.
FILE_WEIGHT = {"knowledge_base/00_INDEX.md": 0.6}

_TOKEN = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*")
_HEADING = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")

STOPWORDS = set("""
a an and are as at be been but by can could do does did for from had has have how i if
in into is it its me my no not of on or our should so than that the their them then there
these they this to us was we were what when where which who why will with would you your
any all also get got need needs needed use used using about up out over under per vs via
""".split())

# Query-side expansion: each key adds the listed terms (all lowercase tokens).
SYNONYMS = {
    "inrack": ["in-rack", "iras", "in", "rack"],
    "in-rack": ["iras", "inrack"],
    "iras": ["in-rack"],
    "sprinkler": ["sprinklers"],
    "sprinklers": ["sprinkler"],
    "deflector": ["clearance"],
    "clearance": ["deflector", "clearances"],
    "deck": ["decks", "decking", "shelving", "shelf", "wire"],
    "decks": ["deck", "decking", "shelving", "wire"],
    "wire": ["deck", "mesh", "shelving"],
    "handstack": ["hand-stack", "shelf", "shelving", "deck"],
    "hand-stack": ["handstack", "shelf", "shelving"],
    "shelving": ["shelf", "solid", "open"],
    "flue": ["flues", "transverse", "longitudinal"],
    "flues": ["flue"],
    "aisle": ["aisles"],
    "aisles": ["aisle"],
    "fm": ["global", "8-9", "ds"],
    "insurer": ["fm", "global"],
    "edition": ["adopted", "editions"],
    "adopted": ["edition", "editions"],
    "code": ["edition", "adopted"],
    "utah": ["ut", "slc", "salt", "lake"],
    "slc": ["utah", "salt", "lake"],
    "california": ["ca", "cfc", "cbc"],
    "washington": ["wa", "sbcc"],
    "seismic": ["sdc", "asce", "earthquake", "cs"],
    "earthquake": ["seismic"],
    "high-piled": ["high", "piled", "3206", "ch"],
    "commodity": ["class", "classification"],
    "plastic": ["plastics", "group"],
    "plastics": ["plastic", "group"],
    "beam": ["beams", "pitch", "elevation"],
    "beams": ["beam"],
    "level": ["levels", "tier"],
    "levels": ["level", "tier"],
    "tier": ["level", "levels"],
    "frame": ["frames", "upright"],
    "upright": ["frame", "uprights"],
    "ceiling": ["height", "esfr"],
    "esfr": ["k-25.2", "ceiling"],
    "density": ["cmda", "design", "area"],
    "anchor": ["anchorage", "base", "overstrength"],
    "800mm": ["31.5"],
    "tied": ["tie", "cross-aisle"],
    "tie": ["cross-aisle", "tied"],
    "run": ["python", "command"],
    "tool": ["python", "command", "rack", "selector"],
    "capacity": ["capacities", "lb"],
    "dealer": ["interlake", "spacerak", "hannibal", "catalog"],
    "catalog": ["dealer", "published", "representative"],
}

# Tool routing: (pattern, tool, why)
ROUTES = [
    (r"in[- ]?rack|iras|avoid|virtual floor|solid shel|wire deck|open rack|esfr.*(ceiling|height)"
     r"|ceiling[- ]only",
     "python -m rack_selector.fire_check --project projects/<job>.json",
     "in-rack decision (open rack vs solid shelving, ESFR envelope, listings, level plan)"),
    (r"how many levels|levels fit|pitch|clear opening|opening|beam (size|height)|3\.5|5\s*(in|\")"
     r"|800 ?mm|31\.5",
     "python -m rack_selector.levels --load-height <in> --beams 3.5,5 --deflector-height-ft <ft>",
     "pitch / clear opening / levels that fit"),
    (r"frame|upright|beam capacity|capacit|seismic|base shear|\bcs\b|anchor|which rack|rack type",
     "python -m rack_selector --project projects/<job>.json --levels <n> --shelf-load <lb>",
     "frame/beam selection + ASCE 7 seismic"),
]


def stem(t: str) -> str:
    """Tiny plural normalizer: racks->rack, flues->flue, boxes->box, categories->category."""
    if len(t) <= 3 or not t.isalpha():
        return t
    if t.endswith("ies") and len(t) > 4:
        return t[:-3] + "y"
    if t.endswith(("sses", "xes", "zes", "ches", "shes")):
        return t[:-2]
    if t.endswith("s") and not t.endswith(("ss", "us", "is")):
        return t[:-1]
    return t


def tokenize(text: str) -> list:
    toks = []
    for t in _TOKEN.findall(text.lower()):
        if t in STOPWORDS:
            continue
        toks.append(stem(t))
        if "-" in t:  # also index the parts of hyphenated terms (in-rack -> in, rack)
            toks.extend(stem(p) for p in t.split("-") if p and p not in STOPWORDS)
        if "." in t:  # rack_selector.levels -> selector, levels (alpha parts only)
            toks.extend(stem(p) for p in t.split(".") if p.isalpha() and p not in STOPWORDS)
    return toks


@dataclass
class Section:
    file: str        # repo-relative path
    heading: str     # "Parent > Child"
    line: int        # 1-based line of the heading
    text: str


def _sources() -> list:
    """Markdown sources: knowledge_base/*.md + tool docs."""
    files = sorted(os.path.join(KB_DIR, f) for f in os.listdir(KB_DIR) if f.endswith(".md"))
    return files + [p for p in EXTRA_SOURCES if os.path.exists(p)]


def _project_sources() -> list:
    """Project profiles (projects/*.json, excluding _TEMPLATE-style files)."""
    if not os.path.isdir(PROJECTS_DIR):
        return []
    return sorted(os.path.join(PROJECTS_DIR, f) for f in os.listdir(PROJECTS_DIR)
                  if f.endswith(".json") and not f.startswith("_"))


def _all_sources() -> list:
    extra = [CATALOG_PATH] if os.path.exists(CATALOG_PATH) else []
    return _sources() + _project_sources() + extra


def catalog_sections(path: str) -> list:
    """One section per dealer family in rack_catalog.json (beams and frames)."""
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    cat = json.loads(raw)
    lines = raw.splitlines()
    out = []
    for kind, cap_key, label in (("beams", "capacity_by_length_lb", "beam"),
                                 ("frames", "capacity_by_unsupported_length_lb", "frame")):
        for fam in cat.get(kind, []):
            line = next((i for i, ln in enumerate(lines, 1)
                         if f'"family": "{fam["family"]}"' in ln), 1)
            body = [f"{fam['dealer']} {fam['family']} — {fam['confidence']} data. {fam.get('note', '')}",
                    f"Source: {fam.get('source', '')}"]
            for m in fam["models"]:
                size = (f"face {m['face_in']} in" if "face_in" in m else f"column {m.get('column', '')}")
                caps = ", ".join(f"{k} in = {v:,} lb" for k, v in m[cap_key].items())
                unit = "per pair at length" if kind == "beams" else "per frame at unsupported length"
                body.append(f"{label} {m['id']} ({size}) capacity {unit}: {caps}")
            out.append(Section(rel, f"Rack catalog > {kind.title()} > {fam['dealer']} "
                                    f"{fam['family']}", line, "\n".join(body)))
    return out


def _flatten(prefix: str, value, out: list) -> None:
    if value is None or value == [] or value == {}:
        return
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten(f"{prefix} {k}".strip(), v, out)
    elif isinstance(value, list) and all(isinstance(v, (str, int, float)) for v in value):
        out.append(f"{prefix.replace('_', ' ')}: {', '.join(str(v) for v in value)}")
    elif isinstance(value, list):
        for v in value:
            _flatten(prefix, v, out)
    else:
        out.append(f"{prefix.replace('_', ' ')}: {value}")


def project_sections(path: str) -> list:
    """Turn a project profile into Overview / Open questions / History sections."""
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    proj = json.loads(raw)
    lines = raw.splitlines()

    def line_of(key: str) -> int:
        return next((i for i, ln in enumerate(lines, 1) if f'"{key}"' in ln), 1)

    title = f"Project {proj.get('project_id', '?')} — {proj.get('name', '')}"
    overview: list = []
    for key in ("client", "drawing", "insurer", "site", "building", "fire", "rack"):
        _flatten(key, proj.get(key), overview)
    out = [Section(rel, f"{title} > Overview", 1, "\n".join(overview))]
    for key, label in (("open_questions", "Open questions"), ("history", "History")):
        items = proj.get(key) or []
        if items:
            out.append(Section(rel, f"{title} > {label}", line_of(key),
                               "\n".join(f"- {x}" for x in items)))
    return out


def _fingerprint(paths: list) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(os.path.relpath(p, ROOT).encode())
        with open(p, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


def split_sections(path: str) -> list:
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    sections, stack, buf, start = [], [], [], 1
    title = os.path.basename(path)

    def flush():
        body = "\n".join(buf).strip()
        if stack and stack[-1][1].lower() in SKIP_HEADINGS:
            return  # link lists add noise, not answers
        if body:
            sections.append(Section(rel, " > ".join(h for _, h in stack) or title, start, body))

    for i, line in enumerate(lines, 1):
        m = _HEADING.match(line)
        if m:
            flush()
            level, heading = len(m.group(1)), m.group(2).strip("# ").strip()
            stack = [(lv, h) for lv, h in stack if lv < level] + [(level, heading)]
            buf, start = [line], i
        else:
            buf.append(line)
    flush()
    return sections


def build_index(write: bool = True) -> dict:
    paths = _all_sources()
    sections = [s for p in _sources() for s in split_sections(p)]
    sections += [s for p in _project_sources() for s in project_sections(p)]
    if os.path.exists(CATALOG_PATH):
        sections += catalog_sections(CATALOG_PATH)
    docs = []
    df: dict = {}
    for s in sections:
        toks = tokenize(s.heading + " " + s.heading + " " + s.text)  # heading weighted x2
        tf: dict = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        for t in tf:
            df[t] = df.get(t, 0) + 1
        docs.append({"section": asdict(s), "tf": tf, "len": len(toks),
                     "htoks": sorted(set(tokenize(s.heading)))})
    index = {
        "version": INDEX_VERSION,
        "fingerprint": _fingerprint(paths),
        "n": len(docs),
        "avgdl": (sum(d["len"] for d in docs) / len(docs)) if docs else 0.0,
        "df": df,
        "docs": docs,
    }
    if write:
        with open(INDEX_PATH, "w", encoding="utf-8") as fh:
            json.dump(index, fh)
    return index


def load_index(rebuild: bool = False) -> dict:
    """Load the cached index, rebuilding if missing, stale, or forced."""
    if not rebuild and os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, encoding="utf-8") as fh:
                idx = json.load(fh)
            if (idx.get("version") == INDEX_VERSION
                    and idx.get("fingerprint") == _fingerprint(_all_sources())):
                return idx
        except (OSError, ValueError):
            pass
    try:
        return build_index(write=True)
    except OSError:
        return build_index(write=False)


def expand_query(q: str) -> list:
    base = tokenize(q)
    if re.search(r"in\s*rack", q.lower()):
        base.append("in-rack")
    out = list(base)
    for t in base:
        for syn in SYNONYMS.get(t, []):
            out.extend(tokenize(syn))
    return out


def route(q: str) -> list:
    ql = q.lower()
    return [{"tool": tool, "why": why} for pat, tool, why in ROUTES if re.search(pat, ql)]


@dataclass
class Hit:
    score: float
    file: str
    line: int
    heading: str
    snippet: str
    snippet_line: int


def _best_line(text: str, start_line: int, terms: set) -> tuple:
    best, best_n, best_i = "", -1, 0
    for i, ln in enumerate(text.splitlines()):
        s = ln.strip()
        if not s or s.startswith("#") or set(s) <= set("|-: "):
            continue
        n = len(terms & set(tokenize(s)))
        if n > best_n:
            best, best_n, best_i = s, n, i
    return best[:240], start_line + best_i


def query(q: str, top: int = 5, index: Optional[dict] = None, k1: float = 1.4,
          b: float = 0.75) -> list:
    idx = index or load_index()
    terms = expand_query(q)
    if not terms or not idx["docs"]:
        return []
    qtf: dict = {}
    for t in terms:
        qtf[t] = qtf.get(t, 0) + 1
    N, avgdl, df = idx["n"], idx["avgdl"] or 1.0, idx["df"]
    qbase = set(tokenize(q))
    scored = []
    for d in idx["docs"]:
        tf, dl, s = d["tf"], d["len"], 0.0
        for t, qn in qtf.items():
            f = tf.get(t)
            if not f:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            s += qn * idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        s *= FILE_WEIGHT.get(d["section"]["file"], 1.0)
        if s > 0 and qbase:
            # Heading boost: up to 2x when every question term appears in the heading.
            s *= 1.0 + HEADING_BOOST * len(qbase & set(d.get("htoks", []))) / len(qbase)
        if s > 0:
            scored.append((s, d["section"]))
    scored.sort(key=lambda x: -x[0])
    tset = set(terms)
    hits = []
    for s, sec in scored[:top]:
        snip, sl = _best_line(sec["text"], sec["line"], tset)
        hits.append(Hit(round(s, 3), sec["file"], sec["line"], sec["heading"], snip, sl))
    return hits


def render(q: str, hits: list, routes: list) -> str:
    L = [f'Q: {q}', ""]
    if not hits:
        L.append("No matching KB sections. Rephrase, or the KB may not cover this yet.")
    for i, h in enumerate(hits, 1):
        L.append(f"{i}. {h.file}:{h.line}  —  {h.heading}   (score {h.score})")
        if h.snippet:
            L.append(f"     line {h.snippet_line}: {h.snippet}")
    if routes:
        L.append("")
        L.append("For a numeric / project-specific answer, run:")
        for r in routes:
            L.append(f"  - {r['tool']}    # {r['why']}")
    L.append("")
    L.append("Quote the ADOPTED edition for the jurisdiction (knowledge_base/adopted_codes_*.md) "
             "and keep the FPE/PE review caveat.")
    return "\n".join(L)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="rack_selector.ask", description="Query the nicet_agent KB.")
    p.add_argument("question", nargs="*")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--rebuild", action="store_true", help="Force an index rebuild")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    from ._io import safe_stdout
    safe_stdout()
    idx = load_index(rebuild=a.rebuild)
    q = " ".join(a.question).strip()
    if not q:
        print(f"Index: {idx['n']} sections from {len(_sources())} markdown files, "
              f"{len(_project_sources())} project profile(s) and the rack catalog -> {INDEX_PATH}")
        return 0
    hits, routes = query(q, a.top, idx), route(q)
    if a.json:
        print(json.dumps({"question": q, "hits": [asdict(h) for h in hits], "routes": routes},
                         indent=2))
    else:
        print(render(q, hits, routes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
