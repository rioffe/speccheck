"""T-84: the golden fixture's adjacent subset under two C-10 texts (opt-in, not CI).

Runs `check --judge llm` three times per prompt text over a copy of `fixtures/target/`, scores
only the eight adjacent edges against `golden/judge_labels.json`, and prints each run's verdicts,
its downgrade count, its accuracy over the subset and the `judge_prompt_sha256` the run recorded.

The two arms are the shipped v1.16 C-10 text and the pre-v1.16 text, recovered from this
repository's git history by digest. The second arm is what makes the row falsifiable: without it,
"six of eight downgraded" cannot be told apart from a model that downgrades adjacent edges anyway.

Usage:
  uv run python tools/adjacent_eval.py [--model M] [--url U] [--api-key K] [--runs 3]
                                       [--concurrency 8] [--old-sha f6b124bd...] [--verbose]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from speccheck import judge_llm
from speccheck.cli import run_check

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "target"
LABELS = FIXTURE / "golden" / "judge_labels.json"
OLD_SHA = "f6b124bdd6ea5948d052f6cb45de85eb5409e0165ba2371cd784a313472bcfd1"  # pre-v1.16 C-10
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
    "llm",
]

# T-84/T-76: the eight adjacent edges of fixtures/target/ — each cites an id whose own statement
# names another id, and asserts only that neighbour's fact (so the label is UNRELATED)
ADJACENT = (
    "R-01 tests/test_core.py::test_add_rounding_fact",
    "R-01 tests/test_core.py::test_add_rounding_of_a_half_cent",
    "R-02 tests/test_core.py::test_subtract_rounding_fact",
    "E-02 tests/test_core.py::test_scale_empty_input_is_not_mutated",
    "I-001 tests/test_core.py::test_add_commutes_on_plain_sum",
    "I-001 tests/test_core.py::test_add_commutes_rounding_fact",
    "C-04 tests/test_summary.py::test_summary_total_rounding_fact",
    "C-04 tests/test_summary.py::test_summary_mean_rounding_fact",
)
DOWNGRADED = ("UNRELATED", "EXECUTES_ONLY")


def old_prompt(wanted_sha: str) -> str:
    """The first historical version of `judge_prompt.md` whose sha256 equals `wanted_sha`."""
    revs = subprocess.run(
        ["git", "log", "--format=%H", "--", "src/speccheck/judge_prompt.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for rev in revs:
        text = subprocess.run(
            ["git", "show", f"{rev}:src/speccheck/judge_prompt.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        if hashlib.sha256(text.encode("utf-8")).hexdigest() == wanted_sha:
            return text
    raise SystemExit(f"no revision of judge_prompt.md has sha256 {wanted_sha}")


def one_run(env: dict[str, str], prompt: str | None, concurrency: str = "8") -> tuple[dict, str]:
    """One `check --judge llm` over a fresh copy of the fixture, under `prompt` when given."""
    original = judge_llm.load_prompt
    if prompt is not None:
        judge_llm.load_prompt = lambda: prompt  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            shutil.copytree(FIXTURE, target)
            old = os.getcwd()
            os.chdir(target)
            out = io.StringIO()
            try:
                run_check(
                    [*ARGS, "--out", "out", "--judge-concurrency", concurrency], env, out
                )
            finally:
                os.chdir(old)
            doc = json.loads((target / "out" / "speccheck.json").read_text(encoding="utf-8"))
    finally:
        judge_llm.load_prompt = original  # type: ignore[assignment]
    return doc, out.getvalue().strip()


def score_adjacent(doc: dict) -> tuple[dict[str, str], int]:
    """The adjacent edges' verdicts (UNKNOWN included) and how many were downgraded."""
    verdicts = {
        f"{rec['id']} {t['file']}::{t['name']}": t["verdict"]["verdict"]
        for rec in doc["ids"]
        for t in rec["tests"]
        if t["verdict"] is not None
    }
    found = {k: verdicts.get(k, "not judged") for k in ADJACENT}
    return found, sum(1 for v in found.values() if v in DOWNGRADED)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("SPECCHECK_JUDGE_URL", "https://openrouter.ai/api/v1/chat/completions"),
    )
    parser.add_argument("--model", default=os.environ.get("SPECCHECK_JUDGE_MODEL", ""))
    parser.add_argument("--api-key", default=os.environ.get("SPECCHECK_JUDGE_API_KEY", ""))
    parser.add_argument("--timeout", default=os.environ.get("SPECCHECK_JUDGE_TIMEOUT", "120"))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--concurrency", default="8")
    parser.add_argument("--old-sha", default=OLD_SHA)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    env = {
        "SPECCHECK_JUDGE_URL": args.url,
        "SPECCHECK_JUDGE_MODEL": args.model,
        "SPECCHECK_JUDGE_API_KEY": args.api_key,
        "SPECCHECK_JUDGE_TIMEOUT": str(args.timeout),
    }
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    # C-10's vocabulary grades these EXECUTES_ONLY (they run the cited id's code); T-76/T-84's
    # floor is "downgraded", so both tokens count (F-1)
    assert all(labels[k] in DOWNGRADED for k in ADJACENT), "the adjacent set must be downgraded"
    previous = old_prompt(args.old_sha)
    print(f"model: {args.model}  url: {args.url}  date: {dt.date.today().isoformat()}")
    print(f"shipped C-10 sha256: {hashlib.sha256(judge_llm.load_prompt().encode()).hexdigest()}")
    print(f"pre-v1.16 C-10 sha256: {args.old_sha}")
    for name, prompt in (("v1.16 (shipped)", None), ("pre-v1.16", previous)):
        for i in range(1, args.runs + 1):
            doc, summary = one_run(env, prompt, args.concurrency)
            verdicts, downgraded = score_adjacent(doc)
            print(
                f"{name} run {i}: {downgraded}/8 downgraded  "
                f"judge_prompt_sha256={doc['judge_prompt_sha256']}  unknown_rate="
                f"{doc['metrics']['unknown_rate']}"
            )
            print(f"  {summary}")
            if args.verbose:
                for key, verdict in verdicts.items():
                    print(f"  {key}: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
