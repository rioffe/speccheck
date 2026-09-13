#!/usr/bin/env python3
"""Self-contained clickable cross-reference preprocessor for md2pdf.sh --click.

Turns KNOWN requirement-id mentions (R-/C-/I-/K-/E-/T-/D-) into pandoc internal
links [ID](#anchor) and adds {#anchor}s to the definitions, so the rendered
PDF has clickable jump-links -- the canonical, 100%-pandoc way (the render
engine + hyperref do the rest; NO raw LaTeX in the user's source).

Anchor resolution
-----------------
* ### C-0x sub-headings  get a per-id anchor {#C-0x}  -> exact jump.
* Every family id (R/I/K/E/T) is defined in its section table col-0, so it
  resolves to that section's anchor (e.g.  R-* -> #sec-requirements).
* A referenced-but-undefined id (e.g. C-13) falls back by id PREFIX to its
  family's section anchor -- so a link is never "dead", just coarse.

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
    (re.compile(r"##\s+\d+\.\s+.*?nterface", re.I), "sec-contracts"),
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
    for ln in lines:
        s = ln.strip()
        if s.startswith("###"):
            m = SUBHDR.match(ln)
            if m:
                c_sub.add(m.group(1))
            continue
        if s.startswith("## "):
            section = current_section(ln)
            continue
        if section and s.startswith("|"):
            for cell in s.strip("|").split("|"):
                m = TOKEN.search(re.sub(r"[*_`\\]", "", cell.strip()))
                if m:
                    fam[m.group(0)] = section
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
    msg = "wrote {0}    ({1} C-sub anchors, {2} section anchors, "
    msg += "known: {3} C-sub + {4} family)\n"
    sys.stderr.write(msg.format(out, c_sub_count, section_count,
                                len(c_sub), len(fam)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
