# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains trajectory analysis tooling for Claude Code production sessions. It analyzes real human-AI interaction logs from two game development projects (wzp: 脑力大冒险, zzj: 超时空要塞) built on the UrhoX Lua engine via TapTap Maker.

The raw data lives in `wzp-project-logs/.claude/` and `zzj-project-logs/.claude/` — these are real Claude Code workspace directories containing JSONL session logs, debug files, subagent transcripts, and todo records. The `SWE-agent-trajectory.md` document provides the analytical framework (adapted from SWE-agent's trajectory analysis methodology).

## Architecture

The repo has a two-stage data pipeline plus legacy tools:

```
Raw JSONL logs (.claude/)
    ↓ converter_v2.py + phase_tagger.py
v2 .traj files (traj-data-new/)
    ↓ loader.py
traj-viz (FastAPI + Vue 3 SPA)      ← active viewer (v2)
```

Legacy tools in `zzj-project-logs/`:
```
Raw JSONL logs → task-prompt-pipeline/ → LLM retrospective reports
Raw JSONL logs → project-viz/ (FastAPI + React) → SQLite-backed session browser
```

Legacy v1 pipeline (preserved for reference):
```
Raw JSONL logs → traj-data/converter.py → v1 .traj files (flat trajectory)
```

### 1. traj-data-new/ — V2 JSONL → .traj Conversion Pipeline (Active)

Converts Claude Code JSONL session logs to v2 `.traj` format with multi-turn grouping, structured actions, token usage, and extended thinking.

**Modules:**
- `converter_v2.py` — JSONL parsing, multi-turn grouping (user messages + agent runs), structured tool call extraction, thinking block preservation, token capture, subagent nesting
- `phase_tagger.py` — Classifies structured action objects into phases, detects behavioral markers

**V2 schema key features:**
- Multi-turn grouped: `messages[]` array with alternating user messages and agent runs
- Structured actions: `{"tool_name": "Read", "tool_use_id": "...", "args": {...}}`
- Structured observations: `{"type": "tool_result", "text": "...", "exit_code": null}`
- Per-step token usage: `{input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens}`
- Extended thinking preserved (base64 signatures stripped)
- Subagents as nested structures with parent references

### 2. traj-viz/ — Interactive Trajectory Viewer (Active, v2)

FastAPI + Vue 3 SPA for browsing converted v2 `.traj` files. Conversation-first design. Reads from `traj-data-new/` (no database).

**Backend** (`traj-viz/backend/`):
- `loader.py` — Scans `traj-data-new/{wzp,zzj}/*.traj`, builds in-memory index with mtime-based detail cache, provides token analytics
- `main.py` — FastAPI app factory with 6 API endpoints (trajectories, projects, tools/phases/tokens analytics)
- `models.py` — Pydantic models: SessionSummary, SessionDetail, StepDetail, AgentRun, UserMessage, TokenUsage, etc.

**Frontend** (`traj-viz/frontend/`): Vue 3 + vue-router + TypeScript + Vite
- Two routes: `/ → TrajectoryList`, `/trajectory/:project/:sessionHash → TrajectoryDetail`
- Conversation-first detail view: user message bubbles → collapsible agent runs with expandable steps
- Each step shows: phase color, tool badge, thinking text, action args, observation, token usage bar
- Phase colors: blue=localization, violet=editing, green=verification, gold=setup/submission

**Data flow:** `traj-data-new/{wzp,zzj}/*.traj` → `TrajectoryLoader` → REST API → Vue SPA

### 3. traj-data/ — V1 Conversion Pipeline (Legacy)

Original flat trajectory converter. Kept for reference. Use `traj-data-new/converter_v2.py` for new conversions.

### 4. task-prompt-pipeline/ — Batch Analysis Pipeline (Legacy)

In `zzj-project-logs/task-prompt-pipeline/`. Extracts user prompts from JSONL, summarizes via Qwen-Plus LLM, generates retrospective reports + game task specs. **Requires:** `DASHSCOPE_API_KEY` env var, `openai` package.

### 5. project-viz/ — Interactive Session Viewer (Legacy)

In `zzj-project-logs/project-viz/`. FastAPI + React 19 SPA with SQLite + FTS5. Superseded by traj-viz.

## Data Layout

```
traj-data-new/{wzp,zzj}/*.traj       # V2 converted trajectory files (active)
traj-data-new/swe-agent-traj-*.md/json # V2 schema docs + examples
traj-data/{wzp,zzj}/*.traj            # V1 trajectory files (legacy)
wzp-project-logs/.claude/             # Raw JSONL logs (~680 user prompts, 18 dev days)
zzj-project-logs/.claude/             # Raw JSONL logs (~840 user prompts, 30 dev days)
*/TapCode-User_Workspace/             # UrhoX game assets (not analysis targets)
UrhoX-SCE-Overview/                   # UrhoX platform architecture analysis (7-layer model)
```

## Common Commands

```bash
# traj-viz backend (from repo root)
cd traj-viz && python -m uvicorn backend.main:app --port 8000 --reload

# traj-viz frontend dev server (proxies /api to :8000)
cd traj-viz/frontend && npm install && npm run dev

# traj-viz frontend build (output in frontend/dist/, served by FastAPI)
cd traj-viz/frontend && npm run build

# traj-viz backend tests (9 tests)
cd traj-viz && python -m pytest backend/tests/ -v

# traj-data-new converter + tagger tests (47 tests)
cd traj-data-new && python -m pytest tests/ -v

# v2 data conversion
cd traj-data-new && python converter_v2.py \
  --wzp-workspace ../wzp-project-logs/.claude/projects/-workspace \
  --zzj-workspace ../zzj-project-logs/.claude/projects/-workspace \
  --output-dir .

# task-prompt-pipeline tests (25 tests, mock LLM)
cd zzj-project-logs/task-prompt-pipeline && ../.venv/bin/python -m pytest tests/test_e2e.py -v

# project-viz backend tests
cd zzj-project-logs/project-viz && ../.venv/bin/python -m pytest backend/tests/ -v
```

## Key Design Decisions

- **Two-stage pipeline**: Raw JSONL → v2 `.traj` (offline, via converter_v2.py) → viewer (runtime, via loader.py). The viewer never touches raw JSONL
- **Multi-turn grouping**: V2 schema groups steps under user turns, matching the natural conversation flow of Claude Code sessions
- **In-memory index**: `TrajectoryLoader` scans all `.traj` files at startup and caches detail by mtime — no database needed
- **Phase tagging is tool-based**: Classification relies on `action.tool_name` in structured action objects. `respond_to_user` inherits the previous step's phase
- **Token tracking**: Per-step, per-run, and per-session token usage including Anthropic prompt cache metrics (cache_read, cache_creation)
- **Thinking preservation**: Extended thinking blocks preserved for reasoning analysis; base64 signatures stripped
- **Project name mapping**: `wzp` → 脑力大冒险, `zzj` → 超时空要塞
- **System message filtering**: 9 prefix patterns filtered to isolate genuine user input
