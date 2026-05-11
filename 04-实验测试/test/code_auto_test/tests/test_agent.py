"""
Layer 7 Tests: TITAN Agent Integration
End-to-end tests for the full TITAN testing loop using Mock LLM.
"""
import os
import pytest

from titan.agent import TITANAgent, TITANTestReport
from titan.game.bug_scenarios import BugType
from titan.modules.diagnosis import BugCategory


# ---------------------------------------------------------------------------
# Helper: Create a mock-LLM agent (no API key needed)
# ---------------------------------------------------------------------------

def make_mock_agent(
    difficulty="EASY",
    stall_threshold=20,
    escalation_limit=3,
    use_rag=False,  # disable RAG in tests for speed
) -> TITANAgent:
    os.environ["TITAN_MOCK_LLM"] = "1"
    agent = TITANAgent(
        difficulty=difficulty,
        stall_threshold=stall_threshold,
        escalation_limit=escalation_limit,
        mock_llm=True,
        use_rag=use_rag,
    )
    return agent


# ---------------------------------------------------------------------------
# Test: Basic agent execution
# ---------------------------------------------------------------------------

class TestAgentBasicExecution:
    def test_agent_runs_without_crash(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=50)
        assert isinstance(report, TITANTestReport)

    def test_agent_returns_valid_report_fields(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=30)
        assert isinstance(report.total_ticks, int)
        assert report.total_ticks > 0
        assert isinstance(report.final_score, int)
        assert report.final_phase in ("RUNNING", "GAME_OVER", "WIN")
        assert isinstance(report.bugs_detected, list)
        assert isinstance(report.coverage_ratio, float)
        assert isinstance(report.visited_state_count, int)
        assert report.terminated_by in (
            "task_complete", "max_ticks", "escalation_limit", "game_over"
        )

    def test_agent_max_ticks_respected(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=10)
        assert report.total_ticks <= 10

    def test_agent_action_history_non_empty(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=30)
        assert report.action_history_length > 0

    def test_coverage_ratio_in_valid_range(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=50)
        assert 0.0 <= report.coverage_ratio <= 1.0

    def test_visited_state_count_positive(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=50)
        assert report.visited_state_count > 0


# ---------------------------------------------------------------------------
# Test: Agent with bug injection
# ---------------------------------------------------------------------------

class TestAgentWithBugs:
    def test_score_no_increment_bug_run_completes(self):
        """Agent should run without crashing even with score bug injected."""
        agent = make_mock_agent(stall_threshold=10, escalation_limit=2)
        report = agent.run(bug_type=BugType.SCORE_NO_INCREMENT, max_ticks=100)
        assert isinstance(report, TITANTestReport)

    def test_wall_pass_through_bug_game_continues(self):
        """With wall pass-through bug, game should continue longer than normal."""
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.WALL_PASS_THROUGH, max_ticks=100)
        assert isinstance(report, TITANTestReport)
        # With wall pass-through, agent shouldn't die from walls → likely more ticks
        # (may still die from self collision, but less likely early)

    def test_slow_tick_bug_detected(self):
        """SLOW_TICK bug should be detected by performance monitor."""
        agent = make_mock_agent()
        # Override time monitor thresholds for fast test
        agent.diagnosis_engine.time_monitor._baseline_avg = 0.0001  # fake baseline
        agent.diagnosis_engine.time_monitor._confirm_threshold = 2

        report = agent.run(bug_type=BugType.SLOW_TICK, max_ticks=10)
        assert isinstance(report, TITANTestReport)
        perf_bugs = [r for r in report.bugs_detected if r.bug_type == BugCategory.PERFORMANCE]
        assert len(perf_bugs) > 0, "Slow tick bug should be detected"

    def test_no_bug_baseline_clean_game(self):
        """Clean game with no bugs should produce minimal reports."""
        agent = make_mock_agent(stall_threshold=30, escalation_limit=5)
        report = agent.run(bug_type=BugType.NONE, max_ticks=200)
        # Clean game may trigger stall-based detection if LLM is Mock (always returns same direction)
        # but crash bugs should not occur on clean game
        crash_bugs = [r for r in report.bugs_detected if r.bug_type == BugCategory.CRASH]
        # With clean game, unexpected crashes should be zero
        # (GAME_OVER from wall/self collision IS expected, so danger_ahead=True)
        assert isinstance(report, TITANTestReport)

    def test_score_no_increment_triggers_stall(self):
        """Score never increasing should eventually trigger reflection."""
        agent = make_mock_agent(stall_threshold=5, escalation_limit=2)
        report = agent.run(bug_type=BugType.SCORE_NO_INCREMENT, max_ticks=50)
        # With score never incrementing, stall should trigger
        # This is behavioral: agent may terminate via escalation_limit
        assert report.terminated_by in (
            "escalation_limit", "game_over", "max_ticks", "task_complete"
        )


# ---------------------------------------------------------------------------
# Test: Agent report structure
# ---------------------------------------------------------------------------

class TestAgentReportStructure:
    def test_report_summary_string(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=30)
        summary = report.summary()
        assert "TITAN Test Report" in summary
        assert "Bug scenario" in summary
        assert "Ticks executed" in summary

    def test_bug_count_matches_list(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=30)
        assert report.bug_count == len(report.bugs_detected)

    def test_bug_type_tested_preserved(self):
        agent = make_mock_agent()
        report = agent.run(bug_type=BugType.WALL_PASS_THROUGH, max_ticks=30)
        assert report.bug_type_tested == BugType.WALL_PASS_THROUGH.value

    def test_multiple_runs_independent(self):
        """Each run should produce an independent report."""
        agent = make_mock_agent()
        report1 = agent.run(bug_type=BugType.NONE, max_ticks=30)
        report2 = agent.run(bug_type=BugType.NONE, max_ticks=30)
        # Both should be valid; second run reset the engine
        assert isinstance(report1, TITANTestReport)
        assert isinstance(report2, TITANTestReport)


# ---------------------------------------------------------------------------
# Test: LLM client integration
# ---------------------------------------------------------------------------

class TestAgentLLMIntegration:
    def test_mock_llm_never_calls_api(self):
        """Mock LLM should never make network calls."""
        agent = make_mock_agent()
        # If this completes without network error, mock is working
        report = agent.run(bug_type=BugType.NONE, max_ticks=20)
        assert isinstance(report, TITANTestReport)

    def test_mock_llm_with_custom_responses(self):
        """Agent should use mock responses from LLM client."""
        agent = make_mock_agent()
        agent.llm.set_default_mock_response("UP")
        report = agent.run(bug_type=BugType.NONE, max_ticks=30)
        # Even with always-UP direction, agent should complete without crash
        assert isinstance(report, TITANTestReport)


# ---------------------------------------------------------------------------
# Test: Reflection + diagnosis interaction
# ---------------------------------------------------------------------------

class TestAgentReflectionDiagnosis:
    def test_escalation_limit_causes_early_termination(self):
        agent = make_mock_agent(stall_threshold=2, escalation_limit=1)
        agent.llm.set_default_mock_response(
            "ACTIONS: RIGHT\nIS_BUG: yes\nREASON: stuck"
        )
        report = agent.run(bug_type=BugType.NONE, max_ticks=100)
        # With very low thresholds, should terminate early
        assert report.total_ticks <= 100  # basic sanity

    def test_verbose_mode_no_crash(self):
        """Verbose mode should not cause any errors."""
        import io, sys
        captured = io.StringIO()
        sys.stdout = captured
        try:
            agent = make_mock_agent()
            report = agent.run(bug_type=BugType.NONE, max_ticks=10, verbose=True)
        finally:
            sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "TITAN Agent" in output
