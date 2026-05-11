"""
SMART Stage 1 - Phase 2: AST Builder
Builds Python ASTs from source strings or files.
"""
import ast
from pathlib import Path


def build_ast(source: str, filename: str = "<unknown>") -> ast.Module:
    """
    Parse Python source code into an AST.

    Args:
        source: Python source code as a string.
        filename: Optional filename for error messages.

    Returns:
        Parsed ast.Module node.

    Raises:
        SyntaxError: If the source is not valid Python.
    """
    return ast.parse(source, filename=filename, type_comments=False)


def read_source(file_path: str) -> str:
    """
    Read the contents of a Python source file.

    Args:
        file_path: Path to the .py file.

    Returns:
        File contents as a string (UTF-8).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return Path(file_path).read_text(encoding="utf-8")


def build_ast_from_file(file_path: str) -> tuple[ast.Module, str]:
    """
    Read a file and parse it into an AST.

    Args:
        file_path: Path to the .py file.

    Returns:
        Tuple of (ast.Module, source_string).
    """
    source = read_source(file_path)
    tree = build_ast(source, filename=file_path)
    return tree, source


def get_top_level_names(tree: ast.Module) -> list[str]:
    """
    Return the names of all top-level function and class definitions.

    Args:
        tree: Parsed ast.Module.

    Returns:
        List of definition names in order of appearance.
    """
    names = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
    return names
