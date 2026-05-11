SWE-agent 的 “trajectory” 可以从两个层面看：

**第一层是运行时消息轨迹**：system prompt、issue、thought/action、environment response、submit patch 这一整串交互。论文用 **Figure 9** 专门画了这个结构。
**第二层是落盘后的轨迹文件**：`.traj`，通常是 JSON，里面会记录逐步的 thought / action / observation，以及完整 history、结果信息和复现实验配置。官方文档把它描述为包含 `(thought, action, observation)` turns 的主输出文件。([swe-agent.com][1])

下面我分三部分讲：

1. **轨迹格式长什么样**
2. **怎么分析一条轨迹**
3. **怎么判断轨迹里哪些问题导致了后续失败**

---

## 1. SWE-agent 轨迹格式长什么样

### 1.1 论文里的“消息轨迹”长什么样

论文在 Figure 9 里给的是一个抽象结构：

* **System prompt**
* **Demonstration（可选）**
* **Issue statement**
* 然后进入多轮循环：

  * agent 输出 **Thought & Action**
  * environment 返回 **Environment Response**
* 老的 observation 可以被 **collapsed**
* 最后 agent **Submit**
* 系统根据代码状态产出 **Patch File**。

论文正文还补充了交互规则：

* 每一步都要求 agent 生成 **一个 thought 和一个 action**。
* 如果格式不合法，会收到专门的 **Format Error**，要求重试；连续 3 次格式错误会提前终止。
* 如果命令没有 stdout，环境不会沉默，而会显式返回一句：**“Your command ran successfully and did not produce any output”**，避免 agent 猜不透刚才那一步有没有成功。
* 旧 observation 会被折叠成一行占位，例如 “Old output omitted (101 lines)” 之类，以减少上下文污染。

所以从论文视角看，一条轨迹本质上是：

> **任务初始化上下文 + 多轮 thought/action/observation 闭环 + 最终提交结果。** 

---

### 1.2 落盘后的 `.traj` 文件一般长什么样

官方文档把 `.traj` 说明为 JSON 格式的主输出文件，核心会记录每一步的 `(thought, action, observation)`。([swe-agent.com][1])

根据官方文档与代码说明，一个典型轨迹文件通常至少包含这几类字段：

* `trajectory`：逐步 action/observation 记录
* `history`：完整消息历史
* `info`：执行结果、token/cost、submission 等元信息
* `replay_config`：复现这次运行所需的配置。([DeepWiki][2])

其中单步记录通常会包含：

* `thought`
* `action`
* `observation`
* `response`
* `execution_time`。([DeepWiki][2])

可以把它理解成一个“黑匣子”：

* `trajectory` 负责看 agent **怎么一步步走**
* `history` 负责看 prompt / error / collapse **怎么组织上下文**
* `info` 负责看 **最后为什么停**
* `replay_config` 负责 **能不能复现**。([DeepWiki][2])

---

## 2. 怎么分析一条 SWE-agent 轨迹

我建议用 **四层分析法**。这和论文自己的分析方式是对齐的：他们既分析动作分布，也分析成功/失败模式，还会做具体 case study。

---

### 2.1 第一层：先看轨迹有没有走对“阶段”

论文对成功轨迹的分析表明，SWE-agent 的成功模式通常不是一上来就 edit，而是大致经历这样的阶段：

1. **定位 / 搜索**
2. **打开相关文件并细看**
3. **编辑**
4. **运行 python / pytest 验证**
5. **清理并 submit**。

论文对成功样例 `psf/requests-2317` 的 qualitative analysis 就是这样展开的：先定位 `sessions.py`，再 `search_file` 找相关调用位置，再 edit，接着新建 `reproduce_issue.py` 做复现测试，确认 200 OK 之后再清理和提交。

所以分析一条轨迹时，第一件事不是看 patch 对不对，而是问：

* 它有没有完成 **定位**
* 有没有完成 **修改**
* 有没有完成 **验证**
* 有没有在某个阶段卡死

如果一条轨迹长时间停留在 `find_file/search_dir/open/scroll`，那问题大概率在 **localization**。
如果长时间在 `edit/edit/edit` 来回打转，大概率是 **编辑稳定性 / 恢复失败**。
如果已经 edit 完了但没有有效测试，大概率是 **验证链路不足**。这个判断与论文对成功动作模式和失败模式的分析是一致的。

---

### 2.2 第二层：看动作序列有没有异常模式

论文专门统计了成功轨迹的动作频率和 n-gram pattern。它发现：

* 常见成功序列里，`find_file / search_dir -> open -> search_file -> goto` 这类 localization 模式很常见
* 常见结束模式是 `[edit, python, rm, submit]`
* 一些重复动作模式本身就是失败信号，比如反复 `edit (4x)` 或 `scroll_down (4x)` 往往会持续级联。

所以分析轨迹时，可以把动作序列当成一个行为信号：

#### 典型异常 1：搜索-浏览循环过长

表现是：
`find_file -> open -> scroll_down -> search_file -> goto -> scroll_down -> ...`
这通常意味着 agent 还没找到真正相关位置，或者搜索反馈没帮助它收缩空间。论文在失败模式里也有 “Failed to Find Relevant File” 和 “Failed to Find Edit Location”。

#### 典型异常 2：编辑循环过长

表现是：
`edit -> error/observation -> edit -> error/observation -> edit ...`
这通常意味着 agent 在自我修复上失败，和论文里的 **Failed to Recover from Edit** 对应。论文指出这类失败占 unresolved 实例的 **23.4%**。

#### 典型异常 3：过早 submit

表现是还没建立可靠 reproduction / testing 就 `submit`。
这通常落在 **Incorrect Implementation** 或 **Overly Specific Implementation**。论文指出这两类加起来占 unresolved 的 **52.0%**。

---

### 2.3 第三层：看 observation 是否支持下一步决策

这层很关键，因为 SWE-agent 的核心是 thought/action/observation 闭环。

论文明确说，environment response 的设计目标是让最近动作的效果更清楚；旧 observation 会被折叠；无输出命令会给显式成功信息。

所以分析轨迹时，要检查的是：

* action 执行后，observation 有没有明确告诉 agent **状态变了什么**
* edit 后有没有看到 **更新后的窗口**
* lint/syntax error 时有没有拿到 **错误位置和局部 before/after**
* 测试命令有没有暴露出 **真正失败原因**

如果 observation 本身是弱的，后续跑偏就不一定是“模型不会推理”，可能是 **状态反馈不足**。这也是论文把 ACI 定义成“命令 + 状态通信”的原因。

---

### 2.4 第四层：把轨迹、生成 patch、gold patch 放在一起看

论文在失败模式自动分类时，做法不是只看轨迹。它是把：

* **agent trajectory**
* **agent 生成的 patch**
* **gold patch（参考答案）**

三者一起交给模型做失败分类。作者说明，他们先从行为分析中整理出候选失败类别，再对 unresolved trajectories 做自动分类；在一个小验证集上，LM 标签和作者手工标签的一致率达到 **87%**。

这说明只看轨迹还不够。
很多失败不是“没动作”，而是“动作看起来合理，但 patch 的语义不对”。这类问题只有把最终 diff 也放进来，才能判断是：

* 改到了合理区域但解法错了
* 改法太特例化
* 其实方向对，但没来得及做完。

---

## 3. 怎么判断轨迹中哪些问题导致了后续任务失败

这里最关键的是：**不要把失败当作“最后一步错了”，而要当作“前面某个转折点把轨迹推到了坏状态”**。

我建议按“根因链”来判。

---

### 3.1 先找第一个不可逆转的坏信号

坏轨迹通常不是从 submit 才开始坏，而是更早就出现了第一个“错误拐点”。常见拐点有：

#### A. 没找到相关文件

表现：

* 一直没打开正确文件
* 搜索 query 反复漂移
* 在无关文件里长时间浏览

这类对应论文的 **Failed to Find Relevant File**。

#### B. 找到了文件，但没找到具体编辑位置

表现：

* 打开了正确文件
* 但一直在 `scroll/goto/search_file` 间打转
* edit 总是改错行段或改到不关键位置

这类对应 **Failed to Find Edit Location**。

#### C. 编辑引入坏状态后没恢复

表现：

* edit 后反复 lint/syntax error
* 无效 edit 一直被拒
* 后续 thought 开始混乱或重复

这类对应 **Failed to Recover from Edit**。论文说这类失败占 23.4%。

#### D. 方案方向合理，但实现错了

表现：

* 找对文件、改对区域、也做了测试
* 但 patch 语义不满足 issue，或者破坏更一般情形

这对应 **Incorrect Implementation** 或 **Overly Specific Implementation**，也是论文里最大头的失败来源。

#### E. 没复现成功，就在盲改

表现：

* issue 不能稳定复现
* 没有有效测试脚本或断言
* patch 完全靠直觉提交

这会落在 **Failed to Reproduce / Can’t Reproduce** 一类。

---

### 3.2 用“前因后果”而不是“最终标签”来归因

论文给出的失败标签很有用，但真正分析轨迹时，最好再往前追一层因果。

例如：

* **最终标签：Incorrect Implementation**
  不代表根因一定是“模型不会写代码”。
  也可能是因为前面 reproduction 不充分，导致它误解了 issue 的真实语义。

* **最终标签：Failed to Recover from Edit**
  也不一定根因就是 edit 本身。
  有可能是 earlier localization 不准，导致后面编辑一直在错误区域修修补补。

所以我建议用这条规则：

> **最终失败标签回答“死法是什么”，而根因分析回答“是在哪个 turn 开始不可逆地走偏”。**

---

### 3.3 一个实用的轨迹诊断框架

你可以直接拿这套去看一条 `.traj`：

#### 第一步：看终止方式

先看 `info` / 末尾 history：

* 是 `submit`
* 是 cost limit
* 还是连续 format errors 终止。论文在附录把 episode 终止条件画出来了：submit、超预算、连续格式错误都会导致结束。

#### 第二步：给动作分阶段

把每个 turn 粗分成：

* Localization
* Reproduction
* Editing
* Verification
* Submission

然后看有没有某个阶段异常冗长或直接缺失。这个阶段化方法与论文的 qualitative analysis 和 action pattern 分析一致。

#### 第三步：找第一个坏拐点

通常是第一次出现以下之一：

* 打开了错误文件并一直没回来
* 开始在无意义搜索里循环
* 第一次 invalid edit 后没恢复
* 第一次测试结果已经提示方向错了，但后续没有纠偏

#### 第四步：对照最终 patch

把 agent patch 和 gold patch 对比：

* 如果改动区域完全不同，多半是 localization 问题
* 如果区域接近但逻辑不同，多半是 implementation 问题
* 如果 agent patch 只 hardcode 了具体 case，多半是 overly specific
* 如果只差最后几步但 episode 提前结束，多半是 budget/time 问题。论文在 Table 9 里对这些失败类型给了文字定义。

#### 第五步：给出“根因 + 表现 + 证据”

不要只说“失败了”，而要说：

* **根因**：Failed to find edit location
* **表现**：在正确文件里反复 `scroll_down/search_file/goto`，但从未 edit 到 gold patch 所在函数
* **证据**：动作序列 + 最终 patch 未触及目标区域 + 测试前无有效 reproduction

这种写法最接近论文自己的 failure-mode analysis 精神。

---

## 4. 论文实际上是怎么做失败分析的

论文的失败分析不是凭直觉，而是有一个比较清晰的流程：

1. 对默认配置下 **SWE-bench Lite 未解决的 248 条轨迹**做分析。
2. 先根据前面的行为分析，总结出一组 **failure categories**。
3. 抽取一个小验证集，由作者 **手工标注**。
4. 然后把 **trajectory + agent patch + gold patch** 交给另一个 LM 做自动分类。
5. 在验证集上，自动标签和人工标签 **87% 一致**。

他们最后得到的主要失败类包括：

* Failed to Reproduce
* Failed to Find Relevant File
* Failed to Find Edit Location
* Failed Edit Recovery
* Overly Specific Implementation
* Incorrect Implementation
* Ran Out of Budget 等。

这套方法本质上说明：

> **判断失败原因，最好不要只看轨迹本身，而要把“行为过程 + 最终产物 + 理想产物”三者联合起来。** 

---

## 5. 一句话总结

SWE-agent 的轨迹本质上是一个 **system / issue / thought-action / environment-response / submit** 的多轮交互记录，旧 observation 会折叠，格式错误会被显式纠正，最终会落成 `.traj` 文件保存完整 history 和逐步 state。
分析轨迹时，最有效的方法不是只看最后 patch，而是沿着 **定位 → 编辑 → 验证 → 提交** 的阶段去看哪里第一次不可逆地走偏，再结合最终 patch 与 gold patch，把失败归因为 **找错文件、找错位置、编辑恢复失败、实现错误、过度特化、未复现成功或预算耗尽** 等类别。

我可以下一条直接给你做一个 **“SWE-agent 轨迹诊断 checklist”**，或者给你一个 **可直接用于标注轨迹失败原因的 rubric 模板**。

[1]: https://swe-agent.com/latest/usage/trajectories/ "Output files - SWE-agent documentation"
[2]: https://deepwiki.com/SWE-agent/SWE-agent/8.1-trajectory-files-and-format "Trajectory Files and Format | SWE-agent/SWE-agent | DeepWiki"
