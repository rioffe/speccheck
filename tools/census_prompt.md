You are classifying one obligation of a software specification by what would be cheapest to
verify it, not by how it reads.

You will receive one JSON object with these fields:
  id        - a specification ID, e.g. "K-14"
  family    - one of "R", "C", "I", "K", "E"
  statement - the normative text of that ID: its title on the first line and, for an ID declared
              by a heading, the section beneath it - prose, tables, and code blocks.

Classify the obligation along two axes and report what you found.

form is exactly one of:
  "expr"     - reduces to one closed boolean or arithmetic proposition over named quantities the
               implementation exposes; a checker could evaluate it from values alone, with no
               need to run the system or read its source (e.g. a byte bound, a ratio range, an
               injective-mapping property).
  "struct"   - asserts that a named thing exists with a named shape - a key, a field, a file, a
               symbol, a column, an exact literal - rather than a computed relationship between
               values.
  "behavior" - a stimulus and an observable response that only running the system can show (an
               input that produces an exit code, a sequence of calls that must be reflected in
               output); it is not one static proposition, and it is not merely a shape.
  "prose"    - intent, scope, or a quality no single observation settles (why something exists,
               a boundary drawn in words, a property with no stated formula or test).

checker is the cheapest mechanism that could verify the form:
  "ast"    - a pattern found in source code, no execution needed
  "schema" - a structural check of a produced artifact (a file, a JSON object)
  "test"   - execute the system and observe the result
  "llm"    - the obligation needs judgment; no mechanical check suffices

The mapping is: expr -> ast or test; struct -> schema or ast; behavior -> test; prose -> llm.
Choose the one that best fits within that set; if two apply equally, prefer the cheaper (ast or
schema over test; test over llm).

Also report:
  expression - if form is "expr" or "struct", the check itself, written in the specification's
               own notation (a formula, a comparison, a pinned key list) - not a paraphrase. ""
               for "behavior" and "prose", or when no closed expression exists.
  scope      - {"stated": true|false, "text": "..."}. "stated" is true when the statement itself
               names, in words, the conditions under which the obligation applies (a mode, a
               flag, a precondition). "text" is the condition under which the obligation actually
               applies: quote it from the statement when "stated" is true; when "stated" is
               false, give your own best inference of an implicit condition if you can see one
               (a reader would have to work out the same condition to apply the row correctly),
               and leave "text" as "" only when the obligation is genuinely unconditional or you
               see no condition at all. A non-empty "text" with "stated": false is itself a
               finding - it means you had to infer something the statement never says.
  quantities - the named quantities the obligation is written over (variable names, field names,
               metric names as the statement spells them), or [] if none.
  confidence - your confidence in this classification, 0.0 to 1.0.
  rationale  - one sentence, at most 280 characters, naming what in the statement drove the
               classification.

Reply with one JSON object and nothing else - no prose, no markdown fence:
  {"form": <FORM>, "checker": <CHECKER>, "expression": <text>, "scope": {"stated": <bool>, "text": <text>},
   "quantities": [<text>, ...], "confidence": <number>, "rationale": <text>}

Rules:
  - Classify by what a verifier would need to do, not by sentence structure. A row that reads
    like a rule ("X MUST equal Y") but requires running the system to observe X is "behavior" or
    "expr" depending on whether X and Y are already-known values or values only observable at
    runtime; prefer "expr" when the relationship holds over any run's exposed values, "behavior"
    when the obligation is about what a specific stimulus causes to happen.
  - A statement with several distinct obligations should be classified by its dominant,
    load-bearing one - the one whose failure would most clearly make the row false.
  - When genuinely uncertain between two forms, choose the more expensive one to verify (prose
    over behavior over struct over expr) and say so in the rationale; confidence should reflect
    the uncertainty.
  - Do not invent a formula or key list that is not in the statement. If no closed expression
    exists, expression is "".
  - Judge only the given statement. Do not assume context from other IDs unless the statement
    itself references them.
