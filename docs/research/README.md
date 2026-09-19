# chatgpt_share_extract.py

Extract the full conversation from a public `chatgpt.com/share/<id>` link into a readable Markdown transcript or JSON. Stdlib only — no dependencies, no API key, no login.

## Why a plain fetch isn't enough

A share page is a client-rendered React Router app. Reader-mode/HTML-to-text extraction returns only meta tags: the visible conversation is produced by JavaScript, and the OG tags only carry a title. The transcript itself is embedded in the HTML as a **turbo-stream** payload, which this script decodes directly.

## Usage

```bash
./chatgpt_share_extract.py <url-or-id> [options]
```

```bash
# Markdown transcript to stdout
./chatgpt_share_extract.py https://chatgpt.com/share/6aaed58b-9048-83e8-a3cd-4d9ba3e37243

# A bare conversation id works too
./chatgpt_share_extract.py 6aaed58b-9048-83e8-a3cd-4d9ba3e37243

# Write to a file
./chatgpt_share_extract.py 6aaed58b-... -o conversation.md

# Message list as JSON
./chatgpt_share_extract.py 6aaed58b-... --raw

# Full resolved conversation graph as JSON
./chatgpt_share_extract.py 6aaed58b-... --json
```

| Option | Effect |
| --- | --- |
| `-o`, `--output FILE` | Write output to a file instead of stdout |
| `--raw` | Emit only the linearized message list as JSON |
| `--json` | Emit the full resolved conversation graph (metadata, `mapping`, `current_node`) as JSON |

Exit status is `0` on success and `1` on failure, with a diagnostic on stderr.

## Output

Default Markdown output:

```markdown
# Ontological Spec Database

- **Conversation id:** 6aaed58b-9048-83e8-a3cd-4d9ba3e37243
- **Model:** auto
- **Created:** 1789842827.569779
- **Messages:** 10

## USER  (1789619093.436)

Here is a sample spec document; ...

## ASSISTANT  (1789619101.261055)

Yes. In fact, I think ...
```

`--raw` emits one object per message:

```json
[
  {
    "id": "e666c013-12ae-4bed-a41f-b89bc8034f60",
    "role": "user",
    "create_time": 1789619093.436,
    "content_type": "text",
    "text": "Here is a sample spec document; ..."
  }
]
```

Roles are `user`, `assistant`, `tool`, or `system`. Messages with no textual content are omitted. Content of type `code` is re-wrapped in fenced code blocks in Markdown output.

## How it works

Pipeline: `fetch` → `decode_stream` → `find_conversation` → `linearize` → `render_markdown`.

1. **Fetch.** GET the share URL with a browser User-Agent.
2. **Decode the stream.** The page emits one or more
   `window.__reactRouterContext.streamController.enqueue("<js-string-literal>")` calls. Each literal is JSON-decoded and the results concatenated — **all** chunks, since the page normally emits two and using only the first yields truncated JSON with silently shifted indices. The trailing promise-resolution block (`P2031:[{}]`) is then stripped: the stream is `<JSON array>\nP<n>:[...]`.
3. **Resolve tokens.** The JSON array is a flat token table:
   - an integer `N` references the token at index `N` (**0-based**);
   - a dict key `"_N"` — including negative refs such as `"_1396"` — references the *key name* for that entry, while the entry's value is the payload.

   Resolution is memoized and deep-copied on return: the object graph is a DAG, so shared substructures otherwise make serializers fail with `Circular reference detected`. A depth cap converts pathological input into a clean error instead of a `RecursionError`.
4. **Locate the conversation.** Token-table entries are scanned for dicts carrying both `mapping` and `current_node` key names, with a cheap reference-key prefilter so only those names are resolved rather than the entire token table.
5. **Linearize.** The message mapping is a tree; the script walks `parent` links from `current_node` back to the root (cycle-guarded) and reverses the chain.

The module is importable if you want the raw pieces:

```python
from chatgpt_share_extract import extract

result = extract("https://chatgpt.com/share/6aaed58b-...")
result["conversation"]  # full resolved graph
result["messages"]      # ordered [{id, role, create_time, content_type, text}]
```

Lower-level entry points: `share_url`, `fetch`, `decode_stream`, `Resolver`, `find_conversation`, `linearize`, `render_markdown`. All decode failures raise `ExtractionError`.

## Limitations

- **Public share links only.** Private conversations and login walls contain no payload; the script does not authenticate.
- **Redacted plugin output is unrecoverable.** Where ChatGPT suppressed a tool result, the share payload itself contains only `The output of this plugin was redacted.` Decoding cannot recover it.
- **Markup is not reconstructed.** Formatting lives in the message metadata, not the text parts; output is plain Markdown text with code fences added.
- **Branching is linearized.** The mapping is a tree, and only the path from `current_node` to the root is emitted. Messages in abandoned edit branches are not included — use `--json` to inspect them.
- **Unofficial format.** The turbo-stream payload is an internal representation; if ChatGPT changes it, `decode_stream` or `find_conversation` will need updating. Failures are reported as `ExtractionError`, not partial output.

## Requirements

Python 3.9+ (uses `from __future__ import annotations` and PEP 604 union syntax under that import). No third-party packages.
