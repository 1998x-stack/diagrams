# operational — Gene Index

**Gene count:** 15

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_mw_todo_driven_workflow` | TODO-Driven Task Management — Progress Tracking for Multi-Step Work | operational | 6x: 014354fc, 0ea2a577, 4d80bab3 +3 | `intent:new_feature`, `intent:documentation`, `TodoWrite_frequent` |
| 2 | `gene_op_batch_build_verify` | Batch-Build-Verify — Single Build After All Edits Per Turn | operational | 7x: 056c0fdf, 44926b0f, 9bbd20cc +4 | `intent:feature_modification`, `intent:new_feature`, `build_once_per_turn` |
| 3 | `gene_doc_post_implementation_sync` | Post-Implementation Documentation Sync — Multi-Document Update After Code Changes | operational | 14x: 08e306a0, 374e4eb7, 3ee927f3 +11 | `intent:documentation`, `post_code_change_doc_update`, `multi_doc_sync` |
| 4 | `gene_doc_post_audit_report_sync` | Post-Audit Documentation Report Sync — Multi-Document Update After Self-Check Audit and Bug Fixes | operational | 1x: 0ea2a577 | `intent:documentation`, `post_audit_doc_update`, `audit_report_doc_creation` |
| 5 | `gene_op_subagent_warmup_waste` | Subagent Warmup Waste — Parallel Dispatch with Majority Idle Returns | operational | 14x: 36749904, 4a183ae9, 4d80bab3 +11 | `intent:new_feature`, `intent:feature_modification`, `intent:content_creation` |
| 6 | `gene_mw_build_command_triggers_code_fix` | Build Command Triggers Code Fix — Bare Build Preceded by Diagnostic Read-Edit-Build Cycle | operational | 1x: 3ee927f3 | `intent:meta_workflow`, `bare_build_command`, `build_triggers_code_fix` |
| 7 | `gene_mw_git_upload_workflow` | Git Repository Upload Pipeline — Todo-Anchored Bash-Heavy Code Hosting Workflow | operational | 1x: 4c171670 | `intent:meta_workflow`, `target:tooling`, `github_repository_upload` |
| 8 | `gene_doc_maintenance_rhythm` | Documentation Maintenance Rhythm — Proactive Dev Log and Doc Updates During Development | operational | 2x: 5c2aeaee, 6b8bf0cd | `intent:documentation`, `intent:inspection_review`, `target:documentation` |
| 9 | `gene_doc_single_doc_refinement_cascade` | Single-Document Refinement Cascade — Generate-Then-Iteratively-Condense on One File | operational | 2x: 870a5123, c44d6be2 | `intent:content_creation`, `intent:feature_modification`, `intent:planning_design` |
| 10 | `gene_fm_doc_refinement_duplicate_prompts` | Doc Refinement Duplicate Prompts — Near-Identical Documentation Edit Requests Across Consecutive Turns | operational | 4x: bdf118ee, be94308f, ef2c887b +1 | `intent:feature_modification`, `intent:documentation`, `target:documentation` |
| 11 | `gene_doc_dual_inspection_rhythm` | Dual Documentation Inspection Rhythm — Mid-Session and End-Session Documentation Gap Checks | operational | 1x: 61467d20 | `intent:inspection_review`, `target:documentation`, `dual_inspection_in_session` |
| 12 | `gene_doc_cross_project_generalization` | Cross-Project Document Generalization — Abstract Project-Specific Docs into Reusable Templates | operational | 1x: 7a895854 | `intent:feature_modification`, `target:documentation`, `cross_project_reusability` |
| 13 | `gene_doc_heavy_to_light_refinement_cascade` | Doc Heavy-to-Light Refinement Cascade — Multi-Document Sync to Targeted Edit to Terminology Query | operational | 1x: a7d1b207 | `intent:documentation`, `intent:feature_modification`, `target:documentation` |
| 14 | `gene_ir_doc_inspection_heavy` | Heavy Documentation Inspection - Multi-Document Audit Pipeline Triggered by Minimal Request | operational | 1x: cc1dd130 | `intent:inspection_review`, `target:documentation`, `heavy_doc_inspection_ge_80_steps` |
| 15 | `gene_doc_progress_doc_lifecycle` | Documentation Lifecycle Cascade - Create, Refine, Supplement, Extract Complete Pipeline | operational | 1x: cc1dd130 | `intent:documentation`, `intent:content_creation`, `intent:inspection_review` |

---

## `gene_mw_todo_driven_workflow`

**Todo驱动的任务管理工作流** / TODO-Driven Task Management — Progress Tracking for Multi-Step Work

Category: `operational`

**Signals:**
- `intent:new_feature`
- `intent:documentation`
- `TodoWrite_frequent`
- `task_decomposition`
- `progress_tracking`

**Preconditions:**
- 用户提出一个需要多步骤完成的任务（新功能、文档更新等）。
- 任务涉及多个文件或模块的修改。
- 需要跟踪进度，避免遗漏步骤。

**Evidence:** 整个会话共13次TodoWrite调用：T0(音效系统)使用13次，T1(测试UI)使用6次，T2(文档)使用4次，T3(debug按钮)使用1次。Agent在每个复杂任务开始前都用TodoWrite分解步骤，是典型的todo驱动工作模式。0ea2a577也强化了此模式：T0(自查审计)使用4次TodoWrite创建8项检查清单，T1(P1/P2修复)使用9次TodoWrite管理14项带优先级标签的问题清单，T2(文档更新)使用6次TodoWrite跟踪5项文档更新。整个会话共19次TodoWrite，覆盖审计→修复→文档全链路。4d80bab3进一步强化此模式：T2(开始开发连连看)使用11次TodoWrite管理14项实施清单(阅读参考文档→创建基础结构→pathfinder→board→state→save→tile-renderer→board-renderer→hud+result+pause→gameplay→level-select→adapter→构建测试)。每次完成一个子系统就标记completed并标记下一项in_progress。14项清单全部completed后执行build验证。模式确认：TodoWrite在'从零创建完整模块'场景中同样发挥进度锚定作用，防止在大规模Write过程中遗漏子系统。 9bbd20cc进一步强化此模式：整个会话43次TodoWrite调用。T1(开始开发):7次TodoWrite管理7项实施清单(创建目录→config→logic→view→screens→adapter→build)。T3(翻牌动画):4次TodoWrite管理4项动画实施。T4(通关动画):4次TodoWrite。T5(配队特效):4次TodoWrite。T6(胜利UI):4次TodoWrite。T9(云存档):5次TodoWrite管理EnterPlanMode方案实施。T10(检查文档):7次TodoWrite跟踪文档检查。T11(进度查询修复):4次TodoWrite。T12(删除入口):4次TodoWrite。整个会话43次TodoWrite覆盖实施→动画→UI→架构修改→文档检查全链路。模式确认：TodoWrite在'连续多功能开发'场景中同样发挥进度锚定作用，防止在跨turn开发中遗漏子系统。 24a716d1强化了此模式：整个会话29次TodoWrite调用。T01(消消乐暂停+庆祝特效):4次TodoWrite管理4项实施清单(暂停功能+共享特效+status修复+build)。T02(三游戏关卡生成):7次TodoWrite管理6项清单(了解结构+P1/P2/P3关卡生成+文档+build)。T03(关卡分页):9次TodoWrite管理7项清单(P1/P2/P3 level-select+adapter修改+build)。T04(消消乐三星需求降低):3次TodoWrite管理2项清单(调整starScore+build)。T05(文档更新):4次TodoWrite管理3项清单(P3-消消乐.md+完成记录.md+总体进度.md)。整个会话29次TodoWrite覆盖实施→内容生成→架构修改→参数调整→文档全链路。模式跨5个会话确认。2c4b3363进一步强化此模式：整个会话62次TodoWrite调用，为所有已记录会话最高。T0(石头障碍):8次TodoWrite管理石头系统设计(类型定义+填充逻辑+掉落+消除+渲染+关卡配置+文档)。T1(石头出现):4次TodoWrite管理L6-L15关卡配置。T2(冰块):7次TodoWrite管理冰块系统(类型+damage+碎裂状态+渲染+关卡配置)。T3(视觉区分):3次TodoWrite管理冰块/石头形状修改。T5(特效增强):10次TodoWrite管理消消乐+推箱子特效(消除特效+combo+胜利+推动+到位)。T7(combo修改):4次TodoWrite管理combo位置+文本修改。T8(连连看特效):6次TodoWrite管理消除+连线+胜利特效。T9(翻牌特效):7次TodoWrite管理翻牌动画+配对特效。T10(冰块震动):6次TodoWrite管理震动+冰屑粒子效果。T11(文档):4次TodoWrite管理多文档更新。T12(音效文档):3次TodoWrite管理音效设计文档保存。62次TodoWrite覆盖障碍系统→视觉打磨→特效增强→UI调整→文档全链路，刷新此前最高纪录43次(9bbd20cc)。模式跨6个会话确认。

---

## `gene_op_batch_build_verify`

**批量编辑后统一构建** / Batch-Build-Verify — Single Build After All Edits Per Turn

Category: `operational`

**Signals:**
- `intent:feature_modification`
- `intent:new_feature`
- `build_once_per_turn`
- `build_after_all_edits`
- `no_intermediate_build`
- `edit_then_build_sequence`

**Preconditions:**
- 用户提出需要修改代码的功能需求（非纯文档任务）。
- Agent 在一个 turn 内需要多次编辑多个文件。
- Agent 选择在所有编辑完成后统一 build 一次，而非每次编辑后都 build。

**Evidence:** 056c0fdf: Turn 1: 1 edit + 1 build (build at step 18/20, after all edits). Turn 2: 6 edits across 2 files (board-renderer.lua + gameplay.lua) + 1 build at step 50/32 (last but one step). Turn 3: 7 edits across 3 files (board-renderer.lua + gameplay.lua + adapter.lua) + 1 build at step 84/34. Pattern: all edits batched, single build at end. Turn 4 (documentation): 0 builds — correct, doc-only turn. 44926b0f强化了此模式：T2: 8 Edit(页签按钮颜色)+3 build(39步)。T3: 8 Edit(设置页响应式)+1 build(27步)。两个turn均为'批量编辑→统一构建'模式，其中T2的3 build说明修改量大时分多次build验证。模式确认：多编辑turn中build集中在编辑完成后，而非编辑过程中间插入。 9bbd20cc强化了此模式：T1(开始开发):41步12 Write+1 build(末尾)。T3(翻牌动画):22步5 Edit+2 build。T4(通关动画):27步6 Edit+1 build。T5(配队特效):26步7 Edit+1 build。T6(胜利UI):16步2 Edit+1 build。T9(云存档):39步8 Edit+1 build。T10(检查文档):42步10 Edit+1 build。T11(进度查询修复):16步1 Edit+1 build。8个代码turn中6个恰好1 build在末尾，T3有2 build(动画调试需要额外验证)。模式确认：无论turn轻重，build始终在编辑完成后执行。 9df66fd4强化了此模式：38个代码turn中，绝大多数遵循'编辑完成后build'模式。T01(34步,10 Edit+1 build)、T02(15步,2 Edit+1 build)、T03(28步,9 Edit+3 build)、T07(56步,13 Edit+2 build)、T28(48步,8 Edit+1 build)、T33(36步,8 Edit+1 build)均为'批量编辑→统一构建'模式。极轻量turn如T04(6步,3 Edit+1 build)、T05(4步,2 Edit+1 build)、T06(3步,1 Edit+1 build)也遵循'Edit→build'节奏。纯文档turn如T32(8步,5 Edit+0 build)、T40(4步,1 Edit+0 build)正确跳过build。模式确认：无论turn轻重，build始终在编辑完成后执行。 24a716d1强化了此模式：T01(消消乐暂停):83步(24 Edit+2 Write+21 Read+6 Todo+1 build末尾)。T02(三游戏关卡):74步(20 Edit+20 Read+7 Todo+2 Task+3 Bash+1 build末尾)。T03(关卡分页):108步(36 Edit+9 Read+9 Todo+3 Task+2 Write+1 build末尾)。T04(三星需求降低):39步(25 Edit+1 Read+3 Todo+1 build末尾)。T05(文档):33步(13 Edit+3 Read+4 Todo+0 build，纯文档正确跳过)。4个代码turn全部遵循"批量编辑→统一构建"模式，T05纯文档正确跳过build。模式跨5个会话确认。 d8f96672强化了此模式：14个代码turn中11个遵循'编辑完成后build'模式(79%)。T0(18 Edit+1 build末尾)、T1(14 Edit+1 build)、T3(16 Edit+1 build)、T9(16 Edit+1 build)、T11(14 Edit+2 build)、T14(20 Edit+1 build)、T15(1 Edit+1 build)均为'批量编辑→统一构建'模式。纯文档turn如T2(11 Edit+0 build)、T6(5 Edit+0 build)、T18(24 Edit+0 build)正确跳过build。模式跨6个会话确认。 f4dd8c16强化了此模式的"数据文件修改"变体：T0(推箱子步数修改):3 Edit+1 build(末尾)。T1(第十一/十二关步数):2 Edit+1 build(末尾)。T3(消消乐分数公式):25 Edit+1 build(末尾)。T5(targetScore修复):9 Edit+1 build(末尾)。4个代码turn全部遵循"批量编辑→统一构建"模式，其中T3的25 Edit是此模式中最重的单turn编辑量。纯inquiry turn(T2:2步,0 build)和纯诊断turn(T4:3步,0 build)正确跳过build。模式跨7个会话确认。

---

## `gene_doc_post_implementation_sync`

**代码变更后文档同步更新** / Post-Implementation Documentation Sync — Multi-Document Update After Code Changes

Category: `operational`

**Signals:**
- `intent:documentation`
- `post_code_change_doc_update`
- `multi_doc_sync`
- `grep_for_context_before_doc_edit`
- `architecture_doc_update`
- `progress_doc_update`

**Preconditions:**
- 用户在完成代码修改后，要求'更新文档'。
- 项目存在多个文档文件（架构决策记录、完成记录、总体进度、AI开发规范等）。
- Agent需要识别哪些文档受到了代码修改的影响，并同步更新。
- 文档更新不涉及代码文件，仅修改docs/下的.md文件。

**Evidence:** 08e306a0: T5: '更新文档'→16步(7 Edit+4 Read+2 Grep+1 respond)。S0-S1: Grep搜索density/PHONE_REF/缩放因子确认相关文档→S2: Glob列出所有.md→S3-S6: 读取4个文档(架构决策记录.md、AI开发规范.md、完成记录.md、总体进度.md)→S8-S14: 编辑3个文档(架构决策记录.md×3处、完成记录.md×1处、总体进度.md×3处)→S15: respond确认。整个turn纯文档更新，无build，涉及4个文档文件中的3个。374e4eb7强化了此模式——整个会话3次'更新文档'请求：T7: '更新文档'→29步(8 respond+11 Edit+4 TodoWrite+3 Read+3 Glob)，更新换装系统相关文档。T11: '更新文档'→27步(9 respond+7 Edit+6 Read+5 TodoWrite)，更新夸奖台词和点击聊天功能相关文档。T26: '更新文档'→27步(7 respond+10 Edit+3 TodoWrite+3 Glob+2 Read)，更新服装解锁条件和bug修复相关文档。三次文档更新均无build，使用TodoWrite跟踪更新进度，每次涉及5-11个文档编辑。模式确认：'更新文档'=纯文档任务，识别后跳过build，用TodoWrite跟踪多文档更新。3ee927f3进一步强化此模式——整个会话3次'更新文档'请求：T13: '更新文档'→36步(11 Edit+9 respond+6 Read+4 Glob+4 TodoWrite+2 Bash)，更新连连看动画特效和UI布局相关文档。T15: '更新文档'→22步(12 Edit+4 TodoWrite+3 Read+3 respond)，更新连连看关卡布局调整相关文档。T17: '更新文档'→34步(14 Edit+9 respond+4 Read+4 TodoWrite+2 Bash+1 Glob)，更新推箱子高难度关卡重设计相关文档。三次文档更新均无build，使用TodoWrite(各4项)跟踪更新进度，每次涉及11-14个文档编辑。模式确认：'更新文档'=纯文档任务，识别后跳过build，用TodoWrite跟踪多文档更新，edit量随本轮代码修改复杂度递增(11→12→14)。4807e6ed扩展了此模式的触发场景——T0: '检查主线关卡一致性问题报告.md，这些修复方案是否有问题'(inspection_review,5步,0 edit)→T1: '修改文档'(documentation,32步,11 Edit+9 TodoWrite+11 respond)。与'更新文档'触发不同，本session由'审查报告→确认修复方案→修改同一报告文档'驱动，11次Edit全部针对单一文件(主线关卡一致性问题报告.md)，用TodoWrite跟踪7项修复条目(消消乐时间三连平、关卡难度跳跃、万花筒图案相似度等)，无build。模式确认：文档更新不仅由'更新文档'触发，也可由inspection_review→doc-edit管线触发。 76b0acb1进一步强化此模式——整个会话3次'更新文档'请求：T13: '更新文档'→55步(21 respond+18 Edit+8 Read+5 TodoWrite+3 Glob)，更新剧情对话系统和UI布局相关文档。T31: '更新文档'→21步(4 respond+8 Edit+3 Read+3 Glob+3 TodoWrite)，更新角色立绘系统和UI布局相关文档。T42: '更新文档'→18步(4 respond+7 Edit+4 Read+3 TodoWrite)，更新清空存档和解锁所有关卡功能相关文档。三次文档更新均无build，使用TodoWrite(3-5项)跟踪更新进度，每次涉及7-18个文档编辑。Edit量随本轮代码修改复杂度递增(18→8→7)，与T17(99步角色立绘系统)→T13(55步文档)的重度代码→重度文档模式一致。 7a895854扩展了此模式的'级联文档更新'变体——T4: '更新文档'→26步(8 Edit+7 respond+4 Read+3 TodoWrite+3 Bash+1 Task)，更新多文档→T5: '更新完成记录.md'→4步(1 Read+1 Edit+1 TodoWrite+1 respond)，单文件精准更新→T6: '更新游戏自查方向指南.md'→7步(5 Edit+1 Read+1 respond)，另一单文件更新。三次连续文档更新均无build，Edit量递减(8→1→5)，展示了'通用更新→指定文件更新→指定文件更新'的级联模式。T4是通用'更新文档'触发多文档同步，T5-T6是用户指定具体文件的精准更新。模式确认：post_implementation_sync存在'通用触发多文档'(08e306a0/374e4eb7)、'审查报告触发单文档'(4807e6ed)、和'级联通用+指定文件'(7a895854)三种变体。 9df66fd4强化了此模式——整个会话4次'更新文档'请求：T07: '更新文档'→56步(17 respond+13 Edit+12 Read+5 TodoWrite+4 Glob+3 Grep+2 build)，更新UI布局修改相关文档。T19: '更新文档'→6步(1 respond+4 Edit+1 Read)，轻量文档更新。T32: '更新文档'→8步(1 respond+5 Edit+2 Read)，更新云存档修复相关文档。T40: '更新文档'→4步(1 respond+1 Edit+1 Read)，极简文档更新。4次文档更新均无build（纯文档任务），使用TodoWrite跟踪更新进度（T07用5项）。T07的56步是此会话最重的文档turn，因前序T01-T06涉及大规模UI布局修改，需要同步更新多个文档。模式确认：'更新文档'=纯文档任务，识别后跳过build，用TodoWrite跟踪多文档更新。 bc3f2ce9强化了此模式——整个会话5次'更新文档'请求：T18: 39步(11 Edit+5 Todo+4 Read+3 Glob)。T25: 13步(7 Edit+4 Todo+1 Read)。T28: 26步(11 Edit+4 Read)。T32: 14步(5 Edit+3 Todo+2 Read)。T42: 50步(17 Edit+4 Todo+7 Read+1 Task)。5次文档更新均无build，使用TodoWrite跟踪。Edit量随代码修改复杂度波动(11→7→11→5→17)，T42的50步是最重文档turn。 1cd7c1eb强化了此模式的'重度文档漂移'变体：T07: '更新文档' -> 42步(21 Edit+8 Read+7 respond+5 TodoWrite+1 Task)。Read 8文档(文档维护规范.md,完成记录.md,总体进度.md,架构决策记录.md,策划案-大厅.md等) -> TodoWrite 5项清单 -> Edit 21处(完成记录.md x2+总体进度.md x8+架构决策记录.md x3+策划案-大厅.md x8) -> 0 build(纯文档任务)。21 Edit是此模式中最高的单turn文档编辑量，4个drift-start标记(steps 4,73,83,107)确认了edit drift在重度文档更新中的存在。与9df66fd4的T07(56步,13 Edit)和76b0acb1的T13(55步,18 Edit)对比——本session的21 Edit刷新了单turn文档编辑量纪录。模式确认：'更新文档'=纯文档任务，识别后跳过build，用TodoWrite跟踪多文档更新，edit量随本轮代码修改复杂度递增。 24a716d1强化了此模式：T5: "更新文档"→33步(13 Edit+12 respond+4 TodoWrite+3 Read+1 Task)。S0: Task查找文档文件→S2-S4: Read 3个文档(P3-消消乐.md, 完成记录.md, 总体进度.md)→S5: TodoWrite创建3项清单→S7-S19: Edit P3-消消乐.md(8处:星级分数表格和示例更新)→S22: Edit完成记录.md→S25-S30: Edit总体进度.md(4处)。33步中13 Edit，无build（纯文档任务）。与bc3f2ce9的T42(50步,17 Edit)和1cd7c1eb的T07(42步,21 Edit)对比——本session是中等体量文档更新，Edit量(13)随本轮代码修改复杂度(T00-T04的120+ Edit)成比例。模式跨10个会话确认。2c4b3363强化了此模式的'障碍/特效开发后文档同步'变体：T4: '更新文档'→8步(3 Edit+3 respond+1 Read+1 Grep)。T0-T2完成石头+冰块障碍系统后→Grep搜索相关文档→Read P3-消消乐.md→Edit 3处(石头障碍规格+冰块生命值机制+关卡配置更新)→0 build(纯文档任务)。T11: '更新文档'→36步(9 Edit+12 respond+6 Read+4 TodoWrite+1 Grep)。T5-T10完成跨游戏特效增强+冰块震动效果后→TodoWrite创建4项清单→Read 6个文档→Edit 9处(P3-消消乐.md特效规格+推箱子文档+连连看文档+记忆翻牌文档+总体进度.md)→0 build。T12: '之前设计了一个音效相关的文档，保存docs下'→14步(3 Edit+5 respond+2 Read+3 TodoWrite+1 Write)。用户提及已保存音效文档→Read架构决策记录.md→Write保存音效系统设计文档到docs/→Edit 3处更新架构决策记录(音效系统架构条目)→0 build。3次文档更新均无build，Edit量随代码修改复杂度递增(3→9→4)，与T0-T2重度障碍开发(185步)→T4轻量文档(8步)和T5-T10重度特效开发(255步)→T11中等文档(36步)的模式一致。模式跨11个会话确认。 4f916c20强化了此模式的'编辑器开发后文档同步'变体：T13: '更新文档'→66步(21 Edit+6 Read+7 Grep+4 TodoWrite)。大规模编辑器开发后文档更新→21 Edit→0 build。T18: '更新文档'→25步(12 Edit+3 Read+4 TodoWrite)。编辑器输入功能修复后文档更新→12 Edit→0 build。2次文档更新均无build，Edit量递减(21→12)。 c68e9e21展示了此模式的'UI打磨后文档同步'变体：T10: '更新文档'→17步(5 respond+4 Edit+4 Read+3 TodoWrite+1 Task)。S0: Task查找文档文件→S1-S4: Read 4个文档→S5: TodoWrite创建3项清单→S6-S9: Edit 4处更新文档(设置页面UI优化相关记录)→0 build(纯文档任务)。17步中4 Edit，无build。与24a716d1的T5(33步,13 Edit)和4f916c20的T18(25步,12 Edit)对比——本session是轻量级文档更新，Edit量(4)随本轮代码修改复杂度(T1-T9的212步UI打磨)成比例但偏轻，因为本轮主要是UI视觉调整而非新功能开发。模式跨13个会话确认。 ef2c887b展示了此模式的'极轻量配置变更后文档同步'变体：T3: '更新文档'→16步(4 respond+3 Edit+4 Read+2 Glob+2 TodoWrite+1 Grep)。T0-T2完成测试开关配置后→Grep/Glob定位受影响文档→Read 4文档→Edit 3处→0 build(纯文档任务)。T4: '更新文档'→7步(2 respond+2 Edit+1 Read+2 Grep)。极轻量二次文档更新→Read 1文档→Edit 2处→0 build。2次文档更新均无build，Edit量递减(3→2)。与c68e9e21(17步,4 Edit)对比——本session是更轻量的文档更新(16+7步,3+2 Edit)，因T0-T2仅涉及配置开关的小规模代码修改。模式跨14个会话确认。

---

## `gene_doc_post_audit_report_sync`

**审计后文档报告同步** / Post-Audit Documentation Report Sync — Multi-Document Update After Self-Check Audit and Bug Fixes

Category: `operational`

**Signals:**
- `intent:documentation`
- `post_audit_doc_update`
- `audit_report_doc_creation`
- `multi_doc_sync`
- `progress_and_completion_doc_update`
- `level_overview_doc_update`

**Preconditions:**
- 用户在完成自查审计和问题修复后，要求'更新文档'。
- 项目存在多种文档类型：完成记录、自查问题报告、总体进度、主线关卡总览等。
- Agent需要根据本轮审计和修复的结果，同步更新所有相关文档。
- 本次文档更新的核心内容包括：记录已修复的P1/P2问题、更新自查问题报告、更新完成记录和总体进度、更新主线关卡总览中的关卡信息。

**Evidence:** T2: '更新文档'→45步(18 Edit+6 Read+14 respond+6 TodoWrite+1 Task)。S0 Task查找文档文件→S5 TodoWrite创建5项清单(完成记录、自查问题报告、总体进度、主线关卡总览)→S6-S9读取4个文档→S10-S13更新完成记录.md(1次Edit)→S14-S19更新自查问题报告.md(2次Edit)→S20-S24更新总体进度.md(2次Edit)→S25-S42更新主线关卡总览.md(13次Edit，因涉及多个关卡的标题/难度信息)→S43 TodoWrite确认全部完成。典型的'审计修复后→多文档同步报告'模式，特别是自查问题报告.md的创建/更新是本轮特有产物。

---

## `gene_op_subagent_warmup_waste`

**子Agent Warmup浪费模式** / Subagent Warmup Waste — Parallel Dispatch with Majority Idle Returns

Category: `operational`

**Signals:**
- `intent:new_feature`
- `intent:feature_modification`
- `intent:content_creation`
- `intent:planning_design`
- `intent:inquiry`
- `intent:inspection_review`
- `parallel_subagent_ge_3`
- `subagent_warmup_response`
- `subagent_efficiency_lt_0.50`
- `context_budget_waste`
- `warmup_in_doc_only_session`

**Preconditions:**
- Agent分派了3个或更多子agent并行探索。
- 其中超过一半的子agent返回了无实质内容的响应（如仅返回'Warmup'或空响应）。
- 只有1-2个子agent真正执行了有意义的搜索任务。
- 这浪费了context预算和步骤数——每个无效子agent消耗了至少2步（dispatch + result）。
- 此模式不仅出现在new_feature/feature_modification/content_creation场景中，也出现在inquiry和inspection_review场景中——即使是纯信息查询或文档审查，Agent仍可能分派多个子agent并行探索。

**Evidence:** 36749904: T1: 5个子agent分派(a17f38b,a9a6dd7,a9bd74d,ae4c822,ae5c319)，仅2个执行了有效任务(a17f38b搜索关卡点击相关代码,ae4c822搜索健康游戏忠告相关代码)，3个仅返回'Warmup'(a9a6dd7,a9bd74d,ae5c319)。T2: 1个子agent执行了有效任务(搜索onClick/关卡相关代码)。5个子agent中3个(60%)为无效warmup，浪费了至少6步(dispatch+result per idle agent)。这是典型的'批量分派但环境不支持完整子agent执行'模式。4a183ae9强化了此模式：T0: 5个子agent分派(a578ed5,a7b0bd5+3更多)，仅2个执行了有效任务(a578ed5探索游戏结束页面代码,a7b0bd5查找星级评定条件逻辑)，3个仅返回'Warmup'。Agent随后降级为直接Read(4个result-popup.lua文件)+TodoWrite规划。5个子agent中3个(60%)为无效warmup，模式跨会话确认。4d80bab3进一步强化此模式：T2: 7个子agent分派(a1badeb,a326002,a3e0a37,a7968f4,a85c50c,aa4410a,af71228)，仅4个执行了有效任务(a1badeb读取P4已建文件,aa4410a读取P2参考文件,a7968f4搜索矢量图案代码,af71228探索项目结构)，3个仅返回'Warmup'(a326002,a3e0a37,a85c50c)。7个子agent中3个(43%)为无效warmup。虽然有效率(57%)略高于此前会话(40%)，但仍低于50%的理想阈值。Agent在收到有效子agent结果后继续实施，未因warmup失败而阻塞。模式跨3个会话确认。6346da75进一步强化此模式至75%warmup率(最高纪录)：T1(UI暖色调修改):4个子agent分派(a0e7a70,aa0e233,aeef6a8,af2c7c5)，仅1个执行了有效任务(a0e7a70查找项目文档文件和memory目录)，3个仅返回'Warmup'(aa0e233,aeef6a8,af2c7c5)。4个子agent中3个(75%)为无效warmup，刷新此前最高纪录60%。Agent在收到有效子agent结果后继续Read 7个文件+16 Edit+6 TodoWrite完成UI暖色调修改。模式跨4个会话确认，warmup率趋势:43%→57%→60%→75%。870a5123刷新至100%warmup率(绝对纪录)：T0(生成总体进度总结):3个子agent分派(a23cbea,a834bdb,af4b3b3)，全部仅返回2条消息(warmup)，0个执行有效任务。3个子agent中3个(100%)为无效warmup。值得注意的是本session是纯文档任务(content_creation→documentation)，不含任何代码探索需求——即使在这种场景下Agent仍然分派了3个子agent，全部浪费。warmup率趋势:43%→57%→60%→75%→100%，说明在此环境中子agent批量分派的效率持续恶化至完全无效。 9e31e39f强化了此模式的'inquiry场景'变体：T0(检查开发记录阻碍点):5个子agent分派(a406bbc,a987dfb,aaaf52d,ac4abe8,ac955be)，仅2个执行了有效任务(ac4abe8检查代码结构,ac955be检查策划案/架构决策)，3个仅返回'Warmup'(a406bbc,a987dfb,aaaf52d)。5个子agent中3个(60%)为无效warmup。与此前会话不同——本session是纯inquiry场景(0 edits 0 builds)，不含代码实施需求，但仍然分派了5个子agent。warmup率60%与此前36749904/4a183ae9持平。模式跨6个会话确认，warmup率在43%-100%间波动，说明子agent批量分派的浪费是此环境的系统性问题。 b67698e4确认了此模式的'inspection_review场景'变体：T0(审查开发记录+build):3个子agent分派(a40acb2,a8c2da3,ae3b450)，全部仅返回'Warmup'或就绪声明，0个执行有效任务。3个子agent中3个(100%)为无效warmup，与870a5123持平绝对纪录。值得注意的是本session是inspection_review场景(用户打开开发记录文档后输入'build')，不含任何代码探索需求——即使在这种轻量审查场景中Agent仍然分派了3个子agent，全部浪费。warmup率趋势:43%→57%→60%→75%→100%→60%→100%，说明子agent批量分派的浪费是此环境的系统性问题，跨7个会话、覆盖new_feature/feature_modification/content_creation/inquiry/inspection_review全意图类型均出现。 be94308f确认了此模式在'关卡编辑器开发'场景中的持续出现：T0(制作测试总开关):3个子agent分派(a608a8b,a93578d,aed80f1)，全部仅返回'Warmup'或就绪声明，0个执行有效任务。3个子agent中3个(100%)为无效warmup，与870a5123/b67698e4持平绝对纪录。值得注意的是本session是new_feature场景(关卡编辑器开发)，用户在T0-T3连续4个turn提出新功能需求，但子agent在会话启动时即被分派且全部浪费。warmup率趋势:43%→57%→60%→75%→100%→60%→100%→100%，说明子agent批量分派的浪费是此环境的系统性问题，跨8个会话确认。 1cd7c1eb确认了此模式的'planning_design场景'变体：T00(设计游戏大厅方案):8个子agent分派(a031a4a,a1871bc,a27f1a2,a43735e,a46c696,a5a3bf6,a6cedf2,a9b9959)，仅3个执行了有效任务(a031a4a探索scripts目录29步,a43735e探索UI结构25步,a6cedf2读取组件18步)，5个仅返回'Warmup'或空响应(a1871bc,a27f1a2,a46c696,a5a3bf6各1步respond)。8个子agent中5个(62.5%)为无效warmup。这是首个planning_design场景下的subagent warmup waste记录，刷新了此前最高warmup率100%(870a5123/b67698e4)的session数量纪录。warmup率趋势:43%->57%->60%->75%->100%->60%->100%->62.5%。模式跨9个会话确认，覆盖new_feature/feature_modification/content_creation/inquiry/inspection_review/planning_design全意图类型。2c4b3363确认了此模式在'障碍系统+特效增强'场景中的持续出现：整个会话16个子agent分派，5个仅返回'Warmup'(a0bfb83,a2d2468,a3dfdbc,ab9591c,af3c038各1-3步纯respond)，11个执行了有效任务(a1e165e,a2aeb2c,a2f55d5,a328bda,a38b406,a42d0d5,a5dc27a,a708a94,a9eab66,ab8f335,abc44c8各7-71步不等)。16个子agent中5个(31%)为无效warmup。与此前会话不同——本session的warmup率(31%)显著低于此前所有会话(43%-100%)，说明Agent在此会话中的子agent分派效率有所改善，但仍然是系统性问题。16个子agent分布在T0(石头障碍,1个),T2(冰块,3个),T5(特效增强,2个),T6(音效设计,5个),T8(连连看特效,1个),T9(翻牌特效,1个),T10(冰块震动,1个)等多个重度turn中。T6(音效系统设计)分派了5个子agent并行探索音效系统现状，是此会话中子agent最密集的turn。warmup率趋势:43%->57%->60%->75%->100%->60%->100%->100%->62.5%->31%。模式跨10个会话确认。 8a77e633确认了此模式在'音效审计+集成'场景中的持续出现：T1(音效完整性检查):7个子agent分派(a38c493,a399e46,a3a9e2b,a5acd37,a66b98f,a72b7d7,a800113)，仅4个执行了有效任务(a399e46搜索UI按钮点击处理器,a3a9e2b搜索音效测试页面+消消乐音效配置,a5acd37探索大厅/游戏入口UI结构,a800113搜索音效文件设置)，3个仅返回'Warmup'(a38c493,a66b98f,a72b7d7各1-2步纯respond)。7个子agent中3个(43%)为无效warmup。与此前会话不同——本session是inspection_review场景(音效审计)，但分派了7个子agent并行探索音效系统现状、UI按钮结构、音效文件等。warmup率43%与此前36749904/4a183ae9持平。模式跨11个会话确认。 ef2c887b确认了此模式在'配置开关开发'场景中的持续出现：T0(在配置中增加测试开关):3个子agent分派(a12cd4c+2更多)，全部仅返回'Warmup'，0个执行有效任务。3个子agent中3个(100%)为无效warmup，与870a5123/b67698e4/be94308f持平绝对纪录。值得注意的是本session是new_feature场景(配置开关开发)，但子agent在会话启动时即被分派且全部浪费。warmup率趋势:43%->57%->60%->75%->100%->60%->100%->100%->62.5%->31%->43%->100%。模式跨12个会话确认。 f4dd8c16确认了此模式在"数据文件修改"场景中的持续出现：T0(修改推箱子关卡步数):3个子agent分派(a05638f+2更多)，仅1个执行了有效任务(a05638f搜索推箱子关卡文件)，2个仅返回空响应(a52bacf,a535e58各0条消息)。3个子agent中2个(67%)为无效warmup。T0还分派了第2批3个子agent(ab4116d,ac64b28,adf8734)用于消消乐文件搜索，其中2个返回"Warmup"(ac64b28,adf8734)，仅1个有效(ab4116d)。总计6个子agent分派，3个有效(50%)，3个无效(50%)。warmup率50%与此前36749904/4a183ae9持平。模式跨13个会话确认。 019cfa80强化了此模式的'极轻量inquiry场景'变体：T0(调用list_tap_developers获取厂商列表):3个子agent分派(a4122bb,a59de43,aa6b1ef)，全部仅返回Warmup就绪声明(a4122bb:"Ready. What would you like me to explore?",a59de43:"Ready to go.",aa6b1ef:"I'm ready to help you search and analyze")，0个执行有效任务。3个子agent中3个(100%)为无效warmup，与870a5123/b67698e4/be94308f持平绝对纪录。值得注意的是本session是极轻量inquiry场景(仅2步,1 MCP tool call+1 respond,9.7秒)，不含任何代码探索需求——即使在这种单次工具调用场景下Agent仍然分派了3个子agent，全部浪费。warmup率趋势:43%→57%→60%→75%→100%→60%→100%→100%→62.5%→31%→43%→100%→50%→100%。模式跨14个会话确认，覆盖new_feature/feature_modification/content_creation/inquiry/inspection_review/planning_design全意图类型，且从重度实施(170步)到极轻量工具调用(2步)全量级出现。

---

## `gene_mw_build_command_triggers_code_fix`

**Build命令触发代码修复模式** / Build Command Triggers Code Fix — Bare Build Preceded by Diagnostic Read-Edit-Build Cycle

Category: `operational`

**Signals:**
- `intent:meta_workflow`
- `bare_build_command`
- `build_triggers_code_fix`
- `read_before_build`
- `edit_before_build`
- `build_as_diagnostic_trigger`

**Preconditions:**
- 用户仅输入'build'（无附加指令），期望执行构建操作。
- 但Agent在build前发现代码存在问题（如已知错误未修复、代码不完整），主动先修复代码再build。
- 这反映了Agent的判断：直接build会失败，需要先修复已知问题。
- 用户可能在前序turn中报告了错误，但Agent尚未完成修复——用户输入'build'是在催促或确认。

**Evidence:** T2: 用户仅输入'build'→55步(20 respond+9 Read+9 Edit+4 build+4 lua_lsp_client+3 TodoWrite+3 Grep+3 Bash)。Agent没有直接build，而是：S0-S18 respond+Read(9个文件)诊断当前代码状态→S19-S27 Edit(9次)修复adapter.lua中的NanoVG渲染问题→S28-S31 lua_lsp_client检查→S32-S34 Grep验证→S35-S37 Bash执行→S38-S41 TodoWrite跟踪→S42-S45 respond汇报→S46-S49 build(4次build，说明多次尝试)。典型的'bare build→Agent判断代码有问题→大规模Read诊断→9 Edit修复→多次build验证'模式。用户仅输入2个字母'build'，但Agent执行了55步的完整修复管线。这反映了Agent的正确判断：直接build会失败，需要先修复adapter的draw nil问题。

---

## `gene_mw_git_upload_workflow`

**Git仓库上传管线** / Git Repository Upload Pipeline — Todo-Anchored Bash-Heavy Code Hosting Workflow

Category: `operational`

**Signals:**
- `intent:meta_workflow`
- `target:tooling`
- `github_repository_upload`
- `TodoWrite_anchored`
- `Bash_heavy_ge_5`
- `git_init_and_push_pipeline`
- `proxy_config_first`
- `no_code_edit`

**Preconditions:**
- 用户要求将当前项目代码上传到指定的GitHub仓库（或子目录）。
- 目标仓库可能不存在本地副本，需要先初始化git仓库。
- 运行环境可能需要代理配置才能访问GitHub。
- 这是纯操作型任务——不涉及代码修改、bug修复或功能开发。

**Evidence:** T1: '将目前的代码，上传到 https://github.com/Wzp-xd/Tools.git仓库，下新建一个文件夹"game001"中'→15步(5 respond+7 Bash+3 TodoWrite)。S0: TodoWrite创建3步清单→S2: Bash配置git代理(http/https proxy 127.0.0.1:1080)→S5: Bash创建Tools/game001目录，复制scripts/assets/docs/config/levels→S8: Bash配置git user.email/user.name→S9: Bash执行git status确认127个文件→S11: Bash执行git log确认提交→S13: Bash执行git push origin main fallback master。典型的'TodoWrite锚定→代理配置→文件复制→git初始化→状态验证→推送'管线。全程0代码编辑0 build，纯操作型meta_workflow。

---

## `gene_doc_maintenance_rhythm`

**文档维护节奏** / Documentation Maintenance Rhythm — Proactive Dev Log and Doc Updates During Development

Category: `operational`

**Signals:**
- `intent:documentation`
- `intent:inspection_review`
- `target:documentation`
- `proactive_doc_maintenance`
- `dev_log_update`
- `todo_write_doc_tracking`
- `multi_doc_edit`
- `no_build_doc_turn`

**Preconditions:**
- 用户在功能开发过程中或完成后，要求检查或更新开发记录/文档。
- 这不是代码变更后的文档同步（gene_doc_post_implementation_sync），而是主动的文档维护。
- 典型触发词：'增加开发记录'、'检查开发记录'、'检查文档是否有需要更新的地方'。
- 文档更新涉及多个文件（开发记录、总体进度、架构决策记录等）。
- 纯文档turn，不需要build。

**Evidence:** 5c2aeaee T3: '增加P1-推箱子的开发记录'→26步(8 respond+6 Read+3 TodoWrite+3 Edit+2 Write+2 Bash)。TodoWrite创建3项清单→Read现有开发记录→Edit/Write更新开发记录文档→Bash验证。T9: '检查 开发记录，是否有需要更新的地方'→33步(12 respond+10 Edit+5 TodoWrite+3 Glob+2 Read+1 Bash)。主动检查开发记录→Glob列出所有文档→Read当前开发记录→对比本轮代码变更→10 Edit更新遗漏条目。两次文档维护均无build，用TodoWrite跟踪进度。T3是'主动添加'模式，T9是'检查gap并补充'模式。6b8bf0cd强化了此模式并展示了'更新→主动检查'两步节奏变体：T4: '更新开发记录-大厅M1.md'→纯文档更新，Edit开发记录→respond确认。T5: '检查其他文档，是否有需要更新的地方'→ inspection_review，主动检查除开发记录外的其他文档(总体进度.md、架构决策记录.md等)→发现gap→Edit更新。与5c2aeaee不同——本session的T4→T5形成明确的'先更新指定文档→再主动检查其他文档'两步节奏，T4是用户指定的目标文档更新，T5是用户主动发起的跨文档gap检查。模式确认：doc_maintenance_rhythm存在'单步更新'(5c2aeaee T3)、'单步检查gap'(5c2aeaee T9)、和'更新→检查两步节奏'(6b8bf0cd T4→T5)三种变体。

---

## `gene_doc_single_doc_refinement_cascade`

**单文档连续精简级联** / Single-Document Refinement Cascade — Generate-Then-Iteratively-Condense on One File

Category: `operational`

**Signals:**
- `intent:content_creation`
- `intent:feature_modification`
- `intent:planning_design`
- `target:documentation`
- `single_document_focus`
- `consecutive_same_doc_ge_3`
- `read_write_respond_cycle`
- `no_build_no_code_edit`
- `no_todo_write`
- `mcp_doc_tools`
- `ultralight_turns_le_5_steps`
- `generate_then_iterative_refine`

**Preconditions:**
- 用户要求基于已有文档生成新的总结/报告文档，或对单一文档进行连续多轮修改。
- 连续3+次turn都指向同一个文档文件（如总体进度总结.md）。
- 每次修改遵循Read→Write/Edit→respond的极简循环，3-5步/turn。
- 不涉及任何代码编辑、build、Grep、TodoWrite操作。
- 典型节奏：生成新文档→删除不需要的内容→增加新章节→精简文字。
- 用户使用'更加精简'、'删除X内容'、'增加Y'等指令，每次只做一个维度的调整。

**Evidence:** T0: '根据总体进度.md，为我生成一个新的总体进度总结.md'→5步(3 respond+1 Read+1 Write)。Read总体进度.md→Write创建总体进度总结.md→respond确认。T1: '删除总体进度总结.md中和技术特征相关的内容，只总结游戏本身的内容'→3步(1 Read+1 Write+1 respond)。Read当前文档→Write重写(删除技术章节)→respond确认。T2: '增加后续计划：优化关卡，音效，UI细节，制作一个初版。根据初版反馈是否有需要修改的地方。扩展内容：更多游戏、关卡'→3步(1 Read+1 Edit+1 respond)。Read当前文档→Edit追加后续计划章节→respond确认。T3: '更加精简总体进度总结.md'→3步(1 Read+1 Write+1 respond)。Read当前文档→Write精简版本→respond确认。整个会话4个turn全部针对同一文档(总体进度总结.md)，14步总计，平均每turn 3.5步。0 build、0 Grep、0 TodoWrite、0代码编辑。典型的'生成→删除→增加→精简'单文档迭代管线。与gene_doc_maintenance_rhythm不同——后者涉及多文档协调(开发记录+总体进度+架构决策记录)和TodoWrite跟踪，本模式是单一文档的极简迭代。与gene_doc_post_implementation_sync不同——后者是代码变更后的多文档同步更新，本模式是纯文档操作，无代码变更驱动。. c44d6be2强化了此模式的"完成记录精炼"变体：T3: '在文档中增加，游戏主体框架基本完成'→3步(1 Read+1 Edit+1 respond)。T4: '优化和精炼完成记录.md中3月20号的内容'→4步(2 respond+1 Read+1 Edit)。T5: '继续精简完成记录.md中3月20号的内容'→3步(1 Read+1 Edit+1 respond)。T6: '增加完成记录.md中3月20号内容，增加推箱子关卡内容，丰富消消乐玩法'→3步(1 Read+1 Edit+1 respond)。4个连续turn全部针对同一文档(完成记录.md)，13步总计，平均每turn 3.25步。0 build、0 Grep、0 TodoWrite、0代码编辑。与870a5123不同——后者是'生成→删除→增加→精简'的文档类型转换管线，本session是'增加→优化→继续精简→补充内容'的同一日期内容迭代精炼。模式跨2个会话确认。

---

## `gene_fm_doc_refinement_duplicate_prompts`

**文档修改重复请求模式** / Doc Refinement Duplicate Prompts — Near-Identical Documentation Edit Requests Across Consecutive Turns

Category: `operational`

**Signals:**
- `intent:feature_modification`
- `intent:documentation`
- `target:documentation`
- `duplicate_prompt_consecutive_turns`
- `near_identical_prompts_ge_2`
- `ultralight_turns_le_4_steps`
- `read_edit_respond_rhythm`
- `same_document_focus`

**Preconditions:**
- 用户连续2+次发送几乎相同的文档修改请求（如'精简完成记录中3-24日的内容'→再次发送几乎相同的请求）。
- 每次修改针对同一文档文件（如完成记录.md）。
- 每次修改量极小（1 Edit），turn步骤数≤4步（Read+Edit+respond）。
- 这可能是用户重复发送、或网络重传、或对前次修改结果不满意但未明确表达。
- Agent应检测重复请求，避免不必要的重复操作。

**Evidence:** T09: '精简完成记录中，3-24日的内容，增加"增加主线相关功能"的描述'→3步(1 Read+1 Edit+1 respond)。T10: '优化完成记录，3月24日的内容，并增加，角色立绘生成相关描述'→3步(1 Read+1 Edit+1 respond)。T12: 与T09几乎相同的请求→3步(1 Read+1 Edit+1 respond)。T13: 与T10几乎相同的请求→3步(1 Read+1 Edit+1 respond)。P9和P12的请求文本完全相同（均引用完成记录.md+精简3-24日+增加主线功能描述），P10和P13的请求文本完全相同（优化3月24日+角色立绘生成描述）。4个turn均为恰好3步的Read+Edit+respond极简循环，全部针对完成记录.md。这可能是用户重复发送或网络重传。模式：duplicate_prompt→ultralight_3step→same_document。 be94308f强化了此模式：T04: '完成记录中，将3月19日的内容，精简总结一下'→4步(1 Read+1 Edit+2 respond)。T05: '修改完成记录.md，将3月19日的内容，精简总结一下'→3步(1 Read+1 Edit+1 respond)。两个turn几乎相同的请求（均针对完成记录.md的3月19日内容精简），4步→3步递减。T05的请求在T04基础上增加了文件名引用格式，但核心意图完全一致。可能是用户重复发送或对前次结果不满意但未明确表达。模式跨2个会话确认。 ef2c887b强化了此模式的'纯更新文档'变体：T3: '更新文档'→16步(4 respond+3 Edit+4 Read+2 Glob+2 TodoWrite+1 Grep)。T4: '更新文档'→7步(2 respond+2 Edit+1 Read+2 Grep)。两个turn完全相同的请求('更新文档')，16步→7步递减。T3较重因需要先Grep/Glob定位受影响的文档→Read 4文档→Edit 3处；T4极轻量因T3已建立上下文→直接Read 1文档→Edit 2处。与bdf118ee/be94308f不同——后者的重复请求是针对具体文档内容的精简/优化描述，本session是通用'更新文档'请求的重复。但'相同请求→ultralight递减→same_document'模式完全一致。模式跨3个会话确认。. a7d1b207展示了此模式的'执行失败'变体：T11: '修改具体的游戏名字，而不是P1P2P3'→0步（no agent run）。T12: '修改文档中显示具体的游戏名字，而不是P1P2P3'→no agent run。两个几乎相同的请求均未执行（API错误或会话终止），与此前所有会话的重复请求都有成功Edit不同。这是重复请求的'执行失败'变体，详见gene_sr_duplicate_prompt_execution_failure。

---

## `gene_doc_dual_inspection_rhythm`

**双文档检查节奏模式** / Dual Documentation Inspection Rhythm — Mid-Session and End-Session Documentation Gap Checks

Category: `operational`

**Signals:**
- `intent:inspection_review`
- `target:documentation`
- `dual_inspection_in_session`
- `mid_session_and_end_session_checkpoints`
- `read_respond_edit_pattern`
- `no_build_doc_turn`
- `TodoWrite_for_doc_tracking`

**Preconditions:**
- 用户在同一会话中两次提出'检查文档是否有需要更新的地方'的请求。
- 第一次检查通常在中途（完成一批功能修改后），第二次检查在会话末尾（所有修改完成后）。
- 这不是主动的文档维护（gene_doc_maintenance_rhythm）——用户是要求Agent检查文档gap，而非直接要求更新。
- 每次检查的模式为：Read相关文档→respond汇报发现→如有需要则Edit更新。
- 纯文档turn，不需要build。

**Evidence:** T12: '检查文档，是否有需要更新的的内容'→36步(10 Edit+9 respond+7 Read+5 TodoWrite+3 Glob)。完成特效系列修改后的中途文档检查→Glob列出所有.md→Read 7个文档→TodoWrite创建5项清单→Edit 10处更新文档(总体进度.md×5+完成记录.md×3+P3-消消乐.md×2)→0 build(纯文档任务)。T15: '检查文档是否有需要更新的地方'→14步(5 Edit+4 respond+3 TodoWrite+2 Read)。会话末尾的最终文档检查→Read 2个文档→TodoWrite创建3项清单→Edit 5处更新文档(总体进度.md×2+完成记录.md×2+P3-消消乐.md×1)→0 build。两次文档检查形成'中途检查(36步,10 Edit)→末尾检查(14步,5 Edit)'的节奏，Edit量递减说明大部分文档已在此前检查中更新。与gene_doc_maintenance_rhythm不同——后者是主动的'增加开发记录'/'检查开发记录'模式，本模式是被动响应用户的'检查文档是否有需要更新'请求，聚焦文档与代码的一致性检查。

---

## `gene_doc_cross_project_generalization`

**文档跨项目通用化** / Cross-Project Document Generalization — Abstract Project-Specific Docs into Reusable Templates

Category: `operational`

**Signals:**
- `intent:feature_modification`
- `target:documentation`
- `cross_project_reusability`
- `remove_project_specific_details`
- `abstract_to_problem_and_solution`
- `template_conversion`
- `has_attached_doc`
- `mentions_specific_file`

**Preconditions:**
- 用户打开了一个项目特定的文档（如自查指南、开发记录、问题报告），要求修改为跨项目通用的模板。
- 用户明确要求'不要记录项目中的具体文件'——删除项目特定的文件名、路径、变量名等。
- 用户要求'记录需要处理的问题，参考处理方法'——保留问题类型描述和解决思路，抽象为可复用的指南。
- 目标产物是一份可以在其他项目中直接使用的通用文档，而非项目特定的记录。
- 这是纯文档任务——不涉及代码编辑或build。

**Evidence:** T8: '修改游戏自查方向指南.md，这是一个给其他项目用的指南，不要记录项目中的具体文件，记录需要处理的问题，参考处理方法'→6步(2 respond+3 Edit+1 Read)。Read游戏自查方向指南.md→3 Edit删除项目特定文件引用(如kinsoku.lua等)，保留问题类型和解决方法→respond确认。典型的'读取→识别项目特定内容→Edit抽象为通用描述'管线。6步完成，纯文档任务无build。与gene_doc_single_doc_refinement_cascade不同——后者是单一文档的迭代精简(删除内容→增加章节→精简文字)，本模式是'项目特定→跨项目通用'的抽象化转换，关注内容通用性而非篇幅精简。与gene_doc_post_implementation_sync不同——后者是代码变更后的多文档同步更新，本模式是单一文档的通用化改造，与代码变更无关。

---

## `gene_doc_heavy_to_light_refinement_cascade`

**文档重度到轻量精炼级联** / Doc Heavy-to-Light Refinement Cascade — Multi-Document Sync to Targeted Edit to Terminology Query

Category: `operational`

**Signals:**
- `intent:documentation`
- `intent:feature_modification`
- `target:documentation`
- `consecutive_doc_turns_ge_3`
- `heavy_to_medium_to_light_effort_curve`
- `first_turn_multi_doc_heavy_edit`
- `second_turn_single_doc_targeted_edit`
- `third_turn_inquiry_or_ultralight`

**Preconditions:**
- 用户在代码变更后要求'更新文档'，触发大规模多文档同步（30+ Edit，跨多个.md文件）。
- 用户在下一turn针对同一文档的特定日期/章节进行精炼（1 Edit，3步）。
- 用户在再下一turn询问文档中的术语含义（纯inquiry，1步）。
- 这与gene_doc_post_implementation_sync不同——后者是单turn的多文档同步，本模式是'重度同步→轻量精炼→术语查询'的3-turn级联。
- 这也与gene_doc_ultralight_update_rhythm不同——后者是连续3+次极轻量文档更新（≤6步递减），本模式以重度turn开始。

**Evidence:** T8: '更新文档'→67步(34 Edit+18 respond+5 Read+4 Glob+4 TodoWrite+1 Task+1 Grep)。大规模多文档同步：34 Edit跨多个.md文件（完成记录.md、总体进度.md、架构决策记录.md等），受T6-T7消消乐限时模式变更影响。T9: '修改完成记录.md的2026-03-18，将完成项目总结精炼一下，现在的细则太多了'→3步(1 Read+1 Edit+1 respond)。针对完成记录.md中特定日期的精炼，1 Edit。T10: '完成记录中的P1P2P3分别是什么意思'→1步(respond)。纯术语查询，直接回答P1/P2/P3含义。0 Edit 0 build。典型的'重度多文档同步(67步,34 Edit)→ targeted精炼(3步,1 Edit)→术语查询(1步)'级联，effort 67→3→1急剧递减。

---

## `gene_ir_doc_inspection_heavy`

**重度文档检查模式——极简请求触发的多文档审计管线** / Heavy Documentation Inspection - Multi-Document Audit Pipeline Triggered by Minimal Request

Category: `operational`

**Signals:**
- `intent:inspection_review`
- `target:documentation`
- `heavy_doc_inspection_ge_80_steps`
- `check_doc_update_phrase`
- `task_exploration_ge_1`
- `bash_heavy_ge_5`
- `edit_heavy_ge_20`
- `todo_ge_5`
- `zero_user_attached_doc`
- `proactive_multi_doc_audit`

**Preconditions:**
- 用户发送一个极简的文档检查请求（如'检查文档是否有需要更新的部分'），没有附带具体文档。
- 这不是轻量级审查（通常5-15步），而是触发了一次重度的多文档审计。
- Agent需要自主探索项目中的所有文档文件，对比代码变更，识别需要更新的部分。
- 审计turn通常包含：Task探索文档结构、Bash列出文件、Read多个文档、TodoWrite创建检查清单、批量Edit更新。
- 这是一个'主动审计'模式——用户只给了一个模糊指令，Agent自行决定审计范围和深度。

**Evidence:** T4: 检查文档是否有需要更新的部分 -> 89步(30 respond+28 Edit+13 Read+8 Todo+6 Bash+1 Grep+1 Glob+1 Task+1 build)。极简请求触发重度审计：Task探索项目 -> Bash列出docs/文件 -> TodoWrite创建8项检查清单 -> Read 13个文档文件 -> 28 Edit批量更新文档(总体进度.md、完成记录.md、架构决策记录.md等) -> build验证。89步是所有inspection_review turn中最重的，远超典型的5-15步轻量审查。与gene_sr_doc_inspection_rhythm(4次检查分布在会话中)和gene_ir_minimal_inspection_rhythm(1-2步纯Read+respond)不同——本模式是'单次极简请求触发重度多文档审计'的极端变体。

---

## `gene_doc_progress_doc_lifecycle`

**文档生命周期级联——创建、精炼、补充、提取的完整管线** / Documentation Lifecycle Cascade - Create, Refine, Supplement, Extract Complete Pipeline

Category: `operational`

**Signals:**
- `intent:documentation`
- `intent:content_creation`
- `intent:inspection_review`
- `intent:inquiry`
- `target:documentation`
- `doc_creation_then_refinement_cascade`
- `consecutive_doc_turns_ge_5`
- `has_attached_doc`
- `mentions_specific_file`
- `progress_document_pattern`
- `completion_log_creation`
- `doc_extraction_to_separate_file`

**Preconditions:**
- 用户要求创建一份总体进度文档，总结项目当前完成状态。
- 文档创建后，用户在连续5+个turn中对同一文档进行迭代操作：修改呈现方式、询问术语含义、添加完成记录、提取内容到独立文档、指出缺失信息。
- 这是一个完整的'文档生命周期'模式：创建 -> 精炼 -> 查询 -> 补充 -> 提取 -> 审查。
- 用户每次都打开/引用同一文档文件（总体进度.md或完成记录.md），形成文档锚定。
- 每个turn都极度轻量（3-10步），是典型的文档迭代维护节奏。

**Evidence:** T6: 新增总体进度文档，保存在docs下，总结目前游戏的完成内容 -> 20步(2 Edit+5 Read+1 Write+2 Todo+4 Bash+6 respond)。Read开发记录 -> Write创建总体进度.md。T7: 修改总体进度.md只显示已完成内容，不显示具体的细则 -> 6步(2 Read+1 Write+3 respond)。Write重写为总述性描述。T8: Lifecycle SDK是什么 -> 3步(2 respond+1 Task)。纯术语查询，直接回答。T9: 增加完成记录文档。今日已完成的内容，增加日期索引 -> 3步(1 Read+1 Edit+1 respond)。Edit总体进度.md添加完成记录。T10: 将总体进度.md中的已完成内容，整理成一个单独的文档 -> 8步(2 Read+1 Write+1 Edit+3 respond)。Write创建完成记录.md。T11: 完成记录，没有记录大厅和推箱子游戏的开发完成状态 -> 6步(2 Read+1 Write+3 respond)。Read开发记录 -> Write重写完成记录.md。6个连续doc turn(20+6+3+3+8+6=46步)，形成'创建 -> 精炼 -> 查询 -> 补充 -> 提取 -> 审查修复'的完整文档生命周期管线。与gene_doc_single_doc_refinement_cascade(生成 -> 删除 -> 增加 -> 精简)不同——本模式是更完整的文档生命周期，涵盖从创建到维护的全流程。

---
