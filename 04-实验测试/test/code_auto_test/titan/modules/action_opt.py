"""
Action Optimization Module (TITAN Module 2)
Filters and ranks available actions using expert rules + optional LLM heuristics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from titan.game.snake_env import GameState
from titan.modules.perception import (
    check_danger, _turn_left, _turn_right,
    estimate_open_space, _step, DIRECTION_VECTORS,
)
from titan.game.snake_env import is_in_bounds, build_snake_set

if TYPE_CHECKING:
    from titan.llm_client import LLMClient

ALL_DIRECTIONS = ["UP", "DOWN", "LEFT", "RIGHT"]
OPPOSITE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ActionBundle:
    """Result from the action optimization module."""
    recommended: list[str]    # Prioritized valid directions
    reasoning: str            # Human-readable explanation
    safe_actions: list[str]   # All non-immediately-lethal directions


# ---------------------------------------------------------------------------
# Space measurement for action ranking
# ---------------------------------------------------------------------------

def _flood_fill_from(state: GameState, direction: str, max_steps: int = 100) -> int:
    """BFS flood fill count from the position after taking given direction."""
    from collections import deque
    head = state.snake[0]
    next_pos = _step(head, direction)
    grid = state.config.grid_size

    if not is_in_bounds(next_pos, grid):
        return 0

    body_set = build_snake_set(state.snake[:-1])  # exclude tail (it moves away)
    if next_pos.serialize() in body_set:
        return 0

    visited = {next_pos.serialize()}
    queue: deque = deque([next_pos])
    count = 0

    while queue and count < max_steps:
        current = queue.popleft()
        count += 1
        for d in ALL_DIRECTIONS:
            nxt = _step(current, d)
            key = nxt.serialize()
            if (is_in_bounds(nxt, grid) and
                    key not in body_set and
                    key not in visited):
                visited.add(key)
                queue.append(nxt)

    return len(visited)


# ---------------------------------------------------------------------------
# Rule-based filtering (Layer A)
# ---------------------------------------------------------------------------

def _get_safe_actions(state: GameState, current_direction: str) -> list[str]:
    """Return actions that don't cause immediate death (wall or self collision)."""
    safe = []
    for d in ALL_DIRECTIONS:
        if d == OPPOSITE.get(current_direction):
            continue  # skip 180° reverse
        if not check_danger(state, d):
            safe.append(d)
    return safe


def _is_food_direction(abstract_state: dict, action: str) -> bool:
    """Check if taking this action moves toward food."""
    food_dir = abstract_state.get("food_direction", "")
    return action in food_dir  # e.g., "UP" in "UP-RIGHT"


def _rank_by_open_space(
    state: GameState, safe_actions: list[str]
) -> list[tuple[str, int]]:
    """
    Rank safe actions by accessible space after taking them.
    Returns list of (direction, space_count) sorted descending.
    """
    scored = [(d, _flood_fill_from(state, d)) for d in safe_actions]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Main recommendation function
# ---------------------------------------------------------------------------

def recommend(
    abstract_state: dict,
    state: GameState,
    llm_client: Optional["LLMClient"] = None,
) -> ActionBundle:
    """
    Generate recommended action bundle for the current state.

    Priority order:
    1. Filter 180° reversal (always invalid in snake)
    2. Filter immediately lethal actions
    3. Prioritize toward food (if safe)
    4. Rank remaining by open space (flood fill)
    5. Optionally call LLM for final ranking (if >2 candidates)

    Returns ActionBundle with recommended order and reasoning.
    """
    current_dir = abstract_state.get("direction", state.direction)

    # Step 1-2: Get safe non-reverse actions
    safe_actions = _get_safe_actions(state, current_dir)

    if not safe_actions:
        # Dead end: no safe moves available
        return ActionBundle(
            recommended=[],
            reasoning="No safe actions available. Game over expected.",
            safe_actions=[],
        )

    if len(safe_actions) == 1:
        return ActionBundle(
            recommended=safe_actions,
            reasoning=f"Only one safe action: {safe_actions[0]}",
            safe_actions=safe_actions,
        )

    # Step 3: Rank by open space
    ranked = _rank_by_open_space(state, safe_actions)
    space_ordered = [d for d, _ in ranked]

    # Step 4: Move food-directed action to front if it's safe
    food_dir_action = None
    for d in space_ordered:
        if _is_food_direction(abstract_state, d):
            food_dir_action = d
            break

    if food_dir_action:
        ordered = [food_dir_action] + [d for d in space_ordered if d != food_dir_action]
    else:
        ordered = space_ordered

    reasoning_parts = [f"Safe actions: {safe_actions}"]
    if food_dir_action:
        reasoning_parts.append(f"Food direction: {food_dir_action} prioritized")
    reasoning_parts.append(
        f"Space ranking: {[(d, s) for d, s in ranked]}"
    )

    # Step 5: Optional LLM reranking (only if >2 candidates and LLM available)
    if llm_client is not None and len(ordered) > 2:
        try:
            llm_choice = llm_client.decide_action(abstract_state, ordered)
            if llm_choice in ordered:
                # Move LLM choice to front
                ordered = [llm_choice] + [d for d in ordered if d != llm_choice]
                reasoning_parts.append(f"LLM reranked: {llm_choice} moved to front")
        except Exception:
            pass  # LLM failure is non-fatal; fall back to rule-based

    return ActionBundle(
        recommended=ordered,
        reasoning="; ".join(reasoning_parts),
        safe_actions=safe_actions,
    )


# ---------------------------------------------------------------------------
# Action validation
# ---------------------------------------------------------------------------

def validate_action(state: GameState, action: str) -> bool:
    """
    Validate that an action is syntactically and structurally valid.
    Does NOT check if it causes death—that's the agent's decision.
    """
    if action not in ALL_DIRECTIONS:
        return False
    # Check that it's not a 180° reversal of current direction
    if action == OPPOSITE.get(state.direction):
        return False
    return True
