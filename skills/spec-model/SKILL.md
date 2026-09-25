---
name: spec-model
description: Build the formal (Lean 4) model of a SPEC.md when no implementation exists yet — a lake project in `proof_from_spec/` (`lean-toolchain`, `lakefile.toml`, `lake-manifest.json`, `README.md`) that transcribes the spec's normative tables into a pure total Lean function, kernel-checks the spec's *derived* claims for all inputs (exit/status map, byte contracts, diagnostics, invariants, reachability, coverage — that the input space has no silent case), and reifies every under-specified, over-pinned, or unwitnessed case as a kernel-checked `F-nnn` finding in `docs/reviews/SPEC_MODEL_FINDINGS.md`. Phases are classify every ID (proven/structural/deferred/excluded), write scope map and model sketch, scaffold the project, write Spec/Model/Theorems one build each, then audit (`lake build` 0 warnings, anti-tautology re-read, every ID tagged or tabled once), write the findings, and commit. Use when asked to "prove the spec", "model the spec", "formalize SPEC.md", or add the Lean half of a SPEC.md with no implementation.
license: MIT
---

# spec-model

Build the spec's **own** formal model — the Lean project you can write before a single line of the
implementation exists. `spec-proof` proves an *implementation* against its spec, and needs the
implementation to transcribe; this skill proves the *spec*: it turns `SPEC.md`'s normative tables
into a pure, total Lean function, kernel-checks the claims the spec makes about itself, and reports
every place where the spec is silent, over-pinned, or unwitnessed — each as a machine-backed
finding.

Two things make it worth running before the code:

1. **Forcing a spec into a total function finds its holes.** A spec that cannot be rendered as a
   total Lean function is a spec with an unstated case. Prose tolerates the gap; a `match` does not.
2. **It is the interface the implementation proof will refine.** When the code exists, `spec-proof`
   transcribes the *file*; the honest question then is whether that transcription is the one the
   spec implies. `proof_from_spec/` is that reference, kernel-checked.

## The trust boundary (state this first, in every exchange)

Lean proves the **model** — a pure Lean function. It never proves a document, and here there is no
program at all. The bridge has three legs, and this skill builds only the middle one:

| Leg | Claims | Evidence |
| --- | --- | --- |
| A. Transcription | the model is a faithful transcription of the spec's normative tables | **manual** — the correspondence table in `Model.lean`, anchor by anchor; made *checkable* (not proven) by the row theorems |
| B. **Lean (this skill)** | the model satisfies the claims the spec makes about itself — for all inputs | `lake build` — kernel-checked theorems |
| C. Empirical | the *system* the spec describes behaves as specified | **does not exist** — no implementation; the spec's §9 tests are *planned*, not run |

Leg C is the difference from `spec-proof`, and it must be said out loud in the first exchange and in
the README's first screen: **this certifies the spec, not any system.** A green `lake build` here
means the spec is internally consistent, total over the input space it enumerates, and has a
witness plan for everything it does not pin — it does **not** mean anything has been built
correctly. Overclaiming leg B as leg C is the one sin of this skill.

## The tautology rule (this skill's characteristic failure mode)

`spec-proof`'s sin is overclaiming the model as the file. This skill's sin is subtler: **proving a
definition by `rfl` and calling it a proof of the spec.**

```lean
def exitUsage : UInt8 := 2
theorem exitUsageIsTwo : exitUsage = 2 := rfl      -- ✗ evidence about nothing
```

That theorem is true, kernel-checked, and worthless: it re-reads the transcription. A row theorem
of the form `outcome (.usage a b) = some ⟨[], c03, exitUsage⟩` is the *same* object — it is the
transcription, written down a second time.

The rule, enforced at Phase 4:

- **Row theorems are transcription, and their doc comments must say so.** They exist so the
  ID-to-declaration join is complete (every spec row has a declaration the audit can read), not
  because they prove anything.
- **Every other theorem must discharge a spec sentence that is not the definition of the thing it
  is about.** The admissible shapes are: a claim quantified over the whole input space
  ("the *only* permitted stderr output is the C-03 line", "no status outside K-04"), a
  cross-constant relation the spec asserts but does not define, a reachability or coverage claim,
  or a claim about the *input space* itself. These require case analysis over the model — that is
  the work, and it is real.
- Where a theorem is at risk of being a definition re-read, its doc comment says why it is not.

## Prerequisites

`lake` on PATH (elan, the rustup-style manager; `~/.elan` is home for it and the toolchains it
downloads). If it is missing: `./install.sh --lean` in the speccheck checkout, or the official
install, `curl https://elan.lean-lang.org/elan-init.sh -sSf | sh`. A project's `lean-toolchain`
file then pins the exact toolchain lake fetches on first build — the skill does not install or
update the toolchain itself.

## When to use

- "prove the spec" / "model the spec" / "formalize `SPEC.md`" / "build the Lean half" for a project
  that has a `SPEC.md` and **no implementation** (or one so early that transcribing it would pin
  the wrong thing)
- right after `spec-review` returned `READY` / `READY WITH MINOR FIXES` and before `spec-plan`,
  when the spec's contract is a table over a finite input space (byte contracts, exit-code maps,
  state machines, "for all inputs, …" invariants)
- when you want the spec's gaps found mechanically instead of by a third reviewer

Do **not** run it when:

- there is no `SPEC.md` (route through `spec-writing` first)
- the spec is not review-clean — a spec with open P0/P1 findings will produce a model of the
  defects; route to `spec-review` first
- an implementation exists and is green: that is `spec-proof`'s job (it transcribes the file). Run
  this skill first only if you want the spec's own model as the reference that proof refines
- the spec's contract is purely probabilistic, network-bound, or is a UI/visual surface with no
  enumerable input table (there is no total function to write; say so and stop)
- the user asks to "prove the program is correct": there is no program. Set the trust-boundary
  table above in the first exchange and offer `spec-model` + `spec-proof` as the two halves.

## The output contract — `proof_from_spec/` in the project whose spec it is

The proofs **reside in the project whose spec they model** — not in a sibling repository, not in a
build directory. The output is a self-contained lake project at `<project>/proof_from_spec/`:

| File | Purpose | Must contain |
| --- | --- | --- |
| `proof_from_spec/lean-toolchain` | hermeticity | the exact pinned toolchain, one line: `leanprover/lean4:vX.Y.Z` |
| `proof_from_spec/lakefile.toml` | the build | project name `<system>_spec`, `version = "0.1.0"`, `defaultTargets`, the library target |
| `proof_from_spec/lake-manifest.json` | the dependency pin | the minimal manifest, `packages: []` |
| `proof_from_spec/.gitignore` | hygiene | `/.lake` |
| `proof_from_spec/README.md` | the trust boundary, in prose | what it proves / what it does not / the findings / commands (template below) |
| `proof_from_spec/<Lib>.lean` | root module | one comment line; imports the three concern modules |
| `proof_from_spec/<Lib>/<System>/Spec.lean` | the **normative side** | the spec's pinned constants + the facts they pin |
| `proof_from_spec/<Lib>/<System>/Model.lean` | the **transcription** | the spec's tables as a pure total function, plus the correspondence table |
| `proof_from_spec/<Lib>/<System>/Theorems.lean` | **the proof** | the row theorems, the invariants, coverage, reachability, the findings' witnesses, the deferral table |

with `<Lib>` the CamelCase `<System>Spec` (hello → library `HelloSpec`, lake project `hello_spec`,
system directory `Hello`). Example, for `hello`:

```
hello/
├── SPEC.md                            ← the source of truth, unchanged
└── proof_from_spec/
    ├── lakefile.toml   lake-manifest.json   lean-toolchain   .gitignore   README.md
    ├── HelloSpec.lean
    └── HelloSpec/Hello/{Spec,Model,Theorems}.lean
```

plus, beside the spec: `docs/reviews/SPEC_MODEL_FINDINGS.md` — the findings (below).

The four manifest files are the **well-formedness contract**: a fresh clone must build
`proof_from_spec/` with nothing but `lake build`. If it cannot, it is not well-formed.

**The shape is fixed; the names are not.** Keep the three roles and their order — `Spec` imports
nothing but `Lean`; `Model` imports `Spec`; `Theorems` imports both — and name files after the
spec's own section titles where the spec has more than three concerns (a protocol spec may grow
`Protocol.lean` between `Spec` and `Theorems`).

**Namespace rule (a deliberate divergence from `spec-proof`).** The namespace is the *full module
path* (`HelloSpec.Hello.Spec`), with no library-prefix dropping. `spec-proof` drops it
(`HelloProof.Hello.Spec` declares `namespace Hello.Spec`) to keep proof terms short; here that
would collide with the implementation proof's own `Hello.Spec` the moment a later `proof/` imports
`proof_from_spec/` as a path dependency. Keep the prefixes.

## The three files

### `Spec.lean` — the normative side

The constants the spec pins, stated once, plus the spec's own claims about them.

1. **Header doc block** — module name, `=` underline, one paragraph: what this file is, which spec
   (name + version + path) it transcribes, and the file's rule: *every constant quotes the spec's
   normative text; every lemma is a check that the spec's own claims about those constants are
   mutually consistent.*
2. **Constants** — one `def` per pinned value:
   - byte tables as `List UInt8` in the spec's canonical byte order (`[0x48, 0x65, …]`),
   - their named textual forms as `String`,
   - named numeric constants (exit codes, thresholds the spec pins as values).
   Every constant's `/--` doc comment opens with the spec ID(s) and quotes the pinned text
   (`/-- C-02 — the exact 14-byte success payload on fd 1: 48 65 … 0A -/`). Mark every constant
   another module's theorems must normalize through with `@[grind unfold] public def`.
3. **Helpers** the theorems will need (`prefixOf` and its `prefixOf_refl`, `asciiBytes`, …), each
   documented with its purpose and which spec concept it serves.
4. **`section Facts`** — the spec's claims *about the constants*, each its own small theorem closed
   by `decide` / `native_decide` (exactly-N-bytes, pure-ASCII, no-BOM, no-CR, distinct codes, the
   $128\!+\!n$ conventions). Tag each with the spec row that makes the claim.

Imports: `Lean` and sibling modules only. **Zero external packages by default** — the manifest
stays `packages: []`. If a property genuinely requires `mathlib`, that is a decision to present to
the user, not a quiet `lake add`.

### `Model.lean` — the transcription

The spec's tables as a pure, total function. This file is leg A of the trust boundary; its header
is where leg A is stated honestly.

1. **Header: the correspondence table** — spec anchor → model element, covering **every normative
   table, section and edge-case list of the spec** — including the parts deliberately *not*
   modeled, with the reason (the module API, the source/version/line-count constraints, the
   process-level machinery — "not modeled: nothing in §5.2/§8's input space reaches them"). The
   anchor column is a `§`-section, a `C-nn`/`K-nn` row, or an `E-nn` case — never a source line.
2. **The input space** — an `inductive Input` with **one constructor per row of the spec's
   behavior table**, plus one per edge case the spec enumerates outside that table. The fields
   carry each row's *variable* content (the argument list, the bytes a failed write left behind).
   A row the spec states for "any/whatever" inputs gets a constructor with those inputs as fields,
   not a family of constructors.
3. **The outcome** — a `structure Result` (the observable cells: descriptors, status) and
   `def outcome : Input → Option Result`. **`none` means "the spec states no outcome for this
   input"** — the representation of a silent case. This is the device that makes the never-hole
   rule satisfiable: a gap is a `none` to be *found* (and proved present) rather than an outcome
   to be invented. Never invent an outcome to make the type total.
4. **The pins** — a `Prop`-valued predicate per "partial or none"-style cell pinning what the spec
   permits an incomplete output to be (`def inputPinned : Input → Prop`). Invariant theorems take
   these as hypotheses: **the hypotheses are the spec, not the model.** Where the spec's pin is
   narrower than the mechanism admits, carry *both* (the spec's pin and the structural one) and
   witness the difference — that is finding class G-2.
5. **Purity** — the model's entry points are plain functions: no `IO`, no state argument. Where the
   spec pins determinism / environment-invariance, formalize it the way the typing does: either the
   environment is *not a parameter at all*, or it is a parameter the function provably ignores
   (`def runE (_e : Env) (i : Input) : Option Result := outcome i` with a one-line theorem
   `runE e₁ i = runE e₂ i := by rfl`).

### `Theorems.lean` — the proof

1. **Header** — three parts: *what this proves* (per family: coverage, the byte contracts, the exit
   map, the diagnostics contract, the invariants, reachability), *what it does not prove* (there is
   no program; the §9 suite is planned), *the trust boundary* (point at the correspondence table in
   `Model.lean`), and the **tautology rule** (state it: which section is transcription, which is
   evidence).
2. **`section Rows`** — one theorem per row of the spec's behavior table: the row's statement,
   exactly, with the row's inputs quantified universally where the spec says "any / one or more /
   whatever". These are transcription; say so.
3. **`section Invariants`** — the "for all inputs" theorems, each taking the pin predicates as
   hypotheses:
   - **coverage** — `noSilence : ∀ i, (outcome i).isSome`: every input the spec enumerates has a
     stated outcome. This is the model's totality and the theorem a G-1 finding falsifies.
   - the closed exit set, the diagnostics contract (fd 2 is ever only ∅ or the pinned line), the
     fd-1 contract (empty or a prefix of the payload), environment independence.
4. **A reachability section where the spec claims exhaustiveness** — "each of the five codes is
   reached" is proved with one witness per code.
5. **`section Findings`** — the witnesses for the spec-precision gaps (G-2 below): the pair
   (spec pin ⇒ structural pin, plus a witness separating them), or the row theorem that exhibits
   the combination the spec's table does not admit.
6. **Closing doc block: the deferral table** — every spec ID *out of Lean's reach*, as a table:
   `| spec ID | content | carried by |` where *carried by* names the spec's own §9 test IDs, marked
   **(planned)** — no implementation exists, so this table is the spec's witness plan, not a
   result. Then a second small table, **excluded by the spec**: the cases the spec puts out of scope
   *by name* (an interpreter abort before any program code runs, signals whose default disposition
   terminates, a line discipline's translation) — a deliberate boundary, not a missing witness, and
   never silently folded into the deferral table.

**Every spec ID appears in this file exactly once**: as a theorem tag (proven, or structural —
where a one-line theorem states the typing fact, tag it; a structural fact with no statement at all
goes in the header's structural list), in the deferral table, or in the excluded table. No fourth
option. A requirement with both halves appears *twice* — as a tag and as a `(process side)` deferral
row; that dual state is the normal shape, not a conflict.

**The tag discipline** (the machine-consumable contract — the same shape `spec-proof` and evidence
tooling read):

- Each declaration is preceded, **ending at most one line above its head**, by a doc comment whose
  first line opens a **bold span** containing every spec ID the declaration discharges:
  `/-- **R-09, E-03, C-04** (T-20): a `KeyboardInterrupt` … -/`.
- **Bold = discharged**; **unbolded = prose** (free to mention IDs without claiming them). Cite an
  ID in bold if and only if the declaration discharges it.
- Mixed families in one span are fine (`**E-08, D-17, R-03, R-11**`); decision IDs (`D-nn`) may be
  cited for provenance and are excluded from joins; parenthetical test IDs (`(T-05, T-14)`) are
  informational pointers. `(a)`-style sub-case markers are read by consumers with the suffix.

**The closing tactics** (what the reference uses):

- equality over the fully-applied model → `rfl` (the kernel's definitional check *is* the proof);
- closed propositions after a `cases` split → `decide` / `native_decide`;
- case-split leaves with free variables → `grind`, or reduce the goal with `simp [<the constants>]`
  first (see gotchas).

## The findings — `docs/reviews/SPEC_MODEL_FINDINGS.md`

The distinctive output. A finding is a place where the spec is *incomplete or imprecise* — found by
the act of modeling, and backed by a kernel-checked witness. Number them `F-nnn` continuing the
spec's existing review numbering, and give each: the class, the severity on `spec-review`'s scale
(P0/P1/P2), the spec anchor (section + ID), the witness (the theorem name), the argument, and a
proposed resolution. **Do not fix the spec** — this skill reports; `spec-proposal` /
`spec-writing` decide.

| Class | What it is | Lean witness |
| --- | --- | --- |
| **G-1 · silent case** | the spec enumerates an input and states no outcome for it — `outcome` returns `none` | `∃ i, outcome i = none` (kernel-checked) — the negation of `noSilence` |
| **G-2 · over-strong or under-stated pin** | the spec pins an outcome narrower than the mechanism admits (or its table cell admits less than another section of the same spec does) | the pin pair + a separating witness: `(∀ p, pinned p → structural p) ∧ ∃ p, structural p ∧ ¬ pinned p`; or the row theorem exhibiting the combination the table does not admit |
| **G-3 · unwitnessed** | the row is out of Lean's reach and the spec names **no §9 test** that carries it | none — the finding is the absence of a T-id in the deferral table; the machine-checkable part is the audit's ID join |

G-3a (a requirement with no proof and no planned test) is a **defect** — unverifiable by
construction. G-3 with a T-id is the normal deferred state. An `Excluded` row (the spec's own
out-of-scope list) is neither: it is a stated boundary, and it must not be used to hide a G-3a.

A spec that produces zero findings is a fine result — report it as such (`noSilence` closed, no
G-1; the pins are as strong as the mechanism). A spec that produces a finding is *not* a failure of
the run: the finding is the deliverable.

## Lean gotchas (the ones that bite)

- **`decide` refuses *any* free variable**, including ones that cannot affect the goal. A leaf like
  `{ fd1 := part, fd2 := [], exit := exitEpipe }.exit ∈ k04` is closed by `simp [k04]` — `decide`
  errors with *"Expected type must not contain free variables"*. Reduce the projection and the
  membership to a closed proposition first.
- **`decide` does not unfold a `def`-defined `Prop`** for instance search: `¬ usageKiPinned [0x75]`
  fails to synthesize `Decidable` until you `simp only [usageKiPinned]`. Give the witness as
  `by simp [usageKiPinned]`.
- **`grind` vs `decide`.** `decide` is a raw scan; `grind` is a full normalizer + decider and
  reduces `match` through `@[grind unfold]` defs even with free variables in the goal.
- **`match` on constructors, not `if` on reducible predicates.** `List.isEmpty` is
  `implicit_reducible`; write `match argv with | [] => … | _ :: _ => …` — a constructor match
  reduces under `whnf`, an `if` on `isEmpty` may not.
- **Turning `h : outcome i = some r` into `r`'s value.** `simp only [outcome, Option.some.injEq] at h`
  leaves `h : ⟨…⟩ = r`; `rw [← h]` then rewrites `r` in the goal to the literal. (`subst h` also
  works where the literal side is the left one.)
- **Cross-module unfolding.** A def in one module unfolds in another's proofs only if it is
  `public` **and** `@[grind unfold]`. Every model entry point and every constant the theorems
  normalize through needs both markers.
- **Bytes.** Pin byte tables as hex `List UInt8`; prove text-form ↔ byte-list via an `asciiBytes`
  helper + a `native_decide` (and, where the spec claims encoding-independence, an induction lemma
  that the ASCII bytes equal the UTF-8 bytes).
- **Derive `DecidableEq`** on every `Input`/`Result`-like type the theorems `decide` over; a
  `structure`/`inductive` without it makes the leaf undecidable and the error points at the
  instance, not at the omission.
- **No `sorry`, no `admit`, no warnings.** `lake build` *accepts* `sorry` with a warning — the gate
  is exit 0 **and** zero warnings. A statement that will not close is a model defect or a spec
  defect (G-1/G-2), never a license to hole it.
- **The toolchain file is the pin.** Copy the version the building machine reports
  (`lake --version` → `leanprover/lean4:vX.Y.Z`); never a range, never "latest".

## Phase 0 — Read the spec; refuse or classify

1. **Read `SPEC.md` fully** (one pass, before writing anything; the tables and formulas are
   normative, the diagrams are illustrative). Note every table, every `E-nn` list, every
   "for all inputs" sentence, and every "out of scope" clause.
2. **Refuse, out loud, if** there is no `SPEC.md`, the spec is not review-clean, or the contract is
   purely probabilistic / network-bound / visual with no enumerable input table.
3. **Classify every spec ID** into exactly one of:
   - **proven** — a deterministic relation over the spec's finite/enumerable input space: behavior
     rows, exit/status maps, "for all inputs" invariants, reachability, coverage, constant
     consistency. These become theorems.
   - **structural** — true by the model's *typing* (purity, no state, determinism, environment
     independence). Formalize as the typing does and record it in the header; where a one-line
     theorem states the typing fact (an ignored environment parameter), tag it like any other —
     a tag keeps the audit's join mechanical.
   - **deferred** — out of Lean's reach: the process layer, the interpreter, the file itself,
     timing budgets, version/library constraints. Each **must name the §9 T-nn(s)** that carry it
     (marked *planned*); none → a **G-3a finding**.
   - **excluded** — the spec puts it out of scope by name. Recorded in the second table; needs no
     test and must not be used to hide a G-3a.

**Gate:** every ID is in exactly one class; every deferred ID names a test; the user has seen the
classification.

## Phase 1 — Write the scope map and the model sketch

Before any Lean exists, write down:

- the **scope map** — the skeleton of `Theorems.lean`'s header (proves / does not prove) and its
  two closing tables;
- the **model sketch** — the `Input` constructors (one line per spec row), the `Result` cells, and
  the rows whose outcome the spec does not state (each candidate G-1) or pins more strongly than
  the mechanism allows (each candidate G-2).

**Gate:** every spec row and every `E-nn` has an `Input` constructor; every `Result` cell traces to
a spec column; the G-1/G-2 candidates are listed. Present it to the user — a surprise in the
finding list is a trust failure.

## Phase 2 — Scaffold `proof_from_spec/` as a well-formed project

Write the four manifest files, the root module, and the three concern files as **import-only stubs**
(header doc block + `namespace` + `import`s, no content). Then the README skeleton (template below).

**Gate:** `cd proof_from_spec && lake build` exits `0` on the stub tree (lake auto-installs the
pinned toolchain on first run — let it; a fresh-clone build that cannot install is an environment
finding to report, not a workaround to hide).

## Phase 3 — Write the three files, one build per file

In dependency order: **`Spec.lean` → build; `Model.lean` → build; `Theorems.lean` → build.** Each
file lands complete (its whole `section`), then the build runs; the error loop stays per-module
that way.

The order of work *inside* `Theorems.lean` is statement-first:

1. **Write the statement** — translate the spec's sentence verbatim: its conditions become
   quantifiers and hypotheses (the pin predicates), its claim becomes the goal.
2. **Close it** — `rfl` / `grind` / `decide` / the `cases`+`simp` shape above.
3. **If it will not close, decide which of three things it is, and stop and ask if it is not
   obvious.** (a) The model diverges from the spec's table — fix the model (leg A). (b) The spec
   states no outcome for this input — that is a **G-1 finding**: return `none`, prove
   `∃ i, outcome i = none`, and report. (c) The spec's pin is stronger than the mechanism — that is
   a **G-2 finding**: carry both predicates and witness the separation. **Never weaken the theorem
   to fit the model**, and never invent an outcome to make the type total: a theorem that proves
   less than the spec says is a hole wearing a checkmark.

**Gate:** `lake build` exits `0` with **zero warnings**; every `section` of `Theorems.lean` is
present, including both closing tables.

## Phase 4 — Audit, find, document, commit

1. **The tag audit (mechanical).**
   ```sh
   cd proof_from_spec && lake build   # the kernel check — 0 errors, 0 warnings
   grep -rhoE '\*\*[^*]+\*\*' <Lib>/ | tr -d '*' | grep -oE '[RCIKE]-[0-9]+' | sort -u
   ```
   Every **proven** ID in the map appears in the tag set; every **deferred** ID appears in the
   deferral table with a real T-id; every **excluded** ID is in the second table; every ID in the
   tag set is **proven** in the map. An ID in none of the three places is a dropped requirement.
2. **The anti-tautology audit.** For every theorem outside `section Rows`, name the spec sentence it
   discharges and confirm that sentence is not the definition of the thing the theorem is about. A
   theorem that fails this is either deleted or moved into `section Rows` with its doc comment
   corrected.
3. **The statement audit (the half no machine does).** Re-read `SPEC.md` and, for each theorem,
   confirm the Lean statement *is* the spec's claim — same quantifiers, same hypotheses, same goal.
   A *stronger* statement is fine (record it); a *weaker* one is a defect, fixed in Phase 3.
4. **Write the findings** — `docs/reviews/SPEC_MODEL_FINDINGS.md` from the G-classes the build
   actually produced (each with its witness theorem name), or the explicit statement that there are
   none.
5. **The README is the scope map.** Fill the template below from what the files actually contain.
6. **Hermeticity check.** Wipe `proof_from_spec/.lake` and rebuild; record the toolchain version
   lake selected and the final build line.
7. **Commit** in the project whose spec it is:
   `feat(spec): proof_from_spec/ — <N> kernel-checked declarations over <proven IDs>; <G> findings`
   with the finding summary in the body.

**The README template** (adapt; keep all four parts):

```markdown
# <system> — spec model

Lean 4 formalization of what [`SPEC.md`](<path>) <version> *says* — its normative tables
as a pure total function, with the spec's own claims about itself kernel-checked.

> **There is no implementation.** This certifies the spec, not a system. The spec's §9
> tests are planned, not run.

## Layout

- `HelloSpec/Hello/Spec.lean` — the **spec side**: <the pinned constants and the facts
  they pin; one line per constant family>. Every lemma is kernel-checked.
- `HelloSpec/Hello/Model.lean` — the **model**: <§5.2's rows as the <N> constructors of
  `Input`, and the observable outcome as `outcome : Input → Option Result`; `none` = the
  spec states no outcome>. The correspondence table (spec anchor → model element) is the
  manual trust boundary.
- `HelloSpec/Hello/Theorems.lean` — **the proof**: <the row theorems, the invariants over
  all inputs, coverage, reachability>, the findings' witnesses, and the map of every
  out-of-Lean row to the §9 test that will carry it.

## Commands

    lake build            # checks every proof

## What "proven" means here

Lean proves the **model**. It cannot read a document, and there is no program to read
either. The bridge is two-way: the model is a row-by-row transcription (correspondence
table in `Model.lean` — manual), and the *spec* is checked for the claims it makes about
itself (coverage, the closed exit set, the diagnostics contract — kernel-checked, all
inputs). Nothing here says anything about any implementation; that is
[`spec-proof`](../proof/)'s half, and this project is the reference it refines.

## Findings

<N> spec-precision gaps, each with a kernel-checked witness — see
[`docs/reviews/SPEC_MODEL_FINDINGS.md`](<path>). <one line each, or "none">
```

## Done when

All five hold, and the verdict is reported in one block:

1. **Scoped** — the Phase 0 map classifies 100% of spec IDs (proven / structural / deferred /
   excluded); the user has seen it.
2. **Built** — `cd proof_from_spec && lake build` exits `0` with zero warnings, on the full tree,
   after a wiped `.lake` (hermeticity check recorded).
3. **Tagged** — the mechanical audit is clean in all three directions (proven ⇔ tagged;
   deferred ⇔ tabled with a T-id; excluded ⇔ in the boundary table).
4. **Honest** — the anti-tautology audit and the statement audit are done; the README's
   proven / not-proven / trust-boundary sections match the files; **leg C is stated as absent in
   the first screen**.
5. **Committed** — one commit, message per Phase 4.7, plus `SPEC_MODEL_FINDINGS.md`.

```text
Model: <N> declarations, <M> theorems — lake build: exit 0, 0 warnings (<toolchain>, fresh .lake)
Scope: <P> proven / <S> structural / <D> deferred (each naming its planned test) / <X> excluded — every spec ID exactly once
Coverage: noSilence <closed | falsified by G-nnn>; <G> findings (<G-1> silent / <G-2> pin / <G-3a> unwitnessed)
Audit: anti-tautology <clean | F-nnn open>; statement re-read <clean | F-nnn open>
Trust boundary: leg B only — leg A is the correspondence table, leg C does not exist (no implementation)
```

## Anti-rationalization checklist (stop and correct before "done")

- [ ] `proof_from_spec/` is **in the project whose spec it is** and is a complete lake project (all
      four manifest files + module tree) — a fresh clone builds it with `lake build` alone
- [ ] The scope map was written **before** any Lean, and the user saw it; every spec ID is in
      exactly one class (proven / structural / deferred / excluded)
- [ ] Every deferred ID names the §9 test that will carry it, marked *planned*; no "the rest is
      obvious"; no requirement is both unwitnessed and untested without being a **G-3a finding**
- [ ] The correspondence table covers **every normative table, section and edge-case list** of the
      spec, including what was deliberately not modeled (with the reason)
- [ ] The input space has **one constructor per spec row**, plus one per enumerated edge case
      outside the table — and no invented input the spec does not enumerate
- [ ] **No outcome was invented to make the type total**: a case the spec does not state is `none`
      and is proved to be so (G-1), never a plausible default
- [ ] The model is pure: no `IO`, no state argument; determinism is a typing fact (or an
      ignored-parameter theorem), not a promise
- [ ] Every declaration carries its bold ID tag, ending ≤ 1 line above its head; bold means
      discharged, never mentioned
- [ ] **Every theorem outside `section Rows` is not a definition re-read** — the anti-tautology
      audit named the spec sentence each one discharges
- [ ] **No theorem was weakened to fit the model** — every uncloseable statement was resolved as a
      model fix, a G-1, or a G-2, recorded in the findings
- [ ] The findings file exists, is numbered in the spec's review sequence, and every finding names
      its witness theorem
- [ ] `lake build`: exit 0, **zero warnings**, no `sorry` / `admit` anywhere in the tree
- [ ] The zero-dependency manifest held (or the user approved the added package by name)
- [ ] The toolchain file pins the exact version that built it — no range, no "latest"
- [ ] The README's first screen states the trust boundary, **including that leg C does not exist**
- [ ] The build was re-run after wiping `.lake` (hermeticity), with the version recorded
- [ ] The spec was not edited to make the proof close — the model reads the spec; it does not
      negotiate with it, and findings are reported, never silently fixed

> **The model succeeds when `lake build` kernel-checks every theorem in a fresh clone, every spec ID
> appears exactly once (proven and tagged, or tabled with its witness — deferred with a planned test,
> or excluded by name), every theorem outside the row section discharges a sentence the spec
> actually makes rather than a definition it just wrote down, and the README's first screen tells the
> reader that what has been certified is the spec — not a program, which does not exist yet.**
