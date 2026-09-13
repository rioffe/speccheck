"""Shared helpers for the §9 suite: an in-process runner and a tiny project builder."""

from __future__ import annotations

import io
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest

from speccheck import cli

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "target"
DATA = Path(__file__).resolve().parent / "data"


@dataclass
class Run:
    code: int
    stdout: str
    stderr: str
    cwd: Path

    @property
    def json(self) -> dict:
        return json.loads((self.cwd / "speccheck.json").read_text(encoding="utf-8"))

    def json_at(self, out: Path) -> dict:
        return json.loads((out / "speccheck.json").read_text(encoding="utf-8"))

    def md_at(self, out: Path) -> str:
        return (out / "SPEC_CONFORMANCE_REPORT.md").read_text(encoding="utf-8")

    @property
    def md(self) -> str:
        return self.md_at(self.cwd)

    def ids(self) -> dict[str, dict]:
        return {rec["id"]: rec for rec in self.json["ids"]}

    def status(self, ident: str) -> str:
        return self.ids()[ident]["status"]


class TtyWrapper(io.TextIOWrapper):
    """A captured stream that claims to be a terminal (T-63: `--progress auto` on a TTY)."""

    def isatty(self) -> bool:
        return True


def run_cli(
    argv: list[str], cwd: Path, env: Mapping[str, str] | None = None, *, tty: bool = False
) -> Run:
    """Run `speccheck <argv>` in-process with cwd set and stdout/stderr captured as bytes;
    `tty=True` makes the captured stderr report isatty() == True."""
    out_buf, err_buf = io.BytesIO(), io.BytesIO()
    out = io.TextIOWrapper(out_buf, encoding="utf-8", write_through=True)
    err_cls = TtyWrapper if tty else io.TextIOWrapper
    err = err_cls(err_buf, encoding="utf-8", write_through=True)
    old_cwd = os.getcwd()
    old_out, old_err = sys.stdout, sys.stderr
    os.chdir(cwd)
    sys.stdout, sys.stderr = out, err
    try:
        code = cli.main(argv, environ=dict(env) if env is not None else {})
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        os.chdir(old_cwd)
        out.flush()
        err.flush()
    return Run(code, out_buf.getvalue().decode("utf-8"), err_buf.getvalue().decode("utf-8"), cwd)


def spec_table(
    rows: list[tuple[str, str]], *, retired: set[str] = frozenset(), extra: str = ""
) -> str:
    """A minimal SPEC.md: one table with (id, statement) rows; IDs in `retired` are struck."""
    lines = ["# Spec", "", "| ID | Statement |", "| -- | --------- |"]
    for ident, statement in rows:
        cell = f"~~**{ident}**~~" if ident in retired else f"**{ident}**"
        lines.append(f"| {cell} | {statement} |")
    return "\n".join(lines) + "\n" + extra


def junit(cases: list[tuple[str, str, str]], root: str = "testsuites") -> str:
    """cases: (classname, name, outcome) with outcome in passed/failed/error/skipped."""
    body = []
    for classname, name, outcome in cases:
        child = {
            "passed": "",
            "failed": "<failure/>",
            "error": "<error/>",
            "skipped": "<skipped/>",
        }[outcome]
        body.append(f'<testcase classname="{classname}" name="{name}">{child}</testcase>')
    inner = "\n".join(body)
    if root == "testsuites":
        return f'<testsuites><testsuite name="s">{inner}</testsuite></testsuites>'
    return f'<testsuite name="s">{inner}</testsuite>'


def write_tree(base: Path, files: Mapping[str, str | bytes]) -> Path:
    for rel, content in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    return base


@dataclass
class Project:
    path: Path

    def check(
        self,
        *flags: str,
        env: Mapping[str, str] | None = None,
        results: bool | None = None,
        tty: bool = False,
    ) -> Run:
        argv = ["check", "--spec", "SPEC.md"]
        if (self.path / "src").is_dir():
            argv += ["--src", "src"]
        if (self.path / "tests").is_dir():
            argv += ["--tests", "tests"]
        if results is None:
            results = (self.path / "junit.xml").is_file()
        if results:
            argv += ["--results", "junit.xml"]
        argv += list(flags)
        return run_cli(argv, self.path, env, tty=tty)


@pytest.fixture
def project(tmp_path: Path):
    """Build a project from a file mapping: project({...}) -> Project."""

    counter = {"n": 0}

    def build(files: Mapping[str, str | bytes]) -> Project:
        counter["n"] += 1
        base = tmp_path / f"p{counter['n']}"
        base.mkdir()
        return Project(write_tree(base, files))

    return build


SIMPLE_SPEC = spec_table([("R-01", "adds"), ("C-01", "divides"), ("T-01", "add test")])
SIMPLE_SRC = "def add(a, b):\n    # R-01\n    return a + b\n\n\ndef div(a, b):\n    # C-01\n    return a / b\n"
SIMPLE_TESTS = (
    "from calc import add, div\n\n\n"
    "def test_add():\n    '''T-01: R-01'''\n    assert add(1, 2) == 3\n\n\n"
    "def test_div():\n    '''C-01'''\n    assert div(4, 2) == 2\n"
)
SIMPLE_JUNIT = junit(
    [("tests.test_calc", "test_add", "passed"), ("tests.test_calc", "test_div", "passed")]
)
SIMPLE_PROJECT = {
    "SPEC.md": SIMPLE_SPEC,
    "src/calc.py": SIMPLE_SRC,
    "tests/test_calc.py": SIMPLE_TESTS,
    "junit.xml": SIMPLE_JUNIT,
}
