# inquiry — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_inq_feature_status_query` | Feature Status Query — Information-Only Response | informational | 2x: 9dc56f96, 374e4eb7 | `intent:inquiry`, `target:visual_style|game_logic|ui_layout`, `question_format` |

---

## `gene_inq_feature_status_query`

**功能状态查询（纯信息回答）** / Feature Status Query — Information-Only Response

Category: `informational`

**Signals:**
- `intent:inquiry`
- `target:visual_style|game_logic|ui_layout`
- `question_format`
- `cn_what_effect_keywords`
- `cn_what_value_keywords`
- `no_code_change_expected`
- `often_precedes_modification`

**Preconditions:**
- 用户以疑问句形式询问某个功能的当前状态、实现方式或效果描述。
- 不要求代码修改，只需信息回答。
- 可能出现在用户准备决定下一步操作之前（信息收集阶段）。

**Evidence:** 9dc56f96 T48: '转场动画是什么效果' (3 steps). 374e4eb7 T05: '预览区高度是多少...页面排版是怎样的' (3 steps). Pattern: inquiry often precedes a feature_modification (T05→T06 set height to 180). Users gather info before deciding parameter values.

---
