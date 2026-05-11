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

#### `generate_image`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 中文描述，最大 50KB |
| `name` | string | ✅ | 文件名，不含扩展名 |
| `target_size` | string | ✅ | 如 `"256x256"`、`"1024x1024"` |
| `aspect_ratio` | enum | | `1:1` / `2:3` / `3:2` / `3:4` / `4:3` / `9:16` / `16:9` / `21:9` / `5:4` / `4:5` |
| `transparent` | boolean | | 是否透明背景 |
| `reference_images` | string[] | | 参考图片 URL，最多 14 张 |
| `seed` | number | | 随机种子，用于复现结果 |
| `thinking_level` | enum | | `"minimal"` / `"high"` |
| `resolution` | enum | | `"0.5K"` / `"1K"` / `"2K"` / `"4K"` |

**最佳实践：**
- prompt 用中文越具体越好，描述风格、材质、光照、构图
- 图标类素材设 `transparent: true`
- 用 `seed` 固定满意的结果，方便迭代
- 先用 `1K` 验证方向，确认后再出 `2K` / `4K` 终稿
- 用 `reference_images` 传入已有素材，保持视觉风格一致

**常见陷阱：**
- prompt 太短，描述不足，导致结果随机性高
- 忘记设 `target_size`，工具无法确定输出尺寸
- 一次修改太多参数，无法判断哪个参数影响了结果

---

#### `batch_generate_images`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `images` | array | ✅ | 图片请求数组，每项参数同 `generate_image` |

**策略：**
- 一次批量不超过 10-15 张，避免超时
- 每项传入相同的 `reference_images` 保持整套素材风格一致
- 适合一次性生产整套 UI 图标、道具贴图集

---

#### `edit_image`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | string | ✅ | 原图路径 |
| `prompt` | string | ✅ | 编辑指令，如 `"把背景改成蓝色"` |
| `name` | string | ✅ | 输出文件名 |
| `target_size` | string | ✅ | 最终尺寸 |
| `aspect_ratio` | enum | | 同 `generate_image` |
| `reference_images` | string[] | | 参考图（最多 13 张） |
| `seed` | number | | 随机种子 |
| `thinking_level` | enum | | `"minimal"` / `"high"` |
| `resolution` | enum | | `"0.5K"` / `"1K"` / `"2K"` / `"4K"` |

**策略：**
- 用于局部调整，如换颜色、去背景、改细节
- 先 `generate_image` 出基底，再 `edit_image` 微调，效率高于重新生成

---

#### `search_3d_resource`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 自然语言描述，如 `"白衣剑客"`、`"medieval knight"` |

**最佳实践：**
- 中英文关键词都可以，英文搜索范围更广
- 先用宽泛关键词（如 `"knight"`），再用具体关键词缩小范围
- 先搜索确认有合适资源再规划场景，避免后期找不到资产

---

### 2.2 音频资产工具

#### `text_to_music`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 音乐风格和氛围描述 |
| `customMode` | boolean | | 是否自定义模式 |
| `style` | string | | 自定义模式必填，音乐风格标签 |
| `title` | string | | 自定义模式必填，曲目名称 |
| `instrumental` | boolean | | 是否纯器乐（无人声） |
| `model` | enum | | `V3_5` / `V4` / `V4_5` / `V4_5PLUS` / `V5` |
| `negativeTags` | string | | 不想要的风格标签 |
| `vocalGender` | string | | 人声性别，`m`（男）/ `f`（女） |

**最佳实践：**
- BGM 必须设 `instrumental: true`，否则会出现人声
- prompt 描述游戏氛围和情绪，而非技术参数（如"黑暗森林里的探险感"）
- 用 `negativeTags` 排除不想要的元素（如 `"electric guitar, heavy metal"`）
- 推荐使用 `V4_5PLUS` 或 `V5` 获得更好质量
- 可并行发起多首 BGM 任务，用 `query_music_task` 轮询状态

**常见陷阱：**
- 忘记设 `instrumental: true`，导致 BGM 带人声
- prompt 太短（如"战斗音乐"），生成结果质量低且随机

---

#### `text_to_sound_effect`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | ✅ | **必须用英文描述！** |
| `duration_seconds` | number | | 时长，0.5-30 秒 |
| `prompt_influence` | number | | 提示影响力，0-1，默认 0.3 |
| `loop` | boolean | | 是否可循环 |
| `output_name` | string | | 输出文件名 |

**最佳实践：**
- UI 音效：0.5-1 秒（点击、确认、提示音）
- 战斗音效：1-3 秒（爆炸、击中、技能释放）
- 环境音设 `loop: true`，用于持续播放的背景氛围
- 描述要具体：`"heavy sword impact on metal armor"` 优于 `"sword hit"`

**常见陷阱：**
- **用中文描述！** 这是最常见错误。`text` 参数必须使用英文，中文描述会导致生成质量极差或失败

---

#### `batch_sound_effects`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sounds` | array | ✅ | 每项含 `name`(✅)、`text`(✅,英文)、`duration`、`loop` |

**策略：**
- 所有 `text` 字段必须为英文
- 适合一次性生成整套音效包（UI 音效包、战斗音效包、环境音包）
- 比逐个调用 `text_to_sound_effect` 更高效，共享等待时间

---

#### `audition_voices_for_character`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `character_name` | string | ✅ | 角色名称 |
| `character_description` | string | ✅ | 六维度格式的角色声音描述 |
| `audition_line` | string | ✅ | 试听台词，**不少于 100 个字符** |
| `candidate_count` | number | | 候选声音数量，1-3，默认 3 |

**六维度描述格式：**
```
年龄感: [青年/中年/老年]
性别感: [男性/女性/中性]
音色: [低沉/清亮/沙哑/温柔/威严]
语速: [慢/中/快]
情绪基调: [冷静/热情/忧郁/活泼/严肃]
口音特征: [标准普通话/方言/外国口音]
```

**最佳实践：**
- 六维度描述越详细，声音匹配度越高
- `audition_line` 应使用角色典型台词，能充分展示声音特色
- 建议 `candidate_count: 3`，从多个候选中选择最合适的

**常见陷阱：**
- `audition_line` 少于 100 字符会报错，确保台词足够长
- `confirm_character_voice` 会消耗 Voice Slot，一旦确认不可撤销，试听后谨慎选择

---

#### `confirm_character_voice`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `character_name` | string | ✅ | 角色名称，需与试听时一致 |
| `selected_index` | number | ✅ | 选择的候选序号，从 1 开始 |

**Voice Slot 警告：** 每次调用此工具都会消耗一个 Voice Slot，且操作不可撤销。请在 `audition_voices_for_character` 充分试听后再确认。

---

#### `text_to_dialogue`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `inputs` | array | ✅ | 台词列表，每项含 `character_name` 和 `text` |
| `language_code` | string | | 语言代码，默认 `"cmn"`（普通话） |
| `stability` | number | | 语音稳定性，0-1，默认 0.5 |
| `output_name` | string | | 输出文件名 |

**稳定性调节技巧：**
- `stability: 0.2-0.3`：更有感情波动，适合剧情对白、情绪化台词
- `stability: 0.7-0.8`：更稳定平滑，适合旁白、系统提示音
- 必须先 `confirm_character_voice` 后才能使用对应角色生成对白

---

### 2.3 视频工具

#### `create_video_task`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | enum | ✅ | `text_to_video` / `first_frame` / `first_last_frame` / `multi_modal_reference` |
| `prompt` | string | | 视频内容描述 |
| `images` | array | | 参考图，每项含 `url` 和 `role` |
| `duration` | int | | 视频时长，4-15 秒 |
| `ratio` | enum | | 画面比例，如 `16:9`、`9:16` |
| `resolution` | enum | | `480p` / `720p` |
| `generate_audio` | boolean | | 是否自动生成配套音频 |
| `seed` | int | | 随机种子 |

**策略：**
- 宣传片用 `first_frame` 模式，用已有截图作为首帧，确保画面一致性
- 过场动画用 `first_last_frame`，控制开头和结尾画面
- 设 `generate_audio: true` 节省后期配音工作量
- 生成后用 `query_video_task` 轮询状态

---

### 2.4 构建调试工具

#### `build`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scriptsPath` | string | ✅ | 脚本目录，如 `"scripts"` |
| `entry` | string | | 单人游戏入口，如 `"main.lua"` |
| `entry_client` | string | | 多人游戏客户端入口 |
| `entry_server` | string | | 多人游戏服务端入口 |
| `multiplayer` | object | | 多人游戏配置 |

**策略：**
- 每次修改代码后必须调用，不 build 就无法测试
- build 失败时用 `lua_lsp_client` 检查语法和类型错误
- 成功后立刻调用 `generate_test_qrcode` 生成测试码

---

#### `generate_test_qrcode`

无参数。生成当前构建版本的测试二维码，供手机扫码真机测试。

---

#### `get_debug_feedbacks`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | number | | 返回数量，默认 5 |
| `status` | number | | `0` 全部 / `1` 未处理 / `2` 已处理 |
| `fetch_and_mark_processed` | boolean | | 获取后自动标记为已处理，默认 true |

---

### 2.5 发布运营工具

#### `generate_game_material`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `game_name` | string | ✅ | 游戏名称 |
| `material_type` | string / string[] | ✅ | `ICON` / `SCREENSHOT` / `PROMO` / `ALL_IN_PROMO` |
| `images` | string[] | | `SCREENSHOT` / `PROMO` 必需，提供游戏截图 |
| `extra_prompt` | string[] | | `SCREENSHOT` 需要 3 条，面向玩家的卖点描述 |

**策略：**
- 推荐顺序：先生成 `ICON` 确认整体风格，再生成 `SCREENSHOT`，最后生成 `PROMO`
- `extra_prompt` 的 3 条文案应覆盖游戏核心卖点，面向目标玩家的痛点和爽点
- 生成后需用 `upload_game_material` 逐个上传，才能在 TapTap 商店页展示

---

#### `upload_game_material`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | enum | ✅ | `ICON` / `SCREENSHOT` / `PROMO` / `SQUARE_PROMO` |
| `file_path` | string | ✅ | 本地文件路径 |

---

#### `publish_to_taptap`

无参数。读取 `.project/project.json` 中的配置，将游戏发布到 TapTap 平台。发布前确保所有素材已上传，且至少完成一轮内测反馈收集。

---

#### `i18n_extract`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scriptsPath` | string | ✅ | 脚本目录路径 |

从代码中提取所有需要国际化的文本，生成翻译文件模板，用于多语言版本准备。

---

#### `bind_game_jam`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `game_jam_event_name` | string | | 活动名称，支持模糊搜索 |
| `game_jam_event_id` | number | | 活动 ID，精确匹配 |

两个参数至少提供一个。优先用 `game_jam_event_id` 精确绑定；不知道 ID 时用名称模糊搜索。

---

## 3. 场景化工作流模板

### 🔧 工作流 1：角色创建全流程

**场景**：从零创建一个有外观、有声音、有对白的完整角色。

**步骤**：

1. 策划输出角色设计文档（外貌、性格、背景、台词风格）
2. 并行执行：
   - `search_3d_resource(query="角色关键词，如低多边形武士")`
   - `generate_image(prompt="角色立绘描述", target_size="1024x1024", aspect_ratio="3:4", resolution="2K")`
3. `audition_voices_for_character(character_name="角色名", character_description="六维度格式", audition_line="不少于100字的典型台词", candidate_count=3)`
4. `confirm_character_voice(character_name="角色名", selected_index=2)` ← 从候选中选最合适的
5. `text_to_dialogue(inputs=[{character_name:"角色名", text:"台词内容"}], stability=0.3)`
6. 集成验证：`build` + `generate_test_qrcode`

**注意事项：**
- 步骤 2 的搜索和生图可并行，节省时间
- 步骤 3 → 4 → 5 必须串行，有依赖关系
- `audition_line` 不得少于 100 字符，否则报错
- `confirm_character_voice` 消耗 Voice Slot，不可撤销，试听后认真选择

---

### 🔧 工作流 2：关卡原型快速验证

**场景**：快速搭建关卡原型，验证核心玩法是否有趣。

**步骤**：

1. 策划输出关卡设计草案（空间布局、障碍类型、节奏节点）
2. 并行执行：
   - `search_3d_resource(query="场景资产关键词，如废墟工厂")`
   - `generate_image(prompt="关卡概念图描述", target_size="1920x1080", aspect_ratio="16:9", resolution="1K")`
   - `batch_sound_effects(sounds=[{text:"ambient industrial hum", loop:true, name:"env_factory"}, ...])`
   - `text_to_music(prompt="工业风废墟探险氛围，紧张压抑", instrumental=true, model="V4_5PLUS")`
3. `build` + `generate_test_qrcode`
4. 内测后：`get_debug_feedbacks(status=1)` 收集未处理反馈

**注意事项：**
- 步骤 2 的全部四个任务可并行启动
- 第一轮使用 `1K` 分辨率，验证方向正确后再升级
- 音效描述必须用英文
- 目标是验证玩法，不是追求完美美术

---

### 🔧 工作流 3：音频设计全链路

**场景**：为游戏制作完整的音频体系，包括 BGM、音效包和角色配音。

**步骤**：

1. 策划输出音频需求清单（BGM 列表、音效列表、配音角色表）
2. 并行启动所有 BGM 任务：
   - `text_to_music(prompt="主菜单优雅钢琴曲", instrumental=true, title="main_theme")`
   - `text_to_music(prompt="战斗激烈摇滚风格", instrumental=true, title="battle_bgm")`
   - `text_to_music(prompt="胜利欢快铜管乐", instrumental=true, title="victory_bgm")`
3. 并行生成音效包：
   - `batch_sound_effects(sounds=[{text:"UI button click soft", name:"ui_click"}, {text:"menu open whoosh", name:"ui_open"}, ...])`（UI 音效包）
   - `batch_sound_effects(sounds=[{text:"sword slash heavy", name:"sword_slash"}, {text:"explosion medium", name:"explosion"}, ...])`（战斗音效包）
4. 角色配音流程（每角色串行）：
   - `audition_voices_for_character` → `confirm_character_voice` → `text_to_dialogue(stability=0.3)`
5. `build` 集成所有音频资产

**注意事项：**
- BGM、UI 音效包、战斗音效包可完全并行
- 所有音效描述必须使用英文
- 环境音设 `loop: true`
- 不同角色的试听可并行，但同一角色的试听→确认→生成必须串行

---

### 🔧 工作流 4：UI/图标资产批量生产

**场景**：为游戏制作一套风格统一的 UI 图标和界面元素。

**步骤**：

1. 策划输出 UI 资产清单（图标种类、尺寸规格、风格定义）
2. `generate_image(prompt="风格参考图，整体视觉基调描述", name="style_reference", target_size="1024x1024")`（生成风格基准图）
3. `batch_generate_images(images=[{prompt:"剑图标，游戏道具风格", name:"icon_sword", target_size:"256x256", transparent:true}, {prompt:"盾牌图标", name:"icon_shield", target_size:"256x256", transparent:true}, ...], reference_images=["style_reference.png"])`
4. 对需要微调的图标：`edit_image(prompt:"调整颜色为金色", image:"icon_sword.png", name:"icon_sword_v2")`
5. `build` 集成资产

**注意事项：**
- `reference_images` 传入风格参考图是保持统一性的关键
- 图标类素材必须设 `transparent: true`
- 一批次不超过 10-15 张，避免超时
- 先出一两张验证风格，再批量生产

---

### 🔧 工作流 5：宣传素材制作

**场景**：为 TapTap 商店页制作应用图标、截图和宣传图。

**步骤**：

1. 准备 3-5 张游戏内截图（真实游戏画面）
2. `generate_game_material(game_name="游戏名", material_type="ICON")`
3. `generate_game_material(game_name="游戏名", material_type="SCREENSHOT", images=["screenshot1.png", "screenshot2.png", "screenshot3.png"], extra_prompt=["核心玩法卖点描述", "目标玩家痛点解决方案", "独特游戏特色展示"])`
4. `generate_game_material(game_name="游戏名", material_type="PROMO", images=["best_screenshot.png"])`
5. 逐个上传：
   - `upload_game_material(type="ICON", file_path="/path/to/icon.png")`
   - `upload_game_material(type="SCREENSHOT", file_path="/path/to/screenshot.png")`
   - `upload_game_material(type="PROMO", file_path="/path/to/promo.png")`
6. `create_video_task(mode="first_frame", images=[{url:"best_screenshot.png", role:"first_frame"}], ratio="16:9", resolution="720p", generate_audio=true, duration=15)`
7. `query_video_task` 轮询直到完成

**注意事项：**
- 先确认 ICON 风格再继续 SCREENSHOT，确保整体一致
- `extra_prompt` 的 3 条文案面向目标玩家的痛点和爽点
- 上传完成后检查 `.project/project.json` 素材路径是否更新
- 宣传视频用游戏最精彩的画面作为首帧

---

### 🔧 工作流 6：发布上线全流程

**场景**：游戏开发完成，准备正式发布到 TapTap。

**步骤**：

1. `i18n_extract(scriptsPath="scripts")` 提取所有需要翻译的文本
2. 制作发布素材（参考工作流 5）
3. 上传所有素材（`upload_game_material` 逐个类型上传）
4. 并行：`add_test_whitelist` + `generate_test_qrcode` 开放内测
5. `get_debug_feedbacks(status=1)` 收集并处理所有反馈
6. `get_ad_config` 同步广告配置（如需接入广告变现）
7. `list_tap_developers` 确认发布账号
8. `publish_to_taptap` 正式发布

**注意事项：**
- 发布前确保所有素材已成功上传，在 TapTap 后台可预览
- 至少完成一轮内测，收集并修复主要问题
- `publish_to_taptap` 自动读取 `.project/project.json` 配置，发布前核查配置无误
- 国际化文本完成翻译后需重新 build

---

### 🔧 工作流 7：快速原型验证

**场景**：用最短时间验证核心体验是否成立，不追求美术质量。

**步骤**：

1. 用一句话定义核心体验（"玩家用惯性弹射摧毁障碍物"）
2. 并行搜索占位资产：
   - `search_3d_resource(query="场景关键词")`
   - `search_3d_resource(query="角色关键词")`
3. `generate_image(prompt="简单占位图描述", target_size="512x512", resolution="0.5K")` 生成最低质量占位图
4. `build` + `generate_test_qrcode`
5. 真机体验核心循环
6. `get_debug_feedbacks` 收集反馈
7. 根据反馈迭代（回到步骤 1 或步骤 4）

**注意事项：**
- 够丑就行，体验为王
- 所有资产使用最低质量设置（`0.5K`，最小尺寸）
- 不在这个阶段打磨美术
- 目标只有一个：核心体验好不好玩？

---

### 🔧 工作流 8：NPC 角色语音系统

**场景**：为游戏中多个 NPC 角色制作完整的语音对白系统。

**步骤**：

1. 整理 NPC 角色表（名字 / 性格 / 声音需求 / 台词列表）
2. 并行为所有角色试听（不同角色可并行）：
   - `audition_voices_for_character(character_name="老铁匠", character_description="年龄感:老年\n性别感:男性\n音色:沙哑\n语速:慢\n情绪基调:严肃\n口音特征:标准普通话", audition_line="孩子，这把剑跟了我四十年了...每一道刻痕都是一段故事，你拿去吧，但要记住，剑是有灵魂的，善待它。这世上的事啊，没有那么简单，你还年轻，慢慢学吧。", candidate_count=3)`
   - `audition_voices_for_character(character_name="年轻向导", ...)`
3. 串行确认每个角色的声音：
   - `confirm_character_voice(character_name="老铁匠", selected_index=1)`
   - `confirm_character_voice(character_name="年轻向导", selected_index=3)`
4. 批量生成台词：
   - `text_to_dialogue(inputs=[{character_name:"老铁匠", text:"欢迎来到我的铺子"}, {character_name:"老铁匠", text:"需要修理武器吗？"}], stability=0.3)`
5. `build` 集成语音资产

**注意事项：**
- 不同角色的试听可并行，大幅节省时间
- 同一角色的试听→确认→生成必须严格串行
- `audition_line` 不得少于 100 字符，准备足够长的试听台词
- 先处理主要角色（主线 NPC），次要角色后处理

---

### 🔧 工作流 9：游戏氛围构建

**场景**：为游戏建立统一的视听氛围，让玩家进入特定的情绪状态。

**步骤**：

1. 定义氛围关键词（如：孤独 / 壮阔 / 神秘 / 温暖），列出参考作品和色调要求
2. 并行启动所有氛围资产生成：
   - `text_to_music(prompt="孤独的星际旅行者，浩瀚宇宙中的渺小与壮阔，合成器电子音乐", instrumental=true, model="V5")`
   - `batch_sound_effects(sounds=[{text:"deep space ambient hum", loop:true, name:"env_space"}, {text:"distant stellar wind", loop:true, name:"env_wind"}])`
   - `batch_generate_images(images=[{prompt:"宇宙星云背景，冷色调，孤寂感", name:"bg_space", target_size:"1920x1080", aspect_ratio:"16:9", resolution:"2K"}, ...])`
   - `search_3d_resource(query="宇宙飞船科幻场景")`
3. `build` 集成全部氛围资产，整体感受
4. 根据整体感受调整（可能需要调整某个环节）

**注意事项：**
- 步骤 2 的全部任务可完全并行
- 目的是对齐整体感觉，要组合感受而非单独评判每个资产
- 音效描述必须用英文
- 先确认音乐方向，因为音乐对氛围影响最大

---

### 🔧 工作流 10：GameJam 极速开发

**场景**：参加 48/72 小时 GameJam，用最短时间做出可玩、可提交的游戏。

**步骤**：

1. `bind_game_jam(game_jam_event_name="GameJam 活动名称")` 绑定活动
2. 30 分钟极速设计（不超时）：
   - 一句话核心体验（"玩家控制重力躲避障碍"）
   - 最小游戏循环（3 步以内）
   - 唯一胜利条件
3. 全速并行启动所有资产任务：
   - `search_3d_resource(query="场景资产")`
   - `search_3d_resource(query="角色资产")`
   - `batch_generate_images(images=[...], resolution="0.5K")` 最低质量
   - `text_to_music(prompt="游戏主题BGM", instrumental=true, model="V4_5PLUS")`
   - `batch_sound_effects(sounds=[...])` 基础音效包
4. 同步编写核心代码，边写边 `build` 验证
5. `generate_test_qrcode` 真机测试核心循环
6. 核心玩法稳定后：
   - `generate_game_material(game_name="游戏名", material_type="ICON")`
   - `generate_game_material(game_name="游戏名", material_type="SCREENSHOT", images=[...], extra_prompt=[...])`
7. `upload_game_material` 上传素材 → `publish_to_taptap` 提交

**注意事项：**
- 完成 > 完美，能玩能提交就是胜利
- 步骤 3 全部并行，不要等一个完成再启动另一个
- 所有资产使用最低质量设置
- 编码和资产生成同步进行，不要串行等待
- 预留最后 2 小时专门用于发布流程，不要卡在开发上

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

**判断规则**：问自己"B 任务需要 A 任务的输出吗？"如果不需要，就并行。

### 构建时机

- 每完成一组资产整合后立刻 `build`，不要攒太多再 build
- `build` 失败时用 `lua_lsp_client` 检查语法和类型错误，定位问题
- 构建成功后立刻 `generate_test_qrcode` 真机验证，不要只看日志

### 资源质量分级

```
原型阶段：resolution="0.5K"，target_size 用小尺寸，够看就行
验证阶段：resolution="1K"，确认方向正确
正式阶段：resolution="2K"~"4K"，出终稿
```

不要在原型阶段就用高质量设置，浪费时间和等待成本。

### seed 复现策略

- 满意的结果立刻记录 `seed` 值
- 迭代时只改 `prompt`，保持 `seed` 不变，便于对比差异
- 完全不满意当前方向时，换 `seed` 或不设（随机）重新探索
- 多人协作时共享 `seed` 确保大家看到相同的参考结果

### 批量优于逐个

- 能用 `batch_generate_images` 就不逐个调用 `generate_image`
- 能用 `batch_sound_effects` 就不逐个调用 `text_to_sound_effect`
- 批量任务共享等待时间，10 张图并行等待时间 ≈ 1 张图等待时间
- 但批量太大会增加失败风险，建议单批次不超过 10-15 个任务
