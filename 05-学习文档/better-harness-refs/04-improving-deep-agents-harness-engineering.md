# Improving Deep Agents with Harness Engineering

> 来源：LangChain Blog
> 链接：https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering
> 标签：#harness #agent #terminal-bench #langchain
> 核心成果：**仅改 Harness，不换模型，TerminalBench 2.0 从 52.8% → 66.5%（Top 30 → Top 5）**

---

## 一、核心主张

> **Harness 的目标：将模型天生参差不齐的智能，为我们关心的任务塑形。**

Harness 是围绕模型构建的系统层：系统提示、工具选择、执行流程（Middleware/Hooks）。Harness Engineering 是在不换模型权重的前提下，通过工程手段优化 Agent 性能。

---

## 二、实验设置

- **基准**：TerminalBench 2.0（89 个任务，涵盖机器学习、调试、生物学等）
- **模型**：固定为 GPT-5.2-Codex（全程不换）
- **运行框架**：Harbor（沙箱管理）+ LangSmith（Trace 记录）
- **优化对象**：System Prompt、Tools、Middleware（三个 knob）

**起点**：默认 Prompt + 标准工具 + 标准 Middleware → 52.8%

---

## 三、关键改进手段

### 3.1 构建-自验证循环（Build & Self-Verify）

最常见的失败模式：Agent 写完代码 → 自己看了一遍 → 觉得没问题 → 停止。

**改进**：在系统提示中注入结构化问题解决流程：

```
1. 规划 & 探索：读任务、扫代码库、制定计划（带验证方式）
2. 构建：实现计划，同时写测试（覆盖正常路径和边界情况）
3. 验证：运行测试，读完整输出，对比任务规格（不是对比自己的代码）
4. 修复：分析错误，回到原始规格，修复问题
```

**附加机制**：`PreCompletionChecklistMiddleware`
- 在 Agent 即将退出时拦截
- 强制执行一次对 Task 规格的验证遍历
- 类似 Ralph Wiggum Loop（hook 强制 Agent 继续执行直到验证通过）

### 3.2 环境上下文注入

| 注入内容 | 作用 |
|----------|------|
| 目录结构 + 可用工具（Python 环境等） | 减少 Agent 自行探索时的错误 |
| "你的代码会被自动测试"的提示 | 让 Agent 遵守文件路径、接口规格 |
| 时间预算警告 | 纠正 Agent 对时间边界的无知 |

**关键洞察**：Agent 越了解自己的环境、约束和评估标准，越能自主完成工作。

### 3.3 破局循环（Loop Detection）

Agent 容易陷入"死循环"——对同一段破代码反复做小改动（Trace 中有些长达 10+ 次）。

**改进**：`LoopDetectionMiddleware`
- 通过 Tool Call Hook 追踪每个文件的编辑次数
- 第 N 次编辑同一文件时，注入上下文："考虑重新审视你的方案"

### 3.4 推理计算量分配

GPT-5.2-Codex 有 4 个推理模式：low / medium / high / xhigh

**发现**：
- 全程 xhigh → 53.9%（任务超时太多）
- 全程 high → 63.6%
- **"推理三明治"策略 xhigh-high-xhigh → 66.5%**

```
规划阶段（xhigh）：充分理解问题
实现阶段（high）：平衡效率和质量
验证阶段（xhigh）：彻底检查，抓住错误
```

---

## 四、Trace Analyzer Skill（自动化 Trace 分析）

将 Trace 分析工具化为一个 Agent Skill：

```
1. 从 LangSmith 拉取实验 Trace
2. 并行启动多个错误分析 Agent → 主 Agent 综合结论 + 提出改进建议
3. 聚合反馈 → 针对性修改 Harness
```

类似 ML 中的 Boosting——专注于上一轮的错误案例。

---

## 五、实际结果

| 阶段 | 得分 | 变化 |
|------|------|------|
| 基础 Harness | 52.8% | — |
| + Build & Verify | ~58% | +5.x |
| + 环境上下文注入 | ~62% | +4.x |
| + Loop Detection | ~64% | +2.x |
| + 推理三明治 | **66.5%** | +2.5 |

**排名**：Top 30 → **Top 5**（仅改 Harness，模型固定）

---

## 六、实践原则总结

| 原则 | 说明 |
|------|------|
| **代理上下文工程** | 帮 Agent 准备好环境信息，减少其自行探索的错误面 |
| **强制自验证** | 模型偏向第一个可行方案，要主动 prompt 它验证 |
| **Trace 作为反馈信号** | 调试工具（无工具、指令不足）和推理（走错方向）要一起看 |
| **短期修复坏模式** | 针对当前模型短板设计 Guardrail，计划随模型进化移除 |
| **每个模型单独调 Harness** | Codex 和 Claude 的 Prompting 方式不同，不能直接复用 |

---

## 七、相关资源

- [Trace 数据集](https://smith.langchain.com/public/29393299-8f31-48bb-a949-5a1f5968a744/d?tab=2)（公开分享）
- [Deep Agents Python](https://github.com/langchain-ai/deepagents)
- [Deep Agents JavaScript](https://github.com/langchain-ai/deepagentsjs)
- [Codex Prompting Guide](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/)
- [Claude Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
