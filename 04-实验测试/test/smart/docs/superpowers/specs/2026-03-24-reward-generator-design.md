# Stage 3: Reward Generator — Design Spec

**Date:** 2026-03-24
**Status:** Draft
**Builds on:** `subgoal_generator/` (Stage 2), `ast_diff_parser/` (Stage 1)

---

## Context

SMART Stage 3 consumes the `SubgoalSequence` from Stage 2 and an `ObservationSchema` describing the game environment's observable state variables. It calls the Claude API once to produce a `RewardRuleSet` — one `RewardRule` per subgoal — that Stage 5 uses to compute semantic rewards during RL training.

---

## Goals

- Accept `SubgoalSequence` (Stage 2 Pydantic model) and `ObservationSchema` as sole inputs
- Produce a typed, validated `RewardRuleSet` (Pydantic v2)
- Fully testable without a real API key (mock-injectable client)
- Support optional adaptive thinking
- Phase-by-phase approach: each phase must pass its own tests before the next begins

## Non-Goals

- Does not call Stage 4 or downstream stages
- Does not persist results to disk
- Does not validate reward rules against a live game environment

---

## Cross-Stage Import Strategy

Stage 3 is a sibling package to `subgoal_generator/` and `ast_diff_parser/`. Each test file and source module that needs Stage 2 types resolves them via `sys.path`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator"))
from models import SubgoalSequence, Subgoal
```

Because both `ast_diff_parser/models.py` and `subgoal_generator/models.py` share the filename `models.py`, test files must explicitly manage `sys.modules["models"]` (clearing the cache between stage imports) to prevent collision — the same pattern established in Stage 2.

---

## Architecture

### Module Layout

```
reward_generator/
├── models.py               # Phase 1 — Pydantic models + RewardGenerationError
├── client_factory.py       # Phase 2 — Anthropic client creation (independent copy)
├── prompt_builder.py       # Phase 3 — SubgoalSequence + ObservationSchema → prompt
├── reward_generator.py     # Phase 4 — API call + parse
└── tests/
    ├── __init__.py
    ├── test_models.py           # Phase 1
    ├── test_client_factory.py   # Phase 2
    ├── test_prompt_builder.py   # Phase 3
    ├── test_reward_generator.py # Phase 4 — mock client, no real API
    └── test_integration.py      # Phase 5 — real API, skipped if no key
```

`client_factory.py` is an independent copy of the Stage 2 pattern — not imported from `subgoal_generator/`. This keeps stages fully decoupled.

### Data Flow

```
SubgoalSequence (Stage 2)  +  ObservationSchema
          │
          ▼  prompt_builder.build_prompt(seq, schema)
          │
          ▼  reward_generator.generate_reward_rules(seq, schema, client)
                 └─ client_factory.create_client()  [if client is None]
                 └─ client.messages.parse(output_format=RewardRuleSet)
          ▼
RewardRuleSet  ←  validated Pydantic object
```

---

## Phase 1: Data Models (`models.py`)

### `RewardGenerationError`

```python
from __future__ import annotations
from typing import Optional

class RewardGenerationError(Exception):
    """Raised when the LLM fails to produce a valid RewardRuleSet."""
    def __init__(self, message: str, stop_reason: Optional[str] = None):
        super().__init__(message)
        self.stop_reason = stop_reason
```

Note: `from __future__ import annotations` must be the first statement in `models.py` to enable PEP 604 union syntax (`X | Y`) as string literals on Python 3.9.

### `ObservableVariable`

```python
class ObservableVariable(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1, description="e.g. 'list[str]', 'int', \"'raw'|'baking'|'done'\"")
    description: str = Field(..., min_length=1)
```

### `ObservationSchema`

```python
class ObservationSchema(BaseModel):
    variables: list[ObservableVariable] = Field(..., min_length=1)
```

### `RewardEvent`

```python
class RewardEvent(BaseModel):
    event: str = Field(..., min_length=1, description="Short event name, e.g. 'place_raw_pizza_in_oven'")
    condition: str = Field(..., min_length=1, description="Readable predicate using only ObservationSchema variables")
    reward: float = Field(..., description="Reward magnitude (positive)")
    description: str = Field(..., min_length=1, description="Human-readable explanation")
```

### `RewardRule`

```python
class RewardRule(BaseModel):
    subgoal_index: int = Field(..., ge=1, description="Matches Subgoal.index from Stage 2")
    subgoal_description: str = Field(..., min_length=5)
    events: list[RewardEvent] = Field(..., min_length=1)
```

### `RewardRuleSet`

```python
class RewardRuleSet(BaseModel):
    task_name: str = Field(..., min_length=1)
    rules: list[RewardRule] = Field(..., min_length=1)

    def to_dict(self) -> dict:
        return self.model_dump()
```

---

## Phase 2: Client Factory (`client_factory.py`)

Identical interface to Stage 2:

```python
def create_client(api_key: Optional[str] = None) -> anthropic.Anthropic:
    """
    Create an Anthropic client.

    Args:
        api_key: Explicit API key. If None, reads ANTHROPIC_API_KEY env var.

    Returns:
        anthropic.Anthropic instance with SDK-default retry behaviour
        (max_retries=2, exponential backoff on 429 and 5xx).

    Raises:
        EnvironmentError: if no API key is available.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Pass api_key= explicitly or export ANTHROPIC_API_KEY before running."
        )
    return anthropic.Anthropic(api_key=key)
```

---

## Phase 3: Prompt Builder (`prompt_builder.py`)

### Public API

```python
def build_prompt(
    subgoal_sequence: SubgoalSequence,
    observation_schema: ObservationSchema,
) -> str
```

### Prompt structure

```
You are a reinforcement learning reward engineer for a game testing system.
Given the subgoal sequence and observable state variables below, generate
a RewardRuleSet with one RewardRule per subgoal.

Rules:
1. Each RewardRule must have at least one RewardEvent.
2. Conditions must only reference variables listed in the ObservationSchema.
3. Use progressive rewards: small rewards for intermediate events,
   large rewards for subgoal completion (typically 10x the intermediate reward).
4. Conditions must be expressed as readable predicate strings (not code).
5. subgoal_index must match the index field from the subgoal list exactly.

=== SUBGOAL SEQUENCE ===
Task: {task_name}
Summary: {summary}
{index:>3}. {description}
     rationale: {rationale}
     anchors: {anchor_hints or 'none'}
...

=== OBSERVATION SCHEMA ===
{name}: {type} — {description}
...
=== END ===

Respond with a valid RewardRuleSet JSON object.
```

---

## Phase 4: Reward Generator (`reward_generator.py`)

### Public API

```python
def generate_reward_rules(
    subgoal_sequence: SubgoalSequence,
    observation_schema: ObservationSchema,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
) -> RewardRuleSet
```

### Implementation

```python
def generate_reward_rules(...) -> RewardRuleSet:
    if client is None:
        client = create_client()

    prompt = build_prompt(subgoal_sequence, observation_schema)

    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_format=RewardRuleSet,
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    response = client.messages.parse(**kwargs)

    if response.stop_reason == "refusal":
        raise RewardGenerationError(
            "Claude refused to generate reward rules.",
            stop_reason="refusal",
        )
    if response.parsed_output is None:
        raise RewardGenerationError(
            "Claude response did not parse to a valid RewardRuleSet.",
            stop_reason=response.stop_reason,
        )
    return response.parsed_output
```

### Retry policy

SDK default (`max_retries=2`) handles transient 429 and 5xx errors. No additional retry logic.

---

## Phase 5: Integration Test (`tests/test_integration.py`)

Skipped when `ANTHROPIC_API_KEY` is absent. Uses a hand-crafted `SubgoalSequence` + `ObservationSchema` based on the math calculator fixtures (no file I/O needed):

```python
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test"
)
def test_math_calc_produces_valid_reward_rules():
    """End-to-end: synthetic SubgoalSequence + ObservationSchema → RewardRuleSet."""
    seq = make_math_calc_subgoal_sequence()   # fixture helper
    schema = make_math_calc_schema()           # fixture helper
    result = generate_reward_rules(seq, schema)
    assert isinstance(result, RewardRuleSet)
    assert len(result.rules) == len(seq.subgoals)
    assert all(len(r.events) >= 1 for r in result.rules)
```

---

## Mock Pattern for Unit Tests

```python
def make_mock_client(reward_rule_set: RewardRuleSet) -> MagicMock:
    mock_response = MagicMock()
    mock_response.parsed_output = reward_rule_set
    mock_response.stop_reason = "end_turn"
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client
```

---

## Implementation Phases

| Phase | File | Tests | Pass Gate |
|-------|------|-------|-----------|
| 1 | `models.py` | `test_models.py` | Pydantic validation + error class importable |
| 2 | `client_factory.py` | `test_client_factory.py` | Missing key → `EnvironmentError`; valid key → client |
| 3 | `prompt_builder.py` | `test_prompt_builder.py` | Prompt contains subgoal text, variable names, rules instructions |
| 4 | `reward_generator.py` | `test_reward_generator.py` | Mock client; refusal + None → error; happy path |
| 5 | `test_integration.py` | real API (skipped if no key) | `RewardRuleSet` valid, one rule per subgoal |

---

## Dependencies

```
anthropic>=0.40.0     # messages.parse() with Pydantic output_format
pydantic>=2.0         # BaseModel, Field, model_dump()
pytest                # test runner
```

Already installed from Stage 2.

---

## Verification Commands

```bash
cd smart/reward_generator
pytest tests/test_models.py            # Phase 1
pytest tests/test_client_factory.py   # Phase 2
pytest tests/test_prompt_builder.py   # Phase 3
pytest tests/test_reward_generator.py # Phase 4
pytest tests/test_integration.py -v   # Phase 5 (needs ANTHROPIC_API_KEY)
pytest tests/                          # full regression
```
