"""D-24 / T-82: change-impact backtest.

Compares what `speccheck impact --against` *predicts* for a spec change with what a build range
of this repository's own history *actually touched*, over the two ranges named in SPEC.md's T-82
row. Needs `git` and this repository's history (both ends of every range must be reachable
commits); not collected by pytest.

Usage:
  uv run python tools/impact_backtest.py [--help]

With no arguments it runs the two default ranges and writes
build/impact_backtest/<spec-to>.md plus a summary to stdout, per range:

  d  predicted  recall  precision
  1  ...        ...     ...
  2  ...
  3  ...
  inf ...

then the miss list (ids the build touched that `impact` never predicted, at any depth) and,
at the chosen depth, the excess list (predicted, untouched).

The kernel itself never shells out to git (D-24); this script does, and lives outside it.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from speccheck import cli as speccheck_cli  # noqa: E402

DEPTHS = (1, 2, 3, None)  # None = unbounded ("inf")

DEFAULT_RANGES = [
    {
        "name": "v1.6->v1.8",
        "spec_from": "d170433^",
        "spec_to": "c0a770a",
        "build_from": "2a25569",
        "build_to": "2635298",
    },
    {
        "name": "v1.8->v1.11",
        "spec_from": "2635298",
        "spec_to": "c1e3d87",
        "build_from": "330dd4e",
        "build_to": "dfea1a6",
    },
]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def _git_show(rev: str, path: str) -> str:
    return _git("show", f"{rev}:{path}")


def _checkout_tree(rev: str, dest: Path) -> None:
    """Materialize the tree at `rev` under `dest` via `git archive` (read-only; no worktree)."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "archive", rev], cwd=ROOT, capture_output=True, check=True
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")  # noqa: S202 - our own repository's history


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _touched_new_lines(diff_text: str) -> dict[str, set[int]]:
    """file (b/ prefix stripped) -> set of new-file line numbers touched by any hunk."""
    touched: dict[str, set[int]] = {}
    current: str | None = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            path = line[4:]
            current = None if path == "/dev/null" else path[2:]  # strip "b/"
            continue
        if current is None:
            continue
        m = _HUNK_RE.match(line)
        if m:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            if count == 0:
                continue  # pure deletion: no new-file lines to mark
            touched.setdefault(current, set()).update(range(start, start + count))
    return touched


def _run_in(tree: Path, argv: list[str]) -> int:
    """speccheck resolves relative paths against the process cwd, not --root; chdir there."""
    cwd = os.getcwd()
    os.chdir(tree)
    try:
        return speccheck_cli.main(argv, environ={})
    finally:
        os.chdir(cwd)


def _run_impact(tree: Path, spec_to_name: str, against_name: str) -> dict:
    out = tree / "_impact_out"
    argv = [
        "impact",
        "--spec",
        spec_to_name,
        "--against",
        against_name,
        "--depth",
        "0",
        "--src",
        "src",
        "--tests",
        "tests",
        "--root",
        ".",
        "--out",
        str(out),
    ]
    code = _run_in(tree, argv)
    if code != 0:
        raise RuntimeError(f"speccheck impact exited {code}")
    return json.loads((out / "impact.json").read_text(encoding="utf-8"))


def _run_check(tree: Path) -> dict:
    out = tree / "_check_out"
    argv = [
        "check",
        "--spec",
        "SPEC.md",
        "--src",
        "src",
        "--tests",
        "tests",
        "--judge",
        "none",
        "--root",
        ".",
        "--out",
        str(out),
    ]
    _run_in(tree, argv)
    return json.loads((out / "speccheck.json").read_text(encoding="utf-8"))


@dataclass
class RangeResult:
    name: str
    depths: dict[str, tuple[int, float | None, float | None]]  # label -> (predicted, recall, precision)
    misses: list[tuple[str, str, int]]
    excess: list[str]
    chosen_depth: int


def run_range(rng: dict) -> RangeResult:
    with tempfile.TemporaryDirectory(prefix="speccheck-backtest-") as tmp:
        tree = Path(tmp)
        _checkout_tree(rng["build_to"], tree)

        old_spec = _git_show(rng["spec_from"], "SPEC.md")
        new_spec = _git_show(rng["spec_to"], "SPEC.md")
        (tree / "SPEC.md").write_text(new_spec, encoding="utf-8")
        (tree / "OLD_SPEC.md").write_text(old_spec, encoding="utf-8")

        impact_doc = _run_impact(tree, "SPEC.md", "OLD_SPEC.md")
        check_doc = _run_check(tree)

        changed_ids = {c["id"] for c in impact_doc["changed"]}
        depth_of: dict[str, int] = {e["id"]: e["depth"] for e in impact_doc["impact"]}

        diff_text = _git(
            "diff", f"{rng['build_from']}^", rng["build_to"], "-U0", "--", "src", "tests"
        )
        touched = _touched_new_lines(diff_text)

        # citations of every id from the built tree, restricted to src/tests paths
        cites: dict[str, list[tuple[str, int]]] = {}
        for rec in check_doc["ids"]:
            locs = [(s["file"], ln) for s in rec["src"] for ln in s["lines"]]
            for t in rec["tests"]:
                locs += [(t["file"], ln) for ln in t["lines"]]
            if locs:
                cites[rec["id"]] = locs

        actually_affected: dict[str, tuple[str, int]] = {}
        for ident, locs in cites.items():
            if ident in changed_ids:
                continue
            for file, line in locs:
                if line in touched.get(file, ()):
                    actually_affected[ident] = (file, line)
                    break

        labels = {1: "1", 2: "2", 3: "3", None: "inf"}
        depths_out: dict[str, tuple[int, float | None, float | None]] = {}
        for d in DEPTHS:
            predicted = {i for i, dd in depth_of.items() if d is None or dd <= d}
            hit = predicted & set(actually_affected)
            recall = len(hit) / len(actually_affected) if actually_affected else None
            precision = len(hit) / len(predicted) if predicted else None
            depths_out[labels[d]] = (len(predicted), recall, precision)

        # recall by the numbers above: prefer the smallest depth with recall >= 0.80, else "inf"
        chosen = 1
        for d in (1, 2, 3):
            r = depths_out[str(d)][1]
            if r is not None and r >= 0.80:
                chosen = d
                break
        else:
            chosen = 0  # unbounded

        predicted_at_chosen = {
            i for i, dd in depth_of.items() if chosen == 0 or dd <= chosen
        }
        misses = sorted(
            (i, *loc) for i, loc in actually_affected.items() if i not in depth_of
        )
        excess = sorted(predicted_at_chosen - set(actually_affected))

        return RangeResult(
            name=rng["name"],
            depths=depths_out,
            misses=misses,
            excess=excess,
            chosen_depth=chosen,
        )


def render_report(results: list[RangeResult]) -> str:
    lines = ["# Impact backtest (D-24, T-82)", ""]
    for r in results:
        lines.append(f"## {r.name}")
        lines.append("")
        lines.append("| d | predicted | recall | precision |")
        lines.append("| - | --------- | ------ | --------- |")
        for label in ("1", "2", "3", "inf"):
            n, recall, precision = r.depths[label]
            rt = "n/a" if recall is None else f"{recall:.2f}"
            pt = "n/a" if precision is None else f"{precision:.2f}"
            lines.append(f"| {label} | {n} | {rt} | {pt} |")
        lines.append("")
        lines.append(f"Chosen depth: {r.chosen_depth or 'unbounded'}")
        lines.append("")
        lines.append("Misses (touched, never predicted):")
        if r.misses:
            for ident, file, line in r.misses:
                lines.append(f"- {ident}: {file}:{line}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append(f"Excess at chosen depth (predicted, untouched): {len(r.excess)}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        _git("rev-parse", "--is-inside-work-tree")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("impact_backtest: git is not available or this is not a git checkout")
        return 1
    results = []
    for rng in DEFAULT_RANGES:
        try:
            results.append(run_range(rng))
        except subprocess.CalledProcessError as exc:
            print(f"impact_backtest: {rng['name']}: git command failed: {exc}")
            return 1
    report = render_report(results)
    print(report)
    out_dir = ROOT / "build" / "impact_backtest"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{DEFAULT_RANGES[-1]['spec_to']}.md").write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
