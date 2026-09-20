"""Render one census task record (from a .jsonl list) as a readable Markdown document.

Given a `.jsonl` of task records (each line one JSON object) and an `--id`, find the
matching task and print a nicely formatted Markdown rendering to stdout, or to the file
named by `--output`.

The renderer is generic: it handles any task shape it meets, not just the Jev triage
tasks. Recognised fields:

  * `id`, `family`, `model`, `state` -- the universal task fields; `state` is the prose
    body, rendered as a block quote.
  * `questions` -- a mapping of question name -> question object. Two kinds render as a
    table:
        - `choice` -- `options` list + `criteria` (option -> "when to pick it").
        - `noul`   -- `true`/`false` `criteria` (a yes/no question).
    Any other question object renders its remaining fields generically so nothing is lost.
  * Any other scalar top-level field (e.g. `recorded_verdict` in the crosscheck tasks) is
    rendered as an extra note under the heading.

Usage:
  uv run python tools/format_task.py --id R-01
  uv run python tools/format_task.py --tasks build/census/jev_tasks.jsonl --id R-01
  uv run python tools/format_task.py --id R-01 --output out/R-01.md
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path
from typing import Any

# Default tasks file -- the Jev triage census; override with --tasks.
DEFAULT_TASKS = "build/census/jev_tasks.jsonl"

# Top-level keys that get dedicated rendering rather than the generic note list.
RESERVED = {"id", "state", "questions", "answers"}

# Long values become their own quoted note instead of joining the one-line metadata row.
MAX_INLINE = 60

_TYPE_DISPLAY = {"noul": "yes/no", "choice": "choice", "numeric": "numeric"}


def load_jsonl(path: str) -> list[dict[str, Any]]:
    out = []
    with Path(path).open(encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"format_task: skipping {Path(path)}:{lineno}: {e}", file=sys.stderr)
    return out


def humanize(key: str) -> str:
    """recorded_verdict -> 'Recorded verdict', n_total -> 'N total'."""
    out = []
    for word in key.split("_"):
        out.append(word.upper() if len(word) <= 1 else word.capitalize())
    return " ".join(out)


def codeish(v: str) -> bool:
    """A token / id / model -- not a sentence -- so it reads backticked, e.g. `typesafe/jev-1.13`."""
    return bool(v) and "/" in v and " " not in v and len(v) <= 40


def render_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    return f"`{s}`" if codeish(s) else s


def cell(text: str) -> str:
    """Make a value safe for a Markdown table cell: escape pipes, flatten newlines."""
    return str(text).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def blockquote(text: str) -> list[str]:
    out = []
    for line in str(text).split("\n"):
        out.append("> " + line if line.strip() else ">")
    return out


def render_question(index: int, name: str, q: dict[str, Any]) -> list[str]:
    qtype = q.get("type")
    lines = []

    display = qtype if qtype is None else (_TYPE_DISPLAY.get(qtype) or qtype)
    if qtype is not None and qtype not in _TYPE_DISPLAY:
        display = f"{_TYPE_DISPLAY.get(qtype, qtype)} ({qtype})"
    elif qtype in _TYPE_DISPLAY:
        display = f"{_TYPE_DISPLAY[qtype]} ({qtype})" if qtype != "choice" else "choice"

    lines.append(f"### {index}. `{name}` — *{display}*")
    lines.append("")

    instr = q.get("instructions")
    if instr:
        lines.append(f"**Instructions:** {instr}")
        lines.append("")

    if qtype == "choice":
        options = q.get("options", []) or []
        criteria = q.get("criteria", {}) or {}
        order = list(options) + [k for k in criteria if k not in options]
        if not order:
            lines.append("_No options declared._")
            lines.append("")
        else:
            lines.append("| Option | When to pick it |")
            lines.append("| --- | --- |")
            for opt in order:
                crit = criteria.get(opt, "—")
                lines.append(f"| **`{opt}`** | {cell(crit)} |")
            lines.append("")
    elif qtype == "noul":
        criteria = q.get("criteria", {}) or {}
        order = [k for k in ("true", "false") if k in criteria]
        order += [k for k in criteria if k not in ("true", "false")]
        if not order:
            lines.append("_No outcomes declared._")
            lines.append("")
        else:
            lines.append("| Value | When to pick it |")
            lines.append("| --- | --- |")
            for val in order:
                crit = criteria.get(val, "—")
                lines.append(f"| **`{val}`** | {cell(crit)} |")
            lines.append("")
    else:
        # Unknown question kind: dump any remaining fields so nothing is hidden.
        for k, v in q.items():
            if k in ("type", "instructions"):
                continue
            if isinstance(v, dict):
                lines.append(f"- **{humanize(k)}:**")
                for kk, vv in v.items():
                    lines.append(f"  - `{kk}`: {cell(str(vv))}")
            else:
                lines.append(f"- **{humanize(k)}:** {render_scalar(v)}")
        if qtype is None and not any(k not in ("type", "instructions") for k in q):
            lines.append("_No criteria declared._")
        lines.append("")

    return lines


def render_task(rec: dict[str, Any]) -> str:
    lines: list[str] = []

    rec_id = rec.get("id", "?")
    has_questions = isinstance(rec.get("questions"), dict) and rec["questions"]
    lines.append(f"# {rec_id}" + (" — Verification Questionnaire" if has_questions else ""))
    lines.append("")

    # One-line metadata: short scalar fields that aren't reserved for their own section.
    meta: list[tuple[str, Any]] = []
    notes: list[tuple[str, Any]] = []
    for k, v in rec.items():
        if k in RESERVED or isinstance(v, (dict, list)):
            continue
        if "\n" in str(v) or len(str(v)) > MAX_INLINE:
            notes.append((k, v))
        else:
            meta.append((k, v))
    if meta:
        parts = [f"**{humanize(k)}:** {render_scalar(v)}" for k, v in meta]
        lines.append(" · ".join(parts))
        lines.append("")

    if notes:
        lines.append("**Also recorded:**")
        lines.append("")
        for k, v in notes:
            val = str(v)
            if "\n" in val:
                lines.append(f"- **{humanize(k)}:**")
                lines.extend(blockquote(val))
            else:
                lines.append(f"- **{humanize(k)}:** {render_scalar(v)}")
        lines.append("")

    state = rec.get("state")
    if state:
        lines.append("## State")
        lines.append("")
        lines.extend(blockquote(state))
        lines.append("")

    questions = rec.get("questions")
    if isinstance(questions, dict) and questions:
        lines.append("## Questions")
        lines.append("")
        for i, (name, q) in enumerate(questions.items(), start=1):
            if not isinstance(q, dict):
                q = {"value": q}
            lines.extend(render_question(i, name, q))

    text = "\n".join(lines).rstrip() + "\n"
    return text


def main(argv: list[str] | None = None) -> int:
    # Be a well-behaved pipe consumer: when a downstream (e.g. `mdv6`) closes stdin early to
    # launch its viewer, die on SIGPIPE like `head` instead of raising a BrokenPipeError on the
    # stdout flush at exit. (SIG_DFL is POSIX-only; absent on Windows.)
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    parser = argparse.ArgumentParser(
        description="Render a census task record from a .jsonl file as Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tasks", default=DEFAULT_TASKS, help=f"input .jsonl (default: {DEFAULT_TASKS})"
    )
    parser.add_argument(
        "--id", required=True, metavar="ID", help="task id to render (exact match on 'id')"
    )
    parser.add_argument(
        "--output", default=None, metavar="FILE", help="write Markdown to FILE instead of stdout"
    )
    args = parser.parse_args(argv)

    tasks_path = Path(args.tasks)
    if not tasks_path.is_file():
        print(f"format_task: no such tasks file: {args.tasks}", file=sys.stderr)
        return 1
    tasks = load_jsonl(args.tasks)
    matches = [t for t in tasks if t.get("id") == args.id]

    if not matches:
        print(f"format_task: no task with id {args.id!r} in {args.tasks}", file=sys.stderr)
        ids = [t.get("id", "?") for t in tasks]
        preview = ", ".join(str(i) for i in ids[:30])
        tail = " …" if len(ids) > 30 else ""
        print(f"available ids ({len(ids)}): {preview}{tail}", file=sys.stderr)
        return 1

    if len(matches) > 1:
        print(
            f"format_task: {len(matches)} tasks share id {args.id!r}; rendering the first",
            file=sys.stderr,
        )

    text = render_task(matches[0])

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out} ({len(matches[0].get('questions', {}))} question(s))", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
