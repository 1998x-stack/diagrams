"""Tests for the v2 phase tagger."""
from __future__ import annotations
import pytest
from phase_tagger import classify_action_v2, tag_phases_v2, detect_markers_v2


def _step(tool_name: str, args: dict | None = None, step_id: int = 1):
    return {
        "step_id": step_id,
        "action": {
            "tool_name": tool_name,
            "tool_use_id": f"toolu_{step_id}",
            "args": args or {},
        },
    }


class TestClassifyActionV2:
    def test_read_is_localization(self):
        assert classify_action_v2(_step("Read")) == "localization"

    def test_glob_is_localization(self):
        assert classify_action_v2(_step("Glob")) == "localization"

    def test_grep_is_localization(self):
        assert classify_action_v2(_step("Grep")) == "localization"

    def test_lsp_is_localization(self):
        assert classify_action_v2(_step("LSP")) == "localization"

    def test_agent_is_localization(self):
        assert classify_action_v2(_step("Agent")) == "localization"

    def test_edit_is_editing(self):
        assert classify_action_v2(_step("Edit")) == "editing"

    def test_write_is_editing(self):
        assert classify_action_v2(_step("Write")) == "editing"

    def test_bash_test_is_verification(self):
        assert classify_action_v2(_step("Bash", {"command": "pytest -v"})) == "verification"

    def test_bash_npm_test_is_verification(self):
        assert classify_action_v2(_step("Bash", {"command": "npm test"})) == "verification"

    def test_bash_git_commit_is_submission(self):
        assert classify_action_v2(_step("Bash", {"command": "git commit -m 'fix'"})) == "submission"

    def test_bash_git_push_is_submission(self):
        assert classify_action_v2(_step("Bash", {"command": "git push origin main"})) == "submission"

    def test_bash_other_is_editing(self):
        assert classify_action_v2(_step("Bash", {"command": "ls -la"})) == "editing"

    def test_respond_to_user_is_inherited(self):
        assert classify_action_v2(_step("respond_to_user")) == "inherited"

    def test_unknown_tool_is_editing(self):
        assert classify_action_v2(_step("SomeNewTool")) == "editing"


class TestTagPhasesV2:
    def test_empty_steps(self):
        assert tag_phases_v2([]) == []

    def test_single_phase(self):
        steps = [_step("Read", step_id=1), _step("Grep", step_id=2)]
        phases = tag_phases_v2(steps)
        assert len(phases) == 1
        assert phases[0]["label"] == "localization"
        assert phases[0]["start_step"] == 1
        assert phases[0]["end_step"] == 2

    def test_phase_transition(self):
        steps = [
            _step("Read", step_id=1),
            _step("Edit", step_id=2),
            _step("Bash", {"command": "pytest"}, step_id=3),
        ]
        phases = tag_phases_v2(steps)
        assert len(phases) == 3
        assert [p["label"] for p in phases] == ["localization", "editing", "verification"]

    def test_respond_inherits_previous(self):
        steps = [
            _step("Read", step_id=1),
            _step("respond_to_user", step_id=2),
            _step("Edit", step_id=3),
        ]
        phases = tag_phases_v2(steps)
        assert len(phases) == 2
        assert phases[0]["label"] == "localization"
        assert phases[0]["end_step"] == 2


class TestDetectMarkersV2:
    def test_empty_steps(self):
        assert detect_markers_v2([]) == []

    def test_milestone_markers(self):
        steps = [_step("Read", step_id=i) for i in range(1, 4)]
        markers = detect_markers_v2(steps)
        types = [m["type"] for m in markers]
        assert "milestone" in types

    def test_drift_start_detected(self):
        steps = [_step("Edit", step_id=i) for i in range(1, 6)]
        markers = detect_markers_v2(steps)
        drift = [m for m in markers if m["type"] == "drift-start"]
        assert len(drift) == 1

    def test_search_loop_detected(self):
        steps = [_step("Read", step_id=i) for i in range(1, 6)]
        markers = detect_markers_v2(steps)
        loops = [m for m in markers if m["type"] == "search-loop"]
        assert len(loops) == 1

    def test_churn_detected(self):
        steps = [
            _step("Edit", {"file_path": "/a.py"}, step_id=i)
            for i in range(1, 5)
        ]
        markers = detect_markers_v2(steps)
        churn = [m for m in markers if m["type"] == "churn"]
        assert len(churn) == 1
