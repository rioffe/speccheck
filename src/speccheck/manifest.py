"""The provenance manifest (C-25) and `verify` (C-26). v1.25, R-106, R-107, I-020.

The manifest records what one `check --manifest` run read and wrote — the SHA-256 and length of
every input file, by role, and of both reports — so a quality record can say which bytes it was
computed from. It is deterministic (I-020): no wall-clock time, host or absolute path; a time only
from SOURCE_DATE_EPOCH (D-62). `verify` re-hashes; it never re-runs `check` (D-65).

Spec IDs realized here (§11): R-106, R-107, C-25, C-26, I-020, E-83.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from .report import _Num, dumps

MANIFEST_NAME = "speccheck.manifest.json"
MANIFEST_VERSION = "1.0"
MANIFEST_MAX = 2 * 1024 * 1024  # K-20: verify reads a manifest of at most K-02's 2 MiB
ROLES = ("spec", "src", "tests", "proof", "results", "citation_map", "proof_results", "risk_file")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_KEYS = ("manifest_version", "tool", "options", "inputs", "tree_sha256", "reports")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class ReadLog:
    """C-25 `inputs`: one (sha256, bytes) per (path, role) the run read, raw bytes before any
    decoding or CRLF normalization. The first read of a (path, role) wins."""

    entries: dict[tuple[str, str], tuple[str, int]] = field(default_factory=dict)

    def add(self, path: str, role: str, data: bytes) -> None:
        self.entries.setdefault((path, role), (sha256_hex(data), len(data)))

    def add_file(self, path: str, role: str, file: Path) -> None:
        """For a file the scan selected but did not read (K-02/E-10 over 2 MiB): hash it now."""
        if (path, role) not in self.entries:
            try:
                self.add(path, role, file.read_bytes())
            except OSError:
                pass  # unreadable now: it was never read, so it is not listed

    def inputs(self) -> list[dict]:
        return [
            {"path": p, "role": r, "sha256": h, "bytes": n}
            for (p, r), (h, n) in sorted(self.entries.items())
        ]


def tree_sha256(inputs: list[dict]) -> str:
    """C-25: SHA-256 of `<sha256>  <path>\\n` per distinct path, in code-point order — the
    `shasum -a 256 <files> | LC_ALL=C sort -k2 | shasum -a 256` digest."""
    first: dict[str, str] = {}
    for e in inputs:
        first.setdefault(e["path"], e["sha256"])
    text = "".join(f"{first[p]}  {p}\n" for p in sorted(first))
    return sha256_hex(text.encode("utf-8"))


def generated_at(epoch: int) -> str:
    """SOURCE_DATE_EPOCH as RFC 3339 UTC, no fraction (C-25)."""
    return datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def render_manifest(
    *,
    version: str,
    options: dict,
    log: ReadLog,
    reports: list[tuple[str, bytes]],
    epoch: int | None,
) -> str:
    """C-25: the manifest text, keys in the pinned order, serialized as speccheck.json is."""
    inputs = log.inputs()
    doc: dict = {
        "manifest_version": MANIFEST_VERSION,
        "tool": {"name": "speccheck", "version": version},
        "options": {
            "judge": options["judge"],
            "strict": options["strict"],
            "max_unknown": _Num(Decimal(options["max_unknown"])),
            "namespace": options["namespace"],
            "judge_model": options["judge_model"],
            "judge_prompt_sha256": options["judge_prompt_sha256"],
        },
        "inputs": inputs,
        "tree_sha256": tree_sha256(inputs),
        "reports": [
            {"path": path, "sha256": sha256_hex(data), "bytes": len(data)}
            for path, data in reports
        ],
    }
    if epoch is not None:
        doc["generated_at"] = generated_at(epoch)
    return dumps(doc)


class ManifestError(Exception):
    """E-83: a manifest `verify` cannot trust (exit 3, before any input is read)."""


def _entry_path(entry: object, k: str, root: Path, need_role: bool) -> str:
    if not isinstance(entry, dict):
        raise ManifestError(f"verify: malformed manifest: {k} is not an object")
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        raise ManifestError(f"verify: malformed manifest: {k} has no path")
    if need_role and entry.get("role") not in ROLES:
        raise ManifestError(f"verify: malformed manifest: {k} has no valid role")
    if not isinstance(entry.get("sha256"), str) or not _HEX64.fullmatch(entry["sha256"]):
        raise ManifestError(f"verify: malformed manifest: {k} sha256 is not 64 lower-case hex")
    n = entry.get("bytes")
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ManifestError(f"verify: malformed manifest: {k} bytes is not a non-negative integer")
    if Path(path).is_absolute():
        raise ManifestError(f"verify: malformed manifest: {k} path is absolute: {path}")
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise ManifestError(f"verify: malformed manifest: {k} path resolves outside --root: {path}")
    return path


def load_manifest(data: bytes, root: Path) -> tuple[list[dict], list[dict], str]:
    """E-83: validate everything before any input is read. Returns (distinct inputs in manifest
    order, reports, tree_sha256)."""
    if len(data) > MANIFEST_MAX:
        raise ManifestError("verify: malformed manifest: over 2 MiB (K-20)")
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"verify: malformed manifest: not UTF-8 JSON: {exc}") from None
    if not isinstance(doc, dict):
        raise ManifestError("verify: malformed manifest: not a JSON object")
    if doc.get("manifest_version") != MANIFEST_VERSION:
        raise ManifestError('verify: malformed manifest: manifest_version is not "1.0"')
    for key in _KEYS:
        if key not in doc:
            raise ManifestError(f"verify: malformed manifest: no {key} key")
    if not isinstance(doc["inputs"], list) or not isinstance(doc["reports"], list):
        raise ManifestError("verify: malformed manifest: inputs and reports must be lists")
    tree = doc["tree_sha256"]
    if not isinstance(tree, str) or not _HEX64.fullmatch(tree):
        raise ManifestError("verify: malformed manifest: tree_sha256 is not 64 lower-case hex")
    inputs: list[dict] = []
    seen: set[str] = set()
    for k, entry in enumerate(doc["inputs"]):
        path = _entry_path(entry, f"inputs[{k}]", root, need_role=True)
        if path not in seen:  # C-26: a path listed under two roles is checked and counted once
            seen.add(path)
            inputs.append(entry)
    reports = [entry for entry in doc["reports"]]
    for k, entry in enumerate(reports):
        _entry_path(entry, f"reports[{k}]", root, need_role=False)
    return inputs, reports, tree


@dataclass(frozen=True)
class VerifyResult:
    lines: list[str]
    exit_code: int


def verify(data: bytes, root: Path) -> VerifyResult:
    """C-26: re-hash every file the manifest names, inputs first then reports."""
    inputs, reports, tree = load_manifest(data, root)
    failed: list[str] = []
    for entry in inputs + reports:
        path = entry["path"]
        try:
            content = (root / path).read_bytes()
        except OSError:
            failed.append(f"verify: missing {path}")
            continue
        if len(content) != entry["bytes"] or sha256_hex(content) != entry["sha256"]:
            failed.append(f"verify: mismatch {path}")
    total = len(inputs) + len(reports)
    if failed:
        return VerifyResult(failed + [f"verify: FAILED - {len(failed)} of {total} files differ"], 1)
    return VerifyResult([f"verify: ok - {total} files match, tree {tree[:12]}"], 0)
