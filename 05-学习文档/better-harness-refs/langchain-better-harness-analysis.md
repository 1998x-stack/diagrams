# Better Harness：基于评测的 Harness 爬山优化方法

> 原文：LangChain Blog — [Better Harness: A Recipe for Harness Hill-Climbing with Evals](https://www.langchain.com/blog/better-harness-a-recipe-for-harness-hill-climbing-with-evals)
> 整理时间：2026-05-07
> 标签：#harness #约束工程 #eval #评测 #langchain #大模型开发 #agent

---

## 核心主张

> **"Evals 是 Agent 的训练数据。"**

经典机器学习里，训练数据引导模型权重朝"正确"方向更新。Agent 工程里有一个类似的学习闭环——**Eval 编码我们希望 Agent 在生产中表现出来的行为**，而 Harness 是被优化的对象。

自动优化真正难的，不是优化算法本身，而是**设计高质量的评价信号（Evals）**。

---

## 一、什么是 Harness Hill-Climbing（Harness 爬山优化）？

Harness = Agent 的运行约束层（Prompt、工具定义、工具描述、指令集等）

Hill-Climbing = 以 Eval 分数为信号，每次迭代只做一个有针对性的修改，验证之后保留提升、舍弃回退

**整体流程四步**：

```
数据获取（Data Sourcing）
    ↓
实验设计（Experiment Design）
    ↓
优化循环（Optimization Loop）
    ↓
人工审核与验收（Review & Acceptance）
```

---

## 二、Eval 的来源：怎么获取高质量评测案例

### 2.1 三种 Eval 来源

| 来源 | 特点 | 适用场景 |
|------|------|----------|
| **手动编写** | 质量高，覆盖核心行为 | 任何任务的起点 |
| **生产 Trace 挖掘** | 高吞吐、真实失败场景 | 规模化提升的主力 |
| **外部数据集** | 现成但需人工筛选 | 补充领域覆盖 |

最重要的工程建议：**给所有 Eval 打标签（Tag）**，按行为类别分（如 `tool_selection`、`multi_step_reasoning`），这样：
- 可以按类别跑子集，省钱
- 可以设计有意义的 Holdout 集
- 可以定位具体失败模式

### 2.2 Dogfooding（内部试用）的价值

团队内部用 Agent 的时候，直接在 Slack 里分享错误 Trace 链接。这会建立团队对 Agent 行为的共同认知，也是优质 Eval 的天然来源。

---

## 三、防过拟合的设计

Agent 优化和 ML 训练一样，有"作弊"风险——优化循环只想"让分数上去"，不知道泛化。

**解决方案**：

```
所有 Eval 按类别 → 分成两个集合：
  ├── Optimization Set（优化集）：用来爬山
  └── Holdout Set（保留集）：模拟生产，评估泛化
```

每次修改必须在 Holdout Set 上也验证，防止只拟合了优化集。

另外搭配**人工审核**作为第二道防线：自动优化可能加入过度细化的 instruction，虽然不影响分数，但白白消耗 token。人工审核在这里起到"剪枝"作用。

---

## 四、优化循环：每次迭代的具体步骤

### 4.1 流程

```
1. 运行 Baseline（对 Optimization Set + Holdout Set 都跑基线）
    ↓
2. 从 Trace 中诊断失败原因
   （Scores → 聚合到类别维度；Trace → 找具体出错的细节）
    ↓
3. 提出单一目标修改（每次只改一个东西，避免混淆因果）
   例如：更新一条 prompt instruction，或者更新一个工具描述
    ↓
4. 验证：
   - 新 Eval 通过了吗？
   - 之前通过的 Eval 有没有回退？
   - 如果有净提升但有部分回退，把回退信息反馈给 Agent，下轮继续修复
    ↓
5. 人工审核：检查是否过拟合、instruction 是否浪费 token
```

### 4.2 可以优化的 Harness 组件

| 组件 | 典型优化操作 |
|------|-------------|
| **Prompt/指令** | 添加针对性 instruction，纠正 Agent 对输出格式的误解 |
| **工具描述** | 更新 when-to-use、chain 顺序说明、消歧义（区分相似工具）|
| **工具添加/调整** | 加入 example，说明如何组合使用 |

---

## 五、实验结果：发现的通用修复

LangChain 用 Claude Sonnet 4.6 和 GLM-5 跑了一组 Eval，爬山后发现了以下跨模型通用的改进（均对两个模型都有效）：

| Instruction 修改 | 触发场景 | 效果 |
|-----------------|----------|------|
| `"Use reasonable defaults when the request clearly implies them."` | Agent 因缺少细节而停下来追问 | 减少阻塞，任务完成率提升 |
| `"Do not ask for details the user already supplied."` | 重复询问用户已提供的信息 | 消除了重复追问 |
| `"Do not keep issuing near-duplicate searches once you have enough information."` | 过度搜索、循环调用 | 搜索-执行类任务稳定性提升 |
| `"Ask domain-defining questions before implementation questions."` | 不分优先级地追问细节 | 追问质量改善 |

**关键发现**：当 Eval 中注入了特定领域工具（如 search-then-email），优化循环会**自动发现更好的工具组合方式**，这对垂直 Agent 开发者非常有价值。

---

## 六、Eval 维护：回归测试与"春季大扫除"

### 6.1 Eval 作为回归测试

已经修好的问题，对应的 Eval Case 保留下来，变成**回归测试**——以后任何改动不能让这个 Case 重新失败。类似软件工程里的 TDD。

设置一个"始终要过"的核心 Eval 子集，如果这些突然失败，就要怀疑当前改动是否有问题。

### 6.2 Eval 不应无限增长

定期评估每个 Eval 是否还有价值：
- 模型已经很聪明，某些 Eval 已经饱和？→ 删除
- 期望的行为变了？→ 更新或删除
- 质量 > 数量：少量精准覆盖核心行为的 Eval，比大量噪声 Eval 更有价值

---

## 七、未来方向：自动错误检测与修复飞轮

```
更多用户使用
    ↓
更多 Trace 产生
    ↓
从 Trace 中自动分类/聚类失败
    ↓
从失败 Trace 生成 Eval Case（用户纠错的 Trace 尤其有价值）
    ↓
用新 Eval 运行优化循环
    ↓
Harness 变得更好
    ↓
Agent 表现更好
    ↓（循环）
```

所有 Agent 运行都接入 LangSmith 做全 Trace 记录，支持：
- 优化循环的 Trace 级诊断
- 生产环境的回归监控
- Eval 自动生成的原料来源

---

## 八、核心结论与设计原则

| 原则 | 含义 |
|------|------|
| **Eval 质量 > 数量** | 少量精准覆盖核心行为 > 大量噪声 Eval |
| **每次只改一个东西** | 避免混淆因果，保证可归因 |
| **Holdout Set 是泛化能力的代理** | 不在 Holdout 上验证 = 不知道是否真正改善 |
| **人工审核是最后防线** | 防止优化循环加入语义上没价值的 instruction |
| **Trace 是密集反馈信号** | 优化的核心原料，必须全量记录 |
| **每个模型需要单独 Fit** | 同一 Harness 对不同模型效果不同，需分别优化 |

---

## 九、开源资源

- **研究版代码**：[github.com/langchain-ai/deepagents/.../better-harness](https://github.com/langchain-ai/deepagents/tree/main/examples/better-harness)
- **配套论文参考**：
  - [Meta-Harness（Stanford）](https://arxiv.org/abs/2603.28052)
  - [Auto-Harness（DeepMind）](https://arxiv.org/pdf/2603.03329)
- **相关文章**：
  - [How we build evals for Deep Agents](https://blog.langchain.com/how-we-build-evals-for-deep-agents/)
  - [Improving Deep Agents with Harness Engineering](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/)

---

*下载整理：2026-05-07 | 来源：LangChain Blog*
