# Specification Review Report

> - **Subject:** `SPEC.md` v1.7 — Specification Conformance Checker (`speccheck`)
> - **Review date:** 2026-09-18
> - **Method:** `spec-review` four-pass method (comprehension, local precision, cross-consistency, implementation simulation) over all 20 dimensions, plus a mechanical cross-check run with the shipped extractor: 190 declared ids (32 R, 11 C, 11 I, 14 K, 47 E, 74 T; 0 retired), every non-T id has a §11 row (116 rows, none undeclared), every I/K/E id is cited by at least one T row, every T id appears in a §11 "Verified by" cell, no dangling R/C/I/K/E/T/D reference anywhere in the document.
> - **Finding IDs:** `F-301..F-307`. `F-001..F-017` (v0.1), `F-101..F-110` (v0.4), `Q-001..Q-011` (v0.5) and `F-201..F-210` (v1.3) are cited inside `SPEC.md` and are not reused.
> - **Disposition:** all seven findings applied in `SPEC.md` v1.8 on 2026-09-18 (see its revision history); D-08 is re-opened for the requester pending three fresh T-49 runs.
> - **Focus:** v1.4 closed every finding of the v1.3 review; v1.5 and v1.6 were built and self-checked. This pass re-reads the whole document but concentrates on the v1.7 change — a heading-declared id's statement is its title plus its section body (R-33, C-01 (b), C-02, C-06, C-07, C-08, C-10, K-14, E-46, E-47, T-72..T-74, D-20) — and on the seams it opens with the pre-existing determinism (I-002), golden-fixture (T-46, T-60) and judge-evaluation (T-49, D-08) contracts.

---

## 1. Executive Summary

`SPEC.md` v1.7 remains an implementation-grade (Level 3) specification. The v1.7 change is small in surface and precise where it matters: the body grammar names its start, its end (the next heading of level $\leq$ the declaring one, outside fences), what it includes (fenced blocks, deeper headings, thematic breaks), what it drops (leading and trailing blank lines), its cap and the cap's marker and Note, and its two degenerate cases (empty body, inner declarations). The `title`/`statement` split keeps the Markdown report byte-identical and puts the whole change into one JSON key and one schema bump. D-20 is confirmed, with the cap's history recorded.

What the new rows do not close is *how a line is a line*. Through v1.6 every statement was whitespace-collapsed, so the spec never had to say how `SPEC.md` is split into lines, whether a trailing `\r` survives, or whether a whitespace-only line is "blank". A body is now carried byte for byte into `speccheck.json`, and I-002 promises byte-identical output on any OS; those two facts meet at a rule the document does not state (F-301). The other two MEDIUM findings are verification seams: T-72/T-73 use "what v1.6 produced" as their oracle, which is unavailable once the goldens are regenerated (F-302), and the C-10 text changed without the spec saying that the recorded T-49 runs — keyed by `judge_prompt_sha256` — no longer count (F-303).

| Severity | Count |
| -------- | ----: |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 4 |

**Strengths:** the body rule is stated once (C-01) and referenced everywhere else, not restated; the cap is a bound with a marker and a Note rather than a silent cut; E-47 makes explicit that the body is context and never grammar; the Markdown report is provably unchanged (C-08 renders `title`, and `title` is the v1.6 statement by construction); the decision row records the number that was changed and why.

**Weaknesses:** (1) line splitting, CR handling and "blank line" are undefined, so two conforming builds can emit different `statement` bytes from a CRLF spec; (2) two new tests name a superseded version as their expected value; (3) the judge-evaluation evidence is silently stale after a C-10 edit; (4) a handful of ATX-heading edge cases (`###` alone, deep indentation, closing hashes) are left to the implementer and, because they now also end bodies, are worth one sentence each.

None blocks implementation. All three MEDIUM findings are one- or two-row edits.

---

## 2. Overall Maturity

**Level 3 — Implementation-grade.** A coding agent can build v1.7 with minimal semantic inference; conformance is objectively testable through §9, two golden fixtures and the packaged self-check. Level 4 is not assigned, for the same reasons as before: the judge's evaluation (T-49) is recorded rather than gated, and §11 still names intended modules for the v1.7 rows until the build replaces them.

---

## 3. Findings Summary

| ID | Severity | Location | Title |
| -- | -------- | -------- | ----- |
| F-301 | MEDIUM | C-01 (b), C-02, I-002, K-09 | Line splitting, trailing `\r`, and "blank line" are undefined for the SECTION BODY, which is now emitted byte for byte |
| F-302 | MEDIUM | T-72, T-73 | The oracle for `title` and for the Markdown report is "what v1.6 produced" — unavailable once the goldens are regenerated |
| F-303 | MEDIUM | C-10, T-49, D-08, §0, D-06 | C-10 changed; the recorded T-49 runs and D-08's status are stale and nothing says so |
| F-304 | LOW | C-01 (b) | HEADING LINE edge cases: bare `###`, indentation $\geq$ 4 spaces, closing `#` run, `###C-03`, setext headings |
| F-305 | LOW | C-01 (b), C-02 | A heading with an empty title and a non-empty body yields a statement that begins with `\n` |
| F-306 | LOW | §9, §11 (C-09) | C-09 is cited by no §9 test row although §11 says T-33 and T-40 verify it |
| F-307 | LOW | Front matter, §1, §12 revision history | Editorial: revision rows out of order, seven versions of history in the Status line, §1 Extractor row omits `title` |

---

## 4. Detailed Findings

### F-301 — Line splitting, trailing `\r`, and "blank line" are undefined for the SECTION BODY

**Severity:** MEDIUM

**Location:** C-01 (b) `SECTION BODY`; C-02 `SpecId.text`; I-002; K-09

**Observation**

C-01 (b) defines the body as "the lines after the HEADING LINE …, leading and trailing blank lines dropped; whitespace inside preserved line for line", and C-07 emits it as the JSON `statement`. The document never says how `SPEC.md` is divided into lines. Through v1.6 this did not matter: every statement was whitespace-collapsed (C-02), so `\r\n` and `\n` produced the same bytes. From v1.7 a body is carried verbatim. `str.splitlines()` drops a trailing `\r`; `text.split("\n")` keeps it; a spec written on Windows, or one checked out with `core.autocrlf`, therefore yields `statement` values that differ by one byte per line between two conforming builds — and I-002 promises byte-identical reports "on any OS". "Blank line" is likewise undefined: a trailing line of three spaces is dropped by one implementer (whitespace-only is blank) and kept by another (only an empty line is blank), again changing `statement` bytes and, at the margin, whether K-14's cap is crossed.

**Why it matters**

The v1.7 change moves the body from "collapsed" to "byte for byte", which is exactly the regime where line-ending and blank-line conventions become observable. The golden fixtures and `--self-check` would pass on the author's machine and fail on a CRLF checkout with no defect in the code.

**Potential consequence**

Golden-fixture and self-check divergence across operating systems and Git configurations; T-36 and T-46 pass or fail depending on how the repository was cloned.

**Recommended resolution**

Add to C-01, next to the fence definition, one rule that every SPEC.md parser follows:

```text
Lines: SPEC.md is split on "\n"; a trailing "\r" on any line is removed before every other rule
  is applied (a CRLF file parses as its LF twin). A BLANK line is one whose text is empty or
  consists only of spaces and tabs. Body lines are re-joined with "\n"; no other whitespace is
  added or removed (trailing spaces on a body line are kept).
```

Reference the rule from C-02 (`text`) and I-002. Extend T-72 with a sub-case: the same spec saved with CRLF line endings yields byte-identical `SpecIndex` and `speccheck.json`; a whitespace-only line after the body's last text line is dropped, one inside the body is kept.

---

### F-302 — T-72 and T-73 use a superseded version as their oracle

**Severity:** MEDIUM

**Location:** T-72 ("`title` equals the statement v1.6 produced"); T-73 ("byte-identical to its v1.6 version")

**Observation**

Two of the new tests define their expected result as the output of the previous version. That is a one-time regeneration check, not a test: once `fixtures/*/golden/` and `speccheck/_selfcheck/` are regenerated (which T-73 itself requires), the v1.6 artifacts exist only in Git history, and a tester running the suite on a fresh clone has no way to evaluate the clause. It also fails the skill's oracle-independence rule — the expected value is the implementation's own earlier output rather than a property the spec states.

**Why it matters**

The clauses are meant to prove two real properties — that `title` is exactly the old statement (so nothing about the Markdown report changed) and that the Markdown renders `title` and never a body. Both are directly assertable without any historical artifact.

**Potential consequence**

The build either skips the clause (leaving the "Markdown unchanged" claim unverified) or hard-codes a copy of the v1.6 goldens into the test tree, which then drifts.

**Recommended resolution**

Rewrite the two clauses as properties of the current output:

- T-72: for every id in both fixture specs, `title` equals the second cell (table) or the heading remainder after the id token (heading), whitespace-collapsed, computed independently in the test; `text == title` for every table-declared id and for every heading-declared id with an empty body; `text.startswith(title + "\n")` otherwise.
- T-73: in each `golden/SPEC_CONFORMANCE_REPORT.md`, the Statement cell of every per-id row equals that id's JSON `title` and contains no newline; no row of §3 contains the K-14 marker; `speccheck.json` and the Markdown agree on the set of ids. Record the one-time v1.6 → v1.7 golden diff (only `schema_version` and `title` keys added; heading-declared `statement`s changed; Markdown unchanged) in `SPEC_BUILD_REPORT.md`, where a one-time observation belongs.

---

### F-303 — C-10 changed; the recorded T-49 evidence and D-08 are stale and nothing says so

**Severity:** MEDIUM

**Location:** C-10; T-49; D-08; §0 and D-06 (the judge question)

**Observation**

v1.7 adds a rule to the C-10 instruction text and correctly notes that `judge_prompt_sha256` changes. T-49 requires three independent runs "recorded with model name, date, and `judge_prompt_sha256`", and the repository's recorded runs (README, `SPEC_BUILD_REPORT.md`) were made under the v1.6 hash and with title-only statements. The spec does not say that a run whose recorded hash differs from the current C-10 hash does not count toward T-49, so the conformance claim for R-26/T-49 can be made against evidence produced by a different prompt over different inputs. D-08 ("Judge instruction text — confirm after the first T-49 run") was not re-opened when the text changed. Separately, §0 and D-06 still phrase the judge's question as "does this test assert the observable behavior this id describes", while C-10 now answers it at the granularity of a clause; the decision row that owns the question should carry the granularity.

The hand labels are less exposed than they look: the golden fixture's only heading-declared id with a body is C-01 (`The error message MUST name the dividend.`), and its judged test asserts that clause (`pytest.raises(ZeroDivisionError, match="7")`), so its `ASSERTS` label holds under the any-clause rule. That was checked by reading the fixture, not by a rule in the spec.

**Why it matters**

T-49 is the only evidence that the instruction text works; the spec ties each run to a prompt hash precisely so that stale evidence is detectable, but stops one sentence short of saying stale evidence is void.

**Potential consequence**

A v1.7 build ships with T-49 "recorded" figures that were measured for v1.6's prompt and statements; a later regression in the judge's behaviour on body-bearing statements goes unnoticed.

**Recommended resolution**

- T-49: add "A run counts only if its recorded `judge_prompt_sha256` equals the SHA-256 of the current C-10 text; a C-10 change therefore requires three fresh runs before T-49 is satisfied. The labels in `judge_labels.json` are re-read against the current statements whenever C-01's statement rule or C-10 changes."
- D-08: status → "confirm — re-run T-49 after v1.7 (text changed 2026-09-18)".
- D-06: add to the default "… at the granularity of a clause: a statement with several clauses is asserted when any one of them is (C-10, v1.7)"; one clause in §0's judge paragraph to match.

---

### F-304 — HEADING LINE edge cases

**Severity:** LOW

**Location:** C-01 (b) `HEADING LINE`

**Observation**

`HEADING LINE := a line, outside fenced code blocks, whose first non-space characters are one to six "#" followed by whitespace`. Because a HEADING LINE now *ends* every body as well as declaring ids, five cases that were harmless before are worth a sentence each:

1. A bare `###` (nothing after the hashes; CommonMark's empty heading) — "followed by whitespace" is not met at end of line, so it is not a HEADING LINE and does not end a body; one implementer will treat it as a heading anyway.
2. A line indented four or more spaces (`    # comment` inside an *indented*, unfenced code block) is a HEADING LINE by this rule and ends the body; CommonMark allows at most three spaces. The same wording governs declarations, so `    ### R-99 x` inside an indented block also declares — a pre-existing property that the body rule now makes more visible.
3. A closing hash run (`### C-03 Title ###`) — CommonMark strips it; the title here keeps it.
4. `###C-03` (no space) — not a HEADING LINE, but (b)'s declaration sentence does not say the declaring line must be a HEADING LINE, so a reader can take "first token after the `#` run" to admit it.
5. Setext headings (`Title` underlined by `===`/`---`) are not HEADING LINEs; a body runs through them. Acceptable for specs written with `spec-writing` (ATX only), but it should be said, and note that a `---` underline is already "body text like any other line".

**Why it matters**

Each is a place two implementers can differ on where a body ends or whether an id is declared. None occurs in the two fixture specs or in this document, which is why the severity is LOW.

**Potential consequence**

A body that swallows or stops at an unexpected line; a phantom declaration from an indented code sample.

**Recommended resolution**

One block in C-01: "ATX headings only; at most three leading spaces (four or more is not a heading and not a declaration); a bare `#` run with nothing after it is a HEADING LINE with an empty title; a trailing run of `#` preceded by whitespace is not part of the title; the declaring line of (b) MUST be a HEADING LINE." Add the indented-block and bare-`###` cases to T-72. If the three-space limit is adopted it changes declaration semantics too — keep the two uses of HEADING LINE on one rule rather than two.

---

### F-305 — Empty title with a non-empty body

**Severity:** LOW

**Location:** C-01 (b) `statement`; C-02 `text`

**Observation**

`statement := title, then — when the SECTION BODY is non-empty — a newline and the SECTION BODY`. For `### C-03` with nothing after the id and a body beneath it, `title` is `""` and the statement begins with `\n`. Harmless to the judge, but it is a leading blank line the same rule says bodies never have, and the Markdown Statement cell is empty while the JSON statement is not.

**Recommended resolution**

"When `title` is empty the statement is the SECTION BODY alone." One sub-case in T-72.

---

### F-306 — C-09 is cited by no §9 test row

**Severity:** LOW

**Location:** §9.5 T-33, §9.7 T-40; §11 row C-09

**Observation**

§11 lists C-09 as verified by T-33 and T-40, but neither row's citation list names C-09 (T-33 cites K-05, K-06, R-26; T-40 cites K-01, E-09, E-21, R-23). Every other R/C/I/K/E id is cited by at least one T row (mechanically checked). Pre-existing; noticed because the cross-check was re-run for v1.7.

**Potential consequence**

Under §9's own rule ("every test cites … the R/C/I/K/E ids it proves"), a test author following the T rows literally never cites C-09, and the T-48 self-application reports it `UNTESTED`.

**Recommended resolution**

Add C-09 to T-33's and T-40's parentheticals (T-33 asserts the URL/model/key/timeout are read from the C-09 variables; T-40 asserts a missing one exits `2`).

---

### F-307 — Editorial

**Severity:** LOW

**Location:** front-matter Status; §1 Extractor row; §12 revision history

**Observation**

1. The revision-history table runs v0.1 … v1.3, v1.7, v1.6, v1.5, v1.4 — the last four are in reverse order after v1.3, because each new row was inserted above the previous one.
2. The Status bullet now narrates seven versions (≈ 1,900 characters) and duplicates the revision table; its job is to say what the current version is and why.
3. §1's Extractor row still says "declared IDs (with statement text, family, retired flag)"; `title` is now a fourth field.

**Recommended resolution**

Sort the revision table ascending; cut the Status bullet to the v1.7 paragraph plus "see revision history"; add `title` to the §1 row. No normative effect.

---

## 5. Requirements Review

R-01..R-33 are observable obligations in normative language, each with a source. R-33 is fully observable: it names the three places the statement appears (`SpecId.text`, `JudgeRequest.statement`, JSON `statement`), the field that preserves the old rendering (`title`), and the one contract it leaves alone (table rows). No requirement conflicts with another; the R-33/I-002 seam (F-301) is an omission in the grammar, not a conflict between requirements.

## 6. Interface and Data-Contract Review

C-01..C-11 pin every externally significant shape. The v1.7 grammar in C-01 (b) is written in the same style as the fence and row rules and reuses them (a HEADING LINE is "outside fenced code blocks"; inner rows and headings are parsed "exactly as before"). C-02 and C-07 agree on `title`/`text`; C-07's example, key order and rules paragraph agree with each other; the schema bump is stated in C-07, §3.3 and the revision row. Defects: the line/blank definition (F-301), the empty-title corner (F-305), and the heading edge cases (F-304). No rendered surface — the Visual-surface row of the scorecard is n/a.

## 7. State and Failure Review

Unchanged from v1.4: §3.1's pipeline is complete for success, exit 2/3 and interruption. v1.7 adds no state and no failure mode — the cap is a deterministic transformation with a Note, never an error — and E-46/E-47 give both degenerate body cases a defined outcome.

## 8. Determinism and Algorithm Review

C-05 is closed and total; metrics are Decimal-quantized; the body rule is deterministic given a line model — which is the gap (F-301). K-14's truncation is precisely specified (whole lines, $\leq$ 16,384 bytes of UTF-8, title line always kept, marker excluded from the cap). The measured sizes cited in K-14 (C-03 of this document 8.4 kB; the largest MonteCarloPi contract 2.7 kB) were re-measured during this review and are correct under the v1.7 rule.

## 9. Edge-Case Review

E-01..E-47 cover the body's two boundary cases (empty; over the cap) and its one structural case (declarations inside it). Missing: CRLF and whitespace-only lines (F-301), the empty title (F-305), and the ATX corner cases (F-304). The `###` immediately before end of file is covered by T-72.

## 10. Non-Functional Requirement Review

K-08 unchanged and still recorded, not gated (D-14 open). K-14 is measurable and its rationale is honest about being a payload bound rather than a working limit. The judge-payload cost is now quantified in the README rather than the spec, which is the right place.

## 11. Security and Trust-Boundary Review

Unchanged and sound. The statement now carries more of `SPEC.md` to the provider; the spec is already explicit that the judge receives spec and test text (C-06, §5.3 DEBUG), so no new boundary is crossed. I-007 still excludes statements from INFO.

## 12. Observability and Provenance Review

Improved: the JSON now records both what the operator wrote (`title`) and what the judge was shown (`statement`), truncation is visible in the statement itself and in a Note, and the prompt hash changes with the text. The one provenance gap is that a stale T-49 record is not declared void (F-303).

## 13. Testing and Verification Review

Every I/K/E id has a T id and every T id is in §11 (verified). T-72 and T-74 are concrete and reproducible with the fixtures they describe; T-73's and part of T-72's oracle is the previous version (F-302). T-49's evidence needs an explicit staleness rule (F-303). C-09's citation gap is pre-existing (F-306).

## 14. Metrics and Evaluation Review

No metric changed. `unknown_rate`, `judge_strength`, `conformance` and their zero-denominator rules are as in v1.0 and remain reproducible from the report.

## 15. Traceability Review

Intent (§0, the proposal) → R-33 → C-01/C-02/C-06/C-07/C-08/C-10 → K-14, E-46, E-47 → T-72..T-74 → §11 rows: complete, and the proposal file is named in Sources. D-20 records the decision, the alternatives, the changed number and its date. The single break is F-306.

## 16. Internal-Consistency Review

Cross-checked: the cap value (16,384) in K-14, T-72, D-20 and the revision row; `schema_version` `"1.1"` in §3.3, C-07 heading, C-07 example and rules, and the revision row; the Note text in K-14 and E-46; the marker text in K-14 only (T-72 refers to it as "the marker line"); `title` semantics in C-01 (a)/(b), C-02, C-07, C-08. All agree. The §3.2 diagram still labels SpecIndex "declared IDs, statements" — accurate. The only drift found is editorial (F-307) and the D-06/§0 wording (F-303).

## 17. Architecture Review

Unchanged. The change lives entirely in the Extractor (title/body/cap), the Reporter (one key) and the LLM provider (pass-through); the Grapher, the mock judge and the status algorithm are untouched, as the revision row claims.

## 18. Implementation-Agent Readiness

**YES — WITH MINOR CLARIFICATIONS.**

Minimum questions an implementer would ask:

1. Split `SPEC.md` on `\n` and strip a trailing `\r`? Is a whitespace-only line blank? (F-301 — assume yes and yes.)
2. What do I compare `title` against in T-72/T-73 once the goldens are regenerated? (F-302 — assume the property form above.)
3. Do the recorded T-49 runs still count? (F-303 — assume no; re-run.)
4. Is `    # x` (four spaces) a heading? Is a bare `###`? (F-304 — assume CommonMark: no and yes.)
5. Empty title with a body — leading newline or body alone? (F-305 — assume body alone.)

None lacks an obvious default; none affects the golden fixtures as they stand.

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
| Failure semantics | 5 |
| Edge-case coverage | 4 |
| Non-functional requirements | 4 |
| Security specification | 5 |
| Observability/provenance | 4 |
| Testability | 4 |
| Evaluation/metrics | 4 |
| Traceability | 4 |
| Internal consistency | 5 |
| Architecture consistency | 5 |
| Implementation readiness | 4 |

## 20. Remediation Plan

### P0 — Blocking

None.

### P1 — Important (resolve before the v1.7 build claims conformance)

- **F-301** — line model in C-01 (split on `\n`, strip `\r`, BLANK := empty or whitespace-only, re-join with `\n`); cite from C-02 and I-002; CRLF sub-case in T-72.
- **F-302** — restate T-72's and T-73's oracle as properties of the current output; move the one-time golden diff to `SPEC_BUILD_REPORT.md`.
- **F-303** — T-49 counts only runs under the current `judge_prompt_sha256`; D-08 re-opened; D-06/§0 name the clause granularity.

### P2 — Improvement (may be deferred)

- **F-304** — ATX-only, three-space limit, bare `###`, closing hashes, declaring line is a HEADING LINE.
- **F-305** — empty title → statement is the body alone.
- **F-306** — cite C-09 from T-33 and T-40.
- **F-307** — sort the revision table; shorten the Status bullet; `title` in §1.

Suggested version bump: `v1.7 → v1.8` with `fix(speccheck):` commits per the spec-writing convention, before or alongside the v1.7 build (the P1 items change no behaviour the build would otherwise get wrong, only what the spec pins).

## 21. Final Verdict

```text
Specification maturity:
Level 3

Implementation readiness:
READY WITH MINOR FIXES

Primary blocker:
NONE

Most important improvement:
State the line model for SPEC.md (split, trailing CR, blank line) so that the section body — now emitted byte for byte — is the same bytes on every OS and every Git checkout (F-301).
```
