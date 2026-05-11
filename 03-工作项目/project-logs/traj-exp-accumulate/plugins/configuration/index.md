# configuration — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_cfg_debug_toggle_management` | Debug Toggle Management — Config Switch With Conditional Visibility | workflow | 1x: 9dc56f96 | `intent:configuration`, `target:build_config`, `test_toggle_keywords` |

---

## `gene_cfg_debug_toggle_management`

**调试开关管理与条件显隐** / Debug Toggle Management — Config Switch With Conditional Visibility

Category: `workflow`

**Signals:**
- `intent:configuration`
- `target:build_config`
- `test_toggle_keywords`
- `debug_visibility_control`
- `cn_switch_on_off_keywords`

**Preconditions:**
- 用户请求修改配置开关（测试开关、调试开关），控制调试功能的显示/隐藏。
- 通常在功能开发完成后、准备发布前执行。
- 可能伴随后续的条件显示需求（如'开启时显示D按钮，关闭时不显示'）。

**Evidence:** T47: close test toggle (16 steps, heavier than expected due to code search). T49: toggle controls D button visibility (5 steps).

---
