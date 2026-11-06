"""§9.19 The validation pack: intended use, `qualify`, the tool risk file, known anomalies
(R-110..R-115, C-29..C-31, I-022, I-023, E-85..E-88; v1.26).

Tool-hazard (`TH-01`), case (`OQ-01`) and anomaly (`KA-01`) labels are not spec-id tokens, so
naming them here cites nothing.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from speccheck.extract import parse_spec

from .conftest import run_cli

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "speccheck"
QDATA = PKG / "_qualify"
SPEC_TEXT = (ROOT / "SPEC.md").read_text(encoding="utf-8")


def _hazard_table() -> dict[str, tuple[str, list[str], list[str]]]:
    """C-30's hazard table: id -> (title, controlled-by ids, OQ cases)."""
    start = SPEC_TEXT.index("| Hazard | Title (as in `tool_risk.json`)")
    out: dict[str, tuple[str, list[str], list[str]]] = {}
    for line in SPEC_TEXT[start:].split("\n")[2:]:
        if not line.startswith("| TH-"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        out[cells[0]] = (cells[1], cells[2].split(", "), cells[3].split(", "))
    return out


def _intended_use_block() -> str:
    i = SPEC_TEXT.index("**Intended use (v1.26; R-110, D-67).**")
    start = SPEC_TEXT.index("```text\n", i) + len("```text\n")
    return SPEC_TEXT[start : SPEC_TEXT.index("\n```\n", start) + 1]


def _tracked(directory: Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def test_intended_use_block_is_packaged_byte_for_byte():
    """T-130 (the R-110 half that needs no wheel): SPEC.md §0's *Intended use* block — the lines
    between its fence lines, each ending in a newline — equals `_qualify/intended_use.md` byte for
    byte, and it states the validated function and the advisory surfaces. (R-110)"""
    block = _intended_use_block()
    assert (QDATA / "intended_use.md").read_bytes() == block.encode("utf-8")
    assert (
        "Validated function: `speccheck check`, `speccheck verify` and `speccheck impact`" in block
    )
    assert "`--judge none` or `--judge mock`" in block
    assert (
        "Outside validated use: `--judge llm`, `--jev-pre-triage` and `speccheck explain`" in block
    )


def test_tool_risk_file_markers_cases_and_anomalies_agree():
    """T-135: `tool_risk.json` is a C-28 file whose ids and titles equal C-30's hazard table;
    every *Controlled by* id carries exactly the hazards the table gives it in its CONTROLS marker,
    and no other declaration carries a tool hazard; every hazard is challenged by some case and
    the table's OQ column equals the catalog's; every anomaly has C-31's shape and names only
    tool hazards; every case's fixture and goldens exist. (R-114, R-115, C-30, C-31)"""
    table = _hazard_table()
    assert list(table) == [f"TH-{n:02d}" for n in range(1, 11)]
    risk = json.loads((QDATA / "tool_risk.json").read_text(encoding="utf-8"))
    assert risk == {"hazards": [{"id": h, "title": t} for h, (t, _c, _q) in table.items()]}

    expected: dict[str, list[str]] = {}
    for hazard, (_title, controls, _cases) in table.items():
        for ident in controls:
            expected.setdefault(ident, []).append(hazard)
    index = parse_spec(SPEC_TEXT, "SPEC.md")
    marked = {s.id: list(s.controls) for s in index.ids if s.controls}
    assert marked == {k: sorted(v) for k, v in expected.items()}
    assert len(marked) == 31

    cases = json.loads((QDATA / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert [c["id"] for c in cases] == [f"OQ-{n:02d}" for n in range(1, 6)]
    challenged = {h: [c["id"] for c in cases if h in c["hazards"]] for h in table}
    assert challenged == {h: sorted(q) for h, (_t, _c, q) in table.items()}
    for case in cases:
        fixture = PKG / case["fixture"]
        assert fixture.is_dir(), case["fixture"]
        for step in case["steps"]:
            assert set(step) == {"argv", "edit", "exit", "stdout", "goldens"}
            assert step["stdout"].endswith("\n")
            for golden in step["goldens"].values():
                assert (fixture / golden).is_file(), golden
            if step["edit"] is not None:
                assert (fixture / step["edit"]["append"]).is_file()

    anomalies = json.loads((QDATA / "known_anomalies.json").read_text(encoding="utf-8"))
    entries = anomalies["anomalies"]
    assert [a["id"] for a in entries] == [f"KA-{n:02d}" for n in range(1, 6)]
    version = re.compile(r"\d+\.\d+\.\d+")
    for a in entries:
        assert list(a) == ["id", "summary", "hazards", "workaround", "found_in", "fixed_in"]
        assert a["hazards"] and set(a["hazards"]) <= set(table)
        assert a["summary"] and a["workaround"]
        assert version.fullmatch(a["found_in"])
        assert a["fixed_in"] is None or version.fullmatch(a["fixed_in"])


def test_packaged_fixture_copies_do_not_drift():
    """T-135 (drift): `_qualify/swift/` is byte-identical to `fixtures/target-swift/`, and
    `_qualify/hazards/` to the §9.8 fixture except its SPEC.md, `risk.json` and `golden/`; its
    SPEC.md differs from the fixture's only by three CONTROLS markers. (C-30)"""
    assert _tracked(QDATA / "swift") == _tracked(ROOT / "fixtures" / "target-swift")
    target = _tracked(ROOT / "fixtures" / "target")
    hazards = _tracked(QDATA / "hazards")
    own = {"SPEC.md", "risk.json"}
    assert {k: v for k, v in hazards.items() if k not in own and not k.startswith("golden/")} == {
        k: v for k, v in target.items() if k != "SPEC.md" and not k.startswith("golden/")
    }
    stripped = re.sub(r" \*\(controls: [^)]*\)\*", "", hazards["SPEC.md"].decode("utf-8"))
    assert stripped == target["SPEC.md"].decode("utf-8")
    assert hazards["SPEC.md"].decode("utf-8").count("*(controls: ") == 3


def test_self_application_lists_every_tool_hazard_with_its_controls(tmp_path: Path):
    """T-135 (self-application half): `check --risk-file src/speccheck/_qualify/tool_risk.json`
    over this repository lists exactly the ten tool hazards, each with C-30's *Controlled by* ids
    as its `controls` (in C-07 id order). Whether every control is PASSING needs this suite's own
    results and is recorded with T-48 (F-901). (R-114, C-30)"""
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(ROOT / "SPEC.md", repo / "SPEC.md")
    shutil.copytree(PKG, repo / "src" / "speccheck", ignore=shutil.ignore_patterns("__pycache__"))
    run = run_cli(
        [
            "check",
            "--spec",
            "SPEC.md",
            "--src",
            "src",
            "--judge",
            "mock",
            "--risk-file",
            "src/speccheck/_qualify/tool_risk.json",
            "--out",
            "out",
        ],
        repo,
    )
    assert run.code in (0, 1), run.stderr
    doc = run.json_at(repo / "out")
    order = [r["id"] for r in doc["ids"]]
    table = _hazard_table()
    assert [h["id"] for h in doc["hazards"]] == list(table)
    for h in doc["hazards"]:
        title, controls, _cases = table[h["id"]]
        assert h["title"] == title
        assert h["controls"] == sorted(controls, key=order.index)
    assert re.search(r"; hazards: \d+/10 verified\n$", run.stdout), run.stdout
