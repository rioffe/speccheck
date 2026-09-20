"""§9.2 Citation and attribution (C-03)."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from speccheck.attribute import attribute_file, module_classname
from speccheck.extract import ScannedFile

from .conftest import DATA, SIMPLE_PROJECT, junit, spec_table


def _scanned(path: str, text: str) -> ScannedFile:
    return ScannedFile(path, text, tuple(text.split("\n")))


def _src_lines(run, ident: str) -> list[tuple[str, int]]:
    return [(s["file"], ln) for s in run.ids()[ident]["src"] for ln in s["lines"]]


def test_source_citations_in_code_comments_and_strings(project):
    """T-08: source citations are recorded per (file, line) for tokens in code, comments, and
    strings alike. (R-03)"""
    src = 'R_01 = "R-01"  # code-ish string\n# a comment citing R-01 and C-01\nx = """\nC-01 inside a docstring\n"""\n'
    run = project({"SPEC.md": spec_table([("R-01", "a"), ("C-01", "b")]), "src/m.py": src}).check()
    assert _src_lines(run, "R-01") == [("src/m.py", 1), ("src/m.py", 2)]
    assert _src_lines(run, "C-01") == [("src/m.py", 2), ("src/m.py", 4)]


def test_python_test_citations_attributed_to_enclosing_case(project):
    """T-09: citations inside `def test_*` and `class Test*` methods are attributed to the
    enclosing case with the correct classname, start, end. (R-04)"""
    text = (
        "import unittest\n\n\n"
        "@some.decorator\n"
        "def test_alpha():\n    '''R-01'''\n    assert True\n\n\n"
        "class TestBeta:\n    def test_beta(self):\n        # C-01\n        assert True\n\n"
        "    def helper(self):\n        pass  # K-01 belongs to the file\n"
    )
    attributed, notes = attribute_file(_scanned("tests/unit/test_x.py", text))
    assert notes == []
    cases = {c.name: c for c in attributed.cases}
    assert (cases["test_alpha"].classname, cases["test_alpha"].start, cases["test_alpha"].end) == (
        "tests.unit.test_x",
        4,
        7,
    )
    assert (cases["test_beta"].classname, cases["test_beta"].start, cases["test_beta"].end) == (
        "tests.unit.test_x.TestBeta",
        11,
        13,
    )
    owners = {(c.id, c.line): c.testcase.name for c in attributed.citations}
    assert owners == {("R-01", 6): "test_alpha", ("C-01", 12): "test_beta", ("K-01", 16): ""}
    run = project(
        {
            "SPEC.md": spec_table([("R-01", "a"), ("C-01", "b"), ("K-01", "c")]),
            "tests/unit/test_x.py": text,
        }
    ).check()
    beta = run.ids()["C-01"]["tests"][0]
    assert (beta["file"], beta["name"], beta["classname"], beta["lines"]) == (
        "tests/unit/test_x.py",
        "test_beta",
        "tests.unit.test_x.TestBeta",
        [12],
    )


def test_module_docstring_and_helper_citations_are_file_level(project):
    """T-10: a citation in a module docstring or helper is attributed to the file-level case and
    reported with name `(file)`. (E-13)"""
    text = '"""Module docstring cites R-01."""\n\n\ndef helper():\n    return 1  # C-01\n\n\ndef test_a():\n    assert helper() == 1\n'
    run = project(
        {"SPEC.md": spec_table([("R-01", "a"), ("C-01", "b")]), "tests/test_m.py": text}
    ).check()
    for ident in ("R-01", "C-01"):
        (edge,) = run.ids()[ident]["tests"]
        assert (
            edge["name"] == "" and edge["outcome"] is None and edge["classname"] == "tests.test_m"
        )
        assert run.status(ident) == "UNVERIFIED"
    assert "| `(file)` tests/test_m.py:1 (unrun · —) |" in run.md
    assert "| R-01 | tests/test_m.py | (file) |" in run.md


def test_unparseable_python_falls_back_to_file_level_with_note(project):
    """T-11: an unparseable .py test file falls back to one file-level case and produces a Note. (E-12)"""
    text = "def test_broken(:\n    # R-01\n    pass\n"
    attributed, notes = attribute_file(_scanned("tests/test_bad.py", text))
    assert notes == ["parse fallback: tests/test_bad.py"]
    assert attributed.cases == ()
    assert attributed.citations[0].testcase.name == ""
    run = project({"SPEC.md": spec_table([("R-01", "a")]), "tests/test_bad.py": text}).check()
    assert run.json["notes"] == ["parse fallback: tests/test_bad.py"]
    assert run.ids()["R-01"]["tests"][0]["name"] == ""


def test_non_python_test_files_get_file_level_attribution(project):
    """T-12: a non-Python test file (.go, .ts) gets file-level attribution. (R-04, O-2)"""
    go = "package calc\n\nfunc TestAdd(t *testing.T) {\n\t// R-01\n}\n"
    ts = "test('adds', () => { /* C-01 */ });\n"
    run = project(
        {
            "SPEC.md": spec_table([("R-01", "a"), ("C-01", "b")]),
            "tests/core_test.go": go,
            "tests/core.test.ts": ts,
        }
    ).check()
    go_edge = run.ids()["R-01"]["tests"][0]
    ts_edge = run.ids()["C-01"]["tests"][0]
    assert (go_edge["file"], go_edge["name"], go_edge["classname"], go_edge["lines"]) == (
        "tests/core_test.go",
        "",
        "tests.core_test",
        [4],
    )
    assert (ts_edge["file"], ts_edge["name"], ts_edge["classname"]) == (
        "tests/core.test.ts",
        "",
        "tests.core.test",
    )
    assert module_classname("tests/core_test.go") == "tests.core_test"
    assert module_classname("tests/noext") == "tests.noext"


def test_excluded_dirs_oversized_nonutf8_binary_and_symlinks(project):
    """T-13: excluded directories (K-03), oversized / non-UTF-8 / binary files (K-02), and symlinks
    are skipped or decoded exactly as specified; a symlink cycle terminates.
    (K-02, K-03, E-10, E-11, E-29, E-30)"""
    files = {
        "SPEC.md": spec_table([("R-01", "a"), ("C-01", "b"), ("K-01", "c"), ("E-01", "d")]),
        "src/ok.py": "# R-01\n",
        "src/.git/hidden.py": "# C-01\n",
        "src/.hiddendir/x.py": "# C-01\n",
        "src/node_modules/x.js": "// C-01\n",
        "src/__pycache__/x.py": "# C-01\n",
        "src/.venv/x.py": "# C-01\n",
        "src/venv/x.py": "# C-01\n",
        "src/.hg/x": "C-01\n",
        "src/.svn/x": "C-01\n",
        "src/big.txt": ("# K-01\n" * 1000 + "x" * (2 * 1024 * 1024)).encode("utf-8"),
        "src/latin1.py": b"# K-01 caf\xe9\n",
        "src/blob.bin": b"E-01\x00binary\n",
        "src/late_nul.txt": b"E-01 text\n" + b"a" * 9000 + b"\x00",
    }
    proj = project(files)
    os.symlink(proj.path / "src" / "ok.py", proj.path / "src" / "link.py")
    os.symlink(proj.path / "src", proj.path / "src" / "cycle")
    (proj.path / "src" / "sub").mkdir()
    os.symlink(proj.path / "src" / "sub", proj.path / "src" / "sub" / "loop")
    run = proj.check()
    assert run.code in (0, 1)
    assert _src_lines(run, "R-01") == [("src/ok.py", 1)]
    # K-03: every C-01 citation was planted inside a never-descended directory (.git, .hg, .svn,
    # node_modules, __pycache__, .venv, venv, and a dot-directory), so C-01 is UNCITED and no
    # path from any of those directories appears anywhere in the report, while their sibling
    # src/ok.py was scanned.
    assert run.status("C-01") == "UNCITED" and _src_lines(run, "C-01") == []
    excluded = (".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", ".hiddendir")
    cited_paths = {s["file"] for rec in run.json["ids"] for s in rec["src"]}
    cited_paths |= {d["file"] for d in run.json["dangling"] + run.json["stale"]}
    assert cited_paths and not any(f"src/{d}/" in path for d in excluded for path in cited_paths)
    assert not any(f"/{d}/" in json.dumps(run.json) for d in excluded)
    assert _src_lines(run, "K-01") == [("src/latin1.py", 1)]
    assert _src_lines(run, "E-01") == [("src/late_nul.txt", 1)]
    # E-29: src/blob.bin has a 0x00 byte within its first 8192 bytes -> skipped silently: it
    # yields no citation anywhere in the report, no test case, and no Note; src/late_nul.txt,
    # whose only NUL is past byte 8192, is text and its citation above was kept.
    raw = json.dumps(run.json)
    assert "blob.bin" not in raw
    assert run.json["notes"] == [
        "invalid UTF-8 decoded with replacement: src/latin1.py",
        "skipped 1 file over 2 MiB: src/big.txt",
        "skipped 3 symlink(s)",
    ]


def test_class_recognition_and_async_and_undelimited(project):
    """T-56: test_* and testFoo methods of *TestCase subclasses, testFoo methods of Test* classes,
    and async def test_* functions are delimited; a module-level testFoo is not a test case; a
    test* method of an unrecognized class is not, its citations are file-level, and the file gets
    an `undelimited tests` Note. (E-28, C-03)"""
    text = (
        "import unittest\n\n\n"
        "class CalcCase(unittest.TestCase):\n"
        "    def test_one(self):\n        assert True  # R-01\n"
        "    def testTwo(self):\n        assert True  # R-02\n\n\n"
        "class TestThree:\n"
        "    def testThree(self):\n        assert True  # R-03\n\n"
        "    class Inner:\n        def test_nested(self):\n            pass  # R-04\n\n\n"
        "async def test_four():\n    assert True  # R-05\n\n\n"
        "def testFive():\n    assert True  # R-06\n\n\n"
        "class Plain:\n    def test_six(self):\n        pass  # R-07\n"
    )
    attributed, notes = attribute_file(_scanned("tests/test_c.py", text))
    spans = {c.name: (c.classname, c.start, c.end) for c in attributed.cases}
    assert spans == {
        "test_one": ("tests.test_c.CalcCase", 5, 6),
        "testTwo": ("tests.test_c.CalcCase", 7, 8),
        "testThree": ("tests.test_c.TestThree", 12, 13),
        "test_four": ("tests.test_c", 20, 21),
    }
    owners = {c.id: c.testcase.name for c in attributed.citations}
    assert owners == {
        "R-01": "test_one",
        "R-02": "testTwo",
        "R-03": "testThree",
        "R-04": "",
        "R-05": "test_four",
        "R-06": "",
        "R-07": "",
    }
    assert notes == [
        "undelimited tests in tests/test_c.py: TestThree.Inner.test_nested, Plain.test_six"
    ]
    attributed2, _ = attribute_file(
        _scanned(
            "tests/test_d.py",
            "from x import Base\nclass C(x.FooTestCase):\n    def testIt(self):\n        pass  # R-01\n",
        )
    )
    assert [c.name for c in attributed2.cases] == ["testIt"]


def test_ignore_markers(project, tmp_path: Path):
    """T-57: a line carrying the line-ignore marker yields no citations but still counts toward
    its case's span; a file with the file-ignore marker on line 2 yields nothing; a marker on
    line 4 has no file-level effect; markers inside SPEC.md change nothing; the Note counts
    ignored files. The marker strings live only in tests/data/markers/ (F-109). (R-27, E-33)"""
    markers = DATA / "markers"
    proj = project({"src/keep.py": "# R-01\n"})
    tests_dir = proj.path / "tests"
    tests_dir.mkdir()
    for name in ("ignore_line.py", "ignore_file_line2.py", "marker_on_line4.py"):
        shutil.copy(markers / name, tests_dir / f"test_{name}")
    shutil.copy(markers / "spec_with_markers.md", proj.path / "SPEC.md")
    run = proj.check()
    ids = run.ids()
    assert set(ids) == {"R-01", "C-01"}  # markers inside SPEC.md changed nothing
    r01_tests = {(t["file"], t["name"], tuple(t["lines"])) for t in ids["R-01"]["tests"]}
    assert r01_tests == {
        ("tests/test_ignore_line.py", "test_marker", (7,)),  # line 6 ignored, line 7 kept
        ("tests/test_marker_on_line4.py", "test_scanned", (6,)),
    }
    (c01_edge,) = ids["C-01"]["tests"]
    assert c01_edge["name"] == "test_marker" and c01_edge["lines"] == [5]
    assert not any(
        t["file"].endswith("test_ignore_file_line2.py") for i in ids.values() for t in i["tests"]
    )
    # the marker text is assembled so that it never appears literally in this module (F-109)
    assert run.json["notes"] == ["ignored 1 file(s) by " + "speccheck:" + "ignore-file"]
    # the ignored line still counts toward the span: the mock judge sees lines 4..7 of the case
    run2 = proj.check("--judge", "mock")
    assert run2.code in (0, 1)


def test_several_citations_in_one_case_yield_one_edge(project):
    """T-14: several citations of one ID in one case yield one edge with all lines listed. (E-22)"""
    text = "def test_a():\n    '''R-01'''\n    x = 1  # R-01\n    assert x  # R-01 again\n"
    files = dict(SIMPLE_PROJECT)
    files["tests/test_calc.py"] = text
    run = project(files).check(results=False)
    (edge,) = run.ids()["R-01"]["tests"]
    assert edge["name"] == "test_a" and edge["lines"] == [2, 3, 4]


SWIFT_TESTING_FILE = "\n".join(
    [
        "import Testing",  # 1
        "@testable import Probe",  # 2: `@testable` is not `@Test`
        "",  # 3
        "/// R-01 free function",  # 4
        "@Test func freeFunction() {",  # 5
        "    #expect(add(1, 1) == 2)",  # 6
        "}",  # 7
        "",  # 8
        '@Suite("Outer suite")',  # 9
        "struct Outer {",  # 10
        "    /// C-01 named",  # 11
        '    @Test("named test") func named() {',  # 12
        "        #expect(add(2, 2) == 4)  // K-01 in the body",  # 13
        "    }",  # 14
        "",  # 15
        "    @Test(arguments: [",  # 16
        "        1, 2, 3])  // E-01 on an attribute continuation line",  # 17
        "    func parameterized(x: Int) {",  # 18
        "        #expect(add(x, 0) == x)",  # 19
        "    }",  # 20
        "",  # 21
        "    @Suite struct Inner {",  # 22
        "        /** T-01",  # 23
        "            block doc comment */",  # 24
        "        @Test",  # 25
        "        func nested() throws {",  # 26
        "            try #require(add(0, 0) == 0)",  # 27
        "        }",  # 28
        "    }",  # 29
        "",  # 30
        "    func helper() {",  # 31
        "        // I-001 belongs to the file",  # 32
        "    }",  # 33
        "",  # 34
        "    func testHelper() {}  // E-02 undelimited: no @Test, not an XCTestCase",  # 35
        "}",  # 36
    ]
)


def test_swift_testing_cases_are_delimited_with_doc_comment_spans(project):
    """T-65: Swift Testing `@Test` functions at file scope, in a `@Suite`, with a multi-line
    attribute and in a nested suite are cases named by identifier with classnames `<Module>`,
    `<Module>.Outer`, `<Module>.Outer.Inner`; spans start on the first doc-comment line and end
    on the closing brace; doc-comment, attribute-continuation and body citations belong to the
    case; the helper's citation is file-level; `testHelper` is undelimited; `@testable` is not
    `@Test`; MODULE is the first path component under the tests root. (R-31, C-03, E-43)"""
    scanned = ScannedFile(
        "Tests/ProbeTests/Cases.swift",
        SWIFT_TESTING_FILE,
        tuple(SWIFT_TESTING_FILE.split("\n")),
        "Tests",
    )
    attributed, notes = attribute_file(scanned)
    assert notes == ["undelimited tests in Tests/ProbeTests/Cases.swift: Outer.testHelper"]
    spans = {c.name: (c.classname, c.start, c.end) for c in attributed.cases}
    assert spans == {
        "freeFunction": ("ProbeTests", 4, 7),
        "named": ("ProbeTests.Outer", 11, 14),
        "parameterized": ("ProbeTests.Outer", 16, 20),
        "nested": ("ProbeTests.Outer.Inner", 23, 28),
    }
    owners = {(c.id, c.line): c.testcase.name for c in attributed.citations}
    assert owners == {
        ("R-01", 4): "freeFunction",
        ("C-01", 11): "named",
        ("K-01", 13): "named",
        ("E-01", 17): "parameterized",
        ("T-01", 23): "nested",
        ("I-001", 32): "",
        ("E-02", 35): "",
    }
    # MODULE for a file directly under the tests root is the root's own name.
    direct = ScannedFile("tests/Cases.swift", SWIFT_TESTING_FILE, scanned.lines, "tests")
    assert {c.classname for c in attribute_file(direct)[0].cases} == {
        "tests",
        "tests.Outer",
        "tests.Outer.Inner",
    }
    # End to end: the citations reach the report attributed, and join SwiftPM-shaped results.
    run = project(
        {
            "SPEC.md": spec_table([("R-01", "a"), ("C-01", "b"), ("T-01", "c"), ("I-001", "d")]),
            "tests/ProbeTests/Cases.swift": SWIFT_TESTING_FILE,
            "junit.xml": junit(
                [
                    ("ProbeTests", "freeFunction()", "passed"),
                    ("ProbeTests.Outer", "named()", "passed"),
                    ("ProbeTests.Outer", "parameterized(x:)", "passed"),
                    ("ProbeTests.Outer.Inner", "nested()", "passed"),
                ]
            ),
        }
    ).check()
    ids = run.ids()
    assert ids["R-01"]["status"] == "PASSING"
    assert ids["C-01"]["status"] == "PASSING"
    assert ids["T-01"]["status"] == "PASSING"
    assert ids["I-001"]["status"] == "UNVERIFIED"  # file-level helper citation
    edge = ids["T-01"]["tests"][0]
    assert (edge["name"], edge["classname"], edge["lines"]) == (
        "nested",
        "ProbeTests.Outer.Inner",
        [23],
    )


XCTEST_FILE = "\n".join(
    [
        "import XCTest",  # 1
        "@testable import Probe",  # 2
        "",  # 3
        "final class LegacyTests: XCTestCase {",  # 4
        "    /// R-01",  # 5
        "    func testAddition() {",  # 6
        "        XCTAssertEqual(Probe.add(1, 2), 3)",  # 7
        "    }",  # 8
        "    func helper() {}",  # 9
        "    class Nested {",  # 10
        "        func testNested() {}  // C-01 undelimited",  # 11
        "    }",  # 12
        "}",  # 13
        "",  # 14
        "class Plain {",  # 15
        "    func testFoo() {}  // K-01 undelimited",  # 16
        "}",  # 17
    ]
)


def test_xctest_methods_are_delimited_and_others_undelimited():
    """T-66: a `test*` method directly inside an `XCTestCase` class is a case named by identifier
    with classname `<Module>.LegacyTests` and a doc-comment-to-brace span; a `test*` method of a
    nested class or of a non-`XCTestCase` class is undelimited with one Note; `helper` produces
    no Note. (R-31, C-03, E-43)"""
    scanned = ScannedFile(
        "Tests/ProbeTests/Legacy.swift", XCTEST_FILE, tuple(XCTEST_FILE.split("\n")), "Tests"
    )
    attributed, notes = attribute_file(scanned)
    assert notes == [
        "undelimited tests in Tests/ProbeTests/Legacy.swift: LegacyTests.Nested.testNested, Plain.testFoo"
    ]
    assert [(c.name, c.classname, c.start, c.end) for c in attributed.cases] == [
        ("testAddition", "ProbeTests.LegacyTests", 5, 8)
    ]
    owners = {(c.id, c.line): c.testcase.name for c in attributed.citations}
    assert owners == {("R-01", 5): "testAddition", ("C-01", 11): "", ("K-01", 16): ""}


def test_swift_brace_fallback_and_braces_in_strings_and_comments():
    """T-67: an unclosed `{` or a stray `}` makes the file one file-level case with a
    `parse fallback` Note; braces inside string literals and `//` comments do not count, so a
    file whose only extra braces are quoted delimits correctly. (E-42, C-03)"""
    unclosed = "/// R-01\n@Test func a() {\n    #expect(true)  // R-02\n"  # depth 1 at EOF
    stray = "/// R-01\n@Test func a() {\n}\n}  // R-02\n"  # depth goes negative on line 4
    for text in (unclosed, stray):
        scanned = ScannedFile("Tests/M/F.swift", text, tuple(text.split("\n")), "Tests")
        attributed, notes = attribute_file(scanned)
        # E-42: the whole file is ONE file-level case (name "", span = the file) with the Note;
        # no @Test case is delimited, and every citation belongs to that file-level case
        assert notes == ["parse fallback: Tests/M/F.swift"]
        assert attributed.cases == ()
        assert attributed.file_case.name == "" and attributed.file_case.start == 1
        assert attributed.file_case.end == len(text.split("\n"))
        assert {(c.id, c.line, c.testcase.name) for c in attributed.citations} == {
            ("R-01", 1, ""),
            ("R-02", 3 if text is unclosed else 4, ""),
        }
    quoted = "\n".join(
        [
            "/// R-01",
            "@Test func a() {",
            '    let open = "{"',
            '    let multi = """',
            "        } } {",
            '        """',
            "    // }",
            '    #expect(open == "{")  // R-02',
            "}",
            "/// R-03",
            "@Test func b() { #expect(true) }",
        ]
    )
    scanned = ScannedFile("Tests/M/F.swift", quoted, tuple(quoted.split("\n")), "Tests")
    attributed, notes = attribute_file(scanned)
    assert notes == []
    assert [(c.name, c.start, c.end) for c in attributed.cases] == [("a", 1, 9), ("b", 10, 11)]
    owners = {(c.id, c.line): c.testcase.name for c in attributed.citations}
    assert owners == {("R-01", 1): "a", ("R-02", 8): "a", ("R-03", 10): "b"}


PY_DECLARED = "\n".join(
    [
        '"""Module docstring citing R-09 (a file-level citation, E-56)."""',
        "",
        "",
        "def test_case():",
        '    """T-85: DECLARED on the first docstring line (R-01) and',
        '    on the second docstring line (R-02)."""',
        "    # whole-line comment citing R-03",
        '    value = "R-04 in a string literal"',
        "    assert value  # R-05 trailing comment",
        "",
    ]
)

SWIFT_DECLARED = "\n".join(
    [
        "import Testing",
        "",
        "/// T-85: doc-comment line naming R-01.",
        "/** R-02 inside a doc block opened and closed on this line. */",
        "@Test func declaredCase() {",
        '    #expect("R-03" == "R-04")  // R-04 trailing',
        "}",
        "",
    ]
)


def test_declared_vs_incidental_classification():
    """T-85: DECLARED/INCIDENTAL classification (C-14): a citation on the case's own docstring
    line and one on a whole-line `#` comment are DECLARED; a citation inside a string literal and
    one on a code line with a trailing comment (`x = 1  # R-02`) are INCIDENTAL; a citation
    attributed to the file-level fallback case is INCIDENTAL with no Note (E-56); a multi-line
    docstring whose citation is on its second line is DECLARED; the Swift adapter's doc-comment
    recognition (`///`, `/** … */`) classifies an equivalent Swift example the same way. (R-39,
    C-03, C-14, E-56, I-014)"""
    attributed, notes = attribute_file(_scanned("tests/test_d.py", PY_DECLARED))
    flags = {(c.id, c.line): c.declared for c in attributed.citations}
    assert flags[("R-01", 5)] is True  # first docstring line
    assert flags[("R-02", 6)] is True  # second line of a multi-line docstring
    assert flags[("R-03", 7)] is True  # whole-line `#` comment
    assert flags[("R-04", 8)] is False  # inside a string literal
    assert flags[("R-05", 9)] is False  # code line with a trailing comment
    assert flags[("R-09", 1)] is False  # file-level case (E-56)
    assert notes == []  # E-56 is definitional, not an anomaly
    swift, swift_notes = attribute_file(_scanned("tests/CalcTests.swift", SWIFT_DECLARED))
    sflags = {(c.id, c.line): c.declared for c in swift.citations}
    assert sflags[("R-01", 3)] is True  # `///` doc-comment line
    assert sflags[("R-02", 4)] is True  # `/** ... */` line
    assert sflags[("R-03", 6)] is False and sflags[("R-04", 6)] is False  # body line
    assert swift_notes == []



