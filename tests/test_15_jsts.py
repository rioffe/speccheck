"""§9.16 JavaScript / TypeScript adapter (R-104, C-03, C-04; v1.22)."""

from __future__ import annotations

import pytest

from speccheck.attribute import attribute_file
from speccheck.extract import ScannedFile
from speccheck.jsts import JsParseError, delimit_js

from .conftest import spec_table

SOURCE = """import { describe, it, test, expect } from 'vitest'
describe('calc', () => {
  /** R-01 */
  it('adds', () => { expect(1 + 1).toBe(2) })
  describe('inner (x)', () => {
    test('subtracts [neg]', () => { // R-02
      expect(2 - 1).toBe(1)
    })
  })
  it.each([[1, 2], [3, 4]])('sums %i and %i', (a, b) => { expect(a + b).toBeGreaterThan(0) /* R-03 */ })
  it.skip('skipped one', () => {})
})
// R-05
test('top level', () => { expect(/a)b/.test('a)b')).toBe(true) })
"""

# measured 2026-10-27 with vitest 2.1.8: `vitest run --reporter=junit` over SOURCE
VITEST_JUNIT = """<?xml version="1.0" encoding="UTF-8" ?>
<testsuites name="vitest tests" tests="6" failures="0" errors="0" time="0.326">
    <testsuite name="src/calc.test.ts" tests="6" failures="0" errors="0" skipped="1">
        <testcase classname="src/calc.test.ts" name="calc &gt; adds" time="0.0004"></testcase>
        <testcase classname="src/calc.test.ts" name="calc &gt; inner (x) &gt; subtracts [neg]" time="0.0001"></testcase>
        <testcase classname="src/calc.test.ts" name="calc &gt; sums 1 and 2" time="0.0001"></testcase>
        <testcase classname="src/calc.test.ts" name="calc &gt; sums 3 and 4" time="0.0001"></testcase>
        <testcase classname="src/calc.test.ts" name="calc &gt; skipped one" time="0"><skipped/></testcase>
        <testcase classname="src/calc.test.ts" name="top level" time="0.0001"></testcase>
    </testsuite>
</testsuites>
"""


def test_delimits_describe_chains_modifiers_and_regex_literals():
    """T-113: `describe` titles and the test title join with " > "; `.each`, `.skip` and nested
    suites delimit; a regex literal holding `)` does not unbalance the span; the comment block
    above a call is inside its span, and only whole-line comments are flagged. (R-104, C-03)"""
    cases, undelimited, comment_only = delimit_js(tuple(SOURCE.split("\n")))
    assert [(c.name, c.start, c.end) for c in cases] == [
        ("calc > adds", 3, 4),
        ("calc > inner (x) > subtracts [neg]", 6, 8),
        ("calc > sums %i and %i", 10, 10),
        ("calc > skipped one", 11, 11),
        ("top level", 13, 14),
    ]
    assert undelimited == []
    assert comment_only[2] and comment_only[12] and not comment_only[5] and not comment_only[3]


def test_dynamic_titles_member_calls_and_unbalanced_files():
    """T-114: a non-literal title is reported as `line N` and is not a case; `re.test(x)` is not a
    test call; an unbalanced file raises JsParseError (the parse fallback, E-74). (E-74, E-75)"""
    src = "const t = 'x'\nit(t, () => {})\nit(`a ${t}`, () => {})\nre.test('x')\ntest('ok', () => {})\n"
    cases, undelimited, _ = delimit_js(tuple(src.split("\n")))
    assert [c.name for c in cases] == ["ok"]
    assert undelimited == ["line 2", "line 3"]
    with pytest.raises(JsParseError):
        delimit_js(("test('a', () => {",))


def test_attribution_declared_and_classname():
    """T-115: a citation inside a case's span is attributed to it, the classname is the file path
    with `/` -> `.` and the extension kept, a comment-only line is DECLARED and a code line is
    not, and a citation outside any case is file-level. (R-104, C-03, C-14)"""
    scanned = ScannedFile("web/src/calc.test.ts", SOURCE, tuple(SOURCE.split("\n")), "web")
    attributed, notes = attribute_file(scanned)
    assert notes == []
    by_id = {c.id: c for c in attributed.citations}
    assert by_id["R-01"].testcase.name == "calc > adds" and by_id["R-01"].declared
    assert by_id["R-02"].testcase.name == "calc > inner (x) > subtracts [neg]"
    assert not by_id["R-02"].declared  # a trailing comment on a code line (C-14)
    assert by_id["R-02"].testcase.classname == "web.src.calc.test.ts"
    assert by_id["R-05"].testcase.name == "top level" and by_id["R-05"].declared


def test_joins_vitest_junit_end_to_end(project):
    """T-116: the measured vitest JUnit joins by path classname (vitest's root differs from
    --root), titles containing `[` and `(`, and a templated `it.each` title that expands to two
    results; the skipped case is SKIPPED. (R-104, C-04, E-76)"""
    spec = spec_table(
        [("R-01", "adds"), ("R-02", "subtracts"), ("R-03", "sums"), ("R-04", "skipped"), ("R-05", "top")]
    )
    tests = SOURCE.replace("it.skip('skipped one', () => {})", "it.skip('skipped one', () => {}) // R-04")
    run = project(
        {"SPEC.md": spec, "web/src/calc.test.ts": tests, "junit.xml": VITEST_JUNIT}
    ).check("--tests", "web/src", "--results", "junit.xml")
    statuses = {i: run.status(i) for i in ("R-01", "R-02", "R-03", "R-04", "R-05")}
    assert statuses == {
        "R-01": "PASSING",
        "R-02": "PASSING",
        "R-03": "PASSING",
        "R-04": "SKIPPED",
        "R-05": "PASSING",
    }
    assert run.json["unattributed_results"] == []
    each = run.ids()["R-03"]["tests"][0]
    assert each["name"] == "calc > sums %i and %i" and each["outcome"] == "passed"
