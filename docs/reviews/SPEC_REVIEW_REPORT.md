# Specification Review Report

> - **Subject:** `SPEC.md` working tree of 2026-10-27: v1.22 shipped, v1.23 (namespaces and citation map) specified and not built. Specification Conformance Checker (`speccheck`).
> - **Review date:** 2026-10-27
> - **Method:** the `spec-review` four-pass method (comprehension, local precision, cross-consistency, implementation simulation) over all 20 dimensions and the whole document (2,334 lines), plus three mechanical checks: (1) the shipped 1.22.0 checker run over this `SPEC.md` (`check --spec SPEC.md --src src --tests tests --judge none`): 299 declared ids (46 R, 23 C, 19 I, 19 K, 76 E, 116 T), none retired, no dangling or stale citation, and 8 `edge to undeclared id: … -> R-99` Notes, all of them the deliberate `R-99` example idiom; (2) the C-06, C-18 and mock-judge rows read against `judge_llm.py`, `explain.py` and `judge_mock.py`; (3) `git log -S` used to date the C-06 defect.
> - **Finding IDs:** `F-701..F-717`. Earlier ranges (`F-001..F-017`, `F-101..F-110`, `Q-001..Q-011`, `F-201..F-210`, `F-301..F-307`, `F-401..F-407`, `F-501..F-504`, `F-601..F-612`) are cited inside `SPEC.md` or its review files and are not reused.
> - **Relationship to `SPEC_REVIEW_v1.23_fold.md`:** that file was a self-check by the fold's author and asked for an independent pass. This is that pass, and also the first full review since v1.10. It re-reads the whole document rather than only the fold.
> - **Disposition:** all seventeen findings folded into `SPEC.md` v1.23.1 on 2026-10-27 (see its revision history). F-704 took the `mapped: true` branch, F-712 the uncapped-recognition branch, F-716 (a) the stated-limitation branch, and F-707 is recorded as the new T-117 rather than asserted.

---

## 1. Executive Summary

`SPEC.md` is still an **implementation-grade (Level 3)** specification. The deterministic kernel (C-01..C-05, C-07, C-12, C-13) remains among the most tightly specified parts. Its grammars are total, its orders are total, its zero-denominator cases have values, and earlier review rounds closed their findings with row-level fixes. The v1.23 fold is well shaped: it is conditional on its inputs (I-019), it leaves C-05 alone, and it splits E-70's exit codes along K-18's line.

The weak spots are in the increments since v1.13, which were added by appending rows and did not always revisit older rows:

- **The LLM wire format in C-06 is corrupted** (F-701). Since v1.16 a prose paragraph has sat inside the pinned request body, the user-message object has no opening, and the paragraph says the two messages are *not* sent as an array, which contradicts the `"messages": [` line above it. The code is right; the contract R-26 calls "exactly" pinned is not.
- **The citation-map file is not excluded from the scan** (F-702). A map kept where a project naturally puts it (`tests/citation_map.json`) gets scanned by the fallback adapter, so every id it names becomes a literal file-level test citation. Undeclared ids then become dangling citations that `--strict` gates on.
- **The v1.22 JavaScript/TypeScript adapter left four rows behind:** C-14's DECLARED rule (F-705), the mock judge's assertion tokens (F-706), the jest-junit join configuration (F-707), and the tokenizer's regex-versus-division rule (F-708).
- **Several summary lists went stale:** §5.4's exit-3 lists (F-710), the C-18 reason strings measured against C-05's step numbers (F-711), K-18's readability gap (F-709), and the §5.1 flag-table rows (F-715).

| Severity | Count |
| -------- | ----: |
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 11 |
| LOW | 4 |

**Strengths:** C-01's grammar and its fence, heading, row and decision-table rules; C-05 as the only place verdicts act; C-07's Decimal quantization and Note order; the downgrade-only boundary (I-004, I-015) has survived six model-facing increments; K-18 and E-70's 2/3 split; every non-T id has a §11 row and a verifying T.

**Weaknesses:** the same fact restated in three or four places and updated in one or two (exit-3 lists, flag lists, C-14 versus the C-03 JS paragraph); a pinned wire format that nobody re-read after an edit; one v1.23 decision (D-57) that makes `declared` mean two different things.

---

## 2. Overall Maturity

**Level 3 — Implementation-grade.** A coding agent can build v1.23 from this document with few semantic questions, and conformance can be tested objectively through §9, three golden fixtures, `--self-check`, the help goldens and the T-109 byte-identity test. Level 4 is not assigned. The judge's evaluation is recorded rather than gated (by design). The JS/TS join is measured for vitest only. And the defects below show that the spec's normative blocks are not yet mechanically checked against themselves: an edit in v1.16 could corrupt a pinned body without any test failing, because T-33 tests the code, not the spec text.

---

## 3. Findings Summary

| ID | Severity | Location | Title |
| -- | -------- | -------- | ----- |
| F-701 | HIGH | C-06 "LLM provider wire format" | The pinned request body is corrupted: prose inside the JSON, no user-message opener, and a sentence saying the opposite of `"messages": [` |
| F-702 | HIGH | C-03 "Excluded from every scan", C-23 | The `--citation-map` file (and the `--proof-results` manifest) is scanned like any test file, so its ids become literal citations |
| F-703 | MEDIUM | D-57, E-72, C-10, C-14, C-16 | A mapped citation is `declared: true`, which contradicts the definition the judge is given and inflates `declared_ratio` |
| F-704 | LOW | C-23, E-72, C-08 | A mapped dangling or stale citation is reported at a test line that does not contain the id; the map entry that caused it is not named |
| F-705 | MEDIUM | C-14, D-27, R-39 vs C-03 JS paragraph | C-14 says every citation that is not a Python or Swift comment or docstring is INCIDENTAL; C-03 says a JS comment-only line is DECLARED |
| F-706 | MEDIUM | C-06 mock provider, R-22 | The mock judge has no JS/TS assertion token, so every vitest/jest edge is `EXECUTES_ONLY` under `--judge mock` |
| F-707 | MEDIUM (plausible) | C-03 "What the join sees", D-56 | The jest-junit configuration given is not enough for nested `describe`s; `ancestorSeparator` is not named |
| F-708 | MEDIUM | C-03 JS/TS adapter, E-74 | Whether a `/` starts a regular-expression literal or is division is not defined, yet it decides whether a file parses |
| F-709 | MEDIUM | K-18, §5.1 `--spec`/`--results`/`--proof-results` rows | K-18 says validation finishes before any file is read, but "unreadable → exit 2" needs a read; only the citation map states that its readability is part of validation |
| F-710 | MEDIUM | §5.4 table and the `impact`/`explain` paragraphs | Exit-3 lists omit E-65 and E-70, and `explain`'s omits E-05 even though `explain` reads `--results` |
| F-711 | MEDIUM | C-18 "Status and reason" vs C-05 | The reason strings name the wrong C-05 steps, and `<outcome>` omits `error` |
| F-712 | MEDIUM | C-22 FOREIGN, R-101 | A namespace longer than 32 characters makes no FOREIGN match, so the token silently falls back to a local citation |
| F-713 | MEDIUM | T-112, D-51, T-107 | T-112 expects 0 foreign references in this repository, but T-107's own test will carry `platform:R-99` in a scanned docstring |
| F-714 | MEDIUM | §12 D-57 *Affects* | D-57 changes what `declared` means (C-14, C-10, C-16) but its *Affects* cell names none of them |
| F-715 | LOW | §5.1 flag table | The `impact`, `explain` and `--root` rows were not updated for v1.23; the `--namespace`-twice rule is in R-102 only |
| F-716 | LOW | C-23, C-12 ranges | Two small undecided cases: a Python method cannot be addressed by class in a map entry; a range with one foreign endpoint |
| F-717 | LOW | throughout | Editorial: broken Markdown tables, out-of-order rows, stale sentences, proposal-local "Part A/B" labels |

---

## 4. Detailed Findings

### F-701 — The C-06 wire format is corrupted

**Severity:** HIGH

**Location:** C-06, the `LLM provider wire format` block (the line after `{ "role": "system", … }`). Introduced by `f9d8d6c` (v1.16, 2026-09-20).

**Observation**

The pinned body opens `"messages": [ { "role": "system", "content": <the C-10 instruction text, verbatim> },`. The next line is not the user message. It is a prose paragraph ("The user message of each request is, in JSON, the object `{id, statement, related, declared, file, start, end, source}` (Part A adds `declared` … **Part B adds `related`** …)"), and that paragraph includes the sentence *"The two messages of this request are not sent as an array of messages to the provider."* After it come the orphaned tail of the old user-message comment (`formatting; declared = Citation.declared …`) and the closer `> } ] }`. The `{ "role": "user", "content": <…` opener is gone. `judge_llm.py:214-217` sends a two-element `messages` array, which is what the corrupted text contradicts.

**Why it matters**

R-26 requires the provider to use "exactly the request body … pinned in C-06", and T-33 asserts the body "byte-for-byte the C-06 shape". The only pinned shape is now unreadable, and one sentence in it, read literally, forbids the shape the code sends.

**Potential consequence**

A fresh implementation of the provider from this text can send the user object as a third top-level key, or as a single merged message. Either breaks every OpenAI-compatible endpoint. A verifier cannot tell which reading T-33 should enforce.

**Recommended resolution**

Restore the block. Keep prose outside the fence:

```text
"messages": [
  { "role": "system", "content": <the C-10 instruction text, verbatim> },
  { "role": "user",   "content": <JSON text of {id, statement, related, declared, file, start, end, source};
                                  statement = SpecId.text verbatim (R-33, T-74); related per R-38;
                                  declared = Citation.declared for this edge (C-14, C-15);
                                  source = the span, each line prefixed by its 1-based number and one TAB (F-109)> } ] }
```

Delete the "not sent as an array" sentence. Move the `declared`/`related` rationale below the fence, and replace "Part A/Part B" with the version numbers (v1.14, v1.16).

---

### F-702 — The citation map and the proof manifest are scanned as test files

**Severity:** HIGH

**Location:** C-03 "Excluded from every scan (F-002)"; C-23; R-103; T-110.

**Observation**

The exclusion list names `--spec`, `--results`, the report files, `--against` and the temporaries. It does not name the `--citation-map` file, and it does not name the `--proof-results` manifest either (that one is pre-existing). A map is a JSON file whose content is mostly id tokens (`{"id": "R-03", …}`). Placed under a `--tests` root, it goes to the fallback adapter: one file-level case, with one literal test citation per id token.

**Why it matters**

§0 says the checker never reads its own inputs as citations, and F-002 established the rule that any file the run reads as an input is excluded. C-23 breaks that rule for one new input.

**Potential consequence**

Take `tests/citation_map.json`, the obvious location. Every mapped id gains a second, literal, `mapped: false`, `declared: false` citation from a file-level case that never has a result, so it appears under `unrun`. Every map entry for an undeclared id produces a *literal* dangling citation as well as the mapped one, and so does every `R-99`-style example. `declared_ratio` drops. T-110's "reproduces the statuses of the same project with literal citations" holds only if the map lives outside the scan roots, which nothing requires.

**Recommended resolution**

Add "the file named by `--citation-map`, and the file named by `--proof-results`" to C-03's exclusion list (by resolved path, silent, as for `--results`). Extend T-36 or T-110 with a map placed under `--tests`.

---

### F-703 — `declared: true` for a mapped citation contradicts what `declared` means

**Severity:** MEDIUM

**Location:** D-57, E-72, C-23 (`declared = true`); C-10 (field definition); C-14; C-16 / C-07 `declared_ratio`.

**Observation**

C-10 tells the judge: *"declared — true when this test's own docstring or a comment names this ID"*. C-14 defines DECLARED as a citation line inside the case's docstring or on a whole-line comment. A mapped citation is neither, because the test's source does not contain the id at all. D-57 sets `declared: true` anyway. Its reasoning is that the map states the owner's intent. That is a reasonable policy, but it changes the meaning of the field without changing the field's definition.

**Why it matters**

The judge is now told something false about the source it is reading: no line in `source` names the id. `declared_ratio` was defined (C-16) as a measure of the docstring convention, so it now counts map entries as convention-following.

**Potential consequence**

A careful model, told the docstring names the id and finding that it doesn't, may distrust the request or return `UNKNOWN`. `declared_ratio` on a map-retrofitted project reads near 1.0 while no test follows the convention.

**Recommended resolution**

Keep D-57's policy and say it where `declared` is defined: in C-10's text ("…or a citation map the project owner maintains names this test for this ID"), which bumps `judge_prompt_sha256` and voids T-49 runs per F-303; and in C-14, as a third DECLARED bullet. For `declared_ratio`, choose explicitly: either exclude mapped citations from both numerator and denominator (recommended, since the metric measures the in-code convention), or state that they count. Record the choice in D-57.

---

### F-704 — Where a mapped dangling or stale citation points

**Severity:** LOW

**Location:** C-23 ("a dangling citation … at (file, case.start)"); E-72; C-08 ("`file (map)` — it has no line").

**Observation**

A mapped citation carries `line = case.start` internally, `lines: []` in `tests[]`, renders as `file (map)` with no line in the Markdown, and appears in `dangling`/`stale` at `(file, case.start)`. An operator who follows R-24 and greps that file and line will not find the id, because the evidence is in the map.

**Recommended resolution**

List a mapped dangling or stale entry at the map file instead (`{"id", "file": <map path>, "line": <entry's line in the map>}`), or add `"mapped": true` to such entries so the reader knows where to look. Either way, say which in C-23.

---

### F-705 — C-14 was not updated for JavaScript/TypeScript

**Severity:** MEDIUM

**Location:** C-14 (both bullets name only Python and Swift; "Otherwise X is INCIDENTAL"); C-03 DECLARED paragraph; D-27; R-39 §11 row ("Python and Swift"); C-03 JS paragraph ("A citation on a comment-only line is DECLARED (C-14)").

**Observation**

The JS/TS adapter says a comment-only line is DECLARED and cites C-14 for it. C-14, which owns the rule, enumerates Python (`#`, docstring) and Swift (`///`, `/** */`) and makes everything else INCIDENTAL.

**Why it matters**

Read literally, the two rows give opposite answers for `// R-03` above an `it(…)`. Two implementers following different rows produce different `tests[].declared`, `declared_ratio` and judge requests.

**Recommended resolution**

Add a third bullet to C-14 (and to the C-03 DECLARED paragraph): "for JavaScript/TypeScript, a line holding comment text and no code token (the C-03 JS adapter's comment-only line), including every line of a `/* … */` or `/** … */` block". Amend D-27 and the R-39/C-14 §11 rows.

---

### F-706 — The mock judge cannot recognise a JavaScript assertion

**Severity:** MEDIUM

**Location:** C-06 mock provider (`assertion token := …`); R-22; T-69; `judge_mock.py:15-24`.

**Observation**

The assertion tokens are Python (`assert`, `.assert`, `pytest.raises(`) and Swift (`#expect(`, `#require(`, `XCTAssert`, `XCTFail(`, `Issue.record(`). v1.22 added vitest and jest cases, whose assertions are `expect(…).toBe(…)` and similar. None of these matches.

**Why it matters**

The mock judge is the deterministic judge path used by `--self-check`, the golden fixtures and CI-style runs (R-16, R-22). Its job is to stand in for "the test asserts something".

**Potential consequence**

Every id proven only by JS/TS tests is `WEAKLY_PASSING` under `--judge mock`, and `--strict --judge mock` fails for every JS/TS project, the projects R-104 was added for. T-110's JavaScript case is judged under mock, so its own expectations depend on this choice.

**Recommended resolution**

Add JS/TS tokens: a line containing `expect(`, `expect.`, `assert.` or `assert(`. Add a T-69-style sub-test. Note that this changes no existing golden, since no current fixture has a `.ts` file. If the omission is deliberate, say so in C-06 and in R-104.

---

### F-707 — jest-junit nested describe chains need a third setting *(plausible; verify against a real jest run)*

**Severity:** MEDIUM

**Location:** C-03 "What the join sees" (`jest-junit matches when configured classNameTemplate: "{filepath}" and titleTemplate: "{classname} > {title}"`); D-56.

**Observation**

C-03 names each case by joining the `describe` titles with `" > "`. In jest-junit, `{classname}` inside `titleTemplate` is the chain of describe titles joined by the reporter's `ancestorSeparator` option, whose default is a single space. Under the configuration C-03 names, a case inside `describe("calc") > describe("inner")` should therefore produce `calc inner > subtracts`, not `calc > inner > subtracts`. `SPEC_BUILD_REPORT.md` §0m confirms that the jest-junit shape was "documented from its reader contract, not exercised against a real jest run".

**Potential consequence**

Under jest, every test in a nested `describe` is unattributed (E-07), and its id can reach `UNVERIFIED` and no further, which is the symptom R-104 was written to fix.

**Recommended resolution**

Measure one jest + jest-junit run with a nested describe and pin what it writes, as was done for vitest. If the reading above holds, add `ancestorSeparator: " > "` to C-03's configuration sentence and to a T-116-style fixture.

---

### F-708 — Regular-expression literal versus division is undefined

**Severity:** MEDIUM

**Location:** C-03 JS/TS adapter ("regular-expression literals are single opaque tokens"); E-74; T-113.

**Observation**

The tokenizer must decide, at every `/` that is not a comment, whether it starts a regex literal or is a division operator. JavaScript's grammar decides this by syntactic context. The spec gives no rule. Choosing wrongly can swallow a `)` into a "regex", or expose one inside a real regex, and that changes parenthesis balance. Balance decides CALL END, spans, and whether the whole file falls back to file-level (E-74).

**Potential consequence**

Two conforming tokenizers disagree on files such as `if (ok) /x/.test(s)` or `expect(a) / 2`. One delimits the cases and the other reports `parse fallback` and loses every case in the file.

**Recommended resolution**

Pin the conventional rule: a `/` that is not a comment start begins a regex literal iff the previous significant token is absent, or is one-character punctuation other than `)`, `]` and `}`, or is one of the keywords `return typeof instanceof in of new delete void throw case do else yield await`; otherwise it is division. State that `}` is treated as ending an expression (this misreads a regex at the start of a statement after a block, which is rare and only costs a fallback). Add the two example lines above to T-113.

---

### F-709 — K-18 cannot be met as worded for unreadable files

**Severity:** MEDIUM

**Location:** K-18; §5.1 rows for `--spec` ("unreadable file → usage error", `2`), `--results` (`2`), `--proof-results` (`2`), `--against` (`2`); E-65; E-70.

**Observation**

K-18 says flag, value and containment validation "are completed before `SPEC.md`, the results file, the citation map, the output directory or `--against` is read at all". But four flags make *unreadable* an exit-2 usage fault, and unreadability can only be detected by opening, and in practice reading, the file. K-18 settles this explicitly for one file only ("including that a `--citation-map` file exists and is readable"). The implementation (`cli.py:525-679`) reads `--spec`, `--results` and `--proof-results` in its validation stage, which matches the spirit of the rule, not its text.

**Potential consequence**

Take `--results` unreadable (exit 2) together with a spec that declares nothing (E-01, exit 3). An implementation that follows the §3.1 stage order exits 3. One that follows the code exits 2. K-18 was written to stop exactly this kind of disagreement.

**Recommended resolution**

Reword K-18's validation clause to "… and that every file a flag names (`--spec`, `--results`, `--proof-results`, `--against`, `--citation-map`) exists and can be read as bytes …", and keep parsing (E-01..E-03, E-05, E-65's malformed half, E-70's shape half) in the exit-3 stages. Extend T-103 with the `--results`-unreadable plus E-01 pair.

---

### F-710 — Stale exit-3 lists in §5.4

**Severity:** MEDIUM

**Location:** §5.4 row `3` ("E-01, E-02, E-03, E-05, E-18"); the `impact` paragraph ("E-01/E-02/E-03 on either spec, E-18"); the `explain` paragraph ("E-01/E-02/E-03").

**Observation**

E-65 (malformed proof manifest) and E-70 (map shape faults) are exit 3 and appear in none of the lists. `explain` reads `--results` (R-40), so E-05 applies to it, and it reads `--citation-map`, so E-70 does too. `impact` reads the map as well (§3.1 `impact` table: "exit `3` (E-70)").

**Why it matters**

§5.4 is the table operators and the C-19 exit-code epilog take the exit contract from. A verifier writing exit-code tests from §5.4 would miss three cases.

**Recommended resolution**

Row `3`: "E-01, E-02, E-03, E-05, E-18, E-65, E-70 (shape half)". `impact`: "… E-18, E-70". `explain`: "E-01/E-02/E-03, E-05, E-70". Better still, make the row say "every E row whose Semantics column says exit `3`", so the list stops being a copy.

---

### F-711 — C-18's reason strings cite the wrong C-05 steps

**Severity:** MEDIUM

**Location:** C-18 "Status and reason"; C-05; `explain.py:23-28`; T-92, T-93.

**Observation**

C-05 numbers its steps 1 = RETIRED, 2a/2b = UNCITED/UNTESTED (2b is the T-family branch), 3 = UNVERIFIED, 4 = FAILING/SKIPPED/PASSING, 5 = WEAKLY_PASSING. C-18 renders `UNCITED → step 1`, `UNTESTED → step 2`, `UNVERIFIED → step 2b`, `FAILING`/`SKIPPED → step 3`, `PASSING → step 4`. Only `WEAKLY_PASSING → step 5` is right. R-40 promises "the C-05 step that set it". The code copies C-18, so the shipped trace is wrong for six of eight statuses. Separately, `<outcome>` lists `passed`, `failed`, `skipped` or `—`, and omits C-04's fourth outcome, `error`.

**Potential consequence**

An operator who follows the trace's step number back to C-05 lands on the wrong rule (C-05's "step 2b" is the *T-family UNCITED* branch, not UNVERIFIED). A second implementation that renders the true step numbers fails T-92's pinned `step 4: …` string only by coincidence of that one row.

**Recommended resolution**

Change the strings to match C-05: `RETIRED → step 1`, `UNCITED → step 2a` (or `2b` for a T id), `UNTESTED → step 2a`, `UNVERIFIED → step 3`, `FAILING`/`SKIPPED`/`PASSING → step 4`, `WEAKLY_PASSING → step 5`. Add `error` to `<outcome>`. This is a visible change to T-92/T-93's expected text; record it in the revision history.

---

### F-712 — A long namespace silently becomes a local citation

**Severity:** MEDIUM

**Location:** C-22 `FOREIGN` (`(?<![A-Za-z0-9])(?P<ns>[A-Za-z][A-Za-z0-9_-]{0,31}):…`); R-101.

**Observation**

The left look-behind forbids a match that starts mid-word, and `ns` is capped at 32 characters. A 33-character label (`regulated_platform_core_services_v2:R-03`) therefore yields no FOREIGN match. The TOKEN rule then sees `:` as a boundary and records `R-03` as a local citation. This is the false-green R-101 exists to close, and it happens without a Note.

**Recommended resolution**

Either drop the length cap from the *recognition* regex (`[A-Za-z][A-Za-z0-9_-]*`) and keep the 32-character limit for `--namespace` values only, or keep the cap and emit a Note ("namespace-like prefix longer than 32 characters read as local: …"). The first is simpler and has no false positive that the current rule lacks. Add the case to T-107.

---

### F-713 — T-112's "expected 0 here" will be false after the build

**Severity:** MEDIUM

**Location:** T-112; D-51 ("this repository's own scan finds no code or test using the old reading"); T-107 ("A test docstring naming `platform:R-99` …").

**Observation**

The v1.23 suite will contain `platform:R-99` (T-107, T-108) and probably more `ns:ID` text, inline in `tests/test_*.py`, unless a rule puts it elsewhere. T-48's self-application and T-112's "before and after" run then find foreign references in this repository. F-109's rule for `speccheck:ignore` markers ("MUST live in data files under `tests/data/`") has no counterpart for foreign tokens.

**Potential consequence**

T-112 records a non-zero count for this repository, the evidence D-51 says would reopen D-51, purely as an artefact of the suite. Its "ids, statuses identical before and after" also fails if any v1.23 test cites a real id with a prefix.

**Recommended resolution**

Extend §9's preamble rule to foreign tokens: test inputs containing `<ns>:ID` text live under `tests/data/`. Alternatively, restate T-112 as "excluding the files that carry the T-107/T-108 fixtures" and name them.

---

### F-714 — D-57's *Affects* cell omits the rows it changes

**Severity:** MEDIUM

**Location:** §12 D-57 *Affects* = `R-103, C-23, E-72, T-110`.

**Observation**

D-57's decision is about what `declared` means for the judge. Its own prose names the judge's `declared` context, which C-10 defines, C-14 computes and C-16 aggregates. None of those ids is in the cell. Under C-01 (c) and C-12, the cell is read mechanically as `affects` edges, so `impact --changed D-57` reaches neither C-10 nor C-14 nor C-16, and the reviewer of a later change to D-57 is not told to re-verify T-85, T-86 or T-88.

**Recommended resolution**

D-57 *Affects*: `R-103, C-10, C-14, C-16, C-23, E-72, T-110`. Do it together with F-703, which is the same decision seen from the contract side.

---

### F-715 — The §5.1 flag table was not updated for v1.23

**Severity:** LOW

**Location:** §5.1 rows `impact` ("Accepts `--spec`, `--src`, `--tests`, `--root`, `--out`, `--verbose`"), `explain ID` (its accepted-flag list), `--root` ("All of `--spec/--src/--tests/--results/--out` MUST resolve inside it"), `--namespace`.

**Observation**

The synopsis gives `impact` and `explain` the two new flags, but their behaviour rows still enumerate the old sets. The `--root` row omits `--proof`, `--proof-results`, `--against` and `--citation-map`, all of which E-09 or their own rows contain. The rule that a second `--namespace` is exit 2 with `--namespace: given more than once` lives only in R-102, not in the flag's own row or in E-68.

**Recommended resolution**

Append `--namespace` and `--citation-map` to both accepted-flag lists. Make the `--root` row say "every path flag (E-09)". Copy R-102's at-most-once rule into the `--namespace` row and into E-68.

---

### F-716 — Two small undecided cases

**Severity:** LOW

**Location:** C-23 (`test` = `TestCase.name`); C-12 Ranges together with C-22.

**Observation**

(a) A Python method's `TestCase.name` is the bare function name (C-03), so two `test_x` methods in different classes of one file are indistinguishable to a map entry. C-23 resolves them deterministically to the one with the smallest `start`, and the other cannot be mapped at all. (b) `platform:R-01..R-05`: the first endpoint is foreign and so "not a token for this pass", the second is a bare token. Whether the range expands, which would make R-02..R-04 local edges, is undecided.

**Recommended resolution**

(a) Allow an optional `"class"` key, or accept `Class.test_x` in `test`, matched against the classname suffix. If not, state the limitation in C-23. (b) Add one sentence to C-12: a range whose first endpoint is a foreign reference names nothing beyond its own bare endpoint.

---

### F-717 — Editorial (one finding per kind)

**Severity:** LOW

- **Broken tables.** A prose paragraph ("Every row of this table is also stated …") splits the §5.1 flag table, so every row after it (`--self-check` onward) renders as plain text. Blank lines detach T-89 (§9.5), T-90 (§9.7) and T-91 (§9.11) from their tables. The checker still declares them, because C-01 (a) needs only a row, but `spec2pdf.sh` and GitHub render them as pipe-filled paragraphs.
- **Order.** R-104 precedes R-101..R-103 in §2. §8 runs E-64, E-66, E-74..E-76, E-67..E-73, E-65. §11 interleaves the same way. Sort by number.
- **Stale sentences.** O-2: "Go and JS/TS remain optional" (JS/TS shipped in v1.22). C-12: "The judge (C-06) is not shown edges in v1.13" (R-38 has shown the `depends_on` neighbourhood since v1.16). E-14: "`judge_available` set `false` if *every* call failed" (C-07 since v1.20 also covers the never-issued case). §0 "Previous status" chain skips v1.21, and the "Sources" bullet stops at the v1.16 proposals.
- **Proposal-local labels.** "Part A", "Part B", "Part C" (C-06, C-16, E-57, T-84, T-86) refer to sections of proposals, not of this document. Replace them with the version number or the id.
- **Mixed order phrases.** R-38 says `related` is "in C-07 id order", while the C-10 text says "in the order of that section". Use one.

---

## 5. Requirements Review

The R rows are observable and almost all carry a condition, an input, a result and a failure case. R-100..R-104 continue that style. Two requirements are now stated inconsistently with their contracts: R-40's "the C-05 step that set it" (F-711), and R-39's scope, which C-03 widened to JS/TS without C-14 following (F-705). No requirement conflicts with another. R-15 and R-28 still define the only gates, and nothing in v1.23 adds one, which is consistent with D-55.

## 6. Interface and Data-Contract Review

C-01..C-05, C-07, C-12 and C-13 are complete: types, orders, defaults, null cases and versioning are all stated, and `schema_version` is stated in one place (F-401's fix holds). C-22's grammar is precise apart from the length edge (F-712). C-23's file format, resolution and counts are precise, but its interaction with the scan (F-702), with `declared` (F-703) and with error locations (F-704) is not. C-06's wire format is the one corrupted interface (F-701). The JS/TS adapter (C-03) is precise about calls, titles and spans, but leaves the tokenizer's hardest decision open (F-708), and its jest-junit join is asserted rather than measured (F-707). **Visual surface:** n/a. The product is a CLI with byte-pinned text outputs (summary line, C-08, C-13, C-18, help goldens), and those are specified as text contracts with their own regexes and goldens.

## 7. State and Failure Review

The run is a stateless pipeline. Its only state machine is the write discipline of §3.1 (leftover deletion, nonce temporaries, JSON-then-Markdown rename, cleanup on any failure including SIGINT), and it is complete. The failure model per stage is explicit (§3.1 "Fails with"). Partial-judge failure, budget exhaustion and triage failure each have a defined outcome. The remaining gap is K-18's treatment of unreadable files (F-709), and the exit-3 inventory is out of date (F-710). There are no retries anywhere, by design (K-06).

## 8. Determinism and Algorithm Review

Determinism is strong. Every output list has a total order, ratios are Decimal-quantized, Notes are code-point sorted, and the edge order covers D ids. The algorithms with a gap are the JS tokenizer (F-708) and two corners (F-716). The K-15 matcher, the K-12 `N%` count (as a ceiling), C-11's bar and estimate, and the C-13 breadth-first walk with its `via` tie-break are each fully determined.

## 9. Edge-Case Review

§8 now has 76 rows and covers the empty, duplicate, oversized, malformed, retired, recorded, and interrupted cases of every input. New edge cases found in this pass: a map under a scan root (F-702), a namespace longer than 32 characters (F-712), a range with a foreign endpoint (F-716 b), same-name Python methods addressed by a map (F-716 a), jest nested describes (F-707), and regex versus division (F-708).

## 10. Non-Functional Requirement Review

K-08 (performance) is measurable, with a named reference machine, and recorded rather than gated by stated choice. K-02, K-14 and K-19 are byte limits with stated behaviour beyond them. K-05, K-06, K-12 and K-13 bound the judge's time and concurrency precisely. There is no performance statement for the JS tokenizer or for a 2 MiB map with about 50,000 entries. Neither is likely to matter at K-08's scale; P2.

## 11. Security and Trust-Boundary Review

The trust boundaries are well stated: the network boundary (I-006, enforced by the socket guard in `--self-check`), secret hygiene (R-23, I-007, redaction in C-09/C-17, help screens carry no values), read-only inputs (I-001), `--root` containment of every path (E-09), and the downgrade-only model (I-004, I-015). v1.23 adds one trust input, the map, which can only add citations of tests that already exist. It cannot create a passing outcome, so it cannot fabricate green beyond what a literal citation could. Nothing to report beyond F-702, whose effect is wrong evidence, not escalation.

## 12. Observability and Provenance Review

Every status points at `file:line`; the judge's verdicts carry evidence, clause, rationale and the prompt hash; and `explain` renders the whole trail. Provenance is weakened in two places: the trail's step label is wrong (F-711), and a mapped dangling or stale entry points at a line that does not contain its id (F-704). `citation_map` counts and the foreign Note (F-609's fix) are good additions.

## 13. Testing and Verification Review

Every R/C/I/K/E id has at least one verifying T, and the shipped checker confirms that no T id is unreferenced. Oracles are independent where it matters: golden fixtures are hand-planted with known defects (T-46, T-47), metrics are recomputed independently (T-37), the JS join is checked against measured vitest output (T-116), and the help tokens are checked against the validator (T-95). Gaps: no test reads C-06's *spec text* (T-33 tests the code against an expected body the test author wrote, which is how F-701 survived); no test places a map under a scan root (F-702); and T-112's expected value conflicts with T-107's fixture placement (F-713). Recorded tests are honestly marked `*(recorded)*`.

## 14. Metrics and Evaluation Review

`conformance`, `by_family`, `judge_strength`, `unknown_rate` and `declared_ratio` each have a formula, a population and a zero-denominator value. `declared_ratio`'s population becomes ambiguous under v1.23 (F-703). Its denominator, "all such citations", is still prose rather than an expression. A precise form would be:

$$
\mathrm{declared\_ratio} = \frac{|\{c \in C : c.\mathrm{declared}\}|}{|C|}, \qquad C = \{\, c : c.\mathrm{kind} = \texttt{test},\ c.\mathrm{family} \in \{R,C,I,K,E\},\ c.\mathrm{id} \text{ in scope},\ c.\mathrm{testcase} \text{ not file-level} \,\}
$$

Here $C$ is restricted to citations in non-file-level cases, which is R-39's population and what the shipped code computes, and the ratio is `null` when $|C| = 0$. (The first version of this report wrote that file-level citations were included. That was wrong, and the v1.23.1 fold initially copied it. It was corrected before the build.) Under F-703's recommendation, $C$ additionally requires $\neg c.\mathrm{mapped}$. T-49's judge-accuracy evaluation is well defined: three runs, no pooling, the hash tied to C-10.

## 15. Traceability Review

The intent → R → C → I/K/E → T → evidence chain is complete for every id (§11 has one row per non-T id, and the self-application run shows no dangling id). The §12 *Affects* cells parse cleanly (no undeclared id) except where they are deliberately prose. One cell is incomplete (F-714). The §11 "where realized" column still names intended modules for the v1.23 rows, as it should before the build.

## 16. Internal-Consistency Review

The main source of defects. Findings F-701, F-705, F-709, F-710, F-711, F-714, F-715 and the stale sentences in F-717 all have the same shape: a fact stated in several places, with one place updated. The cheapest structural fix is to make summary rows reference their owner instead of copying it, as §5.4 row `3` could ("every E row that exits `3`"), and as F-401 already did for `schema_version`.

## 17. Architecture Review

The component split (Extractor, Attributor, Results Mapper, Grapher, Judge, Triage, Reporter, Impact walker, CLI) still supports every requirement, and dependencies point one way. v1.23 places map resolution in a new `apply-map` stage owned by the Extractor (§3.1), but §11 assigns it to `cli.py` (C-23, E-70..E-73). Either is fine, but the two tables should agree. The JS adapter's standard-library constraint (D-56) is what makes F-708 a spec problem rather than a library choice. That is a consistent trade-off, and pinning the rule finishes it.

## 18. Implementation-Agent Readiness

**YES — WITH MINOR CLARIFICATIONS.**

Blocking questions an implementer of v1.23 would have to ask:

1. Is the `--citation-map` file excluded from the `--tests` scan? (F-702)
2. Does a mapped citation count in `declared_ratio`, and is C-10's definition of `declared` amended? (F-703)
3. Does an unreadable `--results` or `--spec` count as a usage fault for K-18's precedence? (F-709)
4. What exactly is the user message of the LLM request? (F-701; answerable from the code, not from the spec)

Non-blocking questions (a reasonable choice is safe): F-704, F-706, F-707, F-708, F-711, F-712, F-716.

## 19. Quality Scorecard

| Dimension | Score |
| --------- | ----: |
| Scope clarity | 5 |
| Terminology | 4 |
| Requirement precision | 4 |
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
| Testability | 4 |
| Evaluation/metrics | 4 |
| Traceability | 4 |
| Internal consistency | 3 |
| Architecture consistency | 4 |
| Implementation readiness | 4 |

## 20. Remediation Plan

### P0 — Blocking (before the v1.23 build)

- **F-702:** exclude `--citation-map` and `--proof-results` files from every scan.
- **F-701:** restore C-06's pinned body.
- **F-703 + F-714:** settle what `declared` means for a mapped citation in C-10, C-14 and `declared_ratio`, and widen D-57's *Affects*.

### P1 — Important (before claiming v1.23 conformance)

- **F-705, F-706:** finish the JS/TS adapter's reach into C-14 and the mock judge.
- **F-709, F-710:** K-18 readability wording; §5.4 exit-3 lists.
- **F-711:** C-18 step labels and `error`.
- **F-712:** FOREIGN length edge.
- **F-713:** foreign-token fixtures under `tests/data/`.
- **F-707:** measure jest-junit nested describes (or mark the jest path as unmeasured in R-104).
- **F-708:** pin the regex-versus-division rule.

### P2 — Improvement

- **F-704, F-715, F-716, F-717.**

## 21. Final Verdict

```text
Specification maturity:
Level 3

Implementation readiness:
READY WITH MINOR FIXES

Primary blocker:
The citation-map file is not excluded from the scan, so a map kept under the tests tree turns every id it names into a literal, file-level, never-run citation (F-702).

Most important improvement:
Stop restating facts in summary rows: have §5.4, the §5.1 flag rows, C-14 and C-18 reference the row that owns each fact, which removes the class of drift behind seven of these seventeen findings.
```
