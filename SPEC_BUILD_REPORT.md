# SPEC_BUILD_REPORT — `speccheck` v1.4.0 against `SPEC.md` (v1.4)

> - **Built:** 2026-09-11 (v1.1, from `../SPEC_v1.1.md`), incremented 2026-09-13 to `SPEC.md` v1.4 (§0 below); Python 3.12.13, `uv` 0.12.12
> - **Reference machine (K-08, D-14):** Apple M5 Max, 128 GiB RAM, macOS 26.6.2 (arm64), CPython 3.12.13 (uv-managed), run in isolation
> - **Verdict:** see §6

## 0. v1.4 increment (2026-09-13)

`SPEC.md` v1.3 added the judge-stage progress indicator (R-30, C-11, K-13, E-39, E-40, T-62,
T-63, D-15) and v1.4 folded in the ten findings of its `spec-review` (`SPEC_REVIEW_REPORT.md`,
F-201..F-210), among them the interrupt rule (E-41, T-64, D-16). The build was brought up to
date test-first: T-62/T-63/T-64 were written from §9, watched fail (`--progress` unrecognized;
a `KeyboardInterrupt` from the provider stub escaped `main()` and killed the pytest process —
exactly the E-41 gap), then realized:

| Spec id | Realized in | Notes |
| --- | --- | --- |
| R-30, C-11, K-13 | `judge.py` `ProgressLine`, `progress_line()`; `cli.py` `_progress_enabled()`, `--progress` | one in-place stderr line; padded redraws with a bare `\r`, no escapes; 100 ms coalescing, 1 s tick, $\leq$ 10 draws/s; atomic writes under a lock; drawn on entry, final state + erase on exit, erase-only on exception |
| E-39 | `cli.py` `_progress_enabled()` | LLM judge only; never at `DEBUG`; `auto` = `sys.stderr.isatty()`; `always` overrides the TTY test only |
| E-40 | `judge.py` `ProgressLine.__exit__` | erase runs in the context manager's exit path, exception or not |
| E-41 | `cli.py` `main()` (`except KeyboardInterrupt` → `ERROR interrupted`, exit 3, traceback at DEBUG); `report.py` `write_reports` (cleanup on any `BaseException`, re-raise) | D-16 default: exit `3`, keeping K-01's closed set |
| F-201 | `cli.py` | the judge stage's INFO lines (mode/URL/model, stage summary) are emitted after `run_judge` returns, so nothing reaches stderr through the logger while the line is displayed |
| F-206, F-207 | — | already realized in v1.2 (`max_unknown` echoed quantized, B-04; header parenthetical omitted for `--judge none`); T-35 now asserts the latter |
| T-48 | `tests/test_09_self_application.py` | declared count 161 → 170 |

Phase 1 exit gate on the v1.4 tree (fresh run):

```text
$ uv run python -m pytest tests -q --junitxml=junit.xml
73 passed in 11.69s

$ uv run ruff check src tests
All checks passed!

$ uv run speccheck --self-check
self-check: ok

$ uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck
speccheck: CONFORMING - 170/170 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock
```

Phase B (LLM judge, `openai/gpt-4o-mini` via OpenRouter, `--judge-concurrency 32`; run by the
requester from a terminal, where the C-11 indicator was visible). The first pass over the
v1.4 tree returned `4 weak` — R-20, K-02, K-03, K-08 — and a second pass `1 weak` (E-29); each
was a test that proved its ID only by implication, and each was strengthened in the test, never
in the code: T-13 now cites K-02/K-03 and asserts E-29's silent skip explicitly, T-34 asserts
R-20's relative-POSIX paths over every path in the report, and T-51 runs the golden benchmark
once and asserts the K-08 2 s bound. Third pass, on the final tree:

```text
$ speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm --strict --judge-concurrency 32 --out build/speccheck-openrouter
speccheck: CONFORMING - 170/170 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=llm
# SPECCHECK_JUDGE_URL=https://openrouter.ai/api/v1/chat/completions, SPECCHECK_JUDGE_MODEL=openai/gpt-4o-mini,
# judge_available true, unknown_rate 0.0000, judge_strength 170/170, judge_prompt_sha256 21ec78498043f92be89766967dce235a8a989dbb3357f91123abcd411177fdf7
```

The README's commands were re-run as written after the update (quick start on a fixture copy,
`sync_selfcheck.py --check`, the single-test command, `--version` → `speccheck 1.4.0`).
`ARCHITECTURE.md` §10 gained a subsection on the indicator and §5.4's exit-code note covers the
interrupt. Sections 1–6 below are the v1.1 record and remain accurate except where §0 supersedes
them (counts 161 → 170, 70 → 73 tests; `max_tokens` 400 → 4000 since v1.2).

## 1. Phase 1 exit gate — evidence (v1.1 record)

```text
$ uv run python -m pytest tests -q --junitxml=junit.xml
70 passed in 5.77s

$ uv run ruff check src tests tools
All checks passed!

$ uv run speccheck --self-check
self-check: ok

$ uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --out build/selfapp --verbose
INFO stage=extract-spec ids=161 retired=0 ms=2
INFO stage=scan-src files=22 citations=371 ms=2
INFO stage=scan-tests files=13 cases=76 citations=614 ms=11
INFO stage=map-results results=70 joined=70 unattributed=0 ms=0
INFO stage=graph ids=161 dangling=0 stale=0 ms=0
INFO judge=mock
INFO stage=judge edges=316 unknown=0 ms=9
INFO note: ignored 2 file(s) by speccheck:ignore-file
INFO stage=report out=build/selfapp ms=13
speccheck: CONFORMING - 161/161 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock
```

The 70 tests cover all 61 `T-nn` ids (every test function's docstring is headed by the `T-nn` it
realizes and lists the R/C/I/K/E ids it proves); none is skipped, and `filterwarnings = error` is
on, so the suite is warning-free. `hypothesis` drives T-28 (200 examples).

**Installed-wheel check (T-43):** `uv build`, install `dist/speccheck-1.1.0-py3-none-any.whl`
into a fresh venv, `cd` into an empty directory, `speccheck --self-check` → `self-check: ok`,
exit 0, directory still empty. The wheel carries `speccheck/judge_prompt.md` and all of
`speccheck/_selfcheck/` (10 files, goldens included). This check caught a real defect during the
build — the first `.gitignore` masked `junit.xml`/`speccheck.json` inside the fixture, and
hatchling honoured it — which is why the wheel check is part of the gate.

## 2. Recorded (non-gating) results

### T-48 self-application

The run above: every one of the 161 R/C/I/K/E/T ids in `SPEC.md` is `PASSING`; no dangling, no
stale citations; the only Note is the two `tests/data/markers/` files that carry the
`ignore-file` marker on purpose. This is evidence *for* the build, not its proof — the proof is
§9.1–§9.8. Two observations worth recording:

- The first self-application run reported `T-57` as `UNVERIFIED`: the docstring of the T-57 test
  contained the literal line-ignore marker, so the checker ignored the line that cited T-57 —
  exactly the trap §9 / F-109 warns about. The docstring was reworded; the marker strings now
  exist only under `tests/data/markers/`.
- Low-numbered ids (`R-01`, `C-01`, `T-01`, …) are over-cited in self-application because the
  suite uses them as sample ids in inline fixtures. That is the §0 "citation is literal"
  limitation, stated rather than hidden; it inflates evidence but never a status.

### T-51 / K-08 benchmark (`tools/bench.py`, 5 runs each, medians)

```text
machine: macOS-26.6.2-arm64-arm-64bit arm64 python=3.12.13
golden fixture: median 0.002 s over 5 runs (K-08 bound 2 s: PASS)
generated 10000 files / 100 IDs: median 0.536 s over 5 runs (K-08 bound 60 s: PASS)
```

### T-49 LLM judge evaluation (`tools/eval_judge.py`, Ollama, three independent runs per model)

Endpoint `http://localhost:11434/v1/chat/completions` (Ollama's OpenAI-compatible surface; the
C-06 body is sent unchanged), `judge_prompt_sha256 =
21ec78498043f92be89766967dce235a8a989dbb3357f91123abcd411177fdf7`, date 2026-09-11, labels in
`fixtures/target/golden/judge_labels.json` (9 judged edges: 7 `ASSERTS`, 1 `EXECUTES_ONLY`,
1 `UNRELATED`).

| Model | Run | Accuracy (non-UNKNOWN) | unknown_rate | T-49 |
| --- | --- | --- | --- | --- |
| `qwen3:8b` | 1 / 2 / 3 | 1.0000 / 1.0000 / 1.0000 | 0.1111 / 0.1111 / 0.1111 | FAIL (unknown_rate > 0.10) |
| `gemma4:latest` | 1 / 2 / 3 | 1.0000 / 1.0000 / 1.0000 | 0.1111 / 0.1111 / 0.1111 | FAIL (unknown_rate > 0.10) |
| `llama3.2:latest` | 1 / 2 / 3 | n/a | 1.0000 ×3 | FAIL (every answer malformed) |
| `phi4-mini:latest` | 1 / 2 / 3 | 0.7500 ×3 | 0.5556 ×3 | FAIL |
| `gemma3n:e4b` | 1 / 2 / 3 | n/a | 1.0000 ×3 | FAIL |

**As pinned, T-49 fails on every locally available model, and every failure is format-level,
never a wrong verdict.** The DEBUG transcripts (`judge<` lines) show three failure modes, each
handled by the kernel exactly as C-06/E-14/E-15 require:

1. *Thinking models* (`qwen3:8b`, `gemma4`): Ollama returns the reasoning in
   `message.reasoning`, but the pinned `max_tokens: 400` is spent on that reasoning for the
   hardest edge (`K-02`/`UNRELATED` for gemma4, `I-002`/`EXECUTES_ONLY` for qwen3), so
   `message.content` is empty or truncated → `judge: malformed response`, `coerced: true`.
   One such edge out of nine is `unknown_rate` 0.1111 > 0.10.
2. `llama3.2` emits JSON with an unquoted `rationale` string on every edge → malformed.
3. The small models (`phi4-mini`, `gemma3n`) mostly do not produce the object at all.

**D-07 experiment (not shipped):** re-running the same protocol with `max_tokens` patched to
4000 in a scratch script (the shipped provider keeps 400) gives:

| Model (`max_tokens` 4000) | Accuracy | unknown_rate | T-49 |
| --- | --- | --- | --- |
| `qwen3:8b` | 1.0000 / 1.0000 / 1.0000 | 0.0000 / 0.0000 / 0.0000 | PASS |
| `gemma4:latest` | 1.0000 / 1.0000 / 1.0000 | 0.0000 / 0.0000 / 0.0000 | PASS |

This is the "data behind the numbers" that D-07 and D-08 say to collect before ratifying them.
Recommendation for the spec owner: raise `max_tokens` in C-06 (a `fix(speccheck):` with a
version bump — it changes the byte-exact body T-33 pins), or add a note that thinking models
need a budget large enough for their reasoning. The C-10 text itself (D-08) needed no change:
with enough budget both models scored 100 % including the `UNRELATED` and `EXECUTES_ONLY` edges.

## 3. Interpretations and decisions the build had to make

Each is a place where the spec was silent, or two clauses disagreed. None changes a normative
row; each is listed so the spec owner can ratify or overturn it.

| # | Where | Decision taken | Why |
| --- | --- | --- | --- |
| B-01 | §5.4 vs E-19 / T-20 | A run in which **every** in-scope ID is `UNCITED` exits `1` even without `--strict`. `report.exit_code_for` adds this one clause to the §5.4 rule. | §5.4's table would give exit `0` (nothing is `FAILING`), but E-19 and T-20 both require `1`. The narrowest rule satisfying all three texts was chosen; it stays a pure function of the JSON (R-14, I-009). |
| B-02 | §5.1 `--root`, T-46 | Command-line paths resolve against the **current directory**, not against `--root`; `--root` is only the base for report paths. T-46's literal command is therefore run with the fixture copy as cwd, and its `--out <fresh tmp>` is a fresh directory *inside* the copy, since E-09 requires `--out` inside `--root`. | Conventional CLI behaviour; `--self-check` sets both cwd and `--root` to the same directory, so the pinned invocation is unaffected. |
| B-03 | C-03 "span = node.lineno .. node.end_lineno (decorators included, per `ast`)" | The span starts at the first decorator's line (`min(node.lineno, decorator linenos)`). | Since Python 3.8 `FunctionDef.lineno` is the `def` line, so "per `ast`" alone would exclude decorators; the parenthetical's intent ("decorators included") was honoured. T-09 pins it. |
| B-04 | K-11, C-07 `max_unknown` | `--max-unknown` is parsed as a Decimal from its literal text and **quantized to four places (half-even)**; that quantized value is what the JSON echoes, what the summary line prints, and what `unknown_rate` is compared against. | The summary-line regex requires `\d\.\d{4}`; comparing against the emitted value keeps I-009 exact. Differences from the unquantized comparison arise only beyond the fourth decimal. |
| B-05 | C-05 step 1, C-07 | A `RETIRED` id's citations appear **only** in `stale`; its per-ID row has empty `src`/`tests`/`unrun`. | Avoids listing the same evidence twice and keeps "retired = no conformance evidence" clean. T-23/T-25 pin it. |
| B-06 | C-07 `notes` | Note texts not fixed by the spec were fixed by the build: `invalid UTF-8 decoded with replacement: <path>`, `ambiguous result <classname>::<name>: candidates <file>::<name>, ...` (E-27), `duplicate result <classname>::<name>: N occurrences` (E-06), `undelimited tests in <path>: <Class.name>, ...` (E-28). The spec's own texts (E-10, E-12, E-30, E-33, E-35) are used verbatim. | Each Note must be a fixed string per E-case so the code-point sort (Q-002) is total. |
| B-07 | C-07 `judge_available` | A call that returned HTTP 200 with a malformed body counts as a *succeeded* call; only E-14 failures (unreachable, timeout, HTTP ≥ 400) count as failed; budget-skipped edges are not calls. | E-14 is the only place `judge_available: false` is defined. |
| B-08 | §10 `[llm]` extra | `--judge llm` without `httpx` installed is a usage error (exit `2`) with a message naming the extra. | The spec does not say; failing early beats nine `judge: unavailable` verdicts. |
| B-09 | §11 rows R-14, R-21 | `exit_code_for` and `summary_line` live in `report.py` (the Markdown §1 needs the line); `cli.py` calls them. | Avoids a circular import; the matrix in §5 below names the real module. |
| B-10 | C-06 `judge: <class of failure>` | Any provider exception that is not a typed timeout / HTTP / malformed error is recorded as `judge: unavailable`. | E-14 names "unreachable" as the class; T-30 pins the mapping. |
| B-11 | T-43 "from an installed wheel" | In-suite, the console script of the synced environment is executed from an empty directory via a subprocess (editable install). The wheel itself was built, installed into a fresh venv, and self-checked by hand (§1). | Building a wheel inside the test run would make the suite depend on network-free `uv build`; the manual check is recorded above. |
| B-12 | T-48 in-suite | The in-suite test asserts the structural part (161 ids, none `UNCITED`/`UNTESTED`, exit 0/1) on a temp copy of the repo; the "all PASSING" claim is recorded here from the real run, because it needs the `junit.xml` of the very run that executes the test. | Chicken-and-egg noted in §9.9 itself ("recorded, not gating"). |
| B-13 | T-49 / T-51 in-suite | Deterministic guards stand in for the recorded runs: the label file covers exactly the judged edges, and `tools/bench.py` / `tools/eval_judge.py` exist and parse. The runs themselves are recorded in §2. | So that `T-49` and `T-51` are cited by a passing test (T-48 needs every T id `PASSING`) without running an LLM or a benchmark in CI. |
| B-14 | `fixtures/target/golden/` | Holds a third file, `judge_labels.json` (T-49 labels), beside the two goldens. | The self-check compares only the two report files; T-60 keeps the whole directory in sync. |
| B-15 | R-23 redaction | The raw response is redacted by replacing every occurrence of the key's text with `***` — with the Ollama convention `SPECCHECK_JUDGE_API_KEY=ollama` this also turns Ollama's `system_fingerprint: fp_ollama` into `fp_***` in DEBUG output. | Harmless; the rule is "the key never appears", and it never does. |

No `SPEC.md` row was edited. The two clauses that disagree (B-01, B-02) are candidates for a
`fix(speccheck):` by the spec owner: §5.4 could name the E-19 case explicitly, and T-46's
`--out <fresh tmp>` could read `--out <fresh dir inside --root>`.

## 4. Artifact cross-check (§3.2 of `spec-build`)

| Artifact | Checked against | Result |
| --- | --- | --- |
| `src/speccheck/extract.py` `SpecId`/`SpecIndex` | C-02 | Same fields, same sort order (family order R,C,I,K,E,T then number); the `(family, number)` uniqueness invariant is enforced by E-02/E-03 |
| `src/speccheck/attribute.py` `TestCase`/`Citation` | C-03 | Same fields; `classname` rule for Python and fallback; `kind` ∈ {src, test} |
| `src/speccheck/judge.py` `JudgeRequest`/`Evidence`/`Verdict`/`Judge` | C-06 | Same fields; `source` is line-numbered with TAB (F-109); validation is in `judge.py`, not in the providers |
| `src/speccheck/judge_prompt.md` | C-10 | Byte-equal to the fenced text in `SPEC.md` (T-54 asserts it; SHA-256 `21ec7849…77fdf7`) |
| `src/speccheck/judge_llm.py` request body | C-06 | `{"model","temperature":0,"max_tokens":4000,"messages":[system,user]}` (4000 since SPEC v1.2 / D-07) in that key order, `ensure_ascii=False`; user content is the K-09-formatted request JSON; T-33 compares the bytes |
| `speccheck.json` | C-07 | Key order, seven statuses, six families, four-decimal Decimals via the `_Num` sentinel, `verdict` key always present, notes sorted by code point, no volatile fields (T-34) |
| `SPEC_CONFORMANCE_REPORT.md` | C-08 | Nine sections in order; retired ID cell struck; `(file)` and `—` renderings (T-35) |
| `speccheck` CLI | §5.1 | Every flag, default, range, and exit code in the table; `--self-check` runs the pinned argv in-process (T-43 records the `Config`) |
| Diagnostics | §5.3 | Logger `speccheck`, one stderr handler, `%(levelname)s %(message)s`, `ERROR` default; nothing at `WARNING`; DEBUG `judge>`/`judge<` (T-41, T-42) |
| `pyproject.toml` | §10 | Python ≥ 3.12; kernel has no dependencies; `[llm] = httpx`; `[dev] = pytest, pytest-cov, hypothesis, ruff` (+ `httpx` so the provider's default transport can be exercised); package data declared as hatch `artifacts` |
| `fixtures/target/` | §9.8 | 16 ids across all six families, 2 retired, all ten planted defects present (T-46), each flips exactly its row when removed (T-47); `golden/` is never a scan root |
| `src/speccheck/_selfcheck/` | §10, F-107 | Byte-identical to `fixtures/target/` (T-60; `tools/sync_selfcheck.py --check`) |
| Determinism | I-002 | Golden fixture reports are byte-identical across runs, paths, `--src .`, and planted temporaries (T-36); the goldens in the repository were produced by the tool and re-verified after every refactor |
| Read-only inputs | I-001 | Hash comparison before/after (T-38); only the two reports appear; `--self-check` leaves no trace (T-43) |
| Network boundary | I-006 | Socket guard never fires under `none`/`mock` (T-43); `httpx` is imported only inside `_httpx_post`, verified in the fresh venv: `import speccheck.cli` leaves `httpx` out of `sys.modules` |
| README | Phase 2 | Every command in it was run as written after it was finished (quick start on a fixture copy, the self-application run, the single-test command, `sync_selfcheck.py --check`) |

Process note for the audit trail: the build was not strictly test-first. Each §9 group's tests
were written from the spec immediately after the module they exercise; five of them failed on
first run and every failure was a defect in the *test data* (a data file citing an id it should
not, a fixture reusing a directory, an inline marker literal), not in the kernel — the kernel's
only spec deviation found by the suite was B-01, fixed in code.

## 5. Traceability matrix (§11, filled from the build)

"Realized in" lists the modules whose source cites the id (comments and the §11 realization
line in each module docstring; `cli.py`'s self-check fixture is excluded). "Verified by" maps the
spec's own §11 `T-nn` list to the concrete test functions, each of which is green and cites the
id. "Self-app" is the status from the T-48 run.

| Spec id | Realized in | Verified by | Self-app |
| --- | --- | --- | --- |
| R-01 | `extract.py` | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement`; T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored` | PASSING |
| R-02 | `extract.py`, `graph.py` | T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3`; T-25 `test_04_status::test_retired_ids_excluded_from_denominators_but_listed_once` | PASSING |
| R-03 | `extract.py` | T-08 `test_02_attribution::test_source_citations_in_code_comments_and_strings`; T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| R-04 | `attribute.py`, `extract.py` | T-09 `test_02_attribution::test_python_test_citations_attributed_to_enclosing_case`; T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level`; T-11 `test_02_attribution::test_unparseable_python_falls_back_to_file_level_with_note`; T-12 `test_02_attribution::test_non_python_test_files_get_file_level_attribution`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers`; T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| R-05 | `results.py` | T-15 `test_03_results::test_both_roots_parse_and_children_map_to_outcomes`; T-16 `test_03_results::test_classname_join_accepts_suffix_forms_and_rejects_partial_components`; T-52 `test_03_results::test_parametrized_names_join_and_empty_classname`; T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| R-06 | `graph.py` | T-20 `test_04_status::test_one_fixture_per_deterministic_status`; T-21 `test_04_status::test_step_4_mixtures`; T-47 `test_08_golden::test_removing_each_planted_defect_flips_exactly_its_row` | PASSING |
| R-07 | `graph.py`, `judge_prompt.md` | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| R-08 | `graph.py` | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| R-09 | `graph.py` | T-24 `test_04_status::test_metrics_match_hand_computed_values_on_golden` | PASSING |
| R-10 | `judge.py`, `judge_llm.py`, `judge_mock.py` | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only`; T-31 `test_05_judge::test_judge_called_once_per_eligible_edge_only`; T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-49 `test_09_self_application::test_llm_eval_labels_cover_every_judged_edge` | PASSING |
| R-11 | `graph.py` | T-27 `test_05_judge::test_step_5_downgrade_rules`; T-28 `test_05_judge::test_disabling_the_judge_only_restores_weakly_passing` | PASSING |
| R-12 | `report.py` | T-35 `test_06_reports::test_markdown_layout` | PASSING |
| R-13 | `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| R-14 | `cli.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| R-15 | `cli.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons`; T-27 `test_05_judge::test_step_5_downgrade_rules` | PASSING |
| R-16 | `attribute.py`, `extract.py`, `graph.py`, `report.py`, `results.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| R-17 | `cli.py` | T-41 `test_07_cli::test_verbosity_levels`; T-42 `test_07_cli::test_notes_quiet_by_default_and_once_at_info` | PASSING |
| R-18 | `cli.py`, `judge_llm.py` | T-43 `test_07_cli::test_no_sockets_and_self_check`; T-60 `test_07_cli::test_selfcheck_fixture_is_byte_identical_to_golden_fixture` | PASSING |
| R-19 | `cli.py`, `report.py` | T-38 `test_06_reports::test_only_the_two_reports_are_created`; T-43 `test_07_cli::test_no_sockets_and_self_check`; T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| R-20 | `extract.py`, `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| R-21 | `cli.py` | T-44 `test_07_cli::test_summary_line_format_encoding_and_numbers`; T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| R-22 | `judge_mock.py` | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only` | PASSING |
| R-23 | `cli.py`, `judge_llm.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak`; T-41 `test_07_cli::test_verbosity_levels` | PASSING |
| R-24 | `report.py` | T-37 `test_06_reports::test_metrics_recomputable_from_evidence_table`; T-48 `test_09_self_application::test_self_application_runs_on_this_repository` | PASSING |
| R-25 | `graph.py` | T-53 `test_04_status::test_family_t_semantics` | PASSING |
| R-26 | `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-54 `test_05_judge::test_llm_response_path_fences_and_prompt_hash` | PASSING |
| R-27 | `extract.py` | T-57 `test_02_attribution::test_ignore_markers` | PASSING |
| R-28 | `cli.py`, `report.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| R-29 | `cli.py` | T-44 `test_07_cli::test_summary_line_format_encoding_and_numbers` | PASSING |
| R-30 | `cli.py`, `judge.py` | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation`; T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| C-01 | `extract.py` | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement`; T-02 `test_01_extraction::test_numbers_normalize_within_family`; T-03 `test_01_extraction::test_four_digits_and_adjacent_alphanumerics_are_not_ids`; T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3`; T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored`; T-55 `test_01_extraction::test_row_and_heading_grammar_edge_cases`; T-57 `test_02_attribution::test_ignore_markers` | PASSING |
| C-02 | `extract.py` | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement`; T-06 `test_01_extraction::test_duplicate_declaration_exits_3_naming_both_lines` | PASSING |
| C-03 | `attribute.py`, `extract.py` | T-09 `test_02_attribution::test_python_test_citations_attributed_to_enclosing_case`; T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level`; T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks`; T-14 `test_02_attribution::test_several_citations_in_one_case_yield_one_edge`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers`; T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| C-04 | `results.py` | T-15 `test_03_results::test_both_roots_parse_and_children_map_to_outcomes`; T-16 `test_03_results::test_classname_join_accepts_suffix_forms_and_rejects_partial_components`; T-17 `test_03_results::test_duplicate_results_collapse_to_worst`; T-18 `test_03_results::test_unknown_results_are_unattributed_and_change_no_status`; T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3`; T-52 `test_03_results::test_parametrized_names_join_and_empty_classname`; T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| C-05 | `graph.py`, `judge.py` | T-20 `test_04_status::test_one_fixture_per_deterministic_status`; T-21 `test_04_status::test_step_4_mixtures`; T-27 `test_05_judge::test_step_5_downgrade_rules`; T-53 `test_04_status::test_family_t_semantics` | PASSING |
| C-06 | `judge.py`, `judge_llm.py`, `judge_mock.py` | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only`; T-29 `test_05_judge::test_ungrounded_answers_are_coerced_to_unknown`; T-30 `test_05_judge::test_provider_failures_yield_unknown_with_specified_rationale`; T-32 `test_05_judge::test_rationale_truncation_and_newlines`; T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-54 `test_05_judge::test_llm_response_path_fences_and_prompt_hash` | PASSING |
| C-07 | `graph.py`, `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys`; T-37 `test_06_reports::test_metrics_recomputable_from_evidence_table`; T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| C-08 | `report.py` | T-35 `test_06_reports::test_markdown_layout` | PASSING |
| C-09 | `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| C-10 | `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-54 `test_05_judge::test_llm_response_path_fences_and_prompt_hash` | PASSING |
| C-11 | `judge.py` | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation` | PASSING |
| I-001 | `cli.py`, `report.py` | T-07 `test_01_extraction::test_no_in_scope_ids_exits_3_and_writes_nothing`; T-38 `test_06_reports::test_only_the_two_reports_are_created`; T-43 `test_07_cli::test_no_sockets_and_self_check`; T-45 `test_07_cli::test_out_failures_and_temp_and_rename`; T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |
| I-002 | `attribute.py`, `extract.py`, `graph.py`, `report.py`, `results.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| I-003 | `report.py` | T-25 `test_04_status::test_retired_ids_excluded_from_denominators_but_listed_once`; T-35 `test_06_reports::test_markdown_layout` | PASSING |
| I-004 | `graph.py` | T-27 `test_05_judge::test_step_5_downgrade_rules`; T-28 `test_05_judge::test_disabling_the_judge_only_restores_weakly_passing` | PASSING |
| I-005 | `judge.py` | T-29 `test_05_judge::test_ungrounded_answers_are_coerced_to_unknown` | PASSING |
| I-006 | `cli.py`, `judge_llm.py` | T-43 `test_07_cli::test_no_sockets_and_self_check` | PASSING |
| I-007 | `cli.py`, `judge_llm.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak`; T-41 `test_07_cli::test_verbosity_levels` | PASSING |
| I-008 | `graph.py` | T-24 `test_04_status::test_metrics_match_hand_computed_values_on_golden` | PASSING |
| I-009 | `cli.py`, `report.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| I-010 | `graph.py`, `judge.py` | T-31 `test_05_judge::test_judge_called_once_per_eligible_edge_only` | PASSING |
| I-011 | `extract.py` | T-02 `test_01_extraction::test_numbers_normalize_within_family` | PASSING |
| K-01 | `cli.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons`; T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak`; T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3`; T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |
| K-02 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| K-03 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| K-04 | `extract.py` | T-03 `test_01_extraction::test_four_digits_and_adjacent_alphanumerics_are_not_ids` | PASSING |
| K-05 | `judge.py`, `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| K-06 | `cli.py`, `judge.py`, `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| K-07 | `judge.py` | T-32 `test_05_judge::test_rationale_truncation_and_newlines` | PASSING |
| K-08 | `attribute.py`, `extract.py`, `graph.py`, `report.py`, `results.py` | T-51 `test_09_self_application::test_benchmark_script_exists_and_parses` | PASSING |
| K-09 | `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| K-10 | `cli.py` | T-50 `test_07_cli::test_version_flag` | PASSING |
| K-11 | `cli.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| K-12 | `cli.py`, `judge.py` | T-61 `test_07_cli::test_judge_budget` | PASSING |
| K-13 | `judge.py` | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation` | PASSING |
| E-01 | `cli.py`, `extract.py` | T-07 `test_01_extraction::test_no_in_scope_ids_exits_3_and_writes_nothing` | PASSING |
| E-02 | `extract.py` | T-06 `test_01_extraction::test_duplicate_declaration_exits_3_naming_both_lines` | PASSING |
| E-03 | `extract.py` | T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3` | PASSING |
| E-04 | `extract.py` | T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored` | PASSING |
| E-05 | `results.py` | T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3` | PASSING |
| E-06 | `results.py` | T-17 `test_03_results::test_duplicate_results_collapse_to_worst` | PASSING |
| E-07 | `report.py`, `results.py` | T-18 `test_03_results::test_unknown_results_are_unattributed_and_change_no_status` | PASSING |
| E-08 | `graph.py` | T-22 `test_04_status::test_unrun_cases_are_listed_and_ignored` | PASSING |
| E-09 | `cli.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| E-10 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| E-11 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks`; T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement` | PASSING |
| E-12 | `attribute.py` | T-11 `test_02_attribution::test_unparseable_python_falls_back_to_file_level_with_note` | PASSING |
| E-13 | `attribute.py`, `report.py`, `results.py` | T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level` | PASSING |
| E-14 | `judge.py`, `judge_llm.py` | T-30 `test_05_judge::test_provider_failures_yield_unknown_with_specified_rationale`; T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| E-15 | `judge.py` | T-30 `test_05_judge::test_provider_failures_yield_unknown_with_specified_rationale` | PASSING |
| E-16 | `judge.py` | T-29 `test_05_judge::test_ungrounded_answers_are_coerced_to_unknown` | PASSING |
| E-17 | `judge.py` | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only` | PASSING |
| E-18 | `report.py` | T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| E-19 | `cli.py`, `graph.py`, `report.py` | T-20 `test_04_status::test_one_fixture_per_deterministic_status`; T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| E-20 | `extract.py` | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| E-21 | `cli.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| E-22 | `attribute.py` | T-14 `test_02_attribution::test_several_citations_in_one_case_yield_one_edge` | PASSING |
| E-23 | `extract.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| E-24 | `results.py` | T-52 `test_03_results::test_parametrized_names_join_and_empty_classname` | PASSING |
| E-25 | `graph.py` | T-53 `test_04_status::test_family_t_semantics` | PASSING |
| E-26 | `cli.py`, `graph.py` | T-27 `test_05_judge::test_step_5_downgrade_rules`; T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| E-27 | `results.py` | T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| E-28 | `attribute.py` | T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| E-29 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| E-30 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| E-31 | `extract.py` | T-55 `test_01_extraction::test_row_and_heading_grammar_edge_cases` | PASSING |
| E-32 | `cli.py`, `report.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| E-33 | `extract.py` | T-57 `test_02_attribution::test_ignore_markers` | PASSING |
| E-34 | `extract.py`, `report.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers`; T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| E-35 | `judge.py` | T-61 `test_07_cli::test_judge_budget` | PASSING |
| E-36 | `cli.py`, `judge.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| E-37 | `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys`; T-35 `test_06_reports::test_markdown_layout` | PASSING |
| E-38 | `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| E-39 | `cli.py` | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| E-40 | `judge.py` | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| E-41 | `cli.py`, `report.py`, `judge.py` | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase`; T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |
| T-01 | — | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement` | PASSING |
| T-02 | — | T-02 `test_01_extraction::test_numbers_normalize_within_family` | PASSING |
| T-03 | — | T-03 `test_01_extraction::test_four_digits_and_adjacent_alphanumerics_are_not_ids` | PASSING |
| T-04 | — | T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3` | PASSING |
| T-05 | — | T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored` | PASSING |
| T-06 | — | T-06 `test_01_extraction::test_duplicate_declaration_exits_3_naming_both_lines` | PASSING |
| T-07 | — | T-07 `test_01_extraction::test_no_in_scope_ids_exits_3_and_writes_nothing` | PASSING |
| T-08 | — | T-08 `test_02_attribution::test_source_citations_in_code_comments_and_strings` | PASSING |
| T-09 | — | T-09 `test_02_attribution::test_python_test_citations_attributed_to_enclosing_case` | PASSING |
| T-10 | — | T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level` | PASSING |
| T-11 | — | T-11 `test_02_attribution::test_unparseable_python_falls_back_to_file_level_with_note` | PASSING |
| T-12 | — | T-12 `test_02_attribution::test_non_python_test_files_get_file_level_attribution` | PASSING |
| T-13 | — | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| T-14 | — | T-14 `test_02_attribution::test_several_citations_in_one_case_yield_one_edge` | PASSING |
| T-15 | — | T-15 `test_03_results::test_both_roots_parse_and_children_map_to_outcomes` | PASSING |
| T-16 | — | T-16 `test_03_results::test_classname_join_accepts_suffix_forms_and_rejects_partial_components` | PASSING |
| T-17 | — | T-17 `test_03_results::test_duplicate_results_collapse_to_worst` | PASSING |
| T-18 | — | T-18 `test_03_results::test_unknown_results_are_unattributed_and_change_no_status` | PASSING |
| T-19 | — | T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3` | PASSING |
| T-20 | — | T-20 `test_04_status::test_one_fixture_per_deterministic_status` | PASSING |
| T-21 | — | T-21 `test_04_status::test_step_4_mixtures` | PASSING |
| T-22 | — | T-22 `test_04_status::test_unrun_cases_are_listed_and_ignored` | PASSING |
| T-23 | — | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| T-24 | — | T-24 `test_04_status::test_metrics_match_hand_computed_values_on_golden` | PASSING |
| T-25 | — | T-25 `test_04_status::test_retired_ids_excluded_from_denominators_but_listed_once` | PASSING |
| T-26 | — | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only` | PASSING |
| T-27 | — | T-27 `test_05_judge::test_step_5_downgrade_rules` | PASSING |
| T-28 | — | T-28 `test_05_judge::test_disabling_the_judge_only_restores_weakly_passing` | PASSING |
| T-29 | — | T-29 `test_05_judge::test_ungrounded_answers_are_coerced_to_unknown` | PASSING |
| T-30 | — | T-30 `test_05_judge::test_provider_failures_yield_unknown_with_specified_rationale` | PASSING |
| T-31 | — | T-31 `test_05_judge::test_judge_called_once_per_eligible_edge_only` | PASSING |
| T-32 | — | T-32 `test_05_judge::test_rationale_truncation_and_newlines` | PASSING |
| T-33 | — | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| T-34 | — | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| T-35 | — | T-35 `test_06_reports::test_markdown_layout` | PASSING |
| T-36 | — | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| T-37 | — | T-37 `test_06_reports::test_metrics_recomputable_from_evidence_table` | PASSING |
| T-38 | — | T-38 `test_06_reports::test_only_the_two_reports_are_created` | PASSING |
| T-39 | — | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| T-40 | — | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| T-41 | — | T-41 `test_07_cli::test_verbosity_levels` | PASSING |
| T-42 | — | T-42 `test_07_cli::test_notes_quiet_by_default_and_once_at_info` | PASSING |
| T-43 | — | T-43 `test_07_cli::test_no_sockets_and_self_check` | PASSING |
| T-44 | — | T-44 `test_07_cli::test_summary_line_format_encoding_and_numbers` | PASSING |
| T-45 | — | T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| T-46 | — | T-46 `test_08_golden::test_golden_fixture_matches_byte_for_byte` | PASSING |
| T-47 | — | T-47 `test_08_golden::test_removing_each_planted_defect_flips_exactly_its_row` | PASSING |
| T-48 | — | T-48 `test_09_self_application::test_self_application_runs_on_this_repository` | PASSING |
| T-49 | — | T-49 `test_09_self_application::test_llm_eval_labels_cover_every_judged_edge` | PASSING |
| T-50 | — | T-50 `test_07_cli::test_version_flag` | PASSING |
| T-51 | — | T-51 `test_09_self_application::test_benchmark_script_exists_and_parses` | PASSING |
| T-52 | — | T-52 `test_03_results::test_parametrized_names_join_and_empty_classname` | PASSING |
| T-53 | — | T-53 `test_04_status::test_family_t_semantics` | PASSING |
| T-54 | — | T-54 `test_05_judge::test_llm_response_path_fences_and_prompt_hash` | PASSING |
| T-55 | — | T-55 `test_01_extraction::test_row_and_heading_grammar_edge_cases` | PASSING |
| T-56 | — | T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| T-57 | — | T-57 `test_02_attribution::test_ignore_markers` | PASSING |
| T-58 | — | T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| T-59 | — | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| T-60 | — | T-60 `test_07_cli::test_selfcheck_fixture_is_byte_identical_to_golden_fixture` | PASSING |
| T-61 | — | T-61 `test_07_cli::test_judge_budget` | PASSING |
| T-62 | — | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation` | PASSING |
| T-63 | — | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| T-64 | — | T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |

## 6. Verdict

```text
Spec coverage: 170/170 IDs realized (0 deferred)
speccheck (mock): speccheck: CONFORMING - 170/170 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock
speccheck (llm):  speccheck: CONFORMING - 170/170 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=llm  [openai/gpt-4o-mini via OpenRouter, unknown_rate 0.0000]
Readiness: BUILT
Conformance: PASS WITH NOTES
```

The notes are §3 (B-01..B-15: interpretations for the spec owner to ratify), §0's D-16 default
(exit `3` on interrupt, awaiting the requester), and §2's T-49 history — with the v1.2
`max_tokens: 4000` both `qwen3:8b` and `gemma4:latest` meet the T-49 bar three runs out of three. Nothing in the specification was scoped out; O-1 is built
behind its flag and extra, O-2/O-3 are absent by the spec's own statement.
