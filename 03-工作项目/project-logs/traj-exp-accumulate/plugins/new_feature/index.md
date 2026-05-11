# new_feature — Gene Index

**Gene count:** 4

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_nf_level_data_batch_injection` | Batch Level Data Injection — External Design Import | workflow | 1x: 9dc56f96 | `intent:new_feature`, `target:game_logic`, `structured_data_in_prompt` |
| 2 | `gene_nf_settings_feature_cascade` | Settings Feature Cascade — UI → Logic → Persistence Build | workflow | 1x: 9dc56f96 | `intent:new_feature`, `target:ui_layout|game_logic`, `settings_ui_keywords` |
| 3 | `gene_nf_audio_event_first_binding` | First-Time Audio Event Binding — SFX on Game Event | workflow | 1x: 9dc56f96 | `intent:new_feature`, `target:audio`, `sfx_name_plus_game_event` |
| 4 | `gene_nf_character_system_with_progression_unlock` | Character Customization System — Outfit + Progression Unlock + Content | workflow | 1x: 374e4eb7 | `intent:new_feature`, `target:game_logic`, `costume_outfit_keywords` |

---

## `gene_nf_level_data_batch_injection`

**批量关卡数据注入（外部设计导入）** / Batch Level Data Injection — External Design Import

Category: `workflow`

**Signals:**
- `intent:new_feature`
- `target:game_logic`
- `structured_data_in_prompt`
- `level_config_lua_table`
- `consecutive_level_injection`
- `cn_level_apply_keywords`

**Preconditions:**
- 用户在prompt中直接粘贴完整的关卡配置数据（Lua table格式），包含地图尺寸、玩家位置、墙壁、箱子、目标等。
- 连续多次(2+)提交同类型的关卡数据，属于批量关卡导入场景。
- 每次数据注入的步骤数极少(5-6步)：Read→Edit→Build，效率极高。

**Evidence:** 4 consecutive turns pasting Sokoban level configs (levels 9-12), each exactly 5-6 steps (Read→Edit→Build), zero errors

---

## `gene_nf_settings_feature_cascade`

**设置功能级联构建（UI→逻辑→持久化）** / Settings Feature Cascade — UI → Logic → Persistence Build

Category: `workflow`

**Signals:**
- `intent:new_feature`
- `target:ui_layout|game_logic`
- `settings_ui_keywords`
- `volume_control_keywords`
- `feature_then_polish_chain`
- `cn_settings_cascade`

**Preconditions:**
- 用户请求添加一个包含UI+逻辑+持久化的完整功能（如设置页面）。
- 初始请求后会紧跟多轮迭代：bug修复→UX打磨→数据持久化→再验证。
- 属于单session内从0到完成的完整功能构建。

**Evidence:** 5-turn cascade: BGM setup → settings UI (42 steps) → bug fix slider (30 steps) → UX polish (5 steps) → persistence (24 steps)

---

## `gene_nf_audio_event_first_binding`

**首次音效事件绑定** / First-Time Audio Event Binding — SFX on Game Event

Category: `workflow`

**Signals:**
- `intent:new_feature`
- `target:audio`
- `sfx_name_plus_game_event`
- `first_time_audio_for_event`
- `cn_play_sound_on_event`

**Preconditions:**
- 用户首次为某个游戏事件（关卡失败、关卡成功、角色移动、翻牌点击）添加音效。
- prompt中同时指定了音效名称和触发事件，信息完整。
- 需要在事件处理函数中插入新的音效调用代码。

**Evidence:** Multiple first-time SFX bindings: bounce_boing on fail, success_fanfare on win, level_complete with 0.5s delay, bloop_bounce on move/flip, BGM loop

---

## `gene_nf_character_system_with_progression_unlock`

**角色自定义系统（换装+进度解锁+内容关联）** / Character Customization System — Outfit + Progression Unlock + Content

Category: `workflow`

**Signals:**
- `intent:new_feature`
- `target:game_logic`
- `costume_outfit_keywords`
- `unlock_condition_keywords`
- `content_generation_in_feature`
- `cn_character_customization`

**Preconditions:**
- 用户要求构建角色自定义系统（换装/皮肤/角色变体），包含多个子系统。
- 通常包含：UI入口、预览展示、解锁条件（关卡进度/购买）、状态持久化。
- 可能伴随内容生成需求：每套装扮对应不同的台词/对话/行为。

**Evidence:** Full costume system build across 13 turns: design doc → implement → delete outfit + fix white square → adjust layout → adjust height x2 → doc checkpoint → add outfit-specific compliments → add portrait chat → unlock conditions. 280+ steps total.

---
