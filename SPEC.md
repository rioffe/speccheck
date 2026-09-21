# SPECIFICATION — Specification Conformance Checker (`speccheck`; traceability graph, JUnit results, model-judged test strength; Python 3.12 + uv)

> - **Status:** v1.18 — the CLI documents its own parameters and environment (R-41, C-19, I-017; T-95..T-98; `PROPOSAL_v1.18_cli_help_contract.md`, 2026-09-20; D-37..D-42 confirmed on the recommended branches). Every argument definition of the three parsers carries a help entry naming purpose, accepted values as literal tokens, the default and every precondition (C-19), and every `--help` screen carries an `environment:` block naming the eight `SPECCHECK_*` variables with their read condition, requiredness and default plus `COLUMNS` (D-41), and an exit-code/summary-line epilog (D-40). The help's value tokens are the validator's own usage-error tokens (T-95), every definition must carry help and a C-19 metavar (T-96), the screens are byte-pinned at `COLUMNS=80` (T-97, D-39), and the environment block is bound to the code's own `SPECCHECK_*` literals (T-98). No accepted value, default or exit code changes; C-06's wrong variable name (`SPECCHECK_LLMMODEL` → `SPECCHECK_JUDGE_MODEL`) is fixed here because v1.16 and v1.17 had already landed (D-42).
>
> - **Previous status:** v1.17 — `speccheck explain <ID>` (R-40, C-18, I-016, E-60, E-61; `PROPOSAL_v1.17_explain_id.md`, 2026-09-20; D-33..D-36 confirmed) adds a third subcommand that renders one id's evidence trail — its statement, its status and the C-05 step that set it, its source and test citations with each citing case's outcome and verdict, and the C-12 blast radius at `--depth` — as one stdout trace. It computes nothing new: it is a renderer over the `IdRecord`/edge/`Verdict` facts `check` already produces and the `walk`/`reverify` facts `impact` already runs (I-016), writes no report file (D-33), and carries `check`'s judge contract unchanged (E-61).
>
> - **Previous status:** v1.16 — a judged edge now receives `related`, the titles of the other obligations its own statement names and that name it (a C-12 `depends_on` neighbourhood, both directions), so the judge can tell an assertion about this clause apart from an assertion about a neighbour it refers to (`PROPOSAL_v1.14_obligation_aware_judge.md`, 2026-09-20; D-28 and its sub-decision D-28b confirmed). R-38 requires the request to carry `related` — the neighbourhood, own references first, at most eight, each a whitespace-collapsed 160-character title, a retired neighbour tagged `(retired)` (E-57), `[]` when the id has no neighbour — and C-10 defines that an assertion corresponding only to a related obligation is not evidence this statement holds, advisory, no new coercion rule (D-28 extends D-26's stance); the field is request-side only, so no `speccheck.json` field, status, Markdown row, or `schema_version` changes, and it also rides the C-17 Jev triage `state` (D-28b), roughly doubling that input. v1.15 — a truncated judge budget can now be spent on the edges Jev is least sure about (`PROPOSAL_v1.16_jev_pre_triage.md`, 2026-09-20; D-29..D-32 confirmed). A new `--jev-pre-triage` flag (K-16) sends one triage task per judge-eligible edge — the C-06 request object for that edge, rendered as C-17's `state` text — to the C-17 Jev provider before any real-judge request is issued, and orders the otherwise unchanged real-judge issue loop (K-05, K-06, C-06) by ascending Jev top-choice probability, ties by ascending id; Jev's answer is read for that order and discarded (I-015). `--judge-budget` grows an `N%` form (K-12): exactly $\lceil N/100 \times E \rceil$ of the $E$ eligible edges, least-confident first, are issued, and the rest take today's `judge: budget` disposition; `N%` requires `--jev-pre-triage` under `--judge llm` (E-58), the `SECONDS` form is unchanged, and `0%` is a pure triage dry run. A per-edge Jev failure orders that edge first and is counted in one Note (E-59). No `speccheck.json` field, no status, no Markdown row, and no `schema_version` changes (D-29..D-32). v1.14 — a citation's own words now tell the checker, and the judge, whether a test *declares* an id or merely *reuses* it (`PROPOSAL_v1.15_declared_vs_incidental_citations.md`, 2026-09-20; D-26 and D-27 confirmed). A citation of an in-scope R/C/I/K/E id inside an attributed test case is **DECLARED** when its line sits inside that case's own docstring or is a whole-line comment, and **INCIDENTAL** otherwise (C-03, C-14; R-39); `Citation.declared` and a new `JudgeRequest.declared` (C-06, C-15) carry the fact into the judge, and `C-10`'s instruction text asks the model not to credit `ASSERTS` on an INCIDENTAL citation without checking the assertion is actually about that clause — advisory only, no new coercion rule (D-26's `yes` branch). `speccheck.json` gains `tests[].declared` and `metrics.declared_ratio` under every `--judge` mode, including `none` (C-07, C-16, `schema_version` `"1.5"`). Detection is whole-line-comment only, reusing the doc-comment-line recognition the Swift adapter already has rather than adding token-level parsing (D-27's `yes` branch; E-56, I-014). Statuses, the mock judge, and the Markdown report are unchanged. v1.13 made the edges this document already carries into data and added a second subcommand that walks them (D-24, D-25); v1.12 made `--src`/`--tests` comma-separated lists of files and/or directories (D-23, I-012, E-52); v1.11 applied F-401..F-407; v1.10 settled D-22 (R-35); v1.9 added clause-grounded verdicts (R-34). Earlier versions: see the revision history.
> - **Language / stack:** Python 3.12 | standard library for the deterministic kernel (`re`, `ast`, `xml.etree`, `json`, `argparse`, `pathlib`) | CLI only; optional model-backed judge behind an `[llm]` extra
> - **Sources:** `one_sentence_prompt.md` (the brief); `../skills/spec-writing/SKILL.md` (the ID taxonomy and `SPEC.md` shape the checker consumes); `../skills/spec-build/SKILL.md` §Phase 3 (the manual conformance audit this tool automates); `../skills/spec-review/SKILL.md` §3.17 (the intent → requirement → contract → invariant → test → evidence chain); `../outline.md` Chapters 15–18 (where this system is the worked example); `SPEC_REVIEW_REPORT.md` (one file, rewritten per review: v0.1 → F-001..F-017, v1.3 → F-201..F-210, v1.7 → F-301..F-307, v1.10 → F-401..F-407; all cited below); `FINAL_SPEC_REVIEW_REPORT.md` (review of v0.4; F-101..F-110 below point at it); `SPEC_v0.5_REVIEW_REPORT_by_QWEN.md` (independent review of v0.5 by a second model; its F-001..F-011 are cited below as Q-001..Q-011 to avoid collision); `PROPOSAL_v1.7_heading_bodies.md` (the v1.7 change, its evidence, and D-20); `PROPOSAL_v1.9_clause_grounding.md` (the v1.9 change, its two-model evidence, D-21, and the D-22 question); `PROPOSAL_v1.13_impact.md` (the v1.13 change, its measurement of the edges in this document — 186 `depends_on`, 240 `verifies`, 110 `affects` in v1.12 — and D-24, D-25); `PROPOSAL_v1.15_declared_vs_incidental_citations.md` (the v1.14 change; `JUDGE_CROSSCHECK_REPORT.md` §2b's cross-model evidence — 153/613 genuine judge conflicts on this document's own `check --judge llm` run, concentrated in ids reused as generic fixture data — and D-26, D-27); `PROPOSAL_v1.16_jev_pre_triage.md` (the v1.15 change; its §1 calibration measurement — Jev's top-choice probability bucketed against a real `check --judge llm --strict` run's committed verdicts on this repository's own `SPEC.md`, monotonic from 53/111 = 47.75% below 0.60 to 279/295 = 94.58% at $\geq$ 0.95 over 582 edges, and 51.5% of all judge-eligible edges already at $\geq$ 0.95 — plus D-29..D-32); `PROPOSAL_v1.14_obligation_aware_judge.md` (the v1.16 change; its sec. 1 evidence — the cross-checker's finding that a test can cite an id as placeholder data while asserting a fact about a neighbour it names, `JUDGE_CROSSCHECK_REPORT.md` sec. 2b — plus D-28 and its D-28b sub-decision)
> - **Scope of this document:** The deterministic conformance kernel (spec-ID extraction, citation graph, test-result mapping, status computation, reporting) and the contract around the optional model-backed *judge*. It does not specify the quality of the specification under check (`spec-review` owns that), does not specify how tests are run (results are consumed, not produced), and does not specify any semantic analysis of source code. Since v1.13 it also specifies the typed edges between declared ids that the kernel records (C-12) and the `impact` walk over them (C-13); it does not specify what an edge *means* — an edge records that one statement names another id, nothing more. Since v1.15 it also specifies the optional Jev triage pass that orders — and, under `--judge-budget N%`, truncates — the queue of edges the judge is asked about (K-16, C-17, I-015); that pass is never the source of a status, and it does not change what the judge is asked or how its answer is validated. Since v1.16 it also specifies the `related` field a judged edge's request carries — the C-12 `depends_on` neighbourhood of the statement — so the judge can distinguish an assertion about the clause from one about a neighbour it names; `related` is a request-side, non-report field, carries no status or metric or `speccheck.json` key, and rides the triage `state` as well as the real-judge request (R-38, C-06, C-10, D-28, D-28b).
> - **Normative language:** MUST/MUST NOT/SHALL/SHALL NOT = normative; SHOULD = strong recommendation; MAY = optional.
> - **Principle:** *The model may only ever make the news worse.* Every status is computed deterministically from evidence the operator can `grep`; the judge is permitted to downgrade a status with cited evidence, never to upgrade one, and every claim in the report points at a file and line.

---

## 0. Intent and purpose

`speccheck` answers one question about a project: **for every ID the specification declares, what evidence exists that the implementation realizes it?** It reads a `SPEC.md` written in the house ID taxonomy (R-nn requirements, C-nn contracts, I-nnn invariants, K-nn constraints, E-nn edge cases, T-nn tests), finds where each ID is cited in the source and test trees, joins those citations to the outcomes in a JUnit XML results file, and writes a conformance report in which every ID has exactly one status and every status has traceable evidence.

This is Phase 3 of `spec-build` ("re-read the spec and audit every artifact") made mechanical. Humans doing that audit are slow and get tired; agents doing it are fast and confabulate. The design splits the work accordingly:

- The **deterministic kernel** does everything that can be done by pattern, graph, and arithmetic: which IDs exist, which are cited where, which tests ran and how they ended, what that makes each ID's status, and what the coverage ratios are. Two runs on identical inputs produce byte-identical reports.
- The **judge** — a model-backed component, off by default — answers exactly one question per (test case, ID) edge: *does this test assert the observable behavior this ID describes, or does it merely execute code near it?* — at the granularity of a clause: a statement with several clauses (a pinned interface and the prose around it, R-33) is asserted when a test asserts any one of them (C-10). Its answer MUST cite lines inside the test and MUST quote the clause of the statement it judged against; an answer without valid evidence, or whose clause cannot be found in the statement, is discarded as `UNKNOWN` (v1.9, R-34). The judge can turn a `PASSING` into a `WEAKLY_PASSING`; it can never turn anything into `PASSING`. It is never consulted about a *recorded* test — a T id marked `*(recorded)*` whose proof is a recorded run rather than an assertion (v1.10, R-35).
- The **triage pass** — a second, optional model-backed component, off by default, enabled by `--jev-pre-triage` (v1.15) — answers the same question about *every* judge-eligible edge before the judge is asked about any of them, and its answers are used for exactly one thing: the order in which edges are issued to the judge (K-16). A budgeted run (`--judge-budget`, K-12) then spends itself on the edges the triage is least sure about instead of on whatever declaration order produced first. Its verdict, probabilities, and rationale are never validated against C-06, never written to `speccheck.json` or the Markdown report, and never the source of a `Verdict` (I-015).

**Why this boundary (context the implementer should not re-derive):** a checker that lets a model decide conformance has merely moved the vibe-coding problem one level up — the report becomes something to trust rather than something to verify. Keeping the model on the downgrade-only side of the line means a green report is as trustworthy as `grep` plus the test runner, and a yellow one carries a reason you can click on. The triage pass sits on the same side of that line: it may reorder the judge's queue and, under K-12's `N%` form, shorten it, but it can never write a verdict, a clause, or a status.

- The **`explain` surface** (v1.17) — a third subcommand, `speccheck explain <ID>` — renders one id's
  evidence trail as a single readable trace on stdout: its statement, its status and the C-05 step
  that set it, its source citations, each citing test case with its outcome and its verdict, and the
  C-12 blast radius a change to it might touch. It computes nothing new — it is a renderer over the
  `IdRecord`/edge/`Verdict` facts `check` already produces and the `walk`/`reverify` facts `impact`
  already runs (R-40, C-18, I-016) — and it writes no report file (D-33).

- The **help surface** (v1.18) — the CLI documents its own interface: every flag's purpose, its
  accepted values as literal tokens, its default and every precondition under which it is ignored
  or rejected, plus the environment the kernel reads and the exit-code contract, all reachable from
  `--help` (R-41, C-19). The value tokens are the *validator's own* tokens (T-95) and the
  environment block is bound to the code's own `SPECCHECK_*` literals (T-98), so the help cannot
  rot the way a prose copy without a mechanical tie does; `--help` itself reads nothing and exits
  `0` (I-017).

**Non-goals (explicit, to constrain the solution space):**

- No semantic analysis of source code — no type inference, control-flow, or "does this function implement R-07" reasoning, by the kernel *or* the judge. Source citations are literal token matches.
- No test execution. The checker consumes a results file; it never runs `pytest`, `go test`, or anything else.
- No spec-quality review (ambiguity, contradictions, missing sections). That is `spec-review`.
- No remediation. The checker reports; it never edits the spec, the code, or the tests.
- No multi-repository or multi-spec runs; one spec, one source tree set, one results file per invocation. `impact --against` reads a second spec file only as a *prior version of the same spec*, to diff its declarations against `--spec`; the prior version is never checked, scanned for, or reported on (C-13).
- No change semantics. An edge (C-12) records that one statement names another id — not why, and not whether the dependency is real. `impact` (R-37) lists what a change *might* touch, at the depth the operator asked for; it never marks an id stale, failed, or non-conformant. The next `check` reports what actually happened.
- No IDE integration, daemon mode, watch mode, or web UI.
- Language adapters exist for Python (v0.1) and Swift (v1.6, R-31); every other language gets file-level attribution (O-2). No adapter parses its language with a real parser except Python (`ast`); the Swift adapter is line-based (D-17).
- The checker never reads its own outputs as inputs: the spec, the results file, the two report files of `check` and the two of `impact` are excluded from every scan (C-03, F-002).

**A known limitation, stated rather than hidden (F-013):** citation is literal. A test that mentions `R-03` as *data* — asserting on a report that contains it, or on an error message — cites R-03 exactly as a test that proves it does. The `speccheck:ignore` markers in C-01 are the opt-out; they are the author's responsibility, and `speccheck` never infers intent from context.

**Relationship to the skills:** `spec-writing` produces the input; `spec-review` grades it; `spec-build` builds from it and, in Phase 3, does by hand what this tool does by machine. The report this tool writes is intended to be pasted into `SPEC_BUILD_REPORT.md` as the per-ID evidence table.

---

## 1. Actors and goals

| Actor | Goals |
| ----- | ----- |
| **Operator** (human at a terminal, or a CI job) | Run one command against a project and get a report plus an exit code that can gate a merge. Never has to trust a number without a path to its evidence. |
| **Extractor** (`speccheck/extract.py`) | Turn `SPEC.md` into the set of declared IDs (with title, statement text, family, retired flag), the §12 decision rows, and the typed edges between ids (C-12; v1.13), and turn source/test files into citations, deterministically. |
| **Attributor** (`speccheck/attribute.py`) | Map each citation in a test file to the test case that contains it (Python adapter), falling back to file-level attribution for anything it cannot parse. |
| **Results Mapper** (`speccheck/results.py`) | Read a JUnit XML file and join each `<testcase>` to an attributed test case, yielding outcomes per test case. |
| **Grapher** (`speccheck/graph.py`) | Build the ID → source-file / ID → test-case edge sets and compute each ID's deterministic status and the coverage metrics. |
| **Impact walker** (`speccheck/impact.py`) | From the spec-internal edges the Extractor records (C-12: `depends_on`, `verifies`, `affects`), and a changed set given on the command line or computed by diffing two versions of the spec, list every id reached at its shortest depth, the T ids that verify the set, and — through the Extractor's citations — what to re-cite and re-run (C-13). Deterministic; consults no judge and no results file. |
| **Judge** (`speccheck/judge.py`; providers `judge_mock.py`, `judge_llm.py`) | For each (test case, ID) edge of a `PASSING` ID, return a verdict with evidence lines; the mock provider is deterministic, the LLM provider is opt-in. Single-principal: the judge sees one edge at a time and holds no state across calls. |
| **Reporter** (`speccheck/report.py`) | Render the Markdown and JSON reports from the graph and judge results — for `impact`, the two C-13 reports from the walk, and for `explain` (v1.17) the one-id C-18 trace on stdout — in a fixed order, with no content that varies between identical runs. |
| **Triage provider** (`speccheck/jev.py`) | With `--jev-pre-triage` under `--judge llm` (v1.15), ask the C-17 Jev endpoint the C-06 verdict question once per judge-eligible edge and return one confidence per edge; the kernel uses those confidences only to order the judge's issue queue (K-16) and discards the answers (I-015). Stateless, advisory, and single-principal like the judge; its answer is never a `Verdict` and never reaches a report. |
| **CLI** (`speccheck/cli.py`, entry point `speccheck`) | The only surface; three subcommands, `check`, `impact` (v1.13) and `explain` (v1.17), each documenting its own flags and the environment it reads (v1.18, R-41). Parse arguments, wire the pipeline, apply the exit-code and verbosity contracts. |

---

## 2. Requirements (intent, high level)

| ID | Statement | Source |
| -- | --------- | ------ |
| **R-01** | The checker MUST read a Markdown specification and extract every *declared* spec ID together with its family and statement text, per the grammar in C-01. | prompt; spec-writing §ID taxonomy |
| **R-02** | The checker MUST recognize a declared ID as *retired* when its declaration is struck through (`~~R-07~~`), and MUST exclude retired IDs from coverage denominators. | spec-writing §ID taxonomy ("retire old ones with a strike-through") |
| **R-03** | The checker MUST scan every text file under each directory — and every file named directly — in the `--src` list, except the files C-03 excludes, and record a *source citation* for each (file, ID) pair where the ID token occurs, per C-03. The `--src` list is the comma-separated, per-occurrence, deduplicated effective set defined by C-03's PATHS rule (D-23). | prompt ("analyzes an implementation") |
| **R-04** | The checker MUST scan every text file under each directory — and every file named directly — in the `--tests` list, except the files C-03 excludes, and record a *test citation* for each (test case, ID) pair, attributing the citation to the enclosing test case when the file's language adapter can delimit test cases, and to the file otherwise. The `--tests` list is the comma-separated, per-occurrence, deduplicated effective set defined by C-03's PATHS rule (D-23). | prompt ("and its tests") |
| **R-05** | When `--results` is given, the checker MUST read a JUnit XML file and join each `<testcase>` to an attributed test case, recording the outcome `passed`, `failed`, `error`, or `skipped` per C-04. | spec-build Phase 1 exit gate |
| **R-06** | The checker MUST assign every declared, non-retired ID exactly one deterministic status from the set in C-05, computed by the algorithm in C-05 and by nothing else. | spec-build Phase 3.1 |
| **R-07** | The checker MUST list every *dangling citation*: an ID token cited in a source or test file that is not declared in the specification. | spec-build Phase 3.1 ("no ID is dangling") |
| **R-08** | The checker MUST list every *stale citation*: a citation of a retired ID. | R-02 |
| **R-09** | The checker MUST compute the coverage metrics in C-07 §metrics, applying the zero-denominator rules stated there; it MUST NOT raise or emit `0.0` for an undefined ratio. | spec-writing §precision rules |
| **R-10** | When `--judge` is `mock` or `llm`, the checker MUST obtain, for each (test case, ID) edge whose ID is `PASSING` and whose test outcome is `passed` (F-104), one judge verdict from the set `ASSERTS`, `EXECUTES_ONLY`, `UNRELATED`, `UNKNOWN`, with evidence per C-06. | prompt ("AI-assisted") |
| **R-11** | A judge verdict MUST only ever lower an ID's status (`PASSING` → `WEAKLY_PASSING`); the judge MUST NOT change any status other than `PASSING` and MUST NOT create, remove, or re-attribute citations. | §0 principle |
| **R-12** | The checker MUST write a Markdown report (`SPEC_CONFORMANCE_REPORT.md`) laid out per C-08 in which every declared ID appears exactly once. | prompt ("traceable conformance report") |
| **R-13** | The checker MUST write a JSON report (`speccheck.json`) conforming to C-07 that contains everything the Markdown report shows. | CI consumption |
| **R-14** | The checker MUST exit with the codes in §5.4, and the exit code MUST be a pure function of the JSON report content plus the `--strict` flag. | CI gating |
| **R-15** | With `--strict`, any in-scope ID whose status is not `PASSING`, any dangling citation, and any stale citation MUST cause exit `1`. Status (C-05) is the only input to this rule; individual judge verdicts are not consulted again (F-003). | spec-build "done when" |
| **R-16** | With `--judge none` or `--judge mock`, two runs over byte-identical inputs MUST produce byte-identical `SPEC_CONFORMANCE_REPORT.md` and `speccheck.json`. | spec-writing §precision rules (determinism) |
| **R-17** | The checker MUST implement the diagnostics contract in §5.3: silent by default; `--verbose`/`--verbose INFO` emit metadata only; `--verbose DEBUG` additionally emits judge prompts and responses; all diagnostics go to stderr and never alter stdout or the report files. | spec-writing §5 cross-cutting contracts |
| **R-18** | With `--judge none` or `--judge mock`, the process MUST perform no network I/O, and `speccheck --self-check` MUST verify this boundary. | §0 boundary |
| **R-19** | The checker MUST treat all inputs as read-only; it MUST NOT create, modify, or delete any file outside `--out`, except as I-001 permits for `--self-check` (F-104). | safety |
| **R-20** | All paths in reports MUST be relative to `--root` (default: current directory) and use `/` as separator regardless of host OS. | R-16 (portability of golden reports) |
| **R-21** | On completion (exit 0 or 1) the checker MUST print exactly one summary line to stdout in the format of §5.1 and nothing else. | CI log hygiene |
| **R-22** | The mock judge MUST be deterministic and MUST NOT require configuration: it returns `ASSERTS` when the test case's span contains an assertion token per C-06, else `EXECUTES_ONLY`. | R-16; testability of the judge path |
| **R-23** | The LLM judge MUST read its endpoint, model name, and API key from environment variables per C-09; a missing variable MUST be a usage error (exit `2`), and the key MUST never appear in any output, log, or report at any verbosity. | secret handling |
| **R-24** | Every deterministic status (C-05 steps 1–4), every count, and every metric in the report MUST be reproducible by an operator using only the report's own evidence table, `grep`, and the results file; `WEAKLY_PASSING` and the judge-derived metrics MUST be reproducible from the same inputs plus the verdicts *as recorded* in the report (F-017). | prompt ("traceable") |
| **R-25** | The checker MUST treat family `T` per C-05: a T id's status is determined by test citations and their outcomes only; source citations of a T id are recorded as evidence but never change its status, and a T id with no test citation is `UNCITED`, never `UNTESTED` (F-001). | spec-build ("every T-nn cites its spec ID") |
| **R-26** | The LLM judge MUST use exactly the request body, response path, and instruction text pinned in C-06 and C-10, and the report MUST record the SHA-256 of the instruction text used (F-004). | review F-004 |
| **R-27** | The checker MUST honor the ignore markers in C-01: a line containing `speccheck:ignore` yields no citations, and a file whose first three lines contain `speccheck:ignore-file` is not scanned; ignored files are counted in a Note (F-013). | review F-013 |
| **R-28** | With `--strict` and `--judge llm`, the checker MUST exit `1` when the judge was unavailable (`judge_available == false`) or when `unknown_rate` exceeds `--max-unknown` (K-11), and the summary line MUST name the reason (F-012). | review F-012 |
| **R-29** | The summary line MUST be a single line of ASCII text written to stdout as UTF-8 regardless of locale, in the exact format of §5.1 (F-010). | review F-010 |
| **R-30** | With `--judge llm`, the checker MUST display a progress indicator for the judge stage on stderr, in the format of C-11, whenever `--progress` resolves to on (default `auto`: on iff stderr is a TTY and verbosity is not `DEBUG`; §5.1). The indicator MUST be redrawn in place per K-13, MUST be erased before anything else is written to stderr or stdout after the judge stage begins, and MUST NOT alter stdout, either report file, or the exit code. With `--judge none` or `--judge mock` no indicator is ever drawn. | requester (2026-09-13: "speccheck should include progress bar when running with LLM judge, since that takes quite a bit of time") |
| **R-31** | For every `.swift` file in the `--tests` list (named directly as a PATHS element or found under a directory element; D-23) the checker MUST delimit test cases per the C-03 Swift adapter — Swift Testing `@Test` functions and XCTest `test*` methods — with a span that begins at the first line of the doc comment / attribute block above the declaration and ends at the function's closing brace, and MUST join their citations to SwiftPM's xUnit `<testcase>` outcomes by function identifier (C-04), so that a citation written where `spec-build` puts it (the test's doc comment) counts exactly as a Python citation does under R-04 and R-05. | requester (2026-09-17: "what would it take to make it work for Swift projects as well as Python ones?" — "go ahead"); the MonteCarloPi Swift build (`SPEC_BUILD_REPORT.md` of that project), where every Swift citation was file-level and the run reported `62 unverified` |
| **R-32** | The declaration parser MUST declare an ID whose bold form is the *beginning* of a table row's first cell and is followed by whitespace-separated decoration (`\| **K-07** **[port]** \|`), ignoring the decoration; the statement remains the second cell (C-01 (a), E-44). | the MonteCarloPi port spec marks port-specific ids `**[port]**` inside the id cell; six declared ids were reported as 43 dangling citations |
| **R-33** | For an ID declared by a heading (C-01 (b)), the checker MUST use the heading text followed by the section body beneath it — prose, bullets, and fenced code blocks, up to the next heading of the same or a higher level, capped per K-14 — as the ID's statement (`SpecId.text`, `JudgeRequest.statement`, JSON `statement`), so that the judge and the JSON report see the contract's pinned shape and not its title. The heading text alone is kept as `SpecId.title` / JSON `title`, and that is what the Markdown report renders (C-08). Table-row declarations are unchanged. | `PROPOSAL_v1.7_heading_bodies.md` (2026-09-17): two judges over the same 130 MonteCarloPi edges — `gpt-4o-mini` 65/70, 0 weak; `gemini-3.8-flash` 56/70, 9 weak, 15 UNRELATED, 3 UNKNOWN — and every disagreement was a `###`-declared contract whose statement was a title (`Data structures`, `` `EstimationWorker` (an `actor`) ``) while the pinned API sat unsent beneath it |
| **R-34** | For every `ASSERTS` or `EXECUTES_ONLY` verdict the judge MUST name the clause of the statement it judged against, as a verbatim excerpt, and the kernel MUST discard as `UNKNOWN` any such verdict whose excerpt cannot be located in the statement (K-15, E-48) — the statement-side mirror of the evidence-line rule (C-06, I-005), so that a recorded verdict is grounded in both the test and the statement. | `PROPOSAL_v1.9_clause_grounding.md`: with bodies in the statement, `gpt-4o-mini` graded long contracts by their gist — 13 of 18 stable downgrades on the mdv tree were tests asserting a body clause nearly verbatim — while a model that located the clause (`gemini-3.8-flash`) did not; nothing in the report showed *which* clause either had judged |
| **R-35** | A T id declared with the literal marker `*(recorded)*` immediately after its ID form (C-01) is RECORDED: the checker MUST compute its status by C-05 steps 1–4 exactly as for any other T id — it still needs a citing test case with a passed outcome to be `PASSING` — and MUST NOT send any of its edges to the judge, so that C-05 step 5 never applies to it; the marker MUST be carried into both reports (C-07 `recorded`, C-08). On a non-T id the marker is ignored with a Note (E-50). | D-22: the recorded tests of this document (T-48, T-49, T-51) are cited by presence checks so that they are not `UNCITED`; an honest judge reads such a check as `EXECUTES_ONLY` — `gemini-3.8-flash` did so to T-48 on 2026-09-18 — and `--strict --judge llm` went red for a reason the spec intended but had not written down |
| **R-36** | The checker MUST extract, from every declared id's statement, the ids it names, and record them as typed edges — `depends_on` between two R/C/I/K/E ids, `verifies` between a T id and an R/C/I/K/E id, `depends_on` between two T ids — together with every §12 decision row (family D, declaration-only) and the ids its *Affects* cell names as `affects` edges, in `speccheck.json` (C-12, C-07 `decisions`, `edges`). An edge whose target is undeclared is a Note, not an error; an edge whose target is retired is recorded with `retired: true` (E-55). D ids are never citation targets, never appear in `ids`, and count in no metric. | `PROPOSAL_v1.13_impact.md` §1: in v1.12 of this document 134 of 203 live ids name another id (434 tokens; 186 `depends_on`, 240 `verifies`, 110 `affects` edges), and nothing read them |
| **R-37** | The checker MUST provide an `impact` subcommand that, given a changed set — the ids of `--changed`, or the ids whose declarations differ between `--spec` and a prior version named by `--against` — reports every id reached from that set by `affects` edges and by *reverse* `depends_on` edges (dependents, never what the changed id itself depends on), each at its shortest depth with the edge that first reached it, up to `--depth`; the T ids that verify any id of the set; and, when `--src`/`--tests` are given, every source citation and every test case citing any of them; as `impact.json` and `IMPACT_REPORT.md` under `--out` (C-13), deterministically (I-002) and under I-001's write discipline. `impact` never consults a results file or the judge and has no gate. | `PROPOSAL_v1.13_impact.md` §2 Part B; D-24 |
| **R-38** | For every judged edge the checker MUST send the judge, with the statement, the **`related`** titles of the obligations the statement names and of those that name it — a C-12 `depends_on` neighbourhood, both directions, in-scope R/C/I/K/E ids only, the statement's own references first, at most eight total in C-07 id order, each a whitespace-collapsed title tail-truncated to 160 characters with `…`, a retired neighbour keeping its title with `(retired)` (D-28, E-57), and `[]` when the id has no neighbour — so that the judge can distinguish an assertion about this obligation from an assertion about a neighbour it refers to. The C-10 instruction text MUST define that an assertion corresponding only to a related obligation is not evidence for this one (C-10), and the `related` field MUST ride the C-17 triage `state` as well as the real-judge request (D-28's sub-decision, recorded as `D-28b`). `related` is request-side context only: it is never a status, a metric, or a `speccheck.json` field, and it changes no C-06 coercion rule — the D-26 advisory stance extends to it. | `PROPOSAL_v1.14_obligation_aware_judge.md` §1–2 and §5 (reach); §7 addendum (the triage `state` sub-decision) |
| **R-39** | The checker MUST compute, for every citation of an in-scope R/C/I/K/E id inside an attributed (non-file-level) test case, whether it is DECLARED (a citation line inside the case's own docstring, or a whole-line comment) or INCIDENTAL (C-03, C-14); the fact MUST be available under every `--judge` mode, including `none`, and MUST NOT depend on the results file, the judge, or any network access (I-014). | `PROPOSAL_v1.15_declared_vs_incidental_citations.md` §1–2 |
| **R-40** | The checker MUST accept a third subcommand, `speccheck explain <ID>`, that runs the same extract / attribute / map-results / graph / (triage /) judge stages as `check` over the same inputs, then renders the one id named by `<ID>` as a single human-readable trace on stdout (C-18); `explain` produces no status, verdict, citation, metric or note that a `check` run over the same inputs does not already compute, and its stdout is a pure function of those inputs and of C-18 (I-016). | `PROPOSAL_v1.17_explain_id.md` §1 |
| **R-41** | The checker MUST document its own interface: for every flag the parser defines on `speccheck`, `speccheck check`, `speccheck impact` and `speccheck explain`, the `--help` output MUST name the flag's purpose, every accepted value as a literal token where the set is finite, the default where the flag has one, and every precondition under which the flag is ignored or rejected — `--judge-budget N%`'s companion (`--jev-pre-triage` with `--judge llm`, E-58), every judge flag's `--judge llm` precondition, `--root` containment (E-09), and `impact`'s absent directory default for `--src`/`--tests` (C-13) — and the help MUST also name every environment variable the checker reads (C-09, C-17) with the condition under which it is read, whether it is required and its default, and MUST carry the §5.4 exit codes and the §5.1 summary line (C-19). | `PROPOSAL_v1.18_cli_help_contract.md` §1–2 |

---

## 3. Behavior and state model

### 3.1 Lifecycle

A run is a single, stateless pipeline. There is no persistent state between runs, no cache, and no partial-output mode: either both report files are written or neither is. The Reporter guarantees this by rendering both documents in memory, then, in this order (F-106): (1) delete any leftover `<out>/.speccheck.json.*.tmp` and `<out>/.SPEC_CONFORMANCE_REPORT.md.*.tmp` from earlier runs; (2) write `.speccheck.json.<nonce>.tmp` and `.SPEC_CONFORMANCE_REPORT.md.<nonce>.tmp`, where `<nonce>` is 8 random hex digits chosen per run (F-103); (3) rename the JSON temporary to `speccheck.json`; (4) rename the Markdown temporary to `SPEC_CONFORMANCE_REPORT.md`. If any step fails — an interrupt (E-41) included — every temporary and any file this run already renamed is removed before exit `3` (F-015). The nonce never appears in either report, so I-002 is unaffected.

| Stage | Owner | Input | Output | Fails with |
| ----- | ----- | ----- | ------ | ---------- |
| parse-args | CLI | argv, env | `Config` | exit `2` |
| extract-spec | Extractor | `SPEC.md` | `SpecIndex` (C-02) | exit `3` (E-01, E-02, E-03) |
| scan-src | Extractor | `--src` roots minus C-03 exclusions | `Citation[]` (C-03) | never (E-10, E-11 are notes) |
| scan-tests + attribute | Extractor, Attributor | `--tests` roots | `TestCase[]`, `Citation[]` | never (E-12 is a note) |
| map-results | Results Mapper | `--results` | `Outcome[]` (C-04) | exit `3` (E-05) |
| graph + status | Grapher | all of the above | `IdRecord[]` with deterministic status; dangling/stale lists; metrics | never |
| triage (optional) | Triage provider | judge-eligible edges (I-010) | one confidence per edge, used to order the judge's queue and then discarded (K-16, C-17, I-015) | never (E-59 is a Note) |
| judge (optional) | Judge | eligible edges, in K-16's ascending-confidence order when triage ran, else declaration order | `Verdict[]` (C-06); progress indicator on stderr while running (R-30, C-11) | never (E-14..E-17 yield `UNKNOWN`) |
| report | Reporter | everything | `SPEC_CONFORMANCE_REPORT.md`, `speccheck.json` | exit `3` if `--out` unwritable |
| exit | CLI | JSON report, `--strict` | exit code (§5.4), summary line | — |

**The `impact` pipeline (v1.13).** `speccheck impact` is a second, shorter pipeline over the same Extractor and Reporter; it shares parse-args, extract-spec, and — only when `--src`/`--tests` are given — the two scan stages, and it has no results, graph, or judge stage. It writes `impact.json` and `IMPACT_REPORT.md` with the same in-memory render, nonce-named temporaries (`.impact.json.<nonce>.tmp`, `.IMPACT_REPORT.md.<nonce>.tmp`), leftover deletion, and rename order (JSON first) as above, and the same cleanup on failure (E-18, E-41). The two subcommands never write each other's files.

| Stage | Owner | Input | Output | Fails with |
| ----- | ----- | ----- | ------ | ---------- |
| parse-args | CLI | argv | `ImpactConfig` (exactly one of `--changed`, `--against`; E-54) | exit `2` |
| extract-spec | Extractor | `--spec` (and `--against`, parsed by the same C-01 rules) | `SpecIndex` ×1 or ×2 with `decisions` and `edges` (C-02, C-12) | exit `3` (E-01, E-02, E-03 — for `--against`, the message names that file) |
| changed-set | Impact walker | `--changed` ids, or the diff of the two indexes (C-13) | `Changed[]` with a reason each; an undeclared `--changed` id → E-53 | exit `2` (E-53) |
| walk | Impact walker | `edges`, changed set, `--depth` | `Impact[]` (id, depth, via), `Reverify[]` | never |
| scan (optional) | Extractor, Attributor | `--src`/`--tests` per C-03 (no directory default here) | `Citation[]`, `TestCase[]` restricted to the impact and re-verify sets | never |
| report | Reporter | everything | `IMPACT_REPORT.md`, `impact.json` | exit `3` if `--out` unwritable |
| exit | CLI | — | `0`; one summary line (§5.1) | — |

### 3.2 Executable flow

```text
+-----------+     +---------------+     +-------------------+
|  SPEC.md  |---->|   Extractor   |---->|    SpecIndex      |
+-----------+     | (ID grammar,  |     | declared IDs,     |
                  |  retired)     |     | statements        |
                  +---------------+     +---------+---------+
                                                  |
+-----------+     +---------------+               |
| --src ... |---->|   Extractor   |--> src        |
+-----------+     | (token scan)  |    citations  |
                  +---------------+        |      |
                                           v      v
+-----------+     +---------------+     +-------------------+     +------------------+
| --tests   |---->|  Attributor   |---->|     Grapher       |---->| deterministic    |
+-----------+     | (test spans,  |     | edges, status     |     | status per ID    |
                  |  fallback)    |     | algorithm (C-05), |     | metrics, dangling|
                  +---------------+     | metrics           |     | stale            |
                                        +---------^---------+     +---------+--------+
+-----------+     +---------------+               |                         |
| junit.xml |---->| Results Mapper|---------------+                         |
+-----------+     | (C-04)        |                                         |
                  +---------------+                          --judge none   |  --judge mock|llm
                                                                    |       |       |
                                                                    |       v       v
                                                                    |  +------------------+
                                                                    |  |      Judge       |
                                                                    |  | one call / edge, |
                                                                    |  | evidence checked |
                                                                    |  | downgrade only   |
                                                                    |  +---------+--------+
                                                                    |            |
                                                                    v            v
                                                             +------------------------+
                                                             |        Reporter        |
                                                             | SPEC_CONFORMANCE_      |
                                                             |   REPORT.md            |
                                                             | speccheck.json         |
                                                             +-----------+------------+
                                                                         |
                                                                         v
                                                              exit code (pure fn of JSON)
                                                              + one summary line (stdout)
```

**The triage pass (v1.15).** With `--jev-pre-triage` under `--judge llm`, the judge stage above is preceded by one triage pass over the same eligible-edge set (K-16): one C-17 request per edge, at most `--judge-concurrency` in flight, whose per-edge top-choice probability orders the queue the Judge box then consumes (ascending, ties by C-07's id order; a failed edge first). The pass writes nothing — no report, no citation, no status — and its answer is discarded once the order is computed (I-015). With `--judge-budget N%` (K-12) the same order also decides which edges are issued at all.

**The `explain` surface (v1.17).** `explain <ID>` runs the same stages as `check` — extract-spec,
scan-src, scan-tests, map-results, graph, and (unless `--judge none`) the triage and judge stages —
and then renders the C-18 trace for the one named id instead of writing the two reports. It adds no
stage, reads no report file as input (§0's boundary), and writes nothing at all (D-33, I-016).

### 3.3 Durable artifacts

| Artifact | Written to | Version | Shape |
| -------- | ---------- | ------- | ----- |
| `SPEC_CONFORMANCE_REPORT.md` | `--out` (default `.`) | mirrors JSON `schema_version` | C-08 |
| `speccheck.json` | `--out` | `schema_version: "1.5"` (`"1.0"` through v1.6; `"1.1"` added `title` in v1.7; `"1.2"` `clause` per verdict in v1.9; `"1.3"` `recorded` per id in v1.10; `"1.4"` `decisions` and `edges` in v1.13; `"1.5"` `declared` per test edge and `declared_ratio` in v1.14) | C-07 |
| `IMPACT_REPORT.md` | `--out`, by `impact` only | mirrors `impact.json` `schema_version` | C-13 |
| `impact.json` | `--out`, by `impact` only | `schema_version: "1.0"` (v1.13) | C-13 |

A subcommand's two files are overwritten on every successful run of that subcommand, via the temp-and-rename sequence in §3.1; `check` never touches the `impact` files and vice versa. No other file is ever written, and no temporary survives a run (I-001).

`explain` (v1.17) writes **no** durable artifact: its trace goes to stdout only (C-18, D-33), so this table and every golden in it are unchanged by it.

---

## 4. Interfaces / contracts

### C-01 Spec ID grammar, declaration, citation, retirement

```text
ID        := FAMILY "-" DIGITS
FAMILY    := "R" | "C" | "I" | "K" | "E" | "T"          # O-n, D-nn and F-nnn are NOT conformance IDs;
                                                        # D-nn is DECLARATION-ONLY since v1.13 — rule (c)
DIGITS    := [0-9]{1,3}
TOKEN     := ID bounded by non-alphanumerics on both sides   # regex: (?<![A-Za-z0-9])([RCIKET])-([0-9]{1,3})(?![A-Za-z0-9])

Declaration (in SPEC.md only) — an ID is DECLARED when, outside fenced code blocks,
either form occurs (F-009). A fenced code block (F-108) opens at a line whose first non-space
characters are three backticks (U+0060 x3) or three tildes (~~~), optionally followed by an info
string, and closes at the next line whose first non-space characters are the same three-character
marker — the same character as the opener — followed by nothing but whitespace; a closing line's
info string is not permitted, a backtick fence is never closed by tildes nor a tilde fence by
backticks, and an unclosed fence runs to end of file (Q-008).
Lines (F-301): SPEC.md is split into lines on "\n"; a trailing "\r" on any line is removed before
  every other rule is applied, so a CRLF file parses as its LF twin and yields byte-identical
  output (I-002). A BLANK line is one whose text is empty or consists only of spaces and tabs.
  Body lines (see (b)) are re-joined with "\n"; no other whitespace is added or removed — trailing
  spaces on a body line are kept.
  (a) table row:    | **R-07** | <statement> | ...
        row       := a line whose first non-space character is "|"
        cells     := the row split on every "|" that is not preceded by "\" and not inside a
                     backtick span (`...`); the leading and trailing empty cells are dropped
        the trimmed content of the FIRST cell MUST BEGIN with one of the forms
          **ID**   ~~**ID**~~   **~~ID~~**
        and whatever follows the form MUST be empty or begin with whitespace (R-32, E-44):
          `**K-07** **[port]**` declares K-07; `**K-07**x` and `**K-07**, note` declare nothing.
        Text after the form is DECORATION: it is not part of the statement, and a bold ID inside
        it is not a declaration (`**R-01** **R-02**` declares R-01 only).
        RECORDED marker — see the rule after (b); in a row it is the first token of the DECORATION:
          `| **T-48** *(recorded)* | ... |`  and  `| ~~**T-48**~~ *(recorded)* | ... |`  (R-35, F-404)
        statement := the trimmed text of the SECOND cell ("" if there is none)
        title     := statement  (a table declaration has no separate title; R-33)
        A bold ID in any other cell is not a declaration (E-31). A separator row (cells made of
        "-" and ":" only) is never a declaration.
  (b) heading:      ### C-03 <title>
        HEADING LINE := a line, outside fenced code blocks, indented by at most three spaces, whose
                     first non-space characters are one to six "#" followed by whitespace or by end
                     of line; its LEVEL is the number of "#". ATX headings only (F-304): a line
                     indented four or more spaces is not a heading (and not a declaration), a line
                     underlined by === or --- (setext) is not a heading, "###C-03" (no space) is not
                     a heading, and a bare "###" is a HEADING LINE with an empty title.
        the declaring line MUST be a HEADING LINE and the ID token (optionally wrapped ~~ ~~) MUST
        be the first token after the "#" run; "### 9.1 Extraction (C-01, C-02)" declares nothing.
        title     := the rest of the heading text after the ID token — and after the RECORDED marker
                     when the token that follows the ID token is exactly `*(recorded)*` (rule below) —
                     trimmed, whitespace-collapsed, with a trailing run of "#" that is preceded by
                     whitespace removed ("### C-03 Title ###" -> "Title"; "### T-48 *(recorded)* Run"
                     -> "Run")
        statement := title, then — when the SECTION BODY is non-empty — a newline and the
                     SECTION BODY; when title is "" and the body is non-empty, the SECTION BODY
                     alone (F-305). (R-33; v1.7. Through v1.6 the statement was the title alone.)
        SECTION BODY := the lines after the HEADING LINE up to (not including) the next HEADING
                     LINE whose LEVEL is <= the declaring heading's LEVEL, or end of file;
                     fenced code blocks INCLUDED (the pinned shape is the contract; D-20);
                     leading and trailing blank lines dropped; whitespace inside preserved
                     line for line (a code block's indentation is meaning); the body's own
                     deeper headings (#### under a ###) are part of it; a thematic break
                     (---) is body text like any other line; capped at K-14 bytes (E-46).
                     A body that is empty after trimming — "### C-04 Data structures" followed
                     by blank lines and another ### — leaves the statement equal to the title
                     (E-46).
        The body is context, not grammar: a table row inside it is still parsed for its own
        declarations, a deeper heading inside it still declares its own ID (whose own body is
        delimited by the same rule), and a bold ID in the body is not a declaration of the
        heading's ID (E-31, E-47). IDs inside the body's fenced blocks remain non-declarations
        (E-04).
  RECORDED marker (R-35, v1.10; one rule for both forms, F-404): a declaration is RECORDED when the
  whitespace-separated token immediately after its ID form is exactly `*(recorded)*` — in a row, the
  first token of the DECORATION; in a heading, the first token after the ID token, which is then not
  part of the title. The marker is meaningful for family T only; on any other family it is ignored
  and noted (E-50). `*(Recorded)*`, `(recorded)`, and a marker that is not that first token are
  decoration like any other and mark nothing. A retired declaration may also be recorded.
  A SECOND declaration of the same ID is E-02 (exit 3); the message names the ID and both lines.
  Nothing "wins": the run produces no report (Q-006).
  (c) decision row (v1.13; R-36; family D, DECLARATION-ONLY): a TABLE is a maximal run of
        consecutive rows (per (a)) outside fenced code blocks with no BLANK line between them, whose
        second row is a separator row; its first row is the HEADER ROW. The DECISION TABLE is the
        first TABLE in the file whose HEADER ROW has a cell whose trimmed, case-folded content is
        exactly "affects"; that cell's index (cells per (a), leading and trailing empties dropped)
        is the AFFECTS COLUMN. Every row of the decision table after the separator whose trimmed
        first cell matches ^D-[0-9]{1,3}$ (no bold, no strike-through, no decoration) declares the
        decision D-nn (normalized to two digits: D-8 -> D-08; I-011). Its AFFECTS CELL is the cell at
        the AFFECTS COLUMN ("" when the row is shorter); every TOKEN in it (the TOKEN rule above —
        R/C/I/K/E/T only) names an `affects` target (C-12); everything else in the cell ("§10",
        "s5.2", prose) is ignored. A second table with an "affects" header, and a D-nn row anywhere
        else, declare nothing. A second row declaring the same D-nn is E-02 (exit 3). A decision
        is not a conformance ID: it is never in `ids`, never a citation target (the TOKEN regex
        does not match "D-"), never in any metric (D-25); it exists as the source of `affects`
        edges and as a row of C-07 `decisions`.

Retirement — a declaration whose ID token is wrapped in ~~ ~~ :
  | ~~**R-07**~~ | ... |   or   | **~~R-07~~** | ...   or   ### ~~C-03~~ ...
  A retired ID is DECLARED and RETIRED. Retirement is not un-done by a later plain declaration (E-03).

Citation (in --src / --tests files) — every TOKEN occurrence in a text file is a citation,
  regardless of comments, strings, or code. Fenced code blocks are NOT excluded in source files
  (only in SPEC.md). ID numbers are compared numerically: R-7 and R-07 and R-007 are the same ID.
  Since v1.14, a citation inside an attributed test case additionally carries a DECLARED/INCIDENTAL
  fact (C-03, C-14): this changes nothing about what counts as a citation, only what the judge and
  the report are told about it.

Ignore markers (F-013), matched literally and case-sensitively:
  speccheck:ignore        anywhere on a line  -> that line yields no citations (the line still
                                                 counts toward a test case's span)
  speccheck:ignore-file   anywhere in the first 3 lines of a file -> the file is not scanned at
                                                 all (no citations, no test cases); one Note per
                                                 run: "ignored N file(s) by speccheck:ignore-file"
  The markers have no effect inside SPEC.md.

Normalized form used everywhere in output: FAMILY "-" zero-padded to 2 digits for R/C/K/E/T,
  3 digits for I  (R-07, I-005). An ID declared as R-7 is reported as R-07.

Family T (F-001): a T id names an acceptance test. It is IN SCOPE and is expected to be cited by
  the test case that realizes it (in that case's docstring or a comment). Source citations of a
  T id are recorded but do not affect its status (C-05 step 2b). All six families count toward
  `in_scope` and `conformance`. A RECORDED T id (marker above; R-35) is a test whose proof is a
  recorded run (a self-application, an evaluation, a benchmark) rather than an assertion: it is
  still cited by a test case — typically a presence check that the recorded artefact exists and
  has the right shape — and that citation and its outcome give the id its status; its edges are
  never judged (C-05 step 5, I-010).
```

### C-02 `SpecIndex`

```python
@dataclass(frozen=True)
class SpecId:
    family: str          # one of "R","C","I","K","E","T"
    number: int          # 0..999
    title: str           # table: the second cell, whitespace-collapsed, may be ""; heading: the heading
                         # remainder, whitespace-collapsed (C-01). What C-08 renders. Added in v1.7 (R-33).
    text: str            # the statement (C-01). table: == title. heading: title + "\n" + SECTION BODY
                         # when the body is non-empty (body lines per the C-01 Lines rule: "\r" stripped,
                         # re-joined with "\n", other whitespace preserved; fenced blocks included; capped
                         # per K-14); == title when the body is empty; == body when title is "" (R-33, E-46)
    line: int            # 1-based line of the declaration in SPEC.md
    retired: bool
    recorded: bool       # C-01 RECORDED marker (R-35); only ever True for family T

@dataclass(frozen=True)
class Decision:                      # v1.13, C-01 (c); never a SpecId, never in `ids`
    id: str                          # normalized "D-nn"
    line: int                        # 1-based line of the row in SPEC.md
    affects: tuple[str, ...]         # the DECLARED ids named in the AFFECTS CELL, normalized, unique,
                                     # sorted per the C-12 id order; undeclared tokens are Notes (C-12)

@dataclass(frozen=True)
class Edge:                          # v1.13, C-12
    src: str                         # normalized id: a D id for "affects", the T id for "verifies"
    kind: str                        # "affects" | "depends_on" | "verifies"
    dst: str                         # normalized, always a declared R/C/I/K/E/T id
    retired: bool                    # dst is RETIRED (E-55)

@dataclass(frozen=True)
class SpecIndex:
    path: str                       # relative, POSIX
    ids: tuple[SpecId, ...]         # sorted by (family order R,C,I,K,E,T ; number)
    decisions: tuple[Decision, ...] # sorted by number (v1.13)
    edges: tuple[Edge, ...]         # sorted per C-12 (v1.13)
    # invariant: no two SpecId share (family, number); no two Decision share a number;
    #            no two Edge share (src, kind, dst)
```

### C-03 `Citation`, `TestCase`, attribution

```python
@dataclass(frozen=True)
class TestCase:
    file: str            # relative, POSIX
    name: str            # function name, e.g. "test_zero_rate"; "" for file-level
    classname: str       # dotted module path used to match JUnit classname, e.g. "tests.test_core"
    start: int           # 1-based first line of the span; 1 for file-level
    end: int             # inclusive last line; last line of file for file-level

@dataclass(frozen=True)
class Citation:
    id: str              # normalized ID
    file: str
    line: int
    kind: str            # "src" | "test"
    testcase: TestCase | None     # for kind=="test": the enclosing case, or the file-level case
    declared: bool        # kind=="test" only (v1.14, C-14, R-39); DECLARED vs INCIDENTAL, below

DECLARED vs INCIDENTAL (v1.14; R-39; C-14). For a "test"-kind citation of id X inside test case
  T's span, X is DECLARED in T when at least one citation line of X within [T.start, T.end] is:
    - inside T's own docstring (Python: the line range of the `Expr` node `ast.get_docstring`
      reads — the node, not its text; a multi-line docstring's later lines count too), or
    - a whole-line comment: the first non-whitespace character on that citation's own line is
      "#" for Python; for Swift, a line whose first non-space characters are "///", or that
      lies inside a "/** ... */" block — the doc-comment line kind the ATTRIBUTE BLOCK rule
      (below) already recognizes, reused here rather than re-detected.
  Otherwise X is INCIDENTAL in T — including a citation on a code line that also carries a
  trailing comment (`x = 1  # R-02`; a deliberate simplification, no column tracking). A "src"-kind
  citation, and a "test"-kind citation attributed to a file-level case (T.name == ""), are always
  INCIDENTAL (`declared: false`; E-56) — there is no per-test declaration of intent to check
  against a file, or a case that was never delimited. `declared` is computed the same way
  regardless of `--judge` mode, needs no results file, no judge call, and no network access
  (I-014).

Python adapter (files ending .py under a --tests root):
  * parse with `ast`; a test case is (F-007):
      - every top-level FunctionDef or AsyncFunctionDef whose name starts with "test_";
      - every FunctionDef/AsyncFunctionDef whose name starts with "test" (underscore NOT
        required: "testAddition" and "test_addition" both qualify; F-102) that is a direct member
        of a top-level ClassDef which is RECOGNIZED: its name starts with "Test", OR any of its
        bases is a Name/Attribute whose final identifier ends with "TestCase";
    span = node.lineno .. node.end_lineno (decorators included, per `ast`).
  * a "test*" function that is a member of an UNRECOGNIZED top-level class, or of a nested class,
    is not a test case; its lines belong to the file-level case, and the file gets one Note:
    "undelimited tests in <path>: <Class.name>, ..." (E-28).
  * classname = the file path relative to --root with "/" -> "." and ".py" dropped
    ("tests/test_core.py" -> "tests.test_core"); methods append "." + ClassName.
  * a citation on a line inside a span is attributed to that case; any other citation in the file
    is attributed to the file-level case (name "").
  * a .py file that fails to parse -> whole file is file-level (E-12; a note, not an error).
Swift adapter (files ending .swift under a --tests root; R-31, D-17, D-18, D-19). The file is
  delimited BY LINES, not by a parser, so the kernel stays standard-library (D-17). Every rule
  below reads a line's text with its `//` comment removed (a `//` inside a string literal is
  treated as a comment start too — D-17) and counts braces `{` / `}` only outside `"…"` and
  `"""…"""` string literals (the latter may span lines).
    TYPE LINE  := a line matching, after that stripping,
                    ^\s*(?:@\S+\s+|(?:public|package|internal|private|fileprivate|open|final|indirect)\s+)*
                    (?:struct|class|actor|enum|extension)\s+([A-Za-z_][A-Za-z0-9_]*)
                  whose brace depth is greater at the end of the line than at its start. Its CHAIN is
                  the identifiers of the TYPE LINEs still open at that depth (outermost first) plus its
                  own identifier; an `extension X` line contributes `X`. Nesting depth is unbounded.
    FUNC LINE  := a line matching, after that stripping,
                    ^\s*(?:@[A-Za-z_][A-Za-z0-9_]*(?:\([^)]*\))?\s+|(?:public|package|internal|private|fileprivate|open|static|class|final|override|mutating|nonmutating|nonisolated|isolated|consuming|borrowing)\s+)*
                    func\s+([A-Za-z_][A-Za-z0-9_]*)\s*[<(]
                  whose identifier is the FUNC NAME. A FUNC LINE on which no `{` opens before SPAN END
                  can be computed (a protocol requirement, a declaration without a body) is not a case.
    ATTRIBUTE BLOCK := the maximal run of lines immediately above the FUNC LINE, each of which is
                  (i) a doc-comment line: first non-space characters `///`, or any line of a
                      `/** … */` block; or
                  (ii) an attribute line: first non-space character `@`, or a continuation of an
                      attribute whose parentheses had not balanced on the previous line of the run; or
                  (iii) a blank line that lies between two lines of kinds (i)/(ii);
                  together with the text of the FUNC LINE itself that precedes `func`.
    SPAN END   := the first line, at or after the FUNC LINE, on which the running brace depth returns
                  to the depth in force before the FUNC LINE's first `{`.
  A test case is:
    (S) Swift Testing — a FUNC LINE whose ATTRIBUTE BLOCK contains the token `@Test` bounded on the
        right by `(`, whitespace or end of line (`@Testable`, `@TestSuite` do not match).
        name := FUNC NAME (the parameter list is not part of the name; D-19)
        classname := MODULE, or MODULE "." + CHAIN of the innermost enclosing TYPE LINE joined with "."
    (X) XCTest — a FUNC LINE whose FUNC NAME starts with `test`, that is a DIRECT member (brace depth
        exactly one deeper) of a TYPE LINE declaring a `class` whose text contains the token
        `XCTestCase` after the identifier.
        name := FUNC NAME;  classname := MODULE "." + that class's CHAIN joined with "."
    A FUNC LINE that satisfies both is (S). A FUNC LINE whose FUNC NAME starts with `test` and is
    neither (S) nor (X) — a method of a non-`XCTestCase` type, a member of a class nested inside an
    `XCTestCase`, a free function — is NOT a test case: its citations are file-level and the file
    gets one Note "undelimited tests in <path>: <Chain.name>, …" (E-43; E-28's rule). Any other
    function is a helper and produces no Note.
  MODULE := the first path component of the file's path relative to the --tests root under which it
    was found, or the last path component of that root when the file lies directly under it
    (SwiftPM's `Tests/<Target>/…` layout; D-18). `Tests/ProbeTests/Unit/Foo.swift` under
     `--tests Tests` -> `ProbeTests`. (Under `--tests Tests/ProbeTests` the same file yields `Unit`,
   which will not join; pass the `Tests` directory.) A file named DIRECTLY as a --tests list element
   (D-23) is "found under" its own parent directory, so its MODULE is that parent's last path
   component (`--tests p/q/Foo.swift` -> `q`); the Python classname is unaffected, being the path
   relative to --root, never to a --tests root.
  span := first line of the ATTRIBUTE BLOCK .. SPAN END. A citation on a line inside a span is
    attributed to that case (the doc comment is inside the span — that is the point of R-31);
    every other citation is file-level (E-13).
  A .swift file whose brace depth goes negative on any line, or is non-zero at end of file, is
    one file-level case with Note `parse fallback: <path>` (E-42; E-12's rule).
  What the join sees (measured 2026-09-17, Swift 6.4 / SwiftPM; D-19): `swift test --xunit-output
    junit.xml` writes `junit-swift-testing.xml` for Swift Testing with
      classname = "<Module>.<Outer>.<Inner>"   (dotted CHAIN; a free function: "<Module>")
      name      = "<name>(<label>:<label>:)"    (the signature; ONE <testcase> per function —
                                                 parameterized tests are not expanded; a
                                                 `.disabled` test carries <skipped>)
    and, on toolchains that write it, `junit.xml` for XCTest with classname = "<Module>.<Class>"
    and name = "<testName>". C-04 strips the signature, so both forms join by identifier.
Fallback adapter (any other text file): one file-level case per file; its classname is derived
  exactly as for Python (path relative to --root, "/" -> ".", final extension dropped; F-108).

PATHS -- the --src / --tests list (D-23): each --src and each --tests OCCURRENCE on the command
  line is a comma-separated list of paths, and the occurrences build the effective list the
  extractor walks. From the argv occurrences, the effective list is built by:
   1. split each occurrence on the literal "," character;
   2. trim leading and trailing whitespace (" " and "\t") from every resulting segment;
   3. drop every now-empty segment, with no Note and no error (so "--src", "--src a," and
      "--src a,,b" are all tolerable; T-78);
   4. concatenate the surviving segments in occurrence order, then in within-occurrence order;
   5. resolve each surviving path once, inside --root (E-09; a symlink element resolves to its
      target per Q-007), and deduplicate the resolved paths: a file reached by more than one
      element is scanned exactly once, its recorded --src/--tests root is the FIRST-SEEN covering
      element (which fixes a directly-swift-file's MODULE per D-18), and all files are then
      emitted in ascending resolved-path order (determinism, I-002/C-07), independent of the order
      in which they were named.
  A resolved path that is a DIRECTORY is descended exactly as a single --src/--tests root was in
  v1.11 (K-02 size, K-03 never-descend list, E-10 oversized, E-11 UTF-8, E-13 file-level case,
  E-29 binary, E-30 descent-time symlinks, E-33 ignore markers); a resolved path that is a regular
  FILE is scanned as that one file, with no descent. Every per-file filter above applies identically
  whether the file was reached by descent or named directly. A segment that resolves inside --root
  but is NEITHER a directory nor a regular FILE is a usage error: exit 2, message
  "--<flag>: no such file or directory: <segment>", replacing the former "non-directory ->
  usage error" check (E-52). The "src"/"tests" default (the directory if it exists, else none)
  applies ONLY when the flag is entirely absent; a present --src/--tests whose occurrences are all
  empty yields the empty list (no default), and two empty lists together is E-19.

Text vs binary (F-008): a file is BINARY if any of its first 8192 bytes is 0x00. Binary files are
  skipped silently (no Note, no citations, no test case). Everything else is text and is decoded
  as UTF-8 with errors="replace" (E-11). Symbolic links — to files or to directories — ENCOUNTERED
  DURING DESCENT are never followed (K-03); one Note per run if any were skipped (E-30). A path
  given on the command line (--spec, --src, --tests, --results, --out, --root) is resolved once,
  checked against --root (E-09), and then used in its resolved form: a symlinked --src root is
  descended (a directory) or scanned (a file), and is not counted as a skipped symlink (Q-007, D-23).

Excluded from every scan (F-002), whether or not they lie under a --src/--tests root, and
  whether or not they exist yet: the file named by --spec, the file named by --results,
  <out>/SPEC_CONFORMANCE_REPORT.md, <out>/speccheck.json, <out>/IMPACT_REPORT.md, <out>/impact.json
  (v1.13), the file named by --against (impact only), and every file directly under <out> whose
  name starts with ".speccheck.json.", ".SPEC_CONFORMANCE_REPORT.md.", ".impact.json." or
  ".IMPACT_REPORT.md." and ends with ".tmp" (the §3.1 temporaries, including leftovers from a
  killed run; F-103). Exclusion is by
  resolved path (symlinks resolved), is silent (no Note), and applies before K-02/K-03 filtering.
```

### C-04 JUnit XML subset

```text
Root: <testsuites> or <testsuite>. Every <testcase> element anywhere below the root is an outcome.
  classname := @classname (may be ""; an empty classname ends every dotted name on a component
                boundary, so it matches every TestCase with the same join_name, and the
                longest-suffix rule below then applies with suffix length 0 — F-105)
  name      := @name (required; missing -> E-05)
  outcome   := "failed"  if a <failure> child exists
             | "error"   if an <error> child exists
             | "skipped" if a <skipped> child exists
             | "passed"  otherwise
Join to a TestCase (F-006): a result joins the TestCase whose `join_name` equals the result's
  join_name AND whose dotted `classname` ends with the result's dotted classname on a component
  boundary ("tests.test_core" matches "tests.test_core" and "test_core"; it does not match
  "unit_test_core"). Among candidates, the one whose classname has the LONGEST common dotted
  suffix with the result wins; if two or more candidates tie, the result is UNATTRIBUTED and one
  Note names the result and every candidate (E-27). `join_name` is defined as:
    join_name := step 1: if name ends with "]" and contains "[":  name[:name.index("[")]
                         else:                                     name
                 i.e. everything from the FIRST "[" to the end is removed, whatever it contains
                 (F-005, F-101): "test_x[3-True]" -> "test_x"; "test_x[list[int]]" -> "test_x";
                 "test_y[a][b]" -> "test_y".
                 step 2 (R-31, D-19): if the step-1 result ends with ")" and contains "(":
                 everything from the FIRST "(" is removed as well — a Swift signature names the
                 test, not a variant: "twoArgs(a:b:)" -> "twoArgs"; "freeFunction()" ->
                 "freeFunction"; "testAddition" -> "testAddition"; "test_x[f(1)]" -> "test_x".
    param     := the text removed in step 1 without its outer brackets ("3-True", "list[int]",
                 "a][b"), or null; a signature removed in step 2 is never a param.
  Two Swift Testing cases in one type with the same identifier (overloads by label: `f(a:)` and
  `f(b:)`) share `join_name` and `classname`: a result for either ties, is UNATTRIBUTED, and one
  Note names the result and both candidates (E-45; the E-27 rule).
  Every <testcase> that joins the same TestCase (parametrized variants, or duplicates) is kept in
  that case's `results` list; the case's single `outcome` = worst of them, worst order
  error > failed > skipped > passed (E-06, E-24).
  A <testcase> that joins no TestCase is an UNATTRIBUTED result (E-07): listed, never counted.
Malformed XML, or a root that is neither element: E-05 -> exit 3.
```

### C-05 Status algorithm and `IdStatus`

```text
IdStatus (deterministic):  RETIRED | UNCITED | UNTESTED | UNVERIFIED | FAILING | SKIPPED | PASSING
IdStatus (judge-only):     WEAKLY_PASSING

For each declared ID x:
  1. if x.retired                                   -> RETIRED   (excluded from denominators)
  2. T := { test cases with >=1 test citation of x }   # file-level cases included
     S := { source files with >=1 src citation of x }
     2a. if x.family != "T":
           if T == {} and S == {}                       -> UNCITED
           if T == {}                                   -> UNTESTED
     2b. if x.family == "T":                            # F-001: S is evidence only
           if T == {}                                   -> UNCITED
  3. if no --results given, or no case in T has an outcome  -> UNVERIFIED
  4. O := outcomes of cases in T that have one
     if any o in O is failed or error                 -> FAILING
     elif every o in O is skipped                     -> SKIPPED
     else                                             -> PASSING
  5. (judge enabled only) if status == PASSING and not x.recorded:        # R-35: recorded ids skip step 5
       V := verdicts for edges (t, x), t in T with outcome passed
       if V is non-empty and no v in V is ASSERTS and some v in V is EXECUTES_ONLY or UNRELATED
                                                      -> WEAKLY_PASSING
       else                                           -> PASSING   (UNKNOWN never changes status)

Cases in T without an outcome are reported as "unrun" for x and ignored in step 4.
The judge is never consulted for edges whose ID is not PASSING after step 4, nor for any edge of a
  RECORDED id (I-010, R-35); a recorded id's `tests[].verdict` is null (E-37) and its edges are not
  eligible edges for the progress indicator's <total> (C-11).
Step 5 is the ONLY place verdicts influence anything: an ID with verdicts {ASSERTS, EXECUTES_ONLY}
  is PASSING, and PASSING is what --strict tests (R-15, §5.4; F-003). There is no per-edge rule
  anywhere else in this document.
```

### C-06 Judge interface

```python
@dataclass(frozen=True)
class JudgeRequest:
    id: str                 # "R-07"
    statement: str          # SpecId.text — for a heading-declared ID: title, newline, section body (R-33); may be multi-line
    testcase: TestCase
    declared: bool          # v1.14, C-15, R-39: DECLARED vs INCIDENTAL (C-14) for this (id, testcase) edge; read-only context
    source: str             # lines testcase.start..testcase.end, each prefixed "<lineno>\t" (F-109)

@dataclass(frozen=True)
class Evidence:
    file: str
    line: int               # MUST satisfy testcase.start <= line <= testcase.end

@dataclass(frozen=True)
class Verdict:
    verdict: str            # "ASSERTS" | "EXECUTES_ONLY" | "UNRELATED" | "UNKNOWN"
    clause: str             # verbatim excerpt of the statement judged against (K-15); "" for UNRELATED / UNKNOWN (v1.9, R-34)
    evidence: tuple[Evidence, ...]
    rationale: str          # <= 280 characters, single line

class Judge(Protocol):
    def judge(self, req: JudgeRequest) -> Verdict: ...
```

```text
Validation applied by the kernel to EVERY provider's raw answer (judge.py, not the provider).
  The rules are applied IN THIS ORDER; the first rule that fires determines the verdict and the
  rationale, and no later rule is evaluated (F-402). Rule 8 is applied to whatever rationale
  results. A verdict coerced to UNKNOWN by any rule is recorded with `clause` "" (E-49).
  1. provider raised, timed out (K-05), or returned non-JSON   -> UNKNOWN, rationale = "judge: <class of failure>"
  2. verdict not in the four-value set                          -> UNKNOWN, rationale = "judge: malformed response" (E-15)
  3. clause absent, or present but not a JSON string            -> clause := ""   (then continue)
  4. verdict is UNRELATED or UNKNOWN                             -> clause := "" whatever was returned (E-49); done
  5. verdict is ASSERTS or EXECUTES_ONLY and clause is not LOCATED (K-15)
                                                                 -> UNKNOWN, rationale = "judge: unlocated clause" (E-48)
  6. verdict == ASSERTS and evidence is empty                    -> UNKNOWN, rationale = "judge: ungrounded" (E-16)
  7. any evidence.file != testcase.file, or line outside span    -> UNKNOWN, rationale = "judge: ungrounded" (E-16)
  8. rationale longer than 280 chars                             -> truncated to 277 + "..."
  An UNKNOWN produced by validation is recorded with `coerced: true` in the JSON report.

LLM provider wire format (judge_llm.py; F-004) — an OpenAI-compatible chat-completions endpoint:
  Request:  POST SPECCHECK_JUDGE_URL
            Headers: Content-Type: application/json ; Authorization: Bearer <SPECCHECK_JUDGE_API_KEY>
            Body (JSON, exactly these keys):
              { "model": <SPECCHECK_JUDGE_MODEL>,
                "temperature": 0,
                "max_tokens": 4000,
                "messages": [
                  { "role": "system", "content": <the C-10 instruction text, verbatim> },
   The user message of each request is, in JSON, the object `{id, statement, related, declared, file, start, end, source}` (Part A adds `declared`, C-14–C-16; **Part B adds `related`, C-10/D-28/R-38 — a neighbourhood of the names of the obligations this statement names and that name it, see below and R-38**). The field descriptions are below. The system message is the instruction text (C-10). The two messages of this request are not sent as an array of messages to the provider. The model is selected by a dedicated variable `SPECCHECK_JUDGE_MODEL`. The object carries two request-side, non-report fields with no effect on any status, metric, or report JSON — `declared`, from Part A, and `related` (R-38, D-28) from Part B: neither is reported, and no C-06 coercion rule acts on them.
                                                     formatting; declared = Citation.declared for this edge (v1.14, C-14,
                                                     C-15); statement = SpecId.text verbatim — body, fenced blocks and
                                                     indentation included for a heading-declared ID (R-33, T-74);
                                                     source = the span with every line prefixed by its absolute
                                                     1-based line number and one TAB (F-109)> } ] }
  Response: HTTP 200 with a JSON body; the model's text is read from  choices[0].message.content .
            Any other status, a non-JSON body, or a missing path -> E-14 / E-15.
            The text is stripped of surrounding whitespace and of ONE enclosing ``` or ```json fence
            if present, then MUST parse as a single JSON object {verdict, clause, evidence:[{file,line}],
            rationale}; `clause` MAY be absent (it is then ""); anything else is non-JSON (-> UNKNOWN, E-15).
  Exactly one HTTP request per edge; no retries (K-06). The SHA-256 of the C-10 text as sent is
  recorded in the report as `judge_prompt_sha256` (C-07).

Mock provider (judge_mock.py):
  verdict = ASSERTS if the span contains an assertion token, else EXECUTES_ONLY
  assertion token := a line matching ^\s*assert\b  or containing  .assert  or  pytest.raises(
                     or (Swift; R-31) containing  #expect(  or  #require(  or  XCTAssert  or  XCTFail(  or  Issue.record(
  evidence = every such line (file, line); rationale = "mock: assertion token on N line(s)" / "mock: no assertion token"
  clause   = the whitespace-collapsed statement cut to its first 280 characters — a prefix, so it is always LOCATED
             under K-15 (equal to a statement shorter than 12 characters, including ""); the mock reads no statement
             semantics and stays deterministic (R-16, R-22)
```

### C-07 JSON report (`speccheck.json`, `schema_version` "1.5")

```json
{
  "schema_version": "1.5",
  "spec": "SPEC.md",
  "judge": "none | mock | llm",
  "judge_available": null,
  "judge_prompt_sha256": "<64 hex chars; present only when judge == llm>",
  "strict": false,
  "max_unknown": 0.2000,
  "strict_judge_failure": null,
  "ids": [
    {
      "id": "R-07",
      "family": "R",
      "recorded": false,
      "title": "…",
      "statement": "…",
      "line": 88,
      "status": "PASSING",
      "src": [ {"file": "src/pkg/core.py", "lines": [12, 40]} ],
      "tests": [
        {
          "file": "tests/test_core.py", "name": "test_zero_rate", "classname": "tests.test_core",
          "lines": [17], "declared": true,
          "outcome": "passed",
          "results": [ {"name": "test_zero_rate[0]", "param": "0", "outcome": "passed"},
                       {"name": "test_zero_rate[1]", "param": "1", "outcome": "passed"} ],
          "verdict": {"verdict": "ASSERTS", "clause": "returns the arithmetic sum of `a` and `b`",
                      "evidence": [{"file": "tests/test_core.py", "line": 21}],
                      "rationale": "…", "coerced": false}   // null when the case was not judged (Q-001); clause "" for UNRELATED / UNKNOWN (E-49)
        }
      ],
      "unrun": [ {"file": "…", "name": "…"} ]
    }
  ],
  "decisions": [ {"id": "D-08", "line": 1331, "affects": ["C-10", "R-26", "T-49", "T-76"]} ],      // v1.13, C-01 (c); [] when the spec has no decision table
  "edges": [ {"src": "R-01", "kind": "depends_on", "dst": "C-01", "retired": false},              // v1.13, C-12 order; [] when no statement names another id
             {"src": "T-01", "kind": "verifies",   "dst": "R-01", "retired": false},
             {"src": "D-08", "kind": "affects",    "dst": "C-10", "retired": false} ],
  "dangling": [ {"id": "R-99", "file": "src/pkg/x.py", "line": 3} ],
  "stale":    [ {"id": "R-02", "file": "tests/test_old.py", "line": 9} ],
  "unattributed_results": [ {"classname": "tests.test_gone", "name": "test_x", "outcome": "passed"} ],
  "notes": [ "skipped 1 file over 2 MiB: data/big.json", "parse fallback: tests/test_bad.py" ],
  "metrics": {
    "declared": 61, "retired": 2, "in_scope": 59,
    "by_status": {"PASSING": 50, "WEAKLY_PASSING": 3, "FAILING": 1, "SKIPPED": 0, "UNVERIFIED": 2, "UNTESTED": 2, "UNCITED": 1},   // in-scope statuses only; RETIRED is the separate "retired" count
    "conformance_ratio": "50/59",   "conformance": 0.8475,
    "by_family": { "R": {"in_scope": 24, "passing": 22, "ratio": 0.9167}, "C": {"…": "…"}, "I": {"in_scope": 0, "passing": 0, "ratio": null}, "K": {"…": "…"}, "E": {"…": "…"}, "T": {"…": "…"} },
    "judge_strength_ratio": "50/53", "judge_strength": 0.9434,
    "unknown_rate": 0.0000,
    "declared_ratio": 0.9821
  },
  "exit_code": 1
}
```

```text
Rules: keys emitted in exactly this order (`judge_prompt_sha256` omitted entirely unless judge == llm;
  `max_unknown` always present, echoing K-11; `strict_judge_failure` is null, "unavailable", or
  "unknown_rate" and is non-null only when R-28 forced exit 1 — when BOTH reasons hold,
  "unavailable" is recorded, since a fully unavailable judge makes the unknown rate vacuous; Q-004);
  `ids` sorted by (family order R,C,I,K,E,T ; number); `decisions` and `edges` always present, after
  `ids`, sorted per C-12 (v1.13; a D id never appears in `ids`, `dangling`, `stale`, or any metric — D-25);
  `results` sorted by name;
  `src`/`tests`/`dangling`/`stale`/`unattributed_results` sorted by (file, line) then name;
  `notes` is a list of strings sorted ascending by Unicode code point (each Note's text is fixed by
  the E-case that produces it, so this order is total and reproducible; Q-002);
  `lines` ascending, unique. No timestamps, hostnames, absolute paths, durations, or version
  strings other than schema_version (R-16).
Title and statement (R-33): `title` is `SpecId.title` and `statement` is `SpecId.text` (C-01, C-02).
  For a table-declared ID the two are equal; for a heading-declared ID with a body, `statement` is
  multi-line — title, `\n`, the section body with its fenced blocks and indentation, truncated per
  K-14 when over the cap — and `title` is the heading text alone. `schema_version` was `"1.0"`
  through v1.6, `"1.1"` from v1.7 (`title` added), and `"1.2"` from v1.9 (`clause` added to every verdict
  object, after `verdict`; R-34), and `"1.3"` from v1.10 (`recorded` added to every id record, after
  `family`; R-35 — `true` only for a T id carrying the C-01 marker), `"1.4"` from v1.13 (`decisions`
  and `edges` after `ids`; R-36), and `"1.5"` from v1.14 (`declared` added to every `tests[]` entry,
  after `lines`, and `declared_ratio` added to `metrics`; R-39, C-14); no other key changed.
  The literal is stated in this contract (heading and example) and in §3.3 only; no §9 row repeats
  it — a test asserts "the C-07 value" (F-401).
Verdict field (Q-001): every `tests[]` entry has the key `verdict`. It is a verdict object when
  the case was judged (judge enabled, ID `PASSING` after C-05 step 4, ID not RECORDED, outcome
  `passed` — the E-37 condition) and `null` otherwise — including every entry under `--judge none`.
  The key is never omitted.
Names (Q-011): `tests[].name` is the `TestCase.name` — `""` for a file-level case. `(file)` is a
  Markdown-only rendering (C-08) and never appears in the JSON. R-13's "contains everything"
  concerns data; a rendering label is not data.
Numbers (Q-009): every ratio is computed as Decimal(numerator) / Decimal(denominator) under a
  28-digit context and quantized to 4 places with ROUND_HALF_EVEN; it is emitted as a JSON number
  with exactly four decimal places (0.9000, not 0.9), so the JSON text is byte-determined without
  reference to binary floating point. K-11 compares these quantized values. `<pct>` in the summary
  line is the quantized `conformance` times 100, quantized to 1 place with ROUND_HALF_EVEN.
  `max_unknown` is not a ratio but is emitted the same way: the K-11 Decimal quantized to 4 places
  (0.2000), matching the summary-line suffix (F-206).
Metrics:
  conformance        = |PASSING| / in_scope                       (WEAKLY_PASSING is NOT passing)
  by_family[f].ratio = |PASSING in f| / |in_scope in f|
  judge_strength     = |PASSING \ RECORDED| / (|PASSING \ RECORDED| + |WEAKLY_PASSING|)   (judge enabled only; else absent;
                       RECORDED ids are PASSING without a judged edge and are outside this population — F-405;
                       `conformance` and `by_family` DO include them, since they are PASSING by citation and result)
  unknown_rate       = |edges with verdict UNKNOWN| / |judged edges| (judge enabled only; else absent)
  declared_ratio     = |DECLARED citations of in-scope R/C/I/K/E ids| / |all such citations|   (v1.14,
                       C-14, R-39; present under every --judge mode, including none; a T id's own
                       citations are outside this count, matching R-39's scope)
Zero denominators: ratio = null (JSON) / "n/a" (Markdown); the "a/b" string is still emitted ("0/0");
  `judge_strength` is null when every PASSING id is RECORDED and nothing is WEAKLY_PASSING (F-405);
  `declared_ratio` is null when no in-scope R/C/I/K/E id has any citation (E-19's shape).
  in_scope == 0 is E-01 (exit 3), so `conformance` itself is always defined on exit 0/1.
Shape rules (F-016): `by_family` ALWAYS has exactly the six keys R, C, I, K, E, T in that order,
  each with in_scope/passing/ratio, even when in_scope is 0. `by_status` ALWAYS has exactly the
  seven in-scope statuses in the order shown, each a count (0 allowed); RETIRED is never a key.
  `judge_available` is null when judge == none; with mock or llm it is true when at least one
  judge call succeeded OR no edge was eligible (vacuously available), and false only when every
  call failed (E-14). The C-07 example's `// comments` are explanatory and never emitted.
  Family T counts toward in_scope and conformance like every other family (F-001).
```

### C-08 Markdown report layout (`SPEC_CONFORMANCE_REPORT.md`)

```markdown
# Specification Conformance Report

**Spec:** `SPEC.md` · **Judge:** none|mock|llm (available|unavailable) · **Strict:** on|off
# the parenthetical is omitted (with its leading space) when `judge_available` is null, i.e. under --judge none (F-207)

## 1. Verdict
<one line: the §5.1 summary line, verbatim>

## 2. Metrics
| Metric | Value |            # conformance a/b (0.xxxx); by-status counts; per-family table;
                               # judge_strength and unknown_rate rows only when judge enabled

## 3. Per-ID evidence
| ID | Status | Statement | Source citations | Test citations (outcome · verdict) |
# one row per declared ID in C-07 order; RETIRED rows included, with the ID cell (only) struck through: `~~R-07~~`;
# a RECORDED id's ID cell is `T-48 (recorded)`, and a retired recorded id's is `~~T-48~~ (recorded)` — strike the id, then the
# label (R-35, F-404); the verdict position shows the em dash, as for any unjudged case;
# the Statement cell renders the JSON `title` — the heading text or the table cell — never a section body, so
# this table is byte-identical before and after v1.7 (R-33, T-73); the body the judge saw is in `speccheck.json`
# citations rendered as `file:line`; verdict rendered as ASSERTS / EXECUTES_ONLY / UNRELATED / UNKNOWN(coerced),
# or as an em dash (—) when the JSON `verdict` is null (Q-001); a file-level case is rendered with the
# label `(file)` in place of its empty name (Q-011)

## 4. Dangling citations      # table or "None."
## 5. Stale citations         # table or "None."
## 6. Unattributed results    # table or "None."
## 7. Unrun test citations    # table (ID, file, name) or "None."
## 8. Judge details           # present only when judge enabled: one row per judged edge (verdict non-null): ID, case, Verdict,
                               # Clause (the JSON `clause`, tail-truncated to 80 characters, em dash when ""), Rationale (v1.9, R-34)
## 9. Notes                   # bullet list or "None."
```

### C-09 LLM provider configuration

```text
SPECCHECK_JUDGE_URL      required with --judge llm   e.g. https://host/v1/chat/completions
SPECCHECK_JUDGE_MODEL    required with --judge llm   model identifier passed through verbatim
SPECCHECK_JUDGE_API_KEY  required with --judge llm   sent as "Authorization: Bearer <key>"
SPECCHECK_JUDGE_TIMEOUT  optional, seconds, default 30, integer 1..300 (else exit 2)
The URL and model MAY appear at INFO; the key MUST NOT appear anywhere, including DEBUG output
and error messages (redact to "***").
```

### C-10 Judge instruction text (normative; F-004)

The file `speccheck/judge_prompt.md` is shipped as package data and its content is exactly the text below (trailing newline, `\n` line endings). It is sent verbatim as the system message (C-06). Changing it is a spec change: bump this document's version and the file together (v1.7 added the any-clause rule for statements that carry a section body — R-33, D-20; v1.9 made the question clause-first and added the `clause` field — R-34, D-21; v1.14 added the `declared` field and the skepticism rule below — R-39, C-15, D-26; **v1.16 added the `related` field and its rule below, and sent it on the triage `state` as well as the real-judge request — R-38, D-28 incl. its D-28b sub-decision**).

```text
You are a test-strength judge for a specification conformance checker.

You will receive one JSON object with these fields:
  id        - a specification ID, e.g. "R-07"
  statement - the normative text of that ID: its title on the first line and, for an ID declared
              by a heading, the section beneath it - prose, tables, and code blocks. A statement
              may have several clauses: a pinned interface, numbered rules, table rows.
  declared  - true when this test's own docstring or a comment names this ID - the convention
              this project's tests are expected to follow; false when the ID appears only
              elsewhere in the test body.
  related   - the names of the other obligations this statement names and that name it - its
              C-12 `depends_on` neighbourhood, both directions; the statement's own references first,
              then the others, in the order of that section. Context only: an assertion that corresponds
              to a related obligation and not to this statement is not evidence that this statement holds
              (see the related rule in the Rules below). The empty list when the id has no neighbour.
  file      - the path of one test file
  start     - the first line number of one test case in that file
  end       - the last line number of that test case (inclusive)
  source    - the text of lines start..end, one line per source line, each line prefixed by its
              absolute line number and a tab (e.g. "17<TAB>assert x == 2"); cite those numbers

Answer exactly one question: does any assertion in this test case check any one clause of the
statement? Pick the clause you judge against and quote it verbatim in "clause".

Reply with one JSON object and nothing else - no prose, no markdown fence:
  {"verdict": <VERDICT>, "clause": <text>, "evidence": [{"file": <file>, "line": <n>}, ...], "rationale": <text>}

VERDICT is exactly one of:
  "ASSERTS"       - the test contains at least one assertion (assert statement, assertion method,
                    expected-exception context, or equivalent) whose expected value or condition
                    corresponds to the clause. You MUST list every such assertion line in evidence.
  "EXECUTES_ONLY" - the test runs code the clause describes but no assertion checks it
                    (assertions absent, trivial, or about something else).
  "UNRELATED"     - the test does not exercise any clause of the statement.
  "UNKNOWN"       - you cannot decide from the source given. Prefer UNKNOWN over guessing.

Rules:
  - clause is a verbatim excerpt of the statement, at least 12 characters and at most 280; copy
    it, do not paraphrase. For UNRELATED and UNKNOWN, clause is "".
  - A statement with several clauses is asserted when any one of them is; it is not required to
    be asserted whole by one test.
  - Every evidence line number MUST be between start and end inclusive, in the given file.
  - Cite only lines that exist in source. Do not invent lines.
  - rationale is one sentence, at most 280 characters.
  - Judge only the given test case. Do not assume what other tests do.
  - A test that mentions the ID in a comment or string is not evidence of asserting it.
  - When declared is false, do not credit ASSERTS merely because a clause is locatable and some
    assertion exists nearby: check that the assertion's own subject is unambiguously this
    obligation, not a token reused as example or fixture data for a different one.
  - related lists the names of the other obligations this statement names and that name it (its C-12
    depends_on neighbourhood, both directions; own references first, at most eight, in the order of that
    section; a retired neighbour keeps its title with (retired) appended; the empty list when none).
    An assertion that corresponds only to a related obligation is not evidence that this statement holds;
    judge this statement's own clauses, not a neighbour's. When no assertion corresponds to this
    statement's own clause, prefer EXECUTES_ONLY or UNRELATED over an ASSERTS that matches a related obligation only.
```

### C-11 Judge progress indicator (R-30)

The indicator is one physical line on stderr, redrawn in place. It is written directly to the
stderr stream, **not** through the `speccheck` logger, so the §5.3 logging level is unaffected
and the line never carries a level prefix. While it is displayed — from the first draw to the
erase — the indicator owns stderr: nothing else is written to that stream (F-201). Every write
is one of the two byte sequences below, each issued as a single atomic write (F-203, F-205); no
terminal escape sequence is ever used, so the indicator renders on any console that honours a
carriage return:

```text
draw:   "\r" + <line> + " " * (W - len(<line>))     # W = length of the longest <line> drawn so far in this run
erase:  "\r" + " " * W + "\r"                          # what remains on stderr after the judge stage is nothing

<line> ::= "judge: [" <bar> "] " <done> "/" <total> " edges  " <elapsed> " elapsed  ~" <left> " left"
<bar>     exactly 20 cells: k times "#" followed by (20 - k) times "-"
<done>    decimal integer, edges whose verdict is determined (received, coerced to UNKNOWN, or budget-skipped)
<total>   decimal integer, number of eligible edges (I-010)
<elapsed> M:SS  (minutes without upper bound, seconds zero-padded to two digits)
<left>    M:SS, or "?:??" while done == 0

Regex <line> MUST match (T-62), before padding:
^judge: \[[#-]{20}\] \d+/\d+ edges  \d+:\d{2} elapsed  ~(\d+:\d{2}|\?:\?\?) left$
```

The padding exists because `<left>` can shrink (`~12:00 left` → `~9:59 left`); padding every
draw to the widest line so far means a plain `\r` never leaves residue, and the erase needs no
erase-to-end-of-line escape (F-205).

With $n$ the number of eligible edges, $d$ the number determined so far, and $t$ the wall-clock
seconds since $t_0$, the filled cell count and the estimate of time remaining are

$$
\begin{aligned}
k &= \left\lfloor \frac{20\,d}{n} \right\rfloor \\
\mathrm{left} &= \frac{t}{d}\,(n - d) \quad \text{for } d > 0
\end{aligned}
$$

$t_0$ is the instant of the first draw — the start of the judge stage, immediately before the
first request is issued — so the first draw shows `0:00 elapsed`. K-12's budget deadline (the
`SECONDS` form) keeps its own origin, the moment the first request is issued, which is $\geq t_0$
(F-202); under the `N%` form there is no deadline — the edges K-12 does not issue are already
determined when the stage starts, so the first draw MAY count them and `<done>` stays
non-decreasing across draws, exactly as for a verdict received. `left` is
undefined (rendered `?:??`) while $d = 0$; the line is never drawn when $n = 0$ (E-36: no
request is sent). Both durations are floored to whole seconds before rendering, with
$M = \lfloor s / 60 \rfloor$ and $\mathrm{SS} = s \bmod 60$. The line is pure ASCII (the cells are
`#` and `-`, never Unicode block characters) so it renders under any locale (R-29 rationale). It
carries no file name, statement text, prompt, response, or key (I-007). The final state
($d = n$, a full bar) is always drawn before the erase.

### C-12 Spec-internal edges (v1.13; R-36)

```text
Sources of edges -- all read from the SpecIndex, nothing else:
  (1) statement tokens: for every declared id X (retired included), every TOKEN (C-01) in X.text --
      title and section body, fenced blocks included, after the K-14 cap -- whose normalized id Y
      is != X:
        Y undeclared                              -> no edge; one Note per distinct (X, Y):
                                                     "edge to undeclared id: <X> -> <Y>"
        X and Y both in R/C/I/K/E                 -> Edge(X, "depends_on", Y)
        exactly one of X, Y in family T           -> Edge(<the T id>, "verifies", <the other>)
                                                     direction is normalized: an obligation naming its
                                                     T and the T naming the obligation are the SAME
                                                     edge, emitted once
        X and Y both in family T                  -> Edge(X, "depends_on", Y)
  (2) decision rows (C-01 (c)): for every Decision D and every TOKEN Y in its AFFECTS CELL:
        Y undeclared                              -> no edge; Note "edge to undeclared id: <D> -> <Y>"
        otherwise                                 -> Edge(D, "affects", Y)
      Decision.affects is the sorted, unique list of the DECLARED Y only.
  retired := Y is RETIRED (E-55). X being retired does not suppress X's edges: a retired statement
  still names what it named, and whether to walk from a retired id is the operator's call.
  A self-reference (Y == X) and a repeated token produce nothing; each (src, kind, dst) is
  emitted at most once.

Order (total, so I-002 holds): edges sorted by (id_key(src), kind, id_key(dst)), where
  id_key(id) = (family order R, C, I, K, E, T, D ; number) and kind orders
  "affects" < "depends_on" < "verifies" (ASCII); decisions sorted by number.

What an edge is not (D-25; the scope note in the front matter): it is not a citation (C-05 never
  reads it), not a status or metric input, and it carries no meaning beyond "the statement of
  src contains the token dst". The judge (C-06) is not shown edges in v1.13. The Markdown
  conformance report (C-08) does not render them; they live in the JSON and in `impact`.
```

### C-13 `impact`: changed set, walk, `impact.json`, `IMPACT_REPORT.md` (v1.13; R-37)

```text
Changed set:
  --changed IDS   IDS is a comma-separated list, split, trimmed, and deduplicated like a PATHS
                  list (C-03 steps 1-3). Each element MUST be a TOKEN of family R/C/I/K/E/T, or
                  "D-" DIGITS, and is normalized (I-011); an element that is not a declared id or a
                  declared decision -> exit 2, message "--changed: undeclared id: <element>"
                  (E-53); a list that is empty after trimming -> exit 2, "--changed: no ids".
                  Every element gets reason "changed".
  --against FILE  FILE is a prior version of the same spec: resolved inside --root (E-09), decoded
                  and parsed exactly as --spec (C-01, K-14); its E-01/E-02/E-03 exit 3 with the
                  message prefixed "--against: ". The changed set, in the C-12 id order, is:
                    id declared in both, whitespace-collapsed `text` differs     reason "statement differs"
                    id declared in --spec only                                   reason "added"
                    id declared in FILE only                                     reason "removed"
                                                                                 (walked by --spec's edges,
                                                                                 of which it is dst of none;
                                                                                 `line` is its line in FILE)
                    id declared in both, `retired` differs                       reason "retired flag differs"
                    D declared in both, `affects` differs                        reason "affects differs"
                    D declared in exactly one                                    reason "added" / "removed"
                  An id with several reasons carries all of them, in the order above, joined by "; ".
                  An empty changed set is not an error: every section reads "None." and exit is 0.
  Exactly one of --changed / --against MUST be given (E-54).

Walk (over the edges of --spec, C-12; breadth-first):
  depth 0 := the changed set. The successors of a node X at depth d are:
    X a D id            -> every Y with Edge(X, "affects", Y)
    X in R/C/I/K/E      -> every Y with Edge(Y, "depends_on", X)        (REVERSE: X's dependents;
                                                                         what X depends on is never
                                                                         a successor)
    X in T              -> every Y with Edge(Y, "depends_on", X); the obligations X verifies are NOT
                           successors (a test changing does not change what it tests)
  An id enters IMPACT once, at the first depth reached, with `via` := the edge that reached it --
  among several at that depth, the smallest by the C-12 order. Changed-set ids never enter IMPACT.
  No edge has a D id as dst, so a D id is never reached. --depth N (integer 0..999; default 1;
  0 = unbounded): a node that would enter at depth > N is neither entered nor expanded; the count
  of such nodes under N = 0 that are not in IMPACT is one Note when non-zero:
  "<k> further id(s) beyond --depth <N>; --depth 0 lists them".
  REVERIFY := every T id with a "verifies" edge whose dst is in (changed ∪ IMPACT), plus every T id
  in (changed ∪ IMPACT); each with the sorted list of the obligations in (changed ∪ IMPACT) it
  verifies ([] for a T that is there only because it changed or was reached). A retired T is
  included, flagged. Nothing is walked from REVERIFY.
  IMPACT is sorted by (depth, id order); every other list by id order.

Citations (only with --src and/or --tests; the C-03 scan and PATHS rules apply unchanged, except
  that an absent flag means "not scanned" -- the `src`/`tests` directory default of `check` does not
  apply to impact):
  RECITE     := every src-kind citation whose id is in (changed ∪ IMPACT ∪ REVERIFY), grouped as
                (id, file, lines[]), sorted by (id order, file), lines ascending unique.
  TEST_CASES := every TestCase (C-03) holding a test-kind citation of an id in that set, as
                (file, name, classname, ids[]) with ids the sorted ids of the set it cites, sorted
                by (file, start); a file-level case has name "" (Q-011).
  Dangling and stale citations are not computed here; --results is not accepted.

impact.json -- keys in exactly this order (K-09 formatting):
{
  "schema_version": "1.0",
  "spec": "SPEC.md",                                         // relative to --root, as C-07 `spec`
  "against": null,                                           // or the --against path, relative to --root
  "depth": 1,                                                // the --depth value as given; 0 = unbounded
  "changed":    [ {"id": "K-15", "family": "K", "line": 951, "retired": false, "reason": "changed"} ],
  "impact":     [ {"id": "R-34", "depth": 1, "retired": false,
                   "via": {"src": "R-34", "kind": "depends_on", "dst": "K-15"}} ],
  "reverify":   [ {"id": "T-75", "retired": false, "verifies": ["K-15"]} ],
  "recite":     [ {"id": "K-15", "file": "src/speccheck/judge.py", "lines": [6, 76, 143]} ],
  "test_cases": [ {"file": "tests/test_judge.py", "name": "test_clause_bounds",
                   "classname": "tests.test_judge", "ids": ["K-15", "T-75"]} ],
  "notes":      [ "2 further id(s) beyond --depth 1; --depth 0 lists them" ]
}
  `recite` is [] without --src and `test_cases` is [] without --tests; `against` is null under
  --changed; `notes` is sorted as C-07 notes are and also carries the C-12 undeclared-target Notes
  and the scan Notes (E-10, E-11, E-30 ...) when a scan ran. `family` of a D id is "D". No
  timestamps, hostnames, absolute paths, durations, or version strings other than schema_version
  (R-16).

IMPACT_REPORT.md -- sections in this order, every one present, "None." when empty:
# Impact Report
<spec> · changed by `--changed` | against `<file>` · depth <N> | depth unbounded        # one line
## 1. Changed      | ID | Line | Reason |                      the ID cell (only) struck through when retired
## 2. Impact       | ID | Depth | Via |                        Via rendered `R-34 -depends_on-> K-15`
## 3. Re-verify    | T id | Verifies |   then, when --tests was given, a second table | File | Case | IDs |
                                          (a file-level case renders `(file)`, as C-08 does)
## 4. Re-cite      | ID | File | Lines |                       "Not scanned." when --src is absent
## 5. Notes        bullet list, or "None."
  The byte-exact rendering is pinned by the golden fixture (T-80) as C-08's is by T-46. UTF-8, `\n`
  line endings (K-09).

Summary line (stdout, exactly one line, on exit 0 only; pure ASCII, single trailing "\n"):
  speccheck impact: <changed> changed, <impact> impacted (depth <N> | unbounded), <reverify> to re-verify, <recite> citations, <cases> test cases
  Regex it MUST match (T-80):
  ^speccheck impact: \d+ changed, \d+ impacted \((depth \d+|unbounded)\), \d+ to re-verify, \d+ citations, \d+ test cases$
  <recite> is the number of (id, file) rows; <cases> the number of TEST_CASES rows; both 0 when
  the respective root was not given.
```

### C-14 Declared vs. incidental citations (v1.14; R-39)

```text
For a "test"-kind Citation of id X inside test case T's span (C-03), X is DECLARED when at least
one citation line of X within [T.start, T.end] is:
  - inside T's own docstring (Python: the line range of the `Expr` node ast.get_docstring reads,
    not the text it returns; a multi-line docstring's second and later lines count), or
  - a whole-line comment: the first non-whitespace character on that citation's own line is "#"
    for Python; for Swift, a line whose first non-space characters are "///", or that lies inside
    a "/** ... */" block -- the doc-comment line kind the C-03 ATTRIBUTE BLOCK rule already
    recognizes, reused here rather than re-detected.
Otherwise X is INCIDENTAL -- including a citation on a code line that also carries a trailing
comment (`x = 1  # R-02`; a deliberate simplification: line ranges only, no column tracking, and
every real DECLARED citation found while drafting this rule was a whole-line comment or a
docstring line). A "src"-kind citation, and a "test"-kind citation attributed to a file-level case
(T.name == ""), are always INCIDENTAL (E-56) -- there is no per-test declaration of intent to
check a file-level citation, or a case that was never delimited, against.

`Citation.declared` (C-03) carries this fact for every citation; where a report or a judge request
needs one bool per (id, testcase) edge rather than per citation line (C-07's `tests[].declared`,
C-15's `JudgeRequest.declared`), the edge's value is true iff any of its citation lines is DECLARED.
It is computed identically under every --judge mode, including none, and depends on nothing but
the source and test trees already read for attribution -- no results file, no judge call, no
network access (I-014).
```

### C-15 `declared` in the judge request; the instruction text is advisory (v1.14; R-39)

```text
`JudgeRequest` (C-06) gains `declared: bool`, inserted after `testcase`, computed per C-14 for the
specific (id, testcase) edge about to be judged. The field is read-only context: no C-06 validation
rule inspects it, it changes no coercion rule (K-15, E-48, E-49 apply exactly as before), and I-004
and I-005 are untouched.

`C-10`'s instruction text gains the field's definition and one rule: when `declared` is false, the
model MUST NOT credit ASSERTS merely because a clause is locatable and some assertion exists
nearby -- it MUST check that the assertion's own subject is unambiguously this obligation, not a
token reused as example or fixture data for a different one. This is advisory, not a coercion rule
(D-26): the model MAY still return ASSERTS on an INCIDENTAL citation -- the docstring convention is
not literally enforced on every test, and E-56 does not apply outside C-14's own scope -- and no
mechanical rule downgrades a verdict for carrying `declared: false`. Changing C-10's text changes
`judge_prompt_sha256` (R-26) exactly as any other wording change does.
```

### C-16 `declared` and `declared_ratio` in the JSON report (v1.14; R-39)

```text
`speccheck.json` (C-07) gains, on every `tests[]` entry, `"declared": bool` per C-14 (true iff any
of the edge's citation lines is DECLARED), present after `"lines"` under every --judge mode
including none. `metrics` gains `"declared_ratio"`: DECLARED citations of in-scope R/C/I/K/E ids
over all such citations (a T id's own citations are outside this count, matching R-39's scope),
computed as every other ratio is (Decimal, Q-009), null when the denominator is zero.
`schema_version` becomes "1.5". This contract is JSON-only: `SPEC_CONFORMANCE_REPORT.md` (C-08)
is unchanged (Part C of the proposal that motivated this; the report's cost stays zero under
--judge none/mock).
```

### C-17 Jev triage provider (v1.15; K-16, I-015)

```text
SPECCHECK_JEV_URL      optional, default https://openrouter.ai/api/alpha/decisions
SPECCHECK_JEV_MODEL    optional, default ~typesafe/jev-latest  (OpenRouter's floating alias -- not
                       the pinned typesafe/jev-1.13 the calibration in PROPOSAL_v1.16_jev_pre_triage.md
                       §1 was measured against; set it explicitly to hold the measured behaviour fixed)
SPECCHECK_JEV_API_KEY  required when the triage pass runs (--jev-pre-triage with --judge llm);
                       missing -> exit 2, message names the variable, value never echoed (E-21)
SPECCHECK_JEV_TIMEOUT  optional, seconds, default 30, integer 1..300 (else exit 2); per edge,
                       wall-clock, covering DNS, TCP, TLS, send and receive exactly as K-05 does
Read only when the triage pass runs. With --judge none|mock, or without --jev-pre-triage, none of
the four is read, no request is made, and the key is not required (K-16, I-006). The URL and model
MAY appear at INFO; the key MUST NOT appear anywhere, including DEBUG output and error messages
(redact to "***") -- I-007 applies to this provider exactly as it does to the judge.

Request -- exactly one per judge-eligible edge (I-010), at most --judge-concurrency in flight, no
retries, no batching (K-06):
  POST SPECCHECK_JEV_URL
  Headers: Content-Type: application/json ; Authorization: Bearer <SPECCHECK_JEV_API_KEY>
  Body (JSON, exactly these keys):
    { "model": <SPECCHECK_JEV_MODEL>,
      "state": <TEXT, built from the C-06 request object for this edge -- {id, statement, related, declared,
                 (v1.16 D-28b: the C-06 object now carries `related`, R-38; the triage `state` carries it too).
                file, start, end, source} -- by exactly this template:
                  "Specification obligation {id}.\n\nStatement:\n{statement}\n\n"
                   "Related obligations:\n{related}\n\n"   # v1.16 D-28b: {related} = the related titles (R-38/D-28),
                  newline-joined, each whitespace-collapsed to 160 chars, a retired one with (retired), or a blank line when []
                  "Test file {file}, lines {start}-{end}:\n{source}"
                i.e. the task tools/judge_crosscheck_tasks.py builds, and the input the calibration
                figures of PROPOSAL_v1.16_jev_pre_triage.md §1 were measured on>,
      "questions": { "verdict": { "type": "choice",
        "instructions": "Does any assertion in this test case check any clause of the statement? Choose exactly one option.",
        "criteria": {
          "ASSERTS":       "The test contains at least one assertion whose expected value or condition corresponds to a clause of the statement.",
          "EXECUTES_ONLY": "The test runs code the statement describes, but no assertion checks it (assertions absent, trivial, or about something else).",
          "UNRELATED":     "The test does not exercise any clause of the statement.",
          "UNKNOWN":       "Cannot decide from the source given. Prefer this over guessing." } } } }

Response: HTTP 200 with a JSON body; the answer is read from  answers.verdict  as
          {"choice": <label>, "probabilities": {<label>: <number>, ...}}   (a choice answer).
  The edge's CONFIDENCE is  p(e) := max(probabilities.values()) .
  A reply is USABLE iff the status is 200, the body parses as JSON, answers.verdict.choice is one
  of C-06's four verdict tokens, and answers.verdict.probabilities is a non-empty object whose
  values are all numbers. Anything else is a per-edge Jev FAILURE (E-59), not a run failure.

Ordering (K-16): edges are issued to the real judge in ascending p(e); ties are broken by
ascending id in C-07's id order (family R,C,I,K,E,T, then number); a FAILURE is ordered first.
Jev's choice, probabilities and any rationale are used for this order and nothing else: never
validated against C-06, never recorded in either report, never the source of a Verdict (I-015).
p(e) is not a metric and appears in no report field.
```

### C-18 `explain` stdout contract (v1.17; R-40)

`explain <ID>` writes one trace for the named id to stdout and nothing else: no report file, no
`--out`, no `schema_version` entry (§3.3, D-33). The section order, the headings and the two-space
indentation below are pinned, so two runs over identical inputs are byte-identical (I-002, I-016):

```text
ID <id>[ (RETIRED)][ (recorded)]
status: <STATUS> (<the C-05 step that set it>)
statement:
  <the id's statement, C-10/K-14, every line indented by two spaces>
sources:
  <file>:<line>
tests:
  <file>::<name> (<outcome>) [<verdict>]
    clause: <clause>
    rationale: <rationale>
impact (<depth>):
  <id> (depth <n>, via <src> -<kind>-> <dst>)
  <T-id> verifies <id>[, <id>...]
```

- **Status and reason.** `<STATUS>` is the C-05 status, and the parenthetical is C-05's own step:
  `UNCITED` → `step 1: no source or test citation`; `UNTESTED` → `step 2: no test citation`;
  `UNVERIFIED` → `step 2b: no citing test case has a result`; `FAILING` → `step 3: a citing test
  case failed`; `SKIPPED` → `step 3: a citing test case was skipped`; `PASSING` → `step 4: every
  citing test case passed`; `WEAKLY_PASSING` → `step 5: the judge downgraded every judged edge`;
  `RETIRED` → `retired: struck through in the specification`. The `RETIRED` marker in the `ID` line
  is appended for a retired id and the `(recorded)` marker for an R-35 RECORDED id; both may appear.
- **Statement.** `SpecId.text` verbatim (C-10: title, newline, body), each line prefixed by two
  spaces; a K-14 truncation marker is echoed as it stands.
- **Sources.** One line per source citation, ascending by (file, line), each two-space indented as
  `<file>:<line>`; the heading alone when the id has none (E-60's empty-block rule).
- **Tests.** One line per citing test case, ascending by (file, start): `<file>::<name> (<outcome>)
  [<verdict>]`, where `<outcome>` is `passed`, `failed`, `skipped` or `—` (U+2014: no result
  joined); a file-level case renders as `<file> (file-level)`. `<verdict>` is the C-06 token with
  ` (coerced)` appended when the recorded verdict is coerced, and `not judged` when no verdict was
  recorded (under `--judge none`, and for any edge no provider judged; E-61). A `clause:` line is
  printed only when the recorded `clause` is non-empty, and a `rationale:` line only when a verdict
  was recorded, both four-space indented under their case.
- **Impact.** `impact (<depth>):` reuses C-12's `walk` from this id at `--depth` (default `1`,
  `0` = unbounded) and C-13's `reverify` set over `{id} ∪ walked`: one line per walked id in the
  walk's own order as `<id> (depth <n>, via <src> -<kind>-> <dst>)`, then one line per T id that
  verifies the id or a walked id as `<T-id> verifies <id>[, <id>...]` (the obligations it verifies
  among them, ascending); the heading alone when both are empty.
- **Exit.** `0` once the trace is written — nothing it renders is pass/fail, like `impact`; `2` for
  a usage error (E-60 included); `3` for an input-contract violation (§5.4).
- **Determinism.** No timestamp, duration, absolute path or locale-dependent value appears in the
  trace; stdout is UTF-8 (R-29), and the trace is the only thing written to stdout by an `explain`
  run.

### C-19 Help contract (v1.18; R-41)

Every argument definition of the three parsers except `-h` carries a non-empty help string. One
flag's entry is one paragraph, in this order:

1. **Purpose** — one sentence saying what the flag does.
2. **Values** — for a finite set, the tokens in the flag's own usage-error spelling (`none, mock,
   or llm`; `auto, always, or never`; `INFO`/`DEBUG`; `SECONDS` or `N%`); for a bounded numeric
   value, its range (`a decimal in [0, 1]`, `an integer 1..32`, `an integer 0..999`).
3. **Default** — `default: <value>` for every optional flag that has one, including `check`'s
   absent-flag-only `src`/`tests` directory default and `impact`'s/`explain`'s absence of one.
4. **Preconditions** — an `ignored unless …` / `requires …` clause wherever §5.1's row carries
   one (the judge flags under `--judge llm`, `--judge-budget N%` under `--jev-pre-triage`,
   `--root` containment, E-58).

The flag's metavar MUST be the value vocabulary of §5.1's synopsis — `PATHS`, `FILE`, `DIR`,
`IDS`, `MODE`, `FRACTION`, `N`, `SECONDS|N%`, `LEVEL` — never the argparse destination name.

Each `--help` screen additionally carries:

- an **`environment:` block** in its epilog, one entry per variable the kernel reads: its name(s),
  the condition under which it is read, whether it is required, and its default; the names are
  exactly the `SPECCHECK_*` literals `src/speccheck/*.py` reads (T-98), plus one clause for
  `COLUMNS`, the only variable that changes a `--help` run's output (its line wrapping; D-41). No
  entry ever carries a value (R-23, I-007).
- an **exit-code epilog**: the §5.4 set (`0` conforming, `1` not conforming, `2` usage, `3` input
  contract) and the §5.1 summary line, so an operator or agent can construct and interpret a run
  from the help alone (D-40).

The help's value tokens are the *validator's* tokens: for every flag with a finite accepted set,
the tokens its help names equal the tokens its own usage error names (T-95), and the tokens are
checked against the parser, not against this paragraph. Exact wording is not normative (D-38); the
rendered bytes are pinned by T-97's golden at `COLUMNS=80`, and a wording change is a test diff,
not a spec revision. `--help` itself is inert: it exits `0`, writes only to stdout, and reads no
project file, no environment variable and no socket (I-017).

---

## 5. Interface specification

### 5.1 CLI (`speccheck`), the only surface

```text
speccheck check --spec SPEC.md [--src PATHS]... [--tests PATHS]... [--results junit.xml]
                [--root DIR] [--out DIR] [--judge none|mock|llm] [--strict]
                [--judge-concurrency N] [--judge-budget SECONDS|N%] [--jev-pre-triage]
                [--max-unknown FRACTION] [--progress auto|always|never] [--verbose [INFO|DEBUG]]
speccheck impact --spec SPEC.md (--changed IDS | --against OLD_SPEC.md) [--src PATHS]... [--tests PATHS]...
                 [--root DIR] [--out DIR] [--depth N] [--verbose [INFO|DEBUG]]
speccheck explain ID [--spec SPEC.md] [--src PATHS]... [--tests PATHS]... [--results junit.xml]
                 [--root DIR] [--judge none|mock|llm] [--depth N] [--judge-concurrency N]
                 [--judge-budget SECONDS|N%] [--jev-pre-triage] [--max-unknown FRACTION]
                 [--progress auto|always|never] [--verbose [INFO|DEBUG]]
speccheck --self-check [--verbose [INFO|DEBUG]]
speccheck --version
speccheck --help
```

| Subcommand / flag | Behavior | Exit |
| ------ | ---------------- | --- |
| `check` | Run the §3.1 pipeline; write both reports; print the summary line. | `0` conforming, `1` not, `2` usage, `3` input contract |
| `--spec FILE` | Required. Path to the specification; decoded as UTF-8 with `errors="replace"` (a Note is recorded if any byte was replaced). Missing flag or unreadable file → usage error. | `2` |
| `--src PATHS` | Repeatable; each value is a **PATHS list** — comma-separated files and/or directories per C-03, D-23. A resolved path is descended if a directory, scanned as one file otherwise; a segment inside `--root` that is neither a file nor a directory → usage error (E-52). Default: `src` if the directory exists, else none, only when the flag is absent. | `2` |
| `--tests PATHS` | As `--src` — a comma-separated list of files/directories (C-03, D-23) — but for test files and their case attribution; a directly-named `.swift` file's `MODULE` is its parent's last path component (D-18, D-23). Default: `tests` if the directory exists, else none, only when the flag is absent. | `2` |
| `--results FILE` | Optional JUnit XML. Absent → every cited ID is at most `UNVERIFIED`. Unreadable → usage error; malformed → E-05. | `2` / `3` |
| `--root DIR` | Base for relative paths in reports; default `.`. All of `--spec/--src/--tests/--results/--out` MUST resolve inside it (E-09). | `2` |
| `--out DIR` | Where the two reports go; default `.`. MUST resolve inside `--root` (E-09; F-002). Created if missing; not writable → E-18. | `2` / `3` |
| `--judge MODE` | `none` (default), `mock`, `llm`. Any other value → usage error. | `2` |
| `--strict` | Apply R-15 and, with `--judge llm`, R-28. | — |
| `--max-unknown FRACTION` | Threshold for R-28; default `0.2`; a float in `[0, 1]`, else usage error. Accepted with any judge mode; consulted only under `--strict --judge llm`. | `2` |
| `--judge-concurrency N` | K-06; default `4`, integer `1..32`, else usage error. Ignored unless `--judge llm`. | `2` |
| `--judge-budget SECONDS\|N%` | K-12; default `0` (unlimited). `SECONDS`: integer `0..86400`. `N%`: an integer `0..100` followed by `%`, accepted only with `--jev-pre-triage` under `--judge llm` (else E-58, exit `2`). Any other value → usage error. The `SECONDS` form is ignored unless `--judge llm`; the `N%` form is not ignored anywhere — it either applies or is a usage error. | `2` |
| `--jev-pre-triage` | K-16 (v1.15); boolean, default off. Runs the C-17 triage pass and orders the judge's issue queue by it. Ignored unless `--judge llm`: under `--judge none`/`mock` no Jev request is made and no C-17 variable is read. Requires `SPECCHECK_JEV_API_KEY` when it runs (E-21). | `2` |
| `--progress MODE` | R-30, C-11. `auto` (default): draw the judge progress indicator iff `sys.stderr.isatty()` is true and verbosity is not `DEBUG`; `always`: draw it even when stderr is not a TTY (still suppressed under `--verbose DEBUG`, E-39); `never`: never draw it. Any other value → usage error. Ignored unless `--judge llm`. | `2` |
| `--verbose [LEVEL]` | §5.3. Bare = `INFO`. `LEVEL` other than `INFO`/`DEBUG` → usage error. | `2` |

Every row of this table is also stated, in the form C-19 pins, in the `--help` output of the subcommand that defines the flag (v1.18, R-41); the table stays normative and T-95 checks the values against the validator's own usage-error text, so the two cannot disagree about an accepted token.
| `--self-check` | Copy the packaged fixture `speccheck/_selfcheck/` (a byte-identical copy of the §9.8 golden fixture `fixtures/target/`, its `golden/` directory included; F-107) into a fresh temporary directory `<tmp>`; install a socket guard; then run, **in the same process**, exactly `check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --root <tmp> --out <tmp>/out` with the working directory set to `<tmp>` (Q-003). The inner check is **expected** to exit `1` (the fixture has planted defects) and that exit code is not the self-check's result; compare `<tmp>/out/speccheck.json` and `<tmp>/out/SPEC_CONFORMANCE_REPORT.md` to `<tmp>/golden/` byte-for-byte; remove `<tmp>`; print `self-check: ok` when both match, else one line naming the first mismatch or failure (F-011). | `0` / `1` |
| `--version` | Print `speccheck <semver>` and exit. | `0` |
| `impact` | v1.13 (R-37, C-13). Run the §3.1 `impact` pipeline; write `impact.json` and `IMPACT_REPORT.md` under `--out`; print the C-13 summary line. Accepts `--spec`, `--src`, `--tests`, `--root`, `--out`, `--verbose` with the meanings above, except that `--src`/`--tests` have **no directory default** here: absent means not scanned (C-13), since the scan is optional for `impact`; no `--results`, no judge flags — any of them → usage error (E-54). | `0` written, `2` usage, `3` input contract |
| `--changed IDS` | `impact` only. Comma-separated ids (R/C/I/K/E/T or D), each declared in `--spec`; an undeclared one → E-53; empty → usage error. Mutually exclusive with `--against` (E-54). | `2` |
| `--against FILE` | `impact` only. A prior version of the spec, inside `--root` (E-09), parsed by C-01; the changed set is the C-13 diff. Unreadable → usage error; its E-01/E-02/E-03 → `3` with `--against: ` prefixed. Mutually exclusive with `--changed` (E-54). | `2` / `3` |
| `--depth N` | `impact` (v1.13) and `explain` (v1.17). Integer `0..999`, default `1`; `0` = unbounded (C-13; for `explain`, the reach of C-18's `impact (<depth>):` section). Other values → usage error. | `2` |
| `explain ID` | v1.17 (R-40, C-18). Run the §3.1 pipeline over the same inputs as `check` and render the C-18 trace for the one id `ID` to stdout; write no report file. Accepts `--spec`, `--src`, `--tests`, `--results`, `--root`, `--judge`, `--judge-concurrency`, `--judge-budget`, `--jev-pre-triage`, `--max-unknown`, `--progress`, `--verbose` and `--depth` with the meanings above, and `ID` as a positional argument (one id per invocation, D-36). No `--out`, no `--strict`: they are not defined on this subparser, so argparse rejects them as unrecognized arguments (E-54's pattern). An undeclared `ID` → E-60. | `0` rendered, `2` usage, `3` input contract |

**The `--src`/`--tests` PATHS list (D-23).** Each flag value is a comma-separated list, one list per occurrence. To build the effective list the extractor walks, each occurrence is split on the literal `,`, every resulting segment is whitespace-trimmed and empty segments dropped; the surviving paths are resolved inside `--root` (E-09) and deduplicated (I-012). Each resolved path is a directory (descended as in v1.11: K-02/K-03, E-10/E-11/E-13/E-29/E-30/E-33 apply) or a regular file (scanned as one, no descent); a segment that resolves inside `--root` but exists as neither is a usage error (E-52), replacing the former "non-directory → usage error". The full rule — including the absent-flag-only default, the directly-named-file Swift `MODULE`, and the determinism of the emitted order — is C-03 *PATHS*; the summary-line regex, both report files, and the exit codes are otherwise unchanged for two inputs that name the same file set. Example: `--src a.py,b.py,src --tests tests/unit,tests/core` is equivalent to `--src a.py --src b.py --src src --tests tests/unit --tests tests/core` (the list is repeatable), and `--src a.py,,src,` trims and drops to `[a.py, src]`.

**Summary line (stdout, exactly one line, only on exit 0/1):**

```text
speccheck: <STATUS> - <passing>/<in_scope> passing (<pct>%), <failing> failing, <skipped> skipped, <weak> weak, <unverified> unverified, <untested> untested, <uncited> uncited; <dangling> dangling, <stale> stale; judge=<mode><judge-suffix>
```

The line above is shown unwrapped on purpose: it is one physical line, ASCII only, terminated by a
single `\n`, and written to stdout as UTF-8 regardless of locale (R-29; F-010). `<STATUS>` is
`CONFORMING` (exit 0) or `NOT CONFORMING` (exit 1); `<pct>` is `conformance × 100` rounded
half-even to one decimal; `<judge-suffix>` is empty unless R-28 forced exit 1, in which case it is
` (unavailable)` or ` (unknown_rate <rate> > max_unknown <max>)` with both numbers as in the JSON;
when both R-28 reasons hold the suffix is ` (unavailable)` (Q-004). The seven counts after the
ratio are the seven in-scope statuses of C-07 `by_status`, each exactly once (Q-005).

Regex the line MUST match (T-44):

```text
^speccheck: (CONFORMING|NOT CONFORMING) - \d+/\d+ passing \(\d+\.\d%\), \d+ failing, \d+ skipped, \d+ weak, \d+ unverified, \d+ untested, \d+ uncited; \d+ dangling, \d+ stale; judge=(none|mock|llm)( \(unavailable\)| \(unknown_rate \d\.\d{4} > max_unknown \d\.\d{4}\))?$
```

### 5.2 GUI

None. This system has no graphical surface, and O-3 explicitly leaves one out of v0.1.

### 5.3 Diagnostics and verbosity contract

- **Quiet by default.** With no `--verbose`, the process writes nothing to stderr on exit 0/1 and only the usage/contract error message on exit 2/3. Sole exception: the C-11 progress indicator under `--judge llm` (R-30), which is written directly to the stream, is redrawn in place, and is erased before the judge stage ends — so what *remains* on stderr at exit is still nothing (or only the error message). It is never routed through the logger.
- **Syntax.** `--verbose` alone $\equiv$ `--verbose INFO`; `--verbose INFO` and `--verbose DEBUG` are accepted; any other value is a usage error (exit `2`).
- **INFO** (stderr): one line per pipeline stage with counts and elapsed milliseconds (files scanned, IDs declared, citations found, test cases attributed, results joined, edges judged), the judge mode, and for the LLM judge the URL and model. INFO MUST NOT include file contents, statement text, judge prompts, judge responses, or the API key.
- **DEBUG** (stderr): INFO plus, per judged edge, the full `JudgeRequest` JSON as sent and the raw provider response as received, each prefixed `judge>` / `judge<` on its own line. The API key is redacted. DEBUG MUST NOT change stdout or either report file. Because these lines are emitted *during* the judge stage, the progress indicator is not drawn at DEBUG regardless of `--progress` (E-39); the per-edge lines are the progress record at that level.
- **Mechanism.** Python `logging` with a single stderr `StreamHandler`; logger name `speccheck`; format `%(levelname)s %(message)s`. Level is `ERROR` by default and `INFO`/`DEBUG` per flag, so nothing below ERROR reaches stderr without `--verbose` (F-014). The E-10..E-13 and E-27..E-30 Notes are logged at `INFO` (they are always in the report's Notes regardless of level); nothing is ever logged at `WARNING`; the exit-2/3 message is logged at `ERROR`. While the C-11 indicator is displayed, the logger emits nothing: the judge stage's INFO lines (judge mode, URL and model, the stage summary) are written after the erase (K-13; F-201).

### 5.4 Exit codes

| Code | Meaning | Reports written? |
| --- | ---------- | --- |
| `0` | `CONFORMING`: no in-scope ID is `FAILING`; and if `--strict`, every in-scope ID has status `PASSING`, `dangling` and `stale` are empty, and — with `--judge llm` only — `judge_available` is `true` and `unknown_rate` $\leq$ `max_unknown` (R-28). Beyond R-28, status is the only judge-related input (F-003). | yes |
| `1` | `NOT CONFORMING`: anything else the report can express | yes |
| `2` | Usage error (bad flag/value, missing required, path outside root, missing judge env) | no |
| `3` | Input contract violation (E-01, E-02, E-03, E-05, E-18) | no |

Any uncaught exception MUST also map to `3` with a one-line message; a traceback is printed only under `--verbose DEBUG`. `KeyboardInterrupt` is treated the same way, with the message `interrupted` (E-41).

`impact` (v1.13) uses `0` (both C-13 reports written; there is no `1`: nothing it reports is pass/fail), `2` (usage, E-53, E-54), and `3` (E-01/E-02/E-03 on either spec, E-18); the same "reports written?" column applies.

`explain` (v1.17) uses `0` (the C-18 trace written; there is no `1`: nothing it renders is pass/fail), `2` (usage, E-60) and `3` (E-01/E-02/E-03); it writes no file, so E-18 and the "reports written?" column do not apply to it.

Since v1.18 this set is reachable from the CLI itself: every `--help` screen carries the exit-code epilog C-19 pins (D-40), naming the four codes and the summary line.

---

## 6. Invariants (must hold in every valid implementation)

| ID | Invariant |
| -- | --------- |
| **I-001** | **Read-only inputs.** No file under `--root` other than the two report files of the subcommand that ran, under `--out` (`check`: `speccheck.json`, `SPEC_CONFORMANCE_REPORT.md`; `impact`: `impact.json`, `IMPACT_REPORT.md`; v1.13) — and the `--out` directory itself, if it did not exist — is created, modified, or deleted by a run, and no temporary of §3.1 survives a run; no file outside `--root` is written at all. Sole exception: `--self-check` creates, uses, and removes one fresh temporary directory (F-011); it writes nowhere else. |
| **I-002** | **Determinism.** For `--judge none` and `--judge mock`, and for every `impact` run (v1.13), identical inputs (bytes of every file read, argv, env) produce byte-identical report files and summary line, on any OS. A `SPEC.md` that differs from another only in `\r\n` versus `\n` line endings counts as identical input (C-01 Lines rule; F-301). |
| **I-003** | **Exactly-once reporting.** Every declared ID (retired included) appears exactly once in `ids` and exactly once in the Markdown per-ID table; no undeclared ID ever appears there. A decision (C-01 (c)) is not an ID: it appears exactly once in `decisions` and never in `ids` (D-25). |
| **I-004** | **Downgrade-only judge.** For every ID, `status_with_judge` $\in$ `{status_without_judge}` $\cup$ (`{WEAKLY_PASSING}` iff `status_without_judge == PASSING`). Disabling the judge never changes any status except `WEAKLY_PASSING` → `PASSING`. |
| **I-005** | **Grounded verdicts, on both sides.** Every verdict in a report carries an `evidence` list (possibly empty), every `ASSERTS` carries $\geq$ 1 entry, and every evidence entry points to a line inside the judged test case's span in the judged file; and every `ASSERTS` or `EXECUTES_ONLY` carries a `clause` that is LOCATED in the judged ID's statement per K-15 (v1.9, R-34). |
| **I-006** | **Network boundary.** With `--judge none`/`mock`, no socket is opened for the lifetime of the process. |
| **I-007** | **Secret and payload hygiene.** The API key never appears in stdout, stderr, or either report. INFO never contains file contents, statements, prompts, or responses. |
| **I-008** | **Total metrics.** Every ratio is either a number in `[0, 1]` or `null`/`n/a`; no run raises on a zero denominator. |
| **I-009** | **Exit $\equiv$ report.** `exit_code` in `speccheck.json` equals the process exit status, and both are computable from the rest of the JSON plus `strict` by the §5.4 rule. |
| **I-010** | **One judge call per edge.** The judge is invoked at most once per (test case, ID) edge per run, and only for edges whose ID is `PASSING` after C-05 step 4, is not RECORDED (R-35), and whose test outcome is `passed`. |
| **I-011** | **Family-safe numbering.** ID normalization is injective within a family: `R-7`, `R-07`, `R-007` map to one ID; `R-07` and `C-07` never collide. |
| **I-012** | **One scan per physical file (D-23).** For the `--src` list, and separately for the `--tests` list, every physical file reached by the PATHS elements is scanned and produces citations at most once (C-03 PATHS deduplication): a file reached by two overlapping elements, or named directly and also covered by a directory element, is deduplicated by resolved path. Where a direct file and a directory element both cover a file, that file's recorded `--src`/`--tests` root — and therefore a directly-named `.swift` file's `MODULE` (D-18) — is the FIRST element in the effective-list order that covers it; the emitted citation order is by ascending resolved path, independent of the order in which paths were named. Two inputs that name the same physical file set produce byte-identical reports (I-002). |
| **I-013** | **The direct set is exact; depth is a prefix (v1.13).** In every `impact` report, an id is at depth 1 if and only if it is the `dst` of an `affects` edge whose `src` is a changed D id, or the `src` of a `depends_on` edge whose `dst` is a changed id, and it is not itself in the changed set; and for every $N \geq 1$ the `impact` list under `--depth N` is exactly the rows of the `--depth 0` list whose depth is $\leq N$, in the same order with the same `via`. |
| **I-014** | **`declared` is a pure function of the source and test trees (v1.14).** `Citation.declared` and every value derived from it (`JudgeRequest.declared`, `tests[].declared`, `declared_ratio`) depend only on the bytes of the files under `--src`/`--tests` and their citations; two runs with identical source and test trees produce identical `declared` values and `declared_ratio` regardless of `--judge` mode, `--results`, or network access — extending I-002's determinism guarantee to this fact. |
| **I-015** | **Jev stays advisory (v1.15).** For every edge, and under every combination of `--jev-pre-triage` and `--judge-budget`, the recorded `Verdict` (`verdict`, `clause`, `evidence`, `rationale`, `coerced`) is produced only by the configured `--judge` provider (C-06: `mock`, or the C-09 `llm` provider) or by an existing C-06 coercion rule. The C-17 triage provider's response is read only to compute K-16's order; it is never validated against C-06, never written to `speccheck.json` or `SPEC_CONFORMANCE_REPORT.md`, and never the source of a `Verdict`. Its request is not a judge call: I-010 is unchanged and applies to the judge alone, so a triaged run makes one C-17 request per judge-eligible edge and then one C-06 request per edge it issues. |
| **I-016** | **`explain` is additive and read-only (v1.17).** `explain` writes no report file, changes no status, verdict, citation, metric or note, and issues no judge call a `check` run over the same inputs would not issue (E-61). The facts it renders are the same `IdRecord`/edge/`Verdict` facts that run produces and the same `walk`/`reverify` facts `impact` produces (C-12, C-13), so a `check` and an `explain` over identical inputs agree on every status the trace shows, and no `--strict` gate moves. |
| **I-017** | **`--help` is inert (v1.18).** `speccheck --help`, `speccheck check --help`, `speccheck impact --help` and `speccheck explain --help` exit `0`, write only to stdout, and read no project file, no environment variable and no socket — naming the C-09/C-17 variables in the epilog is printing their names, not reading them. They therefore behave identically inside a project tree and in an empty directory, and the help text is a pure function of the installed version and the terminal width, which affects line wrapping only (C-19, T-96). |

---

## 7. Constraints (precise and measurable)

| ID | Constraint |
| -- | ---------- |
| **K-01** | Usage errors exit `2`; input-contract violations exit `3`; conformance outcomes exit `0`/`1`; no other exit codes exist. |
| **K-02** | Files larger than 2 MiB (2,097,152 bytes) under `--src`/`--tests` are skipped with a Note (E-10); binary files (a `0x00` byte within the first 8192 bytes) are skipped silently (E-29); text files that are not valid UTF-8 are decoded with `errors="replace"` and noted (E-11). |
| **K-03** | Directories named `.git`, `.hg`, `.svn`, `node_modules`, `__pycache__`, `.venv`, `venv`, and any directory whose name starts with `.` are never descended into; symbolic links to files or directories are never followed (E-30). |
| **K-04** | ID numbers are 1–3 digits; a token with 4+ digits is not an ID. |
| **K-05** | LLM judge timeout is `SPECCHECK_JUDGE_TIMEOUT` seconds (default 30) per edge, wall-clock, measured from the moment the request is issued to the moment the full response body has been received, and covering every phase in between — DNS resolution, TCP connect, TLS handshake, request send, response receive (Q-010). |
| **K-06** | Exactly one HTTP request per judged edge; no retries, no batching. Requests MAY be issued concurrently, at most `--judge-concurrency` at a time (default `4`, integer `1..32`); output order is fixed by C-07 and MUST NOT depend on completion order (F-110). |
| **K-12** | `--judge-budget` has two forms (v1.15). `SECONDS` (default `0` = unlimited; integer `0..86400`): bounds the wall-clock spent in the judge stage, measured from the first request issued. The deadline is `start + budget`. A request is *started* when it is issued; no request is issued at or after the deadline; requests in flight at the deadline are allowed to complete (each still bounded by K-05) and their verdicts count. `N%` (an integer `0..100` followed by `%`; accepted only with `--jev-pre-triage` under `--judge llm`, else E-58): exactly $\lceil N/100 \times E \rceil$ of the $E$ judge-eligible edges (I-010) are issued, in K-16's ascending-confidence order, and no other edge is issued, regardless of wall-clock time elapsed. Under both forms every edge not issued receives `UNKNOWN` with rationale `judge: budget` and `coerced: true`, and one Note records how many (F-110, Q-010). `SECONDS 0` is unlimited; `N%`'s `0%` issues none (a pure triage dry run) and its `100%` issues every eligible edge — the same report content as `SECONDS 0`, by an explicit count instead of a deadline that never arrives. |
| **K-13** | The progress indicator (C-11) is drawn once when the judge stage starts (with $d = 0$, `0:00 elapsed`); every determined verdict is reflected by a draw within 100 ms of its determination (a burst of verdicts MAY be coalesced into one draw); it is redrawn at least once per second of wall-clock while any request is in flight so that `elapsed` and `left` keep moving; and it is never drawn more than 10 times per second. Each draw and the erase is one atomic write, serialized across threads. The bar has exactly 20 cells. From the first draw to the erase nothing else is written to stderr (F-201). The indicator is erased exactly once, when the judge stage ends, after the final state has been drawn and before the `report` stage begins — before any INFO stage line, Note, error message, or the summary line is written. |
| **K-14** | A statement (C-01: title, newline, section body) is at most 16,384 bytes of UTF-8. A longer statement is truncated to the longest prefix of whole lines whose UTF-8 length, joined by `\n`, is $\leq$ 16,384 — the title line is always kept — followed by `\n` and the marker line `… (statement truncated by speccheck at K-14)` (U+2026, one space, then ASCII); the marker does not count toward the cap. The truncated text is what `SpecId.text`, the judge, and the JSON carry; `title` is unaffected; one Note `statement truncated at K-14: <ID>` is recorded per truncated ID (E-46). Table declarations never approach the cap. Reference points: the largest contract of the MonteCarloPi spec is 2.7 kB and the largest in this document is C-03 at 8.4 kB, so neither T-48 nor any known spec is truncated; the cap is a bound on the judge payload (about 4 k tokens per edge at most), not a working limit (D-20). |
| **K-15** | A `clause` is LOCATED when, after collapsing every run of whitespace in both strings to one space, trimming the clause (F-406), and cutting it to its first 280 characters, it is a case-sensitive substring of the statement and is at least 12 characters long — or the statement itself is shorter than 12 characters and the clause equals it (an empty statement is matched by an empty clause). The cut, not truncated-with-ellipsis, form is what is recorded (a prefix of a located excerpt is still located). |
| **K-07** | `rationale` $\leq$ 280 characters after truncation; single line (newlines replaced by spaces). |
| **K-08** | Kernel performance, measured on the reference machine named in `SPEC_BUILD_REPORT.md` (CPU model, RAM, OS, Python build, run in isolation): `check --judge mock` on the §9.8 golden fixture completes in $\leq$ 2 s wall-clock, and a generated 10,000-file tree with 100 declared IDs in $\leq$ 60 s. Both bounds are recorded, not CI-gated (F-017). |
| **K-09** | JSON output is UTF-8, `indent=2`, `ensure_ascii=False`, sorted per C-07 (not alphabetically), trailing newline; Markdown output is UTF-8 with `\n` line endings. |
| **K-10** | `--version` prints a PEP 440 version equal to the package metadata version. |
| **K-11** | `--max-unknown` defaults to `0.2`, accepts a decimal in `[0, 1]` (parsed as a Decimal from its literal text), and is compared to the quantized `unknown_rate` of C-07 (Decimal, 4 places, ROUND_HALF_EVEN; Q-009); equality passes; a `null` `unknown_rate` (zero judged edges) never exceeds it (F-105). |
| **K-16** | `--jev-pre-triage` (boolean, default off; ignored unless `--judge llm` — under `--judge none`/`mock` no C-17 request is made and no C-17 variable is read). Before any real-judge request is issued, the kernel MUST build one triage task per judge-eligible edge (I-010) in C-17's request shape — the C-06 request object for that edge, `{id, statement, related, declared, file, start, end, source}` (the `related` neighbourhood rides the triage `state` as it does the real-judge request, D-28b, R-38), rendered as C-17's `state` text — and send it to the C-17 endpoint at `--judge-concurrency`, with no retries (K-06). The edges are then handed to the otherwise unchanged real-judge issue loop (K-05, K-12, C-06) in ascending $p(e)$ (C-17), ties broken by ascending id in C-07's id order; a per-edge Jev failure is ordered first and counted in one Note (E-59) and never aborts the run. Jev's answer is discarded once the order is computed (I-015). Under `--judge-budget 0` the pass changes no report content — only the issue order, visible in the C-11 indicator — and one Note `jev-pre-triage had no effect: --judge-budget is unlimited` records that (D-30). |

---

## 8. Edge cases and failure semantics

| ID | Case | Semantics |
| -- | ---- | --------- |
| **E-01** | Spec declares zero IDs (or all declared IDs are retired) | Exit `3`, message `spec declares no in-scope IDs`; no reports written. |
| **E-02** | Same ID declared twice (both non-retired, or both retired); since v1.13 also a decision D-nn declared by two rows of the decision table (C-01 (c)) | Exit `3`, message names the ID and both lines. |
| **E-03** | ID declared retired and also declared non-retired (any order) | Exit `3`, message names the ID and both lines (a spec must retire *or* keep an ID, not both). |
| **E-04** | ID declared inside a fenced code block in `SPEC.md` | Not a declaration; ignored silently (spec templates contain example IDs). |
| **E-05** | `--results` file is not well-formed XML, or root is neither `testsuites` nor `testsuite`, or a `<testcase>` lacks `name` | Exit `3`, message `results: <reason>`. |
| **E-06** | Duplicate `(classname, name)` in results | Single outcome = worst of them (C-04); a Note records the count. |
| **E-07** | Result `<testcase>` joins no attributed test case | Listed under `unattributed_results`; not counted for any ID; exit unaffected. |
| **E-08** | Test case cites an ID but has no result (results absent, or case not run) | Case listed under that ID's `unrun`; ignored in C-05 step 4; if *no* citing case has a result → `UNVERIFIED`. |
| **E-09** | Any of `--spec/--src/--tests/--results/--out` — including any element of a `--src`/`--tests` PATHS list — resolves outside `--root` (after symlink resolution) | Exit `2`, message `path outside --root: <path>`. A PATHS element that is itself a symlink and resolves inside `--root` is used in resolved form and descended (a directory) or scanned (a file); it is not an E-30 skip (Q-007, D-23). |
| **E-10** | File > 2 MiB under a scan root | Skipped; Note `skipped 1 file over 2 MiB: <path>`. |
| **E-11** | A scanned file — or `SPEC.md` itself — is not valid UTF-8 | Decoded with replacement; Note; citations on replaced bytes are impossible (token requires ASCII) so no false citations arise. |
| **E-12** | `.py` test file fails to parse | Whole file is one file-level case; Note `parse fallback: <path>`. |
| **E-13** | Test citation lands in a file-level case (module docstring, helper, fixture) | Attributed to the file-level case; that case has no JUnit outcome by construction (name `""`), so it can only ever contribute `UNVERIFIED`; the JSON carries `"name": ""` and the Markdown renders the label `(file)` (Q-011). |
| **E-14** | Judge provider unreachable, times out, or returns HTTP $\geq$ 400 | Verdict `UNKNOWN`, `coerced: true`, rationale `judge: unavailable` / `judge: timeout` / `judge: http <code>`; `judge_available` set `false` if *every* call failed; exit unaffected unless `--strict` (E-32). |
| **E-15** | Judge returns non-JSON or JSON lacking `verdict` | `UNKNOWN`, `coerced: true`, rationale `judge: malformed response`. |
| **E-16** | Judge returns `ASSERTS` with no evidence, or evidence outside the span / in another file | `UNKNOWN`, `coerced: true`, rationale `judge: ungrounded`. When the same reply also fails K-15, E-48 wins (C-06 rule order, F-402). The raw answer is available only at DEBUG. |
| **E-17** | Judge returns a valid verdict for an ID whose test span contains no code at all (empty function) | Verdict recorded as returned; the kernel does not second-guess content, only grounding. |
| **E-18** | `--out` cannot be created, or a temporary or final report file cannot be written or renamed | Exit `3`; message `out: <reason>`; on exit neither final report from this run exists and no `.tmp` from this run remains. Because renames happen JSON-then-Markdown (§3.1), the only stale combination an operator can find is: a previous run's `SPEC_CONFORMANCE_REPORT.md` with no `speccheck.json` (F-106). |
| **E-19** | Both `--src` and `--tests` empty/absent | Run proceeds; every in-scope ID is `UNCITED`; exit `1` (or `0` only if `in_scope == 0`, which is E-01). |
| **E-20** | Dangling citation of a token that *looks* retired in code (`~~R-99~~` in a comment) | Strikethrough is only meaningful in `SPEC.md`; in code it is a plain citation of `R-99` → dangling. |
| **E-21** | `--judge llm` with a required env var missing | Exit `2`, message names the variable, key value never echoed. |
| **E-22** | Test file cites the same ID on several lines of one case | One edge; `lines` lists every line. |
| **E-23** | `--spec`, `--results`, or a report path lies under a `--src`/`--tests` root (e.g. `--src .`, or `--out` inside `src/`) | Those files are not scanned and produce no citations; no Note; a second run over the same inputs is byte-identical to the first (F-002). |
| **E-24** | JUnit `name` carries a parametrization suffix (`test_x[3-True]`), or several `<testcase>` join one case | Suffix stripped for the join; each raw result kept in `results`; the case's `outcome` is the worst of them (F-005). |
| **E-25** | A T id is cited in source files but by no test case | `UNCITED` (source citations are evidence only for family T); listed under `src` in the report (F-001). |
| **E-26** | An ID has judge verdicts of both `ASSERTS` and `EXECUTES_ONLY` on passed edges | Status `PASSING`; passes `--strict`; the `EXECUTES_ONLY` edge remains visible in §8 of the report (F-003). |
| **E-27** | A result's classname suffix-matches two test cases equally (`tests/a/test_core.py` and `tests/b/test_core.py`, result classname `test_core`) | Unattributed; one Note names the result and all candidates; neither case receives the outcome (F-006). |
| **E-28** | A `test*` function (underscore or not) is a method of a class that is neither `Test*`-named nor a `*TestCase` subclass, or of a nested class | Not a test case; its citations are file-level; one Note per file lists the undelimited names (F-007, F-102). |
| **E-29** | A file under a scan root contains a `0x00` byte in its first 8192 bytes | Skipped silently: no citations, no test case, no Note (F-008). |
| **E-30** | A symbolic link (file or directory) is encountered *during descent* under a `--src`/`--tests` directory element | Not followed; one Note per run: `skipped N symlink(s)` (F-008). A symlink that is itself a PATHS element (on the command line) is E-09's case, not this one (Q-007). |
| **E-31** | A bold ID token appears in a table cell other than the first, or in a heading after other tokens | Not a declaration (F-009). It is also not a citation: `SPEC.md` is never scanned for citations. |
| **E-32** | `--strict --judge llm` and either `judge_available == false` or `unknown_rate > max_unknown` | Exit `1` even if every status is `PASSING`; `strict_judge_failure` set to `"unavailable"` if the judge was unavailable (whether or not the rate also exceeds), else `"unknown_rate"`; summary line carries the matching suffix (F-012, Q-004). Without `--strict`, or with `--judge none|mock`, no effect. |
| **E-33** | A line contains `speccheck:ignore`, or a file's first three lines contain `speccheck:ignore-file` | The line yields no citations / the file is not scanned; ignored files are counted in one Note (F-013). |
| **E-34** | A `.speccheck.json.*.tmp` or `.SPEC_CONFORMANCE_REPORT.md.*.tmp` from a killed run exists under `--out`, which lies under a scan root | Never scanned (C-03); deleted at §3.1 step 1; the run's reports are byte-identical to a run without the leftover (F-103). |
| **E-35** | `--judge llm` and the `--judge-budget` deadline passes with edges not yet started, or the `N%` form's issued count is reached | Each such edge is `UNKNOWN`, `coerced: true`, rationale `judge: budget`; in-flight requests complete and count; one Note `judge budget exhausted: N edge(s) unjudged`; `unknown_rate` counts them; R-28 applies as usual (F-110, Q-010). Under the `N%` form the unissued edges are the ones K-12's order left last, and they are determined before any request is issued — no wall-clock condition is involved. |
| **E-36** | `--judge llm` with zero eligible edges | No request is sent — to the judge, and (with `--jev-pre-triage`) to C-17 either; `judge_available` is `true`; `unknown_rate` is `null` and never trips R-28 (F-105). |
| **E-37** | A `tests[]` entry whose case was not judged: judge disabled, or the ID not `PASSING` after C-05 step 4, or the ID RECORDED (R-35), or the outcome not `passed` — this row owns the condition; C-05, C-07 and T-34 cite it (F-403) | JSON `verdict` is `null` (key present); Markdown renders an em dash in the verdict position; the entry never appears in report §8 (Q-001). |
| **E-38** | Two or more Notes are produced in one run | Emitted in ascending Unicode code-point order of their full text, in both reports (Q-002). |
| **E-39** | `--judge llm` with stderr not a TTY (CI log, redirected file, pipe) under `--progress auto`; or `--verbose DEBUG` under any `--progress` value; or `--progress never`; or `--judge none\|mock` under any `--progress` value | No progress bytes (neither draw nor erase) are written to stderr; the run is otherwise identical. `--progress always` overrides only the TTY test, never the DEBUG or judge-mode suppression (R-30). |
| **E-40** | The judge stage is cut short while the indicator is displayed: a provider raises out of the stage (should not happen — E-14..E-16 coerce), an uncaught exception, or an interrupt (E-41) | The erase sequence is written before the exit-`3` message (§5.4, E-41); no partially drawn line remains on stderr. The erase MUST happen in a `finally`-equivalent path so it cannot be skipped (R-30, K-13). |
| **E-41** | `SIGINT` / `KeyboardInterrupt` at any stage | Exit `3` with the one-line message `interrupted`; the indicator, if displayed, is erased first (E-40); every §3.1 temporary of this run is removed and no report file from this run remains (a report file already renamed is removed, per §3.1's failure rule); judge requests in flight are **abandoned**, not awaited — the process MUST exit within 1 s of the interrupt regardless of K-05 — and edges not yet started are never started (v1.5). No other exit code is produced (K-01); a traceback is printed only under `--verbose DEBUG` (F-204, D-16). |
| **E-42** | A `.swift` test file whose brace depth goes negative on some line or is non-zero at end of file (counted per C-03, outside comments and string literals) | Whole file is one file-level case; Note `parse fallback: <path>` (R-31; the E-12 rule). |
| **E-43** | A `.swift` function named `test*` that is neither `@Test`-attributed nor a direct `test*` method of an `XCTestCase` class (a method of another type, a member of a nested class, a free function) | Not a test case; its citations are file-level; one Note per file lists the undelimited names as `<Chain.name>` (R-31; the E-28 rule). |
| **E-44** | A declaring table row whose first cell begins with a bold ID form and continues with whitespace-separated decoration (`**K-07** **[port]**`) | Declares the ID; the decoration is dropped; a bold ID inside the decoration is not a declaration; a first cell where the form is followed by a non-whitespace character (`**K-07**x`) declares nothing (R-32). |
| **E-45** | Two Swift test cases with the same identifier and classname (overloads by parameter label) | A result with that `join_name` ties between them: unattributed, one Note names the result and both candidates (C-04; the E-27 rule). |
| **E-46** | A heading-declared ID whose statement (title plus section body) exceeds K-14; or whose section body is empty — the heading is followed only by blank lines before the next heading of the same or a higher level, or before end of file | Over the cap: truncated per K-14, marker line appended, one Note `statement truncated at K-14: <ID>`; `title` is unaffected and the Markdown table shows it. Empty body: the statement is the title alone, exactly as through v1.6; no Note. Empty title with a body (`### C-04` followed by text): the statement is the body alone (F-305). (R-33) |
| **E-47** | A heading-declared ID whose section body contains a deeper heading that itself declares an ID (`#### E-09 …` under `### C-01 …`, retired or not), or a table with declaring rows | Those inner declarations are parsed exactly as before, each with its own title, statement, and body; the outer ID's statement includes their text verbatim as context (the judge sees the sub-rows). A declaring heading's body ends only at a heading of level $\leq$ its own, so a deeper declaring heading never ends it (R-33, E-31). |
| **E-48** | Judge returns `ASSERTS` or `EXECUTES_ONLY` with a `clause` that is missing, empty, paraphrased, or shorter than 12 characters against a longer statement | `UNKNOWN`, `coerced: true`, rationale `judge: unlocated clause`; counted in `unknown_rate`, so a model that cannot quote the statement surfaces through R-28 rather than through silent mis-verdicts (R-34, K-15). The raw answer is available only at DEBUG. |
| **E-49** | Judge returns `UNRELATED` or `UNKNOWN` with a non-empty `clause`; or a `clause` that is present but not a JSON string (`null`, a number, an object); or a verdict that any C-06 rule coerces to `UNKNOWN` | Recorded with `clause` `""`; a returned `UNRELATED`/`UNKNOWN` is not coerced and gets no Note; a non-string `clause` is treated as absent before the K-15 check, so on an `ASSERTS`/`EXECUTES_ONLY` it is E-48 (R-34, F-402). |
| **E-50** | The `*(recorded)*` marker on a declaration whose family is not T (`| **R-07** *(recorded)* |`) | The id is declared normally and is not RECORDED (`recorded: false`); one Note `recorded marker ignored on <ID>: not a T id` (R-35). |
| **E-51** | A RECORDED T id whose citing test case failed, was skipped, has no result, or does not exist | Status by C-05 steps 1–4 exactly as for any T id — `FAILING`, `SKIPPED`, `UNVERIFIED`, `UNCITED`; the marker exempts an id from the judge (step 5) and from nothing else, so a recorded test still has to be present and green (R-35, R-15). |
| **E-52** | A `--src`/`--tests` PATHS element that resolves *inside* `--root` but exists there as neither a directory nor a regular file — a non-existent path, or a broken symlink to nowhere (E-09's containment check already passed) | Exit `2`, message `--<flag>: no such file or directory: <segment>` (D-23). This replaces v1.11's "non-directory → usage error": a directory is descended, a regular file is scanned, and anything else is an error. No reports are written. |
| **E-53** | `impact --changed` names an id that is not declared in `--spec` (an undeclared conformance id, an unknown decision, or a token that is neither — `X-01`, `R-`, `1234`) | Exit `2`, message `--changed: undeclared id: <element>` naming the first offending element in list order; no reports written (C-13). |
| **E-54** | `impact` given both `--changed` and `--against`, or neither; or given `--results` or any judge flag | Exit `2`, message `impact: exactly one of --changed, --against is required` (or `impact: --results is not accepted` / `impact: --judge is not accepted`); no reports written. An `--against` file that is unreadable or outside `--root` is the ordinary usage error (E-09); one that fails C-01 is exit `3` with `--against: ` prefixed to the E-01/E-02/E-03 message. |
| **E-55** | A statement or an *Affects* cell names a retired id | The edge is recorded with `retired: true` (C-12); `impact` walks it like any other, and every report row for a retired id — changed, impact, re-verify — strikes through the ID cell; a retired id in `--changed` is accepted. No Note: retirement is declared, not accidental. |
| **E-56** | A citation of family R/C/I/K/E has no test-case span to check for declaration — a `"src"`-kind citation, or a `"test"`-kind citation attributed to a file-level case (no enclosing named test case delimited it) | Always `declared: false`; no Note (this is definitional, not an anomaly — there is no per-test declaration of intent to check a file or an undelimited case against). |
| **E-57** | A `related` edge — a C-12 `depends_on`, both directions (R-38, D-28) — names a retired id, and a `related` field is built for a judged edge | The retired neighbour is included in the edge's `related` with its `title` and `(retired)` appended: a test asserting the retired obligation is exactly the off-topic `ASSERTS` this change exists to catch. The retired target on its `affects`/`depends_on` edge is marked `retired: true` (E-55), and the `affects`/`depends_on` edge is still recorded; an id with no neighbour at all sends `related` `[]`. Not a Note and not a status: it is how the judge's `related` neighbourhood (C-06 Part B, C-10) handles a retired target. |
| **E-58** | `--judge-budget N%` given without `--jev-pre-triage`, or with `--jev-pre-triage` under `--judge none`/`--judge mock` (where K-16 ignores the flag, so there is no ordering for K-12 to issue in) | Exit `2`, message naming both flags (`--judge-budget N% requires --jev-pre-triage with --judge llm`), before any request of either kind is issued and with no reports written; the message never contains a C-09 or C-17 key value (I-007). The `SECONDS` form is unaffected: it stays accepted-and-ignored unless `--judge llm`, exactly as before v1.15. |
| **E-59** | A C-17 triage request fails during `--jev-pre-triage`: non-200 status, transport error, timeout (`SPECCHECK_JEV_TIMEOUT`), non-JSON body, missing `answers.verdict`, a `choice` that is not one of C-06's four verdict tokens, or `probabilities` that are missing, empty, or non-numeric | That edge is ordered first (K-16) and one Note records how many edges this happened to; the run is not aborted, no edge is skipped because of it, and no edge's final `Verdict` is affected beyond its position in the issue order (I-015). A triage failure never sets `judge_available` false — that flag is the C-06 judge's fact (E-14) — and never enters `unknown_rate`. |
| **E-60** | `explain <ID>` names an id the spec does not declare | Exit `2`, message `explain: undeclared id: <ID>` (the R-07 dangling wording), and no trace is written. An id that *is* declared but has no citation and no edge is not an error: its trace carries the C-05 status with its reason and an empty `sources:` and `tests:` block, and exits `0` (E-13/E-19 style). |
| **E-61** | `--judge` on `explain` | Carries `check`'s contract exactly: the same provider, the same I-010 eligibility, the same C-06 validation and coercion, and the same `--judge-concurrency` / `--judge-budget` / `--jev-pre-triage` semantics. A coerced or failed verdict is rendered verbatim (`UNKNOWN (coerced)` with its rationale, E-14/E-15); under `--judge none`, and for any edge no provider judged, the verdict reads `not judged`; `explain` neither issues nor omits a judge call `check` would not make. |

---

## 9. Acceptance criteria, tests, and evals

Every test cites, in its docstring or a comment, its own T id and the R/C/I/K/E ids it proves, so that `speccheck` can check itself (§9.9; F-001) — and, since v1.14, that citation is what `declared` (C-14) checks mechanically: an id cited only elsewhere in a test's body is not this convention's declaration, whatever else it may be evidence of (R-39). Test inputs that contain the literal marker strings of C-01 (`speccheck:ignore`, `speccheck:ignore-file`) MUST live in data files under `tests/data/`, never inline in a test module, so self-application cannot ignore its own tests (F-109). Groups are ordered by pipeline stage.

### 9.1 Extraction (C-01, C-02)

| ID | Test |
| -- | ---- |
| **T-01** | Table-cell and heading declarations are both extracted with correct family, number, statement, and line; a `SPEC.md` containing invalid UTF-8 is decoded with replacement, its ASCII declarations are still found, and a Note is recorded. (R-01, E-11) |
| **T-70** | `\| **K-07** **[port]** \| s \|` declares K-07 with statement `s`; `\| **R-01** **R-02** \| s \|` declares R-01 only; `\| **K-07**x \| s \|` and `\| **K-07**, note \| s \|` declare nothing; the retired forms tolerate decoration the same way; heading declarations are unchanged. (R-32, C-01, E-44) |
| **T-02** | `R-7`, `R-07`, `R-007` in a spec are one ID reported as `R-07`; `I-5` is reported as `I-005`. (I-011, K-04) |
| **T-03** | A token with 4 digits (`R-1234`) and tokens adjacent to alphanumerics (`XR-07`, `R-07a`) are not IDs. (K-04, C-01) |
| **T-04** | Strikethrough declarations yield `retired=True`; a later plain declaration of the same ID exits `3`. (R-02, E-03) |
| **T-05** | IDs inside fenced code blocks in `SPEC.md` are ignored, for both ```` ``` ```` and `~~~` fences, with and without an info string, and for an unclosed fence running to end of file; a backtick fence opened with an info string is closed by a bare backtick line, is not closed by a tilde line, and a candidate closing line carrying an info string does not close it. (E-04, C-01) |
| **T-06** | Duplicate declaration exits `3` and names both lines. (E-02) |
| **T-55** | A bold ID in a second cell, a heading with the ID after other tokens, a separator row, and a row with `\|` and a backtick-quoted pipe in a cell are parsed per C-01: only first-cell/first-token forms declare; the statement is the second cell with escapes intact. (E-31, C-01) |
| **T-72** | A spec with `### C-01 Widget`, a fenced block containing `\| **R-99** \| x \|` and a `# comment` line, a prose paragraph, a `#### note` sub-section holding a declaring `\| **E-09** \| … \|` row, a `---`, then `### C-02 …`: C-01's `text` is `Widget`, a newline, and every line through the `---` with its indentation and trailing spaces intact (the `#### note` section included, C-02's heading excluded); C-01's `title` is `Widget`; R-99 is not declared (E-04) and E-09 is (E-47). A body that takes the statement over K-14 yields a `text` of whole lines $\leq$ 16,384 bytes plus the marker line and one Note naming the ID. A heading with an empty body, and a declaring heading on the last line of the file, each yield `text == title`; `### C-03` with no title and a body yields `text` equal to the body (F-305). The same spec saved with CRLF line endings yields a byte-identical `SpecIndex` and `speccheck.json`; a whitespace-only line after the body's last text line is dropped and one inside the body is kept (F-301). A `    # four-space` line inside an indented block neither ends a body nor declares; a bare `###` ends a body; `### C-05 Title ###` has title `Title`; `###C-06 x` declares nothing (F-304). Property, for every ID of `fixtures/target/SPEC.md` and `fixtures/target-swift/SPEC.md`: `title` equals the second cell (table) or the heading remainder after the ID token (heading), whitespace-collapsed, as computed independently by the test; `text == title` for every table-declared ID and every heading-declared ID with an empty body; `text.startswith(title + "\n")` otherwise (F-302). (R-33, C-01, C-02, K-14, E-46, E-47) |
| **T-07** | A spec with no in-scope IDs exits `3` and writes no files. (E-01, I-001) |

### 9.2 Citation and attribution (C-03)

| ID | Test |
| -- | ---- |
| **T-08** | Source citations are recorded per (file, line) for tokens in code, comments, and strings alike. (R-03) |
| **T-09** | Python test citations inside `def test_*` and `class Test*` methods are attributed to the enclosing case with the correct `classname`, `start`, `end`. (R-04) |
| **T-10** | A citation in a module docstring or helper is attributed to the file-level case and reported with name `(file)`. (E-13) |
| **T-11** | An unparseable `.py` test file falls back to one file-level case and produces a Note. (E-12) |
| **T-12** | A non-Python test file (`.go`, `.ts`) gets file-level attribution. (R-04, O-2) |
| **T-13** | Excluded directories (K-03), oversized / non-UTF-8 files (K-02), binary files, and symlinks are skipped or decoded exactly as specified: oversized and non-UTF-8 produce Notes, binary produces none, symlinks produce one Note per run and are never followed (a symlink cycle terminates). (E-10, E-11, E-29, E-30) |
| **T-56** | `test_*` and `testFoo` methods of a `*TestCase` subclass, `testFoo` methods of a `Test*` class, and `async def test_*` functions are delimited with correct spans; a module-level `testFoo` (no underscore) is not a test case; a `test*` method of an unrecognized class is not, its citations are file-level, and the file gets an `undelimited tests` Note. (E-28, C-03) |
| **T-57** | A line containing `speccheck:ignore` yields no citations but still counts toward its case's span; a file with `speccheck:ignore-file` on line 2 yields no citations and no test cases; a marker on line 4 has no file-level effect; markers inside `SPEC.md` change nothing; the Note counts ignored files. (R-27, E-33) |
| **T-14** | Several citations of one ID in one case yield one edge with all lines listed. (E-22) |
| **T-65** | Swift Testing attribution: a `.swift` file with a doc-commented `@Test func` at file scope, a `@Suite struct Outer` holding a `@Test("named") func`, a `@Test(arguments: [...])` attribute spread over two lines, a nested `@Suite struct Inner` with a `@Test func`, a plain helper, and a `func testHelper()` with no `@Test`, plus a `@testable import`: the cases are named by identifier, their classnames are `<Module>`, `<Module>.Outer`, `<Module>.Outer.Inner`, each span starts on the first doc-comment line above its attribute and ends on the function's closing brace; a citation on a doc-comment line, on an attribute continuation line and on a body line is attributed to that case; the helper's citation is file-level; the Note lists `Outer.testHelper` (E-43); `@testable` is not `@Test`. MODULE is the first path component under the `--tests` root, or the root's own name for a file directly under it. (R-31, C-03, E-43) |
| **T-66** | XCTest attribution: `final class LegacyTests: XCTestCase` with `func testAddition()` and `func helper()`, a class nested inside it with a `test*` method, and a `class Plain` (no `XCTestCase`) with `func testFoo()`: `testAddition` is a case named `testAddition` with classname `<Module>.LegacyTests` and a span from its doc comment to its closing brace; the nested and the `Plain` methods are undelimited with one Note naming `LegacyTests.Nested.testNested, Plain.testFoo`; `helper` produces no Note. (R-31, C-03, E-43) |
| **T-67** | A `.swift` file with an unclosed `{` is one file-level case with Note `parse fallback: <path>`; a file with a stray `}` likewise; a file whose only extra braces are inside `"{"`, `"""…}…"""` and `// }` delimits its cases correctly. (E-42, C-03) |
| **T-85** | DECLARED/INCIDENTAL classification (C-14): a citation on the case's own docstring line is DECLARED; a citation on a whole-line `#` comment inside the span is DECLARED; a citation inside a string literal, and one on a code line with a trailing comment (`x = 1  # R-02`), are INCIDENTAL; a citation attributed to the file-level fallback case is INCIDENTAL with no Note (E-56); a multi-line docstring whose citation is on its second line is DECLARED; the Swift adapter's doc-comment-line recognition (`///`, `/** … */`) classifies an equivalent Swift example the same way the Python path does. `declared` is present under `--judge none` and does not change with `--judge`. (R-39, C-03, C-14, E-56, I-014) |

### 9.3 Results mapping (C-04)

| ID | Test |
| -- | ---- |
| **T-15** | `<testsuites>` and bare `<testsuite>` roots both parse; `failure`/`error`/`skipped` children map to the correct outcome. (R-05) |
| **T-16** | Classname join accepts both `tests.test_core` and `test_core` forms for `tests/test_core.py`, and rejects `unit_test_core` for `test_core`. (C-04) |
| **T-58** | With `tests/a/test_core.py` and `tests/b/test_core.py`, a result with classname `tests.a.test_core` joins `a` only; a result with classname `test_core` is unattributed with a Note naming both candidates. (E-27, C-04) |
| **T-52** | `test_x[3-True]` and `test_x[0-False]` both join `test_x`; `results` lists both with `param`; the case `outcome` is the worst of them; a name with no `[` is unchanged; everything from the first `[` is removed: `test_y[a][b]` → `test_y` and `test_x[list[int]]` → `test_x` with `param` `list[int]`; a result with empty `classname` joins the unique case with its `join_name` and is unattributed when two exist. (E-24, C-04, F-105) |
| **T-68** | A SwiftPM `junit-swift-testing.xml` with `freeFunction()` under `ProbeTests`, `named()`, `parameterized(x:)`, `twoArgs(a:b:)` and a `<skipped>` `disabledOne()` under `ProbeTests.Outer`, and `nested()` under `ProbeTests.Outer.Inner` joins each to its C-03 case with `param` null and the outcomes `passed` / `skipped`; an XCTest `<testcase classname="ProbeTests.LegacyTests" name="testAddition">` joins the XCTest case; results for overloads `f(a:)` and `f(b:)` are unattributed with one Note naming both candidates (E-45); `test_x[f(1)]` still strips from the first `[` and keeps `param` `f(1)`. (R-31, C-04, E-45) |
| **T-17** | Duplicate `(classname, name)` collapses to the worst outcome in the order error > failed > skipped > passed. (E-06) |
| **T-18** | Results for unknown cases are listed as unattributed and change no status. (E-07) |
| **T-19** | Malformed XML and a `<testcase>` without `name` each exit `3`. (E-05) |

### 9.4 Status algorithm and metrics (C-05, C-07)

| ID | Test |
| -- | ---- |
| **T-20** | One fixture per deterministic status — `UNCITED`, `UNTESTED`, `UNVERIFIED`, `FAILING`, `SKIPPED`, `PASSING`, `RETIRED` — each asserting exactly that status; the `UNCITED` fixture has empty `--src` and `--tests` and exits `1`. (R-06, E-19) |
| **T-21** | An ID with one failed and three passed citing tests is `FAILING`; with all citing tests skipped is `SKIPPED`; with some skipped and some passed is `PASSING`. (C-05 step 4) |
| **T-22** | Citing cases absent from results are listed under `unrun` and do not affect the status. (E-08) |
| **T-23** | Dangling and stale citations are listed with file and line; strikethrough in code does not retire anything. (R-07, R-08, E-20) |
| **T-24** | `conformance`, per-family ratios, and counts match hand-computed values on the golden fixture; a family with zero in-scope IDs reports `null`/`n/a`, not `0.0`, and nothing raises. (R-09, I-008) |
| **T-25** | Retired IDs are excluded from every denominator and still appear in `ids` exactly once. (R-02, I-003) |
| **T-53** | A T id cited only in a source file is `UNCITED`; a T id cited by a passing test is `PASSING`; T ids are counted in `in_scope`, `conformance`, and `by_family.T`. (R-25, E-25) |
| **T-77** | `| **T-01** *(recorded)* | s |` declares T-01 with `recorded == True`, `title == "s"`; `### T-02 *(recorded)* Title` declares T-02 recorded with title `Title`; `| **T-03** *(Recorded)* |`, `| **T-04** (recorded) |` and `| **T-05** **[port]** *(recorded)* |` declare their ids not recorded; `| **R-01** *(recorded)* |` declares R-01 not recorded with the E-50 Note. With `--judge mock` and a call-counting stub under `--judge llm`: a recorded T id cited by a passing test with an assertion-free body is `PASSING` and its edge is never sent to the judge (`verdict` null, not counted in `unknown_rate`'s denominator or the C-11 total), while the same test cited by a non-recorded T id yields `WEAKLY_PASSING`; a recorded T id with a failing test is `FAILING`, with a skipped one `SKIPPED`, with no citing test `UNCITED` (E-51); with two recorded `PASSING` ids, one judged `PASSING` id and one `WEAKLY_PASSING` id, `judge_strength` is `1/2` (recorded ids outside the population) while `conformance` counts all three passing (F-405); the JSON carries `"recorded": true` after `"family"` and the Markdown ID cell reads `T-01 (recorded)` and a retired recorded id's `~~T-03~~ (recorded)`; `schema_version` is the C-07 value. (R-35, C-01, C-02, C-05, C-07, C-08, I-010, E-50, E-51) |

### 9.5 Judge contract (C-06)

| ID | Test |
| -- | ---- |
| **T-26** | Mock judge returns `ASSERTS` with one evidence line per assertion token, and `EXECUTES_ONLY` with no evidence when none is present, including for an empty test body. (R-22, E-17) |
| **T-69** | The mock judge returns `ASSERTS` with the line as evidence for a Swift span containing `#expect(`, `#require(`, `XCTAssertEqual(`, `XCTFail(` or `Issue.record(` (one sub-test each), and `EXECUTES_ONLY` for a Swift body that only calls code (`_ = add(1, 2)`). (R-22, C-06) |
| **T-27** | A `PASSING` ID whose only passed edges are `EXECUTES_ONLY` becomes `WEAKLY_PASSING`; with any `ASSERTS` edge it stays `PASSING` and passes `--strict`; with only `UNKNOWN` it stays `PASSING`. (C-05 step 5, R-11, E-26) |
| **T-28** | Disabling the judge changes no status except `WEAKLY_PASSING` → `PASSING` (property test over random fixtures). (I-004) |
| **T-29** | A stub provider returning `ASSERTS` without evidence, evidence outside the span, or evidence in another file is coerced to `UNKNOWN` with `coerced: true` and rationale `judge: ungrounded`. (E-16, I-005) |
| **T-30** | Non-JSON, missing `verdict`, an unknown verdict string, a raised exception, and a timeout each yield `UNKNOWN` with the specified rationale. (E-14, E-15) |
| **T-31** | The judge is called exactly once per eligible edge and never for `FAILING`/`SKIPPED`/`UNVERIFIED`/`UNTESTED`/`UNCITED` IDs or for skipped/failed test outcomes (call-counting stub). (I-010) |
| **T-32** | Rationale over 280 chars is truncated to 277 + `...`; newlines become spaces. (K-07) |
| **T-33** | LLM provider sends exactly one `POST` per edge whose body is byte-for-byte the C-06 shape (`model`, `temperature: 0`, `max_tokens: 4000`, system message equal to the C-10 text, user message equal to the request JSON with line-numbered `source`), with the bearer header, honors the timeout, never retries, and issues at most `--judge-concurrency` requests at once while output order stays fixed (recorded HTTP stub with a concurrency counter); the URL, model, key and timeout are those of the C-09 variables. (K-05, K-06, R-26, C-09) |
| **T-54** | The provider reads `choices[0].message.content`, accepts a bare JSON object and one wrapped in a ```` ``` ````/```` ```json ```` fence, and treats a missing path, a non-200 status, or any other text as E-14/E-15; the report carries `judge_prompt_sha256` equal to the SHA-256 of `speccheck/judge_prompt.md`, and that file equals the C-10 text. (C-06, C-10, R-26) |
| **T-74** | Extends T-33: for a heading-declared ID with a body, the LLM request's user message carries `statement` equal to `SpecId.text` — title, newline, body with its fenced block and indentation, byte for byte — under the keys `{id, statement, related, declared, file, start, end, source}` (`declared` added in v1.14, C-15; `related` added in v1.16, R-38, D-28) and the system message that is the C-10 text; the C-10 file contains the any-clause rule added in v1.7 and `judge_prompt_sha256` is its SHA-256 (recorded HTTP stub). (R-33, C-06, C-15, C-10, R-26) |
| **T-75** | Clause grounding: a stub returning `ASSERTS` with a clause that is a verbatim excerpt of the statement differing only in line breaks and indentation is accepted and recorded with the collapsed excerpt; a 300-character excerpt is accepted and recorded cut to 280; a paraphrase, an 8-character fragment of a longer statement, a missing key, and `""` each yield `UNKNOWN`, `coerced: true`, `judge: unlocated clause`, for `ASSERTS` and for `EXECUTES_ONLY` alike; an `UNRELATED` with a clause is recorded with `""` and not coerced; `"clause": null` on an `UNRELATED` is `""` and not coerced, on an `ASSERTS` it is E-48; an `ASSERTS` whose clause is unlocated *and* whose evidence lies outside the span records `judge: unlocated clause` (rule order); a clause with a leading space that otherwise matches the statement's first words is LOCATED (K-15 trims); a statement of 9 characters is matched by itself and by nothing shorter; the mock judge's clause is the collapsed statement's first 280 characters on every edge of the golden fixture and equals `""` for an ID whose statement is `""`; the LLM request's system message equals the current C-10 text; the JSON verdict object's keys are `verdict, clause, evidence, rationale, coerced` in that order and `schema_version` is the C-07 value; report §8 shows the clause column with an em dash for `""`. (R-34, K-15, E-48, E-49, I-005, C-06, C-07, C-08, C-10, R-22) |
| **T-83** | For a judged edge, the C-06 request's user message now carries `related` — the whitespace-collapsed titles (each at most 160 characters) of the obligations the statement names and that name it, its own references first, at most eight in C-07 id order, a retired neighbour keeping its `(retired)` title (E-57), and the empty list when the id has no neighbour — a request-side field like `declared`: absent from `speccheck.json` and from the Markdown report and not inspected by any C-06 coercion rule or by C-08 (D-28); the C-10 system message contains the `related` rule. The triage `state` (C-17) carries the same `related` section (D-28b). (R-38, C-06, C-10, D-28, E-57) |

| **T-89** | Triage and the `N%` budget (v1.15): with `--judge llm --jev-pre-triage` over a stub fixture of 10 judge-eligible edges, a stub C-17 provider returning fixed confidences (one edge deliberately failing with HTTP 500) and a stub judge recording every edge it is asked about, `--judge-budget 30%` issues exactly $\lceil 0.30 \times 10 \rceil = 3$ edges — the three with the lowest $p(e)$, the failing edge first among them — in ascending-confidence order, and the other 7 are `UNKNOWN` with rationale `judge: budget` and `coerced: true`, with one Note reporting 7 and one reporting the single E-59 failure; `--judge-budget 100%` issues all 10; `--judge-budget 0%` issues none (judge call count 0) while still running the triage pass (10 C-17 requests, none of them in either report); the C-17 stub receives exactly one request per eligible edge, never more than `--judge-concurrency` at once, each carrying `state` equal to C-17's template for that edge — now including its `Related obligations:` section, the neighbourhood of that edge (D-28b, R-38, E-57) — and `questions.verdict.criteria` covering the four C-06 tokens, and none carrying `clause` or `evidence`; the same run under `--judge mock` (K-16 ignored) makes no C-17 request, needs no `SPECCHECK_JEV_API_KEY`, and leaves the golden reports byte-identical; with `--judge-budget 0` the pass reorders but changes no report content, and the D-30 Note is present; a stub that fails every C-17 call leaves `judge_available` and `unknown_rate` exactly as a triage-free run does. (K-16, K-12, C-17, I-015, E-35, E-59, I-006, D-30, D-32, D-28, R-38, E-57) |

### 9.6 Reports and determinism (C-07, C-08)

| ID | Test |
| -- | ---- |
| **T-34** | `speccheck.json` validates against the C-07 shape: key order, sort orders, rounding, no absolute paths, no timestamps; `by_family` has all six keys and `by_status` all seven in-scope statuses on every fixture including single-family ones; `judge_available` is `null` for `none`, `true` for `mock`, `true` for `llm` with zero eligible edges, `false` for `llm` when every call fails; every `tests[]` entry carries the `verdict` key, `null` on a `FAILING` ID, on a skipped-outcome edge of a `PASSING` ID, on every edge of a RECORDED ID (E-37, R-35), and everywhere under `--judge none`; `tests[].name` is `""` for a file-level case; a fixture producing five Notes emits them in code-point order in both reports; every ratio has exactly four decimal places and a hand-picked tie value (e.g. 1/8 = 0.125 at 3 places, 0.00005 at 4) rounds half-even to the quantized Decimal, not to `round()`'s binary result. (R-13, R-20, K-09, C-07, E-37, E-38) |
| **T-35** | `SPEC_CONFORMANCE_REPORT.md` has the nine C-08 sections in order, the header's judge parenthetical reading `(available)`/`(unavailable)` for mock/llm and absent for none, one per-ID row per declared ID, retired rows with exactly the ID cell struck through, an em dash in the verdict position for every unjudged case and `(file)` for every file-level case, and every `file:line` in it also present in the JSON. (R-12, I-003, E-37, Q-011) |
| **T-36** | Two runs on the golden fixture with `--judge mock` produce byte-identical reports and summary lines; the same holds after copying the fixture to a different absolute path, and with `--src .` and `--out` inside the source root (the previous run's reports and the spec itself produce no citations), and with a planted `.speccheck.json.deadbeef.tmp` and `.SPEC_CONFORMANCE_REPORT.md.deadbeef.tmp` under `--out` before the run (never scanned, deleted by the run). (R-16, I-002, E-23, E-34) |
| **T-37** | Every metric in the report is recomputable from the report's own evidence table plus the results file (the test recomputes them independently). (R-24) |
| **T-38** | Only the two report files are created; input trees are byte-identical before and after (hash comparison). (R-19, I-001) |
| **T-88** | `speccheck.json` under `--judge none` and `--judge mock` on the golden fixture (T-46) carries `declared_ratio` in `metrics` and `"declared"` on every `tests[]` entry, `schema_version` `"1.5"`; the Markdown report is byte-identical to its pre-v1.14 form apart from what T-86 changes; `declared_ratio` is recomputable by hand from the evidence table exactly as R-24 requires of every other metric. (C-07, C-16, R-39) |

### 9.7 CLI, exit codes, diagnostics, boundary (§5)

| ID | Test |
| -- | ---- |
| **T-39** | `exit_code` in JSON equals the process exit status for fixtures exercising `0`, `1` (non-strict), `1` (strict-only reasons: `UNVERIFIED`, `UNTESTED`, `UNCITED`, `SKIPPED`, `WEAKLY_PASSING`, dangling, stale), and `0` under `--strict` for a mixed `ASSERTS`/`EXECUTES_ONLY` ID. (R-14, R-15, I-009, E-26) |
| **T-40** | Missing `--spec`, bad `--judge`, bad `--verbose` value, any input or `--out` path outside `--root`, and missing judge env each exit `2` with the specified message; the API key value never appears in the message. (K-01, E-09, E-21, R-23, C-09) |
| **T-41** | Bare `--verbose` $\equiv$ `--verbose INFO`; INFO emits stage lines with counts and no statement text, file contents, or prompts; DEBUG emits `judge>`/`judge<` lines with the key redacted; stdout is the single summary line in all cases. (R-17, I-007) |
| **T-42** | With no `--verbose`, stderr is empty on exit 0/1 even when the run produced Notes; with `--verbose`, each Note appears once at `INFO`. (§5.3) |
| **T-43** | With `--judge none` and `--judge mock`, a socket-creation guard installed for the process lifetime is never triggered; `speccheck --self-check` passes from an installed wheel in an empty working directory, invokes the inner check in-process with exactly the §5.1 argument list (asserted via a recorded `Config`), prints `self-check: ok` although its inner check exits `1`, leaves no files behind, and writes nothing outside its temporary directory. (R-18, I-006, I-001, Q-003) |
| **T-60** | `speccheck/_selfcheck/` is byte-identical to `fixtures/target/` (recursive file-by-file comparison, `golden/` included); the test fails if either side changes without the other. (F-107, §10) |
| **T-44** | Summary line matches the §5.1 regex exactly, is pure ASCII, ends in a single `\n`, is emitted correctly under a C/POSIX locale and a `cp1252` stdout, carries all seven in-scope status counts including `skipped`, and its numbers equal the JSON metrics. (R-21, R-29, Q-005) |
| **T-59** | Under `--strict --judge llm` with a provider stub that fails every call — so that `judge_available` is `false` *and* `unknown_rate` is `1.0000 > max_unknown` — exit is `1`, `strict_judge_failure` is `"unavailable"` (not `"unknown_rate"`), and the summary line ends `judge=llm (unavailable)` (Q-004); with a stub yielding 3 `UNKNOWN` of 10 edges and `--max-unknown 0.2`, exit is `1` with `"unknown_rate"` and the numeric suffix; with `--max-unknown 0.3` exit is `0`; without `--strict` neither affects exit; with a fixture that has zero eligible edges, no request is sent, `unknown_rate` is `null`, and `--strict` exits `0`. (R-28, K-11, E-32, E-36) |
| **T-61** | With `--judge-budget 1`, `--judge-concurrency 2`, and a provider stub that sleeps 2 s per call over six edges, exactly the two requests issued before the deadline complete and are judged (in-flight requests are not cancelled); the remaining four are `UNKNOWN` with rationale `judge: budget` and `coerced: true`; the Note reports 4; `unknown_rate` includes them; with `--judge-budget 0` all six are judged. (K-12, E-35, Q-010) |
| **T-62** | With `--judge llm`, `--progress always`, a provider stub over six edges that sleeps 0.3 s per call, `--judge-concurrency 2`, and stderr captured: splitting the capture on `\r` yields only C-11 draw and erase sequences (after stripping each segment's trailing space padding, every draw matches the C-11 regex); the first draw reads `0/6 edges`, `0:00 elapsed`, `?:??`; `<done>` is non-decreasing across draws; a draw with `6/6` and a full 20-`#` bar exists and is the last draw; the capture ends with the erase sequence (`\r`, $W$ spaces, `\r`) and no `\x1b` byte appears anywhere; every draw is padded to the width of the widest draw so far; the number of `#` in each draw equals $\lfloor 20 d / 6 \rfloor$ for its `<done>`; with a stub that sleeps 2.5 s on a single edge, at least two draws show `0/1` with distinct `elapsed` values (the 1 s tick); with 32 edges answered instantly at `--judge-concurrency 32`, no more than 10 draws occur in any one second and the final draw still shows `32/32` (coalescing); with `--verbose INFO` added, no `INFO` line occurs between the first draw and the erase and the judge stage's `INFO` lines follow the erase; stdout is the single summary line and both report files are byte-identical to a `--progress never` run over the same stub. (R-30, C-11, K-13) |
| **T-63** | No progress bytes reach stderr when: stderr is not a TTY under `--progress auto` (the default in a subprocess capture); `--progress never`; `--verbose DEBUG` with `--progress always`; `--judge mock` or `--judge none` with `--progress always`. With `--progress auto` and a stderr whose `isatty()` returns `True`, the indicator is drawn. `--progress` with any other value exits `2`. Under `--progress always` a stub that raises `KeyboardInterrupt` mid-stage leaves the erase sequence as the last stderr bytes before the `interrupted` message (E-41). (R-30, E-39, E-40, K-01) |
| **T-64** | A `KeyboardInterrupt` raised by a provider stub mid-judge, and one injected between §3.1 steps 3 and 4 (after the JSON rename, before the Markdown rename), each exit `3` with stderr exactly `ERROR interrupted` (plus a traceback only under `--verbose DEBUG`), write nothing to stdout, leave no `.tmp` and no `speccheck.json` from this run under `--out`, and leave a previous run's reports intact; the JSON `exit_code` is never consulted (no report exists). With six edges, `--judge-concurrency 2`, and a stub that sleeps 5 s per call, an interrupt delivered to the main thread 0.5 s in ends the run in under 2 s with at most three requests ever started (in-flight requests abandoned, queued edges never issued). (E-41, K-01, I-001, K-05, §3.1) |
| **T-45** | Unwritable `--out` exits `3` with nothing written; a failure injected after the JSON rename and before the Markdown rename exits `3` with no `.tmp` left, no `speccheck.json`, and the previous run's `SPEC_CONFORMANCE_REPORT.md` intact (the one stale combination E-18 permits); leftover temporaries from an earlier run are deleted first; on success no `.tmp` remains and the two temporaries used carried the same 8-hex-digit nonce. (E-18, I-001, §3.1) |
| **T-50** | `speccheck --version` prints `speccheck <version>` where `<version>` is PEP 440 and equals `importlib.metadata.version("speccheck")`. (K-10) |
| **T-78** | PATHS parsing (D-23, C-03): `--src a.py,b.py,src --tests tests/unit,tests/core` produces byte-identical reports to `--src a.py --src b.py --src src --tests tests/unit --tests tests/core` (one list ≡ repeatable occurrences); `--src ,,,a,` and `--src a ,, b ,` each yield the list `[a, b]` with no Note and no error; a `--src` or `--tests` whose only occurrence is empty (e.g. `--src \" \"`) yields the empty list, and the `src`/`tests` directory default (when it exists) applies only when the flag is *entirely* absent; a directly-named file is scanned as that one file with every per-file filter applied (K-02/E-10 oversized, E-11 UTF-8 replace, E-13 file-level case, E-29 binary, E-33 ignore files/markers), and a directory element is descended per K-03; a file covered by both a direct element and an overlapping directory element is scanned and produces citations exactly once (I-012), its recorded `--src`/`--tests` root — and hence a directly-named `.swift` file's `MODULE` — being the first covering element in list order, and two inputs naming the same physical file set yield byte-identical reports (I-002); a segment that resolves inside `--root` but exists as neither directory nor file exits `2` with message `--<flag>: no such file or directory: <segment>` and writes no reports (E-52), while a segment outside `--root` exits `2` per E-09. (R-03, R-04, C-03, I-012, D-23, E-52, E-09; the scan-filter half cross-references T-13) |

| **T-90** | `--judge-budget 30%` without `--jev-pre-triage` exits `2` with a message naming both flags, before any request of either kind is issued (both stubs record zero calls) and with no report written; so does `--judge-budget 30% --jev-pre-triage --judge mock`; `--judge-budget 30` (the `SECONDS` form) under `--judge mock` is still accepted and ignored, exactly as before v1.15; `--judge-budget 30% --jev-pre-triage --judge llm` with `SPECCHECK_JEV_API_KEY` unset exits `2` naming that variable; no C-09 or C-17 key value appears in any of these messages, and `--judge-budget 101%` and `--judge-budget %` each exit `2` as bad values. (E-58, E-21, K-12, K-16, I-007) |

### 9.8 Golden fixture (end to end)

| ID | Test |
| -- | ---- |
| **T-46** | `fixtures/target/` — a small self-contained project with its own `SPEC.md` ($\geq$ 12 IDs across all six families, 2 retired, one heading-declared contract with a multi-clause body $\geq$ 2,048 bytes per T-76, a §12 decision table per T-79), `src/`, `tests/`, and a checked-in `junit.xml` — contains planted defects: one `UNCITED` R, one `UNTESTED` C, one `UNVERIFIED` E, one `FAILING` T, one `SKIPPED` K, one `EXECUTES_ONLY`-only test, one dangling citation, one stale citation, one unattributed result, one file-level citation. The golden reports live in `fixtures/target/golden/` (outside every scan root). `speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --root fixtures/target --out <fresh tmp>` produces files byte-identical to `golden/speccheck.json` and `golden/SPEC_CONFORMANCE_REPORT.md` and exits `1` (Q-003); `golden/` also holds the `impact` goldens of T-80. (all of §2) |
| **T-47** | Removing each planted defect in turn flips exactly the expected row and metric (one sub-test per defect). (R-06, R-24) |
| **T-71** | `fixtures/target-swift/` — a SwiftPM-shaped project with its own `SPEC.md` ($\geq$ 10 IDs across all six families, one carrying `**[port]**` decoration), `Sources/`, `Tests/<Module>/` holding one Swift Testing file (nested suite, parameterized test, disabled test, doc-comment citations) and one XCTest file, and a checked-in `junit.xml` that concatenates the `junit-swift-testing.xml` SwiftPM wrote and an XCTest `<testsuite>` in SwiftPM's shape — contains planted defects: one `UNCITED` R, one `UNTESTED` C, one `UNVERIFIED` file-level citation, one `FAILING` T, one `SKIPPED` K (the disabled test), one `EXECUTES_ONLY`-only test, one undelimited `test*` helper (E-43), one unattributed result. With `--judge mock` both reports are byte-identical to `fixtures/target-swift/golden/`, and the summary line is exactly the one recorded in that golden. (R-31, R-32, R-16, R-24) |
| **T-73** | Both golden fixtures regenerated for v1.7 and, as properties of the current output: each `golden/speccheck.json` carries the C-07 `schema_version` and a `title` per ID; in `fixtures/target/golden/speccheck.json` C-01's `statement` is its `title`, a newline, and `The error message MUST name the dividend.` while C-02's (empty body) equals its `title`; in each `golden/SPEC_CONFORMANCE_REPORT.md` the Statement cell of every §3 row equals that ID's JSON `title`, contains no newline, and no row contains the K-14 marker; the set of IDs in the Markdown equals the set in the JSON; `speccheck/_selfcheck/` is updated in step (T-60) and `--self-check` prints `self-check: ok`. The one-time v1.6 → v1.7 golden diff (only `schema_version` and the `title` keys added, heading-declared `statement`s changed, Markdown unchanged) is recorded in `SPEC_BUILD_REPORT.md`, not asserted by a test (F-302). (R-33, C-07, C-08, T-46, T-71) |
| **T-76** | `fixtures/target/SPEC.md` declares one heading-declared contract whose SECTION BODY is at least 2,048 bytes and consists of a fenced code block pinning a struct with field comments followed by at least five numbered rules; `tests/` holds four tests that each assert exactly one of those rules or the struct's shape and cite the contract, one test that calls the code and asserts nothing about it while citing the contract, and one test that asserts a different ID's behaviour while citing the contract; the six are attributed to their own cases and appear in `golden/judge_labels.json` as `ASSERTS` ×4, `EXECUTES_ONLY` ×1, `UNRELATED` ×1; the label file has at least 37 entries of which at least 8 are downgraded (`EXECUTES_ONLY` or `UNRELATED`) on an adjacent edge — a test that cites an id, runs its code, and asserts only a fact about an id that id's *statement* names (the v1.16 adjacent subset, T-84; C-10's vocabulary makes such a test `EXECUTES_ONLY`, since it does exercise the statement's code) — and at least 6 are edges of an ID whose statement exceeds 2,048 bytes; under `--judge mock` the contract is `PASSING` and the T-46 goldens are byte-identical. (T-46, T-49, T-84, R-34, R-38, D-28) |
| **T-86** | `fixtures/target/` gains one test whose own docstring names a different id (its DECLARED citation) but whose body also cites an existing id only as fixture/example data (mirroring the real `R-01`/`R-02`/`R-03` pattern `JUDGE_CROSSCHECK_REPORT.md` §2b found): under `--judge none`, `speccheck.json` records `declared: false` for that second edge and the fixture's `declared_ratio` reflects it; `SPEC_CONFORMANCE_REPORT.md` is unchanged by this test (C-16's Part C is JSON-only), and every other T-46 row stays byte-identical. (C-14, C-16, R-39, T-46) |

### 9.9 Self-application (recorded, not gating)

| ID | Test |
| -- | ---- |
| **T-48** *(recorded)* | `speccheck check --spec SPEC.md --src src --tests tests --results <this suite's junit.xml> --judge mock` on this repository reports every R/C/I/K/E/T ID in this document as `PASSING`. Recorded in `SPEC_BUILD_REPORT.md`; it is evidence *for* the build, not the proof of it — the proof is §9.1–§9.8. (R-24) |

### 9.10 Performance (recorded)

| ID | Test |
| -- | ---- |
| **T-51** *(recorded)* | A benchmark script (`tools/bench.py`, not collected by pytest) runs `check --judge mock` on the golden fixture and on the generated 10,000-file tree five times each and prints the median wall-clock; the medians, the reference-machine description, and the pass/fail against K-08 are recorded in `SPEC_BUILD_REPORT.md`. Not run in CI. (K-08) |

### 9.11 LLM judge evaluation (opt-in, `--judge llm`, not run in CI)

| ID | Test |
| -- | ---- |
| **T-49** *(recorded)* | On the golden fixture's judged edges (each hand-labeled `ASSERTS`/`EXECUTES_ONLY`/`UNRELATED`), the LLM judge's non-`UNKNOWN` verdicts agree with labels at $\geq$ 0.90 accuracy and `unknown_rate` $\leq$ 0.10 in **each** of three independent runs (no pooling; one failing run fails T-49); all three per-run figures are recorded with model name, date, and `judge_prompt_sha256`. The labels live in `fixtures/target/golden/judge_labels.json`, a JSON object mapping `"<ID> <file>::<name>"` (the judged edge) to its label, with at least 20 entries of which at least 6 are edges of a statement over 2,048 bytes (T-76), so that a judge which grades a body by its gist fails the run while one that locates the clause passes; the runner is `tools/eval_judge.py` (not collected by pytest), which runs the check three times and scores each run against the labels (F-210). A run counts toward T-49 only if its recorded `judge_prompt_sha256` equals the SHA-256 of the current C-10 text; a change to C-10, or to C-01's statement rule, therefore voids the recorded runs and requires three fresh ones, and the labels are re-read against the current statements before those runs (F-303). (R-10, R-26) |
| **T-87** *(recorded)* | Re-run the three real edges named in `PROPOSAL_v1.15_declared_vs_incidental_citations.md`'s evidence (`R-03`/`test_fenced_code_blocks_are_ignored`, `R-03`/`test_row_and_heading_grammar_edge_cases`, `R-02`/`test_judge_called_once_per_eligible_edge_only`, all recorded `ASSERTS` by `gpt-4o-mini` under the pre-v1.14 `C-10` text and `UNRELATED` by an independent second model) under the v1.14 `C-10` text with the same model, and record the three verdicts and `judge_prompt_sha256` in `SPEC_BUILD_REPORT.md`. Not gating: the claim this proposal makes is falsifiable, and this is the test of it — the honest possible outcomes are "moved on all three," "on some," or "on none," and D-26 is revisited if the answer is the last (§3 of that proposal). (R-39, C-15, D-26) |

| **T-91** *(recorded)* | The calibration measurement of `PROPOSAL_v1.16_jev_pre_triage.md` §1 re-run against this repository's own current `SPEC.md`/`src`/`tests`: a `check --judge llm --strict` run, its committed verdicts (recorded `UNKNOWN` excluded) bucketed by each edge's C-17 $p(e)$ against the C-17 model's own `answers.verdict.choice`, with the bucket sizes, the per-bucket agreement, and the C-17 model name, date and `judge_prompt_sha256` recorded in `SPEC_BUILD_REPORT.md`. Passes — non-gating, like T-49 and T-87 — when the buckets are monotonically non-increasing; a failure is a lead to re-examine D-30 and D-32, not a build break. The suite cites this id by a presence check that the recorded bucket table exists and has at least three rows. (K-16, C-17, D-32) |
| **T-84** *(recorded)* | Part A's evidence (D-28b): the golden fixture's adjacent subset — the judged edges that cite an id but assert only a fact about an id that id's *statement* names — is measured to be not all `EXECUTES_ONLY`/`UNRELATED` (which would leave the neighbourhood change a no-op on this fixture); `judge_labels.json` holds at least 37 entries of which at least 8 are downgraded (`EXECUTES_ONLY` or `UNRELATED`) on an adjacent edge, mirroring T-76's extension, and the measured downgrades are recorded with `model`, `date` and `judge_prompt_sha256` in `SPEC_BUILD_REPORT.md`. Not gating: the honest outcomes are "moved", "on some", or "on none", and if the fixture's adjacent subset is all `EXE`/`UNREL` the fixture is grown, not the claim (T-49, T-87). (R-38, C-10, D-28, T-76, T-49) |

### 9.12 Edges and impact (C-12, C-13; v1.13)

| ID | Test |
| -- | ---- |
| **T-79** | Edge and decision extraction on the golden fixture, whose `SPEC.md` gains a §12 decision table (header cells in an order other than the template's, so the *Affects* column is found by name) with at least three `D-nn` rows — one whose *Affects* cell names two declared ids, one naming an undeclared id, one naming the retired C-03 — plus one `D-nn` row outside that table and one bold `**D-09**` row inside it (both declare nothing): the regenerated `golden/speccheck.json` carries the C-07 `schema_version` and the `decisions` and `edges` arrays exactly as pinned; `ids`, every status, every metric, `dangling`, `stale`, `notes` other than the new C-12 Notes, and `SPEC_CONFORMANCE_REPORT.md` are byte-identical to their v1.12 values (T-73 property, extended); an obligation whose statement names an undeclared id yields the Note `edge to undeclared id: <X> -> <Y>` and no edge; a T naming a T is `depends_on`; an obligation naming its T and that T naming the obligation yield one `verifies` edge with the T as `src`; the *Affects* cell naming C-03 yields an edge with `retired: true` (E-55) and a `decisions[].affects` entry; `D-8` is reported as `D-08`; a spec whose decision table declares `D-01` twice exits `3` naming both lines (E-02); a spec with no decision table has `decisions: []`; a statement's self-reference and a repeated token add nothing; edges are in C-12 order on every fixture including one whose ids are declared out of order. (R-36, C-01 (c), C-02, C-07, C-12, E-02, E-55) |
| **T-80** | `speccheck impact --spec SPEC.md --changed K-02 --src src --tests tests --root fixtures/target --out <fresh tmp>` produces `impact.json` and `IMPACT_REPORT.md` byte-identical to `golden/impact.json` and `golden/IMPACT_REPORT.md`, exits `0`, and prints exactly one stdout line matching the C-13 regex whose five numbers equal the JSON's list lengths; the same command with `--depth 0` lists more rows in `impact`, its rows of depth $\leq$ 1 are the default run's rows in the same order with the same `via` (I-013), and the depth-cap Note is present in the default run and absent under `--depth 0`; two runs are byte-identical, and so is a run from a copy of the fixture at another absolute path (I-002); after a prior `check` into the same `--out`, an `impact` run leaves `speccheck.json` and `SPEC_CONFORMANCE_REPORT.md` byte-identical and writes only its two files, and `check` after `impact` leaves the two `impact` files untouched (I-001); `--changed D-01` reaches exactly D-01's *Affects* ids at depth 1 via `affects` edges; `--changed T-05` lists T-05 in re-verify with `verifies: []` and impacts none of the ids T-05 verifies; `--changed K-2` is accepted as `K-02` (I-011); without `--src` §4 reads `Not scanned.` and `recite` is `[]`; without `--tests` `test_cases` is `[]`; the retired C-03 in `--changed` is accepted and its rows are struck through (E-55); `--self-check` is unchanged and still compares only the two `check` goldens. (R-37, C-13, I-001, I-002, I-011, I-013, K-09, E-55) |
| **T-81** | `--against`: a copy of the fixture spec with one statement reworded, one id newly retired, one id removed, one id added, and one decision's *Affects* cell extended yields a changed set of exactly those five with the C-13 reasons, in C-12 id order, the removed id carrying its line in the `--against` file and appearing in no `impact` row; a byte-identical copy yields an empty changed set, every section `None.`, exit `0`, and the summary `speccheck impact: 0 changed, 0 impacted (depth 1), 0 to re-verify, 0 citations, 0 test cases`; an `--against` file with a duplicate declaration exits `3` with the E-02 message prefixed `--against: `; `--changed R-99`, `--changed X-01`, and `--changed ,` each exit `2` with the E-53 (or `--changed: no ids`) message; `--changed` with `--against`, neither, `--results junit.xml`, and `--judge mock` each exit `2` with the E-54 message; `--depth 1000`, `--depth -1`, `--depth x` exit `2`; in every exit-2/3 case no file is written under `--out` (I-001). (C-13, E-09, E-53, E-54, K-01, I-001) |
| **T-82** *(recorded)* | The backtest `tools/impact_backtest.py` (D-24; not collected by pytest; needs `git` and this repository's history) on two ranges of `main` — spec `d170433^`..`c0a770a` built by `2a25569`..`2635298`, and spec `2635298`..`c1e3d87` built by `330dd4e`..`dfea1a6` — runs `impact --against` on the two spec versions and compares the predicted set at each depth cutoff $d \in \{1, 2, 3, \infty\}$ with the ids whose citations (per the built tree's `speccheck.json`) lie in the build range's touched hunks; recall and precision per cutoff, the miss list, and the chosen `--depth` default are recorded in `SPEC_BUILD_REPORT.md`; the bar is recall $\geq$ 0.80 at the chosen depth on both ranges, or every miss explained as an edge the prose does not and should not carry. The suite cites this id by a presence check that the script exists and `--help` exits `0`. (R-37, C-13, D-24) |

### 9.13 `explain` (C-18; v1.17)

| ID | Test |
| -- | ---- |
| **T-92** | `speccheck explain R-01 --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --root .` on a copy of the fixture prints exactly the C-18 trace for R-01 — `ID R-01`, `status: PASSING (step 4: every citing test case passed)`, `statement:`, its `sources:` line, its `tests:` case with outcome and `[ASSERTS]`, and the `impact (1):` section — exits `0`, writes nothing at all (the fixture copy is byte-identical before and after, T-38's rule; `explain` has no `--out`, D-33), and a second identical run is byte-identical; the status shown equals R-01's status in `golden/speccheck.json` from the same inputs (I-016, I-002 extended to this surface). (R-40, C-18, I-016) |
| **T-93** | `explain R-09 …` (an id `fixtures/target` does not declare) exits `2` with the E-60 message and writes no trace; `explain R-04` (the fixture's retired id) renders `ID R-04 (RETIRED)` with `status: RETIRED (retired: struck through in the specification)` and exits `0`; `explain C-02` (declared, cited in `src/` only) renders its status reason with an empty `tests:` block and exits `0`. (R-40, C-18, E-60) |
| **T-94** *(recorded)* | Under `--judge llm`, `explain <a judge-eligible id>` renders the C-06 verdict with its `clause:` and `rationale:` lines; under `--judge none` the same id's edge lines read `not judged`; in both, the id's status in the trace equals its status in `speccheck.json` from the same inputs (I-016). Recorded in `SPEC_BUILD_REPORT.md`; not gating, like T-49 — it exercises a live model. (R-40, C-18, E-61) |

### 9.14 CLI help (C-19; v1.18)

| ID | Test |
| -- | ---- |
| **T-95** | For every flag whose accepted set is finite (`--judge`, `--progress`, `--verbose`, `--max-unknown`, `--judge-concurrency`, `--judge-budget`, `--depth`), the value tokens and range text named in its `--help` entry equal those named in the message the same flag's own usage error prints (e.g. `check --judge bogus` → `expected none, mock, or llm`, exit `2`), and every token the help names is accepted: a run over the §9.8 fixture carrying that token exits other than `2`, while the control token `bogus` exits `2`. (R-41, C-19) |
| **T-96** | Every argument definition of the four parsers except `-h` carries a non-empty help string; each flag's rendered entry names a metavar from C-19's vocabulary and, where the flag has a default, that default; and each of the four `--help` screens, run from an empty temporary directory with the R-18 socket guard installed, exits `0`, writes a non-empty screen to stdout and nothing to stderr (I-017). (R-41, C-19, I-017) |
| **T-97** | With `COLUMNS=80` fixed, the four `--help` screens render byte-stable text compared against checked-in goldens under `tests/data/help/` (not §9.8 report goldens: C-19's wording is not normative, D-38), so a dropped value token, a dropped default, a new flag without help, or an unintended rewording is a visible diff. (R-41, C-19, D-39) |
| **T-98** | The `environment:` block names exactly the variables the kernel reads and no others: scanning `src/speccheck/*.py` for string literals matching `SPECCHECK_[A-Z_]+` yields the same set the rendered `check --help` block lists (8 — `SPECCHECK_JUDGE_URL`/`_MODEL`/`_API_KEY`/`_TIMEOUT`, `SPECCHECK_JEV_URL`/`_MODEL`/`_API_KEY`/`_TIMEOUT`), each entry naming its read condition and requiredness, with `COLUMNS` documented beside them (D-41); a variable read by the kernel but absent from the block, or named in the block but read by no code, fails the test; and no `_API_KEY` value ever appears in any help screen or usage-error message (R-23, I-007). (R-41, C-19) |

---

## 10. Dependencies and environment

- **Runtime:** Python 3.12; `uv` for environment and lockfile. Install: `uv sync --extra dev`; with the model judge: `uv sync --extra dev --extra llm`.
- **Kernel dependencies:** none beyond the standard library (`re`, `ast`, `xml.etree.ElementTree`, `json`, `argparse`, `pathlib`, `logging`, `hashlib`).
- **Package data:** `speccheck/judge_prompt.md` (C-10) and `speccheck/_selfcheck/` (a byte-identical copy of `fixtures/target/` including its `golden/` directory, kept in sync by T-60; F-011, F-107), both included in the wheel.
- **Golden fixture layout:** `fixtures/target/{SPEC.md, src/, tests/, junit.xml, golden/speccheck.json, golden/SPEC_CONFORMANCE_REPORT.md, golden/impact.json, golden/IMPACT_REPORT.md}` (the last two since v1.13, T-80); `golden/` is never a scan root and is never written to by a run (Q-003).
- **`[llm]` extra:** `httpx` (HTTP client with per-request timeout). No provider SDK; the wire format is C-06. The C-17 triage pass uses the same client and the same extra.
- **`[dev]` extra:** `pytest`, `pytest-cov`, `hypothesis` (T-28), `ruff`.
- **Environment variables:** C-09 (only with `--judge llm`) and C-17 (only with `--jev-pre-triage` under `--judge llm`; v1.15). No configuration files are read.
- **Host prerequisites:** none. No network access is required except with `--judge llm`, and — when `--jev-pre-triage` is given — the C-17 triage pass that flag enables. The kernel never invokes `git` or any subprocess (D-24).
- **Help goldens (T-97, v1.18):** `tests/data/help/{speccheck,check,impact,explain}_help.txt` — the C-19 screens rendered at `COLUMNS=80`, checked in as test data (not a §9.8 report golden; D-39).
- **Tools (not collected by pytest, not part of the wheel):** `tools/bench.py` (T-51), `tools/eval_judge.py` (T-49), `tools/sync_selfcheck.py` (T-60), `tools/impact_backtest.py` (T-82; the only one that needs `git` and the repository history; D-24).
- **Commands:**

```bash
uv sync --extra dev
uv run python -m pytest tests -q --junitxml=junit.xml     # the §9 suite; junit.xml feeds T-48
uv run ruff check src tests
uv run speccheck --self-check
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock
uv run speccheck impact --spec SPEC.md --changed K-15 --src src --tests tests               # v1.13; or --against <prior SPEC.md>
uv run speccheck explain R-01 --spec SPEC.md --src src --tests tests --results junit.xml --judge mock   # v1.17; stdout only
```

- **Optional items:**
  - **O-1** LLM judge provider (`--judge llm`, `[llm]` extra). Specified fully in C-06/C-09; gated by flag and extra. The C-17 triage provider (`--jev-pre-triage`, `[llm]` extra, v1.15) is the same kind of item: fully specified in C-17/K-16, gated by flag and extra, and never the source of a status (I-015).
  - **O-2** Additional language adapters for test-case attribution (Go `func Test*`, JS/TS `test(`/`it(`). Not in v0.1; the fallback path is what v0.1 ships and tests (T-12). Swift joined the shipped adapters in v1.6 (R-31, C-03); Go and JS/TS remain optional.
  - **O-3** Any non-CLI surface (GUI, HTTP, editor plugin). Not in v0.1 and not designed for.

---

## 11. Traceability matrix (id → where realized)

Until the build exists, "where realized" names the component the §1/§4 design assigns; `spec-build` replaces it with the real module and the real test.

| Spec id | Where realized (component / module) | Verified by |
| ------- | ----------------------------------- | ----------- |
| R-01 | `extract.py` (declaration scan, UTF-8 replace) | T-01, T-05, T-46, T-72 |
| R-02 | `extract.py` (retired flag), `graph.py` (denominators) | T-04, T-25, T-46 |
| R-03 | `extract.py` (source scan, PATHS list parsing per C-03, C-03 exclusions, binary/symlink filters) | T-08, T-13, T-36, T-46, T-78 |
| R-04 | `attribute.py` (Python adapter, Swift adapter, fallback, C-03 exclusions), `cli.py` (PATHS list parsing) | T-09, T-10, T-11, T-12, T-36, T-56, T-46, T-65, T-66, T-67, T-78 |
| R-05 | `results.py` | T-15, T-16, T-52, T-58, T-46, T-68 |
| R-06 | `graph.py` (C-05 steps 1–4) | T-20, T-21, T-47, T-46 |
| R-07 | `graph.py` (dangling) | T-23, T-46 |
| R-08 | `graph.py` (stale) | T-23, T-46 |
| R-09 | `graph.py` (metrics) | T-24, T-46 |
| R-10 | `judge.py`, `judge_mock.py`, `judge_llm.py` (passed-outcome edges only) | T-26, T-31, T-33, T-49, T-46 |
| R-11 | `graph.py` (C-05 step 5) | T-27, T-28, T-46 |
| R-12 | `report.py` (Markdown) | T-35, T-46 |
| R-13 | `report.py` (JSON) | T-34, T-46 |
| R-14 | `cli.py` (exit mapping) | T-39, T-46 |
| R-15 | `cli.py` (`--strict`, status-only) | T-39, T-27, T-46 |
| R-16 | all kernel modules (sorted, no volatile fields) | T-36 |
| R-17 | `cli.py` (logging setup, level `ERROR` default) | T-41, T-42 |
| R-18 | `cli.py` (`--self-check`, pinned in-process invocation), `speccheck/_selfcheck/`, `judge_llm.py` import isolation | T-43, T-60 |
| R-19 | `report.py` (only writer, temp-and-rename), `cli.py` | T-38, T-43, T-45 |
| R-20 | `extract.py`, `report.py` (path normalization) | T-34, T-36 |
| R-21 | `cli.py` (summary line) | T-44, T-59 |
| R-22 | `judge_mock.py` (Python and Swift assertion tokens; prefix clause) | T-26, T-69, T-75 |
| R-23 | `judge_llm.py`, `cli.py` (env validation, redaction) | T-40, T-41 |
| R-24 | `report.py` (evidence table completeness) | T-37, T-48 |
| R-25 | `graph.py` (C-05 step 2b) | T-53 |
| R-26 | `judge_llm.py` (body, response path, prompt hash), `speccheck/judge_prompt.md` | T-33, T-54, T-74 |
| R-27 | `extract.py` (ignore markers) | T-57 |
| R-28 | `cli.py` (`--strict` judge gate), `report.py` (`strict_judge_failure`) | T-59 |
| R-29 | `cli.py` (summary line encoding) | T-44 |
| R-30 | `cli.py` (`--progress` resolution, TTY test), `judge.py` (progress callback in `run_judge`) | T-62, T-63 |
| R-31 | `attribute.py` (Swift adapter: type/func lines, attribute block, brace spans, MODULE), `results.py` (signature strip), `judge_mock.py` (Swift tokens) | T-65, T-66, T-67, T-68, T-69, T-71 |
| R-32 | `extract.py` (first-cell prefix rule) | T-70, T-71 |
| R-33 | `extract.py` (heading title, SECTION BODY, K-14 cap and Note), `report.py` (`title` key; Markdown renders `title`), `judge_llm.py` (statement passthrough) | T-72, T-73, T-74 |
| R-34 | `judge.py` (clause validation, K-15 matcher, E-48/E-49 coercion), `judge_llm.py` (`clause` in the reply), `judge_mock.py` (prefix clause), `report.py` (`clause` key, §8 column), `speccheck/judge_prompt.md` | T-75, T-76, T-49 |
| R-35 | `extract.py` (RECORDED marker, `SpecId.recorded`), `graph.py` (step 5 skip, eligible edges), `report.py` (`recorded` key, ID cell) | T-77 |
| R-36 | `extract.py` (decision-table scan, `Decision`, `Edge`, C-12 edge builder and Notes), `report.py` (`decisions`, `edges`) | T-79 |
| R-37 | `impact.py` (changed set, `--against` diff, walk, re-verify, re-cite), `cli.py` (`impact` subcommand), `report.py` (C-13 renderers) | T-80, T-81, T-82 |
| R-38 | `judge_llm.py` (builds the `related` neighbourhood into the C-06 request: the statement's own references first, then those that name it, at most eight, each a 160-char whitespace-collapsed title, a retired neighbour tagged `(retired)` (E-57), the empty list when none), `jev.py` (the D-28b `Related obligations:` section in the C-17 `state` template), `speccheck/judge_prompt.md` (the `related` field and its rule, C-10) — a request-side field: not in `speccheck.json`, C-16, or C-08 | T-83, T-84 |
| R-39 | `attribute.py` (docstring-span and whole-line-comment detection, Python and Swift), `report.py` (`declared`, `declared_ratio`) | T-85, T-86, T-88 |
| R-40 | `cli.py` (the `explain` subparser, `ExplainConfig`, the render wiring), `explain.py` (the C-18 trace renderer) | T-92, T-93, T-94 |
| R-41 | `cli.py` (the help strings, metavars and epilogs of the four parsers) | T-95, T-96, T-97, T-98 |
| C-01 | `extract.py` (`ID_RE`, fence tracker, row/heading parsers incl. first-cell decoration, RECORDED marker and section bodies, decision rows (c), ignore markers) | T-01, T-02, T-03, T-04, T-05, T-55, T-57, T-70, T-72, T-77, T-79 |
| C-02 | `extract.py` (`SpecId` with `title`, `text` and `recorded`, `Decision`, `Edge`, `SpecIndex`) | T-01, T-06, T-72, T-77, T-79 |
| C-03 | `attribute.py` (`TestCase`, `Citation` incl. `declared`, `test*` methods, Swift adapter), `extract.py` (exclusions incl. temporaries, binary, symlinks), `cli.py` (PATHS list parsing; D-23) | T-09, T-10, T-13, T-14, T-36, T-56, T-65, T-66, T-67, T-78, T-85 |
| C-04 | `results.py` (two-step `join_name`) | T-15, T-16, T-17, T-18, T-19, T-52, T-58, T-68 |
| C-05 | `graph.py` (`IdStatus`, `compute_status`, recorded skip in step 5) | T-20, T-21, T-27, T-53, T-77 |
| C-06 | `judge.py` (`JudgeRequest` with numbered `source`, full statement, `declared`, and `related` (R-38), `Verdict` with `clause`, validation incl. K-15), providers; `judge_mock.py` tokens | T-26, T-29, T-30, T-32, T-33, T-54, T-69, T-74, T-75, T-83, T-87 |
| C-07 | `report.py` (`to_json`; `title`; `recorded`; `clause`; `decisions`; `edges`; `declared`; `declared_ratio`; Decimal quantization; `verdict: null`; Note order) | T-34, T-37, T-59, T-73, T-75, T-77, T-79, T-86, T-88 |
| C-08 | `report.py` (`to_markdown`; Statement cell from `title`; `(recorded)` ID cell; §8 Clause column; em dash and `(file)` renderings) | T-35, T-73, T-75, T-77 |
| C-09 | `judge_llm.py` (`from_env`) | T-33, T-40 |
| C-10 | `speccheck/judge_prompt.md` (incl. `declared` and `related` fields, the skepticism rule, and the `related` rule (R-38)), `judge_llm.py` (system message) | T-33, T-54, T-74, T-75, T-83, T-84, T-87 |
| C-11 | `judge.py` (progress line rendering, draw/erase sequences) | T-62 |
| C-12 | `extract.py` (token pass over `SpecId.text`, direction rules, order, undeclared-target Notes) | T-79 |
| C-13 | `impact.py` (changed set and reasons, breadth-first walk, `via`, depth cap, REVERIFY, RECITE, TEST_CASES), `report.py` (`impact.json`, `IMPACT_REPORT.md`, summary line) | T-80, T-81 |
| C-14 | `attribute.py` (docstring-span and whole-line-comment classification, Python and Swift) | T-85, T-86 |
| C-15 | `judge.py` (`JudgeRequest.declared`), `judge_llm.py` (`declared` in the request body), `speccheck/judge_prompt.md` (field definition, skepticism rule) | T-87 |
| C-16 | `report.py` (`tests[].declared`, `metrics.declared_ratio`) | T-86, T-88 |
| C-17 | `jev.py` (the four C-17 variables, the request body and `state` template — now including the D-28b `Related obligations:` section, R-38 — the `answers.verdict` parse and `p(e)`), `cli.py` (variable validation and redaction) | T-89, T-90 |
| C-18 | `explain.py` (the trace renderer: section order, headings, the C-05 reason, the verdict lines, the impact section) | T-92, T-93, T-94 |
| C-19 | `cli.py` (every argument definition's help, the C-19 metavar vocabulary, the `environment:` and exit-code epilogs) | T-95, T-96, T-97, T-98 |
| I-001 | `report.py` (temp-and-rename, interrupt cleanup), `cli.py` | T-07, T-38, T-43, T-45, T-60, T-64 |
| I-002 | kernel modules | T-36 |
| I-003 | `report.py` | T-25, T-35 |
| I-004 | `graph.py` | T-27, T-28 |
| I-005 | `judge.py` (validation: evidence in span, clause located) | T-29, T-75 |
| I-006 | `cli.py`, module import layout | T-43 |
| I-007 | `cli.py` (logging filter), `judge_llm.py` (redaction) | T-40, T-41 |
| I-008 | `graph.py` (metrics) | T-24 |
| I-009 | `cli.py`, `report.py` | T-39 |
| I-010 | `graph.py` (edge selection: PASSING, passed, not recorded), `judge.py` | T-31, T-77 |
| I-011 | `extract.py` (normalization) | T-02 |
| I-012 | `extract.py` (deduplicate by resolved path, first-seen `scan_root`, emit by ascending path) | T-78 |
| I-013 | `impact.py` (breadth-first order, first-reached depth, smallest `via`) | T-80 |
| I-014 | `attribute.py` (`declared` is a pure function of the source/test trees), `report.py` (`declared_ratio`) | T-85, T-88 |
| I-015 | `jev.py` (answer discarded after the order is computed), `report.py` (no triage field in either report) | T-89 |
| I-016 | `cli.py` (the explain path writes no report and carries the judge contract unchanged), `explain.py` (reads only pipeline facts) | T-92, T-94 |
| I-017 | `cli.py` (no help path reads a file, an environment variable or a socket) | T-96 |
| K-01 | `cli.py` | T-39, T-40, T-19, T-64 |
| K-02 | `extract.py` (file filters, binary rule) | T-13 |
| K-03 | `extract.py` (walker, no symlinks) | T-13 |
| K-04 | `extract.py` (`ID_RE`) | T-03 |
| K-05 | `judge_llm.py` (full-lifecycle timeout) | T-33 |
| K-06 | `judge_llm.py` (concurrency), `cli.py` (`--judge-concurrency`) | T-33 |
| K-07 | `judge.py` | T-32 |
| K-08 | kernel (performance) | T-51 |
| K-09 | `report.py` | T-34 |
| K-10 | `cli.py` (`--version`) | T-50 |
| K-11 | `cli.py` (`--max-unknown`, Decimal comparison, `null` rule) | T-59 |
| K-12 | `judge.py` (budget deadline, in-flight completion, `N%` issued count), `cli.py` (`--judge-budget`) | T-61, T-89, T-90 |
| K-13 | `judge.py` (redraw on completion, 1 s ticker, single erase) | T-62 |
| K-14 | `extract.py` (statement cap at line boundary, marker line, Note) | T-72 |
| K-15 | `judge.py` (whitespace-collapsed substring matcher, 12/280 bounds) | T-75 |
| K-16 | `jev.py` (triage pass over the `related`-bearing `state` (D-28b), confidence ordering, D-30 Note), `judge.py` (issue order), `cli.py` (`--jev-pre-triage`) | T-89, T-90 |
| E-01 | `extract.py`, `cli.py` | T-07 |
| E-02 | `extract.py` | T-06 |
| E-03 | `extract.py` | T-04 |
| E-04 | `extract.py` (fence tracking) | T-05 |
| E-05 | `results.py` | T-19 |
| E-06 | `results.py` | T-17 |
| E-07 | `results.py`, `report.py` | T-18 |
| E-08 | `graph.py` (`unrun`) | T-22 |
| E-09 | `cli.py` (path validation incl. `--out`; a PATHS element resolved and used, incl. neither-file-nor-directory → E-52) | T-40, T-78 |
| E-10 | `extract.py` | T-13 |
| E-11 | `extract.py` (scan roots and `SPEC.md`) | T-13, T-01 |
| E-12 | `attribute.py` | T-11 |
| E-13 | `attribute.py`, `report.py` | T-10 |
| E-14 | `judge.py`, `judge_llm.py` | T-30, T-33 |
| E-15 | `judge.py` | T-30 |
| E-16 | `judge.py` | T-29 |
| E-17 | `judge.py` | T-26 |
| E-18 | `report.py` (write/rename/cleanup, JSON-then-Markdown) | T-45 |
| E-19 | `graph.py`, `cli.py` | T-20, T-39 |
| E-20 | `extract.py` (strikethrough only in spec) | T-23 |
| E-21 | `cli.py` | T-40 |
| E-22 | `attribute.py` | T-14 |
| E-23 | `extract.py` (exclusions) | T-36 |
| E-24 | `results.py` (join_name, worst-of) | T-52 |
| E-25 | `graph.py` (step 2b) | T-53 |
| E-26 | `graph.py` (step 5), `cli.py` (`--strict`) | T-27, T-39 |
| E-27 | `results.py` (longest-suffix join) | T-58 |
| E-28 | `attribute.py` (class recognition, `test*` methods) | T-56 |
| E-29 | `extract.py` (binary rule) | T-13 |
| E-30 | `extract.py` (walker; descent-time symlinks only) | T-13 |
| E-31 | `extract.py` (row/heading parsers) | T-55 |
| E-32 | `cli.py` (R-28 gate, `unavailable` precedence) | T-59 |
| E-33 | `extract.py` (ignore markers) | T-57 |
| E-34 | `extract.py` (temporary exclusion), `report.py` (leftover cleanup) | T-36, T-45 |
| E-35 | `judge.py` (budget, both forms) | T-61, T-89 |
| E-36 | `judge.py`, `cli.py` (R-28 with `null`) | T-59 |
| E-37 | `graph.py` (eligibility), `report.py` (`verdict: null`, em-dash rendering) | T-34, T-35, T-77 |
| E-38 | `report.py` (Note ordering) | T-34 |
| E-39 | `cli.py` (`--progress` gating) | T-63 |
| E-40 | `judge.py` (erase in `finally`) | T-63 |
| E-41 | `cli.py` (`KeyboardInterrupt` → exit 3), `report.py` (cleanup), `judge.py` (erase; timed polling of futures, `abort` flag), `judge_llm.py` (abortable deadline wait, daemon transport thread) | T-63, T-64 |
| E-42 | `attribute.py` (Swift brace fallback) | T-67 |
| E-43 | `attribute.py` (Swift undelimited `test*`) | T-65, T-66, T-71 |
| E-44 | `extract.py` (first-cell decoration) | T-70, T-71 |
| E-45 | `results.py` (tie → unattributed) | T-68 |
| E-46 | `extract.py` (cap and Note; empty body → title) | T-72 |
| E-47 | `extract.py` (inner declarations parsed; body ends only at level $\leq$ own) | T-72 |
| E-48 | `judge.py` (unlocated clause → `UNKNOWN`) | T-75 |
| E-49 | `judge.py` (clause blanked for `UNRELATED` / `UNKNOWN`, non-string clause, coerced verdicts) | T-75 |
| E-50 | `extract.py` (marker on a non-T id → Note) | T-77 |
| E-51 | `graph.py` (steps 1–4 unchanged for recorded ids) | T-77 |
| E-52 | `cli.py` (a PATHS element inside `--root` but neither a directory nor a file → usage `2`) | T-78 |
| E-53 | `cli.py` / `impact.py` (`--changed` element validation and message) | T-81 |
| E-54 | `cli.py` (`impact` flag exclusivity; rejected `check`-only flags; `--against` errors) | T-81 |
| E-55 | `extract.py` (`Edge.retired`), `report.py` (struck ID cells in the impact report) | T-79, T-80 |
| E-56 | `attribute.py` (`declared: false` for a `"src"`-kind or file-level citation) | T-85, T-86 |
| E-57 | `judge_llm.py` / `jev.py` (a retired id that appears in a `related` neighbourhood keeps its `title` with `(retired)` appended; the `affects`/`depends_on` edge to it is still marked `retired` per E-55) | T-83 |
| E-58 | `cli.py` (`--judge-budget N%` requires `--jev-pre-triage` with `--judge llm`; message names both flags) | T-90 |
| E-59 | `jev.py` (per-edge failure ordered first, counted in one Note; `judge_available`/`unknown_rate` untouched) | T-89 |
| E-60 | `cli.py` (the `explain` id validation and its message) | T-93 |
| E-61 | `cli.py` (the judge flags carried over), `explain.py` (verdict rendering incl. `coerced` and `not judged`) | T-94 |

---

## 12. Open questions and decisions to confirm

Every row below is a decision the specification's author made on the requester's behalf because `one_sentence_prompt.md` did not settle it. The normative rows assume the default; the reviews checked that the default is precise, not that it is what the requester wanted. Rows are the `D-nn` family (decisions to confirm). A row marked `confirm` is ratified by a human changing its status to `confirmed v1.n`; a row the requester overturns becomes a `fix(speccheck):` change with a version bump. Since v1.13 this table is machine-read: it is the C-01 (c) decision table, and each row's *Affects* cell is the normative list of the ids the decision touches — the source of the `affects` edges (C-12) that `impact` walks. An id a decision affects and the cell omits is a defect the T-82 backtest can find.

| ID | Decision | Default taken | Alternatives rejected | Affects | Owner / status |
| ----- | -------------- | ---------------- | ------------------ | ---------- | ------------ |
| D-01 | Implementation stack | Python 3.12 + `uv`, standard-library kernel, one HTTP client behind an extra | Go or Rust (single static binary; stack-neutral repos would not need a Python runtime); TypeScript (nearest to most agent tooling) | §10, C-02/C-03 type pins, K-10 | requester / confirm |
| D-02 | Test-result input contract | JUnit XML, consumed; the tool never runs tests | run the suite itself (simpler for users, but executes untrusted code and ties the tool to one runner); pytest's own JSON report (richer, Python-only) | R-05, C-04, non-goal "no test execution" | requester / confirm |
| D-03 | What counts as a citation | a literal ID token anywhere in a file, with `speccheck:ignore` opt-outs | a structured annotation (`@spec R-07`, a decorator, a registry) — precise but requires adoption; docstring-only citations — misses comments | C-01, R-03, R-04, R-27, the §0 limitation | requester / confirm |
| D-04 | Family-T semantics | option (a): T ids are in scope, cited by their own test, and count in `conformance` | option (b): T ids declared but out of scope, reported separately — leaves `conformance` about R/C/I/K/E only | R-25, C-05 step 2b, C-07 metrics, T-53 | requester / confirm (F-001 chose (a) on the reviewer's recommendation) |
| D-05 | Mixed judge verdicts under `--strict` | an ID with both `ASSERTS` and `EXECUTES_ONLY` edges is `PASSING` and passes strict | a `MIXED` status that fails strict — stricter, noisier | R-15, C-05 step 5, E-26 | requester / confirm (F-003) |
| D-06 | Judge question and vocabulary | one question per edge — does this test *assert* the behavior? — with `ASSERTS` / `EXECUTES_ONLY` / `UNRELATED` / `UNKNOWN`; from v1.7 answered at the granularity of a clause: a statement with several clauses is asserted when any one of them is (C-10, R-33) | a graded strength score (rejected: a number the model made up); judging code rather than tests (rejected: semantic analysis is a non-goal) | C-06, C-10, I-004, I-005 | requester / confirm |
| D-07 | Judge request parameters | `temperature 0`, `max_tokens 4000` (v1.2; was 400), 30 s timeout, concurrency 4, budget unlimited, `--max-unknown 0.2` | any of these numbers; `max_tokens 400` was rejected after the first T-49 runs because thinking models (`qwen3:8b`, `gemma4:latest`) spend the budget on reasoning and are truncated before the verdict JSON, driving `unknown_rate` above `--max-unknown`; at 4000 both pass T-49 three runs out of three. The other numbers remain defaults with no data behind them | C-06, K-05, K-06, K-11, K-12 | requester / `max_tokens` confirmed; the rest remain confirm |
| D-08 | Judge instruction text and model | the C-10 text as written (v1.9: clause-first question, `clause` field); no default model — the operator's `SPECCHECK_JUDGE_MODEL` | any rewording; the text's only evidence is T-49 | C-10, R-26, T-49, T-76 | requester / confirm — re-opened again in v1.9: the text changed (R-34); confirm after three fresh T-49 runs over the T-76 label set with each candidate model, and record both. Measured 2026-09-18 under the v1.8 text: `openai/gpt-4o-mini` (fast; graded long bodies by their gist) and `google/gemini-3.8-flash` (located clauses, stricter, 4–8× the wall-clock, needs `--judge-concurrency` ≤ 8) — both passed the nine-label T-49 at 1.000, which is why T-76 exists |
| D-09 | Input limits | files over 2 MiB skipped; NUL byte in the first 8 KiB means binary; IDs 1–3 digits | larger cap, or none; MIME sniffing; 4-digit IDs | K-02, K-04, E-10, E-29 | requester / confirm |
| D-10 | LLM endpoint shape | an OpenAI-compatible `chat/completions` body, provider-agnostic | a specific vendor SDK (simpler, vendor-locked); a local-model-only path | C-06, C-09 | requester / confirm |
| D-11 | Fixture and self-check layout | `fixtures/target/` with `golden/`, byte-copied into the wheel as `speccheck/_selfcheck/` | package only the goldens and regenerate the fixture; skip the self-check entirely | §10, T-43, T-46, T-60 | requester / confirm |
| D-12 | Report file names and location | `SPEC_CONFORMANCE_REPORT.md` and `speccheck.json` under `--out`, default `.` | a `reports/` directory; a single JSON with Markdown derived by a separate renderer | §3.3, C-07, C-08, E-18 | requester / confirm |
| D-13 | Python test-case delimitation | `def test_*` at module level; `test*` methods in `Test*` classes and `*TestCase` subclasses; nested classes excluded | honor `pytest.ini` `python_functions` / `python_classes`; collect via pytest itself (rejected: runs code) | C-03, E-28, T-56 | requester / confirm (F-007, F-102) |
| D-14 | Reference machine for K-08 | named in `SPEC_BUILD_REPORT.md` at build time | a CI runner with a generous bound; no performance constraint at all | K-08, T-51 | build owner / open |
| D-15 | Progress indicator shape and gating | a single in-place ASCII line on stderr (`#`/`-` bar of 20 cells, done/total, elapsed, ETA per C-11), padded with spaces and redrawn with a bare `\r` (no terminal escapes; v1.4, F-205), on by default only when stderr is a TTY and not at DEBUG, erased when the judge stage ends, `--progress auto\|always\|never` to override; LLM judge only | leaving the final line on screen (rejected: §5.3 quiet-by-default would then have a visible exception at exit); a per-edge log line instead of a bar (rejected: that is what `--verbose DEBUG` already is); Unicode block characters (rejected: R-29 locale reasoning); a bar for `--judge mock` too (rejected: mock is sub-second, K-08); a spinner without ETA (rejected: the requester's complaint is duration, so ETA is the useful number) | R-30, C-11, K-13, E-39, E-40, §5.1, §5.3 | requester / confirm (the *existence* of the bar is the requester's ask of 2026-09-13; its shape is the author's default) |
| D-16 | Exit code on interrupt | `SIGINT`/`KeyboardInterrupt` exits `3` with message `interrupted`, keeping K-01's closed set `{0,1,2,3}`; temporaries and any already-renamed report removed | the shell convention `130` (rejected by default: it widens K-01 and every CI wrapper that switches on the code; easy to adopt if the requester prefers it); leaving Python's default (rejected: traceback, exit `1`, indistinguishable from `NOT CONFORMING`) | E-41, E-40, §5.4, K-01, I-001, T-64 | requester / confirm (F-204) |
| D-17 | How Swift test files are delimited | by lines and brace counting inside `attribute.py` (C-03 TYPE LINE / FUNC LINE / ATTRIBUTE BLOCK / SPAN END rules; comments and string literals excluded from the count), so the kernel stays standard-library and needs no toolchain at check time | a real parser (`swift-syntax` has no Python binding; `swiftc -dump-parse` or `swift test list` need a Swift toolchain where the checker runs and give names but not line spans); treating `.swift` as file-level as before (the citations then never join — the defect that motivated v1.6) | R-31, C-03, E-42, E-43, T-65..T-67 | requester / confirm |
| D-18 | Where the Swift `MODULE` in a classname comes from | the first path component of the file under its `--tests` root, or the root's last component for a file directly under it, or — a file named *directly* as a `--tests` PATHS element (D-23) — its parent directory's last path component (SwiftPM's `Tests/<Target>/` layout) | parse `Package.swift` for target names and paths (a second grammar); a `--swift-module` flag (one more thing to get wrong); match on the type chain alone ignoring the module (ambiguous across targets) | C-03, T-65, T-68, T-78 | requester / confirm |
| D-19 | How a Swift Testing result name (`twoArgs(a:b:)`) is joined | C-04 strips the signature and joins on the bare identifier; overloads by label tie and are unattributed (E-45) | reconstruct the label signature in the adapter and join exactly (correct for overloads, but default arguments, `_` labels, generics and `inout` all need parsing to get right); join on signature when present and fall back to identifier (two rules where one suffices) | C-04, E-45, T-68 | requester / confirm |
| D-20 | What a heading-declared ID's statement contains | the title plus the whole section body, fenced code blocks included, capped at 16,384 bytes (R-33, C-01 (b), K-14) — the pinned shape is the contract, and it is what a literal judge needs | prose only, code blocks dropped (smaller; rejected because MonteCarloPi's C-02 would still be judged on comment-free prose); the first fenced block only (loses prose clauses such as "throws on the first tick", and bullet-pinned shapes such as C-05's reservoir); the body to the judge but the title as JSON `statement` (two notions of "statement" in one tool; the report could not show what the judge saw); letting the judge fetch context itself (nondeterministic, provider-specific, against the §0 boundary). The cap's value is part of this decision: the proposal drafted 8,192 bytes, which would have truncated this document's own C-03 (8.4 kB) in T-48 and handed the judge a Swift-less C-03; the requester raised it to 16,384 on 2026-09-18 so no known contract is cut | R-33, C-01, C-02, C-06, C-07, C-10, K-14, E-46, E-47, T-72..T-74 | requester / confirmed v1.7 (code blocks included, cap 16,384; 2026-09-18) |
| D-21 | How a verdict is tied to the statement | the judge quotes the clause it judged against and the kernel requires it to be LOCATED (whitespace-collapsed substring, 12..280 characters; K-15), coercing an unlocated `ASSERTS`/`EXECUTES_ONLY` to `UNKNOWN` — the same grounding pattern as evidence lines (R-34, E-48) | prompt rewording only, no `clause` field (smaller; unverifiable — the kernel cannot tell a located match from a gist, and the report cannot show which clause was judged); sending only a "relevant" slice of the body (the kernel cannot know which clause a test is about; D-20's rejected alternative); voting across repeated calls (K-06: one request per edge; hides instability); fuzzy clause matching (arguable at the boundary; "quote it" means verbatim, and a model that cannot is the finding) | R-34, C-06, C-07, C-08, C-10, K-15, E-48, E-49, I-005, T-75 | requester / confirmed v1.9 (2026-09-18: "apply proposal 1.9 in full") |
| D-22 | Recorded-not-gating T ids under an honest judge | v1.10: a `*(recorded)*` marker in the T row's ID cell (C-01) makes the id RECORDED — its citing test still has to exist and pass (C-05 steps 1–4, E-51), but its edges are never judged (step 5, I-010), so a presence check is what it is and the strict LLM gate stays about assertions. This document marks T-48, T-49 and T-51 | no rule (v1.9's state: an honest judge marks the presence check `EXECUTES_ONLY` and `--strict --judge llm` exits 1 on this repository by design — `gemini-3.8-flash` did so to T-48 on 2026-09-18); a stated assertion for the presence check (fragile: what a presence check can honestly assert differs per recorded test); excluding family T from the judge stage entirely (too broad: T ids realized by real tests benefit from the judge) | R-35, C-01, C-02, C-05 step 5, I-010, C-07, C-08, E-50, E-51, T-77 | requester / confirmed v1.10 (2026-09-18: "let's do D-22") |
| D-23 | `--src`/`--tests` accept a comma-separated list of files and/or directories | each occurrence is split on the literal `,`, every resulting segment is whitespace-trimmed and empty segments are dropped (no Note, no error); the surviving paths are resolved inside `--root` and deduplicated by resolved path — a file reached by more than one element is scanned and cites exactly once (I-012), the emits are in ascending-path order (I-002), and a file's recorded `--src`/`--tests` root, and thus a directly-named `.swift` file's `MODULE` (D-18), is fixed by the first-seen covering element; a directory element is descended and a regular file is scanned as one with every per-file filter applied; the default `src`/`tests` (the directory if it exists) applies only when the flag is entirely absent | a strict "any empty or whitespace-only segment is a usage error" policy (rejected: a trailing `--src a,` or a defensive `a,,b` is common and should not fail a run); extending the same list to `--results` (rejected for D-23: `--results` stays one JUnit file — a documented possible later step); a shared path-list primitive for every path flag, including `--out` (rejected: `--out` is a single destination, and a list of output directories is odd); letting a merely present-but-empty flag fall back to the directory default (rejected: an explicitly-given empty list is the operator's statement "no trees", which is E-19) | R-03, R-04, C-03, §5.1, E-09, E-30, E-52, I-012, I-002, T-40, T-78, D-18 | requester / confirmed 2026-09-19 ("trim + drop empties", scoped to `--src`/`--tests`) |
| D-24 | Where the change-impact backtest lives | `tools/impact_backtest.py`: a script outside the kernel that shells out to `git` for two spec versions and a build range, calls `speccheck impact --against`, and scores the prediction against the touched citations (T-82). The kernel exposes only the pure function of files (`--against FILE`) and never invokes `git` or any subprocess. | a kernel `--since REF` that reads the prior spec from `git` (one command for the operator, but the kernel gains a subprocess, a history-dependent input, and a failure mode per git state; I-001/I-002's "same bytes in, same bytes out" would need a git-state clause) | R-37, C-13, §3.1, §10, T-82, I-002 | requester / confirmed 2026-09-19 (`PROPOSAL_v1.13_impact.md` §5) |
| D-25 | How decision rows enter the JSON | a separate `decisions` array (C-07) under a declaration-only family D (C-01 (c)): never in `ids`, never a citation target, never in `by_status`, `by_family`, `conformance`, `dangling`, or `stale`; I-003 and every existing golden §3 row are untouched | a seventh family in `ids` with a status of its own (uniform with the other families, but every denominator, the T-46 goldens, and the C-08 table change, `by_family` needs a seventh key, and `UNCITED`/`UNTESTED` are meaningless for a decision) | R-36, C-01, C-02, C-07, C-12, I-003, T-79 | requester / confirmed 2026-09-19 (`PROPOSAL_v1.13_impact.md` §5) |
| D-26 | Whether `declared: false` changes the judge's verdict on its own | advisory only (Part B as written): `C-10`'s instruction text tells the model `declared` and asks it not to credit `ASSERTS` on an INCIDENTAL citation without checking the assertion's subject, but no C-06 rule coerces the verdict — preserves the model's judgment for the real, undocumented-but-correct cases; T-87 measures whether the text alone is enough | hard coercion: `declared: false` forces `ASSERTS` to `EXECUTES_ONLY` automatically, no model discretion — stronger and fully deterministic, but risks false downgrades on tests that simply predate or don't follow the docstring convention perfectly; kept as the fallback if T-87 shows the advisory text moves nothing | C-06, C-10, C-15, T-87 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.15_declared_vs_incidental_citations.md` §5) |
| D-27 | How a citation line is classified DECLARED | whole-line-comment detection: the first non-whitespace character on the citation's own line is `#` (Python) or the line is a doc-comment line by the Swift adapter's existing recognition (C-14) — no new parsing machinery, matches every real DECLARED example found while drafting the proposal | full token-level comment detection (via `tokenize`, distinguishing a trailing comment from code): more precise (would credit `x = 1  # R-02` as DECLARED) but needs column-accurate token classification the citation scanner does not carry today, for a case that did not appear once in the real evidence read for the proposal; left for a later proposal if it proves necessary | C-03, C-14, T-85 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.15_declared_vs_incidental_citations.md` §5) |
| D-28 | How wide the judge request's `related` neighbourhood reaches, and whether it rides the Jev triage `state` (this row carries both: the reach decision and its sub-decision, recorded here as **D-28b**) | **(a)** `related` is the titles of the obligations this statement names **and** of those that name it (C-12 `depends_on`, both directions), the statement's own references first, at most eight total, each a whitespace-collapsed title tail-truncated to 160 characters with `…`, `[]` when the id has no neighbour; a retired neighbour keeps its title with `(retired)` appended (E-57). `(b)` **D-28b**: `related` is included in the C-17 triage `state` (not stripped) — Jev ranks the exact request the real judge gets — at a cost of roughly doubling the per-edge triage input, which is cents (§3 of `PROPOSAL_v1.14_obligation_aware_judge.md`). | **(a-alt)** own references only, uncapped: smaller on heavily-depended-on ids (C-01 and C-07 have dozens of dependents) but misses the reverse-direction case the §4 flags — a test that cites E-09 yet asserts E-52's message is the same off-topic `ASSERTS` the other way round. **(b-alt)** strip `related` from the triage `state`: cheaper (no neighbourhood pass) at the price of a weaker proxy for "least-sure-about"; kept as the fallback if a T-89 run shows triage ranking is insensitive to the neighbourhood. Advisory: the `related` rule in C-10 tells the model not to credit an `ASSERTS` that matches only a related obligation, but no C-06 rule coerces a verdict for it. | R-38, C-06, C-10, C-16, C-17, K-16, I-015, E-57, T-83, T-84, T-89 | requester / confirmed 2026-09-20 (reach — both directions, own-first, cap 8 — per `PROPOSAL_v1.14_obligation_aware_judge.md` §5; the D-28b sub-decision — include in the triage `state` — per that proposal's §7 addendum; both the recommended options) |
| D-29 | How the triage provider is configured | dedicated variables, `SPECCHECK_JEV_URL` / `SPECCHECK_JEV_MODEL` / `SPECCHECK_JEV_API_KEY` / `SPECCHECK_JEV_TIMEOUT` (C-17), read only when the triage pass runs | reusing `OPENROUTER_API_KEY`, as `tools/jev_client.py` already does — one fewer variable to set, but it couples the kernel's own configuration to a `tools/`-script naming choice and cannot be scoped or rotated independently of any other OpenRouter use | C-17, K-16, §10 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.16_jev_pre_triage.md` §5) |
| D-30 | Whether `--jev-pre-triage` with `--judge-budget 0` complains | yes — one informational Note, `jev-pre-triage had no effect: --judge-budget is unlimited` (K-16). The combination pays Jev's latency and dollar cost for zero effect on the report, and a Note costs nothing while catching a likely mistake, consistent with this project's Notes-not-errors style | silently proceeding — no new Note text, but the one combination that buys nothing looks exactly like the one that buys something | K-16, K-12, E-59, T-89 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.16_jev_pre_triage.md` §5) |
| D-31 | What a per-edge Jev failure during triage does | orders that edge first (as least confident) and records one Note (E-59); the run is never aborted. This session's own `deepseek-v4.1-flash` self-check run hit 110/656 (16.8%) real-provider coercions — 65 timeouts, 42 malformed responses — so "Jev could not answer" is expected to happen, and treating it as "assume this edge needs the real judge" is the safe default for a signal that sometimes fails | aborting the whole run on the first Jev failure — simpler and louder, but fragile against exactly the provider flakiness this project has already measured in a sibling judge model; it would also let a triage-only fault destroy a run that would otherwise have completed | E-59, K-16, T-89 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.16_jev_pre_triage.md` §5) |
| D-32 | How `N%` rounds | up: $\lceil N/100 \times E \rceil$ of the $E$ eligible edges (K-12), so any nonzero percentage issues at least one edge to the real judge | floor or round-to-nearest — floor silently zeroes the real judge at low percentages on a small edge count (1% of 50 edges floors to 0, a pure triage run that does not say so) | K-12, T-89 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.16_jev_pre_triage.md` §5) |
| D-33 | `explain`'s output surface (v1.17) | **stdout only**: no `--out`, no durable file, no `schema_version` entry, no golden pair — the structured view of the same facts already exists as `speccheck.json`, and the narrative is what this command adds (C-18, §3.3) | a durable `EXPLAIN_<ID>.md` + `explain.json` pair matching the two-files-per-subcommand pattern — CI-friendlier, but it adds a durable-artifact contract, a golden pair to regress, and a third pair that must obey §3.1's temp-and-rename rule, while duplicating `speccheck.json` | R-40, C-18, §3.3, I-001, T-92 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.17_explain_id.md` §5, recommended branch) |
| D-34 | Whether the trace carries the upward `impact` section (v1.17) | **include** it, at `--depth 1` by default: the forensic complement to the downward trace — *why this id is weak* beside *what a change to it might touch* — and it costs nothing, since C-12's `walk` and C-13's `reverify` already exist (C-18) | downward-only (the pure "why" trace), which would leave the reader to run `impact` separately for the other half | R-40, C-18, C-13, T-92 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.17_explain_id.md` §5, recommended branch) |
| D-35 | Where `explain`'s facts come from (v1.17) | **recompute** from the same pipeline inputs `check` uses (`--spec`/`--src`/`--tests`/`--results`, judge contract carried over, E-61): deterministic, byte-reproducible, able to show a live verdict under `--judge llm`, and no second input contract | a `--from speccheck.json` fast-path — instant, but it adds a report-as-input surface §0's boundary cautions against and cannot show a verdict a `none`/`mock` run never recorded | R-40, C-18, I-016, §0, T-92 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.17_explain_id.md` §5, recommended branch) |
| D-36 | How many ids one `explain` invocation takes (v1.17) | **one id per invocation**, positional; an undeclared id is exit `2` per E-60 and a retired id is rendered, not an error; a shell loop drives many ids | accepting a list of ids and printing one block each — convenient, but it would need a second output format and its own exit-code rule (does one undeclared id fail the whole run?) | R-40, C-18, E-60, K-01, T-93 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.17_explain_id.md` §5, recommended branch) |
| D-37 | How much a flag's help entry carries (v1.18) | **the full entry** — purpose, values, default and preconditions (C-19) | values and default only (shorter, but it leaves E-58's `N%` companion requirement and E-09's containment rule undocumented — the two failures §1 shows rejecting a well-formed command); values only (the literal ask, and the help still cannot be used to construct a judge invocation) | R-41, C-19, T-95, T-96 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.18_cli_help_contract.md` §5, recommended branch) |
| D-38 | Whether the exact help wording is normative (v1.18) | **content-required, wording free** — C-19 pins what each entry must carry and the metavar vocabulary; T-97's golden in `tests/data/help/` makes every wording change visible without a spec revision | exact strings normative in `SPEC.md` (maximum stability for consumers that parse the help, at a spec revision and version bump per typo, and ~50 lines of CLI prose duplicating §5.1) | R-41, C-19, T-97, §10 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.18_cli_help_contract.md` §5, recommended branch) |
| D-39 | How the help is guarded (v1.18) | **round-trip equality plus width-pinned goldens** — T-95 (the tokens are true), T-96 (every definition has help), T-97 (the bytes, at `COLUMNS=80`) | round-trip equality only (no golden churn on rewording, but a silently reduced entry then passes as long as its remaining tokens are correct) | R-41, C-19, T-95, T-96, T-97 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.18_cli_help_contract.md` §5, recommended branch) |
| D-40 | What the screens carry beyond the per-flag entries (v1.18) | **per-flag help plus an exit-code and summary-line epilog** on every `--help` (the codes are the second thing an operator or agent needs, and they are printed nowhere the CLI can be asked about; §5.4 is a stable K-01-pinned set) | strictly per-flag help (smallest surface, no fourth copy of §5.4); per-flag help plus a machine-readable `--help-json` (exact for a parsing agent, but a new interface, a new contract, and a second rendering of the same facts to keep equal) | R-41, C-19, §5.4, §5.1, T-96, T-97 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.18_cli_help_contract.md` §5, recommended branch) |
| D-41 | What the `environment:` block lists (v1.18) | **the eight `SPECCHECK_*` names with read condition, requiredness and default, plus one clause for `COLUMNS`** — the only variable that changes a `--help` run's own output, and the one T-97's golden pins | the eight names only (`COLUMNS` stays undocumented and T-97's fixed width unexplained); also documenting `install.sh`'s `~/.config/speccheck/judge.env` and its shell-rc `source` line (helpful for a first-time installer, but no kernel code reads that file — it is the installer's shell convenience) | R-41, C-19, T-97, T-98 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.18_cli_help_contract.md` §5, recommended branch) |
| D-42 | Where C-06's wrong variable name is fixed (v1.18) | **in this version's own fold** — `SPECCHECK_LLMMODEL` becomes `SPECCHECK_JUDGE_MODEL`, matching C-06's own request block two lines above it, C-09's block and `judge_llm.py`'s `ENV_MODEL`; the proposal's recommended branch (ride along in the still-uncommitted v1.16 fold) is no longer available because v1.16 and v1.17 have landed, so the fix lands here | leaving it (the name stays wrong and contradicts C-06's own block; T-98 still passes, because it binds the help to the code, not to that sentence) | R-41, C-19, C-06, C-09, T-98 | requester / confirmed 2026-09-20 (`PROPOSAL_v1.18_cli_help_contract.md` §5; branch adapted — see the v1.18 history row) |

None of the first fourteen was raised as a question before v1.1; each was decided and reviewed for precision only. That is the defect this section corrects: a specification can be implementation-grade and still not be what was asked for.

D-28 (and its sub-decision D-28b), E-57 and R-38 — the obligation-aware judge of `PROPOSAL_v1.14_obligation_aware_judge.md` — are now declared by this v1.16 fold, discharging the reservation that held them in v1.15; D-29..D-32 and E-58..E-59 sit in the v1.15 Jev rows. The reservation that stood for the still-pending `PROPOSAL_v1.17_explain_id.md` in v1.16 is discharged: v1.17 declares R-40, C-18, I-016, E-60, E-61 and T-92..T-94 for it. `PROPOSAL_v1.18_cli_help_contract.md` remains pending and will take the next ids in whatever families it declares. Every gap in a family not held by such a pending proposal is an error, and the proposal that owns a held id will declare it when it lands.

## Revision history

| Version | Change |
| -- | -------------- |
| v0.1 | Initial draft from `one_sentence_prompt.md`, for `spec-review`. |
| v0.2 | P0 of `SPEC_REVIEW_REPORT.md` applied: F-001 T-family semantics (C-01, C-05 step 2b, R-25, E-25, T-53, T-48); F-002 scan exclusions and `--out` inside `--root` (C-03, §5.1, E-09, E-23, T-36); F-003 status is the sole input to `--strict` (R-15, §5.4, C-05, E-26, T-27, T-39); F-004 LLM body, response path, and normative instruction text (C-06, C-10, R-26, C-07 `judge_prompt_sha256`, T-33, T-54); F-005 parametrized JUnit names (C-04, C-07 `results`, E-24, T-52). P1 (F-006..F-013) and P2 (F-014..F-017) remain open. |
| v0.3 | P1 of `SPEC_REVIEW_REPORT.md` applied: F-006 longest-suffix classname join (C-04, E-27, T-58); F-007 `*TestCase` classes and `async def` (C-03, E-28, T-56); F-008 binary rule and no symlinks (C-03, K-02, K-03, E-29, E-30, T-13); F-009 row/cell/heading declaration grammar (C-01, E-31, T-55); F-010 one-line ASCII summary with regex, UTF-8 stdout (§5.1, R-29, T-44); F-011 packaged self-check fixture in a temp dir, I-001 exemption, §9.8 reference (§5.1, I-001, §10, T-43); F-012 `--strict --judge llm` requires an available judge and `unknown_rate` $\leq$ `--max-unknown` (R-28, K-11, C-07, §5.4, E-32, T-59); F-013 `speccheck:ignore` markers and the stated literal-citation limitation (§0, C-01, R-27, E-33, T-57). P2 (F-014..F-017) remains open. |
| v0.4 | P2 of `SPEC_REVIEW_REPORT.md` applied: F-014 logging default `ERROR`, Notes at `INFO`, nothing at `WARNING` (§5.3, T-42); F-015 in-memory render, temp-and-rename dual write, cleanup on failure, `--out` creation permitted (§3.1, §3.3, I-001, E-18, T-45); F-016 `judge_available` null/true/false rule, `by_family` always six keys, `by_status` seven in-scope statuses, ID cell struck (C-07, C-08, T-34, T-35); F-017 R-24 scoped to deterministic statuses plus recorded verdicts, T-49 per-run not pooled, K-08/T-51 recorded on a named reference machine via `tools/bench.py`, `SPEC.md` decoded UTF-8-with-replacement (R-24, T-49, K-08, T-51, §5.1, E-11, T-01). No findings open. |
| v0.5 | `FINAL_SPEC_REVIEW_REPORT.md` P1 and P2 applied: F-101 `join_name` strips from the first `[`, T-52 corrected; F-102 `test*` methods (no underscore) in recognized classes (C-03, E-28, T-56); F-103 temporaries get a per-run nonce, are excluded from scans, and leftovers are deleted first (§3.1, C-03, E-34, T-36, T-45); F-104 R-10 passed-outcome clause, R-19 self-check exemption; F-105 empty `classname` join and `null` `unknown_rate` (C-04, K-11, E-36, T-52, T-59); F-106 JSON-then-Markdown rename order and the one permitted stale combination (§3.1, E-18, T-45); F-107 inner self-check exit expectation, `_selfcheck/` byte-identical to `fixtures/target/`, drift guard T-60 (§5.1, §10); F-108 fence definition and fallback `classname` (C-01, C-03, T-05); F-109 line-numbered `source` in the judge request, marker fixtures in data files (C-06, C-10, §9); F-110 `--judge-concurrency` and `--judge-budget` (K-06, K-12, §5.1, E-35, T-33, T-61). No findings open. |
| v1.0 | All eleven findings of the independent `SPEC_v0.5_REVIEW_REPORT_by_QWEN.md` applied (cited as Q-nnn): Q-001 `verdict` key always present, `null` when unjudged, em dash in Markdown (C-07, C-08, E-37, T-34, T-35); Q-002 `notes` sorted by code point (C-07, E-38, T-34); Q-003 exact in-process `--self-check` invocation with `--results`, goldens under `fixtures/target/golden/` (§5.1, §10, T-43, T-46, T-60); Q-004 `unavailable` takes precedence over `unknown_rate` (C-07, §5.1, E-32, T-59); Q-005 `skipped` count added to the summary line and regex (§5.1, T-44); Q-006 "first declaration wins" removed (C-01); Q-007 symlinked command-line roots resolved and descended, descent-time symlinks skipped (C-03, E-09, E-30); Q-008 fence closing pinned — same marker character, no info string, no cross-type closure (C-01, T-05); Q-009 ratios as quantized Decimals emitted with exactly four decimals, K-11 compares the quantized value (C-07, K-11, T-34); Q-010 K-05 timeout spans the full request lifecycle, K-12 deadline semantics with in-flight completion (K-05, K-12, E-35, T-61); Q-011 `name` is `""` in JSON, `(file)` is Markdown-only, R-13 concerns data (C-07, C-08, E-13, T-35). No findings open. |
| v1.1 | Added §12, *Open questions and decisions to confirm*: fourteen decisions the author took by default on the requester's behalf (stack, results contract, citation rule, T-family option, mixed-verdict strict rule, judge question and parameters, instruction text, input limits, endpoint shape, fixture layout, report names, test delimitation, reference machine), each with its default, the alternatives rejected, the IDs it affects, and a `confirm` / `open` status. No normative row changed. The `spec-writing` skill now requires this section. |
| v1.2 | D-07 partly resolved by the first T-49 runs: `max_tokens` raised from 400 to 4000 in the judge request body (C-06), the wire-format test updated to match (T-33), and the D-07 row records the evidence. Thinking models truncated at 400 before emitting the verdict JSON; at 4000 `qwen3:8b` and `gemma4:latest` pass T-49 three runs out of three. No other normative row changed. |
| v1.3 | Judge-stage progress indicator, requested on 2026-09-13 because `--judge llm` runs take minutes: R-30 (requirement), C-11 (the one-line ASCII format, draw/erase byte sequences, regex, $k$ and ETA formulas), K-13 (redraw cadence, 20 cells, single erase before the report stage), E-39 (no bytes when not a TTY, at DEBUG, under `--progress never`, or with `--judge none\|mock`), E-40 (erase on interrupt or failure), `--progress auto\|always\|never` in §5.1, the §5.3 quiet-by-default exception, T-62/T-63, §11 rows, D-15. The indicator is written to the raw stderr stream, not the logger, and is erased at the end of the stage, so stdout, both reports, the exit code, and what remains on stderr at exit are unchanged. |
| v1.4 | All ten findings of the v1.3 `SPEC_REVIEW_REPORT.md` applied. P1: F-201 the logger is silent while the indicator is displayed (C-11, K-13, §5.3, T-62); F-202 one clock origin $t_0$ = first draw, K-12 keeps its own (C-11, K-13, T-62); F-203 coalesced cadence — within 100 ms, $\geq$ 1/s in flight, $\leq$ 10/s — and atomic serialized writes (K-13, T-62); F-204 E-41 interrupt rule: exit `3`, message `interrupted`, temporaries and renamed reports removed (E-40, E-41, §3.1, §5.4, T-63, T-64, §11, D-16); F-206 C-07 example uses `0.2000`/`0.0000` and `max_unknown` is emitted quantized (C-07). P2: F-205 no terminal escapes — draws padded to the widest line so far, erase is `\r` + spaces + `\r` (C-11, T-62, D-15); F-207 C-08 header parenthetical omitted when `judge_available` is null (C-08, T-35); F-208 T-46 cited by R-01..R-15 and T-60 by R-18/I-001 in §11; F-209 I-005 vacuous clause replaced; F-210 T-49 names `fixtures/target/golden/judge_labels.json` and `tools/eval_judge.py`. |
| v1.5 | E-41 tightened from "in-flight requests are not awaited beyond the K-05 timeout" to "abandoned; exit within 1 s" after the first interrupt of a real `--judge llm` run against a local model appeared to be ignored: the main thread was blocked in an untimed future wait (not SIGINT-interruptible on macOS CPython) and then waited for the in-flight requests. T-64 gains the timing case; §11 E-41 row names the mechanism. No other row changed. |
| v1.6 | Swift adapter and two small grammar changes, requested 2026-09-17 after the MonteCarloPi Swift build ran the checker and got `62 unverified; 43 dangling` purely from tool limits: R-31 Swift Testing / XCTest test-case delimiting by lines with doc-comment-inclusive spans and SwiftPM-shaped classnames (C-03, E-42, E-43, D-17, D-18, T-65..T-67), a second `join_name` step that strips a Swift signature (C-04, E-45, D-19, T-68), Swift assertion tokens for the mock judge (C-06, T-69), R-32 decoration after the bold ID in a declaring first cell (C-01, E-44, T-70), a Swift golden fixture (T-71), O-2 and the §0 non-goal updated. |
| v1.7 | A heading-declared ID's statement is its title plus its section body (`PROPOSAL_v1.7_heading_bodies.md`, 2026-09-17): two LLM judges over the same 130 MonteCarloPi edges disagreed almost entirely on `###`-declared contracts because both were handed a title (`Data structures`, `` `EstimationWorker` (an `actor`) ``) and never the pinned API beneath it — one guessed generously, the other refused, and neither had the contract. R-33; C-01 (b) HEADING LINE / SECTION BODY grammar, fenced blocks included (D-20), table declarations unchanged; C-02 `SpecId.title`; C-06 statement passthrough; C-07 `title` key and `schema_version` `"1.1"`; C-08 renders `title`, so the Markdown report is byte-identical; C-10 gains the any-clause rule (new `judge_prompt_sha256`); K-14 16,384-byte cap with marker line and Note (the proposal's 8,192 would have truncated this document's C-03); E-46, E-47; T-72..T-74; §11 rows; D-20. The mock judge, statuses, metrics, and exit codes are unchanged; `--judge none` output differs only in `speccheck.json`. |
| v1.8 | All seven findings of the v1.7 `SPEC_REVIEW_REPORT.md` applied. P1: F-301 line model for `SPEC.md` — split on `\n`, trailing `\r` removed, BLANK := empty or whitespace-only, body lines re-joined with `\n` (C-01, C-02, I-002, T-72); F-302 T-72 and T-73 restated as properties of the current output, the one-time golden diff moved to `SPEC_BUILD_REPORT.md`; F-303 T-49 counts only runs under the current `judge_prompt_sha256`, D-08 re-opened, D-06 and §0 name the clause granularity. P2: F-304 ATX headings only, at most three leading spaces, bare `###` is a heading with an empty title, trailing `#` run stripped from the title, the declaring line is a HEADING LINE (C-01, T-72); F-305 empty title with a body → statement is the body alone (C-01, C-02, E-46, T-72); F-306 C-09 cited by T-33 and T-40; F-307 revision table sorted ascending, Status bullet shortened, `title` in the §1 Extractor row. No behaviour the v1.7 build would produce differently was changed; what changed is what the spec pins. |
| v1.9 | Clause-grounded verdicts and a body in the judge-evaluation fixture (`PROPOSAL_v1.9_clause_grounding.md`, 2026-09-18; D-21 confirmed). Evidence: with bodies in the statement, `gpt-4o-mini` graded long contracts by their gist — 13 of 18 stable downgrades on the mdv tree were tests asserting a body clause nearly verbatim — while `gemini-3.8-flash` located the clauses and found real gaps (`mdv:E-19`, `mdv:T-34`, this document's R-10); both passed the nine-label T-49 at 1.000. R-34; C-06 `Verdict.clause`, K-15 LOCATED rule, E-48 (`judge: unlocated clause`), E-49 (clause blanked for `UNRELATED`/`UNKNOWN`), I-005 grounded on both sides, mock clause = prefix of the statement (R-22); C-07 `clause` key and `schema_version` `"1.2"`; C-08 §8 Clause column; C-10 question reworded clause-first, `clause` in the reply (new `judge_prompt_sha256`); T-75; golden fixture gains a heading-declared contract with a multi-clause body ≥ 2,048 bytes and six labeled tests, label set ≥ 20 entries (T-46, T-76, T-49); §11 rows; D-08 re-opened and made a model row; D-21; D-22 opened (recorded-not-gating T ids under an honest judge). Statuses, metrics, exit codes, and `--judge none`/`mock` Markdown output unchanged; `--judge mock` JSON gains the `clause` key. |
| v1.10 | D-22 settled: RECORDED tests. A T row whose ID cell carries `*(recorded)*` as the first decoration token declares a recorded id (C-01, C-02 `recorded`); its status is computed by C-05 steps 1–4 like any T id (E-51) but its edges are never judged (step 5, I-010) and are not eligible edges for C-11; the marker on a non-T id is ignored with a Note (E-50); JSON gains `recorded` per id (`schema_version` `"1.3"`), the Markdown ID cell reads `T-48 (recorded)` (C-07, C-08); R-35, T-77; T-48, T-49 and T-51 marked in this document. Motivation: under an honest judge the presence checks that keep those ids cited are `EXECUTES_ONLY` by construction, so `--strict --judge llm` was red on this repository for a reason the spec intended but had left implicit. |
| v1.11 | All seven findings of the v1.10 `SPEC_REVIEW_REPORT.md` applied. P0: F-401 `schema_version` stated once (C-07, §3.3), T-73/T-75/T-77 refer to "the C-07 value". P1: F-402 the C-06 validation list is numbered, first-match, with a non-string `clause` treated as absent and every coerced `UNKNOWN` recording `clause` `""` (C-06, E-16, E-49, T-75); F-403 RECORDED named in the null-`verdict` condition, E-37 owning it (E-37, C-07, T-34); F-404 one marker rule after C-01 (b), the heading title strips it, `~~T-48~~ (recorded)` pinned (C-01, C-08, T-77); F-405 `judge_strength` over `PASSING ∖ RECORDED`, null case stated, T-77 arithmetic (C-07). P2: F-406 K-15 trims the clause (T-75 sub-case); F-407 "the current C-10 text", D-08 measurement moved to its status cell, Status bullet trimmed. No behaviour the build would otherwise get wrong changed; what changed is what the spec pins. |
| v1.12 | `--src` and `--tests` accept a comma-separated **list of files and/or directories**, requested 2026-09-19 after these flags accepted only directories (D-23): each occurrence is split on `,`, every segment whitespace-trimmed and empty segments dropped, paths resolved inside `--root` and deduplicated by resolved path (a file reached by more than one element is scanned and cites exactly once, I-012; emits are in ascending-path order; a file's recorded `--src`/`--tests` root — and thus a directly-named `.swift` file's `MODULE`, D-18 — is the first-seen covering element). Each directory element is descended and each regular file scanned as one, with every per-file filter applied identically; a path inside `--root` that exists as neither directory nor file is a usage error, `--<flag>: no such file or directory: <segment>`, replacing the former "non-directory → usage error" (E-52, exit `2`). The change is input-acceptance only: two inputs that name the same physical file set produce byte-identical reports (I-002), so the JSON/Markdown schemas, the summary regex, the statuses, the metrics, and the exit codes are unchanged and `schema_version` stays at the C-07 value. R-03 and R-04 reworded for the `--src`/`--tests` list; a C-03 `PATHS` rule and the directly-named-file `MODULE`; §5.1 synopsis, the `--src`/`--tests` rows, and a PATHS note; E-09 and E-30 generalized to PATHS elements; I-012 and E-52 added; T-78; §11 rows; D-18 extended; D-23 confirmed. |
| v1.13 | Spec-internal edges and the `impact` subcommand (`PROPOSAL_v1.13_impact.md`, 2026-09-19; D-24 and D-25 confirmed). Evidence: in v1.12 of this document 134 of 203 live ids name another id in their statement — 186 `depends_on` and 240 `verifies` edges — and the §12 *Affects* column holds 110 more; following `depends_on` transitively saturates (from 77 of 125 obligations the closure reaches at least 40), so the direct set is the signal and `--depth` defaults to 1 until the T-82 backtest says otherwise. Changes: C-01 (c) decision rows — a declaration-only family D found by the table whose header has an *Affects* cell; C-02 `Decision`, `Edge`, `SpecIndex.decisions`/`edges`; C-12 the edge rules (statement tokens → `depends_on`/`verifies` with normalized direction, *Affects* tokens → `affects`; undeclared targets are Notes; retired targets flagged, E-55; total order); C-07 `decisions` and `edges` after `ids`, `schema_version` `"1.4"`, nothing else in the JSON or the Markdown report changed; C-13 `impact` — `--changed IDS` or `--against FILE` (diff reasons pinned), breadth-first reverse walk with `via` and `--depth` (default 1, 0 unbounded), REVERIFY, RECITE, TEST_CASES, `impact.json` `"1.0"`, `IMPACT_REPORT.md`, a summary line with its regex; §3.1 the `impact` pipeline and its temporaries; §3.3 two artifacts; C-03 exclusions extended; §5.1 synopsis and four rows; §5.4 `impact` codes; §0 two non-goals amended; §1 the Impact walker; R-36, R-37; I-001 and I-002 extended, I-013; E-02 extended, E-53..E-55; §9.12 T-79..T-82 (T-82 recorded: the backtest on two ranges of `main`); §10 tools and goldens; §11 rows; §12 read by machine, D-24, D-25. |
| v1.14 | Declared vs. incidental citations (`PROPOSAL_v1.15_declared_vs_incidental_citations.md`, 2026-09-20; D-26 and D-27 confirmed). Evidence: `JUDGE_CROSSCHECK_REPORT.md` §2b — a `check --judge llm` run of this document's own tree with `gpt-4o-mini`, cross-checked edge-by-edge against an independent second model, found 153/613 genuine conflicts (both models committed and disagreed), 60 concentrated in five ids reused as generic fixture data (`R-01` 36/57, `C-01` 7/34, `R-07` 6/7, `C-06` 6/7, `C-03` 5/12) but 93/496 (18.8%) still conflicting once those are excluded; three non-`R-01` conflicts read in full all showed a test citing an id as placeholder data while proving something else, with neither its own docstring nor any comment naming that id. Changes: C-14 the DECLARED/INCIDENTAL rule — a citation is DECLARED when a citation line of it lies inside the citing test case's own docstring or is a whole-line comment (Python: `#`; Swift: the adapter's existing doc-comment-line recognition, reused rather than duplicated — D-27), INCIDENTAL otherwise, always INCIDENTAL for a `"src"`-kind or file-level citation (E-56); C-03 `Citation.declared`; C-15 `JudgeRequest.declared` (read-only context; no coercion rule reads it — D-26) and `C-10`'s instruction text gains the field and a skepticism rule for `declared: false` (advisory only, D-26); C-16 / C-07 `tests[].declared` and `metrics.declared_ratio` after `unknown_rate`, present under every `--judge` mode including `none`, `schema_version` `"1.5"`; §9's preamble sentence now names what `declared` mechanically checks; I-014 extends I-002's determinism guarantee; R-39; §9.2 T-85; §9.6 T-88; §9.8 T-86; §9.11 T-87 (recorded: re-running the three real conflicting edges under the new `C-10` text); §11 rows; §12 D-26, D-27. Statuses, the mock judge, `--judge` coercion rules (K-15, E-48, E-49), I-004, I-005, and the Markdown report are unchanged. |
| v1.15 | Jev pre-triage (`PROPOSAL_v1.16_jev_pre_triage.md`, 2026-09-20; D-29..D-32 confirmed). Evidence: a real `check --judge llm --strict` run of this document's own tree with `openai/gpt-4o-mini`, cross-checked edge-by-edge against `typesafe/jev-1.13` the way `JUDGE_CROSSCHECK_REPORT.md` already does — 656 judge-eligible edges, 582 the real judge committed to — shows Jev's top-choice probability is a monotonic triage signal (agreement with the real judge 279/295 = 94.58% at $p \geq 0.95$, 62/79 = 78.48% at 0.80–0.95, 53/97 = 54.64% at 0.60–0.80, 53/111 = 47.75% below 0.60), and that 51.5% of all eligible edges already sit at $\geq 0.95$ (41.2% at $\geq 0.99$) — headroom a truncated run was losing to declaration order. Changes: K-16 the triage pass (`--jev-pre-triage`: one task per eligible edge, C-17's request shape, at `--judge-concurrency`, before any real-judge request; ascending-confidence issue order, ties by C-07's id order; a per-edge failure first, with a Note; the D-30 Note under an unlimited budget); C-17 the Jev provider contract (four `SPECCHECK_JEV_*` variables, the `{model, state, questions}` body with the pinned `state` template and criteria, the `answers.verdict` response path, $p(e) := \max \mathrm{probabilities}$, the USABLE rule, and the ordering); K-12 amended — `--judge-budget` grows the `N%` form ($\lceil N/100 \times E \rceil$ of $E$ eligible edges, least-confident first; `0%` a pure triage dry run, `100%` all edges), the `SECONDS` form unchanged; I-015 Jev stays advisory (no `Verdict`, no report field, I-010 unchanged); E-58 (`N%` without a running triage → exit `2`), E-59 (per-edge Jev failure → first + Note, `judge_available`/`unknown_rate` untouched); E-35 and E-36 extended to both budget forms and to the triage pass; §3.1's stage table and §3.2 gain the pass, C-11's clock rule covers the `N%` form, §5.1 gains the flag and the `SECONDS\|N%` grammar, §10 names C-17, O-1 covers the provider; T-89 (triage + `N%` + C-17 request shape), T-90 (E-58/E-21 messages), T-91 *(recorded)* (the §1 calibration re-measured and its buckets recorded); §11 rows; §12 D-29..D-32. `speccheck.json`, `schema_version` `"1.5"`, every status, the mock judge, the C-10 text, and both reports are unchanged. |
| v1.16 | Obligation-aware judge (`PROPOSAL_v1.14_obligation_aware_judge.md`, 2026-09-20; D-28 and its sub-decision D-28b confirmed). Evidence: `JUDGE_CROSSCHECK_REPORT.md` §2b flagged that a test can cite an id as placeholder data while asserting something about a *neighbouring* id it names; a statement's C-12 `depends_on` neighbourhood — the ids it names and that name it — is the context a judge needs to tell its own clause apart from a neighbour's, at a cost of roughly doubling the per-edge judge input, which is cents against the per-edge real judge and the one pass a `--judge llm` run already makes. Changes: R-38 the request carries `related` — the C-12 `depends_on` neighbourhood, both directions, the statement's own references first, at most eight total, each a whitespace-collapsed title of at most 160 characters, a retired neighbour tagged `(retired)` (E-57), the empty list when the id has no neighbour; C-06 `JudgeRequest` gains `related` as a request-side, non-report field (no C-06 coercion rule reads it, so C-16, C-07 and C-08 are unchanged); C-10 gains the field and its rule (an assertion corresponding only to a related obligation is not evidence this statement holds; advisory, no model coercion — D-28's stance extends D-26's); C-17's triage `state` gains a `Related obligations:` section built from the same neighbourhood (D-28b — include, not strip, so Jev ranks the exact request the real judge gets, at roughly double the per-edge triage input); E-57 a retired `related` neighbour keeps its `(retired)` title; §11 rows; §12 D-28 (with D-28b). `related` is never a status, a metric, or a JSON field, so `speccheck.json`, `schema_version` `"1.5"`, the Markdown report, every status, the mock judge, and both reports are unchanged; the C-10 text changed, so `judge_prompt_sha256` is re-pinned by the build (F-004). §9 gains T-83 and T-84 *(recorded)*; T-89 (triage) and T-76 (the label fixture, now ≥ 37 entries, ≥ 8 downgraded on an adjacent edge — the build of this version found the row's `UNRELATED` too narrow: C-10's vocabulary grades a test that runs the statement's code and asserts a neighbour's fact `EXECUTES_ONLY`, F-1) are amended for the `related` section and the adjacent subset. The reservation that held D-28/E-57/R-38 in v1.15 is discharged (§12 note). |
| v1.17 | `speccheck explain <ID>` (`PROPOSAL_v1.17_explain_id.md`, 2026-09-20; D-33..D-36 confirmed, all four on the proposal's recommended branch). Evidence: this is a capability addition, not a defect fix — the tool already computes every fact a reader wants about one id, but a human assembles the trail by hand across `speccheck.json`, the cited source lines and an `impact` run (three structured artifacts plus two greps); §0's own promise is a path to the evidence, and the path was not rendered as one thing. Changes: R-40 the third subcommand runs `check`'s stages and renders one id; C-18 the stdout contract (section order, headings, the C-05 reason per status, the outcome/verdict line, the `clause:`/`rationale:` lines, the `impact (<depth>):` section from C-12's `walk` and C-13's `reverify`, and the exit codes `0`/`2`/`3`); I-016 `explain` is additive and read-only (no report, no new judge call, statuses agree with `check`); E-60 an undeclared id is exit `2` while a declared-but-uncited one renders its reason and exits `0`; E-61 `--judge` carries over `check`'s contract verbatim; §3.1 gains the surface's paragraph, §3.3 records that it writes no durable artifact (D-33), §5.1 gains the synopsis line and the `explain`/`--depth` rows, §5.4 its exit codes; §9.13 gains T-92 (the golden trace and its byte-stability), T-93 (E-60, the retired id, the uncited id) and T-94 *(recorded)* (the live-LLM trace); §11 rows; §12 D-33..D-36. No status, verdict, citation, metric, `schema_version`, `check`/`impact` report or golden moves. |
| v1.18 | The CLI documents its own parameters and environment (`PROPOSAL_v1.18_cli_help_contract.md`, 2026-09-20; D-37..D-42 confirmed on the recommended branches — D-42's branch adapted, because its preferred landing (the uncommitted v1.16 fold) no longer existed once v1.16 and v1.17 shipped). Evidence: `check --help` rendered 755 bytes of flag names and argparse dest names with no help text at all (14 `check` flags and 9 `impact` flags, 0 with help; `grep -c "choices=" src/speccheck/cli.py` = 0), the only machine-readable statement of a flag's values was its usage error, the environment was stated on five surfaces and one of them was wrong (C-06's `SPECCHECK_LLMMODEL`, read by no code), and the one surface that *was* documented had already drifted — six README statements still said `DIR` two versions after D-23 made `--src`/`--tests` PATHS. Changes: R-41 every flag documents purpose, values, default and preconditions, plus the environment, the exit codes and the summary line; C-19 the entry order, the metavar vocabulary, the `environment:` block and the exit-code epilog; I-017 `--help` is inert; T-95 the help↔usage-error token equality and the acceptance round-trip; T-96 every definition carries help and a C-19 metavar, and the screens render inertly; T-97 the byte-pinned goldens at `COLUMNS=80`; T-98 the environment block is bound to the code's own `SPECCHECK_*` literals; §5.1 and §5.4 gain their pointers; §9.14 the new test group; §10 the help goldens; §11 rows; §12 D-37..D-42; C-06's variable name corrected. No accepted value, default, exit code, report byte or golden moves. |
