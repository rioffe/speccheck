"""§9.14 CLI help (C-19; v1.18)."""

from __future__ import annotations

import argparse
import os
import re
import socket
from pathlib import Path

from speccheck import cli

from .conftest import FIXTURE, run_cli

GOLDEN_DIR = Path(__file__).resolve().parent / "data" / "help"
SCREENS = {
    "speccheck": ["--help"],
    "check": ["check", "--help"],
    "impact": ["impact", "--help"],
    "explain": ["explain", "--help"],
}
# C-19's metavar vocabulary: the value shapes §5.1's synopsis names
METAVARS = {"PATHS", "FILE", "DIR", "IDS", "ID", "MODE", "FRACTION", "N", "SECONDS|N%", "LEVEL"}
# T-95's oracle: each finite-set flag, a value its validator rejects, and the message it prints
# (subcommand, flag, a value its validator rejects, whether the accepted set is enumerable)
FINITE = [
    ("check", "--judge", "bogus", True),
    ("check", "--progress", "sometimes", True),
    ("check", "--verbose", "TRACE", True),
    ("check", "--max-unknown", "2", False),  # a range, not a token list
    ("check", "--judge-concurrency", "99", False),
    ("impact", "--depth", "x", False),
]
LLM_ENV = {
    "SPECCHECK_JUDGE_URL": "http://localhost:11434/v1/chat/completions",
    "SPECCHECK_JUDGE_MODEL": "m",
    "SPECCHECK_JUDGE_API_KEY": "sk-secret",
}


def _iter_actions(parser: argparse.ArgumentParser):
    """Every argument definition of `parser` and, recursively, of its subparsers."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for choice, sub in action.choices.items():
                listing = {c.dest: c.help for c in action._choices_actions}[choice]
                assert listing and sub.description, f"{choice}: no help in the listing"
                yield from _iter_actions(sub)
            continue
        yield action


def _help_text(tmp_path: Path, argv: list[str]) -> str:
    run = run_cli(argv, tmp_path)
    assert run.code == 0, run.stderr
    return run.stdout


def test_t96_every_flag_documents_itself(tmp_path: Path):
    """T-96: every argument definition of the four parsers except `-h` carries a non-empty help
    string; each value-taking flag's metavar comes from C-19's vocabulary (never an argparse dest
    name) and its entry names its default where it has one; and each of the four `--help` screens,
    run from an empty directory with the socket guard installed, exits 0, writes a non-empty screen
    to stdout and nothing to stderr. (R-41, C-19, I-017)"""
    parser = cli.build_parser()
    for action in _iter_actions(parser):
        if action.dest == "help":
            continue
        assert action.help, f"{action.dest} has no help string"
        takes_value = action.nargs != 0 and not isinstance(
            action, (argparse._StoreTrueAction, argparse._VersionAction, argparse._HelpAction)
        )
        if takes_value:
            assert action.metavar in METAVARS, f"{action.dest}: metavar {action.metavar!r}"
        if action.default not in (None, False) and takes_value:
            assert "default" in action.help, f"{action.dest}: no default in its help"

    cli.install_socket_guard()
    try:
        empty = tmp_path / "empty"
        empty.mkdir()
        for name, argv in SCREENS.items():
            run = run_cli(argv, empty, env=LLM_ENV)
            assert run.code == 0, (name, run.stderr)
            assert run.stdout.strip(), name
            assert run.stderr == "", name
    finally:
        # undo the guard for the rest of the suite
        socket.socket.__init__ = _ORIGINAL_SOCKET_INIT


_ORIGINAL_SOCKET_INIT = socket.socket.__init__


def test_t95_help_values_match_the_validator(tmp_path: Path):
    """T-95: for every flag whose accepted set is finite, the value tokens and range text named in
    its `--help` entry equal those named in the message the same flag's own usage error prints, and
    every token the help names is accepted — a run carrying it exits other than `2`, while the
    control `bogus` exits `2`. (R-41, C-19)"""
    target = tmp_path / "target"
    import shutil

    shutil.copytree(FIXTURE, target)
    for subcommand, flag, bad, enumerable in FINITE:
        screen = _help_text(target, [subcommand, "--help"])
        # each subcommand's own required companions, so the flag's validator is what fires
        companions = ["--changed", "K-02"] if subcommand == "impact" else []
        rejected = run_cli(
            [subcommand, flag, bad, "--spec", "SPEC.md", *companions], target
        )
        assert rejected.code == 2, (subcommand, flag, rejected.stderr)
        phrase = re.search(r"\(expected (.+)\)\s*$", rejected.stderr.strip())
        assert phrase, rejected.stderr
        assert phrase.group(1) in " ".join(screen.split()), (flag, phrase.group(1))
        # every token the help names for this flag is accepted by the parser
        if not enumerable:
            continue
        tokens = [t for t in re.split(r",| or ", phrase.group(1)) if t.strip()]
        for token in tokens:
            token = token.strip()
            if not token or ".." in token or "[" in token:
                continue  # a range, not an enumerable token
            accepted = run_cli(
                ["check", "--spec", "SPEC.md", "--src", "src", "--tests", "tests", flag, token],
                target,
                env=LLM_ENV,
            )
            assert accepted.code != 2, (flag, token, accepted.stderr)

    # `--judge-budget`'s two forms and its E-58 companion rule are stated where the error states them
    screen = _help_text(target, ["check", "--help"])
    flat = " ".join(screen.split())
    assert "SECONDS|N%" in flat
    assert "requires --jev-pre-triage with --judge llm" in flat
    companion = run_cli(["check", "--judge-budget", "5%", "--spec", "SPEC.md"], target)
    assert companion.code == 2 and "requires --jev-pre-triage" in companion.stderr

    control = run_cli(["check", "--judge", "bogus", "--spec", "SPEC.md"], target)
    assert control.code == 2


def test_t98_environment_block_matches_the_code(tmp_path: Path):
    """T-98: the `environment:` block names exactly the variables the kernel reads and no others —
    the `SPECCHECK_[A-Z_]+` string literals in `src/speccheck/*.py` equal the set the rendered
    `check --help` block lists, each with its read condition and requiredness — and no `_API_KEY`
    value ever appears in a help screen or a usage error. (R-41, C-19, R-23)"""
    source_dir = Path(cli.__file__).resolve().parent
    in_code = set()
    for path in sorted(source_dir.glob("*.py")):
        literals = re.findall(r"SPECCHECK_[A-Z_]+", path.read_text(encoding="utf-8"))
        in_code.update(name for name in literals if not name.endswith("_"))
    assert len(in_code) == 8, sorted(in_code)

    screen = _help_text(tmp_path, ["check", "--help"])
    block = screen.split("environment:", 1)[1]
    in_block = set(re.findall(r"SPECCHECK_[A-Z_]+", block))
    assert in_block == in_code, sorted(in_code ^ in_block)
    # the read conditions and requiredness are stated, not just the names
    assert "required with --judge llm" in block
    assert "optional" in block and "default 30" in block
    assert "ignored under --judge none/mock" in block or "read only when" in block
    assert "COLUMNS" in block  # D-41

    # a value never appears: the screen is rendered with a key in the environment
    run = run_cli(["check", "--help"], tmp_path, env=LLM_ENV)
    assert "sk-secret" not in run.stdout
    leaked = run_cli(["check", "--spec", "SPEC.md", "--judge", "bogus"], tmp_path, env=LLM_ENV)
    assert "sk-secret" not in leaked.stderr


def test_t97_help_screens_match_their_goldens(tmp_path: Path):
    """T-97: with `COLUMNS=80` fixed, the four `--help` screens render byte-stable text equal to the
    goldens checked in under `tests/data/help/`, so a dropped value token, a dropped default, a new
    flag without help, or an unintended rewording is a visible diff. (R-41, C-19, D-39)"""
    env = dict(os.environ, COLUMNS="80")
    for name, argv in SCREENS.items():
        run = run_cli(argv, tmp_path, env=env)
        assert run.code == 0, run.stderr
        golden = (GOLDEN_DIR / f"{name}_help.txt").read_text(encoding="utf-8")
        assert run.stdout == golden, name
