# speccheck — Specification Conformance Checker

For every ID a `SPEC.md` declares (R-nn, C-nn, I-nnn, K-nn, E-nn, T-nn), `speccheck` finds where
the source and test trees cite it, joins those citations to a JUnit XML results file, and writes a
conformance report in which every ID has exactly one status and every status points at a file and
line. An optional model-backed *judge* — off by default — can only ever downgrade a `PASSING` ID
to `WEAKLY_PASSING`, with cited evidence; it can never upgrade anything.

This repository implements `SPEC.md` (v1.2) in full. The specification was written and reviewed
in the `spec_engineering_primer` repository with the three skills under `skills/`, which is why
its header still cites them as `../skills/...`; here they sit next to it.
The LLM judge speaks the OpenAI-compatible chat-completions wire format that Ollama serves
locally, so no cloud account is needed for `--judge llm`.

## Setup

- Python 3.12 and [`uv`](https://docs.astral.sh/uv/). A `.python-version` pins 3.12.
- The kernel has no dependencies beyond the standard library. `httpx` is only pulled in by the
  `llm` extra and only imported when `--judge llm` is used.

```bash
uv sync --extra dev                # kernel + test tooling (pytest, hypothesis, ruff, httpx)
uv sync --extra dev --extra llm    # same, with the LLM judge extra declared explicitly
```

Everything except `--judge llm` is offline and deterministic: two runs over identical inputs
produce byte-identical reports. `--judge llm` needs a reachable chat-completions endpoint and
three environment variables (see *LLM judge via Ollama*).

## Quick start

Run the checker on a copy of the golden fixture that ships in this repository:

```bash
cp -r fixtures/target /tmp/calc && cd /tmp/calc
uv run --project "$OLDPWD" speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --out reports
# speccheck: NOT CONFORMING - 8/14 passing (57.1%), 1 failing, 1 skipped, 1 weak, 1 unverified, 1 untested, 1 uncited; 1 dangling, 1 stale; judge=mock
```

(The fixture is *meant* to fail: it plants one example of every status and defect the checker
can report. `--out` must lie inside `--root`, which defaults to the current directory.)

Then open `SPEC_CONFORMANCE_REPORT.md` and `speccheck.json` in the output directory, or run the
same check on this repository itself:

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --out build/selfapp
# speccheck: CONFORMING - 161/161 passing (100.0%), ...; 0 dangling, 0 stale; judge=mock
```

## Usage

```text
speccheck check --spec SPEC.md [--src DIR]... [--tests DIR]... [--results junit.xml]
                [--root DIR] [--out DIR] [--judge none|mock|llm] [--strict]
                [--max-unknown FRACTION] [--judge-concurrency N] [--judge-budget SECONDS]
                [--verbose [INFO|DEBUG]]
speccheck --self-check [--verbose [INFO|DEBUG]]
speccheck --version
speccheck --help
```

| Flag | Meaning |
| --- | --- |
| `--spec FILE` | Required. The specification (UTF-8; invalid bytes are replaced and noted). |
| `--src DIR` | Repeatable. Source roots to scan for citations. Default: `src` if it exists. |
| `--tests DIR` | Repeatable. Test roots; Python files are split into test cases with `ast`, anything else is attributed at file level. Default: `tests` if it exists. |
| `--results FILE` | JUnit XML. Without it no ID can be better than `UNVERIFIED`. |
| `--root DIR` | Base for every path in the reports (default `.`). Every other path must resolve inside it. Command-line paths themselves are resolved against the current directory. |
| `--out DIR` | Where `SPEC_CONFORMANCE_REPORT.md` and `speccheck.json` go (default `.`; created if missing; must be inside `--root`). |
| `--judge MODE` | `none` (default), `mock` (deterministic: assertion tokens in the test span), `llm`. |
| `--strict` | Exit `1` unless every in-scope ID is `PASSING` and there are no dangling or stale citations; with `--judge llm`, also requires an available judge and `unknown_rate <= --max-unknown`. |
| `--max-unknown` | Decimal in `[0, 1]`, default `0.2`; only consulted under `--strict --judge llm`. |
| `--judge-concurrency N` | `1..32`, default `4`; LLM requests in flight at once. |
| `--judge-budget SECONDS` | `0..86400`, default `0` (unlimited); wall-clock bound on the judge stage. Edges not started before the deadline become `UNKNOWN` (`judge: budget`). |
| `--verbose [LEVEL]` | Diagnostics to stderr. Bare = `INFO` (stage counts, timings, judge URL/model, notes). `DEBUG` adds every judge request (`judge>`) and raw response (`judge<`) with the API key redacted. Nothing is written to stderr otherwise. |
| `--self-check` | Copies the packaged fixture to a temporary directory, installs a socket guard, runs the pinned `check` in-process, compares the output byte-for-byte with the packaged goldens, removes the directory, and prints `self-check: ok`. |

**Statuses** (one per declared ID): `RETIRED` (struck-through declaration; excluded from
denominators), `UNCITED`, `UNTESTED` (source citations only), `UNVERIFIED` (test citations but no
result), `FAILING`, `SKIPPED`, `PASSING`, and — judge only — `WEAKLY_PASSING`. A `T-nn` ID is
judged by test citations alone; source citations of it are recorded but never change its status.

**Exit codes:** `0` conforming, `1` not conforming, `2` usage error (bad flag or value, missing
`--spec`, a path outside `--root`, missing judge environment), `3` input-contract violation
(no in-scope IDs, an ID declared twice or both retired and kept, malformed JUnit XML, unwritable
`--out`). On exit `2`/`3` no report is written. On exit `0`/`1` exactly one summary line goes to
stdout:

```text
speccheck: <STATUS> - <passing>/<in_scope> passing (<pct>%), <failing> failing, <skipped> skipped, <weak> weak, <unverified> unverified, <untested> untested, <uncited> uncited; <dangling> dangling, <stale> stale; judge=<mode>[ (unavailable)| (unknown_rate 0.xxxx > max_unknown 0.xxxx)]
```

**Citations are literal.** Any `R-07`-shaped token in any text file under a scan root is a
citation, in code, comments, and strings alike. Two opt-outs exist: a line containing
`speccheck:ignore` yields no citations, and a file whose first three lines contain
`speccheck:ignore-file` is not scanned at all. Files over 2 MiB, files with a NUL byte in their
first 8 KiB, symlinks, and the directories `.git .hg .svn node_modules __pycache__ .venv venv`
(and any dot-directory) are skipped. The spec, the results file, and the checker's own reports
and temporaries are never scanned.

### LLM judge via Ollama

`--judge llm` posts one OpenAI-compatible chat-completions request per (test case, ID) edge of a
`PASSING` ID whose test passed. [Ollama](https://ollama.com) serves exactly that shape:

```bash
ollama serve                                # if it is not already running
ollama pull qwen3:8b                        # any chat model you like

export SPECCHECK_JUDGE_URL=http://localhost:11434/v1/chat/completions
export SPECCHECK_JUDGE_MODEL=qwen3:8b
export SPECCHECK_JUDGE_API_KEY=ollama       # required by the contract; Ollama ignores its value
export SPECCHECK_JUDGE_TIMEOUT=120          # optional, seconds, 1..300, default 30

uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm --strict --out reports
```

Any other OpenAI-compatible endpoint works the same way; the request body is pinned by the spec
(`model`, `temperature: 0`, `max_tokens: 4000`, a system message equal to
`src/speccheck/judge_prompt.md`, and a user message carrying the line-numbered test source). The
SHA-256 of the instruction text is recorded in `speccheck.json` as `judge_prompt_sha256`. A
missing variable is a usage error; the key never appears in any output.

Every answer is validated by the kernel: an unknown verdict, an `ASSERTS` without evidence, or
evidence outside the judged span is coerced to `UNKNOWN` (`coerced: true`), and a provider
failure yields `UNKNOWN` with `judge: unavailable | timeout | http <code> | malformed response`.

To evaluate a model on the golden fixture's hand-labeled edges (T-49; three independent runs):

```bash
uv run python tools/eval_judge.py --model qwen3:8b --runs 3 --verbose
```

#### Thinking models and `max_tokens` (D-07, resolved in v1.2)

v1.1 pinned `max_tokens: 400`. Thinking models — `qwen3:8b`, `gemma4`, and similar — spend that
budget on their reasoning (which Ollama returns separately in `message.reasoning`), so for a hard
edge the `content` came back empty or truncated and the kernel recorded the edge as `UNKNOWN`
with `judge: malformed response` and `coerced: true` (E-15). In the recorded v1.1 T-49 runs
(`SPEC_BUILD_REPORT.md` §2) this hit one edge of nine on every run of both models, and under
`--strict --judge llm` two such edges in nine pushed `unknown_rate` past the default
`--max-unknown 0.2` even though every decided verdict was correct.

SPEC v1.2 raises the pinned value to `max_tokens: 4000` (C-06, T-33, D-07). With that value
`qwen3:8b` and `gemma4:latest` pass T-49 three runs out of three at 100 % accuracy and zero
`UNKNOWN`. The number is part of the byte-exact request body T-33 pins, so it is not a
configuration knob; if a different model still returns malformed content, the options remain the
same as before:

- raise the threshold, e.g. `--max-unknown 0.3`, if a larger share of `UNKNOWN` edges is
  acceptable for your gate (each one is listed with its rationale in report §8);
- pick a model that emits the JSON object cleanly — note that the small models tried here
  (`llama3.2`, `phi4-mini`, `gemma3n`) did *not*: they produced malformed JSON on most or all
  edges;
- read the raw replies with `--verbose DEBUG` (`judge<` lines) to see which of the two it is.

## Artifacts

Both reports are rendered in memory and written atomically (temporaries with a per-run nonce,
renamed JSON-then-Markdown; either both exist afterwards or neither).

| File | Contract | Notes |
| --- | --- | --- |
| `speccheck.json` | C-07, `schema_version` `"1.0"` | Key order fixed; every ratio is a Decimal quantized to four places (`0.9000`), `null` on a zero denominator; every `tests[]` entry has a `verdict` key (`null` when not judged); no timestamps, absolute paths, or durations. `exit_code` is a pure function of the rest of the document plus `strict`. |
| `SPEC_CONFORMANCE_REPORT.md` | C-08 | Nine sections: verdict line, metrics, per-ID evidence (retired rows struck through, `(file)` for file-level cases, `—` for unjudged edges), dangling, stale, unattributed results, unrun citations, judge details (judge enabled only), notes. |

Diagnostics use Python `logging` (logger `speccheck`, one stderr handler, format
`LEVEL message`), level `ERROR` by default. Nothing is ever logged at `WARNING`.

## Project layout

```text
SPEC.md                         the specification (v1.2; the source of truth)
pyproject.toml                  package `speccheck`, console script, extras [llm] and [dev]
src/speccheck/
  __init__.py                   __version__ (1.2.0, mirrors the spec version)
  __main__.py                   `python -m speccheck`
  cli.py                        argument parsing, path validation, pipeline wiring, exit codes, --self-check
  extract.py                    ID grammar, SPEC.md declarations/retirement/fences, tree walking, citations
  attribute.py                  test-case delimitation (Python `ast`, fallback) and citation attribution
  results.py                    JUnit XML parsing and the classname/join_name join
  graph.py                      status algorithm (C-05), edge selection for the judge, metrics (C-07)
  judge.py                      JudgeRequest/Verdict types, validation, concurrency + budget runner
  judge_mock.py                 deterministic assertion-token judge
  judge_llm.py                  OpenAI-compatible/Ollama provider, env config, response parsing
  judge_prompt.md               the normative C-10 instruction text (package data)
  report.py                     JSON and Markdown renderers, summary line, exit rule, atomic writer
  _selfcheck/                   byte-identical copy of fixtures/target/ (package data for --self-check)
fixtures/target/                golden fixture: SPEC.md, src/, tests/, junit.xml, golden/{speccheck.json,
                                SPEC_CONFORMANCE_REPORT.md, judge_labels.json}
tests/
  conftest.py                   in-process CLI runner and project builder
  test_01_extraction.py         §9.1  T-01..T-07, T-55
  test_02_attribution.py        §9.2  T-08..T-14, T-56, T-57
  test_03_results.py            §9.3  T-15..T-19, T-52, T-58
  test_04_status.py             §9.4  T-20..T-25, T-53
  test_05_judge.py              §9.5  T-26..T-33, T-54
  test_06_reports.py            §9.6  T-34..T-38
  test_07_cli.py                §9.7  T-39..T-45, T-50, T-59, T-60, T-61
  test_08_golden.py             §9.8  T-46, T-47
  test_09_self_application.py   §9.9  T-48; §9.10 T-51 and §9.11 T-49 presence checks
  data/markers/                 the only files that contain the literal ignore markers
tools/
  bench.py                      K-08 benchmark (T-51; recorded, not CI-gated)
  eval_judge.py                 T-49 LLM evaluation against Ollama (opt-in)
  sync_selfcheck.py             copies fixtures/target/ into src/speccheck/_selfcheck/ (guarded by T-60)
SPEC_BUILD_REPORT.md            the Phase 3 conformance audit
ARCHITECTURE.md                 module-by-module design with data-flow, data-model, and sequence diagrams
skills/
  spec-writing/SKILL.md         how a SPEC.md is written (the ID taxonomy speccheck consumes)
  spec-review/SKILL.md          how a spec is reviewed before it is built
  spec-build/SKILL.md           how a spec is built and audited (the process this tool automates)
spec2pdf.sh                     renders a spec/doc to PDF: TOC, mermaid, clickable IDs, 1in margins
scripts/xref_preprocess.py      --click support: rewrites ID mentions into PDF jump-links
```

## Rendering PDFs

`spec2pdf.sh` wraps `pandoc` + XeLaTeX with the spec-friendly options on by default
(`--toc --mermaid --click --margin 1in`); each can be switched off with `--no-toc`,
`--no-mermaid`, `--no-click`, and `--margin` takes another value. It needs `pandoc`, a TeX
distribution with `xelatex`, and — for mermaid diagrams — `mermaid-filter` plus a Chrome/Chromium
(auto-detected, or set `PUPPETEER_EXECUTABLE_PATH`).

```bash
./spec2pdf.sh SPEC.md            # -> SPEC.pdf
./spec2pdf.sh ARCHITECTURE.md    # -> ARCHITECTURE.pdf
```

## Verification

```bash
uv run python -m pytest tests -q --junitxml=junit.xml     # the §9 suite (70 tests); junit.xml feeds self-application
uv run ruff check src tests tools                          # lint
uv run speccheck --self-check                              # packaged golden fixture, in-process, no sockets
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --out build/selfapp
uv run python tools/bench.py                               # K-08 (recorded)
uv run python tools/eval_judge.py --model qwen3:8b         # T-49 (opt-in, needs Ollama)
uv run python tools/sync_selfcheck.py --check              # _selfcheck/ still equals fixtures/target/
```

Run one test with `uv run python -m pytest tests/test_04_status.py::test_family_t_semantics -q`.

## Scope

The full specification is implemented; nothing was scoped out. The optional LLM judge (O-1) is
built behind the `--judge llm` flag and the `[llm]` extra. Additional language adapters (O-2) and
non-CLI surfaces (O-3) are, as the spec states, not part of v1.2: non-Python test files get
file-level attribution. Interpretations the build had to make where the spec was silent or
inconsistent are listed in `SPEC_BUILD_REPORT.md` §3.
