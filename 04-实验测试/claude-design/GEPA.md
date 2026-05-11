下面专门展开 **GEPA 的两个关键机制：trace-driven 反思** 和 **演化搜索 / Pareto search**。我会尽量从“算法怎么跑、为什么有效、怎么设计 metric、工程落地怎么做”四层讲清楚。

---

# 1. GEPA 的核心：不是“改 prompt”，而是“从执行轨迹里学规则”

GEPA 全称通常解释为 **Genetic-Pareto**。论文把它定义为一种 prompt optimizer：给定一个含有一个或多个 LLM prompt 的 AI 系统，GEPA 会采样系统级轨迹，例如 reasoning、tool calls、tool outputs，然后用自然语言反思来诊断问题、提出 prompt 更新，并从 Pareto frontier 上组合互补经验。论文摘要明确强调，它用语言轨迹作为学习介质，而不是只依赖稀疏标量 reward。([Hugging Face][1])

所以 GEPA 的本质不是：

> “让 LLM 帮我写一个更好的 prompt。”

而是：

> **把每一次程序运行产生的 trace、错误、反馈、评分，转化成可泛化的 prompt 规则；再用演化搜索保留不同失败类型上表现最好的候选 prompt。**

这点非常重要。GEPA 有两个互相咬合的机制：

1. **Trace-driven reflection**：从轨迹中提炼“为什么错、下次怎么避免”。
2. **Evolutionary / Pareto search**：生成、测试、保留、交叉、选择 prompt 候选。

可以把 GEPA 想成一个“prompt 编译器”：

```text
DSPy Program + Trainset + Metric + Trace
        ↓
Reflection LM 读失败案例
        ↓
产生 prompt mutation
        ↓
在样本上测试
        ↓
更新 Pareto frontier
        ↓
返回最优 compiled program
```

DSPy 官方对自身的定位也是“Programming—not prompting—LMs”，即用结构化模块、metrics 和 optimizers 来编译 AI 程序，而不是手工维护脆弱 prompt 字符串。官方页面也把 GEPA 列为会为每个 prompt 提出并探索更好自然语言 instructions 的 optimizer。([DSPy][2])

---

# 2. 什么叫 trace-driven？

在普通 prompt tuning 里，optimizer 看到的通常是：

```text
input: 玩家说“充值后不到账”
output: performance issue
gold: payment issue
score: 0
```

这很贫瘠。模型只知道“错了”，不知道：

* 是哪个字段错了？
* 为什么错？
* 输入里哪个词触发了错误？
* 错误是分类边界问题、格式问题、证据不足，还是工具调用失败？
* 应该改 instruction、改 schema，还是改 retrieval？

而 GEPA 的 trace-driven 反思希望看到的是完整执行过程：

```text
Input:
玩家评论：充值后钻石没到账，客服也没人回。

Program trace:
1. classify_sentiment:
   reasoning: 用户表达强烈不满
   sentiment: negative

2. classify_issue:
   reasoning: 用户说客服没人回，可能是 service issue
   issue_type: social

3. escalation:
   needs_human: false

Gold:
issue_type = payment
needs_human = true

Metric feedback:
- issue_type wrong.
- “充值 / 未到账 / 退款 / 支付失败”应优先归为 payment。
- 涉及支付资金问题时 needs_human 通常为 true。
- 不要因为文本里出现“客服”就归为 social/service。
```

这就变成了一个可学习的案例。Reflection LM 可以把它总结成 prompt 更新：

```text
When the review mentions recharge, payment, refund, order not received,
missing purchased currency, or failed transaction, classify issue_type as
payment even if the user also mentions customer service. Payment issues
usually require human escalation.
```

这就是 **trace-driven reflection** 的核心价值：
**它不是从 reward 里估计梯度，而是从语言轨迹里抽取规则。**

论文也正是从这个角度批评 RL/GRPO 类方法：它们通常把 rollout 压缩成稀疏标量 reward，而 GEPA 认为语言本身包含更丰富的学习信号。([ResearchGate][3])

---

# 3. Trace 里到底包含什么？

GEPA 的 trace 不只是最终 output。对一个 DSPy program 来说，trace 可以包含多层信息。

## 3.1 输入输出 trace

最基础：

```text
input
prediction
gold label
score
feedback
```

适合分类、抽取、路由任务。

---

## 3.2 Reasoning trace

如果模块是 `ChainOfThought`，trace 还会包含模型中间 reasoning。

例子：

```text
reasoning:
The user complains about slow loading and FPS drops, so this is a performance issue.

prediction:
issue_type = bug
```

这里 reflection LM 可以发现：

```text
The reasoning identified performance symptoms, but final label became bug.
Instruction should clarify bug vs performance boundary.
```

这比只看 `bug != performance` 有用得多。

---

## 3.3 Tool-call trace

如果是 agent / ReAct / 工具调用任务，trace 可能包含：

```text
tool selected
tool arguments
tool output
tool error
retry behavior
final response
```

比如：

```text
Tool call:
search_docs(query="refund policy")

Tool output:
No result found.

Final answer:
TapTap does not support refunds.

Metric feedback:
The answer is unsupported. The tool query was too narrow; should search
"充值 未到账 退款" or use payment policy index.
```

这时 GEPA 可以生成 prompt 更新：

```text
For payment-related Chinese queries, search using both user wording and
normalized policy terms such as 充值、未到账、退款、订单、支付失败.
Never answer refund policy questions without retrieved evidence.
```

这类 trace 对 RAG 和 agent 特别重要。

---

## 3.4 Parser / schema violation trace

例如模型输出：

```json
{
  "sentiment": "bad",
  "issue_type": "payment_problem"
}
```

但 schema 要求：

```text
sentiment ∈ positive / neutral / negative
issue_type ∈ bug / performance / payment / content / account / social / other
```

feedback 可以写：

```text
Invalid enum. Use exact label "negative", not "bad".
Use exact label "payment", not "payment_problem".
```

GEPA 反思后会把格式约束加入 instruction：

```text
Use only the exact enum values. Do not invent synonyms.
```

这类问题不需要 finetune，prompt 层面往往就能修。

---

## 3.5 Multi-stage program trace

假设一个 RAG pipeline：

```text
query_rewrite → retrieve → rerank → answer → citation_check
```

最终答案错了，但错因可能在不同阶段：

| 错误阶段          | trace 现象  | 应该优化                   |
| ------------- | --------- | ---------------------- |
| query rewrite | 改写丢掉时间条件  | rewrite prompt         |
| retrieval     | 检索词太泛     | retriever query prompt |
| rerank        | 选了无关文档    | rerank prompt          |
| answer        | 有证据但没用    | answer prompt          |
| citation      | 引用了不支持的段落 | citation prompt        |

GEPA 的优势是：它可以不只看“最终 answer 错”，而是根据 trace 判断“哪个 predictor 的 instruction 应该变”。

---

# 4. Trace-driven reflection 的标准流程

可以把 GEPA 的一次反思看成下面 7 步。

## Step 1：选择一个候选 program

当前候选可能是 baseline prompt，也可能是已经进化过几轮的 prompt。

```text
candidate_prompt_v7
```

---

## Step 2：抽一个 minibatch

比如从 trainset 里抽 3 条：

```text
case_12: 充值不到账
case_37: 游戏闪退
case_91: 账号被盗
```

GEPA 不需要每轮看全量数据，因为 reflection LM 的上下文和成本有限。

---

## Step 3：执行 program，记录 trace

每条样本产生：

```text
input
intermediate reasoning
module outputs
tool calls
final answer
metric score
textual feedback
```

---

## Step 4：定位失败模式

Reflection LM 读 trace，判断：

```text
错误不是随机的，而是稳定边界问题：
- 看到“客服”时过度归为 social
- 没有把“充值未到账”识别为 payment
- needs_human 对资金问题过于保守
```

---

## Step 5：把局部错误抽象成规则

从：

```text
这个 case 错了
```

提升为：

```text
凡是涉及支付、充值、退款、订单未到账，应优先归为 payment；
即使文本同时提到客服、登录或情绪抱怨，也不要改变主 issue_type；
资金相关问题 needs_human=true。
```

这一步是 GEPA 的灵魂。

---

## Step 6：生成 prompt mutation

不是重写整个系统，而是对某个 predictor 的 instruction 做变异：

```text
Old instruction:
Classify the review into issue_type and escalation.

New instruction:
Classify the review by the primary actionable issue. Payment/recharge/refund/order
delivery problems override secondary mentions of customer service or emotion.
For money-related issues, set needs_human=true unless the text clearly says the
problem was resolved.
```

---

## Step 7：测试 mutation

新 prompt 会在 minibatch 或 validation slice 上测试。
如果提升，则进入 candidate pool / Pareto frontier；如果没提升，就丢弃或降低优先级。

---

# 5. Reflection prompt 本身通常长什么样？

概念上，GEPA 会给 reflection LM 类似这样的上下文：

```text
You are improving the instruction for a predictor in an AI program.

Current instruction:
...

Program trace examples:
Example 1:
Input: ...
Prediction: ...
Gold: ...
Score: ...
Feedback: ...

Example 2:
...

Task:
Diagnose why the current instruction failed.
Propose a new instruction that preserves what works and fixes the observed errors.
Do not overfit to exact examples.
Prefer general rules.
```

它要求 reflection LM 输出的不是“答案”，而是：

```text
new_instruction
rationale
expected improvement
```

重点是 **generalize from failure**，而不是“记住这几条样本”。

---

# 6. 为什么 trace 比 scalar reward 更有效？

因为 LLM 任务里很多错误是可语言描述的。

比如：

```text
score = 0
```

只能表达失败。

但 trace + feedback 可以表达：

```text
失败原因：模型把“退款”当成情绪抱怨；
边界规则：资金相关优先级高于情绪；
修复方式：instruction 中加入 payment override rule。
```

这是一种“语言梯度”。

你可以把它类比成：

| 优化方式                   | 学习信号                                                    |
| ---------------------- | ------------------------------------------------------- |
| RL / GRPO              | reward number                                           |
| Bayesian prompt search | candidate score                                         |
| supervised finetuning  | input-output pairs                                      |
| GEPA                   | input-output + trace + error explanation + general rule |

GEPA 论文声称，正因为利用了这种更丰富的自然语言学习信号，它在多个任务上可以比 GRPO 用少得多的 rollouts 获得更好表现；论文摘要中提到跨六个任务平均超过 GRPO 6%、最高 20%，并且最多使用 35x 更少 rollouts，也声称超过 MIPROv2 10% 以上。这个结果来自论文实验，不能直接保证业务复现，但说明它的研究假设是“trace 比 reward 更省样本”。([cspaper.org][4])

---

# 7. GEPA 的演化搜索：为什么不只保留一个最佳 prompt？

如果每轮只保留平均分最高的 prompt，会有一个问题：
**LLM 任务常常不是单一错误模式。**

比如评论分类任务里：

| Prompt 候选 | 擅长   | 不擅长  |
| --------- | ---- | ---- |
| A         | 支付问题 | 性能问题 |
| B         | 性能问题 | 账号问题 |
| C         | 账号问题 | 内容问题 |
| D         | 内容风险 | 支付问题 |

如果只看平均分，可能 A 略高，于是 B/C/D 被淘汰。
但 B/C/D 里面有很多有价值的局部规则。

GEPA 用 Pareto frontier 的思想保留这些“局部赢家”。

---

# 8. Pareto frontier 在 GEPA 里是什么意思？

一般意义上的 Pareto 最优是：

> 一个候选如果在某些目标上更好，且没有被另一个候选在所有目标上全面压制，就应该保留。

在 GEPA 里，可以把每个 validation example 或 validation slice 看成一个目标。

比如 5 个验证样本：

```text
v1 支付
v2 性能
v3 账号
v4 社区内容
v5 RAG citation
```

候选 prompt 的分数：

| Candidate | v1 | v2 | v3 | v4 | v5 | avg |
| --------- | -: | -: | -: | -: | -: | --: |
| A         |  1 |  0 |  1 |  0 |  0 | 0.4 |
| B         |  0 |  1 |  0 |  1 |  0 | 0.4 |
| C         |  1 |  1 |  0 |  0 |  0 | 0.4 |
| D         |  0 |  0 |  0 |  0 |  1 | 0.2 |

如果只看 avg，D 会被丢掉。
但 D 是唯一能解决 v5 的候选，它可能包含重要 citation rule。Pareto search 会倾向保留它，因为它覆盖了一个其他候选没覆盖的区域。

这就是 GEPA 保留多样性的关键。

---

# 9. 演化搜索的完整流程

GEPA 的搜索过程可以抽象成：

```text
Initialize:
  candidate_pool = {baseline_prompt}
  pareto_frontier = {baseline_prompt}

Loop until budget exhausted:
  1. Select parent candidate
  2. Sample train minibatch
  3. Run parent, collect traces
  4. Reflect on failures
  5. Mutate prompt
  6. Evaluate child candidate
  7. If useful, add to pool
  8. Update Pareto frontier
  9. Optionally merge/crossover candidates

Return:
  best candidate by validation aggregate score
```

这就是 Genetic-Pareto：

* **Genetic**：候选 prompt 会 mutation、merge、crossover。
* **Pareto**：选择时不只看一个全局平均分，而保留互补候选。

---

# 10. mutation：GEPA 怎么“变异” prompt？

Mutation 通常不是随机编辑，而是基于 trace 的反思编辑。

假设旧 instruction：

```text
Classify the user review into an issue type.
```

Trace 显示三类错误：

```text
1. refund/recharge 被误判成 account
2. FPS/drop frame 被误判成 bug
3. harassment 被误判成 content
```

Reflection LM 可能产生三个不同 mutation：

### Mutation A：支付优先

```text
If the text mentions recharge, refund, payment failure, missing purchased items,
or order not received, classify as payment. Payment issues override account or
customer-service mentions.
```

### Mutation B：性能边界

```text
Classify lag, FPS drops, overheating, loading delays, and stuttering as
performance unless the text names a reproducible crash or broken feature.
```

### Mutation C：社区安全边界

```text
Classify harassment, abusive chat, doxxing, spam, or player misconduct as
social/community rather than content quality.
```

这些 mutation 可能各自解决不同 validation slice。GEPA 会测试它们，不会只因为某个 mutation 对平均分提升小就立刻丢掉。

---

# 11. crossover / merge：怎么组合不同候选的经验？

如果候选 A 学到了支付规则：

```text
payment override rule
```

候选 B 学到了性能规则：

```text
performance vs bug boundary
```

GEPA 可以尝试生成候选 C：

```text
payment override rule
+ performance vs bug boundary
+ keep original concise output format
```

这就是 evolutionary search 里的 crossover / merge。

但这一步也有风险：
prompt 可能变得越来越长、越来越啰嗦、规则冲突。
所以好的 merge 不是简单拼接，而应该压缩成层级化 instruction：

```text
Determine the primary actionable issue using this priority:
1. payment: recharge, refund, order, missing purchased items
2. account: login, ban, lost account, authentication
3. performance: lag, FPS, loading, overheating
4. bug: reproducible broken feature or crash
...
```

这比把所有案例逐条塞进 prompt 更稳。

---

# 12. GEPA 搜索里的几个关键选择

## 12.1 Parent selection：从谁开始变异？

有两种常见策略：

### A. Current best

每次从当前平均分最高的候选继续变异。

优点：

* 收敛快；
* 成本低；
* 简单任务效果好。

缺点：

* 容易局部最优；
* 会丢掉小众但重要的错误类型。

---

### B. Pareto selection

从 Pareto frontier 中选择候选。

优点：

* 保持多样性；
* 覆盖更多错误模式；
* 对多阶段、多类别任务更稳。

缺点：

* 搜索更分散；
* 需要更好的 validation 设计；
* 可能维护较多候选。

GEPA 默认更倾向第二种思想，也就是名字里的 Pareto。

---

## 12.2 Component selection：优化哪个模块？

在单模块任务里无所谓：

```text
review -> issue_type, priority, reason
```

但多模块 program 里很关键：

```text
query_rewrite
retrieve
rerank
answer
judge
```

每次反思时要问：

> 这次失败到底应该改哪个 predictor 的 instruction？

举例：

### 错误 1：query rewrite 丢掉时间

```text
User: 2024 年后 TapTap 社区规则有什么变化？
Rewrite: TapTap 社区规则
```

应该改 `query_rewrite`。

---

### 错误 2：retrieval 拿到了对的文档，但 answer 没引用

```text
Retrieved doc contains exact answer.
Final answer ignores it.
```

应该改 `answer`。

---

### 错误 3：answer 有证据，但 citation 错

```text
Answer content correct, citation points to unrelated paragraph.
```

应该改 `citation`。

GEPA 的 trace-driven 机制在这里尤其有价值：没有 trace，只看最终错，很难知道该改哪一段 prompt。

---

## 12.3 Budget：搜索多深？

GEPA 的成本主要来自：

```text
task LM rollouts
+ reflection LM calls
+ validation evaluations
```

所以实际落地一般分三档：

| 档位     | 用法                |
| ------ | ----------------- |
| light  | POC、快速看有没有收益      |
| medium | 任务定义稳定后做正式优化      |
| heavy  | 高价值节点、较大验证集、上线前优化 |

不要一开始 heavy。
GEPA 的优势是少样本、少 rollout 下就可能有收益；如果一开始就大预算，很容易把 metric 或数据设计的问题掩盖掉。

---

# 13. 一个具体例子：TapTap 评论 triage

假设我们有一个 DSPy module：

```python
class ReviewTriage(dspy.Signature):
    review: str = dspy.InputField()
    sentiment: Literal["positive", "neutral", "negative"] = dspy.OutputField()
    issue_type: Literal[
        "bug", "performance", "payment", "account", "content", "social", "other"
    ] = dspy.OutputField()
    needs_human: bool = dspy.OutputField()
    reason: str = dspy.OutputField()
```

## 13.1 Baseline prompt

```text
Classify the review into sentiment, issue type, whether it needs human handling,
and a short reason.
```

---

## 13.2 第一次 trace

```text
Input:
“充值了月卡但是没有到账，客服也没人回，太坑了。”

Prediction:
sentiment = negative
issue_type = social
needs_human = false
reason = 用户抱怨客服无人回应。

Gold:
sentiment = negative
issue_type = payment
needs_human = true

Feedback:
- issue_type wrong: should be payment.
- needs_human wrong: payment/recharge/order issues require human handling.
- The phrase “客服没人回” is secondary; primary actionable issue is recharge not received.
```

---

## 13.3 Reflection 结果

```text
Failure diagnosis:
The instruction does not define primary actionable issue. The model overweights
emotion and customer-service mentions.

Prompt update:
Classify by primary actionable issue, not by emotional wording. Payment/recharge/
refund/order-not-received problems should be issue_type=payment and usually
needs_human=true, even when the review also mentions customer service.
```

---

## 13.4 第二次 trace

```text
Input:
“更新后掉帧严重，打团的时候卡成 PPT。”

Prediction:
issue_type = bug

Gold:
issue_type = performance

Feedback:
- issue_type wrong.
- FPS drops, lag, stutter, overheating, loading delay are performance.
- Use bug only for broken features, crashes, reproducible functional defects.
```

Reflection 产生第二条规则：

```text
Differentiate performance from bug. Use performance for lag/FPS/loading/heat;
use bug for crashes, broken features, data loss, or reproducible defects.
```

---

## 13.5 Pareto frontier 保留两个候选

候选 A：

```text
payment override rule
```

候选 B：

```text
performance vs bug rule
```

候选 C：

```text
payment + performance rule
```

GEPA 会比较它们在 valset 上的表现。
如果 A 在支付类样本最好，B 在性能类样本最好，C 综合最好，Pareto frontier 可能同时保留 A/B/C，直到后续 merge 出更强版本。

---

# 14. GEPA-friendly metric 应该怎么写？

GEPA 成败很大程度取决于 metric。
普通 metric：

```python
def metric(gold, pred, trace=None):
    return gold.issue_type == pred.issue_type
```

这对 GEPA 不够好，因为没有反馈。

更适合 GEPA 的 metric 应该返回：

1. 总分；
2. 字段级对错；
3. 错误原因；
4. 可泛化规则；
5. 如果可能，指出错误模块。

概念示例：

```python
def metric(gold, pred, trace=None):
    score = 0
    feedback = []

    if pred.sentiment == gold.sentiment:
        score += 0.25
    else:
        feedback.append(
            f"sentiment wrong: expected {gold.sentiment}, got {pred.sentiment}."
        )

    if pred.issue_type == gold.issue_type:
        score += 0.35
    else:
        feedback.append(
            f"issue_type wrong: expected {gold.issue_type}, got {pred.issue_type}."
        )

        if gold.issue_type == "payment":
            feedback.append(
                "Rule: recharge, refund, payment failure, missing purchased items, "
                "or order not received should be classified as payment."
            )

        if gold.issue_type == "performance":
            feedback.append(
                "Rule: lag, FPS drops, loading delays, overheating, and stutter "
                "should be performance, not bug."
            )

    if pred.needs_human == gold.needs_human:
        score += 0.25
    else:
        feedback.append(
            f"needs_human wrong: expected {gold.needs_human}, got {pred.needs_human}."
        )

    if len(pred.reason) <= 120:
        score += 0.15
    else:
        feedback.append("Reason is too long; keep it under 120 characters.")

    return dspy.Prediction(
        score=score,
        feedback="\n".join(feedback)
    )
```

重点不是代码格式，而是反馈质量。

---

# 15. 好 feedback 和坏 feedback 的区别

## 坏 feedback

```text
Wrong.
```

```text
The answer is incorrect.
```

```text
Score: 0.3
```

这些反馈对 GEPA 帮助很小。

---

## 中等 feedback

```text
issue_type is wrong. Expected payment, got social.
```

有用，但还不够。

---

## 好 feedback

```text
issue_type is wrong. Expected payment, got social.
The review says “充值后未到账”, which is a payment fulfillment issue.
The phrase “客服没人回” is secondary and should not determine issue_type.
General rule: recharge, refund, order not received, missing purchased currency,
or failed transaction should map to payment and usually needs_human=true.
```

这种 feedback 能直接被 reflection LM 转化成 instruction。

---

# 16. GEPA 搜索为什么可能比人工 prompt 迭代强？

人工 prompt 迭代通常是：

```text
看到几个 bad case
手工改 prompt
再看几个 case
凭感觉继续改
```

问题是：

* 人容易只记住最近看到的错误；
* prompt 改动没有系统评估；
* 很难保留多个局部最优；
* 很难知道某条规则是否伤害其他样本；
* 很难复现“为什么这版 prompt 更好”。

GEPA 的流程更像实验系统：

```text
每个候选都有 lineage
每次 mutation 有 trace 和 rationale
每个候选在 valset 上有分数
Pareto frontier 保存局部专长
最终选择基于 holdout validation
```

它把 prompt engineering 从“经验编辑”变成“可追踪搜索”。

---

# 17. GEPA 和 MIPROv2 的本质区别

DSPy 官方页面把 MIPROv2 和 GEPA 都归为 instruction/prompt optimizer，但它们侧重点不同：MIPROv2 更像系统化生成 instructions 和 demos 并搜索组合；GEPA 更强调通过自然语言反思轨迹来进化 prompt。([DSPy][2])

| 维度        | MIPROv2                                     | GEPA |
| --------- | ------------------------------------------- | ---- |
| 主要输入      | 数据、metric、候选 instruction、demos              |      |
| GEPA 主要输入 | trace、feedback、失败诊断                         |      |
| 搜索方式      | instruction/demo proposal + discrete search |      |
| GEPA 搜索方式 | mutation + Pareto frontier + optional merge |      |
| 最强场景      | 有稳定标签，想优化 instruction + few-shot            |      |
| GEPA 最强场景 | 有丰富错误反馈，能解释为什么错                             |      |
| 信号类型      | 分数为主                                        |      |
| GEPA 信号类型 | 分数 + 自然语言 trace + feedback                  |      |
| 风险        | demos / instruction 过拟合                     |      |
| GEPA 风险   | reflection 误归纳、prompt 膨胀                    |      |

简单判断：

```text
只有 label 和 accuracy → 先试 MIPROv2
有错误原因 / 日志 / 工具失败 / schema violation → 先试 GEPA
```

---

# 18. GEPA 和 RL / GRPO 的本质区别

| 维度        | RL / GRPO                | GEPA |
| --------- | ------------------------ | ---- |
| 改什么       | 模型策略 / 权重                |      |
| GEPA 改什么  | prompt / instruction     |      |
| 学习信号      | 标量 reward                |      |
| GEPA 学习信号 | trace + feedback + score |      |
| 数据需求      | 通常较大                     |      |
| GEPA 数据需求 | 可少，但反馈要好                 |      |
| 成本        | 高 rollout、高训练成本          |      |
| GEPA 成本   | 编译期调用成本                  |      |
| 可解释性      | 较弱                       |      |
| GEPA 可解释性 | 每次 mutation 可读           |      |
| 适合        | 需要改变模型内部行为               |      |
| GEPA 适合   | 模型已有能力，但 prompt/流程没激发好   |      |

论文主张 GEPA 在多个实验中能用更少 rollout 超过 GRPO 和 MIPROv2，但这仍是研究实验结论；业务落地时应自己用 testset 验证。([cspaper.org][4])

我的判断：

> GEPA 是 RL 之前非常值得做的一层。
> 如果 GEPA 都无法通过 prompt/程序层面改善，再考虑 finetuning 或 RL。

---

# 19. GEPA 最容易失败的地方

## 19.1 Metric 错，GEPA 会优化错

如果 metric 只奖励格式：

```text
JSON valid = 1
JSON invalid = 0
```

GEPA 可能会优化出格式稳定但内容胡说的 prompt。

---

## 19.2 Feedback 太局部，导致过拟合

坏反馈：

```text
This exact sentence should be payment.
```

好反馈：

```text
Recharge/refund/order-not-received language should be payment.
```

GEPA 需要规则，不是记忆。

---

## 19.3 Prompt 越变越长

Reflection LM 可能把每个失败案例都塞进 instruction：

```text
If A then...
If B then...
If C then...
...
```

最后 prompt 变成规则垃圾桶。

解决方式：

* 要求 reflection LM 合并规则；
* 限制 instruction 长度；
* 人工 review compiled prompt；
* 定期蒸馏成优先级表；
* 把复杂规则外置成 policy docs 或 validator。

---

## 19.4 Pareto frontier 被坏 valset 带偏

如果 validation set 不代表真实流量，GEPA 会认真优化一个错误世界。

比如 valset 支付问题过多，prompt 会过度 payment-biased。
所以 valset 应该覆盖真实分布，也要覆盖高价值 hard cases。

---

## 19.5 Reflection LM 过强或过弱都有问题

过弱：看不懂 trace，乱改 prompt。
过强：产生很复杂、看似聪明但不可控的规则。

工程上建议：

* task LM 可以便宜；
* reflection LM 可以强；
* 但 compiled prompt 必须人工 review。

---

# 20. GEPA 落地时的数据切分

建议至少三份：

| 数据       | 用途                         |
| -------- | -------------------------- |
| trainset | 用于 trace-driven reflection |
| valset   | 用于 Pareto frontier 和候选选择   |
| testset  | 完全不参与优化，只做最终验收             |

不要让 GEPA 直接看 testset。
否则你看到的是“被优化过的成绩”，不是泛化能力。

一个实用起点：

```text
train: 100–300
val: 50–100
test: 100–300
```

如果任务很贵，比如 agent / RAG / code repair，可以更少，但 feedback 必须更密。

---

# 21. 工程落地推荐配置

POC 阶段：

```python
optimizer = dspy.GEPA(
    metric=metric,
    reflection_lm=strong_lm,
    auto="light",
    candidate_selection_strategy="pareto",
    component_selector="round_robin",
    log_dir="runs/gepa_triage",
    track_stats=True,
    seed=0,
)
```

我建议默认：

* `auto="light"`：先验证方向；
* `candidate_selection_strategy="pareto"`：保留多样性；
* `component_selector="round_robin"`：多模块时更稳；
* `log_dir`：必须开，方便审计；
* `track_stats=True`：看每轮 mutation 和分数变化；
* 固定 `seed`：方便复现。

---

# 22. 一套推荐的 GEPA POC 流程

```text
1. 选一个稳定 schema 的任务
   例如 review triage / RAG answer / 工单分类

2. 做 baseline
   当前 prompt + 当前模型 + testset

3. 写 GEPA-friendly metric
   score + 字段级 feedback + 可泛化规则

4. 跑 light GEPA
   不追求一次到位，先看 mutation 是否合理

5. 查看 logs
   重点看：prompt 是否变好、规则是否过拟合、是否变长

6. 独立 testset 验收
   只接受真实 holdout 提升

7. 人工 review compiled prompt
   检查安全、隐私、业务规则、幻觉风险

8. 灰度上线
   监控错误类型、解析失败、成本、延迟

9. 定期 recompile
   数据分布或模型变化后重新跑
```

---

# 23. 最适合 GEPA 的业务节点

结合 TapTap / 游戏社区场景，我认为优先级是：

## 第一优先级：评论 / 工单 triage

输入：

```text
玩家评论、客服工单、社区反馈
```

输出：

```text
sentiment
issue_type
priority
needs_human
reason
```

为什么适合：

* schema 清楚；
* feedback 容易写；
* 错误类型可解释；
* prompt 规则对效果影响大。

---

## 第二优先级：RAG grounded answer

输入：

```text
问题 + 检索文档
```

输出：

```text
answer + citations
```

feedback 可以写：

```text
- 引用了不支持的文档
- 漏掉了关键证据
- 没有回答时间条件
- 把旧政策当成新政策
```

这类 trace 对 GEPA 很友好。

---

## 第三优先级：UGC 风险识别

输入：

```text
帖子、评论、聊天文本
```

输出：

```text
risk_type
severity
action
reason
```

feedback 可以区分：

```text
false positive
false negative
policy boundary
context missing
```

但要注意政策敏感性和误杀风险。

---

## 第四优先级：agent / tool-use 修复

输入：

```text
用户任务
```

trace：

```text
tool selection
tool arguments
tool errors
intermediate outputs
```

feedback：

```text
选错工具
参数缺失
没有处理错误
调用顺序错误
```

GEPA 可以把这些 tool traces 转成 action policy。

---

# 24. 最后用一句话总结

**GEPA 的 trace-driven 反思，是把“这次为什么错”转成“下次如何避免的规则”；GEPA 的演化搜索，是把这些规则作为 prompt 候选不断变异、测试、保留和合并。**

它真正强的地方不是“自动写 prompt”，而是：

> **让 prompt 优化进入可评估、可追踪、可复现、可搜索的工程流程。**

在实践中，GEPA 的上限主要取决于三件事：

1. trace 是否足够完整；
2. feedback 是否足够具体；
3. validation set 是否代表真实任务分布。

[1]: https://huggingface.co/papers/2507.19457?utm_source=chatgpt.com "Paper page - GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning"
[2]: https://dspy.ai/?utm_source=chatgpt.com "DSPy"
[3]: https://www.researchgate.net/publication/394049542_GEPA_Reflective_Prompt_Evolution_Can_Outperform_Reinforcement_Learning?utm_source=chatgpt.com "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning | Request PDF"
[4]: https://cspaper.org/openprint/20260416.0001v1?utm_source=chatgpt.com "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning | OpenPrint — CSPaper"
  
