# diagnostic — Gene Index

**Gene count:** 27

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_br_new_panel_click_interception` | New Panel Click Interception — Underlying Button Becomes Unresponsive | diagnostic | 2x: 014354fc, 374e4eb7 | `intent:bug_report`, `target:ui_layout`, `symptom:click_unresponsive` |
| 2 | `gene_br_false_alarm_feature_verification` | False Alarm Bug — Verify Feature Already Implemented Before Accepting Report | diagnostic | 1x: 212062a8 | `intent:bug_report`, `is_correction_of_ai_work`, `feature_supposedly_implemented` |
| 3 | `gene_br_interactive_state_lock_one_shot` | Interactive Element One-Shot Click Bug — State Machine Lock Due to Incomplete Init Reset | diagnostic | 1x: 374e4eb7 | `intent:bug_report`, `target:game_logic`, `symptom:click_only_once` |
| 4 | `gene_elp_nanovg_api_return_type_mismatch` | NanoVG API Return Type Mismatch — Table Return Destructured as Multiple Values | diagnostic | 2x: 374e4eb7, cc1dd130 | `intent:error_log_paste`, `stacktrace_in_prompt`, `lua_runtime_error` |
| 5 | `gene_br_cross_game_structural_comparison_debug` | Persistent Error Cross-Game Structural Comparison Debug — Rewrite from Working Template | diagnostic | 1x: 3ee927f3 | `intent:bug_report`, `intent:error_log_paste`, `symptom:error_persists_after_fix` |
| 6 | `gene_br_web_platform_text_input_disabled` | NanoVG Modal Web Platform Text Input Disabled — SetScreenKeyboardVisible Fix | diagnostic | 1x: 4f916c20 | `intent:bug_report`, `target:ui_layout`, `paste_not_working` |
| 7 | `gene_br_blank_screen_nanovg_render_event_unbound` | Post-Scaffold Blank White Screen — NanoVG Render Event Chain Unbound Diagnostic | diagnostic | 1x: 5c2aeaee | `intent:inquiry`, `symptom:blank_white_screen`, `game_just_scaffolded` |
| 8 | `gene_elp_missing_asset_cross_game_config_ref` | Missing Texture on New Game Registration — Cross-Game Config Comparison → Empty String Fallback | diagnostic | 2x: 61467d20, 9bbd20cc | `intent:error_log_paste`, `target:asset_resource`, `missing_texture_or_asset` |
| 9 | `gene_br_special_block_rainbow_swap_bug` | Match-3 Rainbow Block Swap Bug — Elimination Uses Post-Swap State Instead of Pre-Swap ColorId | diagnostic | 1x: 61467d20 | `intent:bug_report`, `target:game_logic`, `match3_game` |
| 10 | `gene_br_match3_config_field_name_mismatch` | Match-3 Story Level Obstacle Field Name Mismatch — frozenCells/stoneBlocks vs icePositions/stonePositions | diagnostic | 1x: 6b8566ea | `intent:bug_report`, `target:game_logic`, `match3_game` |
| 11 | `gene_ir_stale_report_version_reaudit` | Stale-Report-Driven Current-Version Re-audit — Version Drift Detection and Fix | diagnostic | 1x: 762afe73 | `intent:inspection_review`, `has_attached_doc`, `stale_report_warning` |
| 12 | `gene_br_animation_update_loop_not_wired` | Animation Implemented but Static — Update Loop Not Registered in Game Loop | diagnostic | 1x: 9dc56f96 | `intent:bug_report`, `intent:ai_output_correction`, `symptom:animation_static_no_movement` |
| 13 | `gene_br_pagination_level_index_offset_bug` | Level Select Pagination Bug — Page 2+ Click Fails Due to Missing Page Offset in Level Index | diagnostic | 1x: 9dc56f96 | `intent:bug_report`, `symptom:level_navigation_fails`, `symptom:click_level_does_nothing_on_page2plus` |
| 14 | `gene_br_cloud_save_visual_state_unapplied` | Cloud Save Migration — Skin or Visual State Not Applied on Load Despite Correct Data Read | diagnostic | 1x: 9df66fd4 | `intent:bug_report`, `cloud_save_migration_recent`, `symptom:visual_state_not_applied_on_load` |
| 15 | `gene_br_nanovg_cross_context_image_handle_white` | NanoVG Cross-Context Image Handle White Render — Router.replace Double-Init, Fix by Removing All nvgDeleteImage | diagnostic | 2x: a09c411b, e7d71628 | `intent:bug_report`, `visual_artifact_white`, `nanovg_image_rendering` |
| 16 | `gene_br_auto_win_not_triggered` | Auto-Win Condition Not Triggered — Diagnose Win-Condition Check Path and Event Dispatch | diagnostic | 1x: bc3f2ce9 | `intent:bug_report`, `target:game_logic`, `auto_trigger_not_firing` |
| 17 | `gene_elp_board_init_bypass_data_transform_nil` | Board Init Bypasses Data-Transform Layer — Story-Mode Raw levelData Skips level-loader, Causing nil Field Crash at Runtime | diagnostic | 1x: bdf118ee | `intent:error_log_paste`, `runtime_error_nil_field_access`, `error_field:wallSet_or_similar_derived_field` |
| 18 | `gene_elp_story_level_field_name_adapter_mismatch` | Story-Level Config Field Name Mismatch in Adapter — Runtime Log Pinpoints nil Concatenation, Cross-Game Grep Fixes All Adapters | diagnostic | 1x: bdf118ee | `intent:error_log_paste`, `intent:bug_report`, `runtime_error_nil_concatenation` |
| 19 | `gene_br_transition_overlay_stuck_black_wasm` | NanoVG Fullscreen Overlay Transition → Persistent Black Screen + WASM Crash Cascade Diagnostic | diagnostic | 1x: d8f96672 | `intent:bug_report`, `intent:error_log_paste`, `symptom:screen_stays_black` |
| 20 | `gene_elp_event_handle_userdata_type_error` | UnsubscribeFromEvent Userdata Type Error — String Passed Instead of Subscription Handle Causes Flood of Errors | diagnostic | 1x: e2076a78 | `intent:error_log_paste`, `symptom:hundreds_identical_errors`, `symptom:userdata_expected_string_got` |
| 21 | `gene_elp_lua_api_arg_type_table_not_string` | Lua API Argument Type Error — Table Passed to Get() Expecting String (Common When New Data Structures Introduced) | diagnostic | 1x: e7d71628 | `intent:error_log_paste`, `stacktrace_in_prompt`, `lua_runtime_error` |
| 22 | `gene_elp_callback_closure_nil_entity_id` | Lua Callback Closure Entity ID Nil — Shared Popup Component Callback Fails to Capture or Pass Entity Identifier | diagnostic | 1x: e7d71628 | `intent:error_log_paste`, `stacktrace_in_prompt`, `lua_runtime_error` |
| 23 | `gene_br_bulk_formula_edit_stale_override` | Post-Bulk-Formula-Edit Stale Level Override — Grep-Only Diagnosis Then Fragment-Triggered Patch Fix | diagnostic | 1x: f4dd8c16 | `intent:bug_report`, `target:game_logic`, `follows_arithmetic_formula_bulk_edit` |
| 24 | `gene_aoc_display_config_numerical_mismatch` | Display Text Numerical Mismatch — Align Subtitle / Caption Count with Actual Config | diagnostic | 1x: fa1daf15 | `intent:ai_output_correction`, `intent:inspection_review`, `target:game_logic` |
| 25 | `gene_inq_mcp_tool_unavailable_first_turn` | MCP Tool Unavailable on First Turn: Graceful Disclosure with Available Tools List | diagnostic | 0x:  | `intent:inquiry`, `mcp_tool_invocation_command`, `tool_not_found_in_available_tools` |
| 26 | `gene_aoc_logic_reexplain_cluster` | AOC Logic Re-explanation Cluster — Same Constraint Restated Across Consecutive Correction Turns | diagnostic | 1x: 08754637 | `intent:ai_output_correction`, `consecutive_aoc_ge_2`, `same_target_artifact_consecutive` |
| 27 | `gene_elp_platform_noise_continue_pattern` | Platform Noise Error Log — Acknowledge-and-Continue Pattern Without Unsolicited Fix | diagnostic | 1x: 08754637 | `intent:error_log_paste`, `recurring_same_error_type`, `platform_level_error` |

---

## `gene_br_new_panel_click_interception`

**新增面板导致下层按钮点击失效（点击拦截 Bug）** / New Panel Click Interception — Underlying Button Becomes Unresponsive

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:ui_layout`
- `symptom:click_unresponsive`
- `symptom:button_no_reaction`
- `recent_ui_panel_added`
- `cn_keywords:dianji,wufa,meiyoufanying,anniu`

**Preconditions:**
- 用户报告某个原本正常的 UI 按钮或控件点击后无响应（如「点击没有反应」、「无法点击」）。
- 同一 session 中刚刚实现了一个新的面板组件（Panel/Layer/覆盖层），或该 bug 发生在近期新增 UI 组件之后。
- 点击失效的控件与新增面板位于同一屏幕区域。

**Evidence:** Turn 4 (11 steps): user reported debug button in top-right unresponsive after sound test panel was added in T02. Agent read sound-test-panel.lua, identified the panel was not initially hidden (intercepting clicks), fixed by setting initial state to width=0, height=0 with comment meaning 'no click interception'. Build succeeded. Pattern: new panel with non-zero initial dimensions intercepts touch events from underlying buttons. | 374e4eb7 T13 (45 steps, 1 edit, 1 build): user reported that in main story mode (adventure page), clicking the page-turn arrow button at bottom-left triggers fox mascot character chat instead of turning the page. Root cause: in handleClickAt(), the fox mascot click detection ran before the page-turn button detection. Fix: moved the page-turn button check to run BEFORE the fox mascot check in the event handler priority order. Agent: respond_to_user (identified priority issue), Read adventure/init.lua x2, TodoWrite, Edit adventure/init.lua (reorder click checks), Build success. Pattern confirmed: any newly added interactive component whose touch area overlaps an existing button will intercept clicks if added before the existing button in the click-handling priority chain.

---

## `gene_br_false_alarm_feature_verification`

**疑似遗漏功能的存在性核验（误报 Bug 识别）** / False Alarm Bug — Verify Feature Already Implemented Before Accepting Report

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `is_correction_of_ai_work`
- `feature_supposedly_implemented`
- `issue_still_reported`
- `implementation_existence_questioned`
- `cn_keywords:yinggai_zhizuole,weishenme_hai,haiyou_wenti,shifou_zhengchang`

**Preconditions:**
- 用户相信某个功能已经实现（如「应该制作了…的功能」），但发现对应问题仍被标记为未解决，或在测试中仍复现。
- 用户的表述带有质疑语气（「为什么还有」「为什么没有」），暗示认为是 AI 遗漏了修复或集成不完整。
- 该功能可能已存在于代码库中，只是问题报告未同步更新，或集成路径与用户预期不同。

**Evidence:** 212062a8 T1 (8 steps): user said '应该制作了皮肤解锁时弹窗提示的功能，检查为什么还有5.1的问题'. Agent: (1) respond_to_user declared 'let me verify'. (2) Task SA — search for 皮肤解锁通知 implementation → SA confirmed outfit-unlock-popup component is fully implemented. (3) Grep outfit.unlock|unlockPopup|pendingFirstClear in /workspace/scripts → found outfit-unlock-popup.lua + adventure/init.lua integration. (4) Glob scripts/**/*unlock* → confirmed file exists. (5) Grep outfit.unlock in adventure/init.lua → found pendingFirstClear_ pattern + popup trigger. (6) Read outfit-unlock-popup.lua → confirmed complete implementation (华丽动画, 背景彩条, 皮肤蹦出动画, 确认按钮). (7) respond_to_user — reported 'feature fully implemented; issue 5.1 can be marked resolved'. Pattern: user suspects AI missed a fix → Task SA + Grep + Read verify → confirm existence + report file locations → suggest doc status update.

---

## `gene_br_interactive_state_lock_one_shot`

**点击触发组件单次响应 Bug：状态机锁定未重置** / Interactive Element One-Shot Click Bug — State Machine Lock Due to Incomplete Init Reset

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:game_logic`
- `symptom:click_only_once`
- `symptom:subsequent_clicks_ineffective`
- `interactive_overlay_or_dialog`
- `stateful_component`
- `cn_keywords:zhiyinengdianjiyi,zhihuixianshiyici,houxudianji_wuxiao,haishizhi,haishi`

**Preconditions:**
- 用户报告某个点击触发的交互元素（聊天气泡、弹窗、对话框）只响应第一次点击，后续点击无反应。
- 该交互元素是有状态的组件（state machine），包含 idle/animating/showing 等状态。
- 组件的 init() 或 setActive() 在页面切换时被调用，但未完整重置所有状态变量。
- 可能存在两层问题：(1) init() 未重置状态机变量导致页面复用时锁死；(2) 气泡显示期间点击未被正确处理（未 dismiss 已有气泡 + 再触发）。

**Evidence:** 374e4eb7 T19 (24 steps, 1 edit, 1 build): user reported fox mascot chat bubble on home page only shows once, subsequent clicks do nothing. Agent: Grep notifyChat/chatState/showChat → Read fox-mascot.lua x4 → found: init() sets inited_=true and firstTrigger_=true but does NOT reset state_ or cooldownTimer_ → when page is re-activated via setActive, init() is called again but state_ retains its previous value ('fade_out' or 'showing') → notifyChat() guards with state_~='idle' so returns immediately. Fix: added state_='idle' + cooldownTimer_=0 in init(). Build success. T20: user re-sent 'still only sequential' (no agent run). T21 (17 steps, 1 edit, 2 builds): agent re-investigated — Grep SKIN_CHATS + Read outfit-manager.lua (chat data OK, many lines) → Read home/init.lua (page logic OK) → realized: when bubble is showing and user clicks again, notifyChat() returns immediately because state_~='idle' — there is no 'dismiss current + re-trigger' logic. Added: if state_=='showing' or 'pop_in', skip cooldown guard and force-restart animation. Build (second attempt after initial build error due to missing entry config, recovered via Glob+Read project.json). Pattern: two-layer fix — Layer 1: init() must fully reset state machine; Layer 2: click-while-showing must dismiss and re-trigger.

---

## `gene_elp_nanovg_api_return_type_mismatch`

**NanoVG API 返回值类型误用：table 被当作多返回值解构** / NanoVG API Return Type Mismatch — Table Return Destructured as Multiple Values

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `stacktrace_in_prompt`
- `lua_runtime_error`
- `symptom:arithmetic_on_table`
- `nanovg_api_call`
- `shared_component_error`
- `cn_error:attempt_to_perform_arithmetic_on_a_table_value`
- `cn_error:attempt_to_perform_arithmetic_on_a_nil_value_field_integer_index`
- `nanovg_text_bounds_hud_renderer`

**Preconditions:**
- 用户粘贴了包含结构化头部信息（Generated at、Error Count、Browser 等）的运行时错误报告，大量错误行指向同一个 Lua 文件和同一行号。
- 错误信息为 `attempt to perform arithmetic on a table value`，发生在调用 NanoVG API（如 nvgTextBoxBounds、nvgTextBounds）之后对返回值做算术运算的位置。
- 错误堆栈指向 `shared/components/` 下的共享组件文件（fox-mascot、chat-bubble 等），说明是共享组件中的 API 用法问题。
- 变体：错误信息为 `attempt to perform arithmetic on a nil value (field 'integer index')`，发生在调用 nvgTextBounds 后对返回的 table 进行 bounds[intKey] 索引时，因整数索引越界（如 bounds[0]，Lua 1-indexed）或函数在某些调用路径下返回 nil，导致算术操作失败。

**Evidence:** 374e4eb7 T23 (10 steps, 1 edit, 1 build): user pasted TapTap Maker Error Report with 59 identical errors (same Lua stack trace: fox-mascot:337 'attempt to perform arithmetic on a table value', called from adventure/init.lua renderMap). Agent: (1) respond_to_user — identified line 337 as the problem site: `(b3 or maxW) - (b1 or 0)` arithmetic on what should be nvgTextBoxBounds return values. (2) Read fox-mascot.lua → confirmed: `local b1, b2, b3, b4 = nvgTextBoxBounds(...)` destructuring. (3) 3x Grep nvgTextBoxBounds in engine docs → found .emmylua/NanoVG.d.lua: API returns number[] table {xmin, ymin, xmax, ymax}, NOT 4 separate return values. (4) Edit: changed to `local bounds = nvgTextBoxBounds(...); local xmin=bounds[1]; local ymin=bounds[2]; local xmax=bounds[3]; local ymax=bounds[4]`. (5) Build success. Root cause: NanoVG Lua binding returns bounding-box APIs as array tables, not multiple return values — a common assumption error when porting from C++ NanoVG docs.

cc1dd130 P2 (13 steps, intent: error_log_paste): user pasted TapTap Maker Error Report with 80 errors at board-renderer:996 drawHUD — 'attempt to perform arithmetic on a nil value (field integer index)', called from screens/gameplay:289 render → adapter:120 P1PZ_HandleNanoVGRender. Distinguishes from 374e4eb7 case (arithmetic on TABLE value): here the nil comes from integer indexing — likely bounds[intKey] where intKey=0 (1-indexed Lua) or nvgTextBounds returning nil in some code paths. Agent workflow: (1) respond_to_user (preliminary analysis). (2) Read board-renderer.lua at line ~996 (drawHUD function). (3) respond_to_user. (4-5) 2x Grep nvgTextBounds in puzzle-land scripts. (6) respond_to_user. (7-9) 3x Grep nvgTextBounds in engine-docs, examples, .emmylua (same doc-lookup pattern as 374e4eb7). (10) respond_to_user. (11) Edit board-renderer (targeted fix). (12) Build. (13) respond_to_user. Same diagnosis-and-fix pattern: Read error file → Grep NanoVG API in engine docs → single Edit → build. Nil variant note: this pattern can manifest as 'arithmetic on nil' rather than 'arithmetic on table' depending on whether the code uses table indexing or multiple-return destructuring.

---

## `gene_br_cross_game_structural_comparison_debug`

**持续报错跨游戏结构对比调试：以正常游戏为模板重写问题文件** / Persistent Error Cross-Game Structural Comparison Debug — Rewrite from Working Template

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `intent:error_log_paste`
- `symptom:error_persists_after_fix`
- `user_cites_other_games_as_working`
- `new_game_module_recently_added`
- `nanovg_migration_context`
- `cn_keywords:haishi_baocuo,cankao_qita_youxi,duibi,qita_youxi_zhengchang`

**Preconditions:**
- 用户在多次报告错误并尝试修复后，仍然遇到同类错误，并明确提到「其他游戏是正常的」或「参考其他游戏对比一下」。
- 当前出错的游戏模块是近期新增或迁移的（如 NanoVG 自绘迁移、新游戏模块接入），而其他已有游戏的同类文件（adapter.lua、level-select.lua、init.lua 等）运行正常。
- 错误不是简单的语法错误，而是结构性问题（如模块 return 缺失、require 路径错误、key 覆盖等），需要与正常文件进行对比才能定位。

**Evidence:** 3ee927f3 T00-T07 (8-turn error cascade debugging p4-link-match after NanoVG migration): T00 (33 steps): first error paste — adapter:133 nil value 'draw'. Agent reads adapter.lua, globs files, 0 edits, 1 failed build. T01 (70 steps): second error paste — 2 edits, 2 builds, 24x Bash investigations into level-select and adapter. T02 (55 steps): user says 'build' — agent uses mcp__sce-urhox__lua_lsp_client 4x for type checking, 9 edits, 4 builds (iterative fix). T03 (32 steps): third error — agent examines dist/ compiled files via Bash (manifest.json + compiled lua bytecode) to verify source changes reflect in build output. T04 (1 step): inquiry about p4 file paths → pure respond_to_user. T05 (23 steps): user says '还是报错，参考其他游戏，对比一下，其他游戏是正常的'. Agent: (1) Task SA 'compare p1/p2/p3 vs p4 game structure' → SA did comprehensive structural comparison. (2) Bash loops: compare level-select.lua return statements across all games, compare adapter.lua require patterns, compare init.lua and config files. (3) Read p2-memory-flip/adapter.lua as working template. (4) Write new p4-link-match/adapter.lua from scratch following template. (5) Build → partial success (one more error type remained). T06 (41 steps): user says '还是报错，检查是否覆盖了什么key引起的' — another error variant. Agent: Bash 5x investigating require dependency chain → Read 12 files → 6 edits → build success. T07 (1 step): user says '没有报错，可以正常进入游戏了，总结是什么问题' → pure text explanation of root cause. Pattern: first fix attempts → dist inspection → cross-game Task subagent comparison → Bash structural diff loops → rewrite from working template → verify. Key signal: user explicitly saying 'other games are working' triggers systematic cross-game comparison rather than continued point-by-point patching.

---

## `gene_br_web_platform_text_input_disabled`

**NanoVG 模态框 Web 端键盘输入失效：SetScreenKeyboardVisible 修复** / NanoVG Modal Web Platform Text Input Disabled — SetScreenKeyboardVisible Fix

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:ui_layout`
- `paste_not_working`
- `text_input_not_responding`
- `modal_or_overlay_context`
- `platform_specific_behavior`
- `web_platform_mentioned`
- `nanovg_drawn_ui`
- `cn_keywords:wufa_zhantie,wufa_shuru,web_wufa,zhantie,shuru_wufa`

**Preconditions:**
- 用户报告在某个关卡编辑器或对话框 UI 中无法粘贴或输入文字（「无法粘贴」「无法输入数据」）。
- 该 UI 是用 NanoVG 自绘的模态框（而非引擎原生 UIKit 文本框），显示为覆盖在游戏画布上的自绘弹窗。
- 问题在 Web/WASM 平台（TapTap Maker Web 预览）可复现，可能在本地客户端不复现。
- 第一次报告时用户未指明平台，第二次报告时明确提到「web」或「web无法」。

**Evidence:** 4f916c20 T27-T32: three-prompt escalation pattern for platform-specific paste bug. T27-T28 (P14, 10 steps, 0 edits): user said '输入关卡数据UI，无法粘贴和输入数据' — did not mention platform. Agent: 7x Grep in engine-docs/ + .emmylua/ searching for TextInput, SetTextInput, clipboard, clipboard APIs. Found no direct clipboard paste API in engine docs. respond_to_user — reported: NanoVG-drawn modal has no native paste support; engine needs SetScreenKeyboardVisible to enable keyboard. Zero edits — agent did not implement fix in this turn. T29-T30 (P15, 2 steps, 0 edits, 1 build): user sent 'build' (1 word). Agent built with no code changes (build from T25 implementation). T31-T32 (P16, 33 steps, 6 edits, 1 build): user said '现在推箱子，关卡编辑器，输入关卡数据，web无法使用粘贴' — explicitly named 'web' platform. Agent: (1) Grep clipboard, KEY_PASTE, clipboard in engine-docs/ + .emmylua/ + urhox-libs/UI/Widgets/TextInput. (2) Grep SetScreenKeyboardVisible → found it in .emmylua. (3) TodoWrite: fix modal to call SetScreenKeyboardVisible(true) on open, false on close. (4) Read level-editor.lua. (5) 6x Edit level-editor.lua: add SetScreenKeyboardVisible(true) to showImportModal_ = true block, add false to showImportModal_ = false block, add text character handling to OnTextInput callback, ensure backspace/clear handled, fix input buffer init/clear. (6) Build success. Root cause: TapTap Maker web runtime (WASM) does not route keyboard/paste events to a NanoVG-drawn modal unless explicitly told to via SetScreenKeyboardVisible. Native UIKit components handle this automatically; NanoVG modals must do it manually. Key pattern: first report (no platform specified) → investigation-only (0 edits, finds root cause) → user says 'build' (build old code) → second report (explicit 'web') → implement fix.

---

## `gene_br_blank_screen_nanovg_render_event_unbound`

**新游戏脚手架后白色空白屏幕：NanoVG 渲染事件链未绑定诊断** / Post-Scaffold Blank White Screen — NanoVG Render Event Chain Unbound Diagnostic

Category: `diagnostic`

**Signals:**
- `intent:inquiry`
- `symptom:blank_white_screen`
- `game_just_scaffolded`
- `pause_button_visible`
- `nanovg_adapter_newly_created`
- `render_event_chain_suspect`
- `cn_keywords:baise_yemian,kongbai,zhi_you_anniu,ying_xianshi_shenme,meiyou_huamian`

**Preconditions:**
- 用户进入刚脚手架搭建的新游戏后，看到的是白色（空白）页面，只有游戏容器的系统级 UI（如暂停按钮）可见，游戏主画布完全空白。
- 用户询问「理论上应该出现什么画面」或「为什么是白色页面」，语气为询问而非明确的 bug 报告——这是一个掩盖了 bug 的 inquiry。
- 该游戏的 adapter.lua 在本 session 中刚刚被创建（Write），尚未经过完整的渲染事件绑定验证。
- 项目使用 NanoVG 全自绘渲染，游戏 adapter 需要注册 afterBg/afterUi 回调并调用 nvgBeginFrame → nvgEndFrame 才能在游戏容器中渲染画布。

**Evidence:** 5c2aeaee T7 (index 5, ~25 steps, 1 Write + 1 Edit + 1 build): user said '进入推箱子后，页面是白色的，右侧有一个暂停按钮。理论上应该出现什么画面' — ostensibly an inquiry but describes a blank screen bug. Agent: (1) TodoWrite (switched to diagnosis mode). (2) Read adapter.lua + level-select.lua + gameplay.lua (read all scaffolded screens). (3) Read demo-color-match/adapter.lua (reference for NanoVG rendering pattern). (4) Read game-container/init.lua + NanoVG standalone example. (5) 6x Grep: NanoVGRender event chain, afterBg/afterUi callbacks, nvgBeginFrame usage across files, game container callbacks, render pipeline. (6) Read main.lua + pages/game/init.lua + router.lua. (7) Write adapter.lua (complete rewrite — added correct nvgBeginFrame → board render → nvgEndFrame in afterBg callback, fixed game state initialization). (8) Edit main.lua (add NanoVGRender event subscription + nvg context variable). (9) Build → success. Root cause: adapter.lua was written as a skeleton with empty afterBg callback — it did not include nvgBeginFrame/nvgEndFrame calls, so the NanoVG canvas was never initialized for the game container, producing a white canvas. The pause button appeared because it is rendered by the game-container infrastructure (UIKit layer), not NanoVG. Key behavioral insight: 白色页面 + 系统UI可见 = NanoVG canvas not initialized (nvgBeginFrame never called) or render event not connected, NOT a logical game rendering bug.

---

## `gene_elp_missing_asset_cross_game_config_ref`

**新游戏注册时缺失纹理资源：参照其他游戏改为空字符串兜底** / Missing Texture on New Game Registration — Cross-Game Config Comparison → Empty String Fallback

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `target:asset_resource`
- `missing_texture_or_asset`
- `newly_registered_game`
- `config_file_path_suspect`
- `nvgCreateImageUrho_error`
- `cn_error:Could_not_find_resource`
- `cross_game_config_comparison`

**Preconditions:**
- 用户粘贴了含 'Could not find resource' 或 'Failed to load texture' 的错误报告，错误指向一个 Textures/games/xxx-cover.png 或 icon.png 路径。
- 错误发生在刚刚注册到大厅的新游戏上，该游戏的 config 文件中包含了 icon/cover 字段且值为非空图片路径。
- 项目中其他已正常运行的游戏（P1、P2 等）有相同结构的 config 文件，可用于对比。

**Evidence:** 61467d20 T05 (12 steps, 1 edit, 1 build): user pasted TapTap Maker Error Report with 2 errors — 'ERROR: Could not find resource Textures/games/p3-match-3-cover.png' + 'nvgCreateImageUrho: Failed to load texture'. Agent: (1) respond_to_user — identified P3 missing cover image. (2) Glob assets/Textures/games/* (not found). (3) Glob **/Textures/games/* (not found). (4) Glob **/Textures/games* (not found). (5) respond_to_user — need to check how other games handle this. (6) Grep 'cover.*\.png|icon.*\.png' across configs → found P1/P2 configs. (7) Grep 'cover|icon' across configs → confirmed P1/P2 both use empty string ("") for icon/cover. (8) respond_to_user — P1 and P2 use empty strings; game-card has fallback for missing images; P3 was configured with a path that doesn't exist. Fix: change P3 icon/cover to empty strings. (9) Read scripts/config/games/p3-match-3.lua. (10) Edit: changed icon = "Textures/games/p3-match-3-icon.png" → "" and cover = "Textures/games/p3-match-3-cover.png" → "". (11) Build → success. (12) respond_to_user. Root cause: when generating the new game config file in T01 (97-step scaffolding), agent wrote placeholder image paths that followed convention but the actual asset files were never created. Other existing games (P1, P2) either always used empty strings or had their image paths removed. Pattern: error for missing asset → Glob confirms asset doesn't exist → Grep other game configs to find established fallback pattern → apply same pattern (empty string) → build. | 9bbd20cc T02 (17 steps, 2 edits, 2 builds): user pastes TapTap Maker Error Report — '2026-03-18 03:25:12 ERROR: Could not find resource Textures/games/p2-memory-flip-cover.png'. Agent: (1) respond_to_user. (2) Read scripts/config/games/p2-memory-flip.lua (game config). (3) Bash ls assets/Textures/games/ (confirm asset absent). (4) Bash find assets/ for p1/cover patterns. (5-6) Grep p1-puzzle.*cover|icon in scripts/config/games (find sibling config handling). (7) respond_to_user. (8) Edit scripts/config/games/p2-memory-flip.lua — set cover to empty string (matching P1 pattern). (9) build — passes cover error but reveals secondary lua error in log. (10) Read logs/lua_errors.log. (11) respond_to_user. (12) Grep cjson|diagnostic in p1-puzzle-land/save.lua (diagnose secondary error). (13) respond_to_user. (14) Read p2-memory-flip/save.lua. (15) Edit p2-memory-flip/save.lua (fix secondary save issue). (16) build success. (17) respond_to_user. Two-edit two-build variant: first edit fixes cover config → first build reveals secondary runtime error in save.lua → second edit fixes save → second build succeeds. Grep sibling-config pattern confirmed: agent looked at P1 config to find the empty-string convention for missing cover assets.

---

## `gene_br_special_block_rainbow_swap_bug`

**消消乐彩虹块换位 Bug：pre-swap 颜色状态被覆盖** / Match-3 Rainbow Block Swap Bug — Elimination Uses Post-Swap State Instead of Pre-Swap ColorId

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:game_logic`
- `match3_game`
- `special_block_behavior`
- `rainbow_block_or_wildcard`
- `swap_operation`
- `state_inconsistency_after_swap`
- `cn_keywords:teshu_fangkuai,huancuo_weizhi,bug,huanse,suoyou_yanse,cuhfa_baocuo`

**Preconditions:**
- 用户报告消消乐中与特殊方块（彩虹块/通配块）的换位操作触发了 bug，具体表现为换完位置后出错，或换位后消除逻辑行为异常。
- 游戏逻辑包含 trySwap → _handleRainbowSwap 的调用链，_handleRainbowSwap 内部先执行了物理换位（_swap()），再运行颜色匹配/消除检查。
- 项目中同时存在多个游戏模块（Sokoban、match-3 等），文件名相似（board.lua）可能导致读取错误文件。

**Evidence:** 61467d20 T15 (21 steps, 1 edit, 1 build): user said '检查特殊方块，消除所有相同颜色的方块，与相同颜色的方块换位置时，好像会触发BUG，导致直接换了位置，然后出错'. Agent first read p1-puzzle-land/logic/board.lua (wrong file — Sokoban board), self-corrected: '这是推箱子的 board.lua，不是消消乐的'. Then read p3-match-3/logic/board.lua + gameplay.lua → traced trySwap → _handleRainbowSwap call chain → identified root cause: _handleRainbowSwap called _swap() first (physically moves rainbow block to target position), then ran elimination check — but by the time elimination runs, the rainbow block is already at the target location, so the colorId lookup returns the rainbow block's own (null/wildcard) color rather than the original target block's color, causing state inconsistency. Fix: save target colorId before calling _swap(), pass pre-swap colorId to _handleRainbowSwap. Grep spawnElimParticles confirmed renderer needs no change. 1 edit to board.lua → build success. Key behavioral note: agent self-corrected wrong-file read mid-turn without user prompting — recognized 'p1-puzzle-land' path vs expected 'p3-match-3'.

---

## `gene_br_match3_config_field_name_mismatch`

**消消乐主线关卡障碍物字段名不匹配：frozenCells/stoneBlocks 导致障碍物不显示** / Match-3 Story Level Obstacle Field Name Mismatch — frozenCells/stoneBlocks vs icePositions/stonePositions

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:game_logic`
- `match3_game`
- `obstacle_blocks_recently_added`
- `symptom:obstacle_not_visible`
- `story_level_config_edited`
- `cn_keywords:meiyou_kandao,kanbudao,youxi_nei_meiyou,bingkuai_meiyou_xianshi`

**Preconditions:**
- 在 session 中刚刚对 story-N.lua 主线关卡配置文件添加了障碍物（冰块/石块）数据，使用了 frozenCells 或 stoneBlocks 字段名。
- 用户运行游戏后报告「游戏内看不到冰块/石块」，且该关卡是消消乐（match-3）主线关卡。
- 项目中存在 p3-match-3/logic/board.lua，其中读取障碍物时使用的字段名（icePositions/stonePositions）与关卡配置文件中写入的字段名（frozenCells/stoneBlocks）不同。

**Evidence:** 6b8566ea T07-T09: agent added obstacle blocks using non-canonical field names — frozenCells (for ice) and stoneBlocks (for stones). T12 (24 steps, 5 edits, 1 build): user reported '糖糖的冰火花园关卡，游戏内没有看到冰块'. Agent: (1) Grep 'frozenCells|frozenCell|frozen' → only in story-N.lua, not game logic. (2) Grep 'frozen|ice|冰' → board.lua uses 'icePositions' and 'stonePositions'. (3) Read board.lua → confirmed mismatch. (4) 5 edits: frozenCells→icePositions, stoneBlocks→stonePositions across story-27/31/35.lua. (5) Build success. T13 (6 steps): user asked '检查石块的字段是否正确'. Agent: Grep confirmed all stone fields now use stonePositions. Root cause: agent guessed intuitive field names that don't match board.lua canonical names.

---

## `gene_ir_stale_report_version_reaudit`

**旧版报告驱动的当前版本重审：版本偏差检测与修复** / Stale-Report-Driven Current-Version Re-audit — Version Drift Detection and Fix

Category: `diagnostic`

**Signals:**
- `intent:inspection_review`
- `has_attached_doc`
- `stale_report_warning`
- `version_mismatch_suspected`
- `re_verify_against_current_code`
- `cn_keywords:jiu,baogao,jiuban,dangqianbanben,shifouxiangfu,jiancha`

**Preconditions:**
- 用户打开了之前 AI 生成的问题报告，但明确提示「这个报告是基于旧版写的」，要求验证某一章节的问题在当前版本中是否仍然存在或已变化。
- 问题报告中某个章节描述了数值或内容一致性问题（如关卡配置参数与设计文档不符），而代码库可能已经被其他 session 修改过。
- 需要将报告中描述的期望值与当前代码文件中的实际值进行逐项对比，而非直接相信报告结论。

**Evidence:** 762afe73 T07 (52 steps): user said '三、关卡内容一致性，但是注意，这个报告是基于旧版写的，需要注意与当前版本是否相符，并且检查当前版本是否有问题'. Agent: (1) Read storyline.lua (at 3 offsets) to get current level configs. (2) Task SA — read all 35 story-N.lua files and extract score/board-size/obstacle-count params. (3) Grep for specific values referenced in report (targetScore, boardSize fields). (4) Compare: found 10 items where current storyline.lua values differed from story-N.lua definitions — some were regressions (undone by earlier edits), some were new issues not in the original report. (5) 45 Edits to storyline.lua fixing score/count/boardSize mismatches across all 10 affected levels. (6) 2x build (first revealed a secondary issue, second passed). (7) 20x Edit on 自查问题报告.md: marked all 10 Section III items [已修复], added 2 new entries for newly discovered issues (also marked [已修复]). Pattern: stale-report warning → read actual source files first → 3-way classification (already fixed / still broken / new issue) → fix all categories → 2-pass build → report update includes newly discovered items.

---

## `gene_br_animation_update_loop_not_wired`

**动画效果代码存在但静止不动：Update 回调未注册** / Animation Implemented but Static — Update Loop Not Registered in Game Loop

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `intent:ai_output_correction`
- `symptom:animation_static_no_movement`
- `recent_animation_implemented`
- `update_loop_registration_missing`
- `floating_or_particle_effect`
- `cn_keywords:piaodong,yundong,meiyou,donghua,guanlu,shezhi`

**Preconditions:**
- 上一个 turn 刚刚实现了某种动态效果（浮动、飘动、粒子动画），用户报告效果「看起来没有移动」或「浮动效果不见」。
- 动画逻辑代码已写入目标文件（update 函数、位置累加、速度字段均存在），但视觉上静止不动。
- 这是区别于「空白屏幕」（NanoVG 渲染事件未绑定）的另一种无效果 bug：渲染本身正常，但动画帧每帧不更新。

**Evidence:** 9dc56f96 T08-T09: Two consecutive correction turns for floating background decoration effect. T07 had implemented the animation (colors + movement code written), but T08 (ai_output_correction, 15 steps, E:2, B:1, Read:3): '看起来并没有浮动效果，改为缓慢的向上飘动' — agent rewrote animation velocity logic (upward drift). T09 (bug_report, 17 steps, E:2, B:1, Read:3): '还是没有移动效果，检查是什么问题' — agent investigated and found the animation update function was not registered in the game loop's update callback. Fix: added SubscribeToEvent (or equivalent UrhoX update hook) to call the floating-animation update each frame. Build succeeded after fix, effect became visible. Root cause: the animation function (calculating position offsets per dt) existed but was never called per frame — common when implementing animations in a new file or component without hooking into the engine's update event. Distinct from gene_br_blank_screen_nanovg_render_event_unbound (that pattern: NanoVG render event not bound → nothing drawn; this pattern: drawing happens, but positions never change because update callback missing).

---

## `gene_br_pagination_level_index_offset_bug`

**分页关卡选择页第2页点击无法进关：关卡序号缺少页码偏移** / Level Select Pagination Bug — Page 2+ Click Fails Due to Missing Page Offset in Level Index

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `symptom:level_navigation_fails`
- `symptom:click_level_does_nothing_on_page2plus`
- `pagination_level_select_screen`
- `level_index_computation_error`
- `cn_keywords:dierye,dianjihouguanqajinru,xuanzeGuanqaye,fenye,suoyin,pianyi`

**Preconditions:**
- 关卡选择页面（level-select）实现了分页功能（第1页/第2页/...）。
- 用户报告：在第2页（或后续页）点击关卡后无法进入该关卡，但第1页点击正常。
- 关卡选择的点击回调中计算目标关卡序号的逻辑存在错误（通常是页内 index 未叠加页码偏移量）。

**Evidence:** 9dc56f96 T17 (8 steps, E:1, B:1, Read:2): '连连看选择关卡页面，切到第二页时，点击关卡后无法进入关卡，检查是什么问题' — user reports page 2 level clicks don't navigate. Agent: Read level-select.lua (link-match version) → identified click callback computing level index as itemIndex without adding page offset → Edit to fix: levelIndex = currentPage * LEVELS_PER_PAGE + itemIndex → Build success. Classic off-by-page bug: page 1 (index 0) works because 0 × N + i = i (correct), but page 2 (index 1) gives 1 × N + i which maps to correct levels — the fix is simple once located, but requires reading the callback to find the exact expression. Only 1 edit needed; resolution in 8 steps total.

---

## `gene_br_cloud_save_visual_state_unapplied`

**云存档迁移后皮肤/视觉状态刷新不持久：读取正确但未调用应用函数** / Cloud Save Migration — Skin or Visual State Not Applied on Load Despite Correct Data Read

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `cloud_save_migration_recent`
- `symptom:visual_state_not_applied_on_load`
- `log_shows_correct_data`
- `skin_or_outfit_not_loading`
- `refresh_or_restart_triggers_bug`
- `cn_keywords:pifuweibaoliou,shuaxin,huanzhuang,yunduanbaocun,jiazaishizhi`

**Preconditions:**
- 本 session 或近期 session 完成了从本地存档到云存档（cloud save）的迁移。
- 用户报告刷新或重启后皮肤/换装/视觉状态未被保留（显示为默认外观）。
- 日志中显示 [skinId] 或 [outfitId] 等键的值正确读取自云端，但游戏内渲染仍为默认皮肤。
- 问题在多次修复尝试后仍持续（可能存在多处保存/读取路径未同步更新）。

**Evidence:** 9df66fd4 T28-T31: 4-turn cascade after cloud save migration (completed in T27). T28 (bug_report, 17 steps): user reports skin not persisting after refresh — agent checks write path, appears to fix. T29 (ai_output_correction, 5 steps): user says still broken. T30 (bug_report, 12 steps): escalation — user provides more detail about behavior. T31 (bug_report, 11 steps): user pastes log evidence showing [skinId] reads correct value from cloud, but game renders default skin. Agent re-examines read path: cloud read callback stores skinId but does NOT call OutfitManager.applySkin — the apply-to-render call was missed in the migration. Fix: added applySkin(skinId) in the cloud read success callback. Build succeeded, persistence confirmed. Pattern: cloud save migration bugs typically manifest as a read-write split — write path migrated, read-apply path missed — and require 4+ turns to fully diagnose because write appears to succeed (log confirms) before read-apply is examined.

---

## `gene_br_nanovg_cross_context_image_handle_white`

**NanoVG 跨上下文图像句柄白色渲染：Router.replace 双重 init 触发，修复方向为移除所有 nvgDeleteImage** / NanoVG Cross-Context Image Handle White Render — Router.replace Double-Init, Fix by Removing All nvgDeleteImage

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `visual_artifact_white`
- `nanovg_image_rendering`
- `cross_page_navigation_trigger`
- `shared_component_regression`
- `escalating_scope`
- `cn_keywords:baise,tupian,bai,jiaose,baicheng`
- `page_switch_trigger`
- `init_double_call_symptom`
- `router_replace_lifecycle`
- `purchase_unlock_trigger`
- `ui_state_change_trigger`

**Preconditions:**
- 游戏中有 NanoVG 图像渲染（如 nvgCreateImage/nvgImagePattern），且某个或多个图像显示为白色方块。
- 问题在页面切换（Router.replace / replace 路由）或页面反复进入后出现，而非首次启动时。
- 涉及一个共享组件（如 fox-mascot.lua）在各页面的 init() 函数中创建 NanoVG 图像句柄，并在 init() 或 destroy() 中手动调用 nvgDeleteImage。
- 变体触发场景：问题在购买/解锁操作后出现（不经过页面切换），如购买皮肤后皮肤图像立即显示为白色。此时触发机制可能是购买成功回调引起了 UI 状态重置或组件重新渲染，间接触发了 nvgDeleteImage 被误调用，或图像句柄在状态变更中失效。修复方向与页面切换变体相同：移除 init() 和 destroy() 中的 nvgDeleteImage 调用。

**Evidence:** a09c411b T08-T11: 4-turn escalating white-image bug cascade. T08 (bug_report, ~15 steps, 1 edit, 1 build): user reported '主线模式，左下角的角色图像，现在是一块白色的'. Agent: Read fox-mascot.lua → identified init() has 'delete-then-create' pattern (nvgDeleteImage old → nvgCreateImage new) → changed to 'create-first-then-delete' (create new → nvgDeleteImage old), reasoning this is a safer swap. Build → success, but WRONG FIX DIRECTION — old handle is from a different nvgCtx_, deleting it after creating the new one still corrupts the state. T09 (bug_report, 108 steps, 4 edits, 3 builds): user reported '主线模式，和游戏内，的图片都变为了白色' — scope ESCALATED to ALL images. Agent: deep investigation, multiple re-reads of adventure/init.lua, fox-mascot.lua, Grep chains, Task SA for Router lifecycle. Multiple wrong hypotheses explored (constant extraction from T05 broke something? adventure/init.lua foxImage_ variable shadowing?). Eventually: 4 edits reverting T08 change + additional changes, 3 builds, but still not fully fixed. T10 (bug_report, ~20 steps, 2 edits, 1 build): user reported partial fix — '现在主线模式和游戏内显示正常了，但是自由模式选择游戏的页面左下角的角色变成白色了'. Agent: narrowed to free-mode page specifically, applied targeted fix. T11 (bug_report, ~30 steps, 3 edits, 1 build): user reported '在主线模式，自由模式页面切换时，左下角的角色就会变成白色' — trigger precisely identified as mode switching. Agent: (1) investigated Router.replace lifecycle → confirmed destroyTop()→showPage()→create()→setActive() causes init() to be called TWICE on same nvgCtx_. (2) FINAL FIX: removed ALL nvgDeleteImage calls from fox-mascot.lua init() AND adventure/init.lua (which had a separate foxImage_ variable). (3) Build → success. Root cause: NanoVG creates a separate nvgCtx_ per page; image handles from one context are invalid in another. Router.replace lifecycle double-calls init() on the same context, and any nvgDeleteImage in init() creates handle-lifecycle inconsistency. The safe pattern is: create handles in init(), never explicitly delete them, rely on nvgCtx_ destruction (page destroy) for cleanup. Key learning: wrong fix in T08 (swap order) → regression in T09 (all images white) → 108-step over-investigation → final root cause confirmation in T11.

e7d71628 T03 (intent: feature_modification, target: visual_style): user reported '购买解锁后，突变会变成白色的' (after purchase unlock, the mutation becomes white). This is a distinct trigger variant from the Router.replace double-init case (a09c411b) — the white rendering is triggered by a purchase/unlock event rather than page navigation. Root cause is likely the same: nvgDeleteImage called in init()/destroy() with a stale handle from a different nvgCtx_, invalidating the newly created image handle when the unlock causes a re-render or component re-initialization. The fix direction is identical: remove all nvgDeleteImage calls from init() and destroy().

---

## `gene_br_auto_win_not_triggered`

**自动胜利条件未触发 — 检查条件判断路径与事件分发** / Auto-Win Condition Not Triggered — Diagnose Win-Condition Check Path and Event Dispatch

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:game_logic`
- `auto_trigger_not_firing`
- `win_condition_logic`
- `recent_mode_bifurcation_impl`
- `cn_keywords:zidongshengbai,tongguantiaojian,buhui,jiancha_shenme_yuanyin`

**Preconditions:**
- 用户报告：某个本应在达成条件后自动触发的游戏结束/胜利事件没有发生（如「达成通关分数后不会自动胜利」）。
- 该自动触发逻辑是在最近 1-2 个 turn 内刚实现的（如双轨胜利条件分叉、新增的 checkWin 调用）。
- 用户描述的是「条件已达成，但预期事件没有发生」，而不是「程序崩溃」或「功能完全不存在」。

**Evidence:** bc3f2ce9 T40 (19 steps, 1 edit, 5 reads, 1 build): '现在主线消消乐，达成通关条件后不会自动胜利，检查是什么原因'. This bug occurred immediately after T36+T38 implemented mode-bifurcated win conditions for match-3. Agent: (1) 5x Read: read match-3 game logic files (gameplay.lua, score tracking, win check, event dispatch). (2) Identified root cause: the auto-win trigger in the main story path was not correctly dispatching the win event (likely a conditional branch error or missing function call). (3) 1 Edit: minimal fix to the win condition check / event dispatch. (4) Build success. Pattern: auto-win bugs almost always follow recent mode-bifurcation implementation — the bifurcation introduces conditional branches, and one path (typically the new auto-win path) has a missing or misrouted function call. Reads (5x) >> Edits (1x): diagnosis is read-heavy, fix is minimal. Compare with gene_br_animation_update_loop_not_wired (feature implemented but event/update not registered): both share the 'implemented but not wired' root cause; this gene is the win-condition specialization.

---

## `gene_elp_board_init_bypass_data_transform_nil`

**棋盘初始化绕过数据转换层导致的 nil 字段崩溃 — 主线模式 levelData 未经 loader 转换** / Board Init Bypasses Data-Transform Layer — Story-Mode Raw levelData Skips level-loader, Causing nil Field Crash at Runtime

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `runtime_error_nil_field_access`
- `error_field:wallSet_or_similar_derived_field`
- `story_mode_level_entry`
- `board_or_grid_initialization`
- `cn_keywords:wallSet,nil,board,initializaion,storyline,adapter`

**Preconditions:**
- 错误日志显示 `attempt to index a nil value (field 'wallSet')` 或类似的 nil 字段访问，发生在棋盘/网格渲染或逻辑调用中。
- 游戏在主线/故事模式下进入关卡时崩溃，自由模式无此问题。
- 项目有独立的 level-loader 或 data-transform 模块，负责将原始关卡数据转换为游戏运行时所需格式（如 walls[] → wallSet{} 哈希表）。

**Evidence:** bdf118ee T03 (38 steps, 12 Greps, 4 Reads, 1 Edit): user pasted error log with 62 repeated errors 'attempt to index a nil value (field wallSet)' at board:81 in P1PZ_HandleNanoVGRender. Agent: TodoWrite (fix wallSet nil). Read board.lua → found Board.new(levelData) calls self:reset() which sets self.wallSet = {} from walls data. Read gameplay.lua → confirmed call site. Read level-loader.lua → confirmed M.load(raw) transforms walls[] → wallSet{}. Read adapter.lua at line 588 → found storyline branch: 'levels_ = { ctx.storylineOpts.levelData }' passes raw data directly, bypassing levelLoader.load(). Agent said 'problem is clear: storyline mode uses raw levelData directly'. Edit adapter.lua → wrapped raw data with levelLoader.load(). Then Grep p2/p3/p4 adapters for 'storylineOpts.levelData' → all three had same bypass. Checked p2/p3 level-loaders for matching load functions. Build → confirmed fix.

---

## `gene_elp_story_level_field_name_adapter_mismatch`

**主线关卡字段名与 Adapter 不匹配导致加载失败 — 运行时日志定位 nil 拼接，跨游戏 Grep 统一修复** / Story-Level Config Field Name Mismatch in Adapter — Runtime Log Pinpoints nil Concatenation, Cross-Game Grep Fixes All Adapters

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `intent:bug_report`
- `runtime_error_nil_concatenation`
- `story_level_loading_failure`
- `persistent_bug_repeated_report`
- `adapter_field_name_mismatch`
- `cn_keywords:gamingLoadFailed,story,levelId,lv.id,adapter,nil`

**Preconditions:**
- 玩家进入主线关卡时显示「游戏加载失败，请返回重试」，且该问题在修复后仍复现（用户连续两次报告同一问题）。
- 错误日志或运行时日志中存在 `attempt to concatenate a nil value (field 'id')` 或类似的 nil 字段拼接错误，发生在 adapter.lua 中。
- 项目同时存在主线模式（story-N 关卡，使用自定义字段如 `levelId`）和各游戏模块的自由模式（使用字段如 `id`），两套数据格式字段名不同。

**Evidence:** bdf118ee T04 (52 steps): user said '进入第二关时，显示游戏加载失败，请返回重试'. Agent: Read storyline.lua, story-2.lua, game-container/init.lua. Identified state machine transition issue (game container state not IDLE). Made fix but problem persisted. | bdf118ee T05 (20 steps): user said 'story-2还是显示游戏加载失败'. Agent: Bash 'cat /opt/log/dev/user_script.log | tail -80' → found 'attempt to concatenate a nil value (field id)' at p2-memory-flip/adapter.lua:398. Read adapter.lua:390-410 → found 'logger.info(MODULE, "storyline gameplay started" .. lv.id)' — uses lv.id. Read story-2.lua → field is 'levelId', not 'id'. Grep 'storyline gameplay started.*lv\.id' across all adapters → found p2 and p3 both have same mismatch (p1 correctly uses id because its levels actually use that field). Fixed p2 and p3 adapters. Build passed.

---

## `gene_br_transition_overlay_stuck_black_wasm`

**NanoVG全屏遮蔽转场 → 持续黑屏 + WebAssembly崩溃级联诊断** / NanoVG Fullscreen Overlay Transition → Persistent Black Screen + WASM Crash Cascade Diagnostic

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `intent:error_log_paste`
- `symptom:screen_stays_black`
- `nanovg_overlay_recently_implemented`
- `transition_fade_feature`
- `taptap_maker_platform`
- `wasm_indirect_call_to_null`

**Preconditions:**
- Screen transition/fade overlay was recently implemented using NanoVG full-screen rect rendering
- Bug report says screen fades to black and never recovers (stays permanently black)
- Platform is TapTap Maker (web/WASM runtime)

**Evidence:** d8f96672 T8 (no agent run) + T9 (54 steps, 16 edits, 1 build) + T10 (13 steps, 4 edits, 1 build) + T11 (40 steps, 14 edits, 2 builds) + T12 (18 steps, 9 edits, 1 build): 5-turn cascade. T8: user sent '点击进入和退出游戏时，增加黑屏遮蔽淡入淡出效果' — no agent run (user immediately re-sent in T9). T9: user re-sent '点击进入和退出游戏时，增加遮蔽屏幕的转场效果'. Agent: EnterPlanMode + 2 Task SAs (plan + implementation subtasks) + Grep ×3 + Read ×10 + Edit ×10 + Write ×1 + build. Implemented full NanoVG screen overlay transition. T10: user reported '点击推箱子后，屏幕渐黑，然后就一直维持全黑了'. Agent: Read ×2 → Edit ×2 → build. First fix attempt — partial, bug persisted. T11: user reported '现在仍然是变成全黑' (escalation, still black). Agent: Grep ×4 + Read ×4 + Edit ×8 + Write ×2 + build ×2. Deep investigation of overlay lifecycle. T12: user pasted TapTap Maker Error Report — RuntimeError: indirect call to null (WebAssembly crash at engine level). Agent: Write + Read + Edit ×4 + build. Fixed callback registration. Pattern: new_feature NanoVG overlay (T9, PlanMode+2SA, 54 steps) → bug_report persistent black (T10, 13 steps, partial fix) → escalation still black (T11, 40 steps, deep investigation) → error_log_paste WASM crash (T12, 18 steps, callback fix). 5-turn implementation+debug cascade.

---

## `gene_elp_event_handle_userdata_type_error`

**事件取消订阅 API userdata 类型错误：传入字符串而非订阅句柄导致批量崩溃** / UnsubscribeFromEvent Userdata Type Error — String Passed Instead of Subscription Handle Causes Flood of Errors

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `symptom:hundreds_identical_errors`
- `symptom:userdata_expected_string_got`
- `symptom:timer_or_event_callback_repeated_fire`
- `api:UnsubscribeFromEvent`
- `cn_keywords:unsubscribefromevent,userdata,jiechu,dingyue`

**Preconditions:**
- 错误报告中出现大量相同的错误条目（数百至数千次），所有错误来自同一文件的同一行。
- 错误信息包含 userdata 类型期望但传入了 string（或反之）的类型不匹配描述。
- 错误发生在事件订阅/取消订阅 API 的调用处，常见于 UrhoX 的 `UnsubscribeFromEvent`、定时器取消等场合。
- 通常在近期添加或修改了某个定时器循环（Timer/UpdateEvent/PostUpdateEvent）之后发生，且该循环在每帧都尝试取消订阅。

**Evidence:** e2076a78 T1 (6 steps): error report contained 904 identical errors from health-advisory.lua:98 in HealthAdvisory_FadeTimer. The error was userdata type mismatch on UnsubscribeFromEvent — the code was calling UnsubscribeFromEvent('UpdateEvent') with a string event name instead of passing the userdata handle returned by SubscribeToEvent. UrhoX requires the actual subscription object (userdata), not a string. Agent: read health-advisory.lua, identified the call site at line 98, changed parameter from string to the saved subscription handle, build, 904 errors eliminated. Key distinction from gene_elp_nanovg_api_return_type_mismatch: that gene covers NanoVG C-binding return value misuse (table vs multi-return); this gene covers UrhoX event subscription API where the caller must retain and pass the opaque handle returned by SubscribeToEvent.

---

## `gene_elp_lua_api_arg_type_table_not_string`

**Lua API 参数类型错误：table 传入期望 string 的 Get 函数（新功能引入新数据结构时的常见错误）** / Lua API Argument Type Error — Table Passed to Get() Expecting String (Common When New Data Structures Introduced)

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `stacktrace_in_prompt`
- `lua_runtime_error`
- `symptom:bad_argument_string_expected_got_table`
- `shared_component_init`
- `new_feature_implementation_prior_turn`
- `cn_error:bad_argument_string_expected_got_table`
- `storage_or_data_api_call`
- `outfit_or_skin_system`

**Preconditions:**
- 用户粘贴了包含 TapTap Maker 结构化头部信息的运行时错误报告。
- 错误信息为 ，发生在某个共享模块（如 outfit-manager、storage-manager）的 init 函数中，从主入口（main:Start）调用。
- 触发场景：刚实现了一个新功能（如皮肤购买/换装系统），引入了新的数据结构（如 skinConfig table 或皮肤信息对象），并将该 table 作为参数传递给了一个期望字符串键（key）的 API 函数（如 Storage.Get(key)、DataManager.Get(key)）。
- 错误发生在模块的 init 阶段，说明数据结构初始化时即出错，而非运行时动态调用。

**Evidence:** e7d71628 T01 (intent: error_log_paste, urgency: high): user pasted TapTap Maker Error Report immediately after T00 which implemented a new skin purchase/outfit system. Error: [string "shared/outfit-manager"]:435: bad argument #1 to 'Get' (string expected, got table). Stack: [C] Get → outfit-manager:435 init → main:62 Start. Pattern: new feature implementation (T00) introduced a skin data structure (table) that was incorrectly passed as the key argument to a storage Get() API in the module init function. The error fires at startup (main:Start → init) because the wrong type is passed immediately during initialization, not during user interaction. Distinct from gene_elp_nanovg_api_return_type_mismatch (which covers wrong assumption about return type); this gene covers wrong argument type when calling an API.

---

## `gene_elp_callback_closure_nil_entity_id`

**Lua 回调闭包实体 ID 为 nil：共享弹窗组件回调未正确捕获或传递实体标识符** / Lua Callback Closure Entity ID Nil — Shared Popup Component Callback Fails to Capture or Pass Entity Identifier

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `stacktrace_in_prompt`
- `lua_runtime_error`
- `symptom:concatenate_nil_local_variable`
- `shared_popup_component_callback`
- `new_feature_implementation_prior_turn`
- `cn_error:attempt_to_concatenate_nil_value_local`
- `profile_or_entity_page`
- `purchase_or_unlock_flow`

**Preconditions:**
- 用户粘贴了包含 TapTap Maker 结构化头部信息的运行时错误报告。
- 错误信息为  或类似的命名实体 ID（levelId、itemId、entityId）nil 拼接错误，发生在一个回调函数 (local 'cb') 内部。
- 调用堆栈显示：共享弹窗组件（如 purchase-popup、confirm-dialog）的 handleClick 方法调用了父页面注册的回调函数，而该回调函数内部引用了一个本应非空的局部变量（skinId、levelId 等实体标识符）。
- 触发场景：刚实现了新的购买/解锁流程，父页面（如 profile/init）向共享弹窗组件注册了一个匿名回调函数，该回调函数需要访问当前选中实体的 ID，但 ID 变量（skinId）在回调被调用时为 nil。

**Evidence:** e7d71628 T02 (intent: error_log_paste, urgency: high): user pasted TapTap Maker Error Report after fixing T01 error. Error: [string "pages/profile/init"]:485: attempt to concatenate a nil value (local 'skinId'). Stack: profile/init:485 local 'cb' → purchase-popup:145 handleClick → profile/init:446 upvalue 'handleClickAt' → profile/init:543 Profile_HandleMouseDown. Pattern: the newly created purchase-popup shared component (T00) is registered with a callback from profile/init. When the user clicks confirm in the popup, handleClick calls the callback cb. Inside cb, skinId is nil — the variable was either not captured in the closure at registration time (defined before the skin was selected), or the popup component was expected to pass the skinId back as an argument to cb() but does not. The callback chain: user click → Profile_HandleMouseDown → handleClickAt → purchase-popup registers cb → popup.handleClick calls cb() → cb fails because skinId not in scope. Root pattern: shared popup component with callback interface where the entity identifier is not properly threaded through the closure or argument chain.

---

## `gene_br_bulk_formula_edit_stale_override`

**批量公式更新后遗漏关卡旧值残留：Grep 诊断 + 残缺输入触发补丁修复** / Post-Bulk-Formula-Edit Stale Level Override — Grep-Only Diagnosis Then Fragment-Triggered Patch Fix

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:game_logic`
- `follows_arithmetic_formula_bulk_edit`
- `stale_value_after_bulk_edit`
- `grep_only_diagnosis_no_edits`
- `deferred_fix_on_fragment_followup`
- `cn_keywords:rengran,jiushi,haishi,meibian,jiancha,wenti,xuyao`

**Preconditions:**
- 前一 turn（或本 session 近期 turn）对某个游戏的所有关卡参数执行了算术公式批量 Edit（如「第一关3000，每关增加200」），逐一 Edit 了所有关卡的配置字段。
- 用户随后报告某一特定关卡的该参数「仍然是旧值」（如「第十四关分数需求仍然是9000」），说明批量 Edit 遗漏了该关卡，或该关卡存在独立的硬编码覆盖值未被覆盖。
- 用户描述问题时使用「仍然是X」「还是X」「没变」「检查是什么问题」等表述，并给出具体旧值数值（问题可量化）。
- 用户在诊断结果输出后，发送极短/残缺输入（如「需要」「好」「是」「修」）作为跟进，表明「请执行上一轮识别出的修复」。

**Evidence:** f4dd8c16 T4-T6: T4 (P3, 35 steps, 24 edits, 1 build): '基础值修改为第一关3000，之后每关增加200'. Agent: Grep (locate score config) → Read → TodoWrite → 24x mcp__mkr__Edit (formula 3000+(n-1)*200 applied per level) → respond → Build success. T5 (P4, 3 steps, 0 edits): '现在消消乐第十四关的分数需求仍然是9000，检查是什么问题'. Agent: respond → Grep → respond — diagnosed that Level 14's old value 9000 survived the T4 bulk edit, reported root cause to user, NO edits in this diagnostic turn. T6 (P5, 15 steps, 9 edits, 1 build): '需要'. Fragment input — agent inferred from T5 diagnosis context that user wants the stale value fixed. Agent: respond → TodoWrite → 9x mcp__mkr__Edit → respond → Build success → TodoWrite → respond. The 9 edits address Level 14 plus other levels whose stale values the Grep in T5 had revealed. Pattern: arithmetic formula bulk edit (T4) → stale override reported (T5) → grep-only diagnosis, no fix (T5) → fragment '需要' (T6) → batch patch edits covering all Grep-identified missed locations + build.

---

## `gene_aoc_display_config_numerical_mismatch`

**显示文案数字与配置实际数量不符的修正：三源对齐工作流** / Display Text Numerical Mismatch — Align Subtitle / Caption Count with Actual Config

Category: `diagnostic`

**Signals:**
- `intent:ai_output_correction`
- `intent:inspection_review`
- `target:game_logic`
- `symptom:display_text_number_ne_actual_count`
- `cn_keywords:xianshi,shiji,jiancha,shuzi,zhang,ge,peizhiwen,fubiaoti,shuliang,budui`

**Preconditions:**
- 用户发现游戏中某处显示文字（副标题、提示文案、UI 标签等）中的数字与游戏配置文件中的实际数量不符（如「副标题写36张卡片，但配置中只有32张图片」）。
- 该不一致是 AI 在之前实现功能时引入的笔误——写副标题时使用了估算值或错误记忆，未对照配置核实。
- 用户要求：①检查文档 ②检查游戏内配置 ③修复两处的数字 ④更新文档。
- 通常同时提供了不一致的描述（「副标题是X，但实际上是Y」），使 AI 可以直接定位需要核查的两个来源。

**Evidence:** fa1daf15 T5 (54 steps, 18 edits, 0 builds): user prompt '18关显示的副标题是36张卡片的万花筒挑战，但是实际上是32张图片，检查这个文档和游戏内的配置，修复这些问题，并更新文档'. User identified that level 18's subtitle text claimed '36张卡片' but the actual image array in the game config had only 32 images. Agent: (1) 5x TodoWrite (task planning and progress). (2) 8x mcp__mkr__Read (level config files, game adapter, subtitle source file). (3) 5x Grep (locate the '36' occurrences in docs and image list definitions in config). (4) 18x mcp__mkr__Edit (fix the numerical value in the game config/UI text, fix the document description, update 主线关卡总览.md, update 完成记录.md). (5) 16x respond_to_user (interim status messages throughout the fix). Confirmed fix: subtitle had '36张卡片', actual image array in config had 32 entries → changed subtitle to '32张卡片', updated 主线关卡总览.md level 18 entry, appended fix note to 完成记录.md. This is ai_output_correction: the model introduced the wrong number during a prior feature-build turn by writing the subtitle text without counting the actual images in the config. The intent classification correctly flagged is_correction_of_ai_work=true. Step count (54) is high because the agent must read multiple files to verify before editing — never correct a numerical claim without first confirming the ground-truth count from config data.

---

## `gene_inq_mcp_tool_unavailable_first_turn`

**MCP工具首轮不可用：清晰告知并列出可用工具** / MCP Tool Unavailable on First Turn: Graceful Disclosure with Available Tools List

Category: `diagnostic`

**Signals:**
- `intent:inquiry`
- `mcp_tool_invocation_command`
- `tool_not_found_in_available_tools`
- `tool_name_specified_in_prompt`
- `no_attached_doc`

**Preconditions:**
- User requests a specific named MCP tool
- That tool is not present in the agent's current available tools list
- No fallback or alternative tool is specified by the user

**Evidence:** 

---

## `gene_aoc_logic_reexplain_cluster`

**AI逻辑修正反复聚集 — 同一约束多轮重述** / AOC Logic Re-explanation Cluster — Same Constraint Restated Across Consecutive Correction Turns

Category: `diagnostic`

**Signals:**
- `intent:ai_output_correction`
- `consecutive_aoc_ge_2`
- `same_target_artifact_consecutive`
- `escalating_constraint_specificity`
- `logic_mechanic_correction`
- `correction_not_applied_signal`

**Preconditions:**
- 用户已发送1次 ai_output_correction，AI 作出了修改，但下一轮用户再次用 ai_output_correction 指出同一逻辑约束未被正确实现。
- 同一逻辑规则（如能量扣除时机、删除特定代码路径、方向判断）被用不同措辞重复说明2-3次。
- 后续 AOC turns 的措辞比第一次更精确、更具体，表明 AI 的修改方向根本上是错的，而非细节偏差。

**Evidence:** 08754637 T97-T99: 3 consecutive AOC turns about the charge-mechanic energy rule. T97: '纠正蓄力机制不应扣除能量'. T98: '纠正蓄力时不扣能量的逻辑错误'. T99: '纠正蓄力技能逻辑：蓄力阶段不耗能，持续发射阶段才耗能且可手动停止' — user restated the invariant with increasing specificity, breaking it into two distinct phases, indicating the AI kept treating it as a single-state rule rather than a two-phase state machine. T299-T301: 3 consecutive AOC about beam deletion methodology. T299: '要求用正规方式删除指定光束，避免误恢复已删光束'. T300: '删除AI新添加的2条拖尾，拖尾应加在最长光翼上'. T301: '质疑新增光束的必要性，并要求若必须则使其角度与最高光束重叠'. T834-T835: 2 consecutive AOC about damage formula. T834: '质疑AI提供的怪物伤害公式，认为应为cycle+4'. T835: '质疑AI拉取数据错误，怀疑残留代码导致误导'. Pattern: in all cases the AI made a partial or directionally-wrong correction on first AOC, triggering a 2nd (and sometimes 3rd) AOC with more explicit constraint specification. The escalating specificity is the diagnostic signal.

---

## `gene_elp_platform_noise_continue_pattern`

**平台噪声错误日志 — 确认后继续工作模式** / Platform Noise Error Log — Acknowledge-and-Continue Pattern Without Unsolicited Fix

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `recurring_same_error_type`
- `platform_level_error`
- `followed_by_unrelated_intent`
- `no_explicit_fix_request`
- `next_intent_not_bug_report`

**Preconditions:**
- 用户粘贴错误日志，但错误类型为平台层面的非阻断性警告（如 TapTap Maker 的「View exceeds maximum limit」）。
- 该错误在同一会话中已出现过多次（3次以上），用户每次粘贴后都继续进行不相关的工作（feature_modification 或 inquiry），而非明确要求修复该错误。
- 用户粘贴行为本身是「记录/分享」性质，而非「请修复」请求——下一轮的 intent 不是 bug_report 或 ai_output_correction。

**Evidence:** 08754637: 'View exceeds maximum limit' platform error appeared 11 times across the 854-turn session. Post-paste intents: T58(elp)->T59(fm: remove top beam); T66(elp)->T67(inq: query player speed param); T94(elp)->T95(br: compound bug fix, unrelated to this error); T133(elp)->T134(fm: enlarge player bullet); T164(elp)->T165(nf: implement main-menu music); T207(elp)->T208(br: post-death position bug). In no case did the user request a fix for the 'View exceeds maximum limit' error itself; all follow-up turns addressed unrelated concerns. This error is a TapTap Maker/UrhoX platform constraint triggered when the scene creates too many UI View nodes; it is non-fatal and users implicitly accept it as a background constraint during active development.

---
