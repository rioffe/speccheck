# Proposal — v1.19: a second spec dialect — prefixed terse-IEEE component specs, auto-detected

> - **Status:** proposal, 2026-09-30; for `spec-writing` to turn into `SPEC.md` v1.19 rows after
>   the requester settles D-43..D-47 below. No numbering conflict: every other proposal in
>   `docs/proposals/` is implemented at or before v1.18, and no unimplemented proposal reserves
>   ids in any family this one uses.
> - **Applies to:** `SPEC.md` v1.18 — C-01 (ID grammar, declaration, citation), C-03 (citation
>   scanning), R-01/R-03/R-04 (extraction and scanning), C-05/R-06 (status, untouched in
>   mechanism but newly applied to terse ids), C-07 (`speccheck.json`, one new field), §5 (CLI,
>   one new flag), and `skills/spec-writing/SKILL.md` (a new authoring section). Independent of
>   every pending proposal; none exist.
> - **Notation:** unprefixed ids are this project's own; a foreign id from another project is
>   `project:ID` in inline code (`ir-control:IR-RX-001`).
> - **Evidence:** `speccheck check --root . --spec SPEC.md --src c/src,c/include --tests c/tests`
>   (speccheck 1.18.0) run in `soundguardian-device/ir-control` at `b82ed2a`, and the extraction
>   measurements below taken with this repository's own `extract.ID_RE` and declaration census
>   over that repository's `SPEC.md` and `c/tests/test_learn.c`. Every figure reproduces from
>   those two files and that command.

## 1. The problem

A second specification format now exists in production and the checker cannot read it — and,
worse, partially misreads it as the house format.

`ir-control` (a SoundGuardian component, `soundguardian-device/ir-control` at `b82ed2a`) is
written in a terse IEEE/RFC-2119 component-spec style: numbered sections (Purpose, Terminology,
Constants, …, Verification, Traceability), SHALL/MUST language declared up front, and stable ids
of the form `IR-RX-001` — a component **prefix** (`IR`), a **multi-letter family** (`RX`
receive, `TX` transmit, `IF` interface, `V` verification, plus `A C D E I K L S`), and a
three-digit number — declared as bold bullet items:

```markdown
- **IR-RX-002 — Glitch rejection:** A capture with fewer than $N_{noise} = 16$ durations SHALL
  be treated as noise and SHALL NOT be admitted or counted as a valid candidate. ...
```

Against that spec the checker fails in three distinct ways, all measured:

1. **Total invisibility of declarations.** The spec declares 90 ids by the bullet convention
   (12 families: A 3, C 7, D 3, E 5, I 5, IF 8, K 10, L 5, RX 12, S 5, TX 7, V 20; 93 unique
   ids referenced overall). C-01 recognizes none of them — bullets are not a declaration form,
   and `RX` is not in `FAMILY`. The `check` command exits with
   `ERROR spec declares no in-scope IDs` and writes no report at all.
2. **Substring mis-extraction.** `ID_RE`'s boundary is `(?<![A-Za-z0-9])`, which a hyphen
   passes, so `IR-C-001` matches as house `C-001`. Over `ir-control/SPEC.md` the regex fires
   108 times; **104/108 (96.3%) are substrings of prefixed ids**, not real house tokens. In
   `c/tests/test_learn.c`, which carries 28 prefixed citations, the extractor records 7 bare
   citations (`K-006` ×2, `E-001` ×2, `K-009`, `C-009`, `I-002`) and is blind to the other 21
   (multi-letter families). Read in full, `test_learn.c:19` is
   `/* Canonical Samsung-32 frame for b0..b3 (IR-K-006, IR-K-009). */` — a citation of
   `ir-control:IR-K-006` that the checker would count as evidence for a house `K-006`, i.e. for
   a different obligation in a different taxonomy. Two components sharing one workspace
   (`IR-C-001`, `EA-C-001`) would collapse into one id.
3. **Same letter, different meaning.** The remaining 4/108 genuine bare tokens (`C-10`, `C-16`,
   `C-17`, `C-22` at `SPEC.md:210`) are *legacy SoundGuardian* ids cited as provenance — foreign
   ids, not this spec's. And the letters themselves diverge: house `E` is an edge case, terse
   `E` is the error model (§6); house `K` is a measurable constraint, terse `K` is a protocol
   constant (§3); terse requirements live in `RX`/`TX`/`S`, not `R`; terse verification rows are
   `V`, not `T`. A unified single-namespace grammar was considered and rejected on exactly this
   evidence (§4).

Three sibling components (`edge-audio`, `event-journal`, `action-authority`) plus this
repository's own `SPEC.md` remain in the house format, so dropping or replacing the house
grammar is not an option: both formats are live, and the requester has confirmed both remain so.

## 2. The change

Cheapest first; each part stands alone.

**Part A — token boundary hardening (both dialects).** A house ID token is no longer recognized
when it is immediately preceded by an uppercase-alphanumeric run and a hyphen (the prefix
shape): `IR-C-001` yields no `C-001` citation anywhere — spec, source, or test scan. This fixes
mis-extraction bug (2) even if every other part is rejected. Mechanically: the token rule gains
a second lookbehind rejecting `[A-Z0-9]-` ahead of the family letter, equivalent to requiring
that a hyphen before the token not be preceded by an uppercase-alphanumeric character.

**Part B — the terse-IEEE grammar.** A second ID grammar:

```text
TERSE-ID  := PREFIX "-" TFAMILY "-" TDIGITS
PREFIX    := [A-Z][A-Z0-9]{0,3}        # the component tag, e.g. IR, EA, MP
TFAMILY   := [A-Z]{1,2}                # open set: RX, TX, IF, V, C, K, E, I, ...
TDIGITS   := [0-9]{1,3}
TOKEN     := TERSE-ID bounded by non-alphanumerics, not preceded by [A-Z0-9]"-"
```

Declaration forms, in a terse-dialect spec only:

- **(d) bullet:** a list item whose first token after the bullet marker is `**TERSE-ID`
  followed by an em-dash and a title ending in `:**` — statement := the whole list item
  (continuation lines included, fenced blocks excluded as in C-01), title := the text between
  the em-dash and the closing `:**`.
- The existing heading (b) and table-row (a) forms, accepting a TERSE-ID where they accept an ID.
- Retirement by strike-through, exactly as in house C-01.
- The plain-cell decision rule C-01 (c) is unchanged and already parses `ir-control`'s
  `| D-01 | … |` decision table as declaration-only decisions.

All declared ids in one spec MUST share one PREFIX — the prefix of the first declaration; a
declaration with a different prefix is an error (D-44).

**Part C — dialect detection and the CLI.** `check`/`impact`/`explain` gain
`--dialect {auto,house,terse}`, default `auto`. Under `auto`, the extractor counts declarations
under each grammar: terse > 0 and house = 0 → terse; terse = 0 → house (today's behavior,
including the empty-spec error); both > 0 → error naming both counts. The chosen dialect is
reported (`speccheck.json` `dialect`, one Markdown-report line).

**Part D — citation and status for terse ids.** In terse mode, citations are full-token only;
a bare house-shaped token in a terse spec or its trees (`C-10` at `ir-control/SPEC.md:210`) is a
foreign reference: never a citation, never dangling, counted once in a Note (D-46). Every terse
id takes the C-05 status algorithm exactly as a house non-T id — steps 1–4, judge eligibility
unchanged, statement = the bullet statement; no family gets T's special-casing in v1.19 (D-45).

**Part E — `spec-writing` skill.** A new authoring section defines the terse dialect
normatively (the grammar above, the bullet form, the single-prefix rule, when to choose it over
the house format), so the next component spec is written to a written grammar, not by imitating
`ir-control`.

Proposed rows, drafted for `spec-writing`:

| Family | Draft |
| --- | --- |
| R-42 | The checker MUST support two spec dialects — `house` (C-01) and `terse` (C-20) — selected per run by `--dialect {auto,house,terse}` (default `auto`) per the detection rule in C-21; the selected dialect MUST be recorded in `speccheck.json` (`dialect`) and stated in the Markdown report. Source: §1. |
| R-43 | In terse dialect, the checker MUST extract every declared TERSE-ID with its family, title, and statement per C-20, and MUST record citations by full TERSE-ID token only; every declared, non-retired terse id receives exactly one status by C-05 steps 1–4, with no family receiving family-T semantics. Source: §1 (1), D-45. |
| R-44 | In both dialects, an ID or TERSE-ID token immediately preceded by an uppercase-alphanumeric character and a hyphen MUST NOT be recognized as a token: `IR-C-001` yields no `C-001` citation and no `R-001` declaration anywhere. Source: §1 (2). |
| C-20 | The terse-IEEE grammar and declaration contract: the `TERSE-ID` grammar block of §2 Part B pinned verbatim; declaration forms (a) table row, (b) heading, (d) bullet — `- **TERSE-ID — Title:** statement`, statement spanning the list item's continuation lines; strike-through retirement; C-01 (c) decisions unchanged; all declarations share the PREFIX of the spec's first declaration (E-64 otherwise). |
| C-21 | Dialect detection: under `--dialect auto`, count declarations under C-01 and C-20 outside fenced blocks; terse>0 ∧ house=0 → terse; terse=0 → house; both>0 → error with both counts (E-62). An explicit `--dialect` value skips detection. `speccheck.json` gains top-level `"dialect": "house"\|"terse"`; `schema_version` `"1.6"`. |
| K-17 | Terse bounds: PREFIX 1–4 chars `[A-Z][A-Z0-9]{0,3}`; TFAMILY 1–2 chars `[A-Z]{1,2}`; TDIGITS 1–3 digits; these are the only lengths recognized. |
| E-62 | A spec declaring ids under both grammars | exit with an error naming both counts; no report is written (mixed documents are undefined in v1.19). |
| E-63 | A bare house-shaped token (`C-10`) in a terse-dialect spec, source, or test tree | not a citation, not dangling, not stale; counted once in a Note ("N foreign house-form tokens ignored"). |
| E-64 | A terse declaration whose PREFIX differs from the spec's first declaration's PREFIX | error naming both prefixes and the line; no report is written. |
| T-99 *(recorded)* | `speccheck check --dialect auto` over `ir-control/SPEC.md` at `b82ed2a` with its `c/` trees declares 90 ids across 12 families, records 0 bare-token citations from prefixed ids, and writes both reports; the recorded run replaces the §1 failure. |
| T-100 | House-dialect regression: the packaged golden fixture and this repository's own `SPEC.md` produce byte-identical reports before and after Part A, proving R-44 changes no existing house extraction. |

## 3. What it costs

- **No new dependencies.** Everything is regex, counting, and plumbing in `extract.py`,
  `cli.py`, `report.py`.
- **Schema churn:** `speccheck.json` gains `dialect`; `schema_version` bumps to `"1.6"`. The
  golden fixture regenerates for the new field (T-100 pins that nothing *else* changes).
- **Part A is a behavior change to house extraction** in the narrow case of a token preceded by
  `[A-Z0-9]-`. Measured against this repository's own spec and fixtures, no such token exists
  today (T-100 proves it); a downstream house spec that deliberately cites `X-R-01` expecting an
  `R-01` citation would lose it — judged correct, since that citation was the bug.
- **Fully deterministic.** No part depends on a model honoring an instruction; the judge's
  contract is untouched (it receives terse statements exactly as it receives house statements).
  T-99 is *(recorded)* because it pins real-world figures, not because any outcome is
  model-dependent.
- **Worth doing independently:** Part A alone kills the false-citation bug; Parts B–D are one
  unit (a grammar without detection or status is inert); Part E can trail by one release.

## 4. Alternatives considered

| Alternative | Why not |
| --- | --- |
| Terse-IEEE only — migrate the house grammar away | Breaks `edge-audio`, `event-journal`, `action-authority`, and this repository's own self-application (252 house ids) for zero gain; the requester confirmed both formats stay live. |
| One unified grammar, both shapes in one namespace | The evidence kills it: `IR-C-001` contains a well-formed `C-001`, and the family letters collide semantically (house `E` edge case vs terse `E` error model, `K` constraint vs constant). Any unified reading either double-counts or silently merges two projects' obligations. |
| `--format` flag only, no auto-detection | Deterministic but operator-dependent; the declaration census already decides the question mechanically from the document itself, and the flag remains as the override. |
| A converter tool (terse → house) beside the checker, grammar untouched | Churns 90 published ids in a component the product already cites (`Intent:` headers in 23 files), and every re-conversion re-risks drift; the checker reading the native format is strictly cheaper. |
| Extending a pending proposal instead | None is pending; every `docs/proposals/PROPOSAL_*.md` is implemented at ≤ v1.18. |

## 5. Decision(s) for the requester (D-43..D-47, all `confirm`)

| ID | Statement |
| -- | --------- |
| **D-43** | `--dialect auto` by declaration census with `house`/`terse` as overrides (recommended: the document itself decides, deterministically, and mixed documents fail loudly per E-62) versus explicit flag only (one more thing every caller must know per spec). |
| **D-44** | One PREFIX per spec, fixed by the first declaration, mismatch is an error (recommended: catches typos like `IRC-` and keeps foreign-id detection trivial) versus any prefix accepted per declaration (tolerant, but a typo silently declares a new component's id). |
| **D-45** | All terse families uniform, no T-equivalent in v1.19 (recommended: `ir-control`'s `V` rows are obligations cited *by* tests, not test declarations; T semantics can follow in a later proposal with its own evidence) versus mapping a designated family (default `V`) to house-T semantics now (more faithful if terse specs later declare test rows, speculative today). |
| **D-46** | Foreign house-form tokens in a terse spec ignored with one Note (recommended: `SPEC.md:210`'s `C-10, C-16` are provenance, and four false danglings would fail `--strict` for a non-defect) versus reported as dangling citations (louder, but wrong about what they are). |
| **D-47** | Part A's boundary rule active in both dialects (recommended: the `test_learn.c:19` mis-citation is a live bug in house mode today, and T-100 proves no existing extraction changes) versus terse-mode only (guarantees house byte-identity by construction, at the price of keeping the known false-citation path). |

## 6. What the change does not do

- **No cross-repository id resolution.** `ir-control:IR-RX-001` cited from another repo's spec
  is out of scope; a terse id is checked only within its own spec/src/tests triple.
- **No mixed-dialect documents.** A spec declaring under both grammars errors (E-62); support,
  if ever wanted, is a later proposal.
- **No prose retirement.** `ir-control`'s "Retired ids: IR-C-003 → IR-C-007" sentence is not
  parsed; terse authors retire by strike-through like everyone else (Part E documents this).
- **Bench ids stay invisible.** `B-01`-style rationale rows fit neither grammar and declare
  nothing, before and after.
- **The judge, the status algorithm, the impact walk, and `explain` are mechanism-unchanged** —
  they gain terse ids as inputs, not new rules; house self-application remains byte-identical
  (T-100).
- **Still unfixed even if this ships:** `ir-control`'s `SPEC.md` has three referenced-but-
  undeclared ids (93 referenced vs 90 declared) that will surface as danglings the moment the
  checker can read it — that is the tool working, and the component owner's fix, not this
  proposal's.
