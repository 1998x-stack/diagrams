# content_creation — Gene Index

**Gene count:** 1

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_cc_audio_generate_audition_integrate` | Audio Generate → Audition → Integrate Pipeline | workflow | 1x: 9dc56f96 | `intent:content_creation`, `target:audio`, `generate_sfx_keywords` |

---

## `gene_cc_audio_generate_audition_integrate`

**音频生成→试听→集成工作流** / Audio Generate → Audition → Integrate Pipeline

Category: `workflow`

**Signals:**
- `intent:content_creation`
- `target:audio`
- `generate_sfx_keywords`
- `audition_before_apply`
- `reference_existing_asset`
- `cn_generate_listen_keywords`

**Preconditions:**
- 用户请求生成新的音效或BGM资源，通常指定风格/目标用户/参考资源。
- 用户期望先试听再决定应用，工作流为：生成→放入测试环境→试听→选择→应用。
- 平台具备音频生成能力（如 text_to_music、batch_sound_effects MCP工具）。

**Evidence:** 4 content_creation prompts: generate SFX (batch_sound_effects) → reference-based generation → organize into test category '气泡1' → generate BGM (text_to_music). Clear audition-first workflow.

---
