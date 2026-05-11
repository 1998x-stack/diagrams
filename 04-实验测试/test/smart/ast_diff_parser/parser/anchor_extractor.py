"""
SMART Stage 1 - Phase 4: Anchor Extractor
Converts ChangedNode list → (C_L, C_B) structural anchor sets.

C_L rules:
  - Every ChangedNode with a lineno produces one ModifiedLine per source line
    it spans (lineno … end_lineno inclusive).

C_B rules:
  - ast.If      → if_true branch (always) + if_false / elif branch (if orelse exists)
  - ast.For / ast.While → loop_body branch
  - ast.ExceptHandler   → except branch
  Only control-flow nodes that are themselves ChangedNodes trigger C_B entries.
"""
import ast
from typing import Sequence

from models import ModifiedLine, ModifiedBranch
from parser.tree_differ import ChangedNode


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _source_line(source_lines: list[str], lineno: int) -> str:
    """Return the source text of a 1-based line number (stripped)."""
    idx = lineno - 1
    if 0 <= idx < len(source_lines):
        return source_lines[idx].rstrip()
    return ""


def _extract_lines_from_node(
    node: ast.AST,
    change_type: str,
    file_path: str,
    source_lines: list[str],
) -> list[ModifiedLine]:
    """
    Produce ModifiedLine entries for every source line spanned by *node*.
    For multi-line nodes we emit one entry per line.
    """
    lines: list[ModifiedLine] = []
    if not hasattr(node, "lineno"):
        return lines

    start = node.lineno
    end = getattr(node, "end_lineno", start)

    for lineno in range(start, end + 1):
        src = _source_line(source_lines, lineno)
        if not src.strip():
            continue  # skip blank lines inside a node span
        lines.append(
            ModifiedLine(
                file_path=file_path,
                line_number=lineno,
                change_type=change_type,
                source=src,
            )
        )
    return lines


def _condition_src(node: ast.expr, source_lines: list[str]) -> str:
    """Best-effort: return the source text for a condition expression."""
    try:
        return ast.unparse(node)
    except Exception:
        if hasattr(node, "lineno"):
            return _source_line(source_lines, node.lineno)
        return ""


def _extract_branches_from_node(
    node: ast.AST,
    file_path: str,
    source_lines: list[str],
) -> list[ModifiedBranch]:
    """
    Produce ModifiedBranch entries for a control-flow node.
    Only ast.If / ast.For / ast.While / ast.ExceptHandler are handled.
    """
    branches: list[ModifiedBranch] = []
    stmt_line = getattr(node, "lineno", 0)

    if isinstance(node, ast.If):
        cond = _condition_src(node.test, source_lines)
        # True branch always exists
        branches.append(ModifiedBranch(file_path, stmt_line, "if_true", cond))
        # False / elif branch
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # elif
                elif_cond = _condition_src(node.orelse[0].test, source_lines)
                branches.append(ModifiedBranch(file_path, stmt_line, "elif", elif_cond))
            else:
                branches.append(ModifiedBranch(file_path, stmt_line, "if_false", cond))

    elif isinstance(node, (ast.For, ast.While)):
        branches.append(ModifiedBranch(file_path, stmt_line, "loop_body", ""))

    elif isinstance(node, ast.ExceptHandler):
        exc_type = ""
        if node.type is not None:
            exc_type = _condition_src(node.type, source_lines)
        branches.append(ModifiedBranch(file_path, stmt_line, "except", exc_type))

    return branches


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_anchors(
    changed_nodes: Sequence[ChangedNode],
    source: str,
) -> tuple[list[ModifiedLine], list[ModifiedBranch]]:
    """
    Convert a list of ChangedNodes into structural anchor sets (C_L, C_B).

    Args:
        changed_nodes: Output of tree_differ.diff_asts().
        source: Full source text of the *new* file (used to read line content).

    Returns:
        (modified_lines, modified_branches) — C_L and C_B.
    """
    source_lines = source.splitlines()
    seen_lines: set[tuple[str, int]] = set()   # (file_path, line_number)
    seen_branches: set[tuple[str, int, str]] = set()  # (file_path, line, branch_type)

    all_lines: list[ModifiedLine] = []
    all_branches: list[ModifiedBranch] = []

    for cn in changed_nodes:
        # --- C_L ---
        for ml in _extract_lines_from_node(cn.node, cn.change_type, cn.file_path, source_lines):
            key = (ml.file_path, ml.line_number)
            if key not in seen_lines:
                seen_lines.add(key)
                all_lines.append(ml)

        # --- C_B ---
        for mb in _extract_branches_from_node(cn.node, cn.file_path, source_lines):
            key = (mb.file_path, mb.control_stmt_line, mb.branch_type)
            if key not in seen_branches:
                seen_branches.add(key)
                all_branches.append(mb)

    # Sort for deterministic output
    all_lines.sort(key=lambda l: l.line_number)
    all_branches.sort(key=lambda b: (b.control_stmt_line, b.branch_type))

    return all_lines, all_branches
