"""Fold a Jev batch (`tools/jev_client.py --id ALL --out ...`) into the census's Part C
recommendation and accuracy bar, as a fourth model.

Jev gives one call per subject with a full probability distribution, not `--runs` independent
samples, so it does not go through `census.py`'s consensus-over-runs machinery (which requires
>= 2 samples to call something unanimous). Its analogue of "split" is a close-run distribution:
a subject is flagged when the winning `form` probability is within `--margin` of the runner-up,
or when Jev's own reported `confidence` is below `--min-confidence`.

Usage:
  uv run python tools/jev_report.py --results build/census/jev_results.jsonl [--labels tools/census_labels.json] [--out build/census/jev/CENSUS.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from census import CHECKABLE_FORMS, FAMILIES  # tools/census.py


def load_results(path: str) -> list[dict[str, Any]]:
    subjects = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                subjects.append(json.loads(line))
    return subjects


def top_two(probabilities: dict[str, float]) -> tuple[float, float]:
    values = sorted(probabilities.values(), reverse=True)
    return values[0], (values[1] if len(values) > 1 else 0.0)


def is_close_call(s: dict[str, Any], margin: float) -> bool:
    form = s["answers"]["form"]
    top, second = top_two(form["probabilities"])
    return (top - second) < margin


def recommend(subjects: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = {f: [] for f in FAMILIES}
    for s in subjects:
        by_family[s["family"]].append(s)

    def checkable(group: list[dict[str, Any]]) -> int:
        return sum(1 for s in group if s["answers"]["form"]["choice"] in CHECKABLE_FORMS)

    n_all = len(subjects)
    checkable_all = checkable(subjects)
    c_all = checkable_all / n_all if n_all else 0.0
    per_family = {}
    for f in FAMILIES:
        group = by_family[f]
        n = len(group)
        c = checkable(group)
        per_family[f] = {"n": n, "checkable": c, "ratio": (c / n if n else None)}
    families_hit = [
        f
        for f in FAMILIES
        if per_family[f]["n"] >= 5
        and per_family[f]["ratio"] is not None
        and per_family[f]["ratio"] >= 0.75
    ]
    if c_all >= 0.50:
        rule = 1
    elif families_hit:
        rule = 2
    else:
        rule = 3
    return {
        "n_all": n_all,
        "checkable_all": checkable_all,
        "c_all": c_all,
        "per_family": per_family,
        "rule": rule,
        "families_hit": families_hit,
    }


def score_against_labels(
    subjects_by_id: dict[str, dict[str, Any]], labels: dict[str, Any]
) -> dict[str, Any]:
    total = correct = 0
    prose_as_expr: list[str] = []
    for ident, label in labels.items():
        s = subjects_by_id.get(ident)
        if s is None:
            continue
        total += 1
        form = s["answers"]["form"]["choice"]
        if form == label["form"]:
            correct += 1
        if label["form"] == "prose" and form == "expr":
            prose_as_expr.append(ident)
    accuracy = correct / total if total else None
    return {"total": total, "accuracy": accuracy, "prose_as_expr": prose_as_expr}


def render(
    subjects: list[dict[str, Any]], bar: dict[str, Any], margin: float, min_confidence: float
) -> str:
    rec = recommend(subjects)
    lines = ["# Jev census report", ""]
    acc = "n/a" if bar["accuracy"] is None else f"{bar['accuracy']:.2f}"
    lines.append(
        f"accuracy vs. seed labels: {acc} over {bar['total']} labels "
        f"(prose-as-expr: {bar['prose_as_expr'] or 'none'})"
    )
    lines.append("")
    rule_text = {
        1: f"**Rule 1 — EXPRESSION FIELD, ALL FAMILIES** (c_all = {rec['c_all']:.4f} >= 0.50)",
        2: (
            f"**Rule 2 — EXPRESSION FIELD, FAMILIES {{{', '.join(rec['families_hit'])}}} ONLY** "
            f"(c_all = {rec['c_all']:.4f} < 0.50)"
        ),
        3: f"**Rule 3 — NO EXPRESSION LANGUAGE** (c_all = {rec['c_all']:.4f})",
    }[rec["rule"]]
    lines.append(rule_text)
    lines.append("")
    lines.append(f"c_all = {rec['checkable_all']}/{rec['n_all']} = {rec['c_all']:.4f}")
    lines.append("")
    lines.append("| family | N | checkable | ratio |")
    lines.append("| --- | --- | --- | --- |")
    for f in FAMILIES:
        info = rec["per_family"][f]
        ratio_text = "n/a" if info["ratio"] is None else f"{info['ratio']:.4f}"
        lines.append(f"| {f} | {info['n']} | {info['checkable']} | {ratio_text} |")
    lines.append("")

    close_calls = sorted(
        (s for s in subjects if is_close_call(s, margin)), key=lambda s: s["id"]
    )
    low_conf = sorted(
        (
            s
            for s in subjects
            if s not in close_calls and s["answers"]["form"]["confidence"] < min_confidence
        ),
        key=lambda s: s["id"],
    )
    lines.append(f"## Close calls (top-2 form probabilities within {margin})")
    lines.append("")
    if close_calls:
        for s in close_calls:
            top, second = top_two(s["answers"]["form"]["probabilities"])
            lines.append(
                f"- **{s['id']}**: {s['answers']['form']['choice']} "
                f"({s['answers']['form']['probabilities']})"
            )
    else:
        lines.append("None.")
    lines.append("")
    lines.append(f"## Low confidence (form confidence < {min_confidence})")
    lines.append("")
    if low_conf:
        for s in low_conf:
            lines.append(
                f"- **{s['id']}**: {s['answers']['form']['choice']} "
                f"(confidence={s['answers']['form']['confidence']})"
            )
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", default="build/census/jev_results.jsonl")
    parser.add_argument("--labels", default="tools/census_labels.json")
    parser.add_argument("--out", default="build/census/jev/CENSUS.md")
    parser.add_argument("--margin", type=float, default=0.15)
    parser.add_argument("--min-confidence", type=float, default=0.7)
    args = parser.parse_args(argv)

    subjects = load_results(args.results)
    if not subjects:
        print("jev_report: no results found", file=sys.stderr)
        return 1
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8")) if Path(args.labels).is_file() else {}
    by_id = {s["id"]: s for s in subjects}
    bar = score_against_labels(by_id, labels)

    md = render(subjects, bar, args.margin, args.min_confidence)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    rec = recommend(subjects)
    print(f"c_all = {rec['c_all']:.4f}  rule {rec['rule']}")
    acc = "n/a" if bar["accuracy"] is None else f"{bar['accuracy']:.2f}"
    print(f"accuracy vs. seed labels: {acc} over {bar['total']}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
