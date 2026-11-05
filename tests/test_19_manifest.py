"""§9.18 The provenance manifest and `verify` (C-25, C-26, R-106, R-107, I-020, I-021; v1.25)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from speccheck import __version__, report

from .conftest import FIXTURE, run_cli

ARGV = [
    "check", "--spec", "SPEC.md", "--src", "src", "--tests", "tests", "--results", "junit.xml",
    "--judge", "mock",
]
FULL = ARGV + ["--proof", "proof", "--proof-results", "proof-results.json", "--risk-file",
               "risk.json"]
MANIFEST = "speccheck.manifest.json"
KEYS = ["manifest_version", "tool", "options", "inputs", "tree_sha256", "reports"]


def fixture_copy(tmp_path: Path, name: str = "fx") -> Path:
    dst = tmp_path / name
    shutil.copytree(FIXTURE, dst, ignore=shutil.ignore_patterns("__pycache__", "golden"))
    (dst / "risk.json").write_text('{"hazards": [{"id": "HAZ-1"}]}', encoding="utf-8")
    return dst


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_at(out: Path) -> dict:
    return json.loads((out / MANIFEST).read_text(encoding="utf-8"))


def independent_inputs(base: Path) -> list[tuple[str, str]]:
    """Every file the fixture run reads, found without speccheck: spec, results, proof
    manifest, risk file, and every regular file under the three scan roots."""
    found = [
        ("SPEC.md", "spec"), ("junit.xml", "results"),
        ("proof-results.json", "proof_results"), ("risk.json", "risk_file"),
    ]
    for root, role in (("src", "src"), ("tests", "tests"), ("proof", "proof")):
        for dirpath, dirnames, filenames in os.walk(base / root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__" and not d.startswith(".")]
            for f in filenames:
                if role == "proof" and not f.endswith(".lean"):
                    continue
                found.append(((Path(dirpath) / f).relative_to(base).as_posix(), role))
    return sorted(found)


def tree_digest(inputs: list[dict]) -> str:
    seen: dict[str, str] = {}
    for e in inputs:
        seen.setdefault(e["path"], e["sha256"])
    text = "".join(f"{seen[p]}  {p}\n" for p in sorted(seen))
    return sha(text.encode("utf-8"))


def test_t122_manifest_shape_and_hashes(tmp_path):
    """T-122: key order; `inputs` equal an independent walk of what the run reads, each with its
    role, hash and length; `tree_sha256` reproduces from the `shasum` line format; `reports` hash
    the files written, Markdown first; `tool.version`; the reports are byte-identical to the same
    run without --manifest. (R-106, C-25, I-021)"""
    base = fixture_copy(tmp_path)
    with_m = run_cli(FULL + ["--manifest", "--out", "m"], base)
    without = run_cli(FULL + ["--out", "p"], base)
    assert with_m.code == without.code
    assert not (base / "p" / MANIFEST).exists()
    for name in ("speccheck.json", "SPEC_CONFORMANCE_REPORT.md"):
        assert (base / "m" / name).read_bytes() == (base / "p" / name).read_bytes()

    doc = manifest_at(base / "m")
    assert list(doc) == KEYS  # no SOURCE_DATE_EPOCH -> no generated_at
    assert doc["manifest_version"] == "1.0"
    assert doc["tool"] == {"name": "speccheck", "version": __version__}
    assert doc["options"] == {
        "judge": "mock", "strict": False, "max_unknown": 0.2, "namespace": None,
        "judge_model": None, "judge_prompt_sha256": None,
    }
    assert '"max_unknown": 0.2000' in (base / "m" / MANIFEST).read_text(encoding="utf-8")
    assert [(e["path"], e["role"]) for e in doc["inputs"]] == independent_inputs(base)
    for e in doc["inputs"]:
        data = (base / e["path"]).read_bytes()
        assert e == {"path": e["path"], "role": e["role"], "sha256": sha(data), "bytes": len(data)}
    assert doc["tree_sha256"] == tree_digest(doc["inputs"])
    assert [r["path"] for r in doc["reports"]] == [
        "m/SPEC_CONFORMANCE_REPORT.md", "m/speccheck.json",
    ]
    for r in doc["reports"]:
        data = (base / r["path"]).read_bytes()
        assert (r["sha256"], r["bytes"]) == (sha(data), len(data))
    text = (base / "m" / MANIFEST).read_text(encoding="utf-8")
    assert text.endswith("}\n") and str(base) not in text  # no absolute path (R-20)


def test_t122_manifest_is_never_scanned(tmp_path):
    """T-122 / C-03: with --out inside --tests, a second run neither scans the first run's
    manifest nor lists it among its inputs."""
    base = fixture_copy(tmp_path)
    argv = ARGV + ["--manifest", "--out", "tests/out"]
    run_cli(argv, base)
    first = manifest_at(base / "tests/out")
    run_cli(argv, base)
    second = manifest_at(base / "tests/out")
    paths = [e["path"] for e in second["inputs"]]
    assert "tests/out/" + MANIFEST not in paths and "tests/out/speccheck.json" not in paths
    assert second["inputs"] == first["inputs"]


def test_t123_determinism_epoch_and_crlf(tmp_path):
    """T-123: two runs give byte-identical manifests; SOURCE_DATE_EPOCH becomes `generated_at`;
    an invalid value exits 2 (E-85) before any read and is ignored without --manifest; a CRLF
    twin of the spec gives identical reports and a different spec hash. (I-020, C-25, E-85)"""
    base = fixture_copy(tmp_path)
    run_cli(ARGV + ["--manifest", "--out", "a"], base)
    run_cli(ARGV + ["--manifest", "--out", "b"], base)
    a, b = (base / "a" / MANIFEST).read_text(), (base / "b" / MANIFEST).read_text()
    assert a.replace('"a/', '"b/') == b  # only the report paths differ

    env = {"SOURCE_DATE_EPOCH": "1793836800"}
    run_cli(ARGV + ["--manifest", "--out", "e"], base, env)
    doc = manifest_at(base / "e")
    assert list(doc)[-1] == "generated_at" and doc["generated_at"] == "2026-11-05T00:00:00Z"

    for bad in ("abc", "", "-1", "1.5"):
        run = run_cli(ARGV + ["--manifest", "--out", "x"], base, {"SOURCE_DATE_EPOCH": bad})
        assert run.code == 2
        assert run.stderr == f"ERROR SOURCE_DATE_EPOCH: not a non-negative integer: {bad}\n"
        assert not (base / "x").exists()
    plain = run_cli(ARGV + ["--out", "y"], base, {"SOURCE_DATE_EPOCH": "abc"})
    assert plain.code in (0, 1) and not (base / "y" / MANIFEST).exists()

    crlf = fixture_copy(tmp_path, "crlf")
    spec = (crlf / "SPEC.md").read_bytes()
    (crlf / "SPEC.md").write_bytes(spec.replace(b"\n", b"\r\n"))
    run_cli(ARGV + ["--manifest", "--out", "a"], crlf)
    for name in ("speccheck.json", "SPEC_CONFORMANCE_REPORT.md"):
        assert (crlf / "a" / name).read_bytes() == (base / "a" / name).read_bytes()
    lf_spec = next(e for e in manifest_at(base / "a")["inputs"] if e["role"] == "spec")
    crlf_spec = next(e for e in manifest_at(crlf / "a")["inputs"] if e["role"] == "spec")
    assert lf_spec["sha256"] != crlf_spec["sha256"]


def test_t123_failure_before_the_manifest_rename_leaves_nothing(tmp_path, monkeypatch):
    """T-123 / §3.1: the manifest joins the temp-and-rename sequence; a failure at its rename
    removes the two reports already renamed, and no temporary survives. (I-001)"""
    base = fixture_copy(tmp_path)
    real = report._replace

    def failing(src, dst):
        if Path(dst).name == MANIFEST:
            raise OSError(28, "No space left on device")
        real(src, dst)

    monkeypatch.setattr(report, "_replace", failing)
    run = run_cli(ARGV + ["--manifest", "--out", "o"], base)
    assert run.code == 3
    assert list((base / "o").iterdir()) == []


def verify(base: Path, manifest: str, *extra: str):
    return run_cli(["verify", "--manifest", manifest, *extra], base)


def test_t124_verify_ok_mismatch_missing(tmp_path, monkeypatch):
    """T-124: `verify` prints the ok line on an untouched tree; names a changed byte and a
    deleted report; writes nothing; opens no socket. (R-107, C-26, I-001)"""
    import socket

    base = fixture_copy(tmp_path)
    run_cli(FULL + ["--manifest", "--out", "o"], base)
    doc = manifest_at(base / "o")
    n = len({e["path"] for e in doc["inputs"]}) + 2

    def no_socket(*_a, **_k):
        raise AssertionError("verify opened a socket")

    monkeypatch.setattr(socket, "socket", no_socket)
    before = {p: p.read_bytes() for p in base.rglob("*") if p.is_file()}
    ok = verify(base, "o/" + MANIFEST)
    assert ok.code == 0
    assert ok.stdout == f"verify: ok - {n} files match, tree {doc['tree_sha256'][:12]}\n"
    assert {p: p.read_bytes() for p in base.rglob("*") if p.is_file()} == before

    target = base / "tests" / "test_core.py"
    data = bytearray(target.read_bytes())
    data[0] ^= 0x01
    target.write_bytes(bytes(data))
    bad = verify(base, "o/" + MANIFEST)
    assert bad.code == 1
    assert bad.stdout == (
        f"verify: mismatch tests/test_core.py\nverify: FAILED - 1 of {n} files differ\n"
    )
    (base / "o" / "SPEC_CONFORMANCE_REPORT.md").unlink()
    gone = verify(base, "o/" + MANIFEST)
    assert gone.stdout.splitlines() == [
        "verify: mismatch tests/test_core.py",
        "verify: missing o/SPEC_CONFORMANCE_REPORT.md",
        f"verify: FAILED - 2 of {n} files differ",
    ]


def test_t124_verify_faults(tmp_path):
    """T-124 / E-82 / E-83: a missing or outside --manifest exits 2; a malformed manifest exits 3
    without reading any input. (R-107, E-82, E-83)"""
    base = fixture_copy(tmp_path)
    run_cli(ARGV + ["--manifest", "--out", "o"], base)
    good = manifest_at(base / "o")

    none = run_cli(["verify"], base)
    assert none.code == 2 and none.stderr == "ERROR verify: --manifest is required\n"
    missing = verify(base, "nope.json")
    assert missing.code == 2 and "verify: --manifest not a readable file: nope.json" in missing.stderr
    outside = tmp_path / "m.json"
    outside.write_text("{}", encoding="utf-8")
    out = verify(base, str(outside))
    assert out.code == 2 and out.stderr.startswith("ERROR verify: --manifest outside --root")

    def bad(doc_or_text, reason):
        p = base / "bad.json"
        text = doc_or_text if isinstance(doc_or_text, str) else json.dumps(doc_or_text)
        p.write_text(text, encoding="utf-8")
        run = verify(base, "bad.json")
        assert run.code == 3, (reason, run.stderr)
        assert run.stderr.startswith("ERROR verify: malformed manifest: ") and reason in run.stderr
        assert run.stdout == ""

    bad("{not json", "not UTF-8 JSON")
    bad({**good, "manifest_version": "2.0"}, "manifest_version")
    bad({k: v for k, v in good.items() if k != "reports"}, "reports")
    escape = {**good, "inputs": [{**good["inputs"][0], "path": "../x"}]}
    bad(escape, "outside --root")
    hexed = {**good, "inputs": [{**good["inputs"][0], "sha256": "ABC"}]}
    bad(hexed, "sha256")
    absolute = {**good, "reports": [{**good["reports"][0], "path": str(base / "x")}]}
    bad(absolute, "absolute")


def test_t125_the_v1_25_evidence(tmp_path):
    """T-125: a line appended to a --src file after a manifest run leaves the reports
    byte-identical (the v1.24 behaviour, kept), and `verify` against the first manifest names
    exactly that file. (R-106, R-107)"""
    base = fixture_copy(tmp_path)
    run_cli(ARGV + ["--manifest", "--out", "first"], base)
    with open(base / "src" / "calc" / "core.py", "a", encoding="utf-8") as f:
        f.write("# edited after the test run\n")
    run_cli(ARGV + ["--out", "second"], base)
    for name in ("speccheck.json", "SPEC_CONFORMANCE_REPORT.md"):
        assert (base / "first" / name).read_bytes() == (base / "second" / name).read_bytes()
    run = verify(base, "first/" + MANIFEST)
    assert run.code == 1
    assert [ln for ln in run.stdout.splitlines() if ln.startswith("verify: mismatch")] == [
        "verify: mismatch src/calc/core.py"
    ]


@pytest.mark.parametrize("argv", [["impact", "--spec", "SPEC.md", "--changed", "R-01"],
                                  ["explain", "R-01", "--spec", "SPEC.md"]])
def test_manifest_flag_is_check_only(tmp_path, argv):
    """§5.1: `--manifest` given to `impact` or `explain` is a usage error. (R-106)"""
    base = fixture_copy(tmp_path)
    assert run_cli(argv + ["--manifest"], base).code == 2


def test_t129_help_screens_name_the_v1_25_surface(tmp_path):
    """T-129 (help half): `check --help` names --manifest, --risk-file and SOURCE_DATE_EPOCH;
    `verify --help` names `--manifest FILE` and its four exit codes. (C-19, R-41)"""
    env = {"COLUMNS": "80"}
    check = run_cli(["check", "--help"], tmp_path, env).stdout
    for token in ("--manifest", "--risk-file FILE", "SOURCE_DATE_EPOCH"):
        assert token in check
    ver = run_cli(["verify", "--help"], tmp_path, env)
    assert ver.code == 0
    assert "--manifest FILE" in ver.stdout and "--root DIR" in ver.stdout
    for phrase in ("0 every file matches", "1 a file is missing or differs", "2 usage error",
                   "3 malformed manifest"):
        assert phrase in ver.stdout
