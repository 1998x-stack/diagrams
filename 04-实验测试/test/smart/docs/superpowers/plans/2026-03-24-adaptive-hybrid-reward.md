# Stage 5: Adaptive Hybrid Reward Function — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a stateful `HybridRewardFunction` class that computes `r_t = r_sem + r_str` per RL timestep, integrating Stage 3 reward rules and Stage 4 anchor maps with dual-layer state tracking (episode-level subgoal pointer + global coverage set).

**Architecture:** Three focused files — `models.py` for pure data containers, `condition_evaluator.py` for isolated eval() logic, and `hybrid_reward.py` for the stateful orchestrator. Duck-typed inputs throughout to avoid cross-stage `sys.modules["models"]` collisions. `hybrid_reward.py` loads its own models via `importlib.util` pinned under `"_adaptive_reward_stage5_models"`, following the exact pattern from Stage 4.

**Tech Stack:** Python 3.10+, standard library only (`dataclasses`, `importlib.util`), pytest.

---

## File Structure

```
smart/adaptive_reward/
├── models.py               # StepResult, CoverageStats — pure @dataclass, no Pydantic
├── condition_evaluator.py  # evaluate_condition(condition, state_dict) -> bool
├── hybrid_reward.py        # HybridRewardFunction — stateful reward calculator
└── tests/
    ├── test_models.py
    ├── test_condition_evaluator.py
    └── test_hybrid_reward.py
```

No `__init__.py` anywhere — consistent with all other stages. Tests add the parent directory to `sys.path` and import modules directly.

---

## Critical Context: sys.modules Collision

Five stages each have a `models.py`. When pytest collects all tests together, importing `models` in one stage pollutes `sys.modules["models"]` for other stages. Stage 5 follows Stage 4's solution exactly:

- `hybrid_reward.py` uses `importlib.util.spec_from_file_location("_adaptive_reward_stage5_models", ...)` at module level to load `models.py` under a stable key
- Tests for Stage 5 only import `hybrid_reward` (which triggers the above) — no bare `import models` in test files that could collide

---

### Task 1: Scaffold adaptive_reward package

**Files:**
- Create: `smart/adaptive_reward/` (directory)
- Create: `smart/adaptive_reward/tests/` (directory)
- Create: `smart/adaptive_reward/models.py` (empty stub)
- Create: `smart/adaptive_reward/condition_evaluator.py` (empty stub)
- Create: `smart/adaptive_reward/hybrid_reward.py` (empty stub)
- Create: `smart/adaptive_reward/tests/test_models.py` (empty stub)
- Create: `smart/adaptive_reward/tests/test_condition_evaluator.py` (empty stub)
- Create: `smart/adaptive_reward/tests/test_hybrid_reward.py` (empty stub)

- [ ] **Step 1: Create directories and empty files**

```bash
cd /path/to/smart
mkdir -p adaptive_reward/tests
touch adaptive_reward/models.py
touch adaptive_reward/condition_evaluator.py
touch adaptive_reward/hybrid_reward.py
touch adaptive_reward/tests/test_models.py
touch adaptive_reward/tests/test_condition_evaluator.py
touch adaptive_reward/tests/test_hybrid_reward.py
```

- [ ] **Step 2: Verify structure**

```bash
find adaptive_reward -type f | sort
```

Expected output:
```
adaptive_reward/condition_evaluator.py
adaptive_reward/hybrid_reward.py
adaptive_reward/models.py
adaptive_reward/tests/test_condition_evaluator.py
adaptive_reward/tests/test_hybrid_reward.py
adaptive_reward/tests/test_models.py
```

- [ ] **Step 3: Commit scaffold**

```bash
git add adaptive_reward/
git commit -m "chore: scaffold Stage 5 adaptive_reward package"
```

---

### Task 2: Phase 1 — Data Models

**Files:**
- Create: `smart/adaptive_reward/models.py`
- Test: `smart/adaptive_reward/tests/test_models.py`

- [ ] **Step 1: Write failing tests**

Write `adaptive_reward/tests/test_models.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import StepResult, CoverageStats


class TestStepResult:
    def test_instantiation_and_fields(self):
        result = StepResult(
            total_reward=35.0,
            semantic_reward=30.0,
            structural_reward=5.0,
            subgoal_advanced=True,
            new_anchors_covered={"L:42"},
            is_terminal=False,
        )
        assert result.total_reward == 35.0
        assert result.semantic_reward == 30.0
        assert result.structural_reward == 5.0
        assert result.subgoal_advanced is True
        assert result.new_anchors_covered == {"L:42"}
        assert result.is_terminal is False

    def test_zero_reward_step(self):
        result = StepResult(
            total_reward=0.0,
            semantic_reward=0.0,
            structural_reward=0.0,
            subgoal_advanced=False,
            new_anchors_covered=set(),
            is_terminal=False,
        )
        assert result.total_reward == 0.0
        assert result.new_anchors_covered == set()

    def test_terminal_step(self):
        result = StepResult(
            total_reward=230.0,
            semantic_reward=230.0,
            structural_reward=0.0,
            subgoal_advanced=True,
            new_anchors_covered=set(),
            is_terminal=True,
        )
        assert result.is_terminal is True
        assert result.semantic_reward == 230.0


class TestCoverageStats:
    def test_instantiation(self):
        stats = CoverageStats(
            total_anchors=10,
            covered_count=4,
            coverage_rate=0.4,
        )
        assert stats.total_anchors == 10
        assert stats.covered_count == 4
        assert stats.coverage_rate == 0.4

    def test_full_coverage(self):
        stats = CoverageStats(total_anchors=5, covered_count=5, coverage_rate=1.0)
        assert stats.coverage_rate == 1.0

    def test_zero_coverage(self):
        stats = CoverageStats(total_anchors=0, covered_count=0, coverage_rate=0.0)
        assert stats.coverage_rate == 0.0

    def test_coverage_rate_is_plain_field(self):
        # coverage_rate is a plain float field — caller computes it, not __post_init__
        stats = CoverageStats(total_anchors=10, covered_count=0, coverage_rate=0.99)
        assert stats.coverage_rate == 0.99  # whatever the caller passed, not auto-computed
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd smart && python3 -m pytest adaptive_reward/tests/test_models.py -v
```

Expected: ImportError or similar — `models.py` is empty.

- [ ] **Step 3: Implement models.py**

Write `adaptive_reward/models.py`:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd smart && python3 -m pytest adaptive_reward/tests/test_models.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add adaptive_reward/models.py adaptive_reward/tests/test_models.py
git commit -m "feat: Stage 5 data models StepResult and CoverageStats"
```

---

### Task 3: Phase 2 — Condition Evaluator

**Files:**
- Create: `smart/adaptive_reward/condition_evaluator.py`
- Test: `smart/adaptive_reward/tests/test_condition_evaluator.py`

- [ ] **Step 1: Write failing tests**

Write `adaptive_reward/tests/test_condition_evaluator.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from condition_evaluator import evaluate_condition


class TestEvaluateCondition:
    def test_simple_true(self):
        assert evaluate_condition("x > 0", {"x": 1}) is True

    def test_simple_false(self):
        assert evaluate_condition("x > 0", {"x": -1}) is False

    def test_name_error_returns_false(self):
        # undefined_var not in state_dict → NameError → False
        assert evaluate_condition("undefined_var", {}) is False

    def test_syntax_error_returns_false(self):
        assert evaluate_condition("not valid python !!!", {}) is False

    def test_empty_condition_returns_false(self):
        assert evaluate_condition("", {}) is False

    def test_complex_predicate_true(self):
        state = {"inventory": ["pizza"], "oven": "ready"}
        assert evaluate_condition("'pizza' in inventory and oven == 'ready'", state) is True

    def test_complex_predicate_false(self):
        state = {"inventory": [], "oven": "ready"}
        assert evaluate_condition("'pizza' in inventory and oven == 'ready'", state) is False

    def test_zero_is_falsy(self):
        assert evaluate_condition("count", {"count": 0}) is False

    def test_nonempty_list_is_truthy(self):
        assert evaluate_condition("items", {"items": ["a"]}) is True

    def test_exception_in_eval_returns_false(self):
        # Division by zero inside condition
        assert evaluate_condition("1 / 0", {}) is False

    def test_builtins_restricted(self):
        # __import__ should not be accessible
        assert evaluate_condition("__import__('os')", {}) is False
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd smart && python3 -m pytest adaptive_reward/tests/test_condition_evaluator.py -v
```

Expected: ImportError — `condition_evaluator.py` is empty.

- [ ] **Step 3: Implement condition_evaluator.py**

Write `adaptive_reward/condition_evaluator.py`:

```python
from __future__ import annotations


def evaluate_condition(condition: str, state_dict: dict) -> bool:
    """
    Evaluate a Stage 3 RewardEvent condition string against a game state dict.

    Uses eval() with restricted builtins to reduce risk. Any exception
    (NameError, SyntaxError, TypeError, ZeroDivisionError, etc.) returns False.
    Never raises.

    Args:
        condition: Python expression string, e.g. "'pizza' in inventory and oven == 'ready'"
        state_dict: game state variables, e.g. {"inventory": ["pizza"], "oven": "ready"}

    Returns:
        True if condition evaluates to a truthy value, False otherwise.
    """
    try:
        return bool(eval(condition, {"__builtins__": {}}, state_dict))
    except Exception:
        return False
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd smart && python3 -m pytest adaptive_reward/tests/test_condition_evaluator.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add adaptive_reward/condition_evaluator.py adaptive_reward/tests/test_condition_evaluator.py
git commit -m "feat: Stage 5 condition evaluator with restricted eval()"
```

---

### Task 4: Phase 3 — HybridRewardFunction

**Files:**
- Create: `smart/adaptive_reward/hybrid_reward.py`
- Test: `smart/adaptive_reward/tests/test_hybrid_reward.py`

- [ ] **Step 1: Write failing tests**

Write `adaptive_reward/tests/test_hybrid_reward.py`:

```python
"""
Tests for HybridRewardFunction.

Import order:
  1. Import hybrid_reward — its module-level importlib block loads Stage 5 models
     under "_adaptive_reward_stage5_models" key.
  2. Get StepResult/CoverageStats from that pinned module, NOT from a bare "import models".

No cross-stage imports needed: HybridRewardFunction is duck-typed.
"""
import sys
import os
import pytest
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hybrid_reward import HybridRewardFunction

# Get model classes from the pinned module loaded by hybrid_reward
_S5 = sys.modules["_adaptive_reward_stage5_models"]
StepResult = _S5.StepResult
CoverageStats = _S5.CoverageStats


# ---------------------------------------------------------------------------
# Mock helpers — duck-typed to match Stage 3 / Stage 4 interfaces
# ---------------------------------------------------------------------------

@dataclass
class MockEvent:
    condition: str
    reward: float = 10.0  # not used by Stage 5, but matches Stage 3 shape


@dataclass
class MockRule:
    subgoal_index: int
    events: list = field(default_factory=list)


@dataclass
class MockRuleSet:
    task_name: str
    rules: list = field(default_factory=list)


@dataclass
class MockMapping:
    anchor_key: str
    subgoal_indices: list = field(default_factory=list)


@dataclass
class MockAnchorMap:
    task_name: str
    file_path: str
    mappings: list = field(default_factory=list)


def make_rule_set(n: int) -> MockRuleSet:
    """n subgoals, indices 1..n, each with one event: condition f'step == {i}'"""
    rules = [
        MockRule(
            subgoal_index=i,
            events=[MockEvent(condition=f"step == {i}")]
        )
        for i in range(1, n + 1)
    ]
    return MockRuleSet(task_name="test_task", rules=rules)


def make_multi_event_rule_set(n: int) -> MockRuleSet:
    """n subgoals; each rule has two events: first always False, second matches."""
    rules = [
        MockRule(
            subgoal_index=i,
            events=[
                MockEvent(condition="False"),
                MockEvent(condition=f"step == {i}"),
            ]
        )
        for i in range(1, n + 1)
    ]
    return MockRuleSet(task_name="test_task", rules=rules)


def make_anchor_map(mappings: list) -> MockAnchorMap:
    """
    mappings: list of (anchor_key: str, subgoal_indices: list[int])
    """
    mock_mappings = [
        MockMapping(anchor_key=key, subgoal_indices=indices)
        for key, indices in mappings
    ]
    return MockAnchorMap(task_name="test_task", file_path="test.py", mappings=mock_mappings)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHybridRewardFunction:

    def test_semantic_reward_on_condition_match(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([]),
            r_sem=30.0, r_str=5.0, terminal_reward=200.0,
        )
        result = rf.compute_reward({"step": 1}, set())
        assert result.semantic_reward == 30.0
        assert result.subgoal_advanced is True
        assert result.total_reward == 30.0

    def test_no_semantic_reward_when_condition_false(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([]),
        )
        result = rf.compute_reward({"step": 99}, set())  # no subgoal has step==99
        assert result.semantic_reward == 0.0
        assert result.subgoal_advanced is False
        assert result.total_reward == 0.0

    def test_j_advances_sequentially(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([]),
        )
        assert rf.subgoal_progress == (1, 3)
        rf.compute_reward({"step": 1}, set())
        assert rf.subgoal_progress == (2, 3)
        rf.compute_reward({"step": 2}, set())
        assert rf.subgoal_progress == (3, 3)

    def test_terminal_reward_on_last_subgoal(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([]),
            r_sem=30.0, terminal_reward=200.0,
        )
        rf.compute_reward({"step": 1}, set())  # advance to j=2
        result = rf.compute_reward({"step": 2}, set())  # complete last subgoal
        assert result.semantic_reward == 30.0 + 200.0
        assert result.is_terminal is True
        assert result.subgoal_advanced is True

    def test_terminal_and_structural_reward_same_step(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:10", [2])]),
            r_sem=30.0, r_str=5.0, terminal_reward=200.0,
        )
        rf.compute_reward({"step": 1}, set())  # advance to j=2
        result = rf.compute_reward({"step": 2}, {"L:10"})  # complete last + cover anchor
        assert result.semantic_reward == 230.0   # 30 + 200
        assert result.structural_reward == 5.0   # one new anchor
        assert result.total_reward == 235.0
        assert result.is_terminal is True

    def test_structural_reward_new_anchor(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, {"L:42"})  # j=1, no semantic
        assert result.structural_reward == 5.0
        assert "L:42" in result.new_anchors_covered

    def test_structural_reward_two_new_anchors(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1]), ("B:20:if_true", [1])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, {"L:42", "B:20:if_true"})
        assert result.structural_reward == 10.0  # 2 × r_str
        assert result.new_anchors_covered == {"L:42", "B:20:if_true"}

    def test_structural_reward_dedup_across_steps(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        rf.compute_reward({"step": 99}, {"L:42"})        # covered in step 1
        result = rf.compute_reward({"step": 99}, {"L:42"})  # same anchor in step 2
        assert result.structural_reward == 0.0
        assert result.new_anchors_covered == set()

    def test_structural_reward_dedup_across_episodes(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        rf.compute_reward({"step": 99}, {"L:42"})  # covered in episode 1
        rf.reset()                                  # start episode 2, C_cov preserved
        result = rf.compute_reward({"step": 99}, {"L:42"})
        assert result.structural_reward == 0.0      # already in C_cov

    def test_structural_reward_wrong_subgoal(self):
        # Anchor mapped to subgoal 2, but current j=1 → no structural reward
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([("L:42", [2])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, {"L:42"})  # j=1 at this point
        assert result.structural_reward == 0.0

    def test_reset_resets_j_not_coverage(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(3),
            anchor_map=make_anchor_map([("L:42", [1])]),
        )
        rf.compute_reward({"step": 1}, {"L:42"})  # j→2, L:42 covered
        assert rf.subgoal_progress == (2, 3)
        assert rf.coverage_rate > 0.0

        rf.reset()
        assert rf.subgoal_progress == (1, 3)   # j reset
        assert rf.coverage_rate > 0.0          # C_cov NOT cleared

    def test_coverage_rate_zero_start(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:1", [1]), ("L:2", [2])]),
        )
        assert rf.coverage_rate == 0.0

    def test_coverage_rate_updates(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:1", [1]), ("L:2", [2])]),
        )
        rf.compute_reward({"step": 99}, {"L:1"})
        assert rf.coverage_rate == 0.5
        rf.compute_reward({"step": 99}, {"L:2"})
        # L:2 is mapped to subgoal 2, but j=1 still (step 99 didn't match subgoal 1)
        # So L:2 won't be covered yet — context-aware filter blocks it
        assert rf.coverage_rate == 0.5  # still only L:1 covered

    def test_get_coverage_stats(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:1", [1]), ("L:2", [1]), ("L:3", [2])]),
            r_str=5.0,
        )
        rf.compute_reward({"step": 99}, {"L:1"})
        stats = rf.get_coverage_stats()
        assert stats.total_anchors == 3
        assert stats.covered_count == 1
        assert abs(stats.coverage_rate - 1/3) < 1e-9

    def test_subgoal_progress_property(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(5),
            anchor_map=make_anchor_map([]),
        )
        assert rf.subgoal_progress == (1, 5)
        rf.compute_reward({"step": 1}, set())
        assert rf.subgoal_progress == (2, 5)

    def test_subgoal_progress_after_terminal(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([]),
        )
        rf.compute_reward({"step": 1}, set())
        rf.compute_reward({"step": 2}, set())  # terminal
        assert rf.subgoal_progress == (3, 2)   # current_j == total_n + 1

    def test_empty_covered_anchors(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_str=5.0,
        )
        result = rf.compute_reward({"step": 99}, set())
        assert result.structural_reward == 0.0
        assert result.new_anchors_covered == set()

    def test_unknown_anchor_key_ignored(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(2),
            anchor_map=make_anchor_map([("L:42", [1])]),
        )
        # "L:999" not in anchor_map → silently ignored, no crash, no reward
        result = rf.compute_reward({"step": 99}, {"L:999"})
        assert result.structural_reward == 0.0

    def test_multi_event_or_semantics(self):
        # Rule has two events: first always False, second True when step==1
        rf = HybridRewardFunction(
            reward_rule_set=make_multi_event_rule_set(2),
            anchor_map=make_anchor_map([]),
            r_sem=30.0,
        )
        result = rf.compute_reward({"step": 1}, set())
        assert result.semantic_reward == 30.0   # second event triggered it
        assert result.subgoal_advanced is True

    def test_constructor_raises_on_gap_in_subgoal_indices(self):
        # Indices [1, 3] — gap at 2 → ValueError
        gap_rule_set = MockRuleSet(
            task_name="gap",
            rules=[
                MockRule(subgoal_index=1, events=[MockEvent(condition="True")]),
                MockRule(subgoal_index=3, events=[MockEvent(condition="True")]),
            ]
        )
        with pytest.raises(ValueError, match="contiguous"):
            HybridRewardFunction(
                reward_rule_set=gap_rule_set,
                anchor_map=make_anchor_map([]),
            )

    def test_compute_reward_after_terminal_returns_zero(self):
        rf = HybridRewardFunction(
            reward_rule_set=make_rule_set(1),
            anchor_map=make_anchor_map([("L:42", [1])]),
            r_sem=30.0, r_str=5.0, terminal_reward=200.0,
        )
        rf.compute_reward({"step": 1}, set())   # terminal: j becomes 2
        # Call again without reset — all-zero result
        result = rf.compute_reward({"step": 1}, {"L:42"})
        assert result.total_reward == 0.0
        assert result.semantic_reward == 0.0
        assert result.structural_reward == 0.0
        assert result.subgoal_advanced is False
        assert result.new_anchors_covered == set()
        assert result.is_terminal is False
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd smart && python3 -m pytest adaptive_reward/tests/test_hybrid_reward.py -v
```

Expected: ImportError — `hybrid_reward.py` is empty.

- [ ] **Step 3: Implement hybrid_reward.py**

Write `adaptive_reward/hybrid_reward.py`:

```python
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
    _spec.loader.exec_module(_mod)
    _sys.modules[_S5_MODELS_KEY] = _mod

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
        returns an all-zero StepResult with is_terminal=False.
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

        # Step 2: Structural reward (context-aware, uses j_at_start)
        # Only rewards anchors mapped to j_at_start and not yet in C_cov.
        # Anchors relevant to other subgoals or unknown anchors are silently skipped.
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd smart && python3 -m pytest adaptive_reward/tests/test_hybrid_reward.py -v
```

Expected: all 21 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add adaptive_reward/hybrid_reward.py adaptive_reward/tests/test_hybrid_reward.py
git commit -m "feat: Stage 5 HybridRewardFunction with dual-layer state tracking"
```

---

### Task 5: Full Regression

**Files:**
- No new files — run existing tests in isolation to confirm no regressions.

- [ ] **Step 1: Run Stage 5 tests**

```bash
cd smart && python3 -m pytest adaptive_reward/tests/ -v
```

Expected: all tests PASS (7 + 11 + 21 = 39 tests).

- [ ] **Step 2: Run Stage 1 tests**

```bash
cd smart && python3 -m pytest ast_diff_parser/tests/ -q
```

Expected: 96 passed.

- [ ] **Step 3: Run Stage 2 tests**

```bash
cd smart && python3 -m pytest subgoal_generator/tests/ -q
```

Expected: 47 passed, 6 skipped.

- [ ] **Step 4: Run Stage 3 tests**

```bash
cd smart && python3 -m pytest reward_generator/tests/ -q
```

Expected: 55 passed, 5 skipped.

- [ ] **Step 5: Run Stage 4 tests**

```bash
cd smart && python3 -m pytest anchor_mapper/tests/ -q
```

Expected: 57 passed, 5 skipped.

- [ ] **Step 6: If any stage fails, diagnose the root cause**

The most likely cause of cross-stage failure is a `sys.modules["models"]` collision when pytest collects all five stages at once. Each stage should be run in isolation (as above) — they are designed to be tested independently. If a stage fails in isolation, that is a real regression.

If you see collection errors when running `pytest` across all stages simultaneously, this is expected and pre-existing — it's not a new regression introduced by Stage 5.

- [ ] **Step 7: Commit regression results**

```bash
git commit -m "test: Stage 5 full regression — all stages passing in isolation"
```

(Only commit if there are any staged changes; if all was clean, skip.)
