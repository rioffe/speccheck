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

# Everything on: timestamps, metadata block, redacted blocks, attachments
./chatgpt_share_extract.py 6aaed58b-... --time-tags --conversation-id-block \
    --redacted-blocks --attachments -o conversation.md

# Keep the raw citation markers instead of converting them to links
./chatgpt_share_extract.py 6aaed58b-... --no-citations

# Resolve citation links against copies of the cited files in refs/
./chatgpt_share_extract.py 6aaed58b-... --cite-dir refs -o conversation.md

# Message list as JSON
./chatgpt_share_extract.py 6aaed58b-... --raw

# Full resolved conversation graph as JSON
./chatgpt_share_extract.py 6aaed58b-... --json
```

| Option | Default | Effect |
| --- | --- | --- |
| `-o`, `--output FILE` | stdout | Write output to a file instead of stdout |
| `--json` | off | Emit the full resolved conversation graph (metadata, `mapping`, `current_node`) as JSON |
| `--raw` | off | Emit only the linearized message list as JSON |
| `--time-tags` / `--no-time-tags` | hidden | Show per-message timestamps in Markdown headings |
| `--redacted-blocks` / `--no-redacted-blocks` | hidden | Include redacted plugin output blocks in Markdown |
| `--conversation-id-block` / `--no-conversation-id-block` | hidden | Show the conversation id/model/created/count block |
| `--citations` / `--no-citations` | **shown** | Convert inline client citation markers to Markdown line-range links |
| `--attachments` / `--no-attachments` | hidden | List attachment metadata (never content) |
| `--cite-dir DIR` | `.` | Directory holding local copies of cited files, used to resolve link targets |

Exit status is `0` on success and `1` on failure, with a diagnostic on stderr.

## LaTeX

ChatGPT writes math with escaped delimiters — `\[ ... \]` for display math and `\( ... \)` for inline — which GitHub and most Markdown renderers do not recognise; they show the backslashes literally. The script converts both to dollar delimiters unconditionally, with no flag to disable it:

| Input | Output |
| --- | --- |
| `\[ C(O,I,E) \]` | `$$ C(O,I,E) $$` |
| `\(O\) = obligations` | `$O$ = obligations` |

Content inside fenced code blocks is left untouched, since delimiters there are literal text rather than math.

Unbalanced delimiters are not converted (no matching pair), and LaTeX escapes such as `\_` and `\,` are preserved.

## Citations

Assistant messages carry inline citation markers that look like this, where `\ue200`, `\ue201`, and `\ue202` are invisible private-use sentinels:

```
\ue200filecite\ue202turn0file0\ue202L497-L498\ue201
```

`turn0file0` is an opaque slot, not a filename. The real name and span live alongside the message in `metadata.citations[]`, so the two are cross-referenced. With `--citations` (the default) each marker becomes a GitHub-style line-range link:

```markdown
…derived from it and kept in sync per s11 [SPEC.md L497-498](SPEC.md#L497-L498).
```

Links are relative to the output file, so **a copy of the cited file must sit beside it** for the link to resolve. When a cited file is not found under `--cite-dir`, the link is still emitted and a note is written to stderr:

```
note: cited file 'SPEC.md' not found under .; its links will dangle
```

Line-range fragments (`#L497-L498`) are honoured by GitHub, GitLab, and the VS Code Markdown preview. Obsidian and most static-site renderers ignore them; use `--no-citations` there if you would rather keep the raw markers than emit inert links.

Caveat worth knowing: the ranges index **the file version that was attached**, and the payload pins no revision hash. If your local copy has drifted, links will point at the wrong lines. Verify by checking that a link's landing text matches what the prose claims.

Citations that appear in message metadata but have no inline marker in the text are collected under a `## Citations without an inline marker` heading rather than being silently dropped.

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

`--raw` emits one object per message, including citation and attachment metadata:

```json
[
  {
    "id": "e666c013-12ae-4bed-a41f-b89bc8034f60",
    "role": "user",
    "create_time": 1789619093.436,
    "content_type": "text",
    "text": "Here is a sample spec document; ...",
    "citations": [],
    "attachments": [
      {
        "id": "file_00000000d4b881fd80b0f6555e3a079e",
        "name": "SPEC(1).md",
        "size": 36065,
        "mime_type": "text/markdown",
        "library_file_id": "libfile_bd2bcbdbea948191bcb4bee36c78fdd0",
        "is_big_paste": false
      }
    ]
  }
]
```

A citation object is `{start_ix, end_ix, name, file_id, library_file_id, retrieval_turn, retrieval_file_index, line_range}`.

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
5. **Linearize.** The message mapping is a tree; the script walks `parent` links from `current_node` back to the root (cycle-guarded) and reverses the chain. Each message also yields its `citations` (from `metadata.citations`, see [Citations](#citations)) and `attachments` (metadata only, never content).
6. **Rewrite citations.** Inline markers are matched to citations by `(retrieval_turn, retrieval_file_index)`, then by line range when the marker carries a span; matched markers become Markdown links.
7. **Convert math.** Escaped `\[...\]` / `\(...\)` delimiters become `$$...$$` / `$...$` outside fenced code blocks (see [LaTeX](#latex)).

The module is importable if you want the raw pieces:

```python
from chatgpt_share_extract import extract, citation_targets, rewrite_citations, convert_latex

result = extract("https://chatgpt.com/share/6aaed58b-...")
result["conversation"]  # full resolved graph
result["messages"]      # ordered, each with citations + attachments
citation_targets(result["messages"], ".")  # cited files present locally
```

Lower-level entry points: `share_url`, `fetch`, `decode_stream`, `Resolver`, `find_conversation`, `collect_citations`, `collect_attachments`, `linearize`, `rewrite_citations`, `render_citation`, `citation_targets`, `convert_latex`, `render_markdown`, `render_attachments`. All decode failures raise `ExtractionError`.

## Limitations

- **Public share links only.** Private conversations and login walls contain no payload; the script does not authenticate.
- **Redacted plugin output is unrecoverable.** Where ChatGPT suppressed a tool result, the share payload itself contains only `The output of this plugin was redacted.` Decoding cannot recover it.
- **Attached file content is not in the payload.** The conversation stores only attachment *metadata* — name, size, MIME type, file ids. The extracted text of an attachment (e.g. the tool that ingested a pasted `SPEC.md`) is exactly what ChatGPT redacted, so the file cannot be recovered from a share link. Ask the sharer for the original; `--attachments` reports what was attached so you know what to ask for.
- **Citation line ranges are unpinned.** They index the attached file's revision, and nothing in the payload pins a hash. A drifted local copy yields links that land on the wrong lines.
- **Markup is not reconstructed.** Formatting lives in the message metadata, not the text parts; output is plain Markdown text with code fences and citation links added.
- **Branching is linearized.** The mapping is a tree, and only the path from `current_node` to the root is emitted. Messages in abandoned edit branches are not included — use `--json` to inspect them.
- **Unofficial format.** The turbo-stream payload and the citation marker encoding are internal representations; if ChatGPT changes either, `decode_stream`, `find_conversation`, or `_CITE_TAG_RE` will need updating. Failures are reported as `ExtractionError`, not partial output.

## Requirements

Python 3.9+ (uses `from __future__ import annotations` and PEP 604 union syntax under that import). No third-party packages.
