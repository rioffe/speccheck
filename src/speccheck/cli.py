"""CLI (§5): the only surface. Parses arguments, wires the §3.1 pipeline, applies the exit-code
(§5.4), summary-line (§5.1), and diagnostics (§5.3) contracts, and hosts `--self-check`.

Spec IDs realized here (§11): R-14, R-15, R-17, R-18, R-19, R-21, R-23, R-28, R-29, R-30, I-001,
    I-006, I-007, I-009, K-01, K-06, K-10, K-11, K-12, E-01, E-09, E-19, E-21, E-26, E-32, E-36,
    E-39, E-41, E-52, C-03 (PATHS list parsing, D-23), R-37, C-13, E-53, E-54 (the `impact`
    subcommand; v1.13), E-58 (`--judge-budget N%` requires a running triage; v1.15).
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
from .explain import render_trace
from .extract import (
    ID_RE,
    ScanCounters,
    SpecError,
    SpecIndex,
    citations_in_file,
    decode_text,
    edge_id_key,
    normalize_id,
    parse_spec,
    scan_roots,
    to_posix_relative,
)
from .graph import Graph, apply_verdicts, build_graph, eligible_edges
from .impact import (
    ChangedError,
    ReverifyEntry,
    WalkResult,
    diff_changed_set,
    mark_retired,
    resolve_changed_ids,
    reverify_set,
    walk,
)
from .jev import JevConfig, JevConfigError, JevTriage, run_triage
from .judge import JudgeRequest, ProgressLine, build_request, run_judge
from .judge_llm import LlmConfig, LlmConfigError, related_titles
from .report import (
    IMPACT_JSON_NAME,
    IMPACT_MD_NAME,
    JSON_NAME,
    MD_NAME,
    ImpactInputs,
    OutError,
    ReportInputs,
    build_impact_report,
    build_report,
    dumps,
    impact_summary_line,
    render_impact_markdown,
    render_markdown,
    summary_line,
    write_impact_reports,
    write_reports,
)
from .results import RawResult, ResultsError, join_results, parse_junit

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
    triage: bool = False  # K-16 (v1.15): --jev-pre-triage, ignored unless --judge llm
    budget_percent: int | None = None  # K-12's N% form; None for the SECONDS form
    jev: JevConfig | None = None  # C-17, read only when the triage pass runs


@dataclass(frozen=True)
class ImpactConfig:
    """v1.13 / C-13: `impact`'s own config; no results file, no judge."""

    spec: Path
    changed_raw: str | None
    against: Path | None
    src: tuple[Path, ...]
    tests: tuple[Path, ...]
    src_given: bool
    tests_given: bool
    root: Path
    out: Path
    depth: int
    verbose: str | None
    spec_arg: str
    against_arg: str | None


@dataclass(frozen=True)
class ExplainConfig:
    """v1.17 / C-18: `explain`'s own config — `check`'s config plus the one id and the walk depth.
    No `--out`: the trace is stdout-only (D-33), and the run writes nothing (I-016)."""

    check: Config
    ident: str
    depth: int


@dataclass(frozen=True)
class Action:
    """What argv asked for: a check run, an impact run, an explain run, a self-check, or nothing
    more (help/version handled)."""

    kind: str  # "check" | "impact" | "explain" | "self-check"
    verbose: str | None
    config: Config | None = None
    impact_config: ImpactConfig | None = None
    explain_config: ExplainConfig | None = None


def _expected(values: Sequence[str]) -> str:
    """The `expected …` phrase a finite flag's usage error prints and its help entry repeats — one
    source for both renderings, so they cannot disagree (C-19, T-95)."""
    if len(values) == 2:
        return f"{values[0]} or {values[1]}"
    return ", ".join(values[:-1]) + f", or {values[-1]}"


# C-19's range phrases: the same text the validators print (T-95).
MAX_UNKNOWN_RANGE = "a decimal in [0, 1]"
CONCURRENCY_RANGE = "an integer 1..32"
DEPTH_RANGE = "an integer 0..999"
BUDGET_SECONDS_RANGE = "an integer 0..86400"
BUDGET_PERCENT_RANGE = "an integer N% in 0..100"

ENVIRONMENT_EPILOG = """environment:
  SPECCHECK_JUDGE_URL, SPECCHECK_JUDGE_MODEL, SPECCHECK_JUDGE_API_KEY
                        required with --judge llm: the chat-completions endpoint, the model id
                        (passed through verbatim), and the bearer key -- never printed, at any
                        verbosity
  SPECCHECK_JUDGE_TIMEOUT
                        optional, seconds, an integer 1..300, default 30
  SPECCHECK_JEV_API_KEY required with --jev-pre-triage under --judge llm, and read only when the
                        triage pass runs (ignored under --judge none/mock, where no Jev request
                        is made)
  SPECCHECK_JEV_URL, SPECCHECK_JEV_MODEL
                        optional; default https://openrouter.ai/api/alpha/decisions and
                        ~typesafe/jev-latest
  SPECCHECK_JEV_TIMEOUT optional, seconds, an integer 1..300, default 30
  COLUMNS               optional; the width this help is wrapped to (nothing else in a run reads
                        it)
"""

EXIT_CODE_EPILOG = """exit codes:
  0 conforming   1 not conforming (check only)   2 usage error   3 input-contract violation
summary line (check, stdout, exactly one line):
  speccheck: <STATUS> - <passing>/<in_scope> passing (<pct>%), <failing> failing, <skipped>
  skipped, <weak> weak, <unverified> unverified, <untested> untested, <uncited> uncited;
  <dangling> dangling, <stale> stale; judge=<mode>
"""

_EPILOG = ENVIRONMENT_EPILOG + "\n" + EXIT_CODE_EPILOG
_FORMATTER = argparse.RawDescriptionHelpFormatter

_HELP_SPEC = (
    "the specification to check; decoded as UTF-8 (invalid bytes are replaced and noted). "
    "required; must resolve inside --root"
)
_HELP_SRC = (
    "source roots to scan for citations. repeatable; each value is a comma-separated list of "
    "files and/or directories. default: src if that directory exists, and only when the flag is "
    "absent; every element must resolve inside --root"
)
_HELP_TESTS = (
    "test roots; Python files are split into test cases with ast, Swift files by the line-based "
    "adapter, anything else is attributed at file level. repeatable, comma-separated, as --src. "
    "default: tests if that directory exists, and only when the flag is absent"
)
_HELP_RESULTS = (
    "JUnit XML results to join to the cited test cases; without it no cited ID can be better "
    "than UNVERIFIED. must resolve inside --root"
)
_HELP_ROOT = (
    "base directory for the reports' relative paths and for the containment rule: --spec, --src, "
    "--tests, --results, --out and every list element must resolve inside it. default: ."
)
_HELP_OUT = "where the reports are written. default: .; must resolve inside --root"
_HELP_JUDGE = (
    f"judge to use: {_expected(JUDGE_MODES)} -- llm is model-backed and requires "
    "SPECCHECK_JUDGE_*. default: none"
)
_HELP_MAX_UNKNOWN = (
    f"unknown_rate ceiling for --strict: {MAX_UNKNOWN_RANGE}. default: 0.2; consulted only with "
    "--strict --judge llm"
)
_HELP_CONCURRENCY = (
    f"judge requests in flight at once: {CONCURRENCY_RANGE}. default: 4; ignored unless "
    "--judge llm"
)
_HELP_BUDGET = (
    "judge-stage bound. SECONDS: " + BUDGET_SECONDS_RANGE + ", a wall-clock deadline; N%%: an "
    "integer 0..100 followed by %%, that share of the judge-eligible edges, least confident "
    "first (requires --jev-pre-triage with --judge llm, else exit 2). default: 0 (unlimited); "
    "ignored unless --judge llm"
)
_HELP_JEV = (
    "ask the C-17 Jev endpoint for one confidence per judge-eligible edge before judging, and "
    "issue the judge's queue least-confident first. default: off; ignored unless --judge llm "
    "(under --judge none/mock no Jev request is made and no SPECCHECK_JEV_* variable is read)"
)
_HELP_PROGRESS = (
    f"the judge progress indicator on stderr: {_expected(PROGRESS_MODES)} (auto draws it only "
    "when stderr is a TTY and verbosity is not DEBUG). default: auto; ignored unless --judge llm"
)
_HELP_VERBOSE = (
    f"diagnostics on stderr: {_expected(VERBOSE_LEVELS)} (DEBUG adds the judge request and "
    "response lines, with the API key redacted); bare --verbose means INFO. default: ERROR "
    "(nothing below ERROR reaches stderr)"
)
_HELP_DEPTH = f"walk depth: {DEPTH_RANGE} (0 = unbounded). default: 1"
_HELP_CHANGED = (
    "the changed set: a comma-separated list of ids declared in --spec (R/C/I/K/E/T or D). "
    "exactly one of --changed and --against is required"
)
_HELP_AGAINST = (
    "a prior version of the same spec; the changed set is the diff of its declarations. must "
    "resolve inside --root; exactly one of --changed and --against is required"
)
_HELP_IMPACT_SRC = (
    "source roots to list re-citations from. repeatable, comma-separated, as check's --src, but "
    "there is no directory default here: absent means not scanned"
)
_HELP_IMPACT_TESTS = (
    "test roots to list the citing test cases from. repeatable, comma-separated, as check's "
    "--tests, with no directory default here"
)
_HELP_ID = "the id to render, e.g. R-07; it must be declared in --spec, else exit 2"


def build_parser() -> _Parser:
    """The four parsers. Every argument definition carries a C-19 help entry: purpose, accepted
    values as literal tokens, the default, and the preconditions; the epilog carries the
    environment the kernel reads and the exit-code contract (v1.18, R-41/C-19)."""
    parser = _Parser(
        prog="speccheck",
        description="Specification conformance checker: traceability graph, JUnit results, "
        "model-judged test strength",
        epilog=_EPILOG,
        formatter_class=_FORMATTER,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"speccheck {__version__}",
        help="print the installed version and exit",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="run the packaged golden fixture in a temporary directory, compare its two reports "
        "with the packaged goldens byte for byte, and print 'self-check: ok' on a match. "
        "default: off",
    )
    parser.add_argument(
        "--verbose", nargs="?", const="INFO", default=None, metavar="LEVEL", help=_HELP_VERBOSE
    )
    sub = parser.add_subparsers(dest="command")
    check = sub.add_parser(
        "check",
        help="run the conformance pipeline",
        description="Run the conformance pipeline and write speccheck.json and "
        "SPEC_CONFORMANCE_REPORT.md under --out.",
        epilog=_EPILOG,
        formatter_class=_FORMATTER,
    )
    check.add_argument("--spec", required=True, metavar="FILE", help=_HELP_SPEC)
    check.add_argument("--src", action="append", default=None, metavar="PATHS", help=_HELP_SRC)
    check.add_argument(
        "--tests", action="append", default=None, metavar="PATHS", help=_HELP_TESTS
    )
    check.add_argument("--results", default=None, metavar="FILE", help=_HELP_RESULTS)
    check.add_argument("--root", default=".", metavar="DIR", help=_HELP_ROOT)
    check.add_argument("--out", default=".", metavar="DIR", help=_HELP_OUT)
    check.add_argument("--judge", default="none", metavar="MODE", help=_HELP_JUDGE)
    check.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 unless every in-scope ID is PASSING with no dangling or stale citation and, "
        "with --judge llm, the judge was available and unknown_rate <= --max-unknown. default: off",
    )
    check.add_argument(
        "--max-unknown", default="0.2", metavar="FRACTION", help=_HELP_MAX_UNKNOWN
    )
    check.add_argument(
        "--judge-concurrency", default="4", metavar="N", help=_HELP_CONCURRENCY
    )
    check.add_argument(
        "--judge-budget", default="0", metavar="SECONDS|N%", help=_HELP_BUDGET
    )
    check.add_argument("--jev-pre-triage", action="store_true", help=_HELP_JEV)
    check.add_argument("--progress", default="auto", metavar="MODE", help=_HELP_PROGRESS)
    check.add_argument(
        "--verbose", nargs="?", const="INFO", default=None, metavar="LEVEL", help=_HELP_VERBOSE
    )
    impact = sub.add_parser(
        "impact",
        help="report change impact from spec-internal edges",
        description="Walk the spec's own cross-references from a changed set and write impact.json "
        "and IMPACT_REPORT.md under --out.",
        epilog=_EPILOG,
        formatter_class=_FORMATTER,
    )
    impact.add_argument("--spec", required=True, metavar="FILE", help=_HELP_SPEC)
    impact.add_argument("--changed", default=None, metavar="IDS", help=_HELP_CHANGED)
    impact.add_argument("--against", default=None, metavar="FILE", help=_HELP_AGAINST)
    impact.add_argument(
        "--src", action="append", default=None, metavar="PATHS", help=_HELP_IMPACT_SRC
    )
    impact.add_argument(
        "--tests", action="append", default=None, metavar="PATHS", help=_HELP_IMPACT_TESTS
    )
    impact.add_argument("--root", default=".", metavar="DIR", help=_HELP_ROOT)
    impact.add_argument("--out", default=".", metavar="DIR", help=_HELP_OUT)
    impact.add_argument("--depth", default="1", metavar="N", help=_HELP_DEPTH)
    impact.add_argument(
        "--verbose", nargs="?", const="INFO", default=None, metavar="LEVEL", help=_HELP_VERBOSE
    )
    # v1.17 / R-40: `explain` takes `check`'s flags minus `--out` and `--strict` (both undefined
    # here, so argparse rejects them — E-54's pattern) plus a positional id and `--depth`.
    explain = sub.add_parser(
        "explain",
        help="render one id's evidence trail (C-18)",
        description="Run the same pipeline as check and render one id's trace to stdout; writes "
        "no report file.",
        epilog=_EPILOG,
        formatter_class=_FORMATTER,
    )
    explain.add_argument("id", metavar="ID", help=_HELP_ID)
    explain.add_argument("--spec", required=True, metavar="FILE", help=_HELP_SPEC)
    explain.add_argument("--src", action="append", default=None, metavar="PATHS", help=_HELP_SRC)
    explain.add_argument(
        "--tests", action="append", default=None, metavar="PATHS", help=_HELP_TESTS
    )
    explain.add_argument("--results", default=None, metavar="FILE", help=_HELP_RESULTS)
    explain.add_argument("--root", default=".", metavar="DIR", help=_HELP_ROOT)
    explain.add_argument("--judge", default="none", metavar="MODE", help=_HELP_JUDGE)
    explain.add_argument(
        "--max-unknown",
        default="0.2",
        metavar="FRACTION",
        help=_HELP_MAX_UNKNOWN + " (inert here: explain has no --strict)",
    )
    explain.add_argument(
        "--judge-concurrency", default="4", metavar="N", help=_HELP_CONCURRENCY
    )
    explain.add_argument(
        "--judge-budget", default="0", metavar="SECONDS|N%", help=_HELP_BUDGET
    )
    explain.add_argument("--jev-pre-triage", action="store_true", help=_HELP_JEV)
    explain.add_argument("--progress", default="auto", metavar="MODE", help=_HELP_PROGRESS)
    explain.add_argument("--depth", default="1", metavar="N", help=_HELP_DEPTH)
    explain.add_argument(
        "--verbose", nargs="?", const="INFO", default=None, metavar="LEVEL", help=_HELP_VERBOSE
    )
    return parser


def _validate_verbose(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in VERBOSE_LEVELS:
        raise UsageError(
            f"--verbose: invalid level '{value}' (expected {_expected(VERBOSE_LEVELS)})"
        )
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


def _parse_budget(text: str) -> tuple[int, int | None]:
    """K-12 (v1.15): `SECONDS` (integer 0..86400) or `N%` (integer 0..100 followed by '%').
    Returns (seconds, percent); exactly one is meaningful, the other is its zero value."""
    if text.endswith("%"):
        digits = text[:-1]
        expected = f"expected SECONDS or {BUDGET_PERCENT_RANGE}"
        if not digits.isdigit():
            raise UsageError(f"--judge-budget: invalid value '{text}' ({expected})")
        percent = int(digits)
        if not 0 <= percent <= 100:
            raise UsageError(f"--judge-budget: invalid value '{text}' ({expected})")
        return 0, percent
    return _int_in_range("--judge-budget", text, 0, 86400), None


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _resolve_inside(raw: str, root: Path) -> Path:
    path = Path(raw).resolve()
    if not _inside(path, root):
        raise UsageError(f"path outside --root: {raw}")
    return path


def _resolve_paths(
    flag: str, values: list[str] | None, root: Path, default: str | None
) -> tuple[Path, ...]:
    """C-03 PATHS / D-23: each occurrence is a comma-separated list of files and/or
    directories. Split on the literal ',', trim each segment (" " and "\t"), and drop
    every empty segment (no Note, no error); resolve each surviving segment inside --root
    (E-09, symlinks resolved to their target per Q-007); and deduplicate the resolved
    paths so a file reached by two elements is scanned once. A segment resolved inside
    --root that is neither a directory nor a regular file is a usage error (E-52),
    replacing the former "not a directory" check. `default` applies only when the flag is
    entirely absent; `impact` (v1.13) passes `None`, so an absent flag means "not scanned"
    rather than the `src`/`tests` directory default `check` uses."""
    if values is None:
        values = [default] if default is not None and Path(default).is_dir() else []
    out: list[Path] = []
    seen: set[Path] = set()
    for value in values:
        for raw in value.split(","):
            segment = raw.strip(" \t")
            if not segment:
                continue  # D-23: an empty/whitespace-only segment is dropped, no Note/error
            path = _resolve_inside(segment, root)  # E-09 containment, after symlink resolve
            if not (path.is_dir() or path.is_file()):
                # E-52: resolved inside --root but neither a directory nor a regular file
                raise UsageError(f"{flag}: no such file or directory: {segment}")
            if path in seen:  # I-012 / C-03 step 5: deduplicate the resolved paths
                continue
            seen.add(path)
            out.append(path)
    return tuple(out)


def _build_impact_config(args: argparse.Namespace, verbose: str | None) -> ImpactConfig:
    """v1.13 / C-13: `impact`'s own validation. `--results`/`--judge`/`--strict`/etc. are not
    defined on this subparser at all, so argparse rejects them as unrecognized arguments (E-54)."""
    if (args.changed is None) == (args.against is None):
        raise UsageError("impact: exactly one of --changed, --against is required")  # E-54
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
    against: Path | None = None
    if args.against is not None:
        against = _resolve_inside(args.against, root)
        if not against.is_file():
            raise UsageError(f"--against: not a readable file: {args.against}")
        try:
            with open(against, "rb"):
                pass
        except OSError:
            raise UsageError(f"--against: not a readable file: {args.against}") from None
    depth = _int_in_range("--depth", args.depth, 0, 999)
    src = _resolve_paths("--src", args.src, root, None)
    tests = _resolve_paths("--tests", args.tests, root, None)
    out = _resolve_inside(args.out, root)
    return ImpactConfig(
        spec=spec,
        changed_raw=args.changed,
        against=against,
        src=src,
        tests=tests,
        src_given=args.src is not None,
        tests_given=args.tests is not None,
        root=root,
        out=out,
        depth=depth,
        verbose=verbose,
        spec_arg=args.spec,
        against_arg=args.against,
    )


def _build_explain_config(
    args: argparse.Namespace, environ: Mapping[str, str], verbose: str | None
) -> ExplainConfig:
    """v1.17 / R-40: `explain`'s validation — `check`'s own, with the id and `--depth` added. The
    id is checked against the spec's declarations in `execute_explain` (E-60 needs the parse)."""
    depth = _int_in_range("--depth", args.depth, 0, 999)
    return ExplainConfig(_build_check_config(args, environ, verbose), args.id, depth)


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
    if args.command == "impact":
        return Action("impact", verbose, impact_config=_build_impact_config(args, verbose))
    if args.command == "explain":
        return Action(
            "explain",
            verbose,
            explain_config=_build_explain_config(args, environ, verbose),
        )
    return Action("check", verbose, config=_build_check_config(args, environ, verbose))


def _build_check_config(
    args: argparse.Namespace, environ: Mapping[str, str], verbose: str | None
) -> Config:
    """The `check` validation (C-03, C-09, E-09, E-52, E-58, K-11, K-12). `explain` reuses it:
    its subparser defines neither `--out` nor `--strict`, so both fall back here (D-33: the trace
    is stdout-only, and nothing it renders is pass/fail)."""
    out_arg = getattr(args, "out", ".")
    strict = bool(getattr(args, "strict", False))
    if args.judge not in JUDGE_MODES:
        raise UsageError(
            f"--judge: invalid value '{args.judge}' (expected {_expected(JUDGE_MODES)})"
        )
    try:
        max_unknown = Decimal(args.max_unknown)
    except InvalidOperation:
        raise UsageError(
            f"--max-unknown: invalid value '{args.max_unknown}' (expected {MAX_UNKNOWN_RANGE})"
        ) from None
    if not max_unknown.is_finite() or not Decimal(0) <= max_unknown <= Decimal(1):
        raise UsageError(
            f"--max-unknown: invalid value '{args.max_unknown}' (expected {MAX_UNKNOWN_RANGE})"
        )
    concurrency = _int_in_range("--judge-concurrency", args.judge_concurrency, 1, 32)
    budget, budget_percent = _parse_budget(args.judge_budget)
    triage = bool(args.jev_pre_triage)
    if budget_percent is not None and not (triage and args.judge == "llm"):
        # E-58: the N% form has no ordering to issue in — either the flag is absent, or K-16
        # ignores it under --judge none/mock. The SECONDS form keeps its own rule below.
        raise UsageError("--judge-budget N% requires --jev-pre-triage with --judge llm")
    if args.progress not in PROGRESS_MODES:
        raise UsageError(
            f"--progress: invalid value '{args.progress}' (expected {_expected(PROGRESS_MODES)})"
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

    src = _resolve_paths("--src", args.src, root, "src")
    tests = _resolve_paths("--tests", args.tests, root, "tests")
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
    out = _resolve_inside(out_arg, root)

    llm: LlmConfig | None = None
    if args.judge == "llm":
        try:
            llm = LlmConfig.from_env(environ)
        except LlmConfigError as exc:
            raise UsageError(str(exc)) from None
        if importlib.util.find_spec("httpx") is None:
            raise UsageError("--judge llm requires the [llm] extra (httpx is not installed)")

    # C-17: the four JEV variables are read only when the triage pass actually runs, so
    # --jev-pre-triage under --judge none/mock needs no credential (K-16).
    jev: JevConfig | None = None
    triage_runs = triage and args.judge == "llm"
    if triage_runs:
        try:
            jev = JevConfig.from_env(environ)
        except JevConfigError as exc:
            raise UsageError(str(exc)) from None

    config = Config(
        spec=spec,
        src=src,
        tests=tests,
        results=results,
        root=root,
        out=out,
        judge=args.judge,
        strict=strict,
        max_unknown=max_unknown.quantize(Decimal("0.0001")),
        judge_concurrency=concurrency,
        judge_budget=budget,
        verbose=verbose,
        llm=llm,
        spec_arg=args.spec,
        progress=args.progress,
        triage=triage_runs,
        budget_percent=budget_percent,
        jev=jev,
    )
    return config


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


def _impact_excluded_paths(config: ImpactConfig) -> frozenset[Path]:
    paths = {config.spec, config.out / IMPACT_JSON_NAME, config.out / IMPACT_MD_NAME}
    if config.against is not None:
        paths.add(config.against)
    return frozenset(paths)


@dataclass
class _Stages:
    """What the §3.1 stages produce, for whichever renderer asked for them (v1.17)."""

    index: SpecIndex
    graph: Graph
    unattributed: list[RawResult]
    notes: list[str]
    judge_available: bool | None
    prompt_sha: str | None


def _run_stages(config: Config) -> _Stages:
    """The §3.1 stages every subcommand shares: extract-spec, scan-src, scan-tests, map-results,
    graph, and — unless `--judge none` — triage and judge (v1.17: `check` and `explain` both call
    this, so the two surfaces cannot disagree about a status; I-016)."""
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
        # E-56: a "src"-kind citation is never DECLARED
        src_citations.extend(
            Citation(c.id, c.file, c.line, "src", None, False) for c in citations_in_file(f)
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
                build_request(
                    rec.id,
                    rec.spec.text,
                    edge.case,
                    file_lines[edge.case.file],
                    edge.declared,  # C-15: DECLARED vs INCIDENTAL for this edge
                    related_titles(rec.id, index),  # R-38: the C-12 neighbourhood's titles
                )
            )
        progress = None
        if requests and _progress_enabled(config):
            progress = ProgressLine(sys.stderr, len(requests))
        # K-16 (v1.15): the triage pass runs before any real-judge request is issued, and its
        # answer is used for the issue order and nothing else (I-015).
        if config.triage and requests:
            triage_stage = _Stage("triage")
            triage = run_triage(
                _make_triage_provider(config), requests, concurrency=concurrency
            )
            requests = triage.order
            notes.extend(triage.notes())
            assert config.jev is not None
            log.info(
                "jev url=%s model=%s timeout=%s",
                config.jev.url,
                config.jev.model,
                config.jev.timeout,
            )
            triage_stage.done(edges=len(requests), failed=triage.failures)
            if config.budget_percent is None and config.judge_budget == 0:
                # D-30: the pass paid Jev's cost for no effect on the report.
                notes.append("jev-pre-triage had no effect: --judge-budget is unlimited")
        # K-12's N% form: exactly ceil(N/100 x E) of the E eligible edges are issued.
        issue_count = None
        if config.budget_percent is not None:
            issue_count = -(-config.budget_percent * len(requests) // 100)
        # K-13 / F-201: the logger is silent while the indicator is displayed, so every judge
        # INFO line — including the mode/URL/model line — is emitted after run_judge returns.
        run = run_judge(
            provider,
            requests,
            concurrency=concurrency,
            budget_seconds=budget,
            issue_count=issue_count,
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

    return _Stages(index, graph, unattributed, notes, judge_available, prompt_sha)


def execute(config: Config, stdout: io.TextIOBase | None = None) -> int:
    """Run the §3.1 pipeline and write both reports; returns the exit code (0/1) or raises the
    exit-3 exceptions."""
    root = config.root
    rel_spec = to_posix_relative(config.spec, root)
    stages = _run_stages(config)
    index, graph, notes = stages.index, stages.graph, stages.notes
    unattributed = stages.unattributed
    judge_available, prompt_sha = stages.judge_available, stages.prompt_sha

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
            decisions=index.decisions,
            edges=index.edges,
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


def execute_explain(config: ExplainConfig, stdout: io.TextIOBase | None = None) -> int:
    """v1.17 / R-40, C-18: run the §3.1 stages and render one id's trace to stdout. It writes no
    file at all (D-33, I-016), so there is no `--out` and no exit `1`: `0` once the trace is
    written, `2` for an undeclared id (E-60), `3` for an input-contract violation (§5.4)."""
    check = config.check
    stages = _run_stages(check)
    by_id = stages.index.by_id()
    ident = config.ident.strip()
    match = ID_RE.fullmatch(ident)
    normalized = (
        normalize_id(match.group(1), int(match.group(2))) if match is not None else None
    )
    if normalized is None or normalized not in by_id:
        raise UsageError(f"explain: undeclared id: {ident}")
    rec = next(r for r in stages.graph.records if r.id == normalized)

    # C-12/C-13 (D-34): the same walk and reverify set `impact` reports, from this one id.
    result = walk(stages.index.edges, {normalized}, config.depth)
    impact = mark_retired(result.impact, stages.index)
    if result.beyond_depth:
        log.info(
            "note: %d further id(s) beyond --depth %d; --depth 0 lists them",
            result.beyond_depth,
            config.depth,
        )
    walked = {e.id for e in impact}
    reverify = tuple(
        ReverifyEntry(r.id, by_id[r.id].retired if r.id in by_id else False, r.verifies)
        for r in reverify_set(stages.index.edges, {normalized} | walked)
    )
    for note in stages.notes:
        log.info("note: %s", note)
    _emit_text(
        render_trace(rec, WalkResult(impact, result.beyond_depth), reverify, config.depth),
        stdout,
    )
    return 0


def execute_impact(config: ImpactConfig, stdout: io.TextIOBase | None = None) -> int:
    """v1.13 / C-13: the `impact` pipeline. Always exits 0 once the reports are written --
    nothing here is pass/fail."""
    root = config.root
    rel_spec = to_posix_relative(config.spec, root)
    notes: list[str] = []

    spec_text, replaced = decode_text(config.spec.read_bytes())
    if replaced:
        notes.append(f"invalid UTF-8 decoded with replacement: {rel_spec}")
    index = parse_spec(spec_text, rel_spec)
    notes.extend(index.notes)

    against_path: str | None = None
    if config.changed_raw is not None:
        try:
            changed = resolve_changed_ids(index, config.changed_raw)
        except ChangedError as exc:
            raise UsageError(str(exc)) from None
    else:
        assert config.against is not None
        against_path = to_posix_relative(config.against, root)
        against_text, against_replaced = decode_text(config.against.read_bytes())
        if against_replaced:
            notes.append(f"invalid UTF-8 decoded with replacement: {against_path}")
        try:
            old_index = parse_spec(against_text, against_path)
        except SpecError as exc:
            raise SpecError(f"--against: {exc}") from None
        changed = diff_changed_set(old_index, index)

    changed_ids = {c.id for c in changed}
    result = walk(index.edges, changed_ids, config.depth)
    impact = mark_retired(result.impact, index)
    if result.beyond_depth:
        notes.append(
            f"{result.beyond_depth} further id(s) beyond --depth {config.depth}; "
            "--depth 0 lists them"
        )
    impact_ids = {e.id for e in impact}
    reverify_raw = reverify_set(index.edges, changed_ids | impact_ids)
    by_id = index.by_id()
    reverify = tuple(
        ReverifyEntry(r.id, by_id[r.id].retired if r.id in by_id else False, r.verifies)
        for r in reverify_raw
    )
    target_ids = changed_ids | impact_ids | {r.id for r in reverify}

    recite: list[dict] = []
    test_cases: list[dict] = []
    if config.src_given or config.tests_given:
        excluded = _impact_excluded_paths(config)
        counters = ScanCounters()
        if config.src_given:
            src_files = scan_roots(config.src, root, excluded, config.out, counters)
            hits: dict[str, dict[str, set[int]]] = {}
            for f in src_files:
                for c in citations_in_file(f):
                    if c.id in target_ids:
                        hits.setdefault(c.id, {}).setdefault(f.path, set()).add(c.line)
            for ident in sorted(hits, key=edge_id_key):
                for file in sorted(hits[ident]):
                    recite.append(
                        {"id": ident, "file": file, "lines": sorted(hits[ident][file])}
                    )
        if config.tests_given:
            test_files = scan_roots(config.tests, root, excluded, config.out, counters)
            case_rows = []
            for f in test_files:
                attributed, file_notes = attribute_file(f)
                notes.extend(file_notes)
                all_cases = list(attributed.cases) + [attributed.file_case]
                for case in all_cases:
                    cited = {
                        c.id
                        for c in attributed.citations
                        if c.id in target_ids and c.testcase == case
                    }
                    ids_here = sorted(cited, key=edge_id_key)
                    if ids_here:
                        row = (case.file, case.start, case.name, case.classname, ids_here)
                        case_rows.append(row)
            case_rows.sort(key=lambda r: (r[0], r[1]))
            for file, _start, name, classname, ids_here in case_rows:
                test_cases.append(
                    {"file": file, "name": name, "classname": classname, "ids": ids_here}
                )
        notes.extend(counters.notes())

    inputs = ImpactInputs(
        spec_path=rel_spec,
        against_path=against_path,
        depth=config.depth,
        changed=changed,
        impact=impact,
        reverify=reverify,
        recite=recite,
        test_cases=test_cases,
        notes=notes,
    )
    report = build_impact_report(inputs)
    json_text = dumps(report)
    md_text = render_impact_markdown(
        report, src_given=config.src_given, tests_given=config.tests_given
    )
    write_impact_reports(config.out, json_text, md_text)
    _emit_line(impact_summary_line(report), stdout)
    return 0


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


def _make_triage_provider(config: Config) -> JevTriage:
    """K-16's provider seam; tests replace this to feed fixed confidences."""
    assert config.jev is not None
    return JevTriage(config.jev)


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


def _emit_text(text: str, stream: io.TextIOBase | None) -> None:
    """C-18: the trace, written as UTF-8 bytes regardless of locale (R-29), exactly as rendered."""
    target = stream if stream is not None else sys.stdout
    buffer = getattr(target, "buffer", None)
    if buffer is not None:
        target.flush()
        buffer.write(text.encode("utf-8"))
        buffer.flush()
    else:
        target.write(text)
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
        if action.kind == "impact":
            assert action.impact_config is not None
            return execute_impact(action.impact_config)
        if action.kind == "explain":
            assert action.explain_config is not None
            return execute_explain(action.explain_config)
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
