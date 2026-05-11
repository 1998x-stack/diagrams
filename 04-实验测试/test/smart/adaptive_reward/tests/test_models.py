import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import StepResult, CoverageStats


class TestStepResult:
    def test_instantiation_and_fields(self):
        result = StepResult(
            total_reward=35.0,
            semantic_reward=30.0,
            structural_reward=5.0,
            subgoal_advanced=True,
            new_anchors_covered={"L:42"},
            is_terminal=False,
        )
        assert result.total_reward == 35.0
        assert result.semantic_reward == 30.0
        assert result.structural_reward == 5.0
        assert result.subgoal_advanced is True
        assert result.new_anchors_covered == {"L:42"}
        assert result.is_terminal is False

    def test_zero_reward_step(self):
        result = StepResult(
            total_reward=0.0,
            semantic_reward=0.0,
            structural_reward=0.0,
            subgoal_advanced=False,
            new_anchors_covered=set(),
            is_terminal=False,
        )
        assert result.total_reward == 0.0
        assert result.new_anchors_covered == set()

    def test_terminal_step(self):
        result = StepResult(
            total_reward=230.0,
            semantic_reward=230.0,
            structural_reward=0.0,
            subgoal_advanced=True,
            new_anchors_covered=set(),
            is_terminal=True,
        )
        assert result.is_terminal is True
        assert result.semantic_reward == 230.0


class TestCoverageStats:
    def test_instantiation(self):
        stats = CoverageStats(
            total_anchors=10,
            covered_count=4,
            coverage_rate=0.4,
        )
        assert stats.total_anchors == 10
        assert stats.covered_count == 4
        assert stats.coverage_rate == 0.4

    def test_full_coverage(self):
        stats = CoverageStats(total_anchors=5, covered_count=5, coverage_rate=1.0)
        assert stats.coverage_rate == 1.0

    def test_zero_coverage(self):
        stats = CoverageStats(total_anchors=0, covered_count=0, coverage_rate=0.0)
        assert stats.coverage_rate == 0.0

    def test_coverage_rate_is_plain_field(self):
        # coverage_rate is a plain float field — caller computes it, not __post_init__
        stats = CoverageStats(total_anchors=10, covered_count=0, coverage_rate=0.99)
        assert stats.coverage_rate == 0.99  # whatever the caller passed, not auto-computed
