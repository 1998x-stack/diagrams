# Traj-Evolver: Trajectory → Skill Extraction Pipeline

**Date:** 2026-04-20
**Status:** Design — awaiting user review

## Goal

Turn real Claude Code session trajectories (`traj-data-new/{wzp,zzj}/*.traj`) into reusable ECC-format skill folders that capture both generic development patterns and personal workflow overlays for two game projects:

- **wzp** (脑力大冒险) — casual puzzle game collection, 73 sessions, content-production heavy
- **zzj** (超时空要塞) — TapTap platform integration, 5 sessions (one 3.5-day marathon), search-heavy

Final deliverable: two self-contained skill folders at `project-logs/evolved/wzp/` and `project-logs/evolved/zzj/`, each layered as:

- `skills/` — generic patterns (auto-triggered)
- `commands/` — personal workflows (user-invoked)
- `agents/` — complex multi-step processes

## Lifecycle Mapping

The pipeline implements the Scan → Select → Prompt/Mutate → Validate/Solidify → Event lifecycle:

| Phase | Implementation | Output |
|---|---|---|
| Scan | `traj_miner.py` reads all `.traj` files | raw pattern candidates |
| Select | statistical thresholds (frequency, distinctness) | `patterns.json` top-K |
| Prompt/Mutate | `traj_enricher.py` — per-pattern LLM call | YAML-frontmatter instincts |
| Validate/Solidify | linting + `instinct-cli.py evolve` clustering | evolved skill/command/agent candidates |
| Event | `evolve_skills.py` copies to repo-local `evolved/` | ECC skill folders |

## Architecture

```
traj-evolver/
├── scripts/
│   ├── traj_miner.py        # Stage 1: deterministic pattern mining
│   ├── traj_enricher.py     # Stage 2: LLM enrichment → instincts
│   └── evolve_skills.py     # Stage 3: wraps instinct-cli evolve
├── prompts/
│   └── enrich.md            # cached LLM prompt prefix
├── tests/
│   ├── fixtures/            # synthetic .traj files
│   ├── test_miner.py
│   ├── test_enricher.py
│   └── test_evolve.py
├── Makefile
└── README.md
```

Data flow:

```
traj-data-new/{wzp,zzj}/*.traj
        ↓ [Scan]  traj_miner.py  (pure Python)
traj-evolver/patterns/{wzp,zzj}/patterns.json
        ↓ [Select] threshold filtering
traj-evolver/patterns/{wzp,zzj}/selected.json
        ↓ [Prompt/Mutate] traj_enricher.py  (Sonnet 4.6 via Claude API)
traj-evolver/instincts/{wzp,zzj}/*.md
        ↓ [Validate/Solidify] evolve_skills.py → instinct-cli.py evolve --generate
~/.claude/homunculus/projects/traj-{wzp,zzj}/evolved/
        ↓ [Event] copy to repo
project-logs/evolved/{wzp,zzj}/
  ├── skills/<name>/SKILL.md
  ├── commands/<name>.md
  ├── agents/<name>.md
  └── README.md
```

Each stage writes to disk for resumability and debugging. wzp and zzj run as independent parallel pipelines.

## Stage 1: traj_miner.py (Scan + Select)

Pure Python, no LLM. Reads all `.traj` files for one project and emits a structured pattern index.

### CLI

```bash
python3 traj-evolver/scripts/traj_miner.py \
  --input-dir traj-data-new/wzp \
  --output-dir traj-evolver/patterns/wzp
```

### Pattern families (5)

1. **Tool-sequence n-grams** (bigrams, trigrams, 4-grams)
   - Sequence of `action.tool_name` values across consecutive steps
   - Co-indexed with user-intent keywords from the preceding user message
   - Example: `(Read → Grep → Edit)` × 47, correlated with "fix"/"bug" keywords

2. **Phase-transition patterns**
   - Sequences of phase labels from the `phases[]` array
   - Drift markers (editing without verification) grouped by context
   - Cycle shapes: localization→editing→verification→submission

3. **Task-shape patterns**
   - A "task shape" = user message + tool sequence until next user message
   - Clustered by Jaccard similarity (tool sequence) + TF-IDF keyword overlap (user message)
   - Minimum cluster size: 3 task shapes

4. **User-correction signals**
   - Heuristic: turn N edits file X → turn N+1 user message matches correction keywords (不对, wrong, revert, undo, 应该, actually) → turn N+2 re-edits X
   - High-signal anti-patterns

5. **Project-specific tool fingerprints**
   - Frequency distribution of MCP tools (`mcp__mkr__*`, `mcp__sce-urhox__*`, platform-specific calls)
   - Distinctness = this-project-frequency / (this + other project frequency)

### Selection thresholds

Configurable, with defaults:

| Parameter | Default | Purpose |
|---|---|---|
| min_frequency | 3 | Drop rare patterns |
| top_k_per_family | 20 | Bound total patterns |
| distinctness_weight | 0.5 | Balance frequency × distinctness |
| min_sessions | 2 | Pattern must span multiple sessions |

### Output schema

```json
{
  "project": "wzp",
  "generated_at": "2026-04-20T10:56:00+08:00",
  "stats": {"sessions": 73, "steps": 15085, "tool_calls": 10071},
  "patterns": [
    {
      "id": "ngram_read_grep_edit",
      "family": "tool_sequence",
      "sequence": ["Read", "Grep", "Edit"],
      "frequency": 47,
      "session_count": 23,
      "distinctness": 0.62,
      "keywords": ["fix", "bug"],
      "examples": [
        {"session": "uuid", "turn": 3, "step_range": [12, 18]}
      ]
    }
  ]
}
```

## Stage 2: traj_enricher.py (Prompt/Mutate + Validate)

LLM turns structured patterns into named, documented instincts.

### CLI

```bash
# Default: auto-select first available provider (Qwen preferred)
python3 traj-evolver/scripts/traj_enricher.py \
  --patterns-file traj-evolver/patterns/wzp/patterns.json \
  --traj-dir traj-data-new/wzp \
  --output-dir traj-evolver/instincts/wzp \
  --config traj-evolver/config.yaml

# Force Anthropic provider
python3 traj-evolver/scripts/traj_enricher.py --provider anthropic ...
```

### Approach

One LLM call per pattern. Benefits: small context, parallelizable, cost-predictable.

**Dual-provider support** via config YAML. Default provider: **Qwen** (lower cost); fallback: Anthropic.

- **Temperature:** 0
- **Concurrency:** asyncio, default 5 concurrent requests
- **Prompt caching:** Anthropic path uses cached prefix; Qwen path does not (no cache support) but batches efficiently

### Provider config (`traj-evolver/config.yaml`)

```yaml
enricher:
  # Provider order: first available wins. Override with --provider flag.
  providers:
    - name: qwen
      enabled: true
      api_key_env: DASHSCOPE_API_KEY
      base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
      model: qwen3.6-plus
      extra_body:
        enable_thinking: false    # required by qwen3.6-plus for non-streaming
      sdk: openai                 # OpenAI-compatible SDK

    - name: anthropic
      enabled: true
      api_key_env: ANTHROPIC_API_KEY
      model: claude-sonnet-4-6
      sdk: anthropic
      prompt_caching: true

  temperature: 0
  concurrency: 5
  max_retries: 3
  retry_backoff_sec: 2
```

**Selection logic:**
1. If `--provider <name>` CLI flag is given, use that provider.
2. Otherwise, iterate `providers[]` in order: first one whose `enabled: true` AND whose `api_key_env` resolves to a non-empty value wins.
3. If none available, fail fast with a clear error listing expected env vars.

Default order puts Qwen first, so `DASHSCOPE_API_KEY` being set is sufficient to select it.

### Provider abstraction

A thin `EnricherClient` interface with two implementations:

- `QwenClient` — uses `openai` SDK pointed at DashScope `base_url`. Sends `extra_body={"enable_thinking": false}` on every call.
- `AnthropicClient` — uses `anthropic` SDK. Sends `cache_control` breakpoints on the system prompt for the shared prefix.

Both expose: `async def complete(system: str, user: str) -> str`. Caller is provider-agnostic.

### Prompt structure

**Cached prefix** (one per project, ~2k tokens):
- Project overview (wzp or zzj characteristics)
- Instinct schema documentation
- YAML frontmatter format specification
- Tone/style guidelines (one-sentence action, evidence bullets)
- Two few-shot example instincts

**Dynamic suffix** (per pattern, ~500-1000 tokens):
- The pattern JSON object
- 2-3 concrete examples pulled from raw `.traj` files (truncated to ~500 chars each)
- Request to emit YAML-frontmatter instinct

### Output format

```yaml
---
id: wzp-read-grep-edit-debug-flow
trigger: "when fixing bugs in wzp lua scripts"
confidence: 0.75
domain: debugging
source: trajectory-import
scope: project
project_name: wzp-脑力大冒险
evolved_from_pattern: ngram_read_grep_edit
---

# Read → Grep → Edit Debug Flow

## Action
Start bug investigation by reading the reported file, then grep the codebase for related symbols before editing.

## Evidence
- Pattern occurred 47 times across 73 sessions
- Consistently precedes successful edits when user message contains "fix" or "bug"
- Distinctness score 0.62 (concentrated in wzp)
```

### Deterministic confidence calibration

LLM writes text only; confidence comes from mining stats:

| Frequency | Confidence |
|---|---|
| ≥ 20 | 0.85 |
| 10-19 | 0.75 |
| 5-9 | 0.65 |
| 3-4 | 0.55 |

### Validate/Solidify gates (before writing)

Each LLM output must pass:
- YAML frontmatter parses
- Required fields present: `id`, `trigger`, `confidence`, `domain`, `scope`
- `id` matches `^[a-z0-9-]+$` and ≤ 60 chars
- Action section: 1-2 sentences
- Evidence section: ≥ 2 bullets

Failures → `instincts/{project}/_rejected/<pattern_id>.md` + `error_log.txt` with reason. Never silently dropped.

### Cost estimate

~60 patterns × 2 projects × 3k tokens avg = ~360k tokens total.

- **Qwen (default):** qwen3.6-plus pricing ≈ ¥0.004/1k input, ¥0.012/1k output → well under ¥10 (~$1.50).
- **Anthropic fallback:** Sonnet 4.6 with ~80% cache hit rate → under $5.

## Stage 3: evolve_skills.py (Event)

Thin wrapper around existing `instinct-cli.py evolve --generate`, adapted for batch trajectory input.

### CLI

```bash
python3 traj-evolver/scripts/evolve_skills.py \
  --instincts-dir traj-evolver/instincts/wzp \
  --project-id traj-wzp \
  --project-name "wzp-脑力大冒险" \
  --output-dir project-logs/evolved/wzp
```

### Steps

1. **Stage instincts into a synthetic homunculus project**
   - Create `~/.claude/homunculus/projects/traj-wzp/instincts/inherited/`
   - Copy Stage 2 instincts into `inherited/` (not `personal/`, since these are imported)
   - Register `traj-wzp` in `~/.claude/homunculus/projects.json`

2. **Invoke instinct-cli evolve**
   - Set `CLAUDE_PROJECT_DIR` to the synthetic project root
   - Run `python3 instinct-cli.py evolve --generate` as subprocess
   - CLI clusters instincts into skill/command/agent candidates
   - Output lands in `~/.claude/homunculus/projects/traj-wzp/evolved/`

3. **Copy evolved output to repo**
   - `~/.claude/homunculus/projects/traj-wzp/evolved/*` → `project-logs/evolved/wzp/*`
   - Write `README.md` documenting provenance (sessions, date range, pattern counts, usage)

### Final output layout

```
project-logs/evolved/wzp/
├── README.md
├── skills/              # generic patterns (auto-triggered)
│   ├── wzp-read-grep-edit-debug/SKILL.md
│   ├── wzp-mkr-iterative-patching/SKILL.md
│   └── wzp-todo-driven-workflow/SKILL.md
├── commands/            # personal workflows (user-invoked)
│   ├── wzp-fix-lua-bug.md
│   └── wzp-add-minigame.md
└── agents/              # complex multi-step processes
    └── wzp-content-compliance-checker.md
```

zzj mirrors this structure. Expected zzj-specific output: heavier `grep-search` skills, `tap-platform-integration` commands, a `long-session-drift-guard` agent.

## Testing

### Unit tests

- `test_miner.py` — tiny synthetic `.traj` fixture (3 sessions, ~50 steps). Asserts each of the 5 pattern families detects correctly.
- `test_enricher.py` — mocks both `QwenClient` and `AnthropicClient`. Verifies prompt construction, YAML validation, rejection path, confidence calibration, provider auto-selection (Qwen-first), `enable_thinking=false` passed on Qwen calls, `cache_control` set on Anthropic calls.
- `test_evolve.py` — mocks `instinct-cli.py` subprocess. Verifies staging directory layout and file copy.

### End-to-end smoke test

- Run full pipeline on 3 smallest real `.traj` files from wzp
- Assertions:
  - `patterns.json` non-empty
  - ≥ 3 instincts generated
  - `evolve --generate` returns 0
  - `evolved/wzp/` contains ≥ 1 skill
- CI uses pre-recorded enrichment outputs (no API key needed)

### Manual validation gates

Between stages, human inspects:
1. `patterns/{project}/patterns.json` — meaningful patterns surfaced?
2. `instincts/{project}/*.md` — well-written, evidence-grounded?
3. `evolved/{project}/` — coherent clustered skills?

### Makefile targets

```makefile
mine:       # Stage 1 only
enrich:     # Stage 2 only (requires ANTHROPIC_API_KEY)
evolve:     # Stage 3 only
pipeline:   # all three, per PROJECT={wzp,zzj}
test:       # pytest traj-evolver/tests/
```

### Quality metrics

Reported after each run:
- Patterns mined per project
- Instincts generated / rejected ratio
- Evolved skill/command/agent counts
- Token cost (from API response metadata)

## Documentation & Handoff

### traj-evolver/README.md

1. Quick start (set `DASHSCOPE_API_KEY` for Qwen default, or `ANTHROPIC_API_KEY` for Sonnet; then 3 commands to run the pipeline)
2. Pipeline stages with Scan → Select → Prompt/Mutate → Validate/Solidify → Event framing
3. Configuration reference (thresholds, models, paths)
4. Troubleshooting (missing both API keys, Qwen `enable_thinking` errors, Anthropic cache miss, no patterns, rejection failures, path resolution)
5. Extending (new pattern families, adding a new provider in `config.yaml`, new projects)
6. Provenance & reproducibility (manifest.json per stage records inputs, config, timestamp, and git SHA when available; deterministic Stage 1; bounded-variance Stage 2)

### Per-project evolved/{wzp,zzj}/README.md

- Contributing sessions (IDs, date range)
- Pattern-family breakdown
- How to apply skills in future sessions
- Known gaps (e.g., verification phase underrepresented)

## Non-Goals

- **Not** replacing the live instinct system — this is a one-shot batch pipeline for historical data
- **Not** continuous learning — static snapshot of skills from fixed trajectory set
- **Not** modifying `instinct-cli.py` — treating it as read-only dependency
- **Not** cross-project generalization — wzp and zzj run independently; no global instinct merging

## Open Questions

None at this time; all major decisions resolved during brainstorm:
- Output location: `project-logs/evolved/{wzp,zzj}/` (ECC format, in-repo) ✓
- Skill flavor: layered — generic patterns + personal overlays ✓
- Approach: C (statistical mining + LLM enrichment + native evolve) ✓

## Next Step

Invoke `superpowers:writing-plans` skill to produce a detailed implementation plan.
