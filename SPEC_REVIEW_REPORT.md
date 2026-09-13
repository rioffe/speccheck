# Specification Review Report

> - **Subject:** `SPEC.md` v1.3 — Specification Conformance Checker (`speccheck`)
> - **Review date:** 2026-09-13
> - **Method:** `spec-review` four-pass method (comprehension, local precision, cross-consistency, implementation simulation) over all 20 dimensions, plus a mechanical cross-check of ID declarations, §9 coverage, and §11 rows.
> - **Finding IDs:** `F-201..F-210`. `F-001..F-017` (v0.1 review), `F-101..F-110` (v0.4 review) and `Q-001..Q-011` (v0.5 review) are already cited inside `SPEC.md` and are not reused.
> - **Focus:** v1.0 was cleared by three prior reviews with no findings open. This pass re-reads the whole document but concentrates on what changed since: the v1.3 judge-stage progress indicator (R-30, C-11, K-13, E-39, E-40, T-62, T-63, D-15) and its interaction with the pre-existing diagnostics, exit-code, and portability contracts.

---

## 1. Executive Summary

`SPEC.md` v1.3 is an implementation-grade (Level 3) specification. Every requirement is observable and cites its source; every contract has a pinned shape; every I/K/E id has at least one test; §11 has one row per R/C/I/K/E id (105 rows, mechanically verified — no id missing, none undeclared); §12 lists fifteen defaulted decisions with alternatives. The determinism, downgrade-only-judge, and read-only-input principles are carried consistently through requirements, invariants, edge cases, and tests.

The v1.3 addition is well bounded — it names its stream, its byte sequences, its regex, its formulas and its gating — but it touches three older contracts (§5.3 diagnostics, §5.4 exit codes, R-29 portability) at seams the new rows do not fully close. Those seams are the findings below.

| Severity | Count |
| -------- | ----: |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 6 |
| LOW | 4 |

**Strengths:** closed status algorithm (C-05) with a single point of judge influence; byte-determined JSON via Decimal quantization; exit code a pure function of the report; exhaustive edge table (E-01..E-40) each with a deterministic outcome and a test; §12 honest about what the author decided alone.

**Weaknesses:** (1) the progress indicator's contract with the logger is implied, not stated — an INFO line emitted during the judge stage would corrupt the in-place line; (2) interruption (`KeyboardInterrupt`) now appears in a normative row (E-40) but has no exit-code semantics, contradicting K-01's closed set; (3) the elapsed clock has two origins; (4) the ANSI erase sequence undercuts the Windows/locale portability the spec otherwise invests in.

None blocks implementation. All six MEDIUM findings are one-row edits.

---

## 2. Overall Maturity

**Level 3 — Implementation-grade.** A coding agent can build v1.3 with minimal semantic inference; conformance is objectively testable via §9 and the golden fixture. Level 4 is not assigned: the judge component is contractually bounded but its evaluation (T-49) is recorded, not gated, and the traceability matrix still names intended modules rather than verified ones for the v1.3 rows.

---

## 3. Findings Summary

| ID | Severity | Location | Title |
| -- | -------- | -------- | ----- |
| F-201 | MEDIUM | §5.3, K-13, R-30 | Logger output during the judge stage is not excluded, so an INFO line can land on the progress line |
| F-202 | MEDIUM | C-11, K-13, K-12 | Two origins for the elapsed clock $t$: "first request issued" vs. the $d = 0$ draw that precedes it |
| F-203 | MEDIUM | K-13 | Per-verdict MUST-redraw conflicts with the 10 Hz SHOULD-NOT at high concurrency; write atomicity implied by T-62 but not stated |
| F-204 | MEDIUM | E-40, §5.4, K-01, I-001 | `KeyboardInterrupt` "propagates" — an exit code outside K-01's closed set; interrupt semantics undefined |
| F-205 | MEDIUM | C-11, R-29 | `\x1b[K` is not interpreted by a legacy Windows console; a portable erase exists and the line never shrinks |
| F-206 | MEDIUM | C-07 | Example disagrees with the four-decimal rule (`unknown_rate: 0.0`, `max_unknown: 0.2`); `max_unknown` emission format unstated |
| F-207 | LOW | C-08 | Header `(available\|unavailable)` has no rendering for `judge_available == null` |
| F-208 | LOW | §11, T-46, T-60 | T-46 and T-60 are cited by no §11 row |
| F-209 | LOW | I-005 | "carries $\geq$ 0 evidence entries" is vacuous |
| F-210 | LOW | T-49, §10 | Hand-label file for the T-49 evaluation is not named (the repository has `tools/eval_judge.py`; `tools/bench.py` is named for T-51) |

---

## 4. Detailed Findings

### F-201 — Logger output during the judge stage can corrupt the progress line

**Severity:** MEDIUM

**Location:** §5.3 (INFO), K-13, R-30, C-11

**Observation**

C-11 writes the indicator directly to the stderr stream and redraws it with `\r`. §5.3 INFO says the judge mode and, for the LLM judge, the URL and model are logged at INFO, and that stage lines carry counts and elapsed milliseconds — but does not say *when* within the stage those lines are emitted. K-13 requires the erase to precede "any INFO stage line", which covers the *end* of the stage only. Nothing forbids a logger emission between the first draw and the erase. Under the most common interactive configuration (`--judge llm --verbose` on a TTY) such an emission would be written to the same stream mid-line, leaving `INFO judge=llm url=…` glued to a half-drawn bar, and the next `\r` would overwrite part of it.

**Why it matters**

The indicator is on by default on a TTY. An implementer who logs the URL/model line after building the requests (a natural place) conforms to every row as written and produces garbled stderr. Two conforming implementations differ observably.

**Potential consequence**

T-62 captures stderr with `--progress always` and no `--verbose`, so the defect is invisible to the suite; it appears only to operators.

**Recommended resolution**

Add one sentence to K-13 (or §5.3 *Mechanism*): "While the indicator is displayed — from the first draw to the erase — nothing is written to stderr through the logger; the judge stage's INFO lines (mode, URL, model, stage summary) are emitted after the erase." Extend T-62 with a `--verbose INFO` variant asserting that every `\r`-delimited segment is either a C-11 sequence or a complete `INFO …\n` line and that no `INFO` line occurs between the first draw and the erase.

---

### F-202 — Two definitions of the elapsed-clock origin

**Severity:** MEDIUM

**Location:** C-11 (definition of $t$), K-13 (first draw), K-12

**Observation**

C-11 defines $t$ as "wall-clock seconds since the judge stage started (the same origin as K-12: the moment the first request is issued)". K-13 requires a first draw "when the judge stage starts (with $d = 0$)" — which by construction precedes the first request. At that instant $t$ is undefined (or negative) under the C-11 definition. T-62 asserts the content of that first draw (`0/6 edges`, `?:??`) but not its `elapsed`, so testers could disagree whether `0:00` is required.

**Why it matters**

The two clocks are also semantically different: K-12's budget deadline must not start before a request can be issued, whereas the indicator's elapsed time should include request construction. Conflating them invites an implementer to start the budget clock at the first draw, shortening the budget by the request-building time.

**Potential consequence**

Sub-second discrepancy in practice, but a definitional contradiction between two normative rows.

**Recommended resolution**

In C-11 define $t_0$ as the instant of the first draw (the start of the judge stage, immediately before the first request is issued), and state that K-12's deadline keeps its own origin (first request issued), which is $\geq t_0$. Add to T-62: "the first draw shows `0:00 elapsed`".

---

### F-203 — Redraw cadence: MUST-per-verdict vs. SHOULD-NOT-over-10 Hz; atomicity

**Severity:** MEDIUM

**Location:** K-13, C-11, T-62

**Observation**

K-13 says the indicator is "redrawn after every determined verdict" (normative) and "SHOULD NOT be redrawn more than 10 times per second". With `--judge-concurrency 32` and a fast provider (or a budget-exhausted tail, where remaining edges are determined instantly in a burst), verdicts arrive far faster than 10 Hz; the MUST and the SHOULD cannot both hold. Separately, draws originate from worker threads (completions) and a ticker thread (the 1 s rule); T-62 requires that splitting the capture on `\r` yields *only* well-formed C-11 sequences, which is achievable only if each draw is a single, serialized write — a requirement the spec relies on but does not state.

**Why it matters**

An implementer following the MUST produces a flicker-storm on fast providers; one following the SHOULD violates the MUST as written. Interleaved partial writes would fail T-62 nondeterministically.

**Potential consequence**

Divergent behavior under high concurrency; flaky T-62.

**Recommended resolution**

Rephrase K-13 as coalescing: "Every determined verdict is reflected by a draw within 100 ms; the indicator is redrawn at least once per second while any request is in flight; draws are never more frequent than 10 per second. Each draw and the erase is one atomic write (a single `write()` call, serialized across threads)." T-62's "6/6 with a full bar exists" then still holds (the final state is always drawn before the erase — say so explicitly).

---

### F-204 — Interruption has no exit-code semantics; E-40 contradicts K-01

**Severity:** MEDIUM

**Location:** E-40, §5.4, K-01, I-001, §3.1

**Observation**

E-40 says that on `KeyboardInterrupt` the erase is written "before … the interrupt propagates". If it propagates, Python exits with status 130 (or 1 with a traceback), which K-01 ("no other exit codes exist") and §5.4 forbid; §5.4 additionally says "any uncaught exception MUST also map to `3`" — but `KeyboardInterrupt` is a `BaseException`, and whether it is an "uncaught exception" in the §5.4 sense is exactly the ambiguity. The interrupt case is also absent from §3.1's failure column and from I-001 (an interrupt during the report stage — between steps 2 and 4 — is a "step fails" case only if the reader treats it as one).

**Why it matters**

CI wrappers that send SIGINT on timeout will see either 130, 1 or 3 depending on the implementer; the report-file guarantee ("either both or neither") is unstated for the interrupted case.

**Potential consequence**

Divergent exit codes; a `.tmp` leftover after an interrupt during step 2 if the implementer does not treat the interrupt as a failure.

**Recommended resolution**

Add E-41: "`SIGINT` / `KeyboardInterrupt` at any stage → the progress indicator (if displayed) is erased, every temporary of §3.1 is removed, no report file from this run remains, and the process exits `3` with the one-line message `interrupted`" — or, if the conventional 130 is preferred, widen K-01 explicitly. Either choice needs a T id (a stub raising `KeyboardInterrupt` mid-judge and mid-report) and a §11 row. Rephrase E-40 to reference E-41 instead of "propagates".

---

### F-205 — ANSI erase sequence vs. the spec's own portability posture

**Severity:** MEDIUM

**Location:** C-11 (draw / erase sequences), R-29, T-44, D-15

**Observation**

C-11 pins `\x1b[K` (erase-to-end-of-line) in every draw and in the erase. A legacy Windows console (conhost without `ENABLE_VIRTUAL_TERMINAL_PROCESSING`, still the default for `cmd.exe` on some hosts) prints the sequence literally as `←[K`. The spec elsewhere spends effort on exactly this class of host (R-29's "regardless of locale", T-44's `cp1252` stdout), so Windows terminals are evidently in scope. The sequence is also unnecessary for the draws: every field of `<line>` is non-decreasing in width (`<done>` and `<elapsed>` grow; `~?:?? left` and `~M:SS left` have equal width for $M < 10$ and the field only grows thereafter), so a `\r`-redraw never leaves residue. It is needed only for the final erase.

**Why it matters**

Two conforming implementations produce different visible output on the platform the spec otherwise names; there is no way to conform on that platform without enabling VT mode, which C-11 does not require.

**Potential consequence**

Garbled stderr on legacy Windows consoles; `← [K` residue after the run.

**Recommended resolution**

Replace the sequences with the portable forms: `draw := "\r" + <line>` and `erase := "\r" + " " * len(<last line drawn>) + "\r"`, and state the non-shrinking property as the reason no erase-to-EOL is needed. Alternatively keep ANSI and add a K-row: "on Windows the process enables VT processing on the stderr console handle before the first draw; if that fails, the indicator is not drawn." Update T-62's sequence check accordingly.

---

### F-206 — C-07 example disagrees with the four-decimal rule

**Severity:** MEDIUM

**Location:** C-07 (example and *Numbers* rule), K-11, §5.1 regex

**Observation**

The C-07 rules say every ratio "is emitted as a JSON number with exactly four decimal places (0.9000, not 0.9)", and T-34 asserts it. The example in the same contract shows `"unknown_rate": 0.0` and `"max_unknown": 0.2`. Whether `max_unknown` (an echoed CLI input, not a computed ratio) falls under the four-decimal rule is not stated; the §5.1 summary-line regex renders it with exactly four decimals (`max_unknown \d\.\d{4}`), which suggests the JSON should too.

**Why it matters**

The skill's rule is that examples agree with definitions; a reader using the example as the shape will emit `0.2` and `0.0`, and a golden-comparison test against a hand-written expectation will disagree with one derived from the rule.

**Potential consequence**

Byte-level nonconformance on `max_unknown` between implementations; T-34 ambiguity for the `max_unknown` key.

**Recommended resolution**

Change the example to `"max_unknown": 0.2000` and `"unknown_rate": 0.0000`, and add to *Numbers*: "`max_unknown` is the K-11 Decimal quantized to four places, emitted like a ratio."

---

### F-207 — C-08 header rendering for `judge_available == null`

**Severity:** LOW

**Location:** C-08 header line

**Observation**

The header pins `**Judge:** none|mock|llm (available|unavailable)`. With `--judge none`, `judge_available` is `null` (C-07), and no rendering is given for the parenthetical.

**Recommended resolution**

State: "the parenthetical is omitted when `judge_available` is `null`" (or pin `(n/a)`), and add it to T-35.

---

### F-208 — T-46 and T-60 cited by no §11 row

**Severity:** LOW

**Location:** §11, T-46, T-60

**Observation**

Every R/C/I/K/E id has a §11 row (verified mechanically), but two T ids appear in no *Verified by* cell: T-46 (the golden end-to-end fixture, which the spec calls the proof of "all of §2") and T-60 (the `_selfcheck/` drift guard). T-46 is the strongest single piece of evidence in the suite and is invisible in the matrix.

**Recommended resolution**

Cite T-46 in the rows of R-01..R-15 (or add a footnote row "golden: T-46 covers every row above"), and cite T-60 under I-001 or R-18 (whichever the author regards as owning the packaged fixture).

---

### F-209 — Vacuous clause in I-005

**Severity:** LOW

**Location:** I-005

**Observation**

"Every non-`UNKNOWN` verdict in a report carries $\geq$ 0 evidence entries" is true of any list. The invariant's content is the second and third clauses.

**Recommended resolution**

Drop the clause, or make it meaningful: "carries an `evidence` list (possibly empty)".

---

### F-210 — T-49 hand-labels not located

**Severity:** LOW

**Location:** T-49, §10

**Observation**

T-49 evaluates the LLM judge against "hand-labeled" edges of the golden fixture but does not say where the labels live or what runs the evaluation. The repository contains `tools/eval_judge.py`; T-51 names `tools/bench.py` for the analogous recorded benchmark.

**Recommended resolution**

Name the label file (e.g. `fixtures/target/golden/judge_labels.json`) and the runner (`tools/eval_judge.py`) in T-49 and §10, and pin the label file's shape in one line.

---

## 5. Requirements Review

R-01..R-30 are observable obligations in normative language, each with a source. R-30 (progress) is fully observable — stream, format, gating, and non-effects are all named. The cross-cutting concerns (diagnostics R-17, security R-23, portability R-20/R-29, read-only R-19) each have requirements. No conflicting requirements were found; the closest is the R-30/§5.3 seam covered by F-201, which is an omission rather than a conflict.

## 6. Interface and Data-Contract Review

C-01..C-11 pin every externally significant shape. C-11 is a good contract — grammar, regex, and formulas with symbols defined and the degenerate cases stated ($d = 0$, $n = 0$). Defects: the example/rule mismatch in C-07 (F-206), the `null` rendering gap in C-08 (F-207), and the platform assumption embedded in C-11's escape sequence (F-205). The CLI table in §5.1 now lists every flag, and the synopsis matches the table.

## 7. State and Failure Review

§3.1's pipeline is complete for the success path and for every failure that maps to exit 2/3. The gap is interruption (F-204): E-40 introduces `KeyboardInterrupt` without an outcome, and I-001's "either both or neither" is not restated for it. K-12's budget semantics (in-flight completion, budget-skipped edges) remain precise and are consistent with C-11's definition of "determined".

## 8. Determinism and Algorithm Review

C-05 is closed and total. Metrics are Decimal-quantized and byte-determined. C-11's $k$ and ETA formulas are well defined; the only algorithmic ambiguity is the clock origin (F-202). Note that I-002 (determinism) correctly excludes stderr, so the indicator does not threaten it.

## 9. Edge-Case Review

E-01..E-40 cover empty, malformed, duplicate, oversized, binary, symlink, unavailable-dependency, timeout, budget, and zero-edge cases with deterministic outcomes and tests. E-39 correctly enumerates every suppression condition for the indicator. Missing: the interrupt case (F-204) and the high-concurrency burst case that motivates F-203.

## 10. Non-Functional Requirement Review

K-08 is measurable and recorded on a named machine (D-14 still open). K-13 is measurable except for the internal MUST/SHOULD tension (F-203). The 1 s tick and the 100 ms coalescing window recommended in F-203 are both testable with a sleeping stub, as T-62 already does.

## 11. Security and Trust-Boundary Review

Unchanged from v1.0 and still sound: the key never reaches any output (R-23, I-007, C-09), the network boundary is guarded and self-checked (R-18, I-006), and the judge is downgrade-only (I-004). C-11 explicitly excludes secrets and payloads from the progress line.

## 12. Observability and Provenance Review

The report carries `judge_prompt_sha256`, per-edge rationale and evidence, and coerced-flags; the INFO stream gives stage timings. The indicator adds operator-facing observability without touching the reports. F-201 is the one place where the two observability channels can collide.

## 13. Testing and Verification Review

Every I/K/E id has a T id (verified); every R and C id is cited in §9. T-62/T-63 are concrete and reproducible with the stubs they describe. Gaps: no test for logger/indicator interleaving (F-201), for the first draw's `elapsed` (F-202), or for interruption exit code and cleanup (F-204).

## 14. Metrics and Evaluation Review

`conformance`, `by_family`, `judge_strength`, `unknown_rate` have formula, population, denominator and zero-denominator rule. C-11's ETA has the same. The only defect is presentational (F-206). T-49 remains recorded-not-gated, which is appropriate for a probabilistic component, but its inputs should be located (F-210).

## 15. Traceability Review

Intent → R → C → I → T → evidence is intact. Mechanical check: 168 declared ids; 105 R/C/I/K/E ids each with exactly one §11 row; no undeclared id in §11; no undeclared T referenced anywhere. Two T ids are orphaned from §11 (F-208). Diagrams: §3.2 is ASCII (house style) and matches §3.1's stage table including the v1.3 judge-row note.

## 16. Internal-Consistency Review

Cross-checked: §5.1 synopsis vs. flag table (consistent after v1.3); §5.3 vs. R-17 vs. R-30 (seam: F-201); C-11 vs. K-12 vs. K-13 (seam: F-202); E-40 vs. §5.4 vs. K-01 (contradiction: F-204); C-07 example vs. rule (F-206); §12 count sentence ("first fourteen") vs. fifteen rows (consistent). Revision history matches the front-matter status.

## 17. Architecture Review

Component responsibilities in §1 support every requirement; the v1.3 rows are assigned to `judge.py` (rendering, cadence, erase) and `cli.py` (flag resolution, TTY test), which matches dependency direction (the CLI decides, the judge stage reports). No redesign warranted.

## 18. Implementation-Agent Readiness

**YES — WITH MINOR CLARIFICATIONS.**

Minimum questions an implementer would ask:

1. May the logger write to stderr while the indicator is displayed? (F-201 — assume no.)
2. Is `elapsed` on the first draw `0:00`, and does the budget clock start at the same instant? (F-202 — assume `0:00`; budget starts at first request.)
3. On a burst of verdicts, coalesce or draw each? Are writes atomic? (F-203 — assume coalesce within 100 ms; atomic.)
4. What exit code and cleanup on Ctrl-C? (F-204 — no safe default; the author must choose.)
5. ANSI or portable erase? (F-205 — assume ANSI as written; note Windows caveat.)

Only question 4 lacks an obvious default, and it does not affect the success path.

## 19. Quality Scorecard

| Dimension | Score |
| --------- | ----: |
| Scope clarity | 5 |
| Terminology | 5 |
| Requirement precision | 5 |
| Interface completeness | 4 |
| Data-contract completeness | 4 |
| State/lifecycle definition | 4 |
| Algorithm precision | 4 |
| Failure semantics | 4 |
| Edge-case coverage | 4 |
| Non-functional requirements | 4 |
| Security specification | 5 |
| Observability/provenance | 4 |
| Testability | 5 |
| Evaluation/metrics | 4 |
| Traceability | 4 |
| Internal consistency | 4 |
| Architecture consistency | 5 |
| Implementation readiness | 4 |

## 20. Remediation Plan

### P0 — Blocking

None.

### P1 — Important (resolve before claiming conformance of the v1.3 rows)

- **F-201** — pin "no logger output while the indicator is displayed"; extend T-62.
- **F-202** — single origin for $t$ (first draw); K-12 keeps its own; T-62 asserts `0:00`.
- **F-203** — coalescing cadence (100 ms / 1 s / 10 Hz) and atomic writes.
- **F-204** — E-41 interrupt semantics with exit code and cleanup; T id; §11 row; E-40 references it.
- **F-206** — fix the C-07 example; state `max_unknown` emission format.

### P2 — Improvement (may be deferred)

- **F-205** — portable erase or an explicit VT-mode rule.
- **F-207** — `null` rendering in the C-08 header.
- **F-208** — cite T-46 and T-60 in §11.
- **F-209** — tidy I-005.
- **F-210** — locate the T-49 labels and runner.

Suggested version bump: `v1.3 → v1.4` with `fix(speccheck):` commits per the spec-writing convention.

## 21. Final Verdict

```text
Specification maturity:
Level 3

Implementation readiness:
READY WITH MINOR FIXES

Primary blocker:
NONE

Most important improvement:
Close the seam between the in-place progress line and the stderr logger (F-201), and give interruption an exit code and cleanup rule so E-40 stops contradicting K-01 (F-204).
```
