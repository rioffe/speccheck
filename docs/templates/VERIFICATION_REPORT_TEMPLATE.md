# Software verification report — <Software item name> <version>

<!--
Software system test record and verification report (IEC 62304 5.7.5, 5.8.1, 5.8.2; ISO 13485
7.3.6, 4.2.5). It records ONE verification run and the review of it; the traceability matrix
(TRACEABILITY_MATRIX_TEMPLATE.md) is drawn from the same run. Replace every <...> and delete these
comments.
-->

| Field | Value |
| --- | --- |
| Document | <document id, revision> |
| Software item, version | <name> <version>; source revision `<git commit>` |
| Software safety class | <A / B / C> |
| Specification verified against | `SPEC.md` <version> (`<document id>`) |
| Verification plan | `<plan reference>`; acceptance criteria: SPEC.md §9.2 |

## 1. Scope

<What was verified: the software item and version; which test levels (unit, integration, system);
what was not verified here and where it is (for example, hardware-in-the-loop tests in
`<document>`).>

## 2. Configuration identification (62304 5.7.5, 8.1)

| Item | Identification |
| --- | --- |
| Source | `<repository>` at `<commit>` (tag `<tag>`) |
| Inputs of the verification run | `tree_sha256` `<from speccheck.manifest.json>` over `<n>` files |
| Test results | `junit.xml`, sha256 `<from the manifest's inputs, role results>`, produced by `<test command>` on `<CI job id or machine>` at `<time>` |
| Test environment | <OS, runtime, hardware, simulators, with versions> |
| SOUP | as listed in SPEC.md §10.1 at this version |
| Verification tool | speccheck `<version>`; qualification record `<QUALIFICATION_REPORT.md reference>`, verdict `QUALIFIED`, package tree `<12 hex>` |

## 3. Procedure

1. Run the test suite: `<test command>` → `junit.xml`.
2. Run the conformance check in the validated function (`docs/validation/INTENDED_USE.md` in the
   speccheck distribution):

   ```bash
   speccheck check --spec SPEC.md --src <src> --tests <tests> --results junit.xml \
       --judge mock --strict --risk-file <risk.json> --manifest --out <dir>
   ```

3. Before review and again before signing, confirm nothing the run read has changed:
   `speccheck verify --manifest <dir>/speccheck.manifest.json` → `verify: ok - …`.
4. Review the reports (§5) and the traceability matrix.

## 4. Results (62304 5.7.5: test, result, tester, date)

| Field | Value |
| --- | --- |
| Summary line | `<the one stdout line of step 2, verbatim>` |
| Exit code | `<0 / 1>` |
| Ids in scope / passing | `<in_scope>` / `<by_status.PASSING>` (`speccheck.json` `metrics`) |
| Hazards verified | `<V>/<H>` (summary line suffix; `hazards` in `speccheck.json`) |
| Dangling / stale citations | `<n>` / `<n>` |
| Tests run / failed / skipped | `<from junit.xml>` |
| Run by | <name, role> |
| Date | <date> |
| Reports | `<dir>/SPEC_CONFORMANCE_REPORT.md`, `<dir>/speccheck.json`, `<dir>/speccheck.manifest.json` (filed as `<eQMS reference>`) |

## 5. Review

<!-- What the reviewer checked beyond the summary line. Suggested minimum: -->

- [ ] Every requirement that is a risk control measure is `PASSING`, and every hazard is `VERIFIED`
      (traceability matrix §4).
- [ ] The report's Notes section has been read; every Note is explained below.
- [ ] A sample of `PASSING` ids was opened at their cited test lines, and each test asserts the
      requirement's observable outcome (not just runs the code). Ids sampled: <list>.
- [ ] The tests of every risk control measure were read in full (class B and C).
- [ ] The known anomalies in the speccheck qualification record were reviewed for impact on this
      verification.

| Note or observation | Explanation |
| --- | --- |
| <Note text> | <why it is expected, or the action taken> |

## 6. Anomalies and deviations (62304 5.8.2, 9)

| Id | Anomaly or deviation | Evaluation (contribution to a hazardous situation) | Disposition | Problem report |
| --- | --- | --- | --- | --- |
| <id> | <what failed or deviated from the procedure> | <assessment> | <fixed / deferred / accepted, with rationale> | <reference> |

Known residual anomalies of this release (62304 5.8.2), with their evaluation: <list, or "None">.

## 7. Conclusion

<The software item <name> <version> <meets / does not meet> its software requirements as specified
in SPEC.md <version>, with the exceptions in §6. Verification evidence: the run identified in §2.>

## 8. Approval

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Verified by |  |  |  |
| Reviewed by (independent of the developer) |  |  |  |
| Approved by |  |  |  |
