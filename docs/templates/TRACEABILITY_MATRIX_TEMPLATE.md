# Software traceability matrix — <Software item name> <version>

<!--
Traceability record (IEC 62304 5.1.1 c, 5.7.4, 7.3.3; ISO 13485 7.3.2, 7.3.6). Every row comes
from ONE speccheck run, identified in §1, so the matrix and the verification report cite the same
evidence. Generate §3 and §4 with the script in §6; fill §1, §2 and §5 by hand. Replace every <...>
and delete these comments.
-->

| Field | Value |
| --- | --- |
| Document | <document id, revision> |
| Software item, version | <name> <version or commit> |
| Software safety class | <A / B / C> (from SPEC.md front matter) |
| Specification | `SPEC.md` <version>, sha256 `<from the manifest's inputs, role spec>` |
| Risk file | `<risk.json>`, sha256 `<from the manifest's inputs, role risk_file>`, exported from `<ISO 14971 file id, revision>` |

## 1. The run this matrix is drawn from

| Field | Value |
| --- | --- |
| Command | `speccheck check --spec SPEC.md --src <src> --tests <tests> --results junit.xml --judge mock --strict --risk-file <risk.json> --manifest --out <dir>` |
| speccheck version | <`tool.version` in `speccheck.manifest.json`> |
| Inputs tree hash | `<tree_sha256 from speccheck.manifest.json>` |
| Summary line | `<the one stdout line, verbatim>` |
| Exit code | `<0>` |
| `verify` before signing | `<the line speccheck verify --manifest <dir>/speccheck.manifest.json printed>` |
| Tool qualification record | `<QUALIFICATION_REPORT.md reference: speccheck qualify on the machine that ran the check>` |

## 2. System requirements and user needs → software requirements

<!-- By hand, from SPEC.md §1.1 and the Source column of §2: every system requirement allocated to
this software item, and every user need, lists the software requirements that implement it.
A system requirement with no software requirement is a gap to resolve, not to delete. -->

| System requirement / user need | Software requirements |
| --- | --- |
| SYS-<nn> | R-<nn>, R-<nn> |
| UN-<nn> | R-<nn> |

## 3. Software requirements → implementation → verification

<!-- Generated (§6). One row per declared, non-retired id. Status is speccheck's: PASSING means a
test citing the id ran and passed; anything else is a gap the verification report must address. -->

| Id | Requirement (title) | Controls hazards | Realized in | Verified by (test: outcome) | Status |
| --- | --- | --- | --- | --- | --- |
| R-01 | <title> | — | `<file>` | `<test file>::<test name>`: passed | PASSING |
| R-02 | <title> | HAZ-<nnn> | `<file>` | `<test file>::<test name>`: passed | PASSING |

## 4. Hazards → risk control measures → verification (62304 7.3)

<!-- Generated (§6). One row per hazard in the risk file or named by a CONTROLS marker. VERIFIED:
every non-retired control is PASSING. NOT_VERIFIED: one is not. UNCONTROLLED: none exists, which
fails --strict. Acceptability of the residual risk is decided in the ISO 14971 file. -->

| Hazard | Title | Risk control measures (status) | Hazard status |
| --- | --- | --- | --- |
| HAZ-<nnn> | <title from the risk file> | R-<nn> (PASSING) | VERIFIED |

## 5. Gaps and their disposition

<!-- Every id in §3 that is not PASSING and every hazard in §4 that is not VERIFIED, with what was
decided. A release with an open gap needs the disposition approved in the verification report. -->

| Item | Gap | Disposition | Approved by |
| --- | --- | --- | --- |
| <id or hazard> | <status and reason> | <fixed in / deferred with rationale / accepted with rationale> | <role, date> |

## 6. Generating §3 and §4

From the run's `<dir>/speccheck.json` (C-07 fields: `ids[].id`, `title`, `controls`, `status`,
`src[].file`, `tests[].file`, `tests[].name`, `tests[].outcome`; `hazards[].id`, `title`,
`controls`, `status`):

```python
import json, sys

doc = json.load(open(sys.argv[1], encoding="utf-8"))
status = {r["id"]: r["status"] for r in doc["ids"]}
cell = lambda s: " ".join(str(s).split()).replace("|", "\\|")

print("| Id | Requirement (title) | Controls hazards | Realized in | Verified by (test: outcome) | Status |")
print("| --- | --- | --- | --- | --- | --- |")
for r in doc["ids"]:
    if r["status"] == "RETIRED":
        continue
    src = ", ".join(sorted({f"`{s['file']}`" for s in r["src"]})) or "—"
    tests = "; ".join(
        f"`{t['file']}::{t['name'] or '(file)'}`: {t['outcome'] or 'not run'}" for t in r["tests"]
    ) or "—"
    print(f"| {r['id']} | {cell(r['title'])} | {', '.join(r.get('controls', [])) or '—'} | "
          f"{src} | {tests} | {r['status']} |")

print()
print("| Hazard | Title | Risk control measures (status) | Hazard status |")
print("| --- | --- | --- | --- |")
for h in doc.get("hazards", []):
    controls = ", ".join(f"{c} ({status[c]})" for c in h["controls"]) or "—"
    print(f"| {h['id']} | {cell(h['title'] or '—')} | {controls} | {h['status']} |")
```

Run it as `python matrix.py <dir>/speccheck.json > matrix-rows.md` and paste the two tables into
§3 and §4. The rows carry nothing the report does not: a reviewer can check any row against
`<dir>/SPEC_CONFORMANCE_REPORT.md` §3 and §10.

## 7. Approval

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Prepared by |  |  |  |
| Reviewed by |  |  |  |
| Approved by |  |  |  |
