# Detailed implementation plan — W2: Consumers, goldens, version

> - **Wave:** W2 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 2 — "Consumers, goldens, version").
> - **Spec basis:** `SPEC.md` v1.8, sha256 `d153bde1cafba8e2e726a4bd8b95938fca6ae7d093f7343ce36715eec1af770a`. Not edited by this wave.
> - **Gate:** full suite green (84 passed), `--self-check` ok, speccheck Phase A `CONFORMING 190/190`, `--version` `1.8.0`.
> - **Budget:** +11–18 production lines across `report.py`, `cli.py`, `judge_prompt.md`, `__init__.py`; +120–180 test lines; both goldens and `_selfcheck/` regenerated.
> - **Depends on:** W1's frozen symbols (`SpecId.title/.text`, `SpecIndex.notes`). **Unlocks:** W3 (a tree whose Phase A is clean).

## 1. Objective and spec obligations

| spec id | obligation | how this wave discharges it |
|---|---|---|
| R-33 (other half) | JSON `statement` = `text`, `title` key; Markdown renders `title`; judge gets `text` | `report.py`, `cli.py` (already `rec.spec.text`) |
| C-06 | `JudgeRequest.statement` = `SpecId.text`, wire keys unchanged | no code change; T-74 asserts |
| C-07 | `"title"` before `"statement"`, `schema_version` `"1.1"`, key order | `report.py.build_report`, `SCHEMA_VERSION` |
| C-08 | Statement cell renders `title` | `report.py` Markdown per-ID row |
| C-10 | prompt file gains the any-clause bullet, byte-equal to the spec block | `judge_prompt.md` |
| K-14 / E-46 | the Note reaches the report | `cli.py` extends `notes` from `index.notes` |
| T-73 | goldens, `title`, named values, Statement-cell property, `_selfcheck` | `tests/test_08_golden.py` |
| T-74 | wire `statement` for a heading-declared id byte-equal to `SpecId.text`; new prompt hash | `tests/test_05_judge.py` |
| T-34, T-46, T-48, T-54, T-60, T-71 | re-green under the new schema / count / prompt | updated literals → rules |
| K-10 | `--version` equals package metadata | `__init__.py` `1.8.0` |

## 2. Entry preconditions

- W1 gate green (`uv run python -m pytest tests/test_01_extraction.py -q` → 10 passed).
- `report.py.SCHEMA_VERSION`, `build_report`, Markdown per-ID row at `rec["statement"]`; `cli.py` `notes` list and `parse_spec` call; `tests/test_06_reports.py::ID_KEYS`; `tests/test_09_self_application.py` count `183`; `tools/sync_selfcheck.py`.
- `SPEC.md` C-10 block text (the source of truth for `judge_prompt.md`).

## 3. Deliverables, file by file

### 3.1 `src/speccheck/report.py` — EDIT, +4–8
`SCHEMA_VERSION = "1.1"`; id record `{"id", "family", "title": rec.spec.title, "statement": rec.spec.text, "line", ...}` (C-07 order); Markdown row uses `rec["title"]` (C-08).
### 3.2 `src/speccheck/cli.py` — EDIT, +2–4
After `parse_spec`: `notes.extend(index.notes)` (K-14, E-46). Judge request line unchanged (C-06 passthrough).
### 3.3 `src/speccheck/judge_prompt.md` — EDIT, +3
Append the C-10 bullet exactly as `SPEC.md` prints it (T-54 compares the file with the spec block byte for byte).
### 3.4 `src/speccheck/__init__.py` — EDIT, 1 line: `__version__ = "1.8.0"`, docstring `v1.8`.
### 3.5 Goldens — REGENERATED after 3.1–3.3: `fixtures/target/golden/{speccheck.json,SPEC_CONFORMANCE_REPORT.md}` and `fixtures/target-swift/golden/{speccheck.json,SPEC_CONFORMANCE_REPORT.md,summary.txt}` by running the tool with T-46's / T-71's exact arguments; `src/speccheck/_selfcheck/` via `uv run python tools/sync_selfcheck.py`. Expected diff: `schema_version`, one `title` per id, heading-declared `statement`s; Markdown files byte-identical (asserted by T-73's property, recorded in W3's report).

## 4. Work items, in order

- **W2-01 (test first)** — `tests/test_08_golden.py::test_goldens_carry_title_and_markdown_renders_title` (T-73): after a run over `fixtures/target` and `fixtures/target-swift`, `schema_version == "1.1"`; every id has `title`; `C-01.statement == C-01.title + "\nThe error message MUST name the dividend."` (target) / `"\nThe error MUST carry the dividend."` (swift); `C-02.statement == C-02.title`; every §3 Markdown row's Statement cell equals its `title` and contains no `\n`; no row contains `TRUNCATION_MARKER`; id sets equal. Expected first run: `KeyError: 'title'`.
- **W2-02** — `report.py` 3.1; `test_06_reports.py`: `ID_KEYS` gains `"title"`, `"1.0"` literal → `report.SCHEMA_VERSION`. Run T-73 → the JSON clauses pass; T-46/T-71 byte comparisons now fail (goldens stale) — expected.
- **W2-03** — `cli.py` 3.2. (No golden exercises the cap; T-72 already proves the Note text.)
- **W2-04 (test first)** — `tests/test_05_judge.py::test_llm_request_carries_heading_body_statement` (T-74): project with `### C-01 Widget` + fenced block + prose; recorded stub; assert `payload["statement"] == index.by_id()["C-01"].text` and starts with `"Widget\n"`, keys exactly `{id, statement, file, start, end, source}`, system message == prompt file. Expected first run: passes only if the body already flows — verify it fails first by asserting against the *file's* prompt hash including the new bullet (which 3.3 has not added yet) → `AssertionError` on the hash. Then **W2-05** adds the bullet to `judge_prompt.md`; T-54 and T-74 green.
- **W2-06** — regenerate goldens (3.5); `tools/sync_selfcheck.py`; `test_09_self_application.py` `183 → DECLARED_IDS = 190` with a comment naming SPEC v1.8. Run T-46, T-71, T-60, T-48.
- **W2-07** — `__init__.py` 3.4; `uv run speccheck --version`.
- **W2-08** — the gate below; `git diff --stat` reviewed against the plan's "unchanged files" rule.

## 5. Test plan

| group / file | spec ids | what must be asserted | how it runs |
|---|---|---|---|
| `test_08_golden.py` T-73 | R-33, C-07, C-08, T-46, T-71 | §4 W2-01 | `uv run python -m pytest tests/test_08_golden.py -q` |
| `test_05_judge.py` T-74 | R-33, C-06, C-10, R-26 | §4 W2-04 | `uv run python -m pytest tests/test_05_judge.py -q` |
| `test_06_reports.py` T-34 | C-07 | key order incl. `title`, schema from the constant | `uv run python -m pytest tests/test_06_reports.py -q` |
| `test_09_self_application.py` T-48 | R-24 | 190 declared | full suite |

## 6. Gate: commands and expected results

1. `uv run python -m pytest tests -q --junitxml=junit.xml` — expected: `84 passed`, exit 0, no skips, no warnings.
2. `uv run ruff check src tests && uv run ruff format --check src tests` — expected: clean.
3. `uv run speccheck --self-check` — expected: `self-check: ok`, exit 0.
4. `uv run python tools/sync_selfcheck.py --check` — expected: no output, exit 0.
5. `uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck` — expected: `speccheck: CONFORMING - 190/190 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock`, exit 0.
6. `uv run speccheck --version` — expected `speccheck 1.8.0`.
7. `git diff --stat HEAD~1` — expected: no hunk in `graph.py`, `results.py`, `attribute.py`, `swift.py`, `judge_mock.py`, `judge.py`, `judge_llm.py`.

## 7. Traceability

| spec id | file.symbol | test | status now → after W2 |
|---|---|---|---|
| R-33 | `report.py.build_report`, `cli.py.run_check` | T-72, T-73, T-74 | UNTESTED → PASSING |
| C-06 | `judge.py.JudgeRequest` (unchanged) | T-74 (+existing) | PASSING → PASSING |
| C-07 | `report.py` | T-34, T-73 | PASSING → PASSING |
| C-08 | `report.py.to_markdown` | T-35, T-73 | PASSING → PASSING |
| C-10 | `judge_prompt.md` | T-54, T-74 | FAILING (baseline) → PASSING |
| T-73, T-74 | — | themselves | UNCITED → PASSING |
| T-48 | `test_09` | itself | FAILING (baseline) → PASSING |

## 8. Risks, traps, and the structural rules this wave must not break

- **Regenerate goldens last, from the tool, and read the diff.** Expected diff is exactly `schema_version`, `title` keys, heading `statement`s; anything else (a changed status, a changed Note order) is a W1 defect — fix it there (plan §6 row 1).
- **`_selfcheck/` is a byte copy.** Run `sync_selfcheck.py` after the golden regeneration, not before; T-60 fails otherwise.
- **The prompt file is compared byte for byte with the spec block** (T-54): copy the bullet from `SPEC.md`, including the two-space continuation indent and the ASCII hyphen.
- **Do not emit `title` in the Markdown as a new column** — the header stays `Statement`; only the cell's source changes (C-08, T-73's byte-identical claim).

## 9. Exit criteria and handoff contract

Frozen after W2: `report.SCHEMA_VERSION == "1.1"`, id-record key order `id, family, title, statement, line, status, src, tests, unrun`; `judge_prompt.md` content; both goldens; `__version__ == "1.8.0"`. W3 re-runs gate commands 1 and 5 before Phase B.
