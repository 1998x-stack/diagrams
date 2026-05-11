# Claude Code 源码阅读笔记：Memory 系统深度解析

> 基于 `~/Desktop/codes/claude-code` 源码梳理，共 1858 个 TypeScript/TSX 文件。
> 本文聚焦 Memory 子系统，涵盖架构、数据流、存储结构、类型分类、自动化机制等核心内容。

---

## 一、整体组件地图

先看整个代码库有哪些一级模块：

| 目录/文件 | 职责 |
|-----------|------|
| `memdir/` | Memory 核心引擎：路径、类型、扫描、相关性、截断 |
| `services/SessionMemory/` | 会话内存：自动周期性提取当前对话的关键信息 |
| `services/extractMemories/` | 回合结束时的后台记忆提取（forked agent 模式）|
| `services/autoDream/` | 自动梦境整合：跨 session 定期蒸馏记忆 |
| `services/teamMemorySync/` | 团队记忆同步：与 Anthropic API 做 Git-repo 级别共享 |
| `components/memory/` | UI 组件：`MemoryFileSelector`（/memory 命令界面）、`MemoryUpdateNotification` |
| `commands/memory/` | `/memory` 命令入口 |
| `skills/bundled/remember.ts` | `/remember` skill：审查记忆并提出整理建议 |
| `tools/AgentTool/agentMemory.ts` | Agent 级别的独立记忆目录 |
| `utils/memory/` | 工具函数（版本检测等）|

---

## 二、Memory 的种类（存储层次）

Claude Code 有 **五层**记忆存储，各自位置和生命周期不同：

```
~/.claude/CLAUDE.md                      ← 用户全局指令（User memory）
./CLAUDE.md                              ← 项目级指令（Project memory，可 git 提交）
./CLAUDE.local.md                        ← 项目级私人指令（不提交）
~/.claude/projects/<sanitized-path>/memory/   ← Auto Memory（自动记忆）
  MEMORY.md                              ← 索引文件（入口，自动注入 context）
  <topic>.md                             ← 主题记忆文件
  logs/YYYY/MM/YYYY-MM-DD.md            ← KAIROS 模式下的日记（仅 assistant 长会话）
  team/                                  ← Team Memory（共享记忆）
```

---

## 三、Memory 类型分类系统

源文件：`memdir/memoryTypes.ts`

记忆被强制约束在四种类型中，避免保存可以从代码/git 推导出的信息：

| 类型 | 适用内容 | 存储作用域 |
|------|----------|-----------|
| **user** | 用户角色、目标、技能偏好 | 始终私有 |
| **feedback** | 用户对 Claude 行为的纠正或肯定 | 私有（团队惯例可共享）|
| **project** | 进行中的工作、目标、截止日期、事件 | 倾向共享 |
| **reference** | 外部系统的指针（Linear、Grafana、Slack 等）| 通常共享 |

**明确禁止保存的内容**（直接来自源码注释）：
- 代码模式、架构、文件路径——可以用 grep/读文件推导
- git 历史、谁改了什么——`git log` 是权威来源
- 调试方案或修复方案——已经在代码里
- CLAUDE.md 里已有的内容
- 临时任务状态、当前对话上下文

---

## 四、核心数据结构

### 4.1 Memory 文件格式（Frontmatter）

每个主题记忆文件都是带 frontmatter 的 Markdown：

```markdown
---
name: 用户偏好：不要摘要回复
description: 用户反馈，Claude 不应在每次回复末尾总结刚才做了什么
type: feedback
---

不要在回复末尾添加"我刚才做了……"这类总结。

**Why:** 用户说"我能看到 diff"，不需要重复。
**How to apply:** 所有回复，包括代码修改后的回复。
```

### 4.2 MEMORY.md 作为索引

`MEMORY.md` 是入口文件，只是**一行一条指针**的索引，不包含实际内容：

```markdown
- [用户偏好：不要摘要](feedback_no_summary.md) — 每次回复不要加总结
- [项目：Auth 中间件重写](project_auth_rewrite.md) — 合规驱动，非技术债
```

**截断规则**（`memdir/memdir.ts`）：
- 最大 **200 行**
- 最大 **25,000 字节**（约 25KB）
- 超出时追加警告，提示用户保持索引简洁

### 4.3 MemoryHeader（扫描元数据）

```typescript
type MemoryHeader = {
  filename: string      // 相对路径
  filePath: string      // 绝对路径
  mtimeMs: number       // 修改时间（用于新鲜度判断）
  description: string | null  // frontmatter 的 description 字段
  type: MemoryType | undefined  // 四种类型之一
}
```

---

## 五、Auto Memory 的路径解析

源文件：`memdir/paths.ts`

路径解析优先级（第一个生效的优先）：

1. `CLAUDE_COWORK_MEMORY_PATH_OVERRIDE` 环境变量（Cowork 专用）
2. settings.json 的 `autoMemoryDirectory`（支持 `~/` 展开，仅 user/policy 级别可信）
3. 默认路径：`~/.claude/projects/<sanitized-git-root>/memory/`

**开关优先级**：
1. `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` → 关闭
2. `CLAUDE_CODE_SIMPLE` (--bare 模式) → 关闭
3. CCR 远程模式且无 `CLAUDE_CODE_REMOTE_MEMORY_DIR` → 关闭
4. settings.json `autoMemoryEnabled: false` → 关闭
5. 默认：**开启**

**安全校验**：路径有严格白名单过滤，拒绝相对路径、UNC 路径、null 字节、根目录等危险路径。

---

## 六、记忆召回机制：相关性选择

源文件：`memdir/findRelevantMemories.ts`

**流程**：

```
用户输入 query
    ↓
scanMemoryFiles()：扫描 memory 目录所有 .md（排除 MEMORY.md）
    ↓ 返回 MemoryHeader[] 按 mtime 降序，最多 200 个
过滤掉已在本轮 context 中展示过的文件
    ↓
调用 sideQuery（Sonnet 模型）：根据 query + 文件描述列表，选出最相关的文件名
    ↓ 最多选 5 个
返回 { path, mtimeMs }[]
```

**Selector 的 system prompt 关键约束**：
- 只选「明确有用」的记忆，不确定就不选
- 如果模型正在使用某个工具（如 `mcp__X__spawn`），不选那个工具的参考文档（避免噪音），但**要**选包含该工具 gotcha 的记忆

---

## 七、记忆新鲜度系统

源文件：`memdir/memoryAge.ts`

每条记忆被加载时，会根据 mtime 附加新鲜度标注：

```
≤1 天：不附加警告（fresh）
2+ 天：附加 <system-reminder>This memory is X days old...</system-reminder>
```

警告文本强调：记忆是**某时刻的快照**，代码引用（file:line）可能已失效，建议在实际使用前验证当前状态。

---

## 八、会话记忆（Session Memory）

源文件：`services/SessionMemory/sessionMemory.ts`

**用途**：在单次长对话中，周期性地将对话关键信息提取为结构化笔记，用于支撑 autoCompact（上下文压缩）。

**触发条件**（需同时满足）：
1. Context token 数达到初始化阈值
2. 距上次提取后 token 增量超过 `minimumTokensBetweenUpdate`
3. 距上次提取后 tool call 数超过 `toolCallsBetweenUpdates`
4. 或：token 阈值达到 + 最后一个 assistant turn 无 tool call（自然对话断点）

**执行方式**：`runForkedAgent()`（完美 fork 主对话，共享 prompt cache），在隔离上下文里读取会话文件、写入 session memory 文件，不污染主会话状态。

**存储位置**：会话目录内，不同于 auto memory，仅对当前 session 有效。

---

## 九、回合结束记忆提取（extractMemories）

源文件：`services/extractMemories/extractMemories.ts`

**用途**：在每次完整的 query 回合结束时（模型返回无 tool call 的最终回复后），后台自动判断是否需要提取持久记忆。

**执行逻辑**：
1. 检查 feature flag `EXTRACT_MEMORIES`
2. 统计自上次提取后的对话轮数
3. 检查主 agent 是否已经自己写了记忆（`hasMemoryWritesSince`）——若是则跳过，避免重复
4. 用 `runForkedAgent()` 跑提取任务：分析对话 → 写入 auto memory 目录
5. 更新游标，标记已处理范围

---

## 十、AutoDream：跨 Session 蒸馏

源文件：`services/autoDream/autoDream.ts`

**用途**：定期（默认 24h 间隔、累积 5+ 个 session 后）触发 `/dream` skill，将 auto memory 的日志文件蒸馏整合成主题文件 + 更新 `MEMORY.md`。

**触发门控（从便宜到昂贵）**：
1. 时间门：距上次整合 ≥ `minHours`（stat 操作）
2. Session 门：`mtime > lastConsolidatedAt` 的 transcript 数 ≥ `minSessions`
3. 锁：无其他进程正在整合（防并发）

**关闭条件**：KAIROS 模式（长会话模式）、远程模式、auto memory 未启用。

---

## 十一、Team Memory 同步

源文件：`services/teamMemorySync/index.ts`

**用途**：通过 Anthropic API，将团队记忆文件在同一 git repo 的所有成员间同步。

**API 接口**：
```
GET  /api/claude_code/team_memory?repo={owner/repo}         → 拉取全量
GET  /api/claude_code/team_memory?repo={owner/repo}&view=hashes → 仅哈希（增量检查）
PUT  /api/claude_code/team_memory?repo={owner/repo}         → 推送（upsert 语义）
```

**同步语义**：
- Pull：服务端内容覆盖本地（server wins）
- Push：只上传内容哈希变化的文件（delta 上传）
- **文件删除不传播**：本地删除不会从服务端移除，下次 pull 会恢复

**安全扫描**：推送前会扫描文件内容，拒绝包含 API key、token、密码等密钥的文件（`secretScanner.ts`）。

**per-file 大小限制**：250KB，超出跳过。

---

## 十二、UI 组件

### MemoryFileSelector (`components/memory/MemoryFileSelector.tsx`)

`/memory` 命令打开的交互界面，功能：
- 列出所有 CLAUDE.md 文件（User/Project/imported/@-include 层级）
- 显示 Auto Memory 文件夹入口
- 显示 Team Memory 文件夹入口（若启用）
- 显示各 Agent 的独立记忆文件夹
- 在顶部提供 **Auto-memory on/off** 和 **Auto-dream on/off** 开关

### MemoryUpdateNotification (`components/memory/MemoryUpdateNotification.tsx`)

记忆更新后显示的 inline 提示条：
```
Memory updated in ~/.../.../memory/feedback_no_summary.md · /memory to edit
```

---

## 十三、/remember Skill

源文件：`skills/bundled/remember.ts`

仅 Anthropic 内部（`USER_TYPE === 'ant'`）可用。

功能：审查所有记忆层（auto memory + CLAUDE.md + CLAUDE.local.md），提出：
1. **Promotions**：把 auto memory 里的条目移到 CLAUDE.md 或 CLAUDE.local.md
2. **Cleanup**：跨层重复、矛盾、过期条目
3. **Ambiguous**：不确定目标位置的，等用户决策
4. **No action**：保持原样的条目

**约定**：只提建议，不主动修改文件。

---

## 十四、记忆系统与其他持久化机制的边界

源码里明确区分了三种持久化工具的适用场景：

| 机制 | 适用场景 |
|------|----------|
| **Memory** | 跨对话的持久上下文：用户偏好、项目决策、外部资源位置 |
| **Plan** | 当前实现任务前与用户对齐方案；或中途变更方案时更新 |
| **Task** | 拆解当前对话内的工作步骤、追踪进度 |

Memory 明确**不应**用于：当前对话内的临时状态、任务步骤、进度追踪。

---

## 十五、数据流总览

```
用户输入
  │
  ├──► 启动时：loadMemoryPrompt()
  │       ├── 读 MEMORY.md（截断到200行/25KB）
  │       ├── 构建 buildMemoryLines()（指导 Claude 如何使用记忆）
  │       └── 注入 system prompt
  │
  ├──► 每个 query：findRelevantMemories(query, memoryDir)
  │       ├── scanMemoryFiles()：扫描所有 .md，读 frontmatter
  │       └── sideQuery(Sonnet)：选出最相关的 ≤5 个文件，附加新鲜度警告
  │
  ├──► 回合结束后（stopHooks）：extractMemories
  │       └── runForkedAgent()：分析对话 → 写主题文件 → 更新 MEMORY.md
  │
  ├──► 周期性（postSamplingHook）：SessionMemory
  │       └── runForkedAgent()：提取当前 session 关键信息到会话笔记
  │
  └──► 定期触发（24h/5 sessions）：autoDream
          └── /dream skill：整合 logs/ 日志 → 更新主题文件 + MEMORY.md
```

---

## 十六、值得关注的设计细节

1. **forkedAgent 模式**：所有后台记忆操作（extract、session memory、dream）都用完美 fork 跑，与主对话共享 prompt cache，不污染主会话状态。

2. **工作区和 git 根绑定**：auto memory 路径用 `findCanonicalGitRoot()`，同一 repo 的所有 worktree 共享一个 memory 目录（避免因切 worktree 导致记忆分裂）。

3. **双重防重**：主 agent 写了记忆 → `hasMemoryWritesSince()` 检测到 → `extractMemories` 自动跳过，两者互斥，防止同一段对话被记两次。

4. **新鲜度警告的位置**：在 FileReadTool 输出里注入（`<system-reminder>...`），而不是在 system prompt 里，避免每次都占 token。

5. **MEMORY.md 的截断策略**：先按行截断（自然边界），再按字节截断（在最后一个换行符处），保证不切断一行中间。

6. **Team Memory 安全**：推送前密钥扫描 + per-file 大小限制 + 严格的 key path 校验（防路径穿越）。

---

*生成时间：2026-05-07 | 源码版本：claude-code @ ~/Desktop/codes/claude-code*
