# ai_output_correction — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_aoc_effect_not_visible` | AI Output Correction — Effect Not Visible After Claimed Implementation | diagnostic | 1x: 9dc56f96 | `intent:ai_output_correction|bug_report`, `is_correction_of_ai_work:true`, `cn_no_effect_visible_keywords` |

---

## `gene_aoc_effect_not_visible`

**AI输出效果不可见纠正** / AI Output Correction — Effect Not Visible After Claimed Implementation

Category: `diagnostic`

**Signals:**
- `intent:ai_output_correction|bug_report`
- `is_correction_of_ai_work:true`
- `cn_no_effect_visible_keywords`
- `recent_edit_in_previous_turn`
- `visual_animation_context`

**Preconditions:**
- 用户在AI刚完成修改后报告'没有看到效果'、'并没有XX效果'、'看起来并没有'。
- AI在前一轮声称已实现某个视觉/动画效果，但用户实际看到的结果与预期不符。
- 属于AI交付质量问题而非产品既有bug。

**Evidence:** '看起来并没有浮动效果，改为缓慢的向上飘动' — user corrects AI after floating animation was claimed to be added but wasn't visually apparent. 15 steps to investigate and fix.

---
