import json
from pathlib import Path
from typing import Callable

import pytest


def _step_from_fixture(it: dict) -> dict:
    """Convert a sample_step() fixture dict to the real step schema."""
    action = dict(it.get("action") or {})
    obs = dict(it.get("observation") or {})
    return {
        "step_id": "x",
        "phase": it.get("phase", "editing"),
        "thinking": it.get("thinking", ""),
        "thought": it.get("thought", ""),
        "action": action,
        "observation": obs,
        "status": "ok",
        "timestamp": "2026-01-01T00:00:00Z",
        "execution_time": "0.0",
        "usage": {},
    }


@pytest.fixture
def tmp_traj_file(tmp_path) -> Callable:
    """Build a v2-schema .traj file from a flat list of fixture items."""
    def _make(session_hash: str, items: list, project: str = "wzp") -> Path:
        messages = []
        i = 0
        turn = 0
        while i < len(items):
            it = items[i]
            if it.get("type") == "user_message":
                turn += 1
                messages.append({
                    "turn_id": str(turn),
                    "role": "user",
                    "content": it.get("text", ""),
                    "timestamp": "2026-01-01T00:00:00Z",
                })
                # collect adjacent steps into the agent_run for this turn
                steps = []
                j = i + 1
                while j < len(items) and items[j].get("type") == "step":
                    steps.append(_step_from_fixture(items[j]))
                    j += 1
                if steps:
                    messages.append({
                        "turn_id": str(turn),
                        "agent_run_id": f"run_t{turn}",
                        "steps": steps,
                        "run_summary": {"steps_count": len(steps),
                                        "tool_calls_count": len(steps)},
                    })
                i = j
            elif it.get("type") == "step":
                # leading steps with no preceding user_message — wrap anyway
                turn += 1
                steps = [_step_from_fixture(it)]
                j = i + 1
                while j < len(items) and items[j].get("type") == "step":
                    steps.append(_step_from_fixture(items[j]))
                    j += 1
                messages.append({
                    "turn_id": str(turn),
                    "agent_run_id": f"run_t{turn}",
                    "steps": steps,
                    "run_summary": {"steps_count": len(steps),
                                    "tool_calls_count": len(steps)},
                })
                i = j
            else:
                i += 1
        f = tmp_path / f"{session_hash}.traj"
        f.write_text(json.dumps({
            "schema_version": "2.0",
            "conversation_id": session_hash,
            "session_metadata": {"project": project, "session_id": session_hash},
            "messages": messages,
        }, ensure_ascii=False))
        return f
    return _make


@pytest.fixture
def sample_user_msg() -> Callable:
    return lambda text: {"type": "user_message", "text": text}


@pytest.fixture
def sample_step() -> Callable:
    """Build one agent step with action + observation + phase."""
    def _make(tool, args=None, obs_text="", exit_code=None, phase="editing", thinking=""):
        return {
            "type": "step",
            "action": {"tool_name": tool, "tool_use_id": "x", "args": args or {}},
            "observation": {"type": "tool_result", "text": obs_text, "exit_code": exit_code},
            "phase": phase,
            "thinking": thinking,
        }
    return _make


@pytest.fixture
def sample_session_record() -> Callable:
    """In-memory SessionRecord for downstream-stage tests."""
    def _make(**overrides):
        from scripts.load_trajectories import SessionRecord
        defaults = dict(
            project="wzp", session_hash="abc12345",
            user_corpus="please add inventory UI",
            error_corpus="",
            tool_sequence=["Read", "Edit", "Bash"],
            phase_sequence=["localization", "editing", "verification"],
            correction_signals=[],
            file_targets=["src/inventory.lua"],
            n_steps=3,
        )
        defaults.update(overrides)
        return SessionRecord(**defaults)
    return _make


@pytest.fixture
def sample_signal_record() -> Callable:
    """Dict shape stored in signals.jsonl."""
    def _make(**overrides):
        defaults = dict(
            session_hash="abc12345",
            project="wzp",
            signals=["log_error", "recurring_errsig:lua nil"],
            tool_sequence=["Read", "Edit", "Bash"],
            phase_sequence=["localization", "editing", "verification"],
            correction_signals=[],
            file_targets=["src/menu.lua"],
            n_steps=3,
            user_corpus="脑力大冒险关卡跳转报错 nil 修不好",
        )
        defaults.update(overrides)
        return defaults
    return _make
