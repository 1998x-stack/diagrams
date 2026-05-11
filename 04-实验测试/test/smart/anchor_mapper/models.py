"""
SMART Framework - Stage 4: Structural Anchor Mapper
Data models: AnchorMapping, StructuralAnchorMap, AnchorMappingError, FunctionInfo, CandidateSet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AnchorMappingError(Exception):
    """Raised when anchor mapping fails (LLM refusal or parse error)."""

    def __init__(self, message: str, stop_reason: Optional[str] = None):
        super().__init__(message)
        self.stop_reason = stop_reason


class AnchorMapping(BaseModel):
    """Maps one structural anchor to the subgoals where it is relevant."""

    anchor_key: str = Field(..., description='"L:42" for line 42, "B:20:if_true" for branch')
    anchor_type: Literal["line", "branch"]
    line_number: int = Field(..., description="Line number (or control_stmt_line for branches)")
    branch_type: Optional[str] = Field(None, description="None for lines; branch_type string for branches")
    source_snippet: str = Field(..., description="Code fragment from Stage 1")
    subgoal_indices: list[int] = Field(..., min_length=1)


class StructuralAnchorMap(BaseModel):
    """Full mapping output: each anchor → set of relevant subgoal indices."""

    task_name: str
    file_path: str
    mappings: list[AnchorMapping] = Field(default_factory=list)

    def for_subgoal(self, index: int) -> list[AnchorMapping]:
        """Return all anchors mapped to the given subgoal index."""
        return [m for m in self.mappings if index in m.subgoal_indices]

    def to_dict(self) -> dict:
        return self.model_dump()


@dataclass
class FunctionInfo:
    """AST-derived metadata for one function or method."""

    name: str           # "taylor_series" or "MatrixCalculator.determinant"
    start_line: int
    end_line: int
    calls: list[str] = field(default_factory=list)   # names called in the body


@dataclass
class CandidateSet:
    """Phase 1 output: candidate anchors for one subgoal, before LLM filtering."""

    subgoal_index: int
    subgoal_description: str
    subgoal_rationale: str
    candidates: list   # list[ModifiedLine | ModifiedBranch] — untyped to avoid cross-stage import
