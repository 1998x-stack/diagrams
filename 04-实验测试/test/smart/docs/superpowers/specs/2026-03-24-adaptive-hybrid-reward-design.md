# Stage 5: Adaptive Hybrid Reward Function — Design Spec

## Goal

Implement the execution core of the SMART framework: a stateful reward calculator that integrates the outputs of Stages 1–4 and produces a per-timestep hybrid reward signal `r_t = r_sem + r_str` for RL training loops.

## Architecture

```
smart/adaptive_reward/
├── models.py               # StepResult, CoverageStats
├── condition_evaluator.py  # eval()-based condition evaluation
├── hybrid_reward.py        # HybridRewardFunction main class
└── tests/
    ├── test_models.py
    ├── test_condition_evaluator.py
    └── test_hybrid_reward.py
```

No `__init__.py` — tests import modules directly (e.g., `from hybrid_reward import HybridRewardFunction`), consistent with other stages. No integration tests: Stage 5 is a standalone reward calculator; integration with an actual RL environment is out of scope.

## Tech Stack

- Python 3.10+
- Standard library only (`dataclasses`, `typing`, `importlib.util`) — no third-party dependencies
- `pytest` for testing

---

## Component Design

### models.py

Two dataclasses, no Pydantic (pure data containers, no API serialization needed).

```python
@dataclass
class StepResult:
    total_reward: float
    semantic_reward: float       # r_sem if subgoal advanced, else 0.0
    structural_reward: float     # r_str × number of newly covered anchors
    subgoal_advanced: bool       # True if j incremented this step
    new_anchors_covered: set[str]
    is_terminal: bool            # True when all subgoals complete

@dataclass
class CoverageStats:
    total_anchors: int           # len(_anchor_index) — unique anchor keys, NOT len(anchor_map.mappings)
    covered_count: int           # |C_cov|
    coverage_rate: float         # covered_count / total_anchors (0.0 if total == 0)
                                 # NOTE: plain field — caller computes and passes the value
```

`CoverageStats.coverage_rate` is a plain `float` field (not `__post_init__`). The caller (`get_coverage_stats()`) computes `covered_count / total_anchors` (with 0.0 guard) and passes it as a constructor argument.

### condition_evaluator.py

Single public function. Evaluates a Stage 3 `RewardEvent.condition` string against a game state dict using `eval()`. Restricts builtins to reduce risk. Any exception (NameError, SyntaxError, TypeError, etc.) returns `False` — never raises.

```python
def evaluate_condition(condition: str, state_dict: dict) -> bool:
    try:
        return bool(eval(condition, {"__builtins__": {}}, state_dict))
    except Exception:
        return False
```

### hybrid_reward.py — HybridRewardFunction

The stateful core. Duck-typed inputs (no direct imports from Stages 3/4) to avoid `sys.modules["models"]` cross-stage collisions.

#### Constructor

```python
class HybridRewardFunction:
    def __init__(
        self,
        reward_rule_set,           # Stage 3 RewardRuleSet (duck-typed)
        anchor_map,                # Stage 4 StructuralAnchorMap (duck-typed)
        r_sem: float = 30.0,
        r_str: float = 5.0,
        terminal_reward: float = 200.0,
    ):
```

At construction time:

1. **Sort rules**: Extract `reward_rule_set.rules`, sort by `rule.subgoal_index` → `_rules: list`. Validate that the sorted `subgoal_index` values form a contiguous sequence starting at 1 (i.e., `[1, 2, 3, ..., n]`). Raise `ValueError` if any gap exists (e.g., indices `[1, 3]` without `2`), since a gap would cause `_j` to get stuck forever with no matching rule.

2. **Build anchor-to-subgoals lookup dict**: Iterate over `anchor_map.mappings` (each mapping has `anchor_key: str` and `subgoal_indices: list[int]`). For each mapping, iterate over all values in `mapping.subgoal_indices` and union the result into `_anchor_index[anchor_key]`. This normalizes the list-of-mappings structure into a single flat dict keyed by anchor_key (merging any mappings that share the same key):
   ```python
   _anchor_index: dict[str, set[int]] = {}   # anchor_key → set of subgoal indices
   for mapping in anchor_map.mappings:
       for idx in mapping.subgoal_indices:
           _anchor_index.setdefault(mapping.anchor_key, set()).add(idx)
   ```
   The resulting shape is `dict[str, set[int]]`: look up by `anchor_key`, get the set of subgoal indices where that anchor is relevant. **Not** the inverse direction (`dict[int, set[str]]`).

3. Set `_total_subgoals = len(_rules)`

4. Initialize `_C_cov: set[str] = set()` (global, **never reset** across episodes)

5. Initialize `_j: int = 1` (episode-level subgoal pointer)

#### reset()

Resets `_j = 1`. Does **not** clear `_C_cov`. Called at the start of each new episode.

#### compute_reward(state_dict: dict, covered_anchors: set[str]) → StepResult

`state_dict`: current game state as `{variable_name: value}` — same schema used to generate Stage 3 conditions.
`covered_anchors`: set of `anchor_key` strings (e.g., `{"L:42", "B:20:if_true"}`) triggered by the environment in this timestep.

Implements Algorithm 1 from the paper. Capture `j_at_start = _j` before any modification — this is used for structural scoping in Step 2.

**Step 1 — Semantic reward:**
- If `_j <= _total_subgoals`:
  - Get the rule at position `_j - 1` in `_rules` (rules are sorted by `subgoal_index`, so `_rules[_j - 1]` is the rule for subgoal `_j`)
  - Evaluate each `RewardEvent.condition` in the rule's `events` list via `evaluate_condition(condition, state_dict)`
  - If **any** event condition is `True` (logical OR across all events in the rule) → `r_sem_step = r_sem`, set `subgoal_advanced = True`, increment `_j`
  - If `_j` after increment `> _total_subgoals` → also add `terminal_reward` to `r_sem_step` and set `is_terminal = True`
  - Note: both terminal_reward and structural_reward from Step 2 can fire in the same timestep; they are independent and additive.
- If `_j > _total_subgoals` (i.e., called post-terminal without `reset()`): Step 1 is skipped entirely (condition `_j <= _total_subgoals` is False). Step 2 uses `j_at_start = _j` which exceeds all mapped subgoal indices, so no structural reward fires either. The result is an all-zero `StepResult` with `is_terminal = False`. This is the defined behavior for post-terminal calls — the RL loop should call `reset()` before starting a new episode.

**Step 2 — Structural reward (context-aware):**

This extends the paper's base algorithm with the context-scoping described in the paper's prose: "the agent is rewarded only for covering structural changes relevant to the current gameplay stage." Structural reward uses `j_at_start` (the subgoal index *before* any semantic advance in this step):

- For each `anchor_key` in `covered_anchors`:
  - If `anchor_key` is in `_anchor_index` AND `j_at_start` is in `_anchor_index[anchor_key]`:
    - If `anchor_key` not in `_C_cov` → add `r_str` to structural reward, add `anchor_key` to `_C_cov`, add to `new_anchors_covered`
  - Otherwise (unknown key or wrong subgoal): skip silently

**Step 3 — Return** `StepResult(total_reward=r_sem_step + r_str_step, semantic_reward=r_sem_step, structural_reward=r_str_step, subgoal_advanced=subgoal_advanced, new_anchors_covered=new_anchors_covered, is_terminal=is_terminal)`

#### Properties and helpers

```python
@property
def coverage_rate(self) -> float:
    """Fraction of unique anchors covered. 0.0 if no anchors in anchor_map."""

@property
def subgoal_progress(self) -> tuple[int, int]:
    """(current_j, total_n). After terminal, current_j == total_n + 1 exactly."""

def get_coverage_stats(self) -> CoverageStats:
    """
    total_anchors = len(_anchor_index)  — unique anchor keys, NOT len(anchor_map.mappings).
    Using len(mappings) would overcount if two mappings share the same anchor_key,
    causing coverage_rate > 1.0. Always use the deduped _anchor_index size.
    coverage_rate = covered_count / total_anchors (0.0 if total_anchors == 0).
    """
```

---

## sys.modules Collision Handling

`adaptive_reward/models.py` shares the name `models.py` with Stages 1, 3, and 4. Following the pattern used by `anchor_mapper.py` (Stage 4), `hybrid_reward.py` uses `importlib.util` at module-level to load Stage 5 models under a stable pinned key, avoiding reliance on `sys.path` ordering:

```python
import importlib.util as _ilu
import os as _os
import sys as _sys

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
```

Tests load Stage 5 models by importing `hybrid_reward` (which triggers the above block) after clearing any conflicting `sys.modules["models"]` entry.

---

## Algorithm Fidelity

Implements Algorithm 1 from the SMART paper, with the context-aware extension described in the paper's prose:

| Paper | Implementation |
|---|---|
| `j` resets per episode | `reset()` sets `_j = 1` |
| `C_cov` persists globally | `_C_cov` never cleared by `reset()` |
| `r_j(s_{t+1}) > 0` | any `RewardEvent.condition` evaluates truthy (logical OR across events in rule) |
| `r_t += r_sem; j += 1` | `_j` increments, `r_sem` added to step |
| `c not in C_cov → r_t += r_str; C_cov.add(c)` | each new anchor rewarded once, **only if mapped to current subgoal `j_at_start`** (context-aware extension per paper prose) |
| Context-aware: anchor relevant only at current stage | `_anchor_index[key]` checked against `j_at_start` |
| Terminal reward on task completion | added when `_j` exceeds `_total_subgoals`; can coincide with structural reward in same step |

**Deliberate deviation from paper pseudocode**: The raw Algorithm 1 rewards any uncovered anchor from `C_step`. This implementation adds context-scoping (filter by `j_at_start`) per the paper's prose: "ensures that the agent is rewarded only for covering structural changes relevant to the current gameplay stage."

The paper's `r_sem` is a fixed magnitude (not per-event values from Stage 3). Stage 3's `RewardEvent.reward` values are **not** used in Stage 5 — only their `condition` strings are evaluated.

---

## Test Plan

### test_models.py
- `StepResult` instantiation and field access
- `CoverageStats` instantiation; `coverage_rate` is a plain field (caller passes value, no auto-computation)

### test_condition_evaluator.py
- Simple true condition: `"x > 0"` with `{"x": 1}` → `True`
- Simple false condition: `"x > 0"` with `{"x": -1}` → `False`
- Exception (NameError): `"undefined_var"` with `{}` → `False`
- Syntax error: `"not valid python !!!"` → `False`
- Empty condition string → `False`
- Complex predicate: `"'pizza' in inventory and oven == 'ready'"` with matching state → `True`

### test_hybrid_reward.py (~19 tests)

**Setup helpers:**
- `make_rule_set(n)` — builds a mock `RewardRuleSet` with `n` subgoals (indices 1..n), each with one event and a simple condition like `f"step == {i}"`
- `make_multi_event_rule_set(n)` — like `make_rule_set` but each rule has two events; first condition always False, second matches
- `make_anchor_map(mappings)` — builds a mock `StructuralAnchorMap` from a list of `(anchor_key, [subgoal_indices])` tuples

**Tests:**
1. `test_semantic_reward_on_condition_match` — condition satisfied → r_sem in result, j advances
2. `test_no_semantic_reward_when_condition_false` — condition not satisfied → r_sem=0, j unchanged
3. `test_j_advances_sequentially` — two compute_reward calls, j goes 1→2→3
4. `test_terminal_reward_on_last_subgoal` — completing subgoal n → terminal_reward added, is_terminal=True
5. `test_terminal_and_structural_reward_same_step` — completing last subgoal while also covering new anchor → both rewards fire in same step
6. `test_structural_reward_new_anchor` — covered anchor mapped to current j, not in C_cov → r_str
7. `test_structural_reward_two_new_anchors` — two distinct new covered anchors both mapped to current j → structural_reward == 2×r_str
8. `test_structural_reward_dedup_across_steps` — anchor covered in step 1, present again in step 2 → 0
9. `test_structural_reward_dedup_across_episodes` — anchor covered in episode 1, still in C_cov after reset → 0
10. `test_structural_reward_wrong_subgoal` — anchor mapped to subgoal 2, current j=1 → 0 (context-aware filter)
11. `test_reset_resets_j_not_coverage` — after reset(), j=1 but C_cov preserved
12. `test_coverage_rate_zero_start` — 0.0 before any compute_reward
13. `test_coverage_rate_updates` — increases as new anchors covered
14. `test_get_coverage_stats` — total_anchors, covered_count, coverage_rate all correct
15. `test_subgoal_progress_property` — returns (current_j, total_n)
16. `test_subgoal_progress_after_terminal` — after all subgoals complete, current_j == total_n + 1
17. `test_empty_covered_anchors` — compute_reward with empty set → structural=0
18. `test_unknown_anchor_key_ignored` — anchor_key not in anchor_map → no reward, no crash
19. `test_multi_event_or_semantics` — rule with two events, first False / second True → semantic reward fires (logical OR)
20. `test_constructor_raises_on_gap_in_subgoal_indices` — RewardRuleSet with indices [1, 3] raises ValueError
21. `test_compute_reward_after_terminal_returns_zero` — after all subgoals complete, calling compute_reward again (without reset) returns StepResult with total_reward=0.0, semantic_reward=0.0, structural_reward=0.0, subgoal_advanced=False, new_anchors_covered=set(), is_terminal=False
