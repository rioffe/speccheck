"""§9.13 `explain` (C-18; v1.17)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .conftest import FIXTURE, run_cli

ARGS = [
    "explain",
    "R-01",
    "--spec",
    "SPEC.md",
    "--src",
    "src",
    "--tests",
    "tests",
    "--results",
    "junit.xml",
    "--judge",
    "mock",
]

# C-18: R-01's trace, exactly (the fixture's own facts: one source citation, five citing cases,
# each with the mock's verdict, and the walk's one dependent plus the one T id that verifies it)
R01_TRACE = """\
ID R-01
status: PASSING (step 4: every citing test case passed)
statement:
  `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
sources:
  src/calc/core.py:10
tests:
  tests/test_core.py::test_add (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: mock: assertion token on 1 line(s)
  tests/test_core.py::test_add_result (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: mock: assertion token on 1 line(s)
  tests/test_core.py::test_add_rounding_fact (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: mock: assertion token on 1 line(s)
  tests/test_core.py::test_add_rounding_of_a_half_cent (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: mock: assertion token on 1 line(s)
  tests/test_summary.py::test_summary_module_does_not_change_add (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: mock: assertion token on 2 line(s)
impact (1):
  I-001 (depth 1, via I-001 -depends_on-> R-01)
  T-01 verifies R-01
"""


def _copy(tmp_path: Path) -> Path:
    dst = tmp_path / "target"
    shutil.copytree(FIXTURE, dst)
    return dst


def _tree_digest(root: Path) -> str:
    """A digest over every file under `root`, so a run that writes anything is caught (T-38)."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_t92_explain_golden_trace_is_stable(tmp_path: Path):
    """T-92: `explain R-01` on a copy of the fixture prints exactly the C-18 trace — the ID line,
    the status with its C-05 reason, `statement:`, its `sources:` line, each citing case with its
    outcome and mock verdict (clause and rationale included), and the `impact (1):` section —
    exits 0, writes nothing at all (the copy is byte-identical before and after), a second
    identical run is byte-identical, and the status shown equals R-01's status in
    `golden/speccheck.json` from the same inputs. (R-40, C-18, I-016)"""
    target = _copy(tmp_path)
    before = _tree_digest(target)
    run = run_cli(ARGS + ["--root", "."], target)
    assert run.code == 0, run.stderr
    assert run.stdout == R01_TRACE
    # nothing was written: no report, no temporary, no `--out` directory a `check` would create
    assert _tree_digest(target) == before
    assert not (target / "speccheck.json").exists() and not (target / "out").exists()
    # a second run is byte-identical, and the status is the one the golden JSON records
    again = run_cli(ARGS + ["--root", "."], target)
    assert again.stdout == run.stdout
    golden = json.loads((FIXTURE / "golden" / "speccheck.json").read_text(encoding="utf-8"))
    status = next(r["status"] for r in golden["ids"] if r["id"] == "R-01")
    assert f"status: {status} (" in run.stdout
    # `--depth 0` (unbounded) widens only the impact heading here — R-01's walk is one hop deep —
    # and the trace is still byte-stable
    deep = run_cli(ARGS + ["--root", ".", "--depth", "0"], target)
    assert deep.code == 0
    assert deep.stdout == run.stdout.replace("impact (1):", "impact (0):")


def test_t93_explain_undeclared_retired_and_uncited(tmp_path: Path):
    """T-93: `explain R-09` (an id the fixture does not declare) exits 2 with E-60's message and
    prints no trace; `explain R-04` (the fixture's retired id) renders `ID R-04 (RETIRED)` with the
    retired reason and exits 0; `explain C-02` (declared, cited in `src/` only) renders its status
    reason with an empty `tests:` block and exits 0; `--out` and `--strict` are not flags of the
    subcommand, so each is a usage error. (R-40, C-18, E-60)"""
    target = _copy(tmp_path)
    undeclared = run_cli([*ARGS[:1], "R-09", *ARGS[2:], "--root", "."], target)
    assert undeclared.code == 2
    assert "explain: undeclared id: R-09" in undeclared.stderr
    assert undeclared.stdout == ""

    retired = run_cli([*ARGS[:1], "R-04", *ARGS[2:], "--root", "."], target)
    assert retired.code == 0, retired.stderr
    assert retired.stdout.splitlines()[:2] == [
        "ID R-04 (RETIRED)",
        "status: RETIRED (retired: struck through in the specification)",
    ]

    untested = run_cli([*ARGS[:1], "C-02", *ARGS[2:], "--root", "."], target)
    assert untested.code == 0, untested.stderr
    body = untested.stdout.splitlines()
    assert body[0] == "ID C-02" and body[1] == "status: UNTESTED (step 2: no test citation)"
    assert body[body.index("sources:") + 1] == "  src/calc/core.py:27"
    # an empty block: the heading is printed and the next line is the following heading (E-60)
    assert body[body.index("tests:") + 1] == "impact (1):"

    for flag in ("--out", "--strict"):
        rejected = run_cli([*ARGS[:1], "R-01", *ARGS[2:], "--root", ".", flag, "x"], target)
        assert rejected.code == 2, flag
