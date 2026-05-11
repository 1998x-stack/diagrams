# draw.io MCP 安装与使用指南

> 创建时间: 2026-05-11 | OpenClaw v2026.5.7

## 是什么

[draw.io MCP](https://github.com/jgraph/drawio-mcp) 是 draw.io 官方的 MCP Server，让 LLM 能创建和编辑 diagram。

提供 **4 种方式**（选一种即可）：

| 方式 | 原理 | 适合场景 |
|------|------|----------|
| **MCP App Server** | 远程 HTTP 端点，图表 inline 渲染在对话中 | Claude.ai、VS Code、任何 MCP Apps host |
| **MCP Tool Server** | 本地 npm 包，直接在 draw.io 编辑器中打开 | Claude Desktop、任意 MCP 客户端 |
| **Skill + CLI** | 复制 skill 文件 + draw.io Desktop | Claude Code 本地开发 |
| **Project Instructions** | 纯指令方式，无需安装 | Claude.ai 项目 |

## 在 OpenClaw 中安装（推荐：MCP App Server）

### 前提条件

- 已安装 OpenClaw（v2026.5.7+）
- `openclaw` CLI 可用

### 步骤

```bash
# 1. 添加 draw.io MCP Server（使用官方远程端点，无需本地安装）
openclaw mcp set drawio '{"url":"https://mcp.draw.io/mcp","transport":"streamable-http"}'
```

这会在 `~/.openclaw/openclaw.json` 中写入：

```json
{
  "mcp": {
    "servers": {
      "drawio": {
        "url": "https://mcp.draw.io/mcp",
        "transport": "streamable-http"
      }
    }
  }
}
```

### 验证

```bash
openclaw mcp list
```

应看到 `drawio` 条目。

### 备用方案：本地 MCP Tool Server

如果远程端点不可用，可以用本地 npm 包：

```bash
# 本地安装
openclaw mcp set drawio '{"command":"npx","args":["@drawio/mcp"]}'
```

需要确保 Node.js 已安装且网络可达 npm。

## 使用方式

### 生成 .drawio 文件

让 AI 助手生成 diagram 时，会直接创建 `.drawio` XML 文件。文件可以直接在 draw.io 中打开编辑。

### 在线打开

```
https://app.diagrams.net/#U<raw-file-url>
```

例如：
```
https://app.diagrams.net/#Uhttps://raw.githubusercontent.com/1998x-stack/diagrams/main/transformer-architecture.drawio
```

### 推荐工作流

1. 让 AI 生成 `.drawio` 文件
2. 推送到 GitHub `diagrams` 仓库
3. 分享 `app.diagrams.net/#U...` 链接
4. 点链接直接在浏览器中打开/编辑

### 生成 draw.io 文件 + 导出 PNG/SVG/PDF

```bash
# 需要安装 draw.io Desktop CLI
# 默认生成 .drawio 文件
# 在请求中指定格式可导出：/drawio png ...
```

## GitHub 图仓库

我们建了一个专门的 diagrams 仓库：

- **仓库**: https://github.com/1998x-stack/diagrams
- **克隆**: `git clone git@github.com:1998x-stack/diagrams.git`

其他电脑只需：
1. 配置 OpenClaw MCP（见上文）
2. 确保有 GitHub SSH 访问权限
3. clone diagrams 仓库即可获取所有历史图文件

## 参考

- [draw.io MCP 官方仓库](https://github.com/jgraph/drawio-mcp)
- [MCP App Server 文档](https://github.com/jgraph/drawio-mcp/blob/main/mcp-app-server/README.md)
- [MCP Tool Server 文档](https://github.com/jgraph/drawio-mcp/blob/main/mcp-tool-server/README.md)
- [XML 生成参考](https://github.com/jgraph/drawio-mcp/blob/main/shared/xml-reference.md)
