# Proposal — v1.7: send a contract's body, not only its heading, to the judge

> - **Status:** proposal, 2026-09-17; for `spec-writing` to turn into `SPEC.md` v1.7 rows after the requester settles D-20 below
> - **Applies to:** `SPEC.md` v1.6 — C-01 (b) (heading declarations), C-02 (`SpecId.text`), C-06 (`JudgeRequest.statement`), C-10 (judge instruction text), C-07 (`statement` in `speccheck.json`)
> - **Evidence:** two `--judge llm` runs over the same 130 edges of the MonteCarloPi Swift build (`SPEC_swift.md` v0.1-swift, speccheck 1.6.0): `openai/gpt-4o-mini` → `65/70, 0 weak`; `google/gemini-3.8-flash` → `56/70, 9 weak, 15 UNRELATED, 3 UNKNOWN` (43 s at concurrency 16, 0 malformed replies). The two judges disagree almost entirely on ids declared by `###` headings.

## 1. The problem

C-01 (b) defines the statement of a heading declaration as *the rest of the heading text*:

```text
  (b) heading:      ### C-03 <statement>
        statement := the rest of the heading text, trimmed.
```

That statement is what C-06 sends the judge as `JudgeRequest.statement`, and what C-07 records
as `statement`. For a table row this is the right thing: the row *is* the requirement. For a
contract it is the title of the requirement; the requirement is the fenced code block and the
prose beneath the heading, which the judge never sees.

What the judge received for four contracts of `SPEC_swift.md`, verbatim from `speccheck.json`:

| id | `statement` sent | body under the heading (not sent) |
| --- | --- | --- |
| C-02 | `` `EstimationWorker` (an `actor`) `` | 1,794 bytes: the pinned actor API with behavioural comments — `startRun` returns `false` when a run is live (E-05), `pause`/`resume` no-ops outside their states (E-13), `stop()` joins within K-06, `.unbounded` stream — plus the paragraph that out-of-range parameters throw `invalidRunParameters` on the first tick and surface as `.crashed` |
| C-04 | `Data structures` | the three pinned structs `Progress`, `Checkpoint`, `Summary` with their field comments (nullability of `standardError` / `zScore`, the `checkpoints` cap of 512) |
| C-05 | `` Scatter plot (SwiftUI `Canvas`) `` | 1,885 bytes, six bullets: three about drawing (canvas, arc, two colours) and three about the *model* — the 60 000-point reservoir with preallocated `x/y/isHit/ordinal`, the `seed &+ 1` reservoir seed (E-15), the `generation` repaint counter |
| C-07 | `` `EstimatorViewModel` (`@MainActor @Observable final class`) **[port]** `` | 2,685 bytes: the whole view-model surface — inputs, validation, `can*`, stats, plot models, actions, `displayString` |

A literal judge does the only thing it can with a title. Gemini's rationales, one per edge:

- C-02, all five `WorkerTests` edges, `EXECUTES_ONLY`: *"does not assert that EstimationWorker is an actor"* — while `secondStartRunRejected` asserts `startRun == false`, `invalidParametersCrash` asserts the `.crashed` message, `redundantControlsAreNoOps` asserts `runState` unchanged: three of the body's clauses, verbatim.
- C-05, four edges, `UNRELATED`: *"does not exercise or assert anything regarding the SwiftUI Canvas scatter plot"* — the four tests are `reservoirCapsAndSamplesUniformly`, `reservoirSeedWrapsAtMax`, `scatterBounded`, `shapesAndLimits`: bullets 4–6 of the body, which are the model half of the contract.
- C-04, three edges, `UNKNOWN`: *"the statement 'Data structures' specifies no normative requirement or observable behavior to evaluate"* — a correct refusal; the three `UNKNOWN`s are the whole of that run's `unknown_rate` (0.023).
- C-07, ten edges, `EXECUTES_ONLY`: *"does not assert that the class is @MainActor, @Observable, or final"*.

`gpt-4o-mini` marked every one of those edges `ASSERTS`. It is not that one judge is right and the
other wrong: one guessed generously from a title, the other refused to. Neither had the contract.
The spec's own principle — *every claim points at evidence the operator can grep* — is not met by
a judge that grades a heading.

## 2. The change

For a heading declaration, the statement becomes the heading text **followed by the section
body**: every line after the heading up to (not including) the next line that is a heading of
the same or a higher level (`#`…`###` for a `###` declaration), fenced code blocks **included**
(the pinned shape is the contract), leading and trailing blank lines trimmed, whitespace inside
preserved (a code block's indentation is meaning). Table declarations are unchanged.

Proposed rows, drafted for `spec-writing`:

| Family | Draft |
| --- | --- |
| R-33 | For an ID declared by a heading (C-01 (b)), the checker MUST use the heading text followed by the section body as the ID's statement, so that the judge and the report see the contract's pinned shape, not its title. Source: the Gemini run above. |
| C-01 (b) | `statement := the rest of the heading text, trimmed, then a newline, then the SECTION BODY` … `SECTION BODY := the lines after the heading up to the next heading of level <= the declaring heading's level, or end of file; fenced blocks included; leading/trailing blank lines dropped; the body's own sub-headings (deeper levels) are part of it; capped at K-14 bytes (E-46).` A table row inside the body is still parsed for its own declarations (unchanged); a bold ID in the body is not a declaration of the heading's ID (unchanged, E-31). |
| C-02 | `SpecId.text` carries the full statement; a new `SpecId.title` carries the heading text alone (the report's per-ID table and the summary keep using `title` so C-08's layout does not grow). |
| C-06 / C-10 | `JudgeRequest.statement` is the full statement. The instruction text gains one sentence: *"The statement may contain a code block pinning an interface; a test that asserts any clause of the statement ASSERTS it — a contract with several clauses is not required to be asserted whole by one test."* (This is the rule that makes the C-05 model/drawing split judge correctly.) |
| C-07 | `speccheck.json` gains `"title"` per ID; `"statement"` is the full statement. `schema_version` → `"1.1"`. |
| K-14 | Statement cap: a body longer than 8,192 bytes is truncated at the last line boundary before the cap with a final line `… (statement truncated by speccheck at K-14)`; the report Notes name every truncated ID. (The largest body in `SPEC_swift.md` is C-07 at 2,685 bytes; speccheck's own C-10 instruction text, itself a heading-declared contract, is the case this cap exists for.) |
| E-46 | Body exceeds K-14 → truncated as above, one Note per ID. A heading with an empty body (`### C-04 Data structures` followed immediately by another heading) → statement is the heading text alone, as today. |
| E-47 | A heading declaration whose body contains a *retired* heading of deeper level, or a table with declarations → those declarations are parsed exactly as before; the outer statement includes their text verbatim (the judge sees the sub-rows as context). |
| T-72 | A spec with `### C-01 Widget` + code block + prose + `#### note` + `### C-02 …` yields C-01's statement = heading + body through the `####` sub-section, excluding C-02's heading; a body over K-14 is truncated with the marker and a Note; an empty body gives the heading alone; `SpecId.title` equals the old statement for every ID in `fixtures/target/SPEC.md`. |
| T-73 | Golden: `fixtures/target/golden/speccheck.json` regenerated with `title`; the C-08 Markdown is byte-identical to before for every table-declared ID (only heading-declared rows change, via `title`). |
| T-74 | Judge request wire format (extends T-33): the user message's `statement` for a heading-declared ID is the full statement. |

## 3. What it costs

- **Tokens per edge.** Each judged edge of a heading-declared ID carries its body: for C-07 that
  is ~2.7 kB on each of its ten edges. On the MonteCarloPi tree the eight contracts add roughly
  30 kB across their 40-odd edges — a few cents on `gpt-4o-mini`, nothing measurable in time at
  concurrency 16. On speccheck's own spec (eleven heading contracts, some large) the increase is
  larger; T-49's cost note in the README needs a new number.
- **A schema bump** (`1.0` → `1.1`) and both golden fixtures regenerated for `title`.
- **The mock judge is unaffected** (it looks at the test span, not the statement) — R-16
  determinism holds as before.
- **`--judge none` output changes only in `speccheck.json`'s `statement` field** for
  heading-declared IDs; the Markdown report shows `title`.

## 4. Alternatives considered

| Alternative | Why not |
| --- | --- |
| Leave C-01 (b) alone; tell authors to put the contract in the heading | Headings are titles; a 2 kB heading is not a spec anyone reads. |
| Send only the first fenced block of the body | Loses the prose clauses (C-02's "throws on the first tick" paragraph is prose), and some contracts pin their shape in bullets (C-05). |
| Send the body to the judge but keep `statement` in JSON as the heading | Two notions of "statement" in one tool; the report could not show what the judge saw. `title` + `statement` keeps one. |
| Let the judge fetch context itself (tool use) | Nondeterministic, provider-specific, and against the principle that the deterministic kernel decides what the model sees. |

## 5. Decision for the requester (D-20, `confirm`)

**Include fenced code blocks in the statement** (recommended: the pinned shape is the contract,
and it is what a literal judge needs) — versus prose only (smaller, but C-02 would still be judged
on comments-free prose). Everything else in §2 stands in both branches.

## 6. What the change does not do

It does not make a rendering claim assertable headlessly: after v1.7 a literal judge would still
mark `scatterBounded` as not asserting "the quarter-circle arc is drawn", and it should — that
clause belongs to the observed T-17, and the build report's job is to say so. What changes is that
the same test would be judged `ASSERTS` for the reservoir clauses it does assert, which is the
truth the gate is meant to record.
