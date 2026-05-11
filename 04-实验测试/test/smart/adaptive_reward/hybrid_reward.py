"""
SMART Framework - Stage 5: Adaptive Hybrid Reward Function

Implements Algorithm 1 from the SMART paper with the context-aware extension:
structural reward is gated to anchors relevant to the current subgoal j.

sys.modules collision guard: this module loads its own models.py via importlib.util
under the stable key "_adaptive_reward_stage5_models", following Stage 4's pattern.
This prevents class identity issues when pytest collects all five stages together.
"""
from __future__ import annotations

import importlib.util as _ilu
import os as _os
import sys as _sys

from condition_evaluator import evaluate_condition

# ---------------------------------------------------------------------------
# Stage 5 sys.modules collision guard
# ---------------------------------------------------------------------------
# Five stages each have a models.py. This block fires once at import time and
# loads Stage 5's models.py under a stable pinned key, guaranteeing that the
# StepResult/CoverageStats class objects are always the same ones, regardless
# of import ordering across the five stages during pytest collection.
_S5_MODELS_KEY = "_adaptive_reward_stage5_models"
_S5_MODELS_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "models.py")

if _S5_MODELS_KEY not in _sys.modules:
    _spec = _ilu.spec_from_file_location(_S5_MODELS_KEY, _S5_MODELS_PATH)
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules[_S5_MODELS_KEY] = _mod   # register BEFORE exec so dataclasses can resolve __module__
    _spec.loader.exec_module(_mod)

_STAGE5_MODELS = _sys.modules[_S5_MODELS_KEY]
StepResult = _STAGE5_MODELS.StepResult
CoverageStats = _STAGE5_MODELS.CoverageStats


# ---------------------------------------------------------------------------
# HybridRewardFunction
# ---------------------------------------------------------------------------

class HybridRewardFunction:
    """
    Stateful hybrid reward calculator implementing Algorithm 1 from the SMART paper.

    Integrates Stage 3 reward rules and Stage 4 anchor maps. Duck-typed inputs —
    no direct imports from Stage 3 or Stage 4 models to avoid sys.modules collisions.

    Dual-layer state:
      - _j (int): episode-level subgoal pointer; reset() sets it back to 1
      - _C_cov (set[str]): global anchor coverage; never cleared by reset()

    Usage:
        rf = HybridRewardFunction(reward_rule_set, anchor_map, r_sem=30, r_str=5)
        rf.reset()  # call at the start of each episode
        for step in episode:
            state_dict, covered_anchors = env.step(action)
            result = rf.compute_reward(state_dict, covered_anchors)
            total_reward = result.total_reward
    """

    def __init__(
        self,
        reward_rule_set,           # Stage 3 RewardRuleSet (duck-typed)
        anchor_map,                # Stage 4 StructuralAnchorMap (duck-typed)
        r_sem: float = 30.0,
        r_str: float = 5.0,
        terminal_reward: float = 200.0,
    ) -> None:
        # Sort rules by subgoal_index
        self._rules = sorted(reward_rule_set.rules, key=lambda r: r.subgoal_index)
        self._total_subgoals = len(self._rules)

        # Validate contiguous 1-based indices: must be exactly [1, 2, ..., n]
        actual = [r.subgoal_index for r in self._rules]
        expected = list(range(1, self._total_subgoals + 1))
        if actual != expected:
            raise ValueError(
                f"subgoal_index values must be contiguous starting at 1, got {actual}"
            )

        # Build anchor-to-subgoals lookup: anchor_key → set[subgoal_index]
        # Shape: dict[str, set[int]] — look up by anchor_key to get relevant subgoal indices.
        # Iterates mapping.subgoal_indices (plural) and merges mappings sharing the same key.
        self._anchor_index: dict[str, set[int]] = {}
        for mapping in anchor_map.mappings:
            for idx in mapping.subgoal_indices:
                self._anchor_index.setdefault(mapping.anchor_key, set()).add(idx)

        self._r_sem = r_sem
        self._r_str = r_str
        self._terminal_reward = terminal_reward

        self._C_cov: set[str] = set()   # global anchor coverage — never reset
        self._j: int = 1               # episode-level subgoal pointer

    def reset(self) -> None:
        """Reset episode-level state. _C_cov is NOT cleared."""
        self._j = 1

    def compute_reward(self, state_dict: dict, covered_anchors: set[str]) -> StepResult:
        """
        Compute r_t = r_sem + r_str for one environment timestep.

        Args:
            state_dict: game state as {variable_name: value}, matching Stage 3 schema.
            covered_anchors: set of anchor_key strings triggered this step
                             (e.g. {"L:42", "B:20:if_true"}).

        Returns:
            StepResult with breakdown of semantic/structural rewards.

        Post-terminal behavior: if called after is_terminal=True without reset(),
        returns an all-zero StepResult with is_terminal=False. Semantic reward is
        skipped by the `_j <= _total_subgoals` guard. Structural reward is zeroed
        because j_at_start exceeds all anchor subgoal indices (context filter blocks
        all anchors). Call reset() before starting a new episode.
        """
        # Capture j before any modification — used for structural scoping in Step 2
        j_at_start = self._j

        # Step 1: Semantic reward
        r_sem_step = 0.0
        subgoal_advanced = False
        is_terminal = False

        if self._j <= self._total_subgoals:
            rule = self._rules[self._j - 1]
            if any(evaluate_condition(event.condition, state_dict) for event in rule.events):
                r_sem_step = self._r_sem
                subgoal_advanced = True
                self._j += 1
                if self._j > self._total_subgoals:
                    r_sem_step += self._terminal_reward
                    is_terminal = True

        # Step 2: Structural reward (context-aware extension per paper prose, uses j_at_start)
        # This extends the base Algorithm 1 pseudocode with subgoal scoping:
        # only anchors MAPPED to the current subgoal (j_at_start) are eligible for reward.
        # Anchors for future/past subgoals or unknown keys are silently skipped.
        # This prevents the agent from earning structural credit for code it cannot
        # meaningfully reach at the current gameplay stage, and prevents pre-terminal
        # anchors from polluting C_cov before their subgoal becomes reachable.
        #
        # Post-terminal: j_at_start will be > _total_subgoals, so no anchor's subgoal
        # set can contain j_at_start. The context filter incidentally zeroes structural
        # reward post-terminal without a separate guard — this is intentional.
        r_str_step = 0.0
        new_anchors_covered: set[str] = set()

        for anchor_key in covered_anchors:
            if (
                anchor_key in self._anchor_index
                and j_at_start in self._anchor_index[anchor_key]
                and anchor_key not in self._C_cov
            ):
                r_str_step += self._r_str
                self._C_cov.add(anchor_key)
                new_anchors_covered.add(anchor_key)

        return StepResult(
            total_reward=r_sem_step + r_str_step,
            semantic_reward=r_sem_step,
            structural_reward=r_str_step,
            subgoal_advanced=subgoal_advanced,
            new_anchors_covered=new_anchors_covered,
            is_terminal=is_terminal,
        )

    @property
    def coverage_rate(self) -> float:
        """Fraction of unique anchors covered. 0.0 if anchor_map has no anchors."""
        total = len(self._anchor_index)
        return len(self._C_cov) / total if total > 0 else 0.0

    @property
    def subgoal_progress(self) -> tuple[int, int]:
        """(current_j, total_n). After terminal, current_j == total_n + 1 exactly."""
        return (self._j, self._total_subgoals)

    def get_coverage_stats(self) -> CoverageStats:
        """
        Return a CoverageStats snapshot.

        total_anchors = len(_anchor_index) — unique anchor keys after dedup.
        Using len(anchor_map.mappings) would overcount if anchor_keys repeat,
        causing coverage_rate > 1.0.
        """
        total = len(self._anchor_index)
        covered = len(self._C_cov)
        return CoverageStats(
            total_anchors=total,
            covered_count=covered,
            coverage_rate=(covered / total) if total > 0 else 0.0,
        )
