# Stage 4: Structural Anchor Mapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `anchor_mapper/` — a package that takes a `DiffResult` (Stage 1) + `SubgoalSequence` (Stage 2) + new-version source code, and produces a `StructuralAnchorMap` mapping each structural anchor to the subgoals where it is semantically relevant.

**Architecture:** Two-phase pipeline: Phase 1 uses Python AST call graph analysis to find candidate anchors per subgoal (static, intra-file BFS); Phase 2 calls Claude once per subgoal to semantically filter candidates. Five implementation tasks (models → client_factory → call_graph_analyzer → prompt_builder → anchor_mapper orchestrator) plus integration test. Package follows the exact same layout as Stages 2 & 3.

**Tech Stack:** Python 3.9+, `ast` standard library, Pydantic v2, `anthropic` SDK (`messages.parse(output_format=...)`), pytest, `from __future__ import annotations`.

---

## File Structure

```
smart/anchor_mapper/
├── models.py               # AnchorMapping, StructuralAnchorMap, AnchorMappingError, FunctionInfo, CandidateSet
├── client_factory.py       # Identical to Stages 2 & 3
├── call_graph_analyzer.py  # Phase 1: AST analysis → list[CandidateSet]
├── prompt_builder.py       # Phase 2: prompt construction + FilterResult schema
├── anchor_mapper.py        # Orchestrator: Phase 1 → Phase 2 → StructuralAnchorMap
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_client_factory.py
    ├── test_call_graph_analyzer.py
    ├── test_prompt_builder.py
    ├── test_anchor_mapper.py
    └── test_integration.py
```

**Critical:** Do NOT create `anchor_mapper/__init__.py`. If one exists, `from anchor_mapper import generate_anchor_map` will import the package instead of the module.

**Cross-stage import pattern** (same as Stages 2 & 3): Test files manage `sys.modules["models"]` explicitly. Load Stage 1 models first, Stage 2 models second, Stage 4 models last — so `sys.modules["models"]` = Stage 4 at call time. `anchor_mapper.py` lazily resolves `AnchorMappingError` from `sys.modules["models"]` inside `generate_anchor_map()`.

---

## Task 1: Scaffold

**Files:**
- Create: `smart/anchor_mapper/` (directory)
- Create: `smart/anchor_mapper/tests/__init__.py`

- [ ] **Step 1: Create directories**

```bash
cd /Users/xd/Desktop/codes/smart
mkdir -p anchor_mapper/tests
touch anchor_mapper/tests/__init__.py
```

- [ ] **Step 2: Verify — no `__init__.py` at package root**

```bash
ls anchor_mapper/
ls anchor_mapper/tests/
ls anchor_mapper/__init__.py 2>/dev/null && echo "ERROR: remove this" || echo "OK"
```

Expected: `tests/` visible; tests/ has `__init__.py`; no `anchor_mapper/__init__.py`.

---

## Task 2: Phase 1 — Data Models

**Files:**
- Create: `smart/anchor_mapper/models.py`
- Create: `smart/anchor_mapper/tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/anchor_mapper/tests/test_models.py`:

```python
"""Phase 1 tests: data models for Stage 4 anchor mapper."""
import os, sys
import pytest
from pydantic import ValidationError

# Stage 4 models (only — no cross-stage identity needed for model unit tests)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import (
    AnchorMapping, StructuralAnchorMap, AnchorMappingError,
    FunctionInfo, CandidateSet,
)


class TestAnchorMapping:
    def test_creates_line_anchor(self):
        m = AnchorMapping(
            anchor_key="L:42",
            anchor_type="line",
            line_number=42,
            source_snippet="return x + 1",
            subgoal_indices=[1],
        )
        assert m.anchor_key == "L:42"
        assert m.anchor_type == "line"
        assert m.branch_type is None

    def test_creates_branch_anchor(self):
        m = AnchorMapping(
            anchor_key="B:20:if_true",
            anchor_type="branch",
            line_number=20,
            branch_type="if_true",
            source_snippet="if x > 0:",
            subgoal_indices=[1, 2],
        )
        assert m.branch_type == "if_true"
        assert m.subgoal_indices == [1, 2]

    def test_invalid_anchor_type_raises(self):
        with pytest.raises(ValidationError):
            AnchorMapping(
                anchor_key="X:10",
                anchor_type="unknown",
                line_number=10,
                source_snippet="x",
                subgoal_indices=[1],
            )

    def test_empty_subgoal_indices_raises(self):
        with pytest.raises(ValidationError):
            AnchorMapping(
                anchor_key="L:10",
                anchor_type="line",
                line_number=10,
                source_snippet="x",
                subgoal_indices=[],
            )


class TestStructuralAnchorMap:
    def _make_map(self):
        return StructuralAnchorMap(
            task_name="Test Task",
            file_path="test.py",
            mappings=[
                AnchorMapping(
                    anchor_key="L:10", anchor_type="line", line_number=10,
                    source_snippet="foo()", subgoal_indices=[1],
                ),
                AnchorMapping(
                    anchor_key="L:20", anchor_type="line", line_number=20,
                    source_snippet="bar()", subgoal_indices=[1, 2],
                ),
                AnchorMapping(
                    anchor_key="B:30:if_true", anchor_type="branch", line_number=30,
                    branch_type="if_true", source_snippet="if x:", subgoal_indices=[2],
                ),
            ],
        )

    def test_for_subgoal_returns_correct_subset(self):
        m = self._make_map()
        result = m.for_subgoal(1)
        assert len(result) == 2
        keys = {r.anchor_key for r in result}
        assert keys == {"L:10", "L:20"}

    def test_for_subgoal_returns_empty_for_no_match(self):
        m = self._make_map()
        assert m.for_subgoal(99) == []

    def test_to_dict_returns_serializable_dict(self):
        m = self._make_map()
        d = m.to_dict()
        assert isinstance(d, dict)
        assert d["task_name"] == "Test Task"
        assert len(d["mappings"]) == 3

    def test_empty_mappings_is_valid(self):
        m = StructuralAnchorMap(task_name="T", file_path="f.py", mappings=[])
        assert m.mappings == []
        assert m.to_dict()["mappings"] == []


class TestAnchorMappingError:
    def test_default_stop_reason_is_none(self):
        err = AnchorMappingError("fail")
        assert err.stop_reason is None
        assert str(err) == "fail"

    def test_stop_reason_stored(self):
        err = AnchorMappingError("refused", stop_reason="refusal")
        assert err.stop_reason == "refusal"

    def test_is_exception(self):
        with pytest.raises(AnchorMappingError):
            raise AnchorMappingError("boom")


class TestFunctionInfo:
    def test_creates_with_defaults(self):
        fi = FunctionInfo(name="foo", start_line=1, end_line=5)
        assert fi.name == "foo"
        assert fi.calls == []

    def test_creates_with_calls(self):
        fi = FunctionInfo(name="foo", start_line=1, end_line=5, calls=["bar", "baz"])
        assert fi.calls == ["bar", "baz"]


class TestCandidateSet:
    def test_creates_correctly(self):
        cs = CandidateSet(
            subgoal_index=1,
            subgoal_description="Do the thing",
            subgoal_rationale="line 10",
            candidates=[],
        )
        assert cs.subgoal_index == 1
        assert cs.candidates == []
```

- [ ] **Step 2: Run — confirm all fail**

```bash
cd /Users/xd/Desktop/codes/smart
pytest anchor_mapper/tests/test_models.py -v 2>&1 | head -30
```

Expected: ImportError (models.py doesn't exist yet).

- [ ] **Step 3: Create `smart/anchor_mapper/models.py`**

```python
"""
SMART Framework - Stage 4: Structural Anchor Mapper
Data models: AnchorMapping, StructuralAnchorMap, AnchorMappingError, FunctionInfo, CandidateSet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AnchorMappingError(Exception):
    """Raised when anchor mapping fails (LLM refusal or parse error)."""

    def __init__(self, message: str, stop_reason: Optional[str] = None):
        super().__init__(message)
        self.stop_reason = stop_reason


class AnchorMapping(BaseModel):
    """Maps one structural anchor to the subgoals where it is relevant."""

    anchor_key: str = Field(..., description='"L:42" for line 42, "B:20:if_true" for branch')
    anchor_type: Literal["line", "branch"]
    line_number: int = Field(..., description="Line number (or control_stmt_line for branches)")
    branch_type: Optional[str] = Field(None, description="None for lines; branch_type string for branches")
    source_snippet: str = Field(..., description="Code fragment from Stage 1")
    subgoal_indices: list[int] = Field(..., min_length=1)


class StructuralAnchorMap(BaseModel):
    """Full mapping output: each anchor → set of relevant subgoal indices."""

    task_name: str
    file_path: str
    mappings: list[AnchorMapping] = Field(default_factory=list)

    def for_subgoal(self, index: int) -> list[AnchorMapping]:
        """Return all anchors mapped to the given subgoal index."""
        return [m for m in self.mappings if index in m.subgoal_indices]

    def to_dict(self) -> dict:
        return self.model_dump()


@dataclass
class FunctionInfo:
    """AST-derived metadata for one function or method."""

    name: str           # "taylor_series" or "MatrixCalculator.determinant"
    start_line: int
    end_line: int
    calls: list[str] = field(default_factory=list)   # names called in the body


@dataclass
class CandidateSet:
    """Phase 1 output: candidate anchors for one subgoal, before LLM filtering."""

    subgoal_index: int
    subgoal_description: str
    subgoal_rationale: str
    candidates: list   # list[ModifiedLine | ModifiedBranch] — untyped to avoid cross-stage import
```

- [ ] **Step 4: Run — confirm all pass**

```bash
pytest anchor_mapper/tests/test_models.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
cd /Users/xd/Desktop/codes/smart
git add anchor_mapper/models.py anchor_mapper/tests/__init__.py anchor_mapper/tests/test_models.py
git commit -m "feat(stage4): Phase 1 — data models for anchor mapper"
```

---

## Task 3: Phase 2 — Client Factory

**Files:**
- Create: `smart/anchor_mapper/client_factory.py`
- Create: `smart/anchor_mapper/tests/test_client_factory.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/anchor_mapper/tests/test_client_factory.py`:

```python
"""Phase 2 tests: Anthropic client factory."""
import os, sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client_factory import create_client


class TestCreateClient:
    def test_raises_env_error_when_no_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
            create_client()

    def test_accepts_explicit_key(self):
        import anthropic
        client = create_client(api_key="sk-ant-test-key")
        assert isinstance(client, anthropic.Anthropic)

    def test_reads_env_var(self, monkeypatch):
        import anthropic
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
        client = create_client()
        assert isinstance(client, anthropic.Anthropic)

    def test_explicit_key_overrides_env(self, monkeypatch):
        import anthropic
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
        client = create_client(api_key="sk-ant-explicit-key")
        assert isinstance(client, anthropic.Anthropic)

    def test_returns_anthropic_instance(self):
        import anthropic
        client = create_client(api_key="sk-ant-any-key")
        assert isinstance(client, anthropic.Anthropic)
```

- [ ] **Step 2: Run — confirm fail**

```bash
pytest anchor_mapper/tests/test_client_factory.py -v 2>&1 | head -20
```

Expected: ImportError.

- [ ] **Step 3: Create `smart/anchor_mapper/client_factory.py`**

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
        anthropic.Anthropic instance with SDK-default retry behaviour.

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

- [ ] **Step 4: Run — confirm pass**

```bash
pytest anchor_mapper/tests/test_client_factory.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add anchor_mapper/client_factory.py anchor_mapper/tests/test_client_factory.py
git commit -m "feat(stage4): Phase 2 — client factory"
```

---

## Task 4: Phase 3 — Call Graph Analyzer

**Files:**
- Create: `smart/anchor_mapper/call_graph_analyzer.py`
- Create: `smart/anchor_mapper/tests/test_call_graph_analyzer.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/anchor_mapper/tests/test_call_graph_analyzer.py`:

```python
"""Phase 3 tests: AST-based call graph analyzer."""
import os, sys
import pytest

# Stage 1 imports FIRST
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch

# Stage 2 imports SECOND (via importlib — avoids clobbering sys.modules["models"])
import importlib.util as _ilu
_s2_spec = _ilu.spec_from_file_location(
    "_s2_models",
    os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator", "models.py"),
)
_s2 = _ilu.module_from_spec(_s2_spec)
_s2_spec.loader.exec_module(_s2)
Subgoal = _s2.Subgoal
SubgoalSequence = _s2.SubgoalSequence

# Stage 4 imports LAST
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import CandidateSet
from call_graph_analyzer import analyze_call_graph


# ── Fixtures ─────────────────────────────────────────────────────────────────

# Simple inline source: known line numbers for predictable tests.
# Line 1: def foo(x):
# Line 2:     return bar(x) + 1
# Line 3: (blank)
# Line 4: def bar(x):
# Line 5:     if x > 0:
# Line 6:         return x
# Line 7:     return -x
# Line 8: (blank)
# Line 9: class MyClass:
# Line 10:     def method_a(self):
# Line 11:         return self.method_b()
# Line 12: (blank)
# Line 13:     def method_b(self):
# Line 14:         return 42
SIMPLE_SOURCE = """\
def foo(x):
    return bar(x) + 1

def bar(x):
    if x > 0:
        return x
    return -x

class MyClass:
    def method_a(self):
        return self.method_b()

    def method_b(self):
        return 42
"""


def make_diff(lines=None, branches=None) -> DiffResult:
    return DiffResult(
        file_path="test.py",
        modified_lines=lines or [],
        modified_branches=branches or [],
    )


def make_seq(*hint_lists) -> SubgoalSequence:
    """Create a SubgoalSequence with one subgoal per hint list."""
    subgoals = [
        Subgoal(
            index=i + 1,
            description=f"Subgoal {i + 1}",
            rationale="test",
            anchor_hints=hints,
        )
        for i, hints in enumerate(hint_lists)
    ]
    return SubgoalSequence(
        task_name="Test Task",
        summary="Test summary for unit tests.",
        subgoals=subgoals,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAnalyzeCallGraph:
    def test_direct_line_hint_includes_anchor(self):
        """Anchor at line 2 (inside foo); hint '2' → candidate for subgoal 1."""
        diff = make_diff(lines=[ModifiedLine("test.py", 2, "added", "return bar(x) + 1")])
        seq = make_seq(["2"])
        result = analyze_call_graph(diff, seq, SIMPLE_SOURCE)
        assert len(result) == 1
        assert any(
            getattr(c, 'line_number', None) == 2 for c in result[0].candidates
        )

    def test_bfs_follows_call_edge(self):
        """foo calls bar; hint '1' (foo's line) → anchors inside bar are also candidates."""
        diff = make_diff(lines=[
            ModifiedLine("test.py", 2, "added", "return bar(x) + 1"),  # in foo
            ModifiedLine("test.py", 6, "added", "return x"),           # in bar
        ])
        seq = make_seq(["1"])  # hint points to foo
        result = analyze_call_graph(diff, seq, SIMPLE_SOURCE)
        assert len(result) == 1
        line_nums = {getattr(c, 'line_number', None) for c in result[0].candidates}
        assert 6 in line_nums  # bar line reachable via foo→bar BFS

    def test_method_in_class_reachable_via_class_hint(self):
        """Hint '10' (line of method_a) → method_a is entry; method_b reachable via call."""
        diff = make_diff(lines=[
            ModifiedLine("test.py", 14, "added", "return 42"),  # in method_b
        ])
        seq = make_seq(["10"])  # method_a's line
        result = analyze_call_graph(diff, seq, SIMPLE_SOURCE)
        assert len(result) == 1
        line_nums = {getattr(c, 'line_number', None) for c in result[0].candidates}
        assert 14 in line_nums  # method_b reachable via method_a call

    def test_branch_hint_resolved_by_line(self):
        """Hint '5/if_true' → resolves to function containing line 5 (bar)."""
        diff = make_diff(branches=[
            ModifiedBranch("test.py", 5, "if_true", "x > 0"),
        ])
        seq = make_seq(["5/if_true"])
        result = analyze_call_graph(diff, seq, SIMPLE_SOURCE)
        assert len(result) == 1
        branch_lines = {getattr(c, 'control_stmt_line', None) for c in result[0].candidates}
        assert 5 in branch_lines

    def test_unmatched_anchor_is_fallback_for_all(self):
        """Anchor at line 99 (no function) → conservative fallback: candidate in all subgoals."""
        diff = make_diff(lines=[ModifiedLine("test.py", 99, "added", "# orphan")])
        seq = make_seq(["1"], ["4"])  # two subgoals
        result = analyze_call_graph(diff, seq, SIMPLE_SOURCE)
        assert len(result) == 2
        # The orphan anchor must appear in both candidate sets
        for cs in result:
            orphan = [c for c in cs.candidates if getattr(c, 'line_number', None) == 99]
            assert len(orphan) == 1, f"Subgoal {cs.subgoal_index} missing orphan anchor"

    def test_empty_source_raises(self):
        diff = make_diff(lines=[ModifiedLine("test.py", 1, "added", "x")])
        seq = make_seq(["1"])
        with pytest.raises((ValueError, Exception)):
            analyze_call_graph(diff, seq, "")

    def test_returns_one_candidate_set_per_subgoal(self):
        diff = make_diff(lines=[ModifiedLine("test.py", 2, "added", "x")])
        seq = make_seq(["1"], ["4"], ["10"])
        result = analyze_call_graph(diff, seq, SIMPLE_SOURCE)
        assert len(result) == 3
        indices = [cs.subgoal_index for cs in result]
        assert indices == [1, 2, 3]
```

- [ ] **Step 2: Run — confirm fail**

```bash
cd /Users/xd/Desktop/codes/smart
pytest anchor_mapper/tests/test_call_graph_analyzer.py -v 2>&1 | head -30
```

Expected: ImportError on `call_graph_analyzer`.

- [ ] **Step 3: Create `smart/anchor_mapper/call_graph_analyzer.py`**

```python
"""
SMART Framework - Stage 4: Structural Anchor Mapper
Phase 1: AST-based call graph analysis.
Produces a list[CandidateSet] — one per subgoal, each containing candidate anchors.
"""
from __future__ import annotations

import ast
import sys
import os
from typing import TYPE_CHECKING

_S4_PATH = os.path.dirname(os.path.abspath(__file__))
if _S4_PATH not in sys.path:
    sys.path.insert(0, _S4_PATH)

# Conditional reload: only reload if the cached "models" isn't Stage 4
if not (sys.modules.get("models") and hasattr(sys.modules["models"], "CandidateSet")):
    if "models" in sys.modules:
        del sys.modules["models"]
from models import FunctionInfo, CandidateSet


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_function_map(source_code: str) -> dict[str, FunctionInfo]:
    """Parse source_code and return a map of qualified name → FunctionInfo."""
    if not source_code.strip():
        raise ValueError("source_code is empty")
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        raise ValueError(f"Failed to parse source code: {e}") from e

    function_map: dict[str, FunctionInfo] = {}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = _extract_calls(node)
            function_map[node.name] = FunctionInfo(
                name=node.name,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                calls=calls,
            )
        elif isinstance(node, ast.ClassDef):
            class_name = node.name
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified = f"{class_name}.{item.name}"
                    calls = _extract_calls(item)
                    function_map[qualified] = FunctionInfo(
                        name=qualified,
                        start_line=item.lineno,
                        end_line=item.end_lineno or item.lineno,
                        calls=calls,
                    )

    return function_map


def _extract_calls(func_node: ast.AST) -> list[str]:
    """Extract all called function/method names from a function node."""
    calls = set()
    for child in ast.walk(func_node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.add(child.func.attr)
    return list(calls)


def _find_functions_for_line(
    line_number: int, function_map: dict[str, FunctionInfo]
) -> list[str]:
    """Return qualified names of all functions whose line range contains line_number."""
    return [
        name
        for name, info in function_map.items()
        if info.start_line <= line_number <= info.end_line
    ]


def _bfs_reachable(
    entry_names: list[str], function_map: dict[str, FunctionInfo]
) -> set[str]:
    """BFS from entry_names, following call edges. Returns all reachable function names."""
    visited: set[str] = set()
    queue = list(entry_names)
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        info = function_map.get(current)
        if info is None:
            continue
        for callee in info.calls:
            # Match exact name or qualified name ending with .callee
            matching = [
                name for name in function_map
                if name == callee or name.endswith(f".{callee}")
            ]
            for m in matching:
                if m not in visited:
                    queue.append(m)
    return visited


def _anchor_line(anchor) -> int:
    """Return the relevant line number for a ModifiedLine or ModifiedBranch."""
    if hasattr(anchor, "line_number"):
        return anchor.line_number
    return anchor.control_stmt_line


def _make_anchor_key(anchor) -> str:
    if hasattr(anchor, "line_number"):
        return f"L:{anchor.line_number}"
    return f"B:{anchor.control_stmt_line}:{anchor.branch_type}"


# ── Public interface ──────────────────────────────────────────────────────────

def analyze_call_graph(
    diff_result,
    subgoal_sequence,
    source_code: str,
) -> list[CandidateSet]:
    """
    Phase 1 static analysis: build candidate anchor sets for each subgoal.

    Args:
        diff_result: DiffResult from Stage 1 (duck-typed).
        subgoal_sequence: SubgoalSequence from Stage 2 (duck-typed).
        source_code: Full text of the new-version source file.

    Returns:
        list[CandidateSet] — one entry per subgoal, in subgoal index order.

    Raises:
        ValueError: If source_code is empty or cannot be parsed.
    """
    function_map = _build_function_map(source_code)
    all_anchors = list(diff_result.modified_lines) + list(diff_result.modified_branches)

    # Track which anchors have been placed in at least one candidate set
    anchors_placed: set[int] = set()  # id(anchor) → placed

    candidate_sets: list[CandidateSet] = []

    for subgoal in subgoal_sequence.subgoals:
        # Step 1: identify entry points from anchor_hints (all line-number based)
        entry_names: list[str] = []
        for hint in subgoal.anchor_hints:
            parts = hint.split("/")
            try:
                line_num = int(parts[0])
                found = _find_functions_for_line(line_num, function_map)
                entry_names.extend(found)
            except ValueError:
                pass  # malformed hint — skip

        # Step 2: BFS to find reachable functions
        reachable = _bfs_reachable(entry_names, function_map) if entry_names else set()

        # Step 3: collect candidate anchors
        candidates = []
        for anchor in all_anchors:
            line = _anchor_line(anchor)

            # Direct hint match: anchor's line explicitly named in anchor_hints
            is_direct = any(
                _hint_line(h) == line for h in subgoal.anchor_hints
            )

            # Reachable via call graph
            containing = _find_functions_for_line(line, function_map)
            is_reachable = bool(reachable & set(containing))

            if is_direct or is_reachable:
                candidates.append(anchor)
                anchors_placed.add(id(anchor))

        candidate_sets.append(CandidateSet(
            subgoal_index=subgoal.index,
            subgoal_description=subgoal.description,
            subgoal_rationale=subgoal.rationale,
            candidates=candidates,
        ))

    # Conservative fallback: any anchor not placed in any set → add to all
    orphan_anchors = [a for a in all_anchors if id(a) not in anchors_placed]
    for cs in candidate_sets:
        cs.candidates.extend(orphan_anchors)

    return candidate_sets


def _hint_line(hint: str) -> int | None:
    """Parse hint string to line number. Returns None if not parseable."""
    try:
        return int(hint.split("/")[0])
    except ValueError:
        return None
```

- [ ] **Step 4: Run — confirm pass**

```bash
cd /Users/xd/Desktop/codes/smart
pytest anchor_mapper/tests/test_call_graph_analyzer.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add anchor_mapper/call_graph_analyzer.py anchor_mapper/tests/test_call_graph_analyzer.py
git commit -m "feat(stage4): Phase 3 — AST call graph analyzer"
```

---

## Task 5: Phase 4 — Prompt Builder

**Files:**
- Create: `smart/anchor_mapper/prompt_builder.py`
- Create: `smart/anchor_mapper/tests/test_prompt_builder.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/anchor_mapper/tests/test_prompt_builder.py`:

```python
"""Phase 4 tests: prompt builder and FilterResult schema."""
import os, sys

# Stage 4 only (no cross-stage identity needed for prompt builder)
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import CandidateSet
from prompt_builder import build_prompt, FilterResult

# Minimal duck-typed anchors for testing
class FakeLine:
    def __init__(self, line_number, source):
        self.line_number = line_number
        self.source = source

class FakeBranch:
    def __init__(self, control_stmt_line, branch_type, condition_source):
        self.control_stmt_line = control_stmt_line
        self.branch_type = branch_type
        self.condition_source = condition_source


def make_candidate_set(candidates=None):
    return CandidateSet(
        subgoal_index=2,
        subgoal_description="Perform a determinant calculation",
        subgoal_rationale="determinant method handles singular check",
        candidates=candidates or [],
    )


class TestBuildPrompt:
    def test_prompt_contains_subgoal_description(self):
        cs = make_candidate_set()
        prompt = build_prompt(cs)
        assert "Perform a determinant calculation" in prompt

    def test_prompt_contains_subgoal_index(self):
        cs = make_candidate_set()
        prompt = build_prompt(cs)
        assert "Index: 2" in prompt

    def test_prompt_contains_subgoal_rationale(self):
        cs = make_candidate_set()
        prompt = build_prompt(cs)
        assert "determinant method handles singular check" in prompt

    def test_line_anchor_appears_with_key(self):
        cs = make_candidate_set([FakeLine(51, "def determinant(self, matrix):")])
        prompt = build_prompt(cs)
        assert "[L:51]" in prompt
        assert "def determinant" in prompt

    def test_branch_anchor_appears_with_key(self):
        cs = make_candidate_set([FakeBranch(54, "if_true", "det == 0")])
        prompt = build_prompt(cs)
        assert "[B:54:if_true]" in prompt
        assert "det == 0" in prompt

    def test_anchor_type_shown_in_prompt(self):
        cs = make_candidate_set([FakeLine(10, "x = 1")])
        prompt = build_prompt(cs)
        assert "(line)" in prompt

    def test_empty_candidates_does_not_crash(self):
        cs = make_candidate_set([])
        prompt = build_prompt(cs)
        assert isinstance(prompt, str)
        assert "SUBGOAL" in prompt

    def test_multiple_anchors_all_present(self):
        cs = make_candidate_set([
            FakeLine(10, "x = 1"),
            FakeLine(20, "y = 2"),
            FakeBranch(30, "if_false", "x < 0"),
        ])
        prompt = build_prompt(cs)
        assert "[L:10]" in prompt
        assert "[L:20]" in prompt
        assert "[B:30:if_false]" in prompt


class TestFilterResult:
    def test_creates_valid_instance(self):
        fr = FilterResult(relevant_keys=["L:10", "B:20:if_true"], rationale="Both relevant")
        assert fr.relevant_keys == ["L:10", "B:20:if_true"]
        assert fr.rationale == "Both relevant"

    def test_empty_keys_valid(self):
        fr = FilterResult(relevant_keys=[], rationale="None relevant")
        assert fr.relevant_keys == []
```

- [ ] **Step 2: Run — confirm fail**

```bash
pytest anchor_mapper/tests/test_prompt_builder.py -v 2>&1 | head -20
```

Expected: ImportError on `prompt_builder`.

- [ ] **Step 3: Create `smart/anchor_mapper/prompt_builder.py`**

```python
"""
SMART Framework - Stage 4: Structural Anchor Mapper
Phase 2: Prompt builder for per-subgoal LLM semantic filtering.
Also defines FilterResult — the structured output schema for each LLM call.
"""
from __future__ import annotations

import sys
import os
from pydantic import BaseModel

_S4_PATH = os.path.dirname(os.path.abspath(__file__))
if _S4_PATH not in sys.path:
    sys.path.insert(0, _S4_PATH)

# Conditional reload guard for CandidateSet
if not (sys.modules.get("models") and hasattr(sys.modules["models"], "CandidateSet")):
    if "models" in sys.modules:
        del sys.modules["models"]
from models import CandidateSet


class FilterResult(BaseModel):
    """Structured output for one per-subgoal LLM filtering call."""
    relevant_keys: list[str]
    rationale: str


# ── Internal helpers ──────────────────────────────────────────────────────────

def _anchor_key(anchor) -> str:
    if hasattr(anchor, "line_number"):
        return f"L:{anchor.line_number}"
    return f"B:{anchor.control_stmt_line}:{anchor.branch_type}"


def _anchor_type_label(anchor) -> str:
    return "line" if hasattr(anchor, "line_number") else "branch"


def _anchor_snippet(anchor) -> str:
    if hasattr(anchor, "source"):
        return anchor.source
    return anchor.condition_source


# ── Public interface ──────────────────────────────────────────────────────────

def build_prompt(candidate_set: CandidateSet) -> str:
    """
    Build the per-subgoal filtering prompt for Claude.

    Args:
        candidate_set: CandidateSet produced by Phase 1 call graph analysis.

    Returns:
        Formatted prompt string.
    """
    lines = [
        "You are a code relevance analyst for a game testing framework.",
        "",
        "Given the subgoal and candidate code anchors below, determine which anchors",
        "are DIRECTLY and SEMANTICALLY relevant to completing that subgoal.",
        "",
        "An anchor is relevant if a player performing this subgoal would necessarily",
        "trigger or interact with that code. Exclude anchors that are technically",
        "reachable but serve unrelated functionality.",
        "",
        "=== SUBGOAL ===",
        f"Index: {candidate_set.subgoal_index}",
        f"Description: {candidate_set.subgoal_description}",
        f"Rationale: {candidate_set.subgoal_rationale}",
        "",
        "=== CANDIDATE ANCHORS ===",
    ]

    for anchor in candidate_set.candidates:
        key = _anchor_key(anchor)
        atype = _anchor_type_label(anchor)
        snippet = _anchor_snippet(anchor)
        lines.append(f"[{key}] ({atype}) {snippet}")

    lines.extend([
        "",
        "Return the keys of relevant anchors and a brief rationale.",
    ])

    return "\n".join(lines)
```

- [ ] **Step 4: Run — confirm pass**

```bash
pytest anchor_mapper/tests/test_prompt_builder.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add anchor_mapper/prompt_builder.py anchor_mapper/tests/test_prompt_builder.py
git commit -m "feat(stage4): Phase 4 — prompt builder and FilterResult schema"
```

---

## Task 6: Phase 5 — Anchor Mapper Orchestrator

**Files:**
- Create: `smart/anchor_mapper/anchor_mapper.py`
- Create: `smart/anchor_mapper/tests/test_anchor_mapper.py`

- [ ] **Step 1: Write the failing tests**

Create `smart/anchor_mapper/tests/test_anchor_mapper.py`:

```python
"""Phase 5 tests: anchor mapper orchestrator with mock Anthropic client."""
import os, sys
import pytest
from unittest.mock import MagicMock

# Stage 1 imports FIRST
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch

# Stage 2 imports SECOND (loaded via importlib to avoid clobbering sys.modules["models"])
import importlib.util as _ilu
_s2_spec = _ilu.spec_from_file_location(
    "_s2_models",
    os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator", "models.py"),
)
_s2 = _ilu.module_from_spec(_s2_spec)
_s2_spec.loader.exec_module(_s2)
Subgoal = _s2.Subgoal
SubgoalSequence = _s2.SubgoalSequence

# Stage 4 imports LAST — sys.modules["models"] = Stage 4 at call time
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import AnchorMapping, StructuralAnchorMap, AnchorMappingError
from anchor_mapper import generate_anchor_map
from prompt_builder import FilterResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

# Inline source matching the anchors below
# Line 1: def compute(x):
# Line 2:     if x > 0:
# Line 3:         return x
# Line 4:     return -x
COMPUTE_SOURCE = """\
def compute(x):
    if x > 0:
        return x
    return -x
"""


def make_diff() -> DiffResult:
    return DiffResult(
        file_path="compute.py",
        modified_lines=[ModifiedLine("compute.py", 3, "added", "return x")],
        modified_branches=[ModifiedBranch("compute.py", 2, "if_true", "x > 0")],
    )


def make_seq() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Compute Task",
        summary="Test compute function with if branch.",
        subgoals=[
            Subgoal(index=1, description="Trigger positive branch", rationale="line 2",
                    anchor_hints=["2"]),
        ],
    )


def make_mock_client(relevant_keys=None, stop_reason="end_turn") -> MagicMock:
    mock_response = MagicMock()
    mock_response.stop_reason = stop_reason
    mock_response.parsed_output = FilterResult(
        relevant_keys=relevant_keys if relevant_keys is not None else ["L:3", "B:2:if_true"],
        rationale="Both relevant to subgoal 1",
    )
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestGenerateAnchorMapHappyPath:
    def test_returns_structural_anchor_map(self):
        client = make_mock_client()
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert isinstance(result, StructuralAnchorMap)

    def test_task_name_and_file_path_set(self):
        client = make_mock_client()
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert result.task_name == "Compute Task"
        assert result.file_path == "compute.py"

    def test_mappings_contain_relevant_anchors(self):
        client = make_mock_client(relevant_keys=["L:3"])
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        keys = {m.anchor_key for m in result.mappings}
        assert "L:3" in keys

    def test_for_subgoal_returns_relevant_anchors(self):
        client = make_mock_client(relevant_keys=["L:3"])
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        sg1_anchors = result.for_subgoal(1)
        assert len(sg1_anchors) >= 1
        assert all(1 in a.subgoal_indices for a in sg1_anchors)

    def test_calls_messages_parse_once_per_nonempty_candidate_set(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert client.messages.parse.call_count == 1

    def test_passes_model_to_api(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE,
                            client=client, model="claude-opus-4-6")
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("model") == "claude-opus-4-6"

    def test_passes_output_format(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("output_format") is FilterResult

    def test_use_thinking_adds_kwargs(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE,
                            client=client, use_thinking=True)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("thinking") == {"type": "adaptive"}

    def test_no_thinking_by_default(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert "thinking" not in call_kwargs

    def test_to_dict_on_result(self):
        client = make_mock_client()
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "mappings" in d

    def test_hallucinated_key_discarded(self):
        client = make_mock_client(relevant_keys=["L:3", "L:999"])  # L:999 not in diff
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        keys = {m.anchor_key for m in result.mappings}
        assert "L:999" not in keys

    def test_empty_candidate_sets_returns_empty_mappings(self):
        """Empty diff → no candidates → no LLM calls → empty mappings."""
        empty_diff = DiffResult(file_path="compute.py", modified_lines=[], modified_branches=[])
        client = make_mock_client()
        result = generate_anchor_map(empty_diff, make_seq(), COMPUTE_SOURCE, client=client)
        assert result.mappings == []
        assert client.messages.parse.call_count == 0


class TestGenerateAnchorMapErrorHandling:
    def test_refusal_raises_anchor_mapping_error(self):
        client = make_mock_client(stop_reason="refusal")
        with pytest.raises(AnchorMappingError) as exc_info:
            generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert exc_info.value.stop_reason == "refusal"

    def test_none_parsed_output_raises_error(self):
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.parsed_output = None
        mock_client = MagicMock()
        mock_client.messages.parse.return_value = mock_response
        with pytest.raises(AnchorMappingError):
            generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=mock_client)

    def test_api_error_propagates(self):
        import anthropic
        mock_client = MagicMock()
        mock_client.messages.parse.side_effect = anthropic.APIStatusError(
            message="server error",
            response=MagicMock(status_code=500),
            body={},
        )
        with pytest.raises(anthropic.APIStatusError):
            generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=mock_client)


class TestGenerateAnchorMapClientFactory:
    def test_no_client_raises_env_error_when_no_key(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError):
                generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE)
```

- [ ] **Step 2: Run — confirm fail**

```bash
pytest anchor_mapper/tests/test_anchor_mapper.py -v 2>&1 | head -30
```

Expected: ImportError on `anchor_mapper`.

- [ ] **Step 3: Create `smart/anchor_mapper/anchor_mapper.py`**

```python
"""
SMART Framework - Stage 4: Structural Anchor Mapper
Main entry point: orchestrates Phase 1 (call graph) + Phase 2 (LLM filter)
and returns a validated StructuralAnchorMap.
"""
from __future__ import annotations

import os
import sys
from typing import Optional
import anthropic

_S4_PATH = os.path.dirname(os.path.abspath(__file__))
if _S4_PATH not in sys.path:
    sys.path.insert(0, _S4_PATH)

from client_factory import create_client
from call_graph_analyzer import analyze_call_graph
from prompt_builder import build_prompt, FilterResult


def _make_anchor_key(anchor) -> str:
    """Local helper — matches call_graph_analyzer._make_anchor_key."""
    if hasattr(anchor, "line_number"):
        return f"L:{anchor.line_number}"
    return f"B:{anchor.control_stmt_line}:{anchor.branch_type}"


def generate_anchor_map(
    diff_result,
    subgoal_sequence,
    source_code: str,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
):
    """
    Map each structural anchor to the subgoals where it is semantically relevant.

    Phase 1: AST call graph analysis (intra-file BFS from each subgoal's entry points).
    Phase 2: One Claude call per non-empty CandidateSet to semantically filter candidates.

    Args:
        diff_result: DiffResult from Stage 1 (duck-typed).
        subgoal_sequence: SubgoalSequence from Stage 2 (duck-typed).
        source_code: Full text of the new-version source file.
        client: Anthropic client. If None, created via create_client().
        model: Claude model ID.
        max_tokens: Maximum output tokens per LLM call.
        use_thinking: If True, enable adaptive thinking.

    Returns:
        StructuralAnchorMap — validated mapping of anchors to subgoal indices.

    Raises:
        EnvironmentError: If client is None and ANTHROPIC_API_KEY is not set.
        AnchorMappingError: If Claude refuses or output fails to parse.
        anthropic.APIStatusError: On API-level errors (caller handles retry).
    """
    # Lazy import: resolve Stage 4 models from sys.modules["models"] at call time.
    _cached = sys.modules.get("models")
    if _cached and hasattr(_cached, "AnchorMappingError"):
        _m = _cached
    else:
        if "models" in sys.modules:
            del sys.modules["models"]
        if _S4_PATH not in sys.path:
            sys.path.insert(0, _S4_PATH)
        import models as _m  # type: ignore[import]

    AnchorMappingError = _m.AnchorMappingError
    AnchorMapping = _m.AnchorMapping
    StructuralAnchorMap = _m.StructuralAnchorMap

    if client is None:
        client = create_client()

    # Phase 1: static call graph analysis
    try:
        candidate_sets = analyze_call_graph(diff_result, subgoal_sequence, source_code)
    except ValueError as e:
        raise AnchorMappingError(str(e)) from e

    # Build a key → anchor lookup for metadata retrieval
    all_anchors = list(diff_result.modified_lines) + list(diff_result.modified_branches)
    anchor_lookup = {_make_anchor_key(a): a for a in all_anchors}

    # Phase 2: per-subgoal LLM semantic filtering
    all_mappings: dict[str, set[int]] = {}  # anchor_key → set of subgoal indices

    for candidate_set in candidate_sets:
        if not candidate_set.candidates:
            continue  # skip — no LLM call needed

        valid_keys = {_make_anchor_key(a) for a in candidate_set.candidates}
        prompt = build_prompt(candidate_set)

        kwargs: dict = dict(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            output_format=FilterResult,
        )
        if use_thinking:
            kwargs["thinking"] = {"type": "adaptive"}

        response = client.messages.parse(**kwargs)

        if response.stop_reason == "refusal":
            raise AnchorMappingError(
                f"Claude refused to filter anchors for subgoal {candidate_set.subgoal_index}.",
                stop_reason="refusal",
            )
        if response.parsed_output is None:
            raise AnchorMappingError(
                f"Claude response did not parse for subgoal {candidate_set.subgoal_index}.",
                stop_reason=response.stop_reason,
            )

        for key in response.parsed_output.relevant_keys:
            if key in valid_keys:  # hallucination guard: only accept valid keys
                all_mappings.setdefault(key, set()).add(candidate_set.subgoal_index)

    # Build AnchorMapping objects
    mappings: list = []
    for key, subgoal_indices in all_mappings.items():
        anchor = anchor_lookup.get(key)
        if anchor is None:
            continue
        if hasattr(anchor, "line_number"):
            mappings.append(AnchorMapping(
                anchor_key=key,
                anchor_type="line",
                line_number=anchor.line_number,
                branch_type=None,
                source_snippet=anchor.source,
                subgoal_indices=sorted(subgoal_indices),
            ))
        else:
            mappings.append(AnchorMapping(
                anchor_key=key,
                anchor_type="branch",
                line_number=anchor.control_stmt_line,
                branch_type=anchor.branch_type,
                source_snippet=anchor.condition_source,
                subgoal_indices=sorted(subgoal_indices),
            ))

    return StructuralAnchorMap(
        task_name=subgoal_sequence.task_name,
        file_path=diff_result.file_path,
        mappings=mappings,
    )
```

- [ ] **Step 4: Run — confirm pass**

```bash
cd /Users/xd/Desktop/codes/smart
pytest anchor_mapper/tests/test_anchor_mapper.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add anchor_mapper/anchor_mapper.py anchor_mapper/tests/test_anchor_mapper.py
git commit -m "feat(stage4): Phase 5 — anchor mapper orchestrator"
```

---

## Task 7: Phase 6 — Integration Test

**Files:**
- Create: `smart/anchor_mapper/tests/test_integration.py`

- [ ] **Step 1: Create `smart/anchor_mapper/tests/test_integration.py`**

```python
"""
Phase 6: Integration test — real Claude API call.
Skipped automatically when ANTHROPIC_API_KEY is not set.
Run with: pytest anchor_mapper/tests/test_integration.py -v -s
"""
import os, sys
import pytest

# Stage 1 imports FIRST
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch

# Stage 2 imports via importlib (avoids sys.modules["models"] collision)
import importlib.util as _ilu
_s2_spec = _ilu.spec_from_file_location(
    "_s2_models",
    os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator", "models.py"),
)
_s2 = _ilu.module_from_spec(_s2_spec)
_s2_spec.loader.exec_module(_s2)
Subgoal = _s2.Subgoal
SubgoalSequence = _s2.SubgoalSequence

# Stage 4 imports LAST
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import StructuralAnchorMap
from anchor_mapper import generate_anchor_map

needs_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API integration test",
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

_FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "ast_diff_parser", "tests", "fixtures"
)
_V2_PATH = os.path.join(_FIXTURES_DIR, "math_calc_v2.py")


def make_source_code() -> str:
    with open(_V2_PATH) as f:
        return f.read()


def make_diff_result() -> DiffResult:
    """Synthetic DiffResult with a few representative anchors from math_calc_v2."""
    return DiffResult(
        file_path=_V2_PATH,
        modified_lines=[
            ModifiedLine(_V2_PATH, 31, "modified", "return (f(x + h) - f(x - h)) / (2 * h)"),
            ModifiedLine(_V2_PATH, 69, "added", "def taylor_series(f, x0: float, n: int, x: float) -> float:"),
            ModifiedLine(_V2_PATH, 87, "added", "class MatrixCalculator:"),
        ],
        modified_branches=[
            ModifiedBranch(_V2_PATH, 46, "if_true", 'method == "midpoint"'),
            ModifiedBranch(_V2_PATH, 52, "elif", 'method == "simpson"'),
        ],
    )


def make_subgoal_sequence() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Math Calculator Extended",
        summary="Player uses the calculator to perform matrix operations and Taylor series.",
        subgoals=[
            Subgoal(
                index=1,
                description="Use the derivative function with central difference",
                rationale="derivative modified in v2",
                anchor_hints=["31"],
            ),
            Subgoal(
                index=2,
                description="Apply Taylor series expansion to approximate a function",
                rationale="taylor_series added in v2",
                anchor_hints=["69"],
            ),
            Subgoal(
                index=3,
                description="Perform numerical integration using the Simpson method",
                rationale="integrate gained multi-method support",
                anchor_hints=["52/elif"],
            ),
        ],
    )


# ── Tests ──────────────────────────────────────────────────────────────────────

@needs_key
def test_returns_structural_anchor_map():
    diff = make_diff_result()
    seq = make_subgoal_sequence()
    source = make_source_code()
    result = generate_anchor_map(diff, seq, source)
    assert isinstance(result, StructuralAnchorMap)


@needs_key
def test_at_least_one_mapping_exists():
    diff = make_diff_result()
    seq = make_subgoal_sequence()
    source = make_source_code()
    result = generate_anchor_map(diff, seq, source)
    assert len(result.mappings) >= 1


@needs_key
def test_to_dict_serializable():
    diff = make_diff_result()
    seq = make_subgoal_sequence()
    source = make_source_code()
    result = generate_anchor_map(diff, seq, source)
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "mappings" in d


@needs_key
def test_for_subgoal_does_not_raise_for_valid_index():
    diff = make_diff_result()
    seq = make_subgoal_sequence()
    source = make_source_code()
    result = generate_anchor_map(diff, seq, source)
    for sg in seq.subgoals:
        anchors = result.for_subgoal(sg.index)
        assert isinstance(anchors, list)


@needs_key
def test_prints_readable_report(capsys):
    diff = make_diff_result()
    seq = make_subgoal_sequence()
    source = make_source_code()
    result = generate_anchor_map(diff, seq, source)
    print(f"\n{'='*60}")
    print("SMART Stage 4 — Structural Anchor Map Report")
    print(f"Task: {result.task_name}")
    print(f"Total mapped anchors: {len(result.mappings)}")
    print(f"{'='*60}")
    for mapping in result.mappings:
        print(f"  [{mapping.anchor_key}] ({mapping.anchor_type}) subgoals={mapping.subgoal_indices}")
        print(f"    {mapping.source_snippet[:60]}")
    print(f"{'='*60}")
    captured = capsys.readouterr()
    assert "Stage 4" in captured.out
```

- [ ] **Step 2: Run (expect all skipped without key)**

```bash
cd /Users/xd/Desktop/codes/smart
pytest anchor_mapper/tests/test_integration.py -v
```

Expected: 5 tests SKIPPED (no API key).

- [ ] **Step 3: Commit**

```bash
git add anchor_mapper/tests/test_integration.py
git commit -m "feat(stage4): Phase 6 — integration test"
```

---

## Task 8: Full Regression

- [ ] **Step 1: Run all anchor_mapper tests**

```bash
cd /Users/xd/Desktop/codes/smart
pytest anchor_mapper/tests/ -v
```

Expected: all unit tests pass, integration tests skipped.

- [ ] **Step 2: Run Stage 1 full suite (verify no regression)**

```bash
pytest ast_diff_parser/tests/ -v
```

Expected: all green.

- [ ] **Step 3: Run Stage 2 full suite (verify no regression)**

```bash
pytest subgoal_generator/tests/ -v
```

Expected: all green (3 unit tests + 1 integration test skipped).

- [ ] **Step 4: Run Stage 3 full suite (verify no regression)**

```bash
pytest reward_generator/tests/ -v
```

Expected: all green, integration tests skipped.

- [ ] **Step 5: Commit final**

```bash
git add -A
git commit -m "feat(stage4): complete Stage 4 structural anchor mapper — all tests passing"
```
