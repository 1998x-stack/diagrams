# planning_design — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_pd_design_doc_then_implement` | Design Document Then Implement — Plan-Approve-Execute Pattern | workflow | 1x: 374e4eb7 | `intent:planning_design`, `target:game_logic`, `design_doc_first_keyword` |

---

## `gene_pd_design_doc_then_implement`

**先设计文档后实现（规划-确认-执行）** / Design Document Then Implement — Plan-Approve-Execute Pattern

Category: `workflow`

**Signals:**
- `intent:planning_design`
- `target:game_logic`
- `design_doc_first_keyword`
- `cn_check_then_start_pattern`
- `followed_by_start_command`

**Preconditions:**
- 用户明确要求先写设计文档，等检查无误后再开始制作。
- 请求中包含系统性的功能描述（入口位置、UI结构、数据流、扩展性考虑）。
- 用户对质量有明确预期：先规划再实现，不希望AI直接动手写代码。

**Evidence:** T01: 24 steps, 0 edits, 0 builds — pure design doc output (EnterPlanMode→ExitPlanMode). T02: '开始制作' triggers 56 steps, 11 edits, 1 build. Clear 2-phase pattern: design→approve→implement.

---
