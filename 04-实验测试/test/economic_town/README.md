# 封闭小镇经济体 — Multi-Agent 仿真

> 一个用 Python 构建的多智能体经济仿真系统，模拟银行、工厂、工人和零售商在封闭小镇中的完整经济循环，并结合本地 LLM（qwen2.5）进行经济分析。

---

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd economic_town

# 2. 一键初始化（安装依赖 + ollama + 拉取模型）
bash scripts/setup.sh

# 3. 运行仿真
bash scripts/run.sh

# 4. 运行测试
bash scripts/test.sh
```

**最低要求：** Python 3.8+，macOS（有 brew）

---

## 运行选项

```bash
# 默认：跑 60 个月，含 LLM 年度分析报告
bash scripts/run.sh

# 自定义月数
bash scripts/run.sh --months 24

# 逐月打印状态（调试用）
bash scripts/run.sh --months 12 --verbose

# 跳过 LLM，纯规则引擎（速度极快）
bash scripts/run.sh --no-llm

# 组合使用
bash scripts/run.sh --months 24 --verbose --no-llm
```

```bash
# 测试选项
bash scripts/test.sh              # 全套测试（需要 ollama 运行）
bash scripts/test.sh --fast       # 快速（跳过 LLM 真实调用）
bash scripts/test.sh --stage 1    # 只测试某阶段（1~5）
bash scripts/test.sh --coverage   # 含覆盖率报告
```

---

## 经济体设计

小镇包含 **5 类主体**，通过资金和商品流动相互连接：

```
外部市场（需求曲线）
     │ 销售收入
     ▼
工厂主 × 3  ──贷款──▶  银行
     │ 工资              ▲ 存款
     ▼                   │
工人 × 30  ──本地消费──▶  零售商
     │                   │ 利润存入银行
     ▼
 外部消费品（流出镇外）
```

| 主体 | 数量 | 核心行为 |
|------|------|---------|
| 银行 | 1 | 调整存贷款利率，管理信贷风险 |
| 工厂主 | 3 | 借贷→雇工→生产→销售→还贷 |
| 工人 | 30 | 求职→收入→储蓄/消费 |
| 零售商 | 1 | 接收本地消费，转化为进口成本+利润 |
| 外部市场 | 虚拟 | 价格弹性需求曲线 + 随机景气冲击 |

---

## 输出文件

仿真结束后自动生成：

| 文件 | 说明 |
|------|------|
| `data/simulation_results.csv` | 每月所有经济指标的历史数据 |
| `data/charts/overview.png` | 就业率、工资、存款、基尼系数 4 宫格图 |
| `data/charts/financial.png` | 利率走势 + 银行坏账率 |
| `data/charts/production.png` | 产量、收入、净外部资金流入 |

LLM 分析报告**直接打印到终端**（每 12 个月一次，异常时触发）。

---

## 项目结构

```
economic_town/
├── README.md               ← 你在这里
├── main.py                 ← 主入口
├── config/
│   └── params.py           ← 所有参数（修改这里调节经济）
├── agents/                 ← 5 类经济主体
│   ├── bank.py
│   ├── factory.py
│   ├── worker.py
│   ├── retailer.py
│   └── external_market.py
├── core/
│   └── simulation.py       ← 月度仿真主循环
├── analysis/
│   ├── statistics.py       ← 经济指标计算
│   ├── llm_analyst.py      ← LLM 分析层（ollama）
│   └── visualizer.py       ← matplotlib 图表
├── scripts/
│   ├── setup.sh            ← 一键初始化
│   ├── run.sh              ← 运行仿真
│   └── test.sh             ← 运行测试
├── tests/                  ← 81 个单元/集成测试
└── docs/
    ├── architecture.md     ← 系统架构详解
    └── learning_guide.md   ← 新手学习路径
```

---

## 调参指南

所有经济参数集中在 `config/params.py`，修改后重新运行即可：

```python
# 扩大经济规模
NUM_WORKERS = 50          # 增加工人数

# 模拟高利率环境（紧缩政策）
BANK_LOAN_RATE = 0.08     # 月贷款利率从 5% → 8%

# 模拟外部需求冲击
EXTERNAL_DEMAND_VOLATILITY = 0.3   # 加大需求波动

# 模拟保守储蓄社会
WORKER_SAVINGS_RATE_RANGE = (0.3, 0.6)  # 储蓄率提高
```

---

## 新手学习路径

1. 先读 `docs/learning_guide.md` — 了解经济学概念和代码对应关系
2. 读 `docs/architecture.md` — 理解整体架构和数据流
3. 跑一次仿真，观察输出
4. 修改 `config/params.py` 中的参数，对比结果
5. 阅读 `agents/` 下各主体的代码

---

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 核心语言 |
| 纯标准库 | Agent 逻辑（无框架依赖）|
| matplotlib | 图表生成 |
| pytest | 测试框架 |
| ollama | 本地 LLM 服务 |
| qwen2.5:0.5b | 经济分析 LLM（397MB）|
