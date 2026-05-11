# patching.py 深度解析：Surface 注入机制

> 文件：`better_harness/patching.py`
> 行数：约 90 行
> 定位：系统的"效果执行层"——负责把外层 Agent 提出的 Harness 修改，真正注入到目标 Agent 运行环境中

---

## 一、核心问题

外层 Agent 编辑了 Proposer Workspace 里的文件，但被测试的内层 Agent 运行在完全不同的进程/环境中。

**如何让内层 Agent 用上修改后的 Harness 值？**

patching.py 解决的就是这个问题，提供了两种注入机制。

---

## 二、两种注入机制

### 2.1 module_attr：修改 Python 模块属性

用于修改 Prompt 字符串等 Python 模块级别的常量：

```python
def patch_module_attrs(overrides: dict[str, str]) -> None:
    for target, value in overrides.items():
        # target 格式: "deepagents.graph:BASE_AGENT_PROMPT"
        module_name, _, attribute = target.partition(":")
        module = importlib.import_module(module_name)
        setattr(module, attribute, value)
```

**工作原理**：
1. 解析 `module:attribute` 格式的 target
2. 动态导入模块
3. 用 `setattr` 替换模块属性的值

**触发时机**：在 pytest 启动时，通过 `sitecustomize.py` 自动调用（见下文）。

### 2.2 workspace_file：临时替换工作区文件

用于修改工具代码、Middleware 实现等实际文件：

```python
@contextlib.contextmanager
def workspace_override_context(workspace_root, overrides):
    backups: dict[Path, str | None] = {}
    try:
        for relative_path, value in overrides.items():
            target = workspace_root / relative_path
            # 备份原文件（或记录不存在）
            backups[target] = target.read_text() if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value)
        yield  # 在此期间运行 Eval
    finally:
        # 恢复所有文件
        for target, original in backups.items():
            if original is None:
                if target.exists():
                    target.unlink()  # 原本不存在的，删掉临时文件
            else:
                target.write_text(original)  # 恢复原内容
```

**设计亮点**：
- 使用 context manager，保证即使 Eval 崩溃也能恢复文件
- 支持新建文件（原本不存在的文件在退出后自动删除）
- 每个 case 运行前设置，运行后恢复，完全隔离

---

## 三、运行时注入链路

整个注入链路的关键是 `sitecustomize.py`：

### 3.1 sitecustomize.py 是什么？

Python 在解释器启动时会自动寻找并执行 `sitecustomize.py`，早于任何用户代码。这是 Python 提供的最早期钩子。

### 3.2 better-harness 的利用方式

```python
def ensure_sitecustomize(runtime_dir: Path) -> Path:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    sitecustomize_path = runtime_dir / "sitecustomize.py"
    sitecustomize_path.write_text(
        "from better_harness.patching import patch_from_env\n"
        "patch_from_env()\n"
    )
    return runtime_dir
```

生成的 `sitecustomize.py` 只做一件事：调用 `patch_from_env()`。

### 3.3 patch_from_env()

```python
VARIANT_ENV = "BETTER_HARNESS_VARIANT_FILE"

def patch_from_env() -> None:
    raw_path = os.environ.get(VARIANT_ENV)
    if not raw_path:
        return
    variant = Variant.load(Path(raw_path))
    patch_module_attrs(variant.attr_overrides())
```

通过环境变量 `BETTER_HARNESS_VARIANT_FILE` 找到当前 Variant 的 JSON 文件，加载它，提取所有 `module_attr` 类型的 surface 值，并注入到模块中。

### 3.4 完整注入链路（module_attr）

```
runner.py 启动 pytest 子进程
    ↓ 设置 BETTER_HARNESS_VARIANT_FILE=/path/to/iter-001.json 环境变量
    ↓ 设置 PYTHONPATH 包含 runtime_dir（含 sitecustomize.py）
        ↓
Python 解释器启动
    ↓ 自动执行 sitecustomize.py
    ↓ 调用 patch_from_env()
    ↓ 读取 iter-001.json
    ↓ setattr(deepagents.graph, "BASE_AGENT_PROMPT", <new prompt>)
        ↓
pytest 运行 test cases
    ↓ test 创建 Agent，Agent 读取 deepagents.graph.BASE_AGENT_PROMPT
    ↓ 此时已是修改后的值
```

### 3.5 完整注入链路（workspace_file）

```
runner.py 运行每个 case 前
    ↓ with workspace_override_context(workspace_root, variant.file_overrides()):
    ↓   临时用修改后的代码替换 libs/deepagents/deepagents/custom_tools.py
        ↓
    pytest 运行 test case
        ↓ test 导入 custom_tools，此时是修改后的版本
        ↓
    ↓ context manager 退出，自动恢复文件
```

---

## 四、VARIANT_ENV + sitecustomize 的设计价值

这个设计的精妙之处：

1. **无侵入**：内层 Agent 和 Eval 代码完全不知道自己在被优化循环控制，不需要修改任何被测代码
2. **早期注入**：sitecustomize 在 Python 启动时就运行，早于所有 import，确保模块被导入时就已经是修改后的版本
3. **环境变量传递**：Variant 文件路径通过环境变量传递，subprocess 隔离中也能正常工作
4. **可复现**：每个 Variant 对应一个 JSON 文件，随时可以重新注入同一套值

---

## 五、PYTHONPATH 管理

```python
def prepend_pythonpath(paths: list[Path], existing: str | None) -> str:
    parts = [str(path) for path in paths]
    if existing:
        parts.append(existing)
    return os.pathsep.join(parts)
```

Runner 会把以下路径放到 PYTHONPATH 最前面：
1. `runtime_dir`（含 sitecustomize.py）← **必须最先**，确保 sitecustomize 被找到
2. `repo_root`（better-harness 包本身）
3. `experiment.workspace_root`（目标 Agent 的 workspace）

---

## 六、pytest 插件入口

```python
# better_harness_plugin.py
from better_harness import patch_from_env
patch_from_env()
```

这是通过 `-p better_harness_plugin` 参数加载的 pytest 插件。它是 sitecustomize 方式的备选/补充——如果 sitecustomize 没有被执行（某些特殊环境），这个插件会在 pytest 启动早期同样调用 `patch_from_env()`。

---

## 七、build_baseline_variant() 和 build_variant()

```python
def build_baseline_variant(experiment: Experiment) -> Variant:
    values = {name: surface.base_value for name, surface in experiment.surfaces.items()}
    return Variant(label="baseline", model=experiment.model, changed_surfaces=(), ...)

def build_variant(*, experiment, label, values) -> Variant:
    changed_surfaces = tuple(
        name for name, surface in experiment.surfaces.items()
        if values[name] != surface.base_value  # 与基准值比较，不是与当前值比较
    )
    return Variant(label=label, ...)
```

**注意**：`changed_surfaces` 记录的是**与基准（baseline）的差异**，而不是与上一轮的差异。这意味着：

- 即使迭代了多轮，`changed_surfaces` 始终反映与原始 base_value 的累积差距
- 如果某轮改了某个 surface 之后，下一轮又改回来，该 surface 会从 `changed_surfaces` 中消失

---

## 八、设计要点总结

| 设计决策 | 原因 |
|----------|------|
| sitecustomize.py + VARIANT_ENV | 对被测代码零侵入，最早期注入 |
| context manager 替换文件 | 保证 Eval 结束后文件状态完全恢复 |
| 两种注入方式并存 | 覆盖所有场景：静态 Prompt 常量 + 动态代码文件 |
| 环境变量传递 Variant 路径 | subprocess 隔离中也能正常工作 |
| changed_surfaces 对比基准 | 清晰反映累积优化量 |
