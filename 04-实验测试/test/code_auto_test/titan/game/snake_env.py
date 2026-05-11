"""
Snake Game Environment - Python simulation mirroring TypeScript GameEngine.ts
Pure functions, immutable state updates.
"""
from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Types (mirror src/types.ts)
# ---------------------------------------------------------------------------

Direction = Literal["UP", "DOWN", "LEFT", "RIGHT"]
GamePhase = Literal["IDLE", "RUNNING", "PAUSED", "GAME_OVER", "WIN"]

DIRECTION_VECTORS: dict[str, tuple[int, int]] = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
}

OPPOSITE_DIRECTION: dict[str, str] = {
    "UP": "DOWN", "DOWN": "UP",
    "LEFT": "RIGHT", "RIGHT": "LEFT",
}

DIFFICULTIES = {
    "EASY":   {"tick_interval": 200, "grid_size": 20, "initial_length": 3},
    "NORMAL": {"tick_interval": 130, "grid_size": 25, "initial_length": 4},
    "HARD":   {"tick_interval": 80,  "grid_size": 30, "initial_length": 5},
}


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def serialize(self) -> str:
        return f"{self.x},{self.y}"

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y


@dataclass
class Difficulty:
    tick_interval: int   # ms per tick
    grid_size: int       # square grid side length
    initial_length: int  # initial snake length


@dataclass
class GameState:
    snake: list[Point]           # index 0 = head, last = tail
    food: Point
    direction: str               # current active direction
    next_direction: str          # direction for next tick
    phase: str                   # GamePhase
    score: int
    high_score: int
    tick_count: int
    config: Difficulty

    def copy(self) -> "GameState":
        return GameState(
            snake=list(self.snake),
            food=self.food,
            direction=self.direction,
            next_direction=self.next_direction,
            phase=self.phase,
            score=self.score,
            high_score=self.high_score,
            tick_count=self.tick_count,
            config=Difficulty(
                tick_interval=self.config.tick_interval,
                grid_size=self.config.grid_size,
                initial_length=self.config.initial_length,
            ),
        )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def is_in_bounds(point: Point, grid_size: int) -> bool:
    return 0 <= point.x < grid_size and 0 <= point.y < grid_size


def build_snake_set(snake: list[Point]) -> set[str]:
    return {p.serialize() for p in snake}


def random_free_point(grid_size: int, occupied: set[str]) -> Point:
    """Generate a random point not in occupied set."""
    total = grid_size * grid_size
    if len(occupied) >= total:
        raise ValueError("No free cells available")

    # Strategy A: random retry
    for _ in range(20):
        x = random.randint(0, grid_size - 1)
        y = random.randint(0, grid_size - 1)
        p = Point(x, y)
        if p.serialize() not in occupied:
            return p

    # Strategy B: enumerate all free cells
    all_free = [
        Point(x, y)
        for x in range(grid_size)
        for y in range(grid_size)
        if f"{x},{y}" not in occupied
    ]
    return random.choice(all_free)


# ---------------------------------------------------------------------------
# State factory
# ---------------------------------------------------------------------------

def create_initial_state(difficulty: str = "EASY") -> GameState:
    """Create initial game state for given difficulty."""
    cfg_dict = DIFFICULTIES[difficulty]
    config = Difficulty(**cfg_dict)
    grid = config.grid_size
    length = config.initial_length

    # Start snake horizontally in center, moving RIGHT
    cx, cy = grid // 2, grid // 2
    snake = [Point(cx - i, cy) for i in range(length)]
    occupied = build_snake_set(snake)
    food = random_free_point(grid, occupied)

    return GameState(
        snake=snake,
        food=food,
        direction="RIGHT",
        next_direction="RIGHT",
        phase="IDLE",
        score=0,
        high_score=0,
        tick_count=0,
        config=config,
    )


# ---------------------------------------------------------------------------
# Core game logic (pure functions, mirror GameEngine.ts)
# ---------------------------------------------------------------------------

def set_next_direction(state: GameState, direction: str) -> GameState:
    """Update next direction, ignoring 180° reversals."""
    if OPPOSITE_DIRECTION.get(state.direction) == direction:
        return state  # ignore reverse
    new = state.copy()
    new.next_direction = direction
    return new


def tick(state: GameState) -> GameState:
    """
    Advance game by one tick. Pure function.
    Returns new GameState (immutable pattern).
    """
    if state.phase != "RUNNING":
        return state

    direction = state.next_direction
    dx, dy = DIRECTION_VECTORS[direction]
    head = state.snake[0]
    new_head = Point(head.x + dx, head.y + dy)

    new = state.copy()
    new.direction = direction
    new.tick_count = state.tick_count + 1

    # Wall collision
    if not is_in_bounds(new_head, state.config.grid_size):
        new.phase = "GAME_OVER"
        new.high_score = max(state.score, state.high_score)
        return new

    # Self collision (exclude tail, which moves away)
    body_without_tail = state.snake[:-1]
    body_set = build_snake_set(body_without_tail)
    if new_head.serialize() in body_set:
        new.phase = "GAME_OVER"
        new.high_score = max(state.score, state.high_score)
        return new

    # Check food eaten
    ate = new_head == state.food

    if ate:
        new_snake = [new_head] + list(state.snake)  # grow
    else:
        new_snake = [new_head] + list(state.snake[:-1])  # normal move

    new.snake = new_snake

    # Handle food eaten
    if ate:
        new.score = state.score + 10
        new.high_score = max(new.score, state.high_score)
        occupied = build_snake_set(new_snake)
        try:
            new.food = random_free_point(state.config.grid_size, occupied)
        except ValueError:
            # No free cells → WIN
            new.phase = "WIN"
            return new

    # Win condition: snake fills the grid
    total_cells = state.config.grid_size * state.config.grid_size
    if len(new_snake) == total_cells:
        new.phase = "WIN"

    return new


def set_phase(state: GameState, phase: str) -> GameState:
    """Directly set the game phase (for agent use)."""
    new = state.copy()
    new.phase = phase
    return new
