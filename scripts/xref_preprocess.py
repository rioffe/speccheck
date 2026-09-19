#!/usr/bin/env python3
"""Self-contained clickable cross-reference preprocessor for md2pdf.sh --click.

Turns KNOWN requirement-id mentions (R-/C-/I-/K-/E-/T-/D-) into pandoc internal
links [ID](#anchor) and adds {#anchor}s to the definitions, so the rendered
PDF has clickable jump-links -- the canonical, 100%-pandoc way (the render
engine + hyperref do the rest; NO raw LaTeX in the user's source).

Anchor resolution
-----------------
* Every DECLARATION gets its own anchor, so a link jumps to the row or heading
  that declares the id, not to its section:
    - a table row whose first cell BEGINS with the bold id form -- `**R-07**`,
      `~~**R-07**~~` or `**~~R-07~~**`, speccheck's own C-01 (a) rule, which is
      what keeps the plain `R-07` column of a traceability table from becoming
      a second anchor -- is rewritten to `[**R-07**]{#R-07}` (or, for a struck
      form, `[]{#R-07}~~**R-07**~~`, since soul's st{} cannot hold a label);
    - a `### R-07 ...` heading gets `{#R-07}`;
    - a `| D-01 |` row (plain id, first cell) in the decisions section gets
      `[D-01]{#D-01}` -- D rows are not bold by convention.
  pandoc turns the span into phantomsection+label{R-07} and the link into
  hyperref[R-07]{R-07}; hyperref does the rest.
* A referenced-but-undeclared id (e.g. C-13) falls back by id PREFIX to its
  family's section anchor -- so a link is never "dead", just coarse.
* A second declaration of the same id (a spec defect, E-02) keeps the first
  anchor; the duplicate row is linkified like any other mention.

Left VERBATIM: fenced code blocks (incl. the traceability graph / diagrams),
inline-code (`...`), and $$...$$ display-math (a link inside LaTeX math is
invalid). Sub-headings (###) do NOT clear a family section, so ids defined in
###  subsections (e.g.  the T-xx test tables under  "## 9. ... tests") stick.

Usage:  xref_preprocess.py <in.md> [out.md]       (out defaults to <in>.xref.md)
"""
import os
import re
import sys

FENCE = re.compile(r"^\s*```")
SUBHDR = re.compile(r"^###\s+([A-Z]{1,3}-\d+[A-Za-z]*)")            # ### C-01 ...
INLINE = re.compile(r"`[^`]*`")                             # inline code: plain
TOKEN = re.compile(r"([A-Z]{1,3}-\d{1,3}[A-Za-z]*)")                # a KNOWN-id token

# Level-2 family / contracts section headings -> their unique PDF anchor.
SECTION_RULES = [
    (re.compile(r"##\s+\d+\.\s+Requirements", re.I), "sec-requirements"),
    (re.compile(r"##\s+\d+\.\s+.*?nvariant", re.I), "sec-invariants"),
    (re.compile(r"##\s+\d+\.\s+.*?Constraint", re.I), "sec-constraints"),
    (re.compile(r"##\s+\d+\.\s+.*?dge\b", re.I), "sec-edgecases"),
    (re.compile(r"##\s+\d+\.\s+.*[\bT]est", re.I), "sec-tests"),
    (re.compile(r"##\s+\d+\.\s+Interfaces\s*/\s*contracts", re.I), "sec-contracts"),
    (re.compile(r"##\s+\d+\.\s+Open questions", re.I), "sec-decisions"),
]
PREFIX = {
    "R": "sec-requirements", "I": "sec-invariants", "K": "sec-constraints",
    "E": "sec-edgecases", "T": "sec-tests", "C": "sec-contracts",
    "D": "sec-decisions",
}


def current_section(line):
    """Return the family/contracts anchor of a level-2 heading, else None."""
    if line.startswith("###"):
        return None
    for rule, key in SECTION_RULES:
        if rule.match(line):
            return key
    return None


def derive(lines):
    """Return (c_sub, fam):
       c_sub -> C ids that have a ### C-0x sub-heading (get a per-id anchor);
       fam   -> every family id -> its section anchor."""
    c_sub = set()
    fam = {}
    section = None
    in_fence = False
    for ln in lines:
        if FENCE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = ln.strip()
        if s.startswith("###"):
            m = SUBHDR.match(ln)
            if m:
                c_sub.add(m.group(1))          # heading declaration: per-id anchor
            continue
        if s.startswith("## "):
            section = current_section(ln)
            continue
        if s.startswith("|"):
            decl = declaration_in_row(ln, section)
            if decl and decl[0] not in c_sub:
                c_sub.add(decl[0])             # row declaration: per-id anchor (first one wins)
            elif section:
                for cell in s.strip("|").split("|"):
                    m = TOKEN.search(re.sub(r"[*_`\\]", "", cell.strip()))
                    if m:
                        fam.setdefault(m.group(0), section)
                        break
    return c_sub, fam


def make_anchor_for(c_sub, fam):
    def anchor_for(tok):
        if tok in c_sub:
            return tok
        if tok in fam:
            return fam[tok]
        key = re.match(r"^([A-Z]+)", tok)
        if key and key.group(1) in PREFIX:
            return PREFIX[key.group(1)]
        return None
    return anchor_for


STRIKE = re.compile(r"(~~.*?~~)")                            # ~~retired~~ span: never linked
# C-01 (a): the first cell must BEGIN with one of the three bold forms; whatever follows must be
# empty or start with whitespace (decoration such as **[port]** or *(recorded)*).
DECL_CELL = re.compile(
    r"^(?P<form>\*\*(?P<a>[A-Z]{1,3}-\d{1,3})\*\*"
    r"|~~\*\*(?P<b>[A-Z]{1,3}-\d{1,3})\*\*~~"
    r"|\*\*~~(?P<c>[A-Z]{1,3}-\d{1,3})~~\*\*)(?=$|\s)"
)
DECISION_CELL = re.compile(r"^(?P<tok>D-\d{1,3})$")


def declaration_in_row(line, section):
    """(token, form, is_struck, is_plain_decision) for a declaring table row, else None."""
    cells = line.strip().strip("|").split("|")
    if not cells:
        return None
    first = cells[0].strip()
    m = DECL_CELL.match(first)
    if m:
        tok = m.group("a") or m.group("b") or m.group("c")
        return tok, m.group("form"), m.group("a") is None, False
    if section == "sec-decisions":
        m = DECISION_CELL.match(first)
        if m:
            return m.group("tok"), first, False, True
    return None


def anchor_row(line, decl):
    """Rewrite the declaring first cell so it carries the id's anchor."""
    tok, form, struck, plain = decl
    if plain:
        anchored = "[{}]{{#{}}}".format(form, tok)
    elif struck:
        anchored = "[]{{#{}}}{}".format(tok, form)
    else:
        anchored = "[{}]{{#{}}}".format(form, tok)
    return line.replace(form, anchored, 1)


def linkify(line, anchors, anchor_for, skip_leading=False):
    """Rewrite KNOWN-id tokens in `line` to [ID](#anchor).

    Tokens inside a ~~strikethrough~~ span are left alone: a struck-through id
    is a RETIRED declaration, not a reference, and pandoc renders the span with
    soul's \\st{}, which cannot contain a \\hyperref (xelatex: "Package soul
    Error: Reconstruction failed")."""
    if "~~" in line and len(pieces := STRIKE.split(line)) > 1:
        # len == 1 means no closed ~~span~~ on this line (e.g. a literal `~~~` fence
        # marker); fall through, or the recursion below never terminates.
        return "".join(seg if i % 2 else linkify(seg, anchors, anchor_for, skip_leading and i == 0)
                       for i, seg in enumerate(pieces))
    parts = TOKEN.split(line)
    if len(parts) == 1:
        return line
    out = []
    for i, seg in enumerate(parts):
        if i % 2 == 0:
            out.append(INLINE.sub(lambda m: m.group(0), seg))
        elif seg in anchors:
            if skip_leading and i == 1:
                out.append(seg)
            else:
                out.append("[{}]({})".format(seg, "#" + anchor_for(seg)))
        else:
            out.append(seg)
    return "".join(out)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: xref_preprocess.py <in.md> [out.md]\n")
        return 2
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else in_path[:-3] + ".xref.md"
    try:
        with open(in_path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        sys.stderr.write("cannot read {0!r}: {1}\n".format(in_path, exc))
        return 1

    c_sub, fam = derive(lines)
    anchors = dict(fam)
    for c in c_sub:
        anchors[c] = c                         # per-id C anchors override the section
    anchor_for = make_anchor_for(c_sub, fam)

    out_lines = []
    c_sub_count = 0
    section_count = 0
    row_count = 0
    anchored_ids = set()
    section_now = None
    in_fence = False
    in_math = False
    for ln in lines:
        if FENCE.match(ln):
            in_fence = not in_fence
            out_lines.append(ln)
            continue
        if in_fence:
            out_lines.append(ln)
            continue
        if ln.strip() == "$$":
            in_math = not in_math
            out_lines.append(ln)
            continue
        if in_math:
            out_lines.append(ln)
            continue

        if re.match(r"^#{1,6}\s+", ln):
            key = current_section(ln)
            if ln.startswith("## "):
                section_now = key
            sm = SUBHDR.match(ln)
            if sm:
                key = sm.group(1)
                c_sub_count += 1
                if key in c_sub:
                    section_count += 1
            elif key:
                section_count += 1
            linked = linkify(ln, anchors, anchor_for, skip_leading=True)
            if key:
                linked = re.sub(r"\s*\{#[^}]+\}\s*$", "", linked).rstrip()
                linked = linked + " {#" + key + "}"
            out_lines.append(linked)
            continue

        if ln.lstrip().startswith("|"):
            decl = declaration_in_row(ln, section_now)
            if decl and decl[0] not in anchored_ids:
                anchored_ids.add(decl[0])
                tok, form = decl[0], decl[1]
                head, sep, tail = ln.partition(form)
                # the declaring cell becomes the anchor; the rest of the row is linkified as usual
                out_lines.append(head + anchor_row(form, decl) + linkify(tail, anchors, anchor_for))
                row_count += 1
                continue
        out_lines.append(linkify(ln, anchors, anchor_for, skip_leading=False))

    out = os.path.join(os.path.dirname(out_path) or ".", os.path.basename(out_path))
    try:
        if os.path.dirname(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out_lines) + "\n")
    except OSError as exc:
        sys.stderr.write("cannot write {0!r}: {1}\n".format(out, exc))
        return 1
    msg = "wrote {0}    ({1} heading anchors, {2} row anchors, {3} section anchors; "
    msg += "{4} ids anchored, {5} resolve to a section only)\n"
    sys.stderr.write(msg.format(out, c_sub_count, row_count, section_count,
                                len(c_sub), len(set(fam) - c_sub)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
