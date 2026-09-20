"""Send one request to Jev (`typesafe/jev-1.13` or any model on OpenRouter's alpha decisions
API) and print its typed answers.

Jev answers structured questions against a `state`: `noul` (a yes/no probability, 0..1),
`choice` (one of a fixed set, with the full probability distribution), `score` (one level of an
ordered rubric). Your code owns the workflow; this script only sends one task and prints what
came back -- it does not loop over a batch (see `tools/census_jev_tasks.py`, which generates one
task per census subject; use this script to try one of those, or any other task, at a time).

Needs OPENROUTER_API_KEY in the environment. OPENROUTER_REFERER / OPENROUTER_TITLE are optional
(OpenRouter's ranking attribution headers; omitted if unset).

Usage, three ways to give it a task:
  uv run python tools/jev_client.py --task path/to/task.json
  uv run python tools/jev_client.py --task-file build/census/jev_tasks.jsonl --id K-14
  echo '{"model": "...", "state": "...", "questions": {...}}' | uv run python tools/jev_client.py

A task is {"model", "state", "questions"} (extra keys such as "id"/"family" are ignored). Prints
one line per question -- noul as true/false with its probability, choice as the winner with its
distribution, score as the chosen level -- then, with --raw, the full JSON response.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"
ENV_KEY = "OPENROUTER_API_KEY"
ENV_REFERER = "OPENROUTER_REFERER"
ENV_TITLE = "OPENROUTER_TITLE"


def load_task(args: argparse.Namespace) -> dict[str, Any]:
    if args.task_file:
        if not args.id:
            raise SystemExit("--task-file requires --id (which line to pick, by its \"id\" key)")
        with Path(args.task_file).open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("id") == args.id:
                    return obj
        raise SystemExit(f"no task with id {args.id!r} found in {args.task_file}")
    if args.task:
        return json.loads(Path(args.task).read_text(encoding="utf-8"))
    text = sys.stdin.read()
    if not text.strip():
        raise SystemExit("no task given: use --task, --task-file --id, or pipe JSON on stdin")
    return json.loads(text)


def build_request(task: dict[str, Any], model_override: str | None) -> dict[str, Any]:
    for key in ("state", "questions"):
        if key not in task:
            raise SystemExit(f"task is missing required key {key!r}")
    return {
        "model": model_override or task.get("model") or DEFAULT_MODEL,
        "state": task["state"],
        "questions": task["questions"],
    }


def post(url: str, api_key: str, body: dict[str, Any], timeout: float, referer: str | None, title: str | None) -> tuple[int, str]:
    import httpx  # lazy: importable without the [llm] extra only if httpx happens to be present

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-OpenRouter-Title"] = title
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, content=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers)
    return resp.status_code, resp.text


def format_answers(questions: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    lines = []
    for name, q in questions.items():
        a = answers.get(name)
        qtype = q.get("type")
        if a is None:
            lines.append(f"{name} ({qtype}): <no answer>")
            continue
        if qtype == "noul":
            p = a.get("noul")
            verdict = "n/a" if p is None else ("true" if p > 0.5 else "false")
            lines.append(f"{name} (noul): {verdict}  [p={p}]")
        elif qtype == "choice":
            lines.append(f"{name} (choice): {a.get('choice')}  {a.get('probabilities')}")
        elif qtype == "score":
            lines.append(f"{name} (score): {a.get('score')}")
        else:
            lines.append(f"{name} ({qtype}): {a}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--task", default=None, help="a JSON file holding one task")
    parser.add_argument("--task-file", default=None, help="a JSONL file of many tasks")
    parser.add_argument("--id", default=None, help="with --task-file: the task's \"id\" to send")
    parser.add_argument("--model", default=None, help="override the task's model field")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--referer", default=os.environ.get(ENV_REFERER))
    parser.add_argument("--title", default=os.environ.get(ENV_TITLE))
    parser.add_argument("--raw", action="store_true", help="also print the full JSON response")
    args = parser.parse_args(argv)

    api_key = os.environ.get(ENV_KEY)
    if not api_key:
        print(f"jev_client: {ENV_KEY} is not set", file=sys.stderr)
        return 2

    task = load_task(args)
    body = build_request(task, args.model)

    try:
        status, text = post(args.url, api_key, body, args.timeout, args.referer, args.title)
    except Exception as exc:  # noqa: BLE001 - report and exit, don't traceback on a network hiccup
        print(f"jev_client: request failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    if status != 200:
        print(f"jev_client: HTTP {status}", file=sys.stderr)
        print(text, file=sys.stderr)
        return 1

    try:
        envelope = json.loads(text)
        answers = envelope["answers"]
    except (ValueError, KeyError) as exc:
        print(f"jev_client: unexpected response shape: {exc}", file=sys.stderr)
        print(text, file=sys.stderr)
        return 1

    ident = task.get("id")
    print(f"model: {body['model']}" + (f"  id: {ident}" if ident else ""))
    for line in format_answers(body["questions"], answers):
        print(f"  {line}")
    if args.raw:
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
