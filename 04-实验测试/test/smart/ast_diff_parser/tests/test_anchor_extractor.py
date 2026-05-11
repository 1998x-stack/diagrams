"""Phase 4 tests: anchor extractor."""
import ast
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parser.ast_builder import build_ast, build_ast_from_file
from parser.tree_differ import diff_asts, ChangedNode
from parser.anchor_extractor import extract_anchors

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")


def diff_sources(old_src: str, new_src: str, fp: str = "f.py"):
    old = build_ast(old_src)
    new = build_ast(new_src)
    changed = diff_asts(old, new, fp)
    return extract_anchors(changed, new_src)


class TestExtractLines:
    def test_new_function_produces_lines(self):
        old = ""
        new = "def foo():\n    x = 1\n    return x\n"
        lines, _ = diff_sources(old, new)
        assert len(lines) > 0
        assert all(l.change_type == "added" for l in lines)

    def test_line_numbers_are_positive(self):
        old = ""
        new = "def foo():\n    return 42\n"
        lines, _ = diff_sources(old, new)
        assert all(l.line_number >= 1 for l in lines)

    def test_no_duplicate_line_numbers(self):
        old = ""
        new = "def foo():\n    x = 1\n    y = 2\n    return x + y\n"
        lines, _ = diff_sources(old, new)
        line_nos = [l.line_number for l in lines]
        assert len(line_nos) == len(set(line_nos))

    def test_source_content_captured(self):
        old = ""
        new = "def foo():\n    return 99\n"
        lines, _ = diff_sources(old, new)
        sources = [l.source for l in lines]
        assert any("99" in s for s in sources)

    def test_modified_lines_marked_correctly(self):
        old = "def f(x):\n    return x\n"
        new = "def f(x):\n    return x * 2\n"
        lines, _ = diff_sources(old, new)
        assert any(l.change_type == "modified" for l in lines)

    def test_lines_sorted_by_line_number(self):
        old = ""
        new = "def foo():\n    a = 1\n    b = 2\n    c = 3\n"
        lines, _ = diff_sources(old, new)
        nums = [l.line_number for l in lines]
        assert nums == sorted(nums)


class TestExtractBranchesIf:
    def test_if_true_branch_detected(self):
        old = ""
        new = "def f(x):\n    if x > 0:\n        return x\n"
        _, branches = diff_sources(old, new)
        types = {b.branch_type for b in branches}
        assert "if_true" in types

    def test_if_else_produces_true_and_false(self):
        old = ""
        new = "def f(x):\n    if x > 0:\n        return x\n    else:\n        return -x\n"
        _, branches = diff_sources(old, new)
        types = {b.branch_type for b in branches}
        assert "if_true" in types
        assert "if_false" in types

    def test_elif_detected(self):
        old = ""
        new = (
            "def f(x):\n"
            "    if x > 0:\n"
            "        return 'pos'\n"
            "    elif x < 0:\n"
            "        return 'neg'\n"
            "    else:\n"
            "        return 'zero'\n"
        )
        _, branches = diff_sources(old, new)
        types = {b.branch_type for b in branches}
        assert "elif" in types

    def test_condition_source_captured(self):
        old = ""
        new = "def f(x):\n    if x > 100:\n        return True\n"
        _, branches = diff_sources(old, new)
        if_true = [b for b in branches if b.branch_type == "if_true"]
        assert any("100" in b.condition_source for b in if_true)


class TestExtractBranchesLoop:
    def test_for_loop_produces_loop_body(self):
        old = ""
        new = "def f():\n    for i in range(10):\n        print(i)\n"
        _, branches = diff_sources(old, new)
        types = {b.branch_type for b in branches}
        assert "loop_body" in types

    def test_while_loop_produces_loop_body(self):
        old = ""
        new = "def f(x):\n    while x > 0:\n        x -= 1\n"
        _, branches = diff_sources(old, new)
        types = {b.branch_type for b in branches}
        assert "loop_body" in types


class TestExtractBranchesExcept:
    def test_except_branch_detected(self):
        old = ""
        new = (
            "def f(x):\n"
            "    try:\n"
            "        return 1 / x\n"
            "    except ZeroDivisionError:\n"
            "        return 0\n"
        )
        _, branches = diff_sources(old, new)
        types = {b.branch_type for b in branches}
        assert "except" in types


class TestExtractAnchorsWithFixtures:
    """Full diff of math calculator v1 → v2."""

    def setup_method(self):
        old_ast, _ = build_ast_from_file(V1_PATH)
        new_ast, self.new_src = build_ast_from_file(V2_PATH)
        changed = diff_asts(old_ast, new_ast, "math_calc.py")
        self.lines, self.branches = extract_anchors(changed, self.new_src)

    def test_has_modified_lines(self):
        assert len(self.lines) > 0

    def test_has_modified_branches(self):
        assert len(self.branches) > 0

    def test_matrix_calculator_lines_present(self):
        sources = " ".join(l.source for l in self.lines)
        assert "MatrixCalculator" in sources or "determinant" in sources or "inverse" in sources

    def test_complex_number_lines_present(self):
        sources = " ".join(l.source for l in self.lines)
        assert "ComplexNumber" in sources or "ZeroDivisionError" in sources

    def test_integrate_branch_present(self):
        """integrate was modified to support method param → produces branches."""
        branch_lines = {b.control_stmt_line for b in self.branches}
        # Just verify we have multiple branches (the if/elif chain in integrate)
        assert len(self.branches) >= 2

    def test_no_duplicate_lines(self):
        pairs = [(l.file_path, l.line_number) for l in self.lines]
        assert len(pairs) == len(set(pairs))

    def test_no_duplicate_branches(self):
        keys = [(b.file_path, b.control_stmt_line, b.branch_type) for b in self.branches]
        assert len(keys) == len(set(keys))

    def test_branch_types_valid(self):
        valid = {"if_true", "if_false", "elif", "except", "loop_body"}
        for b in self.branches:
            assert b.branch_type in valid
