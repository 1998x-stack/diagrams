"""
Build the prompt for gene generation via `opencode run`.

Usage:
    python3 prompt.py --session 9dc56f96 --project wzp
    # Prints the prompt to stdout; used by run.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = Path(__file__).resolve().parent / "plugins"
SCHEMA_PATH = ROOT / "plugins" / "_schema.json"

INTENT_TAXONOMY = {
    "new_feature": "First-time request for a new capability, system, screen, or game mechanic that does not yet exist.",
    "feature_modification": "Tweak / adjust / extend an existing feature the user already accepted.",
    "bug_report": "User observed broken behavior in the running product; expects diagnosis + fix.",
    "ai_output_correction": "User is correcting the AI's most-recent or recent delivery.",
    "inquiry": "Question seeking information, status, or judgment. Does not request code change.",
    "inspection_review": "Ask the AI to inspect / audit / review existing code, docs, or designs.",
    "planning_design": "Request to design / draft / spec something before implementation.",
    "documentation": "Update, create, or refresh documentation specifically.",
    "content_creation": "Generate non-code assets — images, text/copy, audio specs, character bios, dialogue.",
    "refactor_redesign": "Re-architect or redo something already built (not a small tweak).",
    "error_log_paste": "User pastes raw error logs / crash reports / stack traces.",
    "configuration": "Change a config value, environment variable, build flag, or registry entry.",
    "meta_workflow": "Operational request not about the product itself — saving sessions, switching tools, summarizing progress.",
    "other": "Use only if none of the above clearly fits.",
}


def load_existing_index(plugins_dir: Path) -> str:
    parts = []
    for idx in sorted(plugins_dir.rglob("index.md")):
        rel = idx.relative_to(plugins_dir)
        content = idx.read_text(encoding="utf-8")
        parts.append(f"=== {rel} ===\n{content}")
    if not parts:
        return "(No existing genes yet — this is a fresh run.)"
    return "\n\n".join(parts)


def load_schema() -> str:
    if SCHEMA_PATH.exists():
        return SCHEMA_PATH.read_text(encoding="utf-8")
    return "(Schema not found — use the example gene format below.)"


def load_example_gene() -> str:
    ref_dir = ROOT / "plugins" / "feature_modification" / "genes.json"
    if ref_dir.exists():
        genes = json.loads(ref_dir.read_text(encoding="utf-8"))
        if genes:
            return json.dumps(genes[0], ensure_ascii=False, indent=2)
    return "(No example available.)"


def build_prompt(session: str, project: str) -> str:
    json_path = ROOT / "examples" / project / f"{session}.json"
    traj_path = ROOT.parent / "traj-data-new" / project / f"{session}.traj"
    existing_index = load_existing_index(PLUGINS_DIR)
    schema = load_schema()
    example_gene = load_example_gene()
    taxonomy_str = "\n".join(f'  - {k}: {v}' for k, v in INTENT_TAXONOMY.items())
    plugins_abs = str(PLUGINS_DIR)

    return f"""你是一位轨迹分析专家。你的任务是分析一个游戏开发AI Agent的会话轨迹，从中提取可复用的行为模式（"基因/Gene"）。

## 目标
分析会话 `{session}`（项目: `{project}`），生成按意图分类组织的Gene对象，写入plugins目录。

## 输入文件（使用工具读取）
1. **意图分类数据**: `{json_path}`
   - 包含已分类的用户prompts，含 intent_primary, target_artifact, summaries
2. **完整轨迹**: `{traj_path}`
   - 包含完整的agent轨迹（文件可能很大，请用python/jq提取摘要，不要一次性读取整个文件）

## 分析步骤
1. 读取 .json 文件，理解意图分布和prompt序列
2. 用工具从 .traj 文件中提取per-turn摘要：
   - 每个turn: 步骤数、工具分布、phase、编辑数、build数、错误数
   - 会话级: 总时长、总步骤、工具频率、phase分布
3. 识别可复用的行为模式：
   - 连续同intent序列（如连续5+次视觉微调）
   - 工作流链（如设计文档→实现→打磨→文档检查点）
   - 失败模式（重复bug报告、升级序列）
   - 会话节奏（文档检查点频率、阶段边界）
   - 内容创建工作流（生成→预览→应用）
4. 检查已有基因是否有重叠
5. 生成新基因或增强已有基因

## 意图分类体系
{taxonomy_str}

## Gene Schema
{schema}

## Gene示例
{example_gene}

## 已有基因索引（用于重叠检测）
{existing_index}

## 输出规则 — 去重优先工作流

**在创建任何新gene之前，必须先用以下流程检查是否已有相似的gene：**

### 步骤A：Grep检查重叠
对于每个你想创建的gene模式，先运行：
```bash
grep -r "intent:{{category}}" {plugins_abs}/*/genes.json
grep -r "{{关键signal}}" {plugins_abs}/*/genes.json
```
其中 `{{关键signal}}` 是最具辨识性的signal标签（如 `consecutive_same_intent`、`sfx_name_in_prompt`、`stacktrace_in_prompt`）。

### 步骤B：如果grep匹配到 — 增强，不要新建
1. 读取匹配到的 `{plugins_abs}/{{category}}/genes.json`
2. 找到signals重叠的那个gene对象
3. 用Edit工具只更新 `_provenance` 部分：
   - 在 `session_hashes` 数组中追加 `"{session}"`
   - 在 `evidence` 中追加新session的turn/prompt引用
   - 设置或递增 `session_count`
   - 更新 `turn_range`，格式: `"旧hash:T01-T03, {session}:T05-T08"`
4. 如果新session揭示了额外的signals或preconditions，可以追加到 `signals_match` 和 `preconditions`——但不要删除已有的。

### 步骤C：如果grep无匹配 — 创建新gene
1. 如果 `{plugins_abs}/{{category}}/genes.json` 已存在，先Read，然后向JSON数组追加新gene。
2. 如果文件不存在，创建为包含你新gene的JSON数组: `[ {{gene}} ]`
3. 如果分类目录不存在，先创建: `mkdir -p {plugins_abs}/{{category}}`

### 步骤D：全部写入完成后
运行: `python3 {ROOT}/gen_index.py --plugins-dir {plugins_abs}`

## Gene ID 命名规范
- 格式: `gene_{{intent_prefix}}_{{pattern_name}}`
- 前缀: fm=feature_modification, nf=new_feature, br=bug_report, aoc=ai_output_correction, inq=inquiry, pd=planning_design, doc=documentation, cc=content_creation, cfg=configuration, mw=meta_workflow, elp=error_log_paste, meta=session_meta

## 重要规则
- 每个gene必须包含schema中所有必填字段
- preconditions和strategy用中文
- title_zh中文，title_en英文
- _provenance必须包含session_hashes, turn_range, prompt_indices, evidence
- prompt数少于3个的session不要生成gene（除非模式非常突出）
- 质量优先：每个session 3-5个高质量gene比10个弱gene更好
- 输出目录: `{plugins_abs}`

现在开始分析会话并生成基因。先读取 .json 文件。"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    print(build_prompt(args.session, args.project))


if __name__ == "__main__":
    main()
