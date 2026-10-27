"""JavaScript / TypeScript adapter: delimit `it` / `test` calls of vitest, jest and the
`node:test` family by tokens (C-03 JS/TS adapter; R-104, D-56). No parser: the kernel stays
standard-library.

Spec IDs realized here (§11): R-104, C-03, E-74, E-75.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

EXTENSIONS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")

_SUITES = frozenset({"describe", "suite"})
_TESTS = frozenset({"it", "test"})
_MODIFIERS = frozenset(
    {
        "only",
        "skip",
        "todo",
        "concurrent",
        "sequential",
        "fails",
        "failing",
        "shuffle",
        "each",
        "for",
        "runIf",
        "skipIf",
    }
)
# these take one group (or a template table) before the title
_ARGUMENT_MODIFIERS = frozenset({"each", "for", "runIf", "skipIf"})
# C-03 REGEX vs DIVISION (F-708): a `/` begins a regex literal iff the previous significant token is
# absent, one-character punctuation other than `)`, `]`, `}`, or one of these identifiers
_REGEX_KEYWORDS = frozenset(
    "return typeof instanceof in of new delete void throw case do else yield await".split()
)
_DIVISION_PUNCTUATION = frozenset(")]}")

# vitest / jest `each` placeholders: printf-style `%s %d %i %f %j %o %O %p %#`, `$name`, `$a.b`.
_PLACEHOLDER_RE = re.compile(r"%[sdifjoOp#%]|\$[A-Za-z_][A-Za-z0-9_.]*")


class JsParseError(Exception):
    """E-74: parentheses did not balance, or a literal ran off the end of the file."""


@dataclass(frozen=True)
class JsCase:
    name: str  # enclosing `describe` titles and the test title joined with " > " (vitest's name)
    start: int  # 1-based, first line of the comment block above the call
    end: int  # inclusive, the line holding the call's closing parenthesis


@dataclass
class _Token:
    kind: str  # "id" | "str" | "dyn" (template with `${}`) | "p" (one punctuation character)
    value: str
    line: int


def _skip_template(text: str, i: int) -> int:
    """`i` indexes the opening backtick; return the index just past the closing one."""
    n = len(text)
    i += 1
    while i < n:
        ch = text[i]
        if ch == "\\":
            i += 2
        elif ch == "`":
            return i + 1
        elif ch == "$" and text.startswith("${", i):
            i = _skip_expression(text, i + 2)
        else:
            i += 1
    raise JsParseError("unterminated template literal")


def _skip_expression(text: str, i: int) -> int:
    """Skip a `${ ... }` body; `i` indexes the first character after `${`."""
    depth = 1
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "`":
            i = _skip_template(text, i)
            continue
        if ch in "'\"":
            i = _skip_quoted(text, i)
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise JsParseError("unterminated template expression")


def _skip_quoted(text: str, i: int) -> int:
    quote = text[i]
    n = len(text)
    i += 1
    while i < n and text[i] != "\n":
        if text[i] == "\\":
            i += 2
        elif text[i] == quote:
            return i + 1
        else:
            i += 1
    return i  # unterminated on this line: end at the newline


def _unescape(raw: str) -> str:
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), raw)


def _tokenize(text: str) -> tuple[list[_Token], list[bool]]:
    """Tokens outside comments, plus per-line "comment-only" flags (the C-14 whole-line comment)."""
    n_lines = text.count("\n") + 1
    has_code = [False] * (n_lines + 1)
    has_comment = [False] * (n_lines + 1)
    tokens: list[_Token] = []
    n = len(text)
    i = 0
    line = 1
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
        elif ch in " \t\r":
            i += 1
        elif text.startswith("//", i):
            has_comment[line] = True
            while i < n and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise JsParseError("unterminated block comment")
            for k in range(text.count("\n", i, end) + 1):
                has_comment[line + k] = True
            line += text.count("\n", i, end)
            i = end + 2
        elif ch in "'\"":
            end = _skip_quoted(text, i)
            tokens.append(_Token("str", _unescape(text[i + 1 : end - 1]), line))
            has_code[line] = True
            i = end
        elif ch == "`":
            end = _skip_template(text, i)
            body = text[i + 1 : end - 1]
            kind = "dyn" if "${" in body else "str"
            tokens.append(_Token(kind, body if kind == "str" else "", line))
            has_code[line] = True
            line += text.count("\n", i, end)
            has_code[line] = True
            i = end
        elif ch.isalpha() or ch in "_$":
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in "_$"):
                j += 1
            tokens.append(_Token("id", text[i:j], line))
            has_code[line] = True
            i = j
        elif ch == "/" and _starts_regex(tokens):
            j = i + 1
            in_class = False
            while j < n and text[j] != "\n":
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == "[":
                    in_class = True
                elif text[j] == "]":
                    in_class = False
                elif text[j] == "/" and not in_class:
                    break
                j += 1
            if j >= n or text[j] != "/":
                raise JsParseError("unterminated regular expression literal")  # E-74
            j += 1
            while j < n and (text[j].isalnum() or text[j] in "_$"):  # flags
                j += 1
            tokens.append(_Token("str", "", line))  # a regex literal is an opaque operand
            has_code[line] = True
            i = j
        else:
            tokens.append(_Token("p", ch, line))
            has_code[line] = True
            i += 1
    comment_only = [has_comment[k] and not has_code[k] for k in range(n_lines + 1)]
    return tokens, comment_only[1:]


def _starts_regex(tokens: list[_Token]) -> bool:
    if not tokens:
        return True
    last = tokens[-1]
    if last.kind == "p":
        return last.value not in _DIVISION_PUNCTUATION
    if last.kind == "id":
        return last.value in _REGEX_KEYWORDS
    return False


def _matching_paren(tokens: list[_Token], open_idx: int) -> int:
    depth = 0
    for k in range(open_idx, len(tokens)):
        tok = tokens[k]
        if tok.kind != "p":
            continue
        if tok.value == "(":
            depth += 1
        elif tok.value == ")":
            depth -= 1
            if depth == 0:
                return k
    raise JsParseError("unbalanced parentheses")


def _is(tokens: list[_Token], k: int, value: str) -> bool:
    return k < len(tokens) and tokens[k].kind == "p" and tokens[k].value == value


def delimit_js(lines: tuple[str, ...]) -> tuple[list[JsCase], list[str], list[bool]]:
    """Return (cases, undelimited `line N` list, per-line comment-only flags). Raises
    JsParseError (E-74). The flags are the C-14 whole-line-comment test for every line."""
    text = "\n".join(lines)
    tokens, comment_only = _tokenize(text)
    depth = 0  # C-03 / E-74: the whole file's parentheses balance, not only each call's
    for tok in tokens:
        if tok.kind == "p" and tok.value in "()":
            depth += 1 if tok.value == "(" else -1
            if depth < 0:
                raise JsParseError("unbalanced parentheses")
    if depth:
        raise JsParseError("unbalanced parentheses")
    suites: list[tuple[int, int, str]] = []  # (open_idx, close_idx, title)
    raw_tests: list[tuple[int, int, int, str]] = []  # (open_idx, start, end, title)
    undelimited: list[str] = []
    for i, tok in enumerate(tokens):
        if tok.kind != "id" or (tok.value not in _SUITES and tok.value not in _TESTS):
            continue
        if i > 0 and _is(tokens, i - 1, "."):
            continue  # a member call such as `pattern.test(x)`
        j = i + 1
        valid = True
        while _is(tokens, j, ".") and j + 1 < len(tokens) and tokens[j + 1].kind == "id":
            mod = tokens[j + 1].value
            if mod not in _MODIFIERS:
                valid = False
                break
            j += 2
            if mod in _ARGUMENT_MODIFIERS:
                if _is(tokens, j, "("):
                    j = _matching_paren(tokens, j) + 1
                elif j < len(tokens) and tokens[j].kind in ("str", "dyn"):
                    j += 1  # a tagged template table
                else:
                    valid = False
                    break
        if not valid or not _is(tokens, j, "("):
            continue
        close = _matching_paren(tokens, j)
        title_tok = tokens[j + 1] if j + 1 < len(tokens) else None
        literal = title_tok is not None and title_tok.kind == "str" and title_tok.value != ""
        if tok.value in _SUITES:
            if literal:
                assert title_tok is not None
                suites.append((j, close, title_tok.value))
            else:
                undelimited.append(f"line {tok.line}")
            continue
        if not literal:
            undelimited.append(f"line {tok.line}")
            continue
        assert title_tok is not None
        raw_tests.append((j, tok.line, tokens[close].line, title_tok.value))
    suites.sort()
    cases: list[JsCase] = []
    for open_idx, start, end, title in raw_tests:
        chain = [t for o, c, t in suites if o < open_idx < c]
        first = start
        while first - 2 >= 0 and comment_only[first - 2]:  # contiguous comment block above
            first -= 1
        cases.append(JsCase(" > ".join(chain + [title]), first, end))
    return cases, undelimited, comment_only


def is_each_template(name: str) -> bool:
    """True when a test name carries `each` placeholders and so stands for several results."""
    return _PLACEHOLDER_RE.search(name) is not None


def each_pattern(name: str) -> re.Pattern[str]:
    """E-76: the regular expression a result name must fully match to join a templated case."""
    parts: list[str] = []
    pos = 0
    for m in _PLACEHOLDER_RE.finditer(name):
        parts.append(re.escape(name[pos : m.start()]))
        parts.append("%" if m.group(0) == "%%" else ".*?")
        pos = m.end()
    parts.append(re.escape(name[pos:]))
    return re.compile("".join(parts), re.DOTALL)
