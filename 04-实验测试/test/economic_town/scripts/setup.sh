#!/usr/bin/env bash
# =============================================================
# setup.sh — 一键初始化小镇经济体仿真环境
# 用法: bash scripts/setup.sh
# =============================================================
set -euo pipefail

# ── 颜色输出 ─────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── 项目根目录 ───────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   封闭小镇经济体 Multi-Agent 仿真         ║"
echo "  ║   Environment Setup                      ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ─────────────────────────────────────────────────────────────
# Step 1: 检查 Python
# ─────────────────────────────────────────────────────────────
info "检查 Python 版本..."
if ! command -v python3 &>/dev/null; then
    error "未找到 python3，请先安装 Python 3.8+"
fi
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ]]; then
    error "需要 Python 3.8+，当前版本: $PY_VERSION"
fi
success "Python $PY_VERSION"

# ─────────────────────────────────────────────────────────────
# Step 2: 安装 Python 依赖
# ─────────────────────────────────────────────────────────────
info "安装 Python 依赖 (matplotlib, pytest)..."
python3 -m pip install --quiet matplotlib pytest 2>&1 | grep -v "^$" | grep -v "already satisfied" || true

# 验证
python3 -c "import matplotlib, pytest" 2>/dev/null \
    && success "matplotlib + pytest 已就绪" \
    || error "依赖安装失败，请手动运行: pip3 install matplotlib pytest"

# ─────────────────────────────────────────────────────────────
# Step 3: 检查 / 安装 ollama
# ─────────────────────────────────────────────────────────────
info "检查 ollama..."
if ! command -v ollama &>/dev/null; then
    warn "ollama 未安装，尝试通过 brew 安装..."
    if ! command -v brew &>/dev/null; then
        error "需要 Homebrew 来安装 ollama。请先安装 brew: https://brew.sh"
    fi
    brew install ollama
    success "ollama 安装完成"
else
    success "ollama $(ollama --version 2>/dev/null | head -1)"
fi

# ─────────────────────────────────────────────────────────────
# Step 4: 启动 ollama 服务
# ─────────────────────────────────────────────────────────────
info "检查 ollama 服务状态..."
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    success "ollama 服务已在运行"
else
    info "启动 ollama 服务..."
    if command -v brew &>/dev/null; then
        brew services start ollama 2>/dev/null || true
    else
        # 后台启动
        nohup ollama serve >/tmp/ollama.log 2>&1 &
    fi
    # 等待服务就绪（最多 15 秒）
    for i in $(seq 1 15); do
        if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
            success "ollama 服务已启动"
            break
        fi
        sleep 1
        if [[ $i -eq 15 ]]; then
            error "ollama 服务启动超时，请手动运行: ollama serve"
        fi
    done
fi

# ─────────────────────────────────────────────────────────────
# Step 5: 拉取 LLM 模型
# ─────────────────────────────────────────────────────────────
MODEL="qwen2.5:0.5b"
info "检查模型 $MODEL..."
if ollama list 2>/dev/null | grep -q "qwen2.5"; then
    success "模型 $MODEL 已存在"
else
    info "拉取模型 $MODEL（约 400MB，请等待）..."
    ollama pull "$MODEL"
    success "模型 $MODEL 拉取完成"
fi

# ─────────────────────────────────────────────────────────────
# Step 6: 创建输出目录
# ─────────────────────────────────────────────────────────────
mkdir -p "$PROJECT_ROOT/data/charts"
success "输出目录 data/charts 已就绪"

# ─────────────────────────────────────────────────────────────
# Step 7: 快速验证
# ─────────────────────────────────────────────────────────────
info "快速验证（运行单步仿真）..."
python3 -c "
import sys; sys.path.insert(0, '.')
from core.simulation import TownEconomy
e = TownEconomy(seed=42)
snap = e.step()
assert snap['month'] == 1
print('  仿真验证通过')
"
success "环境验证通过"

echo ""
echo -e "${BOLD}${GREEN}  ✓ 环境初始化完成！${NC}"
echo ""
echo "  下一步："
echo -e "    运行仿真:    ${BOLD}bash scripts/run.sh${NC}"
echo -e "    运行测试:    ${BOLD}bash scripts/test.sh${NC}"
echo -e "    查看文档:    ${BOLD}docs/README.md${NC}"
echo ""
