"""CLI (§5): the only surface. Parses arguments, wires the §3.1 pipeline, applies the exit-code
(§5.4), summary-line (§5.1), and diagnostics (§5.3) contracts, and hosts `--self-check`.

Spec IDs realized here (§11): R-14, R-15, R-17, R-18, R-19, R-21, R-23, R-28, R-29, R-30, I-001,
    I-006, I-007, I-009, K-01, K-06, K-10, K-11, K-12, E-01, E-09, E-19, E-21, E-26, E-32, E-36,
    E-39, E-41.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import logging
import os
import shutil
import socket
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import __version__
from .attribute import Citation, TestCase, attribute_file
from .extract import (
    ScanCounters,
    SpecError,
    citations_in_file,
    decode_text,
    parse_spec,
    scan_roots,
    to_posix_relative,
)
from .graph import apply_verdicts, build_graph, eligible_edges
from .judge import JudgeRequest, ProgressLine, build_request, run_judge
from .judge_llm import LlmConfig, LlmConfigError
from .report import (
    JSON_NAME,
    MD_NAME,
    OutError,
    ReportInputs,
    build_report,
    dumps,
    render_markdown,
    summary_line,
    write_reports,
)
from .results import ResultsError, join_results, parse_junit

log = logging.getLogger("speccheck")

JUDGE_MODES = ("none", "mock", "llm")
VERBOSE_LEVELS = ("INFO", "DEBUG")
PROGRESS_MODES = ("auto", "always", "never")
SELF_CHECK_FIXTURE = Path(__file__).parent / "_selfcheck"


class UsageError(Exception):
    """Exit 2."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


@dataclass(frozen=True)
class Config:
    spec: Path
    src: tuple[Path, ...]
    tests: tuple[Path, ...]
    results: Path | None
    root: Path
    out: Path
    judge: str
    strict: bool
    max_unknown: Decimal
    judge_concurrency: int
    judge_budget: int
    verbose: str | None
    llm: LlmConfig | None
    spec_arg: str
    progress: str = "auto"


@dataclass(frozen=True)
class Action:
    """What argv asked for: a check run, a self-check, or nothing more (help/version handled)."""

    kind: str  # "check" | "self-check"
    verbose: str | None
    config: Config | None = None


def build_parser() -> _Parser:
    parser = _Parser(prog="speccheck", description="Specification conformance checker")
    parser.add_argument("--version", action="version", version=f"speccheck {__version__}")
    parser.add_argument(
        "--self-check", action="store_true", help="run the packaged golden fixture in a temp dir"
    )
    parser.add_argument("--verbose", nargs="?", const="INFO", default=None, metavar="LEVEL")
    sub = parser.add_subparsers(dest="command")
    check = sub.add_parser("check", help="run the conformance pipeline")
    check.add_argument("--spec", required=True)
    check.add_argument("--src", action="append", default=None)
    check.add_argument("--tests", action="append", default=None)
    check.add_argument("--results", default=None)
    check.add_argument("--root", default=".")
    check.add_argument("--out", default=".")
    check.add_argument("--judge", default="none")
    check.add_argument("--strict", action="store_true")
    check.add_argument("--max-unknown", default="0.2")
    check.add_argument("--judge-concurrency", default="4")
    check.add_argument("--judge-budget", default="0")
    check.add_argument("--progress", default="auto")
    check.add_argument("--verbose", nargs="?", const="INFO", default=None, metavar="LEVEL")
    return parser


def _validate_verbose(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in VERBOSE_LEVELS:
        raise UsageError(f"--verbose: invalid level '{value}' (expected INFO or DEBUG)")
    return value


def _int_in_range(flag: str, text: str, low: int, high: int) -> int:
    try:
        value = int(text)
    except ValueError:
        raise UsageError(
            f"{flag}: invalid value '{text}' (expected an integer {low}..{high})"
        ) from None
    if not low <= value <= high:
        raise UsageError(f"{flag}: invalid value '{text}' (expected an integer {low}..{high})")
    return value


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _resolve_inside(raw: str, root: Path) -> Path:
    path = Path(raw).resolve()
    if not _inside(path, root):
        raise UsageError(f"path outside --root: {raw}")
    return path


def parse_config(argv: Sequence[str], environ: Mapping[str, str]) -> Action:
    """argv + env -> Action (exit 2 on any usage error; K-01)."""
    parser = build_parser()
    args = parser.parse_args(list(argv))
    verbose = _validate_verbose(args.verbose)
    if args.command is None:
        if args.self_check:
            return Action("self-check", verbose)
        raise UsageError("expected the 'check' subcommand, --self-check, or --version")
    if args.self_check:
        raise UsageError("--self-check cannot be combined with the 'check' subcommand")
    verbose = _validate_verbose(args.verbose) or verbose
    if args.judge not in JUDGE_MODES:
        raise UsageError(f"--judge: invalid value '{args.judge}' (expected none, mock, or llm)")
    try:
        max_unknown = Decimal(args.max_unknown)
    except InvalidOperation:
        raise UsageError(
            f"--max-unknown: invalid value '{args.max_unknown}' (expected a decimal in [0, 1])"
        ) from None
    if not max_unknown.is_finite() or not Decimal(0) <= max_unknown <= Decimal(1):
        raise UsageError(
            f"--max-unknown: invalid value '{args.max_unknown}' (expected a decimal in [0, 1])"
        )
    concurrency = _int_in_range("--judge-concurrency", args.judge_concurrency, 1, 32)
    budget = _int_in_range("--judge-budget", args.judge_budget, 0, 86400)
    if args.progress not in PROGRESS_MODES:
        raise UsageError(
            f"--progress: invalid value '{args.progress}' (expected auto, always, or never)"
        )

    root = Path(args.root).resolve()
    if not root.is_dir():
        raise UsageError(f"--root: not a directory: {args.root}")
    spec = _resolve_inside(args.spec, root)
    if not spec.is_file():
        raise UsageError(f"--spec: not a readable file: {args.spec}")
    try:
        with open(spec, "rb"):
            pass
    except OSError:
        raise UsageError(f"--spec: not a readable file: {args.spec}") from None

    def dirs(flag: str, values: list[str] | None, default: str) -> tuple[Path, ...]:
        if values is None:
            values = [default] if Path(default).is_dir() else []
        out: list[Path] = []
        for value in values:
            path = _resolve_inside(value, root)
            if not path.is_dir():
                raise UsageError(f"{flag}: not a directory: {value}")
            out.append(path)
        return tuple(out)

    src = dirs("--src", args.src, "src")
    tests = dirs("--tests", args.tests, "tests")
    results: Path | None = None
    if args.results is not None:
        results = _resolve_inside(args.results, root)
        if not results.is_file():
            raise UsageError(f"--results: not a readable file: {args.results}")
        try:
            with open(results, "rb"):
                pass
        except OSError:
            raise UsageError(f"--results: not a readable file: {args.results}") from None
    out = _resolve_inside(args.out, root)

    llm: LlmConfig | None = None
    if args.judge == "llm":
        try:
            llm = LlmConfig.from_env(environ)
        except LlmConfigError as exc:
            raise UsageError(str(exc)) from None
        if importlib.util.find_spec("httpx") is None:
            raise UsageError("--judge llm requires the [llm] extra (httpx is not installed)")

    config = Config(
        spec=spec,
        src=src,
        tests=tests,
        results=results,
        root=root,
        out=out,
        judge=args.judge,
        strict=bool(args.strict),
        max_unknown=max_unknown.quantize(Decimal("0.0001")),
        judge_concurrency=concurrency,
        judge_budget=budget,
        verbose=verbose,
        llm=llm,
        spec_arg=args.spec,
        progress=args.progress,
    )
    return Action("check", verbose, config)


# --------------------------------------------------------------------------------------------
# pipeline
# --------------------------------------------------------------------------------------------


class _Stage:
    def __init__(self, name: str) -> None:
        self.name = name
        self.t0 = time.perf_counter()

    def done(self, **counts: object) -> None:
        ms = int((time.perf_counter() - self.t0) * 1000)
        fields = " ".join(f"{k}={v}" for k, v in counts.items())
        log.info("stage=%s %s ms=%d", self.name, fields, ms)


def _excluded_paths(config: Config) -> frozenset[Path]:
    paths = {config.spec, config.out / JSON_NAME, config.out / MD_NAME}
    if config.results is not None:
        paths.add(config.results)
    return frozenset(paths)


def execute(config: Config, stdout: io.TextIOBase | None = None) -> int:
    """Run the §3.1 pipeline; returns the exit code (0/1) or raises the exit-3 exceptions."""
    root = config.root
    rel_spec = to_posix_relative(config.spec, root)
    notes: list[str] = []

    stage = _Stage("extract-spec")
    spec_text, replaced = decode_text(config.spec.read_bytes())
    if replaced:
        notes.append(f"invalid UTF-8 decoded with replacement: {rel_spec}")
    index = parse_spec(spec_text, rel_spec)
    notes.extend(index.notes)  # K-14 / E-46: one Note per truncated statement
    stage.done(ids=len(index.ids), retired=sum(1 for s in index.ids if s.retired))

    excluded = _excluded_paths(config)
    counters = ScanCounters()

    stage = _Stage("scan-src")
    src_files = scan_roots(config.src, root, excluded, config.out, counters)
    src_citations: list[Citation] = []
    for f in src_files:
        src_citations.extend(
            Citation(c.id, c.file, c.line, "src", None) for c in citations_in_file(f)
        )
    stage.done(files=len(src_files), citations=len(src_citations))

    stage = _Stage("scan-tests")
    test_files = scan_roots(config.tests, root, excluded, config.out, counters)
    test_citations: list[Citation] = []
    cases: list[TestCase] = []
    file_lines: dict[str, tuple[str, ...]] = {}
    for f in test_files:
        attributed, file_notes = attribute_file(f)
        notes.extend(file_notes)
        cases.extend(attributed.cases)
        cases.append(attributed.file_case)
        test_citations.extend(attributed.citations)
        file_lines[f.path] = f.lines
    notes.extend(counters.notes())
    stage.done(files=len(test_files), cases=len(cases), citations=len(test_citations))

    stage = _Stage("map-results")
    outcomes = {}
    unattributed = []
    if config.results is not None:
        raw_results = parse_junit(config.results.read_bytes())
        mapping = join_results(raw_results, cases)
        outcomes = mapping.outcomes
        unattributed = mapping.unattributed
        notes.extend(mapping.notes)
        stage.done(results=len(raw_results), joined=mapping.joined, unattributed=len(unattributed))
    else:
        stage.done(results=0, joined=0, unattributed=0)

    stage = _Stage("graph")
    graph = build_graph(index, src_citations, test_citations, outcomes, config.results is not None)
    stage.done(ids=len(graph.records), dangling=len(graph.dangling), stale=len(graph.stale))

    judge_available: bool | None = None
    prompt_sha: str | None = None
    if config.judge != "none":
        stage = _Stage("judge")
        provider, concurrency, budget = _make_provider(config)
        if config.judge == "llm":
            prompt_sha = provider.prompt_sha256
        requests: list[JudgeRequest] = []
        for rec, edge in eligible_edges(graph):
            requests.append(
                build_request(rec.id, rec.spec.text, edge.case, file_lines[edge.case.file])
            )
        progress = None
        if requests and _progress_enabled(config):
            progress = ProgressLine(sys.stderr, len(requests))
        # K-13 / F-201: the logger is silent while the indicator is displayed, so every judge
        # INFO line — including the mode/URL/model line — is emitted after run_judge returns.
        run = run_judge(
            provider,
            requests,
            concurrency=concurrency,
            budget_seconds=budget,
            progress=progress,
        )
        if config.judge == "llm":
            log.info(
                "judge=llm url=%s model=%s timeout=%s",
                config.llm.url,
                config.llm.model,
                config.llm.timeout,
            )
        else:
            log.info("judge=%s", config.judge)
        apply_verdicts(graph, run.verdicts)
        judge_available = run.available
        notes.extend(run.notes())
        stage.done(
            edges=len(requests),
            unknown=sum(1 for v in run.verdicts.values() if v.verdict == "UNKNOWN"),
        )

    stage = _Stage("report")
    report, _metrics = build_report(
        ReportInputs(
            spec_path=rel_spec,
            judge=config.judge,
            judge_available=judge_available,
            judge_prompt_sha256=prompt_sha,
            strict=config.strict,
            max_unknown=config.max_unknown,
            graph=graph,
            unattributed=unattributed,
            notes=notes,
        )
    )
    for note in report["notes"]:
        log.info("note: %s", note)
    json_text = dumps(report)
    md_text = render_markdown(report)
    write_reports(config.out, json_text, md_text)
    stage.done(out=to_posix_relative(config.out, root) if _inside(config.out, root) else ".")

    _emit_line(summary_line(report), stdout)
    return int(report["exit_code"])


def _progress_enabled(config: Config) -> bool:
    """R-30 / §5.1 / E-39: LLM judge only; never at DEBUG; `auto` means stderr is a TTY."""
    if config.judge != "llm" or config.verbose == "DEBUG" or config.progress == "never":
        return False
    if config.progress == "always":
        return True
    try:
        return bool(sys.stderr.isatty())
    except (AttributeError, ValueError):
        return False


def _make_provider(config: Config):
    if config.judge == "mock":
        from .judge_mock import MockJudge

        return MockJudge(), 1, 0
    from .judge_llm import LlmJudge

    assert config.llm is not None
    return LlmJudge(config.llm), config.judge_concurrency, config.judge_budget


def _emit_line(line: str, stream: io.TextIOBase | None) -> None:
    """R-21 / R-29: exactly one line, UTF-8 bytes regardless of locale."""
    target = stream if stream is not None else sys.stdout
    data = line + "\n"
    buffer = getattr(target, "buffer", None)
    if buffer is not None:
        target.flush()
        buffer.write(data.encode("utf-8"))
        buffer.flush()
    else:
        target.write(data)
        target.flush()


# --------------------------------------------------------------------------------------------
# --self-check (R-18, I-001 exemption, Q-003)
# --------------------------------------------------------------------------------------------


def install_socket_guard() -> None:
    """I-006: any socket creation for the rest of the process raises."""

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("speccheck: network I/O is forbidden (I-006)")

    socket.socket.__init__ = blocked  # type: ignore[method-assign]


def run_check(
    argv: Sequence[str], environ: Mapping[str, str], stdout: io.TextIOBase | None = None
) -> int:
    action = parse_config(argv, environ)
    assert action.config is not None
    return execute(action.config, stdout)


def self_check(
    stdout: io.TextIOBase | None = None, environ: Mapping[str, str] | None = None
) -> int:
    fixture = SELF_CHECK_FIXTURE
    tmp = Path(tempfile.mkdtemp(prefix="speccheck-selfcheck-")).resolve()
    cwd = os.getcwd()
    try:
        shutil.copytree(fixture, tmp, dirs_exist_ok=True)
        install_socket_guard()
        os.chdir(tmp)
        inner_stdout = io.StringIO()
        try:
            run_check(
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
                    "--strict",
                    "--root",
                    str(tmp),
                    "--out",
                    str(tmp / "out"),
                ],
                environ if environ is not None else os.environ,
                inner_stdout,
            )
        finally:
            os.chdir(cwd)
        for name in (JSON_NAME, MD_NAME):
            produced = tmp / "out" / name
            golden = tmp / "golden" / name
            if not produced.is_file():
                _emit_line(f"self-check: failed: {name} was not written", stdout)
                return 1
            if produced.read_bytes() != golden.read_bytes():
                _emit_line(f"self-check: mismatch: {name} differs from golden/{name}", stdout)
                return 1
        _emit_line("self-check: ok", stdout)
        return 0
    except (UsageError, SpecError, ResultsError, OutError) as exc:
        _emit_line(f"self-check: failed: {exc}", stdout)
        return 1
    finally:
        if os.getcwd() != cwd:
            os.chdir(cwd)
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------------------------


def configure_logging(verbose: str | None) -> None:
    """§5.3: one stderr StreamHandler, `%(levelname)s %(message)s`, ERROR unless --verbose."""
    for handler in list(log.handlers):
        log.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    log.addHandler(handler)
    log.propagate = False
    log.setLevel({"INFO": logging.INFO, "DEBUG": logging.DEBUG}.get(verbose or "", logging.ERROR))


def _peek_verbose(argv: Sequence[str]) -> str | None:
    """Best-effort look at --verbose before parsing, so usage errors log at the right level."""
    for i, arg in enumerate(argv):
        if arg == "--verbose":
            nxt = argv[i + 1] if i + 1 < len(argv) else None
            return nxt if nxt in VERBOSE_LEVELS else "INFO"
        if arg.startswith("--verbose="):
            value = arg.split("=", 1)[1]
            return value if value in VERBOSE_LEVELS else "INFO"
    return None


def main(argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    environ = os.environ if environ is None else environ
    configure_logging(_peek_verbose(argv))
    try:
        action = parse_config(argv, environ)
        configure_logging(action.verbose)
        if action.kind == "self-check":
            return self_check(environ=environ)
        assert action.config is not None
        return execute(action.config)
    except UsageError as exc:
        log.error("%s", exc)
        return 2
    except (SpecError, ResultsError, OutError) as exc:
        log.error("%s", exc)
        return 3
    except SystemExit as exc:  # argparse --help / --version
        code = exc.code
        return int(code) if isinstance(code, int) else 0
    except KeyboardInterrupt:  # E-41: SIGINT is a failure like any other, exit 3
        log.error("interrupted")
        log.debug("traceback", exc_info=True)
        return 3
    except Exception as exc:  # noqa: BLE001 - §5.4: any uncaught exception maps to 3
        log.error("internal error: %s: %s", type(exc).__name__, exc)
        log.debug("traceback", exc_info=True)
        return 3


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
