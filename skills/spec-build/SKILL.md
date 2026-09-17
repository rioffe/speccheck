---
name: spec-build
description: Implement a SPEC.md (the source of truth for a system) in any language or stack using test-driven development **executed wave by wave against an implementation plan this skill produces first**, then make README.md reflect the built reality, then re-read SPEC.md, audit every produced artifact for conformance, and run and **look at** the product against the spec's reference images (or report VERIFICATION PENDING), writing SPEC_BUILD_REPORT.md. Phase 0 runs spec-plan to write IMPLEMENTATION_PLAN.md and one DETAILED_IMPLEMENTATION_PLAN_W<n>.md per wave; each later wave is implemented test-first, gated with the wave's own commands, and committed before the next begins. Use when asked to "build the spec", "implement SPEC.md", "make this spec real", or after spec-writing/spec-review/spec-plan produce a Level-2/3 spec and its plan. Pairs with spec-plan (the order this skill executes), spec-writing (authoring the spec) and spec-review (auditing it, yielding SPEC_REVIEW_REPORT.md + F-nnn findings and a P0/P1/P2 remediation plan).
license: MIT
---

# spec-build

Turn a `SPEC.md` into a working, tested, documented implementation. This is the **implementer
companion** to `spec-writing` (which authors the spec) and `spec-review` (which audits it). The
spec is the **source of truth**; the build must satisfy it, and the README must report what was
actually built.

This skill is stack-agnostic. It assumes only that the project has (or can be given) three
things: a way to run **one** test, a way to run **all** tests, and a way to lint/type-check.
Wherever a command appears below, substitute the project's own — and if the project already has
a task runner, CI config, or contributing guide, use its commands rather than inventing new ones.

The build has four phases and you do not skip any — and the first one writes a plan the
other three execute:

1. **Plan (Phase 0).** Read the spec, then produce the implementation plan: the shape, the
   dependency waves and each wave's gate, the slice budgets, and the one fork the user must
   settle — `IMPLEMENTATION_PLAN.md`, plus one `DETAILED_IMPLEMENTATION_PLAN_W<n>.md` per wave.
   Planning is `spec-plan`'s job; run it (or invoke that skill) rather than improvising an order
   in your head, and do not write production code before the plan exists.
2. **Build (Phase 1, TDD).** Implement the spec test-first, **one wave at a time, in the plan's
   order** — write the failing test from §9, watch it fail for the right reason, write the
   minimal code, watch it pass, refactor — then run the wave's gate and **commit the wave**
   before starting the next one.
3. **Document (Phase 2).** When the suite is green, make `README.md` reflect the implemented
   system (not the intended one).
4. **Prove conformance (Phase 3).** Re-read `SPEC.md`, then review *every* produced artifact
   against it and write a conformance report. Do not call the work done until this pass is
   clean.

**The default is to implement everything in the spec.** Every requirement, contract, invariant,
constraint, edge case, and acceptance test in the spec gets realized — unless the user explicitly
told you to scope something out. A `MAY`/`SHOULD`/optional (`O-n`) item is still implemented to
the depth the spec states; "optional" means gated (behind a flag, config key, or feature toggle),
not omitted. If you decide *not* to build an in-scope item, say so, name the spec ID, and get the
user's approval first.

## When to use

- "implement SPEC.md" / "build the <X> spec" / "make `<SPEC.md>` real"
- a project has a `SPEC.md` but no implementation, or only a partial one
- after `spec-review` returns `READY` (or `READY WITH MINOR FIXES`) — then `spec-plan`
  writes the plan, then this skill executes it wave by wave
- "finish this project" where the spec is written but the code isn't

Do **not** start building while `spec-review` returned `NOT READY` or left unresolved **P0**
findings. Fold P0 (blocking) and P1 (important) findings into the spec / acceptance suite first;
P2 (improvement) MAY be deferred. See *Phase 0* below.

## The project layout

Use the layout the repository already has. If the project is empty, choose the conventional
layout for its language/ecosystem (the spec's §10 names the stack) and keep these artifacts
present and in sync regardless of stack:

| Artifact | Purpose | Must track |
| --- | --- | --- |
| `SPEC.md` | Source of truth | unchanged during build; only a `fix(<scope>):` after a found defect |
| `IMPLEMENTATION_PLAN.md` | the order the spec is built in (Phase 0) | the §4 waves, their gates, the §5 budgets; amended only by re-planning, never used as a results log |
| `DETAILED_IMPLEMENTATION_PLAN_W<n>.md` | one wave's executable brief | that wave's files, work items, tests, gate and handoff contract |
| source tree | the implementation | every §2 requirement, §4 contract, §6 invariant, §7 constraint |
| test tree | the §9 acceptance suite | every T-nn id, one group per §9 subsection |
| schemas / fixtures / sample data | artifacts the spec pins | the §4 contract shapes, §10 data |
| build / package manifest | env, deps, entry points | the §5 surfaces, §10 deps |
| `README.md` | the built reality | Setup / Usage / Artifacts / Verification / layout |
| `junit.xml` (or the runner's equivalent) | test results the gate joins to citations | regenerated by every `<run all tests>` |
| `build/speccheck/` (`SPEC_CONFORMANCE_REPORT.md`, `speccheck.json`) | the mechanical §11 walk | one status per spec ID; dangling / stale citations |
| `SPEC_BUILD_REPORT.md` | conformance evidence | per-ID evidence + verdict (Phase 3) |

Define, once, the commands you will use throughout and put them in the README:

```bash
<run one test>      # e.g. pytest tests/test_x.py::test_y -q | go test ./pkg -run TestY | cargo test y | npm test -- -t "y"
<run all tests>     # the full §9 acceptance suite, emitting JUnit XML (see "The speccheck gate")
<lint / typecheck>  # whatever the project's CI runs
<self-check>        # only if the spec pins a boundary/self-check command (e.g. a §6 "no network" invariant)
<speccheck>         # the conformance gate (Python projects), see below; two phases, exit 0 on both is the bar
```

## The speccheck gate

`speccheck` is the mechanical half of Phase 3: for every ID `SPEC.md` declares (R/C/I/K/E/T) it
finds where the source and test trees cite it, joins the citations to a JUnit XML results file,
and assigns each ID exactly one status backed by a file and line. It is what turns "every T-nn
cites its spec ID" from a convention into a gate. Install it from its repository
(`uv tool install <path-or-url of the speccheck checkout>`, or `uv run --project <checkout>
speccheck …`).

**Scope: Python projects.** speccheck currently understands `pytest` test cases (it splits test
files with `ast` and joins them to pytest's JUnit XML); on other stacks it cannot attribute
citations to test cases, so the gate is Python-only for now. For a non-Python project use the
`grep` walk at the end of this section and say so in `SPEC_BUILD_REPORT.md`.

**The gate has two phases, in order.** Phase A uses the deterministic mock judge; Phase B uses
the LLM judge and is run only once Phase A is clean. Both must exit `0`.

```bash
uv run python -m pytest tests -q --junitxml=junit.xml           # fresh results every time

# Phase A — mock judge: citation / result join, deterministic, offline
speccheck check --spec SPEC.md --src src --tests tests \
    --results junit.xml --judge mock --strict --out build/speccheck
# speccheck: CONFORMING - 61/61 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock

# Phase B — LLM judge: does each passing test actually ASSERT the ID it cites?
export SPECCHECK_JUDGE_URL=http://localhost:11434/v1/chat/completions   # Ollama, or any OpenAI-compatible endpoint
export SPECCHECK_JUDGE_MODEL=qwen3:8b
export SPECCHECK_JUDGE_API_KEY=ollama
speccheck check --spec SPEC.md --src src --tests tests \
    --results junit.xml --judge llm --strict --out build/speccheck-llm
# speccheck: CONFORMING - 61/61 passing (100.0%), ..., 0 weak, ...; 0 dangling, 0 stale; judge=llm
```

`--strict` exits `0` only when **every in-scope ID is `PASSING` and there are no dangling or
stale citations** — which is exactly the "§11 matrix fully traced" condition of Phase 3. Under
`--judge llm` it additionally requires the judge to have been reachable and
`unknown_rate` $\leq$ `--max-unknown` (default `0.2`). Each non-passing status names the fix:

| Status | Meaning | What you do |
| --- | --- | --- |
| `UNCITED` | no source or test mentions the ID | the item was silently dropped — build it, test-first |
| `UNTESTED` | source cites it, no test does | write the T-nn test that proves it |
| `UNVERIFIED` | a test cites it but no result was joined | the test did not run, or the results file is stale / the classname join failed — rerun, then check the JUnit `classname`/`name` |
| `FAILING` / `SKIPPED` | joined result is red / skipped | fix the code; a skipped T-nn is not done |
| `WEAKLY_PASSING` | the judge found the test *executes* the behavior but never asserts on it | strengthen the test so it asserts the specified outcome; the judge only ever downgrades, never upgrades, so a mock-clean run can still be red here |
| `UNKNOWN` edges (Phase B) | the model gave no usable verdict for a (test, ID) edge | read `build/speccheck-llm/SPEC_CONFORMANCE_REPORT.md` §8 for the rationale; a thinking model that truncates needs a different model, not a higher `--max-unknown` |
| dangling | a citation of an ID the spec does not declare | a typo in a citation, or an ID the spec deleted outright (spec-writing retires with a strike-through instead) — fix the citation or the spec |
| stale | a citation of a retired ID | remove or re-point the citation |

Rules of the road:

- **Citations are literal tokens.** Any `R-07`-shaped token in any text file under a scan root
  is a citation — in code, comments, and strings alike. Cite IDs deliberately (test names,
  docstrings, comments); put `speccheck:ignore` on a line that mentions an ID without realizing
  it (a changelog line, a "unlike R-07" aside) and `speccheck:ignore-file` in the first three
  lines of a file that must not be scanned at all.
- **A `T-nn` is judged by test citations alone** — citing it from source changes nothing. Cite
  R/C/I/K/E ids from both the code that realizes them and the test that proves them.
- **Phase A before Phase B, always.** The mock judge is deterministic and offline (assertion
  tokens inside the test span); run it after every group and at every gate. The LLM judge is
  slower and probabilistic, so it is run only on a mock-clean tree, where the only thing it can
  find is `WEAKLY_PASSING` — a test that runs the code but never asserts the cited behavior.
  Fix every `WEAKLY_PASSING` by strengthening the test, then re-run **both** phases.
- **Phase B needs a reachable judge** (a local Ollama serving `SPECCHECK_JUDGE_MODEL`, or any
  OpenAI-compatible chat-completions endpoint) and the three `SPECCHECK_JUDGE_*` variables. If
  none is available, do not quietly skip it: ask the user, and if they defer it, record
  "Phase B not run: <reason>" in `SPEC_BUILD_REPORT.md` and the verdict block.
- **Record both summary lines** and, for Phase B, the model name and `unknown_rate` from
  `speccheck.json`, so the evidence is reproducible.
- **Keep `--out` inside `--root`** and out of the scan roots; the tool never scans the spec, the
  results file, or its own reports.
- **Exit `2`/`3` is not a red gate — it is a broken invocation or a broken spec** (missing
  `--spec`, a path outside `--root`, an ID declared twice, malformed JUnit XML). Fix the cause;
  a duplicate or ambiguous declaration is a spec defect handled per Phase 3.3.

For a non-Python project (or if `speccheck` genuinely cannot be installed), fall back to
`grep -rnE '\b[RCIKET]-[0-9]{2,3}\b' <test tree>` and walk §11 by hand — and say so in
`SPEC_BUILD_REPORT.md`.

---

# Phase 0 — Commit to the spec before writing a line

Do this once, up front. It is the plan that keeps TDD honest — Phase 0 ends with a wave
plan on disk (`IMPLEMENTATION_PLAN.md` + its `DETAILED_IMPLEMENTATION_PLAN_W<n>.md` files),
and Phase 1 executes it.

### 0.1 Read the spec fully, end to end

Read the whole `SPEC.md` in one pass **before** touching code — do not skim. Build a mental
model of the §0 intent, the §3 state flow, and any boundary the spec draws (deterministic $\leftrightarrow$
probabilistic, trusted $\leftrightarrow$ untrusted, online $\leftrightarrow$ offline). If a `SPEC_REVIEW_REPORT.md` exists,
read its **Remediation Plan** (P0/P1/P2), **Final Verdict**, and detailed findings (`F-nnn`,
with severity). If the verdict is `NOT READY`, stop and route through `spec-review` /
`spec-writing` first.

Read the spec's notation the way it was written: **mermaid / ASCII diagrams are illustrative;
the R/C/I/K/E rows and §3.1 transition entries are normative.** Build from the rows. If a
diagram shows a transition or branch no row backs (or omits one a row requires), that is a
spec defect — record it as `F-nnn` and resolve it per Phase 3.3 before implementing either
version; never implement the picture. **LaTeX formulas (`$..$`, `$$..$$`) are normative**: the
symbols, the denominator, and the stated degenerate-case value are the contract you implement.

### 0.2 Plan the waves — run `spec-plan`

Do not start implementing until the order exists as a document. Invoke the **`spec-plan`** skill on
this `SPEC.md` (and `SPEC_REVIEW_REPORT.md` if present); if that skill is unavailable in your
environment, follow its template yourself. It produces:

- **`IMPLEMENTATION_PLAN.md`** — the 7-section plan: the verdict (the shape and the ordering it
  commits to), the evidence (measured facts about any prior builds and the starting tree, and the
  systemic failure modes this system must not repeat), the target shape (the module/target graph,
  literal filenames from §11, any purity/headless rule, the one-way layer direction), **the order**
  (waves `W0…W<n>`, each ending at a gate with named commands and spec IDs), the LOC budget per
  slice with anchors, the failure→structural-rule table that makes the observed failures
  impossible, and **one fork** for the user to settle plus the next concrete action;
- **`DETAILED_IMPLEMENTATION_PLAN_W<n>.md`**, one per wave — the executable brief: §1 the ids it
  discharges, §2 entry preconditions, §3 deliverables file by file with signatures, §4 work items
  `W<n>-01…` (test first, then the delta, then the evidence), §5 the test plan, §6 the gate as
  copy-pasteable commands with expected results, §7 traceability including the §11 status rows it
  closes, §8 the traps specific to the slice, §9 the exit criteria and the handoff contract.

Rules for Phase 0.2:

- **The plan is an argument from evidence, not a greenfield guess.** If prior builds exist, measure
  them (production LOC, file count, shape, what ended them) before choosing the shape or the
  budgets. Never cite a digest, tag or version you did not compute.
- **Order by dependency and by apparatus.** Verification apparatus (harnesses, goldens, fixtures,
  metric/oracle functions) lands before the feature it guards; the spec's own formulas are code and
  belong in the first pure wave; any trust boundary (input ceilings, sanitizers, network isolation)
  precedes the parsers it bounds; the first wave leaves a runnable artifact end to end.
- **Name the slice that prior attempts failed to start.** It gets its own wave, its own gate and, if
  it is only observable through the product, live verification.
- **Present the plan's §7 fork to the user and get their answer** before implementing. If they are
  unavailable and the fork is reversible, take the plan's recommendation, say so, and record it in
  the report. A fork left open is a decision the implementation will make silently.
- **The plan is a plan.** No wave, budget, gate or claim in it may say that something was executed.

### 0.3 Extract the build list from the spec's own IDs

The spec already numbers everything. Turn it into a checklist so nothing is silently dropped.
For each family collect the open items:

- **R-nn** requirements (§2) → the behaviors to build.
- **C-nn** contracts (§4) → the interfaces, data shapes, and module boundaries to honor.
- **I-nnn** invariants (§6) → global properties every implementation must keep (determinism,
  no-partial-writes, forbidden dependencies, numeric fallbacks).
- **K-nn** constraints (§7) → measurable limits (exit codes, thresholds, size/latency budgets).
- **E-nn** edge cases (§8) → the failure semantics you must encode, not discover later.
- **T-nn** tests (§9) → **one failing test first** for each, grouped by §9 subsection.
- **§11 traceability matrix** → the `ID → component → test` edges you must be able to point at
  for every ID by the end.

Record this list as a task list — one entry per §9 test group (or per R/C cluster) — as your
implementation order. The plan's waves, not the §9 order, are the *execution* order: group each wave's test
groups under its wave id so a wave's commit closes a whole line of the checklist. This checklist *is* your proof that "everything got implemented": every
box closes on a green test that cites its spec ID.

### 0.4 Seed the skeleton (if empty)

Create the layout from the table above: source modules named after the §4 contract headers, an
empty test tree with one file per §9 group, schema/fixture directories, and the package/build
manifest with the entry points from §5 and the dependencies from §10. Verify that
`<run all tests>` and `<lint>` execute (trivially) before adding behavior. **Commit the skeleton**
— `feat(<scope>): scaffold <name> + manifest + test stubs` — so intermediate work lands on the
history before behavior is added.

---

# Phase 1 — Build with TDD (one §9 test group at a time)

The rule that governs every line of production code:

```text
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

If your environment provides a dedicated TDD skill or workflow, use it; the loop is the same.

### The wave loop — one wave at a time, each ending at a gate and a commit

`IMPLEMENTATION_PLAN.md` §4 fixes the order, and each wave's `DETAILED_IMPLEMENTATION_PLAN_W<n>.md`
is the brief you execute. A wave is the unit of verification *and* of history:

1. **Read the wave document first** — §2 (preconditions) and §3 (deliverables) before editing
   anything. A missing precondition is the previous wave's defect: fix it where it belongs, or
   record why it could not be met, rather than working around it in this wave's files.
2. **Execute its §4 work items in order**, each with the red-green-refactor loop below. The work
   item names the test written first and the evidence that closes it — that order is the item.
3. **Run the wave's §6 gate exactly as written**, plus `<lint / typecheck>`. A wave is done when
   its gate's commands reach their expected results, not when its files exist.
4. **Commit the wave** — one commit per wave, before the next wave starts, e.g.
   `feat(<scope>): W<n> — <the wave's title from the plan>`, with the wave id and the spec ids it
   discharges in the body. Include the code, its tests, and any fixture/corpus the wave owns.
   Inside a large wave, commit per test group too; the rule is that **no wave is left
   uncommitted**, so the history and the plan read in the same order.
5. **Record the wave's ledger row** — wave id, the gate command, its real exit code, the commit
   sha — for the conformance report to collect in Phase 3. If a gate cannot be run as written
   (no signing identity, no tag, no service, no device, no window server), record the stand-in
   and the reason; never record a gate as passed that you did not run. The T-nn that gate
   covers are **pending**, and Phase 3 cannot report PASS while a pending T-nn covers a
   user-visible surface.
6. **Leave the plan alone unless it is wrong.** A plan document is never a results log: the
   commits and the report carry the evidence. If the plan *is* wrong — a slice is misordered, a
   wave is too large, a file belongs to another wave — amend the plan document and say so in the
   commit body. Re-plan explicitly instead of drifting.

If a wave's gate reveals a defect in an earlier wave, fix it there and say so; do not paper over
it in the later wave's commit.

**How a wave is executed.** One agent, one wave, one sitting — the wave document is its brief.
Fanning several agents out across one wave, or across several waves at once, has been measured
to cost more than it returns: continuation agents re-deriving context after a peer died mid-run,
scratch test files left inside the package that broke every other agent's build, and a commit
whose message claimed green while one test failed. If parallelism is unavoidable, the plan's
ownership table decides who touches which file, **no scratch or probe files are written inside
the package tree**, and the orchestrator re-runs the wave's gate itself before any commit message
says "green". A wave document written for one reader is also cheaper to write: name the
preconditions, the frozen interfaces and the gate commands (its §2, §9, §6), and stop.

**The plan's budget is an estimate, not a floor.** `IMPLEMENTATION_PLAN.md` §5 exists so a
subsystem is not silently dropped to fit a number; it is not a target to fill. "Never drop a
subsystem" and "never be smaller than the budget" are different rules, and only the first is
one. If the same spec has a smaller complete build, that build is the anchor, and code above it
is structure you chose to add — name it in the report.

### The inner loop — red-green-refactor, one test group at a time

For each T-nn group inside the wave, run red-green-refactor:

1. **RED — write the failing test first.** Translate the §9 T-nn line (+ the §8 E-nn edge it
   depends on, + the §6 I-nnn it guards) into a concrete test. Name it after the behavior and
   cite the spec ID(s) in a comment or docstring, e.g. `test_empty_input_exits_2  # E-03, K-01`.
   Assert on **observable** behavior from §2/§4/§5, not on internals. Citing IDs keeps §11
   traceability mechanically checkable — `speccheck` reads exactly these tokens — so the ID
   must appear literally (`E-03`, not "edge case three") inside the test case's span.
2. **Verify RED — watch it fail.** Run that one test; confirm it **fails** (not errors) for the
   right reason — the missing behavior, not a typo or an import. Errors? fix the test until it
   *fails correctly*, then proceed. A test that passes immediately is testing nothing — it
   already encodes existing code; delete it and test what you are about to build.
3. **GREEN — minimal code.** Write the *smallest* implementation that passes and keeps the
   others green. Do not add features, options, or polish the test does not require. Honor the
   §4 contract shape and the §6 invariant exactly.
4. **Verify GREEN — watch it pass.** Re-run the whole suite; confirm the new test passes,
   nothing regressed, and output is clean (no warnings). **Fix code, never the test, to reach
   green.**
5. **REFACTOR — clean up while green.** Remove duplication, name things, extract helpers.
   Keep every test green; add no behavior.
6. **Commit.** `feat(<scope>): <what the T-nn group realized>` — one commit per group or per
   cohesive slice, and at minimum one per wave (*The wave loop*). **Commit intermediate
   work; never leave a finished wave uncommitted.**

Repeat until the §9 suite (and every I/K/E in §6/§7/§8) is green.

### The "implement everything" rule, concretely

- **Every** R/C/I/K/E/T in the spec is built. Close each with its green test.
- **Optional items** (`O-n`, `MAY`, `SHOULD`) are implemented *to the depth the spec states* —
  behind the gate the §4/§5 contract describes (a flag, an opt-in dependency group, an
  alternate surface), not omitted. If the spec says a surface is "optional", you *build* it as
  the optional surface; "optional" ≠ "skip".
- **Never silently drop a spec item.** Omitting an in-scope requirement is a conformance failure
  you will catch in Phase 3. If the user told you to scope something out, record the exact spec
  ID(s) excluded and the reason in the README and the conformance report.
- **Cross-cutting contracts (§5).** If the spec pins a diagnostics/verbosity contract, an
  error-code scheme, a configuration-precedence rule, or similar, implement it exactly as
  specified — including what must *not* happen (e.g. secrets or raw payloads never reaching a
  log level that forbids them, diagnostics never altering primary output) — and add the T-nn
  tests the spec allocates for it.
- **Determinism.** Where §6 requires determinism / reproducibility, make the deterministic path
  deterministic (seeds, stable ordering, stable serialization) and add its invariant test
  (repeat with identical inputs → identical outputs).
- **Edge semantics.** Implement the §8 E-nn outcomes as written (documented fallbacks, specific
  exit codes / error types, partial-work rules) — don't let them surface as unhandled
  exceptions or undefined behavior.
- **Formulas and metrics.** Compute every `$..$` / `$$..$$` formula exactly as written — same
  population, same denominator, same rounding — and give its zero-denominator / empty-population
  rule its own test (`test_unknown_rate_is_zero_when_no_judged_edges  # K-06`). Name the code's
  variables after the spec's symbols (`tp`, `fp`, `unknown_rate`) so a grader can read the
  formula off the implementation. If a symbol is undefined or a denominator unstated, stop and
  treat it as a spec defect (Phase 3.3), not as freedom to choose.

### When a bug shows up mid-build

Reproduce it, write a **failing regression test** (citing the E-nn/I-nnn it fixes), then run the
same red-green loop. Never fix a bug without the test that proves it — the fix and its guard
land together. Do not edit a *passing* test to make a *real* failure go away; fix the code or,
if the test itself was wrong, explain which and why. If the spec is what was wrong, see Phase 3.3.

### Phase 1 exit gate (run before Phase 2)

This is the last wave's gate plus the whole-suite run, and it closes Phase 1 only when **every
wave in the plan** has been executed, gated and committed — the wave ledger is the evidence.

Do not proceed until, all true:

```bash
<run all tests>     # green, no skipped T-nn, no warnings; junit.xml regenerated
<lint / typecheck>  # clean
<self-check>        # if the spec pins one
<speccheck>         # Phase A (--judge mock --strict): CONFORMING, 0 dangling, 0 stale, exit 0
```

The speccheck summary line is the proof that every §9 test group has a green test citing its
ID and that no R/C/I/K/E is uncited or untested. An ID that is `UNCITED`/`UNTESTED` here is a
spec item the loop above skipped — go back to RED for it. Verification is **evidence** (the run
output and the summary line), not assertion.

---

# Phase 2 — Make README.md reflect reality

When the suite is green, **rewrite/refresh `README.md` from what was actually built**, not from
the plan. A README that describes an intended interface the code does not have is a defect this
phase exists to prevent. If the repository has a README convention (a template, a peer project),
follow it; otherwise cover:

1. **Title + one-line what-it-does** — the §0 intent, in one sentence.
2. **Setup** — exact runtime/toolchain version, install command, optional dependency groups,
   required environment variables or host prerequisites. State which paths are offline /
   deterministic and which need external services.
3. **Quick start** — a copy-pasteable happy path using the **fixtures / sample data that exist**
   in the repo. No invented data.
4. **Usage** — one subsection per surface actually in §5 (CLI subcommands, API endpoints,
   library entry points, GUI screens), with the real flags/parameters and the real error
   codes / responses. Mark optional surfaces exactly as the code gates them.
5. **Artifacts and schemas** — the files/formats the implementation reads and writes, with
   versions, mirroring the §4 contracts. Where the README explains a metric or a flow, reuse the
   spec's formula (`$..$` / `$$..$$`) or `mermaid` diagram verbatim rather than paraphrasing it
   in prose — one source, no drift.
6. **Project layout** — a tree of the real source, test, and schema directories (each module's
   one-line role), generated from what exists, not from the spec's plan.
7. **Verification** — the exact commands from the Phase 1 exit gate, including the JUnit-emitting
   test run and the `speccheck … --strict` invocation, so the reader reproduces green and
   `CONFORMING`.
8. **Scope / deferrals** — if the user scoped anything out, list the excluded spec ID(s) and why;
   otherwise state that the full spec was implemented.

If the project renders the README into another format (PDF, site, docs bundle), regenerate it in
the same commit so the two never drift. Commit as
`docs(<scope>): README reflects built implementation`.

---

# Phase 3 — Proof: re-read the spec and audit every artifact

Implementation "works" is necessary; **conforms to the spec** is the goal. Do this pass last,
with fresh eyes, and write `SPEC_BUILD_REPORT.md` so the work is auditable.

### 3.1 Re-read SPEC.md as a grader

Run the gate first, on a fresh test run:

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck       # Phase A
speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm  --strict --out build/speccheck-llm   # Phase B, only once A is clean
```

`build/speccheck/SPEC_CONFORMANCE_REPORT.md` is the per-ID evidence table (§3 of that report:
ID → status → citing files and lines → joined test result); `speccheck.json` is the same data
for filling the §11 matrix. Anything not `PASSING` in either phase, and every dangling or stale
row, is a conformance defect to open as `F-nnn` before you go further. A `WEAKLY_PASSING` from
Phase B is fixed in the test (make it assert the specified outcome), after which both phases
are re-run.

Then re-read the spec *whole again* — as if grading someone else's build — for what the gate
cannot see: that a cited contract actually has the pinned shape, that a §5 table matches the
real surface, that a passing test asserts the *specified* outcome and not merely an outcome.
For **each spec family**, walk the checklist from Phase 0 and, for every ID, point at the
concrete evidence:

| Walk | Check, per ID | Evidence to produce |
| --- | --- | --- |
| §2 R-nn | requirement observable in the build | the module + test that realizes it |
| §4 C-nn | contract shape honored (type / schema / boundary) | the type / schema / file that pins it |
| §5 surfaces | operations, parameters, errors match the tables | the entry point + a test per operation |
| §6 I-nnn | invariant holds in the implementation | the invariant test (assert it, don't trust it) |
| §7 K-nn | measurable constraint met | error-code / threshold check, or a test |
| §8 E-nn | edge semantics implemented | the edge test's actual outcome |
| §9 T-nn | acceptance test present and green | the test file + green run |
| §11 | every ID traces to component → behavior → test | fill the matrix from evidence; flag any broken edge |

Open the §11 traceability matrix and confirm **no ID is dangling** — every
`ID → component → test` edge points at real, green code. Fill "where realized" and "verified
by" from `speccheck.json` (its per-ID source and test citations), not from memory. A dangling
edge (an ID with no code, or code with no test) is a conformance defect; open it as `F-nnn` and
either fix it or confirm it was an explicit user-directed deferral — and a deferred ID still
shows as `UNCITED` in the gate, so record the exact summary line and the deferred ids together
in the report rather than pretending the gate was clean.

### 3.2 Cross-check the artifacts against the spec

Review *every* produced artifact — not just the source tree — for adherence:

- **Every contract (§4) exists** with the pinned shape; names / fields / versions match the
  spec, not a close variant.
- **Every surface (§5)** matches the spec's tables — no extra or missing operations, no renamed
  parameters, the specified error codes / responses.
- **Schemas / fixtures** match the contract shapes; version numbers match §4.
- **Dependencies (§10)** are the ones the spec names; nothing the spec forbade sneaked in
  (verify a §6 boundary invariant with the self-check if one is pinned, otherwise by inspection
  of imports / manifest).
- **Data artifacts** the build writes are schema-valid and the shape §4/§10 pins.
- **Determinism:** where required, re-run the deterministic path with identical inputs →
  identical result; the invariant test holds.
- **Formulas:** each spec formula is computed as written (symbols, denominator, rounding,
  degenerate case) and its worked examples in the spec reproduce from the implementation.
- **Diagrams:** the built state machine / flow has exactly the transitions the normative rows
  specify; where the spec's diagram disagreed with its rows, the `F-nnn` and the `fix(<scope>):`
  that reconciled them are recorded.
- **Reference images and the design document:** every element the spec's `reference/*.png`
  show is present in the product, in the state the caption names; the rhythm, alignment and
  sizes the typography / design document assigns are what the product draws (§3.2b is where you
  look; this row is where you record that each image was compared).
- **README (Phase 2)** describes what the code *does*, verified command-by-command (run the
  README's commands; every one works as written).
- **Every wave closed:** each wave in `IMPLEMENTATION_PLAN.md` §4 has its gate command, its
  real exit code and its commit sha in the ledger; a wave with no gate run is not built, and a
  wave with no commit is not reviewable.
- **No silent omissions:** diff the Phase 0 checklist against reality — every in-scope box is
  closed, or its deferral is explicitly recorded with user approval.

### 3.2b Look at it — the observed pass

The gate and the walk above see ids, tests and citations. They do not see the product. A build
has reached `CONFORMING` with every heading rendered flush against the preceding paragraph and
display math left-aligned, because every test it cited was green and every golden it compared
against had been produced by the same pipeline. This step exists so that cannot be the verdict.

1. **Run the product** — not the harness, the product — on the spec's own corpus, in the state
   the spec's reference images show (the theme, the panes open, the features set).
2. **Compare region by region against the reference images** the spec ships (`reference/`) and
   against the typography / design document where the spec delegates values to it: every element
   present, every row's anatomy, every state, the rhythm between blocks. Write down each
   difference as an `F-nnn` — a difference from the reference is a defect unless the spec says
   otherwise.
3. **Record what you looked at**: the screenshot path or the window you drove, the document, the
   theme, and the outcome of every *observed* T-nn (§9), one line each. A screenshot a person
   opened counts; a screenshot nobody opened does not.
4. **If the environment cannot show a window** (locked console, no screen-recording permission,
   a CI runner without a window server), the observed group is **pending**: say so in the
   report, mark every observed T-nn *verification pending*, and set the verdict to
   `VERIFICATION PENDING` — never `PASS`. Do not substitute the harness for the look.
5. **Self-generated goldens are not an oracle.** A golden image or fixture produced by the code
   under test is a regression guard: it proves the output is *stable*, not that it is *right*.
   Conformance evidence for a rendered surface needs an oracle the build did not produce — the
   spec's reference images, a measured quantity the spec states (a gap in points, a centred
   bounding box), or a person. Say in the report which of the three each visual claim rests on.

### 3.3 Fix, then re-verify

For every defect found (`F-nnn`: location, what's off, why it matters, resolution): fix the
**code or the spec**, not the report. Prefer fixing the implementation to match the spec; only
edit `SPEC.md` (`fix(<scope>): ...`, bump its version header) when the spec itself was
ambiguous or wrong — and say so in the report. After fixes, re-run the Phase 1 exit gate and
re-walk §3.1 — gate first, then by hand — until both are clean. Paste the real (truncated) run
output as evidence, always including the speccheck summary line verbatim.

Write `SPEC_BUILD_REPORT.md` in the spec's notation: cite formulas in `$..$` / `$$..$$` and keep
requirement ids outside math and mermaid blocks (the report is rendered with the same
`spec2pdf.sh` pipeline, whose clickable-id pass rewrites ids inside inline math and skips fenced
blocks). Any mermaid diagram in the report (e.g. the realized module graph) carries a caption
naming the ids it depicts.

### Done when — all four hold

0. **Planned:** the plan exists (`IMPLEMENTATION_PLAN.md` and one detail document per wave),
   its §7 fork was answered by the user, and every wave in it is closed with a gate run and a
   commit.
1. **Built:** §9 suite green (no skipped T-nn), lint clean, self-check (if pinned) passes; every
   R/C/I/K/E/T realized or explicitly deferral-recorded.
2. **Documented:** `README.md` (and any rendered copy) describes the running system,
   command-verified.
2b. **Observed:** every §9 *observed* T-nn has a recorded outcome from a person looking at the
   running product against the reference images (§3.2b), or the verdict is
   `VERIFICATION PENDING` with the environmental reason named.
3. **Conforming:** on the final test run `speccheck … --judge mock --strict` exits `0`
   (`CONFORMING`, 0 dangling, 0 stale) and then `speccheck … --judge llm --strict` exits `0`
   (0 weak, judge available, `unknown_rate` within bound) — or every exception is a
   user-approved deferral named in the report; the §11 matrix is fully traced; the §3.2 artifact cross-check found no open
   (unapproved) defect; `SPEC_BUILD_REPORT.md` records the per-ID evidence, the summary line, and
   the final verdict.

Report the verdict in one line, then stop:

```text
Spec coverage: <NN>/<NN> IDs realized (<k> deferred: <ids + why>)
speccheck (mock): <summary line, verbatim, from the final --judge mock --strict run>
speccheck (llm):  <summary line, verbatim, + model name; or "not run: <reason>">
Observed: <observed T-nn outcomes, one line each, with the screenshot or window driven; or "PENDING: <reason>">
Readiness: BUILT / BUILT WITH DEFERRALS / INCOMPLETE
Conformance: PASS / PASS WITH NOTES / VERIFICATION PENDING / FAIL
```

---

# Anti-rationalization checklist (stop and correct before "done")

- [ ] The plan existed **before** the first line of production code: `IMPLEMENTATION_PLAN.md`
      plus one `DETAILED_IMPLEMENTATION_PLAN_W<n>.md` per wave, with the §7 fork answered
- [ ] Implemented **wave by wave in the plan's order**, each wave ending at its §6 gate with the
      real commands and exit codes, and **committed before the next wave began**
- [ ] Wrote the failing **test first** for each T-nn and *watched it fail for the right reason*
      (no production code ahead of its test)
- [ ] Implemented **every** in-scope spec item; nothing silently dropped
- [ ] Optional items implemented to spec depth (**gated**, not omitted)
- [ ] §8 edge cases + §6 invariants have tests that assert the outcome, not just run the code
- [ ] Every spec formula is implemented as written, with a test for its degenerate case; every
      diagram/row disagreement went through `F-nnn` + `fix(<scope>):`, not a silent choice
- [ ] §5 surfaces (operations, parameters, error codes / responses) match the spec exactly
- [ ] Cross-cutting §5 contracts (diagnostics, errors, config) built + tested, including their
      "must not" clauses
- [ ] Full suite green, no skipped T-nn, no warnings; lint clean; self-check (if pinned) passes
- [ ] `README.md` rewritten from the built system; its commands all run as written; any rendered
      copy regenerated in the same commit
- [ ] Every T-nn cites its spec ID literally so `speccheck` can see it
- [ ] Phase A `speccheck … --judge mock --strict` on the **final** test results: `CONFORMING`,
      0 dangling, 0 stale, exit `0`; then Phase B `--judge llm --strict`: 0 weak, exit `0` (or
      every exception is a named, user-approved deferral); both summary lines pasted into
      `SPEC_BUILD_REPORT.md`
- [ ] Re-read `SPEC.md`; §11 matrix fully traced from `speccheck.json` (no dangling
      `ID → component → test` edge)
- [ ] Cross-checked **all** artifacts (source, tests, schemas, manifest, data, README) against the
      spec; defects recorded and fixed; `SPEC_BUILD_REPORT.md` written
- [ ] Deferrals (if any) are explicit, user-approved, id-listed in both README and the report
- [ ] Verification is evidenced with real run output, not assertion
- [ ] I ran the product and looked at it against the spec's reference images (§3.2b), and the
      report records what I looked at — or the verdict says `VERIFICATION PENDING` and why
- [ ] No golden or fixture used as conformance evidence was produced by the code it certifies
- [ ] Each wave was executed by one agent against its brief; no scratch files inside the package;
      every "green" in a commit message was a gate the orchestrator re-ran
- [ ] The plan's LOC budget was treated as an estimate; code above the smallest known complete
      build of the same spec is named in the report as added structure, not as requirement

> **The build succeeds when `speccheck` can point every spec ID at a green test, the README
> reads like the thing that was built, and a grader re-reading the spec and walking §11 finds
> nothing dangling — no undocumented intent left on either side of the contract.**
