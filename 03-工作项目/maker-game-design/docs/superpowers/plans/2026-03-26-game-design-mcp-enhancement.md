# Game-Design Skill MCP Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the game-design skill from pure consulting to "design-as-execution" by weaving MCP tool awareness into SKILL.md, creating a new mcp-toolkit.md reference, and slimming ai-era-design.md.

**Architecture:** Three-file change set — organic edits to SKILL.md (tool hints in existing sections), a new heavy-duty mcp-toolkit.md (tool catalog + 10 workflow templates), and targeted deletions in ai-era-design.md with cross-references to the new file.

**Tech Stack:** Markdown documentation files. No code changes.

**Spec:** `docs/superpowers/specs/2026-03-26-game-design-mcp-enhancement-design.md`

---

### Task 1: Enhance SKILL.md Core Workflow

**Files:**
- Modify: `game-design/SKILL.md:22-29` (core workflow code block)

- [ ] **Step 1: Replace the core workflow code block**

In `game-design/SKILL.md`, replace lines 22-29 (the code block content) with:

```
1. 明确体验目标      → 这个游戏/功能要让玩家感受到什么？
   🔧 可用 generate_image 生成概念图辅助沟通体验愿景
2. 理解目标玩家      → 他们是谁？动机是什么？
   🔧 可用 WebSearch 快速调研竞品和目标市场
3. 设计核心循环      → 重复单元是否自带乐趣？
   🔧 可用 search_3d_resource 找原型资产 → build 快速构建可玩原型
4. 构建反馈系统      → 行为→响应链是否清晰、即时、有意义？
   🔧 可用 batch_sound_effects 批量生成反馈音效，generate_image 生成特效贴图
5. 校验整体节奏      → 张弛是否有度？心流通道是否维持？
   🔧 可用 text_to_music 生成适配节奏的背景音乐原型
6. 审视商业逻辑      → 付费/留存设计是否尊重玩家？
   🔧 可用 generate_game_material 生成商店素材 → publish_to_taptap 发布测试
```

The old_string for the Edit tool is the 6-line block inside the ``` fences (lines 23-28). The new_string adds a 🔧 line after each step.

- [ ] **Step 2: Verify the edit**

Read `game-design/SKILL.md` lines 18-35 and confirm the 6 workflow steps each have a 🔧 tool hint line beneath them, all inside the code block.

---

### Task 2: Enhance SKILL.md Reference Table, Judgment Framework, Output Spec, Intuition, and Directory

**Files:**
- Modify: `game-design/SKILL.md:37-48` (reference table)
- Modify: `game-design/SKILL.md:56-61` (judgment framework)
- Modify: `game-design/SKILL.md:101-109` (output spec)
- Modify: `game-design/SKILL.md:127` (intuition item 6)
- Modify: `game-design/SKILL.md:133-147` (directory tree)

- [ ] **Step 1: Add new row to reference file table**

In `game-design/SKILL.md`, find the line:

```
| 撰写GDD、立项文档、提案 | `references/gdd-template.md` |
```

After it, insert:

```
| 工具编排、资产生产、原型构建、发布上线 | `references/mcp-toolkit.md` |
```

- [ ] **Step 2: Add fourth question to judgment framework**

Find:

```
三问都通过，才值得进入详细设计。
```

Replace with:

```
4. **可执行性**：现有 MCP 工具能否在1小时内生成该功能的原型？如果能，直接原型验证比纸上推演更有效。

四问都通过，才值得进入详细设计。
```

- [ ] **Step 3: Enhance output spec — design category**

Find:

```
**设计类**（新功能、新系统）：
- 先陈述体验目标
- 再描述机制实现
- 配合数据/数值示例
- 列出风险与边界条件
```

Replace with:

```
**设计类**（新功能、新系统）：
- 先陈述体验目标
- 再描述机制实现
- 配合数据/数值示例
- 列出风险与边界条件
- 列出实现所需的工具编排步骤（参考 `references/mcp-toolkit.md` 工作流模板）
- 标注哪些资产可以 AI 生成 vs 必须手工制作
```

- [ ] **Step 4: Enhance output spec — document category**

Find:

```
**文档类**（GDD、提案）：
- 参考 `references/gdd-template.md`
- 结构清晰，每部分都能独立阅读
```

Replace with:

```
**文档类**（GDD、提案）：
- 参考 `references/gdd-template.md`
- 结构清晰，每部分都能独立阅读
- GDD 的「技术实现」章节应引用可用 MCP 工具（参考 `references/mcp-toolkit.md`）
```

- [ ] **Step 5: Update intuition item 6**

Find:

```
6. **原型优于文档**：用最粗糙的方式验证核心体验，再花资源精细化。
```

Replace with:

```
6. **原型优于文档**：用 MCP 工具链在1小时内构建最粗糙的可玩原型，再花资源精细化。能 build 出来测试的，就不要停留在文档阶段。
```

- [ ] **Step 6: Update reference directory tree**

Find:

```
│   ├── ai-era-design.md              ← AI时代的游戏设计：工具/UGC/生成内容
│   └── gdd-template.md               ← GDD标准模板与撰写指南
```

Replace with:

```
│   ├── ai-era-design.md              ← AI时代的游戏设计：工具/UGC/生成内容
│   ├── mcp-toolkit.md               ← MCP工具实战手册：工具速查/工作流模板/编排原则
│   └── gdd-template.md               ← GDD标准模板与撰写指南
```

- [ ] **Step 7: Verify all SKILL.md edits**

Read the entire `game-design/SKILL.md` and verify:
- Reference table has 9 rows (8 original + 1 new)
- Judgment framework has 4 questions + "四问都通过"
- Design output spec has 6 bullet points
- Document output spec has 3 bullet points
- Intuition item 6 mentions "MCP 工具链"
- Directory tree includes mcp-toolkit.md

---

### Task 3: Create mcp-toolkit.md — Header, Tool Catalog, and Visual/Audio Sections

**Files:**
- Create: `game-design/references/mcp-toolkit.md`

- [ ] **Step 1: Write the complete mcp-toolkit.md file**

Create `game-design/references/mcp-toolkit.md` with the following full content:

````markdown
# MCP 工具实战手册

> 本手册是游戏策划的工具执行层。当你完成设计思考后，用这里的工具和工作流将设计变为可玩原型。

---

## 1. 工具总览速查表

| 分类 | 工具 | 一句话用途 | 典型场景 |
|------|------|----------|---------|
| **视觉** | `generate_image` | AI 生成图片 | 概念图、立绘、图标、贴图、UI 素材 |
| **视觉** | `batch_generate_images` | 批量并行生成多张图片 | 一次性生成整套 UI 图标 |
| **视觉** | `edit_image` | AI 编辑已有图片 | 修改颜色、背景、局部细节 |
| **视觉** | `search_3d_resource` | 搜索 3D 模型资源库 | 找角色模型、场景道具、建筑 |
| **音频** | `text_to_music` | AI 生成背景音乐/歌曲 | BGM、主题曲、战斗音乐 |
| **音频** | `query_music_task` | 查询音乐生成状态 | 等待 BGM 生成完成 |
| **音频** | `text_to_sound_effect` | AI 生成音效 | 爆炸、脚步、UI 点击音 |
| **音频** | `batch_sound_effects` | 批量生成多个音效 | 一次性生成战斗音效包 |
| **音频** | `text_to_dialogue` | AI 生成角色语音对白 | NPC 台词、剧情语音 |
| **音频** | `audition_voices_for_character` | 为角色试听 AI 声音 | 选择最适合角色性格的声线 |
| **音频** | `confirm_character_voice` | 确认角色声音选择 | 锁定声音（消耗 Voice Slot） |
| **视频** | `create_video_task` | AI 生成视频 | 过场动画、宣传片 |
| **视频** | `query_video_task` | 查询视频生成状态 | 等待视频生成完成 |
| **构建** | `build` | 构建项目 | 每次改代码后必须调用 |
| **构建** | `generate_test_qrcode` | 生成测试二维码 | 手机扫码测试 |
| **构建** | `add_test_whitelist` | 添加测试白名单 | 邀请测试用户 |
| **构建** | `get_debug_feedbacks` | 获取调试反馈 | 收集测试玩家的 bug 报告 |
| **构建** | `lua_lsp_client` | Lua 语言服务器 | 类型检查、代码补全、跳转定义 |
| **发布** | `generate_game_material` | 生成发布素材 | 应用图标、商店截图、宣传图 |
| **发布** | `upload_game_material` | 上传素材到 OSS | 图标/截图/宣传图上传 |
| **发布** | `publish_to_taptap` | 发布到 TapTap | 正式上架 |
| **发布** | `list_tap_developers` | 查询开发者列表 | 确认发布账号 |
| **发布** | `get_ad_config` | 同步广告配置 | 接入广告变现 |
| **发布** | `bind_game_jam` | 绑定 GameJam 活动 | 参加比赛 |
| **发布** | `i18n_extract` | 国际化文本提取 | 多语言翻译准备 |

---

## 2. 工具分类详解

### 2.1 视觉资产工具

#### generate_image — AI 生成图片

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 中文图片描述（最大 50KB） |
| `name` | string | ✅ | 文件名（不含扩展名） |
| `target_size` | string | ✅ | 最终尺寸，如 `"256x256"` |
| `aspect_ratio` | enum | | `1:1` / `2:3` / `3:2` / `3:4` / `4:3` / `9:16` / `16:9` / `21:9` / `5:4` / `4:5` |
| `transparent` | boolean | | 是否透明背景（图标常用） |
| `reference_images` | string[] | | 参考图路径列表（最多 14 张） |
| `seed` | number | | 随机种子（可复现结果） |
| `thinking_level` | enum | | `"minimal"` / `"high"` |
| `resolution` | enum | | `"0.5K"` / `"1K"` / `"2K"` / `"4K"` |

**最佳实践**：
- prompt 用中文，描述越具体越好。包含风格、色调、构图、氛围
- 生成图标时设 `transparent: true`，后续合成不需要抠图
- 用 `seed` 固定随机种子，迭代时只改 prompt，保证对比有意义
- 先用 `resolution: "1K"` 快速验证，满意后用 `"2K"` 或 `"4K"` 出终稿
- 用 `reference_images` 传入风格参考图，保持美术风格一致性

**常见陷阱**：
- prompt 太短或太抽象（如"一个角色"）→ 结果不可控。至少写 50 字描述
- 忘记设 `target_size` 导致尺寸不匹配游戏资源规格
- 一次改太多参数导致无法判断哪个改动有效 → 每次只改一个变量

#### batch_generate_images — 批量生成

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `images` | array | ✅ | 图片请求数组，每项参数同 `generate_image` |

**策划视角**：当需要一套风格统一的图标（如 10 个技能图标、8 个道具图标），用同一个 reference_image + 不同 prompt 批量生成，比逐个调用快得多。

#### edit_image — 编辑已有图片

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | string | ✅ | 原图路径 |
| `prompt` | string | ✅ | 编辑指令，如 `"把背景改成蓝色"` |
| `name` | string | ✅ | 输出文件名 |
| `target_size` | string | ✅ | 最终尺寸 |

**策划视角**：已有基本满意的图，只需微调（换配色、改背景、加装饰）时用这个。比重新生成更稳定。

#### search_3d_resource — 搜索 3D 模型

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 自然语言描述，如 `"白衣剑客"`、`"medieval knight"` |

**最佳实践**：
- 中英文关键词都可以，英文搜索范围更广
- 先用宽泛关键词（如 `"knight"`），再用具体关键词（如 `"knight with shield medieval"` ）缩小范围
- 返回结果包含模型名称、描述、下载 URL，选中后即可集成到项目

---

### 2.2 音频资产工具

#### text_to_music — 生成背景音乐

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 音乐描述或歌词 |
| `customMode` | boolean | | 自定义模式（需要同时设 style 和 title） |
| `style` | string | | 音乐风格（自定义模式必填） |
| `title` | string | | 曲名（自定义模式必填） |
| `instrumental` | boolean | | `true` = 纯器乐无人声 |
| `model` | enum | | `"V3_5"` / `"V4"` / `"V4_5"` / `"V4_5PLUS"` / `"V5"` |
| `negativeTags` | string | | 需避免的风格 |
| `vocalGender` | string | | `"m"` 男声 / `"f"` 女声 |

**最佳实践**：
- 游戏 BGM 通常设 `instrumental: true`（纯器乐）
- prompt 描述氛围而非技术参数：`"神秘森林探索，木管乐器为主，缓慢节奏，偶尔出现精灵铃铛声"` 比 `"C大调4/4拍"` 效果好
- 用 `negativeTags` 排除不想要的风格：`"heavy metal, rap, electronic"`
- model 选 `"V4_5PLUS"` 或 `"V5"` 获得最佳质量
- 返回后自动轮询直到完成，无需手动调用 `query_music_task`

**常见陷阱**：
- 忘记设 `instrumental: true`，BGM 里出现了人声歌唱
- prompt 太短（如"战斗音乐"）→ 结果太泛。描述具体的情绪和乐器

#### text_to_sound_effect — 生成音效

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | ✅ | **英文**音效描述 |
| `duration_seconds` | number | | 时长 0.5-30 秒 |
| `prompt_influence` | number | | 提示词影响度 0-1（默认 0.3） |
| `loop` | boolean | | 是否循环音效 |
| `output_name` | string | | 输出文件名 |

**最佳实践**：
- **描述必须用英文**，这是最常见的错误
- UI 音效用短时长（0.5-1秒）：`"soft click"`, `"gentle pop"`, `"whoosh"`
- 环境音设 `loop: true`：`"forest ambience with birds and wind"`
- 战斗音效用中等时长（1-3秒）：`"sword clash with metallic ring"`
- `prompt_influence` 越高越忠于描述，越低越自然随机

#### batch_sound_effects — 批量生成音效

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sounds` | array | ✅ | 音效数组，每项含 `name`(✅), `text`(✅), `duration`, `loop` |

**策划视角**：一次性规划好全部音效需求（UI 音效包、战斗音效包、环境音效包），用 batch 一次生成。

#### audition_voices_for_character — 角色试听

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `character_name` | string | ✅ | 角色名 |
| `character_description` | string | ✅ | 声音描述（六维度格式） |
| `audition_line` | string | ✅ | 试听台词（**必须 ≥100 字符**） |
| `candidate_count` | number | | 候选数量 1-3（默认 3） |

**六维度声音描述格式**：
```
年龄感: [青年/中年/老年]
性别感: [男性/女性/中性]
音色: [低沉/清亮/沙哑/温柔/威严]
语速: [慢/中/快]
情绪基调: [冷静/热情/忧郁/活泼/严肃]
口音特征: [标准普通话/方言/外国口音]
```

**常见陷阱**：
- `audition_line` 少于 100 字符会报错 → 写一段完整的角色台词，不要用短句
- 试听是免费的，但 `confirm_character_voice` 会消耗 Voice Slot → 确认前多听几次

#### confirm_character_voice — 确认声音

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `character_name` | string | ✅ | 角色名 |
| `selected_index` | number | | 选择的候选编号（1-based，不填用推荐） |

**注意**：每次确认消耗 1 个 Voice Slot，不可撤销。

#### text_to_dialogue — 生成角色语音

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `inputs` | array | ✅ | 对白数组：`[{ character_name, text }]` |
| `language_code` | string | | 语言代码，默认 `"cmn"`（中文） |
| `stability` | number | | 稳定性 0-1（默认 0.5，越低越有情感波动） |
| `output_name` | string | | 输出文件名 |

**最佳实践**：
- 必须先 `confirm_character_voice` 后才能使用该角色的声音
- `stability` 设低（0.2-0.3）让对白更有感情，设高（0.7-0.8）让旁白更稳定
- 可以一次传入多段对白批量生成

---

### 2.3 视频工具

#### create_video_task — 生成视频

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | enum | ✅ | `"text_to_video"` / `"first_frame"` / `"first_last_frame"` / `"multi_modal_reference"` |
| `prompt` | string | | 视频描述（text_to_video 必填） |
| `images` | array | | 图片列表 `[{ url, role }]` |
| `duration` | integer | | 时长 4-15 秒 |
| `ratio` | enum | | `"16:9"` / `"9:16"` / `"1:1"` 等 |
| `resolution` | enum | | `"480p"` / `"720p"` |
| `generate_audio` | boolean | | 是否生成有声视频 |
| `seed` | integer | | 随机种子 |

**策划视角**：
- 宣传片用 `"text_to_video"` 模式 + `ratio: "16:9"`
- 过场动画用 `"first_frame"` 模式，传入概念图作为起始画面
- 用 `generate_audio: true` 生成有声视频减少后期拼接

**注意**：视频生成较慢，调用后用 `query_video_task` 轮询状态。

---

### 2.4 构建调试工具

#### build — 构建项目

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scriptsPath` | string | ✅ | 脚本目录，如 `"scripts"` |
| `entry` | string | | 单人游戏入口，如 `"main.lua"` |
| `entry_client` | string | | 多人游戏客户端入口 |
| `entry_server` | string | | 多人游戏服务端入口 |
| `multiplayer` | object | | 多人游戏配置 |

**策划视角**：这是你的「验证按钮」。每完成一轮资产整合，立刻 build 验证效果。不要等所有东西都做完才 build。

#### generate_test_qrcode — 生成测试二维码

无参数。直接调用，返回二维码图片，手机扫码即可测试。

#### get_debug_feedbacks — 获取测试反馈

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | number | | 返回数量（默认 5） |
| `status` | number | | `0`=全部, `1`=未处理, `2`=已处理 |
| `fetch_and_mark_processed` | boolean | | 拉取未处理并标记已处理（默认 true） |

**策划视角**：内测后第一时间调用，获取玩家反馈。日志和截图会自动下载到 `logs/feed_back/`。

---

### 2.5 发布运营工具

#### generate_game_material — 生成发布素材

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `game_name` | string | ✅ | 游戏名称 |
| `material_type` | string/string[] | ✅ | `"ICON"` / `"SCREENSHOT"` / `"PROMO"` / `"ALL_IN_PROMO"` |
| `images` | string[] | | 游戏截图路径（SCREENSHOT/PROMO 必需） |
| `extra_prompt` | string[] | | 宣传语（SCREENSHOT 需提供 3 条） |

**策划视角**：
- 先生成 `"ICON"`（应用图标），再截几张游戏画面，然后生成 `"SCREENSHOT"` 和 `"PROMO"`
- `extra_prompt` 写 3 条能打动目标玩家的宣传语

#### upload_game_material — 上传素材

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | enum | ✅ | `"ICON"` / `"SCREENSHOT"` / `"PROMO"` / `"SQUARE_PROMO"` |
| `file_path` | string | ✅ | 本地图片路径 |

#### publish_to_taptap — 发布到 TapTap

无参数。读取 `.project/project.json` 配置后发布。发布前确保素材已上传。

#### i18n_extract — 国际化文本提取

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scriptsPath` | string | ✅ | 脚本目录 |

**策划视角**：发布前调用，提取所有待翻译文本到 `{lang}.pending.json`，然后安排翻译。

#### bind_game_jam — 绑定 GameJam

**核心参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `game_jam_event_name` | string | | 活动名（模糊搜索） |
| `game_jam_event_id` | number | | 活动 ID（精确匹配） |

---

## 3. 场景化工作流模板

### 🔧 工作流 1：角色创建全流程

**场景**：从角色概念到可在游戏中体验的完整角色（3D 模型 + 立绘 + 配音 + 台词）

**步骤**：

1. **策划输出：角色设计文档**
   - 确定角色三维度：表层外貌 / 中层性格 / 深层动机
   - 输出角色描述文本（用于后续所有工具的 prompt）

2. **视觉：搜索 3D 模型**
   ```
   search_3d_resource: query="角色外貌关键词（如：白衣女剑客，长发飘逸）"
   ```
   - 从返回结果中选择最接近的模型下载

3. **视觉：生成角色立绘**（可与步骤 2 并行）
   ```
   generate_image:
     prompt="[详细角色外貌描述，50字以上，包含风格/色调/构图]"
     name="character_xxx_portrait"
     target_size="1024x1024"
     aspect_ratio="3:4"
     resolution="2K"
   ```
   - 不满意可用 `edit_image` 微调

4. **音频：试听角色声音**
   ```
   audition_voices_for_character:
     character_name="角色名"
     character_description="年龄感: 青年\n性别感: 女性\n音色: 清亮\n语速: 中\n情绪基调: 冷静\n口音特征: 标准普通话"
     audition_line="[≥100字符的角色代表台词，体现性格特征的完整段落]"
     candidate_count=3
   ```
   - 听完 3 个候选，选择最满意的

5. **音频：确认声音**
   ```
   confirm_character_voice:
     character_name="角色名"
     selected_index=2  (选中的候选编号)
   ```
   - ⚠️ 消耗 Voice Slot，确认前务必多听

6. **音频：生成角色台词**
   ```
   text_to_dialogue:
     inputs=[
       { character_name: "角色名", text: "台词1" },
       { character_name: "角色名", text: "台词2" },
       { character_name: "角色名", text: "台词3" }
     ]
     language_code="cmn"
     stability=0.3  (角色对白用低稳定性，更有感情)
   ```

7. **集成验证**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   generate_test_qrcode
   ```
   - 手机扫码验证角色在游戏中的整体表现

**注意事项**：
- 步骤 2（3D 模型）和步骤 3（立绘）可并行执行
- 步骤 4→5→6 必须串行（试听→确认→生成台词）
- `audition_line` 必须 ≥100 字符，写一段完整的角色独白

---

### 🔧 工作流 2：关卡原型快速验证

**场景**：验证关卡设计是否好玩，1小时内出可玩版本

**步骤**：

1. **策划输出：关卡设计草案**
   - 核心机制、难度曲线、空间布局、引导路径
   - 明确关卡体验目标（如：「紧张刺激」「探索发现」）

2. **视觉：搜索场景素材**
   ```
   search_3d_resource: query="关卡场景关键词（如：废弃城堡、地下洞穴）"
   ```

3. **视觉：生成概念图**（与步骤 2 并行）
   ```
   generate_image:
     prompt="[关卡场景描述，包含氛围、光线、色调]"
     name="level_xxx_concept"
     target_size="1920x1080"
     aspect_ratio="16:9"
   ```

4. **音频：生成环境音效**（与步骤 2、3 并行）
   ```
   batch_sound_effects:
     sounds=[
       { name: "ambient_loop", text: "dark cave ambience with dripping water and distant echoes", duration: 10, loop: true },
       { name: "footstep_stone", text: "footsteps on wet stone floor", duration: 2 },
       { name: "door_creak", text: "heavy wooden door creaking open slowly", duration: 3 }
     ]
   ```

5. **音频：生成关卡 BGM**（与步骤 2、3、4 并行）
   ```
   text_to_music:
     prompt="神秘地下洞穴探索，低沉弦乐缓慢推进，偶尔出现尖锐音效制造紧张感，整体氛围阴暗压抑"
     instrumental=true
     model="V4_5PLUS"
   ```

6. **集成验证**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   generate_test_qrcode
   ```

7. **收集反馈 → 迭代**
   ```
   get_debug_feedbacks: status=1, limit=10
   ```
   - 根据反馈调整关卡设计，重复步骤 2-6

**注意事项**：
- 步骤 2、3、4、5 全部可以并行执行，极大缩短时间
- 第一轮用 `resolution: "1K"` 快速出原型，确认方向后再提升质量
- 音效描述必须用英文

---

### 🔧 工作流 3：音频设计全链路

**场景**：为游戏构建完整的声音系统（BGM + 音效 + 角色配音）

**步骤**：

1. **策划输出：音频需求清单**
   - 列出所有需要的 BGM（主菜单、战斗、探索、boss 战等）
   - 列出所有 UI 音效（点击、确认、取消、升级等）
   - 列出所有游戏音效（攻击、受击、技能、环境等）
   - 列出需要配音的角色和台词

2. **BGM 批量生成**
   ```
   text_to_music:
     prompt="轻松愉快的主菜单音乐，钢琴为主，温暖明亮，让玩家感到放松"
     instrumental=true
     model="V4_5PLUS"
   ```
   ```
   text_to_music:
     prompt="紧张激烈的战斗音乐，快节奏鼓点，电吉他riff，充满能量"
     instrumental=true
     model="V4_5PLUS"
     negativeTags="calm, peaceful, slow"
   ```
   （每首 BGM 单独调用，可并行）

3. **UI 音效批量生成**
   ```
   batch_sound_effects:
     sounds=[
       { name: "ui_click", text: "soft button click", duration: 0.5 },
       { name: "ui_confirm", text: "positive confirmation chime", duration: 1 },
       { name: "ui_cancel", text: "soft cancel sound", duration: 0.5 },
       { name: "ui_upgrade", text: "magical upgrade sparkle sound ascending", duration: 1.5 },
       { name: "ui_error", text: "gentle error buzz", duration: 0.5 },
       { name: "ui_open_menu", text: "soft whoosh menu opening", duration: 0.8 }
     ]
   ```

4. **游戏音效批量生成**
   ```
   batch_sound_effects:
     sounds=[
       { name: "attack_sword", text: "sword slash through air with impact", duration: 1 },
       { name: "hit_receive", text: "character getting hit grunt with impact", duration: 1 },
       { name: "skill_fire", text: "fire spell casting with flames roaring", duration: 2 },
       { name: "pickup_coin", text: "coin pickup jingle", duration: 0.5 },
       { name: "env_wind", text: "gentle wind blowing through trees", duration: 10, loop: true },
       { name: "env_rain", text: "light rain on rooftop", duration: 10, loop: true }
     ]
   ```

5. **角色配音**（如需要）
   - 对每个角色执行：`audition_voices_for_character` → `confirm_character_voice` → `text_to_dialogue`
   - 详见工作流 1 的步骤 4-6

6. **集成验证**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   ```

**注意事项**：
- 步骤 2、3、4 可完全并行
- 所有音效描述必须用英文
- 环境音效设 `loop: true`
- BGM 完成后自动轮询，无需手动 query

---

### 🔧 工作流 4：UI/图标资产批量生产

**场景**：短时间内生成游戏所需的全部 UI 图标和素材

**步骤**：

1. **策划输出：UI 资产清单**
   - 列出所有需要的图标（技能图标、道具图标、状态图标等）
   - 确定统一的美术风格（写成 prompt 前缀）
   - 确定尺寸规格

2. **选定风格参考**
   ```
   generate_image:
     prompt="[风格参考描述]，游戏图标风格示例，卡通渲染，金色边框，深色背景"
     name="style_reference"
     target_size="256x256"
   ```
   - 对这张参考图满意后，用它作为后续所有图标的 `reference_images`

3. **批量生成图标**
   ```
   batch_generate_images:
     images=[
       {
         prompt: "火球技能图标，橙红色火焰球体，[统一风格描述]",
         name: "icon_skill_fireball",
         target_size: "256x256",
         aspect_ratio: "1:1",
         transparent: true,
         reference_images: ["style_reference.png的路径"]
       },
       {
         prompt: "冰冻技能图标，蓝色冰晶，[统一风格描述]",
         name: "icon_skill_ice",
         target_size: "256x256",
         aspect_ratio: "1:1",
         transparent: true,
         reference_images: ["style_reference.png的路径"]
       },
       // ... 更多图标
     ]
   ```

4. **迭代修改不满意的图标**
   ```
   edit_image:
     image="不满意的图标路径"
     prompt="把火焰颜色改得更亮，增加火花粒子"
     name="icon_skill_fireball_v2"
     target_size="256x256"
   ```

5. **集成验证**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   ```

**注意事项**：
- 用 `reference_images` 统一风格是关键，否则每个图标风格都不同
- 图标设 `transparent: true`，方便在游戏中叠加背景
- 一批不要超过 10-15 张，太多会增加失败风险

---

### 🔧 工作流 5：宣传素材制作

**场景**：准备应用商店上架所需的全部宣传素材（图标 + 截图 + 宣传图 + 视频）

**步骤**：

1. **准备游戏截图**
   - 在游戏中截取 3-5 张最能展现核心玩法的画面
   - 记录截图文件路径

2. **生成应用图标**
   ```
   generate_game_material:
     game_name="你的游戏名"
     material_type="ICON"
   ```

3. **生成商店截图**
   ```
   generate_game_material:
     game_name="你的游戏名"
     material_type="SCREENSHOT"
     images=["截图1路径", "截图2路径", "截图3路径"]
     extra_prompt=["一句话核心卖点", "独特玩法亮点", "情感共鸣点"]
   ```

4. **生成宣传图**
   ```
   generate_game_material:
     game_name="你的游戏名"
     material_type="PROMO"
     images=["截图1路径", "截图2路径"]
   ```

5. **上传素材**
   ```
   upload_game_material: type="ICON", file_path="图标路径"
   upload_game_material: type="SCREENSHOT", file_path="截图路径"
   upload_game_material: type="PROMO", file_path="宣传图路径"
   ```

6. **生成宣传视频**（可选）
   ```
   create_video_task:
     mode="first_frame"
     images=[{ url: "最佳截图路径", role: "first_frame" }]
     prompt="展现游戏核心玩法的15秒宣传视频"
     duration=15
     ratio="16:9"
     resolution="720p"
     generate_audio=true
   ```
   ```
   query_video_task: task_id="返回的task_id"
   ```

**注意事项**：
- 先生成 ICON，确认风格后再生成 SCREENSHOT 和 PROMO
- `extra_prompt` 的 3 条宣传语要面向目标玩家痛点，不要用空洞的形容词
- 素材上传后会更新 `project.json`

---

### 🔧 工作流 6：发布上线全流程

**场景**：从开发完成到 TapTap 正式上线的完整流程

**步骤**：

1. **国际化文本提取**
   ```
   i18n_extract: scriptsPath="scripts"
   ```
   - 输出 `{lang}.pending.json`，安排翻译

2. **生成发布素材**（详见工作流 5 步骤 2-4）

3. **上传素材**（详见工作流 5 步骤 5）

4. **内测准备**
   ```
   add_test_whitelist: user_id=测试用户的TapTap ID
   generate_test_qrcode
   ```
   - 分发二维码给测试用户

5. **收集内测反馈**
   ```
   get_debug_feedbacks: status=1, limit=20
   ```
   - 修复关键问题 → `build` → 重新分发

6. **广告配置**（如需要）
   ```
   get_ad_config
   ```
   - 广告配置写入 settings.json

7. **正式发布**
   ```
   list_tap_developers  (确认发布账号)
   publish_to_taptap
   ```

**注意事项**：
- 发布前确保所有素材已 `upload_game_material`
- 内测至少跑 1 轮 `get_debug_feedbacks` 确认无严重 bug
- `publish_to_taptap` 读取 `.project/project.json`，确保配置正确

---

### 🔧 工作流 7：快速原型验证

**场景**：1 小时内从概念到可玩原型，验证核心体验是否成立

**步骤**：

1. **策划输出：核心体验定义**
   - 一句话描述：玩家在什么情境下做什么动作，感受到什么？
   - 确定最小可玩范围（只保留验证体验必须的元素）

2. **搜索现成素材**（并行）
   ```
   search_3d_resource: query="核心场景关键词"
   search_3d_resource: query="核心角色关键词"
   ```

3. **生成占位图**（与步骤 2 并行）
   ```
   generate_image:
     prompt="[核心场景概念图]"
     name="prototype_scene"
     target_size="512x512"
     resolution="0.5K"  (原型阶段用最低分辨率，够看就行)
   ```

4. **构建最小原型**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   ```

5. **手机测试**
   ```
   generate_test_qrcode
   ```

6. **收集反馈 → 快速迭代**
   ```
   get_debug_feedbacks: status=1
   ```
   - 根据反馈调整 → 重新 build → 重新测试
   - 循环直到核心体验验证通过

**注意事项**：
- 原型阶段的核心原则：**够丑就行，体验为王**
- 所有资产用最低质量设置（`resolution: "0.5K"`, `target_size` 用小尺寸）
- 不要在原型阶段花时间打磨美术
- 目标是回答一个问题：「这个核心体验好不好玩？」

---

### 🔧 工作流 8：NPC 角色语音系统

**场景**：为游戏中的多个 NPC 构建完整的语音系统

**步骤**：

1. **策划输出：NPC 角色表**
   - 每个 NPC 的名字、性格、声音特征、代表台词（≥100 字符）
   - 每个 NPC 的全部台词文本

2. **逐角色试听**（不同角色可并行）
   ```
   audition_voices_for_character:
     character_name="村长老王"
     character_description="年龄感: 老年\n性别感: 男性\n音色: 沙哑低沉\n语速: 慢\n情绪基调: 慈祥\n口音特征: 标准普通话"
     audition_line="年轻人啊，这片土地上的每一棵树，每一块石头，都有它们自己的故事。你可别小看了这些看起来普通的东西，它们可是见证了几百年的风雨啊。来，让老夫给你讲讲这个村子的由来……"
     candidate_count=3
   ```

3. **确认各角色声音**
   ```
   confirm_character_voice:
     character_name="村长老王"
     selected_index=1
   ```
   - ⚠️ 每次确认消耗 Voice Slot

4. **批量生成台词**
   ```
   text_to_dialogue:
     inputs=[
       { character_name: "村长老王", text: "台词1" },
       { character_name: "村长老王", text: "台词2" },
       { character_name: "村长老王", text: "台词3" }
     ]
     stability=0.3
   ```
   - 对每个角色的全部台词批量生成

5. **集成验证**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   ```

**注意事项**：
- 不同角色的试听（步骤 2）可以并行
- 同一角色的试听→确认→生成必须串行
- `audition_line` 必须 ≥100 字符，短了会报错
- 建议先处理主要角色（出场多的），次要角色后面补

---

### 🔧 工作流 9：游戏氛围构建

**场景**：建立游戏的整体视听氛围（音乐 + 环境音 + 场景概念图 + 3D 场景），让团队/自己对「这个游戏的感觉」达成共识

**步骤**：

1. **策划输出：氛围定义文档**
   - 核心情绪关键词（如：「孤独」「神秘」「温暖」）
   - 参考作品（如：「像《空洞骑士》的阴郁但不恐怖」）
   - 色调倾向（冷/暖/对比色）

2. **生成主题音乐**
   ```
   text_to_music:
     prompt="[基于氛围定义的详细音乐描述，100字以上]"
     instrumental=true
     model="V5"
   ```

3. **生成环境音效**（与步骤 2 并行）
   ```
   batch_sound_effects:
     sounds=[
       { name: "env_main_ambience", text: "[主环境音描述]", duration: 15, loop: true },
       { name: "env_detail_1", text: "[细节音效1]", duration: 5, loop: true },
       { name: "env_detail_2", text: "[细节音效2]", duration: 3 }
     ]
   ```

4. **生成场景概念图**（与步骤 2、3 并行）
   ```
   batch_generate_images:
     images=[
       {
         prompt: "[主场景概念图描述]",
         name: "mood_scene_main",
         target_size: "1920x1080",
         aspect_ratio: "16:9",
         resolution: "2K"
       },
       {
         prompt: "[次要场景概念图描述]",
         name: "mood_scene_secondary",
         target_size: "1920x1080",
         aspect_ratio: "16:9",
         resolution: "2K"
       }
     ]
   ```

5. **搜索 3D 场景素材**（与步骤 2、3、4 并行）
   ```
   search_3d_resource: query="[场景关键词]"
   ```

6. **集成验证**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   ```
   - 在游戏中体验完整的视听氛围是否符合预期

**注意事项**：
- 步骤 2、3、4、5 全部可并行，充分利用等待时间
- 氛围构建的目的是「对齐感觉」，不追求最终质量
- 用概念图 + 音乐 + 环境音组合起来感受，而非单独评判

---

### 🔧 工作流 10：GameJam 极速开发

**场景**：48 小时 GameJam，从零到发布的极速全流程

**步骤**：

1. **绑定 GameJam**
   ```
   bind_game_jam: game_jam_event_name="活动名称"
   ```

2. **策划输出：30 分钟极速设计**
   - 一句话核心体验
   - 最小核心循环（不超过 3 步）
   - 唯一的胜利条件

3. **全速并行资产生成**（所有步骤同时启动）

   **视觉**：
   ```
   search_3d_resource: query="核心角色关键词"
   search_3d_resource: query="核心场景关键词"
   batch_generate_images:
     images=[
       { prompt: "游戏图标", name: "game_icon", target_size: "512x512", transparent: true },
       { prompt: "场景背景", name: "bg_main", target_size: "1920x1080", aspect_ratio: "16:9" },
       { prompt: "角色立绘", name: "char_main", target_size: "512x512", transparent: true }
     ]
   ```

   **音频**：
   ```
   text_to_music:
     prompt="[核心BGM描述]"
     instrumental=true
     model="V4_5PLUS"
   batch_sound_effects:
     sounds=[
       { name: "sfx_action", text: "[核心玩法音效]", duration: 1 },
       { name: "sfx_feedback", text: "[反馈音效]", duration: 0.5 },
       { name: "ui_click", text: "button click", duration: 0.3 }
     ]
   ```

4. **编码 + 构建（边写边 build）**
   ```
   build: scriptsPath="scripts", entry="main.lua"
   ```
   - 每完成一个功能模块就 build 一次

5. **快速测试**
   ```
   generate_test_qrcode
   ```

6. **制作发布素材**
   ```
   generate_game_material:
     game_name="游戏名"
     material_type="ICON"
   generate_game_material:
     game_name="游戏名"
     material_type="SCREENSHOT"
     images=["截图路径"]
     extra_prompt=["宣传语1", "宣传语2", "宣传语3"]
   ```

7. **上传 + 发布**
   ```
   upload_game_material: type="ICON", file_path="图标路径"
   upload_game_material: type="SCREENSHOT", file_path="截图路径"
   publish_to_taptap
   ```

**注意事项**：
- GameJam 核心原则：**完成 > 完美**
- 所有资产生成在步骤 3 全部并行启动，不等待
- 用最低质量设置（`resolution: "0.5K"`），只在最终截图时用高质量
- 编码和资产生成同步进行，不要串行等待
- 预留最后 2 小时做发布素材 + 上线

---

## 4. 工具编排原则

### 并行 vs 串行判断

```
可并行（互不依赖）：
  视觉资产 ‖ 音频资产 ‖ 视频资产
  generate_image ‖ text_to_music ‖ batch_sound_effects
  不同角色的 audition_voices_for_character

必须串行（有依赖）：
  audition_voices → confirm_voice → text_to_dialogue（同一角色）
  generate_game_material → upload_game_material → publish_to_taptap
  i18n_extract → 翻译 → build
  代码修改 → build → generate_test_qrcode → get_debug_feedbacks
```

### 构建时机

- **每完成一组资产整合后立刻 build**，不要攒到最后
- build 失败时优先检查脚本语法（用 `lua_lsp_client` 辅助）
- 构建后立刻 `generate_test_qrcode` 在真机上验证

### 资源质量分级

```
原型阶段：resolution="0.5K", target_size 用小尺寸，够看就行
验证阶段：resolution="1K", 确认方向正确
正式阶段：resolution="2K"~"4K", 出终稿
```

### seed 复现策略

- 满意的结果记录 seed 值
- 迭代时只改 prompt，保持 seed 不变 → 对比有意义
- 完全不满意时换 seed 或不设 seed 让系统随机

### 批量优于逐个

- 能用 `batch_generate_images` 就不要逐个 `generate_image`
- 能用 `batch_sound_effects` 就不要逐个 `text_to_sound_effect`
- 批量调用共享等待时间，总耗时远小于逐个调用之和
````

- [ ] **Step 2: Verify the file**

Read `game-design/references/mcp-toolkit.md` and verify:
- Section 1 has a 26-row tool catalog table
- Section 2 covers all 5 tool categories with parameter tables
- Section 3 has 10 workflow templates
- Section 4 has orchestration principles

---

### Task 4: Slim Down ai-era-design.md

**Files:**
- Modify: `game-design/references/ai-era-design.md:25-84` (sections 2-3)
- Modify: `game-design/references/ai-era-design.md:87-131` (section 4)

- [ ] **Step 1: Replace section 2 content table and add cross-reference**

In `game-design/references/ai-era-design.md`, find lines 25-37 (section 2 header + content generation table):

```
## 2. AI 在游戏内容生产中的应用现状

### 内容生成

| 内容类型 | 当前能力 | 代表工具/技术 |
|---------|---------|-------------|
| **3D 模型** | 文字/图片 → 3D Mesh，质量快速提升 | Meshy、Tripo、Rodin、Hunyuan3D |
| **纹理/贴图** | 高质量程序化纹理生成 | Adobe Firefly、Stable Diffusion |
| **动画** | 基础动作生成，专业级动作仍需人工 | DeepMotion、Cascadeur AI |
| **关卡布局** | 给定规则的程序化生成 | PCG + LLM 结合 |
| **对话/剧情** | NPC 实时对话，长篇剧情生成 | LLM（GPT、Claude、Qwen）|
| **音效/音乐** | 背景音乐、环境音效生成 | Suno、Udio、ElevenLabs |
| **代码** | 游戏逻辑、工具脚本 | Cursor、Claude Code |
```

Replace with:

```
## 2. AI 在游戏内容生产中的应用现状

> 📌 实际可用的 AI 工具和完整工作流，详见 [mcp-toolkit.md](mcp-toolkit.md)

AI 已能覆盖游戏内容生产的主要环节：3D 模型、纹理贴图、关卡布局、对话剧情、音效音乐、代码逻辑。当前动画生成仍需人工精修。
```

- [ ] **Step 2: Delete Roblox Cube 3D section (original section 3)**

Find and delete the entire section 3 (lines 57-84):

```
## 3. Roblox Cube 3D 与 AI UGC 趋势

### Cube 3D 的战略意义

Roblox 的 Cube 3D 基础模型代表着：
- 游戏公司内部的 AI 基础设施建设
- UGC 创作工具的 AI 化（降低创作门槛至接近零）
- 玩家即策划的愿景

**核心能力**（2024年披露）：
- 文字 → 3D 资产生成
- 图片 → 3D 模型重建
- 语义理解的风格迁移

**对游戏策划的影响**：
1. 传统美术工作流被压缩
2. "粗糙但自己做的"比"精细但无法参与"更受用户喜爱
3. 内容审核变成核心挑战（AI生成内容的质量和安全性）

### AI UGC 平台的策划挑战

| 挑战 | 描述 | 设计应对 |
|------|------|---------|
| **内容质量参差** | AI生成内容差异大 | 建立策划层的质量过滤机制 |
| **版权边界模糊** | 训练数据争议 | 使用权清晰的训练数据集 |
| **有害内容生成** | 玩家可能生成不当内容 | 多层审核：AI预审 + 人工抽检 |
| **创意同质化** | 大量相似 AI 生成内容 | 引入差异化约束和风格引导 |

---
```

- [ ] **Step 3: Slim section 4 — remove generic AI scenarios, keep prompt engineering**

Find lines 87-111 (section 4 header + generic scenarios):

```
## 4. AI 辅助策划工作流

### 当前最有价值的 AI 辅助场景

**快速原型验证**：
```
策划构思 → 用 LLM 生成初版 GDD → 识别设计漏洞
         → 用 AI 生成粗糙 Prototype → 玩家测试
         → 压缩验证时间 60-80%
```

**竞品分析**：
- 让 AI 快速汇总多款竞品特征
- 生成比较矩阵
- 识别市场空白

**数值平衡辅助**：
- 用 LLM 生成数值公式的变体
- 用代码模拟大量对战轮次
- 快速识别数值异常（极端情况）

**本地化与对话生成**：
- 多语言 NPC 对话生成
- 方言/风格的快速适配
- 翻译质量的快速迭代
```

Replace with:

```
## 3. AI 辅助策划工作流

> 📌 具体的工具调用和工作流模板，详见 [mcp-toolkit.md](mcp-toolkit.md)
```

Note: Section number changes from 4 to 3 because the old section 3 (Roblox) was deleted.

- [ ] **Step 4: Renumber remaining sections**

The prompt engineering section (old "### 策划提示词工程最佳实践") stays under the new section 3.

Old section 5 → new section 4: "AI 时代策划的不可替代能力"
Old section 6 → new section 5: "未来 5 年的游戏设计预判"

Find:
```
## 5. AI 时代策划的不可替代能力
```
Replace with:
```
## 4. AI 时代策划的不可替代能力
```

Find:
```
## 6. 未来 5 年的游戏设计预判
```
Replace with:
```
## 5. 未来 5 年的游戏设计预判
```

- [ ] **Step 5: Verify the slimmed file**

Read the entire `game-design/references/ai-era-design.md` and verify:
- Section 1: 范式转变概览 (preserved)
- Section 2: 精简版 + 交叉引用 to mcp-toolkit.md + AI NPC 革命 (preserved)
- Section 3: AI 辅助策划工作流 (交叉引用 + prompt engineering preserved)
- Section 4: 策划的不可替代能力 (preserved)
- Section 5: 未来预判 (preserved)
- No Roblox Cube 3D content
- No generic AI scenario descriptions (原型验证/竞品分析/数值平衡/本地化)

---

### Task 5: Final Cross-Reference Verification

**Files:**
- Read: `game-design/SKILL.md`
- Read: `game-design/references/mcp-toolkit.md`
- Read: `game-design/references/ai-era-design.md`

- [ ] **Step 1: Verify all cross-references**

Read all three files and verify:
1. SKILL.md reference table includes `references/mcp-toolkit.md` row
2. SKILL.md directory tree includes `mcp-toolkit.md` entry
3. ai-era-design.md section 2 links to `mcp-toolkit.md`
4. ai-era-design.md section 3 links to `mcp-toolkit.md`
5. SKILL.md output spec references `references/mcp-toolkit.md`
6. SKILL.md document output spec references `references/mcp-toolkit.md`

- [ ] **Step 2: Verify tool name consistency**

Grep all three files for tool names and verify they match the actual MCP tool names:
- `generate_image` (not `generate-image` or `generateImage`)
- `batch_generate_images` (not `batch_generate_image`)
- `text_to_music` (not `text-to-music`)
- `text_to_sound_effect` (not `text_to_sound_effects`)
- `batch_sound_effects` (not `batch_sound_effect`)
- `audition_voices_for_character` (not `audition_voice`)
- `confirm_character_voice` (not `confirm_voice`)
- `text_to_dialogue` (not `text_to_dialog`)
- `search_3d_resource` (not `search_3d_resources`)
- `generate_game_material` (not `generate_materials`)
- `upload_game_material` (not `upload_materials`)
- `publish_to_taptap` (not `publish_taptap`)
