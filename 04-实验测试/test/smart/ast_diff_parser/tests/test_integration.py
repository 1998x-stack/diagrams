"""
Phase 6: Integration tests — full pipeline with math calculator fixtures.

Validates the complete SMART Stage 1 output for the v1 → v2 update:
  - New components: MatrixCalculator, ComplexNumber, taylor_series
  - Modified: integrate (multi-method), derivative (central difference)
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from diff_parser import parse_diff_files
from models import DiffResult

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")


@pytest.fixture(scope="module")
def result() -> DiffResult:
    return parse_diff_files(V1_PATH, V2_PATH)


# ── C_L: Modified Lines ──────────────────────────────────────────────────────

class TestModifiedLines:
    def test_c_l_is_nonempty(self, result):
        assert len(result.modified_lines) > 0

    def test_contains_matrix_calculator_code(self, result):
        sources = " ".join(l.source for l in result.modified_lines)
        # MatrixCalculator class or its methods
        assert any(kw in sources for kw in ["MatrixCalculator", "determinant", "inverse", "multiply"])

    def test_contains_complex_number_code(self, result):
        sources = " ".join(l.source for l in result.modified_lines)
        assert any(kw in sources for kw in ["ComplexNumber", "ZeroDivisionError", "modulus", "argument"])

    def test_contains_taylor_series_code(self, result):
        sources = " ".join(l.source for l in result.modified_lines)
        assert "taylor_series" in sources or "Taylor" in sources or "factorial" in sources

    def test_contains_modified_integrate_code(self, result):
        """integrate was changed to support method param."""
        sources = " ".join(l.source for l in result.modified_lines)
        assert any(kw in sources for kw in ["simpson", "trapezoidal", "method"])

    def test_contains_modified_derivative_code(self, result):
        """derivative was changed to support order param."""
        sources = " ".join(l.source for l in result.modified_lines)
        assert any(kw in sources for kw in ["order", "central", "2 * h"])

    def test_no_trigonometry_code_in_c_l(self, result):
        """Trigonometry class is unchanged — must not appear in C_L."""
        sources = " ".join(l.source for l in result.modified_lines)
        # The class definition itself must not be a changed line
        trig_class_lines = [l for l in result.modified_lines
                            if "class Trigonometry" in l.source]
        assert len(trig_class_lines) == 0

    def test_added_lines_greater_than_modified(self, result):
        """Most changes are additions (new classes), not modifications."""
        added = sum(1 for l in result.modified_lines if l.change_type == "added")
        modified = sum(1 for l in result.modified_lines if l.change_type == "modified")
        assert added > modified

    def test_all_line_numbers_valid(self, result):
        for l in result.modified_lines:
            assert l.line_number >= 1

    def test_no_duplicate_line_entries(self, result):
        pairs = [(l.file_path, l.line_number) for l in result.modified_lines]
        assert len(pairs) == len(set(pairs))

    def test_lines_cover_substantial_portion_of_v2(self, result):
        """At least 50 modified lines expected given the scale of new code."""
        assert len(result.modified_lines) >= 50


# ── C_B: Modified Branches ──────────────────────────────────────────────────

class TestModifiedBranches:
    def test_c_b_is_nonempty(self, result):
        assert len(result.modified_branches) > 0

    def test_has_if_true_branches(self, result):
        types = {b.branch_type for b in result.modified_branches}
        assert "if_true" in types

    def test_has_if_false_or_elif_branches(self, result):
        types = {b.branch_type for b in result.modified_branches}
        assert "if_false" in types or "elif" in types

    def test_has_loop_body_branches(self, result):
        """MatrixCalculator uses nested for-loops."""
        types = {b.branch_type for b in result.modified_branches}
        assert "loop_body" in types

    def test_singular_matrix_branch_present(self, result):
        """inverse() checks for singular matrix → if_true / if_false."""
        conditions = " ".join(b.condition_source for b in result.modified_branches)
        assert any(kw in conditions for kw in ["det", "singular", "pivot", "1e-10"])

    def test_zero_division_branch_present(self, result):
        """ComplexNumber.__truediv__ checks denom == 0."""
        conditions = " ".join(b.condition_source for b in result.modified_branches)
        assert any(kw in conditions for kw in ["denom", "1e-15", "imag", "real"])

    def test_integrate_method_branches(self, result):
        """integrate has if/elif/else for method selection."""
        conditions = " ".join(b.condition_source for b in result.modified_branches)
        assert any(kw in conditions for kw in ["method", "simpson", "midpoint", "trapezoidal"])

    def test_no_duplicate_branch_entries(self, result):
        keys = [(b.file_path, b.control_stmt_line, b.branch_type)
                for b in result.modified_branches]
        assert len(keys) == len(set(keys))

    def test_all_branch_types_valid(self, result):
        valid = {"if_true", "if_false", "elif", "except", "loop_body"}
        for b in result.modified_branches:
            assert b.branch_type in valid, f"Invalid branch type: {b.branch_type}"

    def test_at_least_five_branches(self, result):
        """v2 introduces many control-flow paths."""
        assert len(result.modified_branches) >= 5


# ── Summary & Serialization ──────────────────────────────────────────────────

class TestSummaryAndOutput:
    def test_summary_matches_actual_counts(self, result):
        s = result.summary
        assert s["total_modified_lines"] == len(result.modified_lines)
        assert s["total_modified_branches"] == len(result.modified_branches)
        assert s["added_lines"] + s["modified_lines"] == s["total_modified_lines"]

    def test_to_dict_round_trip(self, result):
        d = result.to_dict()
        assert isinstance(d, dict)
        assert len(d["modified_lines"]) == len(result.modified_lines)
        assert len(d["modified_branches"]) == len(result.modified_branches)

    def test_printable_report(self, result, capsys):
        """Verify the result can be printed as a human-readable report."""
        s = result.summary
        print(f"\n{'='*60}")
        print(f"SMART Stage 1 — AST Diff Report")
        print(f"File: {result.file_path}")
        print(f"{'='*60}")
        print(f"C_L (Modified Lines): {s['total_modified_lines']}")
        print(f"  Added   : {s['added_lines']}")
        print(f"  Modified: {s['modified_lines']}")
        print(f"C_B (Modified Branches): {s['total_modified_branches']}")
        for bt, count in s["branch_types"].items():
            if count:
                print(f"  {bt:<12}: {count}")
        print(f"{'='*60}")
        captured = capsys.readouterr()
        assert "C_L" in captured.out
        assert "C_B" in captured.out

    def test_file_path_label(self, result):
        assert result.file_path == "math_calc_v2.py"
