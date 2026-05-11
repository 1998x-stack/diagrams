# Subgoal Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Stage 2 of the SMART framework — a module that takes a `DiffResult` from Stage 1 and calls the Claude API to produce an ordered `SubgoalSequence` of natural-language gameplay testing steps.

**Architecture:** Five focused modules (models → client_factory → prompt_builder → subgoal_generator → integration test), each independently testable. Unit tests use a mock Anthropic client; only the optional integration test makes real API calls.

**Tech Stack:** Python 3.9+, anthropic>=0.40.0, pydantic>=2.0, pytest

---

## File Map

| File | Role |
|------|------|
| `subgoal_generator/models.py` | Pydantic models + `SubgoalGenerationError` |
| `subgoal_generator/client_factory.py` | Create `anthropic.Anthropic` from env var |
| `subgoal_generator/prompt_builder.py` | `DiffResult` → structured prompt string |
| `subgoal_generator/subgoal_generator.py` | Call `client.messages.parse()`, return `SubgoalSequence` |
| `subgoal_generator/tests/__init__.py` | Empty marker |
| `subgoal_generator/tests/test_models.py` | Phase 1 tests |
| `subgoal_generator/tests/test_client_factory.py` | Phase 2 tests |
| `subgoal_generator/tests/test_prompt_builder.py` | Phase 3 tests |
| `subgoal_generator/tests/test_subgoal_generator.py` | Phase 4 tests (mock client) |
| `subgoal_generator/tests/test_integration.py` | Phase 5 tests (real API, skipped if no key) |

**sys.path note:** Every test file and every source module that needs Stage 1 types prepends `ast_diff_parser/` to `sys.path` using:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `smart/subgoal_generator/__init__.py` (empty)
- Create: `smart/subgoal_generator/tests/__init__.py` (empty)

- [ ] **Step 1: Create directories and empty init files**

```bash
cd /Users/xd/Desktop/codes/smart
mkdir -p subgoal_generator/tests
touch subgoal_generator/__init__.py subgoal_generator/tests/__init__.py
```

- [ ] **Step 2: Install dependencies**

```bash
pip3 install anthropic pydantic pytest
```

Expected: all three installed without error.

- [ ] **Step 3: Verify pytest can discover the package**

```bash
cd /Users/xd/Desktop/codes/smart/subgoal_generator
python3 -m pytest tests/ --collect-only 2>&1 | head -10
```

Expected: "no tests ran" (no test files yet) — no import errors.

---

## Task 2: Phase 1 — Data Models

**Files:**
- Create: `smart/subgoal_generator/models.py`
- Create: `smart/subgoal_generator/tests/test_models.py`

- [ ] **Step 1: Write the failing tests first**

Create `smart/subgoal_generator/tests/test_models.py`:

```python
"""Phase 1 tests: Pydantic models and SubgoalGenerationError."""
import pytest
from pydantic import ValidationError

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Subgoal, SubgoalSequence, SubgoalGenerationError


class TestSubgoal:
    def test_valid_instantiation(self):
        sg = Subgoal(index=1, description="Pick up an ingredient", rationale="Line 45 adds item pickup logic")
        assert sg.index == 1
        assert sg.anchor_hints == []

    def test_index_must_be_positive(self):
        with pytest.raises(ValidationError):
            Subgoal(index=0, description="step", rationale="r")

    def test_description_min_length(self):
        with pytest.raises(ValidationError):
            Subgoal(index=1, description="hi", rationale="r")

    def test_anchor_hints_default_empty(self):
        sg = Subgoal(index=1, description="Do something", rationale="r")
        assert sg.anchor_hints == []

    def test_anchor_hints_populated(self):
        sg = Subgoal(index=1, description="Do something", rationale="r",
                     anchor_hints=["45", "67/if_true"])
        assert len(sg.anchor_hints) == 2


class TestSubgoalSequence:
    def _make_seq(self):
        return SubgoalSequence(
            task_name="Pizza Quest",
            summary="Player assembles and delivers an onion pizza.",
            subgoals=[
                Subgoal(index=1, description="Obtain and chop a tomato", rationale="line 45"),
                Subgoal(index=2, description="Assemble the pizza base", rationale="line 52"),
            ]
        )

    def test_valid_instantiation(self):
        seq = self._make_seq()
        assert seq.task_name == "Pizza Quest"
        assert len(seq.subgoals) == 2

    def test_subgoals_min_length_one(self):
        with pytest.raises(ValidationError):
            SubgoalSequence(task_name="T", summary="A summary text here", subgoals=[])

    def test_summary_min_length(self):
        with pytest.raises(ValidationError):
            SubgoalSequence(task_name="T", summary="short", subgoals=[
                Subgoal(index=1, description="Do something", rationale="r")
            ])

    def test_to_dict_returns_dict(self):
        seq = self._make_seq()
        d = seq.to_dict()
        assert isinstance(d, dict)
        assert "subgoals" in d
        assert len(d["subgoals"]) == 2

    def test_to_dict_subgoal_keys(self):
        seq = self._make_seq()
        d = seq.to_dict()
        first = d["subgoals"][0]
        assert "index" in first
        assert "description" in first
        assert "anchor_hints" in first


class TestSubgoalGenerationError:
    def test_is_exception(self):
        err = SubgoalGenerationError("Something went wrong")
        assert isinstance(err, Exception)

    def test_message_accessible(self):
        err = SubgoalGenerationError("bad response", stop_reason="refusal")
        assert str(err) == "bad response"
        assert err.stop_reason == "refusal"

    def test_default_stop_reason_none(self):
        err = SubgoalGenerationError("oops")
        assert err.stop_reason is None

    def test_can_be_raised_and_caught(self):
        with pytest.raises(SubgoalGenerationError) as exc_info:
            raise SubgoalGenerationError("fail", stop_reason="refusal")
        assert exc_info.value.stop_reason == "refusal"
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
cd /Users/xd/Desktop/codes/smart/subgoal_generator
python3 -m pytest tests/test_models.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError: No module named 'models'`

- [ ] **Step 3: Implement `models.py`**

Create `smart/subgoal_generator/models.py`:

```python
"""
SMART Framework - Stage 2: Subgoal Generator
Data models: SubgoalGenerationError, Subgoal, SubgoalSequence.
"""
from __future__ import annotations
from pydantic import BaseModel, Field


class SubgoalGenerationError(Exception):
    """Raised when the LLM fails to produce a valid SubgoalSequence."""

    def __init__(self, message: str, stop_reason: str | None = None):
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
```

- [ ] **Step 4: Run tests — verify they PASS**

```bash
python3 -m pytest tests/test_models.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/codes/smart
git add subgoal_generator/models.py subgoal_generator/tests/test_models.py
git commit -m "feat(stage2): Phase 1 — Pydantic models and SubgoalGenerationError"
```

---

## Task 3: Phase 2 — Client Factory

**Files:**
- Create: `smart/subgoal_generator/client_factory.py`
- Create: `smart/subgoal_generator/tests/test_client_factory.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/subgoal_generator/tests/test_client_factory.py`:

```python
"""Phase 2 tests: Anthropic client factory."""
import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client_factory import create_client


class TestCreateClient:
    def test_raises_when_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure ANTHROPIC_API_KEY is absent
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError) as exc_info:
                create_client()
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_explicit_key_creates_client(self):
        client = create_client(api_key="sk-ant-fake-key-for-testing")
        assert client is not None
        # Verify it's an Anthropic client (has messages attribute)
        assert hasattr(client, "messages")

    def test_env_key_creates_client(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-fake-key-env"}):
            client = create_client()
            assert client is not None
            assert hasattr(client, "messages")

    def test_explicit_key_takes_precedence_over_env(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-env-key"}):
            client = create_client(api_key="sk-ant-explicit-key")
            assert client is not None

    def test_error_message_is_helpful(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError) as exc_info:
                create_client()
            msg = str(exc_info.value)
            assert "ANTHROPIC_API_KEY" in msg
            assert "export" in msg.lower() or "set" in msg.lower()
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
python3 -m pytest tests/test_client_factory.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError: No module named 'client_factory'`

- [ ] **Step 3: Implement `client_factory.py`**

Create `smart/subgoal_generator/client_factory.py`:

```python
"""
SMART Framework - Stage 2: Subgoal Generator
Client factory: creates an Anthropic SDK client from env var or explicit key.
"""
import os
import anthropic


def create_client(api_key: str | None = None) -> anthropic.Anthropic:
    """
    Create an Anthropic client.

    Args:
        api_key: Explicit API key. If None, reads ANTHROPIC_API_KEY env var.

    Returns:
        anthropic.Anthropic instance.
        SDK default: max_retries=2 (handles 429 and 5xx automatically).

    Raises:
        EnvironmentError: If no API key is available from either source.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Pass api_key= explicitly or export ANTHROPIC_API_KEY before running."
        )
    return anthropic.Anthropic(api_key=key)
```

- [ ] **Step 4: Run tests — verify they PASS**

```bash
python3 -m pytest tests/test_client_factory.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/codes/smart
git add subgoal_generator/client_factory.py subgoal_generator/tests/test_client_factory.py
git commit -m "feat(stage2): Phase 2 — Anthropic client factory"
```

---

## Task 4: Phase 3 — Prompt Builder

**Files:**
- Create: `smart/subgoal_generator/prompt_builder.py`
- Create: `smart/subgoal_generator/tests/test_prompt_builder.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/subgoal_generator/tests/test_prompt_builder.py`:

```python
"""Phase 3 tests: DiffResult → prompt string."""
import os, sys
import pytest

# Stage 1 imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch
from diff_parser import parse_diff_files

# Stage 2 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from prompt_builder import build_prompt

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser", "tests", "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")


def make_diff_result(n_lines=3, n_branches=2) -> DiffResult:
    lines = [
        ModifiedLine("f.py", i + 1, "added", f"    x_{i} = {i}")
        for i in range(n_lines)
    ]
    branches = [
        ModifiedBranch("f.py", 10 + i, "if_true", f"x > {i}")
        for i in range(n_branches)
    ]
    return DiffResult("f.py", lines, branches)


class TestBuildPromptStructure:
    def test_returns_string(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert isinstance(prompt, str)

    def test_contains_file_path(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "f.py" in prompt

    def test_contains_cl_section(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "C_L" in prompt or "Modified Lines" in prompt

    def test_contains_cb_section(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "C_B" in prompt or "Modified Branches" in prompt

    def test_contains_line_numbers(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "1" in prompt  # first line number

    def test_contains_branch_type(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "if_true" in prompt

    def test_contains_condition_source(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "x > 0" in prompt

    def test_contains_rules(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        # Rules section must instruct the LLM
        assert "anchor_hints" in prompt

    def test_mentions_subgoal_sequence(self):
        result = make_diff_result()
        prompt = build_prompt(result)
        assert "SubgoalSequence" in prompt


class TestBuildPromptTruncation:
    def test_no_truncation_under_limit(self):
        result = make_diff_result(n_lines=5)
        prompt = build_prompt(result, max_lines=10)
        assert "omitted" not in prompt

    def test_truncation_message_appears(self):
        result = make_diff_result(n_lines=20)
        prompt = build_prompt(result, max_lines=5)
        assert "more" in prompt.lower() and "omitted" in prompt.lower()

    def test_truncated_shows_correct_count(self):
        result = make_diff_result(n_lines=20)
        prompt = build_prompt(result, max_lines=5)
        assert "15" in prompt  # 20 - 5 = 15 omitted

    def test_branches_never_truncated(self):
        """C_B always shown in full regardless of max_lines."""
        branches = [ModifiedBranch("f.py", i + 1, "loop_body", "") for i in range(30)]
        result = DiffResult("f.py", [], branches)
        prompt = build_prompt(result, max_lines=5)
        # All 30 branch lines present
        assert prompt.count("loop_body") == 30

    def test_empty_diff_still_builds_prompt(self):
        result = DiffResult("empty.py", [], [])
        prompt = build_prompt(result)
        assert isinstance(prompt, str)
        assert len(prompt) > 50


class TestBuildPromptWithFixtures:
    def test_math_calc_prompt_contains_matrix(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        prompt = build_prompt(result)
        assert "MatrixCalculator" in prompt or "determinant" in prompt or "inverse" in prompt

    def test_math_calc_prompt_contains_branches(self):
        result = parse_diff_files(V1_PATH, V2_PATH)
        prompt = build_prompt(result)
        assert "if_true" in prompt or "if_false" in prompt or "loop_body" in prompt
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
python3 -m pytest tests/test_prompt_builder.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError: No module named 'prompt_builder'`

- [ ] **Step 3: Implement `prompt_builder.py`**

Create `smart/subgoal_generator/prompt_builder.py`:

```python
"""
SMART Framework - Stage 2: Subgoal Generator
Prompt Builder: converts DiffResult into a structured LLM prompt.
"""
from __future__ import annotations

import sys
import os

# Resolve Stage 1 types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ast_diff_parser"))
from models import DiffResult  # noqa: E402


_SYSTEM_INSTRUCTIONS = """\
You are a game testing engineer analyzing a Python code update.
Given the AST diff report below, decompose the changes into an ordered
sequence of verifiable gameplay subgoals.

Rules:
1. Each subgoal must describe one atomic, testable player action or game state change.
2. Subgoals must be ordered by logical dependency (earlier steps enable later ones).
3. Every subgoal must reference at least one entry in C_L or C_B via anchor_hints.
   Format anchor_hints as: '<line_number>' for C_L entries,
   '<line_number>/<branch_type>' for C_B entries.
   Example: anchor_hints=["45", "67/if_true", "67/if_false"]
4. Descriptions must be natural language, not code.

Respond with a valid SubgoalSequence JSON object.\
"""


def build_prompt(diff_result: DiffResult, max_lines: int = 150) -> str:
    """
    Convert a DiffResult into a structured LLM prompt.

    Args:
        diff_result: Output from Stage 1 ast_diff_parser.
        max_lines: Maximum C_L entries shown. Excess lines are summarised.
                   C_B (branches) are never truncated.

    Returns:
        Complete prompt string ready for the Claude API.
    """
    lines = list(diff_result.modified_lines)
    branches = list(diff_result.modified_branches)

    # ── C_L section ──────────────────────────────────────────────────────────
    total_lines = len(lines)
    shown_lines = lines[:max_lines]
    omitted = total_lines - len(shown_lines)

    cl_header = (
        f"--- Modified Lines (C_L): {total_lines} entries"
        + (f" (showing first {max_lines})" if omitted > 0 else "")
        + " ---"
    )
    cl_rows = "\n".join(
        f"{ml.line_number:>6} | {ml.change_type:<8} | {ml.source}"
        for ml in shown_lines
    )
    if omitted > 0:
        cl_rows += f"\n... and {omitted} more lines (omitted to fit context window)"

    # ── C_B section ──────────────────────────────────────────────────────────
    cb_header = f"--- Modified Branches (C_B): {len(branches)} entries ---"
    cb_rows = "\n".join(
        f"{mb.control_stmt_line:>6} | {mb.branch_type:<12} | {mb.condition_source}"
        for mb in branches
    ) or "  (none)"

    # ── Assemble ──────────────────────────────────────────────────────────────
    report = (
        f"=== AST DIFF REPORT ===\n"
        f"File: {diff_result.file_path}\n\n"
        f"{cl_header}\n{cl_rows}\n\n"
        f"{cb_header}\n{cb_rows}\n"
        f"=== END REPORT ==="
    )

    return f"{_SYSTEM_INSTRUCTIONS}\n\n{report}"
```

- [ ] **Step 4: Run tests — verify they PASS**

```bash
python3 -m pytest tests/test_prompt_builder.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/codes/smart
git add subgoal_generator/prompt_builder.py subgoal_generator/tests/test_prompt_builder.py
git commit -m "feat(stage2): Phase 3 — prompt builder with C_L/C_B formatting and truncation"
```

---

## Task 5: Phase 4 — Subgoal Generator (mock client)

**Files:**
- Create: `smart/subgoal_generator/subgoal_generator.py`
- Create: `smart/subgoal_generator/tests/test_subgoal_generator.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/subgoal_generator/tests/test_subgoal_generator.py`:

```python
"""Phase 4 tests: subgoal generator with mock Anthropic client."""
import os, sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Subgoal, SubgoalSequence, SubgoalGenerationError
from subgoal_generator import generate_subgoals


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_diff_result() -> DiffResult:
    return DiffResult(
        file_path="test.py",
        modified_lines=[ModifiedLine("test.py", 10, "added", "class Foo: pass")],
        modified_branches=[ModifiedBranch("test.py", 20, "if_true", "x > 0")],
    )


def make_subgoal_sequence() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Test Task",
        summary="A test task with two steps.",
        subgoals=[
            Subgoal(index=1, description="Do the first thing", rationale="line 10",
                    anchor_hints=["10"]),
            Subgoal(index=2, description="Do the second thing", rationale="line 20",
                    anchor_hints=["20/if_true"]),
        ],
    )


def make_mock_client(seq: SubgoalSequence, stop_reason: str = "end_turn") -> MagicMock:
    mock_response = MagicMock()
    mock_response.parsed_output = seq
    mock_response.stop_reason = stop_reason
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client


# ── Tests ────────────────────────────────────────────────────────────────────

class TestGenerateSubgoalsHappyPath:
    def test_returns_subgoal_sequence(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        result = generate_subgoals(make_diff_result(), client=client)
        assert isinstance(result, SubgoalSequence)

    def test_subgoals_preserved(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        result = generate_subgoals(make_diff_result(), client=client)
        assert len(result.subgoals) == 2
        assert result.subgoals[0].index == 1

    def test_calls_messages_parse(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client)
        assert client.messages.parse.called

    def test_passes_model_to_api(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client, model="claude-opus-4-6")
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("model") == "claude-opus-4-6"

    def test_passes_output_format(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("output_format") is SubgoalSequence

    def test_uses_thinking_when_requested(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client, use_thinking=True)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("thinking") == {"type": "adaptive"}

    def test_no_thinking_by_default(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert "thinking" not in call_kwargs

    def test_to_dict_on_result(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        result = generate_subgoals(make_diff_result(), client=client)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert len(d["subgoals"]) == 2


class TestGenerateSubgoalsErrorHandling:
    def test_refusal_raises_error(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq, stop_reason="refusal")
        with pytest.raises(SubgoalGenerationError) as exc_info:
            generate_subgoals(make_diff_result(), client=client)
        assert exc_info.value.stop_reason == "refusal"

    def test_none_parsed_output_raises_error(self):
        mock_response = MagicMock()
        mock_response.parsed_output = None
        mock_response.stop_reason = "end_turn"
        mock_client = MagicMock()
        mock_client.messages.parse.return_value = mock_response
        with pytest.raises(SubgoalGenerationError):
            generate_subgoals(make_diff_result(), client=mock_client)

    def test_api_error_propagates(self):
        import anthropic
        mock_client = MagicMock()
        mock_client.messages.parse.side_effect = anthropic.APIStatusError(
            message="server error",
            response=MagicMock(status_code=500),
            body={},
        )
        with pytest.raises(anthropic.APIStatusError):
            generate_subgoals(make_diff_result(), client=mock_client)


class TestGenerateSubgoalsClientFactory:
    def test_no_client_raises_env_error_when_no_key(self):
        """When client=None and no API key set, EnvironmentError from factory."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError):
                generate_subgoals(make_diff_result())
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
python3 -m pytest tests/test_subgoal_generator.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError: No module named 'subgoal_generator'`

- [ ] **Step 3: Implement `subgoal_generator.py`**

Create `smart/subgoal_generator/subgoal_generator.py`:

```python
"""
SMART Framework - Stage 2: Subgoal Generator
Main entry point: calls Claude API and returns a validated SubgoalSequence.
"""
from __future__ import annotations

import anthropic

from models import SubgoalSequence, SubgoalGenerationError
from client_factory import create_client
from prompt_builder import build_prompt

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ast_diff_parser"))
from models import DiffResult  # noqa: E402


def generate_subgoals(
    diff_result: DiffResult,
    client: anthropic.Anthropic | None = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
) -> SubgoalSequence:
    """
    Generate an ordered subgoal sequence from a Stage 1 DiffResult.

    Args:
        diff_result: Structural anchors (C_L, C_B) from ast_diff_parser.
        client: Anthropic client. If None, created via create_client().
        model: Claude model ID to use.
        max_tokens: Maximum output tokens.
        use_thinking: If True, enable adaptive thinking for deeper reasoning.

    Returns:
        SubgoalSequence — validated Pydantic object.

    Raises:
        EnvironmentError: If client is None and ANTHROPIC_API_KEY is not set.
        SubgoalGenerationError: If Claude refuses or output fails to parse.
        anthropic.APIStatusError: On API-level errors (caller handles retry).
    """
    if client is None:
        client = create_client()

    prompt = build_prompt(diff_result)

    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_format=SubgoalSequence,
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    response = client.messages.parse(**kwargs)

    if response.stop_reason == "refusal":
        raise SubgoalGenerationError(
            "Claude refused to generate subgoals for this diff.",
            stop_reason="refusal",
        )
    if response.parsed_output is None:
        raise SubgoalGenerationError(
            "Claude response did not parse to a valid SubgoalSequence.",
            stop_reason=response.stop_reason,
        )
    return response.parsed_output
```

- [ ] **Step 4: Run tests — verify they PASS**

```bash
python3 -m pytest tests/test_subgoal_generator.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/codes/smart
git add subgoal_generator/subgoal_generator.py subgoal_generator/tests/test_subgoal_generator.py
git commit -m "feat(stage2): Phase 4 — subgoal generator with mock-tested Claude API call"
```

---

## Task 6: Phase 5 — Integration Test

**Files:**
- Create: `smart/subgoal_generator/tests/test_integration.py`

- [ ] **Step 1: Write the integration test**

Create `smart/subgoal_generator/tests/test_integration.py`:

```python
"""
Phase 5: Integration test — real Claude API call.
Skipped automatically when ANTHROPIC_API_KEY is not set.
Run with: pytest tests/test_integration.py -v -s
"""
import os, sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from diff_parser import parse_diff_files
from models import DiffResult

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import SubgoalSequence, Subgoal
from subgoal_generator import generate_subgoals

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser", "tests", "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")

needs_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API integration test"
)


@needs_key
def test_real_api_returns_subgoal_sequence():
    """Full pipeline: math_calc v1→v2 diff → Claude API → SubgoalSequence."""
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    assert isinstance(seq, SubgoalSequence)


@needs_key
def test_real_api_subgoals_nonempty():
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    assert len(seq.subgoals) >= 2


@needs_key
def test_real_api_subgoals_reference_diff_content():
    """Subgoal descriptions must mention new components from v2."""
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    all_text = " ".join(s.description + " " + s.rationale for s in seq.subgoals).lower()
    keywords = ["matrix", "complex", "taylor", "integrate", "derivative"]
    assert any(kw in all_text for kw in keywords), (
        f"No expected keyword found in subgoals. Got: {all_text[:200]}"
    )


@needs_key
def test_real_api_subgoals_have_anchor_hints():
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    # At least some subgoals should have anchor hints
    hints = [s for s in seq.subgoals if s.anchor_hints]
    assert len(hints) >= 1


@needs_key
def test_real_api_to_dict_serializable():
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    d = seq.to_dict()
    assert isinstance(d, dict)
    assert len(d["subgoals"]) >= 1


@needs_key
def test_real_api_prints_readable_report(capsys):
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    print(f"\n{'='*60}")
    print(f"SMART Stage 2 — Subgoal Report")
    print(f"Task: {seq.task_name}")
    print(f"Summary: {seq.summary}")
    print(f"{'='*60}")
    for sg in seq.subgoals:
        print(f"  [{sg.index}] {sg.description}")
        if sg.anchor_hints:
            print(f"       anchors: {', '.join(sg.anchor_hints)}")
    print(f"{'='*60}")
    captured = capsys.readouterr()
    assert "Stage 2" in captured.out
```

- [ ] **Step 2: Run without API key — verify tests SKIP**

```bash
python3 -m pytest tests/test_integration.py -v 2>&1 | tail -10
```

Expected: all tests show `SKIPPED` with reason `"ANTHROPIC_API_KEY not set"`.

- [ ] **Step 3: Full regression (all phases)**

```bash
python3 -m pytest tests/ -v --ignore=tests/test_integration.py
```

Expected: all unit tests PASS (0 failures).

- [ ] **Step 4: Commit**

```bash
cd /Users/xd/Desktop/codes/smart
git add subgoal_generator/tests/test_integration.py
git commit -m "feat(stage2): Phase 5 — integration test (skips without API key)"
```

---

## Task 7: Full Regression

- [ ] **Step 1: Run all Stage 2 unit tests**

```bash
cd /Users/xd/Desktop/codes/smart/subgoal_generator
python3 -m pytest tests/ --ignore=tests/test_integration.py -v
```

Expected: all PASS, 0 failures.

- [ ] **Step 2: Run Stage 1 regression to verify no breakage**

```bash
cd /Users/xd/Desktop/codes/smart/ast_diff_parser
python3 -m pytest tests/ -v
```

Expected: 96 PASS (unchanged from Stage 1).

- [ ] **Step 3: (Optional) Run integration test with real API key**

```bash
cd /Users/xd/Desktop/codes/smart/subgoal_generator
ANTHROPIC_API_KEY=your_key python3 -m pytest tests/test_integration.py -v -s
```

Expected: all 6 integration tests PASS with readable SubgoalSequence output.

- [ ] **Step 4: Final commit**

```bash
cd /Users/xd/Desktop/codes/smart
git add -A
git commit -m "feat(stage2): complete Stage 2 — subgoal generator, all phases passing"
```
