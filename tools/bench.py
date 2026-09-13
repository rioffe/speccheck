"""K-08 / T-51 benchmark (recorded, not CI-gated; not collected by pytest).

Runs `check --judge mock` five times on the golden fixture and five times on a generated
10,000-file tree with 100 declared IDs, and prints the median wall-clock of each. Record the
medians and the machine description in SPEC_BUILD_REPORT.md.

Usage: uv run python tools/bench.py [--files 10000] [--ids 100] [--runs 5]
"""

from __future__ import annotations

import argparse
import io
import os
import platform
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

from speccheck.cli import run_check

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "target"
ARGS = [
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
    "mock",
    "--strict",
]


def _timed(argv: list[str], cwd: Path) -> float:
    old = os.getcwd()
    os.chdir(cwd)
    try:
        t0 = time.perf_counter()
        run_check(argv + ["--out", "bench-out"], {}, io.StringIO())
        return time.perf_counter() - t0
    finally:
        os.chdir(old)


def bench_golden(runs: int) -> float:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "target"
        shutil.copytree(FIXTURE, target)
        return statistics.median(_timed(ARGS, target) for _ in range(runs))


def generate_tree(base: Path, files: int, ids: int) -> None:
    rows = ["| ID | Statement |", "| -- | --------- |"]
    families = "RCIKET"
    for i in range(ids):
        rows.append(f"| **{families[i % 6]}-{i // 6 + 1:02d}** | requirement {i} |")
    (base / "SPEC.md").write_text("# Generated\n\n" + "\n".join(rows) + "\n", encoding="utf-8")
    src = base / "src"
    tests = base / "tests"
    src.mkdir()
    tests.mkdir()
    n_src = files // 2
    n_tests = files - n_src
    for i in range(n_src):
        d = src / f"pkg{i % 50}"
        d.mkdir(exist_ok=True)
        ident = f"{families[i % 6]}-{(i % ids) // 6 + 1:02d}"
        (d / f"mod{i}.py").write_text(
            f'"""Module {i} realizes {ident}."""\n\n\ndef f{i}(x):\n    # {ident}\n    return x + {i}\n',
            encoding="utf-8",
        )
    cases = []
    for i in range(n_tests):
        d = tests / f"grp{i % 50}"
        d.mkdir(exist_ok=True)
        ident = f"{families[i % 6]}-{(i % ids) // 6 + 1:02d}"
        (d / f"test_mod{i}.py").write_text(
            f"def test_f{i}():\n    '''{ident}'''\n    assert {i} == {i}\n", encoding="utf-8"
        )
        cases.append(f'<testcase classname="tests.grp{i % 50}.test_mod{i}" name="test_f{i}" />')
    (base / "junit.xml").write_text(
        "<testsuites><testsuite>" + "".join(cases) + "</testsuite></testsuites>", encoding="utf-8"
    )


def bench_generated(runs: int, files: int, ids: int) -> float:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "gen"
        base.mkdir()
        generate_tree(base, files, ids)
        return statistics.median(_timed(ARGS, base) for _ in range(runs))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=10000)
    parser.add_argument("--ids", type=int, default=100)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args(argv)
    print(f"machine: {platform.platform()} {platform.machine()} python={platform.python_version()}")
    golden = bench_golden(args.runs)
    print(
        f"golden fixture: median {golden:.3f} s over {args.runs} runs (K-08 bound 2 s: {'PASS' if golden <= 2 else 'FAIL'})"
    )
    generated = bench_generated(args.runs, args.files, args.ids)
    print(
        f"generated {args.files} files / {args.ids} IDs: median {generated:.3f} s over {args.runs} runs (K-08 bound 60 s: {'PASS' if generated <= 60 else 'FAIL'})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
