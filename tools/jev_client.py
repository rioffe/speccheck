"""Send one or many requests to Jev (`typesafe/jev-1.13` or any model on OpenRouter's alpha
decisions API) and print the typed answers.

Jev answers structured questions against a `state`: `noul` (a yes/no probability, 0..1),
`choice` (one of a fixed set, with the full probability distribution), `score` (one level of an
ordered rubric). Your code owns the workflow.

Needs OPENROUTER_API_KEY in the environment. OPENROUTER_REFERER / OPENROUTER_TITLE are optional
(OpenRouter's ranking attribution headers; omitted if unset).

Usage, four ways to give it work:
  uv run python tools/jev_client.py --task path/to/task.json
  uv run python tools/jev_client.py --task-file build/census/jev_tasks.jsonl --id K-14
  uv run python tools/jev_client.py --task-file build/census/jev_tasks.jsonl --id ALL [--concurrency 8] [--out results.jsonl]
  echo '{"model": "...", "state": "...", "questions": {...}}' | uv run python tools/jev_client.py

A task is {"model", "state", "questions"} (extra keys such as "id"/"family" are ignored). For one
task, prints one line per question -- noul as true/false with its probability, choice as the
winner with its distribution, score as the chosen level -- then, with --raw, the full JSON
response. `--id ALL` sends every line of --task-file (concurrently, --concurrency at a time, no
retries), prints the same block per task as each completes, and with --out writes one JSON object
per line -- {"id", "family", "model", "answers"} (or {"id", "family", "error"} for a failed one)
-- so the batch can be joined back to the subjects afterward. One failed task does not stop the
rest; the exit code is 1 if any task failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

DEFAULT_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"
ENV_KEY = "OPENROUTER_API_KEY"
ENV_REFERER = "OPENROUTER_REFERER"
ENV_TITLE = "OPENROUTER_TITLE"


def load_all_tasks(path: str) -> list[dict[str, Any]]:
    tasks = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


def load_task(args: argparse.Namespace) -> dict[str, Any]:
    if args.task_file:
        if not args.id:
            raise SystemExit("--task-file requires --id (a task's \"id\", or ALL for every task)")
        for obj in load_all_tasks(args.task_file):
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


def send_one(
    task: dict[str, Any],
    model_override: str | None,
    url: str,
    api_key: str,
    timeout: float,
    referer: str | None,
    title: str | None,
) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    """Returns (request body, answers dict or None, error message or None)."""
    try:
        body = build_request(task, model_override)
    except SystemExit as exc:
        return {}, None, str(exc)
    try:
        status, text = post(url, api_key, body, timeout, referer, title)
    except Exception as exc:  # noqa: BLE001 - one bad task must not stop the batch
        return body, None, f"request failed: {exc.__class__.__name__}: {exc}"
    if status != 200:
        return body, None, f"HTTP {status}: {text}"
    try:
        envelope = json.loads(text)
        answers = envelope["answers"]
    except (ValueError, KeyError) as exc:
        return body, None, f"unexpected response shape: {exc}: {text}"
    return body, answers, None


def print_result(
    task: dict[str, Any],
    body: dict[str, Any],
    answers: dict[str, Any] | None,
    error: str | None,
    *,
    raw: bool,
    prefix: str = "",
) -> None:
    ident = task.get("id")
    header = f"{prefix}model: {body.get('model', DEFAULT_MODEL)}" + (f"  id: {ident}" if ident else "")
    if error is not None:
        print(f"{header}\n  ERROR: {error}", file=sys.stderr)
        return
    assert answers is not None
    print(header)
    for line in format_answers(body["questions"], answers):
        print(f"  {line}")
    if raw:
        print(json.dumps({"answers": answers}, indent=2, ensure_ascii=False))


def run_batch(args: argparse.Namespace, api_key: str) -> int:
    tasks = load_all_tasks(args.task_file)
    if not tasks:
        print(f"jev_client: no tasks found in {args.task_file}", file=sys.stderr)
        return 1
    out_f = Path(args.out).open("w", encoding="utf-8") if args.out else None
    failures = 0
    try:
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
            futures = {
                pool.submit(
                    send_one, task, args.model, args.url, api_key, args.timeout, args.referer, args.title
                ): task
                for task in tasks
            }
            done = 0
            for future in as_completed(futures):
                task = futures[future]
                body, answers, error = future.result()
                done += 1
                print_result(task, body, answers, error, raw=args.raw, prefix=f"[{done}/{len(tasks)}] ")
                if error is not None:
                    failures += 1
                if out_f is not None:
                    record: dict[str, Any] = {"id": task.get("id"), "family": task.get("family")}
                    if error is not None:
                        record["error"] = error
                    else:
                        record["model"] = body.get("model")
                        record["answers"] = answers
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        if out_f is not None:
            out_f.close()
    print(f"{len(tasks) - failures}/{len(tasks)} succeeded" + (f"; wrote {args.out}" if args.out else ""))
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--task", default=None, help="a JSON file holding one task")
    parser.add_argument("--task-file", default=None, help="a JSONL file of many tasks")
    parser.add_argument(
        "--id", default=None, help='with --task-file: the task\'s "id" to send, or ALL for every task'
    )
    parser.add_argument("--concurrency", type=int, default=8, help="with --id ALL")
    parser.add_argument("--out", default=None, help="with --id ALL: write results as JSONL")
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

    if args.id == "ALL":
        if not args.task_file:
            print("jev_client: --id ALL requires --task-file", file=sys.stderr)
            return 2
        return run_batch(args, api_key)

    task = load_task(args)
    body, answers, error = send_one(
        task, args.model, args.url, api_key, args.timeout, args.referer, args.title
    )
    print_result(task, body, answers, error, raw=args.raw)
    return 1 if error is not None else 0


if __name__ == "__main__":
    sys.exit(main())
