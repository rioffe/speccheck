"""Generate one Jev task per judged edge of a `speccheck check --judge llm` run, for a
second-opinion cross-check -- not a replacement judge (see the design note below and
`docs/proposals/PROPOSAL_obligation_census.md`'s sibling reasoning: Jev's typed vocabulary has no slot for the
clause-grounding (R-34/K-15) or evidence-grounding (I-005) the real judge contract (C-06/C-10)
requires, so this never feeds back into `--judge llm`; it only asks Jev the bare verdict question
and reports where it disagrees with the recorded one, for a human to look at).

Reads a `speccheck.json` produced by `check --judge llm` (its `strict`/`--out` doesn't matter;
what matters is that some edges have a non-null `verdict`) and the same `--tests` roots that run
used, re-attributes them (the same `attribute.attribute_file` the kernel itself uses) to recover
each judged edge's test span and source, and writes one Jev task per edge -- reusing the real
judge's own request builder (`judge.build_request`) so the `state` Jev sees is the same
statement + line-numbered source the real judge saw, just without asking for `clause`/`evidence`.

Usage:
  uv run python tools/judge_crosscheck_tasks.py --report build/speccheck-llm/speccheck.json \
      --tests tests [--root .] [--out build/census/crosscheck_tasks.jsonl]

Each task also carries "recorded_verdict", "recorded_clause", "recorded_coerced" alongside
"id"/"family" (ignored by Jev; read back by `tools/judge_crosscheck_report.py`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from speccheck.attribute import attribute_file
from speccheck.extract import ScanCounters, scan_roots
from speccheck.judge import VERDICTS, build_request

MODEL = "typesafe/jev-1.13"

VERDICT_CRITERIA = {
    "ASSERTS": "The test contains at least one assertion whose expected value or condition "
    "corresponds to a clause of the statement.",
    "EXECUTES_ONLY": "The test runs code the statement describes, but no assertion checks it "
    "(assertions absent, trivial, or about something else).",
    "UNRELATED": "The test does not exercise any clause of the statement.",
    "UNKNOWN": "Cannot decide from the source given. Prefer this over guessing.",
}
assert set(VERDICT_CRITERIA) == set(VERDICTS)  # stay in lockstep with the real judge's vocabulary


def _resolve_paths(raw_list: list[str], root: Path) -> list[Path]:
    out = []
    for raw in raw_list:
        for segment in raw.split(","):
            segment = segment.strip(" \t")
            if segment:
                out.append((root / segment).resolve())
    return out


def build_lookup(tests_paths: list[Path], root: Path) -> dict[tuple[str, str, str], tuple[Any, tuple[str, ...]]]:
    """(file, name, classname) -> (TestCase, file lines) for every test case and file-level
    fallback under the given roots -- the same shape `cli.execute` builds for the real judge."""
    counters = ScanCounters()
    scanned_files = scan_roots(tests_paths, root, frozenset(), None, counters)
    lookup: dict[tuple[str, str, str], tuple[Any, tuple[str, ...]]] = {}
    for scanned in scanned_files:
        attributed, _notes = attribute_file(scanned)
        for case in (*attributed.cases, attributed.file_case):
            lookup[(case.file, case.name, case.classname)] = (case, scanned.lines)
    return lookup


def render_state(statement: str, req_json: dict[str, Any]) -> str:
    return (
        f"Specification obligation {req_json['id']}.\n\nStatement:\n{statement}\n\n"
        f"Test file {req_json['file']}, lines {req_json['start']}-{req_json['end']}:\n"
        f"{req_json['source']}"
    )


def build_task(ident: str, statement: str, testcase: Any, file_lines: tuple[str, ...], recorded: dict[str, Any]) -> dict[str, Any]:
    req = build_request(ident, statement, testcase, file_lines)
    req_json = json.loads(req.to_json())
    task_id = f"{ident}::{testcase.file}::{testcase.name or '(file)'}"
    return {
        "id": task_id,
        "family": ident.split("-", 1)[0],
        "recorded_verdict": recorded["verdict"]["verdict"],
        "recorded_clause": recorded["verdict"].get("clause", ""),
        "recorded_coerced": recorded["verdict"].get("coerced", False),
        "model": MODEL,
        "state": render_state(statement, req_json),
        "questions": {
            "verdict": {
                "type": "choice",
                "instructions": (
                    "Does any assertion in this test case check any clause of the statement? "
                    "Choose exactly one option."
                ),
                "criteria": VERDICT_CRITERIA,
            }
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", required=True, help="a speccheck.json from --judge llm")
    parser.add_argument("--tests", action="append", required=True, help="same --tests roots as that run")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default="build/census/crosscheck_tasks.jsonl")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    if report.get("judge") not in ("llm",):
        print(f"judge_crosscheck_tasks: report was run with --judge {report.get('judge')!r}, not llm", file=sys.stderr)

    lookup = build_lookup(_resolve_paths(args.tests, root), root)

    tasks = []
    missing = 0
    for rec in report["ids"]:
        for t in rec["tests"]:
            if t["verdict"] is None:
                continue
            key = (t["file"], t["name"], t["classname"])
            found = lookup.get(key)
            if found is None:
                missing += 1
                continue
            testcase, file_lines = found
            tasks.append(build_task(rec["id"], rec["statement"], testcase, file_lines, t))

    if missing:
        print(
            f"judge_crosscheck_tasks: {missing} judged edge(s) could not be matched to a test "
            "case under --tests (source tree likely differs from the run's) -- skipped",
            file=sys.stderr,
        )
    if not tasks:
        print("judge_crosscheck_tasks: no judged edges found", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    print(f"wrote {len(tasks)} tasks to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
