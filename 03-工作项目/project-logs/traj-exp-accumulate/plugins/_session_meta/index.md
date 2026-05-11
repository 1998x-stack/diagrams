# _session_meta — Gene Index

**Gene count:** 2

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_meta_children_game_session_rhythm` | Children's Game Collection Long Session Rhythm Pattern | session_rhythm | 1x: 9dc56f96 | `session_level_pattern`, `children_game_project`, `multi_game_portfolio` |
| 2 | `gene_meta_intent_distribution_fm_dominant` | Feature Modification Dominant — Product Polish Phase | session_rhythm | 1x: 9dc56f96 | `session_level_pattern`, `feature_modification_dominant`, `fm_ratio_gt_40pct` |

---

## `gene_meta_children_game_session_rhythm`

**儿童游戏集合长session节奏模式** / Children's Game Collection Long Session Rhythm Pattern

Category: `session_rhythm`

**Signals:**
- `session_level_pattern`
- `children_game_project`
- `multi_game_portfolio`
- `7h_plus_session`
- `50_plus_prompts`

**Preconditions:**
- 用户正在开发儿童益智游戏集合（多游戏合集项目），session时长超过5小时，prompt数超过40。
- 项目包含多个子游戏（如推箱子、消消乐、连连看、记忆翻牌），需要跨游戏的统一功能应用。
- 长session中呈现明显的阶段性节奏：UI打磨→游戏参数→音效→设置→关卡。

**Evidence:** 53 prompts / 7.6h session. Clear phase rhythm: visual polish (T01-T13) → game params (T14-T20) → audio pipeline (T21-T33) → settings (T34-T39) → level injection (T41-T45) → final tweaks (T46-T53). Doc checkpoints at T14/T34/T40/T50.

---

## `gene_meta_intent_distribution_fm_dominant`

**Feature Modification主导的功能打磨期** / Feature Modification Dominant — Product Polish Phase

Category: `session_rhythm`

**Signals:**
- `session_level_pattern`
- `feature_modification_dominant`
- `fm_ratio_gt_40pct`
- `low_bug_rate`
- `low_correction_rate`

**Preconditions:**
- session中 feature_modification 占比超过40%，且 bug_report + ai_output_correction 总计不超过10%。
- 表明项目处于功能打磨期（产品基本可用，用户在精调参数和扩展应用范围）。
- Agent工作质量较高（错误步骤为0，用户纠正仅2次），用户信任度高。

**Evidence:** Intent distribution: feature_modification 24/53 (45%), new_feature 15/53 (28%), bug_report 3/53 (6%), ai_output_correction 0 (but 2 is_correction=true). 0 error steps in 953 total steps.

---
