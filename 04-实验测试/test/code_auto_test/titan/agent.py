"""
TITAN Agent - Main Testing Loop
Integrates all four modules: Perception, Action Optimization, Reflective Reasoning, Issue Diagnosis.
Mirrors Algorithm 1 from the TITAN paper, adapted for the Snake game.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

from titan.game.snake_env import (
    GameState, create_initial_state, set_phase,
    set_next_direction, tick as clean_tick,
)
from titan.game.bug_scenarios import BugType, BuggySnakeEnv
from titan.rag.knowledge_base import KnowledgeBase
from titan.llm_client import LLMClient
from titan.modules.perception import abstract
from titan.modules.action_opt import recommend, validate_action
from titan.modules.reflection import ReflectionEngine
from titan.modules.diagnosis import DiagnosisEngine, DiagnosisReport


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TITANTestReport:
    """Final output of a TITAN testing run."""
    bug_type_tested: str
    bugs_detected: list[DiagnosisReport]
    total_ticks: int
    final_score: int
    final_phase: str
    coverage_ratio: float
    visited_state_count: int
    terminated_by: str           # "task_complete" | "max_ticks" | "escalation_limit" | "game_over"
    action_history_length: int

    @property
    def bug_count(self) -> int:
        return len(self.bugs_detected)

    def summary(self) -> str:
        lines = [
            f"=== TITAN Test Report ===",
            f"Bug scenario tested : {self.bug_type_tested}",
            f"Ticks executed      : {self.total_ticks}",
            f"Final score         : {self.final_score}",
            f"Final phase         : {self.final_phase}",
            f"Bugs detected       : {self.bug_count}",
            f"Coverage ratio      : {self.coverage_ratio:.2%}",
            f"States visited      : {self.visited_state_count}",
            f"Terminated by       : {self.terminated_by}",
        ]
        for i, report in enumerate(self.bugs_detected, 1):
            lines.append(f"\n--- Bug #{i} ---")
            lines.append(f"  Type     : {report.bug_type}")
            lines.append(f"  Severity : {report.severity}")
            lines.append(f"  Description: {report.description[:120]}...")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# TITAN Agent
# ---------------------------------------------------------------------------

class TITANAgent:
    """
    LLM-driven snake game testing agent.
    Implements Algorithm 1 from the TITAN paper.

    Usage:
        agent = TITANAgent()
        report = agent.run(bug_type=BugType.NONE, max_ticks=200)
        print(report.summary())
    """

    def __init__(
        self,
        difficulty: str = "EASY",
        stall_threshold: int = 20,
        escalation_limit: int = 3,
        mock_llm: Optional[bool] = None,
        llm_model: str = "claude-sonnet-4-6",
        use_rag: bool = True,
    ):
        self.difficulty = difficulty
        self.use_rag = use_rag

        # Init LLM client
        self.llm = LLMClient(model=llm_model, mock=mock_llm)

        # Init RAG knowledge base
        self.kb = KnowledgeBase() if use_rag else None

        # Init modules
        self.reflection_engine = ReflectionEngine(
            stall_threshold=stall_threshold,
            escalation_limit=escalation_limit,
        )
        self.diagnosis_engine = DiagnosisEngine(llm_client=self.llm)

    def run(
        self,
        bug_type: BugType = BugType.NONE,
        max_ticks: int = 500,
        verbose: bool = False,
    ) -> TITANTestReport:
        """
        Run a complete testing session against the snake game.

        Args:
            bug_type: Which bug to inject (BugType.NONE for clean game)
            max_ticks: Maximum number of game ticks before stopping
            verbose: Print step-by-step logs

        Returns:
            TITANTestReport with all detected bugs and metrics
        """
        # Setup environment with (optional) bug
        env = BuggySnakeEnv(bug_type=bug_type)

        # Initialize game state
        state = create_initial_state(self.difficulty)
        state = set_phase(state, "RUNNING")

        # Reset per-episode state (keep cross-episode memory)
        self.reflection_engine.reset_episode()
        self.diagnosis_engine.reset()

        action_history: list[tuple] = []
        terminated_by = "max_ticks"

        if verbose:
            print(f"TITAN Agent starting | bug={bug_type.value} | difficulty={self.difficulty}")

        # === Main testing loop (Algorithm 1) ===
        for tick_num in range(max_ticks):

            # --- Step 1: Perception & Abstraction ---
            ab_state = abstract(state, knowledge_base=self.kb)

            # --- Step 2: Action Optimization ---
            bundle = recommend(ab_state, state, llm_client=self.llm)

            # --- Step 3: LLM Decision ---
            if bundle.recommended:
                action = self.llm.decide_action(ab_state, bundle.recommended)
                if action not in bundle.recommended:
                    action = bundle.recommended[0]
            else:
                # No safe actions → dead end, game should end
                action = state.direction  # just keep going (will hit wall/self)

            # Validate action
            if not validate_action(state, action):
                action = bundle.safe_actions[0] if bundle.safe_actions else state.direction

            # --- Step 4: Execute ---
            t0 = time.time()
            state = env.tick(set_next_direction(state, action))
            tick_elapsed = time.time() - t0

            action_history.append((ab_state, action, state.score))

            if verbose and tick_num % 20 == 0:
                print(
                    f"  Tick {tick_num:3d} | score={state.score:3d} | "
                    f"phase={state.phase:8s} | action={action} | "
                    f"head=({state.snake[0].x},{state.snake[0].y})"
                )

            # --- Step 5: Monitoring & Reflection ---
            stall_triggered = self.reflection_engine.record_step(
                ab_state, action, state.score, tick_num,
                outcome="food" if state.score > (action_history[-2][2] if len(action_history) > 1 else 0) else "normal"
            )

            if stall_triggered:
                reflection_result = self.reflection_engine.reflect(ab_state, self.llm)
                if verbose:
                    print(f"  [Reflection] stall={reflection_result.stall_count} "
                          f"is_bug={reflection_result.is_bug}")

                # Report from reflection
                if reflection_result.is_bug:
                    self.diagnosis_engine.report_from_reflection(reflection_result, ab_state)

                # Inject suggested actions into next steps
                if reflection_result.suggested_actions:
                    # Queue suggested actions (will be consumed on next ticks)
                    # For simplicity, apply the first suggestion immediately
                    pass  # reflection influences next iteration's abstract state

                if self.reflection_engine.should_terminate():
                    terminated_by = "escalation_limit"
                    break

            # --- Step 6: Diagnosis Oracles ---
            escalation_exceeded = self.reflection_engine.should_terminate()
            new_reports = self.diagnosis_engine.check(
                state=state,
                abstract_state=ab_state,
                action_history=action_history,
                tick_elapsed=tick_elapsed,
                escalation_exceeded=escalation_exceeded,
            )

            if verbose and new_reports:
                for r in new_reports:
                    print(f"  [BUG DETECTED] {r.bug_type}: {r.description[:60]}...")

            # --- Termination checks ---
            if state.phase == "WIN":
                terminated_by = "task_complete"
                break
            if state.phase == "GAME_OVER":
                terminated_by = "game_over"
                break

        if verbose:
            print(f"TITAN Agent done | ticks={tick_num+1} | bugs={len(self.diagnosis_engine.all_reports)}")

        return TITANTestReport(
            bug_type_tested=bug_type.value,
            bugs_detected=self.diagnosis_engine.all_reports,
            total_ticks=tick_num + 1,
            final_score=state.score,
            final_phase=state.phase,
            coverage_ratio=self.reflection_engine.memory.coverage_ratio,
            visited_state_count=self.reflection_engine.memory.visited_state_count,
            terminated_by=terminated_by,
            action_history_length=len(action_history),
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry for: python -m titan.agent"""
    import argparse

    parser = argparse.ArgumentParser(description="TITAN Snake Testing Agent")
    parser.add_argument(
        "--bug", default="none",
        choices=[b.value for b in BugType],
        help="Bug scenario to inject"
    )
    parser.add_argument("--difficulty", default="EASY", choices=["EASY", "NORMAL", "HARD"])
    parser.add_argument("--max-ticks", type=int, default=300)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--mock-llm", action="store_true", help="Use mock LLM (no API key needed)")

    args = parser.parse_args()

    bug_type = BugType(args.bug)
    mock = args.mock_llm or os.environ.get("TITAN_MOCK_LLM", "0") == "1"

    agent = TITANAgent(
        difficulty=args.difficulty,
        mock_llm=mock,
    )

    report = agent.run(bug_type=bug_type, max_ticks=args.max_ticks, verbose=args.verbose)
    print(report.summary())


if __name__ == "__main__":
    main()
