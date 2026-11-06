# Installation and operational qualification protocol — speccheck

> **Applies to:** speccheck 1.26.0 and later (`SPEC.md` v1.26, R-111..R-113, C-29, C-30).
> **Output:** `qualification.json` and `QUALIFICATION_REPORT.md`, the record to file and sign.

## 1. Purpose and scope

To show that an installed copy of speccheck is the released one (IQ) and behaves as specified on
this machine (OQ), before first use and after every upgrade (ISO 13485:2016 clause 4.1.6;
`CHANGE_CONTROL.md`). Performance qualification on the manufacturer's own project is out of scope
here (see `TOOL_RISK_ASSESSMENT.md`, last section).

## 2. Prerequisites

- Python 3.12 and `uv`, or any installer that installs a wheel and writes its `RECORD`.
- The release notes of the version being installed, which publish its `package_tree_sha256`.
- No network access is needed by `qualify` itself.

## 3. Installation

Install the released version from a **clean checkout of its tag** (or from the wheel attached to
its release, when there is one):

```bash
git clone --branch v1.26.0 --depth 1 https://github.com/rioffe/speccheck speccheck-1.26.0
uv tool install ./speccheck-1.26.0          # or: uv build --wheel, then install the wheel
```

A wheel built from a working tree that carries untracked files under `src/speccheck/` is not the
release. Dot-paths (editor swap files, a SwiftPM `.build/`) are excluded from the wheel, but any
other stray file is packaged and changes the tree hash. That is the point: IQ then fails.

## 4. Execution

In an empty directory:

```bash
speccheck qualify --out qualification
```

Optionally set `SOURCE_DATE_EPOCH` (seconds since the epoch) to record a time in the record;
without it the record carries none, so two runs are byte-identical.

## 5. Acceptance criteria

All must hold:

1. The command exits `0` and prints
   `qualify: QUALIFIED - IQ <n> files, tree <12 hex>; OQ 5/5 cases`.
2. **IQ:** the record's `package_tree_sha256` equals the value the release notes publish for the
   tag; `record_mismatches`, `record_missing` and `data_faults` are empty.
3. **OQ:** every case OQ-01..OQ-05 is `PASS`. Each case names the tool hazards it challenges
   (`TOOL_RISK_ASSESSMENT.md`).
4. The *Intended use* section of the record is the statement the manufacturer validated against.

`qualify` under `uv run` in a source checkout reports `not an installed wheel (no hashed RECORD)`
and exits `1` by design (E-86): an editable install cannot be qualified.

## 6. Deviations

A failure is named on stdout and in the record (§1 and §3 or §4). Do not edit the record. Record
the deviation in the manufacturer's deviation procedure, resolve it (reinstall from the tag; report
an OQ failure to the supplier with the record attached), and re-run `qualify` into a new
directory.

## 7. The record

`QUALIFICATION_REPORT.md` ends with an empty signature table (*Executed by*, *Reviewed by*). File
both records in the eQMS with the release notes' tree hash, and sign there. speccheck does not
sign or attribute records.

## 8. Known anomalies

The record's §6 lists the known anomalies of the installed version with their workarounds. Review
them against the intended use before release to production use.
