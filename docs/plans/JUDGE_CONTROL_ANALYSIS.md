# Controlling the LLM judge for regulated use — what it would take

> **Status:** analysis, 2026-11-05, for the decision in `ISO13485_READINESS_PLAN.md` §3.4. Not a
> proposal: if the judge is to be controlled, the next step is a `spec-proposal` for v1.27 built
> from §3 below.
> **Current position:** v1.26 keeps the judge **outside validated use** (`SPEC.md` R-110, D-67):
> it may be used, but its output is advisory and is not verification evidence.
> **Evidence:** the v1.26 build's Phase B runs, 2026-11-05: `openai/gpt-6-luna-pro` via
> OpenRouter, `--judge-concurrency 16`, `--strict --risk-file`, on this repository (356 ids, about
> 1,150 judged edges per run, about 17 minutes per run). Recorded in `SPEC_BUILD_REPORT.md` §0q.

## 1. What controlling it would buy

The judge can only turn `PASSING` into `WEAKLY_PASSING` (R-11, I-004). It can never cause the
hazardous failure the tool risk assessment is about — a requirement reported as verified when it
is not (`docs/validation/TOOL_RISK_ASSESSMENT.md`, TH-05). That safety holds today, controlled or
not.

What control adds is the right to put one more claim in a verification record: **"every passing
requirement's tests actually assert it"** — test adequacy, which the deterministic mock judge
approximates only by the presence of an assertion token. For that claim, the judge's errors that
matter are:

| Error | Effect on the claim | Seen in this build |
| --- | --- | --- |
| **Missed weak test**: `ASSERTS` for a test that only executes the code | the claim is false for that id | v1.25's Phase B passed I-020's determinism test; v1.26's run 3 rated the same, unchanged test `EXECUTES_ONLY` — correctly. The test compared manifests written to different `--out` directories, so identical inputs were never compared. |
| **`UNKNOWN`**: no usable verdict (malformed response, timeout) | that edge is unjudged; the claim cannot rest on it | 16–22 of about 1,150 edges per run (`unknown_rate` 0.0139, 0.0191, 0.0147) |
| **Spurious downgrade**: a well-tested id ends `WEAKLY_PASSING` | a nuisance — but in a gated build it blocks the release | run 2: E-13's asserting edge got a malformed response, so E-13 had no `ASSERTS` left; run 3 rated the same edge `ASSERTS` |

**Run-to-run agreement on identical inputs.** Runs 2 and 3 judged the same tree, results file
and prompt. Of 1,154 edges, 1,058 got the same verdict (91.7%). The 96 that changed include 21
flips between `ASSERTS` and `EXECUTES_ONLY` (11 one way, 10 the other) — the distinction the judge
exists to make — 37 between `EXECUTES_ONLY` and `UNRELATED`, and 27 to or from `UNKNOWN`. Each run
downgraded a different id (run 1: R-115, a real gap, since fixed; run 2: E-13, noise; run 3:
I-020, a real gap, since fixed).

So the judge is useful — two of the three downgrades were real test weaknesses — but a single run
is not reproducible evidence.

## 2. What exists today

| Control | State |
| --- | --- |
| Request shape pinned | yes: `temperature 0`, `max_tokens 4000`, one request per edge, no retries (C-06, K-06, T-33) |
| Instruction text pinned and recorded | yes: `judge_prompt_sha256` in `speccheck.json` (R-26) |
| Model recorded | partly: `SPECCHECK_JUDGE_MODEL` is passed through verbatim and recorded in the manifest's `options.judge_model` (C-25); on OpenRouter that name is an alias, and the serving provider is neither pinned nor recorded |
| Requests and responses kept | no: printed to stderr only at `--verbose DEBUG` (`judge>` / `judge<` lines) |
| Accuracy measured | T-49: at least 0.90 agreement on 40 hand-labelled edges of the golden fixture (27 `ASSERTS`, 10 `EXECUTES_ONLY`, 3 `UNRELATED`), three runs, recorded |
| Policy for disagreement between runs | none: one run decides |

## 3. What controlling it would need

### 3.1 Pin the configuration (spec + code)

- An approved **judge profile** file: the exact model snapshot (not an alias), the provider and
  routing (no fallback to another provider or quantization), the endpoint, the request parameters,
  and the `judge_prompt_sha256` it was qualified with.
- A validated run takes the profile (a new flag), refuses to run with any other configuration, and
  records the profile's hash in both reports and the manifest.

### 3.2 Keep every request and response as a record (spec + code)

- A `--judge-log FILE` writing one JSON line per edge: the request as sent, the raw response, the
  parsed verdict, and the time. The file is hashed into the manifest like any other output.
- Because a re-run does not reproduce the verdicts (§1), this log — not re-runnability — is the
  evidence for a judged run.

### 3.3 Measure the judge before relying on it (data + process) — the expensive part

- **A labelled corpus large enough to bound the miss rate.** T-49's 40 edges cannot: with 10
  `EXECUTES_ONLY` labels, one miss moves the measured detection rate by 10 points. An acceptance
  limit on missed weak tests with a stated confidence needs several hundred labelled edges, with
  many genuine weak tests, ideally including tests of the kind the customer writes.
- **An acceptance criterion stated on the errors that matter**: the rate of `ASSERTS` given to
  weak tests (with a confidence bound), the `UNKNOWN` rate, and run-to-run agreement.
- **Performance qualification repeated** whenever the model snapshot, provider, prompt hash,
  request shape or speccheck version changes. Provider-side model deprecations will force this on a
  schedule nobody controls.

### 3.4 A policy for nondeterminism (spec)

- Retries for malformed responses (today: never, T-33), bounded and recorded.
- Possibly a majority of N runs per edge, at N times the cost.
- **Human adjudication**: every `UNKNOWN` and every `WEAKLY_PASSING` on a requirement that controls
  a hazard goes to a named reviewer, whose decision is recorded with the run.

### 3.5 Risk assessment, intended use and qualification (docs + data)

- New tool hazards:
  - the judge misses a weak test that a record relies on;
  - a spurious downgrade blocks a release;
  - **the test source code is sent to a third party.** Every judged test's source goes to the
    endpoint (OpenRouter, then the model provider). For many medical-device teams this is the real
    blocker: it needs a data-processing agreement, or a local model (the README's Ollama setup),
    qualified on that hardware.
- `SPEC.md` R-110's intended-use statement widened to name the controlled judge configuration.
- `speccheck qualify` gains an optional, networked OQ case: the profile's model on a labelled
  set, against the acceptance criterion.
- Known anomalies gain the malformed-response rate and the run-to-run agreement.

### 3.6 Ongoing cost

| Item | Cost |
| --- | --- |
| One gate run | about 17 minutes and about 1,150 paid model calls |
| One performance qualification | several hundred labelled edges × 3 runs (more with majority voting) |
| The labelled corpus | days of expert labelling once, then upkeep as tests change |
| Adjudication | a reviewer's time for every `UNKNOWN` and downgrade on a risk control |

## 4. Options

| Option | What it gives | What it costs |
| --- | --- | --- |
| **A. Exclude (current, recommended)** | the judge stays a review aid: a team strengthens the tests it flags; the verification report's sampling checklist covers test adequacy by hand (`docs/templates/VERIFICATION_REPORT_TEMPLATE.md` §5) | nothing more |
| **B. Narrow control** | the adequacy claim for the requirements that control hazards only: judge only their edges, a human reviews every verdict that is not `ASSERTS`, the log is kept | §3.1, §3.2, a smaller labelled set, and §3.4's adjudication — a fraction of C's calls and labelling |
| **C. Full control** | the adequacy claim for every requirement | everything in §3 |

**Recommendation: A**, and move to B only when a customer needs the adequacy claim in a record —
for example for software safety class C. Whichever is chosen, the judge stays downgrade-only and
the deterministic gate (Phase A) remains the verification evidence.
