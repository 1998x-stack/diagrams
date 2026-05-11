# DeepSeek TUI — 终端 Coding Agent

> 项目：[Hmbown/DeepSeek-TUI](https://github.com/Hmbown/DeepSeek-TUI)  
> Stars：20,956+  
> 已克隆至：`~/Documents/DeepSeek-TUI/`

---

## 一句话总结

DeepSeek V4 的**终端原生 Coding Agent**，支持流式推理块、文件编辑审批、Git 管理、Web 搜索、子 Agent 协调，提供 Plan/Agent/YOLO 三种模式，支持自动模型/思考级别选择。

## 核心特性

| 特性 | 说明 |
|------|------|
| 模型支持 | deepseek-v4-flash / deepseek-v4-pro，1M 上下文 |
| Auto 模式 | `--model auto` 自动选择模型 + 思考级别 |
| 推理流式 | 实时显示 DeepSeek reasoning blocks |
| 工具套件 | 文件操作、Shell、Git、Web 搜索、apply-patch、子 Agent、MCP |
| 三种模式 | Plan(只读) / Agent(交互式) / YOLO(全自动) |
| 思考级别 | Shift+Tab 切换 off → high → max |
| 会话管理 | 保存/恢复、fork 会话、工作区回滚 |
| LSP 诊断 | 每次编辑后内联显示 rust-analyzer/pyright 等诊断 |
| MCP 协议 | 连接 Model Context Protocol 服务器扩展工具 |
| 多语言 UI | en / ja / zh-Hans / pt-BR，自动检测 |
| 成本追踪 | 每轮和会话级 token 用量 + 费用估算 |
|  Skills | 可组合、可安装的技能包 |

## 安装方式

### 方式一：npm（最简单）

```bash
npm install -g deepseek-tui
deepseek --version
```

### 方式二：Homebrew（macOS 推荐）

```bash
brew tap Hmbown/deepseek-tui
brew install deepseek-tui
```

### 方式三：Cargo（Rust 工具链）

```bash
cargo install deepseek-tui-cli --locked  # deepseek 入口命令
cargo install deepseek-tui --locked      # deepseek-tui TUI 运行时
```

### 方式四：直接下载

从 [GitHub Releases](https://github.com/Hmbown/DeepSeek-TUI/releases) 下载 macOS ARM64 预编译二进制。

### 方式五：Docker

```bash
docker run --rm -it \
  -e DEEPSEEK_API_KEY \
  -v "$PWD:/workspace" \
  ghcr.io/hmbown/deepseek-tui:latest
```

## 配置

### API Key 设置

```bash
# 交互式（推荐）
deepseek auth set --provider deepseek

# 环境变量
export DEEPSEEK_API_KEY="sk-xxx"

# 验证
deepseek doctor
```

Key 保存在 `~/.deepseek/config.toml`。

### 多 Provider 支持

```bash
# DeepSeek 官方
deepseek auth set --provider deepseek --api-key "xxx"
deepseek

# OpenAI 兼容端点
deepseek auth set --provider openai --api-key "xxx"
OPENAI_BASE_URL="https://xxx.example/v1" deepseek --provider openai

# Ollama 本地
ollama pull deepseek-coder:1.3b
deepseek --provider ollama --model deepseek-coder:1.3b

# vLLM / SGLang 自托管
VLLM_BASE_URL="http://localhost:8000/v1" deepseek --provider vllm
```

## 使用

### 基本使用

```bash
# 交互式 TUI
deepseek

# 单次问答
deepseek "explain this function"

# 指定模型
deepseek --model deepseek-v4-flash "summarize"

# 自动选择模型 + 思考级别
deepseek --model auto "fix this bug"

# 全自动模式（无需审批）
deepseek --yolo
```

### Auto 模式原理

```
用户请求
  ↓
小型 deepseek-v4-flash 路由调用（thinking off）
  ↓
根据请求复杂度选择：
  - 简单 → flash + thinking off
  - 编码/调试 → pro + thinking high
  - 架构/安全审查 → pro + thinking max
  ↓
实际模型执行，TUI 显示选中的路由
```

Auto 模式是 DeepSeek TUI 本地的，上游 API 永远不会收到 `model: "auto"`。

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Tab | 补全 / 队列草稿 |
| Shift+Tab | 切换推理级别 |
| F1 | 帮助 |
| Ctrl+K | 命令面板 |
| Ctrl+R | 恢复会话 |
| @path | 附加文件上下文 |

完整快捷键：[docs/KEYBINDINGS.md](https://github.com/Hmbown/DeepSeek-TUI/blob/main/docs/KEYBINDINGS.md)

## 与 ds4.c 配合使用

如果你的 ds4-server 已经在本地运行，DeepSeek TUI 可以通过 OpenAI 兼容端点连接：

```bash
export DEEPSEEK_PROVIDER=openai
export OPENAI_BASE_URL="http://127.0.0.1:8000/v1"
export OPENAI_API_KEY="dsv4-local"
export OPENAI_MODEL="deepseek-v4-flash"
deepseek --provider openai --model deepseek-v4-flash
```

## API 定价（截至文档发布时）

| 模型 | 上下文 | 缓存命中输入 | 缓存未命中输入 | 输出 |
|------|--------|-------------|---------------|------|
| deepseek-v4-pro | 1M | $0.003625/1M* | $0.435/1M* | $0.87/1M* |
| deepseek-v4-flash | 1M | $0.0028/1M | $0.14/1M | $0.28/1M |

\* DeepSeek Pro 当前有 75% 限时折扣，截至 2026-05-31 15:59 UTC。

## 集成场景

| 场景 | 命令 |
|------|------|
| Zed 编辑器 | `deepseek serve --acp` |
| HTTP API 服务器 | `deepseek serve --http` |
| MCP 服务器 | `deepseek mcp-server` |
| PR 审查 | `deepseek pr <N>` |

## 项目架构

```
deepseek (CLI 入口)
  ↓ 委派给
deepseek-tui (TUI 运行时)
  ↓ ratatui 界面
async engine ↔ OpenAI 兼容流式客户端
  ↓ 工具调用路由
tool registry: shell / file / git / web / sub-agents / MCP / RLM
```

两个二进制都需要：`deepseek`（调度器）和 `deepseek-tui`（界面）。

## 硬件要求

DeepSeek TUI 本身是**纯客户端**，只负责终端界面和工具协调，**不跑模型推理**。

- **内存**：无特殊要求，几十 MB 即可
- **CPU**：无特殊要求
- **依赖**：仅依赖 API 连接（云端 DeepSeek API 或本地 Ollama/ds4-server）

**你的 M4 Max 64GB 机器完全可以运行 DeepSeek TUI。** 瓶颈在于 API 调用费用和本地模型的可用性（如果选择 Ollama 本地小模型）。

## 中国大陆优化

```bash
# npm 镜像
npm install -g deepseek-tui --registry=https://registry.npmmirror.com

# Cargo 镜像 (~/.cargo/config.toml)
[source.crates-io]
replace-with = "tuna"
[source.tuna]
registry = "sparse+https://mirrors.tuna.tsinghua.edu.cn/crates.io-index/"
```

## 与 OpenClaw 的关系

DeepSeek TUI 可以作为 OpenClaw 的一个**独立终端工具**使用：
- 在终端里直接运行 `deepseek` 进行代码辅助
- 通过 `deepseek serve --acp` 接入 Zed 等编辑器
- 通过 HTTP API 与 OpenClaw 的 agent 交互
- 两者共享 Skills 系统（`~/.agents/skills/`）
