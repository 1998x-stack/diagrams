from __future__ import annotations
from dataclasses import dataclass


@dataclass
class StepResult:
    """Result of one compute_reward() call."""
    total_reward: float
    semantic_reward: float       # r_sem if subgoal advanced this step, else 0.0
    structural_reward: float     # r_str × number of newly covered anchors
    subgoal_advanced: bool       # True if _j incremented this step
    new_anchors_covered: set[str]
    is_terminal: bool            # True when all subgoals complete


@dataclass
class CoverageStats:
    """Snapshot of anchor coverage at a point in time."""
    total_anchors: int           # len(_anchor_index) — unique anchor keys
    covered_count: int           # number of anchors in C_cov
    coverage_rate: float         # covered_count / total_anchors; 0.0 if total == 0
                                 # NOTE: plain field — get_coverage_stats() computes and passes it
