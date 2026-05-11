# feature_modification — Gene Index

**Gene count:** 7

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_fm_visual_polish_cascade` | Visual Polish Cascade — Consecutive Parameter Tweaking Chain | workflow | 2x: 9dc56f96, 374e4eb7 | `intent:feature_modification`, `target:visual_style`, `consecutive_same_intent_ge_4` |
| 2 | `gene_fm_game_param_batch_tune` | Game Parameter Batch Tuning — Numeric Config Adjustment | workflow | 1x: 9dc56f96 | `intent:feature_modification`, `target:game_logic`, `numeric_parameter_in_prompt` |
| 3 | `gene_fm_cross_game_sfx_binding` | Cross-Game SFX Event Binding — Apply Sound to Multiple Games | workflow | 1x: 9dc56f96 | `intent:feature_modification`, `target:audio`, `sfx_name_in_prompt` |
| 4 | `gene_fm_asset_cleanup_selective` | Selective Asset Cleanup With Exception Preservation | workflow | 1x: 9dc56f96 | `intent:feature_modification`, `target:asset_resource|audio`, `delete_keyword` |
| 5 | `gene_fm_prompt_restatement_precision` | Prompt Restatement With Precision — Progressive Intent Clarification | workflow | 1x: 374e4eb7 | `intent:new_feature|feature_modification`, `consecutive_similar_prompt`, `added_precision_in_restatement` |
| 6 | `gene_fm_ui_text_overflow_fix` | UI Text Overflow Fix — Container Boundary Adaptation | workflow | 1x: 374e4eb7 | `intent:feature_modification`, `target:ui_layout`, `text_overflow_keywords` |
| 7 | `gene_fm_delete_asset_plus_fix_visual_glitch` | Delete Asset Plus Fix Visual Glitch — Compound Cleanup | workflow | 1x: 374e4eb7 | `intent:feature_modification`, `intent_secondary:bug_report`, `delete_asset_keywords` |

---

## `gene_fm_visual_polish_cascade`

**视觉打磨连续微调链** / Visual Polish Cascade — Consecutive Parameter Tweaking Chain

Category: `workflow`

**Signals:**
- `intent:feature_modification`
- `target:visual_style`
- `consecutive_same_intent_ge_4`
- `parameter_tweak_chain`
- `size_color_position_adjustment`
- `cn_visual_decoration_keywords`

**Preconditions:**
- 用户已有一个基本可用的视觉元素（装饰物、背景、动画），正在进行迭代打磨。
- 连续4+次 feature_modification 指向 visual_style 或 ui_layout，每次只调整1-2个参数。
- 用户的反馈模式为：观察结果→提出微调→观察→再微调，典型的视觉打磨循环。

**Evidence:** 9dc56f96: 9 consecutive visual tweaks (dots→stars→bigger→colored→moving). 374e4eb7: 5 consecutive shape/size refinements on 连连看 graphics (四角星→正三角形→加大鱼/桃心/箭头/闪电→加大螺旋加粗). Also T06→T07: preview height 180→260 in 2 turns. Pattern confirmed across sessions.

---

## `gene_fm_game_param_batch_tune`

**游戏参数批量调优** / Game Parameter Batch Tuning — Numeric Config Adjustment

Category: `workflow`

**Signals:**
- `intent:feature_modification`
- `target:game_logic`
- `numeric_parameter_in_prompt`
- `level_config_keywords`
- `cn_game_mechanic_tuning`

**Preconditions:**
- 用户正在调整已有游戏机制的数值参数（关卡需求数量、道具数量、难度曲线）。
- 请求中包含明确的数值范围或数列（如1/2/3、3/5/7），属于确定性修改。
- 目标文件通常为关卡配置或游戏逻辑文件，修改集中在数组或配置表中。

**Evidence:** Multiple prompts adjusting match-3 level win requirements (explosion counts 1/2/3, line 3/5/7, rainbow 2/3/4) and game mechanic rules (boom/line can destroy stone/ice)

---

## `gene_fm_cross_game_sfx_binding`

**跨游戏音效事件绑定** / Cross-Game SFX Event Binding — Apply Sound to Multiple Games

Category: `workflow`

**Signals:**
- `intent:feature_modification`
- `target:audio`
- `sfx_name_in_prompt`
- `multi_game_scope`
- `event_trigger_binding`
- `cn_sound_apply_keywords`

**Preconditions:**
- 用户指定一个已存在的音效名称，要求将其绑定到多个游戏的特定事件上。
- 请求中明确列出了多个游戏名（推箱子、消消乐、连连看、记忆翻牌）及对应事件。
- 属于高编辑量任务：每个游戏需定位事件处理逻辑并插入音效调用。

**Evidence:** 5 prompts applying SFX (wrong_buzzer, bounce_boing, success_fanfare, bubble_pop_cute, level_complete) across 4 games, 22-91 steps per turn

---

## `gene_fm_asset_cleanup_selective`

**选择性资源清理（带例外保留）** / Selective Asset Cleanup With Exception Preservation

Category: `workflow`

**Signals:**
- `intent:feature_modification`
- `target:asset_resource|audio`
- `delete_keyword`
- `exception_list_in_prompt`
- `cn_cleanup_keywords`

**Preconditions:**
- 用户要求删除一批资源文件，但保留指定的例外项。
- 请求模式为'删除X分类下的Y，除了A/B/C以外'。
- 需要同时清理代码中对被删除资源的引用，防止运行时错误。

**Evidence:** Delete unused audio except 3 specified files; delete all Sokoban audio + references. 17-35 steps with Grep-heavy reference cleanup

---

## `gene_fm_prompt_restatement_precision`

**用户重述精化（渐进式意图澄清）** / Prompt Restatement With Precision — Progressive Intent Clarification

Category: `workflow`

**Signals:**
- `intent:new_feature|feature_modification`
- `consecutive_similar_prompt`
- `added_precision_in_restatement`
- `zero_steps_on_first_attempt`
- `cn_scope_clarification`

**Preconditions:**
- 用户提交了一个请求，但AI未执行（0 steps）或执行结果不符预期。
- 用户在下一轮重新提交了内容相似但更精确的请求，增加了范围限定或条件。
- 例如：第一次'在主线模式和自由模式下，点击立绘聊天'→第二次增加'主页面不在游戏内'的限定。

**Evidence:** T10→T11: user restated chat feature request, adding '主页面不在游戏内' constraint. T10 had 0 steps, T11 had 43 steps. T17→T18: user restated '加大连连看图形' with slightly different item list. T17 had 0 steps, T18 had 10 steps.

---

## `gene_fm_ui_text_overflow_fix`

**UI文字溢出容器修复** / UI Text Overflow Fix — Container Boundary Adaptation

Category: `workflow`

**Signals:**
- `intent:feature_modification`
- `target:ui_layout`
- `text_overflow_keywords`
- `bubble_chat_container`
- `cn_text_exceeds_boundary`

**Preconditions:**
- 用户报告文字内容超出了容器边界（气泡、按钮、标签）。
- 问题类型：换行后文字超出容器高度、单行文字超出容器宽度、文字紧贴边框无间距。
- 属于UI布局修复，不是功能bug。

**Evidence:** T23: chat bubble text wrapping beyond bubble boundary (14 steps). T25: tab button text too close to edges (8 steps). Both are container sizing issues.

---

## `gene_fm_delete_asset_plus_fix_visual_glitch`

**删除资源并修复关联视觉异常** / Delete Asset Plus Fix Visual Glitch — Compound Cleanup

Category: `workflow`

**Signals:**
- `intent:feature_modification`
- `intent_secondary:bug_report`
- `delete_asset_keywords`
- `white_square_rendering`
- `cn_delete_and_fix_compound`

**Preconditions:**
- 用户在一个prompt中同时提出两个请求：删除某资源 + 修复删除后/相关的视觉异常。
- 视觉异常通常是白色方块（纹理缺失）或显示不正确（引用了不存在的资源）。
- 属于复合请求：feature_modification（删除）+ bug_report（白色方块）。

**Evidence:** T03: '删除学生装及图片资源 + 修复左下角白色方块'. Compound request, 32 steps, 2 builds. Delete triggered the visual fix investigation.

---
