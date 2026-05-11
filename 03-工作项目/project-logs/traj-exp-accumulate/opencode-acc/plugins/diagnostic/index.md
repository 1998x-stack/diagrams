# diagnostic — Gene Index

**Gene count:** 12

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_br_minimal_bug_fix` | Minimal Bug Fix — Read-Edit-Build Cycle for UI Defects | diagnostic | 2x: 014354fc, 13683faf | `intent:bug_report`, `target:ui_layout`, `target:game_logic` |
| 2 | `gene_nf_subagent_fallback_to_direct` | Subagent Delegation Failure to Direct Tool Fallback | diagnostic | 1x: 0428882b | `intent:new_feature`, `subagent_404_error`, `Task_tool_failure` |
| 3 | `gene_br_bug_retry_escalation` | Bug Retry Escalation — Same Bug Reported Across Consecutive Turns with Frustration Signals | diagnostic | 4x: 374e4eb7, bdf118ee, 4f916c20 +1 | `intent:bug_report`, `same_bug_consecutive_turns_ge_2`, `escalating_frustration_language` |
| 4 | `gene_elp_error_log_diagnostic` | Error Log Diagnostic — Stack Trace Parsing to Surgical Fix | diagnostic | 7x: 374e4eb7, 61467d20, 76b0acb1 +4 | `intent:error_log_paste`, `stacktrace_in_prompt`, `mentions_specific_file` |
| 5 | `gene_elp_multi_error_diagnostic_cascade` | Multi-Error Diagnostic Cascade — Second Error Exposed After First Fix | diagnostic | 1x: 3ee927f3 | `intent:error_log_paste`, `stacktrace_in_prompt`, `mentions_specific_file` |
| 6 | `gene_elp_error_log_retry_with_diagnostic_upgrade` | Error Log Retry Escalation — Consecutive Error Log Pasting with Diagnostic Method Upgrade | diagnostic | 1x: 3ee927f3 | `intent:error_log_paste`, `stacktrace_in_prompt`, `same_error_consecutive_turns_ge_2` |
| 7 | `gene_br_bug_retry_with_diagnostic_upgrade` | Bug Retry with Diagnostic Upgrade — Consecutive Bug Reports with User-Provided Debug Info | diagnostic | 1x: 9df66fd4 | `intent:bug_report`, `same_bug_consecutive_turns_ge_3`, `still_not_working_pattern` |
| 8 | `gene_br_white_image_cascade` | White Image Rendering Bug Cascade — Cross-Context Spread with Escalating Investigation | diagnostic | 1x: a09c411b | `intent:bug_report`, `target:visual_style`, `white_image_rendering` |
| 9 | `gene_fm_investigation_without_implementation` | Feature Modification Investigation Without Implementation — Heavy Read, Zero Edit, Session Terminated | diagnostic | 1x: e948a3d9 | `intent:feature_modification`, `zero_edits_zero_builds`, `read_heavy_ge_5` |
| 10 | `gene_aoc_multi_turn_escalation` | AI Output Correction Escalation — Consecutive Misunderstanding with Frustration Signals | diagnostic | 1x: 08754637 | `intent:ai_output_correction`, `consecutive_aoc_ge_3`, `escalating_frustration_language` |
| 11 | `gene_elp_recurrent_engine_error` | Recurrent Engine Limit Error — View Exceeds Maximum Limit Repeatedly Reported | diagnostic | 1x: 08754637 | `intent:error_log_paste`, `same_error_recurring_across_session`, `view_exceeds_maximum_limit` |
| 12 | `gene_br_bug_to_elp_diagnostic_upgrade` | Bug Report to Error Log Diagnostic Upgrade — Natural Language to Stacktrace Escalation | diagnostic | 1x: 3ee927f3 | `intent:bug_report`, `intent:error_log_paste`, `bug_report_then_error_log` |

---

## `gene_br_minimal_bug_fix`

**最小化Bug修复模式** / Minimal Bug Fix — Read-Edit-Build Cycle for UI Defects

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:ui_layout`
- `target:game_logic`
- `single_file_fix`
- `read_edit_build_cycle`
- `minimal_change`
- `grep_for_root_cause`

**Preconditions:**
- 用户报告一个具体的bug（如UI交互异常、游戏逻辑错误、显示错位）。
- 问题范围明确，指向单一文件或组件。
- 不需要大规模重构，只需定位并修复具体问题。
- 对于game_logic类bug（如章节显示错位、点击穿透），可能需要Grep搜索相关关键词来定位根因。

**Evidence:** 014354fc: T3: debug按钮无法点击→读取sound-test-panel.lua→3次edit→1次build→修复。T4: 音效测试UI位置异常→读取sound-test-panel.lua→2次edit→1次build→修复。两个bug均为read→edit→build的简洁循环，无多余操作。13683faf: 扩展了game_logic类bug模式。T2: 章节标题重叠('第一章和第二章同时显示')→1 Edit+1 build→修复。T3: 章节-页码错位('第三页显示第四章')→Read+Edit+build→修复。T5: 点击穿透('点击忠告页面直接进入关卡')→2 Reads+3 Greps+2 Edits+1 build→修复。T5展示了game_logic bug需要Grep辅助定位的特点（搜索事件处理、遮罩层相关代码），与UI bug的纯Read定位不同。

---

## `gene_nf_subagent_fallback_to_direct`

**子Agent失败降级为直接探索** / Subagent Delegation Failure to Direct Tool Fallback

Category: `diagnostic`

**Signals:**
- `intent:new_feature`
- `subagent_404_error`
- `Task_tool_failure`
- `fallback_to_glob`
- `fallback_to_direct_read`
- `localization_without_edit`

**Preconditions:**
- 用户提出新功能需求，Agent 尝试通过 Task 子 Agent 探索代码库。
- 子 Agent 因 404 错误全部失败（环境限制或平台不支持子 Agent 恢复）。
- Agent 需要自行完成代码定位工作，无法委托给子 Agent。

**Evidence:** 4 subagents launched (a53e615, a5ca1be, a9418bf, a9b1bff). a9b1bff partially explored /workspace/scripts/ via Bash before also hitting 404. Agent then fell back to Glob (steps 3-4, 9-10) and mcp__mkr__Read (steps 6-8, 11-12), reading 6 files: router.lua, storyline/init.lua, adventure-sfx.lua, adventure/init.lua, home/init.lua, main menu. Session terminated by API error before any edit could be made. Pattern: 404 -> Glob -> Read -> terminate.

---

## `gene_br_bug_retry_escalation`

**Bug重试升级模式** / Bug Retry Escalation — Same Bug Reported Across Consecutive Turns with Frustration Signals

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `same_bug_consecutive_turns_ge_2`
- `escalating_frustration_language`
- `still_only_once_pattern`
- `target:game_logic`
- `minimal_edit_per_retry`
- `build_after_each_retry_fix`

**Preconditions:**
- 用户报告一个bug后，Agent进行了修复并build。
- 用户在接下来的2-3个连续turn中报告同一个bug仍然存在，使用'还是'、'仍然'、'依旧'等词语。
- 每次报告的措辞略有变化但指向同一问题（如'只会显示一个聊天'→'还是只能点击依次'→'还是只能点击一次'）。
- 这是用户 frustration 升级的信号——说明Agent的前一次修复没有真正解决问题根因。
- 目标产物通常是game_logic类bug（点击事件处理、状态管理、计数器逻辑）。

**Evidence:** T19: '修改主页面，点击角色的聊天，现在只会显示一个聊天，之后点击就无效了'→24步(10 respond+8 Read+4 Grep+1 Edit+1 build)。Agent读取fox-mascot.lua等文件，修改聊天点击逻辑→build。T20: '还是只能点击依次'→0步（空turn，可能是API错误或用户立即发送）。T21: '还是只能点击一次'→17步(6 respond+4 Read+2 Grep+2 build+2 Glob)。Agent再次读取fox-mascot.lua、chat-bubble.lua等，执行第二次修复→2次build。典型的'报告→修复→还是不行→再修复'模式，用户使用'还是'表达frustration。T20的0步可能是API错误或用户连续发送，T21的'还是只能点击一次'与T19的'只会显示一个聊天'指向同一问题。 bdf118ee扩展了此模式的"加载失败"变体：T03: "进入第二关时，显示游戏加载失败，请返回重试"→52步(17 respond+13 Read+9 Edit+6 TodoWrite+5 Grep)。Agent读取多个文件诊断加载失败根因→9 Edit修复→respond确认。T04: "story-2还是显示游戏加载失败，请返回重试"→20步(8 respond+6 Grep+2 Read+2 Edit+1 Bash)。用户使用"还是"表达同一bug仍存在→Grep定位→2 Edit修复→Bash验证。与374e4eb7不同——后者是game_logic点击事件bug(聊天点击无效)，本session是game_logic加载/初始化bug(关卡数据加载失败)，但"报告→修复→还是不行→再修复"模式完全一致。T04的20步比T03的52步显著缩短，说明Agent在第二次报告时更快定位问题。 4f916c20扩展了此模式的'Web剪贴板bug'变体：T15: '输入关卡数据UI，无法粘贴和输入数据'→10步(7 Grep+3 respond)。纯诊断模式，7次Grep搜索→0 Edit。T16: 'build'→2步。T17: 'web无法使用粘贴'→33步(7 Grep+6 Edit+4 Read+4 TodoWrite)。用户提供更多上下文→7 Grep+4 Read定位→6 Edit修复→build。与374e4eb7的game_logic点击事件bug和bdf118ee的加载失败bug不同，本session是Web剪贴板输入bug，但'报告→诊断→build→再报告(带更多上下文)→修复'模式完全一致。 d8f96672展示了此模式的'错误日志升级'变体：T10: '点击推箱子后，屏幕渐黑，然后就一直维持全黑了'→13步(6 respond+2 Read+2 Edit+2 Todo+1 build)。转场效果bug首次报告→Edit修复→build。T11: '现在仍然是变成全黑'→40步(16 respond+8 Edit+4 Grep+4 Todo+4 Read)。用户使用'仍然是'表达同一bug仍存在→Agent扩大调查范围(4 Grep+4 Read)→8 Edit修复→2 build。T12: 粘贴TapTap Maker错误报告(18步,4 Edit+5 Write+1 build)。用户在build后测试仍然失败→直接粘贴原始错误日志(WebAssembly indirect call to null)→Agent切换到错误日志诊断模式→4 Edit+5 Write修复→build。典型的'报告(13步)→仍然是(40步,扩大调查)→错误日志(18步,诊断升级)'管线。与374e4eb7的game_logic点击事件bug不同——本session是转场效果渲染bug，但'报告→修复→仍然是→扩大调查→诊断升级'模式完全一致。T12的错误日志粘贴是诊断方法的终极升级——从自然语言描述到原始错误堆栈。模式跨4个会话确认。

---

## `gene_elp_error_log_diagnostic`

**错误日志诊断模式** / Error Log Diagnostic — Stack Trace Parsing to Surgical Fix

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `stacktrace_in_prompt`
- `mentions_specific_file`
- `error_count_ge_10`
- `same_error_repeated`
- `Grep_for_error_line`
- `Read_target_file`
- `single_edit_fix`
- `build_after_fix`

**Preconditions:**
- 用户直接粘贴原始错误日志/崩溃报告/堆栈跟踪，没有附加指令。
- 错误日志包含文件名和行号（如fox-mascot.lua:337）。
- 同一错误重复出现多次（如59次相同的arithmetic on table value错误）。
- 这是高优先级问题——运行时错误影响游戏正常运行。

**Evidence:** T23: 用户粘贴TapTap Maker错误报告，59次相同错误'fox-mascot:337: attempt to perform arithmetic on a table value'→10步(4 respond+3 Grep+1 Read+1 Edit+1 build)。S1: Grep搜索fox-mascot render函数→S2: Grep搜索第337行附近的arithmetic操作→S3: Read fox-mascot.lua确认问题→S4: Edit修复类型错误→S5: build验证→respond输出修复说明。典型的'错误日志→Grep定位→Read确认→Edit修复→build验证'管线。 61467d20扩展了此模式的变体——资源缺失类错误：T4: 粘贴TapTap Maker错误报告，2次相同错误'Could not find resource Textures/games/p3-match-3-cover.png'→12步(4 respond+3 Glob+2 Grep+1 Read+1 Edit+1 build)。S1-S3: Glob搜索assets/Textures/games/*定位资源目录→S5-S6: Grep搜索cover/icon相关代码→S8: Read p3-match-3.lua确认cover路径配置→S9: Edit修复cover路径→S10: build验证。与374e4eb7的代码逻辑错误不同，本session是资源文件缺失/路径错误类问题，诊断方法从Grep代码行升级为Glob文件搜索+Grep配置引用。模式确认：error_log_paste不仅适用于代码运行时错误，也适用于资源缺失类构建错误，诊断工具从Grep扩展为Glob+Grep组合。 76b0acb1进一步强化此模式：T18: 粘贴TapTap Maker错误报告，69次相同错误'fox-mascot:231: attempt to perform arithmetic on a nil value (field "integer index")'→17步(8 respond+3 Read+3 Edit+2 Grep+1 build)。S1-S2: Grep搜索fox-mascot render函数和integer index变量→S3: Read fox-mascot.lua:231确认问题→S4-S6: Edit×3修复nil值算术运算→S7: build验证→respond输出修复说明。与374e4eb7的fox-mascot:337 table value错误不同，本session是fox-mascot:231 nil value错误，但诊断管线一致：Grep→Read→Edit→build。模式跨会话确认。 7a895854展示了此模式的极轻量变体——Lua语法错误直修：T2: 粘贴TapTap Maker错误报告，5个错误指向kinsoku.lua:10 'unfinished string'→5步(2 respond+1 Read+1 Edit+1 build)。S1: Read kinsoku.lua→S2: Edit修复未闭合字符串→S3: build验证→S4: respond输出修复说明。与此前会话不同——本session **零Grep**，因为错误信息极其明确（'unfinished string near'直接指出语法问题类型和行号），Agent跳过定位阶段直接Read→Edit→build。这是error_log_diagnostic的最简形式：当错误日志包含精确文件名+行号+错误类型时，Grep定位步骤可省略。模式确认：error_log_diagnostic存在'Grep重定位'(10-17步)、'Glob+Grep定位'(12步)、和'零Grep直修'(5步)三种变体，根据错误信息明确度自适应。 9bbd20cc展示了此模式的'资源缺失直修'变体：T2: 粘贴TapTap Maker错误报告，2次相同错误'Could not find resource Textures/games/p2-memory-flip-cover.png'→17步(5 respond+3 Read+3 Grep+2 Edit+2 build+2 Bash)。S1-S3: Grep搜索p2-memory-flip-cover相关代码→S4-S6: Read确认cover路径配置→S7-S8: Edit×2修复cover路径→S9-S10: build×2验证。与61467d20的资源缺失诊断管线一致——Glob/Grep搜索资源目录→Read确认配置→Edit修复路径→build验证。模式跨5个会话确认。 bdf118ee展示了此模式的"wallSet nil"变体：T03: 粘贴TapTap Maker错误报告，62次相同错误"games/p1-puzzle-land/logic/board:81: attempt to index a nil value (field 'wallSet')"→38步(12 respond+12 Grep+7 Read+4 TodoWrite+1 Edit+1 build+1 Bash)。S1-S12: Grep搜索board.lua的wallSet/wall相关代码→S13-S19: Read board.lua等文件确认问题→S20-TodoWrite创建修复清单→S21: Edit修复wallSet初始化→S22: build验证→S23: Bash验证。与374e4eb7的fox-mascot:337 table value错误和76b0acb1的fox-mascot:231 nil value错误不同，本session是board.lua:81 wallSet nil错误，但诊断管线一致：Grep→Read→Edit→build。模式跨6个会话确认。 cc1dd130展示了此模式的'board-renderer nil'变体：T2: 粘贴TapTap Maker错误报告，80次相同错误'board-renderer:996: attempt to perform arithmetic on a nil value (field integer index)'13步(5 respond+5 Grep+1 Read+1 Edit+1 build)。S0: respond确认 -> S1: Read board-renderer.lua -> S2: respond -> S3-S7: 5次Grep搜索nvgTextBounds/drawHUD相关代码 -> S8-S12: respond输出诊断结论 -> S13: Edit修复 -> S14: build验证。与76b0acb1的fox-mascot:231 nil value错误同类型(integer index nil)，但本session的Edit量更少(1 vs 3)，步骤更轻量(13 vs 17)。模式跨7个会话确认。

---

## `gene_elp_multi_error_diagnostic_cascade`

**多错误级联诊断——修复一个错误后暴露新错误** / Multi-Error Diagnostic Cascade — Second Error Exposed After First Fix

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `stacktrace_in_prompt`
- `mentions_specific_file`
- `error_after_fix_new_file`
- `multi_error_cascade`
- `different_error_after_first_fix`
- `Read_target_file`
- `single_edit_fix`
- `build_after_fix`

**Preconditions:**
- 用户粘贴第一个错误日志，Agent定位并修复。
- 修复后用户测试，粘贴了第二个不同的错误日志——错误发生在不同的文件和行号。
- 这说明第一个修复解决了原问题，但暴露了第二个潜在的bug（可能是此前被第一个错误掩盖的）。
- 第二个错误通常发生在相关联的代码路径中（如修复了adapter的渲染入口后，result-popup的渲染逻辑暴露了nil引用）。

**Evidence:** T0: 粘贴adapter:133 'draw' nil错误(68次)→33步(11 respond+8 Read+5 Glob+5 Grep+3 TodoWrite+1 build)，诊断但未修复（纯错误日志分析）。T1: 再次粘贴相同错误(67次)→70步(25 respond+24 Bash+9 Read+3 TodoWrite+3 Glob+2 Grep+2 Edit+2 build)，尝试修复→build。T3: 粘贴adapter:141 'draw' nil错误(78次)—行号从133变为141，说明T1的修复移动了问题但未根除→32步(15 Bash+9 respond+3 TodoWrite+3 Read+1 Edit+1 build)。T5: '还是报错，参考其他游戏对比'→23步(9 respond+6 Bash+3 TodoWrite+2 Read+1 Task+1 Write+1 build)，跨游戏对比诊断→Write修复→build。T6: '还是报错，检查是否覆盖key'+粘贴错误日志→41步(12 respond+12 Read+6 Edit+4 TodoWrite+3 Bash+3 Grep+1 build)，深度调查key覆盖问题→6 Edit→build。T7: '没有报错，可以正常进入游戏了，总结是什么问题'→1步respond，Agent总结根因。T8: 新错误！result-popup:150 'attempt to index a nil value (local ra)'→8步(4 respond+2 Edit+1 Read+1 build)，读取result-popup.lua→2 Edit修复→build。典型的'修复adapter draw错误→暴露result-popup nil引用'级联模式。T8的错误是独立的——发生在不同的文件(result-popup vs adapter)、不同的错误类型(index nil vs call nil)、不同的函数(drawCleared vs P4LM_HandleNanoVGRender)。

---

## `gene_elp_error_log_retry_with_diagnostic_upgrade`

**错误日志重试升级——连续粘贴错误日志的诊断升级模式** / Error Log Retry Escalation — Consecutive Error Log Pasting with Diagnostic Method Upgrade

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `stacktrace_in_prompt`
- `same_error_consecutive_turns_ge_2`
- `error_log_retry`
- `diagnostic_method_change_per_retry`
- `cross_game_comparison`
- `key_overwrite_hypothesis`
- `build_between_retries`

**Preconditions:**
- 用户连续2-3次粘贴相同的错误日志（或行号略有变化），说明Agent的前一次修复没有完全解决问题。
- 每次重试时，用户可能附加诊断性指令（如'参考其他游戏对比'、'检查是否覆盖了key'）。
- 这与bug_report的retry不同——用户不是用自然语言描述bug，而是直接粘贴原始错误日志。
- 每次重试之间通常有build操作，用户是在build后测试发现错误仍然存在。
- 错误日志的行号可能变化（如133→141→133），说明代码被修改但根因未消除。

**Evidence:** T0: 粘贴adapter:133 'draw' nil错误(68次)→33步(11 respond+8 Read+5 Glob+5 Grep+3 TodoWrite+1 build)。诊断分析但未修复。T1: 4分钟后再次粘贴相同错误(67次)→70步(25 respond+24 Bash+9 Read+3 TodoWrite+3 Glob+2 Grep+2 Edit+2 build)。诊断方法升级：使用Bash执行运行时诊断→2 Edit修复→2 build。T3: build后再次粘贴错误(78次)，行号从133变为141→32步(15 Bash+9 respond+3 TodoWrite+3 Read+1 Edit+1 build)。诊断方法再次升级：大量Bash运行时命令→1 Edit→build。T5: '还是报错，参考其他游戏对比'→23步(9 respond+6 Bash+3 TodoWrite+2 Read+1 Task+1 Write+1 build)。诊断方法第三次升级：跨游戏对比（读取其他正常游戏的adapter.lua）→Write修复→build。T6: '还是报错，检查是否覆盖key'+粘贴错误日志→41步(12 respond+12 Read+6 Edit+4 TodoWrite+3 Bash+3 Grep+1 build)。诊断方法第四次升级：检查key覆盖/命名冲突，读取12个文件理解表结构→6 Edit→build。T7: '没有报错，可以正常进入游戏了'→确认修复成功。5次错误日志提交，每次诊断方法不同：Read/Grep→Bash运行时→Bash+行号变化分析→跨游戏对比→key覆盖检查。典型的'错误日志重试→诊断方法升级'模式。

---

## `gene_br_bug_retry_with_diagnostic_upgrade`

**Bug重试与诊断升级模式** / Bug Retry with Diagnostic Upgrade — Consecutive Bug Reports with User-Provided Debug Info

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `same_bug_consecutive_turns_ge_3`
- `still_not_working_pattern`
- `diagnostic_upgrade_per_retry`
- `user_provides_debug_info`
- `target:game_logic`
- `save_persistence_bug`
- `build_between_retries`

**Preconditions:**
- 用户报告一个bug后，Agent进行了修复并build。
- 用户在接下来的3+个连续turn中报告同一个bug仍然存在。
- 与gene_br_bug_retry_escalation不同——用户不是用'还是'+自然语言描述，而是逐步提供更具体的诊断信息（如'还是显示的默认皮肤'→'还是不行，检查是保存问题还是读取问题'→'刷新页面，看到[skinId]=sport，但是游戏内还是初始皮肤'）。
- 用户主动提供调试信息（如观察到的变量值、配置状态），帮助Agent缩小排查范围。
- 每次重试之间通常有build操作，用户是在build后测试发现bug仍然存在。

**Evidence:** T28: '现在刷新网页后，没有读取上一次我设置的皮肤，检查是什么问题'→48步(18 respond+10 Read+8 Edit+7 Grep+2 TodoWrite+2 Bash+1 build)。Agent大规模调查皮肤持久化问题→Read 10文件→8 Edit修复→build。1个error。T29: '还是显示的默认皮肤'→14步(5 respond+4 Read+2 TodoWrite+1 Grep+1 Edit+1 build)。用户提供关键信息'还是默认皮肤'→Agent重新调查→4 Read+1 Edit→build。2个errors。T30: '还是不行，检查是保存问题还是读取问题'→9步(4 respond+2 Read+2 Edit+1 build)。用户明确指示'检查保存还是读取'→Agent聚焦调查→2 Edit→build。4个errors。T31: '刷新页面，看到[skinId]=sport，但是游戏内还是初始皮肤'→13步(6 respond+4 Edit+2 TodoWrite+1 build)。用户提供精确调试信息'skinId=sport但游戏内初始'→说明保存成功但应用失败→4 Edit修复应用逻辑→build。2个errors。4个连续turn报告同一bug，用户逐步提供更精确的诊断信息，从'没读取'(T28)→'还是默认'(T29)→'检查保存还是读取'(T30)→'skinId=sport但初始皮肤'(T31)。典型的'bug报告→用户提供调试信息→Agent聚焦修复'升级模式。

---

## `gene_br_white_image_cascade`

**白色图像渲染bug跨上下文扩散级联** / White Image Rendering Bug Cascade — Cross-Context Spread with Escalating Investigation

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `target:visual_style`
- `white_image_rendering`
- `cross_context_spread_ge_3`
- `escalating_investigation_depth`
- `grep_heavy_ge_10`
- `bash_heavy_ge_5`
- `read_heavy_ge_10`
- `per_turn_build_verify`

**Preconditions:**
- 用户报告游戏内图片/图像显示为白色色块的渲染bug。
- bug在连续3+个turn中报告，每次影响的范围扩大（从单一元素→所有图片→跨页面）。
- 这与gene_br_bug_retry_escalation不同——后者是同一bug反复报告（'还是不行'），本模式是bug影响范围跨上下文扩散。
- Agent的调查深度随bug范围扩大而递增（从14步轻量→108步重度→51步中量→27步修复）。
- 调查方法包括大量Grep搜索渲染相关代码、Bash运行时诊断、多文件读取。

**Evidence:** T08: '主线模式，左下角的角色图像，现在是一块白色的'→14步(6 respond+2 Grep+2 Glob+1 Task+1 Read+1 build)。轻量调查，定位角色图像渲染问题→build。T09: '主线模式，和游戏内，的图片都变为了白色'→108步(38 respond+27 Read+18 Grep+13 Bash+5 TodoWrite)。bug范围扩大到所有图片→升级为重度调查：18次Grep搜索渲染管线+27次Read渲染相关文件+13次Bash运行时诊断→修复→build。T10: '现在主线模式和游戏内显示正常了，但是自由模式选择游戏的页面左下角的角色变成白色了'→51步(18 respond+13 Read+12 Grep+2 TodoWrite+2 Glob+2 build)。修复后新页面出现相同问题→2次build验证。T11: '在主线模式，自由模式页面切换时，左下角的角色就会变成白色'→27步(12 respond+6 Read+6 Edit+1 Grep+1 build)。定位到页面切换时的渲染初始化问题→6 Edit修复→build。4个连续bug_report turn，影响范围从单一元素(角色)→所有图片→跨页面(自由模式)→页面切换，调查深度从14→108→51→27步。典型的'白色渲染bug跨上下文扩散'模式。

---

## `gene_fm_investigation_without_implementation`

**功能修改调查无实施模式** / Feature Modification Investigation Without Implementation — Heavy Read, Zero Edit, Session Terminated

Category: `diagnostic`

**Signals:**
- `intent:feature_modification`
- `zero_edits_zero_builds`
- `read_heavy_ge_5`
- `investigation_without_implementation`
- `session_terminated_before_edit`
- `task_plus_todo_without_action`
- `target:ui_layout`

**Preconditions:**
- 用户提出一个具体的feature_modification需求（如修改UI、调整游戏逻辑）。
- Agent进入调查模式：读取多个文件（5+）、分派Task、创建TodoWrite。
- 但Agent在整个turn中未执行任何Edit或Write操作，也未执行build。
- 会话在调查完成后直接终止（end_of_conversation），未进入实施阶段。
- 这可能是因为token预算耗尽、API错误、或Agent判断需要用户确认后再实施。

**Evidence:** T2: '修改4个游戏结束页面，如果没有满星，在下方显示更高星级需要的条件'→12步(6 Read+4 respond+1 Task+1 TodoWrite)。S0: respond确认方案→S1: Task探索→S2: Read result-popup.lua→S3: respond→S4: TodoWrite创建任务清单→S5-S8: Read gameplay.lua×4→S9: respond→S10: Read board.lua→S11: respond。12步调查，0 Edit 0 Write 0 build，会话直接end_of_conversation终止。典型的'feature_modification→调查(6 Read+Task+TodoWrite)→respond→会话结束(未实施)'模式。与此前所有feature_modification turn不同——其他session的feature_modification均至少包含1次Edit，本session是唯一一个纯调查无实施的feature_modification turn。

---

## `gene_aoc_multi_turn_escalation`

**AI输出纠正升级——连续误解与逐步升级的frustration** / AI Output Correction Escalation — Consecutive Misunderstanding with Frustration Signals

Category: `diagnostic`

**Signals:**
- `intent:ai_output_correction`
- `consecutive_aoc_ge_3`
- `escalating_frustration_language`
- `你搞错了吧_pattern`
- `不不不_pattern`
- `我发现你完全理解错了_pattern`
- `target:game_logic`
- `mechanic_misunderstanding`

**Preconditions:**
- 用户连续3+次使用 ai_output_correction 纠正AI对同一机制的理解。
- 用户的措辞逐步升级：从'你搞错了吧'到'不不不，你是不是还是理解错了'再到'我发现你完全理解错了'。
- 这说明AI多次误解了用户的核心意图，每次修复只解决了表面问题而非根本理解。
- 典型场景：用户描述一个多阶段机制（如蓄力然后持续发射），AI只理解了其中一部分。
- 这是高优先级问题——说明Agent需要停下来重新理解用户的完整意图，而非继续修补。

**Evidence:** T97: '你搞错了吧？我的意思是蓄力不扣能量'。T98: '不不不，你是不是还是理解错了？我的意思是，蓄力的时候不应该扣能量，不扣能量是对的，扣能量是错的'。T99: '我发现你完全理解错了，这个蓄力技能不是有2个阶段吗？蓄力，然后持续发射激光，我说的蓄力是说蓄力阶段不扣能量，持续发射的时候是要扣能量的'。典型的'纠正→还是错→完全理解错了'3-turn升级管线。Agent每次都只修复了表面问题，未理解蓄力技能的两阶段本质（蓄力阶段vs持续发射阶段）。

---

## `gene_elp_recurrent_engine_error`

**重复引擎限制错误——View超出上限的反复报告** / Recurrent Engine Limit Error — View Exceeds Maximum Limit Repeatedly Reported

Category: `diagnostic`

**Signals:**
- `intent:error_log_paste`
- `same_error_recurring_across_session`
- `view_exceeds_maximum_limit`
- `engine_limit_error`
- `error_paste_ge_5_same_type`
- `spread_across_session`
- `not_fixed_by_standard_edit`

**Preconditions:**
- 用户在同一会话中多次（5+次）粘贴相同的引擎级错误日志。
- 错误类型为引擎限制（如'View exceeds maximum limit'），而非代码逻辑错误。
- 此类错误通常由视觉元素过多、粒子过多、或渲染对象超出引擎上限引起。
- 标准的代码Edit修复往往无效——需要从设计上减少渲染对象数量或使用不同的渲染方式。
- 错误分布在会话的不同阶段，说明每次新增视觉元素时都会触发。

**Evidence:** 同一'View exceeds maximum limit'错误在会话中被粘贴9次(T58,T66,T94,T133,T164,T207,T293,T613,T619)，分布在会话全周期。这是TapTap Maker/Urho3D引擎的View数量上限错误，通常由过多UI元素、粒子、或渲染对象引起。标准的代码Edit修复无效，需要从设计上减少渲染对象。错误在每次新增视觉元素（光束、粒子、特效）时反复触发，说明Agent未从根本上解决渲染对象数量问题。

---

## `gene_br_bug_to_elp_diagnostic_upgrade`

**Bug报告到错误日志诊断升级** / Bug Report to Error Log Diagnostic Upgrade — Natural Language to Stacktrace Escalation

Category: `diagnostic`

**Signals:**
- `intent:bug_report`
- `intent:error_log_paste`
- `bug_report_then_error_log`
- `diagnostic_method_upgrade`
- `natural_language_to_stacktrace`
- `user_provides_diagnostic_hypothesis`
- `still_not_working_pattern`
- `cross_game_comparison`

**Preconditions:**
- 用户先用自然语言报告bug（如'还是报错，参考其他游戏对比'），没有粘贴错误日志。
- Agent进行诊断和修复后，用户在下一turn再次报告同一bug，但这次直接粘贴原始错误日志。
- 用户在粘贴错误日志的同时提供诊断性假设（如'检查是否覆盖了什么key'）。
- 这说明用户的工作模式是：先用自然语言描述→Agent修复→仍然失败→升级诊断方法（粘贴原始日志+提供假设）。
- 这与 gene_elp_error_log_retry_with_diagnostic_upgrade 不同——后者是连续2+次粘贴错误日志，本模式是'自然语言bug报告→错误日志粘贴'的诊断升级。

**Evidence:** 3ee927f3: T05: '还是报错，参考其他游戏，对比一下，其他游戏是正常的'→23步(9 respond+6 Bash+3 TodoWrite+2 Read+1 Task)。自然语言bug报告→Agent执行跨游戏对比诊断(6 Bash运行时命令+2 Read)→respond输出发现。T06: '还是报错，检查是否覆盖了什么key'+粘贴TapTap Maker错误报告(61次adapter:133 'draw' nil错误)→41步(12 respond+12 Read+6 Edit+4 TodoWrite+3 Bash+3 Grep+1 build)。诊断方法升级：从自然语言描述→原始错误日志+用户诊断假设('检查key覆盖')→12 Read理解表结构→6 Edit修复→build验证。典型的'自然语言bug报告(23步,跨游戏对比)→错误日志粘贴+诊断假设(41步,key覆盖调查)'升级管线。与gene_elp_error_log_retry_with_diagnostic_upgrade(连续错误日志粘贴)不同——本模式是'自然语言→错误日志'的首次诊断升级。

---
