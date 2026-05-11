# Stage 3: Reward Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `reward_generator/` — a sibling package to `subgoal_generator/` that accepts a `SubgoalSequence` + `ObservationSchema` and calls the Claude API once to produce a validated `RewardRuleSet`.

**Architecture:** Five phases matching the Stage 2 pattern (models → client_factory → prompt_builder → reward_generator → integration test). Each phase has its own test file; a phase must pass before the next begins. The package uses `sys.path` insertion for cross-stage imports, clearing `sys.modules["models"]` to avoid name collisions between Stage 1 and Stage 2 `models.py` files.

**Tech Stack:** Python 3.9+, Pydantic v2, anthropic SDK (`messages.parse(output_format=...)`), pytest, `from __future__ import annotations` for PEP 604 union syntax compatibility.

---

## File Structure

```
smart/reward_generator/
├── models.py                    # Phase 1: Pydantic models + RewardGenerationError
├── client_factory.py            # Phase 2: Anthropic client creation (copy of S2 pattern)
├── prompt_builder.py            # Phase 3: SubgoalSequence + ObservationSchema → prompt
├── reward_generator.py          # Phase 4: API call + parse → RewardRuleSet
└── tests/
    ├── __init__.py              # empty (created in scaffold task)
    ├── test_models.py           # Phase 1 tests
    ├── test_client_factory.py   # Phase 2 tests
    ├── test_prompt_builder.py   # Phase 3 tests
    ├── test_reward_generator.py # Phase 4 tests (mock client)
    └── test_integration.py      # Phase 5 (real API, skipped if no key)
```

**Critical:** Do NOT create a `reward_generator/__init__.py`. If one exists, it will make `from reward_generator import generate_reward_rules` import the package instead of the module, causing an import error.

---

## Task 1: Scaffold the package

**Files:**
- Create: `smart/reward_generator/` (directory)
- Create: `smart/reward_generator/tests/__init__.py`

- [ ] **Step 1: Create directories and empty test init**

```bash
cd /Users/xd/Desktop/codes/smart
mkdir -p reward_generator/tests
touch reward_generator/tests/__init__.py
```

- [ ] **Step 2: Verify structure**

```bash
ls reward_generator/
ls reward_generator/tests/
```

Expected: `tests/` in reward_generator; `__init__.py` in tests/

- [ ] **Step 3: Confirm no `reward_generator/__init__.py` exists**

```bash
ls reward_generator/__init__.py 2>/dev/null && echo "ERROR: must remove this" || echo "OK: no __init__.py"
```

Expected: `OK: no __init__.py`

---

## Task 2: Phase 1 — Data Models

**Files:**
- Create: `smart/reward_generator/models.py`
- Create: `smart/reward_generator/tests/test_models.py`

### Step 2.1: Write the failing tests

- [ ] **Step 1: Create `tests/test_models.py`**

```python
"""Phase 1 tests: Pydantic models and RewardGenerationError."""
import pytest
from pydantic import ValidationError

import sys, os
# Clear any cached 'models' from other stages
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import (
    RewardGenerationError,
    ObservableVariable,
    ObservationSchema,
    RewardEvent,
    RewardRule,
    RewardRuleSet,
)


class TestRewardGenerationError:
    def test_is_exception(self):
        err = RewardGenerationError("Something went wrong")
        assert isinstance(err, Exception)

    def test_message_accessible(self):
        err = RewardGenerationError("bad response", stop_reason="refusal")
        assert str(err) == "bad response"
        assert err.stop_reason == "refusal"

    def test_default_stop_reason_none(self):
        err = RewardGenerationError("oops")
        assert err.stop_reason is None

    def test_can_be_raised_and_caught(self):
        with pytest.raises(RewardGenerationError) as exc_info:
            raise RewardGenerationError("fail", stop_reason="refusal")
        assert exc_info.value.stop_reason == "refusal"


class TestObservableVariable:
    def test_valid_instantiation(self):
        v = ObservableVariable(name="oven_state", type="'raw'|'baking'|'done'", description="Oven status")
        assert v.name == "oven_state"

    def test_name_min_length(self):
        with pytest.raises(ValidationError):
            ObservableVariable(name="", type="int", description="d")

    def test_type_min_length(self):
        with pytest.raises(ValidationError):
            ObservableVariable(name="x", type="", description="d")

    def test_description_min_length(self):
        with pytest.raises(ValidationError):
            ObservableVariable(name="x", type="int", description="")


class TestObservationSchema:
    def test_valid_instantiation(self):
        schema = ObservationSchema(variables=[
            ObservableVariable(name="score", type="int", description="Current score")
        ])
        assert len(schema.variables) == 1

    def test_variables_min_length(self):
        with pytest.raises(ValidationError):
            ObservationSchema(variables=[])


class TestRewardEvent:
    def test_valid_instantiation(self):
        ev = RewardEvent(
            event="place_pizza",
            condition="inventory contains 'pizza'",
            reward=1.0,
            description="Player placed pizza in oven",
        )
        assert ev.reward == 1.0

    def test_event_min_length(self):
        with pytest.raises(ValidationError):
            RewardEvent(event="", condition="c", reward=1.0, description="d")

    def test_condition_min_length(self):
        with pytest.raises(ValidationError):
            RewardEvent(event="e", condition="", reward=1.0, description="d")

    def test_description_min_length(self):
        with pytest.raises(ValidationError):
            RewardEvent(event="e", condition="c", reward=1.0, description="")


class TestRewardRule:
    def _make_rule(self):
        return RewardRule(
            subgoal_index=1,
            subgoal_description="Pick up an ingredient",
            events=[
                RewardEvent(event="grab_item", condition="player near item", reward=5.0,
                            description="Player grabbed item")
            ],
        )

    def test_valid_instantiation(self):
        rule = self._make_rule()
        assert rule.subgoal_index == 1

    def test_subgoal_index_ge_1(self):
        with pytest.raises(ValidationError):
            RewardRule(
                subgoal_index=0,
                subgoal_description="x" * 5,
                events=[RewardEvent(event="e", condition="c", reward=1.0, description="d")],
            )

    def test_subgoal_description_min_length(self):
        with pytest.raises(ValidationError):
            RewardRule(
                subgoal_index=1,
                subgoal_description="hi",
                events=[RewardEvent(event="e", condition="c", reward=1.0, description="d")],
            )

    def test_events_min_length(self):
        with pytest.raises(ValidationError):
            RewardRule(subgoal_index=1, subgoal_description="Do something", events=[])


class TestRewardRuleSet:
    def _make_ruleset(self):
        return RewardRuleSet(
            task_name="Pizza Quest",
            rules=[
                RewardRule(
                    subgoal_index=1,
                    subgoal_description="Pick up ingredient",
                    events=[RewardEvent(event="grab", condition="near item", reward=5.0, description="grabbed")],
                )
            ],
        )

    def test_valid_instantiation(self):
        rs = self._make_ruleset()
        assert rs.task_name == "Pizza Quest"
        assert len(rs.rules) == 1

    def test_task_name_min_length(self):
        with pytest.raises(ValidationError):
            RewardRuleSet(task_name="", rules=[
                RewardRule(
                    subgoal_index=1,
                    subgoal_description="Do something",
                    events=[RewardEvent(event="e", condition="c", reward=1.0, description="d")],
                )
            ])

    def test_rules_min_length(self):
        with pytest.raises(ValidationError):
            RewardRuleSet(task_name="T", rules=[])

    def test_to_dict_returns_dict(self):
        rs = self._make_ruleset()
        d = rs.to_dict()
        assert isinstance(d, dict)
        assert "rules" in d
        assert len(d["rules"]) == 1

    def test_to_dict_contains_events(self):
        rs = self._make_ruleset()
        d = rs.to_dict()
        assert "events" in d["rules"][0]
```

- [ ] **Step 2: Run tests — expect ImportError (models.py doesn't exist yet)**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_models.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError` for `models`

### Step 2.2: Implement models.py

- [ ] **Step 3: Create `models.py`**

```python
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
```

- [ ] **Step 4: Run tests — expect all PASS**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_models.py -v
```

Expected: all green

---

## Task 3: Phase 2 — Client Factory

**Files:**
- Create: `smart/reward_generator/client_factory.py`
- Create: `smart/reward_generator/tests/test_client_factory.py`

- [ ] **Step 1: Create `tests/test_client_factory.py`**

```python
"""Phase 2 tests: Anthropic client factory."""
import os
import pytest
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client_factory import create_client


class TestCreateClient:
    def test_raises_env_error_when_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
                create_client()

    def test_raises_env_error_explicit_message(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError) as exc_info:
                create_client()
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_accepts_explicit_api_key(self):
        import anthropic
        client = create_client(api_key="sk-test-key")
        assert isinstance(client, anthropic.Anthropic)

    def test_reads_env_var(self):
        import anthropic
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
            client = create_client()
            assert isinstance(client, anthropic.Anthropic)

    def test_explicit_key_takes_precedence(self):
        import anthropic
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
            client = create_client(api_key="sk-explicit-key")
            assert isinstance(client, anthropic.Anthropic)
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_client_factory.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError` for `client_factory`

- [ ] **Step 3: Create `client_factory.py`**

```python
import os
from typing import Optional
import anthropic


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

- [ ] **Step 4: Run tests — expect all PASS**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_client_factory.py -v
```

Expected: all green

---

## Task 4: Phase 3 — Prompt Builder

**Files:**
- Create: `smart/reward_generator/prompt_builder.py`
- Create: `smart/reward_generator/tests/test_prompt_builder.py`

- [ ] **Step 1: Create `tests/test_prompt_builder.py`**

The prompt builder takes a `SubgoalSequence` (Stage 2 type) and `ObservationSchema` (Stage 3 type). The test file imports Stage 2 models via sys.path, then Stage 3 models.

```python
"""Phase 3 tests: SubgoalSequence + ObservationSchema → prompt string."""
import os, sys
import pytest

# ── Stage 2 imports ──────────────────────────────────────────────────────────
# Clear any cached 'models' from Stage 1 first
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator"))
from models import Subgoal, SubgoalSequence

# ── Stage 3 imports ──────────────────────────────────────────────────────────
# Clear Stage 2 'models' cache before loading Stage 3 models
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import ObservableVariable, ObservationSchema
from prompt_builder import build_prompt


def make_subgoal_sequence() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Pizza Quest",
        summary="Player assembles and delivers an onion pizza.",
        subgoals=[
            Subgoal(index=1, description="Obtain and chop a tomato", rationale="line 45"),
            Subgoal(index=2, description="Place pizza in the oven", rationale="line 52",
                    anchor_hints=["52/if_true"]),
        ],
    )


def make_observation_schema() -> ObservationSchema:
    return ObservationSchema(variables=[
        ObservableVariable(name="inventory", type="list[str]", description="Items the player carries"),
        ObservableVariable(name="oven_state", type="'raw'|'baking'|'done'", description="State of the oven"),
        ObservableVariable(name="score", type="int", description="Current score"),
    ])


class TestBuildPromptStructure:
    def test_returns_string(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert isinstance(prompt, str)

    def test_contains_task_name(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Pizza Quest" in prompt

    def test_contains_subgoal_description(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Obtain and chop a tomato" in prompt

    def test_contains_subgoal_index(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "1" in prompt

    def test_contains_rationale(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "line 45" in prompt

    def test_contains_anchor_hints(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "52/if_true" in prompt

    def test_contains_observation_variable_names(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "inventory" in prompt
        assert "oven_state" in prompt
        assert "score" in prompt

    def test_contains_variable_types(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "list[str]" in prompt

    def test_contains_variable_descriptions(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Items the player carries" in prompt

    def test_contains_reward_rules_instructions(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        # Must include instructions about reward rules
        assert "RewardRuleSet" in prompt or "reward" in prompt.lower()

    def test_contains_subgoal_section_header(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "SUBGOAL" in prompt.upper()

    def test_contains_observation_section_header(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "OBSERVATION" in prompt.upper() or "SCHEMA" in prompt.upper()

    def test_prompt_non_empty(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert len(prompt) > 100

    def test_subgoal_index_match_instruction(self):
        """Prompt must tell the LLM that subgoal_index must match the subgoal index."""
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "subgoal_index" in prompt or "index" in prompt

    def test_both_subgoals_present(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Place pizza in the oven" in prompt
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_prompt_builder.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError` for `prompt_builder`

- [ ] **Step 3: Create `prompt_builder.py`**

```python
from __future__ import annotations
import sys, os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Runtime imports for Stage 2 models — manage sys.modules to avoid collision
# We import Stage 2 SubgoalSequence at runtime because prompt_builder is called at runtime.
# We resolve the path relative to this file.
_S2_PATH = os.path.join(os.path.dirname(__file__), "..", "subgoal_generator")
if _S2_PATH not in sys.path:
    sys.path.insert(0, _S2_PATH)

# We must manage the 'models' module cache carefully.
# Stage 3 models.py may already be cached as 'models'. We need Stage 2 models here.
# Strategy: import Stage 2 models directly by manipulating the cache.
import importlib

def _import_stage2_models():
    """Import SubgoalSequence from Stage 2, handling sys.modules cache."""
    cached = sys.modules.get("models")
    # Temporarily remove so importlib loads from the S2 path
    if cached is not None:
        del sys.modules["models"]
    try:
        import models as _m2
        SubgoalSequence = _m2.SubgoalSequence
    finally:
        # Restore whatever was there (could be S3 models)
        if cached is not None:
            sys.modules["models"] = cached
        elif "models" in sys.modules:
            del sys.modules["models"]
    return SubgoalSequence


# Import Stage 3 models (ObservationSchema)
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.dirname(__file__))
from models import ObservationSchema


def build_prompt(subgoal_sequence, observation_schema: ObservationSchema) -> str:
    """
    Build the prompt for the LLM to generate a RewardRuleSet.

    Args:
        subgoal_sequence: SubgoalSequence from Stage 2.
        observation_schema: ObservationSchema describing game state variables.

    Returns:
        Formatted prompt string.
    """
    lines = [
        "You are a reinforcement learning reward engineer for a game testing system.",
        "Given the subgoal sequence and observable state variables below, generate",
        "a RewardRuleSet with one RewardRule per subgoal.",
        "",
        "Rules:",
        "1. Each RewardRule must have at least one RewardEvent.",
        "2. Conditions must only reference variables listed in the ObservationSchema.",
        "3. Use progressive rewards: small rewards for intermediate events,",
        "   large rewards for subgoal completion (typically 10x the intermediate reward).",
        "4. Conditions must be expressed as readable predicate strings (not code).",
        "5. subgoal_index must match the index field from the subgoal list exactly.",
        "",
        "=== SUBGOAL SEQUENCE ===",
        f"Task: {subgoal_sequence.task_name}",
        f"Summary: {subgoal_sequence.summary}",
    ]

    for sg in subgoal_sequence.subgoals:
        anchors = ", ".join(sg.anchor_hints) if sg.anchor_hints else "none"
        lines.append(f"{sg.index:>3}. {sg.description}")
        lines.append(f"     rationale: {sg.rationale}")
        lines.append(f"     anchors: {anchors}")

    lines.append("")
    lines.append("=== OBSERVATION SCHEMA ===")

    for var in observation_schema.variables:
        lines.append(f"{var.name}: {var.type} — {var.description}")

    lines.append("=== END ===")
    lines.append("")
    lines.append("Respond with a valid RewardRuleSet JSON object.")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — expect all PASS**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_prompt_builder.py -v
```

Expected: all green

---

## Task 5: Phase 4 — Reward Generator (mock client)

**Files:**
- Create: `smart/reward_generator/reward_generator.py`
- Create: `smart/reward_generator/tests/test_reward_generator.py`

- [ ] **Step 1: Create `tests/test_reward_generator.py`**

```python
"""Phase 4 tests: reward_generator with mock Anthropic client."""
import os, sys
import pytest
from unittest.mock import MagicMock

# ── Stage 2 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator"))
from models import Subgoal, SubgoalSequence

# ── Stage 3 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import (
    ObservableVariable, ObservationSchema,
    RewardEvent, RewardRule, RewardRuleSet,
    RewardGenerationError,
)
from reward_generator import generate_reward_rules


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_subgoal_sequence() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Test Task",
        summary="A test task with two steps.",
        subgoals=[
            Subgoal(index=1, description="Do the first thing", rationale="line 10"),
            Subgoal(index=2, description="Do the second thing", rationale="line 20"),
        ],
    )


def make_observation_schema() -> ObservationSchema:
    return ObservationSchema(variables=[
        ObservableVariable(name="score", type="int", description="Player score"),
    ])


def make_reward_rule_set() -> RewardRuleSet:
    return RewardRuleSet(
        task_name="Test Task",
        rules=[
            RewardRule(
                subgoal_index=1,
                subgoal_description="Do the first thing",
                events=[RewardEvent(event="step1", condition="score > 0", reward=1.0,
                                    description="First step done")],
            ),
            RewardRule(
                subgoal_index=2,
                subgoal_description="Do the second thing",
                events=[RewardEvent(event="step2", condition="score > 10", reward=10.0,
                                    description="Second step done")],
            ),
        ],
    )


def make_mock_client(reward_rule_set: RewardRuleSet, stop_reason: str = "end_turn") -> MagicMock:
    mock_response = MagicMock()
    mock_response.parsed_output = reward_rule_set
    mock_response.stop_reason = stop_reason
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client


# ── Tests ────────────────────────────────────────────────────────────────────

class TestGenerateRewardRulesHappyPath:
    def test_returns_reward_rule_set(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        result = generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert isinstance(result, RewardRuleSet)

    def test_rules_preserved(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        result = generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert len(result.rules) == 2

    def test_calls_messages_parse(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert client.messages.parse.called

    def test_passes_model_to_api(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(),
                               client=client, model="claude-opus-4-6")
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("model") == "claude-opus-4-6"

    def test_passes_output_format(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("output_format") is RewardRuleSet

    def test_uses_thinking_when_requested(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(),
                               client=client, use_thinking=True)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("thinking") == {"type": "adaptive"}

    def test_no_thinking_by_default(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert "thinking" not in call_kwargs

    def test_to_dict_on_result(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        result = generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert len(d["rules"]) == 2


class TestGenerateRewardRulesErrorHandling:
    def test_refusal_raises_error(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs, stop_reason="refusal")
        with pytest.raises(RewardGenerationError) as exc_info:
            generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert exc_info.value.stop_reason == "refusal"

    def test_none_parsed_output_raises_error(self):
        mock_response = MagicMock()
        mock_response.parsed_output = None
        mock_response.stop_reason = "end_turn"
        mock_client = MagicMock()
        mock_client.messages.parse.return_value = mock_response
        with pytest.raises(RewardGenerationError):
            generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=mock_client)

    def test_api_error_propagates(self):
        import anthropic
        mock_client = MagicMock()
        mock_client.messages.parse.side_effect = anthropic.APIStatusError(
            message="server error",
            response=MagicMock(status_code=500),
            body={},
        )
        with pytest.raises(anthropic.APIStatusError):
            generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=mock_client)


class TestGenerateRewardRulesClientFactory:
    def test_no_client_raises_env_error_when_no_key(self):
        """When client=None and no API key set, EnvironmentError from factory."""
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError):
                generate_reward_rules(make_subgoal_sequence(), make_observation_schema())
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_reward_generator.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError` for `reward_generator`

- [ ] **Step 3: Create `reward_generator.py`**

```python
from __future__ import annotations
import os, sys
from typing import Optional
import anthropic

# Stage 3 models — load first (clear any stale cache)
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.dirname(__file__))
from models import ObservationSchema, RewardRuleSet, RewardGenerationError
from client_factory import create_client
from prompt_builder import build_prompt


def generate_reward_rules(
    subgoal_sequence,
    observation_schema: ObservationSchema,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
) -> RewardRuleSet:
    """
    Generate reward rules for a subgoal sequence using the Claude API.

    Args:
        subgoal_sequence: SubgoalSequence from Stage 2.
        observation_schema: ObservationSchema describing game state variables.
        client: Anthropic client. If None, creates one using ANTHROPIC_API_KEY.
        model: Claude model to use.
        max_tokens: Maximum tokens for the response.
        use_thinking: If True, enables adaptive thinking.

    Returns:
        Validated RewardRuleSet Pydantic object.

    Raises:
        RewardGenerationError: If Claude refuses or returns an invalid response.
        EnvironmentError: If no API key is available and client is None.
    """
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

- [ ] **Step 4: Run tests — expect all PASS**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_reward_generator.py -v
```

Expected: all green

---

## Task 6: Phase 5 — Integration Test

**Files:**
- Create: `smart/reward_generator/tests/test_integration.py`

- [ ] **Step 1: Create `tests/test_integration.py`**

```python
"""
Phase 5: Integration test — real Claude API call.
Skipped automatically when ANTHROPIC_API_KEY is not set.
Run with: pytest tests/test_integration.py -v -s
"""
import os, sys
import pytest

# ── Stage 2 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator"))
from models import Subgoal, SubgoalSequence

# ── Stage 3 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import ObservableVariable, ObservationSchema, RewardRuleSet
from reward_generator import generate_reward_rules

needs_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API integration test",
)


def make_math_calc_subgoal_sequence() -> SubgoalSequence:
    """Synthetic subgoal sequence based on math calculator additions."""
    return SubgoalSequence(
        task_name="Math Calculator Extended",
        summary="Player uses the calculator to perform matrix operations and complex arithmetic.",
        subgoals=[
            Subgoal(
                index=1,
                description="Open the matrix calculator interface",
                rationale="MatrixCalculator class added in v2",
                anchor_hints=["MatrixCalculator"],
            ),
            Subgoal(
                index=2,
                description="Perform a determinant calculation on a 2x2 matrix",
                rationale="determinant method handles singular check",
                anchor_hints=["determinant/if_true"],
            ),
            Subgoal(
                index=3,
                description="Apply Taylor series expansion to a function",
                rationale="taylor_series function added in v2",
                anchor_hints=["taylor_series"],
            ),
        ],
    )


def make_math_calc_schema() -> ObservationSchema:
    """Observable variables for the math calculator game environment."""
    return ObservationSchema(variables=[
        ObservableVariable(
            name="calculator_mode",
            type="'basic'|'matrix'|'complex'|'calculus'",
            description="Current mode of the calculator",
        ),
        ObservableVariable(
            name="last_result",
            type="float | None",
            description="Result of the most recent calculation",
        ),
        ObservableVariable(
            name="operations_count",
            type="int",
            description="Number of operations performed so far",
        ),
        ObservableVariable(
            name="error_state",
            type="bool",
            description="True if the last operation raised an error",
        ),
    ])


@needs_key
def test_math_calc_produces_valid_reward_rules():
    """End-to-end: synthetic SubgoalSequence + ObservationSchema → RewardRuleSet."""
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    assert isinstance(result, RewardRuleSet)
    assert len(result.rules) == len(seq.subgoals)
    assert all(len(r.events) >= 1 for r in result.rules)


@needs_key
def test_math_calc_subgoal_indices_match():
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    expected_indices = {sg.index for sg in seq.subgoals}
    actual_indices = {r.subgoal_index for r in result.rules}
    assert actual_indices == expected_indices


@needs_key
def test_math_calc_conditions_reference_schema_variables():
    """Conditions should reference variables from the observation schema."""
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    variable_names = {v.name for v in schema.variables}
    all_conditions = " ".join(
        ev.condition for rule in result.rules for ev in rule.events
    )
    # At least one schema variable must appear in conditions
    assert any(v in all_conditions for v in variable_names), (
        f"No schema variable found in conditions. Conditions: {all_conditions[:300]}"
    )


@needs_key
def test_math_calc_to_dict_serializable():
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "rules" in d
    assert len(d["rules"]) == len(seq.subgoals)


@needs_key
def test_math_calc_prints_readable_report(capsys):
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    print(f"\n{'='*60}")
    print(f"SMART Stage 3 — Reward Rule Report")
    print(f"Task: {result.task_name}")
    print(f"{'='*60}")
    for rule in result.rules:
        print(f"  [{rule.subgoal_index}] {rule.subgoal_description}")
        for ev in rule.events:
            print(f"       event: {ev.event} | reward: {ev.reward}")
            print(f"       cond:  {ev.condition}")
    print(f"{'='*60}")
    captured = capsys.readouterr()
    assert "Stage 3" in captured.out
```

- [ ] **Step 2: Run tests — should SKIP (no key) or PASS (key set)**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/test_integration.py -v
```

Expected: all tests skipped (if no key) OR all passed (if key set)

---

## Task 7: Full Regression

Run all Stage 3 tests, then verify Stage 1 and Stage 2 still pass.

- [ ] **Step 1: Run full Stage 3 test suite**

```bash
cd /Users/xd/Desktop/codes/smart/reward_generator
python -m pytest tests/ -v
```

Expected: all green (integration tests skipped if no key)

- [ ] **Step 2: Run Stage 2 regression**

```bash
cd /Users/xd/Desktop/codes/smart/subgoal_generator
python -m pytest tests/ -v
```

Expected: all green

- [ ] **Step 3: Run Stage 1 regression**

```bash
cd /Users/xd/Desktop/codes/smart/ast_diff_parser
python -m pytest tests/ -v
```

Expected: all green
