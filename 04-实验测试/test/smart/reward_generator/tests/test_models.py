"""Phase 1 tests: Pydantic models and RewardGenerationError."""
import pytest
from pydantic import ValidationError

import sys, os
# Clear any cached 'models' from other stages
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import (
    RewardGenerationError,
    ObservableVariable,
    ObservationSchema,
    RewardEvent,
    RewardRule,
    RewardRuleSet,
)


class TestRewardGenerationError:
    def test_is_exception(self):
        err = RewardGenerationError("Something went wrong")
        assert isinstance(err, Exception)

    def test_message_accessible(self):
        err = RewardGenerationError("bad response", stop_reason="refusal")
        assert str(err) == "bad response"
        assert err.stop_reason == "refusal"

    def test_default_stop_reason_none(self):
        err = RewardGenerationError("oops")
        assert err.stop_reason is None

    def test_can_be_raised_and_caught(self):
        with pytest.raises(RewardGenerationError) as exc_info:
            raise RewardGenerationError("fail", stop_reason="refusal")
        assert exc_info.value.stop_reason == "refusal"


class TestObservableVariable:
    def test_valid_instantiation(self):
        v = ObservableVariable(name="oven_state", type="'raw'|'baking'|'done'", description="Oven status")
        assert v.name == "oven_state"

    def test_name_min_length(self):
        with pytest.raises(ValidationError):
            ObservableVariable(name="", type="int", description="d")

    def test_type_min_length(self):
        with pytest.raises(ValidationError):
            ObservableVariable(name="x", type="", description="d")

    def test_description_min_length(self):
        with pytest.raises(ValidationError):
            ObservableVariable(name="x", type="int", description="")


class TestObservationSchema:
    def test_valid_instantiation(self):
        schema = ObservationSchema(variables=[
            ObservableVariable(name="score", type="int", description="Current score")
        ])
        assert len(schema.variables) == 1

    def test_variables_min_length(self):
        with pytest.raises(ValidationError):
            ObservationSchema(variables=[])


class TestRewardEvent:
    def test_valid_instantiation(self):
        ev = RewardEvent(
            event="place_pizza",
            condition="inventory contains 'pizza'",
            reward=1.0,
            description="Player placed pizza in oven",
        )
        assert ev.reward == 1.0

    def test_event_min_length(self):
        with pytest.raises(ValidationError):
            RewardEvent(event="", condition="c", reward=1.0, description="d")

    def test_condition_min_length(self):
        with pytest.raises(ValidationError):
            RewardEvent(event="e", condition="", reward=1.0, description="d")

    def test_description_min_length(self):
        with pytest.raises(ValidationError):
            RewardEvent(event="e", condition="c", reward=1.0, description="")


class TestRewardRule:
    def _make_rule(self):
        return RewardRule(
            subgoal_index=1,
            subgoal_description="Pick up an ingredient",
            events=[
                RewardEvent(event="grab_item", condition="player near item", reward=5.0,
                            description="Player grabbed item")
            ],
        )

    def test_valid_instantiation(self):
        rule = self._make_rule()
        assert rule.subgoal_index == 1

    def test_subgoal_index_ge_1(self):
        with pytest.raises(ValidationError):
            RewardRule(
                subgoal_index=0,
                subgoal_description="x" * 5,
                events=[RewardEvent(event="e", condition="c", reward=1.0, description="d")],
            )

    def test_subgoal_description_min_length(self):
        with pytest.raises(ValidationError):
            RewardRule(
                subgoal_index=1,
                subgoal_description="hi",
                events=[RewardEvent(event="e", condition="c", reward=1.0, description="d")],
            )

    def test_events_min_length(self):
        with pytest.raises(ValidationError):
            RewardRule(subgoal_index=1, subgoal_description="Do something", events=[])


class TestRewardRuleSet:
    def _make_ruleset(self):
        return RewardRuleSet(
            task_name="Pizza Quest",
            rules=[
                RewardRule(
                    subgoal_index=1,
                    subgoal_description="Pick up ingredient",
                    events=[RewardEvent(event="grab", condition="near item", reward=5.0, description="grabbed")],
                )
            ],
        )

    def test_valid_instantiation(self):
        rs = self._make_ruleset()
        assert rs.task_name == "Pizza Quest"
        assert len(rs.rules) == 1

    def test_task_name_min_length(self):
        with pytest.raises(ValidationError):
            RewardRuleSet(task_name="", rules=[
                RewardRule(
                    subgoal_index=1,
                    subgoal_description="Do something",
                    events=[RewardEvent(event="e", condition="c", reward=1.0, description="d")],
                )
            ])

    def test_rules_min_length(self):
        with pytest.raises(ValidationError):
            RewardRuleSet(task_name="T", rules=[])

    def test_to_dict_returns_dict(self):
        rs = self._make_ruleset()
        d = rs.to_dict()
        assert isinstance(d, dict)
        assert "rules" in d
        assert len(d["rules"]) == 1

    def test_to_dict_contains_events(self):
        rs = self._make_ruleset()
        d = rs.to_dict()
        assert "events" in d["rules"][0]
