# Layer 3: 工具层 (Tool Layer)

> UrhoX SCE 平台七层架构分析 — 第三层

---

## 1. 定义

工具层是平台的 **执行引擎**，包含 AI 可调用的全部工具——从代码构建到资产生成、从发布上架到调试反馈。它是 AI 决策层（L6）将意图转化为行动的唯一通道，也是连接开发者需求与引擎运行时（L4）的桥梁。

**核心隐喻**：如果 AI 决策层是"大脑"，工具层就是"双手"——大脑决定做什么，双手决定能做什么。工具层的能力边界就是整个平台的能力边界。

---

## 2. 设计目标

| 目标 | 说明 |
|------|------|
| **全流程覆盖** | 从编码到发布，一条工具链走通 |
| **异步友好** | 长耗时任务（模型生成、音乐生成）采用异步任务模式 |
| **格式标准化** | 工具输出可被其他工具直接消费 |
| **安全受控** | 高风险操作（发布）需要显式确认 |
| **幂等性** | 重复调用不产生副作用（build、查询类） |

---

## 3. 组成要素

### 3.1 MCP 工具全景（28 个工具）

#### A. 核心构建 (1 个)

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `build` | 构建项目 | entry, scriptsPath, multiplayer config | 构建结果、project_id |

**特殊地位**：build 是所有工具中最关键的一个——每次代码修改后必须调用，且是后续所有发布/测试工具的前置条件。

#### B. 视觉资产生成 (5 个)

| 工具 | 功能 | 模式 |
|------|------|------|
| `generate_image` | 文本→图片 | 单张，支持透明背景/参考图 |
| `batch_generate_images` | 批量生成图片 | 2-10 张并行 |
| `edit_image` | 编辑已有图片 | 基于指令修改 |
| `generate_game_material` | 生成发行素材 | ICON/SCREENSHOT/PROMO 等 7 种类型 |
| `upload_game_material` | 上传发行素材 | 单文件上传到 OSS + 更新 project.json |

#### C. 3D 模型生成 (2 个)

| 工具 | 功能 | 模式 |
|------|------|------|
| `create_tripo_model_task` | 创建 3D 模型任务 | text_to_model / image_to_model / multiview_to_model |
| `query_tripo_model_task` | 查询模型生成状态 | 轮询直到 success/failed |

**异步模式**：创建任务→返回 task_id→轮询状态（≥30s 间隔）→获取结果。

#### D. 音频生成 (5 个)

| 工具 | 功能 | 模式 |
|------|------|------|
| `text_to_music` | AI 音乐生成 | 简单模式/自定义模式（Suno） |
| `query_music_task` | 查询音乐生成状态 | 轮询 |
| `text_to_sound_effect` | AI 音效生成 | ElevenLabs，英文描述 |
| `batch_sound_effects` | 批量音效生成 | 多个音效并行 |
| `text_to_dialogue` | 角色台词生成 | 需先设置声音映射 |

#### E. 声音设计 (2 个)

| 工具 | 功能 | 说明 |
|------|------|------|
| `audition_voices_for_character` | 角色声音试听 | AI 生成 1-3 个候选声音 |
| `confirm_character_voice` | 确认声音选择 | 消耗 Voice Slot |

#### F. 视频生成 (4 个)

| 工具 | 功能 | 模式 |
|------|------|------|
| `create_video_task` | 创建视频任务 | text/first_frame/first_last_frame/multi_modal |
| `query_video_task` | 查询视频状态 | 轮询（≥120s 间隔） |
| `upload_asset` | 上传角色到可信资产库 | 绕过 Deepfake 检测 |
| `get_asset` / `list_assets` | 查询/列出资产 | 资产管理 |

#### G. 资源搜索 (1 个)

| 工具 | 功能 | 输出 |
|------|------|------|
| `search_game_resource` | 搜索预制资源库 | 465+ 预制件，1700+ 动画片段 |

#### H. 代码质量 (2 个)

| 工具 | 功能 | 协议 |
|------|------|------|
| `lua_lsp_client` | Lua LSP 请求 | 标准 LSP JSON-RPC |
| `i18n_extract` | 国际化字符串提取 | 扫描并生成 pending.json |

#### I. 发布与测试 (6 个)

| 工具 | 功能 | 风险等级 |
|------|------|---------|
| `generate_test_qrcode` | 生成测试二维码 | 低 |
| `add_test_whitelist` | 添加测试白名单 | 低 |
| `publish_to_taptap` | 正式发布到 TapTap | 🔴 高 |
| `list_tap_developers` | 查询开发者列表 | 低 |
| `get_ad_config` | 同步广告配置 | 中 |
| `bind_game_jam` | 绑定 GameJam 活动 | 低 |
| `get_debug_feedbacks` | 获取调试反馈 | 低 |

### 3.2 Skills (8 个)

| Skill | 功能 | 触发条件 |
|-------|------|---------|
| `materials` | PBR 材质系统指南 | 材质/纹理/贴图相关需求 |
| `convert-panorama` | 全景图转 Cubemap | 天空盒/天空球需求 |
| `import-fbx` | FBX 模型导入 | .fbx 文件导入 |
| `import-glb` | GLB/glTF 导入 | .glb/.gltf 文件导入 |
| `model-info` | 查询 MDL 模型信息 | 检查模型导入结果 |
| `anim-info` | 查询动画文件信息 | 检查动画导入结果 |
| `nvg-resolution-mode` | NanoVG 分辨率模式 | 项目含 NanoVG 调用时 |
| `skill-creator` | 创建新 Skill | 扩展平台能力 |

### 3.3 通用工具

| 类别 | 工具 | 说明 |
|------|------|------|
| 文件操作 | Read, Write, Edit | 代码读写修改 |
| 搜索 | Grep, Glob | 代码搜索、文件查找 |
| 终端 | Bash | 系统命令执行 |
| 代理 | Task (Explore/Plan/Bash/general-purpose) | 复杂任务委派 |
| 搜索引擎 | WebSearch | 网络信息检索 |

---

## 4. 能力边界

### 能做什么

| 能力 | 覆盖度 | 关键工具 |
|------|--------|---------|
| 代码编写与构建 | 95% | Edit, Write, build |
| 2D 图片资产生成 | 85% | generate_image, batch_generate_images |
| 3D 模型生成 | 70% | create_tripo_model_task, search_game_resource |
| 音乐/音效生成 | 80% | text_to_music, text_to_sound_effect |
| 角色配音 | 75% | audition_voices, text_to_dialogue |
| 视频生成 | 70% | create_video_task |
| 发行素材制作 | 90% | generate_game_material |
| 发布到应用商店 | 90% | publish_to_taptap |
| 代码质量检查 | 40% | lua_lsp_client（很少被调用） |
| 调试与测试 | 30% | generate_test_qrcode, get_debug_feedbacks |

### 不能做什么

| 限制 | 具体表现 |
|------|---------|
| 无可视化场景编辑器 | 不能拖拽放置对象，只能代码描述 |
| 无实时调试 | 不能设断点、看变量、单步执行 |
| 无热重载 | 每次修改都需要完整 build |
| 无性能分析 | 不能 profile CPU/GPU/内存 |
| 无版本回滚 | 构建/发布后不能一键回退 |
| 无协作功能 | 不支持多人协同开发 |
| 无自动化测试 | 不能编写和运行单元测试 |

---

## 5. 与其他层的关系

### 上游依赖

| 依赖层 | 关系 | 说明 |
|--------|------|------|
| L6 AI 决策层 | **被调用** | AI 决策何时调用哪个工具 |
| L2 规范层 | **受约束** | 规则 #1（build 后才能预览）约束工具调用顺序 |

### 下游依赖

| 依赖层 | 关系 | 说明 |
|--------|------|------|
| L4 运行时层 | **触发** | build 工具触发运行时编译和打包 |
| L5 安全层 | **受限** | 安全层限制工具的调用权限（如 publish 需显式确认） |
| L7 UI 层 | **产出** | 工具产出物（构建产物、QR 码）通过 UI 层展示 |

### 关键交互模式

```
L6 (Decision) ──选择工具──→ L3 (Tool) ──触发──→ L4 (Runtime)
                                ↓                     ↓
                           L5 (Security)          构建产物
                           权限检查                   ↓
                                              L7 (UI) 展示
```

---

## 6. 深度洞察

### 6.1 工具间的 12 处矛盾冲突

经过系统性分析，当前工具体系存在以下结构性冲突：

#### 冲突类型 A：工作流断裂

| 编号 | 冲突 | 说明 |
|------|------|------|
| A1 | generate_image → 代码引用 | 图片生成后路径不自动注入代码 |
| A2 | search_game_resource → 场景加载 | 搜索到资源后需手动编写加载代码 |
| A3 | create_tripo_model → 场景注册 | 模型生成后不自动添加到场景 |
| A4 | text_to_music → 音频播放 | 音乐生成后不自动配置到游戏 |

**根因**：资产生成工具和代码编写工具之间缺少 **自动胶水层**。每次资产生成后，AI 需要手动编写代码将资产引入场景，而这个步骤容易出错（路径拼写、资源类型匹配等）。

#### 冲突类型 B：语义边界模糊

| 编号 | 冲突 | 说明 |
|------|------|------|
| B1 | generate_image vs generate_game_material | 游戏图标该用哪个？两者都能生成 |
| B2 | text_to_sound_effect vs text_to_music | "环境音效循环"该用哪个？ |
| B3 | NanoVG (Skill) vs UI 组件 | 同一 UI 需求两个方案 |

**根因**：工具的职责描述有重叠区域，缺少明确的 **选择决策树**。

#### 冲突类型 C：隐式耦合

| 编号 | 冲突 | 说明 |
|------|------|------|
| C1 | publish_to_taptap 依赖 build + game_material + project.json | 3 个前置条件，任一缺失导致失败 |
| C2 | generate_test_qrcode 依赖 build + project.json 配置 | 需要先手动编辑配置文件 |
| C3 | text_to_dialogue 依赖 audition + confirm | 三步链式依赖 |

**根因**：工具间的前置条件缺少 **声明式依赖图**，全靠 AI 记忆或文档描述。

#### 冲突类型 D：安全级别不一致

| 编号 | 冲突 | 说明 |
|------|------|------|
| D1 | upload_game_material 无确认 vs publish_to_taptap 需显式确认 | 上传不可逆但无保护 |
| D2 | confirm_character_voice 消耗 slot 但无二次确认 | 资源消耗操作保护不足 |

#### 冲突类型 E：单向操作

| 编号 | 冲突 | 说明 |
|------|------|------|
| E1 | publish 无 unpublish | 发布后不能撤回 |
| E2 | confirm_voice 无 delete_voice | 声音创建后不能删除 |

### 6.2 诊断真空问题

**核心发现**：在 Edit（代码修改）和 build（构建验证）之间，存在一个 **诊断真空**。

```
Edit 文件 ──────[诊断真空]──────→ build ──→ 发现错误 ──→ 回头修复
     ^                                          |
     └──────────── 浪费一次完整 build ────────────┘
```

**lua_lsp_client 的尴尬**：
- 它具备在 Edit 后立即检查代码的能力（hover、diagnostic、references）
- 但当前 AI 决策层几乎不会主动调用它
- 结果是：简单的语法错误、类型错误要等到 build 才能发现
- 每次 build 耗时数十秒到数分钟，浪费大量时间

**四种解决方案对比**：

| 方案 | 实现 | 成本 | 效果 |
|------|------|------|------|
| A: Edit 内嵌诊断 | 修改 Edit 工具，自动返回 LSP 结果 | 高（需改工具） | 最好，零额外调用 |
| B: quick_check 新工具 | 新建轻量级检查工具 | 中（新工具） | 好，显式调用 |
| C: AI 策略优化 | 在 CLAUDE.md 中添加"Edit 后调用 LSP"规则 | 零（仅改提示词） | 可立即实施 |
| D: build 分层 | build 支持 check-only 模式 | 中（改 build） | 折中方案 |

**推荐**：先实施 C（零成本），同步开发 B（最佳长期方案）。

### 6.3 异步任务模式的一致性

平台有三类异步任务：

| 任务类型 | 创建工具 | 查询工具 | 轮询间隔 | 超时处理 |
|---------|---------|---------|---------|---------|
| 3D 模型 | create_tripo_model_task | query_tripo_model_task | ≥30s | 无自动超时 |
| 音乐 | text_to_music | query_music_task | 20s（内置轮询） | 10分钟自动超时 |
| 视频 | create_video_task | query_video_task | ≥120s | 无自动超时 |

**不一致**：
- 音乐有内置自动轮询，模型和视频没有
- 轮询间隔不统一（20s / 30s / 120s）
- 超时处理策略不同

### 6.4 batch 工具的覆盖不完整

| 单个 | 批量 | 状态 |
|------|------|------|
| generate_image | batch_generate_images | ✅ 有 |
| text_to_sound_effect | batch_sound_effects | ✅ 有 |
| upload_game_material | — | ❌ 缺失 |
| create_tripo_model_task | — | ❌ 缺失 |
| text_to_dialogue | — | ❌ 缺失（inputs 数组可视为内置批量） |

---

## 7. 风险评估

| 风险 | 等级 | 影响 | 缓解措施 |
|------|------|------|---------|
| 诊断真空导致 build 反复失败 | 🔴 高 | 开发效率降低 50%+ | 方案 C+B 组合 |
| 资产→代码断裂 | 🔴 高 | 每次资产生成后需手动集成 | 资产自动注册层 |
| 工具选择歧义 | 🟡 中 | AI 可能选错工具 | 工具选择决策树 |
| 异步任务无统一管理 | 🟡 中 | 多任务并行时难以追踪 | 任务管理器 |
| 单向操作不可逆 | 🟡 中 | 误操作无法回退 | 关键操作添加确认+回滚 |

---

## 8. 优化建议

### 8.1 消除诊断真空（P0 优先级）

**立即实施（零成本）**：在 CLAUDE.md 规则中添加：
```
Rule: Edit 后 LSP 检查
每次 Edit 修改 Lua 文件后，在调用 build 之前，
使用 lua_lsp_client 的 textDocument/diagnostic 方法
检查修改文件的语法和类型错误。
```

**中期实施**：开发 `quick_check` MCP 工具，接受文件路径列表，一次性返回所有诊断信息。

### 8.2 资产→代码自动胶水（P1 优先级）

为资产生成工具添加 `auto_integrate` 参数：

```json
{
  "tool": "generate_image",
  "params": {
    "prompt": "金币图标",
    "auto_integrate": {
      "variable_name": "coinTexture",
      "target_file": "scripts/main.lua",
      "usage": "Texture2D"
    }
  }
}
```

工具完成后自动在目标文件中插入：
```lua
local coinTexture = cache:GetResource("Texture2D", "生成的路径.png")
```

### 8.3 工具选择决策树（P1 优先级）

在工具描述中添加 `prefer_over` 和 `use_when` 字段：

```
generate_image:
  use_when: "需要自定义游戏内贴图、图标"
  prefer_over: generate_game_material when "非发行素材"

generate_game_material:
  use_when: "需要应用商店发行素材（ICON/SCREENSHOT/PROMO）"
  prefer_over: generate_image when "发行用途"
```

### 8.4 统一异步任务管理（P2 优先级）

统一所有异步任务的模式：
- 统一轮询间隔（建议 30s）
- 统一超时策略（建议 10 分钟）
- 统一结果格式：`{ status, progress_percent, result_path, preview_url }`

---

## 9. 总结

工具层是 UrhoX SCE 平台能力最丰富的层级，28 个 MCP 工具 + 8 个 Skills 覆盖了游戏开发的主要环节。其 **核心优势** 在于端到端的工具链覆盖（从编码到发布）和 AIGC 资产生成能力（图片/模型/音乐/视频）。其 **核心短板** 在于工具间的 12 处结构性冲突（工作流断裂、语义模糊、隐式耦合）、诊断真空问题、以及调试/测试工具的严重不足。

**一句话**：工具层"覆盖广但连接弱"——单个工具能力强大，但工具之间的协同需要大量人工（AI）干预来弥补。

---

## 10. 参考

- MCP 工具 schema 定义 — 所有 28 个工具的参数和输出规格
- CLAUDE.md — Skills 列表和触发条件
- CLAUDE.md — build 工具调用规则（Rule #1: Build After Every Change）
- 对话分析 — 诊断真空问题的发现和四方案设计

---

*[返回架构概览](index.md)*

