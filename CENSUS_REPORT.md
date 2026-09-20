# Obligation census — run report

> - **Ran:** 2026-09-19, against `tools/census.py` implementing `PROPOSAL_obligation_census.md`
> - **Subject:** this repository's own `SPEC.md` (v1.13), 133 live obligations across R (37), C (13), I (13), K (15), E (55) — T ids excluded (methods, not obligations), retired ids excluded
> - **Models:** `qwen3:8b` (local, via Ollama), `openai/gpt-4o-mini` (OpenRouter), `google/gemini-3.8-flash` (OpenRouter); 3 runs per subject per model (399 requests each), `prompt_sha256` `ea0e4c17ff4d5b71a0ce36ee7c297b2275147bffdea9ef03096d0679d74f858e` — identical across all three runs, confirming the instrument itself didn't drift between them. Plus `typesafe/jev-1.13` (OpenRouter's alpha decisions API — `tools/jev_client.py`/`tools/jev_report.py`), one call per subject (not `--runs`; it returns a full probability distribution rather than a discrete sample), 133/133 succeeded.
> - **Verdict:** provisional — see §4. None of the four runs is ratified (0/133 each); the `docs/research/SPEC.md` (Monte Carlo π) second subject named in the proposal was not run in this pass.

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

## 2. The four-way comparison

| | `qwen3:8b` (corrected run) | `gpt-4o-mini` | `gemini-3.8-flash` | `jev-1.13` |
| --- | --- | --- | --- | --- |
| c_all | **0.4962** (66/133) | 0.3835 (51/133) | 0.1203 (16/133) | 0.4361 (58/133) |
| R ratio (N=37) | 0.3514 | 0.0811 | 0.0270 | 0.0811 |
| C ratio (N=13) | **0.8462** | 0.6923 | 0.3077 | 0.3846 |
| I ratio (N=13) | 0.4615 | 0.3846 | 0.3846 | 0.3077 |
| K ratio (N=15) | 0.5333 | 0.4667 | 0.0667 | 0.2667 |
| E ratio (N=55) | 0.5091 | 0.4909 | 0.0909 | **0.7636** |
| Accuracy vs. seed labels (10, corrected — §3) | 0.80 | **1.00** | 0.60 | 0.80 |
| Internally uncertain subjects | 3/133 (split) | 4/133 (split) | 23/133 (split) | 7/133 close-call, 48/133 conf.<0.7 |
| Transport/parse errors | 0 (after the fix) | 0 | 4 (minor, non-timeout) | 0 |
| **Recommendation (Part C)** | **Rule 2 — field for C only** | Rule 3 — no language | Rule 3 — no language | **Rule 2 — field for E only** |

Jev is architecturally different from the other three (one call returns a full probability
distribution over the four `form` options plus its own reported `confidence`, not three
independent samples to take a consensus over), so its "uncertain subject" row isn't the same
measurement as `split` — it's listed separately, not averaged in. Two readings of it: a **close
call** (the top two `form` probabilities within 0.15 of each other, 7 subjects) is the nearest
analogue to `split`; **confidence < 0.7** (48 subjects, 36% of the spec) is Jev's own stated
self-doubt, a much larger and more textured signal than any free-text model gave — the other
three mostly reported a flat ~0.9 regardless of subject, which in retrospect reads as
uninformative rather than confident.

**The three free-text models' split subjects have zero overlap with each other** — not one of
the 30 distinct ids any of them flagged as internally unstable was flagged by another of them.
Jev breaks that pattern partially: **3 of its 7 close calls (`E-11`, `E-21`, `E-26`) are also
split for a free-text model** — `E-11` and `E-21` for `gemini-3.8-flash`, `E-26` for
`gpt-4o-mini` — and 15 of its 48 low-confidence subjects overlap the free-text splits too. `E-26`
in particular ("An ID has judge verdicts of both `ASSERTS` and `EXECUTES_ONLY` on passed edges →
status `PASSING`; … the `EXECUTES_ONLY` edge remains visible in §8") is flagged by two
architecturally unrelated models (a general chat model and a purpose-built decision model) — that
is the strongest evidence in this whole run that a *specific* row, not model noise, is genuinely
on the form boundary (it describes a runtime state across several test edges, which reads as
`behavior`, while also asserting a fixed rendering rule, which reads as `struct`). Whatever
"split"/"close call" is measuring overall is still mostly model-specific noise — 4 of 7 Jev close
calls and 33 of 48 low-confidence subjects match nothing any other model flagged — but it is not
*entirely* noise, and `E-26` (plus `E-11`, `E-21`) are the rows to ratify first if this is
followed up.

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
correction is real and kept. `jev-1.13`, run after the correction, adds a fourth independent
confirmation: `behavior` at 0.83 probability (confidence 0.77) — the label now stands on 4/4
models, all architecturally different (three general chat models plus one purpose-built decision
model), none of them shown the correction in advance.

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

**Two of four models say Rule 3 (no expression language); the other two say Rule 2, but not for
the same family** — `qwen3:8b` scopes it to contracts (C at 0.8462), `jev-1.13` to edge cases
(E at 0.7636). No family clears 0.75 in more than one model's reading. Weighted by accuracy and
internal stability, `gpt-4o-mini`'s run (1.00 accuracy, 4 splits, 0 errors) is still the most
trustworthy single data point, and it says Rule 3 — its own family ratios put C highest (0.69)
and E second (0.49), short of 0.75 on both, which is consistent with "close but not there" rather
than with either Rule-2 model's specific claim.

Honest reading: **provisionally no expression language; no family has earned a dedicated field
from more than one model's reading, though C and E are each one model's pick and the two nearest
misses in the most-trusted run too.** Per the proposal's own rule, none of these four runs should
be treated as final until ratified (all four sit at 0/133 ratified, hence `PROVISIONAL` on every
one); the next step, if this is worth settling precisely rather than provisionally, is ratifying
by hand — starting with `E-26`, `E-11`, and `E-21` (§2), the only rows two architecturally
different models both flagged as genuinely hard to classify, rather than the much larger
single-model queues that mostly don't corroborate each other.

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

# jev-1.13, via OpenRouter's alpha decisions API (a different endpoint/schema, not the judge's
# chat-completions one) -- generate one task per subject, run them all, then compute its own
# Part C reading and accuracy bar:
export OPENROUTER_API_KEY=sk-or-...
uv run python tools/census_jev_tasks.py --spec SPEC.md --out build/census/jev_tasks.jsonl
uv run python tools/jev_client.py --task-file build/census/jev_tasks.jsonl --id ALL \
    --concurrency 8 --out build/census/jev_results.jsonl
uv run python tools/jev_report.py --results build/census/jev_results.jsonl
```

`build/` is gitignored; the four runs' `census.json`/`CENSUS.md` (or, for Jev,
`jev_tasks.jsonl`/`jev_results.jsonl`/`jev/CENSUS.md`) this report describes are not committed
and can be regenerated with the commands above (a fresh run will not be byte-identical — the
models are not deterministic at this task — but the `prompt_sha256` and the shape of the
findings should reproduce).
