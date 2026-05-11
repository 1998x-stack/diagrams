# traj-viz v2 Design Spec

**Date:** 2026-04-14
**Status:** Approved
**Scope:** New .traj schema, converter, backend + frontend updates for conversation-first trajectory viewer

## 1. Problem Statement

The v1 traj-viz system uses a flat trajectory array where all steps are at the same level. This loses the multi-turn conversation structure inherent in Claude Code sessions (user prompts trigger agent tool-call sequences). The v1 schema also lacks token usage data, extended thinking content, structured action/observation objects, and per-step status.

The v2 update introduces a multi-turn grouped `.traj` schema inspired by the SWE-agent trajectory format, a new converter for production JSONL data, and a conversation-first viewer.

## 2. Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Schema shape | Multi-turn grouped | Matches natural Claude Code conversation flow |
| Token data | Full per-step breakdown | Enables cost analysis and cache efficiency insights |
| Thinking blocks | Preserve as separate field | Valuable for reasoning analysis; drop base64 signatures |
| Viewer focus | Conversation-first | Design around user→agent turn flow, not flat timeline |
| Compatibility | Clean break | v2 schema in traj-data-new/, v1 stays in traj-data/ |
| Build order | Schema → Converter → Backend → Frontend | Natural data-flow order |

## 3. V2 .traj Schema

### 3.1 Top-level Structure

```json
{
  "schema_version": "2.0",
  "conversation_id": "<session-uuid>",
  "agent": {
    "name": "claude-code",
    "model": "<model-name from first assistant message>",
    "environment": "taptap-maker",
    "tool_protocol": "claude_tool_use"
  },
  "session_metadata": {
    "project": "zzj",
    "project_name": "超时空要塞",
    "session_id": "<full-uuid>",
    "started_at": "<ISO 8601>",
    "ended_at": "<ISO 8601>",
    "duration_sec": 2070.1,
    "cwd": "/workspace",
    "version": "2.1.4",
    "git_branch": ""
  },
  "messages": [ /* see 3.2 */ ],
  "phases": [ /* see 3.3 */ ],
  "markers": [ /* see 3.4 */ ],
  "subagents": [ /* see 3.5 */ ],
  "summary": { /* see 3.6 */ }
}
```

### 3.2 Messages Array

The `messages` array contains alternating user messages and agent runs, grouped by `turn_id`:

**User message:**
```json
{
  "turn_id": 1,
  "role": "user",
  "content": "user prompt text",
  "timestamp": "2026-03-25T07:38:00.000Z"
}
```

**Agent run (follows a user message with the same turn_id):**
```json
{
  "turn_id": 1,
  "agent_run_id": "run_t1",
  "steps": [
    {
      "step_id": 1,
      "phase": "localization",
      "thinking": "extended thinking text or null",
      "thought": "parsed assistant text response",
      "action": {
        "tool_name": "Read",
        "tool_use_id": "toolu_xxx",
        "args": { "file_path": "/workspace/main.lua" }
      },
      "observation": {
        "type": "tool_result",
        "text": "file content (truncated to 2000 chars)",
        "exit_code": null
      },
      "state": {
        "files_touched": ["main.lua"],
        "working_dir": "/workspace"
      },
      "status": "ok",
      "timestamp": "2026-03-25T07:38:05.000Z",
      "execution_time": 2.1,
      "usage": {
        "input_tokens": 5000,
        "output_tokens": 200,
        "cache_read_tokens": 37000,
        "cache_creation_tokens": 15000
      }
    }
  ],
  "run_summary": {
    "result": "completed",
    "total_steps": 8,
    "edit_failures": 0,
    "total_input_tokens": 40000,
    "total_output_tokens": 3000
  }
}
```

**Step fields explained:**

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | int | 1-based within this run |
| `phase` | string | localization/editing/verification/submission/setup |
| `thinking` | string/null | Extended thinking content (stripped of signature) |
| `thought` | string | Assistant text response (non-thinking, non-tool-use content) |
| `action` | object | `{tool_name, tool_use_id, args}` — structured tool call |
| `action` | `{"tool_name": "respond_to_user", "args": {}}` | When assistant responds with text only (no tool call) |
| `observation` | object | `{type, text, exit_code}` — structured result |
| `state` | object | `{files_touched, working_dir}` — environment state after action |
| `status` | string | "ok" or "error" |
| `timestamp` | string | ISO 8601 when this step occurred |
| `execution_time` | float | Seconds since previous step |
| `usage` | object | Token counts for this step's API call |

### 3.3 Phases

Same structure as v1, computed by the phase tagger:

```json
{
  "name": "Localization",
  "name_zh": "问题定位",
  "start_turn": 1,
  "start_step": 1,
  "end_turn": 1,
  "end_step": 4,
  "label": "localization"
}
```

Note: v2 phases reference both turn_id and step_id for precise boundaries.

### 3.4 Markers

Same structure as v1:

```json
{
  "turn": 1,
  "step": 5,
  "type": "drift-start",
  "reason": "4 consecutive edits without verification"
}
```

v2 markers include both turn and step references.

### 3.5 Subagents

Subagents are stored as a top-level array with parent references:

```json
{
  "agent_id": "ab84833",
  "parent_turn_id": 1,
  "parent_step_id": 3,
  "messages": [
    {
      "turn_id": 1,
      "role": "user",
      "content": "subagent task prompt",
      "timestamp": "..."
    },
    {
      "turn_id": 1,
      "agent_run_id": "sub_run_t1",
      "steps": [ /* same step structure */ ],
      "run_summary": { /* ... */ }
    }
  ],
  "summary": {
    "total_steps": 12,
    "total_tool_calls": 10,
    "status": "completed"
  }
}
```

### 3.6 Session Summary

```json
{
  "total_turns": 5,
  "total_steps": 42,
  "total_tool_calls": 38,
  "total_subagents": 2,
  "total_input_tokens": 200000,
  "total_output_tokens": 15000,
  "total_cache_read_tokens": 150000,
  "total_cache_creation_tokens": 50000,
  "exit_reason": "end_of_conversation",
  "status": "completed"
}
```

## 4. Converter (`traj-data-new/converter_v2.py`)

### 4.1 Input

Raw JSONL files from `{project}-project-logs/.claude/projects/-workspace/*.jsonl` plus subagent files from `session_id/subagents/agent-*.jsonl`.

### 4.2 Processing Pipeline

1. **Parse JSONL** — Read entries, skip `queue-operation` type
2. **Filter system messages** — Same 9 prefix patterns as v1
3. **Turn grouping** — Each non-system, non-tool-result user message starts a new turn (turn_id increments)
4. **Step extraction** — Within each turn, each assistant message with tool_use blocks generates steps. Match tool_use_id to tool_result in subsequent user messages.
5. **Thinking extraction** — Extract `type: "thinking"` blocks separately from `type: "text"` blocks. Drop `signature` field.
6. **Token capture** — Read `message.usage` from each assistant entry
7. **Phase tagging** — Reuse phase_tagger.py logic (classify by tool name)
8. **Marker detection** — Reuse drift/churn/search-loop detection
9. **Subagent processing** — Recurse into subagent JSONL files, produce nested messages structure
10. **Summary computation** — Aggregate totals

### 4.3 Output

One `.traj` file per session in `traj-data-new/{wzp,zzj}/{session_hash}.traj`.

### 4.4 CLI

```bash
python converter_v2.py --wzp-workspace <path> --zzj-workspace <path> --output-dir .
python converter_v2.py --session <path.jsonl> --project <name> --output-dir .
```

### 4.5 Dependency

`phase_tagger.py` will be copied from `traj-data/` into `traj-data-new/` and enhanced with turn+step aware phase/marker boundaries.

## 5. Backend Updates (`traj-viz/backend/`)

### 5.1 Models (`models.py`)

New Pydantic models:

```python
class ActionDetail(BaseModel):
    tool_name: str
    tool_use_id: str | None = None
    args: dict

class ObservationDetail(BaseModel):
    type: str
    text: str
    exit_code: int | None = None

class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

class StepDetail(BaseModel):
    step_id: int
    phase: str
    thinking: str | None = None
    thought: str
    action: ActionDetail
    observation: ObservationDetail
    state: dict | None = None
    status: str
    timestamp: str
    execution_time: float
    usage: TokenUsage | None = None
    marker: str | None = None
    marker_reason: str | None = None

class RunSummary(BaseModel):
    result: str
    total_steps: int
    edit_failures: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

class AgentRun(BaseModel):
    turn_id: int
    agent_run_id: str
    steps: list[StepDetail]
    run_summary: RunSummary

class UserMessage(BaseModel):
    turn_id: int
    role: str = "user"
    content: str
    timestamp: str

    # messages list contains UserMessage and AgentRun objects alternating.
    # In the API response, discriminated by presence of "role" (UserMessage) vs "steps" (AgentRun).
    # In Python, the loader returns them as a list[UserMessage | AgentRun].

class SessionSummary(BaseModel):
    # For list view (replaces TrajectorySummary)
    conversation_id: str
    project: str
    project_name: str
    status: str
    started_at: str
    ended_at: str
    duration_sec: float
    total_turns: int
    total_steps: int
    total_tool_calls: int
    total_subagents: int
    total_input_tokens: int
    total_output_tokens: int
    first_user_prompt: str
    phase_labels: list[str]
    marker_count: int
    exit_reason: str

class SessionDetail(SessionSummary):
    # For detail view (replaces TrajectoryDetail)
    messages: list  # UserMessage | AgentRun alternating
    phases: list[Phase]
    markers: list[Marker]
    subagents: list  # Subagent summaries
```

### 5.2 Loader (`loader.py`)

Update `TrajectoryLoader`:
- Change data dir default to `traj-data-new/`
- Parse v2 schema (read `messages[]`, extract turns/steps)
- Build `SessionSummary` for list index from `summary` field
- Build `SessionDetail` from full messages structure
- Keep mtime-based caching

### 5.3 API (`main.py`)

Existing endpoints updated for v2 response shapes:
- `GET /api/trajectories` — returns `list[SessionSummary]` (adds token columns)
- `GET /api/trajectories/{project}/{session_hash}` — returns `SessionDetail` (multi-turn structure)
- `GET /api/projects` — adds token totals per project
- `GET /api/analytics/tools` — unchanged
- `GET /api/analytics/phases` — unchanged

New endpoint:
- `GET /api/analytics/tokens` — Token usage and cache efficiency stats across sessions

## 6. Frontend Updates (`traj-viz/frontend/`)

### 6.1 Type Updates (`types/trajectory.ts`)

Mirror the new Pydantic models. Key new types: `StepDetail`, `AgentRun`, `UserMessage`, `SessionSummary`, `SessionDetail`.

### 6.2 TrajectoryDetail View (Conversation-first)

Layout:
```
[Back button]
[HeroSection — session metadata, total tokens, status]

Turn 1:
  [UserMessage bubble — "Please fix the bug..."]
  [AgentRun — collapsible]
    Step 1: [phase pill] [tool badge: Read] [status: ok] [+2.1s]
      > thinking text (collapsed by default)
      > action args
      > observation text
      > token usage bar
    Step 2: ...
    [RunSummary bar — 8 steps, 0 errors, 40K tokens]

Turn 2:
  [UserMessage bubble — "Also update the tests"]
  [AgentRun — collapsible]
    ...

[EvidenceFooter — phase distribution, total tokens, subagent count]
```

### 6.3 New Components

| Component | Purpose |
|-----------|---------|
| `UserMessage.vue` | User prompt bubble with turn number and timestamp |
| `AgentRun.vue` | Collapsible step sequence with run summary bar |
| `StepCard.vue` | Expandable step with structured action/observation, token bar |
| `TokenUsageBar.vue` | Inline token usage visualization (input/output/cache) |
| `SubagentPanel.vue` | Expandable subagent conversation (lazy-loaded) |

### 6.4 TrajectoryList View Updates

- Add columns: Turns (user messages), Tokens (total)
- Rename "Turns" column to "Steps" for clarity

### 6.5 Existing Components

- `HeroSection.vue` — Add token usage summary, model name
- `FilterBar.vue` — No changes needed
- `PhasePills.vue` — No changes needed
- `MarkerBadge.vue` — No changes needed
- `EvidenceFooter.vue` — Add token totals, cache efficiency %
- `PhaseSection.vue` — Replaced by per-turn AgentRun grouping (remove)
- `TurnCard.vue` — Replaced by StepCard.vue (remove)

## 7. Scripts & Documentation

### 7.1 File Changes Summary

**New files:**
- `traj-data-new/converter_v2.py` — V2 converter
- `traj-data-new/phase_tagger.py` — Copied + enhanced from traj-data/
- `traj-viz/CHANGELOG.md` — Created immediately, appended per change
- `traj-viz/gotchas/` — Directory for implementation notes
- `docs/superpowers/specs/2026-04-14-traj-viz-v2-design.md` — This spec

**Modified files:**
- `traj-viz/backend/models.py` — New v2 Pydantic models
- `traj-viz/backend/loader.py` — Parse v2 schema
- `traj-viz/backend/main.py` — Updated endpoints + token analytics
- `traj-viz/backend/tests/test_api.py` — Updated for v2 response shapes
- `traj-viz/frontend/src/types/trajectory.ts` — New TypeScript interfaces
- `traj-viz/frontend/src/api/client.ts` — Updated API client
- `traj-viz/frontend/src/views/TrajectoryDetail.vue` — Conversation-first layout
- `traj-viz/frontend/src/views/TrajectoryList.vue` — Token/turn columns
- `traj-viz/frontend/src/components/HeroSection.vue` — Token summary
- `traj-viz/frontend/src/components/EvidenceFooter.vue` — Token totals
- `traj-viz/README.md` — Updated for v2

**New frontend components:**
- `src/components/UserMessage.vue`
- `src/components/AgentRun.vue`
- `src/components/StepCard.vue`
- `src/components/TokenUsageBar.vue`
- `src/components/SubagentPanel.vue`

**Removed frontend components:**
- `src/components/PhaseSection.vue` — Replaced by AgentRun
- `src/components/TurnCard.vue` — Replaced by StepCard

## 8. Implementation Phases

1. **Schema + Converter** — Define v2 schema, build converter_v2.py, generate .traj files
2. **Backend** — Update models, loader, API endpoints, tests
3. **Frontend** — New components, updated views, TypeScript types
4. **Docs & Polish** — README, CHANGELOG, gotchas, final review
