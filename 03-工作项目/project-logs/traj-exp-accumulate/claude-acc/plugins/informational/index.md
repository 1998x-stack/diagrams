# informational — Gene Index

**Gene count:** 12

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_inq_design_doc_preflight_review` | Design Doc Preflight Review — Gap Analysis with Default Strategy Proposals | informational | 8x: 06335c24, 11e7ed86, 4cfa39d0 +5 | `intent:inspection_review`, `intent:inquiry`, `has_attached_doc` |
| 2 | `gene_inq_current_impl_audit` | Current Implementation Status Audit — Explore-First Structured Answer | informational | 6x: 08e306a0, 44926b0f, 5dbc4646 +3 | `intent:inquiry`, `target:ui_layout`, `target:game_logic` |
| 3 | `gene_inq_new_system_feasibility` | New System Feasibility Check — Architecture-Grounded Structured Analysis | informational | 1x: 0997e370 | `intent:inquiry`, `intent:planning_design`, `new_system_proposed` |
| 4 | `gene_inq_pre_impl_blocker_audit` | Pre-Implementation Blocker Audit — Subagent-Driven Technical Dependency Check | informational | 2x: 0997e370, 11e7ed86 | `intent:inquiry`, `follows_planning_design_session`, `no_attached_doc` |
| 5 | `gene_inq_full_product_readiness_audit` | Full-Game Product Readiness Audit — Multi-Subagent Read-All, Priority-Tiered Issue Report | informational | 1x: 24a716d1 | `intent:inquiry`, `open_ended_product_review`, `no_attached_doc` |
| 6 | `gene_ir_dev_progress_next_task` | Development Progress Audit — Full Project Scan to Recommend Next Task | informational | 1x: 2bc63c91 | `intent:inspection_review`, `intent:inquiry`, `no_attached_doc` |
| 7 | `gene_ir_checklist_guided_parallel_audit` | Checklist-Guide-Driven Parallel Multi-Dimension Game Audit | informational | 2x: 0ea2a577, 762afe73 | `intent:inspection_review`, `has_attached_doc`, `compliance_checklist_attached` |
| 8 | `gene_ir_issue_report_sequential_triage` | Issue Report Sequential Triage — Per-File Verification with Can-Fix/Cannot-Fix Stratification | informational | 1x: 4463c53b | `intent:inspection_review`, `has_attached_doc`, `target:documentation` |
| 9 | `gene_ir_fix_proposal_logic_audit` | Fix Proposal Logic Audit — Two-Pass Verification of Data Accuracy and Fix Direction | informational | 1x: 4807e6ed | `intent:inspection_review`, `has_attached_doc`, `target:documentation` |
| 10 | `gene_ir_single_doc_quality_audit` | Single-Doc Quality Audit — Glob Project Context Discovery + Structured Issues Report | informational | 2x: 5634a485, d02df5f6 | `intent:inspection_review`, `has_attached_doc`, `single_doc_attached` |
| 11 | `gene_inq_open_ended_optimization_audit` | Open-Ended Optimization Audit — Multi-Subagent Code Scan to Priority-Grouped Checklist | informational | 2x: a09c411b, f14c92eb | `intent:inquiry`, `optimization_opportunities_requested`, `open_ended_product_optimization` |
| 12 | `gene_inq_mcp_tool_poll_loop` | MCP Tool Polling Loop: Consecutive Identical Tool Invocation Prompts | informational | 0x:  | `intent:inquiry`, `consecutive_identical_prompts_ge_5`, `mcp_tool_invocation_command` |

---

## `gene_inq_design_doc_preflight_review`

**设计文档实施前缺口分析：阻碍点审查与默认策略提案** / Design Doc Preflight Review — Gap Analysis with Default Strategy Proposals

Category: `informational`

**Signals:**
- `intent:inspection_review`
- `intent:inquiry`
- `has_attached_doc`
- `target:documentation`
- `pre_implementation_review`
- `blockers_mentioned`
- `readiness_check`
- `reference_impl_reading`
- `cn_keywords:jiancha,zudian,buchong,shifoukeyi,kaishi,zhizuo,xiugai`
- `target:audio`
- `engine_api_docs_check`
- `cn_keywords:zudian,youhua,fengxian,yinxiao`
- `code_pattern_reusability_check`
- `bash_project_state_inspection`
- `multi_doc_review`
- `governance_doc_cross_read`
- `multi_dimension_review_question`

**Preconditions:**
- 用户通过 @文件名 或 file:/// 路径附加了一份设计文档（通常是新功能/新游戏的完整策划方案）。
- 用户的提问围绕「能否开始制作」「是否有缺失内容」「是否有阻碍点」等准备就绪性判断，而非要求立即实现。
- 这是某个新系统或新关卡的首次实施评审，代码库中该功能尚未存在。

**Evidence:** 06335c24 (5 prompts, 81 min, 0 code edits): T01 — user attached P3-消消乐.md via @-mention and asked '是否有阻碍点/缺失内容'. Agent: Read doc → Output structured analysis: 8 non-blockers (工程结构、核心玩法、特殊方块等) + 8-row ambiguity table (交换操作方式、特殊方块生成位置、彩虹组合规则、L10目标判定、选关布局、音效、掉落权重、收集计数) each with scope+default strategy + summary 'no hard blockers'. T02 (same message fragmented by UI @-mention parsing): identical response. T03 — user sent terse '调整'; agent reframed all 8 items as interactive numbered table asking user to specify which to adjust. Pattern: design doc + readiness question → structured gap table + defaults → terse ambiguous follow-up → disambiguation table. | 11e7ed86 T01 (12 steps): user attached P2-记忆翻牌.md + AI开发规范.md and asked '如果要开始制作有什么需要修改的地方'. Agent: Read P2-记忆翻牌.md → Read AI开发规范.md → Read 策划案-大厅.md → Read 架构决策记录.md → Glob scripts/**/*.lua → Read demo-memory-flip.lua (existing config) → Read p1-puzzle-land/init.lua + adapter.lua (reference implementation) → respond_to_user with structured modification list. Key variant: agent read P1's init.lua and adapter.lua as reference implementation before critiquing P2 design doc completeness. 11e7ed86 T03 (17 steps): user re-checked '是否有需要补充和完善的地方，是否有阻碍点' after T02 doc revisions. Agent read P2-记忆翻牌.md (revised) + save.lua + pause-menu.lua + game-lifecycle SDK + colors.lua + layout.lua + game-container + screen-transition + adapter.lua → structured readiness report (all infra available, no blockers). Second-pass variant: direct infra code reading (10 files) instead of structured ambiguity table. | 4cfa39d0 T1 (7 steps, 0 edits): user attached 音效系统设计方案.md + 架构决策记录.md via file:// links and asked '如果要根据设计方案制作音效系统，有什么阻碍，有什么需要优化的内容，有什么风险'. Agent: (1) respond_to_user. (2) Read 音效系统设计方案.md. (3) Read 架构决策记录.md. (4) respond_to_user. (5) Task subagent '探索项目代码结构' — examined scripts/shared/, p3-match-3/, p1-puzzle-land/ adapter.lua onEnter/onExit, board-renderer.lua NanoVG functions. (6) Read engine-docs/api/audio.md (engine audio API verification). (7) respond_to_user — structured obstacle/optimization/risk report. Key variant: user attaches BOTH a design doc AND the ADR; agent reads engine API docs (audio.md) in addition to user-provided docs — to verify that the NanoVG/engine audio functions referenced in the design actually exist in the runtime. Prompt asks for three dimensions (阻碍 + 优化点 + 风险) rather than just blockers/gaps — agent produces a three-section structured report. | 4d80bab3 T0 (14 steps, 0 edits): user attached P4-连连看.md + AI开发规范.md via file:// links and asked 「有什么阻碍点，有什么需要补充的内容」. Agent: (1) respond_to_user. (2) Read AI开发规范.md. (3) Read P4-连连看.md. (4) respond_to_user. (5) Task SA1 「探索项目目录结构」 -- mapped existing games (p1/p2/p3), shared/ components, config/ structure, confirmed p4-link-match not yet created. (6) Task SA2 -- searched for reusable pattern drawing code (shapes_easy, artPool, drawCircle/drawStar) across scripts/ to check if P2 shape library could be reused for P4 tile graphics. (7) Read 架构决策记录.md. (8-11) 4x Grep for NanoVG pattern-drawing functions (function.*draw, PATTERNS, nvgBeginPath, nvgCircle). (12) Read p2-memory-flip/view/card-renderer.lua (auditing reusable shape code). (13) respond_to_user -- structured two-dimension report: ①[无阻碍点] (6 items: 路径搜索算法, 关卡数据格式, 状态机设计, 存档格式, HUD/弹窗设计, 游戏注册) + ②[需补充内容] (4 items: 矢量图案绘制实现, 死盘检测策略, 音效设计, P4特有的提示辅助系统). Key variant: user asks two dimensions (阻碍点 + 补充内容) rather than three (阻碍/优化/风险); agent explicitly searches for reusable code patterns (Grep for shape drawing functions + Read P2 card-renderer) to assess whether tile-renderer.lua must be built from scratch. Two Task subagents: SA1 structure exploration, SA2 code pattern search. | 5634a485 T06-T07 (9 steps, 0 edits): user attached TWO docs via file:// links (AI开发规范.md + 策划案-大厅.md) and asked "如果开始制作，是否有阻碍点，是否有需要补充的内容". Agent: (1) Read AI开发规范.md. (2) Read 策划案-大厅.md. (3) Read 架构决策记录.md (proactively, not user-attached). (4) respond_to_user (thinking phase). (5-7) 3x mcp__mkr__Bash: `find /workspace/scripts -type f | sort` (inspect current code structure), `cat .project/project.json` (inspect project config), `cat .project/settings.json` (inspect build settings). (8) Read 文档维护规范.md (proactively, not user-attached). (9) respond_to_user — structured readiness analysis. New variant signals: (a) user attaches TWO docs simultaneously (design spec + dev guidelines) rather than one; (b) agent uses Bash to inspect actual project file structure and config files alongside doc reading — verifying whether code already exists, what entry points are configured, what build targets are set; (c) agent proactively reads ADR and doc-registry even though user did not attach them, treating them as governance context. Bash state inspection is a new sub-step: inspect real project state to verify claims in docs (e.g., "no scripts directory means no code written yet"). Session context: this is a very early session (session 2026-03-17, project still in planning) — the Bash inspection confirmed that the scripts/ directory had only a stub main.lua from T01. | 5c2aeaee T1 (5 steps, 0 edits): user attached THREE docs simultaneously (AI开发规范.md + 策划案-大厅.md + P1-推箱子关卡详细设计.md) via @-mention file:// links and asked '如果要开始制作推箱子，有什么需要补充的地方，有什么需要优化的地方，有什么阻碍点' — three-dimension question (补充内容 + 优化点 + 阻碍点). Agent: (1) Read all 3 attached docs. (2) Task SA1 '探索项目当前结构' — surveyed scripts/ directory to understand what's already been built. (3) Task SA2 '检查架构决策记录' — read ADR to understand existing architectural decisions. Zero code edits — pure readiness analysis. Key variant: user asks THREE dimensions simultaneously (supplement + optimize + blockers) and attaches all 3 relevant docs in one prompt. ADR read is proactive (not user-attached) but necessary to check for conflicts with existing decisions. Prior session context: this is the early-phase session where wzp project just had lobby + color-match scaffold; p1-puzzle-land didn't exist yet. | 6b8bf0cd T0 (9 steps, 0 edits): EARLIEST session in the project — only main.lua stub exists. User attached TWO docs via @-mention (AI开发规范.md + 策划案-大厅.md) and asked '是否可以开始开发，是否有阻碍点'. Agent: (1) respond_to_user. (2) Read AI开发规范.md. (3) Read 策划案-大厅.md. (4) respond_to_user. (5) Glob docs/架构决策记录* (proactively, not user-attached). (6) Glob scripts/**/*.lua (to confirm code state — returns only main.lua stub). (7) Read 架构决策记录.md (proactively). (8) Read main.lua (verify entry point state). (9) respond_to_user — structured readiness analysis. Minimal-project variant: Glob scripts/ confirms almost no code yet (only stub main.lua) → this verifies project is truly fresh → blocker analysis based solely on doc content. Notable: no Task subagents used (9 steps total vs 12-17 in other sessions); no Bash inspection (unlike 5634a485); read sequence is Read both user docs → proactive Glob + Read ADR → Read entry file → respond. This is the simplest variant in the gene. | 9bbd20cc T00 (7 steps, 0 edits): user opened AI开发规范.md (via <document> tag) and attached P2-记忆翻牌.md via @-mention, asking '如果要开始制作，是否有需要补充的内容，是否有阻碍点'. Agent: (1) respond_to_user. (2) Read P2-记忆翻牌.md. (3) Read AI开发规范.md. (4) respond_to_user. (5) Task SA — explored scripts/ game structure, confirmed existing P1 implementation and available infrastructure for P2. (6) Read 架构决策记录.md. (7) respond_to_user — structured gap analysis for P2 development readiness. Variant: two user-attached docs (design spec + dev guidelines) + Task SA for infra exploration + ADR proactive read. Matches 11e7ed86 T01 structure.

---

## `gene_inq_current_impl_audit`

**当前实现状态审计：先探索代码再结构化回答** / Current Implementation Status Audit — Explore-First Structured Answer

Category: `informational`

**Signals:**
- `intent:inquiry`
- `target:ui_layout`
- `target:game_logic`
- `target:build_config`
- `current_state_question`
- `feature_existence_check`
- `no_attached_doc`
- `cn_keywords:shifou,youmeiyou,shixian,xianzai,dangqian,shidou,jizhi,tanchu,chujian,peizhi,kaiguan,shebei`
- `game_mechanic_trigger_question`

**Preconditions:**
- 用户询问某个功能/机制当前是否已实现、实现程度如何（如「现在是否有自适应」「当前 UI 缩放是基于什么」「通关后是否有弹窗」）。
- 提问不附带设计文档，也不要求立即修改代码，纯粹是在了解现状。
- 需要读取代码才能准确回答，仅凭对话历史无法得出结论。

**Evidence:** 08e306a0 T01 (9 steps): user asked 现在UI是否有自适应 (does current UI have adaptive/responsive behavior?). Agent: (1) Glob scripts/**/*.lua to get project structure. (2) Glob .project/settings.json. (3) Read layout.lua (layout constants). (4) Read main.lua (entry). (5) Task subagent SA acabb62 searched for UIScaler, getWidth/getHeight, dpr/DPR, and board-renderer patterns. (6) Agent synthesized results: output structured assessment — ✓ DPR adaptation (all NanoVG uses Mode B), ✓ touch input DPR conversion, ✗ no layout constants scaling (fixed px values like TITLE_FONT_SIZE=38), ✗ no screen-size-aware game board sizing. Pattern: inquiry about current state → Glob project structure → Explore subagent → read key files → structured present/absent breakdown with specific values cited. | 44926b0f T01 (3 steps): user asked '现在在通关第四关后，是否有弹窗提示，可以进入自由模式' (simple yes/no feature existence question). Agent: (1) respond_to_user — declared intent to check code. (2) Task subagent — searched /workspace/scripts/ for level-4 completion logic and popup trigger. (3) respond_to_user — confirmed: yes, popup exists, described the code flow in adventure page that triggers the free-mode unlock dialog. Pattern (simplified variant): yes/no feature trigger question → respond_to_user (will check) → Task search subagent → answer with code path confirmation. No Glob, no direct file reads by main agent — Task subagent handles all discovery. 3 steps vs 9 steps in 08e306a0. Use this simpler variant when the question is binary (exists/not) about a specific named trigger condition rather than asking about system-wide coverage or degree of implementation. | 5dbc4646 T1 (3 steps, 0 edits): user asked 自由模式，记忆翻牌，不同关卡的卡牌数量是怎样的 (how many cards per level in free-mode memory-flip?). Agent: (1) respond_to_user. (2) Task Explore subagent — searched /workspace/scripts/games/p2-memory-flip/ for level data + free mode config. (3) respond_to_user — reported card counts per level range from levels.lua. Simplified variant matching 44926b0f: game-specific factual inquiry + no Glob/direct reads by main agent + 1 Task SA handles all discovery + 3 total steps. | 9bbd20cc T07 (3 steps, 0 edits): user asks '检查 推箱子、翻牌。目前通关进度是否有保存'. Agent: (1) Task SA1 — read P1-推箱子 save-related code in p1-puzzle-land/ (save.lua, clientCloud usage, progress key format). (2) Task SA2 — read P2-记忆翻牌 save-related code in p2-memory-flip/ (save.lua, same). (3) respond_to_user — structured yes/yes answer with specific file citations and save mechanism description for both games. Multi-game parallel-SAs variant: 2 simultaneous Task subagents each auditing one game's save system. No main-agent file reads — all discovery delegated to subagents. Precedes T08-T09 chain (local→cloud save migration) — this turn is the discovery inquiry that sets up the migration request. | d8f96672 T16 (no agent run) + T17 (1 step, respond_to_user): '现在的游戏，是否有做分辨率适配' (T16, no agent run — user immediately re-sent) → '现在的游戏，是否有做分辨率自适应' (T17). Agent processed only T17 with a single respond_to_user step — answered from session context with no file reads. Duplicate-rephrase consecutive inquiry variant: user sends a vague inquiry, then immediately re-sends with a slightly different phrasing before the agent responds. Agent processes only the second turn and answers from existing session knowledge (no Glob, no Task SA, no file reads) because the relevant code was already visible in session context. Contrast with 08e306a0 T01 (9 steps, full Glob+Explore+Read) where resolution adaptation was a fresh inquiry at session start with no prior context. | e948a3d9 T2 (16 steps, 0 edits): user asked '现在配置中，是否有测试设置，当前游戏是否是未成年人的开关' (Does the current config have test settings? Is there an underage/minor mode switch for the game?). Agent: (1) respond_to_user — acknowledged. (2-3) Glob .project/**/*.json and scripts/**/*.lua to survey project structure. (4-6) mcp__mkr__Read settings.json, project.json, and game-config-schema. (7) respond_to_user (interim). (8) Grep for '未成年|minor|child|age|isMinor|kid|青少年|儿童' across workspace. (9) Grep with extended terms including 'test|debug'. (10-15) mcp__mkr__Read play-time-guard.lua, health-advice component, settings component, anti-addiction.lua, settings-save.lua, feature-flags.lua. (16) respond_to_user — full answer. Target variant: build_config. Pattern: yes/no feature-existence question about config/feature-flags → Glob structure survey → Read config files → Grep for feature keywords → Read specific feature-related files → structured factual answer citing specific files and their content.

---

## `gene_inq_new_system_feasibility`

**新系统构想可行性判断：探索架构后结构化分析** / New System Feasibility Check — Architecture-Grounded Structured Analysis

Category: `informational`

**Signals:**
- `intent:inquiry`
- `intent:planning_design`
- `new_system_proposed`
- `no_attached_doc`
- `feasibility_question`
- `architecture_exploration_needed`
- `cn_keywords:shifoukeyi,kexing,shifoupanduan,ruhe,shifou,zengjia,xinxitong`

**Preconditions:**
- 用户提出了一个尚未开始实现的新功能/新系统构想（如「增加主线剧情」「添加角色成长系统」），并询问「是否可行」或「如何实现」，而非直接要求开始实现。
- 提问不附带设计文档，用户描述的是目标效果（「主页显示主角形象」「游戏随主线解锁」），而非实现路径。
- 回答需要基于对现有代码架构（路由、数据存储、模块结构）的理解，仅凭通用知识无法给出有依据的可行性判断。

**Evidence:** 0997e370 T01 (3 steps): user proposed wrapping the 4-game lobby with a main storyline (protagonist character page + progressive game unlocking) and asked '先判定一下这样做，是否可行'. Agent: (1) respond_to_user — declared 'let me check the code first'. (2) Task subagent — Explore /workspace/scripts/: mapped 82 files, identified router (replace/push/pop), game registry (config/games/*.lua), save system (clientCloud). (3) respond_to_user — structured feasibility: '完全可行，且现有架构天然支持' + breakdown: router supports multi-page nav (add new main storyline route), game registry has per-game config (add unlock flag), save system tracks per-game progress (reuse). Pattern: new system idea + '是否可行' → Explore subagent maps architecture → structured feasibility (ready vs. to-add) → recommended next step ('建议先生成设计文档').

---

## `gene_inq_pre_impl_blocker_audit`

**实施前技术阻碍审计：子代理定向调查各依赖项** / Pre-Implementation Blocker Audit — Subagent-Driven Technical Dependency Check

Category: `informational`

**Signals:**
- `intent:inquiry`
- `follows_planning_design_session`
- `no_attached_doc`
- `pre_implementation_readiness`
- `technical_dependency_check`
- `design_doc_already_exists`
- `cn_keywords:shifou,zudian,chongtu,keyi,kaishi,zhizuo,wenti,fengxian`
- `iterative_post_revision_re_audit`

**Preconditions:**
- 当前 session 已完成了规划阶段（设计文档已生成或确认），用户准备进入实现阶段，询问「是否有阻碍」或「有什么需要提前解决的」。
- 提问不附带新文档，而是基于本 session 已有的设计文档或代码库状态发问。
- 判断是否有阻碍需要检查技术依赖项（现有数据格式、API 接口、存档结构、引擎能力等），仅凭设计文档无法得出结论。

**Evidence:** 0997e370 T06 (9 steps): after T01-T05 produced feasibility analysis + design docs + character assets, user asked '如果要开始制作，是否有阻碍'. Agent: (1) Read 策划案-主线系统.md + 总体进度.md + p4 game config. (2) Task SA1 — audit save system for all 4 games (key name, data structure, clientCloud usage). (3) Task SA2 — audit level ID formats across all 4 games. (4) Structured blocker answer: NO blockers for character assets (generated), design docs (ready), architecture (ADR written); PENDING: save system migration (adapt progress tracking to unified main-storyline format), level ID mapping (confirmed format per game). Pattern: post-planning + '是否有阻碍' → read design docs → dispatch separate subagents per technical dependency → structured blocker/no-blocker analysis with recommended start order. | 11e7ed86 T03 (17 steps): after T01 reviewed P2-记忆翻牌.md and T02 applied doc fixes, user asked '是否有需要补充和完善的地方，是否有阻碍点'. Agent: (1) Read P2-记忆翻牌.md (revised v1.2). (2) Read p1-puzzle-land/save.lua (reference save format). (3) Read pause-menu.lua (component exists). (4) Read game-lifecycle/init.lua (SDK lifecycle hooks). (5) Read colors.lua + layout.lua (shared constants). (6) Read game-container/init.lua (container API). (7) Read screen-transition.lua (transition component). (8) Re-read P2-记忆翻牌.md + pause-menu.lua + save.lua + adapter.lua + screen-transition.lua. (9) Structured readiness report: all infrastructure verified available (save format matches, pause menu component reusable, lifecycle SDK covers all events, game container handles transitions) — no blockers. Variant: direct code reading (10 infra files) without subagents, triggered after doc revision rounds.

---

## `gene_inq_full_product_readiness_audit`

**完整游戏产品就绪性审查：全维度读取后分层问题报告** / Full-Game Product Readiness Audit — Multi-Subagent Read-All, Priority-Tiered Issue Report

Category: `informational`

**Signals:**
- `intent:inquiry`
- `open_ended_product_review`
- `no_attached_doc`
- `no_specific_target_artifact`
- `full_game_assessment`
- `launch_readiness_question`
- `cn_keywords:tuichu,wanzheng,wenti,weitian,yousheme,gaiyin,ruhe,chajian,queshi`

**Preconditions:**
- 用户提出开放性问题，评估当前游戏作为完整产品发布时存在的问题（如「如果作为完整游戏推出，有什么问题」「现在的游戏还缺什么」）。
- 问题没有附带自查清单或具体检查维度，也没有指定目标功能或文件——用户期望 AI 自行识别问题维度。
- 这是一次整体产品成熟度评估，而非对某单一功能的现状调查。

**Evidence:** 24a716d1 T00 (10 steps, 0 edits): user asked '当前的游戏，如果作为一个完整游戏推出，有什么问题'. No checklist, no attached doc, no specific target. Agent: (1) respond_to_user — announced comprehensive review. (2) Task SA1 'Explore game project structure'. (3) respond_to_user. (4) Task SA2 'Read project docs and progress' — 6 design/progress docs. (5) Task SA3 'Read key game files for review' — 5 core game files. (6) Task SA4 'Read game adapters and saves' — 9 adapter/save files. (7) respond_to_user. (8) Task SA5 'Read gameplay and UI details' — 9 gameplay/UI files. (9) Task SA6 'Read result popups and HUDs' — 8 result/HUD files. (10) respond_to_user — structured report. Pattern: open-ended 'what issues if released?' → 5 sequential Task SAs covering structure/docs/logic/adapters/UI/results → holistic product-quality analysis → priority-tiered issue list. Distinct from gene_ir_checklist_guided_parallel_audit (requires attached checklist) and gene_inq_current_impl_audit (targets single feature). Agent self-derives dimensions from full-project read.

---

## `gene_ir_dev_progress_next_task`

**开发进度盘点：全项目扫描后推荐下一步任务** / Development Progress Audit — Full Project Scan to Recommend Next Task

Category: `informational`

**Signals:**
- `intent:inspection_review`
- `intent:inquiry`
- `no_attached_doc`
- `compound_audit_plus_recommend`
- `project_completion_gap_query`
- `next_step_question`
- `cn_keywords:jiancha,wendang,jiexiazuoshenme,jierla_zuoshenme,xiayibu`

**Preconditions:**
- 用户发出「检查文档/项目」+「接下来做什么/应该做什么」的复合式指令，同时包含现状核查和下一步任务推荐两个诉求。
- 问题不附带具体设计文档或检查清单，是面向整体项目开发进度的开放性询问。
- 项目尚处于开发中期，存在已完成模块和待实现模块的混合状态（即部分游戏/功能有代码，部分只有配置或完全缺失）。

**Evidence:** 2bc63c91 T00 (10 main steps + 38 subagent steps, 0 edits, 161s): user said '检查文档，接下来应该做什么'. Single-prompt session. Agent: (1) respond_to_user (thinking: check project state first). (2) Bash ls /workspace/scripts + /workspace/assets + cat project.json. (3) Glob scripts/**/*.lua. (4) respond_to_user. (5) Read main.lua. (6) Bash cat project.json + settings.json. (7) Bash: wc -l on all lua files → 33 files, 7386 total lines. (8) respond_to_user (thinking: understand module status). (9) Task subagent (38 steps): Bash ls tree → Read 18 key files (main.lua, router.lua, game-registry, game-container, home/init.lua, game/init.lua, p1 adapter+config, demo-color-match adapter+config, all 4 game configs, game-card, pause-menu, colors, layout, board, gameplay, levels.lua) → respond_to_user with comprehensive architecture summary. (10) respond_to_user — structured status matrix: 平台框架=已完成, p1-puzzle-land=已完成可上线, demo-color-match=已完成开发阶段, demo-number-puzzle=仅有配置无代码, demo-memory-flip=仅有配置无代码, 发布资源=全部缺失. Plus prioritized next-task recommendations. Pattern: compound '检查文档+接下来做什么' → Bash+Glob code map → Task subagent reads 18+ files → implementation status matrix per module (done/config-only/missing) → prioritized next task list. Key insight: agent expanded '检查文档' to full codebase scan because '接下来做什么' requires understanding complete implementation state, not just doc contents.

---

## `gene_ir_checklist_guided_parallel_audit`

**自查指南驱动的多维度并行游戏审计** / Checklist-Guide-Driven Parallel Multi-Dimension Game Audit

Category: `informational`

**Signals:**
- `intent:inspection_review`
- `has_attached_doc`
- `compliance_checklist_attached`
- `pre_launch_review`
- `multi_dimension_check`
- `priority_tiered_output`
- `cn_keywords:jiancha,zizha,zhidao,wenti,xiugai,yingxiang,chali`
- `save_to_new_doc_requested`

**Preconditions:**
- 用户通过 @文件名 或 file:/// 路径附加了一份「自查方向指南」或「检查清单」类文档，要求对游戏项目进行全面检查。
- 用户的提问是「检查游戏是否有需要修改的内容」，而非针对某个具体功能或代码文件，检查范围是整个项目。
- 检查范围横跨多个独立维度（合规政策、文本规范、数值一致性、结构逻辑、音画性能等），无法通过单次读取几个文件完成，需要多专项并行调查。

**Evidence:** 0ea2a577 T01 (20 steps): user attached 游戏自查方向指南.md via @-mention and asked '检查游戏是否有需要修改的内容'. Agent: (1) mcp__mkr__Read — read self-check guide. (2) Glob — project structure. (3) respond_to_user — 'large project, need systematic check'. (4) TodoWrite — 7 audit dimensions: 项目结构和核心配置、合规政策（健康游戏忠告/适龄提示/防沉迷）、文本规范（标点/语言一致性）、数值文案一致性（配置参数 vs 文案描述）、结构逻辑一致性（章节/里程碑/解锁链）、用户体验与交互、音画与性能。 (5) Task SA1 — Explore project structure. (6-10) 5 parallel Task subagents: SA2 checked compliance (health advisory text completeness, age rating, anti-addiction SDK); SA3 checked text norms (ASCII punctuation, English text residuals); SA4 checked numeric/text consistency (config values vs. copy descriptions); SA5 checked story/level structure and unlock chain consistency; SA6 checked BGM/font memory leaks (nvgCreateFont in render loops). (11) respond_to_user — structured P0/P1/P2/P3 report: 5 P0 (mainly anti-addiction formal SDK not integrated, health advisory non-compliant text), 3 P1, 14 P2 (84 ASCII '!' instances, 24 six-dot ellipsis, text inconsistencies), 4 P3. Pattern: attach checklist guide + broad review request → read guide → Glob + Explore subagent for structure → TodoWrite dimensions → 5 parallel specialist subagents → P0/P1/P2/P3 priority-tiered report with location-specific details. | 762afe73 T00 (11 steps): user attached 自查清单.md via @-mention and asked '根据自查清单检查游戏，将检查到的问题，保存为一个新的文档，后续统一修复'. Agent: (1) Read self-check guide. (2) Glob project structure. (3) 8 parallel Task subagents per checklist dimension (compliance, text norms, numeric consistency, level structure, chapter logic, UX, audio/visual, code quality). (4) Write 自查问题报告.md — structured report with P0/P1/P2 sections, numbered issues (1.1–4.4), summary table, and changelog table. Variant: 'save to new doc' suffix → output is a Write of 自查问题报告.md rather than a respond_to_user inline report. The doc becomes the reference artifact for all subsequent fix turns.

---

## `gene_ir_issue_report_sequential_triage`

**自查问题报告逐项可行性审查：逐文件验证后输出修复分层** / Issue Report Sequential Triage — Per-File Verification with Can-Fix/Cannot-Fix Stratification

Category: `informational`

**Signals:**
- `intent:inspection_review`
- `has_attached_doc`
- `target:documentation`
- `existing_issue_report_attached`
- `issue_status_check`
- `feasibility_triage_needed`
- `external_dependency_blocker`
- `cn_keywords:zifanbaogao,jiancha,wenti,keyi_xiugai,buke_xiugai`

**Preconditions:**
- 用户通过 @文件名 或 file:/// 附加了一份已有的自查问题报告（包含已发现问题列表及其当前修复状态，如「自查问题报告.md」），而非设计文档或检查指南。
- 用户询问「有什么需要修改的」或「检查一下需要修改的内容」，期望 AI 识别哪些开放问题可以修复、哪些存在外部依赖阻碍。
- 问题报告中通常混有「需要外部 SDK / 服务端配合」的阻碍性问题（如防沉迷 SDK 接入）和「代码层面可直接修复」的问题（如文字样式、布局调整）。
- 本轮目的是纯分析，不做任何代码修改——输出结果供下一轮「修复 X.X」terse 指令使用。

**Evidence:** 4463c53b T01 (16 steps, 0 edits, 0 builds): user attached 自查问题报告.md via file:// link and asked '检查是否有内容需要修改的'. Agent: (1) respond_to_user — 'let me read the report'. (2) Read 自查问题报告.md (full doc with open issues). (3) respond_to_user — summarized open issues found: 1.3 (防沉迷 SDK), 3.x (profile page), 5.3 (result popup title shadow), 5.4 (adventure type label shadow). (4) TodoWrite — list each open issue as evaluation task. (5) Read outfit-manager.lua (for skin-related issue). (6) Read result-popup.lua (for issue 5.3 popup title). (7) Read adventure/init.lua (for issue 5.4 type label). (8) Read profile/init.lua (for profile-related issues). (9) respond_to_user — 'checking outfit-unlock-popup existence and health advisory pay text'. (10) Glob scripts/shared/components/outfit-unlock-* (verify if component exists). (11) Grep '付费|充值|购买|消费' (check health advisory pay content). (12) Read outfit-unlock-popup.lua. (13) Read health-advisory.lua. (14) respond_to_user — building analysis. (15) TodoWrite (update task statuses). (16) respond_to_user — structured triage: 1.3 [✗ 不可修复] needs external SDK, no workaround; 5.3 [✓ 可修复] add text-shadow in result-popup.lua; 5.4 [✓ 可修复] add text-shadow in adventure/init.lua; others [⚠️/✓]. Zero code edits. Output sets context for T02 '修复5.3,5.4' (3 edits, 1 build). Pattern: attached issue report + '有什么需要修改' → read report → TodoWrite per issue → sequential source file reads → external-dep check via Glob/Grep → structured triage → zero edits.

---

## `gene_ir_fix_proposal_logic_audit`

**修复方案逻辑正确性审查：数据核实 + 修复方向合理性双重验证** / Fix Proposal Logic Audit — Two-Pass Verification of Data Accuracy and Fix Direction

Category: `informational`

**Signals:**
- `intent:inspection_review`
- `has_attached_doc`
- `target:documentation`
- `fix_proposals_in_doc`
- `proposal_correctness_question`
- `code_verification_needed`
- `data_accuracy_plus_logic_check`
- `cn_keywords:xiufufangan,shifou_youwen,fangxiang,fangan_zhengque,jiancha_xiufufangan`

**Preconditions:**
- 用户通过 @文件名 或 file:/// 路径附加了一份包含「问题分析 + 修复方案」的报告文档——文档中既有已识别的问题（问题现象、数据引用），也有具体的修复策略（如「调整参数 X → Y」「增加/删除某元素」）。
- 用户提问聚焦于修复方案本身的正确性（典型措辞：「这些修复方案是否有问题」），而非询问「有什么问题需要修复」。
- 判断修复方案是否正确需要双重验证：① 数据层核实（报告引用的当前值是否与实际代码/配置一致）；② 逻辑层审查（修复方向是否与问题描述的目标一致，是否存在方向反转）。

**Evidence:** 4807e6ed T01 (5 steps): user attached 主线关卡一致性问题报告.md via file:// link and asked '检查这些修复方案是否有问题'. The doc contained both: problem analysis (3 issues with data tables showing timeLimit/targetScore/starScore values across 35 story-mode levels) and specific fix proposals (e.g. 'reduce story-11 timeLimit 80→75s and story-15 80→70s' for Problem 1: 三连平难度曲线). Agent: (1) respond_to_user — will read doc first. (2) Read 主线关卡一致性问题报告.md — understood all 3 issues plus their proposed fixes. (3) respond_to_user — will verify code claims. (4) Task SA — read story-6.lua, story-11.lua, story-15.lua, story-19.lua, story-24.lua, story-32.lua config files; verify all referenced timeLimit/targetScore/starScore/dialogue values against actual code. SA result: all data claims accurate. (5) respond_to_user — structured audit: data all correct; BUT Problem 1 fix direction is REVERSED — problem goal is to ease difficulty curve (score rises but time is flat), proposed fix REDUCES time 80→75→70s (makes it harder), correct fix should INCREASE time or DECREASE score; identified 5 other correction points across 6 total fix proposals (missing combo analysis, level-35 score citation gap, level-18 text should keep '记忆力' not change to '眼力', level-24 suggestion overly verbose, level-32 scope too broad). Pattern: attached fix-proposal report + '修复方案是否有问题' → Read doc → Task SA verifies referenced config values → reasoning audit of each fix's logical direction → 2-layer structured report (data accuracy + direction/logic issues). Session note: 2-prompt session; pattern deemed distinctive because it audits PROPOSED SOLUTIONS rather than identifying problems, requiring code verification combined with logical contradiction detection.

---

## `gene_ir_single_doc_quality_audit`

**单文档质量审查：Glob 探索项目上下文后输出结构化问题报告** / Single-Doc Quality Audit — Glob Project Context Discovery + Structured Issues Report

Category: `informational`

**Signals:**
- `intent:inspection_review`
- `has_attached_doc`
- `single_doc_attached`
- `target:documentation`
- `doc_quality_question`
- `issues_existence_check`
- `no_implementation_question`
- `glob_project_context_discovery`
- `cn_keywords:jiancha,shifou_you_wenti,you_wenti_ma,wenzhang,guifan,wenti`
- `cross_doc_reference_requested`
- `cn_keywords:genju_qita_wendang,jianchayoumei,youhua`

**Preconditions:**
- 用户通过 @文件名 或 file:/// 路径附加了一份文档（规范文档、设计文档、方案文档等），并询问「是否有问题」或「检查一下是否有问题」——聚焦于文档本身的质量，而非对实现可行性的评估。
- 用户的提问不包含「能否开始制作」「是否有阻碍点」等实施就绪性问题——这是对文档质量/完整性/一致性的独立审查。
- 代码库当前状态与该文档的关联可能需要探索（如文档中的目录结构是否存在，规范中引用的文件是否真实存在），但用户没有提供任何额外上下文。
- （变体）用户明确要求「根据其他文档检查」——此时跨文档一致性是主要目标，代理应直接 Read 相关项目文档进行内容比对，而非仅用 Glob 验证路径存在性。

**Evidence:** 5634a485 T02-T03 (10 steps, 0 edits, 0 builds): user attached AI开发规范.md via @-mention and asked "检查AI开发规范.md文档，是否有问题". Agent: (1) mcp__mkr__Read /workspace/docs/AI开发规范.md — full read. (2) respond_to_user (analyzing). (3-8) 5x Glob: `docs/**/*.md` (discover all docs), `**/*AI开发规范*` (check if multiple copies exist), `scripts/config/**/*.lua` (verify config directory path referenced in doc), `scripts/tests/**/*` (verify test directory referenced in doc), `docs/文档维护规范.md` (check doc formatting standards). (9) respond_to_user — structured analysis report. (10) respond_to_user — detailed findings (doc references paths that don't yet exist: scripts/config/, scripts/tests/; formatting is consistent with 文档维护规范.md conventions; found 5 specific improvable items in sections 2, 4, 6, 7). Zero edits. Output is read-only analysis. Key pattern: user attaches ONE doc + asks "是否有问题" (not "能否开始制作") → Read full doc → Glob to verify all path references exist in project → Read doc registry → structured report of issues found. Distinct from gene_inq_design_doc_preflight_review: this gene audits doc QUALITY (inconsistencies, missing sections, path references) rather than implementation READINESS (blockers, gaps before coding starts). Session context: this is T02 (second prompt in session, right after empty project scaffold was built in T01). | d02df5f6 T00 (15 steps, 7 reads, 2 Bash, 0 edits): user @-attached P3-消消乐.md and asked '检查[@P3-消消乐.md]策划案，根据其他文档检查是否有需要修改和优化的内容'. The explicit '根据其他文档' directive caused agent to Read multiple other project docs (other design documents in the workspace) rather than using Glob for path discovery. Agent produced a structured review report listing issues and optimization opportunities found by cross-referencing the target doc against other project documents. Zero edits. Pure read-and-report. Variant: cross-doc referencing requested → Read-based strategy, not Glob-based.

---

## `gene_inq_open_ended_optimization_audit`

**开放式优化机会审查：多子代理代码扫描 → 优先级分组清单 → 可选文档写入** / Open-Ended Optimization Audit — Multi-Subagent Code Scan to Priority-Grouped Checklist

Category: `informational`

**Signals:**
- `intent:inquiry`
- `optimization_opportunities_requested`
- `open_ended_product_optimization`
- `no_attached_doc`
- `multi_subagent_explore`
- `structured_prioritized_output`
- `cn_keywords:youhua,gaijin,keyi`
- `doc_write_followup`

**Preconditions:**
- 用户发送开放式提问「游戏有什么可以优化的地方」或类似语句，未附加任何文档，也未指定具体系统或范围。
- Agent 可访问项目完整代码库（/workspace/scripts/），项目已有一定实现量（非从零开始）。
- 下一回合用户有可能发送「记录在文档上」「保存下来」，将本回合的优化建议写入文件。

**Evidence:** a09c411b T00 (38 steps, 0 edits): user prompt '游戏有什么可以优化的地方' — no doc attached, no scope specified. Agent: (1) respond_to_user — announced comprehensive review. (2) Task Explore SA1 — scanned scripts/shared/components/ and scripts/pages/ for performance issues (NanoVG calls in render loops, image handle patterns, animation timers, event subscription/unsubscription). (3) Task Explore SA2 — scanned all game modules (p1/p2/p3/p4) for stability and code quality issues (hardcoded constants, duplicate drawing code, missing nil guards, incomplete destroy() cleanup). (4) respond_to_user — structured output: 5 priority levels, 16 optimization items total: 优先级1=性能(3项: render-loop NanoVG text caching, fox-mascot re-render guard, animation timer cleanup), 优先级2=稳定性(4项: event unsubscription, nil guards, destroy lifecycle), 优先级3=代码质量(4项: shared constants extraction, duplicate logic), 优先级4=用户体验(3项: UX polish), 优先级5=测试(2项: coverage gaps). Each item included file name, problem description, fix direction, expected benefit. Output was Markdown checklist format. T01 (5 steps, 1 write): user sent '将可优化的内容记录在文档上保存下来'. Agent: (1) respond_to_user. (2) Write /workspace/docs/optimization-notes.md — full structured document with all 5 priority groups, 16 items as ☐ checklist, each with file path, problem, fix direction, expected benefit. (3) respond_to_user. Zero edits to code. Pattern: open-ended inquiry → multi-SA scan → structured prioritized output → immediate doc write on user request. Downstream: T02/T04/T05 consumed this doc sequentially by priority level (see gene_fm_optimization_backlog_doc_sequential_consume). | f14c92eb T00 (17 steps, 0 edits): user prompt '检查目前的游戏，有什么可以优化或丰富的内容' (inspection_review, no doc, no scope). Agent: Task(1) + mcp__mkr__Read(12) + respond_to_user(4) — dispatched subagent to scan codebase, produced structured multi-category checklist. T01 (3 steps): user '将这些内容保存为文档，后续我视情况进行修改' → mcp__mkr__Write(1) wrote docs/optimization-suggestions.md. Pattern: open-ended audit → immediate doc write.

---

## `gene_inq_mcp_tool_poll_loop`

**MCP工具轮询循环：连续相同工具调用指令** / MCP Tool Polling Loop: Consecutive Identical Tool Invocation Prompts

Category: `informational`

**Signals:**
- `intent:inquiry`
- `consecutive_identical_prompts_ge_5`
- `mcp_tool_invocation_command`
- `explicit_anti_cache_instruction`
- `no_attached_doc`
- `tool_name_specified_in_prompt`

**Preconditions:**
- User prompt contains an explicit instruction to call a named MCP/API tool by name
- Prompt includes anti-caching instruction ('重新调用', 'must re-call', 'no cached results', '不要依赖历史记录')
- Same prompt has been sent 2+ consecutive times
- No other task context beyond the tool invocation command

**Evidence:** 

---
