"""Phase 1 tests: Pydantic models and SubgoalGenerationError."""
import pytest
from pydantic import ValidationError

import sys, os
# Clear any cached 'models' from Stage 1 (if tests run after test_prompt_builder)
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Subgoal, SubgoalSequence, SubgoalGenerationError


class TestSubgoal:
    def test_valid_instantiation(self):
        sg = Subgoal(index=1, description="Pick up an ingredient", rationale="Line 45 adds item pickup logic")
        assert sg.index == 1
        assert sg.anchor_hints == []

    def test_index_must_be_positive(self):
        with pytest.raises(ValidationError):
            Subgoal(index=0, description="step", rationale="r")

    def test_description_min_length(self):
        with pytest.raises(ValidationError):
            Subgoal(index=1, description="hi", rationale="r")

    def test_anchor_hints_default_empty(self):
        sg = Subgoal(index=1, description="Do something", rationale="r")
        assert sg.anchor_hints == []

    def test_anchor_hints_populated(self):
        sg = Subgoal(index=1, description="Do something", rationale="r",
                     anchor_hints=["45", "67/if_true"])
        assert len(sg.anchor_hints) == 2


class TestSubgoalSequence:
    def _make_seq(self):
        return SubgoalSequence(
            task_name="Pizza Quest",
            summary="Player assembles and delivers an onion pizza.",
            subgoals=[
                Subgoal(index=1, description="Obtain and chop a tomato", rationale="line 45"),
                Subgoal(index=2, description="Assemble the pizza base", rationale="line 52"),
            ]
        )

    def test_valid_instantiation(self):
        seq = self._make_seq()
        assert seq.task_name == "Pizza Quest"
        assert len(seq.subgoals) == 2

    def test_subgoals_min_length_one(self):
        with pytest.raises(ValidationError):
            SubgoalSequence(task_name="T", summary="A summary text here", subgoals=[])

    def test_summary_min_length(self):
        with pytest.raises(ValidationError):
            SubgoalSequence(task_name="T", summary="short", subgoals=[
                Subgoal(index=1, description="Do something", rationale="r")
            ])

    def test_to_dict_returns_dict(self):
        seq = self._make_seq()
        d = seq.to_dict()
        assert isinstance(d, dict)
        assert "subgoals" in d
        assert len(d["subgoals"]) == 2

    def test_to_dict_subgoal_keys(self):
        seq = self._make_seq()
        d = seq.to_dict()
        first = d["subgoals"][0]
        assert "index" in first
        assert "description" in first
        assert "anchor_hints" in first


class TestSubgoalGenerationError:
    def test_is_exception(self):
        err = SubgoalGenerationError("Something went wrong")
        assert isinstance(err, Exception)

    def test_message_accessible(self):
        err = SubgoalGenerationError("bad response", stop_reason="refusal")
        assert str(err) == "bad response"
        assert err.stop_reason == "refusal"

    def test_default_stop_reason_none(self):
        err = SubgoalGenerationError("oops")
        assert err.stop_reason is None

    def test_can_be_raised_and_caught(self):
        with pytest.raises(SubgoalGenerationError) as exc_info:
            raise SubgoalGenerationError("fail", stop_reason="refusal")
        assert exc_info.value.stop_reason == "refusal"
