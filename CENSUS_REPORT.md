# Obligation census — run report

> - **Ran:** 2026-09-19, against `tools/census.py` implementing `PROPOSAL_obligation_census.md`
> - **Subject:** this repository's own `SPEC.md` (v1.13), 133 live obligations across R (37), C (13), I (13), K (15), E (55) — T ids excluded (methods, not obligations), retired ids excluded
> - **Models:** `qwen3:8b` (local, via Ollama), `openai/gpt-4o-mini` (OpenRouter), `google/gemini-3.8-flash` (OpenRouter); 3 runs per subject per model (399 requests each), `prompt_sha256` `ea0e4c17ff4d5b71a0ce36ee7c297b2275147bffdea9ef03096d0679d74f858e` — identical across all three runs, confirming the instrument itself didn't drift between them
> - **Verdict:** provisional — see §4. None of the three runs is ratified (0/133 each); the `docs/research/SPEC.md` (Monte Carlo π) second subject named in the proposal was not run in this pass.

## 1. What happened operationally (read this before running it again)

The first local run (`qwen3:8b`, `--concurrency 8 --timeout 90`) lost **87 of 399 requests (22%)**
to `ReadTimeout` — not a classification failure, a resource-contention one: a single local Ollama
instance does not truly serve 8 concurrent requests to an 8B parameter model in parallel, so
later-queued requests exceeded the 90 s per-request timeout while waiting their turn. Two
subjects (`K-15`, `I-011`) came back `UNKNOWN` on **every** run and were flagged `split` for a
reason that had nothing to do with the spec. A second run (`--concurrency 4 --timeout 240`)
completed with no timeouts. **Lesson for next time:** a local, single-instance model needs low
concurrency and a generous timeout; a hosted endpoint (OpenRouter, both models below) handled
`--concurrency 8`–`16` with zero transport errors and finished in a few minutes. The flawed first
run's raw output is kept at `build/census/speccheck-run1-90s-timeout-partial/` for the record; it
is not used below.

A cosmetic bug was also fixed while reading the first clean result: `render_census_md` displayed
`c_all` to two decimal places, which turned a genuine 0.4962 into the self-contradictory-looking
"c_all = 0.50 < 0.50". Rule-boundary values now render to four decimal places.

## 2. The three-way comparison

| | `qwen3:8b` (corrected run) | `gpt-4o-mini` | `gemini-3.8-flash` |
| --- | --- | --- | --- |
| c_all | **0.4962** (66/133) | 0.3835 (51/133) | 0.1203 (16/133) |
| R ratio (N=37) | 0.3514 | 0.0811 | 0.0270 |
| C ratio (N=13) | **0.8462** | 0.6923 | 0.3077 |
| I ratio (N=13) | 0.4615 | 0.3846 | 0.3846 |
| K ratio (N=15) | 0.5333 | 0.4667 | 0.0667 |
| E ratio (N=55) | 0.5091 | 0.4909 | 0.0909 |
| Accuracy vs. seed labels (10, corrected — §3) | 0.80 | **1.00** | 0.60 |
| Split subjects (internal 3-run disagreement) | 3/133 | 4/133 | 23/133 |
| Transport/parse errors | 0 (after the fix) | 0 | 4 (minor, non-timeout) |
| **Recommendation (Part C)** | **Rule 2 — field for family C only** | Rule 3 — no language | Rule 3 — no language |

**The three models' split subjects have zero overlap.** Not one of the 30 distinct ids any model
flagged as internally unstable was flagged by another model. Whatever "split" is measuring, it is
model-specific noise more than a shared, spec-level ambiguity — a human ratifying from any single
model's queue would miss essentially all of what another model would have raised. This is itself
a finding about the instrument, and a reason to weight the *stability* of a run (few splits, few
errors) alongside its raw numbers, not just read off `c_all`.

## 3. One seed label was wrong, not the models

All three models, unanimously across all 3 runs each (9/9 total), classified `R-01` ("The checker
MUST read a Markdown specification and extract every declared spec ID … per the grammar in
C-01") as `behavior` — an input/output observation `T-01` tests directly. The original seed label
called it `prose` ("the obligation is the grammar, which lives in C-01; on its own the row is
intent"). Three independent models agreeing against one hand-written label, with no technical
failure on any side, is stronger evidence than the label — `tools/census_labels.json` has been
corrected. Recomputed accuracy: `qwen3:8b` 0.70 → **0.80**, `gpt-4o-mini` 0.90 → **1.00**,
`gemini-3.8-flash` 0.50 → **0.60**. None of this reaches the ≥20-label, ≥4-per-form bar Part B
sets to actually gate on — these numbers are informative, not a verdict on any model — but the
correction is real and kept.

**A second, unresolved disagreement worth naming:** `gemini-3.8-flash` alone reads `K-14`
(a byte-length bound) and `I-008` (a ratio range) as `behavior`, where the other two models and
the seed labels agree on `expr`. Read across gemini's whole table, this isn't isolated — its
ratio is the lowest in *every* family, and by a wide margin in K (0.07 vs. 0.47–0.53) and E (0.09
vs. 0.49–0.51). The likely mechanism: the census prompt allows `checker: test` for an `expr`
obligation (an expression can still be cheapest to verify by running a test), but gemini appears
to collapse "this gets verified by a test" into `form: behavior` regardless of whether the
underlying proposition is a closed expression. That reads as a prompt-calibration gap for this
model on this task specifically — notable because in this project's own judge history (`§0d` of
`SPEC_BUILD_REPORT.md`) gemini was the *stricter*, more accurate reader; here it is the least
accurate (0.60) and least stable (23 splits) of the three. A model's reliability on one
classification task does not transfer to another.

## 4. Recommendation

**Two of three models say Rule 3 (no expression language); the third — the least accurate and
the one with the closest technical run — says Rule 2 (a field scoped to contracts only), missing
the "no language" line by 0.0038 on `c_all` and clearing the family bar for C at 0.85.** Weighted
by accuracy and internal stability, `gpt-4o-mini`'s run (1.00 accuracy, 4 splits, 0 errors) is the
most trustworthy single data point, and it says Rule 3. But `qwen3:8b`'s C-family ratio (0.85) is
not an outlier by form alone — `gpt-4o-mini` also puts C highest among families (0.69), just short
of the 0.75 bar; the two agree on *which* family is closest to worth a dedicated field, they
disagree on whether it clears the line.

Honest reading: **provisionally no expression language, with contracts (C) as the family to watch
if this is revisited** — not a confident Rule 3, because the evidence is 10 unratified labels and
three models that agree on direction more than magnitude. Per the proposal's own rule, none of
these three runs should be treated as final until ratified (all three sit at 0/133 ratified,
hence `PROVISIONAL` on every one); the next step, if this is worth settling precisely rather than
provisionally, is ratifying the combined 30-id queue by hand — which is also the only way to find
out whether the zero-overlap instability in §2 reflects genuine ambiguity in those specific rows
or model noise that ratification will simply dissolve.

## 5. Reproducing this

```bash
# local, needs Ollama serving qwen3:8b
export SPECCHECK_JUDGE_URL=http://localhost:11434/v1/chat/completions
export SPECCHECK_JUDGE_MODEL=qwen3:8b
export SPECCHECK_JUDGE_API_KEY=ollama
uv run python tools/census.py --spec SPEC.md --runs 3 --concurrency 4 --timeout 240 --out build/census/speccheck

# hosted, needs an OpenRouter key
export SPECCHECK_JUDGE_URL=https://openrouter.ai/api/v1/chat/completions
export SPECCHECK_JUDGE_MODEL=openai/gpt-4o-mini   # or google/gemini-3.8-flash at --concurrency 8
export SPECCHECK_JUDGE_API_KEY=sk-or-...
uv run python tools/census.py --spec SPEC.md --runs 3 --concurrency 16 --timeout 60 --out build/census/speccheck-openrouter

# after hand-ratifying any subject's "ratified" field in a census.json:
uv run python tools/census.py --ratify build/census/speccheck/census.json
```

`build/` is gitignored; the three runs' `census.json`/`CENSUS.md` this report describes are not
committed and can be regenerated with the commands above (a fresh run will not be byte-identical
— the models are not deterministic at this task — but the `prompt_sha256` and the shape of the
findings should reproduce).
