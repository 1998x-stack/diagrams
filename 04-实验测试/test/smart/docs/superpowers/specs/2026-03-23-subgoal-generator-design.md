# Stage 2: Subgoal Generator — Design Spec

**Date:** 2026-03-23
**Status:** Approved
**Builds on:** `ast_diff_parser/` (Stage 1)

---

## Context

SMART Stage 2 consumes the `DiffResult` from Stage 1 and uses Claude API to decompose code changes into an ordered sequence of natural-language subgoals `S = (sg1, sg2, …, sgn)`. Each subgoal is verifiable, atomic, and traceable to specific structural anchors from Stage 1.

---

## Goals

- Accept `DiffResult` (Stage 1 dataclass) as sole domain input
- Produce a typed, validated `SubgoalSequence` (Pydantic v2)
- Fully testable without a real API key (mock-injectable client)
- Support optional adaptive thinking for deeper diff reasoning
- Phase-by-phase approach: each phase must pass its own tests before the next begins

## Non-Goals

- Does not call Stage 3 or downstream stages
- Does not persist results to disk
- Does not validate subgoals against a game environment

---

## Cross-Stage Import Strategy

Stage 2 is a sibling package to `ast_diff_parser/`. Both live under `smart/`. Tests and the generator resolve the Stage 1 import via `sys.path`:

```
smart/
├── ast_diff_parser/        # Stage 1
│   ├── models.py           # DiffResult, ModifiedLine, ModifiedBranch
│   └── diff_parser.py
└── subgoal_generator/      # Stage 2
    ├── models.py
    ├── prompt_builder.py
    ├── subgoal_generator.py
    ├── client_factory.py
    └── tests/
```

Each test file that needs Stage 1 types adds:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch
```

Stage 2 source modules (non-test) use the same `sys.path` pattern in their imports or assume the caller has set the path. A future packaging step (e.g., `pyproject.toml`) would replace this.

---

## Architecture

### Module Layout

```
subgoal_generator/
├── models.py               # Phase 1 — Pydantic models + SubgoalGenerationError
├── client_factory.py       # Phase 2 — Anthropic client creation
├── prompt_builder.py       # Phase 3 — DiffResult → prompt string
├── subgoal_generator.py    # Phase 4 — API call + parse
└── tests/
    ├── __init__.py
    ├── test_models.py           # Phase 1
    ├── test_client_factory.py   # Phase 2
    ├── test_prompt_builder.py   # Phase 3
    ├── test_subgoal_generator.py # Phase 4 — mock client, no real API
    └── test_integration.py      # Phase 5 — real API, skipped if no key
```

### Data Flow

```
DiffResult (Stage 1 dataclass)
    │
    ▼  prompt_builder.build_prompt(diff_result, max_lines=150)
    │
    ▼  subgoal_generator.generate_subgoals(diff_result, client)
    │       └─ client_factory.create_client()  [if client is None]
    │       └─ client.messages.parse(model, messages, output_format=SubgoalSequence)
    ▼
SubgoalSequence  ←  validated Pydantic object
```

---

## Phase 1: Data Models (`models.py`)

### `SubgoalGenerationError`

Defined in `models.py` (imported by all other modules):

```python
class SubgoalGenerationError(Exception):
    """Raised when the LLM fails to produce a valid SubgoalSequence."""
    def __init__(self, message: str, stop_reason: str | None = None):
        super().__init__(message)
        self.stop_reason = stop_reason
```

### `Subgoal`

```python
class Subgoal(BaseModel):
    index: int = Field(..., ge=1)
    description: str = Field(..., min_length=5)
    rationale: str = Field(..., description="Which C_L/C_B entries motivate this step")
    anchor_hints: list[str] = Field(
        default_factory=list,
        description=(
            "References to relevant structural anchors. "
            "Format: '<line_number>' for C_L or '<line_number>/<branch_type>' for C_B. "
            "Example: ['45', '67/if_true', '67/if_false']"
        )
    )
```

### `SubgoalSequence`

```python
class SubgoalSequence(BaseModel):
    task_name: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=10)
    subgoals: list[Subgoal] = Field(..., min_length=1)

    def to_dict(self) -> dict:
        return self.model_dump()
```

---

## Phase 2: Client Factory (`client_factory.py`)

```python
def create_client(api_key: str | None = None) -> anthropic.Anthropic:
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
            "Pass api_key= explicitly or export ANTHROPIC_API_KEY."
        )
    return anthropic.Anthropic(api_key=key)
    # SDK default: max_retries=2 (handles 429 and 5xx automatically)
```

---

## Phase 3: Prompt Builder (`prompt_builder.py`)

### Public API

```python
def build_prompt(diff_result: DiffResult, max_lines: int = 150) -> str
```

### Truncation behaviour

If `len(diff_result.modified_lines) > max_lines`, the prompt includes the first `max_lines` entries followed by:

```
... and {N} more lines (omitted to fit context window)
```

Branches (`C_B`) are never truncated — they are always included in full (branch counts are typically small).

### Prompt structure

```
You are a game testing engineer analyzing a Python code update.
Given the AST diff report below, decompose the changes into an
ordered sequence of verifiable gameplay subgoals.

Rules:
1. Each subgoal must describe one atomic, testable player action or game state change.
2. Subgoals must be ordered by logical dependency (earlier steps enable later ones).
3. Every subgoal must reference at least one entry in C_L or C_B via anchor_hints.
   Format anchor_hints as: '<line_number>' for C_L, '<line_number>/<branch_type>' for C_B.
4. Descriptions must be natural language, not code.

=== AST DIFF REPORT ===
File: {file_path}

--- Modified Lines (C_L): {total} entries (showing {shown}) ---
{line_number:>6} | {change_type:<8} | {source}
...

--- Modified Branches (C_B): {n} entries ---
{control_stmt_line:>6} | {branch_type:<12} | {condition_source}
...
=== END REPORT ===

Respond with a valid SubgoalSequence JSON object.
```

---

## Phase 4: Subgoal Generator (`subgoal_generator.py`)

### Public API

```python
def generate_subgoals(
    diff_result: DiffResult,
    client: anthropic.Anthropic | None = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
) -> SubgoalSequence
```

### Implementation

```python
def generate_subgoals(...) -> SubgoalSequence:
    if client is None:
        client = create_client()

    prompt = build_prompt(diff_result)

    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_format=SubgoalSequence,   # messages.parse() Pydantic integration
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    response = client.messages.parse(**kwargs)

    if response.stop_reason == "refusal":
        raise SubgoalGenerationError(
            "Claude refused to generate subgoals.", stop_reason="refusal"
        )
    if response.parsed_output is None:
        raise SubgoalGenerationError(
            "Claude response did not parse to a valid SubgoalSequence.",
            stop_reason=response.stop_reason,
        )
    return response.parsed_output
    # anthropic.APIStatusError is not caught — propagated to caller
```

### Retry policy

The Anthropic SDK default (`max_retries=2`) handles transient 429 and 5xx errors automatically. No additional retry logic is implemented at this layer. The client created by `create_client()` uses this default.

---

## Phase 5: Integration Test (`tests/test_integration.py`)

Skipped when `ANTHROPIC_API_KEY` is absent:

```python
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test"
)
def test_math_calc_diff_produces_valid_subgoals():
    """End-to-end: math_calc v1→v2 diff → SubgoalSequence via real Claude API."""
    result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(result)
    assert isinstance(seq, SubgoalSequence)
    assert len(seq.subgoals) >= 2
    descriptions = " ".join(s.description for s in seq.subgoals)
    assert any(kw in descriptions.lower() for kw in
               ["matrix", "complex", "taylor", "integrate", "derivative"])
```

---

## Mock Pattern for Unit Tests

```python
def make_mock_client(subgoal_seq: SubgoalSequence) -> MagicMock:
    mock_response = MagicMock()
    mock_response.parsed_output = subgoal_seq
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
| 3 | `prompt_builder.py` | `test_prompt_builder.py` | Prompt contains C_L, C_B, truncation works |
| 4 | `subgoal_generator.py` | `test_subgoal_generator.py` | Mock client; refusal + None → error; happy path |
| 5 | `test_integration.py` | real API (skipped if no key) | SubgoalSequence valid, subgoals reference diff content |

---

## Dependencies

```
anthropic>=0.40.0     # messages.parse() with Pydantic output_format
pydantic>=2.0         # BaseModel, Field, model_dump()
pytest                # test runner
```

Install:

```bash
pip install anthropic pydantic pytest
```

---

## Verification Commands

```bash
cd smart/subgoal_generator
pytest tests/test_models.py            # Phase 1
pytest tests/test_client_factory.py   # Phase 2
pytest tests/test_prompt_builder.py   # Phase 3
pytest tests/test_subgoal_generator.py # Phase 4
pytest tests/test_integration.py -v   # Phase 5 (needs ANTHROPIC_API_KEY)
pytest tests/                          # full regression
```
