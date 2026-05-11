"""
Reflective Reasoning Module (TITAN Module 3)
Progress monitoring, stall detection, reflection prompting, and cross-episode coverage memory.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from titan.llm_client import LLMClient


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HistoryEntry:
    """Single step in the action history."""
    abstract_state: dict
    action: str
    score: int
    tick: int


@dataclass
class ReflectionResult:
    """Output from the reflective reasoning module."""
    suggested_actions: list[str]
    is_bug: bool
    reason: str
    stall_count: int


# ---------------------------------------------------------------------------
# Abstract state hashing
# ---------------------------------------------------------------------------

def _hash_abstract_state(abstract_state: dict) -> str:
    """Create a stable hash for an abstract state (ignoring tick/score)."""
    # Include only stable structural features
    key_fields = {
        "direction": abstract_state.get("direction"),
        "danger_ahead": abstract_state.get("danger_ahead"),
        "danger_left": abstract_state.get("danger_left"),
        "danger_right": abstract_state.get("danger_right"),
        "food_direction": abstract_state.get("food_direction"),
        "food_distance": abstract_state.get("food_distance"),
        "head_position": abstract_state.get("head_position"),
        "snake_length": abstract_state.get("snake_length"),
    }
    raw = json.dumps(key_fields, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Progress Monitor
# ---------------------------------------------------------------------------

class ProgressMonitor:
    """
    Tracks testing progress and detects stalls.
    A stall is defined as N consecutive steps with no measurable progress.
    Progress: score increase OR new abstract state visited OR new action in known state.
    """

    def __init__(self, stall_threshold: int = 20):
        self.stall_threshold = stall_threshold
        self._stall_count = 0
        self._last_score = 0
        self._visited_state_hashes: set[str] = set()

    @property
    def stall_count(self) -> int:
        return self._stall_count

    def update(self, abstract_state: dict, action: str, score: int) -> bool:
        """
        Update with a new step. Returns True if a stall has been detected.
        Resets stall counter if progress was made.
        """
        progressed = False

        # Check score increase
        if score > self._last_score:
            progressed = True
            self._last_score = score

        # Check new abstract state visited
        state_hash = _hash_abstract_state(abstract_state)
        if state_hash not in self._visited_state_hashes:
            progressed = True
            self._visited_state_hashes.add(state_hash)

        if progressed:
            self._stall_count = 0
        else:
            self._stall_count += 1

        return self._stall_count >= self.stall_threshold

    def reset(self) -> None:
        """Reset monitor for a new episode."""
        self._stall_count = 0
        self._last_score = 0
        self._visited_state_hashes.clear()


# ---------------------------------------------------------------------------
# Coverage Memory (cross-episode persistent)
# ---------------------------------------------------------------------------

class CoverageMemory:
    """
    Persistent cross-episode memory of abstract states and action outcomes.
    Stored as a state-action transition graph.
    """

    def __init__(self):
        # state_hash → {action → list of outcomes}
        self._state_action_map: dict[str, dict[str, list[str]]] = {}
        self._visited_hashes: set[str] = set()

    def record(self, abstract_state: dict, action: str, outcome: str) -> None:
        """Record a state-action-outcome triple."""
        h = _hash_abstract_state(abstract_state)
        self._visited_hashes.add(h)
        if h not in self._state_action_map:
            self._state_action_map[h] = {}
        if action not in self._state_action_map[h]:
            self._state_action_map[h][action] = []
        self._state_action_map[h][action].append(outcome)

    def is_explored(self, abstract_state: dict, action: str) -> bool:
        """Return True if this state-action pair has been tried before."""
        h = _hash_abstract_state(abstract_state)
        return (h in self._state_action_map and
                action in self._state_action_map[h])

    def get_outcomes(self, abstract_state: dict, action: str) -> list[str]:
        """Get historical outcomes for this state-action pair."""
        h = _hash_abstract_state(abstract_state)
        return self._state_action_map.get(h, {}).get(action, [])

    def get_unexplored_actions(
        self, abstract_state: dict, candidate_actions: list[str]
    ) -> list[str]:
        """Return actions that haven't been tried in this abstract state."""
        return [a for a in candidate_actions if not self.is_explored(abstract_state, a)]

    @property
    def coverage_ratio(self) -> float:
        """Estimated coverage ratio based on unique states visited."""
        # Normalized by total recorded entries (heuristic)
        if not self._state_action_map:
            return 0.0
        total_pairs = sum(
            len(actions) for actions in self._state_action_map.values()
        )
        explored = sum(
            1 for actions in self._state_action_map.values()
            for outcomes in actions.values()
            if "success" in outcomes or "food" in outcomes
        )
        return min(1.0, len(self._visited_hashes) / max(1, total_pairs))

    @property
    def visited_state_count(self) -> int:
        return len(self._visited_hashes)

    def save(self, path: str) -> None:
        """Persist memory to a JSON file."""
        data = {
            "state_action_map": self._state_action_map,
            "visited_hashes": list(self._visited_hashes),
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "CoverageMemory":
        """Load memory from a JSON file."""
        mem = cls()
        if not os.path.exists(path):
            return mem
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        mem._state_action_map = data.get("state_action_map", {})
        mem._visited_hashes = set(data.get("visited_hashes", []))
        return mem


# ---------------------------------------------------------------------------
# Reflection Engine
# ---------------------------------------------------------------------------

class ReflectionEngine:
    """
    Handles reflective reasoning when progress stalls.
    Calls LLM with structured context to suggest new strategies.
    """

    def __init__(
        self,
        stall_threshold: int = 20,
        escalation_limit: int = 3,
    ):
        self.monitor = ProgressMonitor(stall_threshold=stall_threshold)
        self.memory = CoverageMemory()
        self.escalation_limit = escalation_limit
        self._escalation_count = 0
        self._history: list[HistoryEntry] = []

    @property
    def escalation_count(self) -> int:
        return self._escalation_count

    @property
    def history(self) -> list[HistoryEntry]:
        return list(self._history)

    def record_step(
        self,
        abstract_state: dict,
        action: str,
        score: int,
        tick: int,
        outcome: str = "normal",
    ) -> bool:
        """
        Record a completed step. Returns True if reflection should be triggered.
        """
        entry = HistoryEntry(
            abstract_state=abstract_state,
            action=action,
            score=score,
            tick=tick,
        )
        self._history.append(entry)
        self.memory.record(abstract_state, action, outcome)
        return self.monitor.update(abstract_state, action, score)

    def reflect(
        self,
        abstract_state: dict,
        llm_client: Optional["LLMClient"],
    ) -> ReflectionResult:
        """
        Perform reflection. Returns suggested actions and bug assessment.
        Increments escalation count.
        """
        self._escalation_count += 1
        stall_count = self.monitor.stall_count

        # Build history summary (last 10 steps)
        recent = self._history[-10:] if len(self._history) > 10 else self._history
        history_tuples = [
            (e.abstract_state, e.action, e.score)
            for e in recent
        ]

        if llm_client is not None:
            try:
                result_dict = llm_client.reflect(
                    abstract_state, history_tuples, stall_count
                )
                return ReflectionResult(
                    suggested_actions=result_dict.get("suggested_actions", []),
                    is_bug=result_dict.get("is_bug", False),
                    reason=result_dict.get("reason", ""),
                    stall_count=stall_count,
                )
            except Exception as e:
                # LLM failure: fall through to rule-based
                pass

        # Rule-based reflection fallback (no LLM needed)
        return self._rule_based_reflect(abstract_state, stall_count)

    def _rule_based_reflect(
        self, abstract_state: dict, stall_count: int
    ) -> ReflectionResult:
        """Fallback rule-based reflection when LLM is unavailable."""
        danger_ahead = abstract_state.get("danger_ahead", False)
        danger_left = abstract_state.get("danger_left", False)
        danger_right = abstract_state.get("danger_right", False)
        direction = abstract_state.get("direction", "RIGHT")

        # Build candidate actions
        from titan.modules.perception import _turn_left, _turn_right
        candidates = []
        if not danger_left:
            candidates.append(_turn_left(direction))
        if not danger_right:
            candidates.append(_turn_right(direction))
        if not danger_ahead:
            candidates.append(direction)

        # Prioritize unexplored
        unexplored = self.memory.get_unexplored_actions(abstract_state, candidates)
        suggested = unexplored if unexplored else candidates

        is_bug = (stall_count >= 40)  # very long stall may indicate a game hang

        return ReflectionResult(
            suggested_actions=suggested,
            is_bug=is_bug,
            reason=f"Rule-based reflection after {stall_count} stall steps",
            stall_count=stall_count,
        )

    def should_terminate(self) -> bool:
        """Return True if escalation limit reached (testing should stop)."""
        return self._escalation_count >= self.escalation_limit

    def reset_episode(self) -> None:
        """Reset per-episode state (keep cross-episode memory)."""
        self.monitor.reset()
        self._history.clear()
        self._escalation_count = 0
