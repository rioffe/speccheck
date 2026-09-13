"""T-49: LLM judge evaluation against the golden fixture's hand-labeled edges (opt-in, not CI).

Runs `check --judge llm` three independent times on a copy of fixtures/target/, compares every
non-UNKNOWN verdict with fixtures/target/golden/judge_labels.json, and prints per-run accuracy
and unknown_rate plus the model name, date, and judge_prompt_sha256. T-49 passes only when
every run has accuracy >= 0.90 and unknown_rate <= 0.10.

The endpoint is any OpenAI-compatible chat-completions URL; the defaults target a local Ollama
server (`ollama serve`), which ignores the bearer token but C-09 still requires one.

Usage:
  uv run python tools/eval_judge.py [--model qwen3:8b] [--url http://localhost:11434/v1/chat/completions] [--runs 3]
Environment variables SPECCHECK_JUDGE_URL / _MODEL / _API_KEY override the defaults.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from speccheck.cli import run_check

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "target"
LABELS = FIXTURE / "golden" / "judge_labels.json"
ARGS = [
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
]


def one_run(env: dict[str, str]) -> tuple[dict, str]:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "target"
        shutil.copytree(FIXTURE, target)
        old = os.getcwd()
        os.chdir(target)
        out = io.StringIO()
        try:
            run_check(ARGS + ["--out", "out"], env, out)
        finally:
            os.chdir(old)
        doc = json.loads((target / "out" / "speccheck.json").read_text(encoding="utf-8"))
        return doc, out.getvalue().strip()


def score(doc: dict, labels: dict[str, str]) -> tuple[float | None, float | None, list[str]]:
    agree = decided = judged = unknown = 0
    details = []
    for rec in doc["ids"]:
        for t in rec["tests"]:
            v = t["verdict"]
            if v is None:
                continue
            key = f"{rec['id']} {t['file']}::{t['name']}"
            judged += 1
            if v["verdict"] == "UNKNOWN":
                unknown += 1
                details.append(f"  {key}: UNKNOWN ({v['rationale']})")
                continue
            decided += 1
            ok = v["verdict"] == labels.get(key)
            agree += ok
            details.append(
                f"  {key}: {v['verdict']} vs label {labels.get(key)} {'ok' if ok else 'MISMATCH'} — {v['rationale']}"
            )
    accuracy = agree / decided if decided else None
    unknown_rate = unknown / judged if judged else None
    return accuracy, unknown_rate, details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("SPECCHECK_JUDGE_URL", "http://localhost:11434/v1/chat/completions"),
    )
    parser.add_argument("--model", default=os.environ.get("SPECCHECK_JUDGE_MODEL", "qwen3:8b"))
    parser.add_argument("--api-key", default=os.environ.get("SPECCHECK_JUDGE_API_KEY", "ollama"))
    parser.add_argument("--timeout", default=os.environ.get("SPECCHECK_JUDGE_TIMEOUT", "120"))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--verbose", action="store_true", help="print every edge's verdict")
    args = parser.parse_args(argv)
    env = {
        "SPECCHECK_JUDGE_URL": args.url,
        "SPECCHECK_JUDGE_MODEL": args.model,
        "SPECCHECK_JUDGE_API_KEY": args.api_key,
        "SPECCHECK_JUDGE_TIMEOUT": str(args.timeout),
    }
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    print(f"model: {args.model}  url: {args.url}  date: {dt.date.today().isoformat()}")
    all_ok = True
    for i in range(1, args.runs + 1):
        doc, summary = one_run(env)
        accuracy, unknown_rate, details = score(doc, labels)
        ok = (
            accuracy is not None
            and accuracy >= 0.90
            and unknown_rate is not None
            and unknown_rate <= 0.10
        )
        all_ok = all_ok and ok
        acc_text = "n/a" if accuracy is None else f"{accuracy:.4f}"
        unk_text = "n/a" if unknown_rate is None else f"{unknown_rate:.4f}"
        print(
            f"run {i}: accuracy={acc_text} unknown_rate={unk_text} judge_available={doc['judge_available']} judge_prompt_sha256={doc.get('judge_prompt_sha256')} -> {'PASS' if ok else 'FAIL'}"
        )
        print(f"  {summary}")
        if args.verbose:
            print("\n".join(details))
    print(
        f"T-49: {'PASS' if all_ok else 'FAIL'} ({args.runs} run(s), each must reach accuracy >= 0.90 and unknown_rate <= 0.10)"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
