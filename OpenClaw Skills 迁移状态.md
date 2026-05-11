# OpenClaw Skills 迁移状态

**更新日期:** 2026-05-07 17:00  
**目标:** 将 Anthropic 官方 Skills 迁移到 OpenClaw

---

## 📊 当前状态

### OpenClaw 已安装 Skills (54 个)

**位置:** `/Users/xd/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/`

| 分类 | Skills | 数量 |
|------|--------|------|
| 📝 笔记 | apple-notes, apple-reminders, bear-notes, notion, obsidian, things-mac | 6 |
| 💬 通讯 | discord, himalaya, imsg, slack, bluebubbles | 5 |
| 🎵 媒体 | sag (TTS), sonoscli, spotify-player, songsee, openai-whisper* | 5 |
| 🎮 游戏 | gog, goplaces | 2 |
| 🏠 智能家居 | openhue, eightctl | 2 |
| 🛠️ 工具 | 1password, canvas, clawhub, gifgrep, xurl, peekaboo, camsnap | 7 |
| 💼 生产力 | github, gh-issues, trello, taskflow, summarize | 5 |
| 🌐 网络 | blogwatcher, web 相关 | 2 |
| 🎥 视频 | video-frames, session-logs | 2 |
| 📞 通话 | voice-call, wacli | 2 |
| 🌤️ 其他 | weather, healthcheck, node-connect, oracle, ordercli, etc. | 18 |

**已启用:** `browser-automation` (链接到插件)

---

## 🎯 Anthropic Skills 迁移优先级

### 第一阶段：高优先级 ⭐⭐⭐

| Anthropic Skill | OpenClaw 对应 | 迁移状态 | 说明 |
|-----------------|---------------|----------|------|
| `pdf` | `nano-pdf` | ✅ 已有 | 基础 PDF 处理 |
| `xlsx` | ❌ 无 | 🔄 待迁移 | Excel 处理 |
| `docx` | ❌ 无 | 🔄 待迁移 | Word 文档 |

### 第二阶段：中优先级 ⭐⭐

| Anthropic Skill | OpenClaw 对应 | 迁移状态 | 说明 |
|-----------------|---------------|----------|------|
| `pptx` | ❌ 无 | 🔄 待迁移 | PowerPoint |
| `claude-api` | ❌ 无 | 🔄 待迁移 | API 调用封装 |
| `doc-coauthoring` | `summarize` | ⚠️ 部分 | 文档协作 |

### 第三阶段：低优先级 ⭐

| Anthropic Skill | OpenClaw 对应 | 迁移状态 | 说明 |
|-----------------|---------------|----------|------|
| `algorithmic-art` | `canvas` | ⚠️ 部分 | 算法艺术 |
| `frontend-design` | ❌ 无 | 🔄 待迁移 | 前端设计 |
| `mcp-builder` | ❌ 无 | 🔄 待迁移 | MCP 服务器 |
| `webapp-testing` | `browser-automation` | ⚠️ 部分 | Web 测试 |
| `skill-creator` | `skill-creator` | ✅ 已有 | Skill 开发工具 |
| `web-artifacts-builder` | ❌ 无 | 🔄 待迁移 | Web 构件 |
| `theme-factory` | ❌ 无 | 🔄 待迁移 | 主题生成 |
| `brand-guidelines` | ❌ 无 | 🔄 待迁移 | 品牌指南 |
| `canvas-design` | `canvas` | ⚠️ 部分 | Canvas 设计 |
| `internal-comms` | `slack` | ⚠️ 部分 | 内部沟通 |
| `slack-gif-creator` | `gifgrep` | ⚠️ 部分 | GIF 生成 |

---

## 📋 迁移计划

### 立即执行（本周）

- [ ] **xlsx** - Excel 处理 (openpyxl + pandas)
- [ ] **docx** - Word 文档处理 (python-docx)
- [ ] **pptx** - PowerPoint 处理 (python-pptx)

### 后续执行（本月）

- [ ] **frontend-design** - 前端设计模板
- [ ] **web-artifacts-builder** - Web 构件生成
- [ ] **mcp-builder** - MCP 服务器模板

### 可选执行（按需）

- [ ] **algorithmic-art** - 算法艺术生成
- [ ] **theme-factory** - 主题生成器
- [ ] **brand-guidelines** - 品牌指南模板

---

## 🛠️ 实现方案

### 方案 A: 直接复用 Python 库

```bash
# 文档处理三剑客
pip install pypdf python-docx openpyxl python-pptx pdfplumber
```

**优点:** 简单快速，功能完整  
**缺点:** 需要封装为 OpenClaw 工具

### 方案 B: 使用现有 Skills 扩展

```bash
# 扩展 nano-pdf
cp -r ~/.nvm/.../skills/nano-pdf ~/.openclaw/plugin-skills/document-tools
```

**优点:** 基于现有代码  
**缺点:** 需要阅读原有实现

### 方案 C: 参考 Anthropic 实现

```bash
# 阅读 Anthropic 的 SKILL.md
cat ~/Desktop/codes/anthropic-skills/skills/pdf/SKILL.md
```

**优点:** 学习官方最佳实践  
**缺点:** 需要适配 OpenClaw 格式

---

## 📁 文件位置

| 类型 | 路径 |
|------|------|
| OpenClaw 系统 Skills | `/Users/xd/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/` |
| 用户插件 Skills | `~/.openclaw/plugin-skills/` |
| Anthropic 原始 Skills | `~/Desktop/codes/anthropic-skills/skills/` |
| 迁移文档 | `~/Desktop/codes/anthropic-skills/` |

---

## 🚀 快速开始：创建 xlsx Skill

```bash
# 1. 创建目录
mkdir -p ~/.openclaw/plugin-skills/xlsx-processor

# 2. 安装依赖
pip install openpyxl pandas

# 3. 创建 SKILL.md
cat > ~/.openclaw/plugin-skills/xlsx-processor/SKILL.md << 'EOF'
---
name: xlsx-processor
description: 处理 Excel 文件（读取、写入、数据分析）
user-invocable: true
---

# Excel 处理技能

## 可用命令

| 命令 | 说明 |
|------|------|
| `xlsx_reader.py <file>` | 读取 Excel 内容 |
| `xlsx_writer.py <data>` | 创建 Excel 文件 |
| `xlsx_analyze.py <file>` | 数据分析 |

## 依赖

```bash
pip install openpyxl pandas
```

## 示例

```bash
python ~/.openclaw/plugin-skills/xlsx-processor/xlsx_reader.py data.xlsx
```
EOF

# 4. 创建工具脚本
cat > ~/.openclaw/plugin-skills/xlsx-processor/xlsx_reader.py << 'EOF'
#!/usr/bin/env python3
import sys
from openpyxl import load_workbook

wb = load_workbook(sys.argv[1], read_only=True)
for sheet in wb.sheetnames:
    print(f"=== {sheet} ===")
    ws = wb[sheet]
    for row in ws.iter_rows(values_only=True):
        print('\t'.join(str(c) for c in row))
EOF
chmod +x ~/.openclaw/plugin-skills/xlsx-processor/xlsx_reader.py
```

---

## 📊 迁移进度

```
Anthropic Skills (17 个)
├── ✅ 已有对应 (4 个)   24%
├── ⚠️ 部分对应 (5 个)   29%
└── 🔄 待迁移 (8 个)     47%

优先级排序:
🔴 高优先级 (3 个): xlsx, docx, pptx
🟡 中优先级 (2 个): claude-api, frontend-design
🟢 低优先级 (3 个): 其他创意类
```

---

## 📞 下一步

1. **本周:** 实现 xlsx + docx + pptx 文档处理三件套
2. **下周:** 实现 claude-api 和 frontend-design
3. **本月:** 完成所有高优先级 Skills 迁移

---

*文档由 AI 生成，最后更新：2026-05-07 17:00*
