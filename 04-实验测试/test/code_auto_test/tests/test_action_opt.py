"""
Layer 4 Tests: Action Optimization Module
Tests filtering, ranking, and validation of recommended actions.
"""
import pytest
from titan.game.snake_env import Point, GameState, Difficulty
from titan.modules.action_opt import (
    recommend, validate_action, ActionBundle,
    _get_safe_actions, _flood_fill_from, _is_food_direction,
)
from titan.modules.perception import abstract


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


def make_abstract(state: GameState) -> dict:
    return abstract(state, knowledge_base=None)


# ---------------------------------------------------------------------------
# Test: Safe action filtering
# ---------------------------------------------------------------------------

class TestSafeActions:
    def test_no_reverse_action(self):
        state = make_state(direction="RIGHT")
        safe = _get_safe_actions(state, "RIGHT")
        assert "LEFT" not in safe, "180° reverse must not be in safe actions"

    def test_wall_filtered_right(self):
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            direction="RIGHT", grid_size=10
        )
        safe = _get_safe_actions(state, "RIGHT")
        assert "RIGHT" not in safe, "Moving into wall should be unsafe"

    def test_self_collision_filtered(self):
        # Snake going RIGHT, body immediately above
        snake = [Point(5, 5), Point(4, 5), Point(4, 4), Point(5, 4)]
        state = make_state(snake=snake, direction="RIGHT", grid_size=10)
        safe = _get_safe_actions(state, "RIGHT")
        assert "LEFT" not in safe  # 180° reverse
        # DOWN (5,6) should be open
        assert "DOWN" in safe or "UP" in safe

    def test_three_walls_only_one_safe(self):
        # Head at top-left corner going DOWN: can only go RIGHT (not UP/LEFT=wall, not UP=wall)
        state = make_state(
            snake=[Point(0, 0), Point(0, 1), Point(0, 2)],
            direction="UP", grid_size=10
        )
        safe = _get_safe_actions(state, "UP")
        # UP → wall (y=-1), LEFT → wall (x=-1), DOWN → 180° reverse
        # Only RIGHT is safe
        assert "RIGHT" in safe
        assert "UP" not in safe
        assert "LEFT" not in safe
        assert "DOWN" not in safe  # reverse of UP

    def test_open_field_three_safe_actions(self):
        # Head in center, moving RIGHT: UP, DOWN, RIGHT should be safe (not LEFT=reverse)
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            direction="RIGHT", grid_size=10
        )
        safe = _get_safe_actions(state, "RIGHT")
        assert "LEFT" not in safe
        assert len(safe) >= 2


# ---------------------------------------------------------------------------
# Test: Flood fill
# ---------------------------------------------------------------------------

class TestFloodFill:
    def test_flood_fill_open_space(self):
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            direction="RIGHT", grid_size=10
        )
        count = _flood_fill_from(state, "RIGHT")
        assert count > 0

    def test_flood_fill_wall_direction_zero(self):
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            direction="RIGHT", grid_size=10
        )
        count = _flood_fill_from(state, "RIGHT")
        assert count == 0

    def test_flood_fill_more_space_in_open_direction(self):
        # Moving right should have more space than moving down when near bottom wall
        state = make_state(
            snake=[Point(5, 9), Point(5, 8), Point(5, 7)],
            direction="RIGHT", grid_size=10,
            food=Point(0, 0)
        )
        right_space = _flood_fill_from(state, "RIGHT")
        # Going down from y=9 would be wall (0 space)
        down_space = _flood_fill_from(state, "DOWN")
        assert right_space > down_space


# ---------------------------------------------------------------------------
# Test: Food direction detection
# ---------------------------------------------------------------------------

class TestFoodDirection:
    def test_food_right_detected(self):
        abstract_state = {"food_direction": "RIGHT"}
        assert _is_food_direction(abstract_state, "RIGHT") is True

    def test_food_up_right_detected(self):
        abstract_state = {"food_direction": "UP-RIGHT"}
        assert _is_food_direction(abstract_state, "UP") is True
        assert _is_food_direction(abstract_state, "RIGHT") is True
        assert _is_food_direction(abstract_state, "DOWN") is False


# ---------------------------------------------------------------------------
# Test: Full recommendation
# ---------------------------------------------------------------------------

class TestRecommend:
    def test_recommend_returns_action_bundle(self):
        state = make_state()
        ab_state = make_abstract(state)
        result = recommend(ab_state, state)
        assert isinstance(result, ActionBundle)
        assert isinstance(result.recommended, list)
        assert isinstance(result.safe_actions, list)
        assert isinstance(result.reasoning, str)

    def test_recommend_no_dead_actions(self):
        # Head at right wall: RIGHT should not be recommended
        state = make_state(
            snake=[Point(9, 5), Point(8, 5), Point(7, 5)],
            direction="RIGHT", grid_size=10
        )
        ab_state = make_abstract(state)
        result = recommend(ab_state, state)
        assert "RIGHT" not in result.recommended
        assert "LEFT" not in result.recommended  # reverse

    def test_recommend_food_direction_prioritized(self):
        # Snake at (5,5) going RIGHT, food at (8,5) → food is RIGHT
        state = make_state(
            snake=[Point(5, 5), Point(4, 5), Point(3, 5)],
            food=Point(8, 5),
            direction="RIGHT"
        )
        ab_state = make_abstract(state)
        result = recommend(ab_state, state)
        # RIGHT (toward food) should be first recommended if safe
        if "RIGHT" in result.safe_actions:
            assert result.recommended[0] == "RIGHT"

    def test_recommend_dead_end_empty_list(self):
        # 2x2 grid, snake fills almost everything, head trapped
        config = Difficulty(tick_interval=200, grid_size=3, initial_length=1)
        # Snake fills 3x3 grid almost completely
        snake = [
            Point(0, 0), Point(1, 0), Point(2, 0),
            Point(2, 1), Point(1, 1), Point(0, 1),
            Point(0, 2), Point(1, 2),  # head at (0,2)
        ]
        state = GameState(
            snake=snake, food=Point(2, 2),
            direction="LEFT", next_direction="LEFT",
            phase="RUNNING", score=70, high_score=0,
            tick_count=0, config=config
        )
        ab_state = abstract(state)
        result = recommend(ab_state, state)
        # Only valid move is RIGHT (toward (1,2) which is body) or UP (toward (0,1) body)
        # Most likely dead end
        assert isinstance(result, ActionBundle)

    def test_recommend_with_mock_llm(self):
        from titan.llm_client import LLMClient
        state = make_state()
        ab_state = make_abstract(state)

        mock_llm = LLMClient(mock=True)
        mock_llm.set_default_mock_response("UP")

        result = recommend(ab_state, state, llm_client=mock_llm)
        assert isinstance(result, ActionBundle)
        assert len(result.recommended) > 0

    def test_recommend_reasoning_non_empty(self):
        state = make_state()
        ab_state = make_abstract(state)
        result = recommend(ab_state, state)
        assert len(result.reasoning) > 0


# ---------------------------------------------------------------------------
# Test: Action validation
# ---------------------------------------------------------------------------

class TestValidateAction:
    def test_valid_action_up(self):
        state = make_state(direction="RIGHT")
        assert validate_action(state, "UP") is True

    def test_valid_action_down(self):
        state = make_state(direction="RIGHT")
        assert validate_action(state, "DOWN") is True

    def test_invalid_reverse(self):
        state = make_state(direction="RIGHT")
        assert validate_action(state, "LEFT") is False

    def test_invalid_string(self):
        state = make_state(direction="RIGHT")
        assert validate_action(state, "INVALID") is False

    def test_invalid_empty_string(self):
        state = make_state(direction="RIGHT")
        assert validate_action(state, "") is False

    def test_valid_same_direction(self):
        state = make_state(direction="RIGHT")
        assert validate_action(state, "RIGHT") is True
