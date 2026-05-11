from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class RewardGenerationError(Exception):
    """Raised when the LLM fails to produce a valid RewardRuleSet."""
    def __init__(self, message: str, stop_reason: Optional[str] = None):
        super().__init__(message)
        self.stop_reason = stop_reason


class ObservableVariable(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1, description="e.g. 'list[str]', 'int', \"'raw'|'baking'|'done'\"")
    description: str = Field(..., min_length=1)


class ObservationSchema(BaseModel):
    variables: list[ObservableVariable] = Field(..., min_length=1)


class RewardEvent(BaseModel):
    event: str = Field(..., min_length=1, description="Short event name, e.g. 'place_raw_pizza_in_oven'")
    condition: str = Field(..., min_length=1, description="Readable predicate using only ObservationSchema variables")
    reward: float = Field(..., description="Reward magnitude (positive)")
    description: str = Field(..., min_length=1, description="Human-readable explanation")


class RewardRule(BaseModel):
    subgoal_index: int = Field(..., ge=1, description="Matches Subgoal.index from Stage 2")
    subgoal_description: str = Field(..., min_length=5)
    events: list[RewardEvent] = Field(..., min_length=1)


class RewardRuleSet(BaseModel):
    task_name: str = Field(..., min_length=1)
    rules: list[RewardRule] = Field(..., min_length=1)

    def to_dict(self) -> dict:
        return self.model_dump()
