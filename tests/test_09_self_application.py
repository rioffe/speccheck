"""§9.9 Self-application (recorded, not gating) and §9.10 / §9.11 script presence."""

from __future__ import annotations

import ast
import importlib.util
import json
import shutil
from pathlib import Path

from .conftest import run_cli

ROOT = Path(__file__).resolve().parent.parent


# SPEC.md v1.8 declares 190 ids (33 R, 11 C, 11 I, 14 K, 47 E, 74 T; none retired); bump with the spec
DECLARED_IDS = 190


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
