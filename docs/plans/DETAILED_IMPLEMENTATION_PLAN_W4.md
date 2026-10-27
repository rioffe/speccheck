# Detailed implementation plan — W4: prove it

> - **Wave:** W4 of W1–W4 (`IMPLEMENTATION_PLAN.md` §4 item 4).
> - **Spec basis:** `SPEC.md` v1.23.1; edited only by a recorded `fix(spec):` if the audit finds a defect.
> - **Gate:** full suite green; Phase A and Phase B both `CONFORMING`; recorded runs recorded or named pending.
> - **Budget:** 1 production line (`__version__`). **Depends on:** W1–W3.

## 1. Objective and spec obligations

| id | obligation | how |
|---|---|---|
| T-48, K-10 | self-application all PASSING; version 1.23.1 | `DECLARED_IDS = 300`, `__init__.py`, README/article claims |
| T-112 *(recorded)* | `check --strict` before/after over this repo + two projects (§7 fork) | run with v1.22 (`main`) and v1.23.1 builds; record counts |
| T-117 *(recorded)* | one real jest + jest-junit run, nested describe | scratch dir, `npm install jest jest-junit`, record versions; check in the fixture string |
| T-49 *(recorded)* | three fresh runs under the new prompt hash | `tools/eval_judge.py` with `openai/gpt-6-luna-pro` |
| T-84, T-94 *(recorded)* | re-recorded under the new `judge_prompt_sha256` (their presence checks pin the shipped digest; added during W1) | the runs `SPEC_BUILD_REPORT.md` §0h/§0i describe, repeated with `openai/gpt-6-luna-pro` |
| all | Phase A and Phase B | commands below |

## 2. Entry preconditions

W3 committed; `SPECCHECK_JUDGE_URL/_MODEL/_API_KEY` present in the environment (names checked, values never printed); network for `npm install`.

## 3. Deliverables

`tests/test_09_self_application.py` (counts), `src/speccheck/__init__.py`, `README.md`, `docs/introducing-speccheck.md` (numbers the article test pins), `SPEC_BUILD_REPORT.md` §0n, `tests/data/jest/` (T-117 fixture) and a presence test, rendered PDFs regenerated with the docs.

## 4. Work items

W4-01 counts and version → suite green. W4-02 README and article from the built surface. W4-03 T-117 run and fixture. W4-04 T-112 runs. W4-05 Phase A. W4-06 Phase B; fix any `WEAKLY_PASSING` in the test, re-run both. W4-07 T-49 three runs. W4-08 build report and §11 walk.

## 6. Gate

1. `uv run python -m pytest tests -q --junitxml=junit.xml` — expected: 0 failed.
2. `uv run ruff check src tests` — expected: exit 0. `uv run speccheck --self-check` — expected: `self-check: ok`.
3. Phase A: `uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck` — expected: exit 0, `CONFORMING - 300/300`, 0 dangling, 0 stale.
4. Phase B: `SPECCHECK_JUDGE_MODEL=openai/gpt-6-luna-pro uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm --strict --judge-concurrency 16 --out build/speccheck-llm` — expected: exit 0, 0 weak, `judge_available` true, `unknown_rate` ≤ 0.2000.

## 8. Traps

A Phase B run against a `junit.xml` written mid-edit is not evidence (the v1.22 report records exactly that failure): regenerate `junit.xml` immediately before both phases, and change nothing between them.

## 9. Exit

The verdict block of `SPEC_BUILD_REPORT.md`; branch ready to fast-forward `main`.
