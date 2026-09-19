"""Impact walker (C-13; v1.13): the changed set (`--changed` / `--against`), the breadth-first
reverse walk over C-12 edges with `--depth` and `via`, and REVERIFY. Deterministic; consults no
judge and no results file.

Spec IDs realized here (§11): R-37, C-13, I-013, E-53, E-54, E-55.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from .extract import Decision, Edge, SpecIndex, collapse_ws, edge_id_key, normalize_id

_CHANGE_TOKEN_RE = re.compile(r"^([RCIKETD])-([0-9]{1,3})$")


class ChangedError(Exception):
    """--changed validation failure (E-53) -> usage error (exit 2)."""


@dataclass(frozen=True)
class ChangedEntry:
    id: str
    family: str
    line: int
    retired: bool
    reason: str


@dataclass(frozen=True)
class ImpactEntry:
    id: str
    depth: int
    retired: bool
    via: Edge


@dataclass(frozen=True)
class ReverifyEntry:
    id: str
    retired: bool
    verifies: tuple[str, ...]


@dataclass(frozen=True)
class WalkResult:
    impact: tuple[ImpactEntry, ...]
    beyond_depth: int  # count of ids that would enter at a depth beyond the cap


def _split_changed_list(raw: str) -> list[str]:
    """Split on ",", trim, drop empties -- the C-03 PATHS pattern, applied to --changed."""
    out: list[str] = []
    for segment in raw.split(","):
        trimmed = segment.strip(" \t")
        if trimmed:
            out.append(trimmed)
    return out


def resolve_changed_ids(index: SpecIndex, raw: str) -> tuple[ChangedEntry, ...]:
    """C-13: --changed IDS -> the changed set, each with reason "changed", in C-12 id order.
    Raises ChangedError (E-53) naming the first offending element, or "no ids" on an empty list."""
    elements = _split_changed_list(raw)
    if not elements:
        raise ChangedError("--changed: no ids")
    by_id = index.by_id()
    decisions_by_id = {d.id: d for d in index.decisions}
    seen: dict[str, ChangedEntry] = {}
    for element in elements:
        m = _CHANGE_TOKEN_RE.match(element)
        if not m:
            raise ChangedError(f"--changed: undeclared id: {element}")
        family, number = m.group(1), int(m.group(2))
        ident = normalize_id(family, number)
        if family == "D":
            decision = decisions_by_id.get(ident)
            if decision is None:
                raise ChangedError(f"--changed: undeclared id: {element}")
            seen[ident] = ChangedEntry(ident, "D", decision.line, False, "changed")
        else:
            spec_id = by_id.get(ident)
            if spec_id is None:
                raise ChangedError(f"--changed: undeclared id: {element}")
            seen[ident] = ChangedEntry(ident, family, spec_id.line, spec_id.retired, "changed")
    return tuple(sorted(seen.values(), key=lambda e: edge_id_key(e.id)))


_REASON_ORDER = (
    "statement differs",
    "added",
    "removed",
    "retired flag differs",
    "affects differs",
)


def diff_changed_set(old: SpecIndex, new: SpecIndex) -> tuple[ChangedEntry, ...]:
    """C-13: --against's changed set -- every id (R/C/I/K/E/T, or a decision) whose declaration
    differs between `old` (the --against file) and `new` (--spec), with every applicable reason
    joined by "; " in the fixed order above, in C-12 id order."""
    old_by_id = old.by_id()
    new_by_id = new.by_id()
    out: dict[str, ChangedEntry] = {}

    for ident in set(old_by_id) | set(new_by_id):
        o = old_by_id.get(ident)
        n = new_by_id.get(ident)
        reasons: list[str] = []
        if n is not None and o is not None:
            if collapse_ws(n.text) != collapse_ws(o.text):
                reasons.append("statement differs")
            if n.retired != o.retired:
                reasons.append("retired flag differs")
        elif n is not None:
            reasons.append("added")
        else:
            reasons.append("removed")
        if not reasons:
            continue
        current = n if n is not None else o
        assert current is not None
        out[ident] = ChangedEntry(
            ident, current.family, current.line, current.retired, "; ".join(reasons)
        )

    old_decisions = {d.id: d for d in old.decisions}
    new_decisions = {d.id: d for d in new.decisions}
    for ident in set(old_decisions) | set(new_decisions):
        o = old_decisions.get(ident)
        n = new_decisions.get(ident)
        reasons = []
        if n is not None and o is not None:
            if n.affects != o.affects:
                reasons.append("affects differs")
        elif n is not None:
            reasons.append("added")
        else:
            reasons.append("removed")
        if not reasons:
            continue
        current_d: Decision = n if n is not None else o  # type: ignore[assignment]
        out[ident] = ChangedEntry(ident, "D", current_d.line, False, "; ".join(reasons))

    return tuple(sorted(out.values(), key=lambda e: edge_id_key(e.id)))


def _is_d(ident: str) -> bool:
    return ident.split("-", 1)[0] == "D"


def walk(edges: tuple[Edge, ...], changed: set[str], depth_limit: int) -> WalkResult:
    """C-13: breadth-first from `changed`, reverse `depends_on` from an obligation, forward
    `affects` from a decision; each id enters once, at its first depth, with the smallest `via`
    edge (C-12 order) among those that reach it there. `depth_limit` 0 means unbounded; the
    result is always computed unbounded internally so that a limited run is an exact prefix of
    the unbounded one (I-013)."""
    dep_by_dst: dict[str, list[Edge]] = defaultdict(list)
    aff_by_src: dict[str, list[Edge]] = defaultdict(list)
    for e in edges:
        if e.kind == "depends_on":
            dep_by_dst[e.dst].append(e)
        elif e.kind == "affects":
            aff_by_src[e.src].append(e)

    entries: dict[str, tuple[int, Edge]] = {}
    seen: set[str] = set(changed)
    frontier = sorted(changed, key=edge_id_key)
    depth = 0
    while frontier:
        depth += 1
        candidates: dict[str, Edge] = {}
        for x in frontier:
            succs: list[tuple[str, Edge]] = []
            if _is_d(x):
                succs = [(e.dst, e) for e in aff_by_src.get(x, ())]
            else:
                succs = [(e.src, e) for e in dep_by_dst.get(x, ())]
            for target, e in succs:
                if target in seen:
                    continue
                best = candidates.get(target)
                if best is None or (edge_id_key(e.src), e.kind, edge_id_key(e.dst)) < (
                    edge_id_key(best.src),
                    best.kind,
                    edge_id_key(best.dst),
                ):
                    candidates[target] = e
        if not candidates:
            break
        for target, e in candidates.items():
            entries[target] = (depth, e)
            seen.add(target)
        frontier = sorted(candidates.keys(), key=edge_id_key)

    if depth_limit == 0:
        shown = entries
        beyond = 0
    else:
        shown = {k: v for k, v in entries.items() if v[0] <= depth_limit}
        beyond = len(entries) - len(shown)

    impact = tuple(
        sorted(
            (ImpactEntry(ident, d, False, e) for ident, (d, e) in shown.items()),
            key=lambda entry: (entry.depth, edge_id_key(entry.id)),
        )
    )
    return WalkResult(impact=impact, beyond_depth=beyond)


def mark_retired(entries: tuple[ImpactEntry, ...], index: SpecIndex) -> tuple[ImpactEntry, ...]:
    """Fill in ImpactEntry.retired from the spec index (walk() itself never needs retirement)."""
    by_id = index.by_id()
    return tuple(
        ImpactEntry(e.id, e.depth, by_id[e.id].retired if e.id in by_id else False, e.via)
        for e in entries
    )


def reverify_set(edges: tuple[Edge, ...], ids: set[str]) -> tuple[ReverifyEntry, ...]:
    """C-13: every T id with a "verifies" edge whose dst is in `ids`, plus every T id already
    in `ids`; each with the sorted obligations (within `ids`) it verifies."""
    verifies: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        if e.kind == "verifies" and e.dst in ids:
            verifies[e.src].add(e.dst)
    t_ids = set(verifies) | {i for i in ids if _family(i) == "T"}
    out = [
        ReverifyEntry(t, False, tuple(sorted(verifies.get(t, ()), key=edge_id_key)))
        for t in t_ids
    ]
    return tuple(sorted(out, key=lambda r: edge_id_key(r.id)))


def _family(ident: str) -> str:
    return ident.split("-", 1)[0]
