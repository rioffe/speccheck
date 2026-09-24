"""Proof manifest: read (never run) a `--proof-results` JSON file and join it to the C-20
citations by declaration name and file (C-21, K-17; v1.19).

Spec IDs realized here (§11): C-21, K-17, E-65.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .lean import ProofCitation

REQUIRED_TOP_KEYS = ("build", "theorems")


class ProofError(Exception):
    """E-65: malformed JSON, or missing the `build`/`theorems` keys C-21 requires -> exit 3.
    (Unreadable is checked earlier, at config-build time, and is a usage error -> exit 2.)"""


@dataclass(frozen=True)
class ManifestTheorem:
    file: str
    name: str
    line: int | None
    status: str  # "checked" | "failed"


@dataclass(frozen=True)
class ProofManifest:
    build: dict  # {"exit", "theorems_total", "theorems_checked", "errors": [str]} - echoed verbatim
    theorems: tuple[ManifestTheorem, ...]


@dataclass(frozen=True)
class ProofEdge:
    name: str
    file: str
    line: int
    state: str  # checked | failed | unknown | stale
    error: str | None = None


def parse_proof_results(text: str) -> tuple[ProofManifest, list[str]]:
    """C-21: parse the manifest, reading exactly `build` and `theorems` (plus the optional
    `deferred_to_pytest`, validated for shape only) and ignoring every other top-level key and
    every extra key on a `theorems`/`deferred_to_pytest` entry."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProofError(f"proof-results: not well-formed JSON: {exc}") from None
    if not isinstance(obj, dict):
        raise ProofError("proof-results: not a JSON object")
    missing = [k for k in REQUIRED_TOP_KEYS if k not in obj]
    if missing:
        raise ProofError(f"proof-results: missing required key(s): {', '.join(missing)}")
    build = obj["build"]
    if not isinstance(build, dict):
        raise ProofError("proof-results: 'build' is not an object")
    raw_theorems = obj["theorems"]
    if not isinstance(raw_theorems, list):
        raise ProofError("proof-results: 'theorems' is not an array")
    notes: list[str] = []
    theorems: list[ManifestTheorem] = []
    for i, raw in enumerate(raw_theorems):
        if (
            not isinstance(raw, dict)
            or not isinstance(raw.get("name"), str)
            or not isinstance(raw.get("status"), str)
        ):
            notes.append(f"proof-results: theorems[{i}] malformed, skipped")
            continue
        file = raw.get("file") if isinstance(raw.get("file"), str) else ""
        line = raw.get("line") if isinstance(raw.get("line"), int) else None
        theorems.append(ManifestTheorem(file, raw["name"], line, raw["status"]))
    if "deferred_to_pytest" in obj and not isinstance(obj["deferred_to_pytest"], list):
        notes.append("proof-results: 'deferred_to_pytest' is not an array, ignored")
    return ProofManifest(build, tuple(theorems)), notes


def _same_file(cit_file: str, manifest_file: str) -> bool:
    """K-17's "file" match, tolerant of the two sides' different roots: a proof citation's
    `file` is posix-relative to `--root` (R-20, like every other citation), while a manifest a
    producer wrote (e.g. `tools/proof_evidence.py`) records `file` relative to its own `--proof`
    scan root instead — one is commonly a path suffix of the other. Exact equality is tried
    first (the common case: `--proof` names `--root` itself, or the two conventions happen to
    agree already); a suffix match on path components is the fallback."""
    if cit_file == manifest_file:
        return True
    a, b = f"/{cit_file}", f"/{manifest_file}"
    return a.endswith(b) or b.endswith(a)


def _find_error(build: dict, file: str, line: int) -> str | None:
    errors = build.get("errors")
    if not isinstance(errors, list):
        return None
    target = f"{file}:{line}"
    for e in errors:
        if isinstance(e, str) and e == target:
            return e
    return None


def join_proof(
    citations: list[ProofCitation], manifest: ProofManifest | None
) -> tuple[dict[str, list[ProofEdge]], list[str]]:
    """K-17 / C-21: join citations to manifest theorems by name and file (line, where present).
    A citation without a matching manifest entry is `unknown`; a name match in a different file
    or line is `stale`; a manifest entry with no matching citation is a notes entry. Returns
    (id -> proof edges, notes)."""
    by_id: dict[str, list[ProofEdge]] = {}
    notes: list[str] = []
    if manifest is None:
        # --proof given, --proof-results absent: nothing to confirm status against.
        for cit in citations:
            by_id.setdefault(cit.id, []).append(
                ProofEdge(cit.name, cit.file, cit.line, "unknown")
            )
        return by_id, notes

    by_name: dict[str, list[ManifestTheorem]] = {}
    for t in manifest.theorems:
        by_name.setdefault(t.name, []).append(t)
    matched: set[tuple[str, str, int | None]] = set()

    for cit in citations:
        candidates = by_name.get(cit.name, [])
        match = next(
            (
                t
                for t in candidates
                if _same_file(cit.file, t.file) and (t.line is None or t.line == cit.line)
            ),
            None,
        )
        if match is not None:
            matched.add((match.name, match.file, match.line))
            error = None
            if match.status == "failed":
                error = _find_error(manifest.build, match.file, match.line)
            edge = ProofEdge(cit.name, cit.file, cit.line, match.status, error)
        elif candidates:
            edge = ProofEdge(cit.name, cit.file, cit.line, "stale")
        else:
            edge = ProofEdge(cit.name, cit.file, cit.line, "unknown")
        by_id.setdefault(cit.id, []).append(edge)

    for t in manifest.theorems:
        if (t.name, t.file, t.line) not in matched:
            notes.append(f"proof manifest entry not cited: {t.file}:{t.name}")

    return by_id, notes
