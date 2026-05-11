"""Tests for the v2 converter."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

# We'll import from converter_v2 once implemented
from converter_v2 import (
    build_messages,
    convert_session_v2,
    is_system_message,
    parse_jsonl,
)


# ---------------------------------------------------------------------------
# Test helpers — construct JSONL entries
# ---------------------------------------------------------------------------

def _user_entry(
    text: str,
    session_id: str = "test-session-001",
    timestamp: str = "2026-04-01T10:00:00.000Z",
    cwd: str = "/workspace",
    version: str = "2.1.4",
    git_branch: str = "",
) -> dict:
    """Build a user text entry."""
    return {
        "type": "user",
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
        "version": version,
        "gitBranch": git_branch,
        "userType": "external",
        "message": {
            "role": "user",
            "content": [{"type": "text", "text": text}],
        },
    }


def _tool_result_entry(
    tool_use_id: str,
    result_text: str,
    session_id: str = "test-session-001",
    timestamp: str = "2026-04-01T10:00:05.000Z",
) -> dict:
    """Build a user entry carrying tool results."""
    return {
        "type": "user",
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": "/workspace",
        "version": "2.1.4",
        "gitBranch": "",
        "userType": "external",
        "message": {
            "role": "user",
            "content": [
                {
                    "tool_use_id": tool_use_id,
                    "type": "tool_result",
                    "content": [{"type": "text", "text": result_text}],
                }
            ],
        },
    }


def _assistant_entry(
    text: str | None = None,
    tool_calls: list[dict] | None = None,
    thinking: str | None = None,
    session_id: str = "test-session-001",
    timestamp: str = "2026-04-01T10:00:03.000Z",
    model: str = "claude-sonnet-4",
    input_tokens: int = 5000,
    output_tokens: int = 200,
    cache_read: int = 3000,
    cache_create: int = 1000,
) -> dict:
    """Build an assistant entry with optional text, tool_use, and thinking."""
    content = []
    if thinking:
        content.append({
            "type": "thinking",
            "thinking": thinking,
            "signature": "base64-sig-should-be-stripped",
        })
    if text:
        content.append({"type": "text", "text": text})
    if tool_calls:
        for tc in tool_calls:
            content.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc.get("input", {}),
            })

    return {
        "type": "assistant",
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": "/workspace",
        "version": "2.1.4",
        "gitBranch": "",
        "message": {
            "role": "assistant",
            "model": model,
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_create,
            },
        },
    }


def _write_jsonl(entries: list[dict], path: Path):
    """Write entries as JSONL to a file."""
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Tests: is_system_message
# ---------------------------------------------------------------------------

class TestIsSystemMessage:
    def test_regular_user_message(self):
        assert is_system_message("Help me fix a bug") is False

    def test_session_continuation(self):
        assert is_system_message("This session is being continued from...") is True

    def test_system_reminder(self):
        assert is_system_message("<system-reminder>some context</system-reminder>") is True

    def test_image_caption(self):
        assert is_system_message("<image-caption>a screenshot</image-caption>") is True

    def test_command_name(self):
        assert is_system_message("<command-name>review</command-name>") is True

    def test_local_command(self):
        assert is_system_message("<local-command>ls</local-command>") is True

    def test_skill_base_dir(self):
        assert is_system_message("Base directory for this skill: /foo") is True

    def test_interrupted(self):
        assert is_system_message("[Request interrupted by user]") is True

    def test_image_original(self):
        assert is_system_message("[Image: original path]") is True

    def test_image_generic(self):
        assert is_system_message("[Image: some screenshot]") is True


# ---------------------------------------------------------------------------
# Tests: parse_jsonl
# ---------------------------------------------------------------------------

class TestParseJsonl:
    def test_skips_queue_operations(self, tmp_path):
        entries = [
            {"type": "queue-operation", "operation": "dequeue", "timestamp": "2026-04-01T10:00:00Z", "sessionId": "s1"},
            _user_entry("hello"),
            _assistant_entry(text="hi there"),
        ]
        _write_jsonl(entries, tmp_path / "test.jsonl")
        result = parse_jsonl(str(tmp_path / "test.jsonl"))
        assert len(result) == 2
        assert all(e["type"] in ("user", "assistant") for e in result)

    def test_skips_blank_lines(self, tmp_path):
        p = tmp_path / "test.jsonl"
        with open(p, "w") as f:
            f.write(json.dumps(_user_entry("hello")) + "\n")
            f.write("\n")
            f.write(json.dumps(_assistant_entry(text="hi")) + "\n")
        result = parse_jsonl(str(p))
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Tests: build_messages
# ---------------------------------------------------------------------------

class TestBuildMessages:
    def test_single_turn_single_step(self):
        """One user message + one assistant with one tool call = 1 turn, 1 step."""
        entries = [
            _user_entry("Read file /a.py", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                text="Let me read that file.",
                tool_calls=[{"id": "toolu_001", "name": "Read", "input": {"file_path": "/a.py"}}],
                timestamp="2026-04-01T10:00:03.000Z",
                thinking="I should read the file first.",
            ),
            _tool_result_entry("toolu_001", "file contents here", timestamp="2026-04-01T10:00:05.000Z"),
        ]
        messages = build_messages(entries)
        # Should have 2 items: user message + agent run
        assert len(messages) == 2
        # First is user message
        assert messages[0]["role"] == "user"
        assert messages[0]["turn_id"] == 1
        assert messages[0]["content"] == "Read file /a.py"
        # Second is agent run
        run = messages[1]
        assert run["turn_id"] == 1
        assert run["agent_run_id"] == "run_t1"
        assert len(run["steps"]) == 1
        step = run["steps"][0]
        assert step["step_id"] == 1
        assert step["action"]["tool_name"] == "Read"
        assert step["action"]["args"]["file_path"] == "/a.py"
        assert step["observation"]["text"] == "file contents here"
        assert step["thinking"] == "I should read the file first."

    def test_multi_turn(self):
        """Two user messages = 2 turns."""
        entries = [
            _user_entry("First request", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(text="Done with first.", timestamp="2026-04-01T10:00:03.000Z"),
            _user_entry("Second request", timestamp="2026-04-01T10:01:00.000Z"),
            _assistant_entry(
                tool_calls=[{"id": "toolu_002", "name": "Edit", "input": {"file_path": "/b.py"}}],
                timestamp="2026-04-01T10:01:05.000Z",
            ),
            _tool_result_entry("toolu_002", "edit done", timestamp="2026-04-01T10:01:07.000Z"),
        ]
        messages = build_messages(entries)
        # Turn 1: user + agent_run (respond_to_user)
        # Turn 2: user + agent_run (Edit step)
        turn_ids = [m["turn_id"] for m in messages]
        assert 1 in turn_ids
        assert 2 in turn_ids
        # Count user messages
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assert len(user_msgs) == 2

    def test_system_message_filtering(self):
        """System messages should not create new turns."""
        entries = [
            _user_entry("<system-reminder>context here</system-reminder>", timestamp="2026-04-01T10:00:00.000Z"),
            _user_entry("Real user request", timestamp="2026-04-01T10:00:01.000Z"),
            _assistant_entry(text="Got it.", timestamp="2026-04-01T10:00:03.000Z"),
        ]
        messages = build_messages(entries)
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0]["content"] == "Real user request"
        assert user_msgs[0]["turn_id"] == 1

    def test_thinking_preserved_signature_stripped(self):
        """Thinking content is kept; signature field must not appear."""
        entries = [
            _user_entry("Check something", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                tool_calls=[{"id": "toolu_010", "name": "Read", "input": {"file_path": "/c.py"}}],
                thinking="Extended thinking about the problem",
                timestamp="2026-04-01T10:00:03.000Z",
            ),
            _tool_result_entry("toolu_010", "file content", timestamp="2026-04-01T10:00:05.000Z"),
        ]
        messages = build_messages(entries)
        run = [m for m in messages if "steps" in m][0]
        step = run["steps"][0]
        assert step["thinking"] == "Extended thinking about the problem"
        # Verify no signature anywhere in the step
        step_json = json.dumps(step)
        assert "signature" not in step_json
        assert "base64-sig" not in step_json

    def test_token_usage_captured(self):
        """Usage from assistant entries must appear in step.usage."""
        entries = [
            _user_entry("Do something", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                tool_calls=[{"id": "toolu_020", "name": "Bash", "input": {"command": "ls"}}],
                timestamp="2026-04-01T10:00:03.000Z",
                input_tokens=8000,
                output_tokens=300,
                cache_read=6000,
                cache_create=2000,
            ),
            _tool_result_entry("toolu_020", "file1.py", timestamp="2026-04-01T10:00:05.000Z"),
        ]
        messages = build_messages(entries)
        run = [m for m in messages if "steps" in m][0]
        step = run["steps"][0]
        assert step["usage"]["input_tokens"] == 8000
        assert step["usage"]["output_tokens"] == 300
        assert step["usage"]["cache_read_tokens"] == 6000
        assert step["usage"]["cache_creation_tokens"] == 2000

    def test_respond_to_user_step(self):
        """Assistant text without tool_use produces a respond_to_user step."""
        entries = [
            _user_entry("What is Python?", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(text="Python is a programming language.", timestamp="2026-04-01T10:00:03.000Z"),
        ]
        messages = build_messages(entries)
        run = [m for m in messages if "steps" in m][0]
        step = run["steps"][0]
        assert step["action"]["tool_name"] == "respond_to_user"
        assert step["thought"] == "Python is a programming language."

    def test_tool_result_does_not_start_new_turn(self):
        """User entries with tool_result content should NOT start a new turn."""
        entries = [
            _user_entry("Read two files", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                tool_calls=[{"id": "toolu_030", "name": "Read", "input": {"file_path": "/a.py"}}],
                timestamp="2026-04-01T10:00:03.000Z",
            ),
            _tool_result_entry("toolu_030", "content of a", timestamp="2026-04-01T10:00:05.000Z"),
            _assistant_entry(
                tool_calls=[{"id": "toolu_031", "name": "Read", "input": {"file_path": "/b.py"}}],
                timestamp="2026-04-01T10:00:07.000Z",
            ),
            _tool_result_entry("toolu_031", "content of b", timestamp="2026-04-01T10:00:09.000Z"),
        ]
        messages = build_messages(entries)
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assert len(user_msgs) == 1  # Only 1 turn
        runs = [m for m in messages if "steps" in m]
        assert len(runs) == 1
        assert len(runs[0]["steps"]) == 2

    def test_observation_truncated_to_2000(self):
        """Tool result text should be truncated to 2000 chars."""
        long_text = "x" * 5000
        entries = [
            _user_entry("Read big file", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                tool_calls=[{"id": "toolu_040", "name": "Read", "input": {"file_path": "/big.py"}}],
                timestamp="2026-04-01T10:00:03.000Z",
            ),
            _tool_result_entry("toolu_040", long_text, timestamp="2026-04-01T10:00:05.000Z"),
        ]
        messages = build_messages(entries)
        run = [m for m in messages if "steps" in m][0]
        assert len(run["steps"][0]["observation"]["text"]) <= 2000

    def test_multiple_tool_calls_in_one_assistant(self):
        """An assistant message with multiple tool_use blocks = multiple steps."""
        entries = [
            _user_entry("Read two files at once", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                text="Reading both files.",
                tool_calls=[
                    {"id": "toolu_050", "name": "Read", "input": {"file_path": "/x.py"}},
                    {"id": "toolu_051", "name": "Read", "input": {"file_path": "/y.py"}},
                ],
                timestamp="2026-04-01T10:00:03.000Z",
            ),
            _tool_result_entry("toolu_050", "x content", timestamp="2026-04-01T10:00:05.000Z"),
            _tool_result_entry("toolu_051", "y content", timestamp="2026-04-01T10:00:05.000Z"),
        ]
        messages = build_messages(entries)
        run = [m for m in messages if "steps" in m][0]
        assert len(run["steps"]) == 2
        assert run["steps"][0]["action"]["args"]["file_path"] == "/x.py"
        assert run["steps"][1]["action"]["args"]["file_path"] == "/y.py"


# ---------------------------------------------------------------------------
# Tests: convert_session_v2
# ---------------------------------------------------------------------------

class TestConvertSessionV2:
    def test_full_conversion_valid_schema(self, tmp_path):
        """Full conversion produces valid v2 schema with correct top-level keys."""
        entries = [
            _user_entry("Fix the bug", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                thinking="Let me investigate.",
                tool_calls=[{"id": "toolu_100", "name": "Read", "input": {"file_path": "/app.py"}}],
                timestamp="2026-04-01T10:00:05.000Z",
                input_tokens=10000,
                output_tokens=500,
                cache_read=8000,
                cache_create=2000,
            ),
            _tool_result_entry("toolu_100", "def main(): pass", timestamp="2026-04-01T10:00:07.000Z"),
            _assistant_entry(
                text="The bug is fixed.",
                timestamp="2026-04-01T10:00:10.000Z",
                input_tokens=12000,
                output_tokens=100,
                cache_read=10000,
                cache_create=1000,
            ),
        ]
        jsonl_path = tmp_path / "test-session-001.jsonl"
        _write_jsonl(entries, jsonl_path)
        result = convert_session_v2(str(jsonl_path), "zzj")

        # Top-level schema
        assert result["schema_version"] == "2.0"
        assert result["conversation_id"] == "test-session-001"
        assert result["agent"]["name"] == "claude-code"
        assert result["agent"]["model"] == "claude-sonnet-4"
        assert result["agent"]["environment"] == "taptap-maker"
        assert result["agent"]["tool_protocol"] == "claude_tool_use"

        # Session metadata
        meta = result["session_metadata"]
        assert meta["project"] == "zzj"
        assert meta["project_name"] == "\u8d85\u65f6\u7a7a\u8981\u585e"  # 超时空要塞
        assert meta["session_id"] == "test-session-001"
        assert meta["started_at"] == "2026-04-01T10:00:00.000Z"
        assert meta["ended_at"] == "2026-04-01T10:00:10.000Z"
        assert meta["duration_sec"] == 10.0
        assert meta["cwd"] == "/workspace"
        assert meta["version"] == "2.1.4"

        # Messages
        assert len(result["messages"]) > 0

        # Summary
        summary = result["summary"]
        assert summary["total_turns"] == 1
        assert summary["total_steps"] == 2  # Read + respond_to_user
        assert summary["total_tool_calls"] == 1  # Only Read is a tool call
        assert summary["total_input_tokens"] == 22000
        assert summary["total_output_tokens"] == 600
        assert summary["total_cache_read_tokens"] == 18000
        assert summary["total_cache_creation_tokens"] == 3000
        assert summary["status"] == "completed"
        assert summary["first_user_prompt"] == "Fix the bug"

        # Phases and markers exist
        assert isinstance(result["phases"], list)
        assert isinstance(result["markers"], list)
        assert isinstance(result["subagents"], list)

    def test_empty_session(self, tmp_path):
        """Empty JSONL file produces a valid but empty traj."""
        jsonl_path = tmp_path / "empty-session.jsonl"
        jsonl_path.write_text("")
        result = convert_session_v2(str(jsonl_path), "wzp")

        assert result["schema_version"] == "2.0"
        assert result["conversation_id"] == "empty-session"
        assert result["summary"]["total_turns"] == 0
        assert result["summary"]["total_steps"] == 0
        assert result["summary"]["status"] == "empty"
        assert result["messages"] == []
        assert result["phases"] == []
        assert result["markers"] == []

    def test_subagent_processing(self, tmp_path):
        """Sessions with subagent directories get nested subagent data."""
        # Main session
        main_entries = [
            _user_entry("Do task", session_id="main-session", timestamp="2026-04-01T10:00:00.000Z"),
            _assistant_entry(
                text="Working on it.",
                session_id="main-session",
                timestamp="2026-04-01T10:00:05.000Z",
            ),
        ]
        jsonl_path = tmp_path / "main-session.jsonl"
        _write_jsonl(main_entries, jsonl_path)

        # Create subagent directory and file
        subagent_dir = tmp_path / "main-session" / "subagents"
        subagent_dir.mkdir(parents=True)

        agent_entries = [
            _user_entry("Sub-task", session_id="agent-abc123", timestamp="2026-04-01T10:00:01.000Z"),
            _assistant_entry(
                tool_calls=[{"id": "toolu_sub1", "name": "Read", "input": {"file_path": "/sub.py"}}],
                session_id="agent-abc123",
                timestamp="2026-04-01T10:00:02.000Z",
            ),
            _tool_result_entry("toolu_sub1", "sub content", session_id="agent-abc123", timestamp="2026-04-01T10:00:03.000Z"),
        ]
        _write_jsonl(agent_entries, subagent_dir / "agent-abc123.jsonl")

        result = convert_session_v2(str(jsonl_path), "zzj")
        assert result["summary"]["total_subagents"] == 1
        assert len(result["subagents"]) == 1
        assert result["subagents"][0]["agent_id"] == "abc123"
        assert len(result["subagents"][0]["messages"]) > 0
