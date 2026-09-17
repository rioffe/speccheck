---
name: spec-plan
description: Turn a SPEC.md (plus its SPEC_REVIEW_REPORT.md when one exists) into an IMPLEMENTATION_PLAN.md — the verdict, the evidence from any prior builds, the target shape, the dependency-wave order with a gate per wave, the LOC budget, the structural rules that make the observed failures impossible, and the single fork decision — and, when the waves are big enough to execute one at a time, into per-wave DETAILED_IMPLEMENTATION_PLAN_WN.md documents. Use when asked to "plan the implementation", "make an implementation plan for SPEC.md", "how should we build this spec", "break this spec into waves", or between spec-review (READY) and spec-build. Pairs with spec-writing (authors the spec), spec-review (audits it), and spec-build (implements it, test-first: this plan is what that skill executes).
license: MIT
---

# spec-plan

Turn a `SPEC.md` into an **implementation plan**: the document that decides *in what order* the
spec gets built, *what shape* the repository takes, *how much* code each slice is worth, *which
structural rules* prevent the failures this system has already suffered, and *which single fork*
the human has to settle before work starts.

It sits between `spec-review` (the spec is READY) and `spec-build` (the spec is built). It is a
**plan, not a report**: nothing in it may claim that anything was executed. Every sentence is
either a decision, a measured fact about existing artifacts, or a command with its expected
result.

Two artifacts, both optional to the human and independent of `speccheck`:

| Artifact | What it is | When |
| --- | --- | --- |
| `IMPLEMENTATION_PLAN.md` | the plan proper — 7 sections, one page per section, the wave order and the fork | always |
| `DETAILED_IMPLEMENTATION_PLAN_W<n>.md` | one executable brief per wave — file-by-file deliverables, work items, test plan, gate, traceability, handoff | when the waves are large enough that an agent will execute them one at a time |

## When to use

- "plan the implementation of `<SPEC.md>`" / "how should we build this spec?" / "break it into waves"
- a spec passed review and nobody has decided the target shape, the order, or the slice budgets
- a spec has several prior implementations (or several branches) and the plan must learn from them
- an implementation stalled halfway and the remaining work needs re-planning around what exists

Do **not** use it to:

- write or fix the spec — that is `spec-writing` (and the P0/P1 remediation loop with `spec-review`);
- start building — that is `spec-build`, which executes this plan;
- audit an implementation's conformance — that is `spec-build`'s Phase 3 and its
  `SPEC_BUILD_REPORT.md`.

If `SPEC_REVIEW_REPORT.md` says `NOT READY` or leaves P0 findings open, stop: route through
`spec-writing` first. A plan built on an unresolved spec encodes the ambiguity into the order.

## Before writing: gather the evidence

The plan is an argument from evidence, not a greenfield guess. Collect, and cite in the front
matter, everything you can measure:

1. **The spec, end to end.** `SPEC.md` in one pass — §0 intent, §3 state model, §4 contracts,
   §5 surfaces, §6 invariants, §7 constraints (especially any formula), §8 edge cases, §9 the
   test groups, §10 dependencies, §11 the traceability matrix **including its status markers**,
   §12 the decisions awaiting confirmation. The §11 status column is the top of the work list.
2. **The review**, if present: `SPEC_REVIEW_REPORT.md`'s remediation plan (P0/P1/P2) and its
   dimension scores. A weak dimension predicts which slice will churn.
3. **Prior builds of the same spec**, if any exist — sibling repositories, branches, a comparison
   document, the git history. For each: measured production LOC and file count, its shape in one
   phrase, and *what ended it*. Without this section the plan is a guess wearing a table.
4. **The environment**: toolchain and version, whether the package manager and any vendoring can
   reach their sources, the assets that must be vendored (fonts, grammars, a vendored library),
   the platform limits (a window server? a signing identity? a tag?). Plans fail at these seams.
5. **House conventions**: an existing README layout, a Makefile's targets, a CI workflow, a
   naming scheme the spec already cites. Match them; do not invent a second convention.

**Verify every digest you cite.** If a source document or a comparison document quotes a hash,
a commit, a tag or a version, compute it before repeating it. A plan that cites a hash nobody
computed is the first self-certification in the project.

## The 7-section template

Section order is fixed; the contents scale with the system. Omit a section only when it genuinely
does not apply, and say so in one line rather than leaving it out silently.

````markdown
# Implementation plan — <project> (implementing `SPEC.md` v<x.y>)

> - **Target:** <the artifact and its surfaces> satisfying `SPEC.md` (sha256 `<measured digest>`)
>   and `<any second normative document>` (sha256 `<measured digest>`).
> - **Size expectation:** <the spec's own expectation, if it states one>; this plan budgets
>   **<lo>–<hi> production lines** (~<n> files) plus <lo>–<hi> test lines and <lo>–<hi>
>   non-source lines (<build scripts, launcher, manifests>).
> - **Method:** red-green-refactor over the §9 test groups; verification apparatus before the
>   feature it guards; `SPEC.md` never edited.

---

## 1. Verdict

<One paragraph. Commit to a shape and an ordering, name the two or three decisions that carry
the plan, and state what it refuses to do. Then the number: what this lands production LOC at,
and which shortcut would fit in less by dropping a subsystem — with the subsystem named.>

## 2. What the evidence says (this is not a greenfield guess)

<The measured table of prior builds — production LOC / files, shape, and what ended each one —
or, when there are none, the measured facts about the starting tree: what exists, what the spec
marks *not yet realised*, *open defect*, *verification pending*.>

| Build | Prod LOC / files | Shape | What ended it |
|---|---|---|---|
| … | … | … | … |

<Two or three sentences naming the **systemic** failure modes the evidence exposes — the ones
that are orthogonal, and that a plan which does not structurally address will repeat.>

## 3. Shape

```mermaid
flowchart LR
  <the target graph: executables, libraries, test targets, vendored targets, and which links which>
```

- <Why this split is mandated: cite the spec rows (§9 target groups, a contract that needs a
  library target, a "links, never copies" requirement).>
- **Literal filenames.** §11's "where realized" column names real files. Name them exactly those,
  and §11 becomes mechanically checkable. Renaming everything is traceability drift you get for
  free by not renaming.
- **Headless/purity rule**, if the spec has one: <what must not be read ambiently — clock, locale,
  bundle, screen, user defaults, network — and what is injected instead>.
- **Layer direction:** <the one-way dependency order, e.g. contracts → pipelines → services →
  session → views. No cycles.>

## 4. Order (waves; each ends at a gate, not at a file count)

1. **W0 <name>** — <contents> Gate: <commands>, <T-nn>.
2. **W1 <name>** — <contents> Gate: <commands>, <T-nn>.
   *<why this wave is here, when the ordering is the whole point>*
…
N. **W<n> Prove it** — the live pass (below), the README rewrite, the §11 walk and the
   conformance report.

## 5. LOC budget (production source, excludes vendored code)

| Slice | Files | LOC |
|---|---|---|
| <slice> (W<i>) | <n–n> | <lo>–<hi> |
| **Total** | **~<n>** | **<lo>–<hi>** |
| Tests (separate; not "the program") | <n–n> | <lo>–<hi> |
| <build scripts / launcher / manifests> | — | <lo>–<hi> |

<Anchors: the measured sizes of prior builds or of the closest comparable modules, which set the
floor and the ceiling. Then the rule: if the estimate approaches the ceiling, decompose the
expensive slice — never drop a subsystem to fit the number.>

## 6. Rules that make the observed failures impossible

| Prior failure | Structural rule |
|---|---|
| <the failure, with its evidence> | <the rule that makes it impossible, and where it is checked> |

**Live verification (the last wave).** <Name the surface that can only be verified by driving the
running product, the exact commands, and the artifacts to inspect. Any manual test is not "done"
until that pass.>

## 7. One fork, then action

**<The single decision the human must settle, in bold, with its rationale, the alternative, and
what the alternative costs.>**

<If the alternative is genuinely viable, say what stays true in both branches: the ordering, the
budgets, the rules. Never present a fork as a menu.>

**Next concrete action:** <the first wave's first command, with what "done" looks like.>
````

## Wave design rules

The order is the plan's real content. These rules come from plans that were executed, and the
failures they prevent are the ones the evidence section names.

- **Verification apparatus before the feature it guards.** A harness, a golden set, a metrics
  function or a fixture lands in an earlier wave than the code it measures. This is what lets the
  later waves assert anything at all instead of asserting that a table has the right names.
- **The spec's own formulas and metrics are code, and they are the first pure wave.** If §7 or a
  contract defines a metric, a tolerance, a width, a score or a budget, it is an oracle. Write it,
  test it with synthetic inputs, and let every later wave measure itself against it.
- **The trust boundary precedes every parser and decoder.** Ceilings, sanitisers and network
  isolation go in before the components they bound, or invariants like "no oversized input
  reaches a parser" become a retrofit into every pipeline.
- **A runnable artifact exists by the end of the first wave.** Packaging, the manifest, the build
  script and the launcher come before the features, so the first gate is a real end-to-end one.
- **Name the slice that every prior attempt failed to start.** If the evidence says one subsystem
  was never written, that subsystem gets its own wave, its own gate, and — when it is only
  observable through the product — live verification. Do not let it fall out of the plan as
  "remaining work".
- **Each wave ends at a gate, and the gate names commands and spec IDs.** A wave whose gate is a
  file count is not a wave. Prefer `build`, `test`, a filtered test group, a scripted harness run,
  a signature check, an exit code.
- **Wave size is a session, not a subsystem.** A wave should be executable by one agent in one
  sitting, with its plan document as the brief. When a wave is larger than that, split it (and
  give each part its own detail document) rather than writing a wave nobody can execute.
- **Partial coverage is declared, not implied.** When a wave only half-proves a `T-nn`, write
  which clauses it proves now and which wave proves the rest — in the plan and in the wave doc.

## Optional: the per-wave detail documents

When the order is settled and the waves are large, one `DETAILED_IMPLEMENTATION_PLAN_W<n>.md` per
wave turns the plan into something an agent can execute without re-reading the spec to make
decisions. Same conventions: exhaustive, evidence-cited, and free of execution claims.

```markdown
# Detailed implementation plan — W<n>: <title from §4>

> - **Wave:** W<n> of W0–W<m> (`IMPLEMENTATION_PLAN.md` §4 item <k> — "<that item's wording>").
> - **Spec basis:** `SPEC.md` v<x.y>, sha256 `<measured digest>`; <second doc, digest>. Neither is
>   edited by this wave.
> - **Gate:** <one sentence: the observable state the wave must end in>
> - **Budget:** <lo>–<hi> production lines across <n> files (`IMPLEMENTATION_PLAN.md` §5 row
>   "<slice>").
> - **Depends on:** W… (exact symbols/files). **Unlocks:** W… (exact symbols/files).

## 1. Objective and spec obligations
## 2. Entry preconditions
## 3. Deliverables, file by file
### 3.1 `path/File.ext` — NEW|EDIT, ~NNN–NNN lines
## 4. Work items, in order (red → green → refactor)
## 5. Test plan
## 6. Gate: commands and expected results
## 7. Traceability
## 8. Risks, traps, and the structural rules this wave must not break
## 9. Exit criteria and handoff contract
```

Section contract:

- **§1** — table `spec id | obligation (paraphrase, ≤20 words) | how this wave discharges it`.
  Mark half-discharged ids `(half)` and name the wave that proves the rest.
- **§2** — the exact files/symbols that must already exist, each attributed to the wave that
  created it, plus the external assets this wave needs (vendored libraries, fonts, fixtures).
- **§3** — one subsection per file: responsibility, the **public surface as a signature block**,
  numbered behaviour rules each ending in a spec-id citation, the invariants it must hold, and
  every error/edge path it owns. No file outside the plan's ownership table.
- **§4** — numbered work items `W<n>-01 …`: *test written first* (file + case name + the
  assertion), *then* the implementation delta, *then* the evidence that closes it. Order is
  dependency-true: no item may need a later item.
- **§5** — table `group/target file | spec ids | what must be asserted | how it runs`.
- **§6** — numbered shell commands, each with its expected exit code and the observable that
  proves it. Only commands the spec or the plan already define. No "run the tests".
- **§7** — table `spec id | file.symbol | test | status now → status after this wave`, covering
  the §11 status rows this wave closes (*not yet realised* / *open defect* / *verification
  pending*) and every id in §1.
- **§8** — the traps specific to this slice, each tied to a row of the plan's §6 and to the
  observation that produced it, plus the rule that makes it impossible here.
- **§9** — frozen files; the symbols later waves may call (with signatures); the gate command the
  next wave re-runs to confirm this wave is still intact.

Two rules keep a set of wave documents coherent, and both were learned the hard way:

- **One ownership table, written once** (in the plan or in a shared conventions file): which wave
  creates each file, which wave edits it later. Two waves editing one file is how a plan becomes
  a merge conflict; a wave editing a file it does not own must instead send the owning wave the
  exact signature it needs.
- **Interfaces are frozen by name in §9.** Later waves call the earlier wave's symbols by the
  names the earlier wave's §9 published. A rename after publication breaks every downstream doc.

## Rules of the road

- **No invented IDs.** Every `R/C/I/K/E/T/O/D/F` id cited must exist in `SPEC.md`. Never renumber,
  reword, merge or delete an id — the spec retires with a strike-through, and so does the plan.
- **No execution claims.** Nothing is built yet. Gates are commands plus *expected* results. Never
  write "tests pass", "verified", "as shown", "we ran". Say "expected: exit 0, …".
- **Cite measured numbers.** LOC, file counts, timings, digests: measured, or marked as an
  estimate with the anchor it came from. A budget column with no anchor is decoration.
- **Plans never certify.** A plan that reports its own success has replaced evidence with
  assertion. The plan's job ends at "here is the order and the gate"; whether the gate passed is
  the build report's job.
- **No stubs in the plan's language.** No "scaffold for later", "MVP", "v1 of this", "TODO" — those
  are permissions to ship a subset, and they are how a plan loses a subsystem without anyone
  deciding to.
- **Stay out of the spec.** The plan never edits `SPEC.md`, never "uplifts" its version, never
  renames its artifacts. Spec drift discovered while planning is a finding for `spec-writing`.
- **Documents are written last.** A user-facing document (README, help file, changelog) is a
  deliverable of the final wave, written from the built surface. A plan that schedules the docs
  early has scheduled a lie.
- **Every wave's gate must be runnable by the next wave.** If the gate needs a service, an
  identity, a tag or a device the environment does not have, say so in the plan and name the
  stand-in — before the wave starts, not after it fails.

## Anti-patterns

| Anti-pattern | Why it fails | Instead |
| --- | --- | --- |
| Planning without the evidence section | the same failures are re-discovered in wave 6 | measure prior builds / the starting tree first |
| Waves by file count ("wave 2: the managers") | no gate, no ordering argument, no way to tell if a wave is done | waves by dependency, each ending at a runnable gate |
| A harness written after the feature | the tests assert names and sizes because they have no oracle | apparatus first |
| Budgets with no anchors, summing to a wish | the plan silently drops a subsystem to fit | anchor each slice on a measured comparable |
| Renaming the paths §11 cites | the traceability matrix points at files that do not exist | literal filenames in the first wave |
| A wave doc per file rather than per session | unexecutable documents; agents die mid-wave | one document per wave, split the wave when it is too big |
| Two waves owning one file | merge conflicts, drift, a build no one can repair | one ownership table; cross-wave requests via the owner |
| The plan claims results | self-certification; the human trusts a document instead of a run | commands plus expected results, always |
| The plan's fork section is a menu | work starts on all branches at once | one decision, one recommendation, one cost |

## Done bar

A plan is finished when all of these are true:

1. The 7 sections are present, in order, with the front matter's target, size expectation and
   method filled in.
2. §2 contains measured numbers about real artifacts, not adjectives.
3. Every wave in §4 names its contents, at least one command, and the spec IDs it discharges.
4. §5's rows sum to the stated total, and each row has an anchor.
5. §6 has one row per failure the evidence exposed, each with the rule that prevents it.
6. §7 names exactly one fork, with rationale, alternative and cost — and a next concrete action.
7. Every digest, tag, version and count in the document was computed, not copied.
8. If wave documents exist: each has its nine sections, its ownership is unambiguous, its gate is
   copy-pasteable, and its §7 covers every id in its §1.
9. Nothing in either document claims that something already ran.

## Worked example, and what it cost

`SPEC.md` v0.8 of a native macOS Markdown viewer (an 851-line spec: 41 requirements, 17 contracts,
13 invariants, 15 constraints, 28 edge cases, 43 tests, 39 open decisions) was planned with this
template into a 7-section `IMPLEMENTATION_PLAN.md`, then into eleven wave documents
(`DETAILED_IMPLEMENTATION_PLAN_W0.md` … `_W10.md`), and executed wave by wave against those
documents.

What the plan got right, and should be copied:

- **The order.** Packaging first (a runnable, signed bundle by W0), the pure contracts and the
  spec's metrics second (they are the oracles), the trust boundary third *before* any parser, then
  code, math, diagrams, session, UI, harness, proof. Every wave's gate was runnable by the next.
- **The structural rules.** "Every public symbol has a production call site", "the harness links,
  never copies", "the docs are written last", "no test certifies a table" — each mapped to a
  measured failure of an earlier build, and each one that was checked caught a real defect.
- **The wave documents.** Execution happened against the wave docs, not the plan; they were what
  made an eleven-wave build tractable, and their §9 handoff contracts kept interface drift out.

What the plan got wrong, and should be corrected by the next one:

- **The budget was ~30–100 % low.** Planned 8.45k–11.35k production lines and 2.2k–3.2k test
  lines; measured 14.2k production across 47 files and 10.6k tests across 30. The anchors were
  transcription-level (a prior build's file sizes) rather than shape-level (the repair layers, the
  theme catalogue, the block chrome, two test targets). **Anchor on the shape's branches, not on
  another build's total.**
- **It cited hashes nobody computed.** The plan repeated two digests from its source documents;
  measured, neither matched. Verify every digest, and put the measurement in the plan.
- **It assumed the wave documents would be read once.** The first agent of each wave re-derived
  context it needed anyway; a wave doc earns its keep when it names the *preconditions*, the
  *frozen interfaces* and the *gate commands*, which is exactly what §2, §9 and §6 are for.
