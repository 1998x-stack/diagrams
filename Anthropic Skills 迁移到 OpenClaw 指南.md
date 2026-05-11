# Anthropic Skills 迁移到 OpenClaw 指南

**创建日期:** 2026-05-07  
**来源:** https://github.com/anthropics/skills  
**目标:** OpenClaw Plugin Skills 系统

---

## 📊 对比分析

### Claude Code Skills 格式

```markdown
---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files...
license: Proprietary
---

# PDF Processing Guide

## Overview
...

## Quick Start
```python
from pypdf import PdfReader, PdfWriter
...
```
```

### OpenClaw Skills 格式

```markdown
---
name: browser-automation
description: Use when controlling web pages with the OpenClaw browser tool...
user-invocable: false
---

# Browser Automation

Use this skill when you need the `browser` tool for anything beyond a single page check.

## Operating Loop

1. Check browser state before acting...
```

---

## 🔑 核心差异

| 特性 | Claude Code | OpenClaw |
|------|-------------|----------|
| **元数据** | name, description, license | name, description, user-invocable |
| **触发方式** | 自动匹配关键词 | 工具调用 + 技能描述匹配 |
| **代码组织** | Markdown 内嵌代码示例 | 独立代码文件 + SKILL.md 指导 |
| **API 依赖** | Claude API | OpenClaw 工具系统 |
| **执行环境** | Claude Code 沙箱 | 本地 exec/process |

---

## 📦 迁移步骤

### 步骤 1: 克隆仓库

```bash
cd ~/Desktop/codes
git clone https://github.com/anthropics/skills.git anthropic-skills
```

✅ **已完成:** `/Users/xd/Desktop/codes/anthropic-skills/`

---

### 步骤 2: 查看结构

```
anthropic-skills/
├── skills/              # 17 个官方 Skills
│   ├── pdf/
│   │   └── SKILL.md    # 主要指导文档
│   ├── docx/
│   ├── xlsx/
│   └── ...
├── template/            # Skill 模板
├── spec/               # 规范文档
└── .claude-plugin/     # Claude 特定配置
```

---

### 步骤 3: 适配为 OpenClaw Skill

以 `pdf` skill 为例：

#### 3.1 创建目录

```bash
mkdir -p ~/.openclaw/plugin-skills/pdf-processor
```

#### 3.2 编写 SKILL.md

```markdown
---
name: pdf-processor
description: 处理 PDF 文件（读取、合并、拆分、提取文字/表格）
user-invocable: true
---

# PDF 处理技能

## 可用操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 读取 PDF | `pdf_reader.py <file>` | 提取文字内容 |
| 合并 PDF | `pdf_merge.py <out> <in1> <in2>...` | 合并多个 PDF |
| 拆分 PDF | `pdf_split.py <file>` | 拆分为单页 |
| 提取表格 | `pdf_table.py <file>` | 提取表格数据 |

## 依赖安装

```bash
pip install pypdf pdfplumber
```

## 使用示例

```bash
# 读取 PDF
python ~/.openclaw/plugin-skills/pdf-processor/pdf_reader.py document.pdf

# 合并 PDF
python ~/.openclaw/plugin-skills/pdf-processor/pdf_merge.py merged.pdf doc1.pdf doc2.pdf
```
```

#### 3.3 创建工具脚本

```python
#!/usr/bin/env python3
# ~/.openclaw/plugin-skills/pdf-processor/pdf_reader.py

import sys
from pypdf import PdfReader

def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: pdf_reader.py <file.pdf>")
        sys.exit(1)
    print(extract_text(sys.argv[1]))
```

---

## 🎯 推荐迁移顺序

### 第一阶段：文档处理（高优先级）

| Skill | 工作量 | 依赖 | 优先级 |
|-------|--------|------|--------|
| `pdf` | 中 | pypdf, pdfplumber | ⭐⭐⭐ |
| `xlsx` | 中 | openpyxl, pandas | ⭐⭐⭐ |
| `docx` | 低 | python-docx | ⭐⭐ |

### 第二阶段：开发工具（中优先级）

| Skill | 工作量 | 依赖 | 优先级 |
|-------|--------|------|--------|
| `claude-api` | 低 | requests | ⭐⭐ |
| `mcp-builder` | 高 | MCP SDK | ⭐ |
| `webapp-testing` | 高 | Playwright | ⭐ |

### 第三阶段：设计创意（低优先级）

| Skill | 工作量 | 依赖 | 优先级 |
|-------|--------|------|--------|
| `frontend-design` | 中 | 浏览器 | ⭐ |
| `algorithmic-art` | 中 | Pillow | ⭐ |
| `theme-factory` | 低 | - | ⭐ |

---

## 🛠️ 实现模板

### 标准 Skill 结构

```
~/.openclaw/plugin-skills/<skill-name>/
├── SKILL.md           # 必需：技能说明
├── tools/             # 可选：工具脚本
│   ├── tool1.py
│   └── tool2.sh
├── templates/         # 可选：模板文件
└── requirements.txt   # 可选：Python 依赖
```

### SKILL.md 模板

```markdown
---
name: <skill-name>
description: <一句话描述>
user-invocable: true/false
---

# <Skill 名称>

## 功能说明

<描述技能用途>

## 可用命令

| 命令 | 说明 |
|------|------|
| `command1` | 功能 1 |
| `command2` | 功能 2 |

## 依赖安装

```bash
pip install -r requirements.txt
```

## 使用示例

```bash
# 示例 1
command1 args

# 示例 2
command2 args
```
```

---

## 📋 迁移检查清单

- [ ] 克隆 anthropic-skills 仓库 ✅
- [ ] 阅读目标 Skill 的 SKILL.md
- [ ] 确定需要的 Python/Node 依赖
- [ ] 创建 OpenClaw Skill 目录
- [ ] 编写 SKILL.md（适配 OpenClaw 格式）
- [ ] 实现工具脚本（如需要）
- [ ] 测试功能
- [ ] 更新 TOOLS.md（如需要）

---

## 🔗 参考资源

- **Anthropic Skills:** https://github.com/anthropics/skills
- **OpenClaw Skills:** `~/.openclaw/plugin-skills/`
- **Skill Creator:** `~/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/skill-creator/SKILL.md`

---

## 🚀 快速开始：迁移 PDF Skill

```bash
# 1. 创建目录
mkdir -p ~/.openclaw/plugin-skills/pdf-processor

# 2. 安装依赖
pip install pypdf pdfplumber

# 3. 创建 SKILL.md
# (参考上方模板)

# 4. 创建工具脚本
cat > ~/.openclaw/plugin-skills/pdf-processor/pdf_reader.py << 'EOF'
#!/usr/bin/env python3
from pypdf import PdfReader
import sys
reader = PdfReader(sys.argv[1])
for page in reader.pages:
    print(page.extract_text())
EOF
chmod +x ~/.openclaw/plugin-skills/pdf-processor/pdf_reader.py

# 5. 测试
python ~/.openclaw/plugin-skills/pdf-processor/pdf_reader.py test.pdf
```

---

*文档由 AI 生成，最后更新：2026-05-07 16:55*
