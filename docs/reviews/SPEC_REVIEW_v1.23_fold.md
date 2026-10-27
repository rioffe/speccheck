# Review of `SPEC.md` v1.23 — the namespaces and citation-map fold

> - **Scope:** the 20 rows and 2 contracts folded from
>   `docs/proposals/PROPOSAL_v1.23_namespaces_and_citation_map.md` (R-101..R-103, C-22, C-23,
>   I-019, K-19, E-67..E-73, T-107..T-112, D-51..D-55), and every pre-existing row they touch
>   (C-01, C-03, C-07, C-08, C-12, C-18, §3.1, §5.1, K-18). Not a full 20-dimension review of the
>   299-id spec; `docs/reviews/SPEC_REVIEW_REPORT.md` remains the last full one.
> - **Method:** (1) parse with the project's own extractor and check ids, edges, Notes and the
>   traceability table; (2) simulate an implementation row by row, looking for a case no row
>   decides; (3) check each touched contract for a sentence the fold left false.
> - **Limit — not independent.** The author of the fold wrote this review, in the same session.
>   The method's own rule is that the writer never grades their own work, so treat this as a
>   self-check that found defects, not as a clean bill. An independent `spec-review` pass over the
>   fold is still owed.
> - **Verdict:** READY WITH MINOR FIXES to build, after the open items in §3 are decided.
>   Eight defects were found and fixed in the spec during the review (§1); the four open items of §3 were then dispositioned (two folded into the spec, two accepted with no row change).

## 1. Defects found and fixed during the fold and this review

| ID | Severity | Finding | Fix |
| -- | -------- | ------- | --- |
| **F-601** | HIGH | The proposal put `--namespace` and `--citation-map` on `check` only. `impact` re-cites from the same scan, so a project retrofitted by map would get an empty re-cite list from `impact`, and `explain` would disagree with `check` on the same id. | Both flags are accepted by `check`, `impact` and `explain` (R-102, R-103, §5.1 synopsis and flag table, §3.1 `impact` table). Recorded in the v1.23 changelog as a change from the proposal. |
| **F-602** | HIGH | The FOREIGN grammar let an ID-shaped label be a namespace: `R-01:R-02` would make `R-02` foreign — a silent loss of a real citation in any list written with colons. | `ns` MUST NOT match `[RCIKET]-[0-9]{1,3}` (R-101, C-22). |
| **F-603** | HIGH | The summary line is pinned by a regex (T-44) and by the article test. The proposal added a suffix without touching either; every mapped run would fail its own spec. | Suffix `; citations: <M> mapped` added to the §5.1 prose and regex, after the judge-suffix, only when M > 0. |
| **F-604** | MEDIUM | `--citation-map` unreadable is exit `2`, but the map is read after the scan. K-18 says no exit-3 fault may be reported before every exit-2 fault. | E-70 splits the faults: readability and containment are decided with the flags (K-18); shape faults in a new `apply-map` stage (§3.1). K-18's list of exit-3 faults names E-70. |
| **F-605** | MEDIUM | The proposal's K-19 allowed 100,000 entries and 2 MiB. The smallest well-formed entry is about 40 bytes, so 2 MiB caps the count near 52,000 and the entry limit could never fire — a limit no test can reach. | K-19, C-23, E-70 and T-111 state only the 2 MiB cap and why. |
| **F-606** | MEDIUM | `--namespace` given twice was undefined (argparse would take the last). | R-102: at most once; a second occurrence is exit `2`. |
| **F-607** | LOW | The Markdown report (C-08) was silent on how a mapped citation renders; C-23 reached into C-08's layout. | C-08's citation comment now states `file (map)`; C-23 defers to it. |
| **F-608** | LOW | Illustrative ids in the new rows (`R-01:R-02`, `platform:C-03`, `R-03` in the JSON example) created real C-12 edges to unrelated rows, so `impact` would have listed R-01, R-02, C-03 and R-03 as depending on the new rows. | Examples now use the undeclared id `R-99` (the house idiom, T-72) or no id; this adds four `edge to undeclared id: … -> R-99` Notes (R-101, T-107, T-108, C-23); the first three disappear once E-69 is built, because `platform:R-99` becomes foreign, and C-23's stays (its example id is bare). |

## 2. Checked and found consistent

- **Ids and traceability.** The extractor parses 299 ids (279 + 20), no duplicate, none retired.
  Every new R/C/I/K/E id has one traceability row; every new E, C, I, K row cites at least one T;
  every T row cites the rows it verifies; D-51..D-55 `Affects` cells name only declared ids.
- **Inertness (I-019).** Every addition is conditional on its input: `foreign`, `citation_map`,
  `tests[].mapped`, the summary suffix, and the Note. `schema_version` stays `"1.5"` on the C-07
  precedent for `proof` (v1.19). The golden fixtures contain no `ns:`-prefixed token, so T-109
  should hold; it must be measured, not assumed.
- **C-05 is untouched.** A mapped citation is a `Citation`; the status algorithm, I-004 and the
  judge's downgrade-only rule read it like any other. The label is the only difference.
- **Ordering and determinism (I-002).** `foreign` is sorted by `(file, line, namespace, id)`;
  the map's entry order cannot change any output (entries resolve to a set, duplicates collapse
  under E-73); an unresolved entry's Note is sorted with the other Notes (Q-002).
- **Retired and undeclared ids.** A mapped entry for a retired id is a stale citation, for an
  undeclared id a dangling one, both at the case's `start` line; both feed R-15 like a literal one.
- **Excluded and ignored files.** A map entry naming a file the scan never reads
  (`speccheck:ignore-file`, an excluded directory, a symlink) is unresolved (E-71), not an error.
- **Jest/vitest (v1.22) interaction.** A map entry for a `.ts` file resolves against the names the
  JS/TS adapter produces (`describe > test`); T-110 includes a JavaScript case so the two rows are
  tested together.

## 3. Open items

| ID | Severity | Finding | Recommendation | Disposition |
| -- | -------- | ------- | -------------- | ----------- |
| **F-609** | MEDIUM | **D-51 default-on has a measured scope of one project.** T-112 records that this repository has no `ns:`-prefixed token in code or tests. Other projects may write `Note:R-03` or YAML `key:R-03` and silently lose a citation. The Note `N foreign reference(s) ignored` is the only warning. | Keep default-on (it closes a silent false-green), but build the Note to name the first three tokens with `file:line`, and run the recorded T-112 against two more real projects before the release. Not a spec change until there is evidence. | **Folded.** E-67 and C-22: the Note names the first three tokens as `<ns>:<id> <file>:<line>` and ` and <N-3> more`; T-107 pins it; T-112 now runs over this repository plus at least two further real projects. D-51 stays default-on. |
| **F-610** | MEDIUM | **`declared: true` for a mapped citation is a judgment call.** A map states the owner's intent, so the judge is told the citation is DECLARED (R-39); but nobody wrote that intent next to the test. It is the one place where mapped and literal citations are treated identically by design. | Either confirm (the map *is* the declaration) or add a decision D-57. The fold follows the proposal. | **Folded.** Confirmed on the recommended branch as D-57 (`declared: true`; `mapped` is the separate label); E-72 cites it and T-110 asserts the judge request carries it. |
| **F-611** | LOW | **Unmapped-test drift is invisible.** If a test is renamed, its entry becomes unresolved (E-71, a Note only, D-55) and the id usually falls to `UNCITED` or `UNVERIFIED`, which `--strict` already gates. But a rename that lands on another existing test name resolves silently to the wrong case. | Out of scope for a lexical join. The `citation_map` counts make a sudden change in `resolved` visible in review; no row change. | **Accepted, no change.** |
| **F-612** | LOW | **Build impact the spec states only implicitly.** The new flags must appear in `--help` for all three subcommands (R-41; T-95..T-97 pin four screens byte for byte under `tests/data/help/`), the T-44 regex in the test suite and the article test regex must gain the optional suffix, and the article's id and test counts change. | Listed here so the build plan carries them; no spec change. | **Accepted, no change.** Carried into the build plan below. |

## 4. Recommendation

Build, test first, in this order: C-22 and R-101/E-67..E-69 (the false-green fix, deliverable on
its own), then R-102, then the map (C-23, R-103, E-70..E-73, K-19), then the `impact`/`explain`
surfaces. Gate each wave with T-109 (byte identity) before the next begins. F-610 is decided (D-57). Request an independent `spec-review` of the fold before the release; this document does
not replace it.
