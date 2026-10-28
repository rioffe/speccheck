# Proposal — v1.24: say `UNPROVEN` instead of `CONFORMING`, stop and report cut table rows, and name the ids no edge touches

> - **Status:** proposal, 2026-10-27; for `spec-writing` to turn into `SPEC.md` v1.24 rows after
>   the requester settles D-58, D-59 and D-60 below. No other proposal is pending, so the draft ids
>   (R-105, E-77, T-118..T-121, D-58..D-60) collide with nothing.
> - **Applies to:** `SPEC.md` v1.23.1 — §5.1's summary line and its T-44 regex, R-21, C-08's §1
>   verdict line, C-01 (a)'s cell-splitting rule, E-66, C-12's Notes, and the T-46/T-71 goldens.
>   Parts A, B, C and D are independent: any subset can land.
> - **Notation:** unprefixed ids are this project's own; ids in another project's spec are named
>   with that project (`mdv_claude_opus`'s R-24).
> - **Evidence:** three suggestions from a regulated-domain debrief (`letter_from_johnathan.md`,
>   "Suggestions", rows 1, 3 and 6), each reproduced on 2026-10-27 with speccheck 1.23.1:
>   (A) `check --spec SPEC.md --src src --tests tests --out out` on a copy of `fixtures/target/`
>   with no `--results` prints `speccheck: CONFORMING - 0/20 passing (0.0%), … 18 unverified, 1
>   untested, 1 uncited; 1 dangling, 1 stale; judge=none` and exits `0`; (B, C) the declared-row
>   splitter, compared against a CommonMark code-span splitter over 14 specs (this one, its two
>   fixtures, `gpu-quicksort-revisited` and ten `mdv*` specs; 5,869 table rows), differs on 43 rows:
>   R-24, a statement silently cut in half, in all ten `mdv*` specs, with E-66 silent; 32 rows whose
>   closing `|` is absorbed into the statement; and one row that is not a declaration. (D) Of 300 ids in this `SPEC.md`, 51 name no other id
>   but only 1 touches no C-12 edge at all (T-42). Of 128 in `gpu-quicksort-revisited`, 2 do
>   (E-17, T-33). In `mdv_claude_opus` (210 ids), none do.

## 1. The problem

**A. A non-strict run calls an unproven tree `CONFORMING`.** Without `--strict`, §5.4 exits `0`
unless an in-scope id is `FAILING`, and §5.1 ties the summary line's first word to the exit code
(`CONFORMING` on `0`). So a run where nothing is proven reads as a pass:

```text
speccheck: CONFORMING - 0/20 passing (0.0%), 0 failing, 0 skipped, 0 weak, 18 unverified, 1 untested, 1 uncited; 1 dangling, 1 stale; judge=none
```

That is the golden fixture without its results file. Eighteen of its 20 ids are cited but have no
result, and the line still opens with the word a reader looks for. The debrief's team uses
non-strict runs on purpose, "as a trend rather than a gate" during prototyping, so the exit code is
doing what they want. The word is not. The run with no citations at all is already handled: E-19
exits `1`.

**B. The row splitter's idea of a backtick span is not CommonMark's.** C-01 (a) splits a declared
row "on every `|` that is not preceded by `\` and not inside a backtick span". The implementation
(`extract.split_row`) toggles "inside a span" on every single backtick. CommonMark defines a code
span as a run of N backticks closed by the next run of *exactly* N, so the two disagree on any row
holding a run of two or more backticks. Read in full, `mdv_claude_opus/SPEC.md` line 87 is:

> `| **R-24** | ⌘F MUST open an in-document find bar. … when it is a code fence (`` ` ``` ` ``/`~~~`), a `$$` math fence (C-02 rule 3), a GFM table (first line contains `` `|` ``; the second line … consists only of `-`, `:`, `` `|` ``, space), or contains `![` anywhere. Every other matching block MUST be inline-highlighted: … |`

`` ` ``` ` `` holds a run of three backticks inside single ones, and toggling on each backtick
leaves the splitter "outside" when it reaches `` `|` ``. The row splits into four cells. The
statement ends at `(first line contains \``, and the obligation "Every other matching block MUST
be inline-highlighted" drops out of the statement the judge is sent and the JSON reports. The
same row appears in all ten `mdv*` specs. Of the other 33 rows where the two splitters differ,
32 are declarations with the opposite failure: a span left open absorbs the row's closing `|` into
the last cell, so the statement ends with a stray ` |`. That is this repository's own T-05,
`mdv_claude_opus`'s R-09, R-46, T-06 and T-39, and the same rows in the other `mdv*` specs. The
33rd is a row that declares nothing. With CommonMark spans, all 43 rows parse as their authors
meant. The fixtures' 55 rows and `gpu-quicksort-revisited`'s
349 come out identical either way.

**C. A cut that a span rule cannot prevent is still silent.** E-66 (v1.21) Notes a row only when its
statement has an odd number of unescaped `$`, which catches `|` inside inline math and nothing
else. A plain `a | b` in a statement cell, or the R-24 case above, splits the row without a word.
The signal is mechanical: the row now has more cells than its table's header. Over the 14 specs,
11 declared rows had more cells than their header. One was `gpu-quicksort-revisited`'s R-08 (6
cells under a 2-column header), which E-66 already Notes. The other ten were R-24 (4 under 2) in
each `mdv*` spec, which it does not. No declared row had fewer cells, and none had more without being
cut, so the check produced no false positive in this sample.

**D. An id that no edge touches is invisible to `impact` and to every reviewer of the graph.** The
debrief reported "a one-word transition row (just a target state) carried no edges" and asked for
"a lint that flags declared rows with no references at all". v1.21 tried that literally and
withdrew it, because it put a Note on every fixture and which rows it should cover was undecided
(`SPEC_BUILD_REPORT.md` §0m). Measuring the two candidate rules shows why:

| Rule | This `SPEC.md` (300 ids) | `gpu-quicksort-revisited` (128) | `mdv_claude_opus` (210) |
| --- | --- | --- | --- |
| names no other id | 51 (8 R, 1 C, 7 I, 7 K, 26 E, 2 T) | 32 | 33 |
| touches no C-12 edge at all | 1: T-42 | 2: E-17, T-33 | 0 |

The first rule is noise. Read in full, the rows it flags are correct leaf obligations: E-01 "Spec
declares zero IDs", E-03, E-04, E-05 and E-07 are complete as written and have no reason to name
another id. The second rule is rare, and every hit is a real gap. This repository's T-42 is
`… with --verbose, each Note appears once at INFO. (§5.3)`. It cites a section, not an id, so it
verifies nothing that the graph or `impact` can see. `gpu-quicksort-revisited`'s E-17 "Phase-one
child of length 0" is an edge case that no requirement names and no test row verifies.

## 2. The change

**Part A — `UNPROVEN`.** The summary line gets a third first word. On exit `0` without `--strict`,
it reads `UNPROVEN` instead of `CONFORMING` unless R-15's conditions hold: every in-scope id
`PASSING`, and `dangling` and `stale` empty. `CONFORMING` then means what a reader takes it to
mean, under either mode. Nothing else changes: not the exit code, not any status, not the JSON. The
word is computed from `speccheck.json` like the rest of the line, so R-14 still holds.

**Part B — CommonMark backtick spans in C-01 (a).** The splitting rule keeps its meaning ("not
inside a backtick span") and gains a definition of a span: a run of N backticks opens a span that
closes at the next run of exactly N backticks on the line. A run with no matching close is literal
text and protects nothing. This fixes R-24's cut and the 32 stray closing pipes, and changes no row
in either fixture.

**Part C — Note a row with more cells than its header.** E-66's condition widens. A declared row
inside a TABLE (C-01 (c)'s definition: a maximal run of rows whose second row is a separator) with
more cells than that table's header row gets the same Note E-66 already emits. A row matching both
the old `$` test and the new cell-count test gets one Note, not two. Rows outside a TABLE keep only
the `$` test, since they have no header to compare against.

**Part D — one Note naming the ids no edge touches.** After C-12 builds the edges, every declared,
non-retired id that is the `src` or `dst` of no edge is *isolated*. One Note per run names how many
there are and the first three, in C-07 id order. No status, metric, edge or exit code changes.

Proposed rows, drafted for `spec-writing`:

| Family | Draft |
| --- | --- |
| **R-105** | On exit `0` without `--strict`, the summary line's `<STATUS>` (§5.1) MUST be `UNPROVEN` instead of `CONFORMING` whenever R-15's conditions do not hold — some in-scope id is not `PASSING`, or `dangling` or `stale` is non-empty. `CONFORMING` MUST be printed only when they all hold, and `NOT CONFORMING` on exit `1` as before. The exit code, every status and `speccheck.json` are unchanged (R-14, §5.4). C-08's §1 verdict line, being the summary line verbatim, follows. Source: §1 A. |
| **§5.1 (amended)** | `<STATUS>` is `CONFORMING` (exit `0` and R-15's conditions hold), `UNPROVEN` (exit `0` and they do not; R-105; only possible without `--strict`) or `NOT CONFORMING` (exit `1`). The T-44 regex's first group becomes `(CONFORMING\|NOT CONFORMING\|UNPROVEN)`. |
| **C-01 (a) (amended)** | `cells := the row split on every "\|" that is not preceded by "\" and not inside a backtick span; a backtick span is a run of N backticks (N >= 1) together with everything up to and including the next run of exactly N backticks on the same line (the CommonMark code span); a run with no such closing run is literal text and opens no span; the leading and trailing empty cells are dropped` |
| **E-66 (amended)** | Case: a table-declared row whose statement cell contains an odd number of unescaped `$` outside backtick spans and which has further cells, **or** a table-declared row inside a TABLE (C-01 (c)) with more cells than that TABLE's header row. Semantics: the statement is the cell as split (unchanged); one Note `statement may be cut at an unescaped '\|': <ID>` per such row, emitted once when both conditions hold. The fix is `\|` or a backtick span. (R-36; v1.24 adds the cell-count condition.) |
| **E-77** | A declared, non-retired id is the `src` or `dst` of no C-12 edge: no statement, row cell or *Affects* cell names it, and its own statement and row cells name no declared id. No edge, status, metric or exit-code change. One Note per run, when at least one id is isolated: `<N> declared id(s) touch no edge: <ID>, <ID>, <ID>` followed by ` and <N-3> more` when N > 3, the ids in C-07 order. A retired id is never counted. `impact` and `explain` do not emit it. (R-36, C-12) |
| **T-118** | On a copy of `fixtures/target/` without `--results`, `check` prints `speccheck: UNPROVEN - 0/20 passing (0.0%), …` and exits `0`; the same run with `--strict` prints `NOT CONFORMING` and exits `1`; a project whose every in-scope id is `PASSING` with no dangling or stale citation prints `CONFORMING` with and without `--strict`; the same project plus one dangling citation prints `UNPROVEN` without `--strict`; in every case the Markdown §1 line equals stdout, the line matches the amended T-44 regex, and `speccheck.json` is byte-identical to v1.23.1's except where Part D adds its Note. (R-105, §5.1, C-08, R-14) |
| **T-119** | C-01 (a) with CommonMark spans: a row whose statement is `` a fence (` ``` `), a table (first line contains `\|`) `` and continues past it has exactly two cells and its full text as the statement; a row ending in `` `x` `` then ` \|` carries no trailing `\|` in its last cell; an unmatched backtick does not protect a later `\|`, which splits; `` `a\|b` `` (the escaped form) stays one cell; the T-46/T-71 goldens are unchanged by this part. (C-01, E-04) |
| **T-120** | In a two-column TABLE, `\| **R-01** \| a \| b \|` yields the E-66 Note and the statement `a`; the same row inside `$..$` yields exactly one Note; a three-column TABLE's three-cell row yields none; a declared row outside any TABLE with an extra cell and no `$` yields none. (E-66, C-01) |
| **T-121** | A spec with an isolated R id, an isolated E id and a retired isolated C id yields one Note `2 declared id(s) touch no edge: R-.., E-..`, the retired id uncounted; adding a statement that names the R id removes it from the Note; with five isolated ids the Note lists three and ends ` and 2 more`; the `fixtures/target` golden carries `3 declared id(s) touch no edge: R-03, K-01, E-01`; `impact.json` carries no such Note. (E-77, C-12, R-36) |

## 3. What it costs

- **No new dependency.** Parts B and C reuse C-01 (c)'s TABLE detection, which already exists for
  the decision table. Part D reads the edges C-12 already builds.
- **Golden churn, once.**
  - Part D adds a Note to both fixture goldens: `fixtures/target/golden/speccheck.json` and its
    Markdown get `3 declared id(s) touch no edge: R-03, K-01, E-01`, the Swift fixture's get a Note
    for 7 ids, and `src/speccheck/_selfcheck/` follows (T-60). This is the one-time cost that ended
    v1.21's attempt, now with a rule narrow enough that the Note is worth reading. The planted
    UNCITED R-03, the unrelated K-01 and the scale-only E-01 really are disconnected in that
    fixture.
  - Part B changes this repository's T-05 statement (its stray trailing ` |` goes), and with it T-05's
    `statement` in self-application. No fixture changes.
  - Part A changes no file a test pins, except T-44's regex and any non-strict summary line a user's
    log parser matches on. None of the README's or the article's quoted lines change, because every
    one of them is all-`PASSING` or exits `1`.
- **This repository's own self-application gains one Note** (E-77: T-42) until T-42's row names
  the id it verifies (R-17, §5.3's requirement). That is a spec edit worth making whatever happens
  to D-60.
- **What is not guaranteed:** nothing here depends on a model; all four parts are deterministic, so
  every claim is checked by a gating test (T-118..T-121) and there is no `*(recorded)*` row. What
  Part C cannot see is a cut that leaves the cell count equal to the header's, for example a row
  authored with one cell too few plus a stray `|`. The 14-spec sample had no such row, which shows
  it is rare, not that it cannot happen.
- **Parts worth doing even if others are rejected:** B alone fixes the only silent truncation found
  in real specs; A alone removes the false green the debrief led with.

## 4. Alternatives considered

| Alternative | Why not |
| --- | --- |
| A: keep `CONFORMING` and append a suffix (`; 18 of 20 unproven`) | The word a reader and a log grep look for still says pass. The debrief asked for "a louder line, or a distinct word", and only the distinct word changes what `grep CONFORMING` matches. |
| A: print `UNPROVEN` only below a threshold (say < 50 % passing) | The threshold is arbitrary and moves the false green rather than removing it: 11/20 would read `CONFORMING`. R-15's conditions are the spec's own definition of conforming, with no new constant. |
| A: exit `1` without `--strict` when nothing passes | Breaks the use the debrief describes, non-strict runs "as a trend rather than a gate", and K-01's exit meanings. The exit code is not the defect; the word is. |
| A: a stderr warning | §5.3 makes default runs silent on stderr, and CI logs often show only stdout. |
| B: split the way GFM does (a `\|` inside a code span still splits) | Contradicts C-01 (a)'s stated rule, which deliberately protects code spans, and would split rows in specs that rely on it. CommonMark spans keep the rule and fix only its definition. |
| B and C: detection only, keep the current splitter | R-24 would get a Note but stay cut: the judge would still see half a statement until the author edits the row. Prevention is cheap and changes no fixture row. |
| C: Note a statement that "looks truncated" (ends mid-sentence, unbalanced brackets) | A heuristic over prose; it would fire on legitimate rows and miss clean cuts. The cell count is exact. |
| D: a Note per id that names no other id (the debrief's literal wording, v1.21's attempt) | 51 Notes on this spec, every one a correct leaf row (E-01, E-03, E-05 …). Noise of that size teaches readers to skip Notes. |
| D: one Note per isolated id | Same signal as the aggregated Note, but N Notes instead of one. The JSON's `edges` already let a tool list them all. |
| D: an opt-in `--lint` flag | The people who most need it (a spec author who left an edge case disconnected) are the ones who would not know to pass it, which is the debrief's point. With the narrow rule the default-on Note is rare: 0–2 per real spec measured. |

## 5. Decisions for the requester (D-58, D-59, D-60, all `confirm`)

| ID | Statement |
| -- | --------- |
| **D-58** | A distinct first word, `UNPROVEN`, on a non-strict exit-0 run that would not pass R-15 (recommended: removes the false green without touching the exit code the trend use depends on; one regex alternative more for log parsers) versus keeping `CONFORMING` with a suffix naming the unproven count (no parser change, but `CONFORMING` still prints over 0 % passing). |
| **D-59** | Define C-01 (a)'s backtick span as the CommonMark code span (recommended: fixes the one silent truncation found in real specs and 32 stray closing pipes, changes no fixture row) versus keeping the single-backtick toggle and relying on Part C's Note to report cuts (no parse change, but R-24 stays cut until edited). |
| **D-60** | One default-on Note naming the ids no edge touches, aggregated (recommended: 0–2 per real spec, every hit measured so far a real gap) versus the same check behind an opt-in `--lint` flag (no golden churn, but the authors who need it will not run it). |

Part C has no decision of its own: it widens an existing Note's condition, and every measured hit
is a true cut.

## 6. What the change does not do

- **No exit code, status, verdict or metric changes** under any branch. `UNPROVEN` is a word on the
  summary line, and E-66/E-77 are Notes. `--strict` behaves exactly as today.
- **It does not make GitHub render R-24 correctly.** GFM splits a table cell on a `|` even inside a
  code span. After Part B, speccheck reads `mdv_claude_opus`'s R-24 whole while GitHub still shows
  it cut. The author's fix is still `\|`, and Part C's Note names the row only while the cell count
  is off.
- **It does not catch every row the debrief worried about.** Their example was "a one-word
  transition row (just a target state)". If a test row names that transition, the transition
  touches an edge and E-77 stays silent, even though the row itself names nothing and a change to
  the state it targets will not reach it in `impact`. Catching that needs to know which rows *should*
  reference something, which is a semantic judgement the kernel does not make (§0's non-goals). We
  could not check their spec, so whether E-77 would have caught their specific row is unmeasured.
- **It does not detect a cut that leaves the cell count unchanged** (§3), or a cut in a declared row
  outside any TABLE beyond E-66's `$` case.
- **Cross-spec references (the debrief's row 9) are not touched.** `<ns>:ID` tokens stay foreign and
  ignored, as v1.23 specified.
