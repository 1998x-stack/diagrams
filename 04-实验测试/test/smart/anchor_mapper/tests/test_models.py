"""Phase 1 tests: data models for Stage 4 anchor mapper."""
import os, sys
import pytest
from pydantic import ValidationError

# Stage 4 models (only — no cross-stage identity needed for model unit tests)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import (
    AnchorMapping, StructuralAnchorMap, AnchorMappingError,
    FunctionInfo, CandidateSet,
)


class TestAnchorMapping:
    def test_creates_line_anchor(self):
        m = AnchorMapping(
            anchor_key="L:42",
            anchor_type="line",
            line_number=42,
            source_snippet="return x + 1",
            subgoal_indices=[1],
        )
        assert m.anchor_key == "L:42"
        assert m.anchor_type == "line"
        assert m.branch_type is None

    def test_creates_branch_anchor(self):
        m = AnchorMapping(
            anchor_key="B:20:if_true",
            anchor_type="branch",
            line_number=20,
            branch_type="if_true",
            source_snippet="if x > 0:",
            subgoal_indices=[1, 2],
        )
        assert m.branch_type == "if_true"
        assert m.subgoal_indices == [1, 2]

    def test_invalid_anchor_type_raises(self):
        with pytest.raises(ValidationError):
            AnchorMapping(
                anchor_key="X:10",
                anchor_type="unknown",
                line_number=10,
                source_snippet="x",
                subgoal_indices=[1],
            )

    def test_empty_subgoal_indices_raises(self):
        with pytest.raises(ValidationError):
            AnchorMapping(
                anchor_key="L:10",
                anchor_type="line",
                line_number=10,
                source_snippet="x",
                subgoal_indices=[],
            )


class TestStructuralAnchorMap:
    def _make_map(self):
        return StructuralAnchorMap(
            task_name="Test Task",
            file_path="test.py",
            mappings=[
                AnchorMapping(
                    anchor_key="L:10", anchor_type="line", line_number=10,
                    source_snippet="foo()", subgoal_indices=[1],
                ),
                AnchorMapping(
                    anchor_key="L:20", anchor_type="line", line_number=20,
                    source_snippet="bar()", subgoal_indices=[1, 2],
                ),
                AnchorMapping(
                    anchor_key="B:30:if_true", anchor_type="branch", line_number=30,
                    branch_type="if_true", source_snippet="if x:", subgoal_indices=[2],
                ),
            ],
        )

    def test_for_subgoal_returns_correct_subset(self):
        m = self._make_map()
        result = m.for_subgoal(1)
        assert len(result) == 2
        keys = {r.anchor_key for r in result}
        assert keys == {"L:10", "L:20"}

    def test_for_subgoal_returns_empty_for_no_match(self):
        m = self._make_map()
        assert m.for_subgoal(99) == []

    def test_to_dict_returns_serializable_dict(self):
        m = self._make_map()
        d = m.to_dict()
        assert isinstance(d, dict)
        assert d["task_name"] == "Test Task"
        assert len(d["mappings"]) == 3

    def test_empty_mappings_is_valid(self):
        m = StructuralAnchorMap(task_name="T", file_path="f.py", mappings=[])
        assert m.mappings == []
        assert m.to_dict()["mappings"] == []


class TestAnchorMappingError:
    def test_default_stop_reason_is_none(self):
        err = AnchorMappingError("fail")
        assert err.stop_reason is None
        assert str(err) == "fail"

    def test_stop_reason_stored(self):
        err = AnchorMappingError("refused", stop_reason="refusal")
        assert err.stop_reason == "refusal"

    def test_is_exception(self):
        with pytest.raises(AnchorMappingError):
            raise AnchorMappingError("boom")


class TestFunctionInfo:
    def test_creates_with_defaults(self):
        fi = FunctionInfo(name="foo", start_line=1, end_line=5)
        assert fi.name == "foo"
        assert fi.calls == []

    def test_creates_with_calls(self):
        fi = FunctionInfo(name="foo", start_line=1, end_line=5, calls=["bar", "baz"])
        assert fi.calls == ["bar", "baz"]


class TestCandidateSet:
    def test_creates_correctly(self):
        cs = CandidateSet(
            subgoal_index=1,
            subgoal_description="Do the thing",
            subgoal_rationale="line 10",
            candidates=[],
        )
        assert cs.subgoal_index == 1
        assert cs.candidates == []
