"""§9.17 Namespaces (C-22, R-101, R-102, E-67..E-69, I-019; v1.23).

Every input that carries a `<ns>:ID` form lives in tests/data/namespaces/ behind a line-1
`speccheck:ignore-file` marker, dropped when the file is copied into a project, so this suite's
own self-application counts none of them (F-713).
"""

from __future__ import annotations

import json

from .conftest import DATA, FIXTURE, junit, run_cli, spec_table

NS_DATA = DATA / "namespaces"
SPEC = spec_table([("R-01", "one"), ("R-02", "two"), ("R-03", "three"), ("R-04", "four")])
P = "platform"  # every `<ns>:ID` below is built at runtime, so this file cites none (F-713)


def _data(name: str) -> str:
    """The data file without its line-1 ignore marker."""
    return (NS_DATA / name).read_text(encoding="utf-8").split("\n", 1)[1]


def _check(proj, *extra: str) -> tuple[int, dict, str]:
    run = run_cli(
        ["check", "--spec", "SPEC.md", "--src", "src", "--tests", "tests", "--out", "out", *extra],
        proj.path,
    )
    doc = (
        json.loads((proj.path / "out" / "speccheck.json").read_text()) if run.code in (0, 1) else {}
    )
    return run.code, doc, run.stderr


def _status(doc: dict, ident: str) -> str:
    return next(r["status"] for r in doc["ids"] if r["id"] == ident)


def test_t107_foreign_reference_is_no_citation(project):
    """T-107: a test docstring naming a `platform`-prefixed R-04 against a spec declaring R-04 leaves R-04
    UNCITED, lists the token in `foreign` with its file and line, and emits one Note naming it;
    with `--namespace` for that ns the id is PASSING, `foreign` is absent and no Note is emitted.
    (R-101, R-102, E-67, E-68, C-22, C-07)"""
    files = {"SPEC.md": SPEC, "src/x.py": "", "tests/test_x.py": _data("foreign_test.py")}
    files["junit.xml"] = junit([("tests.test_x", "test_platform_rule", "passed")])
    proj = project(files)
    code, doc, _ = _check(proj, "--results", "junit.xml")
    assert code == 1 and _status(doc, "R-04") == "UNCITED"
    assert doc["foreign"] == [{"namespace": P, "id": "R-04", "file": "tests/test_x.py", "line": 5}]
    assert f"1 foreign reference(s) ignored: {P}:R-04 tests/test_x.py:5" in doc["notes"]
    keys = list(doc)
    assert (
        keys.index("unattributed_results") + 1 == keys.index("foreign") == keys.index("notes") - 1
    )
    code, doc, _ = _check(proj, "--results", "junit.xml", "--namespace", P)
    assert _status(doc, "R-04") == "PASSING" and "foreign" not in doc
    assert not any("foreign reference" in n for n in doc["notes"])


def test_t107_note_names_three_then_counts_the_rest(project):
    """T-107: with four foreign tokens the Note lists the first three in `foreign` order
    (file, line, namespace, id) and ends ` and 1 more`. (E-67, C-22)"""
    proj = project({"SPEC.md": SPEC, "src/x.py": "", "tests/test_m.py": _data("four_tokens.py")})
    _, doc, _ = _check(proj)
    assert [(f["namespace"], f["id"]) for f in doc["foreign"]] == [
        ("other", "R-02"),
        (P, "R-03"),
        (P, "R-04"),
        ("x-y", "R-01"),
    ]
    assert (
        f"4 foreign reference(s) ignored: {'other'}:R-02 tests/test_m.py:5, {P}:R-03 "
        f"tests/test_m.py:5, {P}:R-04 tests/test_m.py:5 and 1 more"
    ) in doc["notes"]


def test_t107_long_namespace_is_foreign_and_id_shaped_label_is_not(project):
    """T-107 (v1.23.1, F-712): a namespace longer than 32 characters is foreign, not local; two
    ids joined by a colon (the first an ID-shaped label) are both local citations. (R-101, C-22)"""
    proj = project({"SPEC.md": SPEC, "src/x.py": "", "tests/test_l.py": _data("long_and_pair.py")})
    _, doc, _ = _check(proj)
    assert _status(doc, "R-04") == "UNCITED"
    assert doc["foreign"][0]["namespace"] == "regulated_platform_core_services_v2_extra"
    assert _status(doc, "R-01") == _status(doc, "R-02") == "UNVERIFIED"


def test_t107_namespace_flag_validation(project):
    """T-107 / E-68 / R-102: `--namespace` at most once; a value over 32 characters or shaped
    like an ID exits 2 before any file is read; all three subcommands accept the flag. (R-102,
    E-68, K-18)"""
    proj = project({"SPEC.md": SPEC, "src/x.py": "", "tests/test_x.py": _data("foreign_test.py")})
    base = ["check", "--spec", "SPEC.md", "--out", "out"]
    twice = run_cli([*base, "--namespace", "a", "--namespace", "b"], proj.path)
    assert twice.code == 2 and "--namespace: given more than once" in twice.stderr
    for bad in ("a" * 33, "R-01", "9lives"):
        run = run_cli([*base, "--namespace", bad], proj.path)
        assert run.code == 2 and f"--namespace: invalid namespace: {bad}" in run.stderr, bad
    assert not (proj.path / "out").exists()
    ok = run_cli([*base, "--namespace", "a" * 32], proj.path)
    assert ok.code in (0, 1), ok.stderr


def test_t107_impact_and_explain_agree(project):
    """T-107: `impact` and `explain` over the same inputs agree with `check` — the foreign
    citation is no re-cite site and no citing case until `--namespace` names its ns. (R-101,
    R-102, C-13, C-18)"""
    files = {"SPEC.md": SPEC, "src/x.py": "", "tests/test_x.py": _data("foreign_test.py")}
    proj = project(files)
    imp = ["impact", "--spec", "SPEC.md", "--changed", "R-04", "--tests", "tests", "--out", "imp"]
    assert run_cli(imp, proj.path).code == 0
    assert json.loads((proj.path / "imp" / "impact.json").read_text())["test_cases"] == []
    assert run_cli([*imp, "--namespace", P], proj.path).code == 0
    cases = json.loads((proj.path / "imp" / "impact.json").read_text())["test_cases"]
    assert [c["name"] for c in cases] == ["test_platform_rule"]
    exp = ["explain", "R-04", "--spec", "SPEC.md", "--src", "src", "--tests", "tests"]
    assert "status: UNCITED" in run_cli(exp, proj.path).stdout
    assert "status: UNVERIFIED" in run_cli([*exp, "--namespace", P], proj.path).stdout


def test_t108_foreign_reference_in_spec_is_no_edge(project):
    """T-108: a statement naming a `platform`-prefixed R-02 yields no edge to R-02 and no Note, while a bare
    R-03 beside a foreign one still yields its edge; an Affects cell likewise; a range whose first
    endpoint is foreign names only its bare endpoint (F-716); `foreign` lists none of them.
    (R-101, E-69, C-12)"""
    proj = project({"SPEC.md": _data("spec_foreign.md"), "src/x.py": "", "tests/t.py": ""})
    _, doc, _ = _check(proj)
    edges = {(e["src"], e["kind"], e["dst"]) for e in doc["edges"]}
    assert edges == {
        ("R-02", "depends_on", "R-03"),
        ("R-05", "depends_on", "R-04"),
        ("D-01", "affects", "R-02"),
    }
    assert not any(n.startswith("edge to undeclared") for n in doc["notes"])
    assert "foreign" not in doc
    assert doc["decisions"][0]["affects"] == ["R-02"]


def test_t109_runs_without_the_flags_are_byte_identical(tmp_path):
    """T-109 (half: the namespace side; the citation-map side is in test_17): the §9.8 golden
    fixture, with no `--namespace` and no `ns:`-prefixed token, reproduces its v1.22 goldens, exit
    code and summary line byte for byte. (I-019)"""
    import shutil

    target = tmp_path / "target"
    shutil.copytree(FIXTURE, target)
    args = [
        "check",
        "--spec",
        "SPEC.md",
        "--src",
        "src",
        "--tests",
        "tests",
        "--results",
        "junit.xml",
        "--judge",
        "mock",
        "--strict",
        "--out",
        "fresh",
    ]
    run = run_cli(args, target)
    assert run.code == 1
    for name in ("speccheck.json", "SPEC_CONFORMANCE_REPORT.md"):
        assert (target / "fresh" / name).read_bytes() == (FIXTURE / "golden" / name).read_bytes()
    golden_md = (FIXTURE / "golden" / "SPEC_CONFORMANCE_REPORT.md").read_text(encoding="utf-8")
    assert run.stdout.strip() in golden_md
    assert "foreign" not in json.loads((target / "fresh" / "speccheck.json").read_text())
