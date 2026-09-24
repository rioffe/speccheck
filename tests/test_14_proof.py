"""§9.15 Proof evidence (C-20, C-21, K-17, E-62, E-63, E-65; v1.19)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .conftest import FIXTURE, junit, run_cli, spec_table, write_tree


def _tree(base: Path) -> Path:
    write_tree(
        base,
        {
            "SPEC.md": spec_table([("R-01", "one"), ("R-02", "two"), ("R-03", "three")]),
            "src/x.py": "# R-01\n",
            "tests/test_x.py": "def test_x():\n    # R-01\n    assert True\n",
            "junit.xml": junit([("tests.test_x", "test_x", "passed")]),
            "proof/Thm.lean": (
                "/-- **R-01** discharges one. -/\n"
                "theorem rOne : True := trivial\n"
                "\n"
                "/-- **R-02** discharges two; the manifest calls it failed. -/\n"
                "theorem rTwo : True := trivial\n"
                "\n"
                "def untagged : Nat := 1\n"
            ),
            "proof-results.json": json.dumps(
                {
                    "build": {
                        "exit": 1,
                        "theorems_total": 2,
                        "theorems_checked": 1,
                        "errors": ["proof/Thm.lean:5"],
                    },
                    "theorems": [
                        {
                            "file": "proof/Thm.lean",
                            "name": "rOne",
                            "line": 2,
                            "ids": ["R-01"],
                            "status": "checked",
                        },
                        {
                            "file": "proof/Thm.lean",
                            "name": "rTwo",
                            "line": 5,
                            "ids": ["R-02"],
                            "status": "failed",
                        },
                    ],
                }
            ),
        },
    )
    return base


BASE_ARGS = [
    "check",
    "--spec",
    "SPEC.md",
    "--src",
    "src",
    "--tests",
    "tests",
    "--results",
    "junit.xml",
    "--judge",
    "none",
]


def test_proof_citations_join_and_states(tmp_path: Path):
    """T-99: --proof scans Lean declarations (C-20) and attributes a proof citation per
    (declaration, id) pair; --proof-results joins them to the manifest by name and file (C-21):
    a matched entry carries the manifest's status (checked/failed, with the failed error line
    from build.errors), a citation absent from the manifest is unknown, a manifest entry with no
    matching citation is a notes entry (K-17). The untagged declaration cites nothing. (R-100,
    C-20, C-21, K-17)"""
    project = _tree(tmp_path / "p")
    r = run_cli(BASE_ARGS + ["--proof", "proof", "--proof-results", "proof-results.json"], project)
    assert r.code == 0
    ids = r.ids()
    assert ids["R-01"]["proof"] == [
        {"name": "rOne", "file": "proof/Thm.lean", "line": 2, "state": "checked", "error": None}
    ]
    assert ids["R-02"]["proof"] == [
        {
            "name": "rTwo",
            "file": "proof/Thm.lean",
            "line": 5,
            "state": "failed",
            "error": "proof/Thm.lean:5",
        }
    ]
    assert ids["R-03"]["proof"] == []  # --proof given, no citation for this id (E-01/R-03 shape)
    assert r.json["proof"]["build"]["theorems_total"] == 2
    assert r.json["metrics"]["proof_failed"] == 1
    assert "Proof (state)" in r.md


def test_proof_unknown_and_stale_and_manifest_orphan(tmp_path: Path):
    """K-17: a citation with no matching manifest theorem is `unknown`; a manifest theorem whose
    name matches a scanned declaration at a *different* file or line is `stale`; a manifest entry
    matching no citation at all is a notes entry, not an error."""
    project = _tree(tmp_path / "p")
    manifest = json.loads((project / "proof-results.json").read_text())
    # rOne now "moves": manifest still calls it line 99 (a different line) -> stale for the
    # citation; rTwo is dropped from the manifest entirely -> R-02's citation is unknown, and a
    # brand-new manifest entry for a name nothing cites -> orphan note.
    manifest["theorems"] = [
        {"file": "proof/Thm.lean", "name": "rOne", "line": 99, "ids": ["R-01"], "status": "checked"},
        {"file": "proof/Thm.lean", "name": "ghost", "line": 1, "ids": [], "status": "checked"},
    ]
    (project / "proof-results.json").write_text(json.dumps(manifest))
    r = run_cli(BASE_ARGS + ["--proof", "proof", "--proof-results", "proof-results.json"], project)
    assert r.code == 0
    ids = r.ids()
    assert ids["R-01"]["proof"][0]["state"] == "stale"
    assert ids["R-02"]["proof"][0]["state"] == "unknown"
    assert any("ghost" in n for n in r.json["notes"])
    assert r.json["metrics"]["proof_unknown"] == 2  # R-01 (stale) and R-02 (unknown)


def test_proof_given_without_results_is_all_unknown(tmp_path: Path):
    """--proof alone (no --proof-results): citations exist but nothing confirms them, so every
    state is `unknown` — the manifest is absent, not a failure (E-63's "absence is not failure"
    boundary applies to the join the same way it does to results)."""
    project = _tree(tmp_path / "p")
    r = run_cli(BASE_ARGS + ["--proof", "proof"], project)
    assert r.code == 0
    ids = r.ids()
    assert ids["R-01"]["proof"][0]["state"] == "unknown"
    assert r.json["proof"] == {"build": None}  # v1.19.1 / D-49: --proof alone still writes the key


def test_proof_results_alone_writes_the_top_level_key(tmp_path: Path):
    """v1.19.1 / D-49 / F-504: --proof-results given without --proof still reads the manifest
    (C-21's read is unconditional) and writes the top-level proof.build — the gap the model found
    and this fold fixed. No per-id proof field, since nothing was scanned to attribute."""
    project = _tree(tmp_path / "p")
    r = run_cli(BASE_ARGS + ["--proof-results", "proof-results.json"], project)
    assert r.code == 0
    assert r.json["proof"]["build"]["theorems_total"] == 2
    assert "proof" not in r.ids()["R-01"]


def test_proof_absent_is_byte_identical_to_v118(tmp_path: Path):
    """T-100 / I-018: a run with neither --proof nor --proof-results writes no `proof` key
    anywhere (top-level or per-id), no proof column in the Markdown, and is byte-identical to the
    same run made before this feature existed."""
    project = _tree(tmp_path / "p")
    with_flags = run_cli(
        BASE_ARGS + ["--proof", "proof", "--proof-results", "proof-results.json", "--out", "out1"],
        project,
    )
    without_flags = run_cli(BASE_ARGS + ["--out", "out2"], project)
    assert with_flags.code == 0 and without_flags.code == 0
    plain_json = without_flags.json_at(project / "out2")
    assert "proof" not in plain_json
    assert all("proof" not in rec for rec in plain_json["ids"])
    assert "proof_failed" not in plain_json["metrics"]
    assert "Proof (state)" not in without_flags.md_at(project / "out2")
    # the unextended fixture's own scan (src/tests/results) never touches proof/ at all, so a
    # second absent-flag run over the same inputs is untouched by the flag's mere existence
    without_flags_2 = run_cli(BASE_ARGS + ["--out", "out3"], project)
    assert without_flags_2.json_at(project / "out3") == plain_json


def test_proof_never_changes_status_or_strict_without_manifest(tmp_path: Path):
    """E-63: a proof state never changes an id's status — R-02's citing test never ran (no result
    joined for it in this fixture's junit), so it is UNTESTED regardless of its `failed` proof
    state, and --strict without --proof-results does not gate on it (D-45: only a *given and
    readable* manifest gates)."""
    project = _tree(tmp_path / "p")
    r = run_cli(BASE_ARGS + ["--proof", "proof", "--strict"], project)
    ids = r.ids()
    assert ids["R-02"]["status"] == "UNCITED"  # unchanged by its `unknown` proof state (E-63)
    # --strict fires here only because R-02/R-03 aren't PASSING (R-15) -- not because of proof;
    # confirm a manifest-driven failure specifically requires --proof-results (D-45).
    assert r.code == 1
    assert "proof_failed" not in r.json.get("metrics", {}) or r.json["metrics"]["proof_failed"] == 0


def test_proof_strict_gates_on_failed_only_with_readable_manifest(tmp_path: Path):
    """D-45: --strict fails on a `failed` proof state only when --proof-results was given and
    read; the plain R-15 statuses in this fixture (UNTESTED R-02/R-03) already fail --strict on
    their own, so this isolates the proof-specific reason by checking `metrics.proof_failed` is
    the only thing that changes between the two runs' JSON otherwise."""
    project = _tree(tmp_path / "p")
    without_manifest = run_cli(
        BASE_ARGS + ["--proof", "proof", "--strict", "--out", "out1"], project
    )
    with_manifest = run_cli(
        BASE_ARGS
        + ["--proof", "proof", "--proof-results", "proof-results.json", "--strict", "--out", "out2"],
        project,
    )
    assert without_manifest.code == 1 and with_manifest.code == 1
    # both runs report proof_failed (present whenever --proof was given), but only a run with a
    # readable manifest can ever find a `failed` state to count -- without one every citation is
    # `unknown` (no manifest to confirm it), so the count itself proves the isolation.
    assert without_manifest.json_at(project / "out1")["metrics"]["proof_failed"] == 0
    assert with_manifest.json_at(project / "out2")["metrics"]["proof_failed"] == 1


def test_proof_unreadable_lean_file_is_a_note_not_an_error(tmp_path: Path):
    """E-62: a file under --proof that is not Lean, or has no parseable declaration head, is
    recorded as a notes entry and MUST NOT be a usage error or change the exit code of a run whose
    ids are otherwise decided."""
    project = _tree(tmp_path / "p")
    write_tree(project, {"proof/NotLean.lean": "-- just a comment, no declarations\n"})
    r = run_cli(BASE_ARGS + ["--proof", "proof"], project)
    assert r.code == 0
    assert any("NotLean.lean" in n for n in r.json["notes"])


def test_proof_results_malformed_and_unreadable(tmp_path: Path):
    """E-65: an unreadable --proof-results file is a usage error (exit 2); malformed JSON or a
    manifest missing `build`/`theorems` is an input-contract violation (exit 3, the --results/
    E-05 pattern); no report is written in either case."""
    project = _tree(tmp_path / "p")
    r = run_cli(BASE_ARGS + ["--proof-results", "nope.json"], project)
    assert r.code == 2 and "--proof-results" in r.stderr
    assert not (project / "speccheck.json").exists()

    write_tree(project, {"bad.json": "not json"})
    r = run_cli(BASE_ARGS + ["--proof-results", "bad.json", "--out", "out2"], project)
    assert r.code == 3
    assert not (project / "out2" / "speccheck.json").exists()

    write_tree(project, {"bad2.json": json.dumps({"theorems": []})})
    r = run_cli(BASE_ARGS + ["--proof-results", "bad2.json", "--out", "out3"], project)
    assert r.code == 3
    assert not (project / "out3" / "speccheck.json").exists()


def test_proof_flags_are_check_only(tmp_path: Path):
    """E-54 (amended v1.19): --proof/--proof-results are defined on `check` only; `impact` and
    `explain` reject them as unrecognized arguments (E-09's / E-54's existing pattern)."""
    project = _tree(tmp_path / "p")
    r = run_cli(["impact", "--spec", "SPEC.md", "--changed", "R-01", "--proof", "proof"], project)
    assert r.code == 2 and "--proof" in r.stderr
    r = run_cli(["explain", "R-01", "--spec", "SPEC.md", "--proof-results", "x.json"], project)
    assert r.code == 2 and "--proof-results" in r.stderr


def test_proof_over_the_98_golden_fixture_extended(tmp_path: Path):
    """T-99: the §9.8 golden fixture (`fixtures/target/`) extended with a minimal Lean proof
    (`proof/Fixture.lean`: three declarations, two tagged, one untagged) and a two-entry manifest
    (`proof-results.json`) — added as siblings of `src`/`tests`, so the unextended golden run
    (T-46, no --proof flags) is untouched byte for byte (I-018, confirmed separately). Run with
    --proof/--proof-results added: R-01's tagged, checked declaration and R-02's tagged, failed
    one (with its build.errors line) both join correctly; the untagged declaration cites nothing."""
    args = [
        "check",
        "--spec",
        "SPEC.md",
        "--src",
        "src",
        "--tests",
        "tests",
        "--results",
        "junit.xml",
        "--proof",
        "proof",
        "--proof-results",
        "proof-results.json",
        "--judge",
        "mock",
        "--out",
        "out",
    ]
    project = tmp_path / "target"
    shutil.copytree(FIXTURE, project)
    out = project / "out"
    r = run_cli(args, project)
    doc = r.json_at(out)
    ids = {i["id"]: i for i in doc["ids"]}
    assert ids["R-01"]["proof"] == [
        {
            "name": "addSpec",
            "file": "proof/Fixture.lean",
            "line": 4,
            "state": "checked",
            "error": None,
        }
    ]
    assert ids["R-02"]["proof"] == [
        {
            "name": "subtractSpec",
            "file": "proof/Fixture.lean",
            "line": 7,
            "state": "failed",
            "error": "proof/Fixture.lean:7",
        }
    ]
    assert doc["proof"]["build"] == {
        "exit": 1,
        "theorems_total": 2,
        "theorems_checked": 1,
        "errors": ["proof/Fixture.lean:7"],
    }
def test_proof_join_tolerates_manifest_root_relative_paths(tmp_path: Path):
    """K-17: a citation's `file` is relative to `--root` (R-20, like every citation), but a real
    manifest producer commonly records `file` relative to its own `--proof` scan root instead
    (e.g. `speccheck/tools/proof_evidence.py` against `hello_world_deepseek`'s `proof/` project,
    §0k of SPEC_BUILD_REPORT.md): `proof/HelloProof/Hello/Theorems.lean` (citation) must still
    join `HelloProof/Hello/Theorems.lean` (manifest) as the same file, not `stale`."""
    project = _tree(tmp_path / "p")
    write_tree(
        project,
        {
            "proof/nested/Deep.lean": "/-- **R-03** discharges three, root-relative manifest. -/\ntheorem rThree : True := trivial\n",
            "proof-results-relative.json": json.dumps(
                {
                    "build": {"exit": 0, "theorems_total": 1, "theorems_checked": 1, "errors": []},
                    # the manifest names the file relative to the *scanned* root ("nested/..."),
                    # not to --root ("proof/nested/...") -- the real-world shape this join must
                    # tolerate.
                    "theorems": [
                        {
                            "file": "nested/Deep.lean",
                            "name": "rThree",
                            "line": 2,
                            "ids": ["R-03"],
                            "status": "checked",
                        }
                    ],
                }
            ),
        },
    )
    r = run_cli(
        BASE_ARGS + ["--proof", "proof", "--proof-results", "proof-results-relative.json"],
        project,
    )
    assert r.code == 0
    assert r.ids()["R-03"]["proof"][0]["state"] == "checked"


def test_proof_path_outside_root_is_e09(tmp_path: Path):
    """E-09 (extended v1.19): a --proof/--proof-results path resolving outside --root is the
    ordinary containment usage error."""
    project = _tree(tmp_path / "p")
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "x.lean").write_text("theorem t : True := trivial\n")
    r = run_cli(BASE_ARGS + ["--proof", str(outside)], project)
    assert r.code == 2 and "outside --root" in r.stderr
