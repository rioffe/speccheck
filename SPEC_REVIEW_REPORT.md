# Specification Review Report

> - **Subject:** `SPEC.md` v1.10 — Specification Conformance Checker (`speccheck`)
> - **Review date:** 2026-09-18
> - **Method:** `spec-review` four-pass method (comprehension, local precision, cross-consistency, implementation simulation) over all 20 dimensions, plus a mechanical cross-check run with the shipped 1.8.0 extractor: 200 declared ids (35 R, 11 C, 11 I, 15 K, 51 E, 77 T; 0 retired; 3 carrying the new `*(recorded)*` marker and still declared under the 1.8.0 grammar), every non-T id has a §11 row (124 rows, none undeclared), every I/K/E id is cited by at least one T row, every T id appears in a §11 "Verified by" cell, no dangling R/C/I/K/E/T/D reference.
> - **Finding IDs:** `F-401..F-407`. `F-001..F-017`, `F-101..F-110`, `Q-001..Q-011`, `F-201..F-210`, `F-301..F-307` are cited inside `SPEC.md` and are not reused.
> - **Focus:** v1.8 closed the v1.7 review. This pass re-reads the whole document but concentrates on the two increments since — v1.9 (clause-grounded verdicts: R-34, C-06 `clause`, K-15, E-48, E-49, I-005, C-07 `"1.2"`, C-08 §8, C-10, T-75, T-76; D-21) and v1.10 (recorded tests: R-35, C-01 marker, C-02 `recorded`, C-05 step 5, I-010, C-07 `"1.3"`, C-08 ID cell, E-50, E-51, T-77; D-22) — and on the seams they open with the pre-existing verdict, metric, and golden contracts.

---

## 1. Executive Summary

`SPEC.md` v1.10 remains an implementation-grade (Level 3) specification. Both increments are well shaped: v1.9 reuses the grounding pattern the spec already had for evidence lines and states its matcher as a deterministic rule (K-15) with both degenerate cases (short statement, empty statement); v1.10 adds one bit to a declaration and touches exactly the one algorithm step it needs to (C-05 step 5), with the important negative stated plainly (E-51: the marker exempts an id from the judge and from nothing else). The D-21/D-22 rows record the alternatives and the evidence that produced the decisions, including the two-model comparison that motivated both.

What the increments did not do is walk the older rows that restate the same facts. Three test rows now pin three different `schema_version` literals against a contract that names one (F-401) — an implementer cannot make T-73, T-75 and T-77 all pass. Two places still define "when is `verdict` null" without the recorded case that C-05 now adds (F-403). The heading form of the `*(recorded)*` marker is described in C-01 (a)'s marker paragraph but C-01 (b)'s `title :=` rule was not amended to strip it (F-404). The kernel's validation list grew to eight rules that can fire together and has no stated precedence, so two implementations would record different rationales for the same reply (F-402). And `judge_strength` now counts ids the judge never saw (F-405).

| Severity | Count |
| -------- | ----: |
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 4 |
| LOW | 2 |

**Strengths:** K-15 is a real matcher definition (collapse, cut, then substring; both short-statement cases named) rather than "must quote"; the mock judge's clause is a prefix, which makes Phase A's determinism a one-line argument; E-51 closes the hole a `recorded` marker would otherwise open; T-76 turns the judge's known failure into a measurable fixture; D-08 became a text-*and-model* row with measured numbers.

**Weaknesses:** literal `schema_version` values scattered across three T rows (the same class of defect as v1.8's F-302: a value pinned in a test rather than a rule); the null-verdict condition stated in three places and updated in one; C-01's two declaration forms drifted on the marker; validation precedence and the `clause` type left to the implementer; a metric population that quietly widened.

The HIGH finding is a slip, not a design problem, and is a three-cell edit. Nothing blocks implementation once it is made.

---

## 2. Overall Maturity

**Level 3 — Implementation-grade.** A coding agent can build v1.10 with minimal semantic inference once F-401 is resolved; conformance is objectively testable through §9, two golden fixtures, the packaged self-check, and — now — a T-49 label set that can distinguish judges. Level 4 is not assigned: the judge's evaluation remains recorded rather than gated (by design, and now honestly marked `*(recorded)*`), and §11 names intended modules for the v1.9/v1.10 rows until the build replaces them.

---

## 3. Findings Summary

| ID | Severity | Location | Title |
| -- | -------- | -------- | ----- |
| F-401 | HIGH | T-73, T-75, T-77, C-07 | Three test rows pin three different `schema_version` literals (`"1.1"`, `"1.2"`, `"1.3"`); C-07 says `"1.3"` |
| F-402 | MEDIUM | C-06 validation list, E-48, E-16, K-15 | Eight coercion rules with no precedence; `clause` of a non-string type and the recorded `clause` of a coerced `UNKNOWN` undefined |
| F-403 | MEDIUM | E-37, C-07 "Verdict field (Q-001)", T-34 | The null-`verdict` condition is stated in three places; only C-05 gained the RECORDED case |
| F-404 | MEDIUM | C-01 (b) `title :=`, C-08 | The heading form of `*(recorded)*` is described but (b)'s title rule does not strip it; retired-and-recorded ID cell unspecified |
| F-405 | MEDIUM | C-07 metrics `judge_strength` | Recorded ids are `PASSING` without being judged and now count in a judge-quality ratio |
| F-406 | LOW | K-15 | Leading/trailing whitespace of the clause is collapsed but not trimmed, so a clause quoted from the start of the statement with a leading space fails |
| F-407 | LOW | T-75, D-08, front matter | Editorial: "the v1.9 C-10 file" (v1.10 did not change it — say "the current C-10 text"); D-08's `Default taken` cell now carries measurement prose that belongs in the alternatives cell |

---

## 4. Detailed Findings

### F-401 — Three `schema_version` literals in test rows, one in the contract

**Severity:** HIGH

**Location:** T-73 (`schema_version` `"1.1"`), T-75 (`"1.2"`), T-77 (`"1.3"`); C-07 heading and example (`"1.3"`); §3.3

**Observation**

C-07, §3.3 and the v1.10 revision row agree on `"1.3"`. T-73 — written for v1.7 and not revisited — asserts each golden `speccheck.json` carries `"1.1"`; T-75 — written for v1.9 — asserts `"1.2"`; T-77 asserts `"1.3"`. All three describe the same file after the same run.

**Why it matters**

The three assertions cannot all hold. A builder must either break two tests or quietly edit their expectations to whatever the code emits — which is the self-certification the v1.8 review's F-302 removed from these same rows. This is also the exact failure mode the v1.8 build's plan §6 named ("literals pinned in tests turn a spec bump into red with no defect") and guarded against in the *code's* tests but not in the spec's own T rows.

**Potential consequence**

Two of three tests red on a correct build; or a test tree whose expected schema version is edited per release and therefore proves nothing.

**Recommended resolution**

Pin the value once, in C-07, and make every T row refer to it: replace each literal with "`schema_version` equal to the C-07 value" (T-73, T-75, T-77). If a row needs to prove the *bump*, say "greater than the previous release's value, as the revision history records it", not a number. Add to C-07's rules: "`schema_version` is stated in this contract only; no §9 row repeats the literal."

---

### F-402 — Validation precedence, non-string `clause`, and the recorded `clause` of a coerced verdict

**Severity:** MEDIUM

**Location:** C-06 "Validation applied by the kernel"; E-16; E-48; E-49; K-15

**Observation**

The validation list now has eight rules, and several can apply to one reply: an `ASSERTS` with an unlocatable clause *and* an evidence line outside the span matches both the E-48 rule (`judge: unlocated clause`) and the E-16 rule (`judge: ungrounded`). The list is not declared ordered and "first match wins" is not stated, so two implementations record different rationales for the same reply — a byte difference in `speccheck.json` under `--judge llm`, and a different §8 row. Three smaller gaps sit beside it: (1) a `clause` that is present but not a string (`null`, a number, an object) is neither "absent" (→ `""`) nor a string to match — is it E-15 non-JSON or E-48?; (2) the `clause` recorded for a *coerced* `UNKNOWN` (the reply said `ASSERTS`, K-15 failed) is not stated — E-49 covers verdicts *returned* as `UNRELATED`/`UNKNOWN`, not verdicts that became `UNKNOWN`; (3) the mock provider's clause is defined but the rule that the mock's answer also passes through the same validation (it does: "EVERY provider") means K-15 must accept the prefix even when the statement's first 280 collapsed characters end mid-word — true by construction, but worth one clause so nobody "fixes" it.

**Why it matters**

R-24 promises every recorded verdict is reproducible from the report; two implementations that disagree on which coercion fired break that at the rationale. The `clause` type gap is a crash or a silent `""` depending on the JSON library's behaviour.

**Potential consequence**

Golden drift between implementations under `--judge llm`; a provider that returns `"clause": null` (plausible for `UNRELATED`) coerced to `UNKNOWN` by one build and accepted by another.

**Recommended resolution**

- State once, above the list: "Rules are applied in the order listed; the first that fires determines the rationale; later rules are not evaluated." Order them so the cheapest structural checks come first: non-JSON / provider failure → verdict not in set → E-49 blanking → K-15 (E-48) → evidence empty (E-16) → evidence outside span (E-16) → rationale truncation (always applied).
- "`clause` present but not a JSON string → treated as absent (`""`)"; with the E-49 rule that then makes it `""` for `UNRELATED`/`UNKNOWN` and E-48 for the other two.
- "A verdict coerced to `UNKNOWN` by any rule is recorded with `clause` `""`" (extend E-49's wording to *recorded as* `UNKNOWN`).
- T-75 gains the combined case: unlocated clause *and* out-of-span evidence → `judge: unlocated clause` (or whichever order is chosen), and `"clause": null` on an `UNRELATED` → `""`, not coerced.

---

### F-403 — "When is `verdict` null" is stated three times and amended once

**Severity:** MEDIUM

**Location:** E-37; C-07 "Verdict field (Q-001)"; T-34; C-05 (amended)

**Observation**

v1.10 amended C-05's note ("a recorded id's `tests[].verdict` is null (E-37)") and I-010. E-37 itself still lists the three v1.0 conditions — judge disabled, id not `PASSING` after step 4, outcome not `passed` — and C-07's Q-001 paragraph repeats the same three ("judge enabled, ID `PASSING` after C-05 step 4, outcome `passed`"). T-34 enumerates the null cases it must exercise from that list. A reader of E-37 or C-07 alone concludes a recorded id's passed edges carry a verdict object.

**Why it matters**

E-37 is the row §11 points at for the null rule and T-34 is its test; both now disagree with C-05 on the one new case. This is the F-206/F-303 shape again: a fact stated in several rows, changed in one.

**Recommended resolution**

E-37: add "or the ID is RECORDED (R-35)" to the case column. C-07 Q-001 paragraph: "… ID `PASSING` after C-05 step 4, **not RECORDED**, outcome `passed`". T-34: add the recorded-id null case to its list (or cite T-77 for it). Consider making E-37 the single owner of the condition and having C-05 and C-07 cite it rather than restate it.

---

### F-404 — The heading form of the marker is described but not wired into (b)'s title rule; retired + recorded rendering

**Severity:** MEDIUM

**Location:** C-01 (a) "RECORDED marker" paragraph; C-01 (b) `title :=`; C-08 ID cell

**Observation**

The marker paragraph (placed under (a)) says the heading form is `### T-48 *(recorded)* <title>` "where the marker is then not part of the title". C-01 (b)'s formal rule still reads `title := the rest of the heading text after the ID token, trimmed, whitespace-collapsed, with a trailing run of "#" … removed` — which yields the title `*(recorded)* <title>`. One implementer follows the paragraph, another the rule, and `title` (hence the C-08 Statement cell and the first line of `SpecId.text`) differs. Separately, C-08 now specifies `T-48 (recorded)` for a recorded id and `~~R-07~~` for a retired one, but not the cell for an id that is both (a retired recorded test is legal: `| ~~**T-48**~~ *(recorded)* |`).

**Why it matters**

`title` is what the Markdown report renders and the first line of what the judge receives (R-33); T-72's property "title equals the independently computed heading remainder" would be satisfied by either reading.

**Recommended resolution**

Move the marker rule out of (a) into a short block that both forms cite, and amend (b): "if the first token after the ID token is exactly `*(recorded)*`, the declaration is RECORDED and `title` is taken from the text after that token". T-77 already has the heading case (`### T-02 *(recorded)* Title` → title `Title`), so the test is ahead of the grammar — align the grammar. For C-08: "`~~T-48~~ (recorded)`" (strike the id, append the label), and one sub-case in T-77.

---

### F-405 — `judge_strength` now counts ids the judge never saw

**Severity:** MEDIUM

**Location:** C-07 metrics: `judge_strength = |PASSING| / (|PASSING| + |WEAKLY_PASSING|)`

**Observation**

Before v1.10 every `PASSING` id under `--judge mock|llm` had at least one judged edge (a `PASSING` id has, by C-05 step 4, at least one passed edge, and every such edge was eligible), so `judge_strength` was a ratio over judged ids. A RECORDED id is `PASSING` with no judged edge, and it now sits in the numerator and the denominator. On this repository that is three ids; on a spec with many recorded rows it is a systematic upward bias in a number whose name says "judge".

**Why it matters**

§3.16: a metric's population should be the population its name and definition imply. `unknown_rate` is unaffected (its denominator is judged edges); `judge_strength` is the one metric defined over ids rather than edges, and it silently widened.

**Recommended resolution**

Define the population explicitly and exclude recorded ids: `judge_strength = |PASSING ∖ RECORDED| / (|PASSING ∖ RECORDED| + |WEAKLY_PASSING|)`, written in the same `$..$` form as the other ratios, with the zero-denominator rule already stated for it (a spec whose every PASSING id is recorded yields `null`/`n/a`). State in C-07's rules that `conformance` and `by_family` *do* include recorded ids (they are `PASSING` by citation and result). Add the arithmetic to T-77 and to T-37's recomputation.

---

### F-406 — K-15 does not trim the clause

**Severity:** LOW

**Location:** K-15

**Observation**

"After collapsing every run of whitespace in both strings to one space" leaves a single leading or trailing space in place. A model that returns `" Cache: 2048 entries keyed by the URL"` fails against a statement whose text starts at column 0 only when the quoted span begins the statement — an inconsistency at the boundary that has nothing to do with whether the clause was located. The mock's prefix never has a leading space, so the case only arises with the LLM provider.

**Recommended resolution**

"… collapsing every run of whitespace in both strings to one space **and trimming the clause**, then cutting …". One sub-case in T-75.

---

### F-407 — Editorial

**Severity:** LOW

**Location:** T-75; D-08; front matter

**Observation**

1. T-75 says "the LLM request's system message equals the v1.9 C-10 file". v1.10 did not change C-10, so the sentence is true but will read as stale at v1.11; the spec's own convention elsewhere is "the current C-10 text".
2. D-08's *Default taken* cell now contains two sentences of measurement prose ("Models measured on 2026-09-18 …") that belong in *Alternatives rejected* or the *Owner / status* cell; the default itself is one clause.
3. The Status bullet has begun to re-accumulate history (four versions of narration); v1.8's F-307 trimmed it to two.

**Recommended resolution**

"the current C-10 text"; move the measurement sentence to D-08's status cell; keep the Status bullet to the current increment and one pointer.

---

## 5. Requirements Review

R-01..R-35 are observable obligations, each with a source. R-34 names the three things it changes (the reply, the validation, the report) and its mirror (I-005). R-35 is careful about scope — "exempts an id from the judge and from nothing else" — and E-51 makes that testable. No requirement conflicts with another; the conflicts found are between test rows and a contract (F-401) and between rows that restate one condition (F-403).

## 6. Interface and Data-Contract Review

C-01..C-11 still pin every externally significant shape. K-15 is a real matcher definition. Defects: the validation list's precedence and the `clause` type (F-402); the (a)/(b) drift on the marker (F-404); the schema literal scatter (F-401); the null-verdict paragraph in C-07 (F-403). No rendered surface — the Visual-surface row is n/a.

## 7. State and Failure Review

Unchanged pipeline; no new state. E-48/E-49 give both clause outcomes a defined result; E-50/E-51 do the same for the marker. The one failure-path ambiguity is which coercion is recorded when several apply (F-402).

## 8. Determinism and Algorithm Review

C-05 is closed and total; the step-5 skip for recorded ids is a one-token change and I-010 was updated with it. K-15 is deterministic given the order "collapse, cut, match" — stated. The mock clause is a prefix, so Phase A's byte-determinism argument is one line. F-402's precedence gap is the only source of implementation-dependent bytes, and only under `--judge llm`.

## 9. Edge-Case Review

E-01..E-51 cover the new boundaries (unlocated, blank-for-unrelated, marker on the wrong family, recorded-but-red). Missing: the combined-coercion case and a non-string `clause` (F-402); retired + recorded (F-404); a leading-space clause (F-406).

## 10. Non-Functional Requirement Review

K-08 unchanged. K-15's bounds (12/280) are measurable. The v1.9 proposal's cost note (≈ 20–60 output tokens per edge) is in the proposal, not the spec, which is right.

## 11. Security and Trust-Boundary Review

Unchanged and sound. The clause is text the model copied from text the operator wrote; it introduces no new input to trust. I-007 still keeps statements out of INFO.

## 12. Observability and Provenance Review

Improved again: §8 now shows *which* clause was judged, and a recorded id is visibly labelled in both reports. `judge_strength`'s silent population change (F-405) is the one step backward.

## 13. Testing and Verification Review

Every I/K/E id has a T id and every T id is in §11 (verified). T-75 and T-77 are concrete and mostly complete; T-76 is the apparatus the v1.9 proposal argued for. Defects: F-401 (three rows cannot all pass), the missing sub-cases in F-402/F-404/F-406, and T-34's stale null-case list (F-403).

## 14. Metrics and Evaluation Review

`conformance`, `by_family`, `unknown_rate` are unchanged and reproducible. `judge_strength` needs its population restated (F-405). T-49 now has a floor on its label set that gives the 0.90 bar two misses of headroom and a long-body population — the review's F-303 concern is closed.

## 15. Traceability Review

Intent (§0, both proposals) → R-34/R-35 → contracts → K/E rows → T-75..T-77 → §11: complete. D-21 and D-22 record decisions, alternatives, and dated confirmations. The proposal files are named in Sources. No broken edge; the mechanical check is clean.

## 16. Internal-Consistency Review

Cross-checked: `"1.3"` in §3.3, C-07 heading, C-07 example and rules, and the revision row — agree; the three T-row literals do not (F-401). The RECORDED case in C-05, I-010 and C-11 — agree; E-37 and C-07's Q-001 paragraph do not (F-403). Marker grammar between (a)'s paragraph and (b)'s rule — drift (F-404). Marker text in C-01, R-35, E-50, T-77, D-22 — agree (`*(recorded)*`). E-48 rationale text in C-06, E-48, T-75 — agree. Revision table ascending — yes.

## 17. Architecture Review

Unchanged. v1.9 lives in `judge.py` (validation), `judge_llm.py` (reply), `judge_mock.py` (prefix), `report.py` (key, column), `judge_prompt.md`; v1.10 in `extract.py` (marker), `graph.py` (step 5, eligibility), `report.py` (key, cell). Layer direction preserved.

## 18. Implementation-Agent Readiness

**YES — WITH MINOR CLARIFICATIONS** (after F-401).

Minimum questions an implementer would ask:

1. Which `schema_version` do the goldens carry — `"1.1"`, `"1.2"` or `"1.3"`? (F-401 — the contract says `"1.3"`; the three T rows must be edited before the build or two will be red.)
2. When an `ASSERTS` has an unlocatable clause *and* an out-of-span line, which rationale is recorded? Is `"clause": null` absent or malformed? (F-402 — assume list order, first match; null = absent.)
3. Does a recorded id's passed edge carry a verdict object? (F-403 — no, per C-05; E-37/C-07 must say so.)
4. For `### T-02 *(recorded)* Title`, is the title `Title`? (F-404 — yes, per the paragraph and T-77; (b) must say so.)
5. Are recorded ids in `judge_strength`? (F-405 — assume excluded.)

Only question 1 lacks a safe default, and it is a three-cell edit.

## 19. Quality Scorecard

| Dimension | Score |
| --------- | ----: |
| Scope clarity | 5 |
| Terminology | 5 |
| Requirement precision | 5 |
| Interface completeness | 4 |
| Visual-surface completeness | n/a |
| Data-contract completeness | 4 |
| State/lifecycle definition | 5 |
| Algorithm precision | 4 |
| Failure semantics | 4 |
| Edge-case coverage | 4 |
| Non-functional requirements | 4 |
| Security specification | 5 |
| Observability/provenance | 4 |
| Testability | 3 |
| Evaluation/metrics | 4 |
| Traceability | 5 |
| Internal consistency | 3 |
| Architecture consistency | 5 |
| Implementation readiness | 4 |

Testability and internal consistency each drop one point from the v1.7 review for F-401 alone; both return to 4 when it is fixed.

## 20. Remediation Plan

### P0 — Blocking

- **F-401** — one `schema_version` literal, in C-07; T-73/T-75/T-77 refer to it. (Three cells; do it before `spec-plan`, since the goldens' expected bytes depend on it.)

### P1 — Important (resolve before the v1.9/v1.10 build claims conformance)

- **F-402** — ordered validation list, first match wins; non-string `clause` = absent; coerced `UNKNOWN` records `clause` `""`; two T-75 sub-cases.
- **F-403** — RECORDED added to E-37, C-07's Q-001 paragraph, T-34.
- **F-404** — marker rule shared by (a) and (b); (b)'s `title :=` strips it; `~~T-48~~ (recorded)` in C-08; T-77 sub-case.
- **F-405** — `judge_strength` population excludes recorded ids, stated as a formula; T-37/T-77 arithmetic.

### P2 — Improvement (may be deferred)

- **F-406** — trim the clause in K-15.
- **F-407** — "the current C-10 text"; D-08 cell hygiene; Status bullet trimmed.

Suggested version bump: `v1.10 → v1.11` with `fix(speccheck):` commits per the spec-writing convention.

## 21. Final Verdict

```text
Specification maturity:
Level 3

Implementation readiness:
READY WITH MINOR FIXES

Primary blocker:
NONE once F-401 is applied — until then T-73, T-75 and T-77 pin three different schema_version literals and cannot all pass.

Most important improvement:
State the schema version once (C-07) and have every test row refer to it (F-401); then give the kernel's validation list an order so two builds record the same rationale for the same reply (F-402).
```
