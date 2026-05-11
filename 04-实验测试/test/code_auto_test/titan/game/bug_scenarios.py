"""
Bug injection scenarios for TITAN testing.
Wraps the base snake environment with configurable bug behaviors.
"""
from __future__ import annotations

import time
from enum import Enum
from typing import Callable

from titan.game.snake_env import (
    GameState, Point,
    DIRECTION_VECTORS, OPPOSITE_DIRECTION,
    build_snake_set, is_in_bounds, random_free_point,
    set_next_direction as _set_next_direction,
)


class BugType(Enum):
    NONE = "none"
    SCORE_NO_INCREMENT = "score_no_increment"       # Food eaten but score stays same
    WALL_PASS_THROUGH = "wall_pass_through"         # Snake passes through walls (wraps)
    SELF_COLLISION_IGNORED = "self_collision_ignored"  # Self-collision doesn't kill
    FOOD_IN_BODY = "food_in_body"                   # Food can spawn inside snake
    SLOW_TICK = "slow_tick"                         # Artificial delay in tick()


class BuggySnakeEnv:
    """
    Wraps the snake game with an injected bug.
    Provides the same interface as snake_env (tick, set_next_direction).
    """

    def __init__(self, bug_type: BugType = BugType.NONE):
        self.bug_type = bug_type

    def set_next_direction(self, state: GameState, direction: str) -> GameState:
        return _set_next_direction(state, direction)

    def tick(self, state: GameState) -> GameState:
        if self.bug_type == BugType.SLOW_TICK:
            time.sleep(0.1)  # simulate slow tick (100ms artificial delay)

        if self.bug_type == BugType.NONE:
            from titan.game.snake_env import tick as _tick
            return _tick(state)

        return self._buggy_tick(state)

    def _buggy_tick(self, state: GameState) -> GameState:
        """Execute tick with the configured bug injected."""
        if state.phase != "RUNNING":
            return state

        direction = state.next_direction
        dx, dy = DIRECTION_VECTORS[direction]
        head = state.snake[0]
        new_head = Point(head.x + dx, head.y + dy)

        new = state.copy()
        new.direction = direction
        new.tick_count = state.tick_count + 1

        # --- Wall collision (with optional bug) ---
        if not is_in_bounds(new_head, state.config.grid_size):
            if self.bug_type == BugType.WALL_PASS_THROUGH:
                # Bug: wrap around instead of dying
                grid = state.config.grid_size
                new_head = Point(new_head.x % grid, new_head.y % grid)
                # fall through to normal movement
            else:
                new.phase = "GAME_OVER"
                new.high_score = max(state.score, state.high_score)
                return new

        # --- Self collision (with optional bug) ---
        body_without_tail = state.snake[:-1]
        body_set = build_snake_set(body_without_tail)
        if new_head.serialize() in body_set:
            if self.bug_type != BugType.SELF_COLLISION_IGNORED:
                new.phase = "GAME_OVER"
                new.high_score = max(state.score, state.high_score)
                return new
            # Bug: self collision is ignored, continue moving

        # --- Food eaten ---
        ate = new_head == state.food

        if ate:
            new_snake = [new_head] + list(state.snake)
        else:
            new_snake = [new_head] + list(state.snake[:-1])

        new.snake = new_snake

        if ate:
            if self.bug_type != BugType.SCORE_NO_INCREMENT:
                new.score = state.score + 10
                new.high_score = max(new.score, state.high_score)

            # Food placement
            if self.bug_type == BugType.FOOD_IN_BODY:
                # Bug: food can appear anywhere including inside snake
                import random
                grid = state.config.grid_size
                new.food = Point(
                    random.randint(0, grid - 1),
                    random.randint(0, grid - 1),
                )
            else:
                occupied = build_snake_set(new_snake)
                try:
                    new.food = random_free_point(state.config.grid_size, occupied)
                except ValueError:
                    new.phase = "WIN"
                    return new

        total_cells = state.config.grid_size * state.config.grid_size
        if len(new_snake) == total_cells:
            new.phase = "WIN"

        return new
