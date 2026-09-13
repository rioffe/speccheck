#!/usr/bin/env bash
#
# install.sh — install the speccheck toolkit for the local user:
#
#   1. the three skills (spec-writing, spec-review, spec-build) into the skill
#      directories of the coding agents you use: Claude Code, Pi, and Oh My Pi;
#   2. spec2pdf.sh (+ scripts/xref_preprocess.py) onto your PATH, together with
#      its rendering dependencies (pandoc, XeLaTeX, mermaid-filter, a browser);
#   3. the speccheck CLI itself, as a uv tool with the [llm] extra so the
#      spec-build gate's Phase B (--judge llm) works out of the box.
#
# Everything is per-user (nothing under /usr); the only sudo is the one Homebrew
# / apt / tlmgr may ask for themselves. Re-running is safe: files are replaced,
# packages already present are skipped.
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(spec-writing spec-review spec-build)

# ---------------------------------------------------------------- defaults --
DO_SKILLS=0
DO_SPEC2PDF=0
DO_DEPS=1
DO_SPECCHECK=0
AGENTS=""
MODE="copy"     # copy | link
PREFIX="${SPECCHECK_PREFIX:-$HOME/.local}"
TEX="full"      # full | basic
DRY=0
UNINSTALL=0

usage() {
  cat <<'EOF'
Usage: ./install.sh [COMPONENTS] [OPTIONS]

Components (default: all three):
  --skills             install skills/{spec-writing,spec-review,spec-build}
  --spec2pdf           install spec2pdf.sh + scripts/ and its dependencies
  --speccheck          install the speccheck CLI (uv tool, with the [llm] extra)

Options:
  --agents LIST        comma-separated agents to install skills for
                       (default: claude,pi,omp; also accepts "agents" for the
                       shared ~/.agents/skills directory that Pi and OMP read)
  --link               symlink skills and spec2pdf.sh into this checkout instead
                       of copying, so `git pull` updates them in place
  --prefix DIR         install prefix for spec2pdf.sh (default: ~/.local, i.e.
                       DIR/bin/spec2pdf.sh and DIR/share/speccheck/)
  --no-deps            do not install pandoc / TeX / mermaid-filter / browser
  --basic-tex          macOS: install BasicTeX + the needed packages via tlmgr
                       instead of the full MacTeX (no GUI) distribution
  --uninstall          remove what this script installed (skills, spec2pdf.sh,
                       the speccheck tool); dependencies are left alone
  --dry-run            print what would be done without doing it
  -h, --help           this help

Where things go:
  Claude Code   ~/.claude/skills/<skill>/SKILL.md
  Pi            ~/.pi/agent/skills/<skill>/SKILL.md
  Oh My Pi      ~/.omp/agent/skills/<skill>/SKILL.md
  (agents)      ~/.agents/skills/<skill>/SKILL.md
  spec2pdf.sh   <prefix>/bin/spec2pdf.sh -> <prefix>/share/speccheck/spec2pdf.sh
  speccheck     ~/.local/bin/speccheck (uv tool install)

Examples:
  ./install.sh                         # everything, for claude + pi + omp
  ./install.sh --skills --link         # only the skills, as symlinks
  ./install.sh --agents claude --skills
  ./install.sh --spec2pdf --no-deps    # just the script, deps already present
  ./install.sh --uninstall
EOF
}

while [[ $# -gt 0 ]]; do
  case $1 in
  --skills) DO_SKILLS=1 ;;
  --spec2pdf) DO_SPEC2PDF=1 ;;
  --speccheck) DO_SPECCHECK=1 ;;
  --agents)
    shift
    [[ $# -gt 0 && "$1" != -* ]] || { echo "Error: --agents needs a list (e.g. claude,pi,omp)." >&2; exit 2; }
    AGENTS="$1"
    ;;
  --agents=*) AGENTS="${1#--agents=}" ;;
  --link) MODE="link" ;;
  --prefix)
    shift
    [[ $# -gt 0 && "$1" != -* ]] || { echo "Error: --prefix needs a directory." >&2; exit 2; }
    PREFIX="$1"
    ;;
  --prefix=*) PREFIX="${1#--prefix=}" ;;
  --no-deps) DO_DEPS=0 ;;
  --basic-tex) TEX="basic" ;;
  --uninstall) UNINSTALL=1 ;;
  --dry-run) DRY=1 ;;
  -h | --help) usage; exit 0 ;;
  *) echo "Error: unknown argument '$1'." >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# No component named -> all of them.
if [[ $DO_SKILLS -eq 0 && $DO_SPEC2PDF -eq 0 && $DO_SPECCHECK -eq 0 ]]; then
  DO_SKILLS=1; DO_SPEC2PDF=1; DO_SPECCHECK=1
fi
[[ -n "$AGENTS" ]] || AGENTS="claude,pi,omp"

# ----------------------------------------------------------------- helpers --
say()  { printf '%s\n' "$*"; }
step() { printf '\n==> %s\n' "$*"; }
warn() { printf 'Warning: %s\n' "$*" >&2; }
run() {
  # Echo then execute, unless --dry-run.
  printf '    $ %s\n' "$*"
  [[ $DRY -eq 1 ]] || "$@"
}
have() { command -v "$1" >/dev/null 2>&1; }

OS="$(uname -s)"
PKG=""
if [[ "$OS" == "Darwin" ]]; then
  have brew && PKG="brew"
elif [[ "$OS" == "Linux" ]]; then
  if have apt-get; then PKG="apt"; fi
fi

skill_dir_for() {
  case $1 in
  claude) echo "$HOME/.claude/skills" ;;
  pi)     echo "$HOME/.pi/agent/skills" ;;
  omp)    echo "$HOME/.omp/agent/skills" ;;
  agents) echo "$HOME/.agents/skills" ;;
  *) echo "Error: unknown agent '$1' (use claude, pi, omp, agents)." >&2; exit 2 ;;
  esac
}

# Remove a path that is a file, directory, or (dangling) symlink.
remove_path() {
  if [[ -L "$1" || -e "$1" ]]; then
    run rm -rf "$1"
  fi
}

# ------------------------------------------------------------------ skills --
install_skills() {
  step "Skills ($MODE) for: ${AGENTS//,/ }"
  local agent dir src dst
  IFS=',' read -r -a agent_list <<<"$AGENTS"
  for agent in "${agent_list[@]}"; do
    dir="$(skill_dir_for "$agent")"
    run mkdir -p "$dir"
    for s in "${SKILLS[@]}"; do
      src="$REPO/skills/$s"
      dst="$dir/$s"
      [[ -f "$src/SKILL.md" ]] || { echo "Error: $src/SKILL.md missing." >&2; exit 1; }
      remove_path "$dst"
      if [[ "$MODE" == "link" ]]; then
        run ln -s "$src" "$dst"
      else
        run cp -R "$src" "$dst"
      fi
    done
    say "    $agent: $dir/{spec-writing,spec-review,spec-build}"
  done
}

uninstall_skills() {
  step "Removing skills from: ${AGENTS//,/ }"
  local agent dir
  IFS=',' read -r -a agent_list <<<"$AGENTS"
  for agent in "${agent_list[@]}"; do
    dir="$(skill_dir_for "$agent")"
    for s in "${SKILLS[@]}"; do remove_path "$dir/$s"; done
  done
}

# ---------------------------------------------------------------- spec2pdf --
install_spec2pdf() {
  local bin="$PREFIX/bin" share="$PREFIX/share/speccheck"
  step "spec2pdf.sh ($MODE) -> $bin/spec2pdf.sh"
  run mkdir -p "$bin"
  remove_path "$bin/spec2pdf.sh"
  if [[ "$MODE" == "link" ]]; then
    # spec2pdf.sh resolves its own symlink, so scripts/ is found in the checkout.
    run ln -s "$REPO/spec2pdf.sh" "$bin/spec2pdf.sh"
  else
    remove_path "$share"
    run mkdir -p "$share/scripts"
    run cp "$REPO/spec2pdf.sh" "$share/spec2pdf.sh"
    run cp "$REPO/scripts/xref_preprocess.py" "$share/scripts/xref_preprocess.py"
    run chmod +x "$share/spec2pdf.sh"
    run ln -s "$share/spec2pdf.sh" "$bin/spec2pdf.sh"
  fi
  case ":$PATH:" in
  *":$bin:"*) ;;
  *) warn "$bin is not on your PATH; add  export PATH=\"$bin:\$PATH\"  to your shell profile." ;;
  esac
  [[ $DO_DEPS -eq 1 ]] && install_spec2pdf_deps
  return 0
}

uninstall_spec2pdf() {
  step "Removing spec2pdf.sh from $PREFIX"
  remove_path "$PREFIX/bin/spec2pdf.sh"
  remove_path "$PREFIX/share/speccheck"
}

# The LaTeX packages pandoc's default template + our --click output need that
# BasicTeX does not ship. Only used with --basic-tex.
TLMGR_PKGS=(collection-fontsrecommended unicode-math lm-math fontspec xetex
  geometry hyperref bookmark xurl fancyvrb framed booktabs longtable array calc
  etoolbox footnotehyper selnolig soul ulem upquote microtype parskip xcolor
  float caption titling tocloft)

install_spec2pdf_deps() {
  step "spec2pdf.sh dependencies (pandoc, xelatex, mermaid-filter, a Chromium)"
  local need_pandoc=0 need_tex=0 need_node=0 need_mermaid=0 need_browser=0
  have pandoc || need_pandoc=1
  have xelatex || [[ -x /Library/TeX/texbin/xelatex ]] || need_tex=1
  have npm || need_node=1
  { have mermaid-filter && have mmdc; } || need_mermaid=1
  have python3 || warn "python3 not found; spec2pdf.sh --click needs it."

  # A browser for mermaid (mmdc -> puppeteer). Mirror spec2pdf.sh's search.
  if [[ -z "${PUPPETEER_EXECUTABLE_PATH:-}" ]]; then
    need_browser=1
    if [[ "$OS" == "Darwin" ]]; then
      for cand in "/Applications/Google Chrome.app" "/Applications/Google Chrome Canary.app" \
        "/Applications/Chromium.app" "/Applications/Microsoft Edge.app"; do
        [[ -d "$cand" ]] && need_browser=0 && break
      done
    else
      for cand in google-chrome google-chrome-stable chromium chromium-browser; do
        have "$cand" && need_browser=0 && break
      done
    fi
    # puppeteer's own cache counts too.
    [[ -d "$HOME/.cache/puppeteer/chrome" ]] && need_browser=0
  else
    need_browser=0
  fi

  if [[ $need_pandoc -eq 0 && $need_tex -eq 0 && $need_mermaid -eq 0 && $need_browser -eq 0 ]]; then
    say "    all present: $(pandoc --version | head -1); xelatex; mermaid-filter + mmdc; a Chrome/Chromium"
    return 0
  fi

  case $PKG in
  brew)
    [[ $need_pandoc -eq 1 ]] && run brew install pandoc
    if [[ $need_tex -eq 1 ]]; then
      if [[ "$TEX" == "basic" ]]; then
        run brew install --cask basictex
        say "    BasicTeX lacks packages pandoc needs; installing them with tlmgr (asks for sudo)."
        run sudo /Library/TeX/texbin/tlmgr update --self
        run sudo /Library/TeX/texbin/tlmgr install "${TLMGR_PKGS[@]}"
      else
        say "    Installing MacTeX (no GUI, ~5 GB). Use --basic-tex for the small distribution."
        run brew install --cask mactex-no-gui
      fi
      say "    xelatex lands in /Library/TeX/texbin (on PATH after a new shell)."
    fi
    [[ $need_node -eq 1 ]] && run brew install node
    ;;
  apt)
    [[ $need_pandoc -eq 1 ]] && run sudo apt-get install -y pandoc
    [[ $need_tex -eq 1 ]] && run sudo apt-get install -y texlive-xetex texlive-fonts-recommended texlive-latex-extra texlive-fonts-extra fonts-lmodern
    [[ $need_node -eq 1 ]] && run sudo apt-get install -y nodejs npm
    ;;
  *)
    warn "no supported package manager (Homebrew / apt) found; install by hand:"
    [[ $need_pandoc -eq 1 ]] && say "      - pandoc            https://pandoc.org/installing.html"
    [[ $need_tex -eq 1 ]] && say "      - a TeX distribution with xelatex (TeX Live)"
    [[ $need_node -eq 1 ]] && say "      - Node.js + npm       https://nodejs.org"
    ;;
  esac

  if [[ $need_mermaid -eq 1 ]]; then
    if have npm || [[ $DRY -eq 1 ]]; then
      run npm install -g mermaid-filter @mermaid-js/mermaid-cli
    else
      warn "npm not available; run  npm install -g mermaid-filter @mermaid-js/mermaid-cli  once it is."
    fi
  fi

  if [[ $need_browser -eq 1 ]]; then
    say "    No Chrome/Chromium found for mermaid; fetching puppeteer's pinned Chrome into ~/.cache/puppeteer."
    if have npx || [[ $DRY -eq 1 ]]; then
      run npx --yes puppeteer browsers install chrome
    else
      warn "npx not available; install Chrome/Chromium or set PUPPETEER_EXECUTABLE_PATH."
    fi
  fi
}

# --------------------------------------------------------------- speccheck --
ensure_uv() {
  have uv && return 0
  step "uv (Python tool manager) not found; installing"
  if [[ "$PKG" == "brew" ]]; then
    run brew install uv
  else
    run sh -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    export PATH="$HOME/.local/bin:$PATH"
  fi
  have uv || [[ $DRY -eq 1 ]] || { echo "Error: uv still not on PATH; open a new shell and re-run." >&2; exit 1; }
}

install_speccheck() {
  step "speccheck CLI (uv tool install, with [llm] extra)"
  ensure_uv
  # `--force` replaces a previous install; `--reinstall` picks up source changes
  # in this checkout even when the version number did not move.
  run uv tool install --force --reinstall "speccheck[llm] @ $REPO"
  if [[ $DRY -eq 0 ]]; then
    local tool_bin
    tool_bin="$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
    case ":$PATH:" in
    *":$tool_bin:"*) ;;
    *) warn "$tool_bin is not on your PATH (run  uv tool update-shell  or add it to your profile)." ;;
    esac
    say "    $("$tool_bin/speccheck" --version 2>/dev/null || speccheck --version)"
  fi
}

uninstall_speccheck() {
  step "Removing the speccheck tool"
  if have uv; then run uv tool uninstall speccheck || true; fi
}

# ----------------------------------------------------------------- summary --
verify() {
  step "Verification"
  local ok=1
  if [[ $DO_SKILLS -eq 1 ]]; then
    IFS=',' read -r -a agent_list <<<"$AGENTS"
    for agent in "${agent_list[@]}"; do
      dir="$(skill_dir_for "$agent")"
      for s in "${SKILLS[@]}"; do
        if [[ -f "$dir/$s/SKILL.md" ]]; then say "    ok   $dir/$s/SKILL.md"; else say "    MISSING $dir/$s/SKILL.md"; ok=0; fi
      done
    done
  fi
  if [[ $DO_SPEC2PDF -eq 1 ]]; then
    if "$PREFIX/bin/spec2pdf.sh" --help >/dev/null 2>&1; then say "    ok   $PREFIX/bin/spec2pdf.sh --help"; else say "    FAIL $PREFIX/bin/spec2pdf.sh --help"; ok=0; fi
    for t in pandoc xelatex mermaid-filter; do
      if have "$t" || { [[ $t == xelatex ]] && [[ -x /Library/TeX/texbin/xelatex ]]; }; then say "    ok   $t"; else say "    MISSING $t (open a new shell if it was just installed)"; fi
    done
  fi
  if [[ $DO_SPECCHECK -eq 1 ]]; then
    if have speccheck && speccheck --self-check >/dev/null 2>&1; then
      say "    ok   speccheck --self-check"
    elif have speccheck; then
      say "    FAIL speccheck --self-check"; ok=0
    else
      say "    speccheck not on PATH yet (see the PATH warning above)"
    fi
  fi
  if [[ $ok -eq 1 ]]; then
    say "Done."
  else
    say "Done, with problems (see above)."
    return 1
  fi
}

# -------------------------------------------------------------------- main --
say "speccheck toolkit installer — $REPO"
[[ $DRY -eq 1 ]] && say "(dry run: nothing will be changed)"

if [[ $UNINSTALL -eq 1 ]]; then
  [[ $DO_SKILLS -eq 1 ]] && uninstall_skills
  [[ $DO_SPEC2PDF -eq 1 ]] && uninstall_spec2pdf
  [[ $DO_SPECCHECK -eq 1 ]] && uninstall_speccheck
  say "Removed."
  exit 0
fi

[[ $DO_SKILLS -eq 1 ]] && install_skills
[[ $DO_SPEC2PDF -eq 1 ]] && install_spec2pdf
[[ $DO_SPECCHECK -eq 1 ]] && install_speccheck
[[ $DRY -eq 1 ]] || verify
