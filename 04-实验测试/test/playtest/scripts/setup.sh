#!/usr/bin/env bash
# =============================================================================
# setup.sh — One-time environment setup for LLM Game Difficulty Framework
# =============================================================================
set -euo pipefail

REQUIRED_PYTHON="3.9"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
header()  { echo -e "\n${BOLD}${CYAN}=== $* ===${RESET}"; }

# ── Step 1: Python version check ─────────────────────────────────────────────
header "Checking Python"

PYTHON_BIN=""
for bin in python3 python; do
    if command -v "$bin" &>/dev/null; then
        ver=$("$bin" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" -ge 3 && "$minor" -ge 9 ]]; then
            PYTHON_BIN="$bin"
            success "Found $bin $ver"
            break
        fi
    fi
done

[[ -z "$PYTHON_BIN" ]] && error "Python >= $REQUIRED_PYTHON not found. Install from https://python.org"

# ── Step 2: Virtual environment ───────────────────────────────────────────────
header "Setting up virtual environment"

VENV_DIR="$PROJECT_ROOT/.venv"
if [[ -d "$VENV_DIR" ]]; then
    warn "Virtual env already exists at .venv — skipping creation"
else
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    success "Created .venv"
fi

# Activate
source "$VENV_DIR/bin/activate"
success "Activated .venv"

# ── Step 3: Install dependencies ──────────────────────────────────────────────
header "Installing dependencies"

pip install --quiet --upgrade pip
pip install --quiet -r "$PROJECT_ROOT/requirements.txt"
success "All packages installed"

# ── Step 4: API key check ─────────────────────────────────────────────────────
header "Checking API key"

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    warn "ANTHROPIC_API_KEY is not set."
    echo ""
    echo -e "  To set it temporarily (this session only):"
    echo -e "  ${YELLOW}export ANTHROPIC_API_KEY='your-key-here'${RESET}"
    echo ""
    echo -e "  To set it permanently, add to your shell profile (~/.zshrc or ~/.bashrc):"
    echo -e "  ${YELLOW}echo 'export ANTHROPIC_API_KEY=\"your-key-here\"' >> ~/.zshrc${RESET}"
    echo ""
    echo -e "  Get your API key at: https://console.anthropic.com/"
else
    success "ANTHROPIC_API_KEY is set (${#ANTHROPIC_API_KEY} chars)"
fi

# ── Step 5: Run unit tests ────────────────────────────────────────────────────
header "Running unit tests (no API calls)"

cd "$PROJECT_ROOT"
if python3 -m pytest tests/ -m "not integration" -q 2>&1; then
    success "All unit tests passed!"
else
    error "Some tests failed. Check output above."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}Setup complete!${RESET}"
echo ""
echo -e "Next steps:"
echo -e "  1. ${YELLOW}source .venv/bin/activate${RESET}               (activate env each session)"
echo -e "  2. ${YELLOW}export ANTHROPIC_API_KEY='sk-...'${RESET}       (if not already set)"
echo -e "  3. ${YELLOW}bash scripts/quickstart.sh${RESET}               (run a quick demo)"
echo -e "  4. ${YELLOW}python3 main.py --help${RESET}                   (see all options)"
