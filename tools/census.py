"""The obligation census (`PROPOSAL_obligation_census.md`): classify every live R/C/I/K/E id of
a spec by what would be cheapest to verify it -- form in {expr, struct, behavior, prose}, checker
in {ast, schema, test, llm} -- before deciding whether a checkable-expression field is worth
adding to the C-01 grammar. No `SPEC.md` version; this is a decision gate, not a change to the
checker (see the proposal's front matter).

Opt-in, outside the kernel, same shape as `tools/eval_judge.py`: one model, `--runs` independent
requests per subject, no retries, an OpenAI-compatible chat-completions endpoint. Two modes:

  uv run python tools/census.py --spec SPEC.md [--runs 3] [--concurrency 8] [--out build/census] [--model M] [--url U]
  uv run python tools/census.py --ratify build/census/census.json     # after a human edits it

Environment variables SPECCHECK_JUDGE_URL / _MODEL / _API_KEY / _TIMEOUT override the defaults --
the same variables `speccheck --judge llm` uses (C-09's pattern), so one `.env` serves both tools.

Outputs (run mode): `<out>/census.json` (every subject's id/family/statement, every run's raw
reply, the consensus, `split`, and an empty `ratified: {}` for a human to fill) and
`<out>/CENSUS.md` (the four sections: Summary with the Part C recommendation, Ratification
queue, Scope findings, the Full table). `--ratify` re-reads a `census.json` a human has edited
(filled in some subjects' `ratified` dict) and rewrites `CENSUS.md` from ratified-else-consensus
values, printing the ratified fraction; it never re-queries the model and never rewrites the JSON.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from speccheck.extract import decode_text, id_sort_key, parse_spec
from speccheck.judge_llm import strip_fence

ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "census_prompt.md"
LABELS_PATH = ROOT / "census_labels.json"

ENV_URL = "SPECCHECK_JUDGE_URL"
ENV_MODEL = "SPECCHECK_JUDGE_MODEL"
ENV_KEY = "SPECCHECK_JUDGE_API_KEY"
ENV_TIMEOUT = "SPECCHECK_JUDGE_TIMEOUT"

FORMS = ("expr", "struct", "behavior", "prose")
CHECKERS = ("ast", "schema", "test", "llm")
CHECKABLE_FORMS = ("expr", "struct")
FAMILIES = ("R", "C", "I", "K", "E")  # T excluded: a method, not an obligation
MAX_TOKENS = 4000  # D-07's lesson: a thinking model truncates a short budget before its answer

UNKNOWN_RECORD: dict[str, Any] = {
    "form": "UNKNOWN",
    "checker": "UNKNOWN",
    "expression": "",
    "scope": {"stated": None, "text": ""},
    "quantities": [],
    "confidence": None,
    "rationale": "",
    "error": None,
}


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def prompt_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------------
# Part A.1 -- subjects
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Subject:
    id: str
    family: str
    statement: str
    verified_by: tuple[str, ...] = ()  # T ids with a "verifies" edge into this id (v1.13, C-12)


def load_subjects(spec_path: Path) -> list[Subject]:
    """extract.parse_spec -> every live id in R/C/I/K/E, each with the T ids that verify it
    (from the spec's own C-12 edges, when the extractor produces them)."""
    data = spec_path.read_bytes()
    text, _replaced = decode_text(data)
    index = parse_spec(text, spec_path.name)
    verifies: dict[str, list[str]] = {}
    for e in getattr(index, "edges", ()):  # tolerate a pre-v1.13 extractor with no edges
        if e.kind == "verifies":
            verifies.setdefault(e.dst, []).append(e.src)
    subjects = []
    for s in index.ids:
        if s.retired or s.family not in FAMILIES:
            continue
        vb = tuple(sorted(set(verifies.get(s.id, ())), key=id_sort_key))
        subjects.append(Subject(s.id, s.family, s.text, vb))
    return subjects


# --------------------------------------------------------------------------------------------
# Part A.2 -- one request per (subject, run)
# --------------------------------------------------------------------------------------------


def _post(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
    import httpx  # lazy: --ratify never needs it

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, content=body, headers=headers)
    return resp.status_code, resp.text


def request_body(model: str, prompt: str, subject: Subject) -> bytes:
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {"id": subject.id, "family": subject.family, "statement": subject.statement},
                    ensure_ascii=False,
                ),
            },
        ],
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def parse_reply(text: str) -> dict[str, Any]:
    """The model's text -> a run record. Any structural problem -> form/checker "UNKNOWN", never
    coerced to a valid answer (the judge's E-15 discipline)."""
    try:
        obj = json.loads(strip_fence(text))
    except (ValueError, TypeError):
        return {**UNKNOWN_RECORD, "error": "non-JSON"}
    if not isinstance(obj, dict):
        return {**UNKNOWN_RECORD, "error": "not an object"}

    raw_form = obj.get("form")
    raw_checker = obj.get("checker")
    error = None
    form = raw_form if raw_form in FORMS else None
    if form is None:
        error = f"bad form: {raw_form!r}"
    checker = raw_checker if raw_checker in CHECKERS else None
    if checker is None:
        error = error or f"bad checker: {raw_checker!r}"

    raw_expr = obj.get("expression")
    expression = raw_expr if isinstance(raw_expr, str) else ""
    scope_stated: bool | None = None
    scope_text = ""
    raw_scope = obj.get("scope")
    if isinstance(raw_scope, dict):
        s = raw_scope.get("stated")
        scope_stated = s if isinstance(s, bool) else None
        t = raw_scope.get("text")
        scope_text = t if isinstance(t, str) else ""
    raw_q = obj.get("quantities")
    quantities = [q for q in raw_q if isinstance(q, str)] if isinstance(raw_q, list) else []
    raw_conf = obj.get("confidence")
    confidence = (
        float(raw_conf) if isinstance(raw_conf, (int, float)) and not isinstance(raw_conf, bool) else None
    )
    raw_rat = obj.get("rationale")
    rationale = raw_rat if isinstance(raw_rat, str) else ""

    return {
        "form": form or "UNKNOWN",
        "checker": checker or "UNKNOWN",
        "expression": expression,
        "scope": {"stated": scope_stated, "text": scope_text},
        "quantities": quantities,
        "confidence": confidence,
        "rationale": rationale,
        "error": error,
    }


def _single_call(subject: Subject, model: str, url: str, api_key: str, timeout: float, prompt: str) -> dict[str, Any]:
    """One request, no retries. Any transport/HTTP/shape problem -> UNKNOWN, never a crash."""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    try:
        status, text = _post(url, headers, request_body(model, prompt, subject), timeout)
    except Exception as exc:  # noqa: BLE001 - transport failure -> UNKNOWN, not a crash
        return {**UNKNOWN_RECORD, "error": f"transport: {exc.__class__.__name__}"}
    if status != 200:
        return {**UNKNOWN_RECORD, "error": f"HTTP {status}"}
    try:
        envelope = json.loads(text)
        content = envelope["choices"][0]["message"]["content"]
    except (ValueError, TypeError, KeyError, IndexError):
        return {**UNKNOWN_RECORD, "error": "missing choices[0].message.content"}
    if not isinstance(content, str):
        return {**UNKNOWN_RECORD, "error": "content is not text"}
    return parse_reply(content)


def run_subject(
    subject: Subject, model: str, url: str, api_key: str, timeout: float, prompt: str, runs: int
) -> list[dict[str, Any]]:
    """Sequential convenience wrapper (used by tests and by --concurrency 1)."""
    return [_single_call(subject, model, url, api_key, timeout, prompt) for _ in range(runs)]


# --------------------------------------------------------------------------------------------
# Part A.3 -- consensus
# --------------------------------------------------------------------------------------------


def consensus_value(records: list[dict[str, Any]], key: str) -> str | None:
    """Unanimous when every non-UNKNOWN run agrees and at least two runs are non-UNKNOWN."""
    values = [r[key] for r in records if r[key] != "UNKNOWN"]
    if len(values) < 2:
        return None
    first = values[0]
    return first if all(v == first for v in values) else None


def scope_majority(records: list[dict[str, Any]]) -> bool | None:
    values = [r["scope"]["stated"] for r in records if r["scope"]["stated"] is not None]
    if not values:
        return None
    true_n = sum(values)
    false_n = len(values) - true_n
    if true_n == false_n:
        return None
    return true_n > false_n


def build_subject_record(subject: Subject, records: list[dict[str, Any]]) -> dict[str, Any]:
    form_consensus = consensus_value(records, "form")
    checker_consensus = consensus_value(records, "checker")
    confidences = [r["confidence"] for r in records if r["confidence"] is not None]
    return {
        "id": subject.id,
        "family": subject.family,
        "statement": subject.statement,
        "statement_sha256": hashlib.sha256(subject.statement.encode("utf-8")).hexdigest(),
        "verified_by": list(subject.verified_by),
        "runs": records,
        "consensus": {
            "form": form_consensus,
            "checker": checker_consensus,
            "scope_stated": scope_majority(records),
        },
        "confidence": statistics.fmean(confidences) if confidences else None,
        # split = form OR checker disagreement; the ratio below falls back to "prose" on form
        # split specifically (§ Part A.3: "a split subject counts as prose"), which is the
        # conservative direction against overcounting `expr`.
        "split": form_consensus is None or checker_consensus is None,
        "ratified": {},
    }


def effective_form(s: dict[str, Any]) -> str:
    ratified = s.get("ratified") or {}
    if ratified.get("form") in FORMS:
        return ratified["form"]
    return s["consensus"]["form"] or "prose"  # form split -> counts as prose until ratified


def effective_checker(s: dict[str, Any]) -> str | None:
    ratified = s.get("ratified") or {}
    if ratified.get("checker") in CHECKERS:
        return ratified["checker"]
    return s["consensus"]["checker"]


def effective_scope_stated(s: dict[str, Any]) -> bool | None:
    ratified = s.get("ratified") or {}
    if isinstance(ratified.get("scope_stated"), bool):
        return ratified["scope_stated"]
    return s["consensus"]["scope_stated"]


def representative_expression(s: dict[str, Any]) -> str:
    form = effective_form(s)
    for r in s["runs"]:
        if r["form"] == form and r["expression"]:
            return r["expression"]
    return ""


# --------------------------------------------------------------------------------------------
# Part C -- the recommendation heuristic
# --------------------------------------------------------------------------------------------


def recommend(subjects: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = {f: [] for f in FAMILIES}
    for s in subjects:
        by_family[s["family"]].append(s)

    def checkable(group: list[dict[str, Any]]) -> int:
        return sum(1 for s in group if effective_form(s) in CHECKABLE_FORMS)

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

    ratified_n = sum(1 for s in subjects if s.get("ratified"))
    ratified_fraction = ratified_n / n_all if n_all else 0.0
    return {
        "n_all": n_all,
        "checkable_all": checkable_all,
        "c_all": c_all,
        "per_family": per_family,
        "rule": rule,
        "families_hit": families_hit,
        "ratified_fraction": ratified_fraction,
        "provisional": ratified_fraction < 0.50,
    }


def scope_findings(subjects: list[dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for s in subjects:
        if effective_scope_stated(s) is not False:
            continue
        texts = [r["scope"]["text"] for r in s["runs"] if r["scope"]["text"]]
        if texts:
            out.append({"id": s["id"], "text": texts[0]})
    return out


def ratification_queue(
    subjects: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pending = [s for s in subjects if not s.get("ratified")]
    split = [s for s in pending if s["split"]]
    low_conf = [
        s for s in pending if not s["split"] and (s["confidence"] is None or s["confidence"] < 0.7)
    ]
    return split, low_conf


# --------------------------------------------------------------------------------------------
# Part B -- the census's own accuracy bar (recorded, not gating)
# --------------------------------------------------------------------------------------------


def score_against_labels(
    subjects_by_id: dict[str, dict[str, Any]], labels: dict[str, Any]
) -> dict[str, Any]:
    total = 0
    correct = 0
    prose_as_expr: list[str] = []
    by_form_count: dict[str, int] = {}
    for ident, label in labels.items():
        s = subjects_by_id.get(ident)
        if s is None:
            continue
        total += 1
        form = effective_form(s)
        by_form_count[label["form"]] = by_form_count.get(label["form"], 0) + 1
        if form == label["form"]:
            correct += 1
        if label["form"] == "prose" and form == "expr":
            prose_as_expr.append(ident)
    accuracy = correct / total if total else None
    enough_labels = total >= 20 and all(n >= 4 for n in by_form_count.values())
    passed = enough_labels and accuracy is not None and accuracy >= 0.75 and not prose_as_expr
    if not enough_labels:
        status = f"insufficient labels ({total} labeled; need >= 20, >= 4 per form, to gate)"
    else:
        status = "PASS" if passed else "FAIL"
    acc_text = "n/a" if accuracy is None else f"{accuracy:.2f}"
    summary = (
        f"census accuracy bar: {status} (accuracy={acc_text} over {total} labels; "
        f"prose-as-expr: {prose_as_expr or 'none'})"
    )
    return {
        "total": total,
        "accuracy": accuracy,
        "prose_as_expr": prose_as_expr,
        "enough_labels": enough_labels,
        "passed": passed,
        "summary": summary,
    }


# --------------------------------------------------------------------------------------------
# CENSUS.md
# --------------------------------------------------------------------------------------------


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_census_md(
    subjects: list[dict[str, Any]],
    model: str | None,
    date: str | None,
    prompt_hash: str | None,
    spec_name: str | None,
    bar: dict[str, Any] | None,
) -> str:
    rec = recommend(subjects)
    lines = ["# Obligation census", ""]
    lines.append(
        f"spec: {spec_name} | model: {model} | date: {date} | prompt_sha256: {prompt_hash}"
    )
    lines.append("")
    if bar is not None and bar["enough_labels"] and not bar["passed"]:
        lines.append(
            f"**The accuracy bar (Part B) was not met** — {bar['summary']}. This table's "
            "classification should not be ratified from without extra scrutiny."
        )
        lines.append("")
    elif bar is not None:
        lines.append(bar["summary"])
        lines.append("")

    lines.append("## 1. Summary")
    lines.append("")
    # 4 decimals: a c_all of e.g. 0.4962 must never render as the self-contradictory "0.50 < 0.50"
    rule_text = {
        1: f"**Rule 1 — EXPRESSION FIELD, ALL FAMILIES** (c_all = {rec['c_all']:.4f} >= 0.50)",
        2: (
            f"**Rule 2 — EXPRESSION FIELD, FAMILIES {{{', '.join(rec['families_hit'])}}} ONLY** "
            f"(c_all = {rec['c_all']:.4f} < 0.50; "
            f"{', '.join(rec['families_hit'])} clear 0.75 at N >= 5)"
        ),
        3: f"**Rule 3 — NO EXPRESSION LANGUAGE** (c_all = {rec['c_all']:.4f}; no family clears its bar)",
    }[rec["rule"]]
    if rec["provisional"]:
        rule_text += f"  — **PROVISIONAL** (ratified fraction {rec['ratified_fraction']:.2f} < 0.50)"
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

    lines.append("## 2. Ratification queue")
    lines.append("")
    split_q, low_q = ratification_queue(subjects)
    if not split_q and not low_q:
        lines.append("None.")
    else:
        if split_q:
            lines.append("### Split (form or checker disagreement)")
            lines.append("")
            for s in split_q:
                lines.append(
                    f"**{s['id']}** ({s['family']}) — consensus form: "
                    f"{s['consensus']['form'] or 'split'}, checker: "
                    f"{s['consensus']['checker'] or 'split'}"
                )
                lines.append("")
                lines.append(f"> {_cell(s['statement'][:400])}")
                lines.append("")
                for i, r in enumerate(s["runs"], 1):
                    conf = "n/a" if r["confidence"] is None else f"{r['confidence']:.2f}"
                    lines.append(
                        f"- run {i}: form={r['form']} checker={r['checker']} conf={conf} — "
                        f"{_cell(r['rationale'])}"
                    )
                lines.append("")
        if low_q:
            lines.append("### Low confidence (mean < 0.7)")
            lines.append("")
            for s in low_q:
                conf = "n/a" if s["confidence"] is None else f"{s['confidence']:.2f}"
                lines.append(
                    f"- **{s['id']}** ({s['family']}) — form: {effective_form(s)}, "
                    f"mean confidence: {conf}"
                )
            lines.append("")

    lines.append("## 3. Scope findings")
    lines.append("")
    findings = scope_findings(subjects)
    if findings:
        for f in findings:
            lines.append(f"- **{f['id']}**: {_cell(f['text'])}")
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## 4. Full table")
    lines.append("")
    lines.append("| id | form | checker | expression | scope | confidence | verified by | split |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for s in sorted(subjects, key=lambda s: id_sort_key(s["id"])):
        form = effective_form(s)
        checker = effective_checker(s) or "n/a"
        expr = representative_expression(s)
        stated = effective_scope_stated(s)
        scope_text = "yes" if stated else ("no" if stated is False else "n/a")
        conf = "n/a" if s["confidence"] is None else f"{s['confidence']:.2f}"
        verified_by = ", ".join(s.get("verified_by") or []) or (
            "NONE" if form in CHECKABLE_FORMS else ""
        )
        split_text = "yes" if s["split"] else ""
        lines.append(
            f"| {s['id']} | {form} | {checker} | {_cell(expr)} | {scope_text} | {conf} | "
            f"{verified_by} | {split_text} |"
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------


def do_run(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec)
    subjects = load_subjects(spec_path)
    if not subjects:
        print("census: no live R/C/I/K/E ids found", file=sys.stderr)
        return 1
    prompt = load_prompt()
    phash = prompt_sha256(prompt)
    date = dt.date.today().isoformat()
    total_calls = len(subjects) * args.runs
    print(
        f"model: {args.model}  url: {args.url}  date: {date}  subjects: {len(subjects)}  "
        f"runs: {args.runs}  concurrency: {args.concurrency}  requests: {total_calls}"
    )

    tasks = [(subject, run_i) for subject in subjects for run_i in range(args.runs)]
    results: dict[tuple[str, int], dict[str, Any]] = {}
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        futures = {
            pool.submit(
                _single_call, subject, args.model, args.url, args.api_key, args.timeout, prompt
            ): (subject.id, run_i)
            for subject, run_i in tasks
        }
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()
            done += 1
            print(f"\r  {done}/{total_calls} requests", end="", flush=True)
    print()

    subject_records = []
    for subject in subjects:
        records = [results[(subject.id, run_i)] for run_i in range(args.runs)]
        rec = build_subject_record(subject, records)
        subject_records.append(rec)
        print(f"  {subject.id}: form={rec['consensus']['form'] or 'split'} split={rec['split']}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    census_doc = {
        "model": args.model,
        "date": date,
        "prompt_sha256": phash,
        "spec": str(spec_path),
        "subjects": subject_records,
    }
    (out_dir / "census.json").write_text(
        json.dumps(census_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    labels: dict[str, Any] = {}
    labels_path = Path(args.labels)
    if labels_path.is_file():
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
    subjects_by_id = {s["id"]: s for s in subject_records}
    bar = score_against_labels(subjects_by_id, labels) if labels else None
    if bar:
        print(bar["summary"])

    md = render_census_md(subject_records, args.model, date, phash, str(spec_path), bar)
    (out_dir / "CENSUS.md").write_text(md, encoding="utf-8")

    rec = recommend(subject_records)
    print(f"recommendation: rule {rec['rule']} ({'PROVISIONAL' if rec['provisional'] else 'final'})")
    print(f"wrote {out_dir / 'census.json'} and {out_dir / 'CENSUS.md'}")
    return 0


def do_ratify(census_path: Path, labels_path: Path) -> int:
    doc = json.loads(census_path.read_text(encoding="utf-8"))
    subjects = doc["subjects"]
    labels: dict[str, Any] = {}
    if labels_path.is_file():
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
    subjects_by_id = {s["id"]: s for s in subjects}
    bar = score_against_labels(subjects_by_id, labels) if labels else None
    md = render_census_md(
        subjects, doc.get("model"), doc.get("date"), doc.get("prompt_sha256"), doc.get("spec"), bar
    )
    out_md = census_path.parent / "CENSUS.md"
    out_md.write_text(md, encoding="utf-8")
    n = len(subjects)
    ratified_n = sum(1 for s in subjects if s.get("ratified"))
    print(f"ratified: {ratified_n}/{n} ({(ratified_n / n if n else 0.0):.2f})")
    if bar:
        print(bar["summary"])
    rec = recommend(subjects)
    print(f"recommendation: rule {rec['rule']} ({'PROVISIONAL' if rec['provisional'] else 'final'})")
    print(f"wrote {out_md}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--spec", default="SPEC.md")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--out", default="build/census")
    parser.add_argument("--model", default=os.environ.get(ENV_MODEL, "qwen3:8b"))
    parser.add_argument(
        "--url", default=os.environ.get(ENV_URL, "http://localhost:11434/v1/chat/completions")
    )
    parser.add_argument("--api-key", default=os.environ.get(ENV_KEY, "ollama"))
    parser.add_argument(
        "--timeout", type=int, default=int(os.environ.get(ENV_TIMEOUT, "120"))
    )
    parser.add_argument(
        "--ratify",
        metavar="CENSUS_JSON",
        default=None,
        help="recompute CENSUS.md from a hand-ratified census.json; does not re-query the model",
    )
    parser.add_argument("--labels", default=str(LABELS_PATH))
    args = parser.parse_args(argv)

    if args.ratify:
        return do_ratify(Path(args.ratify), Path(args.labels))
    return do_run(args)


if __name__ == "__main__":
    sys.exit(main())
