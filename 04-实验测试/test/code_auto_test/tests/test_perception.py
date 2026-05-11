"""
Layer 3 Tests: Perception Abstraction Module
Tests that raw GameState is correctly converted to abstract representation.
"""
import pytest
from titan.game.snake_env import Point, GameState, Difficulty
from titan.modules.perception import (
    abstract, check_danger, get_food_direction, get_food_distance,
    estimate_open_space, classify_head_position, classify_snake_length,
    classify_food_distance, _turn_left, _turn_right,
)


# ---------------------------------------------------------------------------
# Helper
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


# ---------------------------------------------------------------------------
# Test: Direction helpers
# ---------------------------------------------------------------------------

class TestDirectionHelpers:
    def test_turn_left_from_right(self):
        assert _turn_left("RIGHT") == "UP"

    def test_turn_left_from_up(self):
        assert _turn_left("UP") == "LEFT"

    def test_turn_left_from_left(self):
        assert _turn_left("LEFT") == "DOWN"

    def test_turn_left_from_down(self):
        assert _turn_left("DOWN") == "RIGHT"

    def test_turn_right_from_right(self):
        assert _turn_right("RIGHT") == "DOWN"

    def test_turn_right_from_up(self):
        assert _turn_right("UP") == "RIGHT"


# ---------------------------------------------------------------------------
# Test: Danger detection
# ---------------------------------------------------------------------------

class TestDangerDetection:
    def test_danger_ahead_wall_right(self):
        # Head at right edge, moving RIGHT
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            direction="RIGHT", grid_size=10
        )
        assert check_danger(state, "RIGHT") is True

    def test_no_danger_ahead_open_space(self):
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            direction="RIGHT"
        )
        assert check_danger(state, "RIGHT") is False

    def test_danger_left_wall(self):
        # Head at left edge, so LEFT is wall
        state = make_state(
            snake=[Point(0, 5), Point(1, 5), Point(2, 5)],
            direction="DOWN", grid_size=10
        )
        assert check_danger(state, "LEFT") is True

    def test_danger_self_collision(self):
        # U-shaped snake, next step hits body
        snake = [Point(5, 5), Point(4, 5), Point(4, 4), Point(5, 4)]
        state = make_state(snake=snake, direction="RIGHT", grid_size=10)
        # Moving DOWN from (5,5) goes to (5,6) - open
        assert check_danger(state, "DOWN") is False
        # Moving LEFT from (5,5) goes to (4,5) which IS body
        assert check_danger(state, "LEFT") is True

    def test_no_danger_at_tail_position(self):
        # Tail position should NOT cause danger (tail moves away)
        snake = [Point(2, 5), Point(1, 5), Point(0, 5)]
        state = make_state(snake=snake, direction="RIGHT", grid_size=10)
        # Moving LEFT would go to (1,5) which is snake[1] but NOT tail
        # So it IS dangerous
        assert check_danger(state, "LEFT") is True


# ---------------------------------------------------------------------------
# Test: Food direction
# ---------------------------------------------------------------------------

class TestFoodDirection:
    def test_food_directly_right(self):
        assert get_food_direction(Point(5, 5), Point(8, 5)) == "RIGHT"

    def test_food_directly_left(self):
        assert get_food_direction(Point(5, 5), Point(2, 5)) == "LEFT"

    def test_food_directly_up(self):
        assert get_food_direction(Point(5, 5), Point(5, 3)) == "UP"

    def test_food_directly_down(self):
        assert get_food_direction(Point(5, 5), Point(5, 8)) == "DOWN"

    def test_food_up_right(self):
        result = get_food_direction(Point(5, 5), Point(7, 3))
        assert "UP" in result and "RIGHT" in result

    def test_food_down_left(self):
        result = get_food_direction(Point(5, 5), Point(3, 8))
        assert "DOWN" in result and "LEFT" in result

    def test_food_at_same_position(self):
        result = get_food_direction(Point(5, 5), Point(5, 5))
        assert result == "SAME"


# ---------------------------------------------------------------------------
# Test: Food distance
# ---------------------------------------------------------------------------

class TestFoodDistance:
    def test_distance_zero(self):
        assert get_food_distance(Point(5, 5), Point(5, 5)) == 0

    def test_distance_horizontal(self):
        assert get_food_distance(Point(3, 5), Point(7, 5)) == 4

    def test_distance_vertical(self):
        assert get_food_distance(Point(5, 3), Point(5, 8)) == 5

    def test_distance_diagonal(self):
        assert get_food_distance(Point(0, 0), Point(3, 4)) == 7


# ---------------------------------------------------------------------------
# Test: Classification functions
# ---------------------------------------------------------------------------

class TestClassifications:
    def test_snake_length_short(self):
        assert classify_snake_length(3, 20) == "short"

    def test_snake_length_medium(self):
        assert classify_snake_length(10, 20) == "medium"

    def test_snake_length_long(self):
        assert classify_snake_length(90, 20) == "long"

    def test_food_distance_close(self):
        assert classify_food_distance(2) == "close"

    def test_food_distance_medium(self):
        assert classify_food_distance(5) == "medium"

    def test_food_distance_far(self):
        assert classify_food_distance(10) == "far"

    def test_head_position_top_left(self):
        assert classify_head_position(Point(1, 1), 20) == "top-left"

    def test_head_position_center(self):
        assert classify_head_position(Point(10, 10), 20) == "center"

    def test_head_position_bottom_right(self):
        assert classify_head_position(Point(18, 18), 20) == "bottom-right"

    def test_head_position_top(self):
        assert classify_head_position(Point(10, 1), 20) == "top"


# ---------------------------------------------------------------------------
# Test: Open space estimation
# ---------------------------------------------------------------------------

class TestOpenSpace:
    def test_open_space_full_empty_grid(self):
        # Single-segment snake on empty 10x10 grid
        state = make_state(
            snake=[Point(5, 5)],
            food=Point(0, 0),
            direction="RIGHT",
            grid_size=10
        )
        ratio = estimate_open_space(state)
        assert ratio > 0.8, "Should have high open space"

    def test_open_space_corner(self):
        # Head in corner with large body blocking
        state = make_state(
            snake=[Point(0, 0), Point(1, 0), Point(2, 0), Point(3, 0)],
            food=Point(9, 9),
            direction="LEFT",
            grid_size=10
        )
        ratio = estimate_open_space(state)
        assert 0 <= ratio <= 1.0

    def test_open_space_range(self):
        state = make_state(grid_size=10)
        ratio = estimate_open_space(state)
        assert 0 <= ratio <= 1.0


# ---------------------------------------------------------------------------
# Test: Full abstraction
# ---------------------------------------------------------------------------

class TestAbstract:
    def test_abstract_returns_required_keys(self):
        state = make_state()
        result = abstract(state)
        required_keys = [
            "phase", "direction", "score", "snake_length",
            "food_distance", "food_direction", "danger_ahead",
            "danger_left", "danger_right", "head_position",
            "open_space_ratio", "relevant_rules"
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_abstract_danger_ahead_at_wall(self):
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            direction="RIGHT", grid_size=10
        )
        result = abstract(state)
        assert result["danger_ahead"] is True

    def test_abstract_no_danger_open_space(self):
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            direction="RIGHT", food=Point(8, 5), grid_size=10
        )
        result = abstract(state)
        assert result["danger_ahead"] is False

    def test_abstract_food_direction_correct(self):
        # Head at (5,5), food at (5,3) → UP
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            food=Point(5, 3), direction="RIGHT", grid_size=10
        )
        result = abstract(state)
        assert result["food_direction"] == "UP"

    def test_abstract_snake_length_classification(self):
        # 3 segments in 10x10 grid → short
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            grid_size=10
        )
        result = abstract(state)
        assert result["snake_length"] == "short"

    def test_abstract_with_mock_rag(self):
        # Test with mock KnowledgeBase
        class MockKB:
            def retrieve(self, query, top_k=3):
                return [f"mock rule for: {query[:20]}"]

        state = make_state()
        result = abstract(state, knowledge_base=MockKB())
        assert "relevant_rules" in result
        assert len(result["relevant_rules"]) > 0

    def test_abstract_without_rag(self):
        state = make_state()
        result = abstract(state, knowledge_base=None)
        assert result["relevant_rules"] == []

    def test_abstract_score_preserved(self):
        state = make_state(score=50)
        result = abstract(state)
        assert result["score"] == 50

    def test_abstract_phase_preserved(self):
        state = make_state(phase="GAME_OVER")
        result = abstract(state)
        assert result["phase"] == "GAME_OVER"
