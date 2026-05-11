# The Anatomy of an Agent Harness

> 解读 LangChain 官方博客文章 — [The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness)  
> 作者: Vivek Trivedy | 日期: March 10, 2026 | 阅读时间: 12 min

---

## TL;DR

**Agent = Model + Harness**

- **Model** 包含智能（intelligence）
- **Harness** 让智能变得有用（work engine）
- 如果你不是模型，你就是 Harness

---

## 核心论点

> "A raw model is not an agent. But it becomes one when a harness gives it things like state, tool execution, feedback loops, and enforceable constraints."

原始模型只能接收文本/图像/音频/视频，输出文本。Harness 工程就是围绕模型构建一切，使其成为工作引擎。

---

## 5 大 Harness 组件

| # | 组件 | 说明 |
|---|------|------|
| 1 | **System Prompts** | 指令与约束 |
| 2 | **Tools / Skills / MCPs** | 能力及其描述 |
| 3 | **Infrastructure** | 文件系统、沙箱、浏览器 |
| 4 | **Orchestration** | 子代理生成、交接、模型路由 |
| 5 | **Hooks / Middleware** | 压缩、续接、lint 检查等确定性执行 |

---

## 模型局限性 vs Harness 解决方案

| 模型无法做到 | Harness 如何解决 |
|-------------|-----------------|
| 跨交互保持持久状态 | while 循环 + 消息追踪 |
| 执行代码 | Bash 工具 |
| 获取实时知识 | Web 搜索 |
| 搭建环境/安装依赖 | 沙箱环境 |

---

## 6 大核心原语

### 1. 📁 Filesystem（最基础原语）

文件系统是 Harness 最根本的原语，因为它解锁了：
- Agent 工作区（读取数据、代码、文档）
- 增量工作卸载（不必全放上下文）
- 自然协作表面（多 Agent + 人类通过共享文件协调）
- Git 版本控制（追踪工作、回滚错误、分支实验）

### 2. 💻 Bash + Code Exec

给模型一台"电脑"，让它自主解决问题。编写和执行代码是迈向自主性的重大一步。

### 3. 🏗️ Sandboxes

安全运行环境。不在本地执行，而是连接到沙箱运行代码、检查文件、安装依赖。浏览器、日志、截图、测试运行器让 Agent 能观察和分析工作。

### 4. 🧠 Memory & Search

文件系统再次成为核心原语。Harness 支持 AGENTS.md 等记忆文件标准，在 Agent 启动时注入上下文。Agent 编辑后，下次启动自动加载更新内容 → 跨会话持续学习。

### 5. 📉 Battling Context Rot

**Context Rot（上下文退化）**: 随着上下文窗口填满，模型的推理和完成任务能力下降。

应对策略：
- **Compaction（压缩）**: 上下文窗口快满时如何处理
- **Tool call offloading**: 减少大工具输出的影响
- **Skills**: 避免启动时加载过多工具/MCP 到上下文

### 6. 🔄 Long-Horizon Autonomous Execution

长周期工作需要持久状态、规划、观察和验证：

- **Filesystem + Git**: 跨会话追踪工作
- **Ralph Loops**: 拦截模型退出尝试，在干净上下文窗口中重新注入原始 prompt
- **Planning + Self-verification**: 目标拆解 + 测试验证

---

## Harness 的未来

### 模型训练与 Harness 设计的耦合

今天的 Agent 产品（Claude Code、Codex）在**后训练阶段**就把模型和 Harness 纳入循环。这创建了反馈回路：发现有用的原语 → 加入 Harness → 用于下一代模型训练。

### ⚡ 关键发现

> **最好的 Harness 不一定是模型后训练时使用的那个。**

在 Terminal Bench 2.0 上，Claude Code 中的 Opus 4.6 远低于其他 Harness 中的 Opus 4.6。**仅更换 Harness，一个编码 Agent 就从 Top 30 冲到了 Top 5。**

### 开放问题

- 编排数百个 Agent 并行处理同一代码库
- Agent 分析自身轨迹，识别并修复 Harness 级故障模式
- JIT 动态组装正确的工具和上下文

---

## Diagrams

本目录包含以下图解（`.drawio` 格式，可在 draw.io 或 VS Code 中打开）：

| 文件 | 内容 |
|------|------|
| [01-agent-architecture.drawio](diagrams/01-agent-architecture.drawio) | Agent 架构总览：Model + Harness = Agent |
| [02-harness-components.drawio](diagrams/02-harness-components.drawio) | Harness 5 大组件详细拆解 |
| [03-core-primitives.drawio](diagrams/03-core-primitives.drawio) | 6 大核心原语 + 开放问题 |
| [04-long-horizon.drawio](diagrams/04-long-horizon.drawio) | Ralph Loop 长周期执行流程 |

---

## 在线查看

将 `.drawio` 文件推送到 GitHub 后，可通过以下链接在浏览器中查看：

```
https://app.diagrams.net/#Uhttps://raw.githubusercontent.com/1998x-stack/diagrams/main/agent-harness/01-agent-architecture.drawio
```

---

*Generated: 2026-05-11 | OpenClaw Workspace*
