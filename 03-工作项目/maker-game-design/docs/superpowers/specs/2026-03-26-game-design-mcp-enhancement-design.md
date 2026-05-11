# Game-Design Skill MCP Enhancement — Design Spec

## 概述

将 game-design 技能从「纯策划咨询」升级为「设计即可执行」的实战技能，通过有机融合 MCP 工具意识，让策划思维和工具落地成为一体。

## 方案：骨架融合

SKILL.md 的改动是有机的——在已有结构上生长，不破坏策划思维框架。新建 mcp-toolkit.md 承载重度实战内容。ai-era-design.md 瘦身保留理论精华。

---

## 改动清单

### 文件 1：`game-design/SKILL.md`（融合改动）

#### 1.1 核心工作流增强

6 步流程每步增加 `→ 🔧` 行，提示可用工具：

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

#### 1.2 参考文件索引新增

在「何时读取参考文件」表中新增一行：

| 任务类型 | 读取参考文件 |
|---------|------------|
| 工具编排、资产生产、原型构建、发布上线 | `references/mcp-toolkit.md` |

#### 1.3 快速判断框架增强

在原有「三问」之后增加第四问：

```
4. 可执行性：现有 MCP 工具能否在1小时内生成该功能的原型？
   → 如果能，直接原型验证比纸上推演更有效
```

#### 1.4 输出规范增强

**设计类** 新增：
- 列出实现所需的工具编排步骤（参考 mcp-toolkit.md 工作流模板）
- 标注哪些资产可以 AI 生成 vs 必须手工制作

**文档类** 新增：
- GDD 的「技术实现」章节应引用可用 MCP 工具

#### 1.5 策划大师底层直觉增强

第 6 条改为：
```
6. 原型优于文档：用 MCP 工具链在1小时内构建最粗糙的可玩原型，
   再花资源精细化。能 build 出来测试的，就不要停留在文档阶段。
```

#### 1.6 参考文件目录更新

在 references/ 下新增 mcp-toolkit.md 条目：
```
│   ├── mcp-toolkit.md               ← MCP工具实战手册：工具速查/工作流模板/编排原则
```

---

### 文件 2：新建 `game-design/references/mcp-toolkit.md`

#### 整体结构

```
# MCP 工具实战手册

## 1. 工具总览速查表
## 2. 工具分类详解（5大类）
## 3. 场景化工作流模板（10个）
## 4. 工具编排原则
```

#### 2.1 工具总览速查表

按 5 大功能分类：

| 分类 | 包含工具 | 策划视角 |
|------|---------|---------|
| **视觉资产** | generate_image, batch_generate_images, edit_image, search_3d_resource | 概念图→立绘→UI素材→3D模型 |
| **音频资产** | text_to_music, query_music_task, text_to_sound_effect, batch_sound_effects, text_to_dialogue, audition_voices_for_character, confirm_character_voice | 背景音乐→音效→角色配音全链路 |
| **视频/动态** | create_video_task, query_video_task | 过场动画、宣传片、UI动效参考 |
| **构建调试** | build, generate_test_qrcode, add_test_whitelist, get_debug_feedbacks, lua_lsp_client | 编码→构建→测试→反馈闭环 |
| **发布运营** | generate_game_material, upload_game_material, publish_to_taptap, list_tap_developers, get_ad_config, bind_game_jam, i18n_extract | 素材制作→上传→发布→广告→国际化 |

#### 2.2 每类工具详解

每个分类包含：
- **能力矩阵**：每个工具的核心参数、输出、限制
- **最佳实践**：prompt 写法、参数选择建议
- **常见陷阱**：易犯错的地方和解决方案
- **策划视角**：从策划需求到工具调用的思维映射

关键参数速查（嵌入每个工具下）：
- generate_image: prompt(中文), name, target_size, aspect_ratio, transparent, reference_images, seed, resolution
- text_to_music: prompt, style, instrumental, model(V3_5~V5), vocalGender
- text_to_sound_effect: text(英文!), duration_seconds(0.5-30), loop
- audition_voices_for_character: character_description(六维度格式), audition_line(≥100字符)
- text_to_dialogue: inputs数组[{character_name, text}], language_code, stability
- build: scriptsPath, entry/entry_client/entry_server, multiplayer配置

#### 2.3 场景化工作流模板（10个）

每个模板格式：

```markdown
### 🔧 工作流：[名称]
**场景**：[何时使用]
**预计时间**：[AI辅助时间 vs 传统时间]

**步骤**：
1. [策划输出]
   - 描述
2. [工具调用 1]
   - 工具名: 关键参数=示例值
   - 注意事项
3. [工具调用 N]
   ...
4. 集成验证
   - build + generate_test_qrcode

**注意事项**：
- [陷阱和限制]
```

**10 个工作流模板**：

1. **角色创建全流程**
   场景：从角色概念到可在游戏中体验的完整角色
   流程：角色设计 → search_3d_resource → generate_image(立绘) → audition_voices → confirm_voice → text_to_dialogue → build

2. **关卡原型快速验证**
   场景：验证关卡设计是否好玩，1小时内出可玩版本
   流程：关卡设计 → search_3d_resource(场景素材) → generate_image(概念图) → batch_sound_effects(环境音) → text_to_music(关卡BGM) → build → generate_test_qrcode

3. **音频设计全链路**
   场景：为游戏构建完整的声音系统
   流程：音效规划 → batch_sound_effects(UI音效+战斗音效+环境音) → text_to_music(BGM) → audition_voices(角色) → text_to_dialogue(台词) → build

4. **UI/图标资产批量生产**
   场景：短时间内生成游戏所需的全部UI图标和素材
   流程：UI风格定义 → batch_generate_images(图标集) → edit_image(迭代修改) → build

5. **宣传素材制作**
   场景：准备应用商店上架所需的全部宣传素材
   流程：截图准备 → generate_game_material(ICON+SCREENSHOT+PROMO) → upload_game_material → create_video_task(宣传视频)

6. **发布上线全流程**
   场景：从开发完成到 TapTap 上线的完整流程
   流程：i18n_extract → generate_game_material → upload_game_material → add_test_whitelist → 内测 → get_debug_feedbacks → publish_to_taptap

7. **快速原型验证**
   场景：1小时内从概念到可玩原型
   流程：概念 → search_3d_resource → generate_image → build → generate_test_qrcode → get_debug_feedbacks → 迭代

8. **NPC 角色语音系统**
   场景：为游戏中的 NPC 构建完整的语音系统
   流程：角色性格设计 → audition_voices_for_character(试听3候选) → confirm_character_voice → text_to_dialogue(批量台词) → build

9. **游戏氛围构建**
   场景：建立游戏的整体视听氛围
   流程：世界观设定 → text_to_music(主题曲) → batch_sound_effects(环境音) → generate_image(场景概念图) → search_3d_resource(3D场景) → build

10. **GameJam 极速开发**
    场景：48小时 GameJam 高效产出
    流程：brainstorm → bind_game_jam → 全速并行(视觉+音频+代码) → build → generate_test_qrcode → generate_game_material → publish_to_taptap

#### 2.4 工具编排原则

- **并行优先**：视觉和音频资产互不依赖，应并行生成
- **build 是验证点**：每完成一组资产整合后 build 验证，不要攒到最后
- **串行依赖链**：audition_voices → confirm_voice → text_to_dialogue 必须串行
- **seed 复现**：用 seed 参数确保可复现，迭代时只改 prompt 不改 seed
- **批量优于逐个**：能用 batch_generate_images / batch_sound_effects 时不要一个一个调
- **构建-测试闭环**：build → generate_test_qrcode → get_debug_feedbacks 形成快速反馈环

---

### 文件 3：`game-design/references/ai-era-design.md`（瘦身）

#### 保留内容

- 第 1 节「范式转变概览」— 三阶段演变模型
- 第 3 节「AI NPC 革命」— 设计理论部分
- 第 4 节「策划提示词工程最佳实践」— prompt 工程段落
- 第 5 节「策划的不可替代能力」— 能力定义
- 第 6 节「未来预判」— 方向参考

#### 删除内容

- 第 2 节「内容生成」表格中的第三方工具列举（Meshy、Tripo、Suno、Udio 等）→ 替换为一句交叉引用指向 mcp-toolkit.md
- 第 3 节中 Roblox Cube 3D 的整个子章节「Cube 3D 的战略意义」和「AI UGC 平台的策划挑战」→ 全删，时效性弱
- 第 4 节中「快速原型验证」「竞品分析」「数值平衡辅助」「本地化与对话生成」四个子场景描述 → 删除，mcp-toolkit.md 有更具体的工作流模板

#### 新增交叉引用

- 第 2 节保留位置加：`> 📌 实际可用的 AI 工具和完整工作流，详见 [references/mcp-toolkit.md](mcp-toolkit.md)`
- 第 4 节 prompt 段落加注释指向 mcp-toolkit.md 中的实战模板

#### 改动后结构

```
1. 范式转变概览（保留原文）
2. AI 内容生产能力矩阵（精简 + 交叉引用）
3. AI NPC 革命（保留原文）
4. 策划提示词工程最佳实践（保留精华）
5. AI 时代策划的不可替代能力（保留原文）
6. 未来预判（保留原文）
```

---

## 不改动的文件

以下参考文件不做改动（它们的策划理论内容与 MCP 工具无直接关系）：
- frameworks.md
- player-psychology.md
- loop-and-systems.md
- narrative-design.md
- economy-and-numbers.md
- level-design.md
- gdd-template.md
- design-checklist.md

---

## 验收标准

1. SKILL.md 的核心工作流 6 步中，每步都有对应的 MCP 工具提示
2. mcp-toolkit.md 包含完整的 5 大类工具速查 + 10 个工作流模板
3. 每个工作流模板包含具体的工具名、参数示例、注意事项
4. ai-era-design.md 保留了理论精华，删除了被 mcp-toolkit.md 取代的内容
5. 所有文件之间的交叉引用正确
