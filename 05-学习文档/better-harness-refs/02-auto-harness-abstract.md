# AutoHarness: Improving LLM Agents by Automatically Synthesizing a Code Harness

> 论文来源：DeepMind / arXiv
> arXiv ID：2603.03329
> PDF：`auto-harness-deepmind.pdf`（同目录）
> 链接：https://arxiv.org/abs/2603.03329
> 提交时间：2026-02-10（v1）
> 作者：Xinghua Lou, Miguel Lázaro-Gredilla, Antoine Dedieu, Carter Wendelken, Wolfgang Lehrach, Kevin P. Murphy

---

## Abstract（摘要）

**核心问题**：LLM 作为 Agent 使用时，常常尝试执行不仅低效、而且被外部环境**明确禁止**的动作。例如，在 Kaggle GameArena 象棋竞赛中，78% 的 Gemini-2.5-Flash 失败是因为走了**非法棋步**。

**解决方案**：本文展示了 Gemini-2.5-Flash 可以**自动合成代码 Harness**。
- 只需少量轮次的迭代代码精化
- 利用环境反馈作为信号

**实验结果**：
- 在 145 个不同的 TextArena 游戏（单人 + 双人）中完全消除了非法动作
- 使更小的 Gemini-2.5-Flash 超越了更大的 Gemini-2.5-Pro
- 将技术推向极限：让模型直接用代码生成完整策略（消除决策时对 LLM 的依赖）
- 代码策略在 16 个 TextArena 单人游戏上获得比 Gemini-2.5-Pro 和 GPT-5.2-High 更高的平均奖励

**核心结论**：用较小模型合成定制代码 Harness（或完整策略），可以超越更大模型，同时更具成本效益。

---

## 关键词

agent harness, code synthesis, self-improvement, code-as-policy, text games

---

## 关联资源

- PDF（完整论文）：同目录 `auto-harness-deepmind.pdf`
- DOI：https://doi.org/10.48550/arXiv.2603.03329
