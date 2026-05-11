# TITAN-Snake: LLM驱动的贪吃蛇自动测试框架

> 基于 TITAN 论文（arXiv:2509.22170）实现，针对 Snake 贪吃蛇游戏的 Python 测试框架

---

## 项目目标

将 TITAN 论文的四大核心模块用 Python 实现，测试 `/Users/xd/Desktop/codes/test/snake/` 贪吃蛇项目（TypeScript/Vite），包含：
1. **感知抽象模块**：将游戏状态压缩为 LLM 可处理的符号表示
2. **动作优化模块**：过滤无效动作，推荐最优操作集（≤5个）
3. **反射推理模块**：进度监控 + 卡死自救 + 跨轮次覆盖记忆
4. **问题诊断模块**：三层 Oracle 自动检测 Bug + 结构化报告

---

## 目录结构

```
code_auto_test/
├── CLAUDE.md                     # 本文档
├── requirements.txt              # Python 依赖
├── titan/
│   ├── __init__.py
│   ├── game/
│   │   ├── __init__.py
│   │   ├── snake_env.py          # [Layer 0] Python 贪吃蛇模拟器
│   │   └── bug_scenarios.py      # [Layer 0] Bug 注入机制
│   ├── rag/
│   │   ├── __init__.py
│   │   └── knowledge_base.py     # [Layer 1] RAG 知识库（TF-IDF 检索）
│   ├── llm_client.py             # [Layer 2] Claude API 封装（含 Mock 模式）
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── perception.py         # [Layer 3] 感知抽象模块
│   │   ├── action_opt.py         # [Layer 4] 动作优化模块
│   │   ├── reflection.py         # [Layer 5] 反射推理模块
│   │   └── diagnosis.py          # [Layer 6] 问题诊断模块
│   └── agent.py                  # [Layer 7] TITAN 主循环
└── tests/
    ├── test_snake_env.py
    ├── test_rag.py
    ├── test_perception.py
    ├── test_action_opt.py
    ├── test_reflection.py
    ├── test_diagnosis.py
    └── test_agent.py
```

---

## 模块职责边界

| 模块 | 输入 | 输出 | LLM调用 |
|------|------|------|---------|
| `snake_env` | Direction | GameState | 无 |
| `knowledge_base` | query: str | list[str] | 无 |
| `perception` | GameState + KnowledgeBase | AbstractState | 无 |
| `action_opt` | AbstractState + GameState | ActionBundle | 可选（Mock可跳过）|
| `reflection` | History + AbstractState | ReflectionResult | 是 |
| `diagnosis` | GameState + History + timing | list[DiagnosisReport] | 是 |
| `agent` | BugType + max_ticks | TITANTestReport | 通过子模块 |

---

## 环境变量

```bash
ANTHROPIC_API_KEY=sk-ant-...    # Claude API Key（真实调用必须）
TITAN_MOCK_LLM=1                # 设置后使用 Mock LLM（单元测试用）
```

---

## 测试命令

```bash
# 安装依赖
pip install -r requirements.txt

# 逐层测试（严格顺序，每层通过才能进下一层）
pytest tests/test_snake_env.py -v      # Layer 0
pytest tests/test_rag.py -v            # Layer 1
pytest tests/test_perception.py -v    # Layer 3
pytest tests/test_action_opt.py -v    # Layer 4
pytest tests/test_reflection.py -v    # Layer 5
pytest tests/test_diagnosis.py -v     # Layer 6
pytest tests/test_agent.py -v         # Layer 7

# 全量测试 + 覆盖率
pytest tests/ --cov=titan --cov-report=term-missing -v

# Mock 模式运行 Agent（无需 API Key）
TITAN_MOCK_LLM=1 python -m titan.agent

# 真实运行（需要 API Key）
ANTHROPIC_API_KEY=sk-ant-... python -m titan.agent
```

---

## 设计原则

1. **零训练**：不微调任何模型，纯靠 zero-shot + RAG 知识
2. **分层测试**：每个模块独立可测，Mock LLM 避免 API 消耗
3. **纯 Python RAG**：用 `collections.Counter` 实现 TF-IDF，无重型 ML 依赖
4. **Bug 注入**：通过装饰器包装游戏环境，模拟5种真实 Bug 类型
5. **深度工作法**：每层完成测试后才推进，保证代码质量

---

## 参考资料

- **TITAN 论文分析**: `TITAN_深度分析.md`
- **贪吃蛇项目**: `/Users/xd/Desktop/codes/test/snake/`
- **贪吃蛇游戏引擎**: `/Users/xd/Desktop/codes/test/snake/src/core/GameEngine.ts`
- **贪吃蛇类型定义**: `/Users/xd/Desktop/codes/test/snake/src/types.ts`
