"""
Perception Abstraction Module (TITAN Module 1)
Converts raw GameState into a compact symbolic representation for LLM reasoning.
Integrates RAG knowledge for context injection.
"""
from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Optional

from titan.game.snake_env import (
    GameState, Point,
    DIRECTION_VECTORS, OPPOSITE_DIRECTION,
    is_in_bounds, build_snake_set,
)

if TYPE_CHECKING:
    from titan.rag.knowledge_base import KnowledgeBase


# ---------------------------------------------------------------------------
# Direction utilities
# ---------------------------------------------------------------------------

def _turn_left(direction: str) -> str:
    """Return direction after turning left."""
    turns = {"UP": "LEFT", "LEFT": "DOWN", "DOWN": "RIGHT", "RIGHT": "UP"}
    return turns[direction]


def _turn_right(direction: str) -> str:
    """Return direction after turning right."""
    turns = {"UP": "RIGHT", "RIGHT": "DOWN", "DOWN": "LEFT", "LEFT": "UP"}
    return turns[direction]


def _step(point: Point, direction: str) -> Point:
    """Return next point after one step in given direction."""
    dx, dy = DIRECTION_VECTORS[direction]
    return Point(point.x + dx, point.y + dy)


# ---------------------------------------------------------------------------
# Danger detection
# ---------------------------------------------------------------------------

def check_danger(state: GameState, direction: str) -> bool:
    """
    Check if moving in the given direction from the current head position
    would result in immediate collision (wall or snake body).
    """
    head = state.snake[0]
    next_pos = _step(head, direction)
    grid = state.config.grid_size

    # Wall check
    if not is_in_bounds(next_pos, grid):
        return True

    # Self check (exclude tail, which will move away)
    body_without_tail = state.snake[:-1]
    body_set = build_snake_set(body_without_tail)
    return next_pos.serialize() in body_set


# ---------------------------------------------------------------------------
# Food relative direction
# ---------------------------------------------------------------------------

def get_food_direction(head: Point, food: Point) -> str:
    """Return a compass string indicating food direction relative to head."""
    dx = food.x - head.x
    dy = food.y - head.y

    vertical = ""
    horizontal = ""

    if dy < 0:
        vertical = "UP"
    elif dy > 0:
        vertical = "DOWN"

    if dx > 0:
        horizontal = "RIGHT"
    elif dx < 0:
        horizontal = "LEFT"

    if vertical and horizontal:
        return f"{vertical}-{horizontal}"
    elif vertical:
        return vertical
    elif horizontal:
        return horizontal
    else:
        return "SAME"  # food is at head position (shouldn't happen normally)


def get_food_distance(head: Point, food: Point) -> int:
    """Manhattan distance between head and food."""
    return abs(food.x - head.x) + abs(food.y - head.y)


# ---------------------------------------------------------------------------
# Open space estimation (flood fill)
# ---------------------------------------------------------------------------

def estimate_open_space(state: GameState, max_steps: int = 200) -> float:
    """
    Estimate accessible space ratio from the snake head via BFS flood fill.
    Returns a float in [0, 1] representing fraction of grid cells reachable.
    """
    head = state.snake[0]
    grid = state.config.grid_size
    body_set = build_snake_set(state.snake)
    total_cells = grid * grid

    visited = {head.serialize()}
    queue: deque = deque([head])
    count = 0

    while queue and count < max_steps:
        current = queue.popleft()
        count += 1
        for direction in ("UP", "DOWN", "LEFT", "RIGHT"):
            nxt = _step(current, direction)
            key = nxt.serialize()
            if (is_in_bounds(nxt, grid) and
                    key not in body_set and
                    key not in visited):
                visited.add(key)
                queue.append(nxt)

    return min(1.0, len(visited) / max(1, total_cells))


# ---------------------------------------------------------------------------
# Head position classification
# ---------------------------------------------------------------------------

def classify_head_position(head: Point, grid_size: int) -> str:
    """Classify head position as quadrant or center."""
    mid = grid_size / 2
    threshold = grid_size / 4

    in_top = head.y < threshold
    in_bottom = head.y >= grid_size - threshold
    in_left = head.x < threshold
    in_right = head.x >= grid_size - threshold

    if in_top and in_left:
        return "top-left"
    elif in_top and in_right:
        return "top-right"
    elif in_bottom and in_left:
        return "bottom-left"
    elif in_bottom and in_right:
        return "bottom-right"
    elif in_top:
        return "top"
    elif in_bottom:
        return "bottom"
    elif in_left:
        return "left"
    elif in_right:
        return "right"
    else:
        return "center"


# ---------------------------------------------------------------------------
# Snake length classification
# ---------------------------------------------------------------------------

def classify_snake_length(length: int, grid_size: int) -> str:
    """Classify snake length by absolute segment count."""
    if length < 5:
        return "short"
    elif length <= 20:
        return "medium"
    else:
        return "long"


# ---------------------------------------------------------------------------
# Food distance classification
# ---------------------------------------------------------------------------

def classify_food_distance(distance: int) -> str:
    """Classify food distance as close/medium/far."""
    if distance <= 3:
        return "close"
    elif distance <= 7:
        return "medium"
    else:
        return "far"


# ---------------------------------------------------------------------------
# Main abstraction function
# ---------------------------------------------------------------------------

def abstract(
    state: GameState,
    knowledge_base: Optional["KnowledgeBase"] = None,
) -> dict:
    """
    Convert raw GameState to abstract symbolic representation.

    Returns a dict with:
        phase, direction, score, snake_length, food_distance, food_direction,
        danger_ahead, danger_left, danger_right, head_position,
        open_space_ratio, relevant_rules
    """
    head = state.snake[0]
    direction = state.direction
    grid = state.config.grid_size

    # Danger checks (current, left turn, right turn)
    danger_ahead = check_danger(state, direction)
    danger_left = check_danger(state, _turn_left(direction))
    danger_right = check_danger(state, _turn_right(direction))
    # Also backward (180° reverse - always blocked by input, but useful for diagnosis)
    danger_back = check_danger(state, OPPOSITE_DIRECTION[direction])

    food_dist = get_food_distance(head, state.food)
    food_dir = get_food_direction(head, state.food)
    snake_len_str = classify_snake_length(len(state.snake), grid)
    food_dist_str = classify_food_distance(food_dist)
    head_pos = classify_head_position(head, grid)
    open_space = estimate_open_space(state)

    # Query RAG for relevant knowledge
    relevant_rules: list[str] = []
    if knowledge_base is not None:
        query_parts = []
        if danger_ahead:
            query_parts.append("danger ahead collision")
        if food_dist_str == "close":
            query_parts.append("food close")
        if snake_len_str == "long":
            query_parts.append("long snake strategy")
        query_parts.append(f"score {state.score}")
        query = " ".join(query_parts) or "snake game strategy"
        relevant_rules = knowledge_base.retrieve(query, top_k=3)

    return {
        "phase": state.phase,
        "direction": direction,
        "score": state.score,
        "tick_count": state.tick_count,
        "snake_length": snake_len_str,
        "snake_length_raw": len(state.snake),
        "food_distance": food_dist_str,
        "food_distance_raw": food_dist,
        "food_direction": food_dir,
        "danger_ahead": danger_ahead,
        "danger_left": danger_left,
        "danger_right": danger_right,
        "danger_back": danger_back,
        "head_position": head_pos,
        "open_space_ratio": round(open_space, 3),
        "grid_size": grid,
        "relevant_rules": relevant_rules,
    }
