# SWE-Agent Trajectory Conversion & Visualization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert 162 Claude Code production sessions (wzp + zzj) into SWE-agent `.traj` format and build a FastAPI + Vue 3 narrative timeline visualization app.

**Architecture:** Two independent deliverables. `traj-data/` is a pure Python converter (stdlib only) that reads JSONL → writes `.traj` JSON with heuristic phase/marker annotations. `traj-viz/` is a FastAPI backend reading `.traj` files directly from disk + Vue 3 SPA rendering dark-themed narrative timelines.

**Tech Stack:** Python 3.10+ (stdlib), FastAPI + Pydantic, Vue 3 + TypeScript + Vite + Vue Router

---

## File Structure

### traj-data/

| File | Responsibility |
|---|---|
| `converter.py` | JSONL parsing, message-to-turn mapping, `.traj` file writing, CLI entry point |
| `phase_tagger.py` | Heuristic phase label assignment, consecutive-merge, drift/marker detection |
| `tests/test_converter.py` | Conversion correctness tests |
| `tests/test_phase_tagger.py` | Phase tagging and marker detection tests |
| `requirements.txt` | `pytest` only (converter itself is stdlib) |

### traj-viz/backend/

| File | Responsibility |
|---|---|
| `main.py` | FastAPI app factory, 7 API endpoints, CORS, static file mount |
| `loader.py` | Scan `.traj` files, build in-memory index, on-demand detail loading |
| `models.py` | All Pydantic response models (TrajectorySummary, TrajectoryDetail, TurnStep, Phase, Marker, etc.) |
| `requirements.txt` | fastapi, uvicorn, pydantic |
| `tests/test_api.py` | API endpoint tests |

### traj-viz/frontend/

| File | Responsibility |
|---|---|
| `src/styles/variables.css` | Color tokens, type scale |
| `src/styles/base.css` | Reset, body dark theme, shared utilities |
| `src/types/trajectory.ts` | TypeScript interfaces matching backend models |
| `src/api/client.ts` | Fetch wrapper for `/api/*` |
| `src/composables/useTrajectories.ts` | Fetch + cache trajectory list |
| `src/composables/useTrajectory.ts` | Fetch single trajectory detail |
| `src/router/index.ts` | Vue Router config (2 routes) |
| `src/components/FilterBar.vue` | Project filter pills + search input |
| `src/components/PhasePills.vue` | Mini colored phase bar for list items |
| `src/components/HeroSection.vue` | Task summary + stats grid |
| `src/components/PhaseSection.vue` | Phase header + timeline container |
| `src/components/TurnCard.vue` | Turn card: title, action, summary, tags, expand |
| `src/components/MarkerBadge.vue` | DRIFT / PIVOT / MILESTONE badges |
| `src/components/EvidenceFooter.vue` | Outcome + drift diagnosis panel |
| `src/views/TrajectoryList.vue` | Index page composing FilterBar + table |
| `src/views/TrajectoryDetail.vue` | Narrative timeline composing Hero + Phase sections + Footer |
| `src/App.vue` | Root layout with `<router-view>` |
| `src/main.ts` | Vue app entry point |

### traj-viz/scripts/

| File | Responsibility |
|---|---|
| `start.sh` | Launch backend + frontend dev servers |
| `build.sh` | Build frontend, start production mode |

---

## Task 1: traj-data — Converter Core (JSONL → Trajectory Turns)

**Files:**
- Create: `traj-data/converter.py`
- Create: `traj-data/tests/test_converter.py`
- Create: `traj-data/requirements.txt`

- [ ] **Step 1: Create project structure**

```bash
cd /Users/xd/Desktop/project-logs
mkdir -p traj-data/tests traj-data/wzp traj-data/zzj
```

- [ ] **Step 2: Write requirements.txt**

Create `traj-data/requirements.txt`:
```
pytest>=8.0.0
```

- [ ] **Step 3: Write failing tests for JSONL parsing**

Create `traj-data/tests/test_converter.py`:
```python
"""Tests for JSONL-to-trajectory converter."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

# Will be implemented in converter.py
from converter import (
    parse_jsonl,
    extract_text_content,
    extract_thinking_content,
    extract_tool_calls,
    is_system_message,
    build_trajectory,
    convert_session,
)


# ── Fixtures ────────────────────────────────────────────────


def _make_user_msg(text: str, uuid: str = "u1", parent: str = "", ts: str = "2026-03-01T10:00:00Z") -> dict:
    return {
        "type": "user",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": ts,
        "userType": "external",
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
    }


def _make_assistant_thinking(thinking: str, uuid: str = "a1", parent: str = "u1", ts: str = "2026-03-01T10:00:05Z") -> dict:
    return {
        "type": "assistant",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": ts,
        "userType": "external",
        "message": {"role": "assistant", "content": [{"type": "thinking", "thinking": thinking}]},
    }


def _make_assistant_tool_use(name: str, input_data: dict, tool_id: str = "tool1", uuid: str = "a2", parent: str = "a1", ts: str = "2026-03-01T10:00:06Z") -> dict:
    return {
        "type": "assistant",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": ts,
        "userType": "external",
        "message": {"role": "assistant", "content": [{"type": "tool_use", "id": tool_id, "name": name, "input": input_data}]},
    }


def _make_tool_result(tool_use_id: str, result: str, uuid: str = "tr1", parent: str = "a2", ts: str = "2026-03-01T10:00:07Z") -> dict:
    return {
        "type": "user",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": ts,
        "userType": "external",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": [{"type": "text", "text": result}]}]},
    }


def _make_assistant_text(text: str, uuid: str = "a3", parent: str = "tr1", ts: str = "2026-03-01T10:00:10Z") -> dict:
    return {
        "type": "assistant",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": ts,
        "userType": "external",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def _write_jsonl(entries: list[dict], path: str) -> None:
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


# ── Content extraction tests ───────────────────────────────


class TestExtractTextContent:
    def test_string_content(self):
        assert extract_text_content("hello world") == "hello world"

    def test_list_with_text_blocks(self):
        content = [{"type": "text", "text": "hello"}, {"type": "text", "text": " world"}]
        assert extract_text_content(content) == "hello world"

    def test_list_without_text_blocks(self):
        content = [{"type": "tool_use", "name": "Read"}]
        assert extract_text_content(content) is None

    def test_empty(self):
        assert extract_text_content(None) is None
        assert extract_text_content("") is None
        assert extract_text_content([]) is None


class TestExtractThinkingContent:
    def test_with_thinking_block(self):
        content = [{"type": "thinking", "thinking": "Let me analyze..."}]
        assert extract_thinking_content(content) == "Let me analyze..."

    def test_no_thinking(self):
        content = [{"type": "text", "text": "hello"}]
        assert extract_thinking_content(content) is None

    def test_string_content(self):
        assert extract_thinking_content("hello") is None


class TestExtractToolCalls:
    def test_single_tool(self):
        content = [{"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "/a.py"}}]
        result = extract_tool_calls(content)
        assert len(result) == 1
        assert result[0]["name"] == "Read"

    def test_multiple_tools(self):
        content = [
            {"type": "tool_use", "id": "t1", "name": "Read", "input": {}},
            {"type": "text", "text": "reading..."},
            {"type": "tool_use", "id": "t2", "name": "Grep", "input": {}},
        ]
        result = extract_tool_calls(content)
        assert len(result) == 2

    def test_no_tools(self):
        assert extract_tool_calls("hello") == []
        assert extract_tool_calls([{"type": "text", "text": "hi"}]) == []


class TestIsSystemMessage:
    def test_system_prefixes(self):
        assert is_system_message("This session is being continued from...") is True
        assert is_system_message("<system-reminder>something</system-reminder>") is True
        assert is_system_message("<command-name>/model</command-name>") is True
        assert is_system_message("Base directory for this skill: /path") is True
        assert is_system_message("[Image: screenshot.png]") is True

    def test_normal_messages(self):
        assert is_system_message("请帮我修改子弹速度") is False
        assert is_system_message("OK") is False


# ── JSONL parsing tests ────────────────────────────────────


class TestParseJsonl:
    def test_basic_parsing(self, tmp_path):
        entries = [
            _make_user_msg("hello"),
            _make_assistant_text("hi there"),
        ]
        f = tmp_path / "session.jsonl"
        _write_jsonl(entries, str(f))
        result = parse_jsonl(str(f))
        assert len(result) == 2
        assert result[0]["type"] == "user"
        assert result[1]["type"] == "assistant"

    def test_skips_queue_operations(self, tmp_path):
        entries = [
            {"type": "queue-operation", "timestamp": "2026-03-01T10:00:00Z"},
            _make_user_msg("hello"),
        ]
        f = tmp_path / "session.jsonl"
        _write_jsonl(entries, str(f))
        result = parse_jsonl(str(f))
        assert len(result) == 1

    def test_skips_bad_json(self, tmp_path):
        f = tmp_path / "session.jsonl"
        with open(f, "w") as fh:
            fh.write('{"type": "user", "uuid": "u1"}\n')
            fh.write("not valid json\n")
            fh.write('{"type": "assistant", "uuid": "a1"}\n')
        result = parse_jsonl(str(f))
        assert len(result) == 2


# ── Trajectory building tests ──────────────────────────────


class TestBuildTrajectory:
    def test_tool_use_cycle(self):
        """user -> thinking -> tool_use -> tool_result -> text response"""
        entries = [
            _make_user_msg("请读取文件"),
            _make_assistant_thinking("Let me read the file"),
            _make_assistant_tool_use("Read", {"file_path": "/a.py"}),
            _make_tool_result("tool1", "file contents here"),
            _make_assistant_text("文件内容如下..."),
        ]
        traj, history = build_trajectory(entries, "test-session")
        assert len(traj) >= 1
        # First real action should be the Read tool
        read_step = next(s for s in traj if "Read" in s["action"])
        assert read_step["thought"] == "Let me read the file"
        assert "Read" in read_step["action"]
        assert "file contents here" in read_step["observation"]

    def test_text_only_response(self):
        """user -> text response (no tools)"""
        entries = [
            _make_user_msg("你好"),
            _make_assistant_text("你好！有什么可以帮你的？"),
        ]
        traj, history = build_trajectory(entries, "test-session")
        assert len(traj) >= 1
        step = traj[0]
        assert step["action"] == "respond_to_user()"

    def test_multi_tool_in_one_message(self):
        """Assistant message with 2 tool_use blocks → 2 trajectory steps"""
        entries = [
            _make_user_msg("搜索并读取"),
            _make_assistant_thinking("I'll search then read"),
            {
                "type": "assistant",
                "uuid": "a2",
                "parentUuid": "a1",
                "timestamp": "2026-03-01T10:00:06Z",
                "userType": "external",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "id": "t1", "name": "Grep", "input": {"pattern": "hello"}},
                        {"type": "tool_use", "id": "t2", "name": "Read", "input": {"file_path": "/b.py"}},
                    ],
                },
            },
            _make_tool_result("t1", "grep results", uuid="tr1", parent="a2", ts="2026-03-01T10:00:07Z"),
            _make_tool_result("t2", "file contents", uuid="tr2", parent="a2", ts="2026-03-01T10:00:08Z"),
        ]
        traj, history = build_trajectory(entries, "test-session")
        tool_steps = [s for s in traj if s["action"] != "respond_to_user()"]
        assert len(tool_steps) == 2
        assert "Grep" in tool_steps[0]["action"]
        assert "Read" in tool_steps[1]["action"]
        # Both share the same thought
        assert tool_steps[0]["thought"] == tool_steps[1]["thought"]

    def test_system_messages_filtered(self):
        """System-injected messages should not appear in trajectory"""
        entries = [
            _make_user_msg("<system-reminder>some reminder</system-reminder>"),
            _make_user_msg("请帮我修改代码"),
            _make_assistant_text("好的"),
        ]
        traj, history = build_trajectory(entries, "test-session")
        for step in traj:
            assert "<system-reminder>" not in step.get("thought", "")

    def test_execution_time(self):
        """execution_time = delta between consecutive timestamps"""
        entries = [
            _make_user_msg("请读取", ts="2026-03-01T10:00:00Z"),
            _make_assistant_thinking("reading", uuid="a1", ts="2026-03-01T10:00:05Z"),
            _make_assistant_tool_use("Read", {"file_path": "/a.py"}, uuid="a2", parent="a1", ts="2026-03-01T10:00:06Z"),
            _make_tool_result("tool1", "contents", uuid="tr1", parent="a2", ts="2026-03-01T10:00:10Z"),
        ]
        traj, history = build_trajectory(entries, "test-session")
        read_step = next(s for s in traj if "Read" in s["action"])
        # execution_time should be a positive number (seconds between messages)
        assert read_step["execution_time"] > 0


# ── Full session conversion test ───────────────────────────


class TestConvertSession:
    def test_produces_valid_traj(self, tmp_path):
        entries = [
            _make_user_msg("请帮我创建一个文件"),
            _make_assistant_thinking("I'll create the file"),
            _make_assistant_tool_use("Write", {"file_path": "/new.py", "content": "print('hi')"}),
            _make_tool_result("tool1", "File created"),
            _make_assistant_text("文件已创建"),
        ]
        jsonl_path = tmp_path / "abc12345-test-session.jsonl"
        _write_jsonl(entries, str(jsonl_path))

        result = convert_session(str(jsonl_path), project="zzj")
        assert "trajectory" in result
        assert "history" in result
        assert "info" in result
        assert "phases" in result
        assert "markers" in result
        assert result["info"]["project"] == "zzj"
        assert result["info"]["task_id"] == "zzj/abc12345"
        assert result["info"]["total_turns"] == len(result["trajectory"])
        assert result["info"]["total_tool_calls"] >= 1

    def test_action_formatting(self, tmp_path):
        entries = [
            _make_user_msg("读取文件"),
            _make_assistant_thinking("reading"),
            _make_assistant_tool_use("Read", {"file_path": "/Users/xd/test.py", "limit": 50}),
            _make_tool_result("tool1", "file content"),
        ]
        jsonl_path = tmp_path / "def67890-test.jsonl"
        _write_jsonl(entries, str(jsonl_path))

        result = convert_session(str(jsonl_path), project="wzp")
        tool_step = next(s for s in result["trajectory"] if "Read" in s["action"])
        # Action should be formatted as tool_name(key=val, ...)
        assert tool_step["action"].startswith("Read(")
        assert "file_path=" in tool_step["action"]
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
python -m pytest tests/test_converter.py -v 2>&1 | head -30
```
Expected: ModuleNotFoundError for `converter`

- [ ] **Step 5: Implement converter.py**

Create `traj-data/converter.py`:
```python
"""Convert Claude Code JSONL sessions to SWE-agent .traj format.

Usage:
    python converter.py --wzp-workspace <path> --zzj-workspace <path> --output-dir .
    python converter.py --session <path.jsonl> --project <name> --output-dir .
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ── System message filtering ──────────────────────────────

SYSTEM_PREFIXES = [
    "This session is being continued",
    "<image-caption>",
    "[Image: original",
    "[Image: ",
    "[Request interrupted by user]",
    "Base directory for this skill:",
    "<system-reminder>",
    "<command-name>",
    "<local-command",
]


def is_system_message(text: str) -> bool:
    """Return True if text is a system-injected message (not real user input)."""
    stripped = text.strip()
    return any(stripped.startswith(p) for p in SYSTEM_PREFIXES)


# ── Content extraction ────────────────────────────────────


def extract_text_content(content: Any) -> Optional[str]:
    """Extract concatenated text from content (string or block list)."""
    if content is None:
        return None
    if isinstance(content, str):
        return content.strip() if content.strip() else None
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        combined = " ".join(p for p in parts if p)
        return combined if combined else None
    return None


def extract_thinking_content(content: Any) -> Optional[str]:
    """Extract thinking text from assistant content blocks."""
    if content is None or isinstance(content, str):
        return None
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "thinking":
                parts.append(block.get("thinking", ""))
        combined = " ".join(p for p in parts if p)
        return combined if combined else None
    return None


def extract_tool_calls(content: Any) -> list[dict]:
    """Extract tool_use blocks from content."""
    if content is None or isinstance(content, str):
        return []
    if isinstance(content, list):
        return [
            block for block in content
            if isinstance(block, dict) and block.get("type") == "tool_use"
        ]
    return []


def _extract_tool_result_text(content: Any) -> str:
    """Extract text from a tool_result content block."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif "content" in block:
                    parts.append(str(block["content"])[:500])
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(p for p in parts if p)
    return str(content)[:500] if content else ""


# ── JSONL parsing ─────────────────────────────────────────


def parse_jsonl(filepath: str) -> list[dict]:
    """Parse a JSONL file, returning only user/assistant entries (skip queue-operations, bad lines)."""
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") in ("user", "assistant"):
                entries.append(entry)
    return entries


# ── Action formatting ─────────────────────────────────────


def _format_action(tool_name: str, tool_input: dict) -> str:
    """Format a tool call as tool_name(key=val, ...)."""
    if not tool_input:
        return f"{tool_name}()"
    parts = []
    for k, v in tool_input.items():
        if isinstance(v, str):
            # Truncate long values
            display = v if len(v) <= 80 else v[:77] + "..."
            parts.append(f'{k}="{display}"')
        elif isinstance(v, bool):
            parts.append(f"{k}={str(v).lower()}")
        elif isinstance(v, (int, float)):
            parts.append(f"{k}={v}")
        else:
            parts.append(f"{k}=...")
    return f"{tool_name}({', '.join(parts)})"


# ── Timestamp helpers ─────────────────────────────────────


def _parse_ts(ts_str: str) -> Optional[datetime]:
    """Parse an ISO timestamp string, tolerating various formats."""
    if not ts_str:
        return None
    ts_str = ts_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return None


def _delta_seconds(ts1: str, ts2: str) -> float:
    """Return seconds between two timestamps. Returns 0.0 on parse failure."""
    dt1 = _parse_ts(ts1)
    dt2 = _parse_ts(ts2)
    if dt1 and dt2:
        return abs((dt2 - dt1).total_seconds())
    return 0.0


# ── Trajectory building ──────────────────────────────────


def build_trajectory(entries: list[dict], session_id: str, agent_prefix: str = "") -> tuple[list[dict], list[list[dict]]]:
    """Convert parsed JSONL entries into (trajectory_steps, history).

    Returns:
        trajectory: list of {thought, action, observation, state, execution_time}
        history: list of message groups (SWE-agent history format)
    """
    trajectory = []
    history = []
    current_history_group = []
    prev_ts = ""
    pending_thought = ""
    tool_result_map: dict[str, str] = {}  # tool_use_id -> result text

    i = 0
    while i < len(entries):
        entry = entries[i]
        msg_type = entry.get("type")
        content = entry.get("message", {}).get("content", "")
        timestamp = entry.get("timestamp", "")

        if msg_type == "user":
            # Check if this is a tool result
            if isinstance(content, list):
                is_tool_result = any(
                    isinstance(b, dict) and b.get("type") == "tool_result"
                    for b in content
                )
                if is_tool_result:
                    # Map tool results by tool_use_id
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            tid = block.get("tool_use_id", "")
                            result_text = _extract_tool_result_text(block.get("content", ""))
                            tool_result_map[tid] = result_text
                    i += 1
                    continue

            # External user message
            text = extract_text_content(content)
            if text and is_system_message(text):
                i += 1
                continue

            # Start new history group
            if current_history_group:
                history.append(current_history_group)
            current_history_group = [{"role": "user", "content": text or ""}]

            if not prev_ts:
                prev_ts = timestamp

            i += 1
            continue

        if msg_type == "assistant":
            thinking = extract_thinking_content(content)
            text = extract_text_content(content)
            tool_calls = extract_tool_calls(content)

            if thinking:
                pending_thought = thinking

            if tool_calls:
                # Each tool_use becomes its own trajectory step
                for tc in tool_calls:
                    tool_name = tc.get("name", "unknown")
                    tool_input = tc.get("input", {})
                    tool_id = tc.get("id", "")

                    action = _format_action(tool_name, tool_input)
                    if agent_prefix:
                        action = f"[subagent:{agent_prefix}] {action}"

                    # Look ahead for matching tool_result
                    observation = tool_result_map.pop(tool_id, "")

                    exec_time = _delta_seconds(prev_ts, timestamp)

                    trajectory.append({
                        "thought": pending_thought or "",
                        "action": action,
                        "observation": observation[:2000],
                        "state": "",
                        "execution_time": round(exec_time, 1),
                    })
                    prev_ts = timestamp

                current_history_group.append({"role": "assistant", "content": text or pending_thought or ""})
                pending_thought = ""

            elif text:
                # Text-only response (no tools)
                exec_time = _delta_seconds(prev_ts, timestamp)
                trajectory.append({
                    "thought": text,
                    "action": "respond_to_user()",
                    "observation": "",
                    "state": "",
                    "execution_time": round(exec_time, 1),
                })
                current_history_group.append({"role": "assistant", "content": text})
                pending_thought = ""
                prev_ts = timestamp

        i += 1

    # Flush last history group
    if current_history_group:
        history.append(current_history_group)

    return trajectory, history


# ── Session conversion ────────────────────────────────────


def convert_session(jsonl_path: str, project: str) -> dict:
    """Convert a single JSONL session file into a .traj dict.

    Also processes subagent files if they exist alongside the session.
    """
    from phase_tagger import tag_phases, detect_markers

    session_id = Path(jsonl_path).stem
    session_hash = session_id[:8]

    # Parse main conversation
    entries = parse_jsonl(jsonl_path)
    if not entries:
        return _empty_traj(project, session_id, session_hash)

    trajectory, history = build_trajectory(entries, session_id)

    # Parse subagents
    subagent_dir = Path(jsonl_path).parent / session_id / "subagents"
    subagent_count = 0
    if subagent_dir.is_dir():
        for agent_file in sorted(subagent_dir.glob("agent-*.jsonl")):
            agent_id = agent_file.stem[len("agent-"):]
            agent_entries = parse_jsonl(str(agent_file))
            if agent_entries:
                agent_traj, _ = build_trajectory(agent_entries, session_id, agent_prefix=agent_id)
                trajectory.extend(agent_traj)
                subagent_count += 1

    # Compute info
    timestamps = [e.get("timestamp", "") for e in entries if e.get("timestamp")]
    start_time = timestamps[0] if timestamps else ""
    end_time = timestamps[-1] if timestamps else ""
    duration = _delta_seconds(start_time, end_time)

    tool_call_count = sum(1 for s in trajectory if s["action"] != "respond_to_user()")
    model = ""
    for e in entries:
        m = e.get("message", {}).get("model")
        if m:
            model = m
            break

    # Phase tagging and marker detection
    phases = tag_phases(trajectory)
    markers = detect_markers(trajectory)

    return {
        "trajectory": trajectory,
        "history": history,
        "info": {
            "task_id": f"{project}/{session_hash}",
            "project": project,
            "session_id": session_id,
            "status": "completed",
            "start_time": start_time,
            "end_time": end_time,
            "duration_sec": round(duration, 1),
            "total_turns": len(trajectory),
            "total_tool_calls": tool_call_count,
            "total_subagents": subagent_count,
            "exit_reason": "end_of_conversation",
            "submission": None,
            "model": model,
        },
        "phases": phases,
        "markers": markers,
    }


def _empty_traj(project: str, session_id: str, session_hash: str) -> dict:
    return {
        "trajectory": [],
        "history": [],
        "info": {
            "task_id": f"{project}/{session_hash}",
            "project": project,
            "session_id": session_id,
            "status": "empty",
            "start_time": "",
            "end_time": "",
            "duration_sec": 0,
            "total_turns": 0,
            "total_tool_calls": 0,
            "total_subagents": 0,
            "exit_reason": "no_messages",
            "submission": None,
            "model": "",
        },
        "phases": [],
        "markers": [],
    }


# ── CLI ───────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Convert Claude Code sessions to SWE-agent .traj format")
    parser.add_argument("--wzp-workspace", help="Path to wzp workspace directory")
    parser.add_argument("--zzj-workspace", help="Path to zzj workspace directory")
    parser.add_argument("--session", help="Path to a single session JSONL file")
    parser.add_argument("--project", help="Project name (used with --session)")
    parser.add_argument("--output-dir", default=".", help="Output directory (default: .)")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    total_sessions = 0
    total_turns = 0
    total_tools = 0

    if args.session:
        if not args.project:
            print("Error: --project is required with --session")
            sys.exit(1)
        proj_dir = output_dir / args.project
        proj_dir.mkdir(parents=True, exist_ok=True)
        traj = convert_session(args.session, args.project)
        session_hash = traj["info"]["task_id"].split("/")[1]
        out_path = proj_dir / f"{session_hash}.traj"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(traj, f, ensure_ascii=False, indent=2)
        print(f"  → {out_path} ({traj['info']['total_turns']} turns)")
        total_sessions = 1
        total_turns = traj["info"]["total_turns"]
        total_tools = traj["info"]["total_tool_calls"]
    else:
        workspaces = {}
        if args.wzp_workspace:
            workspaces["wzp"] = args.wzp_workspace
        if args.zzj_workspace:
            workspaces["zzj"] = args.zzj_workspace

        if not workspaces:
            print("Error: provide --wzp-workspace and/or --zzj-workspace, or --session")
            sys.exit(1)

        for project, ws_path in workspaces.items():
            proj_dir = output_dir / project
            proj_dir.mkdir(parents=True, exist_ok=True)
            ws = Path(ws_path)
            jsonl_files = sorted(ws.glob("*.jsonl"))
            print(f"\n[{project}] Converting {len(jsonl_files)} sessions...")

            for jsonl_file in jsonl_files:
                traj = convert_session(str(jsonl_file), project)
                if traj["info"]["status"] == "empty":
                    continue
                session_hash = traj["info"]["task_id"].split("/")[1]
                out_path = proj_dir / f"{session_hash}.traj"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(traj, f, ensure_ascii=False, indent=2)
                total_sessions += 1
                total_turns += traj["info"]["total_turns"]
                total_tools += traj["info"]["total_tool_calls"]
                marker_count = len(traj["markers"])
                phase_count = len(traj["phases"])
                print(f"  {session_hash} → {traj['info']['total_turns']} turns, {phase_count} phases, {marker_count} markers")

    print(f"\n✅ Done: {total_sessions} sessions, {total_turns} turns, {total_tools} tool calls")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
python -m pytest tests/test_converter.py -v
```
Expected: Most tests pass (phase_tagger import will fail — that's Task 2)

- [ ] **Step 7: Commit**

```bash
cd /Users/xd/Desktop/project-logs
git init traj-data
cd traj-data
git add converter.py tests/test_converter.py requirements.txt
git commit -m "feat: add JSONL-to-traj converter core"
```

---

## Task 2: traj-data — Phase Tagger & Marker Detection

**Files:**
- Create: `traj-data/phase_tagger.py`
- Create: `traj-data/tests/test_phase_tagger.py`

- [ ] **Step 1: Write failing tests for phase tagger**

Create `traj-data/tests/test_phase_tagger.py`:
```python
"""Tests for heuristic phase tagging and marker detection."""
from __future__ import annotations

import pytest

from phase_tagger import (
    classify_action,
    tag_phases,
    detect_markers,
    PHASE_NAMES,
)


# ── Action classification ─────────────────────────────────


class TestClassifyAction:
    def test_localization_tools(self):
        assert classify_action('Read(file_path="/a.py")') == "localization"
        assert classify_action('Glob(pattern="**/*.py")') == "localization"
        assert classify_action('Grep(pattern="hello")') == "localization"
        assert classify_action('LSP(operation="goToDefinition")') == "localization"

    def test_editing_tools(self):
        assert classify_action('Write(file_path="/a.py", content="...")') == "editing"
        assert classify_action('Edit(file_path="/a.py", old_string="x", new_string="y")') == "editing"

    def test_verification_bash(self):
        assert classify_action('Bash(command="pytest tests/ -v")') == "verification"
        assert classify_action('Bash(command="npm test")') == "verification"
        assert classify_action('Bash(command="cargo test")') == "verification"

    def test_submission_bash(self):
        assert classify_action('Bash(command="git commit -m \\"feat: add\\"")') == "submission"
        assert classify_action('Bash(command="git push origin main")') == "submission"

    def test_general_bash(self):
        assert classify_action('Bash(command="ls -la")') == "editing"
        assert classify_action('Bash(command="pip install requests")') == "editing"

    def test_respond_to_user(self):
        assert classify_action("respond_to_user()") == "inherited"

    def test_agent_tool(self):
        assert classify_action('[subagent:abc123] Read(file_path="/a.py")') == "localization"
        assert classify_action('Agent(prompt="research this")') == "localization"


# ── Phase tagging ─────────────────────────────────────────


class TestTagPhases:
    def test_single_phase(self):
        trajectory = [
            {"action": 'Read(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Grep(pattern="hello")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        phases = tag_phases(trajectory)
        assert len(phases) == 1
        assert phases[0]["label"] == "localization"
        assert phases[0]["start_turn"] == 0
        assert phases[0]["end_turn"] == 1

    def test_multiple_phases(self):
        trajectory = [
            {"action": 'Read(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Bash(command="pytest")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        phases = tag_phases(trajectory)
        assert len(phases) == 3
        assert phases[0]["label"] == "localization"
        assert phases[1]["label"] == "editing"
        assert phases[2]["label"] == "verification"

    def test_consecutive_merge(self):
        trajectory = [
            {"action": 'Read(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Read(file_path="/b.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Grep(pattern="x")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        phases = tag_phases(trajectory)
        assert len(phases) == 2
        assert phases[0]["label"] == "localization"
        assert phases[0]["end_turn"] == 2  # Merged 3 localization turns
        assert phases[1]["label"] == "editing"

    def test_respond_inherits_phase(self):
        trajectory = [
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": "respond_to_user()", "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Bash(command="pytest")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        phases = tag_phases(trajectory)
        # respond_to_user inherits "editing" from previous → merged with previous editing
        assert phases[0]["label"] == "editing"
        assert phases[0]["end_turn"] == 1

    def test_empty_trajectory(self):
        assert tag_phases([]) == []

    def test_phase_names(self):
        """Phase entries should include name and name_zh."""
        trajectory = [
            {"action": 'Read(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        phases = tag_phases(trajectory)
        assert phases[0]["name"] == "Localization"
        assert phases[0]["name_zh"] == "问题定位"


# ── Marker detection ──────────────────────────────────────


class TestDetectMarkers:
    def test_drift_detection(self):
        """4+ consecutive edits without verification → drift-start"""
        trajectory = [
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Edit(file_path="/b.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Write(file_path="/c.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Edit(file_path="/d.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        markers = detect_markers(trajectory)
        drift_markers = [m for m in markers if m["type"] == "drift-start"]
        assert len(drift_markers) >= 1

    def test_search_loop_detection(self):
        """4+ consecutive search actions → search-loop"""
        trajectory = [
            {"action": 'Read(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Glob(pattern="*.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Grep(pattern="x")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Read(file_path="/b.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        markers = detect_markers(trajectory)
        search_markers = [m for m in markers if m["type"] == "search-loop"]
        assert len(search_markers) >= 1

    def test_churn_detection(self):
        """Same file edited 3+ times in 5 turns → churn"""
        trajectory = [
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Read(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Read(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        markers = detect_markers(trajectory)
        churn_markers = [m for m in markers if m["type"] == "churn"]
        assert len(churn_markers) >= 1

    def test_milestone_markers(self):
        """First and last turns always get milestone markers."""
        trajectory = [
            {"action": "respond_to_user()", "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": "respond_to_user()", "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        markers = detect_markers(trajectory)
        milestones = [m for m in markers if m["type"] == "milestone"]
        assert any(m["turn"] == 0 for m in milestones)
        assert any(m["turn"] == 2 for m in milestones)

    def test_no_markers_on_short_trajectory(self):
        """Short trajectories should only have milestones, not drift/churn."""
        trajectory = [
            {"action": 'Edit(file_path="/a.py")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
            {"action": 'Bash(command="pytest")', "thought": "", "observation": "", "state": "", "execution_time": 1.0},
        ]
        markers = detect_markers(trajectory)
        non_milestone = [m for m in markers if m["type"] != "milestone"]
        assert len(non_milestone) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
python -m pytest tests/test_phase_tagger.py -v 2>&1 | head -10
```
Expected: ModuleNotFoundError for `phase_tagger`

- [ ] **Step 3: Implement phase_tagger.py**

Create `traj-data/phase_tagger.py`:
```python
"""Heuristic phase tagging and drift/marker detection for trajectories."""
from __future__ import annotations

import re
from typing import Optional

PHASE_NAMES = {
    "setup": ("Task Setup", "任务注入"),
    "localization": ("Localization", "问题定位"),
    "editing": ("Editing", "补丁生成"),
    "verification": ("Verification", "验证与测试"),
    "submission": ("Submission", "提交"),
}

LOCALIZATION_TOOLS = {"Read", "Glob", "Grep", "LSP", "Agent"}
EDITING_TOOLS = {"Write", "Edit", "NotebookEdit"}
VERIFICATION_PATTERNS = ["pytest", "test", "npm test", "cargo test", "npm run test"]
SUBMISSION_PATTERNS = ["git commit", "git push"]


def _extract_tool_name(action: str) -> str:
    """Extract the tool name from an action string like 'Read(file_path="...")' or '[subagent:x] Read(...)'."""
    # Strip subagent prefix
    stripped = re.sub(r"^\[subagent:[^\]]+\]\s*", "", action)
    # Extract tool name before first '('
    match = re.match(r"^(\w+)\(", stripped)
    return match.group(1) if match else stripped


def _extract_file_path(action: str) -> Optional[str]:
    """Extract file_path value from an action string."""
    match = re.search(r'file_path="([^"]*)"', action)
    return match.group(1) if match else None


def classify_action(action: str) -> str:
    """Classify a single action string into a phase label.

    Returns one of: 'localization', 'editing', 'verification', 'submission', 'inherited'.
    """
    if action == "respond_to_user()":
        return "inherited"

    tool_name = _extract_tool_name(action)

    if tool_name in LOCALIZATION_TOOLS:
        return "localization"

    if tool_name in EDITING_TOOLS:
        return "editing"

    if tool_name == "Bash":
        # Extract command content from action string
        cmd_match = re.search(r'command="([^"]*)"', action)
        cmd = cmd_match.group(1).lower() if cmd_match else ""

        for pattern in SUBMISSION_PATTERNS:
            if pattern in cmd:
                return "submission"

        for pattern in VERIFICATION_PATTERNS:
            if pattern in cmd:
                return "verification"

        return "editing"  # Default for general Bash commands

    return "editing"  # Default fallback


def tag_phases(trajectory: list[dict]) -> list[dict]:
    """Assign phase labels to trajectory turns and merge consecutive same-label phases.

    Returns a list of phase dicts: {name, name_zh, start_turn, end_turn, label}.
    """
    if not trajectory:
        return []

    # Classify each turn
    labels = []
    for step in trajectory:
        label = classify_action(step["action"])
        labels.append(label)

    # Resolve "inherited" labels
    for i, label in enumerate(labels):
        if label == "inherited":
            labels[i] = labels[i - 1] if i > 0 else "editing"

    # Merge consecutive same-label turns into phases
    phases = []
    current_label = labels[0]
    start = 0

    for i in range(1, len(labels)):
        if labels[i] != current_label:
            en, zh = PHASE_NAMES.get(current_label, (current_label.title(), current_label))
            phases.append({
                "name": en,
                "name_zh": zh,
                "start_turn": start,
                "end_turn": i - 1,
                "label": current_label,
            })
            current_label = labels[i]
            start = i

    # Last phase
    en, zh = PHASE_NAMES.get(current_label, (current_label.title(), current_label))
    phases.append({
        "name": en,
        "name_zh": zh,
        "start_turn": start,
        "end_turn": len(labels) - 1,
        "label": current_label,
    })

    return phases


def detect_markers(trajectory: list[dict]) -> list[dict]:
    """Detect drift, search-loop, churn, and milestone markers.

    Returns a list of marker dicts: {turn, type, reason}.
    """
    markers = []
    n = len(trajectory)

    if n == 0:
        return markers

    # Milestone markers: first and last turn
    markers.append({"turn": 0, "type": "milestone", "reason": "Session start"})
    if n > 1:
        markers.append({"turn": n - 1, "type": "milestone", "reason": "Session end"})

    # Classify all actions
    labels = [classify_action(step["action"]) for step in trajectory]
    # Resolve inherited
    for i, label in enumerate(labels):
        if label == "inherited":
            labels[i] = labels[i - 1] if i > 0 else "editing"

    # Drift detection: 4+ consecutive editing turns without verification
    consecutive_edit = 0
    drift_marked = False
    for i, label in enumerate(labels):
        if label == "editing":
            consecutive_edit += 1
            if consecutive_edit >= 4 and not drift_marked:
                markers.append({
                    "turn": i,
                    "type": "drift-start",
                    "reason": f"{consecutive_edit} consecutive edits without verification",
                })
                drift_marked = True
        elif label == "verification":
            consecutive_edit = 0
            drift_marked = False
        else:
            # Localization or submission breaks the edit streak too
            if label != "editing":
                consecutive_edit = 0
                drift_marked = False

    # Search-loop detection: 4+ consecutive localization turns
    consecutive_search = 0
    search_marked = False
    for i, label in enumerate(labels):
        if label == "localization":
            consecutive_search += 1
            if consecutive_search >= 4 and not search_marked:
                markers.append({
                    "turn": i,
                    "type": "search-loop",
                    "reason": f"Extended search without editing — possible localization failure",
                })
                search_marked = True
        else:
            consecutive_search = 0
            search_marked = False

    # Churn detection: same file edited 3+ times in 5-turn windows
    churn_files: set[str] = set()
    for i in range(n):
        window = trajectory[max(0, i - 4):i + 1]
        file_edits: dict[str, int] = {}
        for step in window:
            action = step["action"]
            tool_name = _extract_tool_name(action)
            if tool_name in ("Edit", "Write"):
                fp = _extract_file_path(action)
                if fp:
                    file_edits[fp] = file_edits.get(fp, 0) + 1

        for fp, count in file_edits.items():
            if count >= 3 and fp not in churn_files:
                churn_files.add(fp)
                markers.append({
                    "turn": i,
                    "type": "churn",
                    "reason": f"Repeated edits to {fp} — possible edit recovery failure",
                })

    # Sort markers by turn
    markers.sort(key=lambda m: (m["turn"], m["type"]))

    return markers
```

- [ ] **Step 4: Run all traj-data tests**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
python -m pytest tests/ -v
```
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
git add phase_tagger.py tests/test_phase_tagger.py
git commit -m "feat: add phase tagger with drift/marker detection"
```

---

## Task 3: traj-data — Run Converter on Real Data

**Files:**
- Modify: `traj-data/converter.py` (if issues found)
- Output: `traj-data/wzp/*.traj`, `traj-data/zzj/*.traj`

- [ ] **Step 1: Run converter on a single zzj session first**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
python converter.py \
  --session ../zzj-project-logs/.claude/projects/-workspace/019c99e5-fc70-74ac-9cc2-d9091e4478a3.jsonl \
  --project zzj \
  --output-dir .
```
Expected: Creates `zzj/019c99e5.traj`, prints turn/phase/marker counts

- [ ] **Step 2: Inspect the output .traj file**

```bash
python -c "
import json
with open('zzj/019c99e5.traj') as f:
    traj = json.load(f)
print(f'Turns: {len(traj[\"trajectory\"])}')
print(f'Phases: {len(traj[\"phases\"])}')
print(f'Markers: {len(traj[\"markers\"])}')
print(f'Info: {json.dumps(traj[\"info\"], indent=2)}')
for i, step in enumerate(traj['trajectory'][:3]):
    print(f'  Step {i}: action={step[\"action\"][:60]}, exec_time={step[\"execution_time\"]}s')
"
```
Expected: Valid structured output with trajectory steps, phases, markers

- [ ] **Step 3: Convert all sessions from both projects**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
python converter.py \
  --wzp-workspace ../wzp-project-logs/.claude/projects/-workspace \
  --zzj-workspace ../zzj-project-logs/.claude/projects/-workspace \
  --output-dir .
```
Expected: Converts 105 wzp + 57 zzj sessions, prints summary stats

- [ ] **Step 4: Verify output files**

```bash
echo "WZP .traj files:" && ls wzp/*.traj | wc -l
echo "ZZJ .traj files:" && ls zzj/*.traj | wc -l
```

- [ ] **Step 5: Commit converted data**

```bash
cd /Users/xd/Desktop/project-logs/traj-data
git add wzp/ zzj/
git commit -m "data: convert 162 Claude Code sessions to .traj format"
```

---

## Task 4: traj-viz — Backend Models & Loader

**Files:**
- Create: `traj-viz/backend/models.py`
- Create: `traj-viz/backend/loader.py`
- Create: `traj-viz/backend/requirements.txt`

- [ ] **Step 1: Create project structure**

```bash
cd /Users/xd/Desktop/project-logs
mkdir -p traj-viz/backend/tests traj-viz/scripts
```

- [ ] **Step 2: Write requirements.txt**

Create `traj-viz/backend/requirements.txt`:
```
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.9.0
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 3: Write models.py**

Create `traj-viz/backend/models.py`:
```python
"""Pydantic response models for the trajectory visualization API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TurnStep(BaseModel):
    step: int
    thought: str
    action: str
    observation: str
    phase: str
    tone: str
    execution_time: float
    marker: Optional[str] = None
    marker_reason: Optional[str] = None


class Phase(BaseModel):
    name: str
    name_zh: str
    start_turn: int
    end_turn: int
    label: str


class Marker(BaseModel):
    turn: int
    type: str
    reason: str


class TrajectorySummary(BaseModel):
    task_id: str
    project: str
    session_id: str
    status: str
    start_time: str
    end_time: str
    duration_sec: float
    total_turns: int
    total_tool_calls: int
    total_subagents: int
    first_user_prompt: str
    phase_labels: list[str]
    marker_count: int
    exit_reason: str


class TrajectoryDetail(TrajectorySummary):
    trajectory: list[TurnStep]
    phases: list[Phase]
    markers: list[Marker]


class ProjectSummary(BaseModel):
    project: str
    project_name: str
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

- [ ] **Step 4: Write loader.py**

Create `traj-viz/backend/loader.py`:
```python
"""Load .traj files from disk into in-memory index."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from models import (
    Marker,
    Phase,
    PhaseStat,
    ProjectSummary,
    ToolStat,
    TrajectoryDetail,
    TrajectorySummary,
    TurnStep,
)

PROJECT_NAMES = {
    "wzp": "脑力大冒险",
    "zzj": "超时空要塞",
}

PHASE_TONE_MAP = {
    "setup": "gold",
    "localization": "blue",
    "editing": "violet",
    "verification": "green",
    "submission": "gold",
}

MARKER_TONE_OVERRIDES = {"drift-start", "churn", "search-loop"}


def _compute_tone(phase_label: str, marker_type: Optional[str]) -> str:
    if marker_type in MARKER_TONE_OVERRIDES:
        return "orange"
    return PHASE_TONE_MAP.get(phase_label, "violet")


def _extract_tool_name(action: str) -> str:
    stripped = re.sub(r"^\[subagent:[^\]]+\]\s*", "", action)
    match = re.match(r"^(\w+)\(", stripped)
    return match.group(1) if match else "unknown"


def _first_user_prompt(history: list) -> str:
    for group in history:
        for msg in group:
            if msg.get("role") == "user":
                text = msg.get("content", "")
                return text[:120] if text else ""
    return ""


class TrajectoryLoader:
    """Scans traj-data/ directories and provides trajectory data."""

    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._index: list[TrajectorySummary] = []
        self._mtime_cache: dict[str, float] = {}
        self._detail_cache: dict[str, TrajectoryDetail] = {}
        self._scan()

    def _scan(self) -> None:
        """Scan data directory for .traj files and build summary index."""
        self._index = []
        for project_dir in sorted(self._data_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            project = project_dir.name
            if project not in PROJECT_NAMES:
                continue
            for traj_file in sorted(project_dir.glob("*.traj")):
                summary = self._load_summary(traj_file, project)
                if summary:
                    self._index.append(summary)

    def _load_summary(self, path: Path, project: str) -> Optional[TrajectorySummary]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        info = data.get("info", {})
        if info.get("status") == "empty":
            return None

        phases = data.get("phases", [])
        markers = data.get("markers", [])
        history = data.get("history", [])

        self._mtime_cache[info.get("task_id", "")] = path.stat().st_mtime

        return TrajectorySummary(
            task_id=info.get("task_id", ""),
            project=project,
            session_id=info.get("session_id", ""),
            status=info.get("status", "unknown"),
            start_time=info.get("start_time", ""),
            end_time=info.get("end_time", ""),
            duration_sec=info.get("duration_sec", 0),
            total_turns=info.get("total_turns", 0),
            total_tool_calls=info.get("total_tool_calls", 0),
            total_subagents=info.get("total_subagents", 0),
            first_user_prompt=_first_user_prompt(history),
            phase_labels=[p.get("label", "") for p in phases],
            marker_count=len([m for m in markers if m.get("type") != "milestone"]),
            exit_reason=info.get("exit_reason", ""),
        )

    def list_trajectories(self, project: Optional[str] = None, q: Optional[str] = None) -> list[TrajectorySummary]:
        result = self._index
        if project:
            result = [t for t in result if t.project == project]
        if q:
            q_lower = q.lower()
            result = [t for t in result if q_lower in t.first_user_prompt.lower()]
        return sorted(result, key=lambda t: t.start_time, reverse=True)

    def get_detail(self, project: str, session_hash: str) -> Optional[TrajectoryDetail]:
        task_id = f"{project}/{session_hash}"

        # Check cache and mtime
        traj_path = self._data_dir / project / f"{session_hash}.traj"
        if not traj_path.exists():
            return None

        current_mtime = traj_path.stat().st_mtime
        cached_mtime = self._mtime_cache.get(task_id, 0)

        if task_id in self._detail_cache and current_mtime <= cached_mtime:
            return self._detail_cache[task_id]

        try:
            with open(traj_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        info = data.get("info", {})
        phases_raw = data.get("phases", [])
        markers_raw = data.get("markers", [])
        trajectory_raw = data.get("trajectory", [])
        history = data.get("history", [])

        # Build marker lookup: turn -> marker
        marker_map: dict[int, dict] = {}
        for m in markers_raw:
            marker_map.setdefault(m["turn"], m)

        # Build phase label lookup: turn -> label
        phase_label_map: dict[int, str] = {}
        for p in phases_raw:
            for t in range(p["start_turn"], p["end_turn"] + 1):
                phase_label_map[t] = p["label"]

        # Build TurnStep list
        turn_steps = []
        for i, step in enumerate(trajectory_raw):
            phase_label = phase_label_map.get(i, "editing")
            marker = marker_map.get(i)
            marker_type = marker["type"] if marker else None
            tone = _compute_tone(phase_label, marker_type)

            turn_steps.append(TurnStep(
                step=i,
                thought=step.get("thought", ""),
                action=step.get("action", ""),
                observation=step.get("observation", ""),
                phase=phase_label,
                tone=tone,
                execution_time=step.get("execution_time", 0),
                marker=marker_type,
                marker_reason=marker["reason"] if marker else None,
            ))

        detail = TrajectoryDetail(
            task_id=task_id,
            project=project,
            session_id=info.get("session_id", ""),
            status=info.get("status", "unknown"),
            start_time=info.get("start_time", ""),
            end_time=info.get("end_time", ""),
            duration_sec=info.get("duration_sec", 0),
            total_turns=info.get("total_turns", 0),
            total_tool_calls=info.get("total_tool_calls", 0),
            total_subagents=info.get("total_subagents", 0),
            first_user_prompt=_first_user_prompt(history),
            phase_labels=[p.get("label", "") for p in phases_raw],
            marker_count=len([m for m in markers_raw if m.get("type") != "milestone"]),
            exit_reason=info.get("exit_reason", ""),
            trajectory=turn_steps,
            phases=[Phase(**p) for p in phases_raw],
            markers=[Marker(**m) for m in markers_raw],
        )

        self._detail_cache[task_id] = detail
        self._mtime_cache[task_id] = current_mtime
        return detail

    def list_projects(self) -> list[ProjectSummary]:
        projects: dict[str, list[TrajectorySummary]] = {}
        for t in self._index:
            projects.setdefault(t.project, []).append(t)

        result = []
        for proj, trajs in sorted(projects.items()):
            dates = [t.start_time[:10] for t in trajs if t.start_time]
            date_range = f"{min(dates)} ~ {max(dates)}" if dates else ""
            result.append(ProjectSummary(
                project=proj,
                project_name=PROJECT_NAMES.get(proj, proj),
                total_sessions=len(trajs),
                total_turns=sum(t.total_turns for t in trajs),
                total_tool_calls=sum(t.total_tool_calls for t in trajs),
                date_range=date_range,
            ))
        return result

    def tool_stats(self) -> list[ToolStat]:
        tool_counts: dict[str, int] = {}
        for traj_path in self._data_dir.rglob("*.traj"):
            try:
                with open(traj_path) as f:
                    data = json.load(f)
                for step in data.get("trajectory", []):
                    tool = _extract_tool_name(step.get("action", ""))
                    if tool != "respond_to_user":
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
            except (json.JSONDecodeError, OSError):
                continue
        return sorted(
            [ToolStat(tool_name=k, count=v) for k, v in tool_counts.items()],
            key=lambda x: x.count,
            reverse=True,
        )

    def phase_stats(self) -> list[PhaseStat]:
        phase_turns: dict[str, int] = {}
        phase_sessions: dict[str, int] = {}
        for t in self._index:
            seen = set()
            for label in t.phase_labels:
                if label not in seen:
                    phase_sessions[label] = phase_sessions.get(label, 0) + 1
                    seen.add(label)
            # Count turns per phase from phase_labels list
            for label in t.phase_labels:
                phase_turns[label] = phase_turns.get(label, 0) + 1

        result = []
        for phase, turns in phase_turns.items():
            sessions = phase_sessions.get(phase, 1)
            result.append(PhaseStat(
                phase=phase,
                total_turns=turns,
                avg_turns_per_session=round(turns / sessions, 1),
            ))
        return sorted(result, key=lambda x: x.total_turns, reverse=True)
```

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz
git init
git add backend/models.py backend/loader.py backend/requirements.txt
git commit -m "feat: add backend models and .traj file loader"
```

---

## Task 5: traj-viz — Backend API (FastAPI)

**Files:**
- Create: `traj-viz/backend/main.py`
- Create: `traj-viz/backend/tests/test_api.py`

- [ ] **Step 1: Write failing tests**

Create `traj-viz/backend/tests/__init__.py` (empty file).

Create `traj-viz/backend/tests/test_api.py`:
```python
"""Tests for the trajectory visualization API."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from main import create_app


@pytest.fixture
def sample_traj_dir(tmp_path):
    """Create a minimal traj-data directory with sample .traj files."""
    wzp_dir = tmp_path / "wzp"
    wzp_dir.mkdir()
    zzj_dir = tmp_path / "zzj"
    zzj_dir.mkdir()

    sample = {
        "trajectory": [
            {"thought": "Let me read", "action": 'Read(file_path="/a.py")', "observation": "file content", "state": "", "execution_time": 2.0},
            {"thought": "I'll edit", "action": 'Edit(file_path="/a.py")', "observation": "edited", "state": "", "execution_time": 3.0},
            {"thought": "Running tests", "action": 'Bash(command="pytest")', "observation": "PASSED", "state": "", "execution_time": 5.0},
        ],
        "history": [[{"role": "user", "content": "请帮我修改文件"}]],
        "info": {
            "task_id": "zzj/abc12345",
            "project": "zzj",
            "session_id": "abc12345-full-uuid",
            "status": "completed",
            "start_time": "2026-03-01T10:00:00Z",
            "end_time": "2026-03-01T10:10:00Z",
            "duration_sec": 600,
            "total_turns": 3,
            "total_tool_calls": 3,
            "total_subagents": 0,
            "exit_reason": "end_of_conversation",
            "submission": None,
            "model": "claude-sonnet-4",
        },
        "phases": [
            {"name": "Localization", "name_zh": "问题定位", "start_turn": 0, "end_turn": 0, "label": "localization"},
            {"name": "Editing", "name_zh": "补丁生成", "start_turn": 1, "end_turn": 1, "label": "editing"},
            {"name": "Verification", "name_zh": "验证与测试", "start_turn": 2, "end_turn": 2, "label": "verification"},
        ],
        "markers": [
            {"turn": 0, "type": "milestone", "reason": "Session start"},
            {"turn": 2, "type": "milestone", "reason": "Session end"},
        ],
    }

    with open(zzj_dir / "abc12345.traj", "w") as f:
        json.dump(sample, f)

    return tmp_path


@pytest.fixture
def app(sample_traj_dir):
    return create_app(data_dir=str(sample_traj_dir))


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_list_trajectories(client):
    resp = await client.get("/api/trajectories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "zzj/abc12345"


@pytest.mark.anyio
async def test_list_trajectories_filter_project(client):
    resp = await client.get("/api/trajectories?project=wzp")
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    resp = await client.get("/api/trajectories?project=zzj")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.anyio
async def test_list_trajectories_search(client):
    resp = await client.get("/api/trajectories?q=修改")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/api/trajectories?q=不存在的文字")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.anyio
async def test_get_detail(client):
    resp = await client.get("/api/trajectories/zzj/abc12345")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "zzj/abc12345"
    assert len(data["trajectory"]) == 3
    assert len(data["phases"]) == 3
    assert data["trajectory"][0]["tone"] == "blue"
    assert data["trajectory"][1]["tone"] == "violet"
    assert data["trajectory"][2]["tone"] == "green"


@pytest.mark.anyio
async def test_get_detail_not_found(client):
    resp = await client.get("/api/trajectories/zzj/nonexist")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_list_projects(client):
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["project"] == "zzj"
    assert data[0]["project_name"] == "超时空要塞"


@pytest.mark.anyio
async def test_analytics_tools(client):
    resp = await client.get("/api/analytics/tools")
    assert resp.status_code == 200
    data = resp.json()
    tool_names = [t["tool_name"] for t in data]
    assert "Read" in tool_names
    assert "Edit" in tool_names


@pytest.mark.anyio
async def test_analytics_phases(client):
    resp = await client.get("/api/analytics/phases")
    assert resp.status_code == 200
    data = resp.json()
    labels = [p["phase"] for p in data]
    assert "localization" in labels
```

- [ ] **Step 2: Write main.py**

Create `traj-viz/backend/main.py`:
```python
"""FastAPI application for SWE-Agent Trajectory Visualization."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from loader import TrajectoryLoader
from models import (
    PhaseStat,
    ProjectSummary,
    ToolStat,
    TrajectoryDetail,
    TrajectorySummary,
)

_DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "traj-data",
)


def create_app(data_dir: str = _DEFAULT_DATA_DIR) -> FastAPI:
    app = FastAPI(title="SWE-Agent Trajectory Viewer", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    loader = TrajectoryLoader(data_dir)

    @app.get("/api/trajectories", response_model=list[TrajectorySummary])
    def list_trajectories(
        project: Optional[str] = Query(None),
        q: Optional[str] = Query(None),
    ):
        return loader.list_trajectories(project=project, q=q)

    @app.get("/api/trajectories/{project}/{session_hash}", response_model=TrajectoryDetail)
    def get_trajectory(project: str, session_hash: str):
        detail = loader.get_detail(project, session_hash)
        if detail is None:
            raise HTTPException(status_code=404, detail="Trajectory not found")
        return detail

    @app.get("/api/projects", response_model=list[ProjectSummary])
    def list_projects():
        return loader.list_projects()

    @app.get("/api/analytics/tools", response_model=list[ToolStat])
    def analytics_tools():
        return loader.tool_stats()

    @app.get("/api/analytics/phases", response_model=list[PhaseStat])
    def analytics_phases():
        return loader.phase_stats()

    # Serve frontend build
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "dist",
    )
    if os.path.isdir(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

    return app


app = create_app()
```

- [ ] **Step 3: Run tests**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz/backend
pip install -r requirements.txt -q
pip install anyio pytest-anyio -q
python -m pytest tests/test_api.py -v
```
Expected: All 8 tests pass

- [ ] **Step 4: Commit**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz
git add backend/main.py backend/tests/
git commit -m "feat: add FastAPI endpoints for trajectory API"
```

---

## Task 6: traj-viz — Frontend Scaffold (Vue 3 + Vite + Router)

**Files:**
- Create: `traj-viz/frontend/` (full Vite + Vue 3 scaffold)
- Create: `traj-viz/frontend/src/styles/variables.css`
- Create: `traj-viz/frontend/src/styles/base.css`
- Create: `traj-viz/frontend/src/types/trajectory.ts`
- Create: `traj-viz/frontend/src/api/client.ts`
- Create: `traj-viz/frontend/src/router/index.ts`
- Create: `traj-viz/frontend/src/App.vue`
- Create: `traj-viz/frontend/src/main.ts`

- [ ] **Step 1: Scaffold Vue project with Vite**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz/frontend
npm create vite@latest . -- --template vue-ts
```

If the directory is not empty, accept the overwrite prompt.

- [ ] **Step 2: Install dependencies**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz/frontend
npm install vue-router@4
```

- [ ] **Step 3: Create CSS variables**

Create `traj-viz/frontend/src/styles/variables.css`:
```css
:root {
  --bg-primary: #0E0E10;
  --bg-card: rgba(255, 255, 255, 0.02);
  --bg-card-hover: rgba(255, 255, 255, 0.04);

  --text-primary: #F2EEE8;
  --text-secondary: #B7AA99;
  --text-tertiary: #7A7068;
  --text-muted: #5A524A;

  --accent-gold: #C9B896;
  --border-subtle: rgba(184, 156, 108, 0.12);
  --border-faint: rgba(255, 255, 255, 0.03);

  --tone-blue: #5B8DEF;
  --tone-violet: #9B6DFF;
  --tone-green: #4ADE80;
  --tone-orange: #F59E0B;
  --tone-red: #EF4444;
  --tone-gold: #C9B896;

  --font-sans: 'Inter', 'SF Pro', -apple-system, system-ui, sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}
```

- [ ] **Step 4: Create base CSS**

Create `traj-viz/frontend/src/styles/base.css`:
```css
@import './variables.css';

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-sans);
  line-height: 1.6;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

a {
  color: inherit;
  text-decoration: none;
}

.mono {
  font-family: var(--font-mono);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 48px;
}

@media (max-width: 768px) {
  .container {
    padding: 0 24px;
  }
}
```

- [ ] **Step 5: Create TypeScript types**

Create `traj-viz/frontend/src/types/trajectory.ts`:
```typescript
export interface TurnStep {
  step: number
  thought: string
  action: string
  observation: string
  phase: string
  tone: string
  execution_time: number
  marker: string | null
  marker_reason: string | null
}

export interface Phase {
  name: string
  name_zh: string
  start_turn: number
  end_turn: number
  label: string
}

export interface Marker {
  turn: number
  type: string
  reason: string
}

export interface TrajectorySummary {
  task_id: string
  project: string
  session_id: string
  status: string
  start_time: string
  end_time: string
  duration_sec: number
  total_turns: number
  total_tool_calls: number
  total_subagents: number
  first_user_prompt: string
  phase_labels: string[]
  marker_count: number
  exit_reason: string
}

export interface TrajectoryDetail extends TrajectorySummary {
  trajectory: TurnStep[]
  phases: Phase[]
  markers: Marker[]
}

export interface ProjectSummary {
  project: string
  project_name: string
  total_sessions: number
  total_turns: number
  total_tool_calls: number
  date_range: string
}
```

- [ ] **Step 6: Create API client**

Create `traj-viz/frontend/src/api/client.ts`:
```typescript
const BASE_URL = '/api'

async function fetchJSON<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`)
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`)
  }
  return resp.json()
}

export const api = {
  listTrajectories(project?: string, q?: string) {
    const params = new URLSearchParams()
    if (project) params.set('project', project)
    if (q) params.set('q', q)
    const qs = params.toString()
    return fetchJSON<import('../types/trajectory').TrajectorySummary[]>(
      `/trajectories${qs ? '?' + qs : ''}`
    )
  },

  getTrajectory(project: string, sessionHash: string) {
    return fetchJSON<import('../types/trajectory').TrajectoryDetail>(
      `/trajectories/${project}/${sessionHash}`
    )
  },

  listProjects() {
    return fetchJSON<import('../types/trajectory').ProjectSummary[]>('/projects')
  },
}
```

- [ ] **Step 7: Create router**

Create `traj-viz/frontend/src/router/index.ts`:
```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'list',
      component: () => import('../views/TrajectoryList.vue'),
    },
    {
      path: '/trajectory/:project/:sessionHash',
      name: 'detail',
      component: () => import('../views/TrajectoryDetail.vue'),
      props: true,
    },
  ],
})

export default router
```

- [ ] **Step 8: Create App.vue and main.ts**

Replace `traj-viz/frontend/src/App.vue`:
```vue
<template>
  <router-view />
</template>
```

Replace `traj-viz/frontend/src/main.ts`:
```typescript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/base.css'

createApp(App).use(router).mount('#app')
```

- [ ] **Step 9: Configure Vite proxy**

Replace `traj-viz/frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 10: Verify build**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz/frontend
npx tsc --noEmit
npm run build
```
Expected: Build succeeds (views are stub components — we create them next)

- [ ] **Step 11: Commit**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz
git add frontend/
git commit -m "feat: scaffold Vue 3 frontend with router and design tokens"
```

---

## Task 7: traj-viz — Frontend List View

**Files:**
- Create: `traj-viz/frontend/src/components/FilterBar.vue`
- Create: `traj-viz/frontend/src/components/PhasePills.vue`
- Create: `traj-viz/frontend/src/views/TrajectoryList.vue`

- [ ] **Step 1: Create FilterBar component**

Create `traj-viz/frontend/src/components/FilterBar.vue`:
```vue
<script setup lang="ts">
defineProps<{
  activeProject: string
  searchQuery: string
}>()

const emit = defineEmits<{
  'update:activeProject': [value: string]
  'update:searchQuery': [value: string]
}>()

const projects = [
  { key: '', label: 'All' },
  { key: 'wzp', label: 'WZP', badge: '脑力大冒险' },
  { key: 'zzj', label: 'ZZJ', badge: '超时空要塞' },
]
</script>

<template>
  <div class="filters">
    <button
      v-for="p in projects"
      :key="p.key"
      class="filter-btn"
      :class="{ active: activeProject === p.key }"
      @click="emit('update:activeProject', p.key)"
    >
      <span v-if="p.badge" class="proj-badge" :class="p.key">{{ p.label }}</span>
      <template v-else>{{ p.label }}</template>
    </button>
    <input
      class="search-input"
      placeholder="Search trajectories..."
      :value="searchQuery"
      @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
    />
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 20px 0;
}

.filter-btn {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: transparent;
  color: var(--text-tertiary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  font-family: var(--font-sans);
}

.filter-btn:hover {
  border-color: rgba(184, 156, 108, 0.3);
  color: var(--text-secondary);
}

.filter-btn.active {
  background: rgba(184, 156, 108, 0.12);
  border-color: rgba(184, 156, 108, 0.3);
  color: var(--accent-gold);
}

.proj-badge {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 3px;
  margin-right: 4px;
}

.proj-badge.wzp {
  background: rgba(91, 141, 239, 0.12);
  color: var(--tone-blue);
}

.proj-badge.zzj {
  background: rgba(155, 109, 255, 0.12);
  color: var(--tone-violet);
}

.search-input {
  margin-left: auto;
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  font-size: 13px;
  width: 240px;
  outline: none;
  font-family: var(--font-sans);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-input:focus {
  border-color: rgba(184, 156, 108, 0.3);
}
</style>
```

- [ ] **Step 2: Create PhasePills component**

Create `traj-viz/frontend/src/components/PhasePills.vue`:
```vue
<script setup lang="ts">
defineProps<{
  labels: string[]
}>()

const toneMap: Record<string, string> = {
  setup: 'var(--tone-gold)',
  localization: 'var(--tone-blue)',
  editing: 'var(--tone-violet)',
  verification: 'var(--tone-green)',
  submission: 'var(--tone-gold)',
}
</script>

<template>
  <div class="phase-pills">
    <div
      v-for="(label, i) in labels"
      :key="i"
      class="phase-pill"
      :style="{ background: toneMap[label] || 'var(--text-muted)' }"
    />
  </div>
</template>

<style scoped>
.phase-pills {
  display: flex;
  gap: 3px;
  margin-top: 6px;
}

.phase-pill {
  width: 18px;
  height: 4px;
  border-radius: 2px;
  opacity: 0.7;
}
</style>
```

- [ ] **Step 3: Create TrajectoryList view**

Create `traj-viz/frontend/src/views/TrajectoryList.vue`:
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import type { TrajectorySummary, ProjectSummary } from '../types/trajectory'
import FilterBar from '../components/FilterBar.vue'
import PhasePills from '../components/PhasePills.vue'

const router = useRouter()
const trajectories = ref<TrajectorySummary[]>([])
const projects = ref<ProjectSummary[]>([])
const activeProject = ref('')
const searchQuery = ref('')
const loading = ref(true)

onMounted(async () => {
  const [t, p] = await Promise.all([
    api.listTrajectories(),
    api.listProjects(),
  ])
  trajectories.value = t
  projects.value = p
  loading.value = false
})

const filtered = computed(() => {
  let result = trajectories.value
  if (activeProject.value) {
    result = result.filter(t => t.project === activeProject.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => t.first_user_prompt.toLowerCase().includes(q))
  }
  return result
})

const totalSessions = computed(() => projects.value.reduce((s, p) => s + p.total_sessions, 0))

function formatDuration(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`
  if (sec < 3600) return `${Math.round(sec / 60)}m`
  const h = Math.floor(sec / 3600)
  const m = Math.round((sec % 3600) / 60)
  return `${h}h ${m}m`
}

function formatDate(ts: string): string {
  return ts ? ts.slice(0, 10) : ''
}

function formatTime(ts: string): string {
  return ts ? ts.slice(11, 16) : ''
}

function goToDetail(t: TrajectorySummary) {
  const [project, hash] = t.task_id.split('/')
  router.push({ name: 'detail', params: { project, sessionHash: hash } })
}
</script>

<template>
  <div>
    <div class="container">
      <header class="page-header">
        <h1>SWE Agent Trajectories</h1>
        <p class="desc">Claude Code production sessions converted to SWE-agent format</p>
      </header>

      <div class="agg-stats">
        <div class="agg-stat" v-for="p in projects" :key="p.project">
          <span class="val">{{ p.total_sessions }}</span>
          <span class="lbl">{{ p.project.toUpperCase() }}</span>
        </div>
        <div class="agg-stat">
          <span class="val">{{ totalSessions }}</span>
          <span class="lbl">Total</span>
        </div>
      </div>

      <FilterBar
        :activeProject="activeProject"
        :searchQuery="searchQuery"
        @update:activeProject="activeProject = $event"
        @update:searchQuery="searchQuery = $event"
      />

      <div v-if="loading" class="loading">Loading trajectories...</div>

      <div v-else class="traj-list">
        <div class="col-header">
          <span>Task ID</span>
          <span>Session</span>
          <span>Date</span>
          <span>Duration</span>
          <span>Turns</span>
          <span>Tools</span>
        </div>

        <div
          v-for="t in filtered"
          :key="t.task_id"
          class="traj-item"
          @click="goToDetail(t)"
        >
          <div class="traj-id">
            <span class="status-dot" :class="t.status" />
            {{ t.task_id.split('/')[1] }}
          </div>
          <div class="traj-info">
            <div class="traj-title">
              <span class="proj-badge" :class="t.project">{{ t.project.toUpperCase() }}</span>
              {{ t.first_user_prompt.slice(0, 40) || '(empty)' }}
            </div>
            <div class="traj-preview">{{ t.first_user_prompt }}</div>
            <PhasePills :labels="t.phase_labels" />
          </div>
          <div class="traj-time">
            {{ formatDate(t.start_time) }}<br />
            <span class="time-detail">{{ formatTime(t.start_time) }}</span>
          </div>
          <div class="traj-duration">{{ formatDuration(t.duration_sec) }}</div>
          <div class="traj-turns">{{ t.total_turns }}</div>
          <div class="traj-tools">{{ t.total_tool_calls }}</div>
        </div>

        <div class="list-footer">
          Showing {{ filtered.length }} of {{ trajectories.length }} trajectories
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  padding: 48px 0 32px;
  border-bottom: 1px solid var(--border-subtle);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 6px;
}

.agg-stats {
  padding: 24px 0;
  display: flex;
  gap: 40px;
  border-bottom: var(--border-faint) solid 1px;
}

.agg-stat {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.agg-stat .val {
  font-size: 28px;
  font-weight: 600;
  color: var(--accent-gold);
}

.agg-stat .lbl {
  font-size: 12px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.loading {
  padding: 48px 0;
  text-align: center;
  color: var(--text-muted);
}

.col-header {
  display: grid;
  grid-template-columns: 100px 1fr 120px 100px 80px 60px;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.col-header span:nth-child(n+3) {
  text-align: right;
}

.traj-item {
  display: grid;
  grid-template-columns: 100px 1fr 120px 100px 80px 60px;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-faint);
  cursor: pointer;
  transition: background 0.15s;
}

.traj-item:hover {
  background: var(--bg-card-hover);
  margin: 0 -16px;
  padding: 16px;
  border-radius: 8px;
}

.traj-id {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-secondary);
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.status-dot.completed { background: var(--tone-green); }
.status-dot.empty { background: var(--text-muted); }

.traj-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.traj-preview {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 500px;
}

.proj-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-right: 6px;
}

.proj-badge.wzp { background: rgba(91, 141, 239, 0.12); color: var(--tone-blue); }
.proj-badge.zzj { background: rgba(155, 109, 255, 0.12); color: var(--tone-violet); }

.traj-time {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: right;
}

.time-detail {
  font-size: 11px;
  color: var(--text-muted);
}

.traj-duration, .traj-turns {
  text-align: right;
  font-size: 13px;
  color: var(--text-secondary);
}

.traj-tools {
  text-align: right;
  font-size: 13px;
  color: var(--text-tertiary);
}

.list-footer {
  padding: 20px 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}
</style>
```

- [ ] **Step 4: Verify build**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz/frontend
npx tsc --noEmit && npm run build
```
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz
git add frontend/src/components/FilterBar.vue frontend/src/components/PhasePills.vue frontend/src/views/TrajectoryList.vue
git commit -m "feat: add trajectory list view with filters and phase pills"
```

---

## Task 8: traj-viz — Frontend Detail View

**Files:**
- Create: `traj-viz/frontend/src/components/HeroSection.vue`
- Create: `traj-viz/frontend/src/components/MarkerBadge.vue`
- Create: `traj-viz/frontend/src/components/TurnCard.vue`
- Create: `traj-viz/frontend/src/components/PhaseSection.vue`
- Create: `traj-viz/frontend/src/components/EvidenceFooter.vue`
- Create: `traj-viz/frontend/src/views/TrajectoryDetail.vue`

- [ ] **Step 1: Create HeroSection**

Create `traj-viz/frontend/src/components/HeroSection.vue`:
```vue
<script setup lang="ts">
import type { TrajectoryDetail } from '../types/trajectory'

const props = defineProps<{ data: TrajectoryDetail }>()

const projectNames: Record<string, string> = {
  wzp: '脑力大冒险',
  zzj: '超时空要塞',
}

function formatDuration(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`
  if (sec < 3600) return `${Math.round(sec / 60)}m`
  const h = Math.floor(sec / 3600)
  const m = Math.round((sec % 3600) / 60)
  return `${h}h ${m}m`
}
</script>

<template>
  <div class="hero">
    <div class="hero-left">
      <h1>SWE Agent Trajectory</h1>
      <div class="subtitle">From issue ingestion to patch submission</div>
      <div class="project-badge">{{ data.project.toUpperCase() }} &middot; {{ projectNames[data.project] || data.project }}</div>
    </div>
    <div class="hero-stats">
      <div class="stat-item">
        <div class="stat-value mono">{{ data.task_id.split('/')[1] }}</div>
        <div class="stat-label">Task ID</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ data.total_turns }}</div>
        <div class="stat-label">Total Turns</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatDuration(data.duration_sec) }}</div>
        <div class="stat-label">Duration</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ data.status }}</div>
        <div class="stat-label">Status</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ data.total_tool_calls }}</div>
        <div class="stat-label">Tool Calls</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ data.total_subagents }}</div>
        <div class="stat-label">Subagents</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero {
  padding: 60px 0 40px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.hero-left h1 {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 6px;
  font-style: italic;
}

.project-badge {
  display: inline-block;
  margin-top: 12px;
  padding: 4px 12px;
  border-radius: 4px;
  background: rgba(184, 156, 108, 0.12);
  color: var(--accent-gold);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, auto);
  gap: 24px;
  text-align: right;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
}

@media (max-width: 768px) {
  .hero { flex-direction: column; }
  .hero-stats { margin-top: 24px; text-align: left; }
}
</style>
```

- [ ] **Step 2: Create MarkerBadge**

Create `traj-viz/frontend/src/components/MarkerBadge.vue`:
```vue
<script setup lang="ts">
defineProps<{ type: string }>()

const styles: Record<string, string> = {
  'drift-start': 'drift',
  'search-loop': 'drift',
  'churn': 'drift',
  'milestone': 'milestone',
  'pivot': 'pivot',
}

const labels: Record<string, string> = {
  'drift-start': 'DRIFT',
  'search-loop': 'SEARCH LOOP',
  'churn': 'CHURN',
  'milestone': 'MILESTONE',
  'pivot': 'PIVOT',
}
</script>

<template>
  <span class="marker-badge" :class="styles[type] || 'drift'">
    {{ labels[type] || type.toUpperCase() }}
  </span>
</template>

<style scoped>
.marker-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-left: 12px;
  vertical-align: middle;
}

.drift {
  background: rgba(239, 68, 68, 0.15);
  color: var(--tone-red);
}

.pivot {
  background: rgba(245, 158, 11, 0.15);
  color: var(--tone-orange);
}

.milestone {
  background: rgba(201, 184, 150, 0.15);
  color: var(--accent-gold);
}
</style>
```

- [ ] **Step 3: Create TurnCard**

Create `traj-viz/frontend/src/components/TurnCard.vue`:
```vue
<script setup lang="ts">
import { ref } from 'vue'
import type { TurnStep } from '../types/trajectory'
import MarkerBadge from './MarkerBadge.vue'

const props = defineProps<{ step: TurnStep; startTime?: string }>()
const expanded = ref(false)

function formatTimeOffset(sec: number): string {
  if (sec < 60) return `T+${Math.round(sec)}s`
  if (sec < 3600) {
    const m = Math.floor(sec / 60)
    const s = Math.round(sec % 60)
    return `T+${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  return `T+${h}:${String(m).padStart(2, '0')}:00`
}
</script>

<template>
  <div class="turn-card" :class="'tone-' + step.tone">
    <div class="turn-meta">
      <div class="step-num">#{{ String(step.step + 1).padStart(2, '0') }}</div>
      {{ formatTimeOffset(step.execution_time) }}
    </div>
    <div class="turn-content">
      <div class="turn-title">
        {{ step.action.split('(')[0] }}
        <MarkerBadge v-if="step.marker" :type="step.marker" />
      </div>
      <div class="turn-action mono">{{ step.action }}</div>
      <div v-if="step.observation" class="turn-summary">
        {{ step.observation.slice(0, 200) }}{{ step.observation.length > 200 ? '...' : '' }}
      </div>
      <div class="tags">
        <span class="tag" :class="step.phase">{{ step.phase }}</span>
      </div>
      <div class="expand-toggle" @click="expanded = !expanded">
        {{ expanded ? '▾ Hide raw data' : '▸ Show raw thought / action / observation' }}
      </div>
      <div v-if="expanded" class="raw-data">
        <div class="raw-section">
          <div class="raw-label">Thought</div>
          <pre>{{ step.thought || '(none)' }}</pre>
        </div>
        <div class="raw-section">
          <div class="raw-label">Action</div>
          <pre>{{ step.action }}</pre>
        </div>
        <div class="raw-section">
          <div class="raw-label">Observation</div>
          <pre>{{ step.observation || '(none)' }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.turn-card {
  position: relative;
  padding: 24px 0 32px 0;
  border-bottom: 1px solid var(--border-faint);
  padding-left: 24px;
}

.turn-card::before {
  content: '';
  position: absolute;
  left: -4px;
  top: 30px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-secondary);
}

.tone-blue::before { background: var(--tone-blue); }
.tone-violet::before { background: var(--tone-violet); }
.tone-green::before { background: var(--tone-green); }
.tone-orange::before { background: var(--tone-orange); }
.tone-red::before { background: var(--tone-red); }
.tone-gold::before { background: var(--tone-gold); box-shadow: 0 0 8px rgba(201,184,150,0.4); }

.turn-meta {
  position: absolute;
  left: -100px;
  top: 24px;
  width: 80px;
  text-align: right;
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.4;
}

.step-num {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.turn-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.turn-action {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 10px;
  word-break: break-all;
}

.turn-summary {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  max-width: 720px;
}

.tags {
  margin-top: 10px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-tertiary);
}

.tag.localization { color: var(--tone-blue); background: rgba(91,141,239,0.1); }
.tag.editing { color: var(--tone-violet); background: rgba(155,109,255,0.1); }
.tag.verification { color: var(--tone-green); background: rgba(74,222,128,0.1); }
.tag.submission { color: var(--accent-gold); background: rgba(201,184,150,0.1); }
.tag.setup { color: var(--accent-gold); background: rgba(201,184,150,0.1); }

.expand-toggle {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
}

.expand-toggle:hover { color: var(--text-secondary); }

.raw-data {
  margin-top: 12px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  border: 1px solid var(--border-faint);
}

.raw-section {
  margin-bottom: 12px;
}

.raw-section:last-child { margin-bottom: 0; }

.raw-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.raw-data pre {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}
</style>
```

- [ ] **Step 4: Create PhaseSection**

Create `traj-viz/frontend/src/components/PhaseSection.vue`:
```vue
<script setup lang="ts">
import type { Phase, TurnStep } from '../types/trajectory'
import TurnCard from './TurnCard.vue'

defineProps<{
  phase: Phase
  steps: TurnStep[]
}>()
</script>

<template>
  <div class="phase-section">
    <div class="phase-header">
      <h2>{{ phase.name_zh }}</h2>
      <div class="phase-subtitle">{{ phase.name }} &middot; Turns {{ phase.start_turn + 1 }}–{{ phase.end_turn + 1 }}</div>
    </div>
    <div class="timeline">
      <TurnCard
        v-for="step in steps"
        :key="step.step"
        :step="step"
      />
    </div>
  </div>
</template>

<style scoped>
.phase-header {
  padding: 48px 0 24px;
  border-bottom: 1px solid rgba(184, 156, 108, 0.1);
}

.phase-header h2 {
  font-size: 20px;
  font-weight: 500;
  color: var(--accent-gold);
}

.phase-subtitle {
  font-size: 13px;
  color: var(--text-tertiary);
  font-style: italic;
  margin-top: 4px;
}

.timeline {
  position: relative;
  padding-left: 100px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 80px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(to bottom, rgba(184,156,108,0.3), rgba(184,156,108,0.05));
}
</style>
```

- [ ] **Step 5: Create EvidenceFooter**

Create `traj-viz/frontend/src/components/EvidenceFooter.vue`:
```vue
<script setup lang="ts">
import type { TrajectoryDetail, Marker } from '../types/trajectory'

const props = defineProps<{ data: TrajectoryDetail }>()

const nonMilestoneMarkers = props.data.markers.filter(m => m.type !== 'milestone')
</script>

<template>
  <div class="evidence-footer">
    <h2>诊断摘要</h2>
    <div class="boxes">
      <div class="result-box" :class="data.status === 'completed' ? 'success' : 'failure'">
        <div class="box-label">OUTCOME</div>
        <div class="box-text">{{ data.status === 'completed' ? 'Completed' : data.status }}</div>
        <div class="box-evidence">{{ data.total_turns }} turns, {{ data.total_tool_calls }} tool calls</div>
      </div>
      <div
        v-for="m in nonMilestoneMarkers"
        :key="`${m.turn}-${m.type}`"
        class="result-box warning"
      >
        <div class="box-label">{{ m.type.toUpperCase().replace('-', ' ') }}</div>
        <div class="box-text">Turn {{ m.turn + 1 }}</div>
        <div class="box-evidence">{{ m.reason }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.evidence-footer {
  padding: 48px 0;
  border-top: 1px solid var(--border-subtle);
}

.evidence-footer h2 {
  font-size: 18px;
  color: var(--accent-gold);
  margin-bottom: 20px;
}

.boxes {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.result-box {
  border-radius: 8px;
  padding: 20px;
  max-width: 400px;
  min-width: 250px;
}

.result-box.success {
  background: rgba(74, 222, 128, 0.04);
  border: 1px solid rgba(74, 222, 128, 0.2);
}

.result-box.failure {
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.15);
}

.result-box.warning {
  background: rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.15);
}

.box-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.success .box-label { color: var(--tone-green); }
.failure .box-label { color: var(--tone-red); }
.warning .box-label { color: var(--tone-orange); }

.box-text {
  font-size: 14px;
  color: var(--text-primary);
}

.box-evidence {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 8px;
}
</style>
```

- [ ] **Step 6: Create TrajectoryDetail view**

Create `traj-viz/frontend/src/views/TrajectoryDetail.vue`:
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import type { TrajectoryDetail } from '../types/trajectory'
import HeroSection from '../components/HeroSection.vue'
import PhaseSection from '../components/PhaseSection.vue'
import EvidenceFooter from '../components/EvidenceFooter.vue'

const props = defineProps<{
  project: string
  sessionHash: string
}>()

const router = useRouter()
const data = ref<TrajectoryDetail | null>(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    data.value = await api.getTrajectory(props.project, props.sessionHash)
  } catch (e: any) {
    error.value = e.message || 'Failed to load trajectory'
  } finally {
    loading.value = false
  }
})

const phasesWithSteps = computed(() => {
  if (!data.value) return []
  return data.value.phases.map(phase => ({
    phase,
    steps: data.value!.trajectory.filter(
      s => s.step >= phase.start_turn && s.step <= phase.end_turn
    ),
  }))
})
</script>

<template>
  <div class="container">
    <button class="back-btn" @click="router.push('/')">← Back to list</button>

    <div v-if="loading" class="loading">Loading trajectory...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else-if="data">
      <HeroSection :data="data" />

      <PhaseSection
        v-for="(ps, i) in phasesWithSteps"
        :key="i"
        :phase="ps.phase"
        :steps="ps.steps"
      />

      <EvidenceFooter :data="data" />
    </template>
  </div>
</template>

<style scoped>
.back-btn {
  margin-top: 24px;
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: transparent;
  color: var(--text-tertiary);
  font-size: 13px;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.15s;
}

.back-btn:hover {
  border-color: rgba(184, 156, 108, 0.3);
  color: var(--text-secondary);
}

.loading, .error {
  padding: 48px 0;
  text-align: center;
  color: var(--text-muted);
}

.error { color: var(--tone-red); }
</style>
```

- [ ] **Step 7: Verify build**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz/frontend
npx tsc --noEmit && npm run build
```
Expected: Build succeeds

- [ ] **Step 8: Commit**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz
git add frontend/src/components/ frontend/src/views/TrajectoryDetail.vue
git commit -m "feat: add trajectory detail view with narrative timeline"
```

---

## Task 9: traj-viz — Launch Scripts & Integration Test

**Files:**
- Create: `traj-viz/scripts/start.sh`
- Create: `traj-viz/scripts/build.sh`

- [ ] **Step 1: Create start.sh**

Create `traj-viz/scripts/start.sh`:
```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "Starting SWE-Agent Trajectory Viewer..."

# Backend
cd backend
pip install -r requirements.txt -q
uvicorn main:app --port 8000 --reload &
BACKEND_PID=$!
echo "Backend: http://localhost:8000 (PID: $BACKEND_PID)"

# Frontend
cd ../frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
echo "Frontend: http://localhost:5173"

echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'" EXIT
wait
```

```bash
chmod +x /Users/xd/Desktop/project-logs/traj-viz/scripts/start.sh
```

- [ ] **Step 2: Create build.sh**

Create `traj-viz/scripts/build.sh`:
```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "Building frontend..."
cd frontend
npm install --silent
npm run build
echo "Frontend built to frontend/dist/"

echo ""
echo "Starting production server..."
cd ../backend
pip install -r requirements.txt -q
uvicorn main:app --port 8000
```

```bash
chmod +x /Users/xd/Desktop/project-logs/traj-viz/scripts/build.sh
```

- [ ] **Step 3: Start the dev servers and verify**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz
bash scripts/start.sh
```

Open http://localhost:5173 in browser. Verify:
1. List view loads with all trajectories
2. Click a trajectory → detail view renders with narrative timeline
3. Phase sections, turn cards, and markers display correctly
4. Back button returns to list view

- [ ] **Step 4: Commit**

```bash
cd /Users/xd/Desktop/project-logs/traj-viz
git add scripts/
git commit -m "feat: add start/build scripts for dev and production"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] 1.1 File system layout → Tasks 1-3
- [x] 1.2 Source data format → Task 1 (parse_jsonl, content extractors)
- [x] 1.3 Output .traj format → Task 1 (convert_session)
- [x] 1.4 Mapping rules → Task 1 (build_trajectory)
- [x] 1.5 Phase tagging → Task 2 (tag_phases)
- [x] 1.6 Drift/marker detection → Task 2 (detect_markers)
- [x] 1.7 Converter CLI → Task 1 (main), Task 3 (real data)
- [x] 2.1 File system layout → Tasks 4-9
- [x] 2.2 Backend API → Tasks 4-5
- [x] 2.3 Frontend design → Tasks 6-8
- [x] 2.4 Scripts → Task 9
- [x] 2.5 Tone mapping → Task 4 (loader._compute_tone)
- [x] 2.6 Three-tier importance → Addressed in TurnCard (expand/collapse), can be refined later

**Placeholder scan:** No TBD/TODO found. All code blocks are complete.

**Type consistency:** Verified: TurnStep, Phase, Marker, TrajectorySummary, TrajectoryDetail — field names and types match across converter.py, models.py, loader.py, trajectory.ts, and all Vue components.
