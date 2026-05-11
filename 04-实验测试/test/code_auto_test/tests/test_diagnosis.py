"""
Layer 6 Tests: Issue Diagnosis Module
Tests for crash detection, logic bug detection, performance monitoring, and report generation.
"""
import time
import pytest

from titan.game.snake_env import Point, GameState, Difficulty, set_phase
from titan.game.bug_scenarios import BugType, BuggySnakeEnv
from titan.modules.diagnosis import (
    DiagnosisEngine, DiagnosisReport,
    CrashMonitor, TaskStatusMonitor, ExecutionTimeMonitor,
    BugCategory, Severity,
)
from titan.modules.perception import abstract
from titan.llm_client import LLMClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_state(
    snake=None, food=None, direction="RIGHT", next_direction=None,
    phase="RUNNING", score=0, grid_size=10
) -> GameState:
    config = Difficulty(tick_interval=200, grid_size=grid_size, initial_length=3)
    if snake is None:
        snake = [Point(5, 5), Point(4, 5), Point(3, 5)]
    if food is None:
        food = Point(8, 5)
    if next_direction is None:
        next_direction = direction
    return GameState(
        snake=snake, food=food, direction=direction, next_direction=next_direction,
        phase=phase, score=score, high_score=0, tick_count=0, config=config,
    )


def make_abstract_state(danger_ahead=False, danger_left=False, danger_right=False) -> dict:
    return {
        "phase": "RUNNING",
        "direction": "RIGHT",
        "score": 0,
        "tick_count": 0,
        "snake_length": "short",
        "food_distance": "medium",
        "food_direction": "RIGHT",
        "danger_ahead": danger_ahead,
        "danger_left": danger_left,
        "danger_right": danger_right,
        "danger_back": False,
        "head_position": "center",
        "open_space_ratio": 0.8,
        "grid_size": 10,
        "relevant_rules": [],
    }


def make_history(n=5, score=0):
    return [(make_abstract_state(), "RIGHT", score)] * n


# ---------------------------------------------------------------------------
# Test: CrashMonitor
# ---------------------------------------------------------------------------

class TestCrashMonitor:
    def test_no_report_when_running(self):
        monitor = CrashMonitor()
        state = make_state(phase="RUNNING")
        ab = make_abstract_state(danger_ahead=False)
        result = monitor.check(state, ab, [])
        assert result is None

    def test_no_report_expected_death(self):
        # Agent knew it was dangerous → expected death, not a bug
        monitor = CrashMonitor()
        state = make_state(phase="GAME_OVER")
        ab = make_abstract_state(danger_ahead=True)  # danger was known
        result = monitor.check(state, ab, [])
        assert result is None

    def test_report_unexpected_crash(self):
        # Agent thought it was safe, but game ended → bug
        monitor = CrashMonitor(confirm_count=1)
        state = make_state(phase="GAME_OVER")
        ab = make_abstract_state(danger_ahead=False)  # no danger detected!
        result = monitor.check(state, ab, make_history())
        assert result is not None
        assert result.bug_type == BugCategory.CRASH
        assert result.severity == Severity.CRITICAL

    def test_confirm_count_prevents_false_positive(self):
        # confirm_count=2 means needs 2 consecutive detections
        monitor = CrashMonitor(confirm_count=2)
        state = make_state(phase="GAME_OVER")
        ab = make_abstract_state(danger_ahead=False)
        # First detection
        result1 = monitor.check(state, ab, make_history())
        assert result1 is None  # not yet confirmed

        # Second detection
        result2 = monitor.check(state, ab, make_history())
        assert result2 is not None  # now confirmed

    def test_report_has_required_fields(self):
        monitor = CrashMonitor(confirm_count=1)
        state = make_state(phase="GAME_OVER", score=30)
        ab = make_abstract_state(danger_ahead=False)
        report = monitor.check(state, ab, make_history())
        assert "snake_head" in report.evidence
        assert "direction" in report.evidence
        assert "score" in report.evidence
        assert report.timestamp != ""


# ---------------------------------------------------------------------------
# Test: TaskStatusMonitor
# ---------------------------------------------------------------------------

class TestTaskStatusMonitor:
    def test_no_report_normal_game(self):
        monitor = TaskStatusMonitor()
        state = make_state(phase="RUNNING", score=0)
        ab = make_abstract_state()
        result = monitor.check(state, ab, [], escalation_exceeded=False)
        assert result is None

    def test_hang_bug_when_escalation_exceeded(self):
        monitor = TaskStatusMonitor()
        state = make_state(phase="RUNNING")
        ab = make_abstract_state()
        result = monitor.check(state, ab, make_history(), escalation_exceeded=True)
        assert result is not None
        assert result.bug_type == BugCategory.HANG

    def test_no_hang_bug_when_game_over(self):
        # Escalation exceeded but game already ended → not a hang
        monitor = TaskStatusMonitor()
        state = make_state(phase="GAME_OVER")
        ab = make_abstract_state()
        result = monitor.check(state, ab, make_history(), escalation_exceeded=True)
        assert result is None

    def test_logic_bug_food_in_body_no_score_change(self):
        # Food is at position inside snake body, score hasn't changed
        monitor = TaskStatusMonitor()
        monitor._confirm_threshold = 2

        # State where food IS inside snake body
        snake = [Point(5, 5), Point(5, 6), Point(8, 5)]  # food at (5,6) is in snake!
        state = make_state(snake=snake, food=Point(5, 6), score=0)
        ab = make_abstract_state()

        # Trigger twice to confirm
        monitor.check(state, ab, make_history(), escalation_exceeded=False)
        result = monitor.check(state, ab, make_history(), escalation_exceeded=False)
        assert result is not None
        assert result.bug_type == BugCategory.LOGIC

    def test_hang_bug_report_has_required_fields(self):
        monitor = TaskStatusMonitor()
        state = make_state(phase="RUNNING", score=20)
        ab = make_abstract_state()
        report = monitor.check(state, ab, make_history(score=20), escalation_exceeded=True)
        assert "phase" in report.evidence
        assert "score" in report.evidence
        assert "tick_count" in report.evidence


# ---------------------------------------------------------------------------
# Test: ExecutionTimeMonitor
# ---------------------------------------------------------------------------

class TestExecutionTimeMonitor:
    def test_no_report_during_baseline(self):
        monitor = ExecutionTimeMonitor(baseline_ticks=5, anomaly_multiplier=3.0)
        for _ in range(4):
            result = monitor.record_tick_time(0.001)
            assert result is None  # baseline not yet established

    def test_no_report_normal_timing(self):
        monitor = ExecutionTimeMonitor(baseline_ticks=3, anomaly_multiplier=3.0)
        # Establish baseline
        for _ in range(3):
            monitor.record_tick_time(0.001)
        # Normal timing
        result = monitor.record_tick_time(0.002)
        assert result is None

    def test_report_slow_tick(self):
        monitor = ExecutionTimeMonitor(baseline_ticks=3, anomaly_multiplier=3.0)
        monitor._confirm_threshold = 2
        # Establish baseline at 0.001s
        for _ in range(3):
            monitor.record_tick_time(0.001)
        # Slow tick: 0.5s >> 3 × 0.001s = 0.003s
        monitor.record_tick_time(0.5)
        result = monitor.record_tick_time(0.5)
        assert result is not None
        assert result.bug_type == BugCategory.PERFORMANCE

    def test_performance_report_has_timing_evidence(self):
        monitor = ExecutionTimeMonitor(baseline_ticks=3, anomaly_multiplier=3.0)
        monitor._confirm_threshold = 1
        for _ in range(3):
            monitor.record_tick_time(0.001)
        report = monitor.record_tick_time(1.0)
        assert "elapsed_seconds" in report.evidence
        assert "baseline_avg_seconds" in report.evidence
        assert "anomaly_factor" in report.evidence

    def test_reset_clears_baseline(self):
        monitor = ExecutionTimeMonitor(baseline_ticks=3)
        for _ in range(3):
            monitor.record_tick_time(0.001)
        assert monitor._baseline_avg is not None
        monitor.reset()
        assert monitor._baseline_avg is None


# ---------------------------------------------------------------------------
# Test: DiagnosisEngine (combined)
# ---------------------------------------------------------------------------

class TestDiagnosisEngine:
    def test_no_bugs_clean_game(self):
        engine = DiagnosisEngine()
        state = make_state(phase="RUNNING", score=10)
        ab = make_abstract_state(danger_ahead=False)
        reports = engine.check(state, ab, make_history(score=10))
        assert len(reports) == 0

    def test_crash_bug_detected_by_engine(self):
        engine = DiagnosisEngine()
        engine.crash_monitor = CrashMonitor(confirm_count=1)
        state = make_state(phase="GAME_OVER")
        ab = make_abstract_state(danger_ahead=False)  # safe state → unexpected crash
        reports = engine.check(state, ab, make_history())
        assert len(reports) == 1
        assert reports[0].bug_type == BugCategory.CRASH

    def test_hang_bug_detected_by_engine(self):
        engine = DiagnosisEngine()
        state = make_state(phase="RUNNING")
        ab = make_abstract_state()
        reports = engine.check(state, ab, make_history(), escalation_exceeded=True)
        assert len(reports) == 1
        assert reports[0].bug_type == BugCategory.HANG

    def test_all_reports_accumulate(self):
        engine = DiagnosisEngine()
        engine.crash_monitor = CrashMonitor(confirm_count=1)

        # Trigger hang
        state_running = make_state(phase="RUNNING")
        ab = make_abstract_state()
        engine.check(state_running, ab, make_history(), escalation_exceeded=True)

        # Trigger crash
        state_dead = make_state(phase="GAME_OVER")
        ab_safe = make_abstract_state(danger_ahead=False)
        engine.check(state_dead, ab_safe, make_history())

        assert len(engine.all_reports) >= 2

    def test_with_mock_llm_enrichment(self):
        mock_llm = LLMClient(mock=True)
        mock_llm.set_default_mock_response("Bug analysis: This looks like a crash bug.")

        engine = DiagnosisEngine(llm_client=mock_llm)
        engine.crash_monitor = CrashMonitor(confirm_count=1)
        state = make_state(phase="GAME_OVER")
        ab = make_abstract_state(danger_ahead=False)
        reports = engine.check(state, ab, make_history())

        assert len(reports) == 1
        assert reports[0].llm_analysis != ""

    def test_report_from_reflection(self):
        from titan.modules.reflection import ReflectionResult
        engine = DiagnosisEngine()
        reflection = ReflectionResult(
            suggested_actions=["UP"],
            is_bug=True,
            reason="Score stuck despite food contact",
            stall_count=25
        )
        ab = make_abstract_state()
        report = engine.report_from_reflection(reflection, ab)
        assert report is not None
        assert report.bug_type == BugCategory.LOGIC
        assert len(engine.all_reports) == 1

    def test_no_report_from_non_bug_reflection(self):
        from titan.modules.reflection import ReflectionResult
        engine = DiagnosisEngine()
        reflection = ReflectionResult(
            suggested_actions=["UP"],
            is_bug=False,
            reason="Just taking a different path",
            stall_count=5
        )
        ab = make_abstract_state()
        report = engine.report_from_reflection(reflection, ab)
        assert report is None
        assert len(engine.all_reports) == 0

    def test_diagnosis_report_to_dict(self):
        report = DiagnosisReport(
            bug_type=BugCategory.LOGIC,
            severity=Severity.HIGH,
            description="Test description",
            evidence={"key": "value"},
        )
        d = report.to_dict()
        assert d["bug_type"] == BugCategory.LOGIC
        assert d["severity"] == Severity.HIGH
        assert d["description"] == "Test description"
        assert "timestamp" in d


# ---------------------------------------------------------------------------
# Test: Bug injection integration with diagnosis
# ---------------------------------------------------------------------------

class TestBugInjectionDiagnosis:
    """Integration tests: inject bugs into game environment, verify diagnosis detects them."""

    def test_slow_tick_detected(self):
        """SLOW_TICK bug should trigger ExecutionTimeMonitor."""
        from titan.game.snake_env import create_initial_state, set_phase, set_next_direction

        env = BuggySnakeEnv(BugType.SLOW_TICK)
        engine = DiagnosisEngine()
        engine.time_monitor = ExecutionTimeMonitor(
            baseline_ticks=3, anomaly_multiplier=3.0
        )
        engine.time_monitor._confirm_threshold = 2

        state = set_phase(create_initial_state("EASY"), "RUNNING")

        # Establish baseline with normal ticks first (mock baseline)
        for _ in range(3):
            engine.time_monitor.record_tick_time(0.0001)

        ab = make_abstract_state()
        reports = []
        for _ in range(3):
            t0 = time.time()
            state = env.tick(state)
            elapsed = time.time() - t0
            new_reports = engine.check(state, ab, [], tick_elapsed=elapsed)
            reports.extend(new_reports)
            if state.phase in ("GAME_OVER", "WIN"):
                break

        perf_reports = [r for r in reports if r.bug_type == BugCategory.PERFORMANCE]
        assert len(perf_reports) > 0, "SlowTick bug should be detected by time monitor"
