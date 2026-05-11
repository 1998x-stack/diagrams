# Better-Harness 代码结构总览

> 源码路径：`~/Desktop/deepagents/examples/better-harness/`
> 分析时间：2026-05-07

---

## 文件结构

```
better-harness/
├── better_harness/
│   ├── __init__.py              # 包入口，导出 patch_from_env
│   ├── core.py                  # 数据模型 + 配置加载 + 主优化循环 + CLI
│   ├── agent.py                 # 外层 Deep Agent + Proposer Workspace 管理
│   ├── patching.py              # Harness Surface 注入机制
│   └── runners.py               # Eval 执行器（Pytest / Harbor）
├── better_harness_plugin.py     # pytest 插件入口
├── examples/
│   └── deepagents_example.toml  # 完整实验配置示例
└── tests/
    └── test_better_harness.py   # 单元测试
```

---

## 各文件职责速览

| 文件 | 核心职责 | 关键类/函数 |
|------|----------|-------------|
| `core.py` | 数据模型定义、配置加载、主优化循环 | `Experiment`、`Variant`、`SplitResult`、`run_experiment()` |
| `agent.py` | 外层 Agent 调用、Proposer Workspace 构建 | `propose_variant()`、`build_proposer_workspace()` |
| `patching.py` | Surface 值注入到目标 workspace | `patch_module_attrs()`、`workspace_override_context()` |
| `runners.py` | 执行 Eval、解析结果 | `PytestRunner`、`HarborRunner` |

---

## 四个核心概念

| 概念 | 含义 |
|------|------|
| **Experiment** | 实验配置实体，从 .toml 加载，描述目标 workspace、模型、Eval 集、Surfaces |
| **Surface** | 一个可编辑的 Harness 组件（Prompt 文本 / 工具文件 / 中间件代码） |
| **Variant** | 一个具体的 Harness 版本：各 Surface 的当前值 |
| **Split** | Eval 分组：`train`（可见，优化用）、`holdout`（隐藏，泛化检验）、`scorecard`（最终验收）|

---

## 详细分析文章

1. [`01-core.md`](./01-core.md) — 数据模型与主优化循环
2. [`02-agent.md`](./02-agent.md) — 外层 Agent 与 Proposer Workspace
3. [`03-patching.md`](./03-patching.md) — Surface 注入机制
4. [`04-runners.md`](./04-runners.md) — Eval 执行器
5. [`05-config.md`](./05-config.md) — 实验配置格式详解
