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
        [--citations|--no-citations] [--attachments|--no-attachments]
        [--cite-dir DIR]

Client-side citation markers such as "turn0file0L497-L498" are rewritten to
GitHub-style line-range links ("SPEC.md#L497-L498") by default; place a copy
of the cited file beside the output for the links to resolve.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

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


def collect_citations(message: dict) -> list[dict]:
    """Extract file citations attached to a message, in document order."""
    metadata = message.get("metadata") or {}
    citations = []
    for cite in metadata.get("citations") or []:
        info = cite.get("metadata") or {}
        extra = info.get("extra") or {}
        line_range = extra.get("line_range") or []
        if len(line_range) != 2:
            continue
        citations.append(
            {
                "start_ix": cite.get("start_ix"),
                "end_ix": cite.get("end_ix"),
                "name": info.get("name"),
                "file_id": info.get("id"),
                "library_file_id": extra.get("library_file_id"),
                "retrieval_turn": extra.get("retrieval_turn") or 0,
                "retrieval_file_index": extra.get("retrieval_file_index") or 0,
                "line_range": list(line_range),
            }
        )
    citations.sort(key=lambda cite: (cite["start_ix"] is None, cite["start_ix"]))
    return citations


def collect_attachments(message: dict) -> list[dict]:
    """Extract attachment metadata (never content) from a message."""
    metadata = message.get("metadata") or {}
    attachments = []
    for item in metadata.get("attachments") or []:
        attachments.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "size": item.get("size"),
                "mime_type": item.get("mime_type"),
                "library_file_id": item.get("library_file_id"),
                "is_big_paste": item.get("is_big_paste"),
            }
        )
    return attachments


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
                "citations": collect_citations(message),
                "attachments": collect_attachments(message),
            }
        )
    return messages


REDACTED_PLACEHOLDER = "The output of this plugin was redacted."

# A client-side citation marker. Fields are separated by U+E202 inside
# U+E200/U+E201 sentinels:
#     \ue200filecite\ue202turn0file0\ue202L497-L498\ue201
# The type field ("filecite", "webcite") and the line-range field are both
# optional in principle, so the pattern accepts either an empty line range or
# a "L<start>" / "L<start>-L<end>" span.
_CITE_TAG_RE = re.compile(
    r"\ue200(?P<type>[a-z]*)\ue202"
    r"turn(?P<turn>\d+)file(?P<file>\d+)"
    r"\ue202(?P<span>L(?P<start>\d+)(?:-L?(?P<end>\d+))?)?\ue201"
)

# ChatGPT writes LaTeX with escaped delimiters: \[...\] display and \(...\)
# inline. Both are converted to dollar form unconditionally (see convert_latex).
_DISPLAY_MATH_RE = re.compile(r"\\\[(.*?)\\\]", re.S)
_INLINE_MATH_RE = re.compile(r"\\\((.*?)\\\)", re.S)
# Fenced code is left alone: delimiters there are literal text, not math.
_FENCE_RE = re.compile(r"(?m)^([ \t]*)(`{3,}|~{3,})[^\n]*\n.*?(?:^\1\2[ \t]*$|\Z)", re.S)


def render_citation(citation: dict, target: str | None = None) -> str:
    """Render one citation as a GitHub-style Markdown line-range link."""
    name = citation.get("name") or citation.get("file_id") or "citation"
    start, end = citation["line_range"]
    fragment = f"#L{start}" + (f"-L{end}" if end != start else "")
    return f"[{name} L{start}-{end}]({target or name}{fragment})"


def rewrite_citations(
    text: str,
    citations: list[dict],
    targets: dict[str, str],
) -> tuple[str, list[dict]]:
    """Replace client citation markers with Markdown links.

    Each marker records the turn and file slot that identify its subject; the
    same turn/file pair may be cited several times with different spans, so
    markers without a line range are matched to citations in call order.

    Returns the rewritten text and the citations that could not be matched.
    """
    by_slot: dict[tuple[int, int], list[dict]] = {}
    for citation in citations:
        key = (citation["retrieval_turn"], citation["retrieval_file_index"])
        by_slot.setdefault(key, []).append(citation)

    for queue in by_slot.values():
        queue.sort(key=lambda c: (c["line_range"][0], c["line_range"][1]))

    used: set[int] = set()
    queue_pos: dict[tuple[int, int], int] = {}

    def replace(match: re.Match) -> str:
        key = (int(match.group("turn")), int(match.group("file")))
        candidates = [c for c in by_slot.get(key, []) if id(c) not in used]
        if not candidates:
            return match.group(0)
        marker_lines = match.group("start")
        if marker_lines:
            want = (
                int(marker_lines),
                int(match.group("end") or marker_lines),
            )
            chosen = next((c for c in candidates if tuple(c["line_range"]) == want), None)
        else:
            chosen = candidates[0]
        if chosen is None:
            return match.group(0)
        used.add(id(chosen))
        queue_pos[key] = queue_pos.get(key, 0) + 1
        name = chosen.get("name") or chosen.get("file_id") or ""
        return render_citation(chosen, targets.get(name))

    rewritten = _CITE_TAG_RE.sub(replace, text)
    unmatched = [c for c in citations if id(c) not in used]
    return rewritten, unmatched


@dataclass(frozen=True)
class RenderOptions:
    """What the Markdown transcript includes."""

    time_tags: bool = False
    redacted_blocks: bool = False
    conversation_id_block: bool = False
    citations: bool = True
    attachments: bool = False


def is_redacted(text: str) -> bool:
    """True for a message whose entire payload is the redaction placeholder."""
    return text.strip() == REDACTED_PLACEHOLDER


def render_attachments(messages: list[dict]) -> list[str]:
    """Render an attachments block; metadata only, never content."""
    lines: list[str] = []
    for message in messages:
        for attachment in message.get("attachments") or []:
            if not lines:
                lines.append("## Attachments")
                lines.append("")
            size = attachment.get("size")
            size_text = f"{size} bytes" if isinstance(size, int) else "unknown size"
            detail = ", ".join(
                part
                for part in (attachment.get("mime_type"), size_text)
                if part
            )
            lines.append(
                f"- **{attachment.get('name') or attachment.get('id')}** "
                f"({detail}) — attached to the {message['role'].upper()} message; "
                "content is not stored in the shared conversation"
            )
    return lines


def convert_latex(text: str) -> str:
    """Convert escaped LaTeX delimiters to dollar delimiters.

    ChatGPT emits ``\\[...\\]`` for display math and ``\\(...\\)`` for inline
    math, which most Markdown renderers (including GitHub) do not recognise —
    they render the delimiters literally. ``$$...$$`` and ``$...$`` are what
    those renderers expect, so the conversion is unconditional, except inside
    fenced code blocks where the delimiters are literal text.
    """

    def convert_segment(segment: str) -> str:
        segment = _DISPLAY_MATH_RE.sub(lambda m: f"$${m.group(1)}$$", segment)
        return _INLINE_MATH_RE.sub(lambda m: f"${m.group(1)}$", segment)

    out: list[str] = []
    position = 0
    for fence in _FENCE_RE.finditer(text):
        out.append(convert_segment(text[position : fence.start()]))
        out.append(fence.group(0))
        position = fence.end()
    out.append(convert_segment(text[position:]))
    return "".join(out)


def render_markdown(
    conversation: dict,
    messages: list[dict],
    options: RenderOptions = RenderOptions(),
    targets: dict[str, str] | None = None,
) -> str:
    """Render the conversation as a readable Markdown transcript.

    ``targets`` maps a citation's file name to the link target to use for it,
    so line-range links can point at a local copy of the cited file. Files
    absent from ``targets`` link to their own name.
    """
    targets = targets or {}
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
    orphaned: dict[str, list[tuple[int, int]]] = {}
    for message in selected:
        header = f"## {message['role'].upper()}"
        if options.time_tags and message.get("create_time"):
            stamp = message["create_time"]
            header += (
                f"  ({stamp})"
                if isinstance(stamp, str)
                else f"  ({float(stamp):.3f})"
            )
        text = message["text"]
        if options.citations:
            text, unmatched = rewrite_citations(
                text, message.get("citations") or [], targets
            )
            for citation in unmatched:
                name = citation.get("name") or citation.get("file_id") or "citation"
                orphaned.setdefault(name, []).append(tuple(citation["line_range"]))
        text = convert_latex(text)
        lines.extend([header, "", text, ""])
    if options.attachments:
        block = render_attachments(selected)
        if block:
            lines.extend(block)
            lines.append("")
    if orphaned:
        lines.append("## Citations without an inline marker")
        lines.append("")
        for name, ranges in orphaned.items():
            spans = ", ".join(
                f"L{start}-{end}" if start != end else f"L{start}" for start, end in ranges
            )
            lines.append(f"- {name}: {spans}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def citation_targets(messages: list[dict], cite_dir: str = ".") -> dict[str, str]:
    """Map cited file names that exist under ``cite_dir`` to link targets.

    A cited file is linked by its own (relative) name, so the rendered link
    resolves when the transcript sits beside a local copy of that file. Names
    absent here link to the same path and will dangle until a copy is placed
    there, which is the honest outcome: the script cannot invent a target for
    a file it does not have.
    """
    names: list[str] = []
    for message in messages:
        for citation in message.get("citations") or []:
            name = citation.get("name")
            if name and name not in names:
                names.append(name)
    return {name: name for name in names if (Path(cite_dir) / name).exists()}


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
    parser.add_argument(
        "--citations",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="convert inline client citation markers to Markdown line-range links (default: shown)",
    )
    parser.add_argument(
        "--attachments",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="list attachment metadata in Markdown (default: hidden)",
    )
    parser.add_argument(
        "--cite-dir",
        default=".",
        help="directory holding local copies of cited files, used to resolve link targets (default: .)",
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
        targets = citation_targets(messages, args.cite_dir) if args.citations else {}
        payload = render_markdown(
            conversation,
            messages,
            RenderOptions(
                time_tags=args.time_tags,
                redacted_blocks=args.redacted_blocks,
                conversation_id_block=args.conversation_id_block,
                citations=args.citations,
                attachments=args.attachments,
            ),
            targets,
        )
        if args.citations:
            missing = sorted(
                {
                    citation.get("name")
                    for message in messages
                    for citation in message.get("citations") or []
                    if citation.get("name") and citation["name"] not in targets
                }
            )
            for name in missing:
                print(
                    f"note: cited file {name!r} not found under {args.cite_dir}; "
                    "its links will dangle",
                    file=sys.stderr,
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
