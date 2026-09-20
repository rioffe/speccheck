# W3 — evidence, docs, and the final gates

## 1. Ids discharged

T-91 (the recorded calibration: presence check in the suite + the real measurement recorded), and
the documentation/conformance obligations of the increment (README, `SPEC_BUILD_REPORT.md`, §11
rows, the verdict block).

## 2. Entry preconditions

W1 and W2 committed; the whole suite green; the mock gate CONFORMING with 233/233.

## 3. Deliverables

- `tests/test_09_self_application.py::test_t91_recorded_calibration_is_measured_and_recorded`
  (presence check: the §0g bucket table exists in `SPEC_BUILD_REPORT.md`, has at least three
  bucket rows, and names the C-17 model and `judge_prompt_sha256`), plus `DECLARED_IDS = 233`
  with the per-version comment the file's convention keeps.
- `README.md`: `--jev-pre-triage`, both `--judge-budget` grammars, the four `SPECCHECK_JEV_*`
  variables, what the pass does and does not do (I-015), and the recorded-measurement pointer.
- `SPEC_BUILD_REPORT.md`: a §0g increment section (the T-91 measurement: model, date, buckets,
  the summary lines), the new ids' §4/§5 evidence rows, and the §6 verdict block.
- The final gate runs, recorded verbatim: `pytest tests -q --junitxml=junit.xml`,
  `ruff check src tests`, `speccheck --self-check`, `check --judge mock --strict`,
  `check --judge llm --strict`.

## 4. Work items

- **W3-01** — the T-91 presence check (RED first: the file has no §0g yet).
- **W3-02** — the real T-91 measurement: `check --judge llm --strict` over this repository's own
  tree, then one C-17 request per committed edge, then the bucket table
  (`p(e) ≥ 0.95`, `0.80–0.95`, `0.60–0.80`, `< 0.60`) of agreement with the recorded verdicts.
  Record the model, the date, `judge_prompt_sha256`, the bucket sizes and the monotonicity.
- **W3-03** — README and `SPEC_BUILD_REPORT.md`; regenerate the root `SPEC_CONFORMANCE_REPORT.md`
  from the final mock run for the reader who opens the file next to the spec.
- **W3-04** — the final gates, both phases, and the verdict block.

## 5. Test plan

The presence check asserts the artifact's shape, not the measurement's outcome (T-91 is
non-gating by its own row). Every README command is run as written.

## 6. Gate

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
uv run ruff check src tests
uv run speccheck --self-check
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm --strict --out build/speccheck-llm
```

## 7. Traceability

T-91 PASSING (presence check + §0g); every §11 row of the increment checked against
`speccheck.json`; no dangling edge.

## 8. Traps

- Phase B on this repository is model-sensitive (D-07/D-08): record the model, and if a model
  yields `WEAKLY_PASSING` ids, say which and why rather than raising `--max-unknown`.
- The T-91 measurement's judge run and the triage run are two different models
  (`SPECCHECK_JUDGE_MODEL` vs `SPECCHECK_JEV_MODEL`); name both.
- Do not paste the Jev key into the report or the README; the bucket table needs no credential.

## 9. Exit criteria

Both phases' summary lines pasted verbatim, the verdict block written, the increment committed
(`feat(speccheck): W3 — the recorded calibration, README and the conformance report (T-91)`).
