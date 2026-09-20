# Judge cross-check — design and a real validation run

> - **Built:** 2026-09-19. Three `tools/` scripts, outside the kernel, no `SPEC.md` change.
> - **What it is:** a second opinion on a `speccheck check --judge llm` run, from Jev
>   (`typesafe/jev-1.13`, OpenRouter's alpha decisions API), for a human to read — never fed back
>   into `--judge llm`, never changes a status.
> - **Why it can't be a judge provider:** see the conversation that motivated this (summarized in
>   §1). The short version: the verdict question fits Jev's `choice` type exactly, but the
>   contract's two grounding mechanisms — `clause` (R-34/K-15, a verbatim quoted excerpt) and
>   `evidence` (I-005, a variable-length list of line numbers) — have no representation in Jev's
>   closed vocabulary (`noul`/`choice`/`score`, nothing free-text or variable-length). Any
>   adaptation (e.g. pre-segmenting statements into candidate clauses) reintroduces exactly the
>   gist-grading problem clause-grounding was built to remove (`SPEC_BUILD_REPORT.md` §0d), and
>   Jev's API is a different wire format from the chat-completions endpoint C-06 pins, so it
>   would need a whole new provider contract, not a config value.

## 1. What it does instead

Three scripts, chained:

1. `tools/judge_crosscheck_tasks.py --report speccheck.json --tests DIR` — reads a
   `check --judge llm` report, re-attributes the same `--tests` roots with `attribute.py` (the
   same code the kernel itself uses) to recover each judged edge's test span, and builds each
   Jev task with `judge.build_request` — the **real judge's own request builder** — so the
   statement and line-numbered source Jev sees are byte-for-byte what the real judge saw. The
   question drops `clause`/`evidence` and asks only the bare verdict, with the same four options
   (`ASSERTS`/`EXECUTES_ONLY`/`UNRELATED`/`UNKNOWN`) and criteria paraphrased from C-10's own text
   (kept in lockstep with `judge.VERDICTS` by an assertion in the script). Each task also carries
   `recorded_verdict`/`recorded_clause`/`recorded_coerced` for the join step.
2. `tools/jev_client.py --task-file ... --id ALL` — unchanged; sends the batch.
3. `tools/judge_crosscheck_report.py --tasks ... --results ...` — joins by task id and reports
   **two different findings, not one**:
   - **Rescue leads**: the real judge formed an opinion but K-15/E-48 discarded it as ungrounded
     (`UNKNOWN`, `coerced: true`); Jev, asked the same question with no grounding requirement,
     answered anyway. Not a verdict to trust — a lead for a human, or evidence the judge
     model/prompt needs work on those specific edges.
   - **Genuine conflicts**: the real judge committed to a real verdict and Jev disagrees. Two
     models both answering and landing differently is a stronger signal than a gap, and the case
     that would actually call the recorded verdict into question.

## 2. A real run (fixture-scale, for validation)

`fixtures/target` (the golden fixture), `--judge llm` with `qwen3:8b` via local Ollama
(`--judge-concurrency 2`), 21 judged edges, then all three scripts against the real result —
no stubs, a live Jev endpoint for both the judge and the cross-check.

```text
21 edges compared (0 Jev request failures excluded).
Agreement (all edges): 16/21 (0.7619)
Agreement on edges the real judge committed to (excludes recorded UNKNOWN): 16/16 (1.0000)

Confusion (recorded -> Jev):
  ASSERTS -> ASSERTS: 13
  UNKNOWN -> ASSERTS: 4
  UNRELATED -> UNRELATED: 2
  UNKNOWN -> EXECUTES_ONLY: 1
  EXECUTES_ONLY -> EXECUTES_ONLY: 1

Rescue leads: 5 (all five of the run's UNKNOWNs, all coerced with rationale
  "judge: unlocated clause" — R-01/test_add, T-01/test_add, T-02/test_divide_by_zero,
  C-04/test_summary_ordering_is_stable_ascending, C-04/test_summary_runs_on_a_mixed_list).
  Jev answered all five confidently (probability >= 0.99 on four; 1.0 on the fifth).

Genuine conflicts: 0.
```

This is close to the intended use case in one clean run: every disagreement is a rescue lead, not
a conflict — the real judge (`qwen3:8b`, already documented elsewhere in this repo as a
thinking model that answers a minority of edges under this kind of constraint) formed an opinion
on all five but lost each one to K-15's verbatim-quote requirement, and Jev's bare-verdict
question recovers a plausible answer for a human to weigh. On the 16 edges the real judge *did*
commit to a verdict, the two models agreed on every single one — no evidence here of the real
judge being substantively wrong, only of it being silenced by grounding on edges a differently-
shaped question can still answer. A single fixture-scale run is not proof this generalizes; the
next real use is running it against a full `--judge llm` pass on this repository's own `SPEC.md`
(488 judged edges per `SPEC_BUILD_REPORT.md` §0d) and reading whether the same pattern holds at
scale, or whether genuine conflicts start appearing once the statement bodies get longer and the
real judge's answers get harder to ground.

## 3. Reproducing this

```bash
# 1. a normal --judge llm run, exactly as spec-build's gate already does
export SPECCHECK_JUDGE_URL=http://localhost:11434/v1/chat/completions   # or an OpenRouter endpoint
export SPECCHECK_JUDGE_MODEL=qwen3:8b
export SPECCHECK_JUDGE_API_KEY=ollama
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml \
    --judge llm --out build/speccheck-llm

# 2. build one Jev task per judged edge, reusing the real judge's own request builder
uv run python tools/judge_crosscheck_tasks.py \
    --report build/speccheck-llm/speccheck.json --tests tests \
    --out build/census/crosscheck_tasks.jsonl

# 3. send them
export OPENROUTER_API_KEY=sk-or-...
uv run python tools/jev_client.py --task-file build/census/crosscheck_tasks.jsonl --id ALL \
    --concurrency 8 --out build/census/crosscheck_results.jsonl

# 4. join and report
uv run python tools/judge_crosscheck_report.py \
    --tasks build/census/crosscheck_tasks.jsonl --results build/census/crosscheck_results.jsonl
```

`build/` is gitignored; nothing here writes to `SPEC.md`, `speccheck.json`, or any status.
