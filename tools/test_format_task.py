"""Regression test: a results record's `answers` block must render, not be dropped.

The crosscheck / jev *results* census carries each judge response under `answers`
(a choice verdict with its probability distribution, a yes/no answer, ...), not under
`questions`. Until format_task rendered `answers`, that whole block was lost — the
record printed only its `id` / `family` / `model` line. These tests pin the fix.

Run: `python3 tools/test_format_task.py` (exits non-zero on any failure).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import format_task as ft

CENSUS = Path(__file__).resolve().parent.parent / "build" / "census"


def _render(tasks_path: str) -> tuple[str, dict[str, Any]]:
    tasks = ft.load_jsonl(tasks_path)
    rec = tasks[0]
    return ft.render_task(rec), rec


FAILS: list[str] = []


def check(cond: bool, label: str) -> None:
    if cond:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        FAILS.append(label)


def test_crosscheck_answers_render() -> None:
    """A crosscheck verdict (choice + probabilities + confidence) must appear."""
    print("crosscheck_results.jsonl")
    text, rec = _render(str(CENSUS / "crosscheck_results.jsonl"))
    verdict = rec["answers"]["verdict"]
    chosen = verdict["choice"]
    probs = verdict["probabilities"]

    check("## Answers" in text, "## Answers section present")
    check(f"`{chosen}`" in text, f"chosen option `{chosen}` rendered")
    check("**Confidence:**" in text, "confidence line rendered")
    for opt, p in probs.items():
        check(str(p) in text, f"probability {p} for {opt} rendered")
    # The whole block was previously gone: make sure the record has more than its
    # metadata row.
    check(text.count("\n") > 4, "render is not just the id/family/model line")


def test_jev_results_multiple_answers() -> None:
    """Multiple answers incl. a noul yes/no answer must each render."""
    print("jev_results.jsonl")
    text, rec = _render(str(CENSUS / "jev_results.jsonl"))
    answers = rec["answers"]
    check("## Answers" in text, "## Answers section present")
    for name, resp in answers.items():
        typ = resp.get("type")
        if typ == "choice":
            check(f"`{resp['choice']}`" in text, f"{name}: choice {resp['choice']} rendered")
        elif typ == "noul":
            # P true for the yes/no answer: 0.75 -> "75%" (or the raw value).
            val = resp.get("noul")
            check(("75%" in text) or (str(val) in text), f"{name}: noul {val} rendered")


def test_task_files_still_use_questions() -> None:
    """A *task* record (questions, no answers) must still render its questions."""
    print("jev_tasks.jsonl")
    text, rec = _render(str(CENSUS / "jev_tasks.jsonl"))
    check("## Questions" in text, "## Questions section present")
    check("## Answers" not in text, "no spurious Answers section when there are none")


def main() -> int:
    for fn in (
        test_crosscheck_answers_render,
        test_jev_results_multiple_answers,
        test_task_files_still_use_questions,
    ):
        fn()
    print()
    if FAILS:
        print(f"{len(FAILS)} check(s) failed:")
        for f in FAILS:
            print(f"  - {f}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
