#!/usr/bin/env bash
#
# install.sh — install the speccheck toolkit for the local user:
#
#   1. the five skills (spec-writing, spec-review, spec-plan, spec-build, spec-proposal) into
#      the skill directories of the coding agents you use: Claude Code, Pi, and Oh My Pi;
#   2. spec2pdf.sh (+ scripts/xref_preprocess.py) onto your PATH, together with
#      its rendering dependencies (pandoc, XeLaTeX, mermaid-filter, a browser);
#   3. the speccheck CLI itself, as a uv tool with the [llm] extra, plus the
#      LLM judge environment (Ollama + a model + the SPECCHECK_JUDGE_* variables
#      in ~/.config/speccheck/judge.env) so the spec-build gate's Phase B
#      (--judge llm) works out of the box.
#
# Everything is per-user (nothing under /usr); the only sudo is the one Homebrew
# / apt / tlmgr may ask for themselves. Re-running is safe: files are replaced,
# packages already present are skipped.
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(spec-writing spec-review spec-plan spec-build spec-proposal)

# ---------------------------------------------------------------- defaults --
DO_SKILLS=0
DO_SPEC2PDF=0
DO_DEPS=1
DO_SPECCHECK=0
AGENTS=""
MODE="copy"     # copy | link
PREFIX="${SPECCHECK_PREFIX:-$HOME/.local}"
TEX="full"      # full | basic
DO_JUDGE=1
JUDGE_MODEL="${SPECCHECK_JUDGE_MODEL:-qwen3:8b}"
JUDGE_URL="${SPECCHECK_JUDGE_URL:-http://localhost:11434/v1/chat/completions}"
JUDGE_ENV="${XDG_CONFIG_HOME:-$HOME/.config}/speccheck/judge.env"
RC_FILE=""
DRY=0
UNINSTALL=0
INTERACTIVE=0
COMPONENTS_GIVEN=0

usage() {
  cat <<'EOF'
Usage: ./install.sh [COMPONENTS] [OPTIONS]

Components (default: all three):
  --skills             install skills/{spec-writing,spec-review,spec-plan,spec-build,spec-proposal}
  --spec2pdf           install spec2pdf.sh + scripts/ and its dependencies
  --speccheck          install the speccheck CLI (uv tool, with the [llm] extra)
                       and the LLM judge environment: Ollama, the judge model,
                       and SPECCHECK_JUDGE_* in ~/.config/speccheck/judge.env

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
  --judge-model M      Ollama model for --judge llm (default: qwen3:8b, or
                       $SPECCHECK_JUDGE_MODEL if set); pulled if missing
  --judge-url URL      chat-completions endpoint (default: local Ollama, or
                       $SPECCHECK_JUDGE_URL if set)
  --no-judge           skip Ollama / model / judge.env
  --rc FILE            append `source judge.env` to this shell rc file (e.g.
                       ~/.zshrc); by default the line is only printed
  --uninstall          remove what this script installed (skills, spec2pdf.sh,
                       the speccheck tool, judge.env); dependencies are left alone
  --dry-run            print what would be done without doing it
  -i, --interactive    ask about every choice above (components, agents,
                       copy/link, prefix, deps, judge model, shell rc) with
                       sensible defaults, show the plan, then confirm
  -h, --help           this help

Where things go:
  Claude Code   ~/.claude/skills/<skill>/SKILL.md
  Pi            ~/.pi/agent/skills/<skill>/SKILL.md
  Oh My Pi      ~/.omp/agent/skills/<skill>/SKILL.md
  (agents)      ~/.agents/skills/<skill>/SKILL.md
  spec2pdf.sh   <prefix>/bin/spec2pdf.sh -> <prefix>/share/speccheck/spec2pdf.sh
  speccheck     ~/.local/bin/speccheck (uv tool install)
  judge env     ~/.config/speccheck/judge.env (SPECCHECK_JUDGE_URL / _MODEL / _API_KEY / _TIMEOUT)

Examples:
  ./install.sh                         # everything, for claude + pi + omp
  ./install.sh --skills --link         # only the skills, as symlinks
  ./install.sh --agents claude --skills
  ./install.sh --spec2pdf --no-deps    # just the script, deps already present
  ./install.sh --speccheck --judge-model gemma4:latest --rc ~/.zshrc
  ./install.sh --uninstall
  ./install.sh -i                      # guided
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
  --judge-model)
    shift
    [[ $# -gt 0 && "$1" != -* ]] || { echo "Error: --judge-model needs a model name." >&2; exit 2; }
    JUDGE_MODEL="$1"
    ;;
  --judge-model=*) JUDGE_MODEL="${1#--judge-model=}" ;;
  --judge-url)
    shift
    [[ $# -gt 0 && "$1" != -* ]] || { echo "Error: --judge-url needs a URL." >&2; exit 2; }
    JUDGE_URL="$1"
    ;;
  --judge-url=*) JUDGE_URL="${1#--judge-url=}" ;;
  --no-judge) DO_JUDGE=0 ;;
  --rc)
    shift
    [[ $# -gt 0 && "$1" != -* ]] || { echo "Error: --rc needs a file (e.g. ~/.zshrc)." >&2; exit 2; }
    RC_FILE="$1"
    ;;
  --rc=*) RC_FILE="${1#--rc=}" ;;
  --uninstall) UNINSTALL=1 ;;
  --dry-run) DRY=1 ;;
  -i | --interactive) INTERACTIVE=1 ;;
  -h | --help) usage; exit 0 ;;
  *) echo "Error: unknown argument '$1'." >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# No component named -> all of them.
if [[ $DO_SKILLS -eq 0 && $DO_SPEC2PDF -eq 0 && $DO_SPECCHECK -eq 0 ]]; then
  DO_SKILLS=1; DO_SPEC2PDF=1; DO_SPECCHECK=1
else
  COMPONENTS_GIVEN=1
fi

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
    say "    $agent: $dir/{spec-writing,spec-review,spec-plan,spec-build,spec-proposal}"
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

# The LLM judge (spec-build gate, Phase B) needs an OpenAI-compatible endpoint
# and three variables; a local Ollama is the zero-account way to get one.
install_judge() {
  step "LLM judge: Ollama + $JUDGE_MODEL + $JUDGE_ENV"
  local local_ollama=0
  case $JUDGE_URL in
  http://localhost:*|http://127.0.0.1:*) local_ollama=1 ;;
  esac

  if [[ $local_ollama -eq 1 ]]; then
    if ! have ollama; then
      case $PKG in
      brew) run brew install ollama ;;
      apt | "") run sh -c 'curl -fsSL https://ollama.com/install.sh | sh' ;;
      esac
    fi
    local tags_url="${JUDGE_URL%/v1/chat/completions}/api/tags"
    if curl -fsS -m 3 "$tags_url" >/dev/null 2>&1; then
      if curl -fsS -m 3 "$tags_url" | grep -q "\"name\":\"$JUDGE_MODEL\""; then
        say "    model $JUDGE_MODEL already pulled"
      else
        run ollama pull "$JUDGE_MODEL"
      fi
    else
      warn "Ollama is not serving at ${tags_url%/api/tags}; start it (\`ollama serve\`, or the Ollama app) and run  ollama pull $JUDGE_MODEL"
    fi
  else
    say "    remote endpoint; not managing a server or model. Set SPECCHECK_JUDGE_API_KEY in $JUDGE_ENV."
  fi

  run mkdir -p "$(dirname "$JUDGE_ENV")"
  if [[ $DRY -eq 1 ]]; then
    say "    would write $JUDGE_ENV"
  else
    # Keep an API key the user already put in the file (a remote endpoint).
    local key="ollama"
    if [[ -f "$JUDGE_ENV" ]]; then
      local old
      old="$(sed -n 's/^export SPECCHECK_JUDGE_API_KEY=//p' "$JUDGE_ENV" | tr -d '"' | tail -1)"
      [[ -n "$old" ]] && key="$old"
    fi
    cat >"$JUDGE_ENV" <<EOF
# speccheck --judge llm configuration (written by install.sh; edit freely).
# Source this from your shell rc:  source "$JUDGE_ENV"
export SPECCHECK_JUDGE_URL="$JUDGE_URL"
export SPECCHECK_JUDGE_MODEL="$JUDGE_MODEL"
export SPECCHECK_JUDGE_API_KEY="$key"      # any value for Ollama; the real key for a hosted endpoint
export SPECCHECK_JUDGE_TIMEOUT=120         # seconds, 1..300; thinking models need more than the default 30
EOF
    chmod 600 "$JUDGE_ENV"
    say "    wrote $JUDGE_ENV"
  fi

  local line="[ -f \"$JUDGE_ENV\" ] && source \"$JUDGE_ENV\"  # speccheck judge"
  if [[ -n "$RC_FILE" ]]; then
    if [[ -f "$RC_FILE" ]] && grep -qF "$JUDGE_ENV" "$RC_FILE"; then
      say "    $RC_FILE already sources it"
    else
      say "    appending to $RC_FILE"
      [[ $DRY -eq 1 ]] || printf '\n%s\n' "$line" >>"$RC_FILE"
    fi
  else
    say "    add to your shell rc (or pass --rc ~/.zshrc):"
    say "      $line"
  fi
}

uninstall_speccheck() {
  step "Removing the speccheck tool"
  if have uv; then run uv tool uninstall speccheck || true; fi
  remove_path "$JUDGE_ENV"
  say "    (a 'source $JUDGE_ENV' line in your shell rc, if you added one, is left for you to remove)"
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
    if [[ $DO_JUDGE -eq 1 ]]; then
      if [[ -f "$JUDGE_ENV" ]]; then say "    ok   $JUDGE_ENV"; else say "    MISSING $JUDGE_ENV"; ok=0; fi
      if [[ "${SPECCHECK_JUDGE_MODEL:-}" == "$JUDGE_MODEL" && "${SPECCHECK_JUDGE_URL:-}" == "$JUDGE_URL" ]]; then
        say "    ok   SPECCHECK_JUDGE_* set in this shell"
      else
        say "    note SPECCHECK_JUDGE_* not in this shell yet: source \"$JUDGE_ENV\" (or open a new shell)"
      fi
    fi
  fi
  if [[ $ok -eq 1 ]]; then
    say "Done."
  else
    say "Done, with problems (see above)."
    return 1
  fi
}

# ------------------------------------------------------------- interactive --
# Prompts read from the terminal directly so the wizard works even when stdout
# is piped. Every question has a default; Enter accepts it.
ask() { # ask VAR "prompt" "default"
  local var="$1" prompt="$2" def="$3" reply
  printf '%s [%s]: ' "$prompt" "$def" >/dev/tty
  IFS= read -r reply </dev/tty
  printf -v "$var" '%s' "${reply:-$def}"
}
ask_yn() { # ask_yn "prompt" y|n  -> returns 0 for yes
  local prompt="$1" def="$2" reply hint="y/N"
  [[ $def == y ]] && hint="Y/n"
  while true; do
    printf '%s [%s]: ' "$prompt" "$hint" >/dev/tty
    IFS= read -r reply </dev/tty
    reply="${reply:-$def}"
    case $reply in
    [Yy]*) return 0 ;;
    [Nn]*) return 1 ;;
    *) say "  please answer y or n" >/dev/tty ;;
    esac
  done
}
ask_choice() { # ask_choice VAR "prompt" "default" opt1 opt2 ...
  local var="$1" prompt="$2" def="$3" reply o
  shift 3
  while true; do
    printf '%s (%s) [%s]: ' "$prompt" "$*" "$def" >/dev/tty
    IFS= read -r reply </dev/tty
    reply="${reply:-$def}"
    for o in "$@"; do
      if [[ "$reply" == "$o" ]]; then printf -v "$var" '%s' "$reply"; return 0; fi
    done
    say "  choose one of: $*" >/dev/tty
  done
}

# Which agents look installed here? Used as the interactive default.
detect_agents() {
  local found=()
  { have claude || [[ -d "$HOME/.claude" ]]; } && found+=(claude)
  { have pi || [[ -d "$HOME/.pi/agent" ]]; } && found+=(pi)
  { have omp || [[ -d "$HOME/.omp/agent" ]]; } && found+=(omp)
  local IFS=','
  echo "${found[*]}"
}

# The rc file for the user's login shell.
default_rc() {
  case "$(basename "${SHELL:-/bin/sh}")" in
  zsh) echo "$HOME/.zshrc" ;;
  bash) if [[ "$OS" == "Darwin" ]]; then echo "$HOME/.bash_profile"; else echo "$HOME/.bashrc"; fi ;;
  fish) echo "$HOME/.config/fish/config.fish" ;;
  *) echo "$HOME/.profile" ;;
  esac
}

interactive() {
  [[ -r /dev/tty && -w /dev/tty ]] || { echo "Error: --interactive needs a terminal." >&2; exit 2; }
  say ""
  say "Guided install — Enter accepts the default shown in brackets."
  say ""

  # 1. components (flags on the command line pre-select; otherwise all on)
  local d_sk=y d_pdf=y d_sc=y
  if [[ $COMPONENTS_GIVEN -eq 1 ]]; then
    [[ $DO_SKILLS -eq 1 ]] || d_sk=n
    [[ $DO_SPEC2PDF -eq 1 ]] || d_pdf=n
    [[ $DO_SPECCHECK -eq 1 ]] || d_sc=n
  fi
  ask_yn "Install the skills (spec-writing, spec-review, spec-plan, spec-build, spec-proposal)?" "$d_sk" && DO_SKILLS=1 || DO_SKILLS=0
  ask_yn "Install spec2pdf.sh (Markdown -> PDF with math, mermaid, clickable ids)?" "$d_pdf" && DO_SPEC2PDF=1 || DO_SPEC2PDF=0
  ask_yn "Install the speccheck CLI (the spec-build conformance gate)?" "$d_sc" && DO_SPECCHECK=1 || DO_SPECCHECK=0
  if [[ $DO_SKILLS -eq 0 && $DO_SPEC2PDF -eq 0 && $DO_SPECCHECK -eq 0 ]]; then
    say "Nothing selected; exiting."
    exit 0
  fi

  # 2. skills: agents + copy/link
  if [[ $DO_SKILLS -eq 1 ]]; then
    local detected
    detected="$(detect_agents)"
    [[ -n "$detected" ]] || detected="claude,pi,omp"
    say ""
    say "Agents: claude (~/.claude/skills), pi (~/.pi/agent/skills), omp (~/.omp/agent/skills),"
    say "        agents (~/.agents/skills, a shared directory both pi and omp read)."
    [[ -n "$AGENTS" ]] && detected="$AGENTS"
    while true; do
      ask AGENTS "Install skills for (comma-separated)" "$detected"
      local ok=1 a
      IFS=',' read -r -a agent_list <<<"$AGENTS"
      for a in "${agent_list[@]}"; do
        case $a in claude | pi | omp | agents) ;; *) say "  unknown agent '$a'"; ok=0 ;; esac
      done
      [[ $ok -eq 1 && ${#agent_list[@]} -gt 0 ]] && break
    done
  fi
  if [[ $DO_SKILLS -eq 1 || $DO_SPEC2PDF -eq 1 ]]; then
    say ""
    say "copy = a snapshot of this checkout; link = symlinks into it, so 'git pull' updates in place."
    ask_choice MODE "Install skills / spec2pdf.sh as" "$MODE" copy link
  fi

  # 3. spec2pdf: prefix, deps, tex flavour
  if [[ $DO_SPEC2PDF -eq 1 ]]; then
    say ""
    ask PREFIX "Prefix for spec2pdf.sh (bin/ and share/ go under it)" "$PREFIX"
    PREFIX="${PREFIX/#\~/$HOME}"
    local d_deps=y
    [[ $DO_DEPS -eq 1 ]] || d_deps=n
    ask_yn "Install rendering dependencies (pandoc, XeLaTeX, mermaid-filter, a browser) if missing?" "$d_deps" && DO_DEPS=1 || DO_DEPS=0
    if [[ $DO_DEPS -eq 1 && "$PKG" == "brew" ]] && ! have xelatex && [[ ! -x /Library/TeX/texbin/xelatex ]]; then
      say "  full  = MacTeX without GUI apps (~5 GB, everything works)"
      say "  basic = BasicTeX (~100 MB) plus the packages pandoc needs via tlmgr (asks for sudo)"
      ask_choice TEX "TeX distribution" "$TEX" full basic
    fi
  fi

  # 4. speccheck: judge
  if [[ $DO_SPECCHECK -eq 1 ]]; then
    say ""
    local d_judge=y
    [[ $DO_JUDGE -eq 1 ]] || d_judge=n
    if ask_yn "Set up the LLM judge (Ollama + model + SPECCHECK_JUDGE_* env) for --judge llm?" "$d_judge"; then
      DO_JUDGE=1
      ask JUDGE_URL "Chat-completions endpoint" "$JUDGE_URL"
      local tags_url="${JUDGE_URL%/v1/chat/completions}/api/tags" models=""
      case $JUDGE_URL in
      http://localhost:* | http://127.0.0.1:*)
        models="$(curl -fsS -m 3 "$tags_url" 2>/dev/null | tr ',' '\n' | sed -n 's/.*"name":"\([^"]*\)".*/\1/p' | tr '\n' ' ')"
        [[ -n "$models" ]] && say "  models already pulled locally: $models"
        ;;
      esac
      ask JUDGE_MODEL "Judge model (pulled if missing)" "$JUDGE_MODEL"
      local rc_default
      rc_default="$(default_rc)"
      if ask_yn "Append 'source judge.env' to your shell rc so the variables are always set?" y; then
        ask RC_FILE "Shell rc file" "${RC_FILE:-$rc_default}"
        RC_FILE="${RC_FILE/#\~/$HOME}"
      else
        RC_FILE=""
      fi
    else
      DO_JUDGE=0
    fi
  fi

  # 5. plan + confirm
  say ""
  say "Plan:"
  [[ $DO_SKILLS -eq 1 ]] && say "  skills      $MODE -> ${AGENTS//,/, }"
  if [[ $DO_SPEC2PDF -eq 1 ]]; then
    say "  spec2pdf.sh $MODE -> $PREFIX/bin/spec2pdf.sh$([[ $DO_DEPS -eq 1 ]] && printf ', with dependencies (tex: %s)' "$TEX" || printf ', no dependencies')"
  fi
  if [[ $DO_SPECCHECK -eq 1 ]]; then
    say "  speccheck   uv tool install speccheck[llm] from $REPO"
    if [[ $DO_JUDGE -eq 1 ]]; then
      say "  judge       $JUDGE_MODEL @ $JUDGE_URL -> $JUDGE_ENV$([[ -n "$RC_FILE" ]] && printf ', sourced from %s' "$RC_FILE")"
    fi
  fi
  say ""
  if ! ask_yn "Proceed?" y; then
    say "Aborted; nothing changed. Equivalent non-interactive command:"
    say "  $(equivalent_command)"
    exit 0
  fi
  say "Equivalent non-interactive command:  $(equivalent_command)"
}

# The flags that reproduce the interactive choices (printed for the record).
equivalent_command() {
  local cmd="./install.sh"
  [[ $DO_SKILLS -eq 1 ]] && cmd+=" --skills --agents $AGENTS"
  [[ $DO_SPEC2PDF -eq 1 ]] && cmd+=" --spec2pdf --prefix $PREFIX"
  [[ $DO_SPEC2PDF -eq 1 && $DO_DEPS -eq 0 ]] && cmd+=" --no-deps"
  [[ $DO_SPEC2PDF -eq 1 && $TEX == basic ]] && cmd+=" --basic-tex"
  [[ $DO_SPECCHECK -eq 1 ]] && cmd+=" --speccheck"
  if [[ $DO_SPECCHECK -eq 1 ]]; then
    if [[ $DO_JUDGE -eq 1 ]]; then
      cmd+=" --judge-model $JUDGE_MODEL --judge-url $JUDGE_URL"
      [[ -n "$RC_FILE" ]] && cmd+=" --rc $RC_FILE"
    else
      cmd+=" --no-judge"
    fi
  fi
  [[ $MODE == link ]] && cmd+=" --link"
  [[ $DRY -eq 1 ]] && cmd+=" --dry-run"
  echo "$cmd"
}

# -------------------------------------------------------------------- main --
say "speccheck toolkit installer — $REPO"
[[ $DRY -eq 1 ]] && say "(dry run: nothing will be changed)"

if [[ $INTERACTIVE -eq 1 && $UNINSTALL -eq 0 ]]; then interactive; fi
[[ -n "$AGENTS" ]] || AGENTS="claude,pi,omp"

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
[[ $DO_SPECCHECK -eq 1 && $DO_JUDGE -eq 1 ]] && install_judge
[[ $DRY -eq 1 ]] || verify
