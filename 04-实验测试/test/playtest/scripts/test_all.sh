#!/usr/bin/env bash
# =============================================================================
# test_all.sh — Run all tests with a clear phase-by-phase report
# =============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
BOLD='\033[1m'; RESET='\033[0m'; YELLOW='\033[1;33m'

INTEGRATION=${1:-""}  # Pass --integration to include API test

passed=0; failed=0

run_phase() {
    local label="$1"; shift
    echo -e "\n${BOLD}${CYAN}Phase: $label${RESET}"
    if python3 -m pytest "$@" -q --tb=short 2>&1; then
        echo -e "${GREEN}✔ $label passed${RESET}"
        passed=$((passed + 1))
    else
        echo -e "${RED}✘ $label FAILED${RESET}"
        failed=$((failed + 1))
    fi
}

echo -e "${BOLD}LLM Game Difficulty Framework — Test Suite${RESET}"
echo "──────────────────────────────────────────"

run_phase "Phase 1: Wordle Engine"     tests/test_engine.py
run_phase "Phase 2: LLM Agent (Mock)" tests/test_agent.py
run_phase "Phase 3: Analysis (Mock)"  tests/test_analysis.py -m "not integration"

if [[ "$INTEGRATION" == "--integration" ]]; then
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        echo -e "\n${YELLOW}⚠ Skipping integration test: ANTHROPIC_API_KEY not set${RESET}"
    else
        echo -e "\n${BOLD}${CYAN}Integration Test (real API — ~11 min)${RESET}"
        if python3 -m pytest tests/test_analysis.py -k integration -v -s 2>&1; then
            echo -e "${GREEN}✔ Integration test passed${RESET}"
            passed=$((passed + 1))
        else
            echo -e "${RED}✘ Integration test FAILED${RESET}"
            failed=$((failed + 1))
        fi
    fi
fi

echo ""
echo "──────────────────────────────────────────"
echo -e "${BOLD}Results: ${GREEN}$passed passed${RESET}, ${RED}$failed failed${RESET}"

[[ "$failed" -eq 0 ]] && echo -e "${GREEN}${BOLD}All tests passed!${RESET}" || exit 1
