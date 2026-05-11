"""
SMART Framework - Stage 1: AST Diff Parser
Data models for structural anchors C_L and C_B.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ModifiedLine:
    """
    A single modified or added line of code (element of C_L).

    Attributes:
        file_path: Source file path (relative or absolute).
        line_number: 1-based line number in the new version.
        change_type: "added" for new lines, "modified" for changed existing lines.
        source: The actual source code of that line (stripped).
    """
    file_path: str
    line_number: int
    change_type: Literal["added", "modified"]
    source: str

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "change_type": self.change_type,
            "source": self.source,
        }


@dataclass
class ModifiedBranch:
    """
    A new or altered logical branch in a control-flow statement (element of C_B).

    Attributes:
        file_path: Source file path.
        control_stmt_line: 1-based line number of the control statement (if/for/while/try).
        branch_type: Which branch this represents.
        condition_source: The condition expression as source text (empty string for loop/except bodies).
    """
    file_path: str
    control_stmt_line: int
    branch_type: Literal["if_true", "if_false", "elif", "except", "loop_body"]
    condition_source: str

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "control_stmt_line": self.control_stmt_line,
            "branch_type": self.branch_type,
            "condition_source": self.condition_source,
        }


@dataclass
class DiffResult:
    """
    Complete output of Stage 1: all structural anchors identified from a diff.

    Attributes:
        file_path: The file that was diffed.
        modified_lines: C_L — set of modified/added lines.
        modified_branches: C_B — set of new/altered control-flow branches.
    """
    file_path: str
    modified_lines: list[ModifiedLine] = field(default_factory=list)
    modified_branches: list[ModifiedBranch] = field(default_factory=list)

    @property
    def summary(self) -> dict:
        added = sum(1 for l in self.modified_lines if l.change_type == "added")
        modified = sum(1 for l in self.modified_lines if l.change_type == "modified")
        return {
            "file_path": self.file_path,
            "total_modified_lines": len(self.modified_lines),
            "added_lines": added,
            "modified_lines": modified,
            "total_modified_branches": len(self.modified_branches),
            "branch_types": {
                bt: sum(1 for b in self.modified_branches if b.branch_type == bt)
                for bt in ("if_true", "if_false", "elif", "except", "loop_body")
            },
        }

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "modified_lines": [l.to_dict() for l in self.modified_lines],
            "modified_branches": [b.to_dict() for b in self.modified_branches],
            "summary": self.summary,
        }
