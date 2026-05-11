# Anthropic 官方 Skills 清单

**来源:** https://github.com/anthropics/skills  
**更新日期:** 2026-05-07  
**总数:** 17 个官方 Skills

---

## 📚 完整清单

| # | Skill 名称 | 功能描述 | 适用场景 |
|---|-----------|----------|----------|
| 1 | `algorithmic-art` | 算法艺术生成 | 创意编程、生成艺术 |
| 2 | `brand-guidelines` | 品牌指南管理 | 企业品牌规范 |
| 3 | `canvas-design` | Canvas 设计 | 视觉设计、原型 |
| 4 | `claude-api` | Claude API 调用 | API 集成开发 |
| 5 | `doc-coauthoring` | 文档协作编写 | 团队文档协作 |
| 6 | `docx` | Word 文档处理 | 文档生成/编辑 |
| 7 | `frontend-design` | 前端设计 | UI/UX 设计 |
| 8 | `internal-comms` | 内部沟通 | 企业通讯、邮件 |
| 9 | `mcp-builder` | MCP 服务器构建 | 工具开发 |
| 10 | `pdf` | PDF 文件处理 | PDF 读取/生成 |
| 11 | `pptx` | PowerPoint 处理 | 演示文稿生成 |
| 12 | `skill-creator` | Skill 创建工具 | 自定义 Skill 开发 |
| 13 | `slack-gif-creator` | Slack GIF 生成 | 团队协作娱乐 |
| 14 | `theme-factory` | 主题生成器 | UI 主题设计 |
| 15 | `web-artifacts-builder` | Web 构件构建 | 前端组件开发 |
| 16 | `webapp-testing` | Web 应用测试 | 自动化测试 |
| 17 | `xlsx` | Excel 表格处理 | 数据分析/报表 |

---

## 🔧 分类整理

### 📄 文档处理类
- `pdf` - PDF 文件读写
- `docx` - Word 文档处理
- `xlsx` - Excel 表格处理
- `pptx` - PowerPoint 演示文稿
- `doc-coauthoring` - 文档协作

### 🎨 设计创意类
- `algorithmic-art` - 算法艺术
- `canvas-design` - Canvas 设计
- `frontend-design` - 前端设计
- `theme-factory` - 主题生成
- `brand-guidelines` - 品牌指南

### 🛠️ 开发工具类
- `claude-api` - API 调用
- `mcp-builder` - MCP 服务器
- `skill-creator` - Skill 开发
- `web-artifacts-builder` - Web 构件
- `webapp-testing` - Web 测试

### 💼 企业应用类
- `internal-comms` - 内部沟通
- `slack-gif-creator` - Slack 娱乐

---

## 📥 安装方法

### 方法 1: 直接克隆

```bash
cd ~/Desktop/codes/claude-howto/skills
git clone https://github.com/anthropics/skills.git anthropic-official-skills
```

### 方法 2: 下载单个 Skill

```bash
# 示例：下载 PDF 处理 Skill
curl -L "https://github.com/anthropics/skills/archive/refs/heads/main.zip" \
  -o skills.zip
unzip skills.zip "skills-main/skills/pdf/*"
```

### 方法 3: OpenClaw Skills 安装

OpenClaw 使用不同的 Skills 系统 (AgentSkills)，需要适配：

```bash
# 查看已安装 skills
ls ~/.openclaw/plugin-skills/

# 安装新 skill (需要 SKILL.md 格式)
cd ~/.openclaw/plugin-skills/
git clone <skill-repo-url>
```

---

## ⚠️ OpenClaw 兼容性说明

### Claude Code Skills vs OpenClaw Skills

| 特性 | Claude Code | OpenClaw |
|------|-------------|----------|
| 格式 | Markdown + 配置 | SKILL.md + Python/Node |
| 安装 | `.claude/skills/` | `~/.openclaw/plugin-skills/` |
| 触发 | 自动匹配 | 工具调用 |
| API | Claude API | 自定义工具 |

### 适配建议

1. **文档处理类** (`pdf`, `docx`, `xlsx`, `pptx`)
   - 可使用现有 Python 库 (PyPDF2, python-docx, openpyxl)
   - 封装为 OpenClaw 工具

2. **设计创意类** (`algorithmic-art`, `canvas-design`)
   - 需要前端环境支持
   - 可考虑生成 HTML 文件

3. **开发工具类** (`mcp-builder`, `webapp-testing`)
   - MCP 协议可复用
   - Web 测试可用 Playwright

---

## 🔗 相关资源

- **GitHub:** https://github.com/anthropics/skills
- **官方文档:** https://claude.com/blog/skills
- **Skills 市场:** https://skillsmp.com/
- **Awesome Claude Skills:** https://awesomeclaudeskills.com/

---

## 💡 推荐优先安装

根据 OpenClaw 使用场景，推荐优先适配：

| 优先级 | Skill | 理由 |
|--------|-------|------|
| ⭐⭐⭐ | `pdf` | 文档处理高频需求 |
| ⭐⭐⭐ | `xlsx` | 数据分析常用 |
| ⭐⭐ | `docx` | 文档生成需求 |
| ⭐⭐ | `claude-api` | API 调用参考 |
| ⭐ | `skill-creator` | 学习 Skill 开发 |

---

## 🚀 快速开始

```bash
# 1. 克隆官方仓库
git clone https://github.com/anthropics/skills.git /tmp/anthropic-skills

# 2. 查看 PDF skill 结构
ls -la /tmp/anthropic-skills/skills/pdf/

# 3. 阅读 SKILL.md 格式
cat /tmp/anthropic-skills/skills/pdf/SKILL.md
```

---

*文档由 AI 生成，最后更新：2026-05-07 16:45*
