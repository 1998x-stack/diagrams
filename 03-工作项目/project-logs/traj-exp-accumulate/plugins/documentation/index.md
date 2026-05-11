# documentation — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_doc_checkpoint_cadence` | Periodic Documentation Checkpoint — Phase Boundary Marker | session_rhythm | 2x: 9dc56f96, 374e4eb7 | `intent:documentation`, `target:documentation`, `cn_update_docs_keyword` |

---

## `gene_doc_checkpoint_cadence`

**阶段性文档检查点更新** / Periodic Documentation Checkpoint — Phase Boundary Marker

Category: `session_rhythm`

**Signals:**
- `intent:documentation`
- `target:documentation`
- `cn_update_docs_keyword`
- `periodic_in_session`
- `phase_boundary_marker`

**Preconditions:**
- 用户在一个session中周期性地发出'更新文档'指令，通常间隔8-12轮。
- 文档更新出现在功能开发阶段的边界（完成一批修改后、开始新主题前）。
- 用户将文档更新视为'检查点'，标记一组工作的完成。

**Evidence:** 9dc56f96: 4x '更新文档' every ~10 turns. 374e4eb7: 3x '更新文档' at T08/T12/T27 every ~8 turns. Pattern confirmed: users consistently checkpoint docs at phase boundaries. Intervals range 6-12 turns.

---
