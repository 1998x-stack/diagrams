"""Phase 4 tests: prompt builder and FilterResult schema."""
import os, sys

# Stage 4 only (no cross-stage identity needed for prompt builder)
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import CandidateSet
from prompt_builder import build_prompt, FilterResult

# Minimal duck-typed anchors for testing
class FakeLine:
    def __init__(self, line_number, source):
        self.line_number = line_number
        self.source = source

class FakeBranch:
    def __init__(self, control_stmt_line, branch_type, condition_source):
        self.control_stmt_line = control_stmt_line
        self.branch_type = branch_type
        self.condition_source = condition_source


def make_candidate_set(candidates=None):
    return CandidateSet(
        subgoal_index=2,
        subgoal_description="Perform a determinant calculation",
        subgoal_rationale="determinant method handles singular check",
        candidates=candidates or [],
    )


class TestBuildPrompt:
    def test_prompt_contains_subgoal_description(self):
        cs = make_candidate_set()
        prompt = build_prompt(cs)
        assert "Perform a determinant calculation" in prompt

    def test_prompt_contains_subgoal_index(self):
        cs = make_candidate_set()
        prompt = build_prompt(cs)
        assert "Index: 2" in prompt

    def test_prompt_contains_subgoal_rationale(self):
        cs = make_candidate_set()
        prompt = build_prompt(cs)
        assert "determinant method handles singular check" in prompt

    def test_line_anchor_appears_with_key(self):
        cs = make_candidate_set([FakeLine(51, "def determinant(self, matrix):")])
        prompt = build_prompt(cs)
        assert "[L:51]" in prompt
        assert "def determinant" in prompt

    def test_branch_anchor_appears_with_key(self):
        cs = make_candidate_set([FakeBranch(54, "if_true", "det == 0")])
        prompt = build_prompt(cs)
        assert "[B:54:if_true]" in prompt
        assert "det == 0" in prompt

    def test_anchor_type_shown_in_prompt(self):
        cs = make_candidate_set([FakeLine(10, "x = 1")])
        prompt = build_prompt(cs)
        assert "(line)" in prompt

    def test_empty_candidates_does_not_crash(self):
        cs = make_candidate_set([])
        prompt = build_prompt(cs)
        assert isinstance(prompt, str)
        assert "SUBGOAL" in prompt

    def test_multiple_anchors_all_present(self):
        cs = make_candidate_set([
            FakeLine(10, "x = 1"),
            FakeLine(20, "y = 2"),
            FakeBranch(30, "if_false", "x < 0"),
        ])
        prompt = build_prompt(cs)
        assert "[L:10]" in prompt
        assert "[L:20]" in prompt
        assert "[B:30:if_false]" in prompt


class TestFilterResult:
    def test_creates_valid_instance(self):
        fr = FilterResult(relevant_keys=["L:10", "B:20:if_true"], rationale="Both relevant")
        assert fr.relevant_keys == ["L:10", "B:20:if_true"]
        assert fr.rationale == "Both relevant"

    def test_empty_keys_valid(self):
        fr = FilterResult(relevant_keys=[], rationale="None relevant")
        assert fr.relevant_keys == []
