"""
SMART Framework - Stage 2: Subgoal Generator
Data models: SubgoalGenerationError, Subgoal, SubgoalSequence.
"""
from typing import Optional
from pydantic import BaseModel, Field


class SubgoalGenerationError(Exception):
    """Raised when the LLM fails to produce a valid SubgoalSequence."""

    def __init__(self, message: str, stop_reason: Optional[str] = None):
        super().__init__(message)
        self.stop_reason = stop_reason


class Subgoal(BaseModel):
    """One atomic, verifiable gameplay testing step."""

    index: int = Field(..., ge=1, description="1-based ordering index")
    description: str = Field(..., min_length=5, description="Natural-language verifiable step")
    rationale: str = Field(..., description="Which C_L/C_B entries motivate this step")
    anchor_hints: list[str] = Field(
        default_factory=list,
        description=(
            "References to structural anchors from Stage 1. "
            "Format: '<line_number>' for C_L or '<line_number>/<branch_type>' for C_B. "
            "Example: ['45', '67/if_true', '67/if_false']"
        ),
    )


class SubgoalSequence(BaseModel):
    """Ordered sequence of subgoals produced by Stage 2."""

    task_name: str = Field(..., min_length=1, description="Inferred name of the game update task")
    summary: str = Field(..., min_length=10, description="One-sentence description of the overall update")
    subgoals: list[Subgoal] = Field(..., min_length=1, description="Ordered subgoal list")

    def to_dict(self) -> dict:
        """Serialize to a plain dict (for Stage 3 handoff or persistence)."""
        return self.model_dump()
