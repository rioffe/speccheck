# Detailed implementation plan — W1: `explain` end to end

> - **Wave:** W1 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 1).
> - **Spec basis:** `SPEC.md` v1.17 (the fold at `287064a`): R-40, C-18, I-016, E-60, E-61, T-92,
>   T-93, §3.1, §3.3, §5.1, §5.4. Not edited by this wave.
> - **Gate:** `tests/test_12_explain.py` green, the whole suite green with every `check`/`impact`
>   golden byte-identical through the refactor, `ruff` clean, `--self-check` `ok`.
> - **Budget:** 180–260 production lines across `explain.py` (new) and `cli.py`; 130–190 test lines.
> - **Depends on:** nothing new. **Unlocks:** W2 (the recorded T-94 needs the surface), W3.

## 1. Objective and spec obligations

| id | obligation (≤20 words) | how this wave discharges it |
| --- | --- | --- |
| R-40 | a third subcommand running `check`'s stages and rendering one id | `cli.py`: subparser, `ExplainConfig`, `execute_explain` |
| C-18 | the stdout trace: six sections, pinned headings, reasons, verdict lines, exit codes | `explain.py`: `render_trace` and its helpers |
| I-016 | additive and read-only; statuses agree with `check` | one `_run_stages` for both subcommands; no write path; T-92 compares against the golden JSON |
| E-60 | undeclared id → exit 2; declared-but-uncited → rendered, exit 0 | `cli.py`'s id validation; the renderer's empty-block rule |
| E-61 | `--judge` carries `check`'s contract verbatim | the same `Config` fields, the same judge stage, no special case |
| T-92 | the golden trace, byte-stable, no file written | `test_12_explain.py::test_t92_*` |
| T-93 | E-60's message, the retired id, the uncited id | `test_12_explain.py::test_t93_*` |

## 2. Entry preconditions

- `287064a` is HEAD; `SPEC.md` declares 245 ids and 36 decisions; the eight new ids are `UNCITED`.
- `src/speccheck/impact.py` exposes `walk(edges, changed, depth_limit) -> WalkResult`,
  `reverify_set(edges, ids) -> tuple[ReverifyEntry, ...]`, `mark_retired(entries, index)`.
- `src/speccheck/graph.py` exposes `IdRecord` (`.spec`, `.status`, `.src`, `.tests`) and `TestEdge`
  (`.case`, `.lines`, `.outcome`, `.verdict`).
- `src/speccheck/cli.py`'s `execute` runs the stages inline (extract-spec → scan-src → scan-tests →
  map-results → graph → judge) and then builds and writes the reports.
- `fixtures/target/`: R-01 `PASSING` (a `src/calc/core.py` citation and `test_add` with a passed
  result), R-04 retired, C-02 cited in `src/` only, R-09 undeclared.

## 3. Deliverables, file by file

### 3.1 `src/speccheck/explain.py` — NEW, ~110–160 lines

```python
REASON = {...}  # C-18: status -> the C-05 step phrase, pinned per status
FILE_LEVEL = "(file-level)"
NO_RESULT = "\u2014"   # the em dash the C-08 report already uses for an unrun case

def render_trace(
    rec: IdRecord, index: SpecIndex, walk: WalkResult, reverify: tuple[ReverifyEntry, ...],
    depth: int,
) -> str:
    """C-18: the one-id trace, as a string ending in exactly one "\n"."""
```
Numbered behaviour rules: (1) the `ID` line with the `RETIRED`/`(recorded)` markers (C-18);
(2) `status:` with the C-05 reason; (3) `statement:` echoing `SpecId.text` two-space indented;
(4) `sources:` ascending by (file, line); (5) `tests:` ascending by (file, start), with the
outcome, the verdict token (`coerced` appended), `clause:`/`rationale:` only when recorded, and the
file-level form; (6) `impact (<depth>):` from the walk and the reverify set. Every section heading
is printed even when empty (E-60).

### 3.2 `src/speccheck/cli.py` — EDIT, ~70–100 lines

- `ExplainConfig(check: Config, ident: str, depth: int)` beside `ImpactConfig`.
- `Action.kind` gains `"explain"`; `Action.explain_config`.
- `build_parser()`: an `explain` subparser with a positional `ID` and the `check` flags minus
  `--out`/`--strict` (so both are rejected by omission, E-54's pattern) plus `--depth`.
- `_build_explain_config(args, verbose)`: the `check` validation reused (`Config` built with
  `out=root`), the positional id normalized and checked against `index`'s declarations later
  (E-60 needs the parsed spec, so the check happens in `execute_explain`).
- `_run_stages(config) -> _Pipeline` — the refactor: the stage sequence extracted verbatim from
  `execute`, returning `(index, graph, notes, file_lines)`. `execute` calls it and then builds the
  reports exactly as today.
- `execute_explain(config, stdout)`: `_run_stages`, then E-60's validation
  (`explain: undeclared id: <ID>`, exit `2`), then `walk`/`reverify_set`/`mark_retired`, then
  `_emit_line(render_trace(...), stdout)` and `return 0`.

### 3.3 `tests/test_12_explain.py` — NEW, ~130–190 lines

- `test_t92_explain_golden_trace_is_stable` — the fixture run twice; the exact sections asserted
  line by line (`ID R-01`, `status: PASSING (step 4: …)`, `statement:`, the `sources:` line, the
  `tests:` case with `(passed)` and `[ASSERTS]`, `impact (1):`); the `--out` directory stays empty;
  the status equals `golden/speccheck.json`'s; the two runs are byte-identical.
- `test_t93_explain_undeclared_retired_and_uncited` — `R-09` → exit `2` with E-60's message and no
  stdout; `R-04` → `ID R-04 (RETIRED)` and exit `0`; `C-02` → its reason with an empty `tests:`
  block and exit `0`; `--out`/`--strict` on the subparser → exit `2`.

## 4. Work items, in order (red → green → refactor)

- **W1-01** — RED: `test_t92_explain_golden_trace_is_stable` fails on
  `ModuleNotFoundError: speccheck.explain`. Then `explain.py` + the `cli.py` wiring; GREEN.
- **W1-02** — RED: `test_t93_explain_undeclared_retired_and_uncited` fails on the missing E-60
  message; add the id validation and the empty-block rendering; GREEN.
- **W1-03** — the refactor under green: `_run_stages` extracted; the whole suite (including every
  byte-compared golden) must stay green — that is the evidence the refactor changed no behaviour.
- **W1-04** — the wave gate; commit.

## 5. Test plan

| group | ids | what must be asserted | how it runs |
| --- | --- | --- | --- |
| `tests/test_12_explain.py` | T-92, T-93, R-40, C-18, I-016, E-60 | the six sections; byte-stability; no file written; the status agreement; E-60's message; the retired and uncited forms; the rejected flags | `pytest tests/test_12_explain.py -q` |
| whole suite | all | the refactor moved nothing: every golden byte-identical, 126 tests green | `pytest tests -q --junitxml=junit.xml` |

## 6. Gate: commands and expected results

```bash
uv run python -m pytest tests/test_12_explain.py -q          # expected: all green
uv run python -m pytest tests -q --junitxml=junit.xml        # expected: 1 failed (test_09 DECLARED_IDS 237), rest green
uv run ruff check src tests tools                            # expected: exit 0
uv run speccheck --self-check                                # expected: "self-check: ok"
uv run speccheck explain R-01 --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --root fixtures/target --out build/explain   # expected: the trace on stdout, exit 0
```

## 7. Traceability

| id | file.symbol | test | status now → after |
| --- | --- | --- | --- |
| R-40 | `cli.py` (`explain` subparser, `ExplainConfig`, `execute_explain`) | T-92, T-93 | UNCITED → PASSING |
| C-18 | `explain.render_trace` | T-92, T-93 | UNCITED → PASSING |
| I-016 | `cli._run_stages` + `execute_explain` (no write path) | T-92 | UNCITED → PASSING |
| E-60 | `cli.execute_explain` (the id validation) | T-93 | UNCITED → PASSING |
| E-61 | `cli._build_explain_config` (the judge flags) | T-94 (W2) | UNCITED → W2 |
| T-92, T-93 | `tests/test_12_explain.py` | themselves | UNCITED → PASSING |

## 8. Traps

- **The refactor is the risk.** `execute`'s stage sequence must move verbatim; the byte-compared
  goldens (T-46, T-71, T-79, T-80) are the proof, and they must be green *before* the commit.
- **`--out` on `explain` must not be silently accepted**: it is undefined on the subparser, so
  argparse rejects it (E-54's pattern) — do not add it "for symmetry".
- **E-60's message is pinned**: `explain: undeclared id: <ID>`; the id is normalized (I-011), so
  `explain r-1` on a spec declaring `R-01` finds it.
- **The trace's paths are `--root`-relative** (`to_posix_relative`), never absolute: an absolute
  path would break I-002 and leak the machine's layout into the surface.
- **`--judge none` renders `not judged`, not an empty bracket** (C-18/E-61), and a coerced verdict
  renders its ` (coerced)` suffix and its rationale.
- **No golden may be regenerated by this wave.** If a golden differs, the refactor changed
  behaviour: fix the refactor, not the golden.

## 9. Exit criteria and handoff contract

- Frozen for W2/W3: `explain.render_trace(rec, index, walk, reverify, depth) -> str`,
  `cli.ExplainConfig(check, ident, depth)`, `cli._run_stages(config)`.
- The next wave re-runs `pytest tests -q` and `--self-check` to confirm W1 is intact, then records
  T-94 against the live provider.
