# session_rhythm — Gene Index

**Gene count:** 13

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_meta_rapid_context_switch` | Rapid Context Switch — Multi-Intent Session with Surgical Per-Turn Focus | session_rhythm | 9x: 13683faf, 76b0acb1, 7a895854 +6 | `intent:mixed_session`, `feature_modification_plus_bug_report_plus_documentation`, `ge_4_intent_types_in_session` |
| 2 | `gene_meta_per_turn_build_verify` | Per-Turn Build Verify — Edit-Then-Build Rhythm for Lightweight Turns | session_rhythm | 3x: 13683faf, 44926b0f, ef2c887b | `intent:feature_modification`, `intent:bug_report`, `build_at_end_of_each_turn` |
| 3 | `gene_nf_edit_drift_without_verification` | Edit Drift Pattern — Consecutive Unverified Multi-File Edits | session_rhythm | 15x: 014354fc, 18479bb5, 374e4eb7 +12 | `intent:new_feature`, `intent:planning_design`, `consecutive_edits_ge_10` |
| 4 | `gene_sr_minimal_confirmation_trigger` | Minimal Confirmation Trigger — Single-Word Confirmation Cascades into Structured Implementation | session_rhythm | 3x: 11e7ed86, 5634a485, f4dd8c16 | `intent:inspection_review`, `single_word_confirmation`, `context_driven_interpretation` |
| 5 | `gene_meta_asymmetric_session_with_dominant_turn` | Asymmetric Session — One Dominant Turn with Lightweight Surroundings | session_rhythm | 1x: 212062a8 | `intent:mixed_session`, `ge_4_intent_types_in_session`, `one_dominant_turn_ge_60pct_steps` |
| 6 | `gene_sr_heavy_to_ultralight_transition` | Heavy-to-Ultralight Turn Transition — 3-Step Edit-Build-Respond Rhythm After Heavy Implementation | session_rhythm | 1x: 44926b0f | `intent:feature_modification`, `heavy_turns_ge_20_steps`, `ultralight_turns_eq_3_steps` |
| 7 | `gene_sr_respond_think_before_act` | Think-Announce-Act Cycle — respond_to_user as Thinking Buffer | session_rhythm | 15x: 056c0fdf, 11e7ed86, 125a7a4a +12 | `intent:feature_modification`, `intent:new_feature`, `intent:documentation` |
| 8 | `gene_sr_context_window_recovery` | Context Window Recovery - Mid-Turn Context Loss, Re-Read 5 Files, Continue Implementation | session_rhythm | 1x: 1cd7c1eb | `intent:feature_modification`, `target:ui_layout`, `session_continuation_message` |
| 9 | `gene_doc_ultralight_update_rhythm` | Ultra-Light Doc Update Rhythm — Consecutive Minimal Documentation Turns with Shrinking Effort | session_rhythm | 1x: a09c411b | `intent:documentation`, `consecutive_doc_turns_ge_3`, `ultralight_turns_le_6_steps` |
| 10 | `gene_sr_duplicate_inquiry_merge` | Duplicate Inquiry Merge — Near-Identical Status Questions Consolidated into Single Response | session_rhythm | 1x: d8f96672 | `intent:inquiry`, `duplicate_inquiry_consecutive_turns_ge_2`, `near_identical_inquiry_prompts` |
| 11 | `gene_sr_doc_inspection_rhythm` | Documentation Inspection Rhythm — Four Cross-Session Checks with Escalating Effort | session_rhythm | 1x: d8f96672 | `intent:inspection_review`, `target:documentation`, `doc_inspection_ge_4_per_session` |
| 12 | `gene_doc_triple_update_cascade` | Triple Documentation Cascade — Lightweight-to-Heavy Escalation Pattern | session_rhythm | 1x: f384a8d8 | `intent:documentation`, `consecutive_doc_turns_eq_3`, `escalating_effort_pattern` |
| 13 | `gene_sr_duplicate_prompt_execution_failure` | Duplicate Prompt Execution Failure — Near-Identical Requests with Second Turn Agent Run Missing | session_rhythm | 1x: a7d1b207 | `intent:feature_modification`, `target:documentation`, `duplicate_prompt_consecutive_turns` |

---

## `gene_meta_rapid_context_switch`

**多意图快速切换模式** / Rapid Context Switch — Multi-Intent Session with Surgical Per-Turn Focus

Category: `session_rhythm`

**Signals:**
- `intent:mixed_session`
- `feature_modification_plus_bug_report_plus_documentation`
- `ge_4_intent_types_in_session`
- `surgical_per_turn_focus`
- `no_cross_turn_contamination`
- `short_turns_avg_steps_le_10`
- `user_tests_while_building`

**Preconditions:**
- 同一会话中包含4种以上不同类型的意图（如feature_modification、bug_report、documentation交替出现）。
- 用户的工作模式为：提出一个小修改→验证→发现bug→报告→修复→继续下一个修改。
- 每个turn只处理一个独立问题，不跨turn混合任务。
- 平均每turn步骤数≤10，说明每个问题都是轻量级的手术式修复。
- 用户在Agent构建新功能后立即测试，并在后续turn中报告发现的问题。

**Evidence:** 13683faf: 9 prompts, 5 intent types interleaved: T0(fm,ui_layout,3steps)→T1(fm,ui_layout+progress bar,18steps,Todo×2)→T2(br,chapter title overlap,4steps)→T3(br,chapter-page mismatch,5steps)→T4(fm,7-levels-per-chapter rule,6steps)→T5(br,click penetration,13steps,Grep×3)→T6(fm,visual style swap,6steps,Task×1)→T7(doc,refine log,3steps,no build)→T8(fm,update log entry,7steps,no build). Avg 7.2 steps/turn. Each turn surgically focused on one issue. Pattern: user builds→tests→reports bugs→fixes→next feature. T1's progress bar feature directly caused T2/T3/T5 bugs (chapter display + click penetration), showing real-time testing feedback loop. 76b0acb1扩展了此模式的intent多样性上限：48 turns, 6 intent types interleaved: new_feature(8), feature_modification(25), documentation(5), bug_report(3), inquiry(4), content_creation(1), error_log_paste(1), planning_design(1)。Avg 20.2 steps/turn（因含重度turn如T1=88步,T17=99步）。典型切换序列：T1(nf,剧情对话,88步)→T2(fm,文字对齐,7步)→T3(nf,新关卡,65步)→T4(fm,按钮移动,27步)→T5(fm,时间+1,12步)→T6(nf,进度条,19步)→T13(doc,更新文档,55步)→T14(pd,设计20关,58步)→T17(nf,角色立绘,99步)→T18(elp,错误日志,17步)→T22(fm,夸奖逻辑,16步)→T23(br,立绘不显示,10步)→T30(fm,立绘左移,4步)→T31(doc,更新文档,21步)→T33(br,立绘不显示,22步)→T40(nf,清空存档,31步)→T42(doc,更新文档,18步)→T43(br,存档未清除,22步)→T44(nf,解锁所有关卡,24步)。6种intent类型刷新此前5种纪录。每个turn保持独立专注，不跨turn混合任务。 7a895854展示了此模式的'轻量混合会话'变体：9 prompts, 5 intent types interleaved: T1(approval,0steps,无agent run)→T2(fm,ui_layout,42步,3 Edit+1 build)→T3(elp,5步,1 Read+1 Edit+1 build)→T4(fm,narrative,37步,9 Edit+1 build)→T5(doc,26步,8 Edit,0 build)→T6(doc,4步,1 Edit,0 build)→T7(doc,7步,5 Edit,0 build)→T8(inquiry,1步)→T9(fm,doc,6步,3 Edit,0 build)。Avg 16 steps/turn。每个turn保持独立专注，不跨turn混合任务。与13683faf和76b0acb1不同——本session的turn步骤更少（无重度turn），且包含approval_or_feedback类型（T0无agent run），是更轻量的快速切换模式。模式确认：rapid_context_switch存在'重度混合'(76b0acb1, avg 20步)、'轻量混合'(13683faf, avg 7步)、和'极轻量混合'(7a895854, avg 16步但无重度turn)三种变体。 9bbd20cc展示了此模式的'5意图混合'变体：13 prompts, 5 intent types interleaved: T0(inspection_review,7步)→T1(new_feature,41步,12 Write)→T2(error_log_paste,17步,2 Edit+2 build)→T3(nf,翻牌动画,22步)→T4(nf,通关动画,27步)→T5(nf,配队特效,26步)→T6(fm,胜利UI,16步)→T7(inquiry,3步)→T8(inquiry,1步)→T9(fm,云存档,39步,EnterPlanMode)→T10(inspection_review,42步)→T11(fm,删除入口,28步)→T12(inspection_review,16步)。Avg 21.9 steps/turn。典型切换序列：inspection→nf实施→error_log→连续3 nf动画→fm→inquiry链→fm架构修改→inspection×2。每个turn保持独立专注。5种intent类型(inspection_review/new_feature/error_log_paste/feature_modification/inquiry)。与76b0acb1(6种,重度)和13683faf(5种,轻量)对比——本session是'中等混合'变体(avg 22步)，含EnterPlanMode架构修改turn和error_log_paste诊断turn。模式确认：rapid_context_switch存在'重度混合'(76b0acb1, avg 20步)、'轻量混合'(13683faf, avg 7步)、'极轻量混合'(7a895854, avg 16步)、和'中等混合'(9bbd20cc, avg 22步)四种变体。 9dc56f96刷新intent多样性纪录至8种：53 turns, 8 intent types interleaved: feature_modification(25), new_feature(13), documentation(4), content_creation(4), bug_report(2), meta_workflow(1), configuration(1), inquiry(1)。Avg 18 steps/turn。典型切换序列：T0(fm,UI优化,41步)→T1(fm,删除new,9步)→T2(fm,删除hot,3步)→T3(fm,关卡页UI,33步)→T5(fm,背景装饰,6步)→T6(fm,加大星星,4步)→T7(fm,装饰物移动,15步)→T8(fm,浮动效果,15步)→T9(br,移动效果未生效,17步)→T10(fm,主菜单增加效果,12步)→T13(doc,更新文档,18步)→T14(fm,消消乐胜利需求,18步)→T16(nf,连连看图形,17步)→T17(br,翻页bug,8步)→T20(fm,删除音频,17步)→T22(cc,生成音效,6步)→T23(fm,应用音效,22步)→T27(nf,关卡胜利音效,91步)→T28(cc,生成更多音效,7步)→T32(cc,生成BGM,20步)→T33(doc,更新文档,32步)→T35(nf,设置按钮,42步,EnterPlanMode)→T36(br,音量bug,30步)→T39(doc,更新文档,12步)→T40(mw,build,2步)→T41(nf,推箱子第九关,6步)→T45(fm,boom摧毁石头,32步)→T46(cfg,关闭测试开关,16步)→T47(inq,转场动画,3步)→T51(nf,飘动速度,11步)。8种intent类型刷新此前6种纪录(76b0acb1)。每个turn保持独立专注，不跨turn混合任务。模式确认：rapid_context_switch的intent多样性趋势为5→6→5→5→8，9dc56f96以8种类型刷新纪录。 9df66fd4展示了此模式的'6意图混合'变体：42 turns, 6 intent types interleaved: feature_modification(26), inquiry(4), bug_report(4), documentation(4), ai_output_correction(1), new_feature(1)。Avg 12.1 steps/turn。典型切换序列：T00(inq,3步)→T01(br,34步)→T02(fm,15步)→T03(fm,28步)→T04(fm,6步)→T05(fm,4步)→T06(fm,3步)→T07(doc,56步)→T08(fm,11步)→T09(fm,5步)→T10(fm,10步)→T11(fm,15步)→T12(fm,20步)→T13(fm,6步)→T14(fm,10步)→T15(fm,4步)→T16(fm,10步)→T17(fm,5步)→T18(fm,9步)→T19(br,6步)→T20(nf,4步)→T21(fm,23步)→T22(fm,4步)→T23(inq,11步)→T24(fm,5步)→T25(inq,2步)→T26(br,16步)→T27(aoc,9步)→T28(br,48步)→T29(br,14步)→T30(br,9步)→T31(br,13步)→T32(doc,8步)→T33(fm,36步)→T34(fm,11步)→T35(fm,8步)→T36(fm,3步)→T37(fm,3步)→T38(fm,6步)→T39(doc,4步)→T40(fm,8步)→T41(fm,4步)。6种intent类型。每个turn保持独立专注，不跨turn混合任务。T26-T31形成bug_report集群(6连续br/aoc)，展示了rapid_context_switch中的'bug集群'变体——用户集中测试并报告同一功能(云存档)的问题。 bdf118ee刷新intent多样性纪录至10种：23 turns, 10 intent types interleaved: feature_modification(9), new_feature(4), bug_report(2), documentation(2), planning_design(1), inquiry(1), error_log_paste(1), inspection_review(1), configuration(1), ai_output_correction(1)。典型切换序列：T01(pd,开发启动,170步)→T02(inq,黑屏查询,49步)→T03(elp,错误日志,38步)→T04(br,加载失败,52步)→T05(br,还是失败,20步)→T06(fm,方块颜色,20步)→T07(fm,分数需求,7步)→T08(nf,S形关卡,68步)→T09(doc,更新文档,67步)→T10(fm,精简记录,3步)→T11(fm,优化记录,3步)→T14(fm,优化UI,55步)→T15(fm,UI布局,16步)→T16(nf,自由模式关卡,20步)→T17(fm,S形布局,13步)→T18(cfg,build,0步)→T19(aoc,纠正UI,25步)→T20(nf,切换按钮,0步)→T21(nf,切换按钮细化,32步)→T22(doc,更新文档,48步)。10种intent类型刷新此前8种纪录(9dc56f96)。每个turn保持独立专注，不跨turn混合任务。模式确认：rapid_context_switch的intent多样性趋势为5→6→5→5→8→6→10，bdf118ee以10种类型刷新纪录。 24a716d1展示了此模式的"4意图极简混合"变体：6 turns, 4 intent types interleaved: T00(inquiry,10步,6 Task审计)→T01(fm,83步,24 Edit+2 Write+1 build)→T02(nf,74步,20 Edit+20 Read+1 build)→T03(nf,108步,36 Edit+EnterPlanMode+1 build)→T04(fm,39步,25 Edit+1 build)→T05(doc,33步,13 Edit+0 build)。Avg 57.8 steps/turn。4种intent类型(inquiry/feature_modification/new_feature/documentation)。每个turn保持独立专注，不跨turn混合任务。与76b0acb1(6种,重度avg 20步)和13683faf(5种,轻量avg 7步)对比——本session是"4意图中等混合"变体，turn数最少(6)但单turn步骤数最高(avg 58步)，展示了rapid_context_switch在"大规模实施+多意图"场景中的变体。模式跨8个会话确认。. c44d6be2刷新了"极轻量混合"变体的下限：7 turns, 4 intent types interleaved: T0(cc,asset_resource,1步,respond only—百度网盘下载失败)→T1(nf,asset_resource,27步,6 Edit+3 Bash+3 Grep+4 Todo+1 build—GitHub字体集成)→T2(doc,7步,2 Edit+1 Grep—更新AI规范)→T3(doc,3步,1 Edit—完成记录增加)→T4(doc,4步,1 Edit—精炼完成记录)→T5(fm,3步,1 Edit—继续精简)→T6(cc,3步,1 Edit—补充内容)。Avg 6.9 steps/turn，为所有rapid_context_switch会话中最低。4 intent types(content_creation/new_feature/documentation/feature_modification)。0 build跨5个doc turn(T2-T6)。展示了"资源获取失败→替代源成功→连续文档维护"的极轻量快速切换模式。

---

## `gene_meta_per_turn_build_verify`

**每turn构建验证节奏** / Per-Turn Build Verify — Edit-Then-Build Rhythm for Lightweight Turns

Category: `session_rhythm`

**Signals:**
- `intent:feature_modification`
- `intent:bug_report`
- `build_at_end_of_each_turn`
- `one_build_per_turn`
- `no_intermediate_build`
- `edit_then_build_sequence`
- `avg_steps_per_turn_le_10`

**Preconditions:**
- 用户提出需要修改代码或修复bug的任务（feature_modification、bug_report）。
- Agent在每个turn内完成所有编辑后，在turn末尾执行一次build验证。
- 每个turn最多1次build，不在编辑过程中插入中间build。
- 平均每turn步骤数较少（≤10），说明是轻量级的单任务turn。
- 纯文档turn（documentation）不需要build。

**Evidence:** 13683faf: 7 code-modification turns, each ending with exactly 1 build: T0(Edit→build,3steps) T1(Grep×2+Todo×2+Edit×4→build,18steps) T2(Edit→build,4steps) T3(Read→Edit→build,5steps) T4(Edit×2→build,6steps) T5(Read×2+Grep×3+Edit×2→build,13steps) T6(Task+Read→Edit→build,6steps). T7(doc,3steps) and T8(doc,7steps) correctly skipped build. Pattern: all code turns = edit(s) then build at end, never intermediate. 0 errors across all builds. 44926b0f进一步强化此模式的极轻量变体：T4: '关卡按钮加大50%'→3步(1 Edit+1 build+1 respond)。T5: 'FOX_RESERVE 80→120'→3步(1 Edit+1 build+1 respond)。T6: '设置页宽度+10%'→3步(1 Edit+1 build+1 respond)。3个turn均为恰好3步，每turn恰好1 Edit+1 build+1 respond，是gene_meta_per_turn_build_verify的最简形式。T2(39步,3 build)和T3(27步,1 build)也符合'编辑完成后build'模式，但因步骤数>10不属于轻量turn。模式确认：无论turn轻重，build始终在编辑完成后执行。 ef2c887b进一步强化此模式的'配置开关'变体：T0: '在配置中增加测试开关'→33步(2 Edit+1 build)。T1: '修改开关为，只测试非可游玩时间'→6步(2 Edit+1 build)。T2: '修改forcePlayTimeRestrict为false'→3步(1 Edit+1 build)。T3(文档,16步)和T4(文档,7步)正确跳过build。3个代码turn各1 build在末尾，2个文档turn 0 build。典型的'配置修改→每turn构建→文档跳过'模式。模式跨3个会话确认。

---

## `gene_nf_edit_drift_without_verification`

**批量编辑漂移模式（无验证连续修改）** / Edit Drift Pattern — Consecutive Unverified Multi-File Edits

Category: `session_rhythm`

**Signals:**
- `intent:new_feature`
- `intent:planning_design`
- `consecutive_edits_ge_10`
- `no_build_between_edits`
- `multi_file_scatter_edit`
- `drift_marker_present`
- `doc_edit_drift`
- `intent:feature_modification`
- `target:audio`
- `multi_file_audio_integration`

**Preconditions:**
- 用户提出一个涉及多文件修改的新功能需求，或要求大规模补充策划文档。
- Agent在没有build验证的情况下连续编辑10+次。
- 修改分散在多个文件（如gameplay.lua、board-renderer.lua、adapter.lua等），或集中在单一策划文档的多个章节。
- 会话标记中出现 drift-start 警告。
- 对于文档类edit drift：因不涉及编译，风险低于代码漂移，但仍需TodoWrite提供进度锚点。
- 用户提出跨多文件的音频集成/删除需求（如'4个游戏都要应用ui_tap音效'、'删除消消乐所有音效'），Agent沉浸于连续Edit而延迟build验证。

**Evidence:** 014354fc T0: 最大连续编辑19次无build（drift-start at step 4）。另有8次、5次、4次连续编辑漂移。整个T0共95次tool calls、37次edit、仅2次build。Phase标记显示editing占step 1-98。这是典型的代码edit drift模式——agent沉浸于批量修改而忘记验证。18479bb5 T0: 5个drift-start标记(steps 4,37,56,75,94)，94步中17次Edit集中在单一策划文档(策划案-主线系统.md)，0次build。因纯文档操作无编译风险，但TodoWrite(8项)提供进度锚点防止遗漏。展示了edit drift在文档场景中的变体——连续编辑同一文档的不同章节，无需build验证。374e4eb7强化了此模式：整个会话23个drift-start标记+4个search-loop标记。T1(开始制作):56步11 Edit+1 build，drift集中在实施阶段。T2(删除学生装+白方块修复):32步4 Edit+2 build。T3(换装页面布局):15步4 Edit+1 build。T7(更新文档):29步11 Edit+0 build，纯文档drift。T8(夸奖台词):17步4 Edit+1 build。T10(点击聊天):43步12 Edit+1 build，最大drift段。T12(服装解锁):29步5 Edit+1 build+EnterPlanMode/ExitPlanMode。T13(翻页按钮bug):45步4 Edit+6 Grep+2 build，调查型drift。整个会话96次Edit仅26次build，edit/build比=3.7:1，说明edit drift是此会话的主导模式。23个drift-start标记确认了agent在编码过程中频繁沉浸于连续编辑而延迟验证。3ee927f3进一步强化此模式：整个会话19个drift-start标记+多个search-loop标记。T1(错误修复):70步2 Edit+1 build。T2(build命令):55步9 Edit+0 build——用户仅输入'build'，但Agent执行了大规模代码修改。T3(错误修复):32步1 Edit+1 build。T6(错误重试):41步6 Edit+1 build。T9(动画特效):39步9 Edit+2 build。T10(UI布局):14步3 Edit+1 build。T11(新方块):14步2 Edit+1 build。T13(更新文档):36步11 Edit+0 build，纯文档drift。T15(更新文档):22步12 Edit+0 build，纯文档drift。T16(推箱子重设计):47步12 Edit+0 build。T17(更新文档):34步14 Edit+0 build。整个会话86次Edit仅18次build，edit/build比=4.8:1，是所有已记录会话中最高的。19个drift-start标记确认了edit drift在此会话中的主导地位，特别是在文档更新turn中（T13/T15/T17共37次Edit无build）。44926b0f进一步强化此模式：整个会话4个drift-start标记(steps 4,10,41,83)。T2(页签按钮颜色):39步8 Edit+3 build，drift-start在step 4(4连续编辑无build)和step 10(4连续编辑无build)。T3(设置页响应式):27步8 Edit+1 build，drift-start在step 41(4连续编辑无build)。T7(忠告提示下移):9步2 Edit+0 build，drift-start在step 83。整个会话21 Edit仅7 build，edit/build比=3.0:1。虽然比例低于3ee927f3(4.8:1)，但drift-start标记确认了agent在UI布局修改中同样存在edit drift模式——沉浸于连续编辑而延迟验证。TodoWrite(13次)在重度turn中提供了进度锚点。5634a485进一步强化此模式的纯文档变体：T5: 'xuyao'(仅拼音)→70步(21 respond+19 Edit+13 Read+8 TodoWrite+6 Grep+3 Bash)。19 Edit分布在5个文档文件(策划案-大厅.md×10、AI开发规范.md×4、文档维护规范.md×3、project.json×1、其他×1)，0次build。编辑模式为Read→Edit×N→Grep定位→Read→Edit×N→TodoWrite锚定→循环。整个turn无build，是典型的纯文档edit drift——Agent在收到极简输入后沉浸于大规模文档修改，依靠TodoWrite(8项)提供进度锚点防止遗漏。与18479bb5(单一文档17 Edit)不同，本session跨5个文档文件，展示了edit drift在多文档协调场景中的变体。6346da75进一步强化此模式：整个会话5个drift-start标记(steps 8,83,134,142,194)，48次Edit仅6次build，edit/build比=8.0:1，刷新所有已记录会话最高纪录。T1(UI暖色调):53步16 Edit+1 build，drift-start在step 8(4连续编辑无build)。T2(玩家动画):47步9 Edit+1 build，drift-start在step 83(4连续编辑无build)。T6(滑动操控):21步6 Edit+1 build，drift-start在step 134和142(两处连续编辑漂移)。T8(文档检查):34步9 Edit+0 build，纯文档drift，drift-start在step 194。与3ee927f3(4.8:1)和44926b0f(3.0:1)对比，本session的8.0:1比例是此前的1.7-2.7倍，说明edit drift在'视觉+动画'连续修改场景中尤为严重——Agent沉浸于逐项视觉调整而大幅延迟验证。8a77e633刷新edit/build比纪录：整个会话6个drift-start标记(steps 4,20,128,154,174,187)+2个search-loop标记(steps 15,169)。T2(加上):6步2 Edit+1 build。T4(ui_tap大厅集成):29步6 Edit+1 build，drift-start在step 4(4连续编辑无build)。T5(4游戏ui_tap批量集成):65步30 Edit+1 build，drift-start在step 20(8连续编辑无build)。T6(消消乐音效删除):71步17 Edit+1 build，drift-start在step 128/154(两处连续编辑漂移)+search-loop在step 169(Grep定位无编辑)。整个会话55次Edit仅3次build，edit/build比=18.3:1，刷新所有已记录会话最高纪录（此前6346da75为8.0:1）。6个drift-start标记确认了Agent在跨游戏音效集成和删除场景中沉浸于连续编辑而大幅延迟验证。与6346da75(视觉+动画场景)不同，本session是'音频集成+删除'场景，edit/build比是此前的2.3倍，说明在跨多文件(4游戏×多按钮)的音频批量操作中，edit drift尤为严重。9bbd20cc进一步强化此模式：整个会话53 Edit仅11 build，edit/build比=4.8:1，与3ee927f3持平。T1(开始开发):41步12 Write+1 build，Write-heavy实施阶段drift。T3(翻牌动画):22步5 Edit+2 build。T4(通关动画):27步6 Edit+1 build。T5(配队特效):26步7 Edit+1 build。T6(胜利UI):16步2 Edit+1 build。T9(云存档):39步8 Edit+1 build+EnterPlanMode。T10(检查文档):42步10 Edit+1 build。T12(删除大厅入口):28步12 Edit+0 build，纯文档drift。T12的12 Edit无build是典型纯文档edit drift。模式跨10个会话确认。bc24c5c3展示了此模式的'单文件视觉打磨漂移'变体：T0: '优化记忆翻牌的图形，现在一些图片看起来太细了'→45步(22 Edit+11 respond+4 Read+4 TodoWrite+2 Glob+2 build)。S1-S5: 轻量定位(2 Glob+2 Read)→S7-S10: TodoWrite锚定→S11-S38: 22 Edit全部针对单一文件card-renderer.lua，仅4次respond穿插→drift-start at step 8(4连续编辑无build)→S40: build验证→S42: 第二次build。22 Edit集中在单一渲染文件，是'单文件edit drift'的典型案例。与8a77e633的'跨游戏音频批量集成'(30 Edit跨4游戏)不同——本session是'单文件视觉参数批量调整'(22 Edit仅card-renderer.lua)，展示了edit drift在视觉打磨场景中的变体。 be94308f确认了此模式在'关卡编辑器开发'场景中的出现：整个会话2个drift-start标记(steps 14,34)。T1(关卡编辑器脚手架):56步13 Edit+1 build，drift-start在step 14(10连续Edit adapter.lua无build)——S23 Write创建level-editor.lua→S26-S43连续10 Edit adapter.lua(添加编辑器入口按钮×9+level-select.lua集成×3)→S53 build验证。T2(拖动放置方块):34步11 Edit+1 build，drift-start在step 34(9连续Edit level-editor.lua+adapter.lua无build)——S8-S28连续11 Edit(level-editor.lua×4+adapter.lua×7)→S31 build验证。T3(测试游玩模式):46步9 Edit+1 build，虽无drift-start标记但仍有9 Edit集中实施。整个会话35 Edit仅4 build，edit/build比=8.8:1，接近6346da75的8.0:1纪录。2个drift-start标记确认了Agent在关卡编辑器开发中沉浸于连续编辑而延迟验证。与bc24c5c3(单文件视觉打磨22 Edit)不同——本session是'多文件编辑器功能实施'(adapter.lua+level-editor.lua+level-select.lua)，展示了edit drift在工具/编辑器开发场景中的变体。 24a716d1确认了此模式的"EnterPlanMode架构扩展"变体：T03(关卡分页):108步(36 Edit+9 Read+9 Todo+3 Task+2 Write+EnterPlanMode/ExitPlanMode+1 build)。36 Edit分布在6个文件(P1/P2/P3的level-select.lua和adapter.lua)，1 build在末尾。与bc24c5c3(单文件视觉打磨22 Edit)和8a77e633(跨游戏音频30 Edit)不同——本session是"EnterPlanMode架构扩展"场景的edit drift，Agent在ExitPlanMode后沉浸于36次连续Edit而延迟验证。模式跨12个会话确认。2c4b3363强化了此模式：整个会话14个drift-start标记(steps 10,171,197,209,227,327,342,350,433,438,469,514,546)+1个search-loop标记(step 6)。T0(石头障碍):72步22 Edit+1 build，drift-start在step 10(4连续编辑无build)——S0-S9 Read+respond定位→S10-S21连续Edit board.lua(石头类型+填充+掉落+消除逻辑)→S22-S27 Edit board-renderer.lua(石头渲染)→S28-S33 Edit levels.lua(关卡配置)→S34-S35 Edit文档→S36 build。T2(冰块):92步38 Edit+1 build，drift-start在steps 171,197,209,227(4处连续编辑漂移)——大规模实现冰块系统(生命值+damage+碎裂渲染)。T5(特效增强):96步23 Edit+1 build，drift-start在steps 327,342,350(3处)——消消乐+推箱子特效批量修改。T8(连连看特效):31步7 Edit+1 build，drift-start在step 433。T9(翻牌特效):39步10 Edit+1 build，drift-start在steps 438,469。T10(冰块震动):89步13 Edit+1 build，drift-start在steps 514,546。整个会话140 Edit仅10 build，edit/build比=14.0:1，接近8a77e633的18.3:1纪录。14个drift-start标记确认了Agent在'障碍系统+视觉特效'连续修改场景中沉浸于连续编辑而大幅延迟验证。与8a77e633(音频集成+删除)不同，本session是'障碍系统+跨游戏特效'场景，edit/build比(14.0:1)是6346da75(8.0:1)的1.75倍。模式跨13个会话确认。 f4dd8c16确认了此模式在"数据文件批量参数更新"场景中的出现：T3: "基础值修改为第一关3000，之后每关增加200"→35步(25 Edit+5 respond+2 TodoWrite+1 build)。drift-start标记在step 11(4连续编辑无build)——S6-S30: 连续25次Edit修改levels.lua中9个关卡的starScore→S32: build验证。与2c4b3363(障碍系统+特效,14个drift-start)和8a77e633(音频集成,6个drift-start)不同——本session是"数据文件参数批量更新"场景的edit drift，25 Edit全部针对单一levels.lua文件，drift-start仅1个(因所有Edit连续无中断)。edit/build比=25:1，说明即使在数据文件修改中，Agent也沉浸于连续编辑而延迟验证。模式跨14个会话确认。 5dbc4646强化了此模式的'关卡设计Write-heavy'变体：T2: '设计主线关卡，到28关'→55步(10 respond+18 Read+12 Write+4 Grep+2 Edit+5 TodoWrite+2 Task+1 build)。3个drift-start标记(steps 4,35,61)：S4-S15连续12 Write创建story-17.lua到story-28.lua(0 build)→drift-start at step 4→S35-S46连续12 Write+2 Edit(0 build)→drift-start at step 35→S61-S72连续Edit+Write(0 build)→drift-start at step 61→S79: 最终build验证。55步中12 Write+2 Edit仅1 build，edit/build比=14:1。与此前会话不同——本session是'关卡叙事设计'场景的Write-heavy drift(12个新story文件)，而非代码Edit drift。但'连续编辑漂移+drift-start标记+延迟验证'模式完全一致。模式跨15个会话确认。

---

## `gene_sr_minimal_confirmation_trigger`

**最小确认词触发结构化实施** / Minimal Confirmation Trigger — Single-Word Confirmation Cascades into Structured Implementation

Category: `session_rhythm`

**Signals:**
- `intent:inspection_review`
- `single_word_confirmation`
- `context_driven_interpretation`
- `TodoWrite_cascade_after_minimal_input`
- `announce_edit_cycle_per_item`
- `version_bump_at_end`
- `summary_report_after_completion`

**Preconditions:**
- 用户在前一轮对话中收到了技术建议或方案对比（如NanoVG自绘 vs UI混用）。
- 用户仅发送一个确认词（如'要'、'好'、'行'），没有附加任何具体指令。
- 该确认词本身语义不完整，需要Agent结合前一轮对话内容推断用户的完整意图。
- Agent需要判断：用户是在确认前一轮讨论中的某个方案，要求按该方案执行。

**Evidence:** 11e7ed86 T4: '自绘重新实现，和UI混用有什么区别'→1步respond，Agent给出NanoVG自绘vsUI混用的详细对比。T5: '要'(仅1字)→25步(7 Edit+1 Read+8 respond+9 TodoWrite)。Agent正确理解'要'=采用NanoVG自绘方案，逐项修改策划案：S67-S68 TodoWrite+读取→S70-S71更新目录结构添加pause-overlay.lua→S73-S74更新渲染方案补充转场混用说明→S76-S77暂停菜单改为NanoVG自绘→S79-S80补充关卡解锁机制→S82-S83补充artPool注册伪代码→S85-S86补充事件函数命名前缀约定→S88-S89更新版本号→S91输出变更汇总。典型的'1字确认→TodoWrite驱动→逐项announce/edit→版本升级→汇总报告'模式。5634a485 T4: 'xuyao'(仅拼音，无汉字)→70步(21 respond+19 Edit+13 Read+8 TodoWrite+6 Grep+3 Bash)。T3刚完成双文档阻碍分析(AI开发规范.md+策划案-大厅.md)，输出结构化gap报告。T4用户输入'xuyao'('需要'的拼音，无附加指令)→Agent正确理解为'按你分析的gap开始修复'→TodoWrite创建8项修复清单→逐项读取→Grep定位→Edit修复(策划案-大厅.md×10、AI开发规范.md×4、文档维护规范.md×3)→0 build(纯文档任务)。与11e7ed86的'要'对比：两者都是极简确认词触发大规模实施，但5634a485的确认词更模糊(拼音vs汉字)，且触发的是文档修复而非策划案更新。模式确认：单字/拼音确认词→回顾前轮分析→TodoWrite锚定→逐项修复。 f4dd8c16强化了此模式的"bug根因确认后修复"变体：T4: "现在消消乐第十四关的分数需求仍然是9000，检查是什么问题"→3步(2 respond+1 Grep)。Agent诊断发现starScore已改但targetScore未改→respond输出根因并询问是否需要修复。T5: "需要"(仅2字)→15步(9 Edit+3 respond+2 TodoWrite+1 build)。T4的respond结尾询问"是否需要我将所有targetScore调整为starScore.two-500？"→用户回复"需要"→Agent正确理解为"按你说的修复"→TodoWrite创建2项清单→9 Edit批量修复9个关卡的targetScore→build验证→respond输出修复总结。与11e7ed86的"要"(确认设计方案)和5634a485的"xuyao"(确认gap修复)对比——本session的"需要"是确认bug修复方案，但"极简确认词→回顾前轮→TodoWrite锚定→批量Edit→build"管线完全一致。模式跨3个会话确认。

---

## `gene_meta_asymmetric_session_with_dominant_turn`

**非对称会话——单一主导turn模式** / Asymmetric Session — One Dominant Turn with Lightweight Surroundings

Category: `session_rhythm`

**Signals:**
- `intent:mixed_session`
- `ge_4_intent_types_in_session`
- `one_dominant_turn_ge_60pct_steps`
- `lightweight_surrounding_turns`
- `surgical_per_turn_focus`
- `no_cross_turn_contamination`

**Preconditions:**
- 同一会话中包含4种以上不同类型的意图。
- 其中一个turn占据总会话步骤的60%以上（如T2占79步中的57步=72%）。
- 其余turn均为轻量级（≤8步），各自处理独立问题。
- 每个turn只处理一个独立问题，不跨turn混合任务。
- 纯文档turn不需要build。

**Evidence:** 5 turns, 4 intent types: T0(inspection_review,2steps)→T1(bug_report,8steps)→T2(feature_modification,57steps,72%of total)→T3(documentation,8steps)→T4(feature_modification,4steps). T2 dominates with 18 Grep+7 Read+5 Edit+4 TodoWrite+20 respond+1 build——UI重叠问题的重度调查管线。其余turns均≤8步：T0(Read+respond)、T1(Task+Grep+Read)、T3(Read+Edit×4+respond)、T4(Read+Edit+respond)。典型的'一个复杂问题+多个轻量问题'混合模式。

---

## `gene_sr_heavy_to_ultralight_transition`

**重度到极轻量turn转换节奏** / Heavy-to-Ultralight Turn Transition — 3-Step Edit-Build-Respond Rhythm After Heavy Implementation

Category: `session_rhythm`

**Signals:**
- `intent:feature_modification`
- `heavy_turns_ge_20_steps`
- `ultralight_turns_eq_3_steps`
- `heavy_to_light_transition`
- `edit_build_respond_3step_rhythm`
- `same_target_cascade`
- `no_cross_turn_contamination`

**Preconditions:**
- 会话开始有2+个重度turn（20+步骤，多文件编辑），完成大规模UI修改。
- 随后出现3+个极轻量turn（恰好3步：Edit→build→respond），每次只调整一个布局参数。
- 极轻量turn的节奏高度一致：1 Edit + 1 build + 1 respond_to_user = 3步。
- 所有turn都指向同一目标（如UI布局），但每次修改的具体参数不同。
- 这说明用户在前序重度turn中完成了主体工作，后续turn是基于build结果的快速微调。
- 与 gene_meta_asymmetric_session_with_dominant_turn 不同——后者是1个主导turn+多个轻量turn（≤8步），本模式是2个重度turn+多个极轻量turn（恰好3步）。

**Evidence:** T2(重度): '修改页签按钮颜色区分度'→39步(8 Edit+3 build+5 Todo+3 Grep+3 Read)。大规模UI修改。T3(重度): '设置页面自适应大小'→27步(8 Edit+1 build+6 Todo+1 Read)。多文件响应式修改。T4(极轻量): '关卡按钮加大50%'→3步(1 Edit+1 build+1 respond)。T5(极轻量): 'FOX_RESERVE 80→120'→3步(1 Edit+1 build+1 respond)。T6(极轻量): '设置页宽度+10%'→3步(1 Edit+1 build+1 respond)。T7(轻量): '忠告提示下移+弹窗暖色'→9步(2 Edit+2 Todo+1 Grep+1 Read+3 respond)。模式：2个重度turn(39+27=66步)→3个极轻量turn(3×3=9步)→1个轻turn(9步)。极轻量turn的3步节奏高度一致：Edit→build→respond，无任何探索步骤。这是典型的'主体工作完成→基于预览结果快速微调'模式。

---

## `gene_sr_respond_think_before_act`

**思考-宣布-执行循环** / Think-Announce-Act Cycle — respond_to_user as Thinking Buffer

Category: `session_rhythm`

**Signals:**
- `intent:feature_modification`
- `intent:new_feature`
- `intent:documentation`
- `intent:bug_report`
- `respond_to_user_ratio_ge_0.30`
- `announce_before_edit`
- `confirm_after_edit`
- `think_act_verify_cycle`

**Preconditions:**
- 用户提出需要修改代码或文档的任务（feature_modification、new_feature、documentation、bug_report）。
- Agent 在每次编辑前，先用 respond_to_user 向用户说明即将做什么、为什么这样做。
- 编辑完成后再次用 respond_to_user 确认结果并预告下一步。

**Evidence:** 056c0fdf: Turn 1: 6/20 steps (30%) respond_to_user — 'Let me first look at existing code' → Read levels.lua/board.lua → 'Now I'll design the new level' → Edit → 'Now let me find build params' → build → done. Turn 2: 12/32 steps (38%) — each of 6 edits preceded by explain-what-I-will-do. Turn 3: 13/34 steps (38%) — '思路清晰了，改动涉及三个文件，从底向上逐层修改' then systematic per-file announce/edit. Turn 4: 17/50 steps (34%) — doc update with per-doc announce. Pattern consistent across all 4 implementation turns. 11e7ed86 T2: 36步中11步respond(31%)——'先处理配置文件重命名'→Write→'接下来检查是否有其他文件引用了旧的demo-memory-flip'→Grep+Edit→'现在集中修改策划案文档'→Edit×4→'现在新增ADR-005'→Edit×3。T5: 25步中8步respond(32%)——'开始逐项修改'→'1.更新目录结构'→Edit→'2.更新渲染方案'→Edit→'3.暂停菜单改为NanoVG自绘'→Edit→...每步Edit前都有announce。两次turn均确认announce-before-edit模式在纯文档修改场景中同样适用。125a7a4a T0: 14步中5步respond(36%)——S0 respond(announce)→S1-S2 Grep定位→S3 respond(确认找到)→S4 Read→S5 respond(确认修改方案)→S6-S7 Edit×2→S8 respond(确认修改完成)→S9 Build→S10-S11 Grep+Glob验证→S12 Build→S13 respond(最终确认)。典型的'announce→localize→edit→confirm→verify→final-confirm'循环，即使在极小会话(1 turn, 2 edits)中也保持了announce-before-edit模式。212062a8 T2: 57步中20步respond(35%)——在18次Grep搜索过程中穿插8次respond汇报阶段性发现（'找到了鼓励文字的渲染位置'、'确认fox-mascot组件在时间条之前渲染'），5次Edit前后各有announce/confirm。即使在重度Grep调查场景中也保持了announce-before-edit模式。374e4eb7进一步强化此模式：整个会话186/504步(37%)为respond_to_user，是所有已记录会话中respond比例最高的。T1(开始制作):21/56步(38%)——每批Edit前announce。T2(删除学生装):15/32步(47%)——respond+TodoWrite交替。T3(换装页面布局):7/15步(47%)。T8(夸奖台词):6/17步(35%)。T10(点击聊天):17/43步(40%)——每文件Edit前announce。T12(服装解锁):12/29步(41%)——EnterPlanMode后announce方案。T13(翻页按钮bug):17/45步(38%)——18步调查过程中穿插respond汇报发现。T15(三角形调整):9/21步(43%)——4次build各有announce/confirm。T19(聊天bug):10/24步(42%)。T25(设置按钮bug):12/34步(35%)。T26(更新文档):7/27步(26%)——纯文档turn比例较低但仍保持announce模式。37%的respond比例确认了announce-before-edit模式在此会话中的主导地位。3ee927f3进一步强化此模式：整个会话165/487步(34%)为respond_to_user。T1(错误修复):25/70步(36%)——respond+Bash交替执行诊断命令。T2(build命令):20/55步(36%)——每批Edit前announce。T3(错误修复):9/32步(28%)——respond汇报诊断进展。T6(错误重试):12/41步(29%)——respond汇报'检查key覆盖'的调查结果。T9(动画特效):18/39步(46%)——每批Edit前announce。T10(UI布局):7/14步(50%)——'参考其他游戏'→Task→Read→Edit→announce。T13(更新文档):9/36步(25%)——纯文档turn比例较低。T16(推箱子重设计):15/47步(32%)——每批Edit前announce+TodoWrite交替。T17(更新文档):9/34步(26%)。34%的respond比例确认了announce-before-edit模式在此会话中的持续主导地位，特别是在动画特效(T9,46%)和UI布局(T10,50%)turn中比例最高。4463c53b进一步强化此模式至42.4%(28/66步)，为所有已记录会话中最高：T0(inspection_review):5/16步(31%)——读取7个文件过程中穿插respond汇报审计发现。T1(bug_report):6/14步(43%)——每批Edit前announce修复方案。T2(chat UI修改):7/14步(50%)——Read fox-mascot.lua→respond确认修改方案→Edit×2→respond确认→build。T3(文档更新):6/12步(50%)——每Edit前announce更新内容。T4(chat背景):4/10步(40%)——Read→respond→Edit×3→build。5个turn中4个respond比例≥40%，即使在仅10步的极短turn(T4)中也保持了announce-before-edit模式。44926b0f进一步强化此模式至40.2%(35/87步)：T2(重度UI修改):16/39步(41%)——每批Edit前announce修改方案。T3(设置页响应式):11/27步(41%)——6项TodoWrite每项前announce。T4(关卡按钮加大):1/3步(33%)——Edit前announce。T5(FOX_RESERVE调整):1/3步(33%)。T6(设置页宽度):1/3步(33%)。T7(忠告提示下移):3/9步(33%)——2项Todo前announce。所有turn的respond比例均≥33%，确认announce-before-edit模式在此会话中的持续主导地位。4807e6ed进一步强化此模式至37.8%(14/37步)：T0(inspection_review):3/5步(60%)——读取主线关卡一致性问题报告.md后respond汇报审查结论。T1(documentation):11/32步(34%)——11次Edit各有announce，每次Edit前respond说明修改哪个问题条目（消消乐时间三连平→关卡难度跳跃→万花筒图案相似度→新手引导文案→迷雾机制→总结表格→修复状态表），Edit后respond确认完成并预告下一项。典型的'announce→Edit→confirm→announce next'循环，在纯文档修改场景中保持了announce-before-edit模式的一致性。6346da75进一步强化此模式至59.1%(75/127步)，刷新所有已记录会话最高纪录：T1(UI暖色调):22/31步(71%)——22次respond穿插16次Edit，每批Edit前announce修改方案。T2(玩家动画):15/32步(47%)——13次Read理解动画系统→每批Edit前announce。T3(眼睛表现):8/10步(80%)——4次Edit各有announce/confirm。T4(眼睛偏移加大):2/4步(50%)——3次Edit前announce。T5(手机操作查询):2/6步(33%)——Read+Grep定位后respond回答。T6(滑动操控):7/14步(50%)——每批Edit前announce。T7(文档检查):13/21步(62%)——9次Edit各有announce。T8(动画时长查询):5/5步(100%)——纯respond回答。T9(推动阻塞):1/4步(25%)——Edit前announce。9个turn中7个respond比例≥33%，T8甚至达到100%(纯信息查询turn)。59.1%的respond比例远超此前最高纪录42.4%(4463c53b)，确认announce-before-edit模式在此会话中的极致表现。 9dc56f96进一步强化此模式至33.0%(314/953步)：整个会话53 turns中，respond_to_user占比33%，超过30%阈值。重度turn如T0(41步,14 respond=34%)、T3(33步,12 respond=36%)、T24(55步,15 respond=27%)、T25(56步,16 respond=29%)、T27(91步,28 respond=31%)、T35(42步,16 respond=38%)均保持announce-before-edit模式。轻量turn如T2(3步,1 respond=33%)、T6(4步,1 respond=25%)、T11(4步,1 respond=25%)也遵循announce模式。纯文档turn如T13(18步,2 respond=11%)、T33(32步,13 respond=41%)中respond比例差异较大——T33的41%说明即使在文档更新中Agent也保持了announce习惯。33%的respond比例确认announce-before-edit模式在此53 turn长会话中的持续主导地位。 9df66fd4强化了此模式至33.6%(171/509步)：整个会话42 turns中，respond_to_user占比33.6%，超过30%阈值。重度turn如T01(34步,16 respond=47%)、T03(28步,10 respond=36%)、T07(56步,17 respond=30%)、T28(48步,18 respond=38%)、T33(36步,13 respond=36%)均保持announce-before-edit模式。轻量turn如T04(6步,2 respond=33%)、T05(4步,1 respond=25%)、T06(3步,1 respond=33%)也遵循announce模式。纯文档turn如T32(8步,1 respond=13%)比例较低。33.6%的respond比例确认announce-before-edit模式在此42 turn长会话中的持续主导地位。 24a716d1强化了此模式至34.3%(119/347步)：T00(审计):4/10步(40%)——6 Task审计过程中穿插respond汇报。T01(消消乐暂停):28/83步(34%)——每批Edit前announce修改方案。T02(关卡生成):21/74步(28%)——TodoWrite每项前announce。T03(关卡分页):45/108步(42%)——EnterPlanMode后announce方案，每批Edit前announce。T04(三星需求):9/39步(23%)——25 Edit前announce调整方向。T05(文档):12/33步(36%)——每Edit前announce更新内容。6个turn中5个respond比例≥23%，确认announce-before-edit模式在此会话中的持续主导地位。模式跨13个会话确认。 d8f96672强化了此模式至37.4%(229/612步)：整个会话19 turns中，respond_to_user占比37.4%，超过30%阈值。重度turn如T0(40步,16 respond=40%)、T1(36步,13 respond=36%)、T3(58步,21 respond=36%)、T9(54步,20 respond=37%)、T11(40步,16 respond=40%)、T14(48步,16 respond=33%)、T18(55步,19 respond=35%)均保持announce-before-edit模式。轻量turn如T5(11步,4 respond=36%)、T7(14步,5 respond=36%)也遵循announce模式。37.4%的respond比例确认announce-before-edit模式在此19 turn长会话中的持续主导地位。模式跨14个会话确认。 f4dd8c16确认了此模式在"数据文件修改"场景中的出现：整个会话17/76步(22.4%)为respond_to_user。T0: 5/16步(31%)——Task探索后announce方案，Grep定位后respond确认，Edit后respond汇报。T1: 1/5步(20%)——Edit后respond确认。T2: 1/2步(50%)——Task搜索后respond回答查询。T3: 5/35步(14%)——批量Edit前announce修改方案，Edit后respond确认，build后respond总结。T4: 2/3步(67%)——Grep定位后respond汇报根因("starScore已改但targetScore未改")。T5: 3/15步(20%)——respond确认修复方案("将所有targetScore调整为starScore.two-500")，Edit后respond确认，build后respond总结。22.4%的respond比例确认announce-before-edit模式在此会话中的持续主导地位。模式跨15个会话确认。

---

## `gene_sr_context_window_recovery`

**上下文窗口溢出恢复模式** / Context Window Recovery - Mid-Turn Context Loss, Re-Read 5 Files, Continue Implementation

Category: `session_rhythm`

**Signals:**
- `intent:feature_modification`
- `target:ui_layout`
- `session_continuation_message`
- `context_window_overflow`
- `mid_turn_context_loss`
- `re_read_ge_5_after_continuation`
- `edit_after_context_restore`
- `double_build_after_recovery`

**Preconditions:**
- 用户在turn中间提出修改需求（如'删除emoji，使用nanovg绘制'）。
- Agent开始实施（Write新文件），但conversation达到context window上限。
- 系统自动插入'This session is being continued from a previous conversation that ran out of context'消息。
- Agent在恢复后丢失了此前的工作上下文——不知道已经做了什么、改了哪些文件。
- Agent需要重新读取5+个关键文件恢复上下文，然后继续完成未竟的修改。

**Evidence:** T05: '删除这些emoji，使用nanovg绘制' -> 39步。前半段: Write 2新文件(nanovg相关)+Edit 4处(game-card.lua x2+home/init.lua x2) -> context window溢出 -> 系统插入continuation消息 -> 后半段: 重新Read 5文件(game-card.lua, home/init.lua, main.lua, colors.lua, layout.lua)恢复上下文 -> Grep搜索NanoVGRender确认渲染管线 -> Read game-registry+game/init.lua确认注册 -> Write补充遗漏文件 -> Edit main.lua x3添加NanoVG初始化+cleanup -> Read lua_errors.log诊断build错误 -> Grep搜索nvgDestroy -> Edit修复home/init.lua -> build x2验证。典型的'实施 -> context溢出 -> re-read 5 files -> 继续 -> build失败 -> 读错误日志 -> 修复 -> build成功'恢复管线。这是首个记录的context window recovery模式。

---

## `gene_doc_ultralight_update_rhythm`

**极轻量文档更新节奏** / Ultra-Light Doc Update Rhythm — Consecutive Minimal Documentation Turns with Shrinking Effort

Category: `session_rhythm`

**Signals:**
- `intent:documentation`
- `consecutive_doc_turns_ge_3`
- `ultralight_turns_le_6_steps`
- `shrinking_step_count`
- `read_edit_respond_only`
- `no_build_no_grep_no_todo`
- `same_doc_or_related_docs`

**Preconditions:**
- 用户连续3+次提出文档更新请求（如'更新文档'、'更新完成记录.md'）。
- 每次turn极度轻量（≤6步），仅包含Read+Edit+respond操作。
- 步骤数呈递减趋势（如4→6→3步），说明文档更新量逐渐减少。
- 不涉及任何Grep、TodoWrite、Bash、build操作——纯文档编辑。
- 这与gene_doc_post_implementation_sync不同——后者是代码变更后的大规模文档同步（20-66步，7-21 Edit），本模式是极轻量文档维护。
- 这也与gene_fm_doc_refinement_duplicate_prompts不同——后者是几乎相同的重复请求，本模式是不同的文档更新内容。

**Evidence:** T12: '更新文档'→4步(2 Edit+1 Read+1 respond)。轻量文档更新→2 Edit→respond确认。0 build。T13: '更新完成记录.md'→6步(3 respond+2 Read+1 Edit)。打开完成记录.md→2 Read确认上下文→1 Edit→respond确认。0 build。T14: '更新完成记录.md'→3步(2 respond+1 Read)。极简文档更新→1 Read→respond确认。0 build 0 Edit。3个连续documentation turn(4+6+3=13步)，步骤数递减(4→6→3)，每次仅1-2 Edit或纯Read+respond。0 build、0 Grep、0 TodoWrite。典型的'极轻量文档维护'节奏。与gene_doc_post_implementation_sync(20-66步,7-21 Edit)和gene_fm_doc_refinement_duplicate_prompts(3步×4,重复请求)不同——本模式是不同的文档更新内容，步骤数递减，更新量逐渐减少。

---

## `gene_sr_duplicate_inquiry_merge`

**重复信息查询合并模式** / Duplicate Inquiry Merge — Near-Identical Status Questions Consolidated into Single Response

Category: `session_rhythm`

**Signals:**
- `intent:inquiry`
- `duplicate_inquiry_consecutive_turns_ge_2`
- `near_identical_inquiry_prompts`
- `merged_into_single_agent_run`
- `ultralight_response_le_2_steps`
- `target:ui_layout`
- `status_question_pattern`

**Preconditions:**
- 用户连续2次提出几乎相同的信息查询请求（如'是否有做分辨率适配'→'是否有做分辨率自适应'）。
- 两次请求的核心意图完全一致，仅措辞略有不同（如'适配'→'自适应'）。
- 这在trajectory中表现为：两个连续user turn之间没有agent run（merged into a single agent run）。
- Agent的响应极度轻量（1步respond_to_user），直接基于已有上下文回答，无需Read/Grep探索。
- 这与gene_fm_doc_refinement_duplicate_prompts不同——后者是文档修改的重复请求（导致重复Edit），本模式是信息查询的重复请求（合并为1次回答）。

**Evidence:** T16: '现在的游戏，是否有做分辨率适配'→T17: '现在的游戏，是否有做分辨率自适应'。两个连续user turn之间无agent run（merged），最终1步respond_to_user回答。与gene_fm_doc_refinement_duplicate_prompts不同——后者导致重复Edit(3步×4)，本模式是纯信息查询重复，合并为1步respond。典型的'用户重复发送同一问题→Agent合并为一次回答'模式。

---

## `gene_sr_doc_inspection_rhythm`

**文档检查跨会话节奏——四次检查逐步升级** / Documentation Inspection Rhythm — Four Cross-Session Checks with Escalating Effort

Category: `session_rhythm`

**Signals:**
- `intent:inspection_review`
- `target:documentation`
- `doc_inspection_ge_4_per_session`
- `spread_across_session`
- `escalating_effort_pattern`
- `final_inspection_triggers_heavy_doc_update`
- `no_code_edit_in_inspection_turns`
- `check_doc_update_phrase`

**Preconditions:**
- 用户在同一会话中4+次提出'检查文档是否有需要更新的地方'类请求。
- 检查请求分布在会话的不同阶段（开头、中间、末尾），而非集中在一起。
- 每次检查的工作量差异巨大——从极简（5步，纯Read）到重度（55步，20 Edit）。
- 最后一次检查通常触发大规模文档更新——因为此前所有代码修改累积的文档gap在此时集中暴露。
- 这与gene_doc_dual_inspection_rhythm不同——后者是2次检查（中途+末尾），本模式是4+次跨会话分布。
- 这也与gene_doc_post_implementation_sync不同——后者由'更新文档'触发（代码变更后的同步），本模式由'检查文档'触发（主动审查gap）。

**Evidence:** T2: '检查文档是否有需要更新的地方'→28步(11 Edit+3 Read+2 Todo+2 Bash)。动画功能实现后文档更新→11 Edit。T4: '检查文档，是否有需要更新的内容'→5步(4 Read+1 respond)。极简检查，纯Read无Edit。T6: '检查文档有什么需要更新的内容'→12步(5 Edit+2 Read+1 Grep+1 Bash)。UI删除后文档更新→5 Edit。T18: '检查文档，是否有需要更新的地方'→55步(20 Edit+6 Read+5 Bash+4 Todo)。会话末尾最终检查，覆盖所有累积gap→20 Edit刷新单turn文档编辑量。4次文档检查分布在会话全周期(28→5→12→55步)，工作量呈'中→极轻→轻→极重'模式，最后一次检查覆盖此前所有代码变更的文档gap。与gene_doc_dual_inspection_rhythm(2次检查)不同——本模式是4次跨会话分布，且最后一次检查极度重(55步,20 Edit)。

---

## `gene_doc_triple_update_cascade`

**三连续文档更新级联——轻量到重度的escalation模式** / Triple Documentation Cascade — Lightweight-to-Heavy Escalation Pattern

Category: `session_rhythm`

**Signals:**
- `intent:documentation`
- `consecutive_doc_turns_eq_3`
- `escalating_effort_pattern`
- `third_turn_heavy_ge_40_steps`
- `single_document_focus_in_heavy_turn`
- `edit_ge_10_in_heavy_doc_turn`
- `todo_ge_10_in_heavy_doc_turn`
- `no_build_in_doc_turns`

**Preconditions:**
- 用户连续3次提出文档更新请求，每次针对不同的文档文件。
- 前两次turn极度轻量（≤7步，≤3 Edit），是常规的文档更新。
- 第三次turn突然变重（40+步骤，10+ Edit，10+ Todo），全部针对单一文档文件。
- 这说明第三份文档需要大幅更新——可能是因为前序代码修改影响了大量内容，或该文档本身结构复杂需要逐项更新。
- 这与gene_doc_ultralight_update_rhythm不同——后者是连续3+次极轻量文档更新（≤6步，递减），本模式是'轻量→轻量→重度'的 escalation。
- 这也与gene_doc_post_implementation_sync不同——后者是单turn的多文档同步（20-66步，7-21 Edit跨多个文档），本模式是3个独立turn，第三个turn聚焦单一文档的重度更新。

**Evidence:** T2: '更新文档'→7步(3 Edit+2 Read+2 respond)。轻量通用文档更新→3 Edit→0 build。T3: '更新完成记录.md'→4步(1 Edit+1 Read+1 Todo+1 respond)。指定文件轻量更新→1 Edit→0 build。T4: '更新主线关卡总览.md'→49步(19 respond+13 Edit+12 Todo+3 Grep+2 Read)。重度单文档更新→TodoWrite 12项→13 Edit全部针对主线关卡总览.md→0 build。3个连续documentation turn(7+4+49=60步)， effort呈'轻→极轻→重'escalation(7→4→49步)。T4的49步是此模式的核心特征——单一文档的重度更新需要12项TodoWrite跟踪和13次Edit。与gene_doc_ultralight_update_rhythm(递减:4→6→3步)和gene_doc_post_implementation_sync(单turn多文档:20-66步跨多个文档)均不同。

---

## `gene_sr_duplicate_prompt_execution_failure`

**重复请求执行失败模式** / Duplicate Prompt Execution Failure — Near-Identical Requests with Second Turn Agent Run Missing

Category: `session_rhythm`

**Signals:**
- `intent:feature_modification`
- `target:documentation`
- `duplicate_prompt_consecutive_turns`
- `near_identical_prompts_eq_2`
- `second_turn_no_agent_run`
- `api_error_or_session_termination`
- `has_attached_doc`
- `mentions_specific_file`

**Preconditions:**
- 用户连续2次发送几乎相同的文档修改请求（如'修改具体的游戏名字，而不是P1P2P3'→'修改文档中显示具体的游戏名字，而不是P1P2P3'）。
- 第一次请求有正常的agent run（Read+Edit+respond）。
- 第二次请求没有agent run（0 steps）——可能是API错误、会话终止、或网络问题。
- 这与gene_fm_doc_refinement_duplicate_prompts不同——后者的重复请求都有成功的Edit执行，本模式的第二次请求执行失败。
- 用户的意图是确认或修正前次修改，但由于执行失败，修改可能未生效。

**Evidence:** T11: '修改具体的游戏名字，而不是P1P2P3'→0步（no agent run）。T12: '修改文档中显示具体的游戏名字，而不是P1P2P3'→no agent run。两个turn几乎相同的请求（均要求将完成记录.md中的P1P2P3替换为具体游戏名），但都没有agent run执行。这可能是API错误、会话终止、或网络问题导致请求未被处理。与gene_fm_doc_refinement_duplicate_prompts不同——后者的重复请求都有成功的Edit执行（3步Read+Edit+respond），本模式的两次请求均为0步，完全未执行。这是重复请求的'执行失败'变体。

---
