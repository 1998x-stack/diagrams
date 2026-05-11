"""
SMART Framework - Stage 1: AST Diff Parser
Public entry point — orchestrates the full pipeline.

Pipeline:
  build_ast (Phase 2)  →  diff_asts (Phase 3)  →  extract_anchors (Phase 4)
  → DiffResult (Phase 1)
"""
import os

from models import DiffResult
from parser.ast_builder import build_ast, build_ast_from_file
from parser.tree_differ import diff_asts
from parser.anchor_extractor import extract_anchors


def parse_diff(
    old_source: str,
    new_source: str,
    file_path: str = "unknown.py",
) -> DiffResult:
    """
    Compare two versions of Python source code and return all structural anchors.

    Args:
        old_source: Source code of the previous version.
        new_source: Source code of the updated version.
        file_path: Logical file path label used in all anchor records.

    Returns:
        DiffResult containing C_L (modified_lines) and C_B (modified_branches).
    """
    old_ast = build_ast(old_source, filename=file_path)
    new_ast = build_ast(new_source, filename=file_path)
    changed_nodes = diff_asts(old_ast, new_ast, file_path=file_path)
    modified_lines, modified_branches = extract_anchors(changed_nodes, new_source)
    return DiffResult(
        file_path=file_path,
        modified_lines=modified_lines,
        modified_branches=modified_branches,
    )


def parse_diff_files(old_path: str, new_path: str) -> DiffResult:
    """
    Compare two Python files on disk and return all structural anchors.

    Args:
        old_path: Path to the old version file.
        new_path: Path to the new version file.

    Returns:
        DiffResult with file_path set to the basename of new_path.
    """
    old_ast, _ = build_ast_from_file(old_path)
    new_ast, new_source = build_ast_from_file(new_path)
    file_path = os.path.basename(new_path)
    changed_nodes = diff_asts(old_ast, new_ast, file_path=file_path)
    modified_lines, modified_branches = extract_anchors(changed_nodes, new_source)
    return DiffResult(
        file_path=file_path,
        modified_lines=modified_lines,
        modified_branches=modified_branches,
    )
