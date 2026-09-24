#!/usr/bin/env python3
"""Proof-evidence sidecar: relate source, tests, test results, proof, and
proof results per spec ID — for *any* project laid out the way `spec-proof`
scaffolds one (a `proof/` lake project beside a `SPEC.md` and an empirical test suite —
pytest by default, or any runner that emits JUnit XML via `--test-cmd`).

This is the five-way provenance layer that the (not-yet-extended) speccheck
tool will eventually consume natively (see `docs/proposals/PROPOSAL_v1.19_proof_parameter.md`
for the `--proof`/`--proof-results` pair). Until then, run it against a project root and it
writes, under `<out>/` (default `<root>/build/proof`):

    proof-results.json   machine-readable manifest (the shape C-21 drafts)
    PROOF_EVIDENCE.md     per-ID evidence table
    junit.xml             fresh test results (unless --skip-pytest)

It READS the target project's Lean proof project (default `<root>/proof`), runs the proof
build there, re-runs its test suite, and joins everything on spec IDs read from its
`SPEC.md`. It never modifies the project it reads.

Exit code: 0 iff the Lean build is green AND the test suite is green (or --skip-pytest and any
reused junit.xml has no failures). If the test launcher fails before writing JUnit XML at all
(wrong command, missing dependency, …), that is reported as 0/0 with a warning on stderr, not
silently as a vacuous pass — check the warning, not just the "N/M passed" count, when it reads 0/0.

Usage
-----
    python3 tools/proof_evidence.py --root .                          # this project
    python3 tools/proof_evidence.py --root ../other-project           # a sibling project
    python3 tools/proof_evidence.py --root ../other-project --proof formal --spec spec/SPEC.md
    # a project with no pytest (its own JUnit-emitting runner):
    python3 tools/proof_evidence.py --root ../other-project --test-cmd \
        'python3 tools/run_suite.py --xml {junit}'

Generalized from a hello_world_deepseek-specific script: no project name, source filename,
or Lean file list is hardcoded. Lean sources are discovered by recursively scanning `--proof`
for `*.lean` (skipping `.lake/`); the "deferred to pytest" table is read from markdown-table
rows (`| ID | ... |`, whether inside a `--` line comment or a `/- ... -/` block comment) found
anywhere in those files, not from one named file — different proof projects format that table
with a different column count, so only the leading `T-\\d+` tokens in the trailing cells are
trusted as the `tests` list.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Bold spans in the proof sources are spec-ID tags, e.g. `**C-02**`,
# `**R-11, I-003**`, or mixed lists like `**E-08, D-17, R-03, R-11**`.
# Every RCIKE ID inside a bold span is collected; D/T tokens and `(a)`-style
# sub-case markers are dropped (a row discharges its own ID).
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ID_IN = re.compile(r"\b([RCIKE]-\d+)(?:\s*\([^)]*\))?")
DECL = re.compile(
    r"^\s*(?:public\s+|protected\s+)*(?:theorem|lemma|def|abbrev|instance)\s+([A-Za-z_][A-Za-z0-9']*)")
DOC_OPEN = re.compile(r"^\s*/--")          # doc comments (section headers use /-!)
DOC_CLOSE = re.compile(r"-/\s*$")
ERROR = re.compile(r"^error: (\S+):(\d+):")
SPEC_ID = re.compile(r"\b([RCIKE]-\d+|T-\d+)\b")
SPEC_VERSION = re.compile(r"\*\*Status:\*\*\s*v?([0-9]+(?:\.[0-9]+)*)")
# A deferral/exclusion table row: a markdown table row — inside a `--` line comment or a
# `/- ... -/` block comment, either way with no code before it on the line — whose first cell
# is a spec ID (optionally annotated with a parenthesized scope), and one or more trailing cells.
DEFER_ROW = re.compile(r"^\s*(?:--\s*)?\|\s*([RCIKE]-\d+)\s*(?:\(([^)]*)\))?\s*\|(.+)\|\s*$")
TEST_REF = re.compile(r"T-\d+")


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, env=env or os.environ.copy(),
                        capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def env_with_lean_toolchain() -> dict[str, str]:
    """`PATH` plus elan's bin dir, in case `lake` isn't already on it."""
    env = os.environ.copy()
    elan = os.path.expanduser("~/.elan/bin")
    if shutil.which("lake") is None and os.path.isdir(elan):
        env["PATH"] = f"{elan}:{env.get('PATH', '')}"
    return env


def default_pytest_cmd(root: Path) -> list[str]:
    """`uv run python -m pytest` if the project uses uv, else its `.venv`, else this interpreter."""
    if shutil.which("uv") and (root / "pyproject.toml").exists():
        return ["uv", "run", "python", "-m", "pytest"]
    venv_py = root / ".venv" / "bin" / "python"
    if venv_py.exists():
        return [str(venv_py), "-m", "pytest"]
    return [sys.executable, "-m", "pytest"]


def spec_ids(spec_path: Path) -> list[str]:
    """Every R/C/I/K/E spec ID in the spec, in document order, de-duplicated."""
    seen: dict[str, None] = {}
    for m in SPEC_ID.finditer(spec_path.read_text("utf-8")):
        seen.setdefault(m.group(1))
    return [i for i in seen if not i.startswith("T-")]


def spec_version(spec_path: Path) -> str | None:
    m = SPEC_VERSION.search(spec_path.read_text("utf-8")[:4000])
    return m.group(1) if m else None


def discover_lean_files(proof_root: Path) -> list[Path]:
    """Every `*.lean` file under `proof_root`, relative paths, `.lake/` build output excluded."""
    return sorted(
        p.relative_to(proof_root)
        for p in proof_root.rglob("*.lean")
        if ".lake" not in p.parts
    )


def _tags(body: list[str]) -> list[str]:
    tags = []
    for line in body:
        for span in BOLD.findall(line):
            tags.extend(ID_IN.findall(span))
    return tags


def doc_blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    """(1-indexed end line, body lines) of every doc comment block."""
    blocks = []
    i = 0
    while i < len(lines):
        if DOC_OPEN.match(lines[i]):
            start = i
            if DOC_CLOSE.search(lines[i]) and lines[i].strip() != "/--":
                blocks.append((start + 1, [lines[i]]))
                i += 1
                continue
            j = i + 1
            while j < len(lines) and not DOC_CLOSE.search(lines[j]):
                j += 1
            blocks.append((j + 1, lines[start:j + 1]))
            i = j + 1
            continue
        i += 1
    return blocks


def parse_lean(text: str, rel: str, err_lines: set[tuple[str, int]]) -> list[dict]:
    """Declarations with their doc-comment spec-ID tags and check status."""
    lines = text.splitlines()
    blocks = doc_blocks(lines)
    out: list[dict] = []
    for k, line in enumerate(lines, 1):
        m = DECL.match(line)
        if not m:
            continue
        # The declaration's doc comment: the nearest block ending directly
        # above it (at most one blank line between).
        tags: list[str] = []
        for end, body in blocks:
            if 0 < k - end <= 2:
                tags = _tags(body)
        ok = (rel, k) not in err_lines
        out.append({
            "file": rel, "name": m.group(1), "line": k,
            "ids": sorted(set(tags), key=lambda s: (s[0], int(s[2:]))),
            "status": "checked" if ok else "failed",
        })
    return out


def parse_deferrals(rel: str, text: str) -> list[dict]:
    """Deferred/excluded-from-Lean spec rows: markdown table rows tagged by a leading spec ID.

    Column count, labeling, and comment style vary by project (a three-cell `id | why | tests`
    row inside a block comment, a two-cell `-- | id | tests` line-comment row, …); only the
    `T-\\d+` tokens anywhere in the trailing cells are trusted, so this is robust to that
    variation at the cost of not knowing which cell was "the test".
    """
    out = []
    for line in text.splitlines():
        m = DEFER_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(3).split("|")]
        content = cells[0] if len(cells) > 1 else None
        tail = " ".join(cells[1:]) if len(cells) > 1 else cells[0]
        out.append({
            "id": m.group(1),
            "scope": (m.group(2) or "").strip() or None,
            "content": content,
            "tests": sorted(set(TEST_REF.findall(tail)), key=lambda s: int(s[2:])),
            "file": rel,
        })
    return out


def parse_junit(path: Path) -> dict:
    root = ET.parse(path).getroot()
    cases = []
    for tc in root.iter("testcase"):
        failed = tc.find("failure") is not None or tc.find("error") is not None
        skipped = tc.find("skipped") is not None
        cases.append({"name": f'{tc.get("classname")}.{tc.get("name")}',
                      "status": "failed" if failed else "skipped" if skipped else "passed"})
    return {"total": len(cases), "failed": [c["name"] for c in cases if c["status"] == "failed"],
            "cases": cases}


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", type=Path, default=Path("."),
                   help="project root to evaluate (default: .)")
    p.add_argument("--proof", type=Path, default=Path("proof"),
                   help="Lean proof project dir, relative to --root (default: proof)")
    p.add_argument("--spec", type=Path, default=Path("SPEC.md"),
                   help="spec file, relative to --root (default: SPEC.md)")
    p.add_argument("--out", type=Path, default=None,
                   help="output dir, relative to --root (default: build/proof)")
    p.add_argument("--source", default=None,
                   help="free-text label recorded in the manifest's 'source' field (default: omitted)")
    p.add_argument("--pytest-cmd", default=None,
                   help="override the pytest launcher, e.g. '.venv/bin/python -m pytest' "
                        "(default: auto-detected from --root: uv, then .venv, then this interpreter). "
                        "Ignored if --test-cmd is given.")
    p.add_argument("--pytest-args", default="tests",
                   help="arguments passed to pytest after the launcher (default: tests). "
                        "Ignored if --test-cmd is given.")
    p.add_argument("--test-cmd", default=None,
                   help="full override for projects whose suite isn't pytest-shaped (e.g. a stdlib-only "
                        "project with its own unittest-based runner): a shell command, run from --root, "
                        "that must itself write JUnit XML to the path given by the literal token "
                        "'{junit}' if present, else to <out>/junit.xml — "
                        "e.g. 'python3 tools/run_suite.py --xml {junit}'. Takes priority over "
                        "--pytest-cmd/--pytest-args.")
    p.add_argument("--lake-cmd", default="lake build",
                   help="command used to build the proof project (default: 'lake build')")
    p.add_argument("--skip-pytest", action="store_true",
                   help="don't re-run the test suite; reuse junit.xml under --out if present")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    proof_root = (root / args.proof).resolve()
    spec_path = (root / args.spec).resolve()
    out = (root / args.out).resolve() if args.out else (root / "build" / "proof")

    if not proof_root.is_dir():
        print(f"error: proof project not found at {proof_root}", file=sys.stderr)
        return 2
    if not spec_path.is_file():
        print(f"error: spec not found at {spec_path}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    # 1. Discover the Lean sources (read-only; nothing under proof_root is copied or modified).
    lean_files = discover_lean_files(proof_root)
    if not lean_files:
        print(f"error: no *.lean files under {proof_root}", file=sys.stderr)
        return 2

    # 2. Build the proof.
    rc, output = run(shlex.split(args.lake_cmd), proof_root, env_with_lean_toolchain())
    err_lines = {(m.group(1), int(m.group(2))) for line in output.splitlines()
                 if (m := ERROR.match(line))}

    # 3. Parse declarations + every deferred/excluded-table row, across all discovered files.
    theorems: list[dict] = []
    deferrals: list[dict] = []
    for rel in lean_files:
        text = (proof_root / rel).read_text("utf-8")
        rel_s = str(rel)
        theorems.extend(parse_lean(text, rel_s, err_lines))
        deferrals.extend(parse_deferrals(rel_s, text))
    theorems.sort(key=lambda d: (d["file"], d["line"]))

    # 4. Test-suite results — fresh, unless told to reuse what's already there.
    junit_path = out / "junit.xml"
    if args.skip_pytest:
        junit = parse_junit(junit_path) if junit_path.exists() else {"total": 0, "failed": [], "cases": []}
        rc_py = 1 if junit["failed"] else 0
    else:
        if args.test_cmd:
            cmd_str = args.test_cmd.replace("{junit}", str(junit_path))
            cmd = shlex.split(cmd_str)
            if "{junit}" not in args.test_cmd:
                cmd += [f"--junitxml={junit_path}"]  # pytest-shaped fallback for a bare custom launcher
        else:
            cmd = [*(shlex.split(args.pytest_cmd) if args.pytest_cmd else default_pytest_cmd(root)),
                   *shlex.split(args.pytest_args), f"--junitxml={junit_path}"]
        rc_py, test_output = run(cmd, root)
        if not junit_path.exists():
            print(f"warning: test command produced no {junit_path.name} "
                  f"(exit {rc_py}); pytest/tests counted as 0/0, not a pass:\n"
                  + "\n".join(f"  {line}" for line in test_output.strip().splitlines()[-10:]),
                  file=sys.stderr)
        junit = parse_junit(junit_path) if junit_path.exists() else {"total": 0, "failed": [], "cases": []}

    # 5. Join on spec IDs.
    ids = spec_ids(spec_path)
    by_id: dict[str, dict] = {i: {"id": i, "theorems": [], "deferred": None, "tests": []} for i in ids}
    for t in theorems:
        for i in t["ids"]:
            if i in by_id:
                by_id[i]["theorems"].append(t["name"])
    for d in deferrals:
        if d["id"] in by_id:
            by_id[d["id"]]["deferred"] = d
            by_id[d["id"]]["tests"] = d["tests"]
    n_checked = sum(t["status"] == "checked" for t in theorems)
    all_green = rc == 0 and rc_py == 0

    manifest = {
        "spec": str(spec_path.relative_to(root)),
        "spec_version": spec_version(spec_path),
        "source": args.source,
        "proof_repo": str(proof_root.relative_to(root)) if proof_root.is_relative_to(root) else str(proof_root),
        "build": {"exit": rc, "theorems_total": len(theorems),
                  "theorems_checked": n_checked,
                  "errors": sorted(f"{f}:{l}" for f, l in err_lines)},
        "pytest": {"skipped": args.skip_pytest, **junit},
        "theorems": theorems,
        "deferred_to_pytest": deferrals,
    }
    (out / "proof-results.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # 6. Markdown table.
    source_line = f"`{args.source}`; " if args.source else ""
    L = ["# Proof evidence — five-way relation", "",
         "Per spec ID: the Lean proof (and its check status), and the pytest",
         "tests that carry the parts Lean cannot see. Source throughout:",
         f"{source_line}proof sources read from `{proof_root.relative_to(root) if proof_root.is_relative_to(root) else proof_root}/`.",
         "",
         f"- **Lean build:** exit {rc} — {n_checked}/{len(theorems)} declarations kernel-checked"
         + ("" if rc == 0 else f" (errors: {', '.join(manifest['build']['errors']) or 'see log'})"),
         f"- **pytest{' (reused)' if args.skip_pytest else ''}:** "
         + (f"{junit['total'] - len(junit['failed'])}/{junit['total']} passed"
            + (f" (failed: {', '.join(junit['failed'])})" if junit["failed"] else "")
            if junit["total"] else "no results"),
         f"- **Verdict: {'GREEN' if all_green else 'RED'}**", "",
         "| spec ID | Lean proof (theorem) | proof status | pytest (spec test) | pytest result |",
         "| --- | --- | --- | --- | --- |"]
    for i in sorted(by_id, key=lambda s: (s[0], int(s[2:]))):
        e = by_id[i]
        th = ", ".join(e["theorems"]) or "—"
        st = "checked" if (rc == 0 and e["theorems"]) else ("failed" if e["theorems"] else "—")
        ts = ", ".join(e["tests"]) or "—"
        tr = "passed" if (all_green and ts != "—") else ("—" if ts == "—" else "see junit")
        if e["deferred"] and e["deferred"]["scope"]:
            th += f" *(defers {e['deferred']['scope']})*"
        L.append(f"| {i} | {th} | {st} | {ts} | {tr} |")
    L += ["",
          "## What each column means", "",
          "- **Lean proof** — the theorem(s) whose statements discharge the ID for",
          "  *all* inputs (deductive, kernel-checked; the Lean build is the proof result).",
          "- **pytest** — the spec's acceptance tests carrying the ID's empirical",
          "  half (one real run per case); result from the fresh (or reused) junit.",
          "- The two are independent evidence kinds; the transcription of the source",
          "  into the Lean model is the single manual bridge between them.", ""]
    (out / "PROOF_EVIDENCE.md").write_text("\n".join(L))

    print(f"proof evidence: build exit {rc} ({n_checked}/{len(theorems)} checked), "
          f"pytest {junit['total'] - len(junit['failed'])}/{junit['total']} passed -> {out}/")
    return 0 if all_green else 1


if __name__ == "__main__":
    sys.exit(main())
