"""
Layer 5 Tests: Reflective Reasoning Module
Tests for progress monitoring, coverage memory, and reflection logic.
"""
import json
import os
import pytest
import tempfile

from titan.modules.reflection import (
    ProgressMonitor, CoverageMemory, ReflectionEngine,
    ReflectionResult, _hash_abstract_state,
)
from titan.llm_client import LLMClient


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_abstract(
    direction="RIGHT", danger_ahead=False, danger_left=False,
    danger_right=False, food_direction="RIGHT", food_distance="medium",
    head_position="center", snake_length="short"
) -> dict:
    return {
        "direction": direction,
        "danger_ahead": danger_ahead,
        "danger_left": danger_left,
        "danger_right": danger_right,
        "food_direction": food_direction,
        "food_distance": food_distance,
        "head_position": head_position,
        "snake_length": snake_length,
        "score": 0,
        "tick_count": 0,
        "relevant_rules": [],
        "phase": "RUNNING",
    }


# ---------------------------------------------------------------------------
# Test: Abstract state hashing
# ---------------------------------------------------------------------------

class TestStateHashing:
    def test_same_state_same_hash(self):
        a = make_abstract(direction="RIGHT")
        b = make_abstract(direction="RIGHT")
        assert _hash_abstract_state(a) == _hash_abstract_state(b)

    def test_different_direction_different_hash(self):
        a = make_abstract(direction="RIGHT")
        b = make_abstract(direction="UP")
        assert _hash_abstract_state(a) != _hash_abstract_state(b)

    def test_score_changes_do_not_affect_hash(self):
        a = make_abstract(direction="RIGHT")
        b = make_abstract(direction="RIGHT")
        a["score"] = 10
        b["score"] = 50
        # Hash should ignore score (structural features only)
        assert _hash_abstract_state(a) == _hash_abstract_state(b)


# ---------------------------------------------------------------------------
# Test: ProgressMonitor
# ---------------------------------------------------------------------------

class TestProgressMonitor:
    def test_stall_after_threshold_steps(self):
        monitor = ProgressMonitor(stall_threshold=5)
        state = make_abstract()
        stalled = False
        for i in range(10):
            # Same state, same score → no progress → should stall after 5
            triggered = monitor.update(state, "RIGHT", 0)
            if triggered:
                stalled = True
        assert stalled, "Should have detected stall after 5 steps with no progress"

    def test_score_increase_resets_stall(self):
        monitor = ProgressMonitor(stall_threshold=5)
        state = make_abstract()
        # First call: new state → progress (stall_count=0)
        # Calls 2-4: same state, same score → 3 stalls
        for _ in range(4):
            monitor.update(state, "RIGHT", 0)
        assert monitor.stall_count == 3  # first call was new state

        # Score increases → progress → reset
        monitor.update(state, "RIGHT", 10)
        assert monitor.stall_count == 0, "Score increase should reset stall counter"

    def test_new_state_resets_stall(self):
        monitor = ProgressMonitor(stall_threshold=5)
        state_a = make_abstract(direction="RIGHT")
        state_b = make_abstract(direction="UP")  # different state

        # First call: new state_a → progress (stall_count=0)
        # Calls 2-4: same state_a → 3 stalls
        for _ in range(4):
            monitor.update(state_a, "RIGHT", 0)
        assert monitor.stall_count == 3  # first call was new state

        # Visit new state B → progress
        monitor.update(state_b, "UP", 0)
        assert monitor.stall_count == 0

    def test_stall_count_increments(self):
        monitor = ProgressMonitor(stall_threshold=20)
        state = make_abstract()
        # Visit state once (new → no stall)
        monitor.update(state, "RIGHT", 0)
        assert monitor.stall_count == 0

        # Visit same state again without progress
        for i in range(5):
            monitor.update(state, "RIGHT", 0)
        assert monitor.stall_count == 5

    def test_reset_clears_state(self):
        monitor = ProgressMonitor(stall_threshold=5)
        state = make_abstract()
        for _ in range(5):
            monitor.update(state, "RIGHT", 0)
        monitor.reset()
        assert monitor.stall_count == 0

    def test_returns_true_when_stall_threshold_reached(self):
        monitor = ProgressMonitor(stall_threshold=3)
        state = make_abstract()
        monitor.update(state, "RIGHT", 0)  # first visit → new state, no stall
        monitor.update(state, "RIGHT", 0)  # stall 1
        monitor.update(state, "RIGHT", 0)  # stall 2
        result = monitor.update(state, "RIGHT", 0)  # stall 3 → threshold reached
        assert result is True


# ---------------------------------------------------------------------------
# Test: CoverageMemory
# ---------------------------------------------------------------------------

class TestCoverageMemory:
    def test_record_and_retrieve(self):
        mem = CoverageMemory()
        state = make_abstract(direction="RIGHT")
        mem.record(state, "UP", "success")
        assert mem.is_explored(state, "UP") is True
        assert mem.is_explored(state, "DOWN") is False

    def test_same_state_different_actions(self):
        mem = CoverageMemory()
        state = make_abstract(direction="RIGHT")
        mem.record(state, "UP", "normal")
        mem.record(state, "RIGHT", "food")
        assert mem.is_explored(state, "UP") is True
        assert mem.is_explored(state, "RIGHT") is True
        assert mem.is_explored(state, "DOWN") is False

    def test_get_outcomes(self):
        mem = CoverageMemory()
        state = make_abstract()
        mem.record(state, "RIGHT", "success")
        mem.record(state, "RIGHT", "food")
        outcomes = mem.get_outcomes(state, "RIGHT")
        assert "success" in outcomes
        assert "food" in outcomes

    def test_unexplored_actions(self):
        mem = CoverageMemory()
        state = make_abstract()
        mem.record(state, "UP", "normal")
        unexplored = mem.get_unexplored_actions(state, ["UP", "RIGHT", "DOWN"])
        assert "UP" not in unexplored
        assert "RIGHT" in unexplored
        assert "DOWN" in unexplored

    def test_visited_state_count(self):
        mem = CoverageMemory()
        state_a = make_abstract(direction="RIGHT")
        state_b = make_abstract(direction="UP")
        mem.record(state_a, "UP", "normal")
        mem.record(state_a, "DOWN", "normal")
        mem.record(state_b, "LEFT", "normal")
        assert mem.visited_state_count == 2

    def test_save_and_load(self, tmp_path):
        mem = CoverageMemory()
        state = make_abstract(direction="RIGHT")
        mem.record(state, "UP", "success")
        mem.record(state, "DOWN", "game_over")

        path = str(tmp_path / "memory.json")
        mem.save(path)

        loaded = CoverageMemory.load(path)
        assert loaded.is_explored(state, "UP") is True
        assert loaded.is_explored(state, "DOWN") is True
        assert loaded.is_explored(state, "LEFT") is False

    def test_load_nonexistent_file(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        mem = CoverageMemory.load(path)
        assert isinstance(mem, CoverageMemory)
        assert mem.visited_state_count == 0


# ---------------------------------------------------------------------------
# Test: ReflectionEngine
# ---------------------------------------------------------------------------

class TestReflectionEngine:
    def test_record_step_no_stall(self):
        engine = ReflectionEngine(stall_threshold=5)
        state_a = make_abstract(direction="RIGHT")
        state_b = make_abstract(direction="UP")
        # Alternate states → always progress
        result = engine.record_step(state_a, "RIGHT", 0, 1)
        assert result is False
        result = engine.record_step(state_b, "UP", 0, 2)
        assert result is False

    def test_record_step_triggers_stall(self):
        engine = ReflectionEngine(stall_threshold=3)
        state = make_abstract()
        # First visit → new state (no stall)
        engine.record_step(state, "RIGHT", 0, 0)
        # Next visits → stall
        engine.record_step(state, "RIGHT", 0, 1)
        engine.record_step(state, "RIGHT", 0, 2)
        triggered = engine.record_step(state, "RIGHT", 0, 3)
        assert triggered is True

    def test_reflect_with_mock_llm(self):
        engine = ReflectionEngine(stall_threshold=5)
        mock_llm = LLMClient(mock=True)
        mock_llm.set_mock_response(
            "ACTIONS: UP,RIGHT\nIS_BUG: no\nREASON: Try turning"
        )
        state = make_abstract()
        result = engine.reflect(state, mock_llm)
        assert isinstance(result, ReflectionResult)
        assert isinstance(result.suggested_actions, list)
        assert isinstance(result.is_bug, bool)

    def test_reflect_with_bug_detection_mock(self):
        engine = ReflectionEngine(stall_threshold=5)
        mock_llm = LLMClient(mock=True)
        mock_llm.set_mock_response(
            "ACTIONS: RIGHT\nIS_BUG: yes\nREASON: Score not changing despite food"
        )
        state = make_abstract()
        result = engine.reflect(state, mock_llm)
        assert result.is_bug is True

    def test_reflect_without_llm_fallback(self):
        engine = ReflectionEngine(stall_threshold=5)
        state = make_abstract(danger_ahead=True, danger_left=False, danger_right=False)
        result = engine.reflect(state, llm_client=None)
        assert isinstance(result, ReflectionResult)
        assert len(result.reason) > 0

    def test_escalation_count_increments(self):
        engine = ReflectionEngine(stall_threshold=5)
        state = make_abstract()
        assert engine.escalation_count == 0
        engine.reflect(state, llm_client=None)
        assert engine.escalation_count == 1
        engine.reflect(state, llm_client=None)
        assert engine.escalation_count == 2

    def test_should_terminate_after_limit(self):
        engine = ReflectionEngine(stall_threshold=5, escalation_limit=3)
        state = make_abstract()
        assert engine.should_terminate() is False
        for _ in range(3):
            engine.reflect(state, llm_client=None)
        assert engine.should_terminate() is True

    def test_reset_episode_clears_history(self):
        engine = ReflectionEngine(stall_threshold=5)
        state = make_abstract()
        engine.record_step(state, "RIGHT", 0, 0)
        engine.record_step(state, "UP", 0, 1)
        assert len(engine.history) == 2

        engine.reset_episode()
        assert len(engine.history) == 0
        assert engine.escalation_count == 0

    def test_coverage_memory_persists_across_episodes(self):
        engine = ReflectionEngine(stall_threshold=5)
        state = make_abstract()
        engine.record_step(state, "RIGHT", 0, 0)
        engine.reset_episode()

        # After reset, memory should persist
        assert engine.memory.is_explored(state, "RIGHT") is True
