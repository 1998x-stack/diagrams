# Meta-Harness: End-to-End Optimization of Model Harnesses

> 论文来源：Stanford / arXiv
> arXiv ID：2603.28052
> PDF：`meta-harness-stanford.pdf`（同目录）
> 链接：https://arxiv.org/abs/2603.28052
> 提交时间：2026-03-30
> 作者：Yoonho Lee 等

---

## Abstract（摘要）

大语言模型系统的性能不仅取决于模型权重，还取决于其 Harness——那段决定"存储什么信息、检索什么信息、向模型呈现什么"的代码。

然而 Harness 目前仍以人工设计为主，而现有的文本优化器又因为对反馈压缩过度而不适合这个场景。

本文提出 **Meta-Harness**：一个对 LLM 应用的 Harness 代码进行搜索优化的外循环系统。

**核心机制**：
- 使用一个 Agentic Proposer（提案 Agent），它能通过文件系统访问所有历史候选的源码、分数和执行 Trace

**实验结果**：
- 在在线文本分类任务上，比 SOTA 上下文管理系统提升 **7.7 个百分点**，且使用的上下文 Token 减少了 **4 倍**
- 在检索增强数学推理上，发现的单一 Harness 在 200 道 IMO 级别题目上平均提升 **4.7 个百分点**（跨 5 个保留模型）
- 在 Agentic 编程任务上，发现的 Harness 超越了最好的人工设计基线（TerminalBench-2）

**核心结论**：更丰富地访问历史经验，可以实现自动化的 Harness 工程。

---

## 关联资源

- PDF（完整论文）：同目录 `meta-harness-stanford.pdf`
- DOI：https://doi.org/10.48550/arXiv.2603.28052
