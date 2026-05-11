# meta_workflow — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_mw_bare_build_command` | Bare Build Command — Execute Build Only | operational | 1x: 9dc56f96 | `intent:meta_workflow`, `target:build_config`, `single_word_command` |

---

## `gene_mw_bare_build_command`

**裸build命令执行** / Bare Build Command — Execute Build Only

Category: `operational`

**Signals:**
- `intent:meta_workflow`
- `target:build_config`
- `single_word_command`
- `build_keyword`

**Preconditions:**
- 用户仅输入'build'，无其他上下文或说明。
- 通常出现在：前一轮修改后忘记build、想手动确认最新状态、准备开始新阶段的工作前。
- 极低步骤任务（2步）：调用build工具→返回结果。

**Evidence:** Single-word 'build' command, 2 steps total. User wanted manual build verification between audio work and level data injection phases.

---
