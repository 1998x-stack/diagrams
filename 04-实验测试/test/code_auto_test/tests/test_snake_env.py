"""
Layer 0 Tests: Python Snake Game Environment
Tests mirror the TypeScript game logic to ensure Python simulation is correct.
"""
import pytest
from titan.game.snake_env import (
    Point, GameState, Difficulty,
    create_initial_state, tick, set_next_direction, set_phase,
    is_in_bounds, build_snake_set, random_free_point,
)
from titan.game.bug_scenarios import BugType, BuggySnakeEnv


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_state(
    snake=None, food=None, direction="RIGHT", next_direction=None,
    phase="RUNNING", score=0, grid_size=10
) -> GameState:
    """Helper to create minimal test state."""
    config = Difficulty(tick_interval=200, grid_size=grid_size, initial_length=3)
    if snake is None:
        snake = [Point(5, 5), Point(4, 5), Point(3, 5)]
    if food is None:
        food = Point(8, 5)
    if next_direction is None:
        next_direction = direction
    return GameState(
        snake=snake,
        food=food,
        direction=direction,
        next_direction=next_direction,
        phase=phase,
        score=score,
        high_score=0,
        tick_count=0,
        config=config,
    )


# ---------------------------------------------------------------------------
# Test: Basic movement
# ---------------------------------------------------------------------------

class TestMovement:
    def test_move_right(self):
        state = make_state(snake=[Point(5, 5), Point(4, 5), Point(3, 5)], next_direction="RIGHT")
        new = tick(state)
        assert new.snake[0] == Point(6, 5), "Head should move right"
        assert len(new.snake) == 3, "Length unchanged without eating"

    def test_move_left(self):
        state = make_state(
            snake=[Point(5, 5), Point(6, 5), Point(7, 5)],
            direction="LEFT", next_direction="LEFT",
            food=Point(0, 0)
        )
        new = tick(state)
        assert new.snake[0] == Point(4, 5)

    def test_move_up(self):
        state = make_state(
            snake=[Point(5, 5), Point(5, 6), Point(5, 7)],
            direction="UP", next_direction="UP",
            food=Point(0, 0)
        )
        new = tick(state)
        assert new.snake[0] == Point(5, 4)

    def test_move_down(self):
        state = make_state(
            snake=[Point(5, 5), Point(5, 4), Point(5, 3)],
            direction="DOWN", next_direction="DOWN",
            food=Point(0, 0)
        )
        new = tick(state)
        assert new.snake[0] == Point(5, 6)

    def test_tick_increments_tick_count(self):
        state = make_state()
        new = tick(state)
        assert new.tick_count == 1

    def test_tick_noop_when_not_running(self):
        state = make_state(phase="PAUSED")
        new = tick(state)
        assert new.phase == "PAUSED"
        assert new.tick_count == 0


# ---------------------------------------------------------------------------
# Test: Food eating
# ---------------------------------------------------------------------------

class TestFoodEating:
    def test_eating_food_increases_score(self):
        # Head will move to (6,5), food is at (6,5)
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            food=Point(6, 5),
            next_direction="RIGHT"
        )
        new = tick(state)
        assert new.score == 10

    def test_eating_food_grows_snake(self):
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            food=Point(6, 5),
            next_direction="RIGHT"
        )
        new = tick(state)
        assert len(new.snake) == 4

    def test_food_regenerates_after_eating(self):
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            food=Point(6, 5),
            next_direction="RIGHT"
        )
        new = tick(state)
        assert new.food != Point(6, 5), "Food should move after being eaten"
        occupied = build_snake_set(new.snake)
        assert new.food.serialize() not in occupied, "Food must not be inside snake"

    def test_no_score_change_without_food(self):
        state = make_state(food=Point(0, 0), next_direction="RIGHT")  # food far away
        new = tick(state)
        assert new.score == 0


# ---------------------------------------------------------------------------
# Test: Collisions
# ---------------------------------------------------------------------------

class TestCollisions:
    def test_wall_collision_right(self):
        # Head at right edge, moving right
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            next_direction="RIGHT",
            grid_size=10
        )
        new = tick(state)
        assert new.phase == "GAME_OVER"

    def test_wall_collision_top(self):
        state = make_state(
            snake=[Point(5, 0), Point(5, 1), Point(5, 2)],
            direction="UP", next_direction="UP",
            grid_size=10
        )
        new = tick(state)
        assert new.phase == "GAME_OVER"

    def test_wall_collision_left(self):
        state = make_state(
            snake=[Point(0, 5), Point(1, 5), Point(2, 5)],
            direction="LEFT", next_direction="LEFT",
            grid_size=10
        )
        new = tick(state)
        assert new.phase == "GAME_OVER"

    def test_wall_collision_bottom(self):
        state = make_state(
            snake=[Point(5, 9), Point(5, 8), Point(5, 7)],
            direction="DOWN", next_direction="DOWN",
            grid_size=10
        )
        new = tick(state)
        assert new.phase == "GAME_OVER"

    def test_self_collision(self):
        # U-shape: head at (5,5), body loops back
        # Snake: head(5,5) → (5,4) → (6,4) → (6,5) - moving LEFT, next is UP
        # Actually create a scenario where head will hit body
        snake = [Point(5, 5), Point(4, 5), Point(4, 4), Point(5, 4), Point(6, 4)]
        state = make_state(
            snake=snake,
            direction="RIGHT",
            next_direction="UP",  # will move to (5,4) which is in body
            food=Point(0, 0),
            grid_size=10
        )
        new = tick(state)
        assert new.phase == "GAME_OVER"

    def test_no_self_collision_with_tail(self):
        # Snake forms a ring: head at (0,0), body (0,1)→(1,1)→(1,0)=tail
        # Head moves RIGHT to (1,0) which is EXACTLY where the tail is.
        # Since tail is excluded from body_without_tail, this should NOT collide.
        snake = [Point(0, 0), Point(0, 1), Point(1, 1), Point(1, 0)]
        state = make_state(
            snake=snake,
            direction="DOWN",
            next_direction="RIGHT",
            food=Point(4, 4),
            grid_size=5
        )
        new = tick(state)
        assert new.phase == "RUNNING"

    def test_high_score_updated_on_game_over(self):
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            next_direction="RIGHT",
            score=50,
            grid_size=10
        )
        new = tick(state)
        assert new.high_score == 50


# ---------------------------------------------------------------------------
# Test: Win condition
# ---------------------------------------------------------------------------

class TestWinCondition:
    def test_win_when_snake_fills_grid(self):
        # 2x2 grid, snake fills 3 cells, food at (1,1)
        # After eating food, snake will be 4 cells = 2x2 = WIN
        config = Difficulty(tick_interval=200, grid_size=2, initial_length=1)
        snake = [Point(0, 0), Point(1, 0), Point(1, 1)]
        state = GameState(
            snake=snake,
            food=Point(0, 1),
            direction="LEFT",
            next_direction="DOWN",
            phase="RUNNING",
            score=20,
            high_score=0,
            tick_count=0,
            config=config,
        )
        new = tick(state)
        # head moves DOWN from (0,0) → (0,1) where food is
        assert new.phase == "WIN"


# ---------------------------------------------------------------------------
# Test: Direction control
# ---------------------------------------------------------------------------

class TestDirectionControl:
    def test_set_next_direction_valid(self):
        state = make_state(direction="RIGHT")
        new = set_next_direction(state, "UP")
        assert new.next_direction == "UP"

    def test_set_next_direction_ignores_180_reverse(self):
        state = make_state(direction="RIGHT")
        new = set_next_direction(state, "LEFT")  # reverse of RIGHT
        assert new.next_direction == "RIGHT", "180° reverse should be ignored"

    def test_set_next_direction_ignores_up_down_reverse(self):
        # Current direction=UP, next_direction=UP; try to set DOWN (reverse) → ignored
        state = make_state(direction="UP", next_direction="UP")
        new = set_next_direction(state, "DOWN")
        assert new.next_direction == "UP"  # unchanged because DOWN reverses UP

    def test_set_next_direction_allows_perpendicular(self):
        state = make_state(direction="RIGHT")
        new = set_next_direction(state, "UP")
        assert new.next_direction == "UP"

        new2 = set_next_direction(state, "DOWN")
        assert new2.next_direction == "DOWN"


# ---------------------------------------------------------------------------
# Test: Initial state
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_create_easy_state(self):
        state = create_initial_state("EASY")
        assert state.phase == "IDLE"
        assert state.config.grid_size == 20
        assert len(state.snake) == 3
        assert state.score == 0

    def test_create_hard_state(self):
        state = create_initial_state("HARD")
        assert state.config.grid_size == 30
        assert len(state.snake) == 5

    def test_food_not_on_snake(self):
        for _ in range(10):
            state = create_initial_state("EASY")
            occupied = build_snake_set(state.snake)
            assert state.food.serialize() not in occupied


# ---------------------------------------------------------------------------
# Test: Bug injection
# ---------------------------------------------------------------------------

class TestBugInjection:
    def test_score_no_increment_bug(self):
        env = BuggySnakeEnv(BugType.SCORE_NO_INCREMENT)
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            food=Point(6, 5),
            next_direction="RIGHT"
        )
        new = env.tick(state)
        assert new.score == 0, "Bug: score should NOT increment"

    def test_wall_pass_through_bug(self):
        env = BuggySnakeEnv(BugType.WALL_PASS_THROUGH)
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            next_direction="RIGHT",
            grid_size=10
        )
        new = env.tick(state)
        assert new.phase != "GAME_OVER", "Bug: wall should NOT kill snake"
        assert new.snake[0] == Point(0, 5), "Snake should wrap around"

    def test_self_collision_ignored_bug(self):
        env = BuggySnakeEnv(BugType.SELF_COLLISION_IGNORED)
        snake = [Point(5, 5), Point(4, 5), Point(4, 4), Point(5, 4), Point(6, 4)]
        state = make_state(
            snake=snake,
            direction="RIGHT",
            next_direction="UP",
            food=Point(0, 0),
            grid_size=10
        )
        new = env.tick(state)
        assert new.phase != "GAME_OVER", "Bug: self collision should be ignored"

    def test_no_bug_baseline(self):
        env = BuggySnakeEnv(BugType.NONE)
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            next_direction="RIGHT",
            grid_size=10
        )
        new = env.tick(state)
        assert new.phase == "GAME_OVER", "No bug: wall collision should kill"
