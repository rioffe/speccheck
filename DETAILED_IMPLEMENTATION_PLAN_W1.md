# Detailed implementation plan — W1: Extractor (line model, title, section body, K-14)

> - **Wave:** W1 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 1 — "Extractor").
> - **Spec basis:** `SPEC.md` v1.8, sha256 `d153bde1cafba8e2e726a4bd8b95938fca6ae7d093f7343ce36715eec1af770a`. Not edited by this wave.
> - **Gate:** `tests/test_01_extraction.py` green including the new T-72 test; ruff clean; no other file changed.
> - **Budget:** +60–95 production lines in one file (`IMPLEMENTATION_PLAN.md` §5 row "Extractor").
> - **Depends on:** nothing new. **Unlocks:** W2 (`SpecId.title`, `SpecId.text`, `parse_spec(...)` returning the K-14 notes).

## 1. Objective and spec obligations

| spec id | obligation | how this wave discharges it |
|---|---|---|
| R-33 (half) | heading-declared id's statement = title + section body | `SpecId.text` carries it; W2 makes JSON/judge consume it |
| C-01 | Lines rule; HEADING LINE; SECTION BODY; (a) `title := statement`; (b) title/statement rules | `parse_spec` line model; `_HEADING_RE` + body scan in `iter_declarations` |
| C-02 | `SpecId.title` and `text` semantics | dataclass field + construction |
| K-14 | 16,384-byte cap at a line boundary, marker line, one Note per truncated id | `_cap_statement`; notes returned from `parse_spec` |
| E-46 | over cap → truncated + Note; empty body → title; empty title + body → body | covered by the same code paths, asserted in T-72 |
| E-47 | inner declarations parsed as before; outer body includes them | body scan stops only at level ≤ own; declarations unaffected |
| T-72 | the acceptance test | `test_heading_section_bodies_title_cap_and_line_model` |

## 2. Entry preconditions

- `src/speccheck/extract.py` at `c0a770a`: `iter_declarations`, `parse_spec(text, rel_path) -> SpecIndex`, `_HEADING_RE`, `_fence_marker`, `collapse_ws`.
- `tests/test_01_extraction.py` and `tests/conftest.py` (`project` fixture, `run_cli`).
- Fixture specs `fixtures/target/SPEC.md`, `fixtures/target-swift/SPEC.md` (read-only in this wave).

## 3. Deliverables, file by file

### 3.1 `src/speccheck/extract.py` — EDIT, +60–95 lines

```python
STATEMENT_CAP_BYTES = 16_384                                   # K-14
TRUNCATION_MARKER = "… (statement truncated by speccheck at K-14)"

@dataclass(frozen=True)
class SpecId:
    family: str; number: int
    title: str          # C-02: table cell / heading remainder, whitespace-collapsed
    text: str           # C-02: the statement (C-01 (a)/(b)), capped per K-14
    line: int; retired: bool

def split_spec_lines(text: str) -> list[str]      # C-01 Lines: split on "\n", strip one trailing "\r"
def is_blank(line: str) -> bool                    # C-01 BLANK: empty or spaces/tabs only
def heading_level(line: str) -> int | None         # C-01 HEADING LINE (≤3 spaces, 1–6 "#", ws or EOL) else None
def cap_statement(statement: str) -> tuple[str, bool]   # K-14: (text, truncated)
def iter_declarations(lines) -> Iterable[tuple[str, int, str, str, bool, int]]   # (fam, num, title, statement, retired, lineno)
def parse_spec(text: str, rel_path: str) -> SpecIndex   # unchanged signature; K-14 notes on SpecIndex.notes
```

Behaviour rules:
1. `parse_spec` calls `split_spec_lines` once; nothing else splits spec text (C-01 Lines, I-002).
2. A heading declaration requires `heading_level(line) is not None` and the id token first after the `#` run; `_HEADING_RE` gains the ≤ 3-space indent and the `(?:\s|$)` after the run (C-01 (b), F-304).
3. `title` = remainder after the token, trailing `\s+#+\s*$` removed, `collapse_ws` (C-01 (b)).
4. SECTION BODY = lines after the heading up to the first later line that is a HEADING LINE (outside fences, using the same fence tracker state) with level ≤ own, or EOF; strip leading/trailing BLANK lines; join with `"\n"` (C-01 (b)). Fence state must be tracked through the body so a `# comment` inside a fenced block never ends it (E-04, T-72).
5. `text` = `title` if body empty; `body` if title empty; else `title + "\n" + body` (C-01 (b), E-46, F-305).
6. `cap_statement`: if `len(text.encode()) <= 16_384` return unchanged; else keep the longest prefix of whole lines (first line always) whose UTF-8 length joined by `"\n"` is ≤ 16,384, append `"\n" + TRUNCATION_MARKER`, flag truncated (K-14).
7. Table declarations: `title == text == collapse_ws(cells[1])` (C-01 (a)).
8. Notes: one `f"statement truncated at K-14: {ident}"` per truncated id, exposed as `SpecIndex.notes: tuple[str, ...]` (default empty) so `cli.py` can extend its list in W2 (K-14, E-46).

Invariants: no two `SpecId` share `(family, number)` (unchanged); `SpecIndex.ids` sort unchanged; E-01/E-02/E-03 behaviour unchanged.

## 4. Work items, in order

- **W1-01 (test first)** — `tests/test_01_extraction.py::test_heading_section_bodies_title_cap_and_line_model` (T-72). Fixture spec (inline string, LF):
  `### C-01 Widget` / blank / ```` ``` ```` / `| **R-99** | x |` / `# comment` / ```` ``` ```` / prose line with two trailing spaces / `#### note` / table `| **E-09** | inner |` / `---` / `### C-02 Two` / `### C-03` + body line / `### C-04 Empty` / blank / `### C-05 Title ###` / `    ### R-98 indented` (must neither declare nor end C-05's body) / `###` (bare — ends C-05's body) / `###C-06 x` (declares nothing) / `## Section` / `### C-07 Last` at EOF.
  Assertions: C-01 `text` == `"Widget\n" + every line from the fence through `---`` with indentation and trailing spaces intact; C-01 `title == "Widget"`; declared set == {C-01, C-02, C-03, C-04, C-05, C-07, E-09}; R-99, R-98, C-06 absent; C-03 `text` == body alone; C-04 `text == title == "Empty"`; C-05 `title == "Title"` and `text` == `"Title\n    ### R-98 indented"`; C-07 `text == title == "Last"`; same spec with `\r\n` → identical `SpecIndex`; a body ending in a whitespace-only line drops it; one inside is kept; a body of 17,000 ASCII bytes → `text` ≤ 16,384 bytes before the marker, ends with `"\n" + TRUNCATION_MARKER`, breaks at a line boundary, `index.notes == ("statement truncated at K-14: C-01",)`. Property over both fixture specs: `title` equals the independently computed cell/remainder; `text == title` for table ids and empty-body headings; `text.startswith(title + "\n")` otherwise.
  Expected first run: `AttributeError: 'SpecId' object has no attribute 'title'`.
- **W1-02** — `SpecId.title`, `split_spec_lines`, `is_blank`, `heading_level`, body scan, `text` rule, `title` rule → run T-72: expected the cap sub-assertion still fails.
- **W1-03** — `cap_statement`, `SpecIndex.notes` → T-72 green.
- **W1-04** — run the whole `test_01_extraction.py`; T-01/T-55/T-70 expectations that mention heading statements still hold (`title == text` for their empty-body headings). Refactor: keep `iter_declarations` readable — body scan as a helper `section_body(lines, start, level, fence_state)`.

## 5. Test plan

| group / file | spec ids | what must be asserted | how it runs |
|---|---|---|---|
| `tests/test_01_extraction.py` (new T-72 case) | R-33, C-01, C-02, K-14, E-46, E-47 | §4 W1-01 list | `uv run python -m pytest tests/test_01_extraction.py -q` |
| existing T-01..T-07, T-55, T-70 | C-01, C-02 | unchanged expectations | same command |

## 6. Gate: commands and expected results

1. `uv run python -m pytest tests/test_01_extraction.py -q` — expected: `10 passed` (9 existing + T-72), exit 0.
2. `uv run ruff check src tests && uv run ruff format --check src tests` — expected: no output, exit 0.
3. `git diff --stat` — expected: exactly `src/speccheck/extract.py` and `tests/test_01_extraction.py`.
4. `uv run python -m pytest tests -q` — expected: the rest of the suite unchanged from baseline except that `test_06_reports` T-34 may now fail on `ID_KEYS` only if `title` is already emitted (it is not, in W1) — i.e. expected `2 failed` (T-54, T-48 as at baseline), nothing new.

## 7. Traceability

| spec id | file.symbol | test | status now → after W1 |
|---|---|---|---|
| R-33 | `extract.py.iter_declarations` | T-72 | UNCITED → UNTESTED-by-W2's-half (cited by source and T-72) |
| C-01 | `extract.py.split_spec_lines/heading_level/section_body` | T-72 (+T-01, T-05, T-55, T-70) | PASSING → PASSING |
| C-02 | `extract.py.SpecId` | T-72 (+T-01) | PASSING → PASSING |
| K-14 | `extract.py.cap_statement` | T-72 | UNCITED → PASSING |
| E-46 | `extract.py` | T-72 | UNCITED → PASSING |
| E-47 | `extract.py.section_body` | T-72 | UNCITED → PASSING |
| T-72 | — | itself | UNCITED → PASSING |

## 8. Risks, traps, and the structural rules this wave must not break

- **Fence state across the body.** The body scan must continue the fence tracker from the heading line onward; a naive "next `#`-line" scan ends C-01's body at the `# comment` inside the fence (T-72's first sub-case exists for this). Rule: one fence tracker, shared by declaration and body scanning (plan §6 "one computation").
- **Indent limit changes declarations too.** `    ### R-98` inside an indented block was a declaration under 1.6.0's `^\s*#` regex; under v1.8 it is not (F-304). T-55's existing cases have no such line; T-72 pins the new behaviour.
- **Byte cap vs. character cap.** `len(text)` is characters; K-14 is UTF-8 bytes. T-72's cap sub-case uses a non-ASCII line so the two differ.
- **Trailing spaces.** `collapse_ws` must not touch body lines; only the title is collapsed.
- **Do not read the body for table rows.** A table declaration's `title == text` always; the body concept exists only for headings (C-01 (a)).

## 9. Exit criteria and handoff contract

Frozen after W1: `SpecId(family, number, title, text, line, retired)`, `SpecIndex(path, ids, notes=())`, `parse_spec(text: str, rel_path: str) -> SpecIndex`, `STATEMENT_CAP_BYTES`, `TRUNCATION_MARKER`. W2 may call exactly these. W2 re-runs gate command 1 first to confirm W1 is intact.
