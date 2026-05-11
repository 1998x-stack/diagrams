# error_log_paste — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_elp_stacktrace_paste_diagnosis` | Error Log Stacktrace Paste — Direct Diagnosis From Crash Report | diagnostic | 1x: 374e4eb7 | `intent:error_log_paste`, `target:game_logic`, `stacktrace_in_prompt` |

---

## `gene_elp_stacktrace_paste_diagnosis`

**错误日志粘贴直接诊断** / Error Log Stacktrace Paste — Direct Diagnosis From Crash Report

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `target:game_logic`
- `stacktrace_in_prompt`
- `lua_error_keywords`
- `high_error_count`
- `mentions_specific_file:true`

**Preconditions:**
- 用户直接粘贴了运行时错误报告，包含完整的stack trace和错误计数。
- 通常无附加指令，用户期望AI直接定位并修复错误。
- 错误日志中包含具体文件名和行号，可直接定位问题代码。

**Evidence:** User pasted TapTap Maker error report with 59 errors, all 'attempt to perform arithmetic on a table value' at fox-mascot.lua:337. 10 steps to fix.

---
