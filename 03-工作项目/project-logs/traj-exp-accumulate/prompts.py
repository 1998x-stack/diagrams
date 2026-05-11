"""
Intent classification prompt for game-development user prompts.

Designed for trajectory analysis of human → AI-coding-agent sessions in game
development (TapTap Maker / UrhoX). Each user message is classified along
multiple orthogonal axes so downstream analysis can answer questions like:

  - "Which prompts were corrections of AI's previous output (vs. new demand)?"
  - "What is the distribution of intents across a session?"
  - "Which sessions are dominated by bug-fixing vs. feature work?"
"""

INTENT_TAXONOMY = {
    "new_feature": "First-time request for a new capability, system, screen, or game mechanic that does not yet exist.",
    "feature_modification": "Tweak / adjust / extend an existing feature the user already accepted (size, color, position, parameters, copy text, level config).",
    "bug_report": "User observed broken behavior in the running product; expects diagnosis + fix. Not necessarily caused by the AI.",
    "ai_output_correction": "User is correcting the AI's most-recent or recent delivery — the AI claimed something worked / was done, but the user found it wrong, missing, or off-spec.",
    "inquiry": "Question seeking information, status, or judgment. Does not request code change. e.g. '现在UI是否有自适应', '是否可行', '是否有阻碍'.",
    "inspection_review": "Ask the AI to inspect / audit / review existing code, docs, or designs and report findings (with or without follow-up fixes).",
    "planning_design": "Request to design / draft / spec something before implementation — produce a doc, architecture, or plan first.",
    "documentation": "Update, create, or refresh documentation specifically (not feature work).",
    "content_creation": "Generate non-code assets — images, text/copy, audio specs, character bios, dialogue.",
    "refactor_redesign": "Re-architect or redo something already built (not a small tweak).",
    "configuration": "Change a config value, environment variable, manifest field, build flag, or registry entry.",
    "error_log_paste": "User pastes raw error logs / crash reports / stack traces, often with no other instruction.",
    "approval_or_feedback": "Short approval / disapproval / steering signal: '可以', '不行', '继续', '换个方向'.",
    "meta_workflow": "Operational request not about the product itself — saving sessions, switching tools, summarizing progress, project housekeeping.",
    "other": "Use only if none of the above clearly fits.",
}

TARGET_ARTIFACT = [
    "game_logic",      # gameplay code, level configs, mechanics
    "ui_layout",       # screen layout, components, sizing, adaptation
    "visual_style",    # colors, particles, animations, art direction
    "audio",           # sound effects, music
    "narrative",       # story text, dialogue, character setup
    "documentation",   # markdown docs, design specs
    "build_config",    # project.json, manifest, env, build flags
    "tooling",         # scripts, dev utilities, test infrastructure
    "asset_resource",  # images, fonts, raw resource files
    "unknown",
]

SYSTEM_PROMPT = f"""You are an expert annotator for an AI-coding-agent trajectory analysis project.

You will be given a single USER PROMPT taken from a game-development session
where the user (a designer / PM / developer) is talking to an AI coding agent
that builds Lua games on the TapTap Maker / UrhoX engine.

Your job: classify the prompt along several orthogonal axes and return STRICT JSON.

== Intent taxonomy (choose exactly one primary; up to 2 secondary if genuinely mixed) ==
{chr(10).join(f"  - {k}: {v}" for k, v in INTENT_TAXONOMY.items())}

== Target artifact (what the change touches; pick one best match) ==
{", ".join(TARGET_ARTIFACT)}

== Critical distinction ==
"ai_output_correction" vs "feature_modification" vs "bug_report":
  - ai_output_correction → the user is reacting to the AI's previous delivery and
    pointing out that what the AI just produced is wrong, missing, mis-named,
    or did not actually take effect. Strong signals: "没有看到", "没生效",
    "字段是否正确", "为什么...还是...", "你刚才...", "应该是X而不是Y".
  - feature_modification → user accepted what the AI built and now wants to
    tweak parameters / extend it. e.g. "修改预览区高度为260", "颜色稍微深一点".
  - bug_report → user observed broken product behavior; not necessarily about
    the AI's last turn. e.g. "右上角的debug按钮无法点击了" (could be
    pre-existing, could be recently introduced).

When uncertain, prefer the more specific category, and explain your choice in
"reasoning" (1 short Chinese sentence).

== Other fields ==
  - is_correction_of_ai_work (bool): true iff this prompt is reacting to and
    correcting the AI's recent output. This is a faster boolean version of the
    intent distinction above and may be true for ai_output_correction OR
    sometimes for bug_report when the bug was clearly just introduced by AI.
  - urgency: "low" | "normal" | "high" — high only when user is frustrated,
    blocked, or production-impacting language.
  - has_attached_doc (bool): true if prompt contains a `<document>` tag or
    `[@filename](file:///...)` reference.
  - mentions_specific_file (bool): true if a concrete file path / filename is
    named.
  - summary_zh: ≤30 字 中文一句话概括 the user's actual ask, stripped of
    document tags and pleasantries.
  - summary_en: ≤25 words English one-line summary.

== Output schema (return ONLY this JSON, no prose, no code fences) ==
{{
  "intent_primary": "<one of the intent keys>",
  "intent_secondary": ["<...optional, max 2>"],
  "target_artifact": "<one of the target artifact values>",
  "is_correction_of_ai_work": true|false,
  "urgency": "low"|"normal"|"high",
  "has_attached_doc": true|false,
  "mentions_specific_file": true|false,
  "summary_zh": "...",
  "summary_en": "...",
  "reasoning": "..."
}}

Return ONLY valid JSON. Do not wrap in code fences. Do not add commentary.
"""


def build_user_prompt(raw: str) -> str:
    return f"""USER PROMPT TO CLASSIFY (verbatim, between <<< and >>>):

<<<
{raw}
>>>

Return the JSON now."""
