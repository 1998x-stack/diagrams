# UrhoX SCE 平台架构深度分析

> 基于对 UrhoX SCE（星火编辑器）AI 辅助游戏开发平台的系统性审计与架构分析。

---

## 平台定位

UrhoX SCE 是 TapTap 星火编辑器团队打造的 **AI-Coding-Friendly 游戏引擎平台**。其核心理念是：通过 AI 辅助（Claude Code + MCP 工具链），让开发者以 Lua 脚本快速构建可发布到 TapTap 的游戏。

平台不仅仅是一个游戏引擎，而是一个 **"AI 驱动的端到端游戏开发与发行平台"**，覆盖从概念构思到应用商店发布的全流程。

---

## 七层架构模型

经过系统性分析，平台架构可抽象为以下七个层次：

```
┌─────────────────────────────────────────────────────┐
│  Layer 7: 用户界面层 (UI Layer)                      │
│  Preview / QR Code / TapTap 发布界面                  │
├─────────────────────────────────────────────────────┤
│  Layer 6: AI 决策层 (AI Decision Layer)               │
│  CLAUDE.md / Rules #0-#14 / 任务路由 / 文档映射        │
├─────────────────────────────────────────────────────┤
│  Layer 5: 安全层 (Security Layer)                     │
│  三级安全模型 / 路径隔离 / 内容审核                      │
├─────────────────────────────────────────────────────┤
│  Layer 4: 运行时层 (Runtime Layer)                    │
│  Lua 5.4 / UrhoX 引擎 / NanoVG / Box2D / Yoga         │
├─────────────────────────────────────────────────────┤
│  Layer 3: 工具层 (Tool Layer)                         │
│  28 MCP Tools / 8 Skills / LSP / Build Pipeline       │
├─────────────────────────────────────────────────────┤
│  Layer 2: 规范层 (Specification Layer)                │
│  Rules #0-#14 / 脚手架 / 编码约定 / Gotchas            │
├─────────────────────────────────────────────────────┤
│  Layer 1: 知识层 (Knowledge Layer)                    │
│  engine-docs/ / examples/ / .emmylua/ / templates/    │
└─────────────────────────────────────────────────────┘
```

### 层间依赖关系

```
L7 (UI)
 ↑ 构建产物展示
L6 (AI Decision) ──读取──→ L1 (Knowledge)
 ↑ 决策驱动         ↑ 规则约束
L5 (Security) ←──横切──→ L3 (Tool) ──调用──→ L4 (Runtime)
                         ↑ 规范指导
                    L2 (Specification)
```

**关键洞察**：
- L6（AI 决策层）是整个平台的 **中枢神经**，协调所有其他层
- L1（知识层）是 L6 的 **唯一知识来源**，其质量直接决定 AI 产出质量
- L5（安全层）以 **横切关注点** 形式渗透到每一层
- L3（工具层）和 L4（运行时层）之间存在 **诊断真空**（Edit → build 之间无验证）

---

## 各层详细分析

| # | 层级 | 文件 | 核心发现 |
|---|------|------|---------|
| 1 | [知识层](01_knowledge_layer.md) | engine-docs/, examples/, .emmylua/ | 文档体系完整但碎片化，gotcha 系统严重不足 |
| 2 | [规范层](02_specification_layer.md) | Rules #0-#14, scaffolds, gotchas | 规则设计精巧但编号混乱，密度不均衡 |
| 3 | [工具层](03_tool_layer.md) | 28 MCP Tools, 8 Skills, LSP | 覆盖广但存在 12 处工具间冲突 |
| 4 | [运行时层](04_runtime_layer.md) | Lua 5.4, UrhoX, NanoVG, Box2D | 双 UI 系统过渡期，API 绑定差异需文档兜底 |
| 5 | [安全层](05_security_layer.md) | 三级安全模型 | 多层防御但粒度不一致 |
| 6 | [AI 决策层](06_ai_decision_layer.md) | CLAUDE.md, 任务路由, 文档映射 | 决策链路完整但缺少反馈闭环 |
| 7 | [用户界面层](07_ui_layer.md) | Preview, QR Code, TapTap | 产出物可视化但调试支持薄弱 |

---

## 平台核心指标

### 游戏开发生命周期覆盖度

| 阶段 | 覆盖度 | 关键工具/能力 |
|------|--------|-------------|
| 概念设计 | 30% | AI 对话辅助，无专用设计工具 |
| 美术资产 | 85% | generate_image, create_tripo_model, search_game_resource |
| 音频资产 | 80% | text_to_music, text_to_sound_effect, text_to_dialogue |
| 编码实现 | 90% | Scaffolds, Examples, LSP, AI Code Generation |
| 构建打包 | 95% | build MCP tool |
| 测试调试 | 40% | Preview, QR Code, get_debug_feedbacks |
| 发布上架 | 90% | publish_to_taptap, generate_game_material |
| 运营迭代 | 25% | get_debug_feedbacks, cloud variables |

### 工具生态规模

| 类别 | 数量 | 说明 |
|------|------|------|
| MCP 工具 | 28+ | 核心开发工具链 |
| Skills | 8 | 领域特化能力 |
| 脚手架 | 4 | 项目起手模板 |
| 示例代码 | 22 | 覆盖主要游戏类型 |
| 编码规则 | 14+ | Rules #0 至 #14（含子规则） |
| 事件类型 | 177 | .emmylua/Events.d.lua 定义 |

---

## 十大优先改进建议

| 优先级 | 改进项 | 影响层级 | 预期收益 |
|--------|-------|---------|---------|
| P0 | 引入 Edit → build 之间的轻量级诊断（消除诊断真空） | L3, L6 | 减少 30-50% 的 build 失败 |
| P0 | 统一 gotcha 系统（从 1 个文件扩展到 10-12 个） | L1, L2 | 减少重复犯错率 |
| P1 | 规则编号体系重构（消除 #9.1/#9.5/#9.6 等混乱编号） | L2, L6 | AI 决策准确度提升 |
| P1 | 工具间数据流自动化（消除格式孤岛） | L3 | 减少手动粘贴步骤 |
| P1 | 增加缺失规则：错误处理、Update 性能、状态管理 | L2 | 代码质量基线提升 |
| P2 | build 工具分层：quick_check + full_build | L3 | 开发迭代速度提升 2-3x |
| P2 | 资源生成结果自动注册到场景 | L3, L6 | 减少断点操作 |
| P2 | 安全层粒度统一（消除 upload vs publish 权限不一致） | L5 | 降低误操作风险 |
| P3 | 测试/调试工具链增强（断点、变量检查、热重载） | L3, L7 | 调试效率提升 |
| P3 | 概念设计阶段工具化（GDD 模板、原型草图工具） | L3 | 覆盖完整生命周期 |

---

## 文档约定

- **分析方法**：基于平台公开架构信息、工具 schema 定义、规则体系的系统性审计
- **评估标准**：功能完整性、一致性、可维护性、开发者体验
- **文档结构**：每层分析均遵循统一的 11 节结构（定义、目标、组成、能力边界、层间关系、洞察、风险、优化建议、总结、参考）

---

*分析时间: 2026-04*
*平台版本: 基于当前可观察的架构状态*

