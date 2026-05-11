# SWE-Agent Trajectory Conversion & Visualization — Design Spec

## Overview

Convert real Claude Code production sessions from two game development projects (wzp: 脑力大冒险, zzj: 超时空要塞) into SWE-agent formatted `.traj` files, and build a narrative timeline visualization app.

**Two deliverables:**
1. **traj-data/** — Python converter that reads Claude Code JSONL session logs and outputs faithful SWE-agent `.traj` JSON files with heuristic phase annotations
2. **traj-viz/** — FastAPI + Vue 3 web app that renders trajectories as dark-themed narrative timeline pages

---

## Part 1: traj-data — Trajectory Conversion

### 1.1 File System Layout

```
traj-data/
  wzp/                           # 105 sessions from 脑力大冒险
    014354fc.traj                 # Session UUID (first 8 chars) .traj
    019cf9e3.traj
    ...
  zzj/                           # 57 sessions from 超时空要塞
    019c99e5.traj
    ...
  converter.py                   # Main conversion script
  phase_tagger.py                # Heuristic phase annotation
  tests/
    test_converter.py
    test_phase_tagger.py
  requirements.txt               # No external deps (stdlib only)
```

### 1.2 Source Data

Claude Code workspace JSONL files from:
- `wzp-project-logs/.claude/projects/-workspace/*.jsonl` (105 sessions)
- `zzj-project-logs/.claude/projects/-workspace/*.jsonl` (57 sessions)

Each session may also have subagent files at `{session_id}/subagents/agent-{agent_id}.jsonl`.

#### JSONL Message Format (input)

Each line is a JSON object with:
- `type`: `"user"` | `"assistant"` | `"queue-operation"`
- `uuid`: unique message ID
- `parentUuid`: links to previous message in conversation tree
- `timestamp`: ISO 8601
- `userType`: `"external"` (human) | `"tool"` (tool result)
- `message.role`: `"user"` | `"assistant"`
- `message.content`: string or array of content blocks

Content block types:
- `{"type": "text", "text": "..."}` — text output
- `{"type": "thinking", "thinking": "..."}` — reasoning (assistant only)
- `{"type": "tool_use", "id": "...", "name": "...", "input": {...}}` — tool call (assistant only)
- `{"type": "tool_result", "tool_use_id": "...", "content": "..."}` — tool result (user/tool messages)

### 1.3 Output Format (Faithful SWE-agent .traj JSON)

Each `.traj` is a single JSON file:

```json
{
  "trajectory": [
    {
      "thought": "用户要求调用 list_tap_developers 获取厂商列表...",
      "action": "mcp__sce-urhox__list_tap_developers()",
      "observation": "已获取到当前用户的厂商列表，共有 2 个厂商...",
      "state": "",
      "execution_time": 3.0
    }
  ],
  "history": [
    [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  ],
  "info": {
    "task_id": "zzj/019c99e5",
    "project": "zzj",
    "session_id": "019c99e5-fc70-74ac-9cc2-d9091e4478a3",
    "status": "completed",
    "start_time": "2026-02-26T12:22:17",
    "end_time": "2026-02-26T14:00:39",
    "duration_sec": 5902,
    "total_turns": 4,
    "total_tool_calls": 1,
    "total_subagents": 0,
    "exit_reason": "end_of_conversation",
    "submission": null,
    "model": "claude-sonnet-4-..."
  },
  "phases": [
    {
      "name": "Task Setup",
      "name_zh": "任务注入",
      "start_turn": 0,
      "end_turn": 0,
      "label": "setup"
    },
    {
      "name": "Localization",
      "name_zh": "问题定位",
      "start_turn": 1,
      "end_turn": 3,
      "label": "localization"
    }
  ],
  "markers": [
    {
      "turn": 11,
      "type": "drift-start",
      "reason": "4 consecutive edits without verification"
    }
  ]
}
```

### 1.4 Mapping Rules: Claude Code -> SWE-agent Turns

| Claude Code Message | Maps To |
|---|---|
| Assistant thinking block | `thought` field |
| Assistant tool_use block | `action` field, formatted as `tool_name(key=val, ...)` |
| User tool_result block | `observation` field |
| Assistant text-only (no tools) | `thought` = text, `action` = `"respond_to_user()"`, `observation` = next user message or "" |
| User external message | Turn boundary — content goes into `history`, first user message is the task description |

**Multi-tool turns:** When an assistant message contains multiple `tool_use` blocks, each becomes its own trajectory step. All steps share the same `thought` (from the thinking block of that message).

**Subagent handling:** Subagent messages are included in the trajectory as regular turns, but their actions are prefixed with `[subagent:{agent_id}]` to distinguish them from main conversation actions.

**System messages:** Messages matching these prefixes are filtered out (not included in trajectory):
- `"This session is being continued"`
- `"<system-reminder>"`
- `"<command-name>"`
- `"<local-command"`
- `"Base directory for this skill:"`
- `"<image-caption>"`
- `"[Image: "`
- `"[Request interrupted by user]"`

**execution_time:** Computed as the difference between the current message timestamp and the previous message timestamp, in seconds.

**history:** Built as a list of message lists. Each "turn" in the history corresponds to one complete user-prompt -> assistant-response cycle, including all intermediate tool calls. Format follows SWE-agent convention: `[{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]`.

### 1.5 Phase Tagging Heuristics

`phase_tagger.py` runs as a post-processing pass on each trajectory, assigning phase labels to consecutive turn ranges.

| Tool Name / Pattern | Phase Label | Phase Name (zh) |
|---|---|---|
| `Read`, `Glob`, `Grep`, `LSP`, `search_*`, `find_*` | `localization` | 问题定位 |
| `Write`, `Edit`, `NotebookEdit` | `editing` | 补丁生成 |
| `Bash` containing `pytest`/`test`/`npm test`/`cargo test` | `verification` | 验证与测试 |
| `Bash` containing `git commit`/`git push` | `submission` | 提交 |
| `Bash` (other) | `editing` (default for general commands) | 补丁生成 |
| First turn in session (user prompt) | `setup` | 任务注入 |
| `Agent` tool | `localization` (subagent research) | 问题定位 |
| `respond_to_user()` | Inherits phase from previous turn | (inherited) |

**Consecutive merging:** Adjacent turns with the same phase label are merged into a single phase entry with `start_turn` and `end_turn` range.

### 1.6 Drift & Marker Detection

Markers are annotated on specific turns:

| Condition | Marker Type | Reason |
|---|---|---|
| 4+ consecutive `Edit`/`Write` turns with no `Bash` verification between them | `drift-start` | "N consecutive edits without verification" |
| 4+ consecutive `Read`/`Glob`/`Grep` turns without reaching an `Edit` | `search-loop` | "Extended search without editing — possible localization failure" |
| Same file edited 3+ times in 5 turns | `churn` | "Repeated edits to {filename} — possible edit recovery failure" |
| First turn in session | `milestone` | "Session start" |
| Last turn in session | `milestone` | "Session end" |

### 1.7 Converter CLI

```bash
# Convert all sessions from both projects
python converter.py \
  --wzp-workspace ../wzp-project-logs/.claude/projects/-workspace \
  --zzj-workspace ../zzj-project-logs/.claude/projects/-workspace \
  --output-dir .

# Convert a single session
python converter.py \
  --session ../zzj-project-logs/.claude/projects/-workspace/019c99e5-fc70-74ac-9cc2-d9091e4478a3.jsonl \
  --project zzj \
  --output-dir .
```

Output: prints conversion stats (sessions converted, total turns, total tool calls, phases detected, markers placed).

---

## Part 2: traj-viz — Trajectory Visualization

### 2.1 File System Layout

```
traj-viz/
  backend/
    main.py                      # FastAPI app factory + all endpoints
    loader.py                    # .traj file reader + in-memory index
    models.py                    # Pydantic response models
    requirements.txt             # fastapi, uvicorn, pydantic
  frontend/
    src/
      views/
        TrajectoryList.vue       # Index page — filters, search, table
        TrajectoryDetail.vue     # Narrative timeline page
      components/
        HeroSection.vue          # Task summary + stats grid
        PhaseSection.vue         # Phase header + timeline container
        TurnCard.vue             # Turn: title, action, summary, tags, expand
        PhasePills.vue           # Mini phase bar for list items
        MarkerBadge.vue          # DRIFT / PIVOT / MILESTONE badges
        EvidenceFooter.vue       # Outcome + drift diagnosis panel
        FilterBar.vue            # Project filters + search input
      composables/
        useTrajectories.ts       # Fetch + cache trajectory list
        useTrajectory.ts         # Fetch single trajectory detail
      api/
        client.ts                # Fetch wrapper for /api/* endpoints
      styles/
        variables.css            # Color tokens, type scale
        base.css                 # Reset + body dark theme
      types/
        trajectory.ts            # TypeScript interfaces
      router/
        index.ts                 # Vue Router config
      App.vue
      main.ts
    index.html
    package.json                 # vue, vue-router, vite, typescript
    vite.config.ts
    tsconfig.json
  scripts/
    start.sh                     # Launch backend + frontend dev servers
    build.sh                     # Build frontend, start production mode
  SWE-Agent轨迹叙事页.md          # Reference design (already exists)
```

### 2.2 Backend API (FastAPI)

**Data loading:** On startup, `loader.py` scans `../traj-data/{project}/*.traj`, reads each file, and builds an in-memory list of `TrajectorySummary` objects (metadata only). Full trajectory data is loaded on-demand from disk. File modification times are cached; if a `.traj` file is newer than the cached mtime, it is re-read on next access.

**Endpoints:**

| Method | Path | Response | Description |
|---|---|---|---|
| `GET` | `/api/trajectories` | `list[TrajectorySummary]` | List all trajectories, sortable by date/turns/duration |
| `GET` | `/api/trajectories?project=wzp` | `list[TrajectorySummary]` | Filter by project |
| `GET` | `/api/trajectories?q=碰撞` | `list[TrajectorySummary]` | Search in first user prompt text |
| `GET` | `/api/trajectories/{project}/{session_hash}` | `TrajectoryDetail` | Full trajectory: turns, phases, markers (e.g., `/api/trajectories/zzj/019c99e5`) |
| `GET` | `/api/projects` | `list[ProjectSummary]` | Aggregate stats per project |
| `GET` | `/api/analytics/tools` | `list[ToolStat]` | Tool usage frequency |
| `GET` | `/api/analytics/phases` | `list[PhaseStat]` | Phase distribution |

**Response models:**

```python
class TrajectorySummary(BaseModel):
    task_id: str                    # "zzj/019c99e5"
    project: str                    # "wzp" or "zzj"
    session_id: str                 # Full UUID
    status: str                     # "completed"
    start_time: str                 # ISO timestamp
    end_time: str
    duration_sec: float
    total_turns: int
    total_tool_calls: int
    total_subagents: int
    first_user_prompt: str          # First 120 chars of first user message
    phase_labels: list[str]         # ["setup", "localization", "editing", ...]
    marker_count: int               # Number of drift/pivot markers
    exit_reason: str

class TrajectoryDetail(TrajectorySummary):
    trajectory: list[TurnStep]
    phases: list[Phase]
    markers: list[Marker]

class TurnStep(BaseModel):
    step: int
    thought: str
    action: str
    observation: str
    phase: str                      # Phase label for this turn
    tone: str                       # Color: blue/violet/green/orange/red/gold
    execution_time: float
    marker: str | None              # "drift-start", "milestone", etc.
    marker_reason: str | None

class Phase(BaseModel):
    name: str                       # "Localization"
    name_zh: str                    # "问题定位"
    start_turn: int
    end_turn: int
    label: str                      # "localization"

class Marker(BaseModel):
    turn: int
    type: str                       # "drift-start", "churn", "milestone", etc.
    reason: str

class ProjectSummary(BaseModel):
    project: str
    project_name: str               # "超时空要塞" / "脑力大冒险"
    total_sessions: int
    total_turns: int
    total_tool_calls: int
    date_range: str

class ToolStat(BaseModel):
    tool_name: str
    count: int

class PhaseStat(BaseModel):
    phase: str
    total_turns: int
    avg_turns_per_session: float
```

**Static file serving:** In production, FastAPI mounts `frontend/dist/` as static files at `/`. The API is at `/api/*`.

### 2.3 Frontend Design (Vue 3 + TypeScript)

#### Visual Design System

Follows the reference design (`SWE-Agent轨迹叙事页.md`): dark-themed narrative timeline with editorial feel.

**Color tokens:**

| Token | Value | Usage |
|---|---|---|
| `--bg-primary` | `#0E0E10` | Page background |
| `--text-primary` | `#F2EEE8` | Main text (warm white) |
| `--text-secondary` | `#B7AA99` | Summaries, descriptions (grey-gold) |
| `--text-tertiary` | `#7A7068` | Timestamps, labels |
| `--text-muted` | `#5A524A` | Least important text |
| `--accent-gold` | `#C9B896` | Phase headers, milestone markers, dividers |
| `--tone-blue` | `#5B8DEF` | Localization phase |
| `--tone-violet` | `#9B6DFF` | Editing phase |
| `--tone-green` | `#4ADE80` | Verification phase |
| `--tone-orange` | `#F59E0B` | Warning / pivot markers |
| `--tone-red` | `#EF4444` | Drift / failure markers |
| `--border-subtle` | `rgba(184,156,108,0.12)` | Section dividers |

**Typography:**
- Headings: Inter / SF Pro, 600 weight
- Body: Inter / SF Pro, 400 weight
- Mono: SF Mono / Fira Code — for action commands, task IDs
- Chinese headings for phase titles, English subtitles

#### View: Trajectory List (`/`)

**Layout:**
- Page header: "SWE Agent Trajectories" + subtitle
- Aggregate stats bar: total trajectories, per-project counts, total dev days
- Filter bar: All / WZP / ZZJ pills + search input
- Table: columns = Task ID (with status dot), Session info (title + first prompt preview + phase pills), Date, Duration, Turns, Tools
- Click any row → navigate to `/trajectory/{project}/{session_hash}`

**Phase pills:** A row of small colored rectangles under each list item, one per phase in the trajectory. Colors match the phase color tokens. Gives an at-a-glance phase distribution.

#### View: Trajectory Detail (`/trajectory/:project/:sessionHash`)

**Layout (top to bottom):**

1. **Hero section**
   - Title: "SWE Agent Trajectory"
   - Subtitle: "From issue ingestion to patch submission" (italic)
   - Project badge: "ZZJ · 超时空要塞"
   - Stats grid (3x2): Task ID, Total Turns, Duration, Status, Tool Calls, Subagents

2. **Phase sections** (repeating for each phase)
   - Phase header: Chinese title + English subtitle + turn range
   - Vertical timeline rail (left side, thin gold line)
   - Turn cards along the timeline:
     - Left: step number (#01) + time offset (T+00:14)
     - Timeline node dot (colored by phase tone)
     - Card content: narrative title, action command (monospace), summary paragraph, tags, optional marker badge
     - Expandable: click to show raw thought/action/observation

3. **Evidence footer**
   - Outcome box (green border for completed, red for failed)
   - Drift detection boxes (if markers exist)

**Interaction model (weak interaction, strong narrative):**
- Scroll to browse chapters
- Click turn card to expand/collapse raw data
- Click tags to highlight matching turns
- Back button returns to list view

### 2.4 Scripts

**`scripts/start.sh`:**
```bash
#!/bin/bash
# Start both backend and frontend dev servers
cd "$(dirname "$0")/.."

# Backend
cd backend
pip install -r requirements.txt -q
uvicorn main:app --port 8000 --reload &
BACKEND_PID=$!

# Frontend
cd ../frontend
npm install -q
npm run dev &
FRONTEND_PID=$!

echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
```

**`scripts/build.sh`:**
```bash
#!/bin/bash
# Build frontend and start production mode
cd "$(dirname "$0")/.."

cd frontend
npm install -q
npm run build

cd ../backend
pip install -r requirements.txt -q
echo "Starting production server..."
uvicorn main:app --port 8000
```

### 2.5 Turn-to-Tone Color Mapping

The `tone` field on each `TurnStep` determines the timeline node color:

| Phase Label | Tone | Node Color |
|---|---|---|
| `setup` | `gold` | `#C9B896` (with glow) |
| `localization` | `blue` | `#5B8DEF` |
| `editing` | `violet` | `#9B6DFF` |
| `verification` | `green` | `#4ADE80` |
| `submission` | `gold` | `#C9B896` (with glow) |

**Override by marker:** If a turn has a `drift-start` or `churn` marker, tone is `orange`. If marker is a recovery failure, tone is `red`.

### 2.6 Three-Tier Node Importance

Per the reference design, not all turns are displayed equally:

| Tier | Criteria | Display |
|---|---|---|
| **A: Primary** | First turn per phase, turns with markers, first/last turn in session | Full card with title, summary, tags |
| **B: Secondary** | Other turns with tool calls | Compact card (title + action only), expandable |
| **C: Noise** | Consecutive same-action turns (e.g., 5x `Read` in a row), tool results only | Collapsed group: "3 more Read operations" |

This keeps the timeline readable even for 50+ turn sessions.

---

## Dependencies

### traj-data
- Python 3.10+ (stdlib only, no external packages)

### traj-viz backend
- Python 3.10+
- `fastapi>=0.115.0`
- `uvicorn>=0.30.0`
- `pydantic>=2.9.0`

### traj-viz frontend
- Node.js 18+
- `vue@3`
- `vue-router@4`
- `vite`
- `typescript`

---

## Testing

### traj-data
- `pytest tests/test_converter.py` — conversion correctness: JSONL parsing, turn building, action formatting
- `pytest tests/test_phase_tagger.py` — phase label assignment, marker detection, edge cases

### traj-viz backend
- `pytest tests/` — API endpoint responses, loader caching, search filtering

### traj-viz frontend
- Manual verification via browser — check both list and detail views render correctly
