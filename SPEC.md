# SPECIFICATION — Specification Conformance Checker (`speccheck`; traceability graph, JUnit results, model-judged test strength; Python 3.12 + uv)

> - **Status:** v1.3 — v1.2 plus a judge-stage progress indicator for `--judge llm` (R-30, C-11, K-13, E-39, E-40, T-62, T-63, D-15): the LLM judge takes minutes, and an operator at a terminal MUST be able to see how far along it is without turning on `--verbose`. v1.2 was v1.1 with D-07 partly resolved by the first T-49 runs: `max_tokens` raised from 400 to 4000 (C-06, T-33) so thinking models can finish the verdict JSON inside the budget; the remaining §12 rows marked `confirm` are still decisions the build inherits from the author, not the requester
> - **Language / stack:** Python 3.12 | standard library for the deterministic kernel (`re`, `ast`, `xml.etree`, `json`, `argparse`, `pathlib`) | CLI only; optional model-backed judge behind an `[llm]` extra
> - **Sources:** `one_sentence_prompt.md` (the brief); `../skills/spec-writing/SKILL.md` (the ID taxonomy and `SPEC.md` shape the checker consumes); `../skills/spec-build/SKILL.md` §Phase 3 (the manual conformance audit this tool automates); `../skills/spec-review/SKILL.md` §3.17 (the intent → requirement → contract → invariant → test → evidence chain); `../outline.md` Chapters 15–18 (where this system is the worked example); `SPEC_REVIEW_REPORT.md` (review of v0.1; F-001..F-017 below point at it); `FINAL_SPEC_REVIEW_REPORT.md` (review of v0.4; F-101..F-110 below point at it); `SPEC_v0.5_REVIEW_REPORT_by_QWEN.md` (independent review of v0.5 by a second model; its F-001..F-011 are cited below as Q-001..Q-011 to avoid collision)
> - **Scope of this document:** The deterministic conformance kernel (spec-ID extraction, citation graph, test-result mapping, status computation, reporting) and the contract around the optional model-backed *judge*. It does not specify the quality of the specification under check (`spec-review` owns that), does not specify how tests are run (results are consumed, not produced), and does not specify any semantic analysis of source code.
> - **Normative language:** MUST/MUST NOT/SHALL/SHALL NOT = normative; SHOULD = strong recommendation; MAY = optional.
> - **Principle:** *The model may only ever make the news worse.* Every status is computed deterministically from evidence the operator can `grep`; the judge is permitted to downgrade a status with cited evidence, never to upgrade one, and every claim in the report points at a file and line.

---

## 0. Intent and purpose

`speccheck` answers one question about a project: **for every ID the specification declares, what evidence exists that the implementation realizes it?** It reads a `SPEC.md` written in the house ID taxonomy (R-nn requirements, C-nn contracts, I-nnn invariants, K-nn constraints, E-nn edge cases, T-nn tests), finds where each ID is cited in the source and test trees, joins those citations to the outcomes in a JUnit XML results file, and writes a conformance report in which every ID has exactly one status and every status has traceable evidence.

This is Phase 3 of `spec-build` ("re-read the spec and audit every artifact") made mechanical. Humans doing that audit are slow and get tired; agents doing it are fast and confabulate. The design splits the work accordingly:

- The **deterministic kernel** does everything that can be done by pattern, graph, and arithmetic: which IDs exist, which are cited where, which tests ran and how they ended, what that makes each ID's status, and what the coverage ratios are. Two runs on identical inputs produce byte-identical reports.
- The **judge** — a model-backed component, off by default — answers exactly one question per (test case, ID) edge: *does this test assert the observable behavior this ID describes, or does it merely execute code near it?* Its answer MUST cite lines inside the test; an answer without valid evidence is discarded as `UNKNOWN`. The judge can turn a `PASSING` into a `WEAKLY_PASSING`; it can never turn anything into `PASSING`.

**Why this boundary (context the implementer should not re-derive):** a checker that lets a model decide conformance has merely moved the vibe-coding problem one level up — the report becomes something to trust rather than something to verify. Keeping the model on the downgrade-only side of the line means a green report is as trustworthy as `grep` plus the test runner, and a yellow one carries a reason you can click on.

**Non-goals (explicit, to constrain the solution space):**

- No semantic analysis of source code — no type inference, control-flow, or "does this function implement R-07" reasoning, by the kernel *or* the judge. Source citations are literal token matches.
- No test execution. The checker consumes a results file; it never runs `pytest`, `go test`, or anything else.
- No spec-quality review (ambiguity, contradictions, missing sections). That is `spec-review`.
- No remediation. The checker reports; it never edits the spec, the code, or the tests.
- No multi-repository or multi-spec runs; one spec, one source tree set, one results file per invocation.
- No IDE integration, daemon mode, watch mode, or web UI.
- No language adapters beyond Python in v0.1 (see O-2); other languages get file-level attribution.
- The checker never reads its own outputs as inputs: the spec, the results file, and the two report files are excluded from every scan (C-03, F-002).

**A known limitation, stated rather than hidden (F-013):** citation is literal. A test that mentions `R-03` as *data* — asserting on a report that contains it, or on an error message — cites R-03 exactly as a test that proves it does. The `speccheck:ignore` markers in C-01 are the opt-out; they are the author's responsibility, and `speccheck` never infers intent from context.

**Relationship to the skills:** `spec-writing` produces the input; `spec-review` grades it; `spec-build` builds from it and, in Phase 3, does by hand what this tool does by machine. The report this tool writes is intended to be pasted into `SPEC_BUILD_REPORT.md` as the per-ID evidence table.

---

## 1. Actors and goals

| Actor | Goals |
| ----- | ----- |
| **Operator** (human at a terminal, or a CI job) | Run one command against a project and get a report plus an exit code that can gate a merge. Never has to trust a number without a path to its evidence. |
| **Extractor** (`speccheck/extract.py`) | Turn `SPEC.md` into the set of declared IDs (with statement text, family, retired flag) and turn source/test files into citations, deterministically. |
| **Attributor** (`speccheck/attribute.py`) | Map each citation in a test file to the test case that contains it (Python adapter), falling back to file-level attribution for anything it cannot parse. |
| **Results Mapper** (`speccheck/results.py`) | Read a JUnit XML file and join each `<testcase>` to an attributed test case, yielding outcomes per test case. |
| **Grapher** (`speccheck/graph.py`) | Build the ID → source-file / ID → test-case edge sets and compute each ID's deterministic status and the coverage metrics. |
| **Judge** (`speccheck/judge.py`; providers `judge_mock.py`, `judge_llm.py`) | For each (test case, ID) edge of a `PASSING` ID, return a verdict with evidence lines; the mock provider is deterministic, the LLM provider is opt-in. Single-principal: the judge sees one edge at a time and holds no state across calls. |
| **Reporter** (`speccheck/report.py`) | Render the Markdown and JSON reports from the graph and judge results, in a fixed order, with no content that varies between identical runs. |
| **CLI** (`speccheck/cli.py`, entry point `speccheck`) | The only surface. Parse arguments, wire the pipeline, apply the exit-code and verbosity contracts. |

---

## 2. Requirements (intent, high level)

| ID | Statement | Source |
| -- | --------- | ------ |
| **R-01** | The checker MUST read a Markdown specification and extract every *declared* spec ID together with its family and statement text, per the grammar in C-01. | prompt; spec-writing §ID taxonomy |
| **R-02** | The checker MUST recognize a declared ID as *retired* when its declaration is struck through (`~~R-07~~`), and MUST exclude retired IDs from coverage denominators. | spec-writing §ID taxonomy ("retire old ones with a strike-through") |
| **R-03** | The checker MUST scan every text file under each `--src` root, except the files C-03 excludes, and record a *source citation* for each (file, ID) pair where the ID token occurs, per C-03. | prompt ("analyzes an implementation") |
| **R-04** | The checker MUST scan every text file under each `--tests` root, except the files C-03 excludes, and record a *test citation* for each (test case, ID) pair, attributing the citation to the enclosing test case when the file's language adapter can delimit test cases, and to the file otherwise. | prompt ("and its tests") |
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

---

## 3. Behavior and state model

### 3.1 Lifecycle

A run is a single, stateless pipeline. There is no persistent state between runs, no cache, and no partial-output mode: either both report files are written or neither is. The Reporter guarantees this by rendering both documents in memory, then, in this order (F-106): (1) delete any leftover `<out>/.speccheck.json.*.tmp` and `<out>/.SPEC_CONFORMANCE_REPORT.md.*.tmp` from earlier runs; (2) write `.speccheck.json.<nonce>.tmp` and `.SPEC_CONFORMANCE_REPORT.md.<nonce>.tmp`, where `<nonce>` is 8 random hex digits chosen per run (F-103); (3) rename the JSON temporary to `speccheck.json`; (4) rename the Markdown temporary to `SPEC_CONFORMANCE_REPORT.md`. If any step fails, every temporary and any file this run already renamed is removed before exit `3` (F-015). The nonce never appears in either report, so I-002 is unaffected.

| Stage | Owner | Input | Output | Fails with |
| ----- | ----- | ----- | ------ | ---------- |
| parse-args | CLI | argv, env | `Config` | exit `2` |
| extract-spec | Extractor | `SPEC.md` | `SpecIndex` (C-02) | exit `3` (E-01, E-02, E-03) |
| scan-src | Extractor | `--src` roots minus C-03 exclusions | `Citation[]` (C-03) | never (E-10, E-11 are notes) |
| scan-tests + attribute | Extractor, Attributor | `--tests` roots | `TestCase[]`, `Citation[]` | never (E-12 is a note) |
| map-results | Results Mapper | `--results` | `Outcome[]` (C-04) | exit `3` (E-05) |
| graph + status | Grapher | all of the above | `IdRecord[]` with deterministic status; dangling/stale lists; metrics | never |
| judge (optional) | Judge | `PASSING` edges | `Verdict[]` (C-06); progress indicator on stderr while running (R-30, C-11) | never (E-14..E-17 yield `UNKNOWN`) |
| report | Reporter | everything | `SPEC_CONFORMANCE_REPORT.md`, `speccheck.json` | exit `3` if `--out` unwritable |
| exit | CLI | JSON report, `--strict` | exit code (§5.4), summary line | — |

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

### 3.3 Durable artifacts

| Artifact | Written to | Version | Shape |
| -------- | ---------- | ------- | ----- |
| `SPEC_CONFORMANCE_REPORT.md` | `--out` (default `.`) | mirrors JSON `schema_version` | C-08 |
| `speccheck.json` | `--out` | `schema_version: "1.0"` | C-07 |

Both files are overwritten on every successful run, via the temp-and-rename sequence in §3.1. No other file is ever written, and no temporary survives a run (I-001).

---

## 4. Interfaces / contracts

### C-01 Spec ID grammar, declaration, citation, retirement

```text
ID        := FAMILY "-" DIGITS
FAMILY    := "R" | "C" | "I" | "K" | "E" | "T"          # O-n, D-nn and F-nnn are NOT conformance IDs
DIGITS    := [0-9]{1,3}
TOKEN     := ID bounded by non-alphanumerics on both sides   # regex: (?<![A-Za-z0-9])([RCIKET])-([0-9]{1,3})(?![A-Za-z0-9])

Declaration (in SPEC.md only) — an ID is DECLARED when, outside fenced code blocks,
either form occurs (F-009). A fenced code block (F-108) opens at a line whose first non-space
characters are three backticks (U+0060 x3) or three tildes (~~~), optionally followed by an info
string, and closes at the next line whose first non-space characters are the same three-character
marker — the same character as the opener — followed by nothing but whitespace; a closing line's
info string is not permitted, a backtick fence is never closed by tildes nor a tilde fence by
backticks, and an unclosed fence runs to end of file (Q-008).
  (a) table row:    | **R-07** | <statement> | ...
        row       := a line whose first non-space character is "|"
        cells     := the row split on every "|" that is not preceded by "\" and not inside a
                     backtick span (`...`); the leading and trailing empty cells are dropped
        the ID MUST be the ENTIRE trimmed content of the FIRST cell, in one of the forms
          **ID**   ~~**ID**~~   **~~ID~~**
        statement := the trimmed text of the SECOND cell ("" if there is none)
        A bold ID in any other cell is not a declaration (E-31). A separator row (cells made of
        "-" and ":" only) is never a declaration.
  (b) heading:      ### C-03 <statement>
        the ID token (optionally wrapped ~~ ~~) MUST be the first token after the "#" run;
        statement := the rest of the heading text, trimmed. "### 9.1 Extraction (C-01, C-02)"
        declares nothing.
  A SECOND declaration of the same ID is E-02 (exit 3); the message names the ID and both lines.
  Nothing "wins": the run produces no report (Q-006).

Retirement — a declaration whose ID token is wrapped in ~~ ~~ :
  | ~~**R-07**~~ | ... |   or   | **~~R-07~~** | ...   or   ### ~~C-03~~ ...
  A retired ID is DECLARED and RETIRED. Retirement is not un-done by a later plain declaration (E-03).

Citation (in --src / --tests files) — every TOKEN occurrence in a text file is a citation,
  regardless of comments, strings, or code. Fenced code blocks are NOT excluded in source files
  (only in SPEC.md). ID numbers are compared numerically: R-7 and R-07 and R-007 are the same ID.

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
  `in_scope` and `conformance`.
```

### C-02 `SpecIndex`

```python
@dataclass(frozen=True)
class SpecId:
    family: str          # one of "R","C","I","K","E","T"
    number: int          # 0..999
    text: str            # statement (table cell or heading remainder), whitespace-collapsed, may be ""
    line: int            # 1-based line of the declaration in SPEC.md
    retired: bool

@dataclass(frozen=True)
class SpecIndex:
    path: str                       # relative, POSIX
    ids: tuple[SpecId, ...]         # sorted by (family order R,C,I,K,E,T ; number)
    # invariant: no two SpecId share (family, number)
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
Fallback adapter (any other text file): one file-level case per file; its classname is derived
  exactly as for Python (path relative to --root, "/" -> ".", final extension dropped; F-108).

Text vs binary (F-008): a file is BINARY if any of its first 8192 bytes is 0x00. Binary files are
  skipped silently (no Note, no citations, no test case). Everything else is text and is decoded
  as UTF-8 with errors="replace" (E-11). Symbolic links — to files or to directories — ENCOUNTERED
  DURING DESCENT are never followed (K-03); one Note per run if any were skipped (E-30). A path
  given on the command line (--spec, --src, --tests, --results, --out, --root) is resolved once,
  checked against --root (E-09), and then used in its resolved form: a symlinked --src root is
  descended, and it is not counted as a skipped symlink (Q-007).

Excluded from every scan (F-002), whether or not they lie under a --src/--tests root, and
  whether or not they exist yet: the file named by --spec, the file named by --results,
  <out>/SPEC_CONFORMANCE_REPORT.md, <out>/speccheck.json, and every file directly under <out>
  whose name starts with ".speccheck.json." or ".SPEC_CONFORMANCE_REPORT.md." and ends with
  ".tmp" (the §3.1 temporaries, including leftovers from a killed run; F-103). Exclusion is by
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
    join_name := if name ends with "]" and contains "[":  name[:name.index("[")]
                 else:                                     name
                 i.e. everything from the FIRST "[" to the end is removed, whatever it contains
                 (F-005, F-101): "test_x[3-True]" -> "test_x"; "test_x[list[int]]" -> "test_x";
                 "test_y[a][b]" -> "test_y".
    param     := the removed text without its outer brackets ("3-True", "list[int]", "a][b"), or null.
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
  5. (judge enabled only) if status == PASSING:
       V := verdicts for edges (t, x), t in T with outcome passed
       if V is non-empty and no v in V is ASSERTS and some v in V is EXECUTES_ONLY or UNRELATED
                                                      -> WEAKLY_PASSING
       else                                           -> PASSING   (UNKNOWN never changes status)

Cases in T without an outcome are reported as "unrun" for x and ignored in step 4.
The judge is never consulted for edges whose ID is not PASSING after step 4 (I-010).
Step 5 is the ONLY place verdicts influence anything: an ID with verdicts {ASSERTS, EXECUTES_ONLY}
  is PASSING, and PASSING is what --strict tests (R-15, §5.4; F-003). There is no per-edge rule
  anywhere else in this document.
```

### C-06 Judge interface

```python
@dataclass(frozen=True)
class JudgeRequest:
    id: str                 # "R-07"
    statement: str          # SpecId.text
    testcase: TestCase
    source: str             # lines testcase.start..testcase.end, each prefixed "<lineno>\t" (F-109)

@dataclass(frozen=True)
class Evidence:
    file: str
    line: int               # MUST satisfy testcase.start <= line <= testcase.end

@dataclass(frozen=True)
class Verdict:
    verdict: str            # "ASSERTS" | "EXECUTES_ONLY" | "UNRELATED" | "UNKNOWN"
    evidence: tuple[Evidence, ...]
    rationale: str          # <= 280 characters, single line

class Judge(Protocol):
    def judge(self, req: JudgeRequest) -> Verdict: ...
```

```text
Validation applied by the kernel to EVERY provider's raw answer (judge.py, not the provider):
  * verdict not in the four-value set                          -> UNKNOWN
  * verdict == ASSERTS and evidence is empty                    -> UNKNOWN
  * any evidence.file != testcase.file, or line outside span    -> UNKNOWN
  * rationale longer than 280 chars                             -> truncated to 277 + "..."
  * provider raised, timed out (K-05), or returned non-JSON     -> UNKNOWN, rationale = "judge: <class of failure>"
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
                  { "role": "user",   "content": <JSON object {id, statement, file, start, end, source}, K-09 formatting;
                                                     source = the span with every line prefixed by its absolute
                                                     1-based line number and one TAB (F-109)> } ] }
  Response: HTTP 200 with a JSON body; the model's text is read from  choices[0].message.content .
            Any other status, a non-JSON body, or a missing path -> E-14 / E-15.
            The text is stripped of surrounding whitespace and of ONE enclosing ``` or ```json fence
            if present, then MUST parse as a single JSON object {verdict, evidence:[{file,line}],
            rationale}; anything else is non-JSON (-> UNKNOWN, E-15).
  Exactly one HTTP request per edge; no retries (K-06). The SHA-256 of the C-10 text as sent is
  recorded in the report as `judge_prompt_sha256` (C-07).

Mock provider (judge_mock.py):
  verdict = ASSERTS if the span contains an assertion token, else EXECUTES_ONLY
  assertion token := a line matching ^\s*assert\b  or containing  .assert  or  pytest.raises(
  evidence = every such line (file, line); rationale = "mock: assertion token on N line(s)" / "mock: no assertion token"
```

### C-07 JSON report (`speccheck.json`, `schema_version` "1.0")

```json
{
  "schema_version": "1.0",
  "spec": "SPEC.md",
  "judge": "none | mock | llm",
  "judge_available": null,
  "judge_prompt_sha256": "<64 hex chars; present only when judge == llm>",
  "strict": false,
  "max_unknown": 0.2,
  "strict_judge_failure": null,
  "ids": [
    {
      "id": "R-07",
      "family": "R",
      "statement": "…",
      "line": 88,
      "status": "PASSING",
      "src": [ {"file": "src/pkg/core.py", "lines": [12, 40]} ],
      "tests": [
        {
          "file": "tests/test_core.py", "name": "test_zero_rate", "classname": "tests.test_core",
          "lines": [17], "outcome": "passed",
          "results": [ {"name": "test_zero_rate[0]", "param": "0", "outcome": "passed"},
                       {"name": "test_zero_rate[1]", "param": "1", "outcome": "passed"} ],
          "verdict": {"verdict": "ASSERTS", "evidence": [{"file": "tests/test_core.py", "line": 21}],
                      "rationale": "…", "coerced": false}   // null when the case was not judged (Q-001)
        }
      ],
      "unrun": [ {"file": "…", "name": "…"} ]
    }
  ],
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
    "unknown_rate": 0.0
  },
  "exit_code": 1
}
```

```text
Rules: keys emitted in exactly this order (`judge_prompt_sha256` omitted entirely unless judge == llm;
  `max_unknown` always present, echoing K-11; `strict_judge_failure` is null, "unavailable", or
  "unknown_rate" and is non-null only when R-28 forced exit 1 — when BOTH reasons hold,
  "unavailable" is recorded, since a fully unavailable judge makes the unknown rate vacuous; Q-004);
  `ids` sorted by (family order R,C,I,K,E,T ; number); `results` sorted by name;
  `src`/`tests`/`dangling`/`stale`/`unattributed_results` sorted by (file, line) then name;
  `notes` is a list of strings sorted ascending by Unicode code point (each Note's text is fixed by
  the E-case that produces it, so this order is total and reproducible; Q-002);
  `lines` ascending, unique. No timestamps, hostnames, absolute paths, durations, or version
  strings other than schema_version (R-16).
Verdict field (Q-001): every `tests[]` entry has the key `verdict`. It is a verdict object when
  the case was judged (judge enabled, ID `PASSING` after C-05 step 4, outcome `passed`) and `null`
  otherwise — including every entry under `--judge none`. The key is never omitted.
Names (Q-011): `tests[].name` is the `TestCase.name` — `""` for a file-level case. `(file)` is a
  Markdown-only rendering (C-08) and never appears in the JSON. R-13's "contains everything"
  concerns data; a rendering label is not data.
Numbers (Q-009): every ratio is computed as Decimal(numerator) / Decimal(denominator) under a
  28-digit context and quantized to 4 places with ROUND_HALF_EVEN; it is emitted as a JSON number
  with exactly four decimal places (0.9000, not 0.9), so the JSON text is byte-determined without
  reference to binary floating point. K-11 compares these quantized values. `<pct>` in the summary
  line is the quantized `conformance` times 100, quantized to 1 place with ROUND_HALF_EVEN.
Metrics:
  conformance        = |PASSING| / in_scope                       (WEAKLY_PASSING is NOT passing)
  by_family[f].ratio = |PASSING in f| / |in_scope in f|
  judge_strength     = |PASSING| / (|PASSING| + |WEAKLY_PASSING|)   (judge enabled only; else absent)
  unknown_rate       = |edges with verdict UNKNOWN| / |judged edges| (judge enabled only; else absent)
Zero denominators: ratio = null (JSON) / "n/a" (Markdown); the "a/b" string is still emitted ("0/0").
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

## 1. Verdict
<one line: the §5.1 summary line, verbatim>

## 2. Metrics
| Metric | Value |            # conformance a/b (0.xxxx); by-status counts; per-family table;
                               # judge_strength and unknown_rate rows only when judge enabled

## 3. Per-ID evidence
| ID | Status | Statement | Source citations | Test citations (outcome · verdict) |
# one row per declared ID in C-07 order; RETIRED rows included, with the ID cell (only) struck through: `~~R-07~~`;
# citations rendered as `file:line`; verdict rendered as ASSERTS / EXECUTES_ONLY / UNRELATED / UNKNOWN(coerced),
# or as an em dash (—) when the JSON `verdict` is null (Q-001); a file-level case is rendered with the
# label `(file)` in place of its empty name (Q-011)

## 4. Dangling citations      # table or "None."
## 5. Stale citations         # table or "None."
## 6. Unattributed results    # table or "None."
## 7. Unrun test citations    # table (ID, file, name) or "None."
## 8. Judge details           # present only when judge enabled: one row per judged edge (verdict non-null) with rationale
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

The file `speccheck/judge_prompt.md` is shipped as package data and its content is exactly the text below (trailing newline, `\n` line endings). It is sent verbatim as the system message (C-06). Changing it is a spec change: bump this document's version and the file together.

```text
You are a test-strength judge for a specification conformance checker.

You will receive one JSON object with these fields:
  id        - a specification ID, e.g. "R-07"
  statement - the normative text of that ID
  file      - the path of one test file
  start     - the first line number of one test case in that file
  end       - the last line number of that test case (inclusive)
  source    - the text of lines start..end, one line per source line, each line prefixed by its
              absolute line number and a tab (e.g. "17<TAB>assert x == 2"); cite those numbers

Answer exactly one question: does this test case ASSERT the observable behavior described by
the statement, or does it merely execute code near it?

Reply with one JSON object and nothing else - no prose, no markdown fence:
  {"verdict": <VERDICT>, "evidence": [{"file": <file>, "line": <n>}, ...], "rationale": <text>}

VERDICT is exactly one of:
  "ASSERTS"       - the test contains at least one assertion (assert statement, assertion method,
                    expected-exception context, or equivalent) whose expected value or condition
                    corresponds to what the statement requires. You MUST list every such assertion
                    line in evidence.
  "EXECUTES_ONLY" - the test runs code related to the statement but no assertion checks the
                    behavior the statement requires (assertions absent, trivial, or unrelated).
  "UNRELATED"     - the test does not exercise the behavior the statement describes at all.
  "UNKNOWN"       - you cannot decide from the source given. Prefer UNKNOWN over guessing.

Rules:
  - Every evidence line number MUST be between start and end inclusive, in the given file.
  - Cite only lines that exist in source. Do not invent lines.
  - rationale is one sentence, at most 280 characters.
  - Judge only the given test case. Do not assume what other tests do.
  - A test that mentions the ID in a comment or string is not evidence of asserting it.
```

### C-11 Judge progress indicator (R-30)

The indicator is one physical line on stderr, redrawn in place. It is written directly to the
stderr stream, **not** through the `speccheck` logger, so the §5.3 logging level is unaffected
and the line never carries a level prefix. Every write is one of the two byte sequences below:

```text
draw:   "\r" + <line> + "\x1b[K"          # carriage return, the line, erase to end of line
erase:  "\r" + "\x1b[K"                   # what remains on stderr after the judge stage is nothing

<line> ::= "judge: [" <bar> "] " <done> "/" <total> " edges  " <elapsed> " elapsed  ~" <left> " left"
<bar>     exactly 20 cells: k times "#" followed by (20 - k) times "-"
<done>    decimal integer, edges whose verdict is determined (received, coerced to UNKNOWN, or budget-skipped)
<total>   decimal integer, number of eligible edges (I-010)
<elapsed> M:SS  (minutes without upper bound, seconds zero-padded to two digits)
<left>    M:SS, or "?:??" while done == 0

Regex <line> MUST match (T-62):
^judge: \[[#-]{20}\] \d+/\d+ edges  \d+:\d{2} elapsed  ~(\d+:\d{2}|\?:\?\?) left$
```

With $n$ the number of eligible edges, $d$ the number determined so far, and $t$ the wall-clock
seconds since the judge stage started (the same origin as K-12: the moment the first request is
issued), the filled cell count and the estimate of time remaining are

$$
\begin{aligned}
k &= \left\lfloor \frac{20\,d}{n} \right\rfloor \\
\mathrm{left} &= \frac{t}{d}\,(n - d) \quad \text{for } d > 0
\end{aligned}
$$

`left` is undefined (rendered `?:??`) while $d = 0$; the line is never drawn when $n = 0$
(E-36: no request is sent). Both durations are floored to whole seconds before rendering, with
$M = \lfloor s / 60 \rfloor$ and $\mathrm{SS} = s \bmod 60$. The line is pure ASCII (the cells are
`#` and `-`, never Unicode block characters) so it renders under any locale (R-29 rationale). It
carries no file name, statement text, prompt, response, or key (I-007). When $d = n$ the last
draw shows a full bar, and the erase follows immediately.

---

## 5. Interface specification

### 5.1 CLI (`speccheck`), the only surface

```text
speccheck check --spec SPEC.md [--src DIR]... [--tests DIR]... [--results junit.xml]
                [--root DIR] [--out DIR] [--judge none|mock|llm] [--strict]
                [--judge-concurrency N] [--judge-budget SECONDS] [--max-unknown FRACTION]
                [--progress auto|always|never] [--verbose [INFO|DEBUG]]
speccheck --self-check [--verbose [INFO|DEBUG]]
speccheck --version
speccheck --help
```

| Subcommand / flag | Behavior | Exit |
| ------ | ---------------- | --- |
| `check` | Run the §3.1 pipeline; write both reports; print the summary line. | `0` conforming, `1` not, `2` usage, `3` input contract |
| `--spec FILE` | Required. Path to the specification; decoded as UTF-8 with `errors="replace"` (a Note is recorded if any byte was replaced). Missing flag or unreadable file → usage error. | `2` |
| `--src DIR` | Repeatable; default `src` if it exists, else none. Non-directory → usage error. | `2` |
| `--tests DIR` | Repeatable; default `tests` if it exists, else none. Non-directory → usage error. | `2` |
| `--results FILE` | Optional JUnit XML. Absent → every cited ID is at most `UNVERIFIED`. Unreadable → usage error; malformed → E-05. | `2` / `3` |
| `--root DIR` | Base for relative paths in reports; default `.`. All of `--spec/--src/--tests/--results/--out` MUST resolve inside it (E-09). | `2` |
| `--out DIR` | Where the two reports go; default `.`. MUST resolve inside `--root` (E-09; F-002). Created if missing; not writable → E-18. | `2` / `3` |
| `--judge MODE` | `none` (default), `mock`, `llm`. Any other value → usage error. | `2` |
| `--strict` | Apply R-15 and, with `--judge llm`, R-28. | — |
| `--max-unknown FRACTION` | Threshold for R-28; default `0.2`; a float in `[0, 1]`, else usage error. Accepted with any judge mode; consulted only under `--strict --judge llm`. | `2` |
| `--judge-concurrency N` | K-06; default `4`, integer `1..32`, else usage error. Ignored unless `--judge llm`. | `2` |
| `--judge-budget SECONDS` | K-12; default `0` (unlimited), integer `0..86400`, else usage error. Ignored unless `--judge llm`. | `2` |
| `--progress MODE` | R-30, C-11. `auto` (default): draw the judge progress indicator iff `sys.stderr.isatty()` is true and verbosity is not `DEBUG`; `always`: draw it even when stderr is not a TTY (still suppressed under `--verbose DEBUG`, E-39); `never`: never draw it. Any other value → usage error. Ignored unless `--judge llm`. | `2` |
| `--verbose [LEVEL]` | §5.3. Bare = `INFO`. `LEVEL` other than `INFO`/`DEBUG` → usage error. | `2` |
| `--self-check` | Copy the packaged fixture `speccheck/_selfcheck/` (a byte-identical copy of the §9.8 golden fixture `fixtures/target/`, its `golden/` directory included; F-107) into a fresh temporary directory `<tmp>`; install a socket guard; then run, **in the same process**, exactly `check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --root <tmp> --out <tmp>/out` with the working directory set to `<tmp>` (Q-003). The inner check is **expected** to exit `1` (the fixture has planted defects) and that exit code is not the self-check's result; compare `<tmp>/out/speccheck.json` and `<tmp>/out/SPEC_CONFORMANCE_REPORT.md` to `<tmp>/golden/` byte-for-byte; remove `<tmp>`; print `self-check: ok` when both match, else one line naming the first mismatch or failure (F-011). | `0` / `1` |
| `--version` | Print `speccheck <semver>` and exit. | `0` |

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
- **Mechanism.** Python `logging` with a single stderr `StreamHandler`; logger name `speccheck`; format `%(levelname)s %(message)s`. Level is `ERROR` by default and `INFO`/`DEBUG` per flag, so nothing below ERROR reaches stderr without `--verbose` (F-014). The E-10..E-13 and E-27..E-30 Notes are logged at `INFO` (they are always in the report's Notes regardless of level); nothing is ever logged at `WARNING`; the exit-2/3 message is logged at `ERROR`.

### 5.4 Exit codes

| Code | Meaning | Reports written? |
| --- | ---------- | --- |
| `0` | `CONFORMING`: no in-scope ID is `FAILING`; and if `--strict`, every in-scope ID has status `PASSING`, `dangling` and `stale` are empty, and — with `--judge llm` only — `judge_available` is `true` and `unknown_rate` $\leq$ `max_unknown` (R-28). Beyond R-28, status is the only judge-related input (F-003). | yes |
| `1` | `NOT CONFORMING`: anything else the report can express | yes |
| `2` | Usage error (bad flag/value, missing required, path outside root, missing judge env) | no |
| `3` | Input contract violation (E-01, E-02, E-03, E-05, E-18) | no |

Any uncaught exception MUST also map to `3` with a one-line message; a traceback is printed only under `--verbose DEBUG`.

---

## 6. Invariants (must hold in every valid implementation)

| ID | Invariant |
| -- | --------- |
| **I-001** | **Read-only inputs.** No file under `--root` other than the two report files under `--out` — and the `--out` directory itself, if it did not exist — is created, modified, or deleted by a run, and no temporary of §3.1 survives a run; no file outside `--root` is written at all. Sole exception: `--self-check` creates, uses, and removes one fresh temporary directory (F-011); it writes nowhere else. |
| **I-002** | **Determinism.** For `--judge none` and `--judge mock`, identical inputs (bytes of every file read, argv, env) produce byte-identical report files and summary line, on any OS. |
| **I-003** | **Exactly-once reporting.** Every declared ID (retired included) appears exactly once in `ids` and exactly once in the Markdown per-ID table; no undeclared ID ever appears there. |
| **I-004** | **Downgrade-only judge.** For every ID, `status_with_judge` $\in$ `{status_without_judge}` $\cup$ (`{WEAKLY_PASSING}` iff `status_without_judge == PASSING`). Disabling the judge never changes any status except `WEAKLY_PASSING` → `PASSING`. |
| **I-005** | **Grounded verdicts.** Every non-`UNKNOWN` verdict in a report carries $\geq$ 0 evidence entries, every `ASSERTS` carries $\geq$ 1, and every evidence entry points to a line inside the judged test case's span in the judged file. |
| **I-006** | **Network boundary.** With `--judge none`/`mock`, no socket is opened for the lifetime of the process. |
| **I-007** | **Secret and payload hygiene.** The API key never appears in stdout, stderr, or either report. INFO never contains file contents, statements, prompts, or responses. |
| **I-008** | **Total metrics.** Every ratio is either a number in `[0, 1]` or `null`/`n/a`; no run raises on a zero denominator. |
| **I-009** | **Exit $\equiv$ report.** `exit_code` in `speccheck.json` equals the process exit status, and both are computable from the rest of the JSON plus `strict` by the §5.4 rule. |
| **I-010** | **One judge call per edge.** The judge is invoked at most once per (test case, ID) edge per run, and only for edges whose ID is `PASSING` after C-05 step 4 and whose test outcome is `passed`. |
| **I-011** | **Family-safe numbering.** ID normalization is injective within a family: `R-7`, `R-07`, `R-007` map to one ID; `R-07` and `C-07` never collide. |

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
| **K-12** | `--judge-budget SECONDS` (default `0` = unlimited; integer `0..86400`) bounds the wall-clock spent in the judge stage, measured from the first request issued. The deadline is `start + budget`. A request is *started* when it is issued; no request is issued at or after the deadline; requests in flight at the deadline are allowed to complete (each still bounded by K-05) and their verdicts count. Every edge not started before the deadline receives `UNKNOWN` with rationale `judge: budget` and `coerced: true`, and one Note records how many (F-110, Q-010). |
| **K-13** | The progress indicator (C-11) is drawn once when the judge stage starts (with $d = 0$), redrawn after every determined verdict, and redrawn at least once per second of wall-clock while any request is in flight so that `elapsed` and `left` keep moving; it SHOULD NOT be redrawn more than 10 times per second. The bar has exactly 20 cells. The indicator is erased exactly once, when the judge stage ends, before the `report` stage begins and before any INFO stage line, Note, error message, or the summary line is written. |
| **K-07** | `rationale` $\leq$ 280 characters after truncation; single line (newlines replaced by spaces). |
| **K-08** | Kernel performance, measured on the reference machine named in `SPEC_BUILD_REPORT.md` (CPU model, RAM, OS, Python build, run in isolation): `check --judge mock` on the §9.8 golden fixture completes in $\leq$ 2 s wall-clock, and a generated 10,000-file tree with 100 declared IDs in $\leq$ 60 s. Both bounds are recorded, not CI-gated (F-017). |
| **K-09** | JSON output is UTF-8, `indent=2`, `ensure_ascii=False`, sorted per C-07 (not alphabetically), trailing newline; Markdown output is UTF-8 with `\n` line endings. |
| **K-10** | `--version` prints a PEP 440 version equal to the package metadata version. |
| **K-11** | `--max-unknown` defaults to `0.2`, accepts a decimal in `[0, 1]` (parsed as a Decimal from its literal text), and is compared to the quantized `unknown_rate` of C-07 (Decimal, 4 places, ROUND_HALF_EVEN; Q-009); equality passes; a `null` `unknown_rate` (zero judged edges) never exceeds it (F-105). |

---

## 8. Edge cases and failure semantics

| ID | Case | Semantics |
| -- | ---- | --------- |
| **E-01** | Spec declares zero IDs (or all declared IDs are retired) | Exit `3`, message `spec declares no in-scope IDs`; no reports written. |
| **E-02** | Same ID declared twice (both non-retired, or both retired) | Exit `3`, message names the ID and both lines. |
| **E-03** | ID declared retired and also declared non-retired (any order) | Exit `3`, message names the ID and both lines (a spec must retire *or* keep an ID, not both). |
| **E-04** | ID declared inside a fenced code block in `SPEC.md` | Not a declaration; ignored silently (spec templates contain example IDs). |
| **E-05** | `--results` file is not well-formed XML, or root is neither `testsuites` nor `testsuite`, or a `<testcase>` lacks `name` | Exit `3`, message `results: <reason>`. |
| **E-06** | Duplicate `(classname, name)` in results | Single outcome = worst of them (C-04); a Note records the count. |
| **E-07** | Result `<testcase>` joins no attributed test case | Listed under `unattributed_results`; not counted for any ID; exit unaffected. |
| **E-08** | Test case cites an ID but has no result (results absent, or case not run) | Case listed under that ID's `unrun`; ignored in C-05 step 4; if *no* citing case has a result → `UNVERIFIED`. |
| **E-09** | Any of `--spec/--src/--tests/--results/--out` resolves outside `--root` (after symlink resolution) | Exit `2`, message `path outside --root: <path>`. A command-line path that is itself a symlink and resolves inside `--root` is used in resolved form and descended; it is not an E-30 skip (Q-007). |
| **E-10** | File > 2 MiB under a scan root | Skipped; Note `skipped 1 file over 2 MiB: <path>`. |
| **E-11** | A scanned file — or `SPEC.md` itself — is not valid UTF-8 | Decoded with replacement; Note; citations on replaced bytes are impossible (token requires ASCII) so no false citations arise. |
| **E-12** | `.py` test file fails to parse | Whole file is one file-level case; Note `parse fallback: <path>`. |
| **E-13** | Test citation lands in a file-level case (module docstring, helper, fixture) | Attributed to the file-level case; that case has no JUnit outcome by construction (name `""`), so it can only ever contribute `UNVERIFIED`; the JSON carries `"name": ""` and the Markdown renders the label `(file)` (Q-011). |
| **E-14** | Judge provider unreachable, times out, or returns HTTP $\geq$ 400 | Verdict `UNKNOWN`, `coerced: true`, rationale `judge: unavailable` / `judge: timeout` / `judge: http <code>`; `judge_available` set `false` if *every* call failed; exit unaffected unless `--strict` (E-32). |
| **E-15** | Judge returns non-JSON or JSON lacking `verdict` | `UNKNOWN`, `coerced: true`, rationale `judge: malformed response`. |
| **E-16** | Judge returns `ASSERTS` with no evidence, or evidence outside the span / in another file | `UNKNOWN`, `coerced: true`, rationale `judge: ungrounded`. The raw answer is available only at DEBUG. |
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
| **E-30** | A symbolic link (file or directory) is encountered *during descent* under a scan root | Not followed; one Note per run: `skipped N symlink(s)` (F-008). A symlink that is itself a command-line root is E-09's case, not this one (Q-007). |
| **E-31** | A bold ID token appears in a table cell other than the first, or in a heading after other tokens | Not a declaration (F-009). It is also not a citation: `SPEC.md` is never scanned for citations. |
| **E-32** | `--strict --judge llm` and either `judge_available == false` or `unknown_rate > max_unknown` | Exit `1` even if every status is `PASSING`; `strict_judge_failure` set to `"unavailable"` if the judge was unavailable (whether or not the rate also exceeds), else `"unknown_rate"`; summary line carries the matching suffix (F-012, Q-004). Without `--strict`, or with `--judge none|mock`, no effect. |
| **E-33** | A line contains `speccheck:ignore`, or a file's first three lines contain `speccheck:ignore-file` | The line yields no citations / the file is not scanned; ignored files are counted in one Note (F-013). |
| **E-34** | A `.speccheck.json.*.tmp` or `.SPEC_CONFORMANCE_REPORT.md.*.tmp` from a killed run exists under `--out`, which lies under a scan root | Never scanned (C-03); deleted at §3.1 step 1; the run's reports are byte-identical to a run without the leftover (F-103). |
| **E-35** | `--judge llm` and the `--judge-budget` deadline passes with edges not yet started | Each such edge is `UNKNOWN`, `coerced: true`, rationale `judge: budget`; in-flight requests complete and count; one Note `judge budget exhausted: N edge(s) unjudged`; `unknown_rate` counts them; R-28 applies as usual (F-110, Q-010). |
| **E-36** | `--judge llm` with zero eligible edges | No request is sent; `judge_available` is `true`; `unknown_rate` is `null` and never trips R-28 (F-105). |
| **E-37** | A `tests[]` entry whose case was not judged: judge disabled, or the ID not `PASSING` after C-05 step 4, or the outcome not `passed` | JSON `verdict` is `null` (key present); Markdown renders an em dash in the verdict position; the entry never appears in report §8 (Q-001). |
| **E-38** | Two or more Notes are produced in one run | Emitted in ascending Unicode code-point order of their full text, in both reports (Q-002). |
| **E-39** | `--judge llm` with stderr not a TTY (CI log, redirected file, pipe) under `--progress auto`; or `--verbose DEBUG` under any `--progress` value; or `--progress never`; or `--judge none\|mock` under any `--progress` value | No progress bytes (neither draw nor erase) are written to stderr; the run is otherwise identical. `--progress always` overrides only the TTY test, never the DEBUG or judge-mode suppression (R-30). |
| **E-40** | The judge stage is cut short while the indicator is displayed: a provider raises out of the stage (should not happen — E-14..E-16 coerce), an uncaught exception, or `KeyboardInterrupt` | The erase sequence is written before the exit-`3` message (§5.4) or the interrupt propagates; no partially drawn line remains on stderr. The erase MUST happen in a `finally`-equivalent path so it cannot be skipped (R-30, K-13). |

---

## 9. Acceptance criteria, tests, and evals

Every test cites, in its docstring or a comment, its own T id and the R/C/I/K/E ids it proves, so that `speccheck` can check itself (§9.9; F-001). Test inputs that contain the literal marker strings of C-01 (`speccheck:ignore`, `speccheck:ignore-file`) MUST live in data files under `tests/data/`, never inline in a test module, so self-application cannot ignore its own tests (F-109). Groups are ordered by pipeline stage.

### 9.1 Extraction (C-01, C-02)

| ID | Test |
| -- | ---- |
| **T-01** | Table-cell and heading declarations are both extracted with correct family, number, statement, and line; a `SPEC.md` containing invalid UTF-8 is decoded with replacement, its ASCII declarations are still found, and a Note is recorded. (R-01, E-11) |
| **T-02** | `R-7`, `R-07`, `R-007` in a spec are one ID reported as `R-07`; `I-5` is reported as `I-005`. (I-011, K-04) |
| **T-03** | A token with 4 digits (`R-1234`) and tokens adjacent to alphanumerics (`XR-07`, `R-07a`) are not IDs. (K-04, C-01) |
| **T-04** | Strikethrough declarations yield `retired=True`; a later plain declaration of the same ID exits `3`. (R-02, E-03) |
| **T-05** | IDs inside fenced code blocks in `SPEC.md` are ignored, for both ```` ``` ```` and `~~~` fences, with and without an info string, and for an unclosed fence running to end of file; a backtick fence opened with an info string is closed by a bare backtick line, is not closed by a tilde line, and a candidate closing line carrying an info string does not close it. (E-04, C-01) |
| **T-06** | Duplicate declaration exits `3` and names both lines. (E-02) |
| **T-55** | A bold ID in a second cell, a heading with the ID after other tokens, a separator row, and a row with `\|` and a backtick-quoted pipe in a cell are parsed per C-01: only first-cell/first-token forms declare; the statement is the second cell with escapes intact. (E-31, C-01) |
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

### 9.3 Results mapping (C-04)

| ID | Test |
| -- | ---- |
| **T-15** | `<testsuites>` and bare `<testsuite>` roots both parse; `failure`/`error`/`skipped` children map to the correct outcome. (R-05) |
| **T-16** | Classname join accepts both `tests.test_core` and `test_core` forms for `tests/test_core.py`, and rejects `unit_test_core` for `test_core`. (C-04) |
| **T-58** | With `tests/a/test_core.py` and `tests/b/test_core.py`, a result with classname `tests.a.test_core` joins `a` only; a result with classname `test_core` is unattributed with a Note naming both candidates. (E-27, C-04) |
| **T-52** | `test_x[3-True]` and `test_x[0-False]` both join `test_x`; `results` lists both with `param`; the case `outcome` is the worst of them; a name with no `[` is unchanged; everything from the first `[` is removed: `test_y[a][b]` → `test_y` and `test_x[list[int]]` → `test_x` with `param` `list[int]`; a result with empty `classname` joins the unique case with its `join_name` and is unattributed when two exist. (E-24, C-04, F-105) |
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

### 9.5 Judge contract (C-06)

| ID | Test |
| -- | ---- |
| **T-26** | Mock judge returns `ASSERTS` with one evidence line per assertion token, and `EXECUTES_ONLY` with no evidence when none is present, including for an empty test body. (R-22, E-17) |
| **T-27** | A `PASSING` ID whose only passed edges are `EXECUTES_ONLY` becomes `WEAKLY_PASSING`; with any `ASSERTS` edge it stays `PASSING` and passes `--strict`; with only `UNKNOWN` it stays `PASSING`. (C-05 step 5, R-11, E-26) |
| **T-28** | Disabling the judge changes no status except `WEAKLY_PASSING` → `PASSING` (property test over random fixtures). (I-004) |
| **T-29** | A stub provider returning `ASSERTS` without evidence, evidence outside the span, or evidence in another file is coerced to `UNKNOWN` with `coerced: true` and rationale `judge: ungrounded`. (E-16, I-005) |
| **T-30** | Non-JSON, missing `verdict`, an unknown verdict string, a raised exception, and a timeout each yield `UNKNOWN` with the specified rationale. (E-14, E-15) |
| **T-31** | The judge is called exactly once per eligible edge and never for `FAILING`/`SKIPPED`/`UNVERIFIED`/`UNTESTED`/`UNCITED` IDs or for skipped/failed test outcomes (call-counting stub). (I-010) |
| **T-32** | Rationale over 280 chars is truncated to 277 + `...`; newlines become spaces. (K-07) |
| **T-33** | LLM provider sends exactly one `POST` per edge whose body is byte-for-byte the C-06 shape (`model`, `temperature: 0`, `max_tokens: 4000`, system message equal to the C-10 text, user message equal to the request JSON with line-numbered `source`), with the bearer header, honors the timeout, never retries, and issues at most `--judge-concurrency` requests at once while output order stays fixed (recorded HTTP stub with a concurrency counter). (K-05, K-06, R-26) |
| **T-54** | The provider reads `choices[0].message.content`, accepts a bare JSON object and one wrapped in a ```` ``` ````/```` ```json ```` fence, and treats a missing path, a non-200 status, or any other text as E-14/E-15; the report carries `judge_prompt_sha256` equal to the SHA-256 of `speccheck/judge_prompt.md`, and that file equals the C-10 text. (C-06, C-10, R-26) |

### 9.6 Reports and determinism (C-07, C-08)

| ID | Test |
| -- | ---- |
| **T-34** | `speccheck.json` validates against the C-07 shape: key order, sort orders, rounding, no absolute paths, no timestamps; `by_family` has all six keys and `by_status` all seven in-scope statuses on every fixture including single-family ones; `judge_available` is `null` for `none`, `true` for `mock`, `true` for `llm` with zero eligible edges, `false` for `llm` when every call fails; every `tests[]` entry carries the `verdict` key, `null` on a `FAILING` ID, on a skipped-outcome edge of a `PASSING` ID, and everywhere under `--judge none`; `tests[].name` is `""` for a file-level case; a fixture producing five Notes emits them in code-point order in both reports; every ratio has exactly four decimal places and a hand-picked tie value (e.g. 1/8 = 0.125 at 3 places, 0.00005 at 4) rounds half-even to the quantized Decimal, not to `round()`'s binary result. (R-13, R-20, K-09, C-07, E-37, E-38) |
| **T-35** | `SPEC_CONFORMANCE_REPORT.md` has the nine C-08 sections in order, one per-ID row per declared ID, retired rows with exactly the ID cell struck through, an em dash in the verdict position for every unjudged case and `(file)` for every file-level case, and every `file:line` in it also present in the JSON. (R-12, I-003, E-37, Q-011) |
| **T-36** | Two runs on the golden fixture with `--judge mock` produce byte-identical reports and summary lines; the same holds after copying the fixture to a different absolute path, and with `--src .` and `--out` inside the source root (the previous run's reports and the spec itself produce no citations), and with a planted `.speccheck.json.deadbeef.tmp` and `.SPEC_CONFORMANCE_REPORT.md.deadbeef.tmp` under `--out` before the run (never scanned, deleted by the run). (R-16, I-002, E-23, E-34) |
| **T-37** | Every metric in the report is recomputable from the report's own evidence table plus the results file (the test recomputes them independently). (R-24) |
| **T-38** | Only the two report files are created; input trees are byte-identical before and after (hash comparison). (R-19, I-001) |

### 9.7 CLI, exit codes, diagnostics, boundary (§5)

| ID | Test |
| -- | ---- |
| **T-39** | `exit_code` in JSON equals the process exit status for fixtures exercising `0`, `1` (non-strict), `1` (strict-only reasons: `UNVERIFIED`, `UNTESTED`, `UNCITED`, `SKIPPED`, `WEAKLY_PASSING`, dangling, stale), and `0` under `--strict` for a mixed `ASSERTS`/`EXECUTES_ONLY` ID. (R-14, R-15, I-009, E-26) |
| **T-40** | Missing `--spec`, bad `--judge`, bad `--verbose` value, any input or `--out` path outside `--root`, and missing judge env each exit `2` with the specified message; the API key value never appears in the message. (K-01, E-09, E-21, R-23) |
| **T-41** | Bare `--verbose` $\equiv$ `--verbose INFO`; INFO emits stage lines with counts and no statement text, file contents, or prompts; DEBUG emits `judge>`/`judge<` lines with the key redacted; stdout is the single summary line in all cases. (R-17, I-007) |
| **T-42** | With no `--verbose`, stderr is empty on exit 0/1 even when the run produced Notes; with `--verbose`, each Note appears once at `INFO`. (§5.3) |
| **T-43** | With `--judge none` and `--judge mock`, a socket-creation guard installed for the process lifetime is never triggered; `speccheck --self-check` passes from an installed wheel in an empty working directory, invokes the inner check in-process with exactly the §5.1 argument list (asserted via a recorded `Config`), prints `self-check: ok` although its inner check exits `1`, leaves no files behind, and writes nothing outside its temporary directory. (R-18, I-006, I-001, Q-003) |
| **T-60** | `speccheck/_selfcheck/` is byte-identical to `fixtures/target/` (recursive file-by-file comparison, `golden/` included); the test fails if either side changes without the other. (F-107, §10) |
| **T-44** | Summary line matches the §5.1 regex exactly, is pure ASCII, ends in a single `\n`, is emitted correctly under a C/POSIX locale and a `cp1252` stdout, carries all seven in-scope status counts including `skipped`, and its numbers equal the JSON metrics. (R-21, R-29, Q-005) |
| **T-59** | Under `--strict --judge llm` with a provider stub that fails every call — so that `judge_available` is `false` *and* `unknown_rate` is `1.0000 > max_unknown` — exit is `1`, `strict_judge_failure` is `"unavailable"` (not `"unknown_rate"`), and the summary line ends `judge=llm (unavailable)` (Q-004); with a stub yielding 3 `UNKNOWN` of 10 edges and `--max-unknown 0.2`, exit is `1` with `"unknown_rate"` and the numeric suffix; with `--max-unknown 0.3` exit is `0`; without `--strict` neither affects exit; with a fixture that has zero eligible edges, no request is sent, `unknown_rate` is `null`, and `--strict` exits `0`. (R-28, K-11, E-32, E-36) |
| **T-61** | With `--judge-budget 1`, `--judge-concurrency 2`, and a provider stub that sleeps 2 s per call over six edges, exactly the two requests issued before the deadline complete and are judged (in-flight requests are not cancelled); the remaining four are `UNKNOWN` with rationale `judge: budget` and `coerced: true`; the Note reports 4; `unknown_rate` includes them; with `--judge-budget 0` all six are judged. (K-12, E-35, Q-010) |
| **T-62** | With `--judge llm`, `--progress always`, a provider stub over six edges that sleeps 0.3 s per call, `--judge-concurrency 2`, and stderr captured: splitting the capture on `\r` yields only C-11 draw and erase sequences; the first draw reads `0/6 edges` with `?:??`, every draw matches the C-11 regex, `<done>` is non-decreasing across draws, a draw with `6/6` and a full 20-`#` bar exists, the capture ends with the erase sequence, and the number of `#` in each draw equals $\lfloor 20 d / 6 \rfloor$ for its `<done>`; with a stub that sleeps 2.5 s on a single edge, at least two draws show `0/1` with distinct `elapsed` values (the 1 s tick); stdout is the single summary line and both report files are byte-identical to a `--progress never` run over the same stub. (R-30, C-11, K-13) |
| **T-63** | No progress bytes reach stderr when: stderr is not a TTY under `--progress auto` (the default in a subprocess capture); `--progress never`; `--verbose DEBUG` with `--progress always`; `--judge mock` or `--judge none` with `--progress always`. With `--progress auto` and a stderr whose `isatty()` returns `True`, the indicator is drawn. `--progress` with any other value exits `2`. Under `--progress always` a stub that raises `KeyboardInterrupt` mid-stage leaves the erase sequence as the last stderr bytes before the interrupt propagates. (R-30, E-39, E-40, K-01) |
| **T-45** | Unwritable `--out` exits `3` with nothing written; a failure injected after the JSON rename and before the Markdown rename exits `3` with no `.tmp` left, no `speccheck.json`, and the previous run's `SPEC_CONFORMANCE_REPORT.md` intact (the one stale combination E-18 permits); leftover temporaries from an earlier run are deleted first; on success no `.tmp` remains and the two temporaries used carried the same 8-hex-digit nonce. (E-18, I-001, §3.1) |
| **T-50** | `speccheck --version` prints `speccheck <version>` where `<version>` is PEP 440 and equals `importlib.metadata.version("speccheck")`. (K-10) |

### 9.8 Golden fixture (end to end)

| ID | Test |
| -- | ---- |
| **T-46** | `fixtures/target/` — a small self-contained project with its own `SPEC.md` ($\geq$ 12 IDs across all six families, 2 retired), `src/`, `tests/`, and a checked-in `junit.xml` — contains planted defects: one `UNCITED` R, one `UNTESTED` C, one `UNVERIFIED` E, one `FAILING` T, one `SKIPPED` K, one `EXECUTES_ONLY`-only test, one dangling citation, one stale citation, one unattributed result, one file-level citation. The golden reports live in `fixtures/target/golden/` (outside every scan root). `speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --root fixtures/target --out <fresh tmp>` produces files byte-identical to `golden/speccheck.json` and `golden/SPEC_CONFORMANCE_REPORT.md` and exits `1` (Q-003). (all of §2) |
| **T-47** | Removing each planted defect in turn flips exactly the expected row and metric (one sub-test per defect). (R-06, R-24) |

### 9.9 Self-application (recorded, not gating)

| ID | Test |
| -- | ---- |
| **T-48** | `speccheck check --spec SPEC.md --src src --tests tests --results <this suite's junit.xml> --judge mock` on this repository reports every R/C/I/K/E/T ID in this document as `PASSING`. Recorded in `SPEC_BUILD_REPORT.md`; it is evidence *for* the build, not the proof of it — the proof is §9.1–§9.8. (R-24) |

### 9.10 Performance (recorded)

| ID | Test |
| -- | ---- |
| **T-51** | A benchmark script (`tools/bench.py`, not collected by pytest) runs `check --judge mock` on the golden fixture and on the generated 10,000-file tree five times each and prints the median wall-clock; the medians, the reference-machine description, and the pass/fail against K-08 are recorded in `SPEC_BUILD_REPORT.md`. Not run in CI. (K-08) |

### 9.11 LLM judge evaluation (opt-in, `--judge llm`, not run in CI)

| ID | Test |
| -- | ---- |
| **T-49** | On the golden fixture's judged edges (each hand-labeled `ASSERTS`/`EXECUTES_ONLY`/`UNRELATED`), the LLM judge's non-`UNKNOWN` verdicts agree with labels at $\geq$ 0.90 accuracy and `unknown_rate` $\leq$ 0.10 in **each** of three independent runs (no pooling; one failing run fails T-49); all three per-run figures are recorded with model name, date, and `judge_prompt_sha256`. (R-10, R-26) |

---

## 10. Dependencies and environment

- **Runtime:** Python 3.12; `uv` for environment and lockfile. Install: `uv sync --extra dev`; with the model judge: `uv sync --extra dev --extra llm`.
- **Kernel dependencies:** none beyond the standard library (`re`, `ast`, `xml.etree.ElementTree`, `json`, `argparse`, `pathlib`, `logging`, `hashlib`).
- **Package data:** `speccheck/judge_prompt.md` (C-10) and `speccheck/_selfcheck/` (a byte-identical copy of `fixtures/target/` including its `golden/` directory, kept in sync by T-60; F-011, F-107), both included in the wheel.
- **Golden fixture layout:** `fixtures/target/{SPEC.md, src/, tests/, junit.xml, golden/speccheck.json, golden/SPEC_CONFORMANCE_REPORT.md}`; `golden/` is never a scan root and is never written to by a run (Q-003).
- **`[llm]` extra:** `httpx` (HTTP client with per-request timeout). No provider SDK; the wire format is C-06.
- **`[dev]` extra:** `pytest`, `pytest-cov`, `hypothesis` (T-28), `ruff`.
- **Environment variables:** C-09 (only with `--judge llm`). No configuration files are read.
- **Host prerequisites:** none. No network access is required except with `--judge llm`.
- **Commands:**

```bash
uv sync --extra dev
uv run python -m pytest tests -q --junitxml=junit.xml     # the §9 suite; junit.xml feeds T-48
uv run ruff check src tests
uv run speccheck --self-check
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock
```

- **Optional items:**
  - **O-1** LLM judge provider (`--judge llm`, `[llm]` extra). Specified fully in C-06/C-09; gated by flag and extra.
  - **O-2** Additional language adapters for test-case attribution (Go `func Test*`, JS/TS `test(`/`it(`). Not in v0.1; the fallback path is what v0.1 ships and tests (T-12).
  - **O-3** Any non-CLI surface (GUI, HTTP, editor plugin). Not in v0.1 and not designed for.

---

## 11. Traceability matrix (id → where realized)

Until the build exists, "where realized" names the component the §1/§4 design assigns; `spec-build` replaces it with the real module and the real test.

| Spec id | Where realized (component / module) | Verified by |
| ------- | ----------------------------------- | ----------- |
| R-01 | `extract.py` (declaration scan, UTF-8 replace) | T-01, T-05 |
| R-02 | `extract.py` (retired flag), `graph.py` (denominators) | T-04, T-25 |
| R-03 | `extract.py` (source scan, C-03 exclusions, binary/symlink filters) | T-08, T-13, T-36 |
| R-04 | `attribute.py` (Python adapter, fallback, C-03 exclusions) | T-09, T-10, T-11, T-12, T-36, T-56 |
| R-05 | `results.py` | T-15, T-16, T-52, T-58 |
| R-06 | `graph.py` (C-05 steps 1–4) | T-20, T-21, T-47 |
| R-07 | `graph.py` (dangling) | T-23 |
| R-08 | `graph.py` (stale) | T-23 |
| R-09 | `graph.py` (metrics) | T-24 |
| R-10 | `judge.py`, `judge_mock.py`, `judge_llm.py` (passed-outcome edges only) | T-26, T-31, T-33, T-49 |
| R-11 | `graph.py` (C-05 step 5) | T-27, T-28 |
| R-12 | `report.py` (Markdown) | T-35 |
| R-13 | `report.py` (JSON) | T-34 |
| R-14 | `cli.py` (exit mapping) | T-39 |
| R-15 | `cli.py` (`--strict`, status-only) | T-39, T-27 |
| R-16 | all kernel modules (sorted, no volatile fields) | T-36 |
| R-17 | `cli.py` (logging setup, level `ERROR` default) | T-41, T-42 |
| R-18 | `cli.py` (`--self-check`, pinned in-process invocation), `speccheck/_selfcheck/`, `judge_llm.py` import isolation | T-43 |
| R-19 | `report.py` (only writer, temp-and-rename), `cli.py` | T-38, T-43, T-45 |
| R-20 | `extract.py`, `report.py` (path normalization) | T-34, T-36 |
| R-21 | `cli.py` (summary line) | T-44, T-59 |
| R-22 | `judge_mock.py` | T-26 |
| R-23 | `judge_llm.py`, `cli.py` (env validation, redaction) | T-40, T-41 |
| R-24 | `report.py` (evidence table completeness) | T-37, T-48 |
| R-25 | `graph.py` (C-05 step 2b) | T-53 |
| R-26 | `judge_llm.py` (body, response path, prompt hash), `speccheck/judge_prompt.md` | T-33, T-54 |
| R-27 | `extract.py` (ignore markers) | T-57 |
| R-28 | `cli.py` (`--strict` judge gate), `report.py` (`strict_judge_failure`) | T-59 |
| R-29 | `cli.py` (summary line encoding) | T-44 |
| R-30 | `cli.py` (`--progress` resolution, TTY test), `judge.py` (progress callback in `run_judge`) | T-62, T-63 |
| C-01 | `extract.py` (`ID_RE`, fence tracker, row/heading parsers, ignore markers) | T-01, T-02, T-03, T-04, T-05, T-55, T-57 |
| C-02 | `extract.py` (`SpecId`, `SpecIndex`) | T-01, T-06 |
| C-03 | `attribute.py` (`TestCase`, `Citation`, `test*` methods), `extract.py` (exclusions incl. temporaries, binary, symlinks) | T-09, T-10, T-13, T-14, T-36, T-56 |
| C-04 | `results.py` | T-15, T-16, T-17, T-18, T-19, T-52, T-58 |
| C-05 | `graph.py` (`IdStatus`, `compute_status`) | T-20, T-21, T-27, T-53 |
| C-06 | `judge.py` (`JudgeRequest` with numbered `source`, `Verdict`, validation), providers | T-26, T-29, T-30, T-32, T-33, T-54 |
| C-07 | `report.py` (`to_json`; Decimal quantization; `verdict: null`; Note order) | T-34, T-37, T-59 |
| C-08 | `report.py` (`to_markdown`; em dash and `(file)` renderings) | T-35 |
| C-09 | `judge_llm.py` (`from_env`) | T-33, T-40 |
| C-10 | `speccheck/judge_prompt.md`, `judge_llm.py` (system message) | T-33, T-54 |
| C-11 | `judge.py` (progress line rendering, draw/erase sequences) | T-62 |
| I-001 | `report.py` (temp-and-rename), `cli.py` | T-07, T-38, T-43, T-45 |
| I-002 | kernel modules | T-36 |
| I-003 | `report.py` | T-25, T-35 |
| I-004 | `graph.py` | T-27, T-28 |
| I-005 | `judge.py` (validation) | T-29 |
| I-006 | `cli.py`, module import layout | T-43 |
| I-007 | `cli.py` (logging filter), `judge_llm.py` (redaction) | T-40, T-41 |
| I-008 | `graph.py` (metrics) | T-24 |
| I-009 | `cli.py`, `report.py` | T-39 |
| I-010 | `graph.py` (edge selection), `judge.py` | T-31 |
| I-011 | `extract.py` (normalization) | T-02 |
| K-01 | `cli.py` | T-39, T-40, T-19 |
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
| K-12 | `judge.py` (budget deadline, in-flight completion), `cli.py` (`--judge-budget`) | T-61 |
| K-13 | `judge.py` (redraw on completion, 1 s ticker, single erase) | T-62 |
| E-01 | `extract.py`, `cli.py` | T-07 |
| E-02 | `extract.py` | T-06 |
| E-03 | `extract.py` | T-04 |
| E-04 | `extract.py` (fence tracking) | T-05 |
| E-05 | `results.py` | T-19 |
| E-06 | `results.py` | T-17 |
| E-07 | `results.py`, `report.py` | T-18 |
| E-08 | `graph.py` (`unrun`) | T-22 |
| E-09 | `cli.py` (path validation incl. `--out`; symlinked roots resolved and used) | T-40 |
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
| E-35 | `judge.py` (budget) | T-61 |
| E-36 | `judge.py`, `cli.py` (R-28 with `null`) | T-59 |
| E-37 | `report.py` (`verdict: null`, em-dash rendering) | T-34, T-35 |
| E-38 | `report.py` (Note ordering) | T-34 |
| E-39 | `cli.py` (`--progress` gating) | T-63 |
| E-40 | `judge.py` (erase in `finally`) | T-63 |

---

## 12. Open questions and decisions to confirm

Every row below is a decision the specification's author made on the requester's behalf because `one_sentence_prompt.md` did not settle it. The normative rows assume the default; the reviews checked that the default is precise, not that it is what the requester wanted. Rows are the `D-nn` family (decisions to confirm). A row marked `confirm` is ratified by a human changing its status to `confirmed v1.n`; a row the requester overturns becomes a `fix(speccheck):` change with a version bump.

| ID | Decision | Default taken | Alternatives rejected | Affects | Owner / status |
| ----- | -------------- | ---------------- | ------------------ | ---------- | ------------ |
| D-01 | Implementation stack | Python 3.12 + `uv`, standard-library kernel, one HTTP client behind an extra | Go or Rust (single static binary; stack-neutral repos would not need a Python runtime); TypeScript (nearest to most agent tooling) | §10, C-02/C-03 type pins, K-10 | requester / confirm |
| D-02 | Test-result input contract | JUnit XML, consumed; the tool never runs tests | run the suite itself (simpler for users, but executes untrusted code and ties the tool to one runner); pytest's own JSON report (richer, Python-only) | R-05, C-04, non-goal "no test execution" | requester / confirm |
| D-03 | What counts as a citation | a literal ID token anywhere in a file, with `speccheck:ignore` opt-outs | a structured annotation (`@spec R-07`, a decorator, a registry) — precise but requires adoption; docstring-only citations — misses comments | C-01, R-03, R-04, R-27, the §0 limitation | requester / confirm |
| D-04 | Family-T semantics | option (a): T ids are in scope, cited by their own test, and count in `conformance` | option (b): T ids declared but out of scope, reported separately — leaves `conformance` about R/C/I/K/E only | R-25, C-05 step 2b, C-07 metrics, T-53 | requester / confirm (F-001 chose (a) on the reviewer's recommendation) |
| D-05 | Mixed judge verdicts under `--strict` | an ID with both `ASSERTS` and `EXECUTES_ONLY` edges is `PASSING` and passes strict | a `MIXED` status that fails strict — stricter, noisier | R-15, C-05 step 5, E-26 | requester / confirm (F-003) |
| D-06 | Judge question and vocabulary | one question per edge — does this test *assert* the behavior? — with `ASSERTS` / `EXECUTES_ONLY` / `UNRELATED` / `UNKNOWN` | a graded strength score (rejected: a number the model made up); judging code rather than tests (rejected: semantic analysis is a non-goal) | C-06, C-10, I-004, I-005 | requester / confirm |
| D-07 | Judge request parameters | `temperature 0`, `max_tokens 4000` (v1.2; was 400), 30 s timeout, concurrency 4, budget unlimited, `--max-unknown 0.2` | any of these numbers; `max_tokens 400` was rejected after the first T-49 runs because thinking models (`qwen3:8b`, `gemma4:latest`) spend the budget on reasoning and are truncated before the verdict JSON, driving `unknown_rate` above `--max-unknown`; at 4000 both pass T-49 three runs out of three. The other numbers remain defaults with no data behind them | C-06, K-05, K-06, K-11, K-12 | requester / `max_tokens` confirmed; the rest remain confirm |
| D-08 | Judge instruction text | the C-10 text as written | any rewording; the text is a first draft whose only evidence is T-49 | C-10, R-26, T-49 | requester / confirm after the first T-49 run |
| D-09 | Input limits | files over 2 MiB skipped; NUL byte in the first 8 KiB means binary; IDs 1–3 digits | larger cap, or none; MIME sniffing; 4-digit IDs | K-02, K-04, E-10, E-29 | requester / confirm |
| D-10 | LLM endpoint shape | an OpenAI-compatible `chat/completions` body, provider-agnostic | a specific vendor SDK (simpler, vendor-locked); a local-model-only path | C-06, C-09 | requester / confirm |
| D-11 | Fixture and self-check layout | `fixtures/target/` with `golden/`, byte-copied into the wheel as `speccheck/_selfcheck/` | package only the goldens and regenerate the fixture; skip the self-check entirely | §10, T-43, T-46, T-60 | requester / confirm |
| D-12 | Report file names and location | `SPEC_CONFORMANCE_REPORT.md` and `speccheck.json` under `--out`, default `.` | a `reports/` directory; a single JSON with Markdown derived by a separate renderer | §3.3, C-07, C-08, E-18 | requester / confirm |
| D-13 | Python test-case delimitation | `def test_*` at module level; `test*` methods in `Test*` classes and `*TestCase` subclasses; nested classes excluded | honor `pytest.ini` `python_functions` / `python_classes`; collect via pytest itself (rejected: runs code) | C-03, E-28, T-56 | requester / confirm (F-007, F-102) |
| D-14 | Reference machine for K-08 | named in `SPEC_BUILD_REPORT.md` at build time | a CI runner with a generous bound; no performance constraint at all | K-08, T-51 | build owner / open |
| D-15 | Progress indicator shape and gating | a single in-place ASCII line on stderr (`#`/`-` bar of 20 cells, done/total, elapsed, ETA per C-11), on by default only when stderr is a TTY and not at DEBUG, erased when the judge stage ends, `--progress auto\|always\|never` to override; LLM judge only | leaving the final line on screen (rejected: §5.3 quiet-by-default would then have a visible exception at exit); a per-edge log line instead of a bar (rejected: that is what `--verbose DEBUG` already is); Unicode block characters (rejected: R-29 locale reasoning); a bar for `--judge mock` too (rejected: mock is sub-second, K-08); a spinner without ETA (rejected: the requester's complaint is duration, so ETA is the useful number) | R-30, C-11, K-13, E-39, E-40, §5.1, §5.3 | requester / confirm (the *existence* of the bar is the requester's ask of 2026-09-13; its shape is the author's default) |

None of the first fourteen was raised as a question before v1.1; each was decided and reviewed for precision only. That is the defect this section corrects: a specification can be implementation-grade and still not be what was asked for.

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
