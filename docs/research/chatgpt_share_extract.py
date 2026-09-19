#!/usr/bin/env python3
"""Extract the full conversation from a public chatgpt.com/share/<id> URL.

The share page is a client-rendered React Router app; the conversation is
embedded in the HTML as a turbo-stream payload (window.__reactRouterContext
.streamController.enqueue(...)).  No login or API key is required.

Payload format
--------------
The stream is delivered as one or more enqueue("<js-string-literal>") calls.
Decoding each literal and concatenating yields:

    <JSON array>\\nP<n>:[<promise resolutions>]

The JSON array is a flat token table:
  * an integer N is a reference to the token at index N (0-based);
  * a dict key "_N" is a reference to the *key name* of that entry, while the
    value is the entry's payload.

Usage
-----
    ./chatgpt_share_extract.py <url-or-id> [-o OUT] [--json] [--raw]
        [--time-tags|--no-time-tags] [--redacted-blocks|--no-redacted-blocks]
        [--conversation-id-block|--no-conversation-id-block]
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import urllib.request
from dataclasses import dataclass

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

_ENQUEUE_RE = re.compile(r'streamController\.enqueue\(("(?:[^"\\]|\\.)*")\s*\)', re.S)
_PROMISE_RE = re.compile(r"(?m)^P\d+:\[")
_SHARE_ID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I)
_REF_KEY_RE = re.compile(r"^-?\d+$")
_MAX_DEPTH = 200


class ExtractionError(RuntimeError):
    """Raised when the page does not contain a decodable conversation."""


def share_url(url_or_id: str) -> str:
    """Accept a full URL or a bare conversation id and return the share URL."""
    if url_or_id.startswith(("http://", "https://")):
        return url_or_id
    match = _SHARE_ID_RE.search(url_or_id)
    if not match:
        raise ExtractionError(f"not a conversation id or URL: {url_or_id!r}")
    return f"https://chatgpt.com/share/{match.group(1)}"


def fetch(url: str, timeout: float = 30.0) -> str:
    """Fetch the share page HTML."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "replace")


def decode_stream(html: str) -> list:
    """Decode the turbo-stream payload embedded in the page into a token table."""
    chunks = _ENQUEUE_RE.findall(html)
    if not chunks:
        raise ExtractionError(
            "no streamController payload found (page may be a login wall, a 404, "
            "or the share link was revoked)"
        )
    # Each match is a JS string literal; concatenating the decoded literals
    # reproduces the single streamed JSON document.
    raw = "".join(json.loads(chunk) for chunk in chunks)
    # Drop trailing promise-resolution block ("P2031:[...]") if present.
    raw = _PROMISE_RE.split(raw, maxsplit=1)[0].rstrip()
    try:
        table = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"stream payload is not valid JSON: {exc}") from exc
    if not isinstance(table, list):
        raise ExtractionError("stream payload is not a token table")
    return table


class Resolver:
    """Resolve turbo-stream token references into plain Python values."""

    def __init__(self, table: list):
        self.table = table
        self.memo: dict[int, object] = {}

    def __call__(self, token):
        return self._resolve(token, 0)

    def _resolve(self, token, depth: int):
        if not isinstance(token, int) or isinstance(token, bool):
            return copy.deepcopy(token)
        if depth > _MAX_DEPTH:
            raise ExtractionError(f"reference nesting exceeded {_MAX_DEPTH} levels")
        if token in self.memo:
            # Deep copy: the graph is a DAG, so shared substructures would be
            # mistaken for cycles by serializers (json.dump raises
            # "Circular reference detected").
            return copy.deepcopy(self.memo[token])
        value = self.table[token] if 0 <= token < len(self.table) else None
        if isinstance(value, dict):
            resolved: dict = {}
            for key, payload in value.items():
                name = self._resolve(_ref_index(key), depth + 1) if _is_ref_key(key) else key
                resolved[name if isinstance(name, str) else str(name)] = self._resolve(
                    payload, depth + 1
                )
        elif isinstance(value, list):
            resolved = [self._resolve(item, depth + 1) for item in value]
        else:
            self.memo[token] = value
            return value
        self.memo[token] = resolved
        return copy.deepcopy(resolved)


def _is_ref_key(key) -> bool:
    return isinstance(key, str) and len(key) > 1 and key[0] == "_" and bool(_REF_KEY_RE.match(key[1:]))


def _ref_index(key: str) -> int:
    return int(key[1:])


def find_conversation(table: list) -> dict:
    """Return the conversation object from the token table."""
    resolve = Resolver(table)
    for token, value in enumerate(table):
        if not isinstance(value, dict):
            continue
        # The conversation object is keyed by reference tokens whose *names*
        # spell "mapping" / "current_node"; cheap numeric prefilter first.
        numeric = [key for key in value if _is_ref_key(key)]
        if len(numeric) < 5:
            continue
        names = {resolve(_ref_index(key)) for key in numeric}
        if not {"mapping", "current_node"} <= names:
            continue
        conversation = resolve(token)
        if isinstance(conversation, dict) and conversation.get("mapping"):
            return conversation
    raise ExtractionError("no conversation object found in the page payload")


def linearize(conversation: dict) -> list[dict]:
    """Walk parent links from current_node to the root; return ordered messages."""
    mapping = conversation.get("mapping") or {}
    node_id = conversation.get("current_node")
    chain = []
    seen = set()
    while node_id and node_id not in seen:
        seen.add(node_id)
        node = mapping.get(node_id)
        if not node:
            break
        chain.append(node)
        node_id = node.get("parent")
    chain.reverse()

    messages = []
    for node in chain:
        message = node.get("message")
        if not message:
            continue
        content = message.get("content") or {}
        parts = content.get("parts") or []
        text = "\n".join(part for part in parts if isinstance(part, str))
        if not text.strip():
            continue
        if content.get("content_type") == "code":
            language = content.get("language") or ""
            text = f"```{language}\n{text}\n```"
        messages.append(
            {
                "id": message.get("id") or node.get("id"),
                "role": (message.get("author") or {}).get("role") or "unknown",
                "create_time": message.get("create_time"),
                "content_type": content.get("content_type") or "text",
                "text": text,
            }
        )
    return messages


REDACTED_PLACEHOLDER = "The output of this plugin was redacted."


@dataclass(frozen=True)
class RenderOptions:
    """What the Markdown transcript includes."""

    time_tags: bool = False
    redacted_blocks: bool = False
    conversation_id_block: bool = False


def is_redacted(text: str) -> bool:
    """True for a message whose entire payload is the redaction placeholder."""
    return text.strip() == REDACTED_PLACEHOLDER


def render_markdown(
    conversation: dict,
    messages: list[dict],
    options: RenderOptions = RenderOptions(),
) -> str:
    """Render the conversation as a readable Markdown transcript."""
    selected = [
        message
        for message in messages
        if options.redacted_blocks or not is_redacted(message["text"])
    ]
    lines = [f"# {conversation.get('title') or 'ChatGPT conversation'}", ""]
    if options.conversation_id_block:
        meta = [
            ("Conversation id", conversation.get("conversation_id")),
            ("Model", conversation.get("default_model_slug")),
            ("Created", conversation.get("create_time")),
            ("Messages", len(messages)),
        ]
        if len(selected) != len(messages):
            meta.append(("Visible messages", len(selected)))
        for label, value in meta:
            if value not in (None, ""):
                lines.append(f"- **{label}:** {value}")
        lines.append("")
    for message in selected:
        header = f"## {message['role'].upper()}"
        if options.time_tags and message.get("create_time"):
            stamp = message["create_time"]
            header += (
                f"  ({stamp})"
                if isinstance(stamp, str)
                else f"  ({float(stamp):.3f})"
            )
        lines.extend([header, "", message["text"], ""])
    return "\n".join(lines).rstrip() + "\n"


def extract(url_or_id: str) -> dict:
    """Fetch and decode a ChatGPT share link into a conversation dict."""
    page = fetch(share_url(url_or_id))
    table = decode_stream(page)
    conversation = find_conversation(table)
    messages = linearize(conversation)
    return {"conversation": conversation, "messages": messages}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract a public ChatGPT share conversation.")
    parser.add_argument("url", help="chatgpt.com/share/<id> URL or bare conversation id")
    parser.add_argument("-o", "--output", help="write output to this file instead of stdout")
    parser.add_argument("--json", action="store_true", help="emit raw JSON (full graph) instead of Markdown")
    parser.add_argument("--raw", action="store_true", help="emit only the message list as JSON")
    parser.add_argument(
        "--time-tags",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="show per-message timestamps in Markdown headings (default: hidden)",
    )
    parser.add_argument(
        "--redacted-blocks",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="include redacted plugin output blocks in Markdown (default: hidden)",
    )
    parser.add_argument(
        "--conversation-id-block",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="show the conversation id/model/created/count block in Markdown (default: hidden)",
    )
    args = parser.parse_args(argv)

    try:
        result = extract(args.url)
    except (ExtractionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    conversation, messages = result["conversation"], result["messages"]
    if args.raw:
        payload = json.dumps(messages, indent=1, ensure_ascii=False)
    elif args.json:
        payload = json.dumps(conversation, indent=1, ensure_ascii=False)
    else:
        payload = render_markdown(
            conversation,
            messages,
            RenderOptions(
                time_tags=args.time_tags,
                redacted_blocks=args.redacted_blocks,
                conversation_id_block=args.conversation_id_block,
            ),
        )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(payload)
        shown = args.output
    else:
        shown = payload
    print(shown, end="" if shown.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
