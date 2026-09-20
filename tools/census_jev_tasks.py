"""Generate one Jev task per census subject (`PROPOSAL_obligation_census.md`).

Jev (`typesafe/jev-1.13`) answers strongly-typed structured questions against a `state` --
`noul` (boolean: true/false), `choice` (one of a fixed option list), `score` (one of a rubric's
levels) -- and nothing free-text. That fits three of the census's fields exactly: `form` (a
4-way choice), `checker` (a 4-way choice), and `scope.stated` (a boolean). It does not fit
`expression`, `quantities`, `rationale`, or `confidence`, which are free text or numeric; this
generator asks Jev only what it can answer in its own typed vocabulary and leaves those four to
`tools/census.py`'s own model-classification path.

One Jev call per subject, all three questions together, in the multi-question shape:
  {"model": "typesafe/jev-1.13", "state": <str>, "questions": {"form": {...}, "checker": {...},
   "scope_stated": {...}}}

Usage:
  uv run python tools/census_jev_tasks.py --spec SPEC.md [--out build/census/jev_tasks.jsonl]

Output: one JSON object per line (JSONL), one line per live R/C/I/K/E id, in C-07 order, ready to
feed to a Jev runner. Each task also carries "id" and "family" alongside "model"/"state"/
"questions" so the runner's answers can be joined back to the subject -- Jev itself only reads
"model", "state", and "questions".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from census import Subject, load_subjects  # tools/census.py

MODEL = "typesafe/jev-1.13"

FORM_CRITERIA = {
    "expr": "Reduces to one closed boolean or arithmetic proposition over named quantities the "
    "implementation already exposes -- checkable from values alone, no run needed (a byte "
    "bound, a ratio range, an injective-mapping property).",
    "struct": "Asserts that a named thing exists with a named shape -- a key, a field, a file, "
    "a symbol, an exact literal -- rather than a computed relationship between values.",
    "behavior": "A stimulus and an observable response that only running the system can show; "
    "not one static proposition, and not merely a shape.",
    "prose": "Intent, scope, or a quality no single observation settles -- why something exists, "
    "a boundary drawn in words, a property with no stated formula or test.",
}

CHECKER_CRITERIA = {
    "ast": "A pattern found in source code; no execution needed.",
    "schema": "A structural check of a produced artifact -- a file, a JSON object.",
    "test": "Execute the system and observe the result.",
    "llm": "The obligation needs judgment; no mechanical check suffices.",
}

SCOPE_CRITERIA = {
    "true": "The statement itself names, in words, the conditions under which the obligation "
    "applies (a mode, a flag, a precondition).",
    "false": "The obligation is unconditional, or applies under a condition the statement never "
    "states (a reader would have to infer it).",
}


def render_state(subject: Subject) -> str:
    verified = f" Verified today by: {', '.join(subject.verified_by)}." if subject.verified_by else ""
    return (
        f"Specification obligation {subject.id} (family {subject.family}) of speccheck's own "
        f"SPEC.md.{verified}\n\nStatement:\n{subject.statement}"
    )


def build_task(subject: Subject) -> dict[str, Any]:
    return {
        "id": subject.id,
        "family": subject.family,
        "model": MODEL,
        "state": render_state(subject),
        "questions": {
            "form": {
                "type": "choice",
                "instructions": (
                    "Classify this obligation by what would be cheapest to verify it, not by "
                    "how it reads. Choose exactly one option."
                ),
                "criteria": FORM_CRITERIA,  # the keys ARE the options (no separate "options" key)
            },
            "checker": {
                "type": "choice",
                "instructions": (
                    "Given the obligation's form, what is the cheapest mechanism that could "
                    "verify it? expr -> ast or test; struct -> schema or ast; behavior -> test; "
                    "prose -> llm. Choose exactly one option."
                ),
                "criteria": CHECKER_CRITERIA,
            },
            "scope_stated": {
                "type": "noul",
                "instructions": (
                    "Does the statement itself name, in words, the conditions under which the "
                    "obligation applies (a mode, a flag, a precondition)?"
                ),
                "criteria": SCOPE_CRITERIA,
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", default="SPEC.md")
    parser.add_argument("--out", default="build/census/jev_tasks.jsonl")
    args = parser.parse_args(argv)

    subjects = load_subjects(Path(args.spec))
    if not subjects:
        print("census_jev_tasks: no live R/C/I/K/E ids found", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for subject in subjects:
            f.write(json.dumps(build_task(subject), ensure_ascii=False) + "\n")

    print(f"wrote {len(subjects)} Jev tasks to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
