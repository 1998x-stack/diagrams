# Better Harness 参考资料集

整理时间：2026-05-07
来源：LangChain 博客文章《Better Harness: A Recipe for Harness Hill-Climbing with Evals》

---

## 文件清单

| 文件 | 类型 | 内容 |
|------|------|------|
| `01-meta-harness-abstract.md` | 论文摘要 | Meta-Harness（Stanford）—— Harness 代码端到端优化 |
| `meta-harness-stanford.pdf` | 论文全文 PDF | arXiv:2603.28052 |
| `02-auto-harness-abstract.md` | 论文摘要 | AutoHarness（DeepMind）—— 自动合成代码 Harness |
| `auto-harness-deepmind.pdf` | 论文全文 PDF | arXiv:2603.03329 |
| `03-how-we-build-evals-langchain.md` | 博客整理 | 如何构建 Deep Agent Eval：数据、指标、运行 |
| `04-improving-deep-agents-harness-engineering.md` | 博客整理 | Harness Engineering 实战：TerminalBench Top5 经验 |

---

## 阅读建议

1. **快速上手** → 先读 `04`（最具实操性，有具体数字和手段）
2. **理解 Eval 体系** → 读 `03`（指标定义最清晰）
3. **学术背景** → 读 `01` 和 `02` 的摘要，有兴趣再看 PDF 全文
4. **代码实验** → `~/Desktop/deepagents/examples/better-harness/`（已下载）

---

## 核心概念速查

| 概念 | 简释 |
|------|------|
| **Harness** | 围绕模型的约束层：System Prompt + Tools + Middleware |
| **Hill-Climbing** | 以 Eval 分数为信号，迭代改进 Harness 的优化方法 |
| **Eval** | Agent 行为评测案例，是 Harness 优化的"训练数据" |
| **Holdout Set** | 保留集，用于检验泛化能力，防止过拟合优化集 |
| **Ideal Trajectory** | 理想执行轨迹，作为效率评估基准 |
| **Solve Rate** | 期望步骤数 / 实际延迟，综合衡量速度与正确性 |
| **AutoDream** | 自动蒸馏历史记忆的机制（Claude Code 内部） |
| **Trace** | Agent 完整执行记录，是分析和生成 Eval 的核心原料 |
