# core.py 深度解析：数据模型与主优化循环

> 文件：`better_harness/core.py`
> 行数：约 600 行
> 定位：整个系统的骨架，定义所有核心数据结构、配置加载逻辑、主优化循环和 CLI 入口

---

## 一、数据模型层

### 1.1 Surface：可编辑的 Harness 组件

```python
@dataclass(frozen=True)
class Surface:
    name: str       # 配置中的 surface 名称，如 "prompt"、"tools"
    kind: str       # "module_attr" 或 "workspace_file"
    target: str     # 注入目标，如 "deepagents.graph:BASE_AGENT_PROMPT" 或 "libs/.../custom_tools.py"
    base_value: str # 基准值（优化前的初始内容）
    filename: str   # 在 Proposer Workspace 中的文件名
```

**两种 kind 的区别**：

| kind | 注入方式 | 典型场景 |
|------|----------|----------|
| `module_attr` | 运行时 `setattr(module, attr, value)` | 修改 Prompt 字符串常量 |
| `workspace_file` | 临时替换目标 workspace 中的文件 | 修改工具代码、Middleware 实现 |

### 1.2 EvalCase：一个具体的测试用例

```python
@dataclass(frozen=True)
class EvalCase:
    case_id: str    # 格式如 "tests/evals/test_tool.py::test_case[{model}]"
    split: str      # "train" / "holdout" / "scorecard"
    stratum: str    # 行为分类，如 "tool_use"、"conversation"
```

`{model}` 是模板变量，由 `case.render(model=experiment.model)` 替换，使同一个 case 配置可以在不同模型上运行。

### 1.3 Experiment：实验配置实体

所有从 `.toml` 文件加载的配置都汇聚在这里：

```python
@dataclass(frozen=True)
class Experiment:
    path: Path                  # 配置文件路径
    name: str                   # 实验名称
    runner: str                 # "pytest" 或 "harbor"
    workspace_root: Path        # 目标 Agent 的 workspace 根目录
    model: str                  # 被优化 Agent 的模型
    max_iterations: int         # 最大优化迭代次数
    better_agent_model: str     # 外层优化 Agent 使用的模型
    better_agent_max_turns: int # 外层 Agent 最大轮次（默认 11000）
    runner_config: dict         # Runner 专属配置
    surfaces: dict[str, Surface]
    cases: tuple[EvalCase, ...]
```

提供了多个便捷方法：
- `cases_for_split(split)` — 按 split 过滤 cases
- `rendered_case_ids(split)` — 渲染后的 case ID 列表（model 已替换）
- `strata_for_split(split)` — 某个 split 下的行为类别集合
- `has_split(split)` — 是否定义了该 split

### 1.4 Variant：一个具体的 Harness 版本

```python
@dataclass(frozen=True)
class Variant:
    label: str                      # 版本标签，如 "baseline"、"iter-001"
    model: str
    changed_surfaces: tuple[str, ...]  # 相比基准改变了哪些 surface
    surfaces: dict[str, Surface]
    values: dict[str, str]          # 每个 surface 的当前值
```

**两个关键方法**：
- `attr_overrides()` — 返回 `{module:attr: value}` 字典，供 module_attr 注入
- `file_overrides()` — 返回 `{relative_path: value}` 字典，供文件替换

Variant 支持序列化/反序列化（`to_dict()` / `save()` / `load()`），确保每次迭代的 Harness 版本都可持久化复现。

### 1.5 CaseOutcome 和 SplitResult：结果结构

```
SplitResult
├── split, variant, model
├── passed / total / score / returncode
└── outcomes: tuple[CaseOutcome, ...]
    └── CaseOutcome
        ├── case_id, split, stratum
        ├── status: "passed" / "failed" / "skipped" / "missing"
        ├── score, duration_s
        ├── failure_message
        ├── artifacts_dir  ← case 级别的产物目录
        └── trace_ref      ← LangSmith Trace URL
```

`SplitResult` 的关键方法：
- `passing_case_ids()` — 返回通过的 case ID 集合（用于计算回退）
- `failing_outcomes()` — 返回失败的 outcome 列表（用于构建失败报告给外层 Agent）
- `correctness` — 通过率 `passed / total`

---

## 二、配置加载：`load_experiment()`

从 `.toml` 文件加载实验配置的核心函数，处理了大量工程细节：

### 2.1 环境变量展开

```python
ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")

def expand_env(value: str) -> str:
    return ENV_PATTERN.sub(lambda match: os.environ[match.group(1)], value)
```

配置文件中可以用 `${DEEPAGENTS_ROOT}` 这种形式引用环境变量，加载时自动展开。

### 2.2 Surface 解析逻辑

Surface 有两种初始值来源（二选一，不能同时有）：

```toml
# 方式1：从文件读取
[surfaces.middleware_impl]
base_file = "libs/deepagents/deepagents/custom_middleware.py"

# 方式2：直接内联
[surfaces.prompt]
base_value = """
You are a helpful agent.
"""
```

代码校验 `base_file` 和 `base_value` 必须恰好存在一个：

```python
if has_base_file == has_base_value:
    raise ValueError(f"surface '{surface_name}' must define exactly one of ...")
```

### 2.3 Split 别名机制

```python
SPLIT_ALIASES = {
    "acceptance": "scorecard",
    "final_eval": "scorecard",
}
```

支持用 `acceptance` 或 `final_eval` 作为 `scorecard` 的别名，方便团队按习惯命名。

### 2.4 校验规则（`validate_experiment()`）

以下规则在加载时就会报错：

| 规则 | 原因 |
|------|------|
| train 和 holdout 的 strata 必须完全一致 | 确保两个集合覆盖相同行为类别，防止泛化检验失效 |
| train 和 holdout 各自至少一个 case | 最小有效实验要求 |
| 渲染后的 case_id 在所有 split 中唯一 | 防止同一个 case 被评估两次造成统计混乱 |
| surface 必须至少有一个 | 无 surface 则无从优化 |

---

## 三、主优化循环：`run_experiment()`

这是整个系统的大脑，约 80 行代码实现了完整的 Harness 爬山优化：

```python
def run_experiment(experiment, *, output_dir, max_iterations=None, reuse_existing=False):
```

### 3.1 完整流程

```
1. 构建文件系统布局 (RunLayout)
2. 构建 baseline variant（所有 surface 取初始值）
3. 运行 baseline 的 train + holdout Eval（建立分数基准）
4. 进入迭代循环（最多 max_iterations 次）：
   a. 如果 train + holdout 已全部通过 → 提前退出
   b. 调用外层 Agent 提出候选 Variant（propose_variant）
   c. 如果外层 Agent 没有改变任何 surface → 退出循环
   d. 运行候选 Variant 的 train + holdout Eval
   e. 比较：candidate_combined > current_combined？
      - 是 → 接受，更新当前最佳 Variant
      - 否 → 拒绝，保持当前 Variant 不变
   f. 记录本轮迭代决策到磁盘
5. 运行 scorecard Eval（若配置了）
6. 生成 RunReport 并写入磁盘
```

### 3.2 接受标准：combined pass count

```python
current_combined = current_train.passed + current_holdout.passed
candidate_combined = train.passed + holdout.passed
accepted = candidate_combined > current_combined
```

**关键设计**：接受标准是 train + holdout 的**合并通过数**，不是只看 train。这意味着：
- 即使 train 分数下降，只要 holdout 提升更多，仍然接受
- 过拟合优化集但损害泛化的改动会被自动拒绝
- 实际上这是一个内置的防过拟合机制

### 3.3 RunLayout：文件系统布局

```
output_dir/
├── manifest.json               # 实验元数据
├── split.json                  # Split 分配清单
├── variants/
│   ├── baseline.json           # 每个 Variant 的 surface 值快照
│   └── iter-001.json
├── history/
│   ├── visible/
│   │   ├── train/              # train split 的运行产物（外层 Agent 可见）
│   │   │   └── baseline/
│   │   │       └── cases/
│   │   └── iterations/
│   │       └── 001/
│   │           ├── decision.json
│   │           ├── decision.md
│   │           └── proposer_workspace/
│   └── private/
│       └── holdout/            # holdout 产物（外层 Agent 不可见）
├── _runtime/
│   └── sitecustomize.py        # 运行时 patch 入口
└── report.json / report.md     # 最终报告
```

**visible / private 分离**是防止外层 Agent 直接看到 holdout 内容（否则可能针对 holdout 过拟合）。

---

## 四、Trace 收集机制

系统内置了从日志中自动提取和保存 LangSmith Trace URL 的功能：

```python
URL_PATTERN = re.compile(r"https?://[^\s\"'>]+")

def extract_trace_refs(*, payload, stdout, stderr) -> list[str]:
    # 递归遍历结构化 payload 中的所有字符串字段
    # 同时扫描 stdout / stderr 文本
    # 提取所有 URL
```

提取到的 Trace URL 会被：
1. 写入 `trace_refs.json` 和 `trace_refs.md`
2. 如果有 `LANGSMITH_API_KEY`，自动通过 API 拉取完整 Trace 内容保存到本地

这让外层 Agent 在下一轮迭代时，可以直接读取历史 Trace 做深度诊断。

---

## 五、CLI 命令

| 命令 | 用途 |
|------|------|
| `validate <config>` | 加载并校验配置，打印摘要信息 |
| `inventory <config>` | 列出所有可用的 Eval 单元 |
| `split <config>` | 生成 split 分配清单文件 |
| `run <config>` | 运行完整优化循环 |
| `inspect <run_dir>` | 打印指定运行目录的 report.json |
| `traces <run_dir>` | 列出该运行下所有保存的 Trace 引用 |

---

## 六、设计要点总结

| 设计决策 | 原因 |
|----------|------|
| 所有数据结构 `frozen=True` | 不可变对象，防止迭代过程中意外修改历史状态 |
| Variant 序列化到磁盘 | 每个版本可完整复现，不依赖内存状态 |
| combined pass count 作为接受标准 | 内置防过拟合：holdout 损失会阻止接受 |
| visible / private 分离 | 外层 Agent 只能看到 train 产物，不能针对 holdout 作弊 |
| Trace URL 自动收集 | 为下一轮迭代提供诊断素材，形成学习闭环 |
