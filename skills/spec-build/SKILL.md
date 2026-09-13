---
name: spec-build
description: Implement a SPEC.md (the source of truth for a system) in any language or stack using test-driven development, then make README.md reflect the built reality, then re-read SPEC.md and audit every produced artifact for conformance, writing SPEC_BUILD_REPORT.md. Use when asked to "build the spec", "implement SPEC.md", "make this spec real", or after spec-writing/spec-review produce a Level-2/3 spec. Pairs with spec-writing (authoring the spec) and spec-review (auditing it, yielding SPEC_REVIEW_REPORT.md + F-nnn findings and a P0/P1/P2 remediation plan). Encodes the red-green-refactor loop over the spec's §9 test groups, the "implement everything unless told otherwise" default, README-sync, and the final spec-conformance pass.
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

The build has three phases and you do not skip any:

1. **Build (TDD).** Implement the spec test-first — write the failing test from §9, watch it
   fail for the right reason, write the minimal code, watch it pass, refactor. Commit
   intermediate work.
2. **Document.** When the suite is green, make `README.md` reflect the implemented system
   (not the intended one).
3. **Prove conformance.** Re-read `SPEC.md`, then review *every* produced artifact against it
   and write a conformance report. Do not call the work done until this pass is clean.

**The default is to implement everything in the spec.** Every requirement, contract, invariant,
constraint, edge case, and acceptance test in the spec gets realized — unless the user explicitly
told you to scope something out. A `MAY`/`SHOULD`/optional (`O-n`) item is still implemented to
the depth the spec states; "optional" means gated (behind a flag, config key, or feature toggle),
not omitted. If you decide *not* to build an in-scope item, say so, name the spec ID, and get the
user's approval first.

## When to use

- "implement SPEC.md" / "build the <X> spec" / "make `<SPEC.md>` real"
- a project has a `SPEC.md` but no implementation, or only a partial one
- after `spec-review` returns `READY` (or `READY WITH MINOR FIXES`) — start building
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
| source tree | the implementation | every §2 requirement, §4 contract, §6 invariant, §7 constraint |
| test tree | the §9 acceptance suite | every T-nn id, one group per §9 subsection |
| schemas / fixtures / sample data | artifacts the spec pins | the §4 contract shapes, §10 data |
| build / package manifest | env, deps, entry points | the §5 surfaces, §10 deps |
| `README.md` | the built reality | Setup / Usage / Artifacts / Verification / layout |
| `SPEC_BUILD_REPORT.md` | conformance evidence | per-ID evidence + verdict (Phase 3) |

Define, once, the three commands you will use throughout and put them in the README:

```bash
<run one test>      # e.g. pytest tests/test_x.py::test_y -q | go test ./pkg -run TestY | cargo test y | npm test -- -t "y"
<run all tests>     # the full §9 acceptance suite
<lint / typecheck>  # whatever the project's CI runs
<self-check>        # only if the spec pins a boundary/self-check command (e.g. a §6 "no network" invariant)
```

---

# Phase 0 — Commit to the spec before writing a line

Do this once, up front. It is the plan that keeps TDD honest.

### 0.1 Read the spec fully, end to end

Read the whole `SPEC.md` in one pass **before** touching code — do not skim. Build a mental
model of the §0 intent, the §3 state flow, and any boundary the spec draws (deterministic $\leftrightarrow$
probabilistic, trusted $\leftrightarrow$ untrusted, online $\leftrightarrow$ offline). If a `SPEC_REVIEW_REPORT.md` exists,
read its **Remediation Plan** (P0/P1/P2), **Final Verdict**, and detailed findings (`F-nnn`,
with severity). If the verdict is `NOT READY`, stop and route through `spec-review` /
`spec-writing` first.

### 0.2 Extract the build list from the spec's own IDs

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
implementation order. This checklist *is* your proof that "everything got implemented": every
box closes on a green test that cites its spec ID.

### 0.3 Seed the skeleton (if empty)

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
For each T-nn group, run red-green-refactor:

1. **RED — write the failing test first.** Translate the §9 T-nn line (+ the §8 E-nn edge it
   depends on, + the §6 I-nnn it guards) into a concrete test. Name it after the behavior and
   cite the spec ID(s) in a comment or docstring, e.g. `test_empty_input_exits_2  # E-03, K-01`.
   Assert on **observable** behavior from §2/§4/§5, not on internals. Citing IDs keeps §11
   traceability mechanically checkable (`grep` the tests for the ID).
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
   cohesive slice. **Commit intermediate work; do not batch.**

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

### When a bug shows up mid-build

Reproduce it, write a **failing regression test** (citing the E-nn/I-nnn it fixes), then run the
same red-green loop. Never fix a bug without the test that proves it — the fix and its guard
land together. Do not edit a *passing* test to make a *real* failure go away; fix the code or,
if the test itself was wrong, explain which and why. If the spec is what was wrong, see Phase 3.3.

### Phase 1 exit gate (run before Phase 2)

Do not proceed until, all true:

```bash
<run all tests>     # green, no skipped T-nn, no warnings
<lint / typecheck>  # clean
<self-check>        # if the spec pins one
```

Every §9 test group has a green test citing its ID; `grep -rnE '\b[RCIKET]-[0-9]{2,3}\b' <test tree>`
shows the requirements/invariants/edges/tests are anchored. Verification is **evidence** (the run
output), not assertion.

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
   versions, mirroring the §4 contracts.
6. **Project layout** — a tree of the real source, test, and schema directories (each module's
   one-line role), generated from what exists, not from the spec's plan.
7. **Verification** — the exact commands from the Phase 1 exit gate, so the reader reproduces green.
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

Re-read the spec *whole again* — as if grading someone else's build. For **each spec family**,
walk the checklist from Phase 0 and, for every ID, point at the concrete evidence:

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
`ID → component → test` edge points at real, green code. A dangling edge (an ID with no code,
or code with no test) is a conformance defect; open it as `F-nnn` and either fix it or confirm
it was an explicit user-directed deferral.

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
- **README (Phase 2)** describes what the code *does*, verified command-by-command (run the
  README's commands; every one works as written).
- **No silent omissions:** diff the Phase 0 checklist against reality — every in-scope box is
  closed, or its deferral is explicitly recorded with user approval.

### 3.3 Fix, then re-verify

For every defect found (`F-nnn`: location, what's off, why it matters, resolution): fix the
**code or the spec**, not the report. Prefer fixing the implementation to match the spec; only
edit `SPEC.md` (`fix(<scope>): ...`, bump its version header) when the spec itself was
ambiguous or wrong — and say so in the report. After fixes, re-run the Phase 1 exit gate and
re-walk §3.1 until the walk is clean. Paste the real (truncated) run output as evidence.

### Done when — all three hold

1. **Built:** §9 suite green (no skipped T-nn), lint clean, self-check (if pinned) passes; every
   R/C/I/K/E/T realized or explicitly deferral-recorded.
2. **Documented:** `README.md` (and any rendered copy) describes the running system,
   command-verified.
3. **Conforming:** the §11 matrix is fully traced; the §3.2 artifact cross-check found no open
   (unapproved) defect; `SPEC_BUILD_REPORT.md` records the per-ID evidence and the final verdict.

Report the verdict in one line, then stop:

```text
Spec coverage: <NN>/<NN> IDs realized (<k> deferred: <ids + why>)
Readiness: BUILT / BUILT WITH DEFERRALS / INCOMPLETE
Conformance: PASS / PASS WITH NOTES / FAIL
```

---

# Anti-rationalization checklist (stop and correct before "done")

- [ ] Wrote the failing **test first** for each T-nn and *watched it fail for the right reason*
      (no production code ahead of its test)
- [ ] Implemented **every** in-scope spec item; nothing silently dropped
- [ ] Optional items implemented to spec depth (**gated**, not omitted)
- [ ] §8 edge cases + §6 invariants have tests that assert the outcome, not just run the code
- [ ] §5 surfaces (operations, parameters, error codes / responses) match the spec exactly
- [ ] Cross-cutting §5 contracts (diagnostics, errors, config) built + tested, including their
      "must not" clauses
- [ ] Full suite green, no skipped T-nn, no warnings; lint clean; self-check (if pinned) passes
- [ ] `README.md` rewritten from the built system; its commands all run as written; any rendered
      copy regenerated in the same commit
- [ ] Every T-nn cites its spec ID so §11 traceability stays `grep`-able
- [ ] Re-read `SPEC.md`; §11 matrix fully traced (no dangling `ID → component → test` edge)
- [ ] Cross-checked **all** artifacts (source, tests, schemas, manifest, data, README) against the
      spec; defects recorded and fixed; `SPEC_BUILD_REPORT.md` written
- [ ] Deferrals (if any) are explicit, user-approved, id-listed in both README and the report
- [ ] Verification is evidenced with real run output, not assertion

> **The build succeeds when the implementer can point every spec ID at a green test, the README
> reads like the thing that was built, and a grader re-reading the spec and walking §11 finds
> nothing dangling — no undocumented intent left on either side of the contract.**
