"""Copy fixtures/target/ byte-for-byte into src/speccheck/_selfcheck/ (F-107; guarded by T-60).

Usage: uv run python tools/sync_selfcheck.py [--check]
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "fixtures" / "target"
TARGET = ROOT / "src" / "speccheck" / "_selfcheck"
IGNORE = {"__pycache__", ".pytest_cache"}


def _is_ignored(name: str) -> bool:
    return name in IGNORE or name.startswith(".")  # editor swap files and caches


def differences(a: Path, b: Path) -> list[str]:
    cmp = filecmp.dircmp(a, b, ignore=list(IGNORE))
    out = [f"only in {a}: {n}" for n in cmp.left_only if not _is_ignored(n)]
    out += [f"only in {b}: {n}" for n in cmp.right_only if not _is_ignored(n)]
    out += [f"differs: {n}" for n in cmp.diff_files]
    for sub in cmp.subdirs:
        out += differences(a / sub, b / sub)
    return out


def main(argv: list[str]) -> int:
    if "--check" in argv:
        diffs = differences(SOURCE, TARGET) if TARGET.is_dir() else ["_selfcheck missing"]
        for d in diffs:
            print(d)
        return 1 if diffs else 0
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=shutil.ignore_patterns(*IGNORE, ".*"))
    print(f"synced {SOURCE} -> {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
