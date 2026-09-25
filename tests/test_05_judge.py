"""§9.5 Judge contract (C-06)."""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
import time
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from speccheck import cli, jev, judge_llm
from speccheck.attribute import TestCase as SpecTestCase
from speccheck.extract import SpecId
from speccheck.graph import Graph, IdRecord, apply_verdicts, eligible_edges
from speccheck.graph import TestEdge as Edge
from speccheck.judge import (
    VERDICTS,
    Evidence,
    JudgedVerdict,
    JudgeHttpError,
    JudgeMalformed,
    JudgeRequest,
    JudgeTimeout,
    Verdict,
    build_request,
    clean_rationale,
    judge_edge,
    run_judge,
    validate,
)
from speccheck.judge_llm import LlmConfig, LlmJudge, parse_answer, strip_fence
from speccheck.judge_mock import MockJudge

from .conftest import FIXTURE, junit, run_cli, spec_table, write_tree

C10_PATH = Path(__file__).resolve().parent.parent / "src" / "speccheck" / "judge_prompt.md"
LLM_ENV = {
    "SPECCHECK_JUDGE_URL": "http://localhost:11434/v1/chat/completions",
    "SPECCHECK_JUDGE_MODEL": "m",
    "SPECCHECK_JUDGE_API_KEY": "sk-secret-key",
}
JEV_ENV = {
    **LLM_ENV,
    "SPECCHECK_JEV_URL": "http://localhost:9/decisions",
    "SPECCHECK_JEV_MODEL": "~typesafe/jev-latest",
    "SPECCHECK_JEV_API_KEY": "sk-jev",
}


def _req(
    source_lines: list[str], start: int = 1, file: str = "tests/test_a.py", name: str = "test_a"
) -> JudgeRequest:
    case = SpecTestCase(file, name, "tests.test_a", start, start + len(source_lines) - 1)
    padded = [""] * (start - 1) + source_lines
    return build_request("R-01", "the statement", case, padded)


def _ok(verdict: str, evidence=(), rationale: str = "r", clause: str = "the statement") -> Verdict:
    """A stub Verdict; the default clause is `_req`'s whole statement, so it is LOCATED (K-15)."""
    return Verdict(verdict, clause, tuple(evidence), rationale)


class StubProvider:
    """Returns canned Verdicts (or raises) and counts calls."""

    def __init__(self, answer):
        self.answer = answer
        self.calls: list[JudgeRequest] = []

    def judge(self, req: JudgeRequest) -> Verdict:
        self.calls.append(req)
        if isinstance(self.answer, BaseException):
            raise self.answer
        if callable(self.answer):
            return self.answer(req)
        return self.answer


def test_mock_judge_recognizes_swift_assertion_tokens():
    """T-69: the mock returns ASSERTS with the line as evidence for a Swift span containing
    `#expect(`, `#require(`, `XCTAssertEqual(`, `XCTFail(` or `Issue.record(` (one sub-test
    each), and EXECUTES_ONLY for a Swift body that only calls code. (R-22, C-06)"""
    mock = MockJudge()
    for token in (
        "#expect(add(1, 1) == 2)",
        "let v = try #require(maybe())",
        "XCTAssertEqual(add(1, 2), 3)",
        'XCTFail("unreachable")',
        'Issue.record("bad state")',
    ):
        verdict = mock.judge(_req(["@Test func t() {", "    " + token, "}"], start=5))
        assert verdict.verdict == "ASSERTS", token
        assert [e.line for e in verdict.evidence] == [6], token
        assert verdict.rationale == "mock: assertion token on 1 line(s)"
    executes = mock.judge(
        _req(["@Test func t() {", "    _ = add(1, 2)", "    // #expectation", "}"])
    )
    assert (executes.verdict, executes.evidence, executes.rationale) == (
        "EXECUTES_ONLY",
        (),
        "mock: no assertion token",
    )


def test_mock_judge_asserts_on_assertion_tokens_else_executes_only():
    """T-26: the mock returns ASSERTS with one evidence line per assertion token, and
    EXECUTES_ONLY with no evidence otherwise, including for an empty body — one verdict from the
    R-10 set per edge, with evidence per C-06. (R-10, R-22, E-17)"""
    mock = MockJudge()
    req = _req(
        [
            "def test_a():",
            "    assert x == 1",
            "    self.assertEqual(1, 1)",
            "    with pytest.raises(ValueError):",
            "        pass  # assert in a comment",
        ],
        start=10,
    )
    verdict = mock.judge(req)
    assert verdict.verdict == "ASSERTS"
    assert [e.line for e in verdict.evidence] == [11, 12, 13]
    assert verdict.rationale == "mock: assertion token on 3 line(s)"
    empty = mock.judge(_req(["def test_a():", "    pass"]))
    assert (empty.verdict, empty.evidence, empty.rationale) == (
        "EXECUTES_ONLY",
        (),
        "mock: no assertion token",
    )
    nothing = mock.judge(_req(["def test_a(): ..."]))
    assert nothing.verdict == "EXECUTES_ONLY"
    judged = judge_edge(mock, empty_req := _req(["def test_a():", "    pass"]))
    assert judged.verdict == "EXECUTES_ONLY" and judged.coerced is False and empty_req.id == "R-01"


def _graph_with_edges(verdict_names: list[str | None]) -> tuple[Graph, dict]:
    spec = SpecId("R", 1, "s", "s", 1, False)
    edges = []
    verdicts = {}
    for i, name in enumerate(verdict_names):
        case = SpecTestCase("tests/test_a.py", f"test_{i}", "tests.test_a", 1 + 3 * i, 3 + 3 * i)
        edges.append(Edge(case, [2 + 3 * i], "passed", []))
        if name is not None:
            verdicts[(case, "R-01")] = JudgedVerdict(name, "s", (), "r", name == "UNKNOWN")
    rec = IdRecord(spec, "PASSING", [], edges)
    return Graph([rec], [], []), verdicts


def test_step_5_downgrade_rules(tmp_path: Path):
    """T-27: a PASSING ID whose only passed edges are EXECUTES_ONLY becomes WEAKLY_PASSING; with
    any ASSERTS edge it stays PASSING and passes --strict; with only UNKNOWN it stays PASSING.
    (C-05 step 5, R-11, E-26)"""
    for names, expected in [
        (["EXECUTES_ONLY"], "WEAKLY_PASSING"),
        (["UNRELATED", "EXECUTES_ONLY"], "WEAKLY_PASSING"),
        (["ASSERTS", "EXECUTES_ONLY"], "PASSING"),
        (["UNKNOWN"], "PASSING"),
        (["UNKNOWN", "EXECUTES_ONLY"], "WEAKLY_PASSING"),
        ([], "PASSING"),
    ]:
        graph, verdicts = _graph_with_edges(names)
        apply_verdicts(graph, verdicts)
        assert graph.records[0].status == expected, names
    # E-26 end to end: mixed ASSERTS / EXECUTES_ONLY passes --strict
    files = {
        "SPEC.md": spec_table([("R-01", "a")]),
        "tests/test_a.py": "def test_strong():\n    '''R-01'''\n    assert True\n\n\ndef test_weak():\n    '''R-01'''\n    pass\n",
        "junit.xml": junit(
            [("tests.test_a", "test_strong", "passed"), ("tests.test_a", "test_weak", "passed")]
        ),
    }
    write_tree(tmp_path, files)
    run = run_cli(
        [
            "check",
            "--spec",
            "SPEC.md",
            "--tests",
            "tests",
            "--results",
            "junit.xml",
            "--judge",
            "mock",
            "--strict",
        ],
        tmp_path,
    )
    assert run.code == 0 and run.status("R-01") == "PASSING"
    assert [t["verdict"]["verdict"] for t in run.ids()["R-01"]["tests"]] == [
        "ASSERTS",
        "EXECUTES_ONLY",
    ]
    assert "| R-01 | tests/test_a.py `test_weak` | EXECUTES_ONLY |" in run.md


@settings(max_examples=200, deadline=None)
@given(
    st.lists(
        st.sampled_from(["ASSERTS", "EXECUTES_ONLY", "UNRELATED", "UNKNOWN", None]),
        min_size=0,
        max_size=6,
    ),
    st.sampled_from(
        ["PASSING", "FAILING", "SKIPPED", "UNVERIFIED", "UNTESTED", "UNCITED", "RETIRED"]
    ),
)
def test_disabling_the_judge_only_restores_weakly_passing(names, status):
    """T-28: disabling the judge changes no status except WEAKLY_PASSING -> PASSING (property
    test over random fixtures). (I-004)"""
    graph, verdicts = _graph_with_edges(names)
    graph.records[0].status = status
    before = status
    apply_verdicts(graph, verdicts)
    after = graph.records[0].status
    if before == "PASSING":
        assert after in ("PASSING", "WEAKLY_PASSING")
    else:
        assert after == before
    # "disabling" = the deterministic status; WEAKLY_PASSING maps back to PASSING, nothing else moves
    restored = "PASSING" if after == "WEAKLY_PASSING" else after
    assert restored == before


def test_ungrounded_answers_are_coerced_to_unknown():
    """T-29: ASSERTS without evidence, evidence outside the span, or evidence in another file is
    coerced to UNKNOWN with coerced: true and rationale `judge: ungrounded`. (E-16, I-005)"""
    req = _req(["def test_a():", "    assert True"], start=5)  # span 5..6
    for raw in [
        _ok("ASSERTS", []),
        _ok("ASSERTS", [Evidence("tests/test_a.py", 7)]),
        _ok("ASSERTS", [Evidence("tests/test_a.py", 4)]),
        _ok("ASSERTS", [Evidence("tests/test_other.py", 6)]),
        _ok("EXECUTES_ONLY", [Evidence("tests/test_a.py", 99)]),
    ]:
        judged = validate(raw, req)
        assert (judged.verdict, judged.coerced, judged.rationale) == (
            "UNKNOWN",
            True,
            "judge: ungrounded",
        )
    good = validate(_ok("ASSERTS", [Evidence("tests/test_a.py", 6)]), req)
    assert (good.verdict, good.coerced, good.evidence) == (
        "ASSERTS",
        False,
        (Evidence("tests/test_a.py", 6),),
    )
    none_needed = validate(_ok("EXECUTES_ONLY", []), req)
    assert none_needed.verdict == "EXECUTES_ONLY" and not none_needed.coerced


def test_provider_failures_yield_unknown_with_specified_rationale():
    """T-30: non-JSON, missing verdict, an unknown verdict string, a raised exception, and a
    timeout each yield UNKNOWN with the specified rationale. (E-14, E-15)"""
    req = _req(["def test_a():", "    assert True"])
    cases = [
        (JudgeMalformed("non-JSON"), "judge: malformed response"),
        (_ok("MAYBE"), "judge: malformed response"),
        (RuntimeError("boom"), "judge: unavailable"),
        (ConnectionError("refused"), "judge: unavailable"),
        (JudgeTimeout(), "judge: timeout"),
        (JudgeHttpError(503), "judge: http 503"),
    ]
    for answer, rationale in cases:
        judged = judge_edge(StubProvider(answer), req)
        assert (judged.verdict, judged.coerced, judged.rationale) == ("UNKNOWN", True, rationale), (
            answer
        )
    judged = judge_edge(StubProvider("not a verdict"), req)
    assert judged.rationale == "judge: malformed response"
    for text in ("not json", '{"evidence": []}', '{"verdict": 3}', "[]"):
        try:
            parse_answer(text)
        except JudgeMalformed:
            pass
        else:
            raise AssertionError(text)
    honest = judge_edge(StubProvider(_ok("UNKNOWN", [], "cannot tell")), req)
    assert honest.verdict == "UNKNOWN" and honest.coerced is False


def test_judge_called_once_per_eligible_edge_only(tmp_path: Path, monkeypatch):
    """T-31: the judge is called exactly once per eligible edge — a PASSING id and a passed
    outcome, R-10's population — and never for FAILING / SKIPPED / UNVERIFIED / UNTESTED / UNCITED
    IDs or for skipped/failed test outcomes. (R-10, I-010)"""
    spec = spec_table(
        [
            ("R-01", "passing"),
            ("R-02", "failing"),
            ("R-03", "skipped"),
            ("R-04", "unverified"),
            ("R-05", "untested"),
            ("R-06", "uncited"),
            ("R-07", "mixed"),
        ]
    )
    tests = (
        "def test_p():\n    '''R-01'''\n    assert True\n\n"
        "def test_f():\n    '''R-02'''\n    assert True\n\n"
        "def test_s():\n    '''R-03'''\n    assert True\n\n"
        "def test_u():\n    '''R-04'''\n    assert True\n\n"
        "def test_m1():\n    '''R-07'''\n    assert True\n\n"
        "def test_m2():\n    '''R-07'''\n    assert True\n\n"
        "def test_m3():\n    '''R-07 R-01'''\n    assert True\n"
    )
    results = junit(
        [
            ("tests.test_a", "test_p", "passed"),
            ("tests.test_a", "test_f", "failed"),
            ("tests.test_a", "test_s", "skipped"),
            ("tests.test_a", "test_m1", "passed"),
            ("tests.test_a", "test_m2", "skipped"),
            ("tests.test_a", "test_m3", "passed"),
        ]
    )
    write_tree(
        tmp_path,
        {"SPEC.md": spec, "src/a.py": "# R-05\n", "tests/test_a.py": tests, "junit.xml": results},
    )
    stub = StubProvider(_ok("EXECUTES_ONLY"))
    monkeypatch.setattr("speccheck.cli._make_provider", lambda config: (stub, 1, 0))
    run = run_cli(
        [
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
        ],
        tmp_path,
    )
    called = sorted((r.id, r.testcase.name) for r in stub.calls)
    assert called == [
        ("R-01", "test_m3"),
        ("R-01", "test_p"),
        ("R-07", "test_m1"),
        ("R-07", "test_m3"),
    ]
    assert len(stub.calls) == len(set(called))
    assert {i: run.status(i) for i in ("R-02", "R-03", "R-04", "R-05", "R-06")} == {
        "R-02": "FAILING",
        "R-03": "SKIPPED",
        "R-04": "UNVERIFIED",
        "R-05": "UNTESTED",
        "R-06": "UNCITED",
    }
    graph_edges = eligible_edges(Graph([], [], []))
    assert graph_edges == []


def test_rationale_truncation_and_newlines():
    """T-32: a rationale over 280 chars is truncated to 277 + `...`; newlines become spaces. (K-07)"""
    long = "x" * 300
    assert clean_rationale(long) == "x" * 277 + "..." and len(clean_rationale(long)) == 280
    assert clean_rationale("a\nb\r\nc") == "a b c"
    assert clean_rationale("y" * 280) == "y" * 280
    req = _req(["def test_a():", "    assert True"])
    judged = validate(_ok("EXECUTES_ONLY", [], "line1\nline2" + "z" * 300), req)
    assert (
        "\n" not in judged.rationale
        and judged.rationale.endswith("...")
        and len(judged.rationale) == 280
    )


class RecordingPost:
    """A recorded HTTP stub with a concurrency counter (T-33)."""

    def __init__(self, reply: str | None = None, delay: float = 0.0):
        self.reply = (
            reply
            if reply is not None
            else json.dumps({"verdict": "EXECUTES_ONLY", "evidence": [], "rationale": "stub"})
        )
        self.delay = delay
        self.requests: list[tuple[str, dict, bytes, float]] = []
        self.in_flight = 0
        self.max_in_flight = 0
        self.lock = threading.Lock()

    def __call__(self, url: str, headers, body: bytes, timeout: float) -> tuple[int, str]:
        with self.lock:
            self.requests.append((url, dict(headers), body, timeout))
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay:
                time.sleep(self.delay)
            return 200, json.dumps(
                {"choices": [{"message": {"role": "assistant", "content": self.reply}}]}
            )
        finally:
            with self.lock:
                self.in_flight -= 1


def test_llm_provider_wire_format_timeout_and_concurrency():
    """T-33: the LLM provider sends exactly one POST per edge whose body is byte-for-byte the
    C-06 shape, with the bearer header; honors the timeout; never retries; issues at most
    --judge-concurrency requests at once while output order stays fixed; each edge yields one
    verdict from the R-10 set. (R-10, K-05, K-06, R-26, C-09)"""
    config = LlmConfig.from_env({**LLM_ENV, "SPECCHECK_JUDGE_TIMEOUT": "1"})
    post = RecordingPost()
    provider = LlmJudge(config, post=post)
    req = _req(["def test_a():", "    assert x == 1"], start=17)
    verdict = provider.judge(req)
    assert verdict.verdict == "EXECUTES_ONLY"
    assert len(post.requests) == 1
    url, headers, body, timeout = post.requests[0]
    assert url == LLM_ENV["SPECCHECK_JUDGE_URL"] and timeout == 1.0
    assert headers == {"Content-Type": "application/json", "Authorization": "Bearer sk-secret-key"}
    expected_user = json.dumps(
        {
            "id": "R-01",
            "statement": "the statement",
            "related": [],  # R-38 (v1.16); `_req` builds a request with no neighbourhood
            "declared": False,  # C-15 (v1.14); `_req` builds an unclassified request
            "file": "tests/test_a.py",
            "start": 17,
            "end": 18,
            "source": "17\tdef test_a():\n18\t    assert x == 1",
        },
        indent=2,
        ensure_ascii=False,
    )
    expected_body = json.dumps(
        {
            "model": "m",
            "temperature": 0,
            "max_tokens": 4000,
            "messages": [
                {"role": "system", "content": C10_PATH.read_text(encoding="utf-8")},
                {"role": "user", "content": expected_user},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    assert body == expected_body
    # timeout honored, no retry: the stub sleeps past the 1 s timeout
    slow = RecordingPost(delay=3.0)

    def slow_post(url, headers, body, timeout):
        done = threading.Event()
        result = {}

        def run():
            result["v"] = slow(url, headers, body, timeout)
            done.set()

        threading.Thread(target=run, daemon=True).start()
        if not done.wait(timeout):
            raise JudgeTimeout()
        return result["v"]

    t0 = time.monotonic()
    judged = judge_edge(LlmJudge(config, post=slow_post), req)
    assert judged.rationale == "judge: timeout" and time.monotonic() - t0 < 2.5
    assert len(slow.requests) == 1
    # concurrency: 6 edges, at most 2 in flight, output keyed by edge regardless of completion order
    counted = RecordingPost(delay=0.05)
    provider = LlmJudge(config, post=counted)
    reqs = [
        _req([f"def test_{i}():", "    assert True"], start=1 + 10 * i, name=f"test_{i}")
        for i in range(6)
    ]
    run = run_judge(provider, reqs, concurrency=2)
    assert counted.max_in_flight <= 2 and len(counted.requests) == 6
    assert set(run.verdicts) == {(r.testcase, r.id) for r in reqs}
    assert run.available is True


def test_llm_response_path_fences_and_prompt_hash(tmp_path: Path, monkeypatch):
    """T-54: the provider reads choices[0].message.content, accepts a bare JSON object and one
    wrapped in a ``` or ```json fence, treats a missing path, a non-200 status, or other text as
    E-14/E-15; the report carries judge_prompt_sha256 equal to the SHA-256 of judge_prompt.md,
    and that file equals the C-10 text. (C-06, C-10, R-26)"""
    answer = {
        "verdict": "ASSERTS",
        "clause": "a",  # the whole 1-character statement (K-15: a short statement matches itself)
        "evidence": [{"file": "tests/test_a.py", "line": 2}],
        "rationale": "ok",
    }
    bare = json.dumps(answer)
    assert parse_answer(bare).verdict == "ASSERTS"
    assert parse_answer(f"```\n{bare}\n```").verdict == "ASSERTS"
    assert parse_answer(f"```json\n{bare}\n```").verdict == "ASSERTS"
    assert parse_answer(f"  \n{bare}\n\n").evidence == (Evidence("tests/test_a.py", 2),)
    assert strip_fence("```json\n{}\n```") == "{}"
    config = LlmConfig.from_env(LLM_ENV)
    req = _req(["def test_a():", "    assert True"])
    for status, text, rationale in [
        (500, "{}", "judge: http 500"),
        (404, "nope", "judge: http 404"),
        (200, "not json at all", "judge: malformed response"),
        (200, json.dumps({"choices": []}), "judge: malformed response"),
        (200, json.dumps({"choices": [{"message": {}}]}), "judge: malformed response"),
        (
            200,
            json.dumps({"choices": [{"message": {"content": "I think it asserts."}}]}),
            "judge: malformed response",
        ),
        (
            200,
            json.dumps({"choices": [{"message": {"content": '{"rationale": "no verdict key"}'}}]}),
            "judge: malformed response",
        ),
    ]:
        provider = LlmJudge(config, post=lambda *a, _s=status, _t=text: (_s, _t))
        judged = judge_edge(provider, req)
        assert (judged.verdict, judged.coerced, judged.rationale) == ("UNKNOWN", True, rationale), (
            status,
            text,
        )
    # the shipped prompt equals the C-10 text in SPEC.md and its hash lands in the report
    spec_text = (Path(__file__).resolve().parent.parent / "SPEC.md").read_text(encoding="utf-8")
    start = spec_text.index("### C-10 Judge instruction text")
    block_start = spec_text.index("```text\n", start) + len("```text\n")
    block_end = spec_text.index("\n```\n", block_start)
    c10 = spec_text[block_start:block_end] + "\n"
    shipped = C10_PATH.read_text(encoding="utf-8")
    assert shipped == c10 and judge_llm.load_prompt() == c10
    expected_hash = hashlib.sha256(shipped.encode("utf-8")).hexdigest()
    write_tree(
        tmp_path,
        {
            "SPEC.md": spec_table([("R-01", "a")]),
            "tests/test_a.py": "def test_a():\n    '''R-01'''\n    assert True\n",
            "junit.xml": junit([("tests.test_a", "test_a", "passed")]),
        },
    )
    monkeypatch.setattr(judge_llm, "_httpx_post", RecordingPost(reply=bare))
    run = run_cli(
        [
            "check",
            "--spec",
            "SPEC.md",
            "--tests",
            "tests",
            "--results",
            "junit.xml",
            "--judge",
            "llm",
        ],
        tmp_path,
        env=LLM_ENV,
    )
    assert run.code == 0
    assert run.json["judge_prompt_sha256"] == expected_hash
    assert list(run.json)[:5] == [
        "schema_version",
        "spec",
        "judge",
        "judge_available",
        "judge_prompt_sha256",
    ]
    assert run.ids()["R-01"]["tests"][0]["verdict"]["verdict"] == "ASSERTS"


def test_llm_request_carries_heading_body_statement(tmp_path: Path, monkeypatch):
    """T-74 (extends T-33): for a heading-declared ID with a body, the LLM request's user message
    carries `statement` equal to `SpecId.text` — title, newline, body with its fenced block and
    indentation, byte for byte — under the keys {id, statement, declared, file, start, end,
    source} and the unchanged system message; the shipped C-10 file contains the v1.7 any-clause
    rule and `judge_prompt_sha256` is its SHA-256 (recorded HTTP stub). (R-33, C-06, C-15, C-10,
    R-26)"""
    from speccheck.extract import parse_spec

    spec = "\n".join(
        [
            "### C-01 `Widget` (an `actor`)",
            "",
            "```swift",
            "actor Widget {",
            "    func startRun() -> Bool   // false when a run is live",
            "}",
            "```",
            "",
            "Out-of-range parameters throw on the first tick.",
            "",
            "### C-02 Empty",
        ]
    )
    write_tree(
        tmp_path,
        {
            "SPEC.md": spec + "\n",
            "src/w.py": "# C-01 C-02\n",
            "tests/test_w.py": "def test_w():\n    '''C-01'''\n    assert True\n",
            "junit.xml": junit([("tests.test_w", "test_w", "passed")]),
        },
    )
    expected = parse_spec(spec + "\n", "SPEC.md").by_id()["C-01"].text
    assert (
        expected.startswith("`Widget` (an `actor`)\n```swift\n") and "    func startRun" in expected
    )
    post = RecordingPost(
        reply=json.dumps(
            {
                "verdict": "ASSERTS",
                "clause": "func startRun() -> Bool",  # a clause of the body, verbatim
                "evidence": [{"file": "tests/test_w.py", "line": 3}],
                "rationale": "r",
            }
        )
    )
    monkeypatch.setattr(judge_llm, "_httpx_post", post)
    run = run_cli(
        [
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
            "llm",
        ],
        tmp_path,
        env=LLM_ENV,
    )
    assert run.code == 0 and len(post.requests) == 1
    body = json.loads(post.requests[0][2].decode("utf-8"))
    user = json.loads(body["messages"][1]["content"])
    assert list(user) == [
        "id",
        "statement",
        "related",
        "declared",
        "file",
        "start",
        "end",
        "source",
    ]
    assert user["id"] == "C-01" and user["statement"] == expected
    assert run.ids()["C-01"]["statement"] == expected  # the JSON records what the judge saw
    assert run.ids()["C-01"]["title"] == "`Widget` (an `actor`)"
    # the shipped instruction text carries the v1.9 clause rule and its hash is what the report records
    shipped = C10_PATH.read_text(encoding="utf-8")
    assert 'quote it verbatim in "clause"' in shipped  # the v1.9 C-10 text
    assert body["messages"][0]["content"] == shipped
    assert run.json["judge_prompt_sha256"] == hashlib.sha256(shipped.encode("utf-8")).hexdigest()


STATEMENT = (
    "Report shape\n```python\nclass Summary:\n    count: int   # rule 1\n```\n\n"
    "1. **Shape.** `summarize` returns a `Summary` whose fields are exactly `count`, `total`.\n"
    "2. **Rounding.** `total` is the sum rounded per K-02."
)


def _req_with(statement: str, source_lines=("def test_a():", "    assert True")) -> JudgeRequest:
    case = SpecTestCase("tests/test_a.py", "test_a", "tests.test_a", 1, len(source_lines))
    return build_request("C-04", statement, case, list(source_lines))


def test_clause_grounding_validation():
    """T-75: an ASSERTS whose clause is a verbatim excerpt differing only in line breaks and
    indentation is accepted and recorded with the collapsed excerpt; a 300-character excerpt is
    cut to 280; a paraphrase, an 8-character fragment, a missing key and "" each yield UNKNOWN
    `judge: unlocated clause` for ASSERTS and EXECUTES_ONLY alike; an UNRELATED with a clause is
    recorded with "" and not coerced; `"clause": null` on an UNRELATED is "" and not coerced, on
    an ASSERTS it is E-48; unlocated clause AND out-of-span evidence records `judge: unlocated
    clause` (rule order); a leading space that otherwise matches is LOCATED (K-15 trims); a
    9-character statement is matched by itself and by nothing shorter; the mock's clause is the
    collapsed statement's first 280 characters and "" for an empty statement. (R-34, K-15, E-48,
    E-49, I-005, C-06, R-22)"""
    from speccheck.judge import locate_clause

    req = _req_with(STATEMENT)
    ev = [Evidence("tests/test_a.py", 2)]
    # verbatim excerpt with different whitespace -> located, recorded collapsed
    v = validate(_ok("ASSERTS", ev, clause="returns a `Summary`\n   whose fields are exactly"), req)
    assert (v.verdict, v.coerced, v.clause) == (
        "ASSERTS",
        False,
        "returns a `Summary` whose fields are exactly",
    )
    # a long excerpt is cut to its first 280 characters (a prefix of a located excerpt is located)
    long_stmt = "x" * 10 + " " + "word " * 100
    v = validate(_ok("EXECUTES_ONLY", clause=long_stmt[:300]), _req_with(long_stmt))
    assert v.verdict == "EXECUTES_ONLY" and len(v.clause) == 280 and long_stmt.startswith(v.clause)
    # paraphrase / short fragment / missing / empty -> unlocated, for both verdicts
    for verdict in ("ASSERTS", "EXECUTES_ONLY"):
        for bad in ("the summary has count and total fields", "rule 1", "", None):
            v = validate(_ok(verdict, ev, clause=bad), req)  # type: ignore[arg-type]
            assert (v.verdict, v.coerced, v.rationale, v.clause) == (
                "UNKNOWN",
                True,
                "judge: unlocated clause",
                "",
            ), (verdict, bad)
    # UNRELATED / UNKNOWN: clause blanked, never coerced for it
    for verdict in ("UNRELATED", "UNKNOWN"):
        for supplied in ("Rounding", None, 7):
            v = validate(_ok(verdict, clause=supplied), req)  # type: ignore[arg-type]
            assert (v.verdict, v.coerced, v.clause) == (verdict, False, "")
    # rule order: unlocated clause wins over out-of-span evidence
    v = validate(_ok("ASSERTS", [Evidence("tests/test_a.py", 99)], clause="nope nope nope"), req)
    assert v.rationale == "judge: unlocated clause"
    v = validate(_ok("ASSERTS", [Evidence("tests/test_a.py", 99)], clause="rounded per K-02."), req)
    assert v.rationale == "judge: ungrounded"
    # K-15 trims; the 12-character floor; a short statement is matched by itself only
    assert locate_clause(" Report shape\n```python", STATEMENT) == "Report shape ```python"
    assert locate_clause("Report shap", STATEMENT) is None  # 11 characters
    assert locate_clause("Report shape", STATEMENT) == "Report shape"  # 12
    assert locate_clause("nine char", "nine char") == "nine char"
    assert locate_clause("nine cha", "nine char") is None
    assert locate_clause("", "") == ""
    assert locate_clause("Nine char", "nine char") is None  # case-sensitive
    # the mock's clause is the collapsed statement's prefix, and "" for an empty statement
    mock = MockJudge()
    assert mock.judge(req).clause == " ".join(STATEMENT.split())[:280]
    assert mock.judge(_req_with(long_stmt)).clause == " ".join(long_stmt.split())[:280]
    assert mock.judge(_req_with("")).clause == ""
    assert validate(mock.judge(_req_with("")), _req_with("")).coerced is False


def test_triage_request_shape_and_response_parse():
    """T-89 (C-17): the triage request is exactly `{model, state, questions}` — `state` built from
    the C-06 request object by C-17's template, `questions.verdict` a choice question whose
    criteria are the four C-06 tokens, no clause and no evidence anywhere — sent with the bearer
    key; the answer is read from `answers.verdict` and the edge's confidence is
    $p(e) = \\max \\mathrm{probabilities}$; a non-200, a non-JSON body, a missing
    `answers.verdict`, a `choice` outside the four tokens, and empty or non-numeric
    `probabilities` are each a per-edge failure (`None`), not an exception; the config's own repr
    and every error message never carry the key. (C-17, K-16, I-015)"""
    req = _req(["def test_a():", "    assert True"], start=3)
    body = json.loads(jev.build_body(req, "~typesafe/jev-latest"))
    assert list(body) == ["model", "state", "questions"]
    assert body["model"] == "~typesafe/jev-latest"
    assert body["state"] == (
        "Specification obligation R-01.\n\nStatement:\nthe statement\n\n"
        "Related obligations:\n\n\n"  # D-28b (v1.16): a blank line when `related` is []
        "Test file tests/test_a.py, lines 3-4:\n3\tdef test_a():\n4\t    assert True"
    )
    question = body["questions"]["verdict"]
    assert question["type"] == "choice" and set(question["criteria"]) == set(VERDICTS)
    # the request carries no clause and no evidence field at any level (C-17)
    assert list(question) == ["type", "instructions", "criteria"]
    assert list(body["questions"]) == ["verdict"]

    def answer(choice: str, probabilities: object, status: int = 200, text: str | None = None):
        payload = text
        if payload is None:
            payload = json.dumps(
                {"answers": {"verdict": {"choice": choice, "probabilities": probabilities}}}
            )
        return lambda *a: (status, payload)

    config = jev.JevConfig("http://localhost:9/decisions", "~typesafe/jev-latest", "sk-jev", 30)
    assert "sk-jev" not in config.redacted() and "***" in config.redacted()
    cases = [
        answer("ASSERTS", {"ASSERTS": 0.7, "UNRELATED": 0.3}),
        answer("UNRELATED", {"UNRELATED": 0.99}),
    ]
    assert jev.JevTriage(config, post=cases[0]).confidence(req) == 0.7
    assert jev.JevTriage(config, post=cases[1]).confidence(req) == 0.99
    unusable = [
        answer("ASSERTS", {"ASSERTS": 0.9}, status=503),
        answer("ASSERTS", {}, text="not json"),
        answer("ASSERTS", {}, text='{"answers": {}}'),
        answer("MAYBE", {"MAYBE": 0.9}),
        answer("ASSERTS", {}),
        answer("ASSERTS", {"ASSERTS": "high"}),
        answer("ASSERTS", [], text='{"answers": {"verdict": {"choice": "ASSERTS", "probabilities": []}}}'),
        lambda *a: (_ for _ in ()).throw(RuntimeError("boom")),
    ]
    for stub in unusable:
        assert jev.JevTriage(config, post=stub).confidence(req) is None

    # K-16: one request per eligible edge, at most `concurrency` in flight
    in_flight = {"now": 0, "max": 0}
    lock = threading.Lock()

    class _SlowTriage:
        def confidence(self, r: JudgeRequest) -> float:
            with lock:
                in_flight["now"] += 1
                in_flight["max"] = max(in_flight["max"], in_flight["now"])
            time.sleep(0.02)
            with lock:
                in_flight["now"] -= 1
            return float(r.testcase.start)

    requests = [
        _req(["def test_a():", "    assert True"], start=n, name=f"test_{n}") for n in range(1, 11)
    ]
    run = jev.run_triage(_SlowTriage(), requests, concurrency=3)
    assert len(run.order) == 10 and run.failures == 0
    assert in_flight["max"] <= 3, in_flight
    assert [r.testcase.start for r in run.order] == list(range(1, 11))  # ascending p(e)

    def post(url, headers, body_bytes, timeout):
        post.seen = (url, dict(headers), body_bytes, timeout)
        return 200, json.dumps({"answers": {"verdict": {"choice": "ASSERTS", "probabilities": {"ASSERTS": 0.5}}}})

    post.seen = None
    jev.JevTriage(config, post=post).confidence(req)
    url, headers, body_bytes, timeout = post.seen
    assert url == "http://localhost:9/decisions" and timeout == 30.0
    assert headers["Authorization"] == "Bearer sk-jev"
    assert json.loads(body_bytes)["model"] == "~typesafe/jev-latest"

    # C-17: the key is required; the URL and the model are optional and default
    env = {k: v for k, v in JEV_ENV.items() if k != "SPECCHECK_JEV_API_KEY"}
    try:
        jev.JevConfig.from_env(env)
    except jev.JevConfigError as exc:
        assert "SPECCHECK_JEV_API_KEY" in str(exc) and "sk-jev" not in str(exc)
    else:
        raise AssertionError("missing key accepted")
    env = {**JEV_ENV, "SPECCHECK_JEV_TIMEOUT": "0"}
    try:
        jev.JevConfig.from_env(env)
    except jev.JevConfigError as exc:
        assert "SPECCHECK_JEV_TIMEOUT" in str(exc)
    else:
        raise AssertionError("timeout 0 accepted")
    defaults = jev.JevConfig.from_env({"SPECCHECK_JEV_API_KEY": "sk-jev"})
    assert defaults.url == "https://openrouter.ai/api/alpha/decisions"
    assert defaults.model == "~typesafe/jev-latest" and defaults.timeout == 30


def _ten_edge_project():
    """A spec with ten ids, one passing test per id: ten judge-eligible edges (I-010)."""
    ids = [f"R-{n:02d}" for n in range(1, 11)]
    spec = spec_table([(ident, f"obligation {ident}") for ident in ids])
    tests = "".join(
        f"def test_r{n:02d}():\n    '''{ident}'''\n    assert True\n\n"
        for n, ident in enumerate(ids, start=1)
    )
    results = junit([("tests.test_a", f"test_r{n:02d}", "passed") for n in range(1, 11)])
    return {"SPEC.md": spec, "tests/test_a.py": tests, "junit.xml": results}


class _RecordingJudge:
    """A judge stub that records the order it was asked in (concurrency 1) and answers ASSERTS."""

    prompt_sha256 = "0" * 64  # R-26: the cli records this as judge_prompt_sha256

    def __init__(self) -> None:
        self.order: list[str] = []

    def judge(self, req: JudgeRequest) -> Verdict:
        self.order.append(req.id)
        return _ok("ASSERTS", [Evidence(req.testcase.file, req.testcase.start)], clause=req.statement)


def _jev_transport(confidences: dict[str, float], failing: set[str] = frozenset()):
    """A C-17 transport stub: one fixed confidence per id, or HTTP 500 for a named edge."""
    calls: list[str] = []

    def post(url, headers, body, timeout):
        state = json.loads(body)["state"]
        ident = state.split("\n", 1)[0].removeprefix("Specification obligation ").rstrip(".")
        calls.append(ident)
        if ident in failing:
            return 503, "unavailable"
        payload = {
            "answers": {
                "verdict": {
                    "choice": "ASSERTS",
                    "probabilities": {"ASSERTS": confidences[ident], "UNRELATED": 1 - confidences[ident]},
                }
            }
        }
        return 200, json.dumps(payload)

    post.calls = calls
    return post


def test_triage_orders_and_truncates_the_judge_queue(tmp_path: Path, monkeypatch):
    """T-89: with --judge llm --jev-pre-triage over ten judge-eligible edges, a stub C-17
    provider returning fixed confidences (one edge failing with HTTP 500) and a stub judge
    recording every edge it is asked about, --judge-budget 30% issues exactly
    ceil(0.30 x 10) = 3 edges — the three with the lowest p(e), the failing edge first among
    them — in ascending-confidence order, and the other 7 are UNKNOWN with rationale
    `judge: budget` and coerced: true, with one Note reporting 7 and one reporting the single
    E-59 failure; --judge-budget 100% issues all 10; --judge-budget 0% issues none (judge call
    count 0) while still running the triage pass, with judge_available FALSE (v1.20: at least
    one edge was eligible and no call succeeded, C-07/E-35 — not vacuously true just because
    the triage pass itself ran); a stub that fails every C-17 call leaves judge_available and
    unknown_rate exactly as a triage-free run does.
    (K-16, K-12, C-17, I-015, E-35, E-59, I-006, D-30, D-32)"""
    write_tree(tmp_path, _ten_edge_project())
    # p(e) is the max over the returned labels (C-17), so every stub confidence stays >= 0.5
    confidences = {f"R-{n:02d}": 0.50 + n / 20 for n in range(1, 11)}
    transport = _jev_transport(confidences, failing={"R-05"})
    monkeypatch.setattr(jev, "_httpx_post", transport)
    judge = _RecordingJudge()
    monkeypatch.setattr(cli, "_make_provider", lambda config: (judge, 1, 0))
    base = ["check", "--spec", "SPEC.md", "--tests", "tests", "--results", "junit.xml",
            "--judge", "llm", "--jev-pre-triage"]

    run = run_cli([*base, "--judge-budget", "30%"], tmp_path, env=JEV_ENV)
    assert run.code == 0, run.stderr
    # the three least confident, the failed edge first, then ascending p(e)
    assert judge.order == ["R-05", "R-01", "R-02"]
    assert len(transport.calls) == 10 and sorted(transport.calls) == sorted(confidences)
    verdicts = {t["name"]: t["verdict"] for t in run.ids()["R-01"]["tests"]}
    assert verdicts["test_r01"]["verdict"] == "ASSERTS"
    doc = run.json
    for ident in ("R-03", "R-04", "R-06", "R-07", "R-08", "R-09", "R-10"):
        row = next(i for i in doc["ids"] if i["id"] == ident)
        verdict = row["tests"][0]["verdict"]
        assert verdict["verdict"] == "UNKNOWN" and verdict["coerced"] is True
        assert verdict["rationale"] == "judge: budget" and verdict["evidence"] == []
    assert doc["notes"] == [
        "jev triage failed: 1 edge(s) ordered first",
        "judge budget exhausted: 7 edge(s) unjudged",
    ]
    assert doc["metrics"]["unknown_rate"] == 0.7 and doc["judge_available"] is True

    judge.order.clear()
    run = run_cli([*base, "--judge-budget", "100%"], tmp_path, env=JEV_ENV)
    assert judge.order == ["R-05", "R-01", "R-02", "R-03", "R-04", "R-06", "R-07", "R-08",
                           "R-09", "R-10"]
    assert run.json["metrics"]["unknown_rate"] == 0.0
    assert run.json["notes"] == ["jev triage failed: 1 edge(s) ordered first"]

    judge.order.clear()
    run = run_cli([*base, "--judge-budget", "0%"], tmp_path, env=JEV_ENV)
    assert judge.order == [] and run.json["judge_available"] is False  # v1.20: C-07, E-35
    assert run.json["metrics"]["unknown_rate"] == 1.0

    # a total C-17 failure changes nothing the judge records (E-59)
    monkeypatch.setattr(jev, "_httpx_post", _jev_transport(confidences, failing=set(confidences)))
    judge.order.clear()
    run = run_cli([*base, "--judge-budget", "100%"], tmp_path, env=JEV_ENV)
    assert len(judge.order) == 10 and run.json["judge_available"] is True
    assert run.json["metrics"]["unknown_rate"] == 0.0
    assert run.json["notes"] == ["jev triage failed: 10 edge(s) ordered first"]


def test_triage_is_ignored_under_mock_and_inert_on_an_unlimited_budget(tmp_path: Path, monkeypatch):
    """T-89: K-16 is ignored unless --judge llm — under --judge mock --jev-pre-triage no C-17
    request is made and no C-17 variable is read (I-006) — and with --judge-budget 0 (the
    SECONDS form's unlimited value) the pass reorders the queue but changes no report content,
    with the D-30 Note recording that it had no effect; 0% is a real truncation and gets no such
    Note. (K-16, K-12, C-17, I-015, E-35, D-30)"""
    write_tree(tmp_path, _ten_edge_project())
    transport = _jev_transport({f"R-{n:02d}": 0.50 + n / 20 for n in range(1, 11)})
    monkeypatch.setattr(jev, "_httpx_post", transport)
    real_make_provider = cli._make_provider
    monkeypatch.setattr(cli, "_make_provider", lambda config: (MockJudge(), 1, 0))

    # K-16 ignored: no Jev call, no SPECCHECK_JEV_* variable needed, no Note
    run = run_cli(
        ["check", "--spec", "SPEC.md", "--tests", "tests", "--results", "junit.xml",
         "--judge", "mock", "--jev-pre-triage", "--judge-budget", "30"],
        tmp_path,
    )
    assert run.code == 0 and transport.calls == []
    assert run.json["notes"] == []
    clean = run.json

    # under --judge llm with an unlimited SECONDS budget the pass reorders the queue but changes
    # no report content, and the D-30 Note records that it had no effect
    judge = _RecordingJudge()
    monkeypatch.setattr(cli, "_make_provider", lambda config: (judge, 1, 0))
    base = ["check", "--spec", "SPEC.md", "--tests", "tests", "--results", "junit.xml",
            "--judge", "llm", "--judge-budget", "0"]
    triaged = run_cli([*base, "--jev-pre-triage"], tmp_path, env=JEV_ENV)
    triaged_doc = triaged.json
    assert judge.order == [f"R-{n:02d}" for n in range(1, 11)]  # ascending p(e)
    judge.order.clear()
    plain = run_cli(base, tmp_path, env=JEV_ENV)
    assert triaged_doc["notes"] == ["jev-pre-triage had no effect: --judge-budget is unlimited"]
    assert plain.json["notes"] == []
    assert {k: v for k, v in triaged_doc.items() if k != "notes"} == {
        k: v for k, v in plain.json.items() if k != "notes"
    }
    assert plain.json["metrics"] == clean["metrics"]

    run = run_cli(
        ["check", "--spec", "SPEC.md", "--tests", "tests", "--results", "junit.xml",
         "--judge", "llm", "--jev-pre-triage", "--judge-budget", "0%"],
        tmp_path,
        env=JEV_ENV,
    )
    assert run.json["notes"] == ["judge budget exhausted: 10 edge(s) unjudged"]

    # E-36: with zero eligible edges no request is sent to either provider
    empty_dir = tmp_path / "empty"
    write_tree(
        empty_dir,
        {"SPEC.md": spec_table([("R-01", "obligation R-01")]), "src/a.py": "# R-01\n"},
    )
    transport.calls.clear()
    run = run_cli(
        ["check", "--spec", "SPEC.md", "--src", "src", "--judge", "llm", "--jev-pre-triage",
         "--judge-budget", "0%"],
        empty_dir,
        env=JEV_ENV,
    )
    assert run.code == 0 and transport.calls == [] and run.json["notes"] == []
    assert run.json["judge_available"] is True and run.json["metrics"]["unknown_rate"] is None

    # the golden fixture is byte-identical when the flag is added to a --judge mock run
    monkeypatch.setattr(cli, "_make_provider", real_make_provider)  # the real MockJudge again
    target = tmp_path / "golden-target"
    shutil.copytree(FIXTURE, target)
    out = target / "fresh-out"
    run = run_cli(
        ["check", "--spec", "SPEC.md", "--src", "src", "--tests", "tests", "--results",
         "junit.xml", "--judge", "mock", "--strict", "--jev-pre-triage",
         "--root", ".", "--out", str(out)],
        target,
    )
    assert run.code == 1  # the fixture has planted defects (T-46)
    for name in ("speccheck.json", "SPEC_CONFORMANCE_REPORT.md"):
        assert (out / name).read_bytes() == (FIXTURE / "golden" / name).read_bytes(), name


def test_judge_request_carries_declared_for_the_edge(tmp_path: Path, monkeypatch):
    """T-85 (C-15): the LLM request's user message carries `declared` for the specific
    (id, testcase) edge — `true` for an id the test's own docstring names, `false` for one that
    appears only in the test body as example data — under the C-06 key order
    `{id, statement, declared, file, start, end, source}`; the value is read-only context and
    coerces no verdict (D-26, R-39, C-06, C-15, C-16)."""
    write_tree(
        tmp_path,
        {
            "SPEC.md": spec_table([("R-01", "adds"), ("R-02", "subtracts")]),
            "tests/test_a.py": (
                "def test_a():\n"
                '    """R-01: the docstring declaration."""\n'
                '    label = "R-02"\n'
                "    assert label\n"
            ),
            "junit.xml": junit([("tests.test_a", "test_a", "passed")]),
        },
    )
    post = RecordingPost()
    monkeypatch.setattr(judge_llm, "_httpx_post", post)
    run = run_cli(
        ["check", "--spec", "SPEC.md", "--tests", "tests", "--results", "junit.xml",
         "--judge", "llm"],
        tmp_path,
        env=LLM_ENV,
    )
    assert run.code == 0
    users = {
        json.loads(body["messages"][1]["content"])["id"]: json.loads(
            body["messages"][1]["content"]
        )
        for _, _, raw, _ in post.requests
        for body in [json.loads(raw.decode("utf-8"))]
    }
    assert set(users) == {"R-01", "R-02"}
    assert list(users["R-01"]) == [
        "id",
        "statement",
        "related",
        "declared",
        "file",
        "start",
        "end",
        "source",
    ]
    assert users["R-01"]["declared"] is True
    assert users["R-02"]["declared"] is False


class _CapturingJudge:
    """A judge stub that records every request object it is asked about (C-06)."""

    prompt_sha256 = "0" * 64

    def __init__(self) -> None:
        self.requests: list[JudgeRequest] = []

    def judge(self, req: JudgeRequest) -> Verdict:
        self.requests.append(req)
        return _ok("ASSERTS", [Evidence(req.testcase.file, req.testcase.start)], clause=req.statement)


def _state_transport(states: list[str]):
    """A C-17 transport stub that records every `state` it is sent and answers one confidence."""

    def post(url, headers, body, timeout):
        states.append(json.loads(body)["state"])
        payload = {
            "answers": {"verdict": {"choice": "ASSERTS", "probabilities": {"ASSERTS": 0.9}}}
        }
        return 200, json.dumps(payload)

    return post


def test_t83_related_neighbourhood_on_request_and_triage_state(tmp_path: Path, monkeypatch):
    """T-83: for a judged edge the C-06 request's user message carries `related` — the
    whitespace-collapsed titles (each at most 160 characters) of the obligations the statement
    names and that name it, its own references first, at most eight in C-07 id order, a retired
    neighbour keeping its `(retired)` title (E-57), and the empty list when the id has no
    neighbour — a request-side field like `declared`: absent from `speccheck.json` and from the
    Markdown report and not inspected by any C-06 coercion rule or by C-08; the triage `state`
    (C-17) carries the same `related` section. (R-38, C-06, C-10, D-28, E-57)"""
    from speccheck.extract import parse_spec
    from speccheck.judge_llm import related_titles

    long_title = "x" * 200  # R-38: a title over 160 characters is cut to 159 + the marker
    index = parse_spec(
        spec_table(
            [
                ("R-01", "names C-01, K-02 and E-02."),
                ("C-01", "the interface."),
                ("K-02", "a bound."),
                ("E-02", "an edge."),
                ("R-02", "second, per R-01."),
                ("R-03", "third, per R-01."),
                ("R-04", "fourth, per R-01."),
                ("R-05", "fifth, per R-01."),
                ("R-06", "sixth, per R-01."),
                ("R-07", "seventh, per R-01."),
                ("R-08", "eighth, per R-01."),
                ("I-001", "no references here."),
                ("K-03", "reads E-01."),
                ("E-01", long_title),
                ("R-09", "names C-02."),
                ("C-02", "the retired neighbour."),
                ("T-01", "proves R-01."),
            ],
            retired={"C-02"},
        ),
        "SPEC.md",
    )
    # own references first (C-07 order), then the ids that name it (C-07 order), capped at 8:
    # the own three, then R-02..R-06 — R-07 and R-08 are dropped, and the T id never appears
    assert related_titles("R-01", index) == (
        "the interface.",
        "a bound.",
        "an edge.",
        "second, per R-01.",
        "third, per R-01.",
        "fourth, per R-01.",
        "fifth, per R-01.",
        "sixth, per R-01.",
    )
    # the reverse direction alone: R-08 names R-01, so R-01 is its neighbourhood
    assert related_titles("R-08", index) == ("names C-01, K-02 and E-02.",)
    assert related_titles("I-001", index) == ()  # [] when the id has no neighbour (R-38)
    # a retired neighbour keeps its title with `(retired)` appended (E-57)
    assert related_titles("R-09", index) == ("the retired neighbour. (retired)",)
    # a 200-character title is whitespace-collapsed and cut to 160 with the R-38 ellipsis
    (truncated,) = related_titles("K-03", index)
    assert truncated == "x" * 159 + "\u2026" and len(truncated) == 160

    # end to end: the same list in the LLM user message and in the C-17 triage `state`
    write_tree(
        tmp_path,
        {
            "SPEC.md": spec_table([("R-01", "names C-01."), ("C-01", "the interface.")]),
            "tests/test_a.py": "def test_r01():\n    '''R-01'''\n    assert True\n",
            "junit.xml": junit([("tests.test_a", "test_r01", "passed")]),
        },
    )
    judge = _CapturingJudge()
    monkeypatch.setattr(cli, "_make_provider", lambda config: (judge, 1, 0))
    states: list[str] = []
    monkeypatch.setattr(jev, "_httpx_post", _state_transport(states))
    run = run_cli(
        [
            "check", "--spec", "SPEC.md", "--tests", "tests", "--results", "junit.xml",
            "--judge", "llm", "--jev-pre-triage",
        ],
        tmp_path,
        env=JEV_ENV,
    )
    assert run.code == 0, run.stderr
    (req,) = judge.requests
    assert req.related == ("the interface.",)
    user = json.loads(req.to_json())
    assert list(user) == [
        "id",
        "statement",
        "related",
        "declared",
        "file",
        "start",
        "end",
        "source",
    ]
    assert user["related"] == ["the interface."]
    (state,) = states
    assert "Related obligations:\nthe interface.\n\nTest file tests/test_a.py, lines 1-3:" in state
    # request-side only: neither report carries it, and no C-06 rule or C-08 section reads it
    raw = (tmp_path / "speccheck.json").read_text(encoding="utf-8")
    assert '"related"' not in raw and "related" not in run.md
