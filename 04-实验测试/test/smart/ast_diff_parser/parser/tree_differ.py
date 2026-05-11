"""
SMART Stage 1 - Phase 3: Tree Differ
Compares two AST modules and identifies changed nodes.

Strategy:
  1. Extract top-level definitions (functions / classes) from both ASTs by name.
  2. Definitions only in new → all descendant statement nodes marked "added".
  3. Definitions in both but changed → walk subtrees in parallel; nodes whose
     canonical dump differs are marked "modified".
  4. Definitions unchanged → skipped entirely.
"""
import ast
from dataclasses import dataclass
from typing import Literal


@dataclass
class ChangedNode:
    """A single AST node that was added or modified in the new version."""
    node: ast.AST
    change_type: Literal["added", "modified"]
    file_path: str


def _get_top_level_defs(tree: ast.Module) -> dict[str, ast.AST]:
    """Return {name: node} for every top-level FunctionDef / ClassDef."""
    defs = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs[node.name] = node
    return defs


def _collect_statement_nodes(node: ast.AST) -> list[ast.AST]:
    """
    Collect all statement-level nodes (those with a lineno) within a subtree.
    Excludes the root node itself so callers can decide how to classify it.
    """
    result = []
    for child in ast.walk(node):
        if child is not node and hasattr(child, "lineno"):
            result.append(child)
    return result


def _find_changed_nodes(
    old_node: ast.AST,
    new_node: ast.AST,
    file_path: str,
    results: list[ChangedNode],
) -> None:
    """
    Recursively compare two subtrees and collect nodes that differ.

    Comparison is done at the statement level: for each pair of corresponding
    child nodes, if their canonical dumps differ, the new node (and all its
    descendants not present in old) is marked "modified".
    """
    old_children = list(ast.iter_child_nodes(old_node))
    new_children = list(ast.iter_child_nodes(new_node))

    # Pair up children positionally up to the shorter list
    paired = zip(old_children, new_children)
    paired_count = min(len(old_children), len(new_children))

    for old_child, new_child in paired:
        if ast.dump(old_child) == ast.dump(new_child):
            continue  # identical sub-tree → skip
        # The child differs; if it has a line number, mark it
        if hasattr(new_child, "lineno"):
            results.append(ChangedNode(new_child, "modified", file_path))
        else:
            # Non-statement node differs → recurse into it
            _find_changed_nodes(old_child, new_child, file_path, results)

    # Extra children in new (appended code) → mark as added
    for new_child in new_children[paired_count:]:
        if hasattr(new_child, "lineno"):
            results.append(ChangedNode(new_child, "added", file_path))
        else:
            for desc in _collect_statement_nodes(new_child):
                results.append(ChangedNode(desc, "added", file_path))


def diff_asts(
    old_ast: ast.Module,
    new_ast: ast.Module,
    file_path: str = "unknown.py",
) -> list[ChangedNode]:
    """
    Compare two AST modules and return all changed nodes.

    Args:
        old_ast: AST of the previous version.
        new_ast: AST of the updated version.
        file_path: Label used in ChangedNode records.

    Returns:
        List of ChangedNode, one per modified or added statement-level node.
    """
    old_defs = _get_top_level_defs(old_ast)
    new_defs = _get_top_level_defs(new_ast)

    results: list[ChangedNode] = []

    for name, new_node in new_defs.items():
        if name not in old_defs:
            # Entire definition is new → mark root + all descendants as added
            results.append(ChangedNode(new_node, "added", file_path))
            for desc in _collect_statement_nodes(new_node):
                results.append(ChangedNode(desc, "added", file_path))
        else:
            old_node = old_defs[name]
            if ast.dump(old_node) == ast.dump(new_node):
                continue  # completely unchanged
            # Definition changed → diff subtrees
            _find_changed_nodes(old_node, new_node, file_path, results)

    return results
