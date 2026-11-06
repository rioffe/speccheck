# Tool risk assessment — speccheck as QMS software

> **Applies to:** speccheck 1.26.0 (`SPEC.md` v1.26, C-30, R-114, D-69).
> **Status:** supplier assessment, for a manufacturer to review against its own intended use and
> risk acceptance criteria. Severities below are proposed; the manufacturer's assessment governs.

## The hazardous failure

speccheck is used to decide whether a requirement was verified. The failure that matters is a
**false `PASSING`**: an id reported as verified when the evidence does not support it, or a
summary line or exit code that claims more than the report shows. A false *failure* (an id
reported as not verified when it was) is a nuisance, caught by review, and is not assessed here.
One more failure is assessed because it defeats change control: `impact` under-reporting what a
specification change touches, so a revalidation is missed.

## How this assessment is kept honest

The hazards are not only written here. `speccheck/_qualify/tool_risk.json` lists them (a v1.25
risk file), every requirement that controls one carries a `*(controls: TH-nn)*` marker in
`SPEC.md`, and speccheck's own build gate runs `check --strict --risk-file
src/speccheck/_qualify/tool_risk.json`. If a control row is retired, renamed or its tests fail,
the hazard becomes `UNCONTROLLED` or `NOT_VERIFIED` and the build fails. Each release's
`SPEC_BUILD_REPORT.md` records the summary line, which ends `; hazards: 10/10 verified` when every
control passes. Every hazard is also challenged on the customer's machine by at least one
operational-qualification case (`speccheck qualify`).

## The hazards

| Hazard | Failure | Cause | Proposed severity | Controlled by | OQ cases | Residual risk |
| --- | --- | --- | --- | --- | --- | --- |
| TH-01 | A token is counted as a citation that realizes nothing | citations are literal tokens; a test may mention an id as data | High | R-03, R-04, R-27 (ignore markers), R-22 (mock judge needs an assertion token), C-01, C-03 | OQ-01 | KA-02: literal citation is a stated limitation; the mock judge narrows it, review closes it |
| TH-02 | A test result is joined to the wrong test case | classname/name join across Python, Swift and JS/TS adapters | High | R-05, R-31, R-104, C-04 | OQ-01, OQ-02 | KA-05: no OQ case for the JS/TS adapter |
| TH-03 | The results file belongs to another tree, or is stale | the results file is an input, produced elsewhere | High | R-15 (`--strict`), R-106 (the manifest hashes the results file read) | OQ-03 | KA-03: the manifest proves which file was read, not where it came from; produce results and run `check` in one CI job |
| TH-04 | A status is computed wrongly | an error in the C-05 status algorithm | High | R-06, R-25, R-35, C-05 (also modelled in Lean, `proof/`) | OQ-01, OQ-02 | — |
| TH-05 | The judge raises a status | a model verdict treated as evidence | High | R-11, I-004 (downgrade-only) | OQ-01 | — |
| TH-06 | The exit code or summary line claims more than the report shows | exit/summary computed apart from the report | High | R-14, R-15, R-105 (`UNPROVEN`), I-009 | OQ-01, OQ-04 | KA-04: the Lean model predates the v1.25 `UNCONTROLLED` exit condition |
| TH-07 | A declared id is silently missing from the report | a declaration the parser does not see | High | R-01, R-12, R-32, I-003 | OQ-01 | KA-01: a row cut by an unescaped `\|` that keeps its cell count is silent |
| TH-08 | A report is altered or replaced after the run | records are ordinary files | High | R-107 (`verify` re-hashes against the manifest) | OQ-03 | — |
| TH-09 | A retired id is counted, or a stale citation goes unreported | retirement by strike-through | Medium | R-02, R-08 | OQ-01 | — |
| TH-10 | `impact` under-reports what a change touches, so a revalidation is missed | the walk follows only edges a statement names | Medium | R-36, R-37, I-013 | OQ-05 | — |

**Severity.** *High*: the failure can let an unverified requirement be recorded as verified.
*Medium*: the failure can delay detection, but the next `check` run reports the true state.

## Residual risk and known anomalies

Every residual risk named above is a known anomaly (`KA-nn`) in
`speccheck/_qualify/known_anomalies.json`, printed in every qualification record with its
workaround. An anomaly is never removed: when fixed, its `fixed_in` is set and it stops being
printed for that version and later.

## What a manufacturer still has to do

Review this table against its own intended use, set its own severities and acceptance criteria,
and run performance qualification on its own project: a `check` over a specification and test
suite it knows, with a planted defect of each kind it cares about, compared with what it expects.
