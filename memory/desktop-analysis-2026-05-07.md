# Desktop 文件系统分析报告

**分析时间:** 2026-05-07 16:20  
**分析范围:** `/Users/xd/Desktop/`  
**总计:** 273 个目录，172 个文件（顶层统计）

---

## 📊 概览

```
Desktop/
├── AgentRx/           # AI Agent 故障诊断研究项目
├── LLMAgentTraceAnalysis.pdf
├── codes/             # 代码项目集合
│   ├── claude-howto/      # GitHub 热门项目 (Claude Code 教程)
│   ├── claude-code/       # Claude Code 相关
│   ├── awesome-design-md/ # 设计资源
│   ├── mygithubs/         # 个人 GitHub 项目列表 (28 个)
│   └── test/              # 测试项目
└── work/              # 工作相关项目 (15 个子项目)
```

---

## 🗂️ 项目分类

### 1️⃣ **AI Agent 研究** (`AgentRx/`)
- **性质:** 研究项目 / 论文
- **内容:** AI Agent 执行轨迹故障诊断框架
- **论文:** https://arxiv.org/abs/2602.02475
- **数据集:** HuggingFace
- **状态:** 活跃开发中
- **关键文件:**
  - `run.py` - 主入口
  - `src/` - 源代码 (invariants, ir, judge, llm_clients, pipeline)
  - `trajectories/` - 测试轨迹数据
  - `data/` - 数据集 (Tau-bench, Magentic-One)

---

### 2️⃣ **开源项目** (`codes/`)

#### 🔥 claude-howto (GitHub #1 Trending)
- **定位:** Claude Code 结构化教程
- **状态:** 多语言版本 (EN/VN/ZH/UK)
- **特点:** 视觉教程 + 模板
- **目录结构完整:** 10 个章节 + 文档 + 脚本

#### 📚 mygithubs/ (28 个个人项目)
包括:
- CEQT, GaoKaoWeb, advisor-implementation
- alpha101_factory, arxiv2notion, autoresearch
- context_engineer, effective-harness
- llm-wiki, math_works, paper-graph
- rl_server, tool-project, voice-input-src
- 等...

---

### 3️⃣ **工作项目** (`work/`) - 15 个子项目

| 项目 | 类型 | 技术栈 |
|------|------|--------|
| `art_resource_search` | 资源搜索 | Python, Docker, ES |
| `feishu-bot` | 飞书机器人 | Python Bot |
| `game_bench_and_eval` | 游戏评测基准 | Python, Luna Graph |
| `game_resource_search` | 游戏资源搜索 | Python, FAISS |
| `hotpot_dspy_langgraph` | DSPy/LangGraph | Python, PyProject |
| `maker-game-design` | 游戏设计文档 | Markdown |
| `maker-github` | TapTap Maker | TypeScript, pnpm monorepo |
| `project-logs` | 项目日志分析 | Trajectory Analysis |
| `sce-tools-github` | SCE 工具 | Node.js |
| `tapmaker-local-scaffold` | 本地脚手架 | Lua, Templates |
| `titan-game-visual` | 游戏可视化 | Python, PPO |
| `urhox-bench` | 基准测试 | TypeScript, Vitest |
| `urhox-github` | UrhoX 游戏引擎 | C++, Lua |
| `urhox-official-res` | 引擎资源库 | Assets, Shaders |

---

## 🎯 核心项目深度分析

### AgentRx (AI Agent 诊断)
```
研究问题: AI Agent 执行失败的根本原因定位
方法论: 不变量合成 + 逐步验证 + LLM 判决
应用领域: Tau-bench, Flash, Magentic-One
输出: 10 类故障分类 + 可审计验证日志
```

### TapTap Maker (游戏创作平台)
```
愿景: 降低游戏制作门槛，让普通人也能做游戏
对标: Roblox + AI 生成
技术: AI 代码生成 + 资源生成
定位: 创作者平台，非专业工具
```

### UrhoX (游戏引擎)
```
基础: Urho3D 深度定制
特色: AI 编程友好，完整 Lua API
平台: Windows/iOS/Android/Web/Linux
渲染: BGFX 多 RHI 支持
```

---

## 📈 技术栈分布

| 语言 | 项目数 | 用途 |
|------|--------|------|
| Python | 8+ | AI/ML, 数据处理，Bot |
| TypeScript | 4+ | Web, 工具链 |
| Lua | 3+ | 游戏脚本 |
| C++ | 1 | 引擎核心 |
| Markdown | 大量 | 文档 |

---

## 🔍 观察与建议

### ✅ 优势
1. **项目聚焦:** AI Agent + 游戏技术 双主线清晰
2. **文档完善:** 大多数项目有 README/CLAUDE.md
3. **工程化:** 使用 Docker, pnpm monorepo 等现代工具
4. **开源意识:** GitHub 项目丰富，有 LICENSE/CONTRIBUTING

### ⚠️ 潜在问题
1. **版本冗余:** `game_resource_search` 有 v0/v12/v13/v14 多版本
2. **备份分散:** `claude-resume.sh` 在多个项目重复
3. **日志积累:** 多个项目有 `logs/` 但未统一清理策略

### 💡 建议
1. 考虑将 `game_resource_search` 多版本合并或归档旧版本
2. 提取公共脚本到共享工具库
3. 建立统一的日志轮转策略

---

## 📁 关键文件索引

| 路径 | 用途 |
|------|------|
| `AgentRx/run.py` | Agent 诊断主入口 |
| `codes/claude-howto/INDEX.md` | 教程索引 |
| `work/maker-github/package.json` | TapTap Maker 配置 |
| `work/urhox-github/CLAUDE.md` | 引擎开发指南 |
| `work/project-logs/trajectory-analysis/` | 轨迹分析数据 |

---

**分析完成时间:** 2026-05-07 16:25  
**下次更新:** 建议每月或项目结构重大变更时
