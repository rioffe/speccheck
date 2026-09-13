#!/bin/bash

# spec2pdf.sh: Converts a Markdown specification (with LaTeX math and mermaid
# diagrams) to PDF using pandoc and xelatex. Derived from md2pdf.sh with the
# spec-friendly options on by default: --toc --mermaid --click --margin 1in.

set -e

usage() {
  cat <<'EOF'
Usage: spec2pdf.sh [OPTIONS] <input_file.md>

Convert a Markdown specification (with LaTeX math and mermaid diagrams) to
PDF via pandoc + XeLaTeX. The output is written next to the input as
<input_file with .md replaced by .pdf>.

Defaults (all on; each can be switched off):
  --toc            Table of contents.                    (off: --no-toc)
  --mermaid        Render ```mermaid diagrams
                   (needs Chrome/Chromium).              (off: --no-mermaid)
  --click          Requirement-id mentions (R-/C-/I-/K-/E-/T-) become
                   clickable PDF jump-links; implies --toc and runs xelatex
                   a 3rd pass so forward links + the TOC resolve. Links are
                   blue.                                 (off: --no-click)
  --margin MARGIN  Page margin on all sides, default 1in (e.g. 0.5in, 1cm).

  -h, --help       Show this help and exit.

Environment variables (all optional; mermaid only):
  PUPPETEER_EXECUTABLE_PATH   Chrome/Chromium binary to use
                              (auto-detected when unset).
  MERMAID_FILTER_FORMAT       Mermaid output format (default: pdf = vector,
                              crisp at any zoom).
  MERMAID_FILTER_SCALE        Raster scale for the mermaid PNG fallback
                              (default: 3).

Examples:
  spec2pdf.sh SPEC.md                   # toc + mermaid + click, 1in margins
  spec2pdf.sh --no-click ARCHITECTURE.md
  spec2pdf.sh --margin 0.5in SPEC.md
EOF
}

TOC_FLAG=(--toc)
MERMAID_FLAG=(--filter mermaid-filter)
MARGIN_VAL="1in"
CLICK=1

while [[ $# -gt 0 ]]; do
  echo "Arg: $1"
  case $1 in
  -h | --help)
    usage
    exit 0
    ;;
  --toc)
    TOC_FLAG=(--toc)
    shift
    ;;
  --no-toc)
    TOC_FLAG=()
    shift
    ;;
  --mermaid)
    MERMAID_FLAG=(--filter mermaid-filter)
    shift
    ;;
  --no-mermaid)
    MERMAID_FLAG=()
    shift
    ;;
  --margin)
    shift
    if [[ $# -eq 0 || "$1" == -* ]]; then
      echo "Error: --margin requires a value (e.g. 0.5in, 1cm, 0.3in)." >&2
      exit 1
    fi
    MARGIN_VAL="$1"
    shift
    ;;
  --click)
    CLICK=1
    shift
    ;;
  --no-click)
    CLICK=0
    shift
    ;;
  *)
    INPUT_FILE="$1"
    shift
    ;;
  esac
done

if [[ -z "$INPUT_FILE" ]]; then
  usage >&2
  exit 1
fi

MARGIN_HEADER_FILE=$(mktemp /tmp/spec2pdf_geometry_$$_XXXXXX)
echo "\usepackage[margin=${MARGIN_VAL}]{geometry}" >"$MARGIN_HEADER_FILE"
GEOMETRY_FLAG=(--include-in-header="$MARGIN_HEADER_FILE")

if [ ! -f "$INPUT_FILE" ]; then
  echo "Error: File '$INPUT_FILE' not found."
  exit 1
fi

# When rendering mermaid, 'mermaid-filter' -> 'mmdc' -> puppeteer needs a
# Chromium executable. puppeteer's pinned rev is often missing from
# ~/.cache/puppeteer; fall back to a system Chrome/Chromium/Edge via
# PUPPETEER_EXECUTABLE_PATH (an already-exported value is always respected).
if [ "${#MERMAID_FLAG[@]}" -gt 0 ]; then
  # mermaid-filter defaults to a low-DPI PNG (800px, scale=1) that looks
  # fuzzy in PDFs. Default to vector output (crisp at any zoom) with a
  # high-scale raster fallback, but always respect a value the user set.
  if [ -z "${MERMAID_FILTER_FORMAT:-}" ]; then
    MERMAID_FILTER_FORMAT="pdf"
    export MERMAID_FILTER_FORMAT
    echo "mermaid: defaulting MERMAID_FILTER_FORMAT=pdf (vector; crisp at any zoom)"
  fi
  if [ -z "${MERMAID_FILTER_SCALE:-}" ]; then
    MERMAID_FILTER_SCALE="3"
    export MERMAID_FILTER_SCALE
    echo "mermaid: defaulting MERMAID_FILTER_SCALE=3 (high-res raster fallback)"
  fi
  # mmdc -> puppeteer needs a Chromium binary. A pinned rev is often
  # missing from ~/.cache/puppeteer, so fall back to a system browser.
  # An already-exported PUPPETEER_EXECUTABLE_PATH is always respected.
  if [ -z "${PUPPETEER_EXECUTABLE_PATH:-}" ]; then
    found=0
    if [ "$(uname)" = "Darwin" ]; then
      for cand in \
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary" \
        "/Applications/Chromium.app/Contents/MacOS/Chromium" \
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"; do
        if [ -x "$cand" ]; then
          PUPPETEER_EXECUTABLE_PATH="$cand"
          export PUPPETEER_EXECUTABLE_PATH
          found=1
          break
        fi
      done
    else
      for cand in google-chrome google-chrome-stable chromium chromium-browser; do
        if bin="$(command -v "$cand" 2>/dev/null)"; then
          PUPPETEER_EXECUTABLE_PATH="$bin"
          export PUPPETEER_EXECUTABLE_PATH
          found=1
          break
        fi
      done
    fi
    if [ "$found" -eq 1 ]; then
      echo "mermaid: using system browser via PUPPETEER_EXECUTABLE_PATH=$PUPPETEER_EXECUTABLE_PATH"
    else
      echo "Warning: no Chromium/Chrome found for mermaid; diagrams may fail to render." >&2
      echo "           (set PUPPETEER_EXECUTABLE_PATH, or run \"npx puppeteer browsers install chrome\")." >&2
    fi
  else
    echo "mermaid: using PUPPETEER_EXECUTABLE_PATH=$PUPPETEER_EXECUTABLE_PATH"
  fi
fi

# Locate /scripts next to the REAL file: install.sh puts a symlink on PATH
# (~/.local/bin/spec2pdf.sh), so follow links before taking dirname.
SELF="$0"
while [ -L "$SELF" ]; do
  link_target=$(readlink "$SELF")
  case $link_target in
  /*) SELF="$link_target" ;;
  *) SELF="$(dirname "$SELF")/$link_target" ;;
  esac
done
SCRIPTS_DIR="$(cd "$(dirname "$SELF")" && pwd)/scripts" # CWD-independent /scripts
OUTPUT_FILE="${INPUT_FILE%.md}.pdf"
TEMP_FILE=$(mktemp /tmp/spec2pdf.XXXXXX).md
LINKED_FILE=""
WORK_DIR=""

# --click implies --toc: the clickable table of contents is the point of it.
if [[ "$CLICK" -eq 1 ]]; then
  TOC_FLAG=(--toc)
fi

echo "Processing '$INPUT_FILE'..."

# When --click, first rewrite requirement-id mentions into [ID](#anchor) links +
# add anchors; leave code/Math/inline-code verbatim.  Default mode skips this, so
# its behavior is unchanged.
if [[ "$CLICK" -eq 1 ]]; then
  echo "Clickable cross-links: generating jump-links + anchors..."
  LINKED_FILE=$(mktemp /tmp/spec2pdf.XXXXXX).md
  if ! python3 "$SCRIPTS_DIR/xref_preprocess.py" "$INPUT_FILE" "$LINKED_FILE" 1>&2; then
    echo "Error: cross-reference pre-processing failed." >&2
    rm -f "$LINKED_FILE" "$MARGIN_HEADER_FILE"
    exit 1
  fi
fi

# Pre-process [ ... ] math blocks to $$ ... $$ (identical for both modes).
# This is FENCE-AWARE: the [ / ] math-fence convention must not fire on a lone
# '[' or ']' line that lives inside a fenced code block (e.g. 'pyproject.toml'
# has 'authors = [ ... ]', and a bare ']' there used to become a stray '$$').
# A line that is only '[ ' opens a math fence; only ']' closes it. We toggle a
# state on any ``` / ~~~ fence and skip substitution inside code fence spans.
SOURCE_MD="$INPUT_FILE"
[[ -n "$LINKED_FILE" ]] && SOURCE_MD="$LINKED_FILE"
awk '
  BEGIN { fence = 0 }
  /^[[:space:]]*(\x60\x60\x60|~~~)/ { fence = !fence; print; next }
  !fence {
    if ($0 ~ /^[[:space:]]*\[[[:space:]]*$/) { print "$$"; print ""; next }
    if ($0 ~ /^[[:space:]]*\][[:space:]]*$/) { print ""; print "$$"; next }
  }
  { print }
' "$SOURCE_MD" >"$TEMP_FILE"

if [[ "$CLICK" -eq 1 ]]; then
  # Standalone .tex (so hyperref / anchors / TOC are emitted) + 3 xelatex passes
  # so the forward links and the TOC resolve.  Blue links come from the -V ops.
  WORK_DIR=$(mktemp -d /tmp/spec2pdf.XXXXXX)
  COLOR_OPS=(-V colorlinks=true -V linkcolor=blue -V urlcolor=red -V toccolor=blue)
  if pandoc "$TEMP_FILE" "${TOC_FLAG[@]}" "${MERMAID_FLAG[@]}" "${GEOMETRY_FLAG[@]}" \
    "${COLOR_OPS[@]}" --to=latex -s -o "$WORK_DIR/doc.tex"; then
    # 3 passes so forward refs + TOC resolve (each pass sees the prior .aux).
    xelatex -interaction=nonstopmode -output-directory="$WORK_DIR" doc.tex >/dev/null 2>&1
    xelatex -interaction=nonstopmode -output-directory="$WORK_DIR" doc.tex >/dev/null 2>&1
    xelatex -interaction=nonstopmode -output-directory="$WORK_DIR" doc.tex >/dev/null 2>&1
    if [[ -f "$WORK_DIR/doc.pdf" ]]; then
      cp "$WORK_DIR/doc.pdf" "$OUTPUT_FILE"
      echo "Success! Created '$OUTPUT_FILE' (clickable cross-references)."
    else
      echo "Error: xelatex did not produce a PDF." >&2
      rm -f "$TEMP_FILE" "$LINKED_FILE" "$MARGIN_HEADER_FILE"
      rm -rf "$WORK_DIR"
      exit 1
    fi
  else
    echo "Error: pandoc failed." >&2
    rm -f "$TEMP_FILE" "$LINKED_FILE" "$MARGIN_HEADER_FILE"
    rm -rf "$WORK_DIR"
    exit 1
  fi
else
  echo "Converting to PDF via pandoc (using xelatex) with ${TOC_FLAG[*]} ${MERMAID_FLAG[*]} ${GEOMETRY_FLAG[*]}..."

  if pandoc "$TEMP_FILE" "${TOC_FLAG[@]}" "${MERMAID_FLAG[@]}" "${GEOMETRY_FLAG[@]}" --pdf-engine=xelatex -o "$OUTPUT_FILE" -V colorlinks=true -V linkcolor=blue -V urlcolor=red -V toccolor=blue; then
    echo "Success! Created '$OUTPUT_FILE'."
    # Fallback to default engine if xelatex fails
  else
    echo "xelatex failed or not found. Retrying with default engine..."
    if pandoc "$TEMP_FILE" "${TOC_FLAG[@]}" "${MERMAID_FLAG[@]}" "${GEOMETRY_FLAG[@]}" -o "$OUTPUT_FILE" -V colorlinks=true -V linkcolor=blue -V urlcolor=red -V toccolor=blue; then
      echo "Success! Created '$OUTPUT_FILE' (using default engine)."
    else
      echo "Error: Conversion failed."
      rm -f "$TEMP_FILE" "$MARGIN_HEADER_FILE"
      exit 1
    fi
  fi
fi

rm -f "$TEMP_FILE" "$LINKED_FILE" "$MARGIN_HEADER_FILE"
[[ -n "$WORK_DIR" ]] && rm -rf "$WORK_DIR"
