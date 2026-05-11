"""
SMART Framework - Stage 2: Subgoal Generator
Prompt Builder: converts DiffResult into a structured LLM prompt.
"""
from __future__ import annotations

import sys
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ast_diff_parser"))
    from models import DiffResult


_SYSTEM_INSTRUCTIONS = """\
You are a game testing engineer analyzing a Python code update.
Given the AST diff report below, decompose the changes into an ordered
sequence of verifiable gameplay subgoals.

Rules:
1. Each subgoal must describe one atomic, testable player action or game state change.
2. Subgoals must be ordered by logical dependency (earlier steps enable later ones).
3. Every subgoal must reference at least one entry in C_L or C_B via anchor_hints.
   Format anchor_hints as: '<line_number>' for C_L entries,
   '<line_number>/<branch_type>' for C_B entries.
   Example: anchor_hints=["45", "67/if_true", "67/if_false"]
4. Descriptions must be natural language, not code.

Respond with a valid SubgoalSequence JSON object.\
"""


def build_prompt(diff_result: DiffResult, max_lines: int = 150) -> str:
    """
    Convert a DiffResult into a structured LLM prompt.

    Args:
        diff_result: Output from Stage 1 ast_diff_parser.
        max_lines: Maximum C_L entries shown. Excess lines are summarised.
                   C_B (branches) are never truncated.

    Returns:
        Complete prompt string ready for the Claude API.
    """
    lines = list(diff_result.modified_lines)
    branches = list(diff_result.modified_branches)

    # ── C_L section ──────────────────────────────────────────────────────────
    total_lines = len(lines)
    shown_lines = lines[:max_lines]
    omitted = total_lines - len(shown_lines)

    cl_header = (
        f"--- Modified Lines (C_L): {total_lines} entries"
        + (f" (showing first {max_lines})" if omitted > 0 else "")
        + " ---"
    )
    cl_rows = "\n".join(
        f"{ml.line_number:>6} | {ml.change_type:<8} | {ml.source}"
        for ml in shown_lines
    )
    if omitted > 0:
        cl_rows += f"\n... and {omitted} more lines (omitted to fit context window)"

    # ── C_B section ──────────────────────────────────────────────────────────
    cb_header = f"--- Modified Branches (C_B): {len(branches)} entries ---"
    cb_rows = "\n".join(
        f"{mb.control_stmt_line:>6} | {mb.branch_type:<12} | {mb.condition_source}"
        for mb in branches
    ) or "  (none)"

    # ── Assemble ──────────────────────────────────────────────────────────────
    report = (
        f"=== AST DIFF REPORT ===\n"
        f"File: {diff_result.file_path}\n\n"
        f"{cl_header}\n{cl_rows}\n\n"
        f"{cb_header}\n{cb_rows}\n"
        f"=== END REPORT ==="
    )

    return f"{_SYSTEM_INSTRUCTIONS}\n\n{report}"
