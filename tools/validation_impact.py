"""The *Validation impact* section of a release's notes (D-71, v1.26).

Joins `speccheck impact --against <the prior release's SPEC.md>` — the ids whose declarations
changed — with the CONTROLS markers of this SPEC.md (the per-id `controls` the self-application
run reports), and lists every tool hazard whose controls changed; then lists every OQ case whose
packaged fixture, goldens or catalog entry changed since that release; then the package tree hash
of this tree (R-112), the value the release notes publish.

Usage: uv run python tools/validation_impact.py <prior release tag, e.g. v1.25.0>

Needs `git` (like tools/impact_backtest.py). Writes Markdown to stdout; changes nothing.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from speccheck import cli
from speccheck.extract import parse_spec
from speccheck.qualify import tree_of_directory

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "speccheck"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def changed_ids(prior: str) -> list[str]:
    """`impact --against` the prior release's SPEC.md: the C-13 changed set."""
    with tempfile.TemporaryDirectory() as tmp:
        old = Path(tmp) / "SPEC.prior.md"
        old.write_text(_git("show", f"{prior}:SPEC.md"), encoding="utf-8")
        out = Path(tmp) / "out"
        with contextlib.redirect_stdout(io.StringIO()):  # impact's own summary line
            code = cli.main(
                [
                    "impact",
                    "--spec",
                    str(ROOT / "SPEC.md"),
                    "--against",
                    str(old),
                    "--root",
                    "/",
                    "--out",
                    str(out),
                ],
                environ={},
            )
        if code != 0:
            raise SystemExit(f"impact --against {prior} exited {code}")
        doc = json.loads((out / "impact.json").read_text(encoding="utf-8"))
    return [c if isinstance(c, str) else c["id"] for c in doc["changed"]]


def hazard_rows(changed: list[str]) -> list[tuple[str, str, list[str]]]:
    """Each tool hazard whose CONTROLS-marked ids include a changed id."""
    index = parse_spec((ROOT / "SPEC.md").read_text(encoding="utf-8"), "SPEC.md")
    risk = json.loads((PKG / "_qualify" / "tool_risk.json").read_text(encoding="utf-8"))
    rows = []
    for hazard in risk["hazards"]:
        controls = [s.id for s in index.ids if hazard["id"] in s.controls]
        hit = [c for c in controls if c in changed]
        if hit:
            rows.append((hazard["id"], hazard["title"], hit))
    return rows


def case_rows(prior: str) -> list[tuple[str, list[str]]]:
    """Each OQ case whose fixture directory, goldens or catalog changed since `prior`."""
    files = _git(
        "diff", "--name-only", prior, "--", "src/speccheck/_qualify", "src/speccheck/_selfcheck"
    ).split()
    cases = json.loads((PKG / "_qualify" / "cases.json").read_text(encoding="utf-8"))["cases"]
    rows = []
    for case in cases:
        prefix = f"src/speccheck/{case['fixture']}/"
        hit = [f for f in files if f.startswith(prefix)]
        if "src/speccheck/_qualify/cases.json" in files:
            hit.append("src/speccheck/_qualify/cases.json")
        if hit:
            rows.append((case["id"], hit))
    return rows


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.strip().split("\n\n")[2], file=sys.stderr)
        return 2
    prior = argv[0]
    changed = changed_ids(prior)
    tree, files = tree_of_directory(PKG)
    out = [f"## Validation impact (since {prior})", ""]
    out += [f"Package tree SHA-256 of this release: `{tree}` ({files} files).", ""]
    out += [f"Spec ids changed since {prior}: {len(changed)}.", ""]
    hazards = hazard_rows(changed)
    out += ["Tool hazards whose controls changed:", ""]
    if hazards:
        out += ["| Hazard | Title | Changed controls |", "| --- | --- | --- |"]
        out += [f"| {h} | {t} | {', '.join(c)} |" for h, t, c in hazards]
    else:
        out.append("None.")
    out += ["", "Operational-qualification cases whose fixture, goldens or catalog changed:", ""]
    cases = case_rows(prior)
    if cases:
        out += ["| Case | Changed files |", "| --- | --- |"]
        out += [f"| {c} | {', '.join(f'`{x}`' for x in fs)} |" for c, fs in cases]
    else:
        out.append("None.")
    out += ["", "Re-run `speccheck qualify` after upgrading, whatever this section lists.", ""]
    sys.stdout.write("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
