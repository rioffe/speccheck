# Detailed implementation plan — W2: `related` on the request and the triage `state` (Part B)

> - **Wave:** W2 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 2).
> - **Spec basis:** `SPEC.md` v1.16, sha256
>   `0e1e7c415e25b1ef609abed14c094b11be31189a1afa034b624e85bbb2b16`-family (measured in the plan);
>   C-06, C-10, C-17, K-16, R-38, E-57, T-83. Not edited by this wave.
> - **Gate:** the whole suite green (the field is inert for every report), `ruff` clean, and T-83
>   asserting the neighbourhood's shape from the parsed spec alone.
> - **Budget:** 60–100 production lines across 4 modules; 80–140 test lines.
> - **Depends on:** W1 (the fixture and its goldens). **Unlocks:** W3's T-84 measurement, which
>   measures exactly this field.

## 1. Objective and spec obligations

| id | obligation (≤20 words) | how this wave discharges it |
| --- | --- | --- |
| R-38 | send the judge the `related` titles of the statement's `depends_on` neighbourhood, both directions, capped and ordered | `judge_llm.related_titles` builds it; `JudgeRequest.related` carries it; both consumers read that one value |
| C-06 | the request object is `{id, statement, related, declared, file, start, end, source}` | `JudgeRequest.to_json` inserts `related` after `statement` |
| C-10 | the instruction text defines `related` and its rule | shipped (v1.16 fold); T-54 already pins file == text |
| C-17 | the triage `state` carries a `Related obligations:` section (D-28b) | `jev.render_state` gains the section |
| K-16 | the triage task is built from the C-06 object | unchanged: `render_state` still reads the one request object |
| E-57 | a retired neighbour keeps its title with `(retired)` appended | the builder tags it; T-83 asserts it |
| T-83 | the request-side check: order, cap, truncation, `[]`, T ids never, absent from both reports | `tests/test_05_judge.py::test_t83_related_neighbourhood_on_request_and_triage_state` |
| T-74/T-33/T-89 | the request/triage shapes the spec now pins | their key lists and `state` expectations are updated |

## 2. Entry preconditions

- W1 committed; `golden/judge_labels.json` has 39 entries; `--self-check` is `ok`.
- `judge.py` has `JudgeRequest` (frozen dataclass, `to_json`), `build_request`, `run_judge`.
- `jev.py` has `render_state(req)` and `build_body(req, model)`.
- `cli.py`'s judge stage builds one `JudgeRequest` per `eligible_edges(graph)` entry and holds the
  parsed `index: SpecIndex` in scope (`index.edges`, `index.by_id()`).

## 3. Deliverables, file by file

### 3.1 `src/speccheck/judge.py` — EDIT (~12 lines)

```python
@dataclass(frozen=True)
class JudgeRequest:
    id: str
    statement: str
    testcase: TestCase
    declared: bool
    source: str
    related: tuple[str, ...] = ()   # R-38/C-06: request-side; never in a report (T-83)
```
`to_json` emits `"related": list(self.related)` between `statement` and `declared`.
`build_request(..., related: tuple[str, ...] = ())` passes it through.

### 3.2 `src/speccheck/judge_llm.py` — EDIT (~55 lines)

```python
RELATED_MAX = 8             # R-38
RELATED_TITLE_MAX = 160     # R-38
RETIRED_TAG = " (retired)"  # E-57
_ID_ORDER = {f: i for i, f in enumerate("RCIKET")}   # C-07's id order

def related_titles(ident: str, index: SpecIndex) -> tuple[str, ...]:
    """R-38: the C-12 depends_on neighbourhood, both directions, in-scope R/C/I/K/E only,
    the statement's own references first, at most RELATED_MAX, each title collapsed and
    tail-truncated to RELATED_TITLE_MAX with '…', a retired neighbour tagged (E-57)."""
```
Rules: own references (`edge.src == ident`) first, then the ids that name it (`edge.dst ==
ident`), each group in C-07 id order, `T` targets dropped, the ident itself dropped, duplicates
collapsed, then the first 8. A title longer than 160 characters is cut to 159 + `…`.

### 3.3 `src/speccheck/jev.py` — EDIT (~8 lines)

`render_state` becomes the four-part C-17 template: id, statement, `Related obligations:` +
newline-joined titles (empty string when `[]`), then the test-file line. `build_body` unchanged.

### 3.4 `src/speccheck/cli.py` — EDIT (~4 lines)

`build_request(..., edge.declared, related=related_titles(rec.id, index))`.

### 3.5 `tests/test_05_judge.py` — EDIT (+~120 lines)

- New: `test_t83_related_neighbourhood_on_request_and_triage_state` — a hand-written spec with one
  id naming three and named by seven (own three first, then dependents in C-07 order, the ninth
  dropped), a 200-character title cut to 160 + `…`, an id with no edges sending `[]`, a T id never
  in `related`, a retired neighbour tagged `(retired)`, the same list in the LLM user message and
  in `jev.render_state`, and `related` absent from `speccheck.json` and from the Markdown report.
- `test_llm_request_carries_heading_body_statement` (T-74): the key list gains `related`.
- `test_t33_*` (T-33) and the T-89 test: the body/`state` expectations gain the field/section.

## 4. Work items, in order (red → green → refactor)

- **W2-01** — RED: `test_t83_related_neighbourhood_on_request_and_triage_state` fails (no
  `related_titles`, no `related` key, no `Related obligations:` section). Implement §3.1–§3.4 in
  that order; GREEN.
- **W2-02** — RED: the T-74 key-list assertion fails once `to_json` carries `related`; update it
  and the T-33/T-89 expectations; GREEN.
- **W2-03** — REFACTOR: one constant for the id order if a second copy appears; re-run the wave
  gate; commit.

## 5. Test plan

| group | ids | what must be asserted | how it runs |
| --- | --- | --- | --- |
| `test_05_judge.py` | T-83, T-74, T-33, T-54, T-89 | the neighbourhood's order/cap/truncation/tag; the key list; the triage `state` section; the prompt hash unchanged | `pytest tests/test_05_judge.py -q` |
| `test_07_cli.py` | T-90, T-41 | no new flag; DEBUG output unchanged; the key never echoed | `pytest tests/test_07_cli.py -q` |
| whole suite | all | no report byte changes (the field is request-side) | `pytest tests -q --junitxml=junit.xml` |

## 6. Gate: commands and expected results

```bash
uv run python -m pytest tests/test_05_judge.py tests/test_07_cli.py -q   # expected: all green
uv run ruff check src tests                                              # expected: exit 0
uv run python -m pytest tests -q --junitxml=junit.xml                    # expected: 1 failed (test_09 DECLARED_IDS), rest green
uv run speccheck --self-check                                            # expected: "self-check: ok"
```

## 7. Traceability

| id | file.symbol | test | status now → after |
| --- | --- | --- | --- |
| R-38 | `judge_llm.related_titles`, `judge.JudgeRequest.related`, `jev.render_state` | T-83, T-84 | UNCITED → PASSING |
| C-06 | `judge.JudgeRequest.to_json` | T-83, T-74, T-33 | PASSING → PASSING |
| C-17 | `jev.render_state` | T-89, T-83 | PASSING → PASSING |
| E-57 | `judge_llm.related_titles` (the tag) | T-83 | UNCITED → PASSING |
| T-83 | `tests/test_05_judge.py` | itself | UNCITED → PASSING |
| T-84 | `SPEC_BUILD_REPORT.md` §0h | the W3 presence check | UNCITED → W3 |

## 8. Traps

- **`related` must not reach a report**: it is on the request only; `report.py`, `graph.py` and
  `judge_mock.py` never read it. A field that leaks into `speccheck.json` breaks T-83 and every
  golden (they are byte-compared).
- **The cap is total, not per group**: own references first, then dependents, then cut at 8 — not
  four of each.
- **Order is C-07's**, i.e. family `R, C, I, K, E, T` then number — not lexicographic (`E-10`
  sorts after `E-9` numerically but before it lexicographically).
- **Truncate before tagging**: `(retired)` is appended to the already-truncated title (E-57), so a
  160-character retired title is 170 characters in the request.
- **The triage `state` is byte-pinned by T-89**: the section goes between the statement and the
  test-file line, with a blank line when `related` is `[]`.
- **The mock judge ignores `related`** (R-16/R-22): its verdicts on the fixture stay byte-identical.

## 9. Exit criteria and handoff contract

- Frozen symbols for W3 and any later wave:
  `judge_llm.related_titles(ident: str, index: SpecIndex) -> tuple[str, ...]`,
  `JudgeRequest.related: tuple[str, ...]`, `jev.render_state(req) -> str`.
- The next wave re-runs the whole suite and `--self-check` to confirm W2 is intact, then measures
  T-84 with the field in place.
