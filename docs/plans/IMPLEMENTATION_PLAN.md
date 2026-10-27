# Implementation plan — speccheck v1.23.1 delta (namespaced ids, the citation map, and the full review's fixes)

> - **Target:** the `speccheck` kernel at `SPEC.md` v1.23.1 (sha256 `7c89742c…` at `761d8d9`,
>   re-measured at the start of W1 after `fix(spec)` `50b723d`). The delta is v1.23 (R-101..R-103,
>   C-22, C-23, I-019, K-19, E-67..E-73, T-107..T-112) plus the v1.23.1 behaviour changes in the
>   revision history (F-701..F-717, new T-117).
> - **Size expectation:** a **delta plan** on the built v1.22 implementation: 4,297 production
>   code lines across 18 modules (`cloc src/speccheck --exclude-dir=_selfcheck`), 5,587 test code
>   lines across 19 files, 164 tests (161 passing, 3 failing on the spec change, below). This plan
>   budgets **~260–420 production lines**, **~500–750 test lines**, plus data files under
>   `tests/data/`, regenerated help goldens, and docs.
> - **Method:** red-green-refactor per §9 group, one wave per sitting, one commit per wave on
>   branch `spec/v1.23.1`; `SPEC.md` is edited only by a recorded `fix(spec):`.

---

## 1. Verdict

Four waves. **W1** lands the v1.23.1 corrections that touch existing code and no new flag: the
mock judge's JS/TS tokens, the regex-versus-division rule, C-18's step labels and the `error`
outcome, and `judge_prompt.md` synced to C-10. It turns the one red test the spec change caused
green, and it gives every later wave a baseline in which every failure is new. **W2** builds
foreign references and `--namespace` (the false-green fix, which can ship on its own). **W3**
builds `--citation-map`: read, validate, resolve, label, exclude from the scan. **W4** proves it:
id counts, README, build report, recorded runs, and both gates.

Three decisions carry the plan:

1. **FOREIGN is one pass in `extract.py`, used by both callers.** `citations_in_file` and C-12's
   `targets_of` read the same matcher, so a token cannot be foreign for citations but local for
   edges.
2. **A mapped citation is an ordinary `Citation` with `mapped=True`, made before `build_graph`.**
   C-05 then cannot treat it differently (C-23's "C-05 untouched"). Only the reporters and
   `declared_ratio` read the flag.
3. **Byte identity (I-019, T-109) is checked against the existing v1.22 goldens at every wave
   gate,** not only at the end. Every new key is conditional, and a regression there is cheapest
   caught the moment it lands.

It refuses to change C-05, add a gate, make `schema_version` move, or let a map entry create a
test case that does not exist. It lands at roughly 4.6–4.7k production lines.

## 2. What the evidence says

| Measure | Value (measured 2026-10-27 at `761d8d9`) |
|---|---|
| Production code | 4,297 lines / 18 modules; largest `cli.py` 1,074, `report.py` 545, `extract.py` 518 |
| Tests | 164 collected: 161 pass; 3 fail: `test_llm_response_path_fences_and_prompt_hash` (C-10 changed, `judge_prompt.md` not yet), and two self-application tests pinning `DECLARED_IDS = 279` (spec now declares 300) |
| Mock gate (`check --judge mock --strict` over this repo) | `NOT CONFORMING - 260/300 passing … 20 failing … 20 uncited` — the 20 uncited are the 19 v1.23 ids plus T-117; the 20 failing are ids cited by the 3 red tests |
| Already true in code, spec-only in v1.23.1 | C-06's two-message body (`judge_llm.py:214`); JS/TS comment-only DECLARED (`attribute.py` passes `comment_only`); K-18 readability (`cli.py:644-680` reads bytes in validation) — these need tests, not code |
| Differs from v1.23.1 | `jsts._REGEX_PRECEDERS` treats `}` as a regex preceder and omits `+ - * % < > ~ ^` and several keywords (F-708); `explain._REASONS` step labels (F-711); `judge_mock` has no `expect(` (F-706) |
| Prior delta builds | v1.21/v1.22 were built directly, without waves (`SPEC_BUILD_REPORT.md` §0m says so); v1.18 used this plan format; v1.22's JS adapter (`jsts.py`, 240 lines) is the closest-sized increment |

Two systemic risks this repository has shown: **pinned-text drift** (help goldens, summary-line
regexes and article numbers that a feature changes and a test then pins; v1.23's own fold review
F-603, F-612), and **a spec claim no code checks** (F-701 survived six versions because no test
reads the spec's C-06 text). The rules in §6 address both.

## 3. Shape

```mermaid
flowchart LR
  cli["cli.py: flags, map read/validate/resolve, exclusions"] --> extract["extract.py: FOREIGN pass, tokens, edges"]
  cli --> attribute["attribute.py: Citation.mapped"]
  cli --> graph["graph.py: declared_ratio, dangling/stale mapped"]
  graph --> report["report.py: foreign, citation_map, mapped, summary suffix"]
  graph --> explain["explain.py: (mapped), step labels, error"]
  cli --> impact["impact.py: unchanged walk; scan gets namespace + map"]
```

*Figure: the modules the delta touches, for R-101..R-103 and C-22/C-23; the arrows are the existing call direction.*

- **Literal filenames from §11:** `extract.py` (FOREIGN, `targets_of`), `cli.py` (flags, map),
  `attribute.py` (`Citation.mapped`), `report.py`, `explain.py`, `judge_mock.py`, `jsts.py`. No
  new production module; the map lives in `cli.py` as §11 says.
- **New test files:** `tests/test_16_namespaces.py` (§9.17 T-107..T-109), `tests/test_17_citation_map.py`
  (T-110, T-111). Foreign-token and map inputs live in `tests/data/namespaces/` and
  `tests/data/citation_map/` (F-713's rule).
- **Layer direction unchanged:** extract → attribute → results → graph → judge → report/explain.

## 4. Order

1. **W1 — v1.23.1 corrections to existing behaviour.** F-706 (mock `expect(`), F-708 (regex rule),
   F-711 (C-18 labels, `error`), F-703's C-10 text into `judge_prompt.md`, F-705/F-709 characterization
   tests (T-115, T-103). Gate: full suite with only the two `DECLARED_IDS` tests red; T-46/T-71
   goldens and `--self-check` byte-identical.
   *First, because these changes alter pinned strings and the prompt hash; landing them before the
   features means W2/W3 regressions are not masked by expected churn.*
2. **W2 — foreign references and `--namespace`.** C-22, R-101, R-102, E-67..E-69, F-712, F-716 (b);
   T-107, T-108, T-109 (half: no map yet); help goldens regenerated. Gate: `test_16_namespaces.py`
   green, goldens byte-identical.
3. **W3 — the citation map.** C-23, R-103, K-19, E-70..E-73, F-702 (exclusion), F-703 (ratio),
   F-704 (`mapped` on dangling/stale), F-716 (a); T-110, T-111, T-109 (rest); help goldens again.
   Gate: `test_17_citation_map.py` green; I-019 holds over every golden.
4. **W4 — prove it.** `DECLARED_IDS` and the article numbers, `__version__ = "1.23.1"`, README,
   `SPEC_BUILD_REPORT.md` §0n, the recorded runs (T-112, T-117, T-49), both speccheck phases.

## 5. LOC budget (production)

| Slice | Files | LOC |
|---|---|---|
| W1 corrections | `judge_mock.py`, `jsts.py`, `explain.py` (+ `judge_prompt.md` text) | 15–40 |
| W2 foreign + namespace | `extract.py`, `cli.py`, `report.py` | 80–140 |
| W3 citation map | `cli.py`, `attribute.py`, `graph.py`, `report.py`, `explain.py` | 160–240 |
| W4 | `__init__.py` | 1 |
| **Total** | 8 | **~260–420** |
| Tests | 2 new + 5 edited | 500–750 |

Anchors: `jsts.py` (v1.22, a token pass plus its join, 240 lines); `proof.py` + `lean.py` (v1.19,
an optional input file read, validated and joined, 206 lines). The map is the same kind of slice
as v1.19's manifest, so W3 above ~250 lines is structure to name, not requirement. The budget is a
ceiling estimate, not a floor.

## 6. Rules that make the observed failures impossible

| Prior failure | Structural rule |
|---|---|
| Help goldens / summary regex / article numbers changed by a feature and left red (v1.23 fold F-603, F-612) | Every wave that adds a flag regenerates `tests/data/help/*` at `COLUMNS=80` in the same commit and reads the diff; the T-44 regex test and the article test run in every gate |
| A spec text claim no test reads (F-701) | W1 adds an assertion that the C-06 request has exactly two `messages`, system first, and that `judge_prompt.md` equals the C-10 block in `SPEC.md` (T-54 already does the latter) |
| Inertness assumed, not measured (I-018, I-019) | Every gate runs the T-46/T-71 goldens and `--self-check`; T-109 is a test, not a claim |
| Self-application counting its own fixtures (F-713) | Any test input containing `ns:ID` or a map lives under `tests/data/`; W4's T-112 run shows the count |
| Built "directly" without waves (v1.21/v1.22) | One commit per wave; the commit body names the gate commands and their exit codes |
| A recorded test claimed without a run | T-112, T-117, T-49 are recorded in `SPEC_BUILD_REPORT.md` with the run's date, versions and output, or listed as not run with the reason |

**Live verification.** The product is a CLI with text outputs; the "look" is running the built
`speccheck` on real projects and reading the reports. W4 runs `check --strict` over this
repository and two further projects (T-112), one real jest + jest-junit run (T-117; needs
`npm install` in a scratch directory, so network access), and Phase B with
`SPECCHECK_JUDGE_MODEL=openai/gpt-6-luna-pro --judge-concurrency 16` against the OpenRouter
endpoint already configured in the environment. Anything not run stays *pending* in the report,
and the verdict cannot be PASS while a gating item is pending.

## 7. One fork, then action

**Which two further real projects T-112 runs over.** The recommendation is
`~/projects/gpu-quicksort-revisited` (Swift: `Sources/`, `Tests/`, a `SPEC.md`) and
`~/projects/mdv_claude_opus` (the Swift app the earlier judge evidence came from). Both are
built from specs in this house's taxonomy, so a `ns:` token there is a real collision, not noise.
The alternative is any project outside this ecosystem (one with plain `Note:R-03`-style prose),
which tests D-51's risk better but may have no ids at all, which proves nothing. Either way the
waves, budgets and gates are unchanged; only W4's record differs.

**Next concrete action:** W1-01: add the failing JS/TS sub-test to T-69 in `tests/test_05_judge.py`,
run `uv run python -m pytest tests/test_05_judge.py -q -k mock`, and expect it to fail on
`EXECUTES_ONLY != ASSERTS`.
