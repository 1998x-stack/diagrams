# Superpowers Skill 安装报告

**安装时间:** 2026-05-07 17:25  
**来源:** https://github.com/obra/superpowers  
**版本:** 5.1.0

---

## ✅ 安装完成

**位置:** `~/.openclaw/plugin-skills/superpowers/`

**仓库:** `/Users/xd/Desktop/codes/superpowers/`

---

## 📚 包含技能 (14 个)

### 🎯 核心方法论 (3 个)

| 技能 | 说明 |
|------|------|
| `test-driven-development` | 测试驱动开发 (TDD) - 红/绿/重构循环 |
| `systematic-debugging` | 系统化调试方法 |
| `verification-before-completion` | 完成前验证 |

### 📋 计划与执行 (4 个)

| 技能 | 说明 |
|------|------|
| `brainstorming` | 需求头脑风暴，设计确认 |
| `writing-plans` | 编写实现计划 |
| `executing-plans` | 执行计划 |
| `dispatching-parallel-agents` | 并行子代理任务分发 |

### 🔧 Git 工作流 (2 个)

| 技能 | 说明 |
|------|------|
| `using-git-worktrees` | Git worktree 隔离开发 |
| `finishing-a-development-branch` | 完成开发分支流程 |

### 🤝 代码协作 (3 个)

| 技能 | 说明 |
|------|------|
| `requesting-code-review` | 请求代码审查 |
| `receiving-code-review` | 接收/进行代码审查 |
| `writing-skills` | 编写新技能 |

### 🧠 元技能 (2 个)

| 技能 | 说明 |
|------|------|
| `using-superpowers` | Superpowers 使用指南 |
| `subagent-driven-development` | 子代理驱动开发 |

---

## 🚀 核心工作流程

```
┌─────────────────┐
│  1. Brainstorm  │ ← 明确需求，确认设计
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Write Plan  │ ← 编写实现计划
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Git Worktree│ ← 创建隔离分支
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. TDD Cycle   │ ← 红/绿/重构循环
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. Debug       │ ← 系统化调试 (如需要)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. Verify      │ ← 完成前验证
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  7. Finish      │ ← 完成分支
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  8. Code Review │ ← 请求审查
└─────────────────┘
```

---

## 📖 TDD 核心原则

### 铁律

> **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

### 红 - 绿-重构循环

```
RED    → 写失败测试
  ↓
GREEN  → 最小代码通过
  ↓
REFACTOR → 重构优化
  ↓
(重复)
```

### 关键规则

- ❌ **禁止**先写实现代码
- ❌ **禁止**看旧代码参考
- ✅ **必须**看着测试失败
- ✅ **必须**最小化实现

---

## 💡 使用场景

### 开始新功能
1. 触发 `brainstorming` - 明确需求
2. 触发 `writing-plans` - 编写计划
3. 触发 `using-git-worktrees` - 创建分支

### 实现功能
4. 触发 `test-driven-development` - TDD 循环
5. 遇到问题触发 `systematic-debugging` - 调试

### 完成开发
6. 触发 `verification-before-completion` - 验证
7. 触发 `finishing-a-development-branch` - 完成
8. 触发 `requesting-code-review` - 审查

---

## 📁 文件结构

```
~/.openclaw/plugin-skills/superpowers/
├── SKILL.md                     # 总览文档
├── brainstorming/
│   └── SKILL.md
├── test-driven-development/
│   └── SKILL.md
├── systematic-debugging/
│   └── SKILL.md
├── writing-plans/
│   └── SKILL.md
├── executing-plans/
│   └── SKILL.md
├── using-git-worktrees/
│   └── SKILL.md
├── finishing-a-development-branch/
│   └── SKILL.md
├── requesting-code-review/
│   └── SKILL.md
├── receiving-code-review/
│   └── SKILL.md
├── verification-before-completion/
│   └── SKILL.md
├── writing-skills/
│   └── SKILL.md
├── dispatching-parallel-agents/
│   └── SKILL.md
├── subagent-driven-development/
│   └── SKILL.md
└── using-superpowers/
    └── SKILL.md
```

---

## 🔗 相关资源

- **GitHub:** https://github.com/obra/superpowers
- **作者:** Jesse Vincent (@obra)
- **许可证:** MIT
- **版本:** 5.1.0

---

## 📊 OpenClaw Skills 总数

| 类别 | 数量 |
|------|------|
| 文档处理 | 3 (xlsx/docx/pptx) |
| 内部沟通 | 1 (internal-comms) |
| 创意设计 | 2 (theme-factory/algorithmic-art) |
| **Superpowers** | **1 (14 skills)** |
| 系统自带 | 54+ |
| **总计** | **65+** |

---

*报告生成时间：2026-05-07 17:25*
