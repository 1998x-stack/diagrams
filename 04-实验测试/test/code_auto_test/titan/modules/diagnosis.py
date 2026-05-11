"""
Issue Diagnosis Module (TITAN Module 4)
Three-layer Oracle: Crash Monitor, Task Status Monitor, Execution Time Monitor.
Generates structured bug reports with LLM-assisted analysis.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from titan.game.snake_env import GameState
from titan.modules.perception import check_danger

if TYPE_CHECKING:
    from titan.llm_client import LLMClient


# ---------------------------------------------------------------------------
# Bug types and report structure
# ---------------------------------------------------------------------------

class BugCategory:
    CRASH = "Crash"
    LOGIC = "Logic"
    PERFORMANCE = "Performance"
    HANG = "Hang"


class Severity:
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class DiagnosisReport:
    """Structured bug report produced by the diagnosis module."""
    bug_type: str                    # BugCategory value
    severity: str                    # Severity value
    description: str                 # Human-readable description
    evidence: dict                   # State snapshot + action history
    llm_analysis: str = ""           # LLM-generated root cause analysis
    timestamp: str = ""              # ISO timestamp

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "bug_type": self.bug_type,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "llm_analysis": self.llm_analysis,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Oracle 1: Crash Monitor
# ---------------------------------------------------------------------------

class CrashMonitor:
    """
    Detects unexpected game crashes (GAME_OVER when agent was in a safe state).
    Uses consecutive-detection to suppress false positives.
    """

    def __init__(self, confirm_count: int = 1):
        self.confirm_count = confirm_count
        self._pending_count = 0

    def check(
        self,
        state: GameState,
        abstract_state: dict,
        action_history: list[tuple],
    ) -> Optional[DiagnosisReport]:
        """
        Check if the game crashed unexpectedly.
        Returns a DiagnosisReport if crash bug detected, else None.
        """
        if state.phase != "GAME_OVER":
            self._pending_count = 0
            return None

        # Check if the last action was safe (danger was False before move)
        # If the last action led to a direction that had no danger → unexpected crash
        if abstract_state.get("danger_ahead") is False:
            # The agent was in a safe state but game ended → suspicious
            self._pending_count += 1
        else:
            self._pending_count = 0
            return None

        if self._pending_count >= self.confirm_count:
            self._pending_count = 0
            recent_actions = action_history[-5:] if len(action_history) >= 5 else action_history
            return DiagnosisReport(
                bug_type=BugCategory.CRASH,
                severity=Severity.CRITICAL,
                description=(
                    "Unexpected GAME_OVER detected. "
                    "The agent was in a safe state (no danger detected) "
                    "but the game ended unexpectedly. Possible crash bug."
                ),
                evidence={
                    "final_phase": state.phase,
                    "snake_head": f"({state.snake[0].x},{state.snake[0].y})" if state.snake else "unknown",
                    "direction": state.direction,
                    "danger_ahead_before_crash": abstract_state.get("danger_ahead"),
                    "recent_actions": [(a[1], a[2]) for a in recent_actions if len(a) >= 3],
                    "score": state.score,
                },
            )
        return None


# ---------------------------------------------------------------------------
# Oracle 2: Task Status Monitor (Logic Bug Detection)
# ---------------------------------------------------------------------------

class TaskStatusMonitor:
    """
    Detects logic bugs:
    - Score not incrementing when food is eaten (SCORE_NO_INCREMENT bug)
    - Food appearing inside snake body
    - Game stuck in RUNNING with no progress (after reflection escalation)
    """

    def __init__(self):
        self._prev_score = 0
        self._snake_had_food_contact = False
        self._no_score_suspicion_count = 0
        self._confirm_threshold = 2

    def check(
        self,
        state: GameState,
        abstract_state: dict,
        action_history: list[tuple],
        escalation_exceeded: bool = False,
    ) -> Optional[DiagnosisReport]:
        """
        Check for logic bugs. Returns DiagnosisReport if detected, else None.
        """
        # Bug 1: Escalation exceeded → game stuck (Hang bug)
        if escalation_exceeded and state.phase == "RUNNING":
            return DiagnosisReport(
                bug_type=BugCategory.HANG,
                severity=Severity.HIGH,
                description=(
                    "Game appears to be stuck (Hang). "
                    "Agent exceeded reflection escalation limit without progress. "
                    "Task cannot be completed under current conditions."
                ),
                evidence={
                    "phase": state.phase,
                    "score": state.score,
                    "tick_count": state.tick_count,
                    "snake_length": abstract_state.get("snake_length"),
                    "recent_actions": [(a[1], a[2]) for a in action_history[-5:] if len(a) >= 3],
                },
            )

        # Bug 2: Score not incrementing when food was nearby and snake grew
        # Detect: snake grew (length increased from previous) but score unchanged
        if len(action_history) >= 2:
            # Check if score should have changed but didn't
            # We detect this by tracking score across steps
            current_score = state.score
            if current_score == self._prev_score:
                # Score hasn't changed; check if food appears to have been consumed
                food_in_snake = any(
                    s == state.food for s in state.snake
                )
                if food_in_snake:
                    self._no_score_suspicion_count += 1
                else:
                    self._no_score_suspicion_count = 0
            else:
                self._prev_score = current_score
                self._no_score_suspicion_count = 0

        if self._no_score_suspicion_count >= self._confirm_threshold:
            self._no_score_suspicion_count = 0
            return DiagnosisReport(
                bug_type=BugCategory.LOGIC,
                severity=Severity.HIGH,
                description=(
                    "Logic bug detected: Score did not increment after food was apparently consumed. "
                    "Expected score increase of 10 points. "
                    "Possible SCORE_NO_INCREMENT bug."
                ),
                evidence={
                    "current_score": state.score,
                    "food_position": f"({state.food.x},{state.food.y})",
                    "snake_length": len(state.snake),
                    "food_in_snake_body": True,
                    "recent_actions": [(a[1], a[2]) for a in action_history[-5:] if len(a) >= 3],
                },
            )

        return None

    def reset(self) -> None:
        self._prev_score = 0
        self._no_score_suspicion_count = 0


# ---------------------------------------------------------------------------
# Oracle 3: Execution Time Monitor
# ---------------------------------------------------------------------------

class ExecutionTimeMonitor:
    """
    Detects performance bugs by tracking tick execution times.
    Establishes a baseline from the first N ticks, then flags anomalies.
    """

    def __init__(self, baseline_ticks: int = 5, anomaly_multiplier: float = 3.0):
        self.baseline_ticks = baseline_ticks
        self.anomaly_multiplier = anomaly_multiplier
        self._timing_samples: list[float] = []
        self._baseline_avg: Optional[float] = None
        self._pending_count = 0
        self._confirm_threshold = 2

    def record_tick_time(self, elapsed: float) -> Optional[DiagnosisReport]:
        """
        Record a tick execution time. Returns DiagnosisReport if anomaly detected.
        elapsed: time in seconds for the tick() call.
        """
        # Establish baseline
        if self._baseline_avg is None:
            self._timing_samples.append(elapsed)
            if len(self._timing_samples) >= self.baseline_ticks:
                self._baseline_avg = sum(self._timing_samples) / len(self._timing_samples)
            return None

        # Check against baseline
        if elapsed > self._baseline_avg * self.anomaly_multiplier:
            self._pending_count += 1
        else:
            self._pending_count = 0

        if self._pending_count >= self._confirm_threshold:
            self._pending_count = 0
            return DiagnosisReport(
                bug_type=BugCategory.PERFORMANCE,
                severity=Severity.MEDIUM,
                description=(
                    f"Performance anomaly detected: tick execution time ({elapsed:.3f}s) "
                    f"exceeds {self.anomaly_multiplier}× baseline average ({self._baseline_avg:.3f}s). "
                    "Possible infinite loop, server lag, or resource leak."
                ),
                evidence={
                    "elapsed_seconds": elapsed,
                    "baseline_avg_seconds": self._baseline_avg,
                    "anomaly_factor": elapsed / self._baseline_avg if self._baseline_avg else None,
                    "baseline_sample_count": len(self._timing_samples),
                },
            )

        return None

    def reset(self) -> None:
        self._timing_samples = []
        self._baseline_avg = None
        self._pending_count = 0


# ---------------------------------------------------------------------------
# DiagnosisEngine: combines all three oracles
# ---------------------------------------------------------------------------

class DiagnosisEngine:
    """
    Orchestrates all three diagnostic oracles.
    Provides a single interface for the TITAN agent to use.
    """

    def __init__(self, llm_client: Optional["LLMClient"] = None):
        self.crash_monitor = CrashMonitor()
        self.task_monitor = TaskStatusMonitor()
        self.time_monitor = ExecutionTimeMonitor()
        self.llm_client = llm_client
        self._all_reports: list[DiagnosisReport] = []

    @property
    def all_reports(self) -> list[DiagnosisReport]:
        return list(self._all_reports)

    def check(
        self,
        state: GameState,
        abstract_state: dict,
        action_history: list[tuple],
        tick_elapsed: float = 0.0,
        escalation_exceeded: bool = False,
    ) -> list[DiagnosisReport]:
        """
        Run all oracles and return any newly detected bugs.
        """
        new_reports = []

        # Oracle 1: Crash
        crash_report = self.crash_monitor.check(state, abstract_state, action_history)
        if crash_report:
            crash_report = self._enrich_with_llm(crash_report, abstract_state)
            new_reports.append(crash_report)

        # Oracle 2: Logic/Hang
        task_report = self.task_monitor.check(
            state, abstract_state, action_history, escalation_exceeded
        )
        if task_report:
            task_report = self._enrich_with_llm(task_report, abstract_state)
            new_reports.append(task_report)

        # Oracle 3: Performance
        if tick_elapsed > 0:
            time_report = self.time_monitor.record_tick_time(tick_elapsed)
            if time_report:
                time_report = self._enrich_with_llm(time_report, abstract_state)
                new_reports.append(time_report)

        self._all_reports.extend(new_reports)
        return new_reports

    def _enrich_with_llm(
        self, report: DiagnosisReport, abstract_state: dict
    ) -> DiagnosisReport:
        """Add LLM analysis to the report if LLM client is available."""
        if self.llm_client is None:
            return report
        try:
            analysis = self.llm_client.generate_bug_report(
                bug_type=report.bug_type,
                abstract_state=abstract_state,
                evidence=report.evidence,
            )
            report.llm_analysis = analysis
        except Exception:
            pass  # LLM failure is non-fatal
        return report

    def report_from_reflection(
        self, reflection_result, abstract_state: dict
    ) -> Optional[DiagnosisReport]:
        """Create a report from a reflection result that suspects a bug."""
        if not reflection_result.is_bug:
            return None
        report = DiagnosisReport(
            bug_type=BugCategory.LOGIC,
            severity=Severity.HIGH,
            description=(
                f"Reflective reasoning detected a potential bug. "
                f"Reason: {reflection_result.reason}"
            ),
            evidence={
                "stall_count": reflection_result.stall_count,
                "suggested_actions": reflection_result.suggested_actions,
                "abstract_state": abstract_state,
            },
        )
        report = self._enrich_with_llm(report, abstract_state)
        self._all_reports.append(report)
        return report

    def reset(self) -> None:
        self.crash_monitor = CrashMonitor()
        self.task_monitor.reset()
        # Preserve time monitor baseline across runs (cross-run learning)
        self.time_monitor._pending_count = 0
        self._all_reports.clear()
