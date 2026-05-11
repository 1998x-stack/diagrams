# bug_report — Gene Index

**Gene count:** 4

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_br_persistent_failure_escalation` | Persistent Failure Escalation — Root Cause on Repeated Bug Report | diagnostic | 2x: 9dc56f96, 374e4eb7 | `intent:bug_report`, `is_correction_of_ai_work:true`, `cn_still_not_working_keywords` |
| 2 | `gene_br_post_feature_functional_bug` | Post-Feature UI Data Binding Bug — Display vs. Logic Mismatch | diagnostic | 1x: 9dc56f96 | `intent:bug_report`, `target:game_logic`, `recent_new_feature_nearby` |
| 3 | `gene_br_pagination_navigation_break` | Pagination Navigation Break — Click Unresponsive After Page Switch | diagnostic | 1x: 9dc56f96 | `intent:bug_report`, `target:game_logic`, `page_navigation_keywords` |
| 4 | `gene_br_touch_target_overlap` | Touch Target Overlap — Element Click Intercepted by Overlapping Area | diagnostic | 1x: 374e4eb7 | `intent:bug_report`, `target:ui_layout`, `click_intercept_by_other_element` |

---

## `gene_br_persistent_failure_escalation`

**持续故障升级诊断（还是没效果）** / Persistent Failure Escalation — Root Cause on Repeated Bug Report

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `is_correction_of_ai_work:true`
- `cn_still_not_working_keywords`
- `consecutive_same_issue`
- `urgency:high`
- `cn_only_once_keywords`

**Preconditions:**
- 用户在前一轮报告了问题且AI声称已修复，但用户在当前轮报告'还是没有效果'或'还是只能XX一次'。
- 问题已持续2~3+轮，属于持续性故障升级场景。用户可能用略微不同的措辞重复反馈。
- 用户的语气从描述性('看起来并没有')升级到追问式('还是没有...检查是什么问题')或简短重复('还是只能点击一次')。

**Evidence:** 9dc56f96 T09-T10: 2-turn escalation on floating effect. 374e4eb7 T20-T22: 3-turn escalation on click-only-once bug ('只会显示一个'→'还是只能点击依次'→'还是只能点击一次'). Pattern confirmed: users repeat near-identical complaints with subtle wording changes.

---

## `gene_br_post_feature_functional_bug`

**新功能交付后UI数据绑定Bug** / Post-Feature UI Data Binding Bug — Display vs. Logic Mismatch

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:game_logic`
- `recent_new_feature_nearby`
- `ui_data_binding_issue`
- `cn_not_updating_keywords`

**Preconditions:**
- 用户刚使用新构建的功能（如设置页面），发现UI与数据不同步的问题。
- bug报告紧跟在 new_feature 交付之后（1-3轮内）。
- 典型症状：滑块拖动但数值不变、进度条总是100%、显示值与实际值不一致。

**Evidence:** Volume slider bug immediately after settings UI feature (T36): percentage not updating, progress bar stuck at 100%. 30 steps to fix (complex data binding issue).

---

## `gene_br_pagination_navigation_break`

**分页导航后点击失效** / Pagination Navigation Break — Click Unresponsive After Page Switch

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:game_logic`
- `page_navigation_keywords`
- `click_no_response`
- `cn_pagination_bug`

**Preconditions:**
- 用户报告在翻页/分页后点击元素无响应。
- 问题仅出现在非首页（如第二页、第三页），首页正常。
- 典型原因：分页切换时事件监听器未重新绑定，或元素ID/索引计算有偏移。

**Evidence:** 连连看 page 2 click → no navigation. 8 steps to fix. Classic pagination index offset bug.

---

## `gene_br_touch_target_overlap`

**触控区域重叠导致按钮失效** / Touch Target Overlap — Element Click Intercepted by Overlapping Area

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:ui_layout`
- `click_intercept_by_other_element`
- `z_order_conflict`
- `cn_cannot_click_keywords`

**Preconditions:**
- 用户报告某个按钮'无法点击'，但该按钮在UI上可见且之前可正常使用。
- 根因是另一个可交互元素（如角色立绘、全屏触控区域）覆盖在按钮上方，拦截了点击事件。
- 通常在新增交互功能（如点击角色聊天、全屏手势）后出现，新元素的触控范围过大。

**Evidence:** T14: 翻页按钮被角色聊天触控区拦截 (45 steps, 2 builds). T26: 换装页面设置按钮无法点击 (34 steps, 2 builds). Both caused by newly added interactive elements overlapping existing buttons.

---
