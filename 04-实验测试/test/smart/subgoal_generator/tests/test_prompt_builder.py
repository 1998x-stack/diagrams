"""Phase 3 tests: DiffResult → prompt string."""
import os, sys
import pytest

# Stage 1 imports (prompt_builder only uses Stage 1 types, no Stage 2 models)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
# Clear any previously cached 'models' to ensure we get Stage 1 models
if "models" in sys.modules:
    del sys.modules["models"]
from models import DiffResult, ModifiedLine, ModifiedBranch
from diff_parser import parse_diff_files

# Stage 2 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from prompt_builder import build_prompt

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser", "tests", "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")


def make_diff_result(n_lines=3, n_branches=2) -> DiffResult:
    lines = [
        ModifiedLine("f.py", i + 1, "added", f"    x_{i} = {i}")
        for i in range(n_lines)
    ]
    branches = [
        ModifiedBranch("f.py", 10 + i, "if_true", f"x > {i}")
        for i in range(n_branches)
    ]
    return DiffResult("f.py", lines, branches)


class TestBuildPromptStructure:
    def test_returns_string(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert isinstance(prompt, str)

    def test_contains_file_path(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "f.py" in prompt

    def test_contains_cl_section(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "C_L" in prompt or "Modified Lines" in prompt

    def test_contains_cb_section(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "C_B" in prompt or "Modified Branches" in prompt

    def test_contains_line_numbers(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "1" in prompt  # first line number

    def test_contains_branch_type(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "if_true" in prompt

    def test_contains_condition_source(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "x > 0" in prompt

    def test_contains_rules(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        # Rules section must instruct the LLM
        assert "anchor_hints" in prompt

    def test_mentions_subgoal_sequence(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "SubgoalSequence" in prompt


class TestBuildPromptTruncation:
    def test_no_truncation_under_limit(self):
        result = make_diff_result(n_lines=5)
        prompt = build_prompt(result, max_lines=10)
        assert "omitted" not in prompt

    def test_truncation_message_appears(self):
        result = make_diff_result(n_lines=20)
        prompt = build_prompt(result, max_lines=5)
        assert "more" in prompt.lower() and "omitted" in prompt.lower()

    def test_truncated_shows_correct_count(self):
        result = make_diff_result(n_lines=20)
        prompt = build_prompt(result, max_lines=5)
        assert "15" in prompt  # 20 - 5 = 15 omitted

    def test_branches_never_truncated(self):
        """C_B always shown in full regardless of max_lines."""
        branches = [ModifiedBranch("f.py", i + 1, "loop_body", "") for i in range(30)]
        result = DiffResult("f.py", [], branches)
        prompt = build_prompt(result, max_lines=5)
        # All 30 branch lines present
        assert prompt.count("loop_body") == 30

    def test_empty_diff_still_builds_prompt(self):
        result = DiffResult("empty.py", [], [])
        prompt = build_prompt(result)
        assert isinstance(prompt, str)
        assert len(prompt) > 50


class TestBuildPromptWithFixtures:
    def test_math_calc_prompt_contains_matrix(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        prompt = build_prompt(result)
        assert "MatrixCalculator" in prompt or "determinant" in prompt or "inverse" in prompt

    def test_math_calc_prompt_contains_branches(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        prompt = build_prompt(result)
        assert "if_true" in prompt or "if_false" in prompt or "loop_body" in prompt
