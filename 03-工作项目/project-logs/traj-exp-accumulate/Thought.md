# Thought: Gene Accumulation Pipeline

## 1. What is a Gene?

A Gene is a **reusable behavioral pattern** extracted from game-development AI agent trajectories. It encodes:
- **When** to activate (signals + preconditions)
- **How** to act (strategy steps)
- **How to verify** (validation checks)
- **Where it came from** (provenance: sessions, turns, evidence)

Genes are organized by **intent category** (from INTENT_TAXONOMY), accumulate across sessions, and strengthen when the same pattern appears in multiple sessions.

## 2. Gene Generation Process (What the LLM Does)

### Input Data (per session)
1. **`examples/{project}/{hash}.json`** — Intent-classified prompts with:
   - `intent_primary`, `intent_secondary`, `target_artifact`
   - `is_correction_of_ai_work`, `urgency`
   - `summary_zh`, `summary_en`, `reasoning`
2. **`traj-data-new/{project}/{hash}.traj`** — Full trajectory with:
   - Per-step: `tool_name`, `phase`, `status`, `execution_time`, `usage`
   - Per-turn: `thinking`, `thought`, `action.args`, `observation`
   - Session metadata: `duration_sec`, `model`, `project`
3. **Existing `plugins/*/index.md`** — Already-generated genes for overlap detection

### Analysis Steps (What the LLM reasons about)
1. **Intent distribution** — Count intents, find dominant categories
2. **Sequence patterns** — Consecutive same-intent runs (visual polish x9, level injection x4)
3. **Per-turn behavioral fingerprint** — Steps count, tool mix, edit count, build count, error rate
4. **Phase transitions** — How the session moves between localization/editing/verification
5. **Failure patterns** — Repeated bug reports, escalation sequences
6. **Session rhythm** — Doc checkpoint cadence, phase boundary markers
7. **Overlap check** — Compare discovered patterns against existing genes in index.md

### Output
- **New genes**: Append to `plugins/{intent_category}/genes.json`
- **Enhanced genes**: Update existing gene's `_provenance` (add session_hash, update evidence)
- **Updated indexes**: Regenerate `plugins/*/index.md`

## 3. Gene Enhancement (Merge Logic)

When a new session exhibits a pattern similar to an existing gene:

```
Existing gene (1 session)     New session evidence
         ↓                            ↓
    Compare signals + preconditions
         ↓
    Match? ──yes──→ ENHANCE: add session_hash to provenance,
         │                   broaden preconditions if needed,
         │                   update evidence with new turn/prompt refs,
         │                   increment session_count
         │
         └──no───→ CREATE NEW GENE
```

**Enhancement signals** (when to merge vs. create):
- Same `intent_primary` + similar `target_artifact`
- Overlapping `signals_match` tags (>50% overlap)
- Similar preconditions (same user behavior pattern, different specific content)

**When NOT to merge** (create new gene instead):
- Different intent categories
- Same intent but different workflow structure (e.g., both are feature_modification but one is visual polish, other is audio binding)
- Different `category` (workflow vs. diagnostic)

## 4. Deduplication Mechanism

**Session-level dedup** using `_processed.json`:

```json
{
  "processed_sessions": {
    "9dc56f96": {
      "project": "wzp",
      "processed_at": "2026-04-22T12:00:00Z",
      "genes_created": 12,
      "genes_enhanced": 0
    },
    "374e4eb7": {
      "project": "wzp",
      "processed_at": "2026-04-22T13:00:00Z",
      "genes_created": 7,
      "genes_enhanced": 4
    }
  }
}
```

**Runner logic**:
1. Load `_processed.json`
2. Scan `examples/{wzp,zzj}/*.json` for all sessions
3. Skip sessions already in `_processed.json`
4. Process remaining sessions one by one
5. After each successful run, update `_processed.json`

## 5. Dual Pipeline Architecture

Two independent pipelines, same logic, different LLM backends:

```
traj-exp-accumulate/
├── examples/{wzp,zzj}/*.json       ← shared input (intent classifications)
├── traj-data-new/{wzp,zzj}/*.traj  ← shared input (full trajectories, via symlink/path)
├── plugins/                         ← manually curated reference genes
│   ├── _schema.json
│   └── {intent_category}/genes.json + index.md
│
├── claude-acc/                      ← Pipeline A: Claude Sonnet 4.6
│   ├── prompt.py                    # Build the LLM prompt
│   ├── run.py                       # Orchestrate: dedup + invoke claude -p
│   ├── _processed.json              # Session-level dedup state
│   └── plugins/                     # Independent output
│       └── {intent_category}/genes.json + index.md
│
├── opencode-acc/                    ← Pipeline B: Qwen 3.6 Plus
│   ├── prompt.py                    # Build the LLM prompt
│   ├── run.py                       # Orchestrate: dedup + invoke opencode run
│   ├── _processed.json              # Session-level dedup state
│   └── plugins/                     # Independent output
│       └── {intent_category}/genes.json + index.md
│
├── prompts.py                       ← shared: INTENT_TAXONOMY
├── gen_index.py                     ← shared: regenerate index.md
└── Thought.md                       ← this document
```

## 6. Prompt Design (Core)

The prompt instructs the LLM agent to:

1. **Read** the session's .json file (intent classifications)
2. **Read** the session's .traj file using tools (Bash/Read/Grep) to extract:
   - Session metadata (duration, model, project)
   - Per-turn summary: step count, tool distribution, phase, errors
   - Key behavioral indicators (audio gen, build frequency, error recovery)
3. **Read** existing `plugins/*/index.md` to check for pattern overlaps
4. **Analyze** patterns: intent sequences, behavioral fingerprints, failure chains
5. **Generate** genes following `_schema.json` format
6. **Write** output to `plugins/{intent_category}/genes.json` (append or enhance)
7. **Regenerate** index.md for affected categories

Key prompt elements:
- INTENT_TAXONOMY definition
- Gene schema with field descriptions
- Example gene (from manually curated plugins/)
- Existing index.md content (for overlap detection)
- Explicit instructions: "If pattern overlaps existing gene, ENHANCE it (add session_hash, update evidence). If new, CREATE new gene."

## 7. Invocation

### Claude pipeline
```bash
cd claude-acc && python3 run.py
# Internally runs:
# claude -p "$(python3 prompt.py --session {hash} --project {project})" --model sonnet-4-6
```

### OpenCode pipeline
```bash
cd opencode-acc && python3 run.py
# Internally runs:
# opencode run "$(python3 prompt.py --session {hash} --project {project})"
# Model configured as alibaba-cn/qwen3.6-plus
```

## 8. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pipeline independence | Separate plugins/ per pipeline | Compare LLM quality without interference |
| Input data | json + traj (LLM reads via tools) | LLM needs behavioral data; tools let it explore 35K-line traj selectively |
| Dedup granularity | Session-level | Simple, reliable; LLM handles gene-level overlap in prompt |
| Gene overlap detection | LLM reads index.md before generating | LLM is better at semantic similarity than rule-based matching |
| Output format | Direct file writes by LLM | Natural workflow — same as manual process, just automated |
| Index regeneration | gen_index.py (shared script) or inline by LLM | Ensures consistent index format |
