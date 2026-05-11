# runners.py 深度解析：Eval 执行器

> 文件：`better_harness/runners.py`
> 行数：约 330 行
> 定位：系统的"执行层"——负责实际运行 Eval，解析结果，产出结构化的 SplitResult

---

## 一、整体架构

系统支持两种 Eval 运行器，共享相同接口：

```python
class PytestRunner:   # 用于 pytest 测试套件
class HarborRunner:   # 用于 Harbor 沙盒任务

def build_runner(experiment) -> PytestRunner | HarborRunner:
    if experiment.runner == "pytest":
        return PytestRunner()
    if experiment.runner == "harbor":
        return HarborRunner()
```

两种 Runner 都实现：
- `collect_inventory(experiment)` — 发现可用的 Eval 单元
- `run_split(experiment, variant, split, layout, reuse_existing)` — 运行一个 split

---

## 二、PytestRunner：pytest 执行器

### 2.1 命令构建

每次运行 case 的 pytest 命令格式：

```bash
uv run --project /path/to/evals --group test \
  pytest \
  -p better_harness_plugin \         # 加载 patch 插件
  --model claude-sonnet-4-6 \        # 注入模型参数
  --evals-report-file case_dir/summary.json \  # 结构化结果输出
  --junitxml case_dir/junit.xml \    # JUnit XML 结果
  -q \                               # pytest 额外参数
  tests/evals/test_tool.py::test_case[claude-sonnet-4-6]  # 具体 case
```

**关键设计**：每个 case 单独运行一次 pytest 进程。虽然比批量运行慢，但：
- 每个 case 的产物（logs、summary、junit、traces）独立存储
- 一个 case 崩溃不影响其他 case
- 每个 case 有独立的 artifacts_dir，便于外层 Agent 查看具体失败原因

### 2.2 环境变量设置

```python
def _build_env(self, *, experiment, variant_path, runtime_dir):
    env = os.environ.copy()
    env[VARIANT_ENV] = str(variant_path)           # Variant 注入路径
    env["PYTHONPATH"] = prepend_pythonpath([       # 三层 PYTHONPATH
        runtime_dir,                               # sitecustomize.py
        self.repo_root,                            # better_harness 包
        experiment.workspace_root,                 # 目标 Agent workspace
    ], env.get("PYTHONPATH"))
    env.setdefault("LANGSMITH_TEST_SUITE",         # LangSmith 测试套件名
                   f"better-harness-{experiment.name}")
    return env
```

`LANGSMITH_TEST_SUITE` 的作用：LangSmith 会把这个测试套件的所有运行 Trace 归组在一起，便于跨版本比较。

### 2.3 文件注入（workspace_file）

```python
with workspace_override_context(experiment.workspace_root, variant.file_overrides()):
    for case in experiment.cases_for_split(split):
        # 在此上下文中运行每个 case
        completed = subprocess.run(command, ...)
```

注意：`workspace_override_context` 包裹了整个 split 的所有 case，而不是每个 case 单独包裹。这意味着：
- 所有 case 共享同一份文件修改
- 整个 split 跑完后才恢复文件
- 减少了频繁的文件 I/O

### 2.4 case 级别的产物

每个 case 运行后产生以下文件：

```
split_dir/
└── cases/
    └── tests-evals-test-tool-py--test-case-claude-sonnet-4-6/  ← safe_slug()
        ├── command.json        # 完整的运行命令（shell 格式 + JSON 格式）
        ├── stdout.log          # pytest 标准输出
        ├── stderr.log          # pytest 标准错误
        ├── junit.xml           # JUnit 结果
        ├── summary.json        # 结构化评估结果
        ├── trace_refs.json     # 提取到的 Trace URL
        ├── trace_refs.md       # Trace URL 的 Markdown 版
        └── traces/langsmith/   # 拉取的 LangSmith Trace 内容（如有 API key）
            └── <uuid>.json
```

### 2.5 结果解析：parse_pytest_outcomes()

```python
def parse_pytest_outcomes(junit_path, cases, model, artifacts_dir):
    root = ET.fromstring(junit_path.read_text())
    configured = {case.render(model=model): case for case in cases}
    
    for testcase in root.iter("testcase"):
        # rebuild_case_id: 从 JUnit XML 的 file/classname/name 字段重建 nodeid
        case_id = rebuild_case_id(file_attr, classname_attr, name_attr)
        # 检查 <failure>/<error>/<skipped> 标签确定状态
        status = "passed" | "failed" | "skipped"
```

`rebuild_case_id()` 是一个 best-effort 重建函数，处理 pytest 和 JUnit XML 之间的字段映射：
- 有 `file` 属性：`{file}::{name}`
- classname 以 `tests.` 开头：转换为路径格式 `{classname.replace('.','/')}.py::{name}`
- 其他：直接用 name

对于 JUnit XML 中找不到对应的 case，会生成 `status="missing"` 的 CaseOutcome。

---

## 三、HarborRunner：Harbor 沙盒执行器

### 3.1 Harbor 是什么

Harbor 是 LangChain 用于运行 TerminalBench 等编程任务的沙盒框架，每个 task 在一个独立的容器/沙盒环境中运行，适合需要文件系统交互的复杂任务。

### 3.2 命令格式

```bash
harbor run \
  -p /path/to/tasks_root \    # 任务定义目录
  --task-name task_name \     # 具体任务名
  -l 1 \                      # 最大重试次数
  -n 1 \                      # 并发数
  -o /path/to/jobs_dir \      # 输出目录
  --job-name case_slug
```

### 3.3 结果解析：parse_harbor_case()

Harbor 任务结果有两种格式（按优先级）：

```python
def parse_harbor_case(jobs_dir, pass_threshold):
    # 方式1：result.json（结构化结果）
    json_paths = sorted(jobs_dir.rglob("result.json"))
    if json_paths:
        payload = json.loads(json_paths[0].read_text())
        score = float(payload.get("score", payload.get("reward", 0.0)))
        return score, payload, failure_message

    # 方式2：reward.txt（简单数值）
    reward_paths = sorted(jobs_dir.rglob("reward.txt"))
    if reward_paths:
        score = float(reward_paths[0].read_text().strip())
        return score, {"score": score}, failure_message

    # 方式3：都没有 → 失败
    return 0.0, None, "missing Harbor result files"
```

`pass_threshold`（默认 1.0）：score 达到或超过此值才算 passed。支持部分分场景（如 60% 正确算通过）。

### 3.4 Harbor 的文件注入

Harbor 任务在独立沙盒中运行，workspace_override_context 在沙盒外执行：

```python
with workspace_override_context(experiment.workspace_root, variant.file_overrides()):
    completed = subprocess.run(command, ...)  # 运行 harbor
```

Harbor 会把 workspace 挂载到沙盒中，所以外层的文件替换对沙盒内是可见的。

---

## 四、safe_slug()：文件系统安全的路径

```python
def safe_slug(value: str) -> str:
    cleaned = [c if c.isalnum() else "-" for c in value]
    slug = "".join(cleaned).strip("-")
    return slug or "case"
```

把 pytest nodeid（如 `tests/evals/test_tool.py::test_case[claude-sonnet-4-6]`）转换成安全的目录名（如 `tests-evals-test-tool-py--test-case-claude-sonnet-4-6`）。

---

## 五、Trace 收集（两个 Runner 共用）

两个 Runner 在每个 case 运行后都会调用：

```python
trace_refs = extract_trace_refs(
    payload=summary_payload,  # 从结构化结果中扫描 URL
    stdout=completed.stdout,  # 从 stdout 扫描 URL
    stderr=completed.stderr,  # 从 stderr 扫描 URL
)
write_trace_refs(case_dir, trace_refs)
```

如果环境变量 `LANGSMITH_API_KEY` 存在，还会自动调用 LangSmith API 拉取完整 Trace 内容。

---

## 六、reuse_existing：增量运行

```python
def run_split(..., reuse_existing=False):
    result_path = split_dir / "result.json"
    if reuse_existing and result_path.exists():
        return SplitResult.load(result_path)
    # 否则正常运行
```

使用 `--reuse-existing` 参数时，如果某个 split 的结果文件已存在，直接加载复用，不重新运行 Eval。适用场景：
- 调试时只想重跑某一步
- 网络问题导致 Eval 中断后续运行
- baseline 结果已有，不想浪费计算资源

---

## 七、运行产物完整结构

```
split_dir/                          ← split 级别
├── result.json                     # SplitResult 序列化
├── summary.json                    # 通过/失败/跳过统计
├── stdout.log                      # 所有 case 的 stdout 汇总
├── stderr.log                      # 所有 case 的 stderr 汇总
└── cases/
    └── <case-slug>/                ← case 级别
        ├── command.json            # 运行命令
        ├── stdout.log
        ├── stderr.log
        ├── junit.xml               # Pytest 专用
        ├── summary.json            # 结构化结果
        ├── trace_refs.json
        ├── trace_refs.md
        └── traces/langsmith/
            └── <uuid>.json
```

---

## 八、设计要点总结

| 设计决策 | 原因 |
|----------|------|
| 每个 case 单独起一个 pytest 进程 | 隔离崩溃，独立产物，便于调试 |
| workspace_override_context 包裹整个 split | 减少文件 I/O，性能更好 |
| Trace URL 自动收集 | 为外层 Agent 提供诊断素材 |
| 两种 Harbor 结果格式支持 | 兼容不同版本/配置的 Harbor |
| reuse_existing 参数 | 支持断点续运行，开发调试友好 |
| summary.json 双重保障 | 即使 eval 框架没生成 summary，也会从 junit.xml 补充推断一个 |
