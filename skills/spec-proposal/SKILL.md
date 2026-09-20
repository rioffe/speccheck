---
name: spec-proposal
description: Write a PROPOSAL document — a scoped, evidence-grounded change to an existing, already-implemented SPEC.md or tool, not a greenfield spec. Encodes the fixed six-section template (the problem, the change, what it costs, alternatives considered, decisions for the requester, what the change does not do) with its front-matter blockquote (Status/Applies to/Notation/Evidence), draft R/C/I/K/E/T rows for spec-writing to fold in once confirmed, and the two-column decision table format (ID | Statement, each cell an option-versus-option choice with a recommendation). Use when asked to "write a proposal", "propose a fix for X", "draft a change to the spec for Y", after a real defect, metric, or run's output surfaces a pattern worth fixing but not yet decided, or when asked to add a new capability to a tool that already has a SPEC.md. Pairs with spec-review and spec-build (the artifacts that usually surface the evidence a proposal is grounded in) and spec-writing (turns a confirmed proposal's draft rows into real SPEC.md rows; a proposal is never itself an edit to SPEC.md).
license: MIT
---

# spec-proposal

Write a **PROPOSAL** — the document that argues for one scoped, evidence-grounded change to a
system that already has a `SPEC.md` and an implementation. It is not a spec: it never edits
`SPEC.md` directly, and no normative row exists until `spec-writing` folds a *confirmed* decision
in. It is not a bug report either: a proposal names the exact rows it would add or change, in the
spec's own ID taxonomy, ready to hand to `spec-writing` the moment the requester confirms it.

## When to use

- "write a proposal for `<X>`" / "propose a fix for `<the thing that just went wrong>`"
- a real run, review, or investigation surfaced a pattern (a defect, a gap, a metric worth
  chasing) and the next step is a considered *change*, not just a report of what was found
- "should we add `<capability>` to this tool" where the tool already has a `SPEC.md`
- between finding something (a build report, a review, an ad-hoc investigation) and
  `spec-writing` turning a decision into real spec rows

Do **not** use it to:

- author a spec from scratch — that is `spec-writing`; a proposal exists only in the shadow of a
  spec that already has rows to amend
- report findings without proposing a change — if there is nothing to decide yet, write the
  report (a build report, a review, a plain investigation write-up), not a proposal
- make the edit yourself — a proposal is read by a human (the "requester") who confirms or
  rejects each decision; only after that does `spec-writing` touch `SPEC.md`

## The one rule everything else follows

> **A proposal is exactly as strong as the evidence under §1, and no stronger than the weakest
> claim in it.**

Every proposal below was written after a real, reproducible investigation — a run's output read
line by line, not an aggregate number trusted at face value. Where a heuristic or a plausible-
sounding mechanism was checked against real data and *didn't* hold up, the honest move was to
narrow the proposal or retract the claim, not to keep it because it was already written. (A live
example: a proposal built on "conflicts concentrate where a cited id is a *structural neighbor*
of the test's real subject" looked well-supported by a first pass — 73 of 153 real conflicts
matched — until reading three of the matches by hand showed the "neighbor" relationship was
coincidental in a densely-connected graph, not causal. The proposal that survived contact with
the examples was a different, better-supported one. Read the examples before trusting the
metric.)

## Before writing: gather the evidence

1. **A real, reproducible artifact** — a build report, a review report, a conformance run's
   JSON/Markdown output, a cross-check between two independent tools, a benchmark. Not a
   hypothesis about what *might* go wrong; something that already did, with a file and a line
   or a command that reproduces it.
2. **At least a few examples read in full**, not just an aggregate rate. If the evidence is "N%
   of edges show pattern P", open several of the actual edges and confirm P is what's really
   happening — the aggregate can be inflated by a handful of outliers (a hub id with many
   structural neighbors, a single misconfigured run) that a full read exposes and a percentage
   hides. Read outliers *and* ordinary cases; an all-outlier sample proves nothing about the
   general case.
3. **The current state of the spec and any competing proposals.** Read the ids the change would
   touch (`C-nn` contracts, the relevant `I`/`K`/`E` rows) as they stand today, and check every
   *other* `PROPOSAL_*.md` file in the repository for draft ids that might collide — a pending,
   unconfirmed proposal's draft numbers are real reservations even though they are not yet in
   `SPEC.md`. Get the true maximum per family from the spec itself (parse it; do not grep bold
   cells, which also match ids inside fenced examples) and from every pending proposal's own
   draft rows; number past both. If two pending proposals could plausibly land in either order,
   say so in the `Status` line (see the template) rather than silently picking one first.
4. **Whether the fix is really new**, or is the *same* failure mode a past proposal already
   named. If it looks like something a past `PROPOSAL_v*.md` or its evidence section already
   solved, say precisely why this is a different mechanism (cite the past proposal by name and
   the mechanism it fixed) rather than assuming the reader remembers, or silently re-fixing the
   same thing twice.

## The template

Every proposal in this house style has the same six sections, in this order, every time —
whether it changes `SPEC.md` or only adds a tool beside it.

```markdown
# Proposal — v<X.Y>: <short, specific description of the change>

> - **Status:** proposal, <date>; for `spec-writing` to turn into `SPEC.md` v<X.Y> rows after
>   the requester settles D-<nn>[, D-<nn>...] below. <If a numbering conflict with another
>   pending proposal is possible, say which one and how it will be resolved.>
> - **Applies to:** `SPEC.md` v<current> — <the ids this touches: C-nn contracts, R/I/K/E rows,
>   fixtures>. <If independent of another pending proposal, say so and why neither needs the
>   other; if it depends on one, name the dependency.>
> - **Notation:** <unprefixed ids are this project's own; a foreign id from another project is
>   `project:ID` in inline code, per the house convention.>
> - **Evidence:** <the exact artifact this is grounded in — a report file and section, a real
>   command's output, measured figures (not rounded away — "153/613 (25%)", not "about a
>   quarter"). This is the line a skeptical reader checks first.>

## 1. The problem

<What went wrong or what's missing, stated from the evidence, not from theory. Cite the exact
numbers and at least one concrete example read in full — a real statement, a real test, a real
verdict — not a hypothetical one. If a plausible-sounding mechanism turned out NOT to explain
the evidence on closer reading, say so here rather than quietly dropping it; that negative
result is itself useful to a future reader.>

## 2. The change

<One or more labeled parts (Part A, Part B, ...) — each a self-contained piece of the fix, cheap
parts first, so a reader can accept some and reject others independently. Use a `mermaid`
diagram when the parts feed into each other in a way prose alone would need several sentences
to trace (see the diagram rules below). End with:>

Proposed rows, drafted for `spec-writing`:

| Family | Draft |
| --- | --- |
| R-<nn> | <full normative text, in the spec's own MUST/SHALL language, exactly as it would
  read in `SPEC.md` — not a paraphrase a later author still has to write. End with "Source: §1."
  or a cross-reference to the evidence it comes from.> |
| C-<nn> | <a contract row, pinning the shape precisely> |
| ... | (one row per new/changed R, C, I, K, E, T id; use fresh numbers — see "ID numbering") |

## 3. What it costs

<Bulleted: new dependencies (ideally none), schema/golden-fixture churn, token/latency cost for
any model-facing change, and — critically — what is NOT guaranteed. If a part depends on a
model honoring an instruction rather than a mechanical check, say plainly that this is not
guaranteed and name the test that will tell you whether it worked (see T-nn discipline below).
Say which parts are worth doing even if others are rejected.>

## 4. Alternatives considered

| Alternative | Why not |
| --- | --- |
| <a stronger/weaker/differently-shaped version of the same fix> | <the concrete reason it was
  not chosen — a real cost, a case it doesn't cover, evidence it wouldn't have caught the actual
  examples in §1. Include the alternative of extending a DIFFERENT pending proposal instead of
  writing a new mechanism, if one exists, and say precisely why it wouldn't carry the needed
  signal (an empty field on the exact edges this proposal targets, not a vague "it's different").>

## 5. Decision(s) for the requester (D-<nn>[, D-<nn>...], <all> `confirm`)

| ID | Statement |
| -- | --------- |
| **D-<nn>** | <option A — the one you recommend> (recommended: <the one-clause reason>) versus
  <option B> (<the one-clause reason it's not the default>). |
| **D-<nn>** | <a second, independent decision, if there is one — do not bundle two unrelated
  choices into one ID> |

## 6. What the change does not do

<Explicit boundaries: what stays true no matter which branch of §5 is taken (an invariant it
never touches, a status it never changes), what it deliberately defers to a later proposal, and
what would still be broken or unmeasured even if this whole proposal ships. A proposal that
claims to fix everything it touched is usually overclaiming; say what's left.>
```

### The front-matter fields, precisely

- **Status** — always starts `proposal, <date>`. For a change that bumps `SPEC.md`'s version,
  say so and name every `D-nn` the reader must settle first. For a proposal that changes no spec
  at all (a new tool, a decision gate, a measurement), say **`no SPEC.md version`** explicitly
  and what kind of artifact it is instead (a tool under `tools/`, a report) — do not leave the
  version question implicit.
- **Applies to** — the exact `SPEC.md` version and the ids it touches (existing contracts,
  rows, fixtures). State the relationship to any other pending proposal explicitly:
  independent ("neither needs the other; both could land"), or dependent (name which).
- **Notation** — one line, even when trivial; keeps every proposal's header the same shape.
- **Evidence** — the single most important field. A reader should be able to go from this line
  straight to the artifact and reproduce the numbers. Round nothing away that changes the
  argument (a rate close to a threshold, e.g. "0.4962" not "about half," matters when the whole
  point is which side of 0.50 it lands on).

### ID numbering

Fresh ids only — never reuse or renumber (the house rule every spec in this repository already
follows). Before drafting §2's table:

1. Parse the real `SPEC.md` (with the project's own extractor, not a bold-cell grep, which also
   matches ids inside fenced examples) and take the true max per family.
2. Grep every other `PROPOSAL_*.md` in the repository for ids in the families you're about to
   use, and number past whichever is higher — a pending proposal's draft numbers are real
   reservations. Note in the `Status` line if two pending proposals could collide and how (e.g.
   "renumber whichever lands second").
3. A tool-only proposal (no `SPEC.md` version) still gets fresh ids if it adds any R/C/I/K/E/T
   rows to the *tool's own* spec (rare) — otherwise it has none, and §2's table is omitted or
   replaced by a description of the tool's own interface.

### Decisions for the requester: the table format

Use a two-column table — `ID | Statement` — one row per decision, **not** the six-column
decision table `spec-writing` uses for already-confirmed defaults in a spec's own §12 (that
table has Default/Alternatives/Affects/Owner columns because it records a settled choice with
its consequences traced; a proposal's decision is not settled yet, so it needs only the id and
the choice itself). Pack each option, its one-line reason, and which one you recommend into a
single cell:

```markdown
| ID | Statement |
| -- | --------- |
| **D-26** | advisory only (Part B as written) (recommended: preserves the model's judgment for
  the real, undocumented-but-correct cases; T-87 measures whether it's enough) versus hard
  coercion (stronger and fully deterministic, but risks false downgrades on tests that don't
  follow the convention perfectly). |
```

Always recommend one side and say why in the same breath as stating it — a decision table with
no recommendation is asking the requester to do the analysis you already did. Never bundle two
independent choices under one `D-nn`; a requester should be able to confirm one and reject the
other without your table forcing them together.

### Diagrams

A `mermaid flowchart` earns its place in §2 when a part's inputs feed into more than one
consumer, or several parts compose into a pipeline a reader would otherwise have to trace across
paragraphs — not for a single linear A-then-B step prose already states in one sentence. Label
nodes with the spec's own vocabulary (field names, contract ids) so a reader can grep from the
picture to the row that backs it, and caption the figure naming which parts it depicts. Quote any
label containing punctuation.

### Test-row discipline for a judge- or model-facing change

If any part depends on a model *doing something differently*, not just a kernel computing a new
fact, add a `*(recorded)*` test that measures whether it worked — re-running the exact edges or
examples named in §1 under the changed behavior and recording the real outcome, not asserting
that it must have worked. State plainly in §3 that this is not guaranteed, and in §6 what to do
if the measurement comes back negative (usually: revisit the harder-but-deterministic alternative
named in §4, if one exists).

## Naming and filing

- **A change that bumps the tool's own `SPEC.md`:** `PROPOSAL_v<X.Y>_<short-slug>.md` at the
  repository root, `<X.Y>` the version it would become. `<short-slug>` names the mechanism, not
  the symptom (`clause_grounding`, not `judge_wrong_sometimes`).
- **A change that adds no spec version** (a new tool, a decision gate, a measurement): 
  `PROPOSAL_<short-slug>.md`, no version segment, and the `Status` line says so explicitly.
- Commit a proposal alongside its implementation, once one exists — not as a standalone
  speculative document the moment it's drafted. An unimplemented proposal is a live idea to
  revisit, not yet a change; leave it untracked (or in a scratch location) until either it is
  built or the requester confirms its decisions and hands it to `spec-writing`.

## After the requester decides

- Every `D-nn` confirmed or rejected → `spec-writing` turns the confirmed rows into real
  `SPEC.md` rows (bumping the version, adding a revision-history line citing this proposal by
  name), then `spec-build` implements them test-first, same as any other spec change.
- A decision rejected outright → say so in the commit that lands whatever *did* get confirmed,
  and leave the proposal file as the record of what was considered and declined, and why.
- A `*(recorded)*` measurement (§2's test-row discipline) comes back negative → do not quietly
  ship the advisory-only version anyway; revisit `§4`'s harder alternative or write a follow-up
  proposal, the same way `PROPOSAL_v1.9_clause_grounding.md` names what its own `§6` left open
  for the next one.

## Pre-publish checklist

- [ ] §1's evidence is a real, reproducible artifact with exact figures, plus at least one
      example read in full — not an aggregate trusted without opening a single real case
- [ ] Every plausible mechanism considered was checked against real examples before being kept;
      one that didn't survive the check is either dropped or explicitly named as rejected, not
      left in as if it were still live evidence
- [ ] §2's draft rows are ready for `spec-writing` to copy, in normative MUST/SHALL language —
      not a description of what a future row should eventually say
- [ ] Every new id is fresher than both the real `SPEC.md`'s current max *and* every other
      pending proposal's draft ids in the same family
- [ ] §5 uses the two-column `ID | Statement` table, one decision per row, each with a stated
      recommendation
- [ ] §3 states plainly which parts are guaranteed (deterministic) and which are not (depend on
      a model's compliance), and names the measurement that tells you which
- [ ] §6 states what stays true regardless of which decision branch is taken, and what is
      deliberately left unfixed
- [ ] The `Status`/`Applies to` lines name every other pending proposal this one depends on or
      could collide with
- [ ] The file is named and filed per "Naming and filing," and left uncommitted until it is
      either implemented or its decisions are confirmed

> **A proposal is done when a requester can read six sections, confirm a table of choices, and
> hand the result to `spec-writing` without re-deriving the argument — and when every claim in it
> would survive someone else opening the actual evidence and checking.**
