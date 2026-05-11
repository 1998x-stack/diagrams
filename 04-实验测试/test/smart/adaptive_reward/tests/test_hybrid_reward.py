"""
Tests for HybridRewardFunction.

Import order:
  1. Import hybrid_reward — its module-level importlib block loads Stage 5 models
     under "_adaptive_reward_stage5_models" key.
  2. Get StepResult/CoverageStats from that pinned module, NOT from a bare "import models".

No cross-stage imports needed: HybridRewardFunction is duck-typed.
"""
import sys
import os
import pytest
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hybrid_reward import HybridRewardFunction

# Get model classes from the pinned module loaded by hybrid_reward
_S5 = sys.modules["_adaptive_reward_stage5_models"]
StepResult = _S5.StepResult
CoverageStats = _S5.CoverageStats


# ---------------------------------------------------------------------------
# Mock helpers — duck-typed to match Stage 3 / Stage 4 interfaces
# ---------------------------------------------------------------------------

@dataclass
class MockEvent:
    condition: str
    reward: float = 10.0  # not used by Stage 5, but matches Stage 3 shape


@dataclass
class MockRule:
    subgoal_index: int
    events: list = field(default_factory=list)


@dataclass
class MockRuleSet:
    task_name: str
    rules: list = field(default_factory=list)


@dataclass
class MockMapping:
    anchor_key: str
    subgoal_indices: list = field(default_factory=list)


@dataclass
class MockAnchorMap:
    task_name: str
    file_path: str
    mappings: list = field(default_factory=list)


def make_rule_set(n: int) -> MockRuleSet:
    """n subgoals, indices 1..n, each with one event: condition f'step == {i}'"""
    rules = [
        MockRule(
            subgoal_index=i,
            events=[MockEvent(condition=f"step == {i}")]
        )
        for i in range(1, n + 1)
    ]
    return MockRuleSet(task_name="test_task", rules=rules)


def make_multi_event_rule_set(n: int) -> MockRuleSet:
    """n subgoals; each rule has two events: first always False, second matches."""
    rules = [
        MockRule(
            subgoal_index=i,
            events=[
                MockEvent(condition="False"),
                MockEvent(condition=f"step == {i}"),
            ]
        )
        for i in range(1, n + 1)
    ]
    return MockRuleSet(task_name="test_task", rules=rules)


def make_anchor_map(mappings: list) -> MockAnchorMap:
    """
    mappings: list of (anchor_key: str, subgoal_indices: list[int])
    """
    mock_mappings = [
        MockMapping(anchor_key=key, subgoal_indices=indices)
        for key, indices in mappings
    ]
    return MockAnchorMap(task_name="test_task", file_path="test.py", mappings=mock_mappings)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHybridRewardFunction:

    def test_semantic_reward_on_condition_match(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([]),
            r_sem=30.0, r_str=5.0, terminal_reward=200.0,
        )
        result = rf.compute_reward({"step": 1}, set())
        assert result.semantic_reward == 30.0
        assert result.subgoal_advanced is True
        assert result.total_reward == 30.0

    def test_no_semantic_reward_when_condition_false(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([]),
        )
        result = rf.compute_reward({"step": 99}, set())  # no subgoal has step==99
        assert result.semantic_reward == 0.0
        assert result.subgoal_advanced is False
        assert result.total_reward == 0.0

    def test_j_advances_sequentially(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([]),
        )
        assert rf.subgoal_progress == (1, 3)
        rf.compute_reward({"step": 1}, set())
        assert rf.subgoal_progress == (2, 3)
        rf.compute_reward({"step": 2}, set())
        assert rf.subgoal_progress == (3, 3)

    def test_terminal_reward_on_last_subgoal(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([]),
            r_sem=30.0, terminal_reward=200.0,
        )
        rf.compute_reward({"step": 1}, set())  # advance to j=2
        result = rf.compute_reward({"step": 2}, set())  # complete last subgoal
        assert result.semantic_reward == 30.0 + 200.0
        assert result.is_terminal is True
        assert result.subgoal_advanced is True

    def test_terminal_and_structural_reward_same_step(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:10", [2])]),
            r_sem=30.0, r_str=5.0, terminal_reward=200.0,
        )
        rf.compute_reward({"step": 1}, set())  # advance to j=2
        result = rf.compute_reward({"step": 2}, {"L:10"})  # complete last + cover anchor
        assert result.semantic_reward == 230.0   # 30 + 200
        assert result.structural_reward == 5.0   # one new anchor
        assert result.total_reward == 235.0
        assert result.is_terminal is True

    def test_structural_reward_new_anchor(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, {"L:42"})  # j=1, no semantic
        assert result.structural_reward == 5.0
        assert "L:42" in result.new_anchors_covered

    def test_structural_reward_two_new_anchors(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1]), ("B:20:if_true", [1])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, {"L:42", "B:20:if_true"})
        assert result.structural_reward == 10.0  # 2 × r_str
        assert result.new_anchors_covered == {"L:42", "B:20:if_true"}

    def test_structural_reward_dedup_across_steps(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        rf.compute_reward({"step": 99}, {"L:42"})        # covered in step 1
        result = rf.compute_reward({"step": 99}, {"L:42"})  # same anchor in step 2
        assert result.structural_reward == 0.0
        assert result.new_anchors_covered == set()

    def test_structural_reward_dedup_across_episodes(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        rf.compute_reward({"step": 99}, {"L:42"})  # covered in episode 1
        rf.reset()                                  # start episode 2, C_cov preserved
        result = rf.compute_reward({"step": 99}, {"L:42"})
        assert result.structural_reward == 0.0      # already in C_cov

    def test_structural_reward_wrong_subgoal(self):
        # Anchor mapped to subgoal 2, but current j=1 → no structural reward
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([("L:42", [2])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, {"L:42"})  # j=1 at this point
        assert result.structural_reward == 0.0

    def test_reset_resets_j_not_coverage(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([("L:42", [1])]),
        )
        rf.compute_reward({"step": 1}, {"L:42"})  # j→2, L:42 covered
        assert rf.subgoal_progress == (2, 3)
        assert rf.coverage_rate > 0.0

        rf.reset()
        assert rf.subgoal_progress == (1, 3)   # j reset
        assert rf.coverage_rate > 0.0          # C_cov NOT cleared

    def test_coverage_rate_zero_start(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:1", [1]), ("L:2", [2])]),
        )
        assert rf.coverage_rate == 0.0

    def test_coverage_rate_updates(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:1", [1]), ("L:2", [2])]),
        )
        rf.compute_reward({"step": 99}, {"L:1"})
        assert rf.coverage_rate == 0.5
        rf.compute_reward({"step": 99}, {"L:2"})
        # L:2 is mapped to subgoal 2, but j=1 still (step 99 didn't match subgoal 1)
        # So L:2 won't be covered yet — context-aware filter blocks it
        assert rf.coverage_rate == 0.5  # still only L:1 covered

    def test_get_coverage_stats(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:1", [1]), ("L:2", [1]), ("L:3", [2])]),
            r_str=5.0,
        )
        rf.compute_reward({"step": 99}, {"L:1"})
        stats = rf.get_coverage_stats()
        assert stats.total_anchors == 3
        assert stats.covered_count == 1
        assert abs(stats.coverage_rate - 1/3) < 1e-9

    def test_subgoal_progress_property(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(5),
            anchor_map=make_anchor_map([]),
        )
        assert rf.subgoal_progress == (1, 5)
        rf.compute_reward({"step": 1}, set())
        assert rf.subgoal_progress == (2, 5)

    def test_subgoal_progress_after_terminal(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([]),
        )
        rf.compute_reward({"step": 1}, set())
        rf.compute_reward({"step": 2}, set())  # terminal
        assert rf.subgoal_progress == (3, 2)   # current_j == total_n + 1

    def test_empty_covered_anchors(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, set())
        assert result.structural_reward == 0.0
        assert result.new_anchors_covered == set()

    def test_unknown_anchor_key_ignored(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
        )
        # "L:999" not in anchor_map → silently ignored, no crash, no reward
        result = rf.compute_reward({"step": 99}, {"L:999"})
        assert result.structural_reward == 0.0

    def test_multi_event_or_semantics(self):
        # Rule has two events: first always False, second True when step==1
        rf = HybridRewardFunction(
            reward_rule_set=make_multi_event_rule_set(2),
            anchor_map=make_anchor_map([]),
            r_sem=30.0,
        )
        result = rf.compute_reward({"step": 1}, set())
        assert result.semantic_reward == 30.0   # second event triggered it
        assert result.subgoal_advanced is True

    def test_constructor_raises_on_gap_in_subgoal_indices(self):
        # Indices [1, 3] — gap at 2 → ValueError
        gap_rule_set = MockRuleSet(
            task_name="gap",
            rules=[
                MockRule(subgoal_index=1, events=[MockEvent(condition="True")]),
                MockRule(subgoal_index=3, events=[MockEvent(condition="True")]),
            ]
        )
        with pytest.raises(ValueError, match="contiguous"):
            HybridRewardFunction(
                reward_rule_set=gap_rule_set,
                anchor_map=make_anchor_map([]),
            )

    def test_compute_reward_after_terminal_returns_zero(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(1),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_sem=30.0, r_str=5.0, terminal_reward=200.0,
        )
        rf.compute_reward({"step": 1}, set())   # terminal: j becomes 2
        # Call again without reset — all-zero result
        result = rf.compute_reward({"step": 1}, {"L:42"})
        assert result.total_reward == 0.0
        assert result.semantic_reward == 0.0
        assert result.structural_reward == 0.0
        assert result.subgoal_advanced is False
        assert result.new_anchors_covered == set()
        assert result.is_terminal is False
