# Stage 4: Structural Anchor Mapper — Design Spec

## Overview

Stage 4 of the SMART framework builds the mapping M: C → P(S) — assigning each structural anchor (from Stage 1's DiffResult) to the subgoals (from Stage 2's SubgoalSequence) where it is semantically relevant. This mapping gates Stage 5's structural reward: an anchor only triggers a reward when the agent is working on a subgoal it has been mapped to.

## Goals

- Produce a `StructuralAnchorMap` that maps every structural anchor to one or more subgoal indices
- Phase 1 (static): AST-based call graph analysis — fast, conservative over-approximation of reachable anchors per subgoal
- Phase 2 (LLM): Per-subgoal Claude call — semantically filters the candidate set to only truly relevant anchors
- Follow the same package structure and patterns established by Stages 2 and 3

## Non-Goals

- Cross-file call graph analysis (intra-file only)
- Runtime / dynamic call graph generation
- Modifying DiffResult or SubgoalSequence models from earlier stages

---

## Architecture

```
anchor_mapper/
├── models.py               # AnchorMapping, StructuralAnchorMap, AnchorMappingError, CandidateSet
├── client_factory.py       # identical pattern to Stages 2 & 3
├── call_graph_analyzer.py  # Phase 1: AST-based static analysis → CandidateSet per subgoal
├── prompt_builder.py       # Phase 2: per-subgoal filtering prompt + FilterResult schema (defined here)
└── anchor_mapper.py        # orchestrator: Phase 1 → Phase 2 → StructuralAnchorMap
tests/
├── test_models.py
├── test_call_graph_analyzer.py
├── test_prompt_builder.py
├── test_anchor_mapper.py   # mock Claude client
└── test_integration.py     # skipped without ANTHROPIC_API_KEY
```

---

## Data Models (`models.py`)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Literal
from pydantic import BaseModel, Field

class AnchorMappingError(Exception):
    def __init__(self, message: str, stop_reason: Optional[str] = None):
        super().__init__(message)
        self.stop_reason = stop_reason

class AnchorMapping(BaseModel):
    anchor_key: str                      # "L:42" or "B:20:if_true"
    anchor_type: Literal["line", "branch"]
    line_number: int                     # line number (or control_stmt_line for branches)
    branch_type: Optional[str] = None   # None for lines; "if_true" / "if_false" / etc.
    source_snippet: str                  # ModifiedLine.source or ModifiedBranch.condition_source
    subgoal_indices: list[int] = Field(..., min_length=1)

class StructuralAnchorMap(BaseModel):
    task_name: str
    file_path: str
    mappings: list[AnchorMapping]       # may be empty if no anchors matched any subgoal

    def for_subgoal(self, index: int) -> list[AnchorMapping]:
        """Return all anchors mapped to the given subgoal index."""
        return [m for m in self.mappings if index in m.subgoal_indices]

    def to_dict(self) -> dict:
        return self.model_dump()

# Internal dataclass — used as the Phase 1 → Phase 2 handoff type.
# Lives in models.py so call_graph_analyzer.py and prompt_builder.py both import it from one place.
@dataclass
class FunctionInfo:
    name: str          # qualified name, e.g. "MatrixCalculator.determinant"
    start_line: int
    end_line: int
    calls: list[str] = field(default_factory=list)   # names of functions/methods called in body

@dataclass
class CandidateSet:
    subgoal_index: int
    subgoal_description: str
    subgoal_rationale: str
    candidates: list   # list[ModifiedLine | ModifiedBranch] from Stage 1
                       # typed as list to avoid importing Stage 1 models at module level
```

**Anchor key format:**
- Modified line at line 42 → `"L:42"`
- Modified branch at line 20, type `if_true` → `"B:20:if_true"`

**`source_snippet` population rules (in orchestrator, when building `AnchorMapping`):**
- For a `ModifiedLine`: `source_snippet = modified_line.source`
- For a `ModifiedBranch`: `source_snippet = modified_branch.condition_source` (may be empty string for `loop_body` / `except` branches — that is acceptable)

---

## Phase 1: Call Graph Analyzer (`call_graph_analyzer.py`)

### Public interface

```python
def analyze_call_graph(
    diff_result: DiffResult,
    subgoal_sequence: SubgoalSequence,
    source_code: str,
) -> list[CandidateSet]:
```

### anchor_hints format

`Subgoal.anchor_hints` is a list of strings produced by Stage 2's Claude call. Stage 2's prompt instructs Claude to use exclusively line-number-based formats (see `subgoal_generator/prompt_builder.py` rule 3):

| Format | Example | Meaning |
|--------|---------|---------|
| Pure integer string | `"42"` | Reference to line 42 (a ModifiedLine entry) |
| Integer/branch | `"20/if_true"` | Reference to line 20, branch type `if_true` (a ModifiedBranch entry) |

**Parsing rule:** Split on `"/"`. Left part is always an integer line number. Optional right part is a branch type string.

Name-based hints (e.g. `"MatrixCalculator"`) may appear in manually crafted test fixtures but are never produced by Stage 2's actual API call. The call graph analyzer only needs to handle line-number-based hints.

### Algorithm

**Step 1 — Build function map**

Walk the AST of `source_code`. For every `FunctionDef`, `AsyncFunctionDef`, and class body method, record a `FunctionInfo`:
- Qualified name: `"MatrixCalculator.determinant"` for methods, `"taylor_series"` for top-level functions
- `start_line`, `end_line` from AST node
- All `ast.Call` targets within the body (resolved to name strings where resolvable; silently skip unresolvable dynamic calls)

**Step 2 — Identify entry points per subgoal**

For each subgoal, parse its `anchor_hints`. All hints are line-number based:
- Parse the left part of each hint as an integer line number
- Find the `FunctionInfo` whose `start_line <= line_number <= end_line`
- That `FunctionInfo` is an entry point for this subgoal
- If no `FunctionInfo` contains that line (e.g. line is in module-level code), use the conservative fallback (candidate for all subgoals)

**Step 3 — BFS through call graph**

From each entry point function, follow `calls` edges recursively (cycle-safe, visited set) to collect all reachable function names.

**Step 4 — Collect candidate anchors**

Any `ModifiedLine` or `ModifiedBranch` from DiffResult whose line number falls within a reachable function is a candidate for that subgoal.

**Direct hint match:** If an anchor's line number exactly matches a line-number hint, it is always included as a candidate for that subgoal regardless of call graph reachability.

**Fallback:** An anchor not reachable from any entry point of any subgoal is added as a candidate for *all* subgoals (conservative — LLM filter will drop irrelevant ones).

---

## Phase 2: Prompt Builder & LLM Filter (`prompt_builder.py`)

### `FilterResult` schema (defined in `prompt_builder.py`, NOT in `models.py`)

```python
from pydantic import BaseModel

class FilterResult(BaseModel):
    relevant_keys: list[str]   # subset of anchor_keys from the prompt's candidate list
    rationale: str             # brief explanation (for debugging)
```

`FilterResult` is defined in `prompt_builder.py` because it is only used as the structured output type for the per-subgoal LLM call. It does not need to be in `models.py` and is NOT imported through `sys.modules["models"]`.

### Public interface

```python
def build_prompt(candidate_set: CandidateSet) -> str:
```

### Prompt structure (per subgoal)

```
You are a code relevance analyst for a game testing framework.

Given the subgoal and candidate code anchors below, determine which anchors
are DIRECTLY and SEMANTICALLY relevant to completing that subgoal.

An anchor is relevant if a player performing this subgoal would necessarily
trigger or interact with that code. Exclude anchors that are technically
reachable but serve unrelated functionality.

=== SUBGOAL ===
Index: {index}
Description: {description}
Rationale: {rationale}

=== CANDIDATE ANCHORS ===
[{anchor_key}] ({anchor_type}) {source_snippet}
...

Return the keys of relevant anchors and a brief rationale.
```

Note: each anchor line includes `anchor_type` ("line" or "branch") to help Claude understand the structural context.

---

## Orchestrator (`anchor_mapper.py`)

### Public interface

```python
def generate_anchor_map(
    diff_result: DiffResult,
    subgoal_sequence: SubgoalSequence,
    source_code: str,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
) -> StructuralAnchorMap:
```

### Algorithm

1. Phase 1: `candidate_sets = analyze_call_graph(diff_result, subgoal_sequence, source_code)`
2. For each `CandidateSet` (one per subgoal):
   - If no candidates → skip LLM call, subgoal gets no anchors
   - Otherwise: call `client.messages.parse(output_format=FilterResult, ...)`
   - On `stop_reason == "refusal"` → raise `AnchorMappingError`
   - On `parsed_output is None` → raise `AnchorMappingError`
   - Collect `relevant_keys`, **discarding any key not present in the candidate set** (guards against LLM hallucinating non-existent keys)
3. Aggregate: `all_mappings: dict[str, set[int]]` — anchor_key → set of subgoal indices
4. Build `AnchorMapping` for each key, pulling metadata (line_number, anchor_type, branch_type, source_snippet) from DiffResult
5. Return `StructuralAnchorMap(task_name=..., file_path=..., mappings=[...])`
   - `mappings` may be empty if all candidates were filtered out — this is a valid return value

**Lazy model import:** `AnchorMappingError` is resolved from `sys.modules["models"]` at call time — same pattern as Stages 2 & 3. The guard:
```python
_cached = sys.modules.get("models")
if _cached and hasattr(_cached, "AnchorMappingError"):
    _m = _cached
else:
    if "models" in sys.modules:
        del sys.modules["models"]
    import models as _m
AnchorMappingError = _m.AnchorMappingError
```
Sentinel attribute: `"AnchorMappingError"`. `FilterResult` is imported directly from `prompt_builder` (no lazy import needed).

---

## Error Handling

| Condition | Behavior |
|---|---|
| `client=None` and no `ANTHROPIC_API_KEY` | `EnvironmentError` from `create_client()` |
| Claude `stop_reason == "refusal"` | `AnchorMappingError(stop_reason="refusal")` |
| `parsed_output is None` | `AnchorMappingError` |
| `anthropic.APIStatusError` | propagates to caller |
| Anchor hint matches no function in AST | conservative fallback (candidate for all subgoals) |
| Source code is empty or unparseable | `AnchorMappingError("Failed to parse source code")` |
| LLM returns a key not in the candidate set | silently discard (hallucination guard) |

---

## Testing Strategy

### `test_models.py`
- Instantiate `AnchorMapping` and `StructuralAnchorMap` with valid data
- `for_subgoal(index)` returns correct subset
- `to_dict()` returns serializable dict
- `AnchorMappingError` carries `stop_reason`
- `StructuralAnchorMap` with empty `mappings` is valid (no constraint violation)

### `test_call_graph_analyzer.py`
Uses an inline Python source string (no file I/O). Fixtures based on `math_calc_v2.py` content.
- Line-number hint `"42"` → resolves to the function containing line 42
- Line/branch hint `"42/if_true"` → resolves to the function containing line 42 (branch type ignored at Phase 1 — it's used to identify the anchor, not to restrict reachability)
- BFS follows call chain: A calls B calls C → C's anchors reachable from A's subgoal
- Anchor hint line falls in module-level code (no function) → conservative fallback (candidate for all subgoals)
- Anchor not reachable from any subgoal → conservative fallback (candidate for all subgoals)

### `test_prompt_builder.py`
- Prompt contains subgoal description, index, and rationale
- Each candidate anchor appears with its key, type, and source snippet
- Empty candidates → `build_prompt` does not crash, produces a valid (minimal) prompt string

### `test_anchor_mapper.py` (mock client)
**Import order (required):** Stage 1 models first (`DiffResult`, `ModifiedLine`, `ModifiedBranch`), then Stage 2 models (`SubgoalSequence`), then Stage 4 models last — so `sys.modules["models"]` = Stage 4 at call time. This mirrors the pattern in `test_reward_generator.py`.
- Returns `StructuralAnchorMap` on happy path
- `for_subgoal()` returns correct anchors after mock filter
- `messages.parse` called once per non-empty `CandidateSet`
- `stop_reason == "refusal"` → `AnchorMappingError`
- `parsed_output is None` → `AnchorMappingError`
- No client + no API key → `EnvironmentError`
- `use_thinking=True` → `thinking={"type": "adaptive"}` in kwargs
- `to_dict()` on result is serializable
- All candidate sets empty → returns `StructuralAnchorMap` with empty `mappings`, no LLM calls made
- LLM returns hallucinated key → key silently discarded, does not appear in output

### `test_integration.py` (skipped without API key)
Uses `math_calc_v2.py` source + synthetic `SubgoalSequence` + real Claude call.
- Result is `StructuralAnchorMap`
- At least one subgoal has at least one mapped anchor (not asserting all subgoals — LLM may legitimately map zero anchors to some)
- `to_dict()` is serializable
- `for_subgoal(index)` does not raise for any valid subgoal index

---

## Module Identity / `sys.modules` Strategy

Same pattern as Stages 2 & 3:
- **Test files**: load Stage 1 models first (`DiffResult`, `ModifiedLine`, `ModifiedBranch`), then Stage 4 models last — so `sys.modules["models"]` = Stage 4 at call time
- **`anchor_mapper.py`**: lazy import of `AnchorMappingError` inside `generate_anchor_map()` — resolves from `sys.modules["models"]` at call time
- **`prompt_builder.py`**: `FilterResult` is defined directly in `prompt_builder.py` — no `sys.modules` management needed; import Stage 4 `CandidateSet` from `models` with the same conditional-reload guard used in Stage 3 (`hasattr(cached, "CandidateSet")`)

---

## Dependencies

- Python 3.9+ (`ast.unparse` needs 3.9+; `from __future__ import annotations` used throughout for type hint compatibility)
- `pydantic` v2
- `anthropic` SDK
- No new third-party dependencies

## Interfaces with Other Stages

| Stage | Consumed by Stage 4 |
|---|---|
| Stage 1 (`DiffResult`) | Source of all structural anchors C_L, C_B |
| Stage 2 (`SubgoalSequence`) | Source of subgoals and anchor_hints |

| Stage | Consumes Stage 4 output |
|---|---|
| Stage 5 | Uses `StructuralAnchorMap.for_subgoal(j)` to gate structural rewards |
