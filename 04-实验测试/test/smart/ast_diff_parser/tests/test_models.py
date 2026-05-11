"""Phase 1 tests: data models."""
import pytest
from models import ModifiedLine, ModifiedBranch, DiffResult


class TestModifiedLine:
    def test_instantiation(self):
        line = ModifiedLine(
            file_path="calc.py",
            line_number=42,
            change_type="added",
            source="    return x * 2",
        )
        assert line.file_path == "calc.py"
        assert line.line_number == 42
        assert line.change_type == "added"
        assert line.source == "    return x * 2"

    def test_to_dict(self):
        line = ModifiedLine("f.py", 10, "modified", "x = 1")
        d = line.to_dict()
        assert d == {
            "file_path": "f.py",
            "line_number": 10,
            "change_type": "modified",
            "source": "x = 1",
        }

    def test_change_type_values(self):
        for ct in ("added", "modified"):
            line = ModifiedLine("f.py", 1, ct, "")
            assert line.change_type == ct


class TestModifiedBranch:
    def test_instantiation(self):
        branch = ModifiedBranch(
            file_path="calc.py",
            control_stmt_line=15,
            branch_type="if_true",
            condition_source="det == 0",
        )
        assert branch.branch_type == "if_true"
        assert branch.condition_source == "det == 0"

    def test_to_dict(self):
        branch = ModifiedBranch("f.py", 5, "if_false", "x > 0")
        d = branch.to_dict()
        assert d["branch_type"] == "if_false"
        assert d["control_stmt_line"] == 5

    def test_all_branch_types(self):
        for bt in ("if_true", "if_false", "elif", "except", "loop_body"):
            b = ModifiedBranch("f.py", 1, bt, "")
            assert b.branch_type == bt


class TestDiffResult:
    def _make_result(self):
        lines = [
            ModifiedLine("f.py", 1, "added", "x = 1"),
            ModifiedLine("f.py", 2, "added", "y = 2"),
            ModifiedLine("f.py", 3, "modified", "z = x + y"),
        ]
        branches = [
            ModifiedBranch("f.py", 10, "if_true", "x > 0"),
            ModifiedBranch("f.py", 10, "if_false", "x > 0"),
            ModifiedBranch("f.py", 20, "loop_body", ""),
        ]
        return DiffResult(file_path="f.py", modified_lines=lines, modified_branches=branches)

    def test_summary_counts(self):
        result = self._make_result()
        s = result.summary
        assert s["total_modified_lines"] == 3
        assert s["added_lines"] == 2
        assert s["modified_lines"] == 1
        assert s["total_modified_branches"] == 3

    def test_summary_branch_types(self):
        result = self._make_result()
        bt = result.summary["branch_types"]
        assert bt["if_true"] == 1
        assert bt["if_false"] == 1
        assert bt["loop_body"] == 1
        assert bt["elif"] == 0
        assert bt["except"] == 0

    def test_empty_result(self):
        result = DiffResult(file_path="empty.py")
        s = result.summary
        assert s["total_modified_lines"] == 0
        assert s["total_modified_branches"] == 0

    def test_to_dict_structure(self):
        result = self._make_result()
        d = result.to_dict()
        assert "modified_lines" in d
        assert "modified_branches" in d
        assert "summary" in d
        assert isinstance(d["modified_lines"], list)
        assert d["modified_lines"][0]["change_type"] == "added"

    def test_default_empty_lists(self):
        result = DiffResult("x.py")
        assert result.modified_lines == []
        assert result.modified_branches == []
