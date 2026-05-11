# informational — Gene Index

**Gene count:** 2

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_inq_ui_status_probe` | UI Status Probe — Lightweight Inquiry with Read-Respond Pattern | informational | 2x: 08e306a0, 9df66fd4 | `intent:inquiry`, `target:ui_layout`, `read_respond_only` |
| 2 | `gene_ir_narrative_game_data_consistency_check` | Narrative-Game Data Consistency Check — Lightweight Cross-Reference Inspection | informational | 1x: 6b8566ea | `intent:inspection_review`, `target:narrative`, `data_consistency_check` |

---

## `gene_inq_ui_status_probe`

**UI状态轻量查询模式** / UI Status Probe — Lightweight Inquiry with Read-Respond Pattern

Category: `informational`

**Signals:**
- `intent:inquiry`
- `target:ui_layout`
- `read_respond_only`
- `no_edit_no_build`
- `status_question_pattern`
- `lightweight_exploration`

**Preconditions:**
- 用户以疑问句形式询问当前UI/功能的现状（如'现在UI是否有自适应'、'缩放基于宽度还是高度'）。
- 用户未要求修改、未报告bug、未要求新增功能。
- Agent的响应模式为：读取1-2个相关文件→respond_to_user回答，不执行任何编辑或build。
- 如果此前已有相关探索上下文（如刚完成大规模UI修改），Agent可直接回答而无需读取文件。

**Evidence:** T0: '现在UI是否有自适应'→9步(2 Glob+2 Read+4 respond)，读取layout.lua和main.lua后回答，0 edits 0 builds。T3: '现在UI缩放是基于屏幕宽度还是高度'→仅1步respond_to_user，因T2刚完成大规模UI自适应修改，Agent直接基于已有上下文回答，无需读取文件。两个turn均为纯信息查询模式，但T3展示了'利用近期上下文直接回答'的优化路径。 9df66fd4强化了此模式并展示了'inquiry→直接回答'变体：T00: '主线模式，按钮的大小是根据宽还是高计算的'→3步(2 respond+1 Task)。纯信息查询→Task探索→respond回答。0 edits 0 builds。T23: '记忆翻牌，25关的牌展示时间是多少'→11步(2 respond+8 Grep+1 Read)。纯参数查询→Grep搜索配置→Read确认→respond回答。0 edits 0 builds。T25: '现在换装是否有保存'→5步(2 respond+1 Grep+1 Read+1 build)。纯状态查询→Grep+Read确认→respond回答。1 build可能是意外触发。3个inquiry turn均为纯信息查询模式，与08e306a0的'UI自适应查询'模式一致。

---

## `gene_ir_narrative_game_data_consistency_check`

**叙事与游戏数据一致性检查** / Narrative-Game Data Consistency Check — Lightweight Cross-Reference Inspection

Category: `informational`

**Signals:**
- `intent:inspection_review`
- `target:narrative`
- `data_consistency_check`
- `narrative_vs_game_data_comparison`
- `grep_only_inspection`
- `read_respond_only`
- `no_edit_no_build`

**Preconditions:**
- 用户要求检查剧情描述/文案中的数值或元素描述是否与游戏内实际数据一致。
- 这不是代码审查或bug修复，而是内容一致性检查。
- 典型场景：剧情中提到'3个石头'，需要确认游戏内该关卡确实配置了3个石头。
- 用户明确说明'如果没有，则不用处理'——这是一个轻量级检查，不要求主动修复。
- Agent的响应模式为：Grep搜索相关文案→respond回答，不执行任何编辑或build。

**Evidence:** T17: '检查剧情描述，是否有出现石头和冰块数量，如果有，确保和游戏内数量一致，如果没有，则不用处理'→2步(1 Grep+1 respond)。Grep搜索剧情描述中石头/冰块数量提及→respond回答检查结果。0 edits 0 builds。典型的'Grep搜索→对比报告'轻量检查模式。与gene_ir_minimal_inspection_rhythm(Read+respond纯文档审查)不同——本模式是跨文档/数据文件的一致性对比检查(narrative vs game data)，需要Grep搜索两个数据源进行对比。与gene_ir_inspection_to_investigation_cascade不同——后者是inspection后紧跟bug调查，本模式是独立的轻量一致性检查，不触发后续修复。

---
