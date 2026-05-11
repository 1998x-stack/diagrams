# The Anatomy of an Agent Harness

> 解读 LangChain 官方博客文章 — [The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness)  
> 作者: Vivek Trivedy | 日期: March 10, 2026

---

## TL;DR

**Agent = Model + Harness**

- **Model** 包含智能（intelligence）
- **Harness** 让智能变得有用（makes intelligence useful）
- 如果你不是模型，你就是 Harness

---

## 核心观点

> A raw model is not an agent. But it becomes one when a harness gives it things like **state, tool execution, feedback loops, and enforceable constraints**.

Harness 包含一切非模型的代码、配置和执行逻辑：

| 组件 | 说明 |
|------|------|
| 1️⃣ System Prompts | 指令与约束 |
| 2️⃣ Tools / Skills / MCPs | 能力及其描述 |
| 3️⃣ Infrastructure | 文件系统、沙箱、浏览器 |
| 4️⃣ Orchestration | 子代理、交接、路由 |
| 5️⃣ Hooks / Middleware | 压缩、续接、lint 检查 |

---

## 模型局限性 → Harness 解决方案

| 模型做不到 | Harness 如何解决 |
|-----------|-----------------|
| ❌ 跨交互保持持久状态 | ✅ while 循环 + 消息追踪 |
| ❌ 执行代码 | ✅ Bash 工具 |
| ❌ 获取实时知识 | ✅ Web 搜索 |
| ❌ 搭建环境/安装依赖 | ✅ 沙箱环境 |

---

## 6 大核心原语

### 1. 📁 Filesystem（最基础原语）
- Agent 工作区（读写数据、代码、文档）
- 增量工作卸载（不必全放上下文）
- 多 Agent + 人类协作表面
- Git 版本控制（追踪、回滚、分支实验）

### 2. 💻 Bash + Code Exec
- 给模型一台"电脑"，让它自主解决问题
- 从"只会说话"到"能动手干活"

### 3. 🏗️ Sandboxes
- 安全运行环境（不直接本地执行）
- 浏览器、日志、截图、测试运行器
- 让 Agent 能观察和分析工作

### 4. 🧠 Memory & Search（持续学习）
- 文件系统作为核心记忆原语
- AGENTS.md 标准：启动时注入上下文
- Agent 编辑后，下次自动加载 → 跨会话知识持久化

### 5. 📉 Battling Context Rot
- **Context Rot**: 上下文窗口填满后推理能力下降
- **Compaction**: 窗口快满时如何处理
- **Tool call offloading**: 减少大工具输出影响
- **Skills**: 避免启动时加载过多工具

### 6. 🔄 Long-Horizon Execution
- **Filesystem + Git**: 跨会话追踪工作
- **Ralph Loops**: 拦截模型退出，干净窗口重新注入 prompt
- **Planning + Self-verification**: 目标拆解 + 测试验证

---

## Harness 的未来

### 训练与 Harness 的耦合

Agent 产品（Claude Code, Codex）在**后训练**阶段就把模型和 Harness 纳入循环：
> 有用的原语被发现 → 加入 Harness → 用于下一代模型训练

### ⚡ 关键发现

> **最好的 Harness ≠ 模型后训练时用的 Harness**

Terminal Bench 2.0 上，仅换 Harness，Opus 4.6 从 **Top 30 → Top 5**。

### 开放问题
- 🤖 数百 Agent 并行协作同一代码库
- 🔍 Agent 分析自身轨迹，修复 Harness 级故障
- ⚡ JIT 动态组装工具和上下文

---

## Diagrams

本目录包含 7 张图解（`.drawio` 格式）：

| # | 文件 | 内容 |
|---|------|------|
| 1 | [01-agent-architecture.drawio](diagrams/01-agent-architecture.drawio) | Agent = Model + Harness 架构总览 |
| 2 | [02-harness-components.drawio](diagrams/02-harness-components.drawio) | 5 大 Harness 组件详细拆解 |
| 3 | [03-core-primitives.drawio](diagrams/03-core-primitives.drawio) | 6 大核心原语 + 开放问题 |
| 4 | [04-long-horizon.drawio](diagrams/04-long-horizon.drawio) | Ralph Loop 长周期执行流程 |
| 5 | [05-future-harness.drawio](diagrams/05-future-harness.drawio) | Harness 演化时间线 |
| 6 | [06-context-rot.drawio](diagrams/06-context-rot.drawio) | Context Rot 问题与 3 种解决方案 |
| 7 | [07-memory-search.drawio](diagrams/07-memory-search.drawio) | 记忆与搜索的持续学习循环 |

### 在线查看

```
https://app.diagrams.net/#Uhttps://raw.githubusercontent.com/1998x-stack/diagrams/main/agent-harness/01-agent-architecture.drawio
```

---

*Generated: 2026-05-11 | OpenClaw Workspace*
