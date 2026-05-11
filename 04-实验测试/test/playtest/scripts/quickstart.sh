#!/usr/bin/env bash
# =============================================================================
# quickstart.sh — Interactive demo for new learners
# Runs a 3-word, 2-trial experiment and prints a full report.
# =============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

header() { echo -e "\n${BOLD}${CYAN}━━━ $* ━━━${RESET}"; }
info()   { echo -e "${CYAN}▶${RESET} $*"; }
ok()     { echo -e "${GREEN}✔${RESET} $*"; }
warn()   { echo -e "${YELLOW}⚠${RESET}  $*"; }
die()    { echo -e "${RED}✘ $*${RESET}"; exit 1; }

# ── Preflight checks ──────────────────────────────────────────────────────────
header "Preflight"

# Virtual env
if [[ -d ".venv" && -z "${VIRTUAL_ENV:-}" ]]; then
    source .venv/bin/activate
    ok "Activated .venv"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
    ok "Virtual env already active: $VIRTUAL_ENV"
else
    warn "No .venv found — using system Python. Run setup.sh first if needed."
fi

# API key
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    die "ANTHROPIC_API_KEY is not set. Export it before running:\n  export ANTHROPIC_API_KEY='sk-...'"
fi
ok "API key detected"

# ── What we're about to do ────────────────────────────────────────────────────
header "Quick Demo Plan"
echo ""
echo -e "  We'll test ${BOLD}3 words${RESET} × ${BOLD}2 trials${RESET} using ${BOLD}Zero-Shot${RESET} strategy."
echo -e "  Words chosen to span easy → hard:"
echo ""
echo -e "    ${GREEN}CRANE${RESET}  — common letters, human avg ≈ 3.8 guesses  (easy)"
echo -e "    ${YELLOW}STARE${RESET}  — moderate difficulty, human avg ≈ 3.7 guesses"
echo -e "    ${RED}JAZZY${RESET}  — rare letters, human avg ≈ 5.4 guesses   (hard)"
echo ""
echo -e "  Expected: LLM ranks them in same relative order as humans."
echo -e "  ${CYAN}This takes ~2-5 minutes (real API calls).${RESET}"
echo ""
read -rp "Press Enter to start, or Ctrl+C to cancel..."

# ── Run experiment ────────────────────────────────────────────────────────────
header "Running Experiment"

REPORT_FILE="quickstart_report.md"

python3 main.py \
    --words CRANE STARE JAZZY \
    --trials 2 \
    --strategy zero_shot \
    --model claude-haiku-4-5-20251001 \
    --output "$REPORT_FILE"

# ── Show report ───────────────────────────────────────────────────────────────
header "Generated Report"
echo ""
cat "$REPORT_FILE"
echo ""
ok "Report saved to: $REPORT_FILE"

# ── What to try next ──────────────────────────────────────────────────────────
header "What to Try Next"
echo ""
echo -e "  ${BOLD}More words, more trials:${RESET}"
echo -e "  ${YELLOW}python3 main.py --words CRANE SLATE ARISE JAZZY QUEEN --trials 5${RESET}"
echo ""
echo -e "  ${BOLD}Try CoT strategy (better correlation, slower):${RESET}"
echo -e "  ${YELLOW}python3 main.py --quick-test --strategy cot${RESET}"
echo ""
echo -e "  ${BOLD}Run only unit tests (no API needed):${RESET}"
echo -e "  ${YELLOW}python3 -m pytest tests/ -m 'not integration' -v${RESET}"
echo ""
echo -e "  ${BOLD}Run full integration test (11+ min):${RESET}"
echo -e "  ${YELLOW}python3 -m pytest tests/test_analysis.py -k integration -v -s${RESET}"
echo ""
echo -e "  ${BOLD}Explore the code:${RESET}"
echo -e "  ${CYAN}wordle/engine.py${RESET}      ← game logic"
echo -e "  ${CYAN}agent/prompts.py${RESET}      ← LLM prompt templates"
echo -e "  ${CYAN}agent/llm_client.py${RESET}   ← Claude API integration"
echo -e "  ${CYAN}analysis/stats.py${RESET}     ← Pearson correlation"
