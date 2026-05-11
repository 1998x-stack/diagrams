# agent.py 深度解析：外层 Agent 与 Proposer Workspace

> 文件：`better_harness/agent.py`
> 行数：约 430 行
> 定位：系统的"大脑驱动层"——负责构建外层 Agent 的工作空间、调用 Deep Agent、解析其提案

---

## 一、整体职责

`agent.py` 解决的核心问题是：**如何把 Harness 优化问题，转化成一个 Agent 可以完成的文件编辑任务？**

答案是构建一个"Proposer Workspace"——一个临时目录，里面放好了：
- 当前 Harness 的各 surface 文件（可编辑）
- 当前 train 失败案例的详细信息
- 历史迭代的决策摘要
- 任务说明文件（task.md）

然后把这个目录交给外层 Deep Agent，让它像一个人类工程师一样，读取失败原因、思考改进方案、直接编辑文件。

---

## 二、DEFAULT_SYSTEM_PROMPT：外层 Agent 的行为约束

这是整个优化质量的关键之一，源码中原文是 350 字以内的英文，核心规则如下：

```python
DEFAULT_SYSTEM_PROMPT = """You are Better Agent, an outer-loop Deep Agent that improves another agent harness.

Rules:
- Edit only files under /current.
- Do not edit train_cases, history, or bookkeeping files except /proposal.md.
- Prefer general harness fixes over case-specific hacks.
- Do not overfit to the visible examples. Infer the broader policy...
- Treat files under /current as the real harness surfaces.
- For code surfaces, write real code, not pseudocode.
- If you change tool or middleware behavior, update both implementation and wiring.
- Make the smallest set of edits needed for the visible train failures.
- When done, write a short explanation to /proposal.md.
"""
```

**几个关键约束的用意**：

| 规则 | 用意 |
|------|------|
| 只能编辑 `/current` 下的文件 | 防止 Agent 污染历史记录或 Eval 源文件 |
| 不要针对可见用例做 hack | 防止过拟合，要求推断出通用策略 |
| 最小改动 | 防止一次改太多导致无法归因 |
| 改了实现必须改注册/配置 | 防止"改了 middleware 实现但没更新 create_agent 调用"这类常见错误 |

---

## 三、ProposerWorkspace：外层 Agent 的沙盒

```python
@dataclass(frozen=True)
class ProposerWorkspace:
    root: Path              # 整个工作区根目录
    current_dir: Path       # /current/ — 可编辑的 surface 文件
    proposal_file: Path     # /proposal.md — Agent 写方案摘要的地方
    surface_files: dict[str, Path]  # surface name → 文件路径映射
```

### 3.1 目录结构（每次迭代独立）

```
runs/experiment-name/
└── history/visible/iterations/001/
    └── proposer_workspace/          ← ProposerWorkspace.root
        ├── current/
        │   ├── prompt.txt           ← surface "prompt" 的当前值
        │   ├── custom_tools.py      ← surface "tools" 的当前值
        │   └── custom_middleware.py ← surface "middleware_impl" 的当前值
        ├── surface_manifest.json    ← surface 名 → 文件 → 真实注入目标的映射
        ├── task.md                  ← 任务说明（外层 Agent 首先读的文件）
        ├── train_failures.json      ← 失败 case 列表
        ├── train_summary.json       ← train 运行汇总
        ├── train_cases/             ← 失败 case 的源文件（外层 Agent 可读）
        │   └── tests/evals/test_tool_selection.py
        ├── proposal.md              ← 外层 Agent 写方案摘要到这里
        ├── history/
        │   ├── visible_history.md   ← 历次迭代决策摘要
        │   └── prior_visible/       ← 历次迭代的 train 产物和决策文件副本
        ├── outer_agent_result.json  ← 外层 Agent 完整输出
        └── result.json              ← 提案结果 + 候选 Variant
```

### 3.2 surface_manifest.json

外层 Agent 通过这个文件了解每个可编辑文件对应的真实注入目标：

```json
{
  "prompt": {
    "kind": "module_attr",
    "target": "deepagents.graph:BASE_AGENT_PROMPT",
    "file": "current/prompt.txt"
  },
  "tools": {
    "kind": "workspace_file",
    "target": "libs/deepagents/deepagents/custom_tools.py",
    "file": "current/custom_tools.py"
  }
}
```

这让 Agent 知道它编辑的文件最终会被注入到哪里，可以做更精准的修改。

### 3.3 task.md：外层 Agent 的任务说明书

自动生成，包含：
- 任务规则（只改 /current，不改其他，推断通用策略）
- 当前 Variant 标签和 train 分数
- 所有可编辑 surface 的列表
- 当前 train 失败列表（case_id + stratum + 失败原因）

---

## 四、propose_variant()：一次提案的完整流程

```python
def propose_variant(experiment, current, train_result, layout, iteration):
    # 1. 构建 Proposer Workspace
    workspace = build_proposer_workspace(...)
    
    # 2. 调用外层 Deep Agent
    final_message = invoke_deepagents_proposer(experiment, workspace)
    
    # 3. 读取 Agent 编辑后的 surface 文件
    values = load_candidate_values(current=current, workspace=workspace)
    
    # 4. 计算哪些 surface 被改了
    changed_surfaces = tuple(
        name for name in experiment.surfaces
        if values[name] != current.values[name]
    )
    
    # 5. 读取 Agent 写的方案摘要
    summary = read_proposal_summary(workspace)
    
    # 6. 返回 Proposal + 候选 Variant
    return Proposal(changed_surfaces, workspace_dir, summary, final_message), \
           build_variant(experiment, label=f"iter-{iteration:03d}", values=values)
```

**changed_surfaces 的用途**：
- 如果为空 → 外层 Agent 没有做任何修改 → 主循环提前退出
- 不为空 → 记录在 Proposal 中，用于报告和调试

---

## 五、invoke_deepagents_proposer()：两种调用模式

```python
def invoke_deepagents_proposer(experiment, workspace):
    deepagents_root = _resolve_deepagents_root(...)
    
    if deepagents_root is not None:
        # 模式1：通过 uv subprocess 调用（推荐，隔离依赖）
        return _invoke_via_uv_project_with_retries(...)
    else:
        # 模式2：直接 importlib 动态导入（需要当前环境已安装 deepagents）
        return _invoke_via_import(...)
```

### 5.1 subprocess 模式（推荐模式）

```python
completed = subprocess.run([
    "uv", "run", "--project", str(project_root),
    "python", "-m", "better_harness.agent",
    str(request_path), str(result_path)
])
```

通过 `uv run --project` 在 deepagents 的独立虚拟环境中运行，避免依赖冲突。

请求/响应通过 JSON 文件传递：
```json
// outer_agent_request.json
{
  "workspace_root": "/path/to/proposer_workspace",
  "model": "claude-sonnet-4-6",
  "max_turns": 11000,
  "system_prompt": "..."
}
```

stdout/stderr 保存到 `outer_agent_stdout.log` / `outer_agent_stderr.log`，便于调试。

### 5.2 重试逻辑

```python
for attempt in range(3):
    try:
        return _invoke_once(...)
    except RuntimeError as exc:
        if attempt == 2 or not _is_transient_model_error(str(exc)):
            raise
        time.sleep(2 * (attempt + 1))  # 指数退避：2s, 4s
```

触发重试的错误类型：
- `overloaded` / `overloaded_error`
- `error code: 529`
- `rate limit`
- `timeout`

### 5.3 外层 Agent 的调用参数

```python
agent.invoke({
    "messages": [HumanMessage(content=
        "Read /task.md first. Then inspect the current surface files, "
        "visible history, and failing train cases, edit only /current, "
        "and finish by updating /proposal.md."
    )]
}, config={"recursion_limit": experiment.better_agent_max_turns})
```

`recursion_limit` 即 `max_turns`，默认 11000——一个非常大的值，确保外层 Agent 有足够轮次完成分析和编辑。

---

## 六、历史感知：外层 Agent 看到什么

每次迭代，外层 Agent 可以访问：

**可见内容（有助于学习）**：
- 当前 surface 文件（/current/）
- 当前 train 失败列表（train_failures.json）
- 当前 train 失败的源文件（train_cases/）
- 历次迭代的决策摘要（visible_history.md）
- 历次迭代的 train 产物（prior_visible/train/）

**不可见内容（防止作弊）**：
- holdout 集的任何内容
- holdout 集的 case 源文件
- holdout 运行的产物

这个设计模拟了机器学习中的 train/test 数据隔离，让外层 Agent 只能从 train 信号中归纳通用策略，而不能针对 holdout 设计特化规则。

---

## 七、`_jsonify()`：通用序列化器

agent.py 内有一个递归序列化器，能处理以下类型：

```python
def _jsonify(value):
    - None / bool / int / float / str  → 直接返回
    - Path                             → str(path)
    - dict / list / tuple / set        → 递归处理
    - Pydantic 对象（model_dump）       → 递归处理
    - LangChain Message 对象（有 .type）→ 提取 type/content/tool_calls 等字段
    - 其他有 __dict__ 的对象           → 遍历 vars()
    - 其余                             → repr()
```

这确保了 `outer_agent_result.json` 无论外层 Agent 返回什么格式的结果，都能被正确序列化保存。

---

## 八、设计要点总结

| 设计决策 | 原因 |
|----------|------|
| Proposer Workspace 每轮独立构建 | 避免跨迭代污染，每轮有完整的快照 |
| task.md 明确告知规则和失败列表 | 减少外层 Agent 的探索负担，直接给它最需要的信息 |
| surface_manifest.json 说明注入目标 | 让外层 Agent 知道自己改的文件对应什么真实组件 |
| subprocess 隔离执行 | 避免 better-harness 和 deepagents 的依赖冲突 |
| visible/private 分离 | 防止外层 Agent 针对 holdout 过拟合 |
| 只读取 changed_surfaces | 自动检测外层 Agent 是否真的做了修改，无修改则退出 |
