"""Phase 2 tests: AST builder."""
import ast
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parser.ast_builder import build_ast, read_source, build_ast_from_file, get_top_level_names

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")


class TestBuildAst:
    def test_returns_module_node(self):
        tree = build_ast("x = 1")
        assert isinstance(tree, ast.Module)

    def test_simple_function(self):
        src = "def foo(x):\n    return x + 1\n"
        tree = build_ast(src)
        funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        assert len(funcs) == 1
        assert funcs[0].name == "foo"

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError):
            build_ast("def broken(:\n    pass")

    def test_empty_source(self):
        tree = build_ast("")
        assert isinstance(tree, ast.Module)
        assert tree.body == []


class TestReadSource:
    def test_reads_v1(self):
        src = read_source(V1_PATH)
        assert "class Trigonometry" in src
        assert "def derivative" in src

    def test_reads_v2(self):
        src = read_source(V2_PATH)
        assert "class MatrixCalculator" in src
        assert "class ComplexNumber" in src

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_source("/nonexistent/path/file.py")


class TestBuildAstFromFile:
    def test_v1_returns_module_and_source(self):
        tree, src = build_ast_from_file(V1_PATH)
        assert isinstance(tree, ast.Module)
        assert isinstance(src, str)
        assert len(src) > 0

    def test_v2_returns_module_and_source(self):
        tree, src = build_ast_from_file(V2_PATH)
        assert isinstance(tree, ast.Module)
        assert "MatrixCalculator" in src


class TestGetTopLevelNames:
    def test_v1_names(self):
        tree, _ = build_ast_from_file(V1_PATH)
        names = get_top_level_names(tree)
        assert "Trigonometry" in names
        assert "derivative" in names
        assert "integrate" in names

    def test_v2_has_new_names(self):
        tree, _ = build_ast_from_file(V2_PATH)
        names = get_top_level_names(tree)
        assert "MatrixCalculator" in names
        assert "ComplexNumber" in names
        assert "taylor_series" in names

    def test_v2_has_all_v1_names(self):
        tree_v1, _ = build_ast_from_file(V1_PATH)
        tree_v2, _ = build_ast_from_file(V2_PATH)
        v1_names = set(get_top_level_names(tree_v1))
        v2_names = set(get_top_level_names(tree_v2))
        assert v1_names.issubset(v2_names)

    def test_empty_module(self):
        tree = build_ast("")
        assert get_top_level_names(tree) == []
