#!/usr/bin/env bash
# =============================================================
# test.sh — 运行全套测试套件
#
# 用法:
#   bash scripts/test.sh              # 运行所有测试
#   bash scripts/test.sh --fast       # 跳过 LLM 真实调用（更快）
#   bash scripts/test.sh --stage 1    # 只跑某阶段测试（1~5）
#   bash scripts/test.sh --coverage   # 含覆盖率报告
# =============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ── 阶段映射（兼容 bash 3）───────────────────────────────────
stage_file() {
    case "$1" in
        1) echo "tests/test_agents.py" ;;
        2) echo "tests/test_simulation.py" ;;
        3) echo "tests/test_statistics.py" ;;
        4) echo "tests/test_llm_analyst.py" ;;
        5) echo "tests/test_visualizer.py" ;;
        *) echo "" ;;
    esac
}
stage_name() {
    case "$1" in
        1) echo "核心 Agent 类" ;;
        2) echo "仿真核心循环" ;;
        3) echo "统计分析模块" ;;
        4) echo "LLM 分析层" ;;
        5) echo "可视化 + 主入口" ;;
        *) echo "未知" ;;
    esac
}

# ── 解析参数 ─────────────────────────────────────────────────
FAST=false
STAGE=""
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fast)     FAST=true; shift ;;
        --stage)    STAGE="$2"; shift 2 ;;
        --coverage) COVERAGE=true; shift ;;
        *)          shift ;;
    esac
done

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   小镇经济体 — 测试套件                   ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 确定测试目标 ─────────────────────────────────────────────
if [[ -n "$STAGE" ]]; then
    TEST_FILE="$(stage_file "$STAGE")"
    [[ -z "$TEST_FILE" ]] && error "无效阶段: $STAGE，可选: 1 2 3 4 5"
    TEST_TARGETS="$TEST_FILE"
    info "只运行阶段 $STAGE：$(stage_name "$STAGE")"
else
    TEST_TARGETS="tests/"
    info "运行全部测试"
fi

# ── 处理 LLM 真实调用 ────────────────────────────────────────
DESELECT_OPTS=""
if $FAST; then
    warn "--fast 模式：跳过 LLM 真实调用测试"
    DESELECT_OPTS="--deselect=tests/test_llm_analyst.py::TestOllamaConnection --deselect=tests/test_llm_analyst.py::TestLLMAnalystRealCall"
else
    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        warn "ollama 未运行，LLM 真实调用测试将失败"
        warn "建议: 先运行 bash scripts/setup.sh，或使用 --fast 跳过"
        echo ""
        printf "  继续？(y/N) "; read -r REPLY; echo ""
        [[ "$REPLY" =~ ^[Yy]$ ]] || exit 0
    fi
fi

# ── 覆盖率选项 ───────────────────────────────────────────────
COV_OPTS=""
if $COVERAGE; then
    python3 -m pip install --quiet pytest-cov 2>/dev/null || true
    COV_OPTS="--cov=. --cov-report=term-missing --cov-omit=tests/*,scripts/*"
fi

# ── 运行测试 ─────────────────────────────────────────────────
echo ""
START_TIME=$(date +%s)

set +e
# shellcheck disable=SC2086
python3 -m pytest -v $DESELECT_OPTS $COV_OPTS $TEST_TARGETS
EXIT_CODE=$?
set -e

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    success "所有测试通过！耗时 ${ELAPSED}s"
    echo ""
    echo "  阶段覆盖:"
    for s in 1 2 3 4 5; do
        echo -e "    阶段$s $(stage_name "$s"): ${GREEN}✓${NC}"
    done
else
    error "测试失败！退出码: $EXIT_CODE"
fi
echo ""
