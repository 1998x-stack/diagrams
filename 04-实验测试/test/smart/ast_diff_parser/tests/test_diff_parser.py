"""Phase 5 tests: unified entry point."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from diff_parser import parse_diff, parse_diff_files
from models import DiffResult, ModifiedLine, ModifiedBranch

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")


class TestParseDiff:
    def test_returns_diff_result(self):
        result = parse_diff("", "def foo():\n    return 1\n")
        assert isinstance(result, DiffResult)

    def test_identical_code_no_changes(self):
        src = "def foo():\n    return 1\n"
        result = parse_diff(src, src)
        assert result.modified_lines == []
        assert result.modified_branches == []

    def test_new_function_detected(self):
        old = "def foo():\n    return 1\n"
        new = "def foo():\n    return 1\ndef bar():\n    return 2\n"
        result = parse_diff(old, new, "test.py")
        assert len(result.modified_lines) > 0
        assert result.file_path == "test.py"

    def test_new_branch_detected(self):
        old = ""
        new = "def f(x):\n    if x > 0:\n        return x\n    else:\n        return -x\n"
        result = parse_diff(old, new)
        assert len(result.modified_branches) > 0
        types = {b.branch_type for b in result.modified_branches}
        assert "if_true" in types
        assert "if_false" in types

    def test_file_path_propagates(self):
        result = parse_diff("", "def f():\n    pass\n", file_path="my/module.py")
        assert result.file_path == "my/module.py"
        for line in result.modified_lines:
            assert line.file_path == "my/module.py"

    def test_summary_is_consistent(self):
        old = ""
        new = "def f(x):\n    if x > 0:\n        return x\n    return 0\n"
        result = parse_diff(old, new)
        s = result.summary
        assert s["total_modified_lines"] == len(result.modified_lines)
        assert s["total_modified_branches"] == len(result.modified_branches)

    def test_empty_old_full_new(self):
        new = "class Foo:\n    def method(self):\n        return 42\n"
        result = parse_diff("", new)
        assert len(result.modified_lines) >= 2

    def test_to_dict_is_serializable(self):
        old = ""
        new = "def f():\n    for i in range(3):\n        print(i)\n"
        result = parse_diff(old, new)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "modified_lines" in d
        assert "modified_branches" in d


class TestParseDiffFiles:
    def test_returns_diff_result(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        assert isinstance(result, DiffResult)

    def test_has_modified_lines(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        assert len(result.modified_lines) > 0

    def test_has_modified_branches(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        assert len(result.modified_branches) > 0

    def test_file_path_is_basename(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        assert result.file_path == "math_calc_v2.py"

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            parse_diff_files("/no/such/file.py", V2_PATH)
