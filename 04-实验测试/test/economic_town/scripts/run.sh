#!/usr/bin/env bash
# =============================================================
# run.sh — 启动小镇经济体仿真
#
# 用法:
#   bash scripts/run.sh                  # 默认 60 个月，含 LLM 分析
#   bash scripts/run.sh --months 24      # 自定义月数
#   bash scripts/run.sh --no-llm         # 跳过 LLM（纯规则，速度快）
#   bash scripts/run.sh --verbose        # 每月打印状态
#   bash scripts/run.sh --months 12 --verbose --no-llm
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

# ── 解析参数（直接透传给 main.py）────────────────────────────
PASS_ARGS=("$@")

# ── 检查 ollama 是否在运行 ───────────────────────────────────
ensure_ollama() {
    # 如果传了 --no-llm，跳过检查
    for arg in "${PASS_ARGS[@]+"${PASS_ARGS[@]}"}"; do
        [[ "$arg" == "--no-llm" ]] && return 0
    done

    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        warn "ollama 服务未运行，正在启动..."
        if command -v brew &>/dev/null; then
            brew services start ollama 2>/dev/null || true
        else
            nohup ollama serve >/tmp/ollama.log 2>&1 &
        fi
        for i in $(seq 1 15); do
            curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 && break
            sleep 1
            [[ $i -eq 15 ]] && error "ollama 启动超时，请手动运行: ollama serve，或使用 --no-llm 跳过"
        done
        success "ollama 已启动"
    else
        info "ollama 服务运行中"
    fi
}

ensure_ollama

# ── 记录开始时间 ─────────────────────────────────────────────
START_TIME=$(date +%s)

echo ""
info "启动仿真..."
echo ""

python3 main.py "${PASS_ARGS[@]+"${PASS_ARGS[@]}"}"

# ── 计算耗时 ─────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINS=$((ELAPSED / 60))
SECS=$((ELAPSED % 60))

echo ""
success "仿真完成，耗时 ${MINS}m${SECS}s"
echo ""
echo "  输出文件:"
[[ -f "data/simulation_results.csv" ]] && echo "    data/simulation_results.csv   （历史数据）"
[[ -f "data/charts/overview.png" ]]   && echo "    data/charts/overview.png       （经济总览图）"
[[ -f "data/charts/financial.png" ]]  && echo "    data/charts/financial.png      （金融指标图）"
[[ -f "data/charts/production.png" ]] && echo "    data/charts/production.png     （生产贸易图）"
echo ""

# ── macOS：自动打开图表目录 ──────────────────────────────────
if [[ "$(uname)" == "Darwin" ]] && [[ -d "data/charts" ]]; then
    read -p "  是否打开图表目录？(y/N) " -n 1 -r
    echo ""
    [[ "$REPLY" =~ ^[Yy]$ ]] && open data/charts
fi
