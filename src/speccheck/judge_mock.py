"""Mock judge provider (C-06, R-22): deterministic, configuration-free, no I/O.

Spec IDs realized here (§11): R-10, R-22, C-06.
"""

from __future__ import annotations

import logging
import re

from .judge import Evidence, JudgeRequest, Verdict

log = logging.getLogger("speccheck")

_ASSERT_STMT = re.compile(r"^\s*assert\b")


_SWIFT_TOKENS = ("#expect(", "#require(", "XCTAssert", "XCTFail(", "Issue.record(")


def is_assertion_line(text: str) -> bool:
    """assertion token := a line matching ^\\s*assert\\b, or containing .assert or pytest.raises(,
    or (Swift, R-31) containing #expect( / #require( / XCTAssert / XCTFail( / Issue.record("""
    if _ASSERT_STMT.match(text) or ".assert" in text or "pytest.raises(" in text:
        return True
    return any(token in text for token in _SWIFT_TOKENS)


class MockJudge:
    def judge(self, req: JudgeRequest) -> Verdict:
        evidence: list[Evidence] = []
        for row in req.source.split("\n"):
            if not row:
                continue
            lineno_text, _tab, text = row.partition("\t")
            if is_assertion_line(text):
                evidence.append(Evidence(req.testcase.file, int(lineno_text)))
        if evidence:
            verdict = Verdict(
                "ASSERTS", tuple(evidence), f"mock: assertion token on {len(evidence)} line(s)"
            )
        else:
            verdict = Verdict("EXECUTES_ONLY", (), "mock: no assertion token")
        log.debug(
            "judge< %s",
            {
                "verdict": verdict.verdict,
                "evidence": [e.__dict__ for e in verdict.evidence],
                "rationale": verdict.rationale,
            },
        )
        return verdict
