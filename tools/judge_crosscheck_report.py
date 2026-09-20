"""Join a Jev judge-crosscheck batch back to the tasks it was generated from and report where
Jev's bare verdict disagrees with the recorded one -- a second opinion for a human to read, not
a re-judgment (see `tools/judge_crosscheck_tasks.py`'s docstring for why this never feeds back
into `--judge llm`).

Usage:
  uv run python tools/judge_crosscheck_tasks.py --report speccheck.json --tests tests --out build/census/crosscheck_tasks.jsonl
  uv run python tools/jev_client.py --task-file build/census/crosscheck_tasks.jsonl --id ALL \
      --concurrency 8 --out build/census/crosscheck_results.jsonl
  uv run python tools/judge_crosscheck_report.py \
      --tasks build/census/crosscheck_tasks.jsonl --results build/census/crosscheck_results.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def load_jsonl(path: str) -> list[dict[str, Any]]:
    out = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", default="build/census/crosscheck_report.md")
    args = parser.parse_args(argv)

    tasks_by_id = {t["id"]: t for t in load_jsonl(args.tasks)}
    results = load_jsonl(args.results)

    rows = []
    errors = 0
    for r in results:
        task = tasks_by_id.get(r["id"])
        if task is None:
            continue
        if "error" in r:
            errors += 1
            continue
        jev_verdict = r["answers"]["verdict"]["choice"]
        probs = r["answers"]["verdict"]["probabilities"]
        rows.append(
            {
                "id": r["id"],
                "recorded": task["recorded_verdict"],
                "recorded_coerced": task["recorded_coerced"],
                "jev": jev_verdict,
                "probabilities": probs,
                "clause": task["recorded_clause"],
            }
        )

    if not rows:
        print("judge_crosscheck_report: no comparable rows", file=sys.stderr)
        return 1

    agree = sum(1 for row in rows if row["recorded"] == row["jev"])
    confusion: Counter[tuple[str, str]] = Counter((row["recorded"], row["jev"]) for row in rows)
    disagreements = [row for row in rows if row["recorded"] != row["jev"]]
    # Two different findings, not one: a coerced UNKNOWN is the real judge's answer being
    # DISCARDED by K-15/E-48 grounding, not a considered verdict -- Jev disagreeing there is a
    # triage lead (an edge worth a human look, or a different judge model). Jev disagreeing with
    # a real, non-UNKNOWN verdict is a substantive conflict between two models that both committed
    # to an answer -- rarer, and worth more scrutiny per edge.
    rescue_leads = [row for row in disagreements if row["recorded"] == "UNKNOWN"]
    genuine_conflicts = [row for row in disagreements if row["recorded"] != "UNKNOWN"]
    committed = [row for row in rows if row["recorded"] != "UNKNOWN"]
    committed_agree = sum(1 for row in committed if row["recorded"] == row["jev"])

    lines = ["# Judge cross-check report (Jev second opinion)", ""]
    lines.append(f"{len(rows)} edges compared ({errors} Jev request failures excluded).")
    lines.append(f"Agreement (all edges): {agree}/{len(rows)} ({agree / len(rows):.4f})")
    if committed:
        lines.append(
            f"Agreement on edges the real judge committed to (excludes recorded UNKNOWN): "
            f"{committed_agree}/{len(committed)} ({committed_agree / len(committed):.4f})"
        )
    lines.append("")
    lines.append("## Confusion (recorded -> Jev)")
    lines.append("")
    lines.append("| recorded | Jev | count |")
    lines.append("| --- | --- | --- |")
    for (recorded, jev), count in sorted(confusion.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {recorded} | {jev} | {count} |")
    lines.append("")

    lines.append(f"## Rescue leads ({len(rescue_leads)}) — recorded UNKNOWN, Jev committed")
    lines.append("")
    lines.append(
        "The real judge formed an opinion but K-15/E-48 discarded it as ungrounded "
        '(`judge: unlocated clause` or similar); Jev, asked the bare verdict question with no '
        "grounding requirement, answered anyway. Not a verdict to trust outright — a lead for a "
        "human to look at, or evidence the judge model/prompt needs work on these specific edges."
    )
    lines.append("")
    if rescue_leads:
        lines.append("| id | Jev verdict | Jev probabilities |")
        lines.append("| --- | --- | --- |")
        for row in sorted(rescue_leads, key=lambda r: r["id"]):
            lines.append(f"| {row['id']} | {row['jev']} | {row['probabilities']} |")
    else:
        lines.append("None.")
    lines.append("")

    lines.append(f"## Genuine conflicts ({len(genuine_conflicts)}) — recorded a real verdict, Jev disagrees")
    lines.append("")
    lines.append(
        "Two models both committed to an answer and it's not the same one. Worth reading the "
        "edge by hand — this is the case that would actually call the recorded verdict into "
        "question, not just flag a gap."
    )
    lines.append("")
    if genuine_conflicts:
        lines.append("| id | recorded | Jev | Jev probabilities | recorded clause |")
        lines.append("| --- | --- | --- | --- | --- |")
        for row in sorted(genuine_conflicts, key=lambda r: r["id"]):
            clause = (row["clause"] or "").replace("|", "\\|").replace("\n", " ")[:120]
            lines.append(
                f"| {row['id']} | {row['recorded']} | {row['jev']} | {row['probabilities']} | {clause} |"
            )
    else:
        lines.append("None.")
    lines.append("")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"agreement: {agree}/{len(rows)} ({agree / len(rows):.4f})")
    print(f"disagreements: {len(disagreements)}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
