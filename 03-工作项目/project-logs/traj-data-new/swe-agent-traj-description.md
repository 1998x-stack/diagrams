下面按 **“常见 trajectory schema 字段 → 含义 → 如何构造”** 来讲。先说结论：

**SWE-agent 的 `.traj` 没有一个跨所有版本完全固定不变的单一 schema。**
官方当前文档明确说明：`<instance_id>.traj` 是一个 JSON 文件，核心在 `trajectory` 键下，记录每一步的 `(thought, action, observation)`；并且在 **1.1.0 之前** 常见的是 `message` 字段，**1.1.0 起改成了 `query`**，表示“当前 step 精确送给模型的输入”。所以更准确的说法是：**有一组稳定的常见字段，外加少量版本相关字段。** ([swe-agent.com][1])

---

# 1. 顶层常见字段

## 1.1 `trajectory`

**什么意思**
这是最核心的字段，保存 agent 的逐步交互记录。官方文档说，`.traj` 文件的主内容就是在 `trajectory` 键下看到每一步 agent 的信息。([swe-agent.com][1])

**如何构造**
每次 agent 完成一轮：

1. 先拿到模型原始输出
2. 解析出 `thought` 和 `action`
3. 执行动作
4. 收集 `observation` 和环境 `state`
5. 把这一轮 append 到 `trajectory` 数组里。
   这和官方示例里每个 step 同时包含 `response / thought / action / observation / state / query` 是一致的。([swe-agent.com][1])

---

## 1.2 `environment`

**什么意思**
这是运行环境标识。官方示例里有 `environment: "swe_main"` 这样的字段。它用于说明这条轨迹是在什么 agent/environment 配置下跑出来的。([swe-agent.com][1])

**如何构造**
通常在轨迹初始化时，从当前运行配置里直接写入环境名或环境 profile。它不是逐步生成的，而是**run-level metadata**。

---

## 1.3 版本相关的其他顶层元数据

官方当前“Output files”文档重点展示的是 `trajectory`，没有承诺所有顶层字段都固定；同时示例还特别提醒，完整示例来自 **v0.7.0**，新版本可能不同。也就是说，顶层通常还会有一些实验元数据，但**跨版本最稳定、最该依赖的是 `trajectory` 本身**。([swe-agent.com][1])

如果你是自己设计一个兼容性更好的 schema，我建议顶层至少保留：

* `instance_id`
* `environment`
* `trajectory`
* `info`
* `config_ref`
* `schema_version`

这里面只有 `environment` 和 `trajectory` 是官方示例里直接出现的；其余是我建议你在自定义实现里补上的工程化字段，便于复现和版本迁移。

---

# 2. `trajectory[]` 里每一步的常见字段

这是最重要的部分。

## 2.1 `response`

**什么意思**
这是 **模型原始输出**。官方文档直接写了注释：`This is the output of the LM`。([swe-agent.com][1])

**如何构造**
把当前 step 送给模型后，拿到的完整文本原样保存。
它通常包含自然语言推理和最终动作文本，例如“先解释一下要做什么，然后给出命令”。

**设计建议**
不要只存解析后的 thought/action。`response` 非常重要，因为：

* 能调 parser 错误
* 能复盘格式错误
* 能做行为分析
  这也是官方把它保留下来的原因之一。([swe-agent.com][1])

---

## 2.2 `thought`

**什么意思**
这是从 `response` 中解析出的“思考部分”。官方文档写得很明确：`We then parse it into thoughts and actions`。([swe-agent.com][1])

**如何构造**
用当前 action parser 按约定模板从 `response` 里抽取 thought 段落。
如果你的 agent 用 ReAct 风格，这通常就是 `Thought:` 后面的文本。

**设计建议**
如果解析失败，最好同时记录：

* `response`
* `parse_error`
* 原始 `query`
  这样更容易定位是不是 prompt 模板、parser 规则或模型输出格式出了问题。这里的“parse_error”是我建议补充的工程字段。

---

## 2.3 `action`

**什么意思**
这是从 `response` 中解析出的“动作部分”，也是实际执行给环境的命令。官方示例里是 `ls -F\n`、`open setup.py\n` 这种字符串。([swe-agent.com][1])

**如何构造**
和 `thought` 一样，由 parser 从 `response` 中抽取。然后把标准化后的动作字符串传给环境执行器。

**设计建议**
这里最好存两份概念：

* `action_raw`：模型原始给出的动作段
* `action`：经过 parser/normalizer 后真正执行的动作
  官方示例只明确展示 `action`，但如果你自己做分析系统，分开存会更稳。

---

## 2.4 `observation`

**什么意思**
这是动作执行后的环境反馈。官方文档注释为：`And execute the action, resulting in the output`。([swe-agent.com][1])

**如何构造**
执行 `action` 后，把 stdout / stderr /工具返回值 /系统整理后的反馈合成为 observation 字符串。
SWE-agent 论文里还提到：即使命令没有输出，也会显式返回成功说明，避免 agent 不知道刚才是否生效。([swe-agent.com][1])

**设计建议**
如果你是自己实现，建议把 observation 再拆成：

* `observation_text`
* `exit_code`
* `observation_type`（例如 shell_output / format_error / lint_error / viewer_output）
  官方文档展示的是合并后的 `observation` 文本；拆细是更利于分析的增强版做法。

---

## 2.5 `state`

**什么意思**
这是动作执行后，从环境中额外抽取出来的状态。官方示例给的是 JSON 字符串，例如：
`{"open_file": "...", "working_dir": "..."}`。文档注释是：`after the action was executed, state can be extracted from the environment`。([swe-agent.com][1])

**如何构造**
每轮 action 执行完成后，从环境对象读取关键状态，再序列化成 JSON 字符串写入。
在官方示例里，最常见的就是：

* `open_file`
* `working_dir` ([swe-agent.com][1])

**设计建议**
如果你想让这个字段更适合机器分析，最好直接存成对象而不是 JSON 字符串，例如：

```json
"state": {
  "open_file": "/repo/foo.py",
  "working_dir": "/repo"
}
```

官方示例里是字符串化 JSON；如果是你自己定义 schema，我更推荐对象形式，解析更简单。

---

## 2.6 `query`

**什么意思**
这是“当前 step 精确送给模型的输入消息列表”。官方文档特别说明：
**1.1.0 之前** 用的是 `message` 字段，近似表示下一步输入；
**1.1.0 起** 换成了 `query`，表示当前 step 的精确输入。([swe-agent.com][1])

**如何构造**
在真正发模型请求之前，把完整 messages 数组保存下来，例如：

* system
* user / issue statement
* demonstration
* recent observations
* collapsed history
  然后把这份精确输入挂到当前 step 上。([swe-agent.com][1])

**设计建议**
`query` 非常关键，因为它能回答：
**“模型为什么会在这一步做出这个 response？”**
如果没有它，你只能看结果，无法精确复原输入条件。

---

# 3. 版本相关字段：`message` vs `query`

## 3.1 `message`

**什么意思**
这是旧版本常见字段。官方文档说，在 **SWE-agent 1.1.0 之前**，有一个 `message` 字段，大致对应“下一步模型输入”。([swe-agent.com][1])

**如何构造**
旧版本里，它通常是在当前步结束后，把下一轮将要发送给模型的消息状态保存下来。

## 3.2 为什么后来改成 `query`

因为 `message` 只是“近似对应”，不够精确。
`query` 更明确：它展示的是**当前 step 真正送给模型的 exact input**。这对调试 prompt、对齐 token 计费、复现轨迹都更可靠。([swe-agent.com][1])

**工程判断**
如果你现在要设计兼容 schema，建议：

* 新写入：只写 `query`
* 旧兼容：读取时同时支持 `query` 和 `message`

---

# 4. 一个最常见、最实用的 schema 模板

如果按官方“当前常见字段”整理，一个最实用的 step-level schema 可以写成这样：

```json
{
  "environment": "swe_main",
  "trajectory": [
    {
      "response": "Let's inspect the repository structure first...\nls -F",
      "thought": "Let's inspect the repository structure first...",
      "action": "ls -F\n",
      "observation": "AUTHORS.rst\nCHANGELOG.rst\nsrc/\ntests/\n",
      "state": "{\"open_file\": \"n/a\", \"working_dir\": \"/repo\"}\n",
      "query": [
        {"role": "system", "content": "You are a helpful assistant ..."},
        {"role": "user", "content": "Fix issue ..."}
      ]
    }
  ]
}
```

这个结构和官方文档展示的字段集合一致。([swe-agent.com][1])

---

# 5. 每个字段分别“如何构造”的标准流水线

如果你是从 0 到 1 自己实现 trajectory logging，我建议严格按这个顺序构造：

## 第一步：构造 `query`

把这一轮真正发给模型的 messages 完整收集好，写入 `query`。
这是**先于**模型调用发生的。([swe-agent.com][1])

## 第二步：拿到模型原文，写入 `response`

把模型输出原样保存。
这是 parser 之前的原始证据。([swe-agent.com][1])

## 第三步：解析 `thought` 和 `action`

按当前 action parser 规则拆分。
如果失败，最好仍然保留 `response`，并额外记 parser 错误。

## 第四步：执行动作，写入 `observation`

把动作交给环境执行器，拿回反馈。
反馈最好是 agent-friendly 的，而不是原始噪声全量透传。论文也强调过 concise feedback 的重要性。

## 第五步：抽取环境状态，写入 `state`

从环境对象拿关键状态，如当前打开文件、工作目录。([swe-agent.com][1])

## 第六步：append 到 `trajectory`

把这一轮完整记录落盘，形成可复盘、可分析的轨迹。

---

# 6. 如果你要做“分析友好”的增强 schema，我建议补哪些字段

这些不是官方当前最小示例里的必需字段，但非常值得补：

## 顶层补充

* `schema_version`：明确轨迹格式版本
* `instance_id`：问题实例 ID
* `run_id`：实验运行 ID
* `agent_version`：SWE-agent / 你自己系统的版本
* `model_name`：底层模型名

## step 级补充

* `step_id`
* `timestamp_start`
* `timestamp_end`
* `parse_error`
* `exit_code`
* `tool_name`
* `tool_args`
* `observation_type`
* `cost`
* `tokens_prompt`
* `tokens_completion`

这些补充字段的价值在于：
官方最小 schema 适合“看轨迹”，但不一定最适合“做诊断、统计、重放”。这是我对官方最小结构的工程化补全建议。官方文档当前明确支持的是 `response / thought / action / observation / state / query` 这一组核心 step 字段。([swe-agent.com][1])

---

# 7. 一句话总结

SWE-agent 的 trajectory 最核心的 schema 可以理解为：

**顶层一个 `trajectory` 数组，里面每个 step 至少包含 `response`、`thought`、`action`、`observation`、`state`、`query`；旧版本常见 `message`，新版本推荐 `query`。**
这些字段分别对应：**模型原文、解析后的思考、执行动作、环境反馈、环境状态、当前步精确输入**；构造顺序就是 **先保存 query，再保存 response，再解析，再执行，再抽状态，再落盘**。([swe-agent.com][1])

你要的话，我下一条可以直接给你一版 **“完整 JSON Schema 草案”**，或者给你 **“Python dataclass / Pydantic 版本的 trajectory schema”**。

[1]: https://swe-agent.com/latest/usage/trajectories/ "Output files - SWE-agent documentation"

