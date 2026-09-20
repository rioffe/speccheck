"""Reporter: the JSON (C-07) and Markdown (C-08) reports, the exit-code rule (§5.4), the summary
line (§5.1), and the only file writer in the program (§3.1 temp-and-rename; I-001, E-18).

Spec IDs realized here (§11): R-12, R-13, R-16, R-19, R-20, R-24, R-28, R-34, R-35, C-07, C-08,
    I-001, I-002, I-003, I-009, K-08, K-09, E-07, E-13, E-18, E-34, E-37, E-38.
"""

from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .attribute import Citation
from .extract import FAMILY_ORDER, Decision, Edge
from .graph import IN_SCOPE_STATUSES, Graph, Metrics, TestEdge, compute_metrics
from .results import RawResult

SCHEMA_VERSION = (
    "1.5"  # C-07: "1.0"-v1.6; "1.1" `title` (v1.7); "1.2" `clause` (v1.9); "1.3" `recorded`
    # (v1.10); "1.4" `decisions`/`edges` (v1.13); "1.5" `declared`/`declared_ratio` (v1.14)
)
JSON_NAME = "speccheck.json"
MD_NAME = "SPEC_CONFORMANCE_REPORT.md"
IMPACT_JSON_NAME = "impact.json"  # C-13; v1.13
IMPACT_MD_NAME = "IMPACT_REPORT.md"  # C-13; v1.13
IMPACT_SCHEMA_VERSION = "1.0"  # C-13; v1.13
EM_DASH = "\u2014"

_NUM_SENTINEL = "\x00NUM:"
_NUM_RE = re.compile(r'"\\u0000NUM:(-?[0-9]+\.[0-9]{4})\\u0000"')


class OutError(Exception):
    """E-18 -> exit 3; message `out: <reason>`."""


class _Num:
    """A Decimal that json.dumps emits as a bare number with exactly four decimals (Q-009)."""

    def __init__(self, value: Decimal) -> None:
        self.text = f"{value:.4f}"


def _num(value: Decimal | None) -> _Num | None:
    return None if value is None else _Num(value)


def dumps(obj: object) -> str:
    """K-09: indent=2, ensure_ascii=False, C-07 key order (insertion order), trailing newline."""

    def default(o: object) -> object:
        if isinstance(o, _Num):
            return f"{_NUM_SENTINEL}{o.text}\x00"
        raise TypeError(f"not serializable: {type(o).__name__}")

    text = json.dumps(obj, indent=2, ensure_ascii=False, default=default)
    return _NUM_RE.sub(r"\1", text) + "\n"


# --------------------------------------------------------------------------------------------
# §5.4 exit code and §5.1 summary line, both pure functions of the JSON report (I-009)
# --------------------------------------------------------------------------------------------


def strict_judge_failure(report: dict) -> str | None:
    """R-28 / E-32: only under --strict --judge llm; `unavailable` takes precedence (Q-004)."""
    if not report["strict"] or report["judge"] != "llm":
        return None
    if report["judge_available"] is False:
        return "unavailable"
    rate = report["metrics"].get("unknown_rate")
    if rate is not None and Decimal(rate.text) > Decimal(report["max_unknown"].text):
        return "unknown_rate"
    return None


def exit_code_for(report: dict) -> int:
    """§5.4: 0 iff no FAILING (and not all-UNCITED, E-19) and, with --strict, everything
    PASSING, no dangling/stale, and R-28 satisfied."""
    by_status = report["metrics"]["by_status"]
    if by_status["FAILING"] > 0:
        return 1
    if by_status["UNCITED"] == report["metrics"]["in_scope"]:
        return 1  # E-19: no evidence at all is not conformance
    if report["strict"]:
        if report["metrics"]["in_scope"] != by_status["PASSING"]:
            return 1
        if report["dangling"] or report["stale"]:
            return 1
        if report["strict_judge_failure"] is not None:
            return 1
    return 0


def summary_line(report: dict) -> str:
    """§5.1, ASCII only, no trailing newline (the caller appends exactly one)."""
    m = report["metrics"]
    s = m["by_status"]
    status = "CONFORMING" if report["exit_code"] == 0 else "NOT CONFORMING"
    conformance = Decimal(m["conformance"].text)
    pct = (conformance * 100).quantize(Decimal("0.1"))
    suffix = ""
    failure = report["strict_judge_failure"]
    if failure == "unavailable":
        suffix = " (unavailable)"
    elif failure == "unknown_rate":
        suffix = (
            f" (unknown_rate {m['unknown_rate'].text} > max_unknown {report['max_unknown'].text})"
        )
    return (
        f"speccheck: {status} - {s['PASSING']}/{m['in_scope']} passing ({pct}%), "
        f"{s['FAILING']} failing, {s['SKIPPED']} skipped, {s['WEAKLY_PASSING']} weak, "
        f"{s['UNVERIFIED']} unverified, {s['UNTESTED']} untested, {s['UNCITED']} uncited; "
        f"{len(report['dangling'])} dangling, {len(report['stale'])} stale; "
        f"judge={report['judge']}{suffix}"
    )


# --------------------------------------------------------------------------------------------
# C-07 JSON
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ReportInputs:
    spec_path: str
    judge: str  # none | mock | llm
    judge_available: bool | None
    judge_prompt_sha256: str | None
    strict: bool
    max_unknown: Decimal
    graph: Graph
    unattributed: list[RawResult]
    notes: list[str]
    decisions: tuple[Decision, ...] = ()  # v1.13, C-12
    edges: tuple[Edge, ...] = ()  # v1.13, C-12


def _edge_json(edge: TestEdge) -> dict:
    verdict = None
    if edge.verdict is not None:
        verdict = {
            "verdict": edge.verdict.verdict,
            "clause": edge.verdict.clause,  # C-07 / R-34: the LOCATED excerpt, "" per E-49
            "evidence": [{"file": e.file, "line": e.line} for e in edge.verdict.evidence],
            "rationale": edge.verdict.rationale,
            "coerced": edge.verdict.coerced,
        }
    return {
        "file": edge.case.file,
        "name": edge.case.name,
        "classname": edge.case.classname,
        "lines": list(edge.lines),
        "declared": edge.declared,  # C-16 / C-14 (v1.14): DECLARED vs INCIDENTAL for this edge
        "outcome": edge.outcome,
        "results": [{"name": r.name, "param": r.param, "outcome": r.outcome} for r in edge.results],
        "verdict": verdict,
    }


def _citation_json(c: Citation) -> dict:
    return {"id": c.id, "file": c.file, "line": c.line}


def build_report(inputs: ReportInputs) -> tuple[dict, Metrics]:
    """The C-07 object with `exit_code` filled in; ratios are `_Num` until `dumps`."""
    metrics = compute_metrics(inputs.graph)
    report: dict = {
        "schema_version": SCHEMA_VERSION,
        "spec": inputs.spec_path,
        "judge": inputs.judge,
        "judge_available": inputs.judge_available,
    }
    if inputs.judge == "llm":
        report["judge_prompt_sha256"] = inputs.judge_prompt_sha256
    report["strict"] = inputs.strict
    report["max_unknown"] = _Num(inputs.max_unknown)
    report["strict_judge_failure"] = None
    report["ids"] = [
        {
            "id": rec.id,
            "family": rec.spec.family,
            "recorded": rec.spec.recorded,  # C-07 / R-35
            "title": rec.spec.title,  # C-07 / R-33: heading text or table cell (C-08 renders it)
            "statement": rec.spec.text,  # the full statement: title + section body for a heading
            "line": rec.spec.line,
            "status": rec.status,
            "src": [{"file": f, "lines": list(lines)} for f, lines in rec.src],
            "tests": [_edge_json(e) for e in rec.tests],
            "unrun": [{"file": e.case.file, "name": e.case.name} for e in rec.unrun],
        }
        for rec in inputs.graph.records
    ]
    report["decisions"] = [
        {"id": d.id, "line": d.line, "affects": list(d.affects)} for d in inputs.decisions
    ]
    report["edges"] = [
        {"src": e.src, "kind": e.kind, "dst": e.dst, "retired": e.retired} for e in inputs.edges
    ]
    report["dangling"] = [_citation_json(c) for c in inputs.graph.dangling]
    report["stale"] = [_citation_json(c) for c in inputs.graph.stale]
    report["unattributed_results"] = [
        {"classname": r.classname, "name": r.name, "outcome": r.outcome}
        for r in inputs.unattributed
    ]
    report["notes"] = sorted(inputs.notes)
    m: dict = {
        "declared": metrics.declared,
        "retired": metrics.retired,
        "in_scope": metrics.in_scope,
        "by_status": {s: metrics.by_status[s] for s in IN_SCOPE_STATUSES},
        "conformance_ratio": f"{metrics.passing}/{metrics.in_scope}",
        "conformance": _num(metrics.conformance),
        "by_family": {
            f: {
                "in_scope": metrics.by_family[f]["in_scope"],
                "passing": metrics.by_family[f]["passing"],
                "ratio": _num(metrics.by_family[f]["ratio"]),
            }
            for f in FAMILY_ORDER
        },
    }
    if inputs.graph.judge_enabled:
        m["judge_strength_ratio"] = metrics.judge_strength_ratio
        m["judge_strength"] = _num(metrics.judge_strength)
        m["unknown_rate"] = _num(metrics.unknown_rate)
    m["declared_ratio"] = _num(metrics.declared_ratio)  # C-16: present under every --judge mode
    report["metrics"] = m
    report["strict_judge_failure"] = strict_judge_failure(report)
    report["exit_code"] = exit_code_for(report)
    return report, metrics


# --------------------------------------------------------------------------------------------
# C-08 Markdown
# --------------------------------------------------------------------------------------------


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _ratio_text(value: _Num | None) -> str:
    return "n/a" if value is None else value.text


def _case_label(name: str) -> str:
    return "(file)" if name == "" else name


def _verdict_text(verdict: dict | None) -> str:
    if verdict is None:
        return EM_DASH
    if verdict["verdict"] == "UNKNOWN" and verdict["coerced"]:
        return "UNKNOWN(coerced)"
    return verdict["verdict"]


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(" --- " for _ in header) + "|"]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return lines


def render_markdown(report: dict) -> str:
    """C-08: nine sections in a fixed order; every declared ID exactly once in §3 (I-003)."""
    m = report["metrics"]
    judge = report["judge"]
    if judge == "none":
        judge_text = "none"
    else:
        judge_text = f"{judge} ({'available' if report['judge_available'] else 'unavailable'})"
    out: list[str] = [
        "# Specification Conformance Report",
        "",
        f"**Spec:** `{report['spec']}` \u00b7 **Judge:** {judge_text} \u00b7 "
        f"**Strict:** {'on' if report['strict'] else 'off'}",
        "",
        "## 1. Verdict",
        "",
        summary_line(report),
        "",
        "## 2. Metrics",
        "",
    ]
    metric_rows = [
        ["Declared", str(m["declared"])],
        ["Retired", str(m["retired"])],
        ["In scope", str(m["in_scope"])],
        ["Conformance", f"{m['conformance_ratio']} ({_ratio_text(m['conformance'])})"],
    ]
    metric_rows += [[s, str(m["by_status"][s])] for s in IN_SCOPE_STATUSES]
    if "judge_strength" in m:
        metric_rows.append(
            ["Judge strength", f"{m['judge_strength_ratio']} ({_ratio_text(m['judge_strength'])})"]
        )
        metric_rows.append(["Unknown rate", _ratio_text(m["unknown_rate"])])
    out += _table(["Metric", "Value"], metric_rows)
    out.append("")
    out += _table(
        ["Family", "In scope", "Passing", "Ratio"],
        [
            [f, str(v["in_scope"]), str(v["passing"]), _ratio_text(v["ratio"])]
            for f, v in m["by_family"].items()
        ],
    )
    out += ["", "## 3. Per-ID evidence", ""]
    rows = []
    for rec in report["ids"]:
        ident = f"~~{rec['id']}~~" if rec["status"] == "RETIRED" else rec["id"]
        if rec["recorded"]:
            ident += " (recorded)"  # C-08 / R-35: strike the id, then the label
        src = ", ".join(f"{s['file']}:{ln}" for s in rec["src"] for ln in s["lines"]) or EM_DASH
        tests = []
        for t in rec["tests"]:
            cites = ", ".join(f"{t['file']}:{ln}" for ln in t["lines"])
            outcome = t["outcome"] or "unrun"
            tests.append(
                f"`{_case_label(t['name'])}` {cites} "
                f"({outcome} \u00b7 {_verdict_text(t['verdict'])})"
            )
        # C-08: the Statement cell renders `title`, never a section body (R-33)
        rows.append([ident, rec["status"], rec["title"], src, "; ".join(tests) or EM_DASH])
    out += _table(
        [
            "ID",
            "Status",
            "Statement",
            "Source citations",
            "Test citations (outcome \u00b7 verdict)",
        ],
        rows,
    )

    def section(title: str, header: list[str], rows: list[list[str]]) -> None:
        out.extend(["", title, ""])
        if rows:
            out.extend(_table(header, rows))
        else:
            out.append("None.")

    section(
        "## 4. Dangling citations",
        ["ID", "File", "Line"],
        [[d["id"], d["file"], str(d["line"])] for d in report["dangling"]],
    )
    section(
        "## 5. Stale citations",
        ["ID", "File", "Line"],
        [[d["id"], d["file"], str(d["line"])] for d in report["stale"]],
    )
    section(
        "## 6. Unattributed results",
        ["Classname", "Name", "Outcome"],
        [[u["classname"], u["name"], u["outcome"]] for u in report["unattributed_results"]],
    )
    section(
        "## 7. Unrun test citations",
        ["ID", "File", "Name"],
        [
            [rec["id"], u["file"], _case_label(u["name"])]
            for rec in report["ids"]
            for u in rec["unrun"]
        ],
    )
    if judge != "none":
        judged = []
        for rec in report["ids"]:
            for t in rec["tests"]:
                v = t["verdict"]
                if v is None:
                    continue
                evidence = ", ".join(f"{e['file']}:{e['line']}" for e in v["evidence"]) or EM_DASH
                # C-08: the clause tail-truncated to 80 characters, em dash when "" (R-34)
                clause = v["clause"]
                clause = (clause[:79] + "\u2026") if len(clause) > 80 else (clause or EM_DASH)
                judged.append(
                    [
                        rec["id"],
                        f"{t['file']} `{_case_label(t['name'])}`",
                        _verdict_text(v),
                        clause,
                        evidence,
                        v["rationale"],
                    ]
                )
        section(
            "## 8. Judge details",
            ["ID", "Test", "Verdict", "Clause", "Evidence", "Rationale"],
            judged,
        )
    out.extend(["", "## 9. Notes", ""])
    if report["notes"]:
        out.extend(f"- {_cell(n)}" for n in report["notes"])
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------------------------
# §3.1 the only writer
# --------------------------------------------------------------------------------------------


def _make_nonce() -> str:
    return secrets.token_hex(4)


def _replace(src: Path, dst: Path) -> None:
    os.replace(src, dst)


def _leftover_temporaries(out_dir: Path, names: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    prefixes = tuple(f".{name}." for name in names)
    try:
        for entry in os.scandir(out_dir):
            name = entry.name
            if (
                name.endswith(".tmp")
                and name.startswith(prefixes)
                and entry.is_file(follow_symlinks=False)
            ):
                found.append(Path(entry.path))
    except OSError:
        pass
    return sorted(found)


def write_named_files(out_dir: Path, files: list[tuple[str, str]]) -> None:
    """§3.1 (extended by v1.13, C-13): all of `files` or none, in the given order (JSON before
    Markdown, for either subcommand's pair): delete leftovers for exactly these names, write
    temporaries, rename in order; on any failure remove every temporary and anything already
    renamed, raise OutError."""
    names = tuple(name for name, _text in files)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OutError(f"out: cannot create {out_dir.name}: {exc.strerror or exc}") from None
    for leftover in _leftover_temporaries(out_dir, names):
        try:
            leftover.unlink()
        except OSError:
            pass
    nonce = _make_nonce()
    temporaries = [(out_dir / f".{name}.{nonce}.tmp", out_dir / name, text) for name, text in files]
    renamed: list[Path] = []
    try:
        for tmp, _final, text in temporaries:
            tmp.write_bytes(text.encode("utf-8"))
        for tmp, final, _text in temporaries:
            _replace(tmp, final)
            renamed.append(final)
    except BaseException as exc:  # E-18 for OSError; E-41 (interrupt) cleans up the same way
        for tmp, _final, _text in temporaries:
            try:
                tmp.unlink()
            except OSError:
                pass
        for path in renamed:
            try:
                path.unlink()
            except OSError:
                pass
        if isinstance(exc, OSError):
            raise OutError(f"out: {exc.strerror or exc}") from None
        raise


def write_reports(out_dir: Path, json_text: str, md_text: str) -> None:
    """`check`'s pair (§3.1): both reports or neither, JSON renamed before Markdown."""
    write_named_files(out_dir, [(JSON_NAME, json_text), (MD_NAME, md_text)])


# --------------------------------------------------------------------------------------------
# C-13 `impact.json` / `IMPACT_REPORT.md` (v1.13)
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ImpactInputs:
    spec_path: str
    against_path: str | None
    depth: int  # 0 = unbounded, as given
    changed: tuple  # ChangedEntry, in id order
    impact: tuple  # ImpactEntry, sorted (depth, id order)
    reverify: tuple  # ReverifyEntry, in id order
    recite: list  # [{"id", "file", "lines"}], in (id order, file) order
    test_cases: list  # [{"file", "name", "classname", "ids"}], in (file, start) order
    notes: list


def build_impact_report(inputs: ImpactInputs) -> dict:
    """C-13: the impact.json object, key order as pinned."""
    return {
        "schema_version": IMPACT_SCHEMA_VERSION,
        "spec": inputs.spec_path,
        "against": inputs.against_path,
        "depth": inputs.depth,
        "changed": [
            {
                "id": c.id,
                "family": c.family,
                "line": c.line,
                "retired": c.retired,
                "reason": c.reason,
            }
            for c in inputs.changed
        ],
        "impact": [
            {
                "id": e.id,
                "depth": e.depth,
                "retired": e.retired,
                "via": {"src": e.via.src, "kind": e.via.kind, "dst": e.via.dst},
            }
            for e in inputs.impact
        ],
        "reverify": [
            {"id": r.id, "retired": r.retired, "verifies": list(r.verifies)}
            for r in inputs.reverify
        ],
        "recite": inputs.recite,
        "test_cases": inputs.test_cases,
        "notes": sorted(inputs.notes),
    }


def _impact_id_cell(ident: str, retired: bool) -> str:
    return f"~~{ident}~~" if retired else ident


def _impact_scope_line(report: dict) -> str:
    if report["against"] is not None:
        scope = f"against `{report['against']}`"
    else:
        scope = "changed by `--changed`"
    depth = "depth unbounded" if report["depth"] == 0 else f"depth {report['depth']}"
    return f"{report['spec']} · {scope} · {depth}"


def render_impact_markdown(report: dict, *, src_given: bool, tests_given: bool) -> str:
    """C-13: the five sections, every one present, "None." when empty. `src_given`/
    `tests_given` say whether that scan ran at all (distinct from it finding nothing)."""
    lines = ["# Impact Report", "", _impact_scope_line(report), ""]

    lines.append("## 1. Changed")
    lines.append("")
    if report["changed"]:
        rows = [
            [_impact_id_cell(c["id"], c["retired"]), str(c["line"]), c["reason"]]
            for c in report["changed"]
        ]
        lines += _table(["ID", "Line", "Reason"], rows)
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## 2. Impact")
    lines.append("")
    if report["impact"]:
        rows = [
            [
                _impact_id_cell(e["id"], e["retired"]),
                str(e["depth"]),
                f"{e['via']['src']} -{e['via']['kind']}-> {e['via']['dst']}",
            ]
            for e in report["impact"]
        ]
        lines += _table(["ID", "Depth", "Via"], rows)
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## 3. Re-verify")
    lines.append("")
    if report["reverify"]:
        rows = [
            [_impact_id_cell(r["id"], r["retired"]), ", ".join(r["verifies"]) or EM_DASH]
            for r in report["reverify"]
        ]
        lines += _table(["T id", "Verifies"], rows)
    else:
        lines.append("None.")
    if tests_given:
        lines.append("")
        if report["test_cases"]:
            rows = [
                [c["file"], _case_label(c["name"]), ", ".join(c["ids"])]
                for c in report["test_cases"]
            ]
            lines += _table(["File", "Case", "IDs"], rows)
        else:
            lines.append("None.")
    lines.append("")

    lines.append("## 4. Re-cite")
    lines.append("")
    if not src_given:
        lines.append("Not scanned.")
    elif report["recite"]:
        rows = [
            [_r["id"], _r["file"], ", ".join(str(n) for n in _r["lines"])]
            for _r in report["recite"]
        ]
        lines += _table(["ID", "File", "Lines"], rows)
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## 5. Notes")
    lines.append("")
    if report["notes"]:
        lines += [f"- {n}" for n in report["notes"]]
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def impact_summary_line(report: dict) -> str:
    """§5.1 (C-13), one physical line, ASCII, no trailing newline."""
    depth = "unbounded" if report["depth"] == 0 else f"depth {report['depth']}"
    return (
        f"speccheck impact: {len(report['changed'])} changed, "
        f"{len(report['impact'])} impacted ({depth}), "
        f"{len(report['reverify'])} to re-verify, "
        f"{len(report['recite'])} citations, {len(report['test_cases'])} test cases"
    )


def write_impact_reports(out_dir: Path, json_text: str, md_text: str) -> None:
    """`impact`'s pair (§3.1): both reports or neither, JSON renamed before Markdown."""
    write_named_files(out_dir, [(IMPACT_JSON_NAME, json_text), (IMPACT_MD_NAME, md_text)])
