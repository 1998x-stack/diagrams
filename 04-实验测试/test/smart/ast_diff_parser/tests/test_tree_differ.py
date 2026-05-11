"""Phase 3 tests: tree differ."""
import ast
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parser.ast_builder import build_ast, build_ast_from_file
from parser.tree_differ import diff_asts, ChangedNode, _get_top_level_defs

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")


def make_ast(src: str) -> ast.Module:
    return build_ast(src)


class TestGetTopLevelDefs:
    def test_identifies_functions_and_classes(self):
        src = "class Foo:\n    pass\ndef bar():\n    pass\n"
        tree = make_ast(src)
        defs = _get_top_level_defs(tree)
        assert "Foo" in defs
        assert "bar" in defs

    def test_empty_module(self):
        defs = _get_top_level_defs(make_ast(""))
        assert defs == {}


class TestDiffAstsNewDefinition:
    """New top-level definitions should produce 'added' nodes."""

    def test_new_function_produces_added_nodes(self):
        old = make_ast("def foo():\n    return 1\n")
        new = make_ast("def foo():\n    return 1\ndef bar():\n    return 2\n")
        nodes = diff_asts(old, new, "f.py")
        types = {n.change_type for n in nodes}
        assert "added" in types
        names = [getattr(n.node, "name", None) for n in nodes]
        assert "bar" in names

    def test_new_class_produces_added_nodes(self):
        old = make_ast("")
        new = make_ast("class Calc:\n    def method(self):\n        return 42\n")
        nodes = diff_asts(old, new, "f.py")
        assert any(n.change_type == "added" for n in nodes)

    def test_added_nodes_reference_correct_file(self):
        old = make_ast("")
        new = make_ast("def new_fn():\n    x = 1\n    return x\n")
        nodes = diff_asts(old, new, "myfile.py")
        assert all(n.file_path == "myfile.py" for n in nodes)


class TestDiffAstsModifiedDefinition:
    """Changed top-level definitions should produce 'modified' nodes."""

    def test_modified_return_value(self):
        old = make_ast("def foo():\n    return 1\n")
        new = make_ast("def foo():\n    return 99\n")
        nodes = diff_asts(old, new, "f.py")
        assert len(nodes) > 0
        assert any(n.change_type == "modified" for n in nodes)

    def test_unchanged_function_not_in_results(self):
        src = "def foo():\n    return 1\n"
        old = make_ast(src)
        new = make_ast(src)
        nodes = diff_asts(old, new, "f.py")
        assert len(nodes) == 0

    def test_new_parameter_detected(self):
        old = make_ast("def f(x):\n    return x\n")
        new = make_ast("def f(x, y=0):\n    return x + y\n")
        nodes = diff_asts(old, new, "f.py")
        assert len(nodes) > 0


class TestDiffAstsWithFixtures:
    """Diff the actual v1 → v2 math calculator fixtures."""

    def setup_method(self):
        self.old_ast, _ = build_ast_from_file(V1_PATH)
        self.new_ast, _ = build_ast_from_file(V2_PATH)
        self.nodes = diff_asts(self.old_ast, self.new_ast, "math_calc.py")

    def test_has_changed_nodes(self):
        assert len(self.nodes) > 0

    def test_new_classes_present(self):
        """MatrixCalculator and ComplexNumber are new → some node named as such."""
        node_names = {getattr(n.node, "name", "") for n in self.nodes}
        assert "MatrixCalculator" in node_names or any(
            "MatrixCalculator" in ast.dump(n.node) for n in self.nodes
        )

    def test_trigonometry_unchanged(self):
        """Trigonometry class is identical in v1 and v2 → must not appear."""
        for n in self.nodes:
            assert getattr(n.node, "name", "") != "Trigonometry"

    def test_added_and_modified_both_present(self):
        change_types = {n.change_type for n in self.nodes}
        assert "added" in change_types
        assert "modified" in change_types

    def test_all_nodes_have_file_path(self):
        assert all(n.file_path == "math_calc.py" for n in self.nodes)
