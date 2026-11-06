"""`speccheck qualify`: installation and operational qualification of the installed tool.
v1.26, R-110..R-115, C-29..C-31, I-022, E-86..E-88.

IQ hashes the installed package against its `RECORD` and into the package tree hash, which equals
the same computation over the release tag (R-112, D-68). OQ runs the packaged case catalog, each
case in a temporary copy of a packaged fixture, in-process, under a scoped socket guard (R-113).
The record names the intended use, the tool hazards and the known anomalies (C-29). It reads only
the installed package and writes only the two records, through the caller (I-022).

Spec IDs realized here (§11): R-110, R-111, R-112, R-113, R-115, C-29, C-30, C-31, I-022, E-86,
E-87, E-88.
"""

from __future__ import annotations

import base64
import contextlib
import csv
import hashlib
import importlib.metadata as metadata
import io
import json
import os
import platform
import re
import shutil
import socket
import sys
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .manifest import generated_at, sha256_hex
from .report import dumps

QUALIFICATION_JSON = "qualification.json"
QUALIFICATION_MD = "QUALIFICATION_REPORT.md"
QUALIFICATION_VERSION = "1.0"
PACKAGE = Path(__file__).resolve().parent
DATA_DIR = "_qualify"
_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
NOT_A_WHEEL = "not an installed wheel (no hashed RECORD)"  # E-86

RunStep = Callable[[list[str], io.StringIO], int]


class SocketBlocked(RuntimeError):
    """I-022 / E-88: a socket was opened during `qualify`."""


@contextlib.contextmanager
def socket_guard() -> Iterator[None]:
    """I-022: no socket for the duration of the run; the original is restored afterwards, so an
    in-process caller (the test suite) is left as it was."""
    original = socket.socket.__init__

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise SocketBlocked("speccheck: network I/O is forbidden (I-022)")

    socket.socket.__init__ = blocked  # type: ignore[method-assign]
    try:
        yield
    finally:
        socket.socket.__init__ = original  # type: ignore[method-assign]


# ------------------------------------------------------------------------------------- IQ


@dataclass
class IQ:
    """R-112: what installation qualification found."""

    tree: str | None = None
    files: int = 0
    mismatches: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    environment: dict = field(default_factory=dict)
    dependencies: list[dict] = field(default_factory=list)


def _tree_text(pairs: list[tuple[str, str]]) -> str:
    """C-25's `shasum` line format, one line per path in code-point order."""
    return "".join(f"{digest}  {path}\n" for path, digest in sorted(pairs))


def tree_of_directory(package_dir: Path) -> tuple[str, int]:
    """R-112 (a) over a source tree (`src/speccheck`): the same value an install of it yields."""
    pairs = [
        (f"speccheck/{p.relative_to(package_dir).as_posix()}", sha256_hex(p.read_bytes()))
        for p in package_dir.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    ]
    return sha256_hex(_tree_text(pairs).encode("utf-8")), len(pairs)


def _record_digest(data: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")


def _in_tree(path: str) -> bool:
    return (
        path.startswith("speccheck/") and "__pycache__/" not in path and not path.endswith(".pyc")
    )


def _environment(dist: metadata.Distribution | None) -> dict:
    source = None
    if dist is not None:
        try:
            text = dist.read_text("direct_url.json")
            url = json.loads(text).get("url") if text else None
            source = url if isinstance(url, str) else None
        except (OSError, ValueError, AttributeError):
            source = None
    return {
        "implementation": sys.implementation.name,
        "python": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "source": source,
    }


def _dependencies(dist: metadata.Distribution | None) -> list[dict]:
    names: set[str] = set()
    for requirement in (dist.requires or []) if dist is not None else []:
        match = _NAME_RE.match(requirement.strip())
        if match:
            names.add(match.group(0))
    out = []
    for name in sorted(names):
        try:
            version: str | None = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = None
        out.append({"name": name, "version": version})
    return out


def _record_rows(dist: metadata.Distribution) -> list[tuple[str, str | None]]:
    """RECORD's (path, sha256 digest or None), read directly: `Distribution.files` drops the
    entries whose file is missing (Python 3.12+), and a missing file is what IQ must report."""
    text = dist.read_text("RECORD") or ""
    rows = []
    for row in csv.reader(text.splitlines()):
        if not row or not row[0]:
            continue
        digest = row[1] if len(row) > 1 else ""
        mode, _, value = digest.partition("=")
        rows.append((row[0].replace("\\", "/"), value if mode == "sha256" and value else None))
    return rows


def package_iq(dist: metadata.Distribution | None) -> IQ:
    """R-112: the package tree hash, the RECORD check, the environment and the dependencies.
    No hashed RECORD entry under speccheck/ (an editable or source-tree install) is E-86."""
    iq = IQ(environment=_environment(dist), dependencies=_dependencies(dist))
    rows = _record_rows(dist) if dist is not None else []
    if dist is None or not any(h is not None and _in_tree(p) for p, h in rows):
        return iq  # E-86: tree stays None, files 0
    pairs: list[tuple[str, str]] = []
    for path, digest in rows:
        try:
            data = Path(str(dist.locate_file(path))).read_bytes()
        except OSError:
            if digest is not None or _in_tree(path):
                iq.missing.append(path)
            continue
        if digest is not None and _record_digest(data) != digest:
            iq.mismatches.append(path)
        if _in_tree(path):
            pairs.append((path, sha256_hex(data)))
    iq.mismatches.sort()
    iq.missing.sort()
    iq.tree = sha256_hex(_tree_text(pairs).encode("utf-8"))
    iq.files = len(pairs)
    return iq


def installed_distribution() -> metadata.Distribution | None:
    try:
        return metadata.distribution("speccheck")
    except metadata.PackageNotFoundError:
        return None


# ----------------------------------------------------------------------- packaged data


@dataclass
class Data:
    """The packaged `_qualify/` data, as far as it parsed (E-87 lists what did not)."""

    intended_use: str = ""
    cases: list[dict] = field(default_factory=list)
    hazards: list[dict] = field(default_factory=list)
    anomalies: list[dict] = field(default_factory=list)
    faults: list[str] = field(default_factory=list)


def _is_str_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _step_fault(step: object) -> str | None:
    if not isinstance(step, dict):
        return "a step is not an object"
    if not _is_str_list(step.get("argv")):
        return "argv is not a list of strings"
    edit = step.get("edit")
    if edit is not None and not (
        isinstance(edit, dict)
        and isinstance(edit.get("append"), str)
        and isinstance(edit.get("text"), str)
    ):
        return "edit is not null or {append, text}"
    if not isinstance(step.get("exit"), int) or isinstance(step.get("exit"), bool):
        return "exit is not an integer"
    if not isinstance(step.get("stdout"), str):
        return "stdout is not a string"
    goldens = step.get("goldens")
    if not isinstance(goldens, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in goldens.items()
    ):
        return "goldens is not an object of strings"
    return None


def _case_fault(case: object) -> str | None:
    """C-30's case shape."""
    if not isinstance(case, dict):
        return "not an object"
    for key in ("id", "title", "fixture"):
        if not isinstance(case.get(key), str) or not case.get(key):
            return f"{key} is not a non-empty string"
    if not _is_str_list(case.get("hazards")):
        return "hazards is not a list of strings"
    steps = case.get("steps")
    if not isinstance(steps, list) or not steps:
        return "steps is not a non-empty list"
    for step in steps:
        fault = _step_fault(step)
        if fault:
            return fault
    return None


def _anomaly_fault(entry: object) -> str | None:
    """C-31's entry shape."""
    if not isinstance(entry, dict):
        return "not an object"
    for key in ("id", "summary", "workaround", "found_in"):
        if not isinstance(entry.get(key), str):
            return f"{key} is not a string"
    if not _is_str_list(entry.get("hazards")):
        return "hazards is not a list of strings"
    if not _VERSION_RE.fullmatch(entry["found_in"]):
        return "found_in is not X.Y.Z"
    fixed = entry.get("fixed_in")
    if fixed is not None and not (isinstance(fixed, str) and _VERSION_RE.fullmatch(fixed)):
        return "fixed_in is not X.Y.Z or null"
    return None


def _read_json(root: Path, name: str, faults: list[str]) -> object | None:
    label = f"{DATA_DIR}/{name}"
    try:
        return json.loads((root / DATA_DIR / name).read_bytes().decode("utf-8"))
    except FileNotFoundError:
        faults.append(f"{label}: missing")
    except OSError as exc:
        faults.append(f"{label}: unreadable: {exc.strerror or exc}")
    except UnicodeDecodeError:
        faults.append(f"{label}: not UTF-8")
    except json.JSONDecodeError as exc:
        faults.append(f"{label}: not JSON: line {exc.lineno} column {exc.colno}")
    return None


def load_data(root: Path) -> Data:
    """E-87: every packaged file read, every fault listed, nothing raised."""
    data = Data()
    label = f"{DATA_DIR}/intended_use.md"
    try:
        data.intended_use = (root / DATA_DIR / "intended_use.md").read_bytes().decode("utf-8")
    except FileNotFoundError:
        data.faults.append(f"{label}: missing")
    except OSError as exc:
        data.faults.append(f"{label}: unreadable: {exc.strerror or exc}")
    except UnicodeDecodeError:
        data.faults.append(f"{label}: not UTF-8")

    doc = _read_json(root, "cases.json", data.faults)
    if doc is not None:
        cases = doc.get("cases") if isinstance(doc, dict) else None
        if not isinstance(cases, list):
            data.faults.append(f"{DATA_DIR}/cases.json: no cases list")
        else:
            for k, case in enumerate(cases):
                fault = _case_fault(case)
                if fault:
                    data.faults.append(f"{DATA_DIR}/cases.json: case {k}: {fault}")
                else:
                    data.cases.append(case)

    doc = _read_json(root, "tool_risk.json", data.faults)
    if doc is not None:
        hazards = doc.get("hazards") if isinstance(doc, dict) else None
        if not isinstance(hazards, list) or not all(
            isinstance(h, dict) and isinstance(h.get("id"), str) for h in hazards
        ):
            data.faults.append(f"{DATA_DIR}/tool_risk.json: not a C-28 risk file")
        else:
            data.hazards = [{"id": h["id"], "title": h.get("title")} for h in hazards]

    doc = _read_json(root, "known_anomalies.json", data.faults)
    if doc is not None:
        entries = doc.get("anomalies") if isinstance(doc, dict) else None
        if not isinstance(entries, list):
            data.faults.append(f"{DATA_DIR}/known_anomalies.json: no anomalies list")
        else:
            for k, entry in enumerate(entries):
                fault = _anomaly_fault(entry)
                if fault:
                    data.faults.append(f"{DATA_DIR}/known_anomalies.json: entry {k}: {fault}")
                else:
                    data.anomalies.append(entry)
    return data


def _version_key(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def open_anomalies(anomalies: list[dict], version: str) -> list[dict]:
    """R-115: entries not fixed in or before the running version, in file order."""
    running = _version_key(version)
    return [
        a
        for a in anomalies
        if a.get("fixed_in") is None or _version_key(a["fixed_in"]) > running
    ]


# ------------------------------------------------------------------------------------- OQ


@dataclass(frozen=True)
class CaseResult:
    id: str
    title: str
    hazards: list[str]
    failure: str | None  # None: PASS


def _missing_paths(root: Path, case: dict) -> list[str]:
    """E-87: the fixture and every golden a case names must be packaged."""
    fixture = root / case["fixture"]
    if not fixture.is_dir():
        return [f"{case['fixture']}: missing"]
    return [
        f"{case['fixture']}/{golden}: missing"
        for step in case["steps"]
        for golden in step["goldens"].values()
        if not (fixture / golden).is_file()
    ]


def _run_case(root: Path, case: dict, run_step: RunStep) -> str | None:
    """R-113: one case in its own temporary copy, the copy as the working directory; returns
    the failure, or None. The copy is removed whatever happens."""
    tmp = Path(tempfile.mkdtemp(prefix="speccheck-qualify-")).resolve()
    cwd = os.getcwd()
    try:
        shutil.copytree(
            root / case["fixture"],
            tmp,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        os.chdir(tmp)
        for n, step in enumerate(case["steps"], 1):
            edit = step["edit"]
            if edit is not None:
                with open(tmp / edit["append"], "ab") as handle:
                    handle.write(edit["text"].encode("utf-8"))
            out = io.StringIO()
            try:
                code = run_step(list(step["argv"]), out)
            except SocketBlocked:
                return f"step {n}: socket"  # E-88
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 0
            except Exception as exc:  # noqa: BLE001 - E-88: a raising step fails its case
                return f"step {n}: {type(exc).__name__}"
            if code != step["exit"]:
                return f"step {n}: exit {code}, expected {step['exit']}"
            if out.getvalue() != step["stdout"]:
                return f"step {n}: stdout differs"
            for produced, golden in step["goldens"].items():
                path = tmp / produced
                if not path.is_file():
                    return f"step {n}: {produced} was not written"
                if path.read_bytes() != (tmp / golden).read_bytes():
                    return f"step {n}: {produced} differs from {golden}"
        return None
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp, ignore_errors=True)


def run_catalog(root: Path, data: Data, run_step: RunStep) -> list[CaseResult]:
    """R-113: every case, in catalog order; a failing case never stops a later one."""
    results = []
    for case in data.cases:
        missing = _missing_paths(root, case)
        if missing:
            data.faults.extend(f"{DATA_DIR}/cases.json: {case['id']}: {m}" for m in missing)
            failure: str | None = "packaged fixture or golden missing"
        else:
            failure = _run_case(root, case, run_step)
        results.append(CaseResult(case["id"], case["title"], list(case["hazards"]), failure))
    return results


# --------------------------------------------------------------------------------- record


@dataclass(frozen=True)
class Record:
    json_text: str
    md_text: str
    line: str
    exit_code: int


def first_failure(iq: IQ, faults: list[str], results: list[CaseResult]) -> str | None:
    """C-29: the first failure that applies, in the pinned order."""
    if iq.tree is None:
        return NOT_A_WHEEL
    if faults:
        return f"packaged data {faults[0]}"
    if iq.mismatches:
        return f"RECORD mismatch {iq.mismatches[0]}"
    if iq.missing:
        return f"RECORD missing {iq.missing[0]}"
    for r in results:
        if r.failure is not None:
            return f"{r.id}: {r.failure}"
    return None


def _cell(text: object) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def _md_list(title: str, items: list[str]) -> list[str]:
    body = [f"- `{item}`" for item in items] if items else ["None."]
    return [f"**{title}:**", "", *body, ""]


def _render_markdown(doc: dict, line: str) -> str:
    env = doc["environment"]
    iq = doc["iq"]
    out = [f"# Qualification record — speccheck {doc['tool']['version']}", "", "## 1. Verdict", ""]
    out += [f"**{doc['verdict']}**", "", f"`{line}`", ""]
    if "generated_at" in doc:
        out += [f"Generated at: {doc['generated_at']}", ""]
    out += ["## 2. Intended use", "", "```text", doc["intended_use"].rstrip("\n"), "```", ""]
    out += ["## 3. Installation qualification", "", "| Item | Value |", "| --- | --- |"]
    for label, value in (
        ("Implementation", env["implementation"]),
        ("Python", env["python"]),
        ("System", env["system"]),
        ("Machine", env["machine"]),
        ("Source", env["source"]),
        ("Package tree SHA-256", iq["package_tree_sha256"]),
        ("Files", iq["files"]),
    ):
        out.append(f"| {label} | {'—' if value is None else _cell(value)} |")
    out.append("")
    out += _md_list("RECORD mismatches", iq["record_mismatches"])
    out += _md_list("RECORD missing", iq["record_missing"])
    out += _md_list("Packaged data faults", iq["data_faults"])
    out += ["| Dependency | Installed |", "| --- | --- |"]
    for dep in doc["dependencies"]:
        out.append(f"| {dep['name']} | {dep['version'] or 'not installed'} |")
    out += ["", "## 4. Operational qualification", ""]
    out += ["| Case | Title | Hazards | Result | Failure |", "| --- | --- | --- | --- | --- |"]
    for case in doc["oq"]:
        failure = "—" if case["failure"] is None else _cell(case["failure"])
        hazards = ", ".join(case["hazards"])
        out.append(
            f"| {case['id']} | {_cell(case['title'])} | {hazards} | {case['result']} | {failure} |"
        )
    out += ["", "## 5. Tool hazards", ""]
    out += ["| Hazard | Title | Challenged by |", "| --- | --- | --- |"]
    for h in doc["hazards"]:
        title = "—" if h["title"] is None else _cell(h["title"])
        out.append(f"| {h['id']} | {title} | {', '.join(h['cases']) or '—'} |")
    out += ["", "## 6. Known anomalies", ""]
    if doc["known_anomalies"]:
        out += [
            "| Anomaly | Summary | Hazards | Workaround | Found in | Fixed in |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for a in doc["known_anomalies"]:
            out.append(
                f"| {a['id']} | {_cell(a['summary'])} | {', '.join(a['hazards'])} | "
                f"{_cell(a['workaround'])} | {a['found_in']} | {a.get('fixed_in') or '—'} |"
            )
    else:
        out.append("None.")
    out += ["", "## 7. Signatures", ""]
    out += ["| Role | Name | Signature | Date |", "| --- | --- | --- | --- |"]
    out += ["| Executed by |  |  |  |", "| Reviewed by |  |  |  |", ""]
    return "\n".join(out)


def build_record(
    *, version: str, iq: IQ, data: Data, results: list[CaseResult], epoch: int | None
) -> Record:
    """C-29: both records, the stdout line (R-111) and the exit code."""
    failure = first_failure(iq, data.faults, results)
    verdict = "QUALIFIED" if failure is None else "NOT QUALIFIED"
    doc: dict = {
        "qualification_version": QUALIFICATION_VERSION,
        "tool": {"name": "speccheck", "version": version},
        "intended_use": data.intended_use,
        "environment": iq.environment,
        "dependencies": iq.dependencies,
        "iq": {
            "package_tree_sha256": iq.tree,
            "files": iq.files,
            "record_mismatches": iq.mismatches,
            "record_missing": iq.missing,
            "data_faults": sorted(data.faults),
        },
        "oq": [
            {
                "id": r.id,
                "title": r.title,
                "hazards": r.hazards,
                "result": "PASS" if r.failure is None else "FAIL",
                "failure": r.failure,
            }
            for r in results
        ],
        "hazards": [
            {
                "id": h["id"],
                "title": h["title"],
                "cases": [r.id for r in results if h["id"] in r.hazards],
            }
            for h in data.hazards
        ],
        "known_anomalies": open_anomalies(data.anomalies, version),
        "verdict": verdict,
    }
    if epoch is not None:
        doc["generated_at"] = generated_at(epoch)
    if failure is None:
        assert iq.tree is not None
        line = (
            f"qualify: QUALIFIED - IQ {iq.files} files, tree {iq.tree[:12]}; "
            f"OQ {len(results)}/{len(results)} cases"
        )
    else:
        line = f"qualify: NOT QUALIFIED - {failure}"
    return Record(dumps(doc), _render_markdown(doc, line), line, 0 if failure is None else 1)


def qualify(
    *,
    version: str,
    run_step: RunStep,
    epoch: int | None,
    root: Path = PACKAGE,
    dist: metadata.Distribution | None = None,
    use_installed: bool = True,
) -> Record:
    """R-111: IQ, then OQ, under the socket guard; nothing written here (the caller writes)."""
    with socket_guard():
        iq = package_iq(installed_distribution() if use_installed and dist is None else dist)
        data = load_data(root)
        results = run_catalog(root, data, run_step)
    return build_record(version=version, iq=iq, data=data, results=results, epoch=epoch)
