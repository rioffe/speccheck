"""§9.9 Self-application (recorded, not gating) and §9.10 / §9.11 script presence."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

from .conftest import run_cli

ROOT = Path(__file__).resolve().parent.parent


# SPEC.md v1.11 declares 200 ids (35 R, 11 C, 11 I, 15 K, 51 E, 77 T; none retired); bump with the spec
# SPEC.md v1.12 declares 203 ids (35 R, 11 C, 12 I, 15 K, 52 E, 78 T; none retired); v1.12 added
# E-52, I-012, T-78; bump with the spec
# SPEC.md v1.13 declares 215 ids (37 R, 13 C, 13 I, 15 K, 55 E, 82 T; none retired); v1.13 added
# new requirements/contracts/an invariant/edge cases/tests for spec-internal edges and the
# impact walk; its own decision table is not counted here — decisions are never in `ids`
# (D-25).  speccheck:ignore (this range notation is not a deliberate citation of every id)
# SPEC.md v1.14 declares 225 ids (38 R, 15 C, 14 I, 15 K, 56 E, 87 T; none retired); v1.14 added
# R-39, C-14..C-16, I-014, E-56 and T-85..T-88 for declared vs. incidental citations
# SPEC.md v1.15 declares 233 ids (38 R, 17 C, 15 I, 16 K, 58 E, 89 T; none retired); v1.15 added
# K-16, C-17, I-015, E-58, E-59 and T-89..T-91 for the Jev pre-triage pass
# SPEC.md v1.16 declares 237 ids (39 R, 17 C, 15 I, 16 K, 59 E, 91 T; none retired); v1.16 added
# R-38, E-57, T-83 and T-84 *(recorded)* for the obligation-aware judge (D-28/D-28b)
# SPEC.md v1.17 declares 245 ids (40 R, 18 C, 16 I, 16 K, 61 E, 94 T; none retired); v1.17 added
# R-40, C-18, I-016, E-60, E-61 and T-92..T-94 for the `explain` subcommand (D-33..D-36)
# SPEC.md v1.18 declares 252 ids (41 R, 19 C, 17 I, 16 K, 61 E, 98 T; none retired); v1.18 added
# R-41, C-19, I-017 and T-95..T-98 for the CLI help contract (D-37..D-42)
DECLARED_IDS = 252


def test_self_application_runs_on_this_repository(tmp_path: Path):
    """T-48: `speccheck check --spec SPEC.md --src src --tests tests --results <this suite's
    junit.xml> --judge mock` on this repository reports every R/C/I/K/E/T ID in SPEC.md; the
    all-PASSING result is recorded in SPEC_BUILD_REPORT.md, not asserted here (it needs the
    junit.xml of the run that is executing this test). (R-24)"""
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(ROOT / "SPEC.md", repo / "SPEC.md")
    shutil.copytree(ROOT / "src", repo / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "tests", repo / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    argv = [
        "check",
        "--spec",
        "SPEC.md",
        "--src",
        "src",
        "--tests",
        "tests",
        "--judge",
        "mock",
        "--out",
        "out",
    ]
    if (ROOT / "junit.xml").is_file():
        shutil.copy(ROOT / "junit.xml", repo / "junit.xml")
        argv += ["--results", "junit.xml"]
    run = run_cli(argv, repo)
    assert run.code in (0, 1), run.stderr
    doc = run.json_at(repo / "out")
    ids = {r["id"] for r in doc["ids"]}
    assert {
        "R-01",
        "R-29",
        "C-01",
        "C-10",
        "I-001",
        "I-011",
        "K-01",
        "K-12",
        "E-01",
        "E-38",
        "T-01",
        "T-61",
    } <= ids
    assert doc["metrics"]["declared"] == DECLARED_IDS and doc["metrics"]["retired"] == 0
    statuses = {r["id"]: r["status"] for r in doc["ids"]}
    # every ID is at least cited by a test in this suite (the outcome depends on junit.xml)
    assert all(s not in ("UNCITED", "UNTESTED") for s in statuses.values()), sorted(
        i for i, s in statuses.items() if s in ("UNCITED", "UNTESTED")
    )
    (tmp_path / "self_application.json").write_text(json.dumps(doc["metrics"]))


def test_benchmark_script_exists_and_golden_bound_holds():
    """T-51: tools/bench.py (not collected by pytest) exists, parses, and exposes the K-08
    benchmark entry points; the golden-fixture half of K-08 — `check --judge mock` on the
    fixture in <= 2 s wall-clock — is asserted here by running that benchmark once; the
    10,000-file median is recorded in SPEC_BUILD_REPORT.md, not asserted. (K-08)"""
    source = (ROOT / "tools" / "bench.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert {"bench_golden", "bench_generated", "main"} <= names
    assert "K-08" in source and "10000" in source or "10_000" in source
    spec = importlib.util.spec_from_file_location("speccheck_bench", ROOT / "tools" / "bench.py")
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)
    golden_seconds = bench.bench_golden(runs=1)
    assert 0.0 <= golden_seconds <= 2.0, golden_seconds  # K-08 golden-fixture bound


def test_llm_eval_labels_cover_every_judged_edge():
    """T-49: the hand labels for the golden fixture's judged edges cover exactly the edges the
    kernel judges, with values from {ASSERTS, EXECUTES_ONLY, UNRELATED}; tools/eval_judge.py runs
    the three independent LLM passes against Ollama and records accuracy and unknown_rate per run
    (opt-in, not run in CI). (R-10, R-26)"""
    labels = json.loads(
        (ROOT / "fixtures" / "target" / "golden" / "judge_labels.json").read_text(encoding="utf-8")
    )
    golden = json.loads(
        (ROOT / "fixtures" / "target" / "golden" / "speccheck.json").read_text(encoding="utf-8")
    )
    judged = {
        f"{rec['id']} {t['file']}::{t['name']}"
        for rec in golden["ids"]
        for t in rec["tests"]
        if t["verdict"] is not None
    }
    assert set(labels) == judged and judged
    assert set(labels.values()) <= {"ASSERTS", "EXECUTES_ONLY", "UNRELATED"}
    assert (ROOT / "tools" / "eval_judge.py").is_file()
    assert shutil.which("python3") is not None


def test_obligation_census_script_and_labels_are_well_formed():
    """PROPOSAL_obligation_census.md: tools/census.py exists, parses, and exposes both CLI modes
    (a fresh run, and --ratify over a hand-edited census.json); tools/census_prompt.md is
    non-empty; tools/census_labels.json's ten seed labels each name a live R/C/I/K/E id of this
    project's own SPEC.md with a valid form/checker (opt-in, no network here, not run in CI)."""
    source = (ROOT / "tools" / "census.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert {
        "main",
        "do_run",
        "do_ratify",
        "load_subjects",
        "recommend",
        "consensus_value",
        "score_against_labels",
        "render_census_md",
    } <= names
    assert (ROOT / "tools" / "census_prompt.md").stat().st_size > 0

    labels = json.loads(
        (ROOT / "tools" / "census_labels.json").read_text(encoding="utf-8")
    )
    assert len(labels) == 10
    for label in labels.values():
        assert label["form"] in {"expr", "struct", "behavior", "prose"}
        assert label["checker"] in {"ast", "schema", "test", "llm"}
        assert isinstance(label["scope_stated"], bool)

    from speccheck.extract import parse_spec

    index = parse_spec((ROOT / "SPEC.md").read_text(encoding="utf-8"), "SPEC.md")
    live = {s.id for s in index.ids if not s.retired and s.family in {"R", "C", "I", "K", "E"}}
    assert set(labels) <= live, sorted(set(labels) - live)


def test_t91_recorded_calibration_is_measured_and_recorded():
    """T-91 (recorded): the §1 calibration measurement of `PROPOSAL_v1.16_jev_pre_triage.md` was
    re-run against this repository's own `SPEC.md`/`src`/`tests` and its bucket table is recorded
    in `SPEC_BUILD_REPORT.md` with the C-17 model name, the date and `judge_prompt_sha256`; the
    run itself is the recorded evidence (non-gating, like T-49 and T-87) — this check proves only
    that the artefact exists and has the shape the row pins. (K-16, C-17, D-32)"""
    report = (ROOT / "SPEC_BUILD_REPORT.md").read_text(encoding="utf-8")
    marker = "T-91 *(recorded)*"
    assert marker in report, "SPEC_BUILD_REPORT.md does not record T-91"
    body = report.split(marker, 1)[1].split("\n## ", 1)[0]
    rows = [
        line
        for line in body.splitlines()
        if line.startswith("|") and "%" in line and "---" not in line
    ]
    assert len(rows) >= 3, rows
    assert "judge_prompt_sha256" in body
    assert "SPECCHECK_JEV_MODEL" in body or "~typesafe/jev-latest" in body
    assert "p(e)" in body or "confidence" in body


def test_t87_recorded_rerun_is_measured_and_recorded():
    """T-87 (recorded): the three real edges named in `PROPOSAL_v1.15_declared_vs_incidental_
    citations.md`'s evidence were re-run under the v1.14 C-10 text with the same model, and the
    three verdicts plus `judge_prompt_sha256` are recorded in `SPEC_BUILD_REPORT.md`; the shipped
    C-10 text carries the skepticism rule. Non-gating (a live model's compliance with an advisory
    instruction). (C-10, C-15, R-39)"""
    report = (ROOT / "SPEC_BUILD_REPORT.md").read_text(encoding="utf-8")
    assert "T-87" in report
    assert "f6b124bdd6ea5948d052f6cb45de85eb5409e0165ba2371cd784a313472bcfd1" in report
    for edge in (
        "test_fenced_code_blocks_are_ignored",
        "test_row_and_heading_grammar_edge_cases",
        "test_judge_called_once_per_eligible_edge_only",
    ):
        assert edge in report
    shipped = (ROOT / "src" / "speccheck" / "judge_prompt.md").read_text(encoding="utf-8")
    assert "When declared is false" in shipped


def test_t84_recorded_adjacent_subset_is_measured_and_recorded():
    """T-84 *(recorded)*: the golden fixture's adjacent subset — the judged edges that cite an id
    but assert only a fact about an id that id's statement names — was measured under the shipped
    v1.16 C-10 text and under the pre-v1.16 text, and both arms are recorded in
    `SPEC_BUILD_REPORT.md` with the model, the date, each text's `judge_prompt_sha256` and the
    per-run downgrade count; the run itself is the recorded evidence (non-gating, like T-49 and
    T-91) — this check proves only that the artefact exists with the shape the row pins. (R-38,
    C-10, D-28, T-76)"""
    report = (ROOT / "SPEC_BUILD_REPORT.md").read_text(encoding="utf-8")
    marker = "T-84 *(recorded)*"
    assert marker in report, "SPEC_BUILD_REPORT.md does not record T-84"
    body = report.split(marker, 1)[1].split("\n## ", 1)[0]
    assert "google/gemini-3.8-flash" in body
    assert "judge_prompt_sha256" in body
    shipped = hashlib.sha256(
        (ROOT / "src" / "speccheck" / "judge_prompt.md").read_bytes()
    ).hexdigest()
    assert shipped in body, "the v1.16 arm's prompt digest is not recorded"
    assert "f6b124bdd6ea5948d052f6cb45de85eb5409e0165ba2371cd784a313472bcfd1" in body, (
        "the pre-v1.16 arm's prompt digest is not recorded"
    )
    for edge in (
        "test_add_rounding_fact",
        "test_subtract_rounding_fact",
        "test_scale_empty_input_is_not_mutated",
        "test_add_rounding_of_a_half_cent",
        "test_add_commutes_on_plain_sum",
        "test_add_commutes_rounding_fact",
        "test_summary_total_rounding_fact",
        "test_summary_mean_rounding_fact",
    ):
        assert edge in body, edge
    rows = [
        ln
        for ln in body.splitlines()
        if ln.startswith(("| v1.16 shipped", "| pre-v1.16")) and "/8" in ln
    ]
    assert len(rows) >= 6, rows  # three runs per prompt text
    assert (ROOT / "tools" / "adjacent_eval.py").is_file()


def test_t94_recorded_explain_trace_is_measured_and_recorded():
    """T-94 *(recorded)*: the live-LLM arm of the C-18 trace was run and recorded — `explain R-01`
    under `--judge llm` renders the C-06 verdict with its `clause:` and `rationale:` lines, the same
    id under `--judge none` renders `not judged`, and the status shown equals the one
    `speccheck.json` records from the same inputs; the run itself is the recorded evidence
    (non-gating, like T-49 and T-84) — this check proves only that the artefact exists with the
    shape the row pins. (R-40, C-18, E-61)"""
    report = (ROOT / "SPEC_BUILD_REPORT.md").read_text(encoding="utf-8")
    marker = "T-94 *(recorded)*"
    assert marker in report, "SPEC_BUILD_REPORT.md does not record T-94"
    body = report.split(marker, 1)[1].split("\n## ", 1)[0]
    assert "explain R-01" in body
    assert "google/gemini-3.8-flash" in body
    assert "judge_prompt_sha256" in body
    shipped = hashlib.sha256(
        (ROOT / "src" / "speccheck" / "judge_prompt.md").read_bytes()
    ).hexdigest()
    assert shipped in body, "the C-10 digest the live run recorded is not in the record"
    assert "clause:" in body and "rationale:" in body  # the judged form
    assert "not judged" in body  # the `--judge none` form
    assert (ROOT / "tests" / "test_12_explain.py").is_file()


def test_prose_artifacts_claim_the_shipped_version():
    """F-3 (2026-09-21): the version claims in the prose artifacts track the shipped version — the
    README's introduction and SPEC_BUILD_REPORT.md's title name the spec version `SPEC.md`'s status
    line declares and the package version `__version__` reports. No spec row covers this prose, so
    the guard is here: the claim drifted for three increments (v1.16, v1.17, v1.18) before the
    requester read it."""
    import re

    from speccheck import __version__

    spec_version = re.search(
        r"\*\*Status:\*\* v(\d+\.\d+)", (ROOT / "SPEC.md").read_text(encoding="utf-8")
    )
    assert spec_version, "SPEC.md has no status version"
    expected = f"v{spec_version.group(1)}"
    assert __version__.startswith(spec_version.group(1)), (__version__, expected)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # the claim is checked on collapsed whitespace: the sentence wraps in the source
    assert (
        f"implements its own `SPEC.md` ({expected}, code {__version__})"
        in " ".join(readme.split())
    )
    report = (ROOT / "SPEC_BUILD_REPORT.md").read_text(encoding="utf-8")
    assert report.startswith(f"# SPEC_BUILD_REPORT — `speccheck` v{__version__} against `SPEC.md` ({expected})")
