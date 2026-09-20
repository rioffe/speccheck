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
   * `answers` -- a mapping of question name -> judge response, the response-side sibling of
     `questions`: a `choice` answer shows its chosen option, probability table and confidence; a
     `noul` answer shows P(true). Any other shape dumps its fields so nothing is lost.
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


def _type_display(type_name: Any) -> str:
    """Display name for a question/answer type: 'noul' -> 'yes/no (noul)', 'choice' -> 'choice'."""
    if type_name is None:
        return "?"
    if type_name in _TYPE_DISPLAY:
        return "choice" if type_name == "choice" else f"{_TYPE_DISPLAY[type_name]} ({type_name})"
    return f"{type_name} ({type_name})"


def _pct(v: Any) -> str:
    """A 0-1 probability as a percentage (0.75 -> '75%'); bools/out-of-range fall back to scalar."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)) and 0.0 <= v <= 1.0:
        return f"{v * 100:g}%"
    return render_scalar(v)


def _render_fields(fields: dict[str, Any]) -> list[str]:
    """Dump leftover fields generically so a new answer shape loses nothing."""
    out = []
    for k, v in fields.items():
        if isinstance(v, dict):
            out.append(f"- **{humanize(k)}:**")
            for kk, vv in v.items():
                out.append(f"   - `{kk}`: {cell(str(vv))}")
        else:
            out.append(f"- **{humanize(k)}:** {render_scalar(v)}")
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


def render_answer(index: int, name: str, a: dict[str, Any]) -> list[str]:
    """One judge response -- the response-side mirror of render_question: choice/noul shapes."""
    atype = a.get("type")
    lines: list[str] = [f"### {index}. `{name}` — *{_type_display(atype)}*", ""]

    if atype == "choice":
        known = {"type", "choice", "probabilities", "confidence"}
        probabilities = a.get("probabilities")
        if not isinstance(probabilities, dict):
            probabilities = {}
        choice = a.get("choice")
        if choice is not None and choice in probabilities:
            lines.append(f"**Chosen:** `{choice}` ({_pct(probabilities[choice])})")
        elif choice is not None:
            lines.append(f"**Chosen:** `{choice}`")
        else:
            lines.append("**Chosen:** _no option recorded_")
        lines.append("")
        order = [choice] if choice in probabilities else []
        order += [k for k in probabilities if k not in order]
        if order:
            lines.append("| Option | Probability |")
            lines.append("| --- | --- |")
            for opt in order:
                mark = f"**`{opt}`**" if opt == choice else f"`{opt}`"
                lines.append(f"| {mark} | {_pct(probabilities[opt])} |")
            lines.append("")
        conf = a.get("confidence")
        if conf is not None:
            lines.append(f"**Confidence:** {_pct(conf)}")
            lines.append("")
    elif atype == "noul":
        known = {"type", "noul"}
        val = a.get("noul")
        if val is None:
            lines.append("_No answer recorded._")
        elif isinstance(val, bool):
            lines.append(f"**Answer:** {render_scalar(val)}")
        elif isinstance(val, (int, float)) and 0.0 <= val <= 1.0:
            lines.append(f"**Probability true:** {_pct(val)}")
        else:
            lines.append(f"**Answer:** {render_scalar(val)}")
        lines.append("")
    else:
        known = {"type"}

    extra = {k: v for k, v in a.items() if k not in known}
    if extra:
        lines.append("**Also recorded:**")
        lines.append("")
        lines.extend(_render_fields(extra))
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
    answers = rec.get("answers")
    if isinstance(answers, dict) and answers:
        lines.append("## Answers")
        lines.append("")
        for i, (name, a) in enumerate(answers.items(), start=1):
            if not isinstance(a, dict):
                a = {"value": a}
            lines.extend(render_answer(i, name, a))

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
        ids = [str(t.get("id", "?")) for t in tasks]
        print(f"available ids ({len(ids)}):", file=sys.stderr)
        for start in range(0, len(ids), 8):
            print("    " + ", ".join(ids[start : start + 8]), file=sys.stderr)
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
