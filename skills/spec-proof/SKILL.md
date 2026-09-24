---
name: spec-proof
description: Create the formal (Lean 4) half of the conformance evidence for a built system — a self-contained lake project in the project's `proof/` directory (`lean-toolchain`, `lakefile.toml`, `lake-manifest.json`, `README.md`) that transcribes the spec's deterministically-provable contract into a Lean model and proves it kernel-checked for all inputs, while mapping every unprovable row to the empirical test that carries it. Phases are read the spec and classify every ID as proven / structural / deferred (the scope map), scaffold the well-formed project, write the three files (Spec / Model / Theorems) one build per file, then audit (`lake build` 0 warnings, every ID tagged exactly once, statement-by-statement re-read of the spec) and commit. Use when asked to "prove the spec", "add a formal proof", or "build the Lean half" of a project that already has a SPEC.md and a green acceptance suite.
license: MIT
---

# spec-proof

Create the **formal half** of a system's conformance evidence. `spec-build`'s test suite shows
the system behaves on a *sample* of runs; a Lean proof shows its *module-level* contract holds
for *all inputs* — every equality a kernel checks, every invariant quantified over every seam
outcome, re-runnable in seconds with no runtime. This skill produces that half, in a fixed
format, as a well-formed Lean project living in the project's `proof/` directory.

The spec is the **source of truth**; the proof must satisfy it. `lake build` is the grader:
it kernel-checks every proof, and a green build with zero warnings is the gate.

## The trust boundary (state this first, in every exchange)

Lean proves the **model** — a pure Lean function — never the system's file. The bridge has
three legs, and this skill builds only the middle one:

| Leg | Claims | Evidence |
| --- | --- | --- |
| 1. Transcription | the model is a faithful transcription of the source file | **manual** — the correspondence table in `Model.lean`; bridged empirically, not formally |
| 2. **Lean (this skill)** | the model satisfies the spec's module-level contract for all inputs | `lake build` — kernel-checked theorems, all inputs |
| 3. Empirical | the *file* satisfies the process-level contract | the spec's acceptance suite (real fds, signals, timing, the interpreter) |

Overclaiming leg 2 as leg 1 or leg 3 is the one sin of proof work. The proof's README says,
in its first screen: what Lean certifies, what it does not, and which tests carry the rest.

## When to use

- "prove the spec" / "add a formal proof" / "build the Lean half" / "prove `<SPEC.md>`" for a
  project that **already has** the implementation and a green acceptance suite
- after `spec-build` returned `CONFORMING` and the user wants machine-checked evidence for the
  deterministic core
- a spec whose contract is a table over a finite input space (byte contracts, exit-code maps,
  state machines, "for all inputs, …" invariants)

Do **not** run it when:

- the spec has no `SPEC.md` (no source of truth for the constants — route through
  `spec-writing` first)
- the system's core is purely probabilistic or network-bound (there is no deterministic half
  to prove; say so and stop — a proof of a stub is theater)
- the user asks to "prove the program is correct, full stop": set the trust-boundary table
  above in the first exchange. The deliverable is leg 2, and the README says so.

## The output contract — `proof/` in the project being proved

The proofs **reside in the project for which they are built** — not in a sibling repository,
not in a build directory. The output is a self-contained lake project at `<project>/proof/`:

| File | Purpose | Must contain |
| --- | --- | --- |
| `proof/lean-toolchain` | hermeticity | the exact pinned toolchain, one line: `leanprover/lean4:vX.Y.Z` |
| `proof/lakefile.toml` | the build | project name `<system>_proof`, `version = "0.1.0"`, `defaultTargets`, the library target, optional demo exe |
| `proof/lake-manifest.json` | the dependency pin | the minimal manifest, `packages: []` by default |
| `proof/.gitignore` | hygiene | `/.lake` |
| `proof/README.md` | the trust boundary, in prose | what it proves / what it doesn't / scope map / commands (template below) |
| `proof/<Lib>.lean` | root module | one comment line; imports the three concern modules |
| `proof/<Lib>/<System>/Spec.lean` | the **normative side** | the spec's pinned constants + the facts they pin |
| `proof/<Lib>/<System>/Model.lean` | the **transcription** | the source file as a pure function with injected seams |
| `proof/<Lib>/<System>/Theorems.lean` | **the proof** | theorems, each tagged with the spec IDs it discharges |

with `<Lib>` the CamelCase `<System>Proof` (hello → library `HelloProof`, lake project
`hello_proof`, system directory `Hello`). Example, for `hello_world_deepseek`:

```
hello_world_deepseek/
├── SPEC.md  hello.py  tests/ …        ← the project, unchanged
└── proof/
    ├── lakefile.toml   lake-manifest.json   lean-toolchain   .gitignore   README.md
    ├── HelloProof.lean
    └── HelloProof/Hello/{Spec,Model,Theorems}.lean
    (optional: Main.lean + [[lean_exe]] — a demo that prints the proven constants)
```

The four manifest files above are the **well-formedness contract**: a fresh clone of the
project must build `proof/` with nothing but `lake build` — the toolchain file makes lake
install the exact toolchain, the manifest pins the (zero) dependencies. If the proof cannot
build in a clean checkout, it is not well-formed.

**The shape is fixed; the names are not.** If the project's own layout differs (a different
system name, more than one concern), keep the three roles and their order — `Spec` imports
nothing but `Lean`; `Model` imports `Spec`; `Theorems` imports both — and name files after
the spec's own section titles where the spec has more than three concerns (e.g. a protocol
spec may grow `Protocol.lean` between `Spec` and `Theorems`, in dependency order).

## The three files

### `Spec.lean` — the normative side

The constants the spec pins, stated once, plus the spec's own claims about them.

1. **Header doc block** — module name, `=` underline, one paragraph: what this file is, which
   spec (name + version + path) it transcribes, and the file's rule: *every constant quotes
   the spec's normative text; every lemma is a check that the spec's own claims about those
   constants are mutually consistent.*
2. **Constants** — one `def` per pinned value:
   - byte tables as `List UInt8` in the spec's canonical byte order (hex literals:
     `[0x48, 0x65, 0x6C, …]`),
   - their named textual forms as `String`,
   - named numeric constants (exit codes, thresholds the spec pins as values).
   Every constant's `/--` doc comment opens with the spec ID(s) and quotes the pinned text
   (`/-- C-02 — the exact 14-byte success payload on fd 1: 48 65 … 0A -/`).
   Mark every constant that another module's theorems must normalize through with
   `@[grind unfold] public def` (see *Lean gotchas*).
3. **Helpers** the theorems will need (`prefixOf`, `asciiBytes`, …), each documented with its
   purpose and which spec concept it serves.
4. **`section Facts`** — the spec's claims *about the constants*, each its own small theorem
   closed by `decide` / `native_decide` (exactly-N-bytes, pure-ASCII, no-BOM, no-CR, distinct
   codes, the $128\!+\!n$ conventions). Tag each with the spec row that makes the claim.

Imports: `Lean` and sibling modules only. **Zero external packages by default** — the manifest
stays `packages: []`. If a property genuinely requires `mathlib`, that is a decision to
present to the user, not a quiet `lake add`.

### `Model.lean` — the transcription

The source file as a pure Lean function. This file is leg 1 of the trust boundary; its header
is where leg 1 is stated honestly.

1. **Header: the correspondence table** — source line → model element, covering **every line of
   the source file** — including the lines deliberately *not* modeled, with the reason
   (the process-level machinery around the I/O: real fds, signal delivery, the interpreter —
   "not modeled: verified empirically by the spec's integration group").
2. **The API surface** — one element per source-level construct (functions, constants), each a
   `def`/`abbrev` whose doc comment cites the source lines and the spec contract.
3. **The seams** — every external effect the source performs becomes an **injected outcome**:
   an `inductive` with one constructor per spec edge case for that effect
   (`PayloadWrite = success | epipe part | ioError part | interrupted part | absent`). The
   seam must be the *same seam the spec's in-process tests inject* — that is what makes leg 2
   and leg 3 interchangeable at the boundary. Document each constructor with the edge-case ID.
4. **Purity** — the model's entry points are plain functions: no `IO`, no state argument.
   Where the spec pins determinism / environment-invariance, formalize it the way the typing
   does: either the environment is *not a parameter at all*, or it is a parameter the
   function provably ignores (`runE (_e : Env) … := guard …` with a one-line theorem
   `runE e₁ … = runE e₂ … := by rfl`).
5. **Seam validity** — a `Prop`-valued predicate per seam pinning what the spec allows its
   incomplete outputs to be (a single 14-byte write can only leave a *prefix* of the payload:
   `def payloadPinned (p : PayloadWrite) : Prop := …`). Invariant theorems take these as
   hypotheses (`(hp : payloadPinned p)`); the hypotheses are the spec, not the model.

### `Theorems.lean` — the proof

1. **Header** — three parts: *what this proves* (per family: the byte contracts, the API, the
   exit map, the invariants, for all inputs), *what it does not prove* (the process layer,
   the file-level facts — carried by the acceptance suite), *the trust boundary* (point at the
   correspondence table in `Model.lean`).
2. **`section Rows`** — one theorem per row of the spec's behavior table (its §5 outcome
   table): the row's statement, exactly, with the row's inputs quantified universally where
   the spec says "any / one or more / whatever".
3. **`section Invariants`** — the "for all inputs" theorems (exit status in the closed set,
   fd 2 is ever only ∅ or the pinned line, fd 1 is ever only a prefix of the payload,
   environment independence), each taking the seam-validity predicates as hypotheses.
4. **A reachability section where the spec claims exhaustiveness** — "each of the five codes is
   reached" is proved with one witness per code (`refine ⟨?_, …⟩; exact ⟨witness, by grind⟩`).
5. **Closing doc block: the deferral table** — every spec ID *out of Lean's reach*, as a
   table: `| spec ID | content | carried by |` where *carried by* names the acceptance test(s)
   (§9 T-ids) that discharge it. **Every spec ID appears in this file exactly once**: as a
   theorem tag (proven) or in the deferral table (witnessed). No third option.

**The tag discipline** (this is the machine-consumable contract — `speccheck --proof` and
evidence tooling read exactly this shape):

- Each declaration is preceded, **ending at most one line above its head**, by a doc comment
  whose first line opens a **bold span** containing every spec ID the declaration discharges:
  `/-- **R-09, E-03, C-04** (T-07, second half): a `KeyboardInterrupt` … -/`.
- **Bold = discharged** (the machine reads bold spans only); **unbolded = prose** (free to
  mention IDs without claiming them). Cite an ID in bold if and only if the declaration
  discharges it.
- Mixed families in one span are fine (`**E-08, D-17, R-03, R-11**`); decision IDs (`D-nn`)
  may be cited for provenance and are excluded from joins; parenthetical test IDs
  (`(T-05, T-14)`) are informational pointers. `(a)`-style sub-case markers are read by
  consumers with the suffix.
- One theorem may discharge a whole row family; a row may need several theorems (module side +
  a structural variant). The join is per-ID, so both shapes work.

**The closing tactics** (what the reference uses, and what you should reach for):

- equality over the fully-applied model → `rfl` (the kernel's definitional check *is* the proof);
- case-split leaves with free seam variables → `grind` (v4.34's normalizer + decider — see gotchas);
- byte-level facts → `decide` / `native_decide` (14 positions, one tactic);
- hypotheses about a pinned seam → `cases` the seam, `simp only [predicate] at h`, then `grind` / `exact h`.

## Lean gotchas (the ones that bite)

- **`grind` vs `decide`.** `decide` is a raw scan: it refuses a goal with any free variable.
  `grind` is a full normalizer + decider: it reduces `match` through `@[grind unfold]` defs
  even with free seam variables in the goal, then decides the remainder. Row theorems with an
  unused seam (`(u : UsageWrite)` left free) close by `grind`, not `decide`.
- **`match` on constructors, not `if` on reducible predicates.** `List.isEmpty` is
  `implicit_reducible` — an `if argv.isEmpty` does not reduce under `decide`/`whnf` and leaves
  the unreduced branch (and its seam variable) in the goal. Write `match argv with | [] => … | _ :: _ => …`.
- **Cross-module unfolding.** A def in one module unfolds in another's proofs only if it is
  `public` **and** `@[grind unfold]`. Every model entry point and every constant the
  theorems normalize through needs both markers; the theorems module needs nothing special.
- **Namespaces omit the library prefix; imports include it.** File `HelloProof/Hello/Spec.lean`
  is module `HelloProof.Hello.Spec`; it declares `namespace Hello.Spec`; other files write
  `import HelloProof.Hello.Spec` and `open Hello.Spec`. (Then `Spec.c02` and bare `c02` both
  resolve; model functions are written bare via `open Hello.Model`.)
- **Bytes.** Pin byte tables as hex `List UInt8`; prove text-form ↔ byte-list via an
  `asciiBytes` helper + a `native_decide` (and, where the spec claims encoding-independence,
  an induction lemma that the ASCII bytes equal the UTF-8 bytes).
- **No `sorry`, no `admit`, no warnings.** `lake build` *accepts* `sorry` with a warning — the
  gate is exit 0 **and** zero warnings. A statement that will not close is a model defect or a
  spec defect (see the never-weaken rule); it is never a license to hole it.
- **The toolchain file is the pin.** Copy the version the building machine reports
  (`lake --version` → `leanprover/lean4:vX.Y.Z`); never a range, never "latest".

## Phase 1 — Read the spec and the system; write the scope map

1. **Read `SPEC.md` fully** (spec-build Phase 0.1's rule: read it whole, once, before writing;
   rows and formulas are normative, diagrams illustrative). Read the implementation it
   specifies — the model is a transcription *of the file*, so the file's structure (its
   functions, its I/O calls, its constants) is the raw material.
2. **Classify every spec ID** into exactly one of:
   - **proven** — a deterministic relation over finite / decidable data: byte contracts,
     exit/status maps, behavior-table rows, "for all inputs" invariants, reachability,
     constant consistency. These become theorems.
   - **structural** — true by the model's *typing* (purity, no state, determinism). Formalize
     as the typing does (no `IO`, ignored environment parameter) and record it in the header;
     it needs no theorem of its own, but the header must say where it lives.
   - **deferred** — the process layer and the file itself: real fds/pipes, signal delivery,
     timing budgets, interpreter behavior, stdlib-only / line-count / audit facts. These stay
     with the acceptance suite; each **must name the T-nn(s)** that carry it.
3. **Write the scope map** — the skeleton of `Theorems.lean`'s header (proves / does not
   prove) and its closing deferral table — **before any Lean exists**.

**Gate:** every spec ID is in exactly one class; every deferred ID names at least one
acceptance test; the user has seen the classification (present the three lists; a surprise in
the deferral table is a trust failure).

## Phase 2 — Scaffold `proof/` as a well-formed project

Write, in `<project>/proof/`:

```toml
# lakefile.toml
name = "hello_proof"
version = "0.1.0"
defaultTargets = ["HelloProof"]

[[lean_lib]]
name = "HelloProof"
```

```json
# lake-manifest.json
{"version": "1.2.0",
 "packagesDir": ".lake/packages",
 "packages": [],
 "name": "hello_proof",
 "lakeDir": ".lake",
 "fixedToolchain": false}
```

```
# lean-toolchain
leanprover/lean4:v4.34.0
```

```
# .gitignore
/.lake
```

plus the module tree from *The output contract*: `HelloProof.lean` (one comment; `import
HelloProof.Hello.Spec` / `…Model` / `…Theorems`) and the three concern files as **import-only
stubs** (header doc block + `namespace` + `import`s, no content yet). An optional `Main.lean`
demo exe (prints the proven constants, as the reference does) with a matching `[[lean_exe]]`
block. Then the README skeleton (template below).

**Gate:** `cd proof && lake build` exits `0` on the stub tree (lake auto-installs the pinned
toolchain on first run — let it; a fresh-clone build that cannot install is an environment
finding to report, not a workaround to hide).

## Phase 3 — Write the three files, one build per file

In dependency order: **`Spec.lean` → build; `Model.lean` → build; `Theorems.lean` → build.**
Each file lands complete (its whole `section`), then the build runs; do not let two files
accumulate unbuilt — the error loop is per-module and stays local that way.

The order of work *inside* `Theorems.lean` is statement-first:

1. **Write the statement** — translate the spec row verbatim into a theorem signature: the
   row's conditions become universal quantifiers and hypotheses (the seam-validity
   predicates, the nonempty-argument hypothesis), the row's pinned outcome becomes the goal.
2. **Close it** — `rfl` / `grind` / `decide` / the `cases`+`simp` shape above.
3. **If it will not close, stop and ask which side is wrong.** The spec's row is the claim;
   the model is the transcription. Either the model diverges from the source (fix the model —
   leg 1) or the spec states more than the source does (a spec defect — route it, do not
   absorb it). **Never weaken the theorem to fit the model**: a theorem that proves less than
   the row says is a hole wearing a checkmark.

**Gate:** `lake build` exits `0` with **zero warnings** (no `sorry`, no unused-variable
noise); every `section` of `Theorems.lean` is present, including the deferral table.

## Phase 4 — Audit, verify, document, commit

1. **The tag audit (mechanical).** Extract the bold ID spans and diff against the Phase 1 map:
   ```sh
   cd proof && lake build   # the kernel check — 0 errors, 0 warnings
   grep -rhoE '\*\*[^*]+\*\*' HelloProof/ | tr -d '*' | grep -oE '[RCIKE]-[0-9]+' | sort -u
   ```
   Every **proven** ID in the map appears in the tag set; every **deferred** ID appears in the
   deferral table with a real test name; every ID in the tag set is **proven** in the map
   (a tag on a deferred ID is a misclassification). An ID in neither place is a dropped
   requirement.
2. **The statement audit (the half no machine does).** Re-read `SPEC.md` and, for each
   theorem, confirm the Lean statement *is* the spec's row — same quantifiers, same
   hypothesis, same goal. A *stronger* statement is fine (record it in the doc comment); a
   *weaker* one is a defect, fixed in Phase 3, not annotated.
3. **The README is the scope map.** Fill the template below from what the three files
   actually contain — the layout paragraphs, the proven / not-proven lists, the trust
   boundary, the commands. The README describes the proof that exists, not the one that was
   planned.
4. **Hermeticity check.** Wipe `proof/.lake` and rebuild; record the toolchain version lake
   selected and the final build line.
5. **Commit** in the project being proved:
   `feat(<scope>): proof/ — <N> kernel-checked declarations covering <proven IDs>` with the
   deferral summary in the body. (If the proof must live in a sibling repository instead —
   the user's layout, not this skill's default — the same files, same gates, and the
   project's README links it.)
6. **Optional — the five-way join.** If the project runs a `speccheck` gate, wire the formal
   half in beside the test half (the `--proof` / `--proof-results` pair, or the
   `proof_evidence` sidecar) so the conformance report shows, per ID, both evidence kinds.
   The proof project is read, never executed, by that join.

**The README template** (adapt; keep all four parts):

```markdown
# <system> proof

Lean 4 formalization of the **observable contract** of [`<system>`](<path to source>) —
the spec is [`SPEC.md`](<path>) <version>.

## Layout

- `HelloProof/Hello/Spec.lean` — the **spec side**: <the pinned constants and the facts
  they pin; one line per constant family>. Every lemma is kernel-checked.
- `HelloProof/Hello/Model.lean` — the **model**: <a <N>-line Lean transcription of
  `<source>`; the program's <K> write calls are the injected seams `…` — the same seam
  the spec's in-process tests inject>.
- `HelloProof/Hello/Theorems.lean` — **the proof**: <per-row theorems and the invariants
  over all inputs>, plus the map of each out-of-Lean row to the test that carries it.

## Commands

    lake build            # checks every proof
    lake exe <name>       # prints the proven constants   (if the demo exe exists)

## What "proven" means here

Lean proves the **model** — a pure Lean function. It cannot execute or inspect
`<source>`. The bridge is two-way: the model is a line-by-line transcription
(correspondence table in `Model.lean` — the manual trust boundary), and the file
is empirically verified by its <N>-test suite. Lean side: module-level contract,
all inputs. Test side: <the deferred list in one sentence each>.
```

## Done when

All five hold, and the verdict is reported in one block:

1. **Scoped** — the Phase 1 map classifies 100% of spec IDs; the user has seen it.
2. **Built** — `cd proof && lake build` exits `0` with zero warnings, on the full tree,
   after a wiped `.lake` (hermeticity check recorded).
3. **Tagged** — the mechanical audit is clean in both directions (proven ⇔ tagged;
   deferred ⇔ tabled with witnesses).
4. **Honest** — statement audit done; README's proven / not-proven / trust-boundary sections
   match the files' actual contents.
5. **Committed** — one commit in the project being proved, message per Phase 4.5.

```text
Proof: <N> declarations, <M> theorems — lake build: exit 0, 0 warnings (<toolchain>, fresh .lake)
Scope: <P> proven / <S> structural / <D> deferred (each witnessed by <tests>) — every spec ID exactly once
Audit: statement re-read <clean | F-nnn open>; tag audit <clean | mismatches listed>
Trust boundary: leg 2 only — transcription (<table>) and process layer (<suite>) are the empirical legs
```

## Anti-rationalization checklist (stop and correct before "done")

- [ ] `proof/` is **in the project being proved** and is a complete lake project (all four
      manifest files + module tree) — a fresh clone builds it with `lake build` alone
- [ ] The scope map was written **before** any Lean, and the user saw it; every spec ID is in
      exactly one class (proven / structural / deferred)
- [ ] Every deferred ID names the acceptance test(s) that carry it — no "the rest is obvious"
- [ ] The correspondence table covers **every source line**, including the lines deliberately
      not modeled (with the empirical witness for each)
- [ ] Every I/O effect is an injected seam with a constructor per spec edge case, matching the
      seam the spec's in-process tests inject
- [ ] The model is pure: no `IO`, no state argument; determinism is a typing fact (or an
      ignored-parameter theorem), not a promise
- [ ] Every declaration carries its bold ID tag, ending ≤ 1 line above its head; bold means
      discharged, never mentioned
- [ ] **No theorem was weakened to fit the model** — every uncloseable statement was resolved
      as a model fix or a spec defect, recorded in the report
- [ ] `lake build`: exit 0, **zero warnings**, no `sorry` / `admit` anywhere in the tree
- [ ] The zero-dependency manifest held (or the user approved the added package by name)
- [ ] The toolchain file pins the exact version that built it — no range, no "latest"
- [ ] The README's first screen states the trust boundary: what Lean certifies, what it does
      not, which tests carry the rest
- [ ] The build was re-run after wiping `.lake` (hermeticity), with the version recorded
- [ ] Nothing in the project source was edited to make the proof close — the proof reads the
      file; it does not negotiate with it

> **The proof succeeds when `lake build` kernel-checks every theorem in a fresh clone, every
> spec ID appears exactly once (proven and tagged, or deferred with its test witness), and a
> grader who diffs each theorem statement against the spec's rows finds no row where the Lean
> says less than the spec says — and the README, in its first screen, tells the grader exactly
> which leg of the bridge they are standing on.**
