# TITAN-Snake：LLM 驱动的贪吃蛇自动测试框架

> 基于 TITAN 论文（[arXiv:2509.22170](https://arxiv.org/abs/2509.22170)）实现
> 用大语言模型（Claude）自动测试贪吃蛇游戏，自动发现并报告 Bug

---

## 目录

- [项目简介](#项目简介)
- [30 秒快速上手](#30-秒快速上手)
- [工作原理](#工作原理)
- [项目结构](#项目结构)
- [各模块详解](#各模块详解)
  - [Layer 0：游戏环境](#layer-0游戏环境)
  - [Layer 1：RAG 知识库](#layer-1rag-知识库)
  - [Layer 2：LLM 客户端](#layer-2llm-客户端)
  - [Layer 3：感知抽象](#layer-3感知抽象)
  - [Layer 4：动作优化](#layer-4动作优化)
  - [Layer 5：反射推理](#layer-5反射推理)
  - [Layer 6：问题诊断](#layer-6问题诊断)
  - [Layer 7：TITAN 主循环](#layer-7titan-主循环)
- [Bug 注入场景](#bug-注入场景)
- [运行测试](#运行测试)
- [输出示例](#输出示例)
- [如何扩展](#如何扩展)
- [常见问题](#常见问题)

---

## 项目简介

这个框架让 AI（Claude 大语言模型）像一个真正的测试工程师一样，自主玩贪吃蛇游戏、发现游戏中的 Bug。

**无需人工介入**，框架会自动：

1. 观察游戏状态 → 2. 决定下一步动作 → 3. 检测异常 → 4. 生成 Bug 报告

```
测试工程师 → [观察] → [分析] → [决策] → [检测] → 生成报告
    ↕
  TITAN  → [感知] → [推理] → [动作] → [诊断] → 结构化报告
```

### 技术亮点

| 特性 | 说明 |
|------|------|
| **零训练** | 不微调模型，纯靠 LLM 的 zero-shot 推理 + RAG 知识注入 |
| **无真实 API 依赖** | Mock 模式下完整运行，开发测试无需消耗 API 配额 |
| **纯 Python** | RAG 用标准库 TF-IDF 实现，仅依赖 `anthropic` 和 `pytest` |
| **190 个测试** | 92% 代码覆盖率，每层独立可测 |
| **可扩展** | 可轻松接入其他游戏或添加新 Bug 类型 |

---

## 30 秒快速上手

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. Mock 模式运行（无需 API Key）
cd /Users/xd/Desktop/codes/code_auto_test
TITAN_MOCK_LLM=1 python -m titan.agent --mock-llm --verbose

# 3. 注入特定 Bug 来测试检测效果
TITAN_MOCK_LLM=1 python -m titan.agent --bug score_no_increment --mock-llm --verbose
```

**真实 LLM 运行**（需要 Anthropic API Key）：
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python -m titan.agent --verbose --bug wall_pass_through
```

### CLI 参数说明

```
python -m titan.agent [选项]

--bug         注入的 Bug 类型（默认: none）
              可选: none, score_no_increment, wall_pass_through,
                    self_collision_ignored, food_in_body, slow_tick

--difficulty  游戏难度（默认: EASY）
              可选: EASY（20×20）, NORMAL（25×25）, HARD（30×30）

--max-ticks   最大游戏步数（默认: 300）
--verbose     打印逐步日志
--mock-llm    使用 Mock LLM（不调用真实 API）
```

---

## 工作原理

### TITAN 测试循环（Algorithm 1）

```
┌─────────────────────────────────────────────────────────┐
│                      TITAN 主循环                        │
│                                                          │
│   ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│   │  游戏状态 │───▶│  感知抽象 │───▶│  动作优化        │  │
│   │ GameState│    │(Module 1)│    │ (Module 2)       │  │
│   └──────────┘    └──────────┘    └────────┬─────────┘  │
│        ▲                                   │             │
│        │                                   ▼             │
│   ┌────┴─────┐    ┌──────────┐    ┌──────────────────┐  │
│   │  执行动作 │◀───│  LLM 决策 │◀───│  候选动作集      │  │
│   │  env.tick│    │  Claude  │    │ [UP, RIGHT, ...]  │  │
│   └──────────┘    └──────────┘    └──────────────────┘  │
│        │                                                  │
│        ▼                                                  │
│   ┌──────────┐    ┌──────────┐                           │
│   │ 反射推理 │    │ 问题诊断  │  ◀── 三层 Oracle:         │
│   │(Module 3)│    │(Module 4)│      Crash / Logic /      │
│   │ 进度监控  │    │ 自动报告  │      Performance          │
│   └──────────┘    └──────────┘                           │
└─────────────────────────────────────────────────────────┘
```

### 数据流图

```
GameState（原始）
    │
    ▼ perception.abstract()
AbstractState（符号化）
    {
      "direction": "RIGHT",
      "danger_ahead": False,
      "food_direction": "UP-RIGHT",
      "snake_length": "short",
      "open_space_ratio": 0.82,
      ...
    }
    │
    ▼ action_opt.recommend()
ActionBundle
    {
      "recommended": ["UP", "RIGHT"],   # 优先级排序
      "safe_actions": ["UP", "RIGHT"],
      "reasoning": "Food direction UP prioritized"
    }
    │
    ▼ llm.decide_action()
action = "UP"
    │
    ▼ env.tick()
new_GameState
    │
    ├──▶ reflection_engine.record_step()
    │       └──▶ (如卡住) llm.reflect() → ReflectionResult
    │
    └──▶ diagnosis_engine.check()
            ├── CrashMonitor.check()
            ├── TaskStatusMonitor.check()
            └── ExecutionTimeMonitor.record_tick_time()
                    └──▶ DiagnosisReport（如发现 Bug）
```

---

## 项目结构

```
code_auto_test/
├── README.md                     ← 本文档
├── CLAUDE.md                     ← AI 助手上下文文档
├── requirements.txt              ← Python 依赖（仅3个包）
│
├── titan/                        ← 核心框架
│   ├── __init__.py
│   │
│   ├── game/                     ← Layer 0: 游戏环境
│   │   ├── snake_env.py          ← Python 贪吃蛇模拟器（镜像 TypeScript 逻辑）
│   │   └── bug_scenarios.py      ← 5种 Bug 注入机制
│   │
│   ├── rag/                      ← Layer 1: 知识检索
│   │   └── knowledge_base.py     ← TF-IDF RAG（纯 Python）
│   │
│   ├── llm_client.py             ← Layer 2: Claude API 封装
│   │
│   ├── modules/                  ← TITAN 四大核心模块
│   │   ├── perception.py         ← Layer 3: 感知抽象（GameState → AbstractState）
│   │   ├── action_opt.py         ← Layer 4: 动作优化（过滤 + 排序 + LLM 辅助）
│   │   ├── reflection.py         ← Layer 5: 反射推理（卡死检测 + 策略调整）
│   │   └── diagnosis.py          ← Layer 6: 问题诊断（三层 Oracle）
│   │
│   └── agent.py                  ← Layer 7: TITAN 主循环
│
└── tests/                        ← 190 个测试（92% 覆盖率）
    ├── test_snake_env.py          ← Layer 0 测试（29个）
    ├── test_rag.py                ← Layer 1 测试（27个）
    ├── test_perception.py         ← Layer 3 测试（44个）
    ├── test_action_opt.py         ← Layer 4 测试（22个）
    ├── test_reflection.py         ← Layer 5 测试（25个）
    ├── test_diagnosis.py          ← Layer 6 测试（24个）
    └── test_agent.py              ← Layer 7 集成测试（19个）
```

---

## 各模块详解

### Layer 0：游戏环境

**文件**: `titan/game/snake_env.py`

Python 实现的贪吃蛇模拟器，完全镜像 TypeScript `GameEngine.ts` 的逻辑。采用**纯函数 + 不可变状态**设计，每个 `tick()` 调用返回新的 `GameState`，不修改原状态。

#### 核心数据结构

```python
from titan.game.snake_env import Point, GameState, Difficulty, create_initial_state, tick

# Point: 网格坐标（不可变）
head = Point(x=10, y=10)
next_pos = Point(head.x + 1, head.y)  # 向右移动一格

# GameState: 完整游戏状态
state = create_initial_state("EASY")
print(state.snake)    # [Point(10,10), Point(9,10), Point(8,10)]  头在前
print(state.food)     # Point(随机)
print(state.phase)    # "IDLE"
print(state.score)    # 0

# 启动游戏并执行一步
from titan.game.snake_env import set_phase, set_next_direction
state = set_phase(state, "RUNNING")
state = set_next_direction(state, "UP")  # 设置下一步方向
state = tick(state)                       # 推进一帧
print(state.tick_count)  # 1
```

#### 难度配置

| 难度 | 网格大小 | 初始蛇长 | Tick间隔 |
|------|---------|---------|---------|
| EASY | 20×20 | 3节 | 200ms |
| NORMAL | 25×25 | 4节 | 130ms |
| HARD | 30×30 | 5节 | 80ms |

#### 游戏规则（镜像 TypeScript 原版）

- 蛇头碰墙 → `phase = "GAME_OVER"`
- 蛇头碰自身（尾巴除外）→ `phase = "GAME_OVER"`
- 蛇头碰食物 → `score += 10`，蛇长 +1，食物重新生成
- 蛇填满整个网格 → `phase = "WIN"`
- 禁止 180° 反转（`set_next_direction` 会忽略反向输入）

---

### Layer 1：RAG 知识库

**文件**: `titan/rag/knowledge_base.py`

基于 TF-IDF 的知识检索系统，将游戏规则文档转化为 LLM 的上下文知识。

**设计亮点**：
- **零 ML 依赖**：只用 `collections.Counter` 和 `math.log` 实现 TF-IDF
- **双语支持**：同时支持中文字符（`\u4e00-\u9fff`）和英文单词分词
- **专家规则**：硬编码的贪吃蛇规则，作为检索的基础知识

```python
from titan.rag.knowledge_base import KnowledgeBase

kb = KnowledgeBase()

# 检索相关知识片段
rules = kb.retrieve("danger ahead collision wall", top_k=3)
for rule in rules:
    print(rule)
# → "当前方向前方有墙壁或蛇身，立即转向"
# → "碰撞墙壁或自身即游戏结束"
# → "蛇填满整个网格即为胜利"

# 获取特定专家规则
score_rule = kb.get_expert_rule("score_increase")
# → "吃到食物分数应增加10分，蛇身长度+1"
```

**知识来源**：
1. 硬编码专家规则（贪吃蛇游戏规律）
2. 贪吃蛇项目 README.md（游戏规则文档）
3. 贪吃蛇项目 CLAUDE.md（架构与算法文档）

---

### Layer 2：LLM 客户端

**文件**: `titan/llm_client.py`

封装 Claude API，提供三种核心能力：

| 方法 | 用途 |
|------|------|
| `chat(system, messages)` | 通用对话接口 |
| `decide_action(abstract_state, actions)` | 从候选动作中选最优 |
| `reflect(abstract_state, history, stall_count)` | 分析卡死原因，建议新策略 |
| `generate_bug_report(bug_type, state, evidence)` | 生成结构化 Bug 报告 |

#### Mock 模式（测试用）

```python
from titan.llm_client import LLMClient

# 方式1：环境变量
# TITAN_MOCK_LLM=1 python your_script.py

# 方式2：代码设置
llm = LLMClient(mock=True)
llm.set_default_mock_response("RIGHT")    # 所有调用返回 "RIGHT"
llm.set_mock_responses(["UP", "LEFT"])    # 按顺序返回，最后一个无限重复

# 方式3：自动检测
import os
os.environ["TITAN_MOCK_LLM"] = "1"
llm = LLMClient()  # 自动使用 Mock 模式
```

#### 真实模式

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

llm = LLMClient(model="claude-sonnet-4-6")
response = llm.chat(
    system="你是贪吃蛇测试专家",
    messages=[{"role": "user", "content": "蛇头在左边界，应该往哪走？"}]
)
```

---

### Layer 3：感知抽象

**文件**: `titan/modules/perception.py`

将原始 `GameState`（坐标、像素级信息）压缩为 LLM 可以理解的**符号化摘要**。

```
GameState（原始）                    AbstractState（符号化）
───────────────────────────────     ───────────────────────────────
snake: [Point(10,10), ...]          direction: "RIGHT"
food: Point(15, 8)               →  danger_ahead: False
direction: "RIGHT"                  danger_left: True
score: 30                           food_direction: "UP-RIGHT"
tick_count: 47                      food_distance: "medium"
config.grid_size: 20                snake_length: "short"
                                    open_space_ratio: 0.72
                                    head_position: "center"
                                    relevant_rules: ["当前..."]
```

#### 关键技术

**危险检测**（排除尾巴位置，因为尾巴会移开）：
```python
from titan.modules.perception import check_danger

# 检查某方向是否会立即碰撞（墙壁或蛇身）
is_dangerous = check_danger(state, "LEFT")
```

**BFS 开放空间估算**：
```python
from titan.modules.perception import estimate_open_space

# 从蛇头出发，用 BFS 估算可达格子比例
ratio = estimate_open_space(state)  # 0.0 ~ 1.0
# 比例越高，蛇越不容易被困住
```

**完整抽象**：
```python
from titan.modules.perception import abstract
from titan.rag.knowledge_base import KnowledgeBase

kb = KnowledgeBase()
ab_state = abstract(state, knowledge_base=kb)
print(ab_state)
# {
#   "phase": "RUNNING",
#   "direction": "RIGHT",
#   "score": 30,
#   "snake_length": "short",        # short / medium / long
#   "food_distance": "medium",      # close / medium / far
#   "food_direction": "UP-RIGHT",   # 8个方向 + SAME
#   "danger_ahead": False,
#   "danger_left": True,
#   "danger_right": False,
#   "danger_back": True,            # 始终为True（不能180°反转）
#   "head_position": "center",      # 9个区域
#   "open_space_ratio": 0.72,
#   "relevant_rules": ["..."],      # RAG 检索结果
# }
```

---

### Layer 4：动作优化

**文件**: `titan/modules/action_opt.py`

从 4 个方向中过滤和排序，生成推荐动作列表。

#### 五步过滤流程

```
4个方向 [UP, DOWN, LEFT, RIGHT]
    │
    ▼ 过滤180°反转
    │   （当前向RIGHT → 过滤掉LEFT）
    │
    ▼ 过滤立即致死动作
    │   （通过 check_danger 检测墙壁/自身碰撞）
    │
    ▼ BFS 洪水填充排序
    │   （优先选择能到达更多格子的方向）
    │
    ▼ 食物方向优先
    │   （如果朝食物方向的动作是安全的，移到最前）
    │
    ▼ 可选：LLM 最终排序
        （如候选 > 2 个，调用 Claude 做最终决策）
```

```python
from titan.modules.action_opt import recommend, ActionBundle
from titan.llm_client import LLMClient

llm = LLMClient(mock=True)
bundle: ActionBundle = recommend(ab_state, state, llm_client=llm)

print(bundle.recommended)   # ["UP", "RIGHT"]  优先级排序
print(bundle.safe_actions)  # ["UP", "RIGHT"]  所有安全动作
print(bundle.reasoning)
# "Safe actions: ['UP', 'RIGHT']; Food direction: UP prioritized;
#  Space ranking: [('UP', 85), ('RIGHT', 72)]"
```

---

### Layer 5：反射推理

**文件**: `titan/modules/reflection.py`

检测测试停滞，触发反思，维护跨轮次的覆盖记忆。

#### 三个核心组件

**1. ProgressMonitor（进度监控）**

连续 N 步无进展（分数不变 + 抽象状态不变）则判定为"停滞"：

```python
from titan.modules.reflection import ProgressMonitor

monitor = ProgressMonitor(stall_threshold=20)
for action in actions:
    triggered = monitor.update(abstract_state, action, score)
    if triggered:
        print(f"停滞 {monitor.stall_count} 步，触发反思！")
```

**2. CoverageMemory（覆盖记忆）**

记录每个抽象状态下执行过哪些动作，结果如何。**跨轮次持久化到 JSON**：

```python
from titan.modules.reflection import CoverageMemory

memory = CoverageMemory()
memory.record(abstract_state, "UP", "normal")    # 记录状态-动作-结果
memory.record(abstract_state, "RIGHT", "food")   # 结果类型：normal/food/game_over

# 查询是否已探索过
explored = memory.is_explored(abstract_state, "UP")   # True
unexplored = memory.get_unexplored_actions(abstract_state, ["UP", "RIGHT", "DOWN"])
# → ["RIGHT", "DOWN"]  （已过滤掉 UP）

# 持久化（跨轮次学习）
memory.save("coverage.json")
loaded = CoverageMemory.load("coverage.json")
```

**3. ReflectionEngine（反思引擎）**

```python
from titan.modules.reflection import ReflectionEngine
from titan.llm_client import LLMClient

engine = ReflectionEngine(stall_threshold=20, escalation_limit=3)
llm = LLMClient(mock=True)

# 每步记录
stall_triggered = engine.record_step(abstract_state, "RIGHT", score, tick_num)

if stall_triggered:
    result = engine.reflect(abstract_state, llm)
    print(result.suggested_actions)  # ["UP", "LEFT"]
    print(result.is_bug)             # True/False
    print(result.reason)             # "Score stuck despite food contact"
    print(result.stall_count)        # 25

if engine.should_terminate():
    print("反思次数超限，终止测试")
```

---

### Layer 6：问题诊断

**文件**: `titan/modules/diagnosis.py`

三层 Oracle 系统，每种 Oracle 针对一类 Bug 类型，并通过**连续检测（默认2次）**来抑制误报。

#### Oracle 1：Crash Monitor（崩溃监控）

**检测逻辑**：当游戏结束（GAME_OVER），但感知模块判断前方没有危险时，说明出现了**意外崩溃 Bug**。

```
正常结束: danger_ahead=True  → GAME_OVER  ✓ 正常
意外崩溃: danger_ahead=False → GAME_OVER  ✗ Bug！
```

#### Oracle 2：Task Status Monitor（任务状态监控）

检测两类逻辑 Bug：
1. **Hang Bug**：反思次数超过上限，游戏仍在运行（游戏卡死）
2. **Logic Bug**：食物坐标在蛇身内，但分数没有增加（分数不递增 Bug）

#### Oracle 3：Execution Time Monitor（执行时间监控）

建立前 5 次 tick 的基准时间，后续超过 **3×基准** 则报告性能 Bug：

```
基准: 平均 0.001s/tick
异常: 0.5s/tick → 500×基准 → Performance Bug!
```

#### 使用方式

```python
from titan.modules.diagnosis import DiagnosisEngine, BugCategory, Severity

engine = DiagnosisEngine(llm_client=llm)  # LLM 可选，用于生成根因分析

reports = engine.check(
    state=state,
    abstract_state=ab_state,
    action_history=history,
    tick_elapsed=0.001,        # 本次 tick 耗时
    escalation_exceeded=False, # 是否反思次数超限
)

for report in reports:
    print(f"[{report.severity}] {report.bug_type}: {report.description}")
    print(f"  证据: {report.evidence}")
    print(f"  LLM 分析: {report.llm_analysis}")
    print(f"  时间: {report.timestamp}")
```

**诊断报告结构**：

```python
@dataclass
class DiagnosisReport:
    bug_type: str     # "Crash" / "Logic" / "Performance" / "Hang"
    severity: str     # "Critical" / "High" / "Medium" / "Low"
    description: str  # 人类可读描述
    evidence: dict    # 状态快照 + 动作历史
    llm_analysis: str # LLM 生成的根因分析
    timestamp: str    # ISO 时间戳
```

---

### Layer 7：TITAN 主循环

**文件**: `titan/agent.py`

整合所有模块，实现完整的 TITAN 测试循环。

```python
from titan.agent import TITANAgent
from titan.game.bug_scenarios import BugType

# 创建 Agent
agent = TITANAgent(
    difficulty="EASY",         # 游戏难度
    stall_threshold=20,        # 多少步不进展算停滞
    escalation_limit=3,        # 最多反思几次
    mock_llm=True,             # 使用 Mock LLM（测试用）
    use_rag=True,              # 启用知识库
)

# 运行测试（注入特定 Bug）
report = agent.run(
    bug_type=BugType.SCORE_NO_INCREMENT,  # 分数不递增 Bug
    max_ticks=500,
    verbose=True,
)

# 查看结果
print(report.summary())
print(f"发现 Bug 数量: {report.bug_count}")
print(f"测试覆盖率: {report.coverage_ratio:.1%}")
print(f"终止原因: {report.terminated_by}")
```

**TITANTestReport 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `bug_type_tested` | str | 注入的 Bug 类型名称 |
| `bugs_detected` | list | 检测到的 DiagnosisReport 列表 |
| `total_ticks` | int | 执行的游戏帧数 |
| `final_score` | int | 最终分数 |
| `final_phase` | str | 最终游戏阶段 |
| `coverage_ratio` | float | 抽象状态覆盖率（0~1） |
| `visited_state_count` | int | 访问过的不同抽象状态数 |
| `terminated_by` | str | 终止原因（见下表） |
| `action_history_length` | int | 动作历史长度 |

**终止原因**：

| 值 | 说明 |
|----|------|
| `task_complete` | 游戏胜利（蛇填满网格） |
| `game_over` | 游戏自然结束（碰墙/碰自身） |
| `max_ticks` | 达到最大帧数限制 |
| `escalation_limit` | 反思次数超过上限，强制终止 |

---

## Bug 注入场景

**文件**: `titan/game/bug_scenarios.py`

通过包装游戏环境来注入各种 Bug，不修改游戏核心代码。

| Bug 类型 | 枚举值 | 注入效果 | 期望检测到 |
|---------|--------|---------|-----------|
| 无 Bug | `NONE` | 正常游戏 | 无报告 |
| 分数不递增 | `SCORE_NO_INCREMENT` | 吃食物但 score 不增加 | Logic Bug |
| 穿墙不死 | `WALL_PASS_THROUGH` | 撞墙不触发 GAME_OVER | Crash Bug |
| 自碰无效 | `SELF_COLLISION_IGNORED` | 撞自身不触发 GAME_OVER | Crash Bug |
| 食物在蛇身 | `FOOD_IN_BODY` | 食物生成在蛇身上 | Logic Bug |
| 慢响应 | `SLOW_TICK` | tick() 人为延迟 0.05s | Performance Bug |

```python
from titan.game.bug_scenarios import BugType, BuggySnakeEnv
from titan.game.snake_env import create_initial_state, set_phase, set_next_direction

# 创建有 Bug 的游戏环境
env = BuggySnakeEnv(BugType.SCORE_NO_INCREMENT)

state = set_phase(create_initial_state("EASY"), "RUNNING")
state = set_next_direction(state, "RIGHT")
state = env.tick(state)  # 分数不会增加，即使吃到食物
```

---

## 运行测试

### 全量测试

```bash
cd /Users/xd/Desktop/codes/code_auto_test

# 快速运行（Mock LLM，2~3秒完成）
TITAN_MOCK_LLM=1 pytest tests/ -q

# 带覆盖率报告
TITAN_MOCK_LLM=1 pytest tests/ --cov=titan --cov-report=term-missing

# 详细输出
TITAN_MOCK_LLM=1 pytest tests/ -v
```

### 分层测试（推荐新手按顺序学习）

```bash
# Layer 0: 游戏环境（29个测试）
pytest tests/test_snake_env.py -v

# Layer 1: RAG 知识库（27个测试）
pytest tests/test_rag.py -v

# Layer 3: 感知抽象（44个测试）
pytest tests/test_perception.py -v

# Layer 4: 动作优化（22个测试）
pytest tests/test_action_opt.py -v

# Layer 5: 反射推理（25个测试）
pytest tests/test_reflection.py -v

# Layer 6: 问题诊断（24个测试）
pytest tests/test_diagnosis.py -v

# Layer 7: 集成测试（19个测试）
pytest tests/test_agent.py -v
```

### 当前测试状态

```
190 passed in ~2.5s  |  覆盖率: 92%
```

---

## 输出示例

### 正常运行（无 Bug）

```
TITAN Agent starting | bug=none | difficulty=EASY
  Tick   0 | score=  0 | phase=RUNNING   | action=RIGHT | head=(10,10)
  Tick  20 | score= 10 | phase=RUNNING   | action=UP    | head=(13, 7)
  Tick  40 | score= 20 | phase=RUNNING   | action=RIGHT | head=(16, 4)
TITAN Agent done | ticks=67 | bugs=0

=== TITAN Test Report ===
Bug scenario tested : none
Ticks executed      : 67
Final score         : 20
Final phase         : GAME_OVER
Bugs detected       : 0
Coverage ratio      : 8.33%
States visited      : 12
Terminated by       : game_over
```

### 注入 Bug 后检测到报告

```
TITAN Agent starting | bug=score_no_increment | difficulty=EASY
  Tick   0 | score=  0 | phase=RUNNING   | action=RIGHT | head=(10,10)
  [Reflection] stall=25 is_bug=True
  [BUG DETECTED] Logic: Logic bug detected: Score did not increment after...
TITAN Agent done | ticks=89 | bugs=1

=== TITAN Test Report ===
Bug scenario tested : score_no_increment
Ticks executed      : 89
Final score         : 0
Final phase         : RUNNING
Bugs detected       : 1
Coverage ratio      : 15.28%
States visited      : 22
Terminated by       : escalation_limit

--- Bug #1 ---
  Type     : Logic
  Severity : High
  Description: Logic bug detected: Score did not increment after food was...
```

---

## 如何扩展

### 添加新的 Bug 类型

1. 在 `titan/game/bug_scenarios.py` 中添加枚举值：
```python
class BugType(Enum):
    # ... 现有类型 ...
    MY_NEW_BUG = "my_new_bug"  # 新增
```

2. 在 `BuggySnakeEnv.tick()` 中添加处理逻辑：
```python
def tick(self, state):
    if self.bug_type == BugType.MY_NEW_BUG:
        # 修改游戏逻辑...
        pass
    return clean_tick(state)
```

3. 在 `tests/test_diagnosis.py` 添加对应测试。

---

### 添加新的 Oracle（诊断规则）

在 `titan/modules/diagnosis.py` 中：

```python
class MyCustomOracle:
    def check(self, state, abstract_state, action_history) -> Optional[DiagnosisReport]:
        # 自定义检测逻辑
        if some_condition:
            return DiagnosisReport(
                bug_type="MyBug",
                severity=Severity.HIGH,
                description="发现了 XX 问题",
                evidence={"key": "value"},
            )
        return None

# 在 DiagnosisEngine 中注册
class DiagnosisEngine:
    def __init__(self, ...):
        # ...
        self.my_oracle = MyCustomOracle()  # 注册

    def check(self, ...):
        # ...
        my_report = self.my_oracle.check(state, abstract_state, action_history)
        if my_report:
            new_reports.append(my_report)
```

---

### 适配其他游戏

TITAN 框架设计为**游戏无关**的，适配步骤：

1. **替换 `titan/game/snake_env.py`**：实现新游戏的 `GameState`、`tick()`、`create_initial_state()`
2. **更新 `titan/modules/perception.py`**：修改 `abstract()` 以提取新游戏的特征
3. **更新 `titan/rag/knowledge_base.py`**：替换为新游戏的专家规则文档
4. **更新 `titan/game/bug_scenarios.py`**：定义新游戏的 Bug 注入场景
5. **所有 4 个诊断 Oracle** 均可直接复用（逻辑/崩溃/性能/卡死检测是通用的）

---

## 常见问题

**Q: 运行时报 `ImportError: anthropic`？**
```bash
pip install anthropic
# 或者使用 Mock 模式（无需 API Key）
TITAN_MOCK_LLM=1 python -m titan.agent --mock-llm
```

**Q: 如何知道 Bug 是否被成功检测？**

运行时加 `--verbose` 标志，检测到 Bug 时会打印 `[BUG DETECTED]`：
```bash
TITAN_MOCK_LLM=1 python -m titan.agent --bug slow_tick --mock-llm --verbose
```

**Q: 覆盖率为什么比较低（如 8%）？**

这是**抽象状态覆盖率**，不是代码覆盖率。贪吃蛇有大量可能的游戏状态，单次测试只能覆盖其中一小部分。多次运行、不同 Bug 类型会积累覆盖率（跨轮次记忆会持久化）。

**Q: Mock 模式下 Agent 总是走同一个方向，不会绕食物？**

是的，Mock LLM 默认返回 "RIGHT"，不像真实 Claude 那样智能决策。Mock 模式的目的是验证框架逻辑正确性，而非测试游戏表现。使用真实 API Key 可获得智能行为。

**Q: 如何只测试某一个具体测试用例？**
```bash
# 运行特定测试类
pytest tests/test_diagnosis.py::TestCrashMonitor -v

# 运行特定测试方法
pytest tests/test_diagnosis.py::TestCrashMonitor::test_report_unexpected_crash -v
```

---

## 依赖说明

```
requirements.txt:
  anthropic>=0.40.0    # Claude API SDK（Mock 模式不需要 API Key）
  pytest>=8.0.0        # 测试框架
  pytest-cov>=5.0.0    # 覆盖率统计
```

**无重型 ML 依赖**：不需要 PyTorch、scikit-learn、sentence-transformers 等。

---

## 参考资料

- **TITAN 论文**: [arXiv:2509.22170](https://arxiv.org/abs/2509.22170)
- **TITAN 深度分析**: `TITAN_深度分析.md`（本项目目录下）
- **贪吃蛇项目**: `/Users/xd/Desktop/codes/test/snake/`（被测目标）
- **Claude API 文档**: https://docs.anthropic.com/

---

*本框架基于 TITAN 论文核心思想构建，适配贪吃蛇游戏场景。*
*实现语言: Python 3.10+，测试框架: pytest，LLM 后端: Claude Sonnet 4.6*
