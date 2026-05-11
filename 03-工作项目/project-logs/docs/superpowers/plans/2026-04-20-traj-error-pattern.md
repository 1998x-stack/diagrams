# traj-error-pattern Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 3-component system (`agent-error-process` analyzer CLI + `backend` FastAPI + `frontend` Vue 3 SPA) that discovers, classifies, and visualizes error patterns in v2 `.traj` files from `traj-data-new/{wzp,zzj}/`.

**Architecture:** Two-stage analyzer pipeline (rule detectors → Qwen LLM judge) writes per-turn JSON + project-level aggregate JSON to disk. FastAPI serves these JSON files read-only. Vue 3 SPA renders aggregate dashboard + per-turn drill-down with errors annotated inline.

**Tech Stack:** Python 3.11 + Pydantic v2 + FastAPI + uvicorn + Vue 3 + vue-router + TypeScript + Vite + Chart.js. Qwen `qwen3.6-plus` (Dashscope, OpenAI-compatible client) with `enable_thinking=False`.

**Repo conventions:** All paths in this plan are relative to repo root `/Users/xd/Desktop/work/project-logs/`. Spec lives at `docs/superpowers/specs/2026-04-20-traj-error-pattern-design.md`.

---

## Phase 0 — Repo skeleton

### Task 0.1: Create top-level layout

**Files:**
- Create: `traj-error-pattern/README.md`
- Create: `traj-error-pattern/.gitignore`

- [ ] **Step 1: Create directories**

```bash
mkdir -p traj-error-pattern/agent-error-process/src/agent_error_process/{rules,llm}
mkdir -p traj-error-pattern/agent-error-process/{tests,data/per_turn,data/aggregates,data/llm_cache}
mkdir -p traj-error-pattern/backend/{tests,tests/fixtures}
mkdir -p traj-error-pattern/frontend
```

- [ ] **Step 2: Write README.md**

```markdown
# traj-error-pattern

Three-component system for discovering and visualizing agent error patterns in v2 `.traj` files.

- `agent-error-process/` — Python CLI analyzer. Reads `../traj-data-new/{wzp,zzj}/*.traj`, writes JSON to `agent-error-process/data/`.
- `backend/` — FastAPI read-only server over the analyzer output.
- `frontend/` — Vue 3 SPA dashboard.

See `docs/superpowers/specs/2026-04-20-traj-error-pattern-design.md` for the full design.
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.pyc
.venv/
node_modules/
dist/
data/per_turn/
data/aggregates/
data/llm_cache/
.env
```

- [ ] **Step 4: Verify**

Run: `ls traj-error-pattern/`
Expected: shows agent-error-process, backend, frontend, README.md, .gitignore

---

### Task 0.2: Set up agent-error-process package

**Files:**
- Create: `traj-error-pattern/agent-error-process/pyproject.toml`
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/__init__.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "agent-error-process"
version = "0.1.0"
description = "Analyzer for agent trajectory error patterns"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.7",
  "openai>=1.40",
  "click>=8.1",
  "tqdm>=4.66",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-mock>=3.12", "pytest-asyncio>=0.23"]

[project.scripts]
agent-error-process = "agent_error_process.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write package __init__.py**

```python
"""Agent trajectory error pattern analyzer."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Install in editable mode**

Run: `cd traj-error-pattern/agent-error-process && python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
Expected: `Successfully installed agent-error-process-0.1.0`

- [ ] **Step 4: Verify CLI entry stub resolves**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/python -c "import agent_error_process; print(agent_error_process.__version__)"`
Expected: `0.1.0`

---

## Phase 1 — Models & taxonomy

### Task 1.1: Write Pydantic models for input trajectory

**Files:**
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/models_traj.py`
- Create: `traj-error-pattern/agent-error-process/tests/test_models_traj.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models_traj.py
import json
from pathlib import Path
from agent_error_process.models_traj import Trajectory

FIXTURE = Path(__file__).parent / "fixtures" / "sample.traj"

def test_parse_real_traj_file():
    """Loads a real .traj file from traj-data-new/wzp."""
    src = Path("/Users/xd/Desktop/work/project-logs/traj-data-new/wzp/014354fc.traj")
    data = json.loads(src.read_text())
    traj = Trajectory.model_validate(data)
    assert traj.session_metadata.project == "wzp"
    assert traj.summary.total_turns >= 1
    assert len(traj.messages) > 0

def test_step_with_error_status():
    data = {
        "schema_version": "2.0", "conversation_id": "x", "agent": "claude",
        "session_metadata": {"project": "wzp", "session_id": "x", "started_at": "2026-01-01T00:00:00Z", "ended_at": "2026-01-01T00:01:00Z"},
        "messages": [
            {"turn_id": 1, "role": "user", "content": "hi", "timestamp": "2026-01-01T00:00:00Z"},
            {"turn_id": 1, "agent_run_id": "run_t1", "steps": [
                {"step_id": 1, "phase": "editing", "thinking": None, "thought": None,
                 "action": {"tool_name": "Edit", "tool_use_id": "t1", "args": {}},
                 "observation": {"type": "edit_error", "text": "syntax error", "exit_code": 1},
                 "state": None, "status": "error", "timestamp": "2026-01-01T00:00:01Z",
                 "execution_time": 0.1, "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0, "cache_creation_tokens": 0}}
            ], "run_summary": None}
        ],
        "phases": [], "markers": [], "subagents": [],
        "summary": {"total_turns": 1, "total_steps": 1, "total_tool_calls": 1, "total_subagents": 0, "total_input_tokens": 1, "total_output_tokens": 1, "total_cache_read_tokens": 0, "total_cache_creation_tokens": 0, "exit_reason": "end", "status": "completed", "first_user_prompt": "hi"}
    }
    traj = Trajectory.model_validate(data)
    run = traj.messages[1]
    assert run.steps[0].status == "error"
    assert run.steps[0].observation.exit_code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_models_traj.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent_error_process.models_traj'`

- [ ] **Step 3: Write models_traj.py**

```python
# src/agent_error_process/models_traj.py
"""Pydantic models for the v2 .traj input format."""
from __future__ import annotations
from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

class Action(BaseModel):
    model_config = ConfigDict(extra="allow")
    tool_name: str
    tool_use_id: str = ""
    args: dict[str, Any] = Field(default_factory=dict)

class Observation(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str
    text: str = ""
    exit_code: Optional[int] = None
    error_kind: Optional[str] = None

class Usage(BaseModel):
    model_config = ConfigDict(extra="allow")
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

class Step(BaseModel):
    model_config = ConfigDict(extra="allow")
    step_id: int
    phase: Optional[str] = None
    thinking: Optional[str] = None
    thought: Optional[str] = None
    action: Action
    observation: Observation
    state: Optional[dict[str, Any]] = None
    status: Literal["ok", "error"] = "ok"
    timestamp: str
    execution_time: float = 0.0
    usage: Optional[Usage] = None
    marker: Optional[str] = None
    marker_reason: Optional[str] = None

class UserMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    turn_id: int
    role: Literal["user"]
    content: str
    timestamp: str

class RunSummary(BaseModel):
    model_config = ConfigDict(extra="allow")
    steps_count: Optional[int] = None
    tool_calls_count: Optional[int] = None
    edit_failures: Optional[int] = None
    result: Optional[str] = None

class AgentRun(BaseModel):
    model_config = ConfigDict(extra="allow")
    turn_id: int
    agent_run_id: str
    steps: list[Step] = Field(default_factory=list)
    run_summary: Optional[RunSummary] = None

Message = Union[UserMessage, AgentRun]

class SessionMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    project: str
    project_name: Optional[str] = None
    session_id: str
    started_at: str
    ended_at: Optional[str] = None
    duration_sec: Optional[float] = None

class TrajSummary(BaseModel):
    model_config = ConfigDict(extra="allow")
    total_turns: int = 0
    total_steps: int = 0
    total_tool_calls: int = 0
    total_subagents: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_creation_tokens: int = 0
    exit_reason: Optional[str] = None
    status: Optional[str] = None
    first_user_prompt: Optional[str] = None

class Trajectory(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: str
    conversation_id: str
    agent: Optional[str] = None
    session_metadata: SessionMetadata
    messages: list[Union[UserMessage, AgentRun]]
    phases: list[Any] = Field(default_factory=list)
    markers: list[Any] = Field(default_factory=list)
    subagents: list[Any] = Field(default_factory=list)
    summary: TrajSummary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_models_traj.py -v`
Expected: PASS, 2 tests

- [ ] **Step 5: Commit**

```bash
git add traj-error-pattern/agent-error-process/src/agent_error_process/models_traj.py \
        traj-error-pattern/agent-error-process/tests/test_models_traj.py
git commit -m "feat(analyzer): add input Trajectory pydantic models"
```

---

### Task 1.2: Write taxonomy enums

**Files:**
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/taxonomy.py`
- Create: `traj-error-pattern/agent-error-process/tests/test_taxonomy.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_taxonomy.py
from agent_error_process.taxonomy import Category, Subtype, SUBTYPES_BY_CATEGORY, TAXONOMY_VERSION

def test_taxonomy_version_is_string():
    assert isinstance(TAXONOMY_VERSION, str)
    assert TAXONOMY_VERSION

def test_every_subtype_belongs_to_one_category():
    seen = set()
    for cat, subs in SUBTYPES_BY_CATEGORY.items():
        for s in subs:
            assert s not in seen, f"duplicate subtype {s}"
            seen.add(s)

def test_known_subtypes_present():
    for s in [
        Subtype.TOOL_EXIT_NONZERO, Subtype.EDIT_REJECTED, Subtype.LSP_DIAGNOSTIC,
        Subtype.WRITE_WITHOUT_READ, Subtype.REDUNDANT_READ, Subtype.REDUNDANT_WRITE,
        Subtype.EDIT_WITHOUT_VERIFY, Subtype.SUBMISSION_WITHOUT_TEST,
        Subtype.SEARCH_LOOP, Subtype.TOOL_THRASH,
        Subtype.MISREAD_INTENT, Subtype.LAZY_FIX,
        Subtype.REPEATED_CORRECTION,
    ]:
        assert s.value
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_taxonomy.py -v`
Expected: FAIL `ModuleNotFoundError`

- [ ] **Step 3: Write taxonomy.py**

```python
# src/agent_error_process/taxonomy.py
"""2-level error taxonomy. Single source of truth.

Bumping TAXONOMY_VERSION invalidates the LLM cache.
"""
from __future__ import annotations
from enum import Enum

TAXONOMY_VERSION = "v1"

class Category(str, Enum):
    TOOL_FAILURE = "tool_failure"
    CONTEXT_HYGIENE = "context_hygiene"
    VERIFICATION_GAP = "verification_gap"
    CONTROL_FLOW = "control_flow"
    INTENT_ALIGNMENT = "intent_alignment"   # LLM
    USER_CORRECTION = "user_correction"     # LLM

class Subtype(str, Enum):
    # tool_failure
    TOOL_EXIT_NONZERO = "tool_failure.tool_exit_nonzero"
    EDIT_REJECTED = "tool_failure.edit_rejected"
    LSP_DIAGNOSTIC = "tool_failure.lsp_diagnostic"
    MCP_CALL_ERROR = "tool_failure.mcp_call_error"
    # context_hygiene
    WRITE_WITHOUT_READ = "context_hygiene.write_without_read"
    REDUNDANT_READ = "context_hygiene.redundant_read"
    REDUNDANT_WRITE = "context_hygiene.redundant_write"
    STALE_READ = "context_hygiene.stale_read"
    # verification_gap
    EDIT_WITHOUT_VERIFY = "verification_gap.edit_without_verify"
    SUBMISSION_WITHOUT_TEST = "verification_gap.submission_without_test"
    IGNORED_TEST_FAILURE = "verification_gap.ignored_test_failure"
    # control_flow
    SEARCH_LOOP = "control_flow.search_loop"
    TOOL_THRASH = "control_flow.tool_thrash"
    PHASE_OSCILLATION = "control_flow.phase_oscillation"
    # intent_alignment (LLM)
    MISREAD_INTENT = "intent_alignment.misread_intent"
    PARTIAL_COMPLETION = "intent_alignment.partial_completion"
    OVER_SCOPE = "intent_alignment.over_scope"
    LAZY_FIX = "intent_alignment.lazy_fix"
    # user_correction (LLM)
    REPEATED_CORRECTION = "user_correction.repeated_correction"
    INSTRUCTION_DRIFT = "user_correction.instruction_drift"
    CONFUSED_RESPONSE = "user_correction.confused_response"

SUBTYPES_BY_CATEGORY: dict[Category, list[Subtype]] = {
    Category.TOOL_FAILURE: [Subtype.TOOL_EXIT_NONZERO, Subtype.EDIT_REJECTED, Subtype.LSP_DIAGNOSTIC, Subtype.MCP_CALL_ERROR],
    Category.CONTEXT_HYGIENE: [Subtype.WRITE_WITHOUT_READ, Subtype.REDUNDANT_READ, Subtype.REDUNDANT_WRITE, Subtype.STALE_READ],
    Category.VERIFICATION_GAP: [Subtype.EDIT_WITHOUT_VERIFY, Subtype.SUBMISSION_WITHOUT_TEST, Subtype.IGNORED_TEST_FAILURE],
    Category.CONTROL_FLOW: [Subtype.SEARCH_LOOP, Subtype.TOOL_THRASH, Subtype.PHASE_OSCILLATION],
    Category.INTENT_ALIGNMENT: [Subtype.MISREAD_INTENT, Subtype.PARTIAL_COMPLETION, Subtype.OVER_SCOPE, Subtype.LAZY_FIX],
    Category.USER_CORRECTION: [Subtype.REPEATED_CORRECTION, Subtype.INSTRUCTION_DRIFT, Subtype.CONFUSED_RESPONSE],
}

LLM_CATEGORIES: set[Category] = {Category.INTENT_ALIGNMENT, Category.USER_CORRECTION}

def category_of(subtype: Subtype) -> Category:
    for cat, subs in SUBTYPES_BY_CATEGORY.items():
        if subtype in subs:
            return cat
    raise ValueError(f"unknown subtype {subtype}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_taxonomy.py -v`
Expected: PASS, 3 tests

- [ ] **Step 5: Commit**

```bash
git add traj-error-pattern/agent-error-process/src/agent_error_process/taxonomy.py \
        traj-error-pattern/agent-error-process/tests/test_taxonomy.py
git commit -m "feat(analyzer): add 2-level error taxonomy"
```

---

### Task 1.3: Write output models (Finding, ErrorReport, Aggregate)

**Files:**
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/models.py`
- Create: `traj-error-pattern/agent-error-process/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from agent_error_process.models import (
    Finding, RuleSignal, LlmFinding, ErrorReport, Severity, Source,
    SessionReport, ProjectAggregate,
)
from agent_error_process.taxonomy import Category, Subtype

def test_rule_finding_round_trips():
    f = Finding(
        finding_id="wzp_abc_t1_f1",
        category=Category.CONTEXT_HYGIENE,
        subtype=Subtype.WRITE_WITHOUT_READ,
        severity=Severity.MED,
        source=Source.RULE,
        step_ids=[4, 7],
        evidence={"tool_name": "Edit", "path": "src/foo.lua"},
        rule_id="context_hygiene.write_without_read.v1",
    )
    js = f.model_dump_json()
    f2 = Finding.model_validate_json(js)
    assert f2.severity == Severity.MED
    assert f2.source == Source.RULE

def test_llm_finding_carries_confidence_and_hypothesis():
    f = Finding(
        finding_id="wzp_abc_t1_f2",
        category=Category.INTENT_ALIGNMENT,
        subtype=Subtype.LAZY_FIX,
        severity=Severity.HIGH,
        source=Source.LLM,
        step_ids=[12],
        confidence=0.82,
        root_cause_hypothesis="suppressed warning instead of fixing nil",
        evidence_text="wrapped in pcall",
        judge_prompt_version="v1",
        judge_model="qwen3.6-plus",
    )
    assert f.confidence == 0.82
    assert f.judge_model == "qwen3.6-plus"

def test_error_report_groups_findings_per_turn():
    rep = ErrorReport(
        turn_id=3,
        agent_run_id="run_t3",
        user_message_excerpt="hi",
        step_count=10,
        tool_calls_count=8,
        findings=[],
        metrics={"tool_failure_count": 0},
    )
    assert rep.turn_id == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_models.py -v`
Expected: FAIL `ModuleNotFoundError`

- [ ] **Step 3: Write models.py**

```python
# src/agent_error_process/models.py
"""Output JSON contract: per-turn findings + aggregates."""
from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from .taxonomy import Category, Subtype

OUTPUT_SCHEMA_VERSION = "1.0"

class Severity(str, Enum):
    LOW = "low"
    MED = "med"
    HIGH = "high"

class Source(str, Enum):
    RULE = "rule"
    LLM = "llm"

class Finding(BaseModel):
    """A single error finding (rule- or LLM-sourced)."""
    model_config = ConfigDict(use_enum_values=True)
    finding_id: str
    category: Category
    subtype: Subtype
    severity: Severity
    source: Source
    step_ids: list[int] = Field(default_factory=list)
    # rule-source extras
    evidence: Optional[dict[str, Any]] = None
    rule_id: Optional[str] = None
    # llm-source extras
    evidence_text: Optional[str] = None
    confidence: Optional[float] = None
    root_cause_hypothesis: Optional[str] = None
    judge_prompt_version: Optional[str] = None
    judge_model: Optional[str] = None

class RuleSignal(BaseModel):
    """Output of a rule detector before merging into Finding."""
    category: Category
    subtype: Subtype
    severity: Severity
    step_ids: list[int]
    evidence: dict[str, Any] = Field(default_factory=dict)
    rule_id: str

class LlmFinding(BaseModel):
    """Output schema returned by the LLM judge."""
    subtype: Subtype
    severity: Severity
    step_ids: list[int]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_text: str
    root_cause_hypothesis: str

class ErrorReport(BaseModel):
    """All findings for one turn."""
    turn_id: int
    agent_run_id: str
    user_message_excerpt: str
    step_count: int
    tool_calls_count: int
    findings: list[Finding]
    metrics: dict[str, int] = Field(default_factory=dict)

class SessionReport(BaseModel):
    """All findings for one session."""
    schema_version: str = OUTPUT_SCHEMA_VERSION
    project: str
    session_hash: str
    session_id: str
    generated_at: str
    turns: list[ErrorReport]

class FindingExample(BaseModel):
    session_hash: str
    turn_id: int
    finding_id: str

class TopOffendingSession(BaseModel):
    session_hash: str
    high_severity_count: int
    total_findings: int

class ProjectAggregate(BaseModel):
    schema_version: str = OUTPUT_SCHEMA_VERSION
    project: str
    generated_at: str
    session_count: int
    turn_count: int
    totals_by_category: dict[str, int]
    totals_by_subtype: dict[str, int]
    severity_breakdown: dict[str, int]
    by_tool: dict[str, dict[str, Any]]
    by_phase: dict[str, dict[str, Any]]
    top_offending_sessions: list[TopOffendingSession]
    examples_per_subtype: dict[str, list[FindingExample]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_models.py -v`
Expected: PASS, 3 tests

- [ ] **Step 5: Commit**

```bash
git add traj-error-pattern/agent-error-process/src/agent_error_process/models.py \
        traj-error-pattern/agent-error-process/tests/test_models.py
git commit -m "feat(analyzer): add output Finding/ErrorReport/Aggregate models"
```

---

## Phase 2 — Loader & turn iteration

### Task 2.1: Loader iterates turns

**Files:**
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/loader.py`
- Create: `traj-error-pattern/agent-error-process/tests/test_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_loader.py
from pathlib import Path
from agent_error_process.loader import load_trajectory, iter_turns, session_hash_from_path

WZP = Path("/Users/xd/Desktop/work/project-logs/traj-data-new/wzp/014354fc.traj")

def test_session_hash_is_basename_stem():
    assert session_hash_from_path(WZP) == "014354fc"

def test_iter_turns_pairs_user_with_run():
    traj = load_trajectory(WZP)
    turns = list(iter_turns(traj))
    assert len(turns) >= 1
    t0 = turns[0]
    assert t0.user.role == "user"
    assert t0.run.turn_id == t0.user.turn_id
    assert isinstance(t0.run.steps, list)

def test_iter_turns_handles_orphan_user_message():
    """A user message not followed by a run should be skipped or marked."""
    from agent_error_process.models_traj import Trajectory, UserMessage, SessionMetadata, TrajSummary
    data = {
        "schema_version":"2.0","conversation_id":"x","agent":"c",
        "session_metadata":{"project":"wzp","session_id":"x","started_at":"2026-01-01T00:00:00Z"},
        "messages":[{"turn_id":1,"role":"user","content":"hi","timestamp":"2026-01-01T00:00:00Z"}],
        "phases":[],"markers":[],"subagents":[],
        "summary":{"total_turns":1,"total_steps":0,"total_tool_calls":0,"total_subagents":0,
                   "total_input_tokens":0,"total_output_tokens":0,"total_cache_read_tokens":0,
                   "total_cache_creation_tokens":0,"exit_reason":"end","status":"completed","first_user_prompt":"hi"}
    }
    traj = Trajectory.model_validate(data)
    turns = list(iter_turns(traj))
    assert turns == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_loader.py -v`
Expected: FAIL `ModuleNotFoundError`

- [ ] **Step 3: Write loader.py**

```python
# src/agent_error_process/loader.py
"""Read .traj files and iterate turns (user_msg + agent_run)."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from .models_traj import Trajectory, UserMessage, AgentRun

@dataclass
class Turn:
    user: UserMessage
    run: AgentRun

def session_hash_from_path(path: Path) -> str:
    return path.stem

def load_trajectory(path: Path) -> Trajectory:
    return Trajectory.model_validate_json(path.read_text(encoding="utf-8"))

def iter_turns(traj: Trajectory) -> Iterator[Turn]:
    """Yield (user_message, agent_run) pairs sharing the same turn_id."""
    msgs = traj.messages
    i = 0
    while i < len(msgs):
        m = msgs[i]
        if isinstance(m, UserMessage):
            j = i + 1
            if j < len(msgs) and isinstance(msgs[j], AgentRun) and msgs[j].turn_id == m.turn_id:
                yield Turn(user=m, run=msgs[j])
                i = j + 1
                continue
        i += 1

def iter_traj_files(root: Path, project: str) -> Iterator[Path]:
    yield from sorted((root / project).glob("*.traj"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/test_loader.py -v`
Expected: PASS, 3 tests

- [ ] **Step 5: Commit**

```bash
git add src/agent_error_process/loader.py tests/test_loader.py
git commit -m "feat(analyzer): add trajectory loader with turn iterator"
```

---

## Phase 3 — Rule detectors

Each detector is a function `detect(turn: Turn) -> list[RuleSignal]`. Pure, no I/O, deterministic.

### Task 3.1: Common helpers + rules package init

**Files:**
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/rules/__init__.py`
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/rules/_common.py`

- [ ] **Step 1: Write _common.py**

```python
# src/agent_error_process/rules/_common.py
"""Helpers shared across rule detectors."""
from __future__ import annotations
from typing import Iterable
from ..models_traj import Step

READ_TOOLS = {"Read", "mcp__mkr__Read"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit",
               "mcp__mkr__Write", "mcp__mkr__Edit"}
SEARCH_TOOLS = {"Glob", "Grep", "mcp__mkr__Glob", "mcp__mkr__Grep"}
VERIFY_TOOLS = {"Bash"}  # plus tool_name endings detected via heuristic

def file_path_from_args(args: dict) -> str | None:
    for k in ("file_path", "path", "notebook_path"):
        v = args.get(k)
        if isinstance(v, str):
            return v
    return None

def is_read_step(step: Step) -> bool:
    return step.action.tool_name in READ_TOOLS

def is_write_step(step: Step) -> bool:
    return step.action.tool_name in WRITE_TOOLS

def is_search_step(step: Step) -> bool:
    return step.action.tool_name in SEARCH_TOOLS

def is_verify_step(step: Step) -> bool:
    """Heuristic: bash steps that look like test/build/lint runs."""
    if step.action.tool_name not in VERIFY_TOOLS:
        return False
    cmd = (step.action.args.get("command") or "").lower()
    return any(tok in cmd for tok in (
        "pytest", "npm test", "npm run", "go test", "cargo test",
        "lua ", "test", "lint", "tsc", "build", "make ", "ruff", "mypy",
    ))

def truncate(text: str, n: int = 240) -> str:
    if not text:
        return ""
    return text if len(text) <= n else text[:n] + "..."
```

- [ ] **Step 2: Write rules/__init__.py**

```python
# src/agent_error_process/rules/__init__.py
"""Rule detector registry."""
from __future__ import annotations
from typing import Callable
from ..loader import Turn
from ..models import RuleSignal

from . import tool_failure, context_hygiene, edit_churn, verification_gap, lsp_error, user_correction

Detector = Callable[[Turn], list[RuleSignal]]

ALL_DETECTORS: list[Detector] = [
    tool_failure.detect,
    context_hygiene.detect,
    edit_churn.detect,
    verification_gap.detect,
    lsp_error.detect,
    user_correction.detect,
]

def run_all(turn: Turn) -> list[RuleSignal]:
    out: list[RuleSignal] = []
    for d in ALL_DETECTORS:
        out.extend(d(turn))
    return out
```

- [ ] **Step 3: Commit**

```bash
git add src/agent_error_process/rules/__init__.py src/agent_error_process/rules/_common.py
git commit -m "feat(analyzer): rules package + shared helpers"
```

(Each detector below provides its own implementation; `run_all` will work once they exist.)

---

### Task 3.2: Detector — tool_failure

**Files:**
- Create: `traj-error-pattern/agent-error-process/src/agent_error_process/rules/tool_failure.py`
- Create: `traj-error-pattern/agent-error-process/tests/rules/__init__.py` (empty)
- Create: `traj-error-pattern/agent-error-process/tests/rules/test_tool_failure.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/rules/test_tool_failure.py
from agent_error_process.models_traj import Step, Action, Observation, AgentRun, UserMessage
from agent_error_process.loader import Turn
from agent_error_process.rules import tool_failure
from agent_error_process.taxonomy import Subtype

def _step(step_id, tool, otype="tool_result", exit_code=None, status="ok", text=""):
    return Step(
        step_id=step_id, phase="editing", thinking=None, thought=None,
        action=Action(tool_name=tool, tool_use_id=f"t{step_id}", args={}),
        observation=Observation(type=otype, text=text, exit_code=exit_code),
        state=None, status=status, timestamp="2026-01-01T00:00:00Z", execution_time=0.0,
        usage=None,
    )

def _turn(steps):
    user = UserMessage(turn_id=1, role="user", content="hi", timestamp="2026-01-01T00:00:00Z")
    run = AgentRun(turn_id=1, agent_run_id="run_t1", steps=steps, run_summary=None)
    return Turn(user=user, run=run)

def test_detects_nonzero_exit():
    turn = _turn([_step(1, "Bash", exit_code=1, status="error", text="boom")])
    sigs = tool_failure.detect(turn)
    assert any(s.subtype == Subtype.TOOL_EXIT_NONZERO for s in sigs)

def test_detects_edit_rejected():
    turn = _turn([_step(1, "Edit", otype="edit_error", exit_code=1, status="error", text="syntax")])
    sigs = tool_failure.detect(turn)
    assert any(s.subtype == Subtype.EDIT_REJECTED for s in sigs)

def test_detects_mcp_error():
    turn = _turn([_step(1, "mcp__mkr__Read", exit_code=1, status="error", text="not found")])
    sigs = tool_failure.detect(turn)
    assert any(s.subtype == Subtype.MCP_CALL_ERROR for s in sigs)

def test_clean_steps_emit_nothing():
    turn = _turn([_step(1, "Bash", exit_code=0, status="ok", text="ok")])
    assert tool_failure.detect(turn) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd traj-error-pattern/agent-error-process && .venv/bin/pytest tests/rules/test_tool_failure.py -v`
Expected: FAIL

- [ ] **Step 3: Write tool_failure.py**

```python
# src/agent_error_process/rules/tool_failure.py
"""Detector for category 1: tool_failure."""
from __future__ import annotations
from ..loader import Turn
from ..models import RuleSignal, Severity
from ..taxonomy import Category, Subtype
from ._common import truncate

def detect(turn: Turn) -> list[RuleSignal]:
    out: list[RuleSignal] = []
    for s in turn.run.steps:
        obs = s.observation
        tname = s.action.tool_name
        if obs.type == "edit_error":
            out.append(RuleSignal(
                category=Category.TOOL_FAILURE, subtype=Subtype.EDIT_REJECTED,
                severity=Severity.MED, step_ids=[s.step_id],
                evidence={"tool_name": tname, "text": truncate(obs.text)},
                rule_id="tool_failure.edit_rejected.v1",
            ))
        elif tname.startswith("mcp__") and (s.status == "error" or (obs.exit_code is not None and obs.exit_code != 0)):
            out.append(RuleSignal(
                category=Category.TOOL_FAILURE, subtype=Subtype.MCP_CALL_ERROR,
                severity=Severity.MED, step_ids=[s.step_id],
                evidence={"tool_name": tname, "text": truncate(obs.text)},
                rule_id="tool_failure.mcp_call_error.v1",
            ))
        elif obs.exit_code is not None and obs.exit_code != 0:
            out.append(RuleSignal(
                category=Category.TOOL_FAILURE, subtype=Subtype.TOOL_EXIT_NONZERO,
                severity=Severity.MED, step_ids=[s.step_id],
                evidence={"tool_name": tname, "exit_code": obs.exit_code, "text": truncate(obs.text)},
                rule_id="tool_failure.tool_exit_nonzero.v1",
            ))
    return out
```

- [ ] **Step 4: Run test, verify pass, commit**

Run: `.venv/bin/pytest tests/rules/test_tool_failure.py -v`
Expected: PASS, 4 tests

```bash
git add src/agent_error_process/rules/tool_failure.py tests/rules/
git commit -m "feat(rules): tool_failure detector"
```

---

### Task 3.3: Detector — lsp_error

**Files:**
- Create: `src/agent_error_process/rules/lsp_error.py`
- Create: `tests/rules/test_lsp_error.py`

- [ ] **Step 1: Test**

```python
# tests/rules/test_lsp_error.py
from tests.rules.test_tool_failure import _step, _turn
from agent_error_process.rules import lsp_error
from agent_error_process.taxonomy import Subtype

def test_detects_syntax_error_in_text():
    turn = _turn([_step(1, "Bash", exit_code=1, status="error",
                        text="SyntaxError: invalid syntax at line 5")])
    sigs = lsp_error.detect(turn)
    assert any(s.subtype == Subtype.LSP_DIAGNOSTIC for s in sigs)

def test_detects_lua_error():
    turn = _turn([_step(1, "Bash", exit_code=1, status="error",
                        text="lua: src/foo.lua:10: attempt to index a nil value")])
    sigs = lsp_error.detect(turn)
    assert any(s.subtype == Subtype.LSP_DIAGNOSTIC for s in sigs)

def test_no_match():
    turn = _turn([_step(1, "Bash", exit_code=0, text="ok")])
    assert lsp_error.detect(turn) == []
```

- [ ] **Step 2: Run + fail**

`.venv/bin/pytest tests/rules/test_lsp_error.py -v` → FAIL

- [ ] **Step 3: Implement**

```python
# src/agent_error_process/rules/lsp_error.py
"""Refines tool_failure observations into LSP-style diagnostics."""
from __future__ import annotations
import re
from ..loader import Turn
from ..models import RuleSignal, Severity
from ..taxonomy import Category, Subtype
from ._common import truncate

PATTERNS = [
    (re.compile(r"SyntaxError|invalid syntax", re.I), "syntax"),
    (re.compile(r"NameError|undefined (?:variable|name)", re.I), "name"),
    (re.compile(r"TypeError|type mismatch", re.I), "type"),
    (re.compile(r"\battempt to (?:index|call)\b", re.I), "lua_runtime"),
    (re.compile(r"cannot find module|module not found", re.I), "import"),
]

def detect(turn: Turn) -> list[RuleSignal]:
    out: list[RuleSignal] = []
    for s in turn.run.steps:
        text = s.observation.text or ""
        for pat, kind in PATTERNS:
            if pat.search(text):
                out.append(RuleSignal(
                    category=Category.TOOL_FAILURE, subtype=Subtype.LSP_DIAGNOSTIC,
                    severity=Severity.MED, step_ids=[s.step_id],
                    evidence={"diagnostic_kind": kind, "tool_name": s.action.tool_name,
                              "text": truncate(text)},
                    rule_id=f"tool_failure.lsp_diagnostic.{kind}.v1",
                ))
                break
    return out
```

- [ ] **Step 4: Pass + commit**

```bash
.venv/bin/pytest tests/rules/test_lsp_error.py -v
git add src/agent_error_process/rules/lsp_error.py tests/rules/test_lsp_error.py
git commit -m "feat(rules): lsp_error diagnostic refiner"
```

---

### Task 3.4: Detector — context_hygiene

**Files:**
- Create: `src/agent_error_process/rules/context_hygiene.py`
- Create: `tests/rules/test_context_hygiene.py`

- [ ] **Step 1: Test**

```python
# tests/rules/test_context_hygiene.py
from tests.rules.test_tool_failure import _step, _turn
from agent_error_process.models_traj import Action
from agent_error_process.rules import context_hygiene
from agent_error_process.taxonomy import Subtype

def _tool_step(sid, tool, path):
    s = _step(sid, tool, exit_code=0)
    s.action = Action(tool_name=tool, tool_use_id=f"t{sid}", args={"file_path": path})
    return s

def test_write_without_read():
    turn = _turn([_tool_step(1, "Edit", "/a.lua")])
    sigs = context_hygiene.detect(turn)
    assert any(s.subtype == Subtype.WRITE_WITHOUT_READ for s in sigs)

def test_read_then_write_is_clean():
    turn = _turn([_tool_step(1, "Read", "/a.lua"), _tool_step(2, "Edit", "/a.lua")])
    sigs = context_hygiene.detect(turn)
    assert not any(s.subtype == Subtype.WRITE_WITHOUT_READ for s in sigs)

def test_redundant_read():
    steps = [_tool_step(i, "Read", "/a.lua") for i in range(1, 5)]
    turn = _turn(steps)
    sigs = context_hygiene.detect(turn)
    assert any(s.subtype == Subtype.REDUNDANT_READ for s in sigs)

def test_redundant_write():
    steps = [_tool_step(1, "Read", "/a.lua")] + [_tool_step(i, "Edit", "/a.lua") for i in range(2, 7)]
    turn = _turn(steps)
    sigs = context_hygiene.detect(turn)
    assert any(s.subtype == Subtype.REDUNDANT_WRITE for s in sigs)

def test_stale_read():
    steps = [_tool_step(1, "Read", "/a.lua")]
    # 12 unrelated steps in between
    for i in range(2, 14):
        steps.append(_tool_step(i, "Bash", "/other"))
        steps[-1].action = Action(tool_name="Bash", tool_use_id=f"t{i}", args={"command": "echo"})
    steps.append(_tool_step(14, "Edit", "/a.lua"))
    turn = _turn(steps)
    sigs = context_hygiene.detect(turn)
    assert any(s.subtype == Subtype.STALE_READ for s in sigs)
```

- [ ] **Step 2: Run + fail**

- [ ] **Step 3: Implement**

```python
# src/agent_error_process/rules/context_hygiene.py
"""Detector for category 2: context_hygiene."""
from __future__ import annotations
from collections import defaultdict
from ..loader import Turn
from ..models import RuleSignal, Severity
from ..taxonomy import Category, Subtype
from ._common import file_path_from_args, is_read_step, is_write_step

STALE_READ_GAP = 10  # steps between Read and Edit

def detect(turn: Turn) -> list[RuleSignal]:
    out: list[RuleSignal] = []
    steps = turn.run.steps
    last_read_step: dict[str, int] = {}   # path -> step_index
    read_count: dict[str, list[int]] = defaultdict(list)
    write_count: dict[str, list[int]] = defaultdict(list)

    for idx, s in enumerate(steps):
        path = file_path_from_args(s.action.args)
        if not path:
            continue
        if is_read_step(s):
            read_count[path].append(s.step_id)
            last_read_step[path] = idx
        elif is_write_step(s):
            write_count[path].append(s.step_id)
            if path not in last_read_step:
                out.append(RuleSignal(
                    category=Category.CONTEXT_HYGIENE, subtype=Subtype.WRITE_WITHOUT_READ,
                    severity=Severity.MED, step_ids=[s.step_id],
                    evidence={"path": path, "tool_name": s.action.tool_name},
                    rule_id="context_hygiene.write_without_read.v1",
                ))
            else:
                gap = idx - last_read_step[path]
                if gap > STALE_READ_GAP:
                    out.append(RuleSignal(
                        category=Category.CONTEXT_HYGIENE, subtype=Subtype.STALE_READ,
                        severity=Severity.LOW, step_ids=[s.step_id],
                        evidence={"path": path, "gap_steps": gap},
                        rule_id="context_hygiene.stale_read.v1",
                    ))

    for path, sids in read_count.items():
        if len(sids) >= 3:
            out.append(RuleSignal(
                category=Category.CONTEXT_HYGIENE, subtype=Subtype.REDUNDANT_READ,
                severity=Severity.LOW, step_ids=sids,
                evidence={"path": path, "count": len(sids)},
                rule_id="context_hygiene.redundant_read.v1",
            ))
    for path, sids in write_count.items():
        if len(sids) >= 4:
            out.append(RuleSignal(
                category=Category.CONTEXT_HYGIENE, subtype=Subtype.REDUNDANT_WRITE,
                severity=Severity.MED, step_ids=sids,
                evidence={"path": path, "count": len(sids)},
                rule_id="context_hygiene.redundant_write.v1",
            ))
    return out
```

- [ ] **Step 4: Pass + commit**

```bash
.venv/bin/pytest tests/rules/test_context_hygiene.py -v
git add src/agent_error_process/rules/context_hygiene.py tests/rules/test_context_hygiene.py
git commit -m "feat(rules): context_hygiene detector"
```

---

### Task 3.5: Detector — verification_gap

**Files:**
- Create: `src/agent_error_process/rules/verification_gap.py`
- Create: `tests/rules/test_verification_gap.py`

- [ ] **Step 1: Test**

```python
# tests/rules/test_verification_gap.py
from tests.rules.test_tool_failure import _step, _turn
from agent_error_process.models_traj import Action, Observation, RunSummary
from agent_error_process.rules import verification_gap
from agent_error_process.taxonomy import Subtype

def test_edit_without_verify_fires_after_4_consecutive_edits():
    steps = [_step(i, "Edit", exit_code=0) for i in range(1, 6)]
    sigs = verification_gap.detect(_turn(steps))
    assert any(s.subtype == Subtype.EDIT_WITHOUT_VERIFY for s in sigs)

def test_edits_broken_by_test_run_clears():
    steps = [_step(1, "Edit"), _step(2, "Edit")]
    bash = _step(3, "Bash")
    bash.action = Action(tool_name="Bash", tool_use_id="t3", args={"command": "pytest tests/"})
    steps.append(bash)
    steps += [_step(4, "Edit"), _step(5, "Edit")]
    sigs = verification_gap.detect(_turn(steps))
    assert not any(s.subtype == Subtype.EDIT_WITHOUT_VERIFY for s in sigs)

def test_ignored_test_failure():
    s1 = _step(1, "Bash", exit_code=1, status="error", text="1 failed")
    s1.observation = Observation(type="test_result", text="1 failed", exit_code=1)
    s2 = _step(2, "respond_to_user")
    sigs = verification_gap.detect(_turn([s1, s2]))
    assert any(s.subtype == Subtype.IGNORED_TEST_FAILURE for s in sigs)
```

- [ ] **Step 2: Run + fail**

- [ ] **Step 3: Implement**

```python
# src/agent_error_process/rules/verification_gap.py
"""Detector for category 3: verification_gap."""
from __future__ import annotations
from ..loader import Turn
from ..models import RuleSignal, Severity
from ..taxonomy import Category, Subtype
from ._common import is_write_step, is_verify_step

CONSECUTIVE_EDITS_THRESHOLD = 4

def detect(turn: Turn) -> list[RuleSignal]:
    out: list[RuleSignal] = []
    steps = turn.run.steps

    # edit_without_verify: scan for runs of >=4 consecutive write steps
    run_start = None
    edit_run: list[int] = []
    for s in steps:
        if is_write_step(s):
            edit_run.append(s.step_id)
        else:
            if len(edit_run) >= CONSECUTIVE_EDITS_THRESHOLD and not is_verify_step(s):
                # close the run; check if any verify follows soon — for simplicity, fire now
                out.append(RuleSignal(
                    category=Category.VERIFICATION_GAP, subtype=Subtype.EDIT_WITHOUT_VERIFY,
                    severity=Severity.MED, step_ids=edit_run,
                    evidence={"consecutive_edit_count": len(edit_run)},
                    rule_id="verification_gap.edit_without_verify.v1",
                ))
            if is_verify_step(s):
                edit_run = []
            else:
                # non-verify, non-edit: keep the run going (e.g., reads between edits)
                pass
    if len(edit_run) >= CONSECUTIVE_EDITS_THRESHOLD:
        out.append(RuleSignal(
            category=Category.VERIFICATION_GAP, subtype=Subtype.EDIT_WITHOUT_VERIFY,
            severity=Severity.MED, step_ids=edit_run,
            evidence={"consecutive_edit_count": len(edit_run)},
            rule_id="verification_gap.edit_without_verify.v1",
        ))

    # ignored_test_failure: test_result exit_code=1 followed by submission/respond
    for i, s in enumerate(steps):
        if s.observation.type == "test_result" and s.observation.exit_code == 1:
            if i + 1 < len(steps) and steps[i + 1].action.tool_name in ("respond_to_user", "submit"):
                out.append(RuleSignal(
                    category=Category.VERIFICATION_GAP, subtype=Subtype.IGNORED_TEST_FAILURE,
                    severity=Severity.HIGH, step_ids=[s.step_id, steps[i + 1].step_id],
                    evidence={"test_output_excerpt": (s.observation.text or "")[:240]},
                    rule_id="verification_gap.ignored_test_failure.v1",
                ))

    # submission_without_test
    rs = turn.run.run_summary
    if rs and rs.result == "submitted":
        if not any(is_verify_step(s) or s.observation.type == "test_result" for s in steps):
            out.append(RuleSignal(
                category=Category.VERIFICATION_GAP, subtype=Subtype.SUBMISSION_WITHOUT_TEST,
                severity=Severity.HIGH, step_ids=[steps[-1].step_id] if steps else [],
                evidence={"steps_count": len(steps)},
                rule_id="verification_gap.submission_without_test.v1",
            ))
    return out
```

- [ ] **Step 4: Pass + commit**

```bash
.venv/bin/pytest tests/rules/test_verification_gap.py -v
git add src/agent_error_process/rules/verification_gap.py tests/rules/test_verification_gap.py
git commit -m "feat(rules): verification_gap detector"
```

---

### Task 3.6: Detector — control_flow (provided as `edit_churn.py` per spec)

**Files:**
- Create: `src/agent_error_process/rules/edit_churn.py`
- Create: `tests/rules/test_edit_churn.py`

- [ ] **Step 1: Test**

```python
# tests/rules/test_edit_churn.py
from tests.rules.test_tool_failure import _step, _turn
from agent_error_process.models_traj import Action
from agent_error_process.rules import edit_churn
from agent_error_process.taxonomy import Subtype

def _named(sid, tool):
    s = _step(sid, tool)
    s.action = Action(tool_name=tool, tool_use_id=f"t{sid}", args={})
    return s

def test_search_loop():
    steps = [_named(i, "Grep") for i in range(1, 5)]
    sigs = edit_churn.detect(_turn(steps))
    assert any(s.subtype == Subtype.SEARCH_LOOP for s in sigs)

def test_tool_thrash():
    steps = [_named(i, "Edit") for i in range(1, 8)]
    sigs = edit_churn.detect(_turn(steps))
    assert any(s.subtype == Subtype.TOOL_THRASH for s in sigs)
```

- [ ] **Step 2: Implement (covers control_flow category)**

```python
# src/agent_error_process/rules/edit_churn.py
"""Detector for category 4: control_flow.

Filename kept as `edit_churn.py` to match spec; covers search_loop, tool_thrash, phase_oscillation.
"""
from __future__ import annotations
from itertools import groupby
from ..loader import Turn
from ..models import RuleSignal, Severity
from ..taxonomy import Category, Subtype
from ._common import is_read_step, is_search_step

SEARCH_LOOP_THRESHOLD = 3
TOOL_THRASH_THRESHOLD = 6
PHASE_OSC_CYCLES = 3

def detect(turn: Turn) -> list[RuleSignal]:
    out: list[RuleSignal] = []
    steps = turn.run.steps

    # search_loop: >= N search steps with no Read between
    run_ids: list[int] = []
    for s in steps:
        if is_search_step(s):
            run_ids.append(s.step_id)
        elif is_read_step(s):
            if len(run_ids) >= SEARCH_LOOP_THRESHOLD:
                out.append(RuleSignal(
                    category=Category.CONTROL_FLOW, subtype=Subtype.SEARCH_LOOP,
                    severity=Severity.LOW, step_ids=run_ids,
                    evidence={"consecutive_search_count": len(run_ids)},
                    rule_id="control_flow.search_loop.v1",
                ))
            run_ids = []
    if len(run_ids) >= SEARCH_LOOP_THRESHOLD:
        out.append(RuleSignal(
            category=Category.CONTROL_FLOW, subtype=Subtype.SEARCH_LOOP,
            severity=Severity.LOW, step_ids=run_ids,
            evidence={"consecutive_search_count": len(run_ids)},
            rule_id="control_flow.search_loop.v1",
        ))

    # tool_thrash: >= N consecutive identical tool names
    for tool, group in groupby(steps, key=lambda s: s.action.tool_name):
        ids = [s.step_id for s in group]
        if len(ids) >= TOOL_THRASH_THRESHOLD:
            out.append(RuleSignal(
                category=Category.CONTROL_FLOW, subtype=Subtype.TOOL_THRASH,
                severity=Severity.LOW, step_ids=ids,
                evidence={"tool_name": tool, "consecutive_count": len(ids)},
                rule_id="control_flow.tool_thrash.v1",
            ))

    # phase_oscillation: edit↔verify cycles >= N
    phases = [s.phase for s in steps if s.phase in ("editing", "verification")]
    cycles = sum(1 for a, b in zip(phases, phases[1:]) if a != b)
    if cycles >= PHASE_OSC_CYCLES * 2:
        out.append(RuleSignal(
            category=Category.CONTROL_FLOW, subtype=Subtype.PHASE_OSCILLATION,
            severity=Severity.LOW, step_ids=[s.step_id for s in steps],
            evidence={"transitions": cycles},
            rule_id="control_flow.phase_oscillation.v1",
        ))
    return out
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/rules/test_edit_churn.py -v
git add src/agent_error_process/rules/edit_churn.py tests/rules/test_edit_churn.py
git commit -m "feat(rules): control_flow detector (search_loop/tool_thrash/phase_oscillation)"
```

---

### Task 3.7: Detector — user_correction (heuristic flags only)

**Files:**
- Create: `src/agent_error_process/rules/user_correction.py`
- Create: `tests/rules/test_user_correction.py`

- [ ] **Step 1: Test**

```python
# tests/rules/test_user_correction.py
from tests.rules.test_tool_failure import _turn
from agent_error_process.models_traj import UserMessage, AgentRun
from agent_error_process.loader import Turn
from agent_error_process.rules import user_correction

def _make_turn(content):
    user = UserMessage(turn_id=1, role="user", content=content, timestamp="2026-01-01T00:00:00Z")
    return Turn(user=user, run=AgentRun(turn_id=1, agent_run_id="run_t1", steps=[], run_summary=None))

def test_correction_keyword_emits_signal():
    sigs = user_correction.detect(_make_turn("不对，这个改错了，重做"))
    assert sigs and sigs[0].evidence.get("hint")

def test_no_keyword_returns_empty():
    assert user_correction.detect(_make_turn("继续下一步")) == []
```

- [ ] **Step 2: Implement**

```python
# src/agent_error_process/rules/user_correction.py
"""Heuristic flag for likely user-correction turns. Provides hint to LLM judge.

Does not emit a finding by itself (LLM will categorize); emits a low-severity
RuleSignal with subtype REPEATED_CORRECTION used as evidence for the LLM stage.
"""
from __future__ import annotations
import re
from ..loader import Turn
from ..models import RuleSignal, Severity
from ..taxonomy import Category, Subtype

CORRECTION_PATTERNS = [
    re.compile(r"\b(no|don't|stop|wrong|undo|revert|again|retry)\b", re.I),
    re.compile(r"(不对|错了|重做|不要|别|撤销|回退|再来)"),
]

def detect(turn: Turn) -> list[RuleSignal]:
    text = turn.user.content or ""
    for pat in CORRECTION_PATTERNS:
        if pat.search(text):
            return [RuleSignal(
                category=Category.USER_CORRECTION, subtype=Subtype.REPEATED_CORRECTION,
                severity=Severity.LOW, step_ids=[],
                evidence={"hint": "user_message_contains_correction_keyword",
                          "matched": pat.pattern},
                rule_id="user_correction.heuristic.v1",
            )]
    return []
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/rules/test_user_correction.py -v
git add src/agent_error_process/rules/user_correction.py tests/rules/test_user_correction.py
git commit -m "feat(rules): user_correction heuristic for LLM context"
```

---

## Phase 4 — LLM judge

### Task 4.1: Content-hash cache

**Files:**
- Create: `src/agent_error_process/llm/__init__.py` (empty)
- Create: `src/agent_error_process/llm/cache.py`
- Create: `tests/llm/__init__.py` (empty)
- Create: `tests/llm/test_cache.py`

- [ ] **Step 1: Test**

```python
# tests/llm/test_cache.py
from pathlib import Path
from agent_error_process.llm.cache import LlmCache

def test_cache_round_trip(tmp_path):
    c = LlmCache(tmp_path)
    payload = {"a": 1}
    key = c.key("hello", "v1", "tax_v1", "qwen3.6-plus")
    assert c.get(key) is None
    c.put(key, payload)
    assert c.get(key) == payload

def test_cache_key_changes_with_inputs(tmp_path):
    c = LlmCache(tmp_path)
    k1 = c.key("hello", "v1", "tax_v1", "qwen3.6-plus")
    k2 = c.key("hello", "v2", "tax_v1", "qwen3.6-plus")
    assert k1 != k2
```

- [ ] **Step 2: Implement**

```python
# src/agent_error_process/llm/cache.py
"""SHA-256 content-hash cache for LLM judgments."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Optional

class LlmCache:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def key(self, turn_payload: str, prompt_version: str, taxonomy_version: str, model: str) -> str:
        h = hashlib.sha256()
        h.update(turn_payload.encode("utf-8"))
        h.update(b"|")
        h.update(prompt_version.encode("utf-8"))
        h.update(b"|")
        h.update(taxonomy_version.encode("utf-8"))
        h.update(b"|")
        h.update(model.encode("utf-8"))
        return h.hexdigest()

    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        p = self._path(key)
        if not p.exists():
            self.misses += 1
            return None
        self.hits += 1
        return json.loads(p.read_text("utf-8"))

    def put(self, key: str, value: Any) -> None:
        self._path(key).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/llm/test_cache.py -v
git add src/agent_error_process/llm/__init__.py src/agent_error_process/llm/cache.py \
        tests/llm/__init__.py tests/llm/test_cache.py
git commit -m "feat(llm): SHA-256 content-hash cache"
```

---

### Task 4.2: Prompt template

**Files:**
- Create: `src/agent_error_process/llm/prompts.py`
- Create: `tests/llm/test_prompts.py`

- [ ] **Step 1: Implement (prompt is data; test only validates structure)**

```python
# src/agent_error_process/llm/prompts.py
"""Versioned prompt templates for the LLM judge."""
from __future__ import annotations
from textwrap import dedent
from ..taxonomy import SUBTYPES_BY_CATEGORY, LLM_CATEGORIES

PROMPT_VERSION = "v1"

def _llm_subtype_catalog() -> str:
    lines = []
    for cat, subs in SUBTYPES_BY_CATEGORY.items():
        if cat not in LLM_CATEGORIES:
            continue
        lines.append(f"## {cat.value}")
        for s in subs:
            name = s.value.split(".", 1)[1]
            lines.append(f"- `{s.value}` ({name})")
    return "\n".join(lines)

SYSTEM_PROMPT = dedent("""\
    You are an agent-trajectory error judge. You read ONE turn (user message + agent's
    actions) and identify subtle, semantic agent errors that rule-based detectors cannot
    catch.

    You only output findings that fit one of the following subtypes (LLM categories only):

    {catalog}

    Rules:
    - Output strictly valid JSON matching the schema below.
    - Only emit a finding when you have concrete evidence in the trajectory.
    - Severity: high = blocks task completion; med = wastes turns; low = inefficiency.
    - confidence in [0.0, 1.0]. Use <0.6 if uncertain; <0.4 means do not emit.
    - Each finding must reference the step_ids that demonstrate it.

    Output schema:
    {{
      "findings": [
        {{
          "subtype": "intent_alignment.lazy_fix",
          "severity": "high",
          "step_ids": [12, 14],
          "confidence": 0.82,
          "evidence_text": "short quote or paraphrase of the offending action",
          "root_cause_hypothesis": "1-sentence explanation"
        }}
      ]
    }}
    """).format(catalog=_llm_subtype_catalog())

USER_PROMPT_TEMPLATE = dedent("""\
    USER MESSAGE (turn {turn_id}):
    ---
    {user_msg}
    ---

    AGENT RUN (run_id={agent_run_id}, {step_count} steps, {tool_calls_count} tool calls):
    {compacted_steps}

    RULE-BASED SIGNALS already detected for this turn (for context, do not re-emit):
    {rule_signals_summary}

    Output JSON only, no commentary.
    """)
```

- [ ] **Step 2: Test**

```python
# tests/llm/test_prompts.py
from agent_error_process.llm.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, PROMPT_VERSION

def test_version():
    assert PROMPT_VERSION == "v1"

def test_system_prompt_lists_only_llm_subtypes():
    assert "intent_alignment.lazy_fix" in SYSTEM_PROMPT
    assert "context_hygiene.write_without_read" not in SYSTEM_PROMPT  # rule-only

def test_user_template_has_placeholders():
    for k in ("turn_id", "user_msg", "agent_run_id", "step_count",
              "tool_calls_count", "compacted_steps", "rule_signals_summary"):
        assert "{" + k + "}" in USER_PROMPT_TEMPLATE
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/llm/test_prompts.py -v
git add src/agent_error_process/llm/prompts.py tests/llm/test_prompts.py
git commit -m "feat(llm): versioned prompt templates"
```

---

### Task 4.3: Judge — Qwen client + payload compaction

**Files:**
- Create: `src/agent_error_process/llm/judge.py`
- Create: `tests/llm/test_judge.py`

- [ ] **Step 1: Test (mock the OpenAI client)**

```python
# tests/llm/test_judge.py
import json
from pathlib import Path
from unittest.mock import MagicMock
from agent_error_process.models_traj import UserMessage, AgentRun, Step, Action, Observation
from agent_error_process.loader import Turn
from agent_error_process.llm.judge import Judge, compact_turn
from agent_error_process.llm.cache import LlmCache

def _turn():
    user = UserMessage(turn_id=1, role="user", content="please fix this", timestamp="t")
    step = Step(step_id=1, phase="editing", thinking=None, thought="ok",
                action=Action(tool_name="Edit", tool_use_id="t1", args={"file_path":"/a"}),
                observation=Observation(type="edit_success", text="ok", exit_code=0),
                state=None, status="ok", timestamp="t", execution_time=0.1)
    run = AgentRun(turn_id=1, agent_run_id="run_t1", steps=[step], run_summary=None)
    return Turn(user=user, run=run)

def test_compact_turn_truncates_long_observations():
    t = _turn()
    t.run.steps[0].observation.text = "x" * 5000
    compact = compact_turn(t)
    assert "..." in compact

def test_judge_uses_cache_on_second_call(tmp_path):
    cache = LlmCache(tmp_path)
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=json.dumps({"findings": []})))
    ]
    j = Judge(client=fake_client, model="qwen3.6-plus", cache=cache)
    j.judge_turn(_turn(), rule_signals=[])
    j.judge_turn(_turn(), rule_signals=[])
    # API called once; second call hits cache
    assert fake_client.chat.completions.create.call_count == 1
    assert cache.hits == 1

def test_judge_returns_empty_when_no_llm_findings(tmp_path):
    cache = LlmCache(tmp_path)
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content='{"findings": []}'))
    ]
    j = Judge(client=fake_client, model="qwen3.6-plus", cache=cache)
    out = j.judge_turn(_turn(), rule_signals=[])
    assert out == []
```

- [ ] **Step 2: Implement**

```python
# src/agent_error_process/llm/judge.py
"""LLM judge: calls Qwen, validates output, applies cache.

Uses OpenAI-compatible Dashscope endpoint:
  base_url=https://dashscope.aliyuncs.com/compatible-mode/v1
"""
from __future__ import annotations
import json
import os
from typing import Any
from openai import OpenAI
from ..loader import Turn
from ..models import LlmFinding, RuleSignal
from ..taxonomy import TAXONOMY_VERSION
from .cache import LlmCache
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, PROMPT_VERSION

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MAX_OBS_LEN = 1000   # truncate observation text beyond this

def make_default_client() -> OpenAI:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY not set")
    return OpenAI(api_key=api_key, base_url=DASHSCOPE_BASE_URL)

def _trunc(t: str, n: int = MAX_OBS_LEN) -> str:
    if not t or len(t) <= n:
        return t or ""
    return t[: n // 2] + f"\n...[truncated {len(t)-n} chars]...\n" + t[-n // 2 :]

def compact_turn(turn: Turn) -> str:
    parts = []
    for s in turn.run.steps:
        a = s.action
        obs = s.observation
        args_brief = json.dumps(a.args, ensure_ascii=False)[:400]
        parts.append(
            f"[step {s.step_id} | phase={s.phase} | status={s.status}] "
            f"{a.tool_name}({args_brief}) -> "
            f"type={obs.type} exit={obs.exit_code} text={_trunc(obs.text)!r}"
        )
    return "\n".join(parts)

def _summarize_signals(sigs: list[RuleSignal]) -> str:
    if not sigs:
        return "(none)"
    return "\n".join(f"- {s.subtype.value} steps={s.step_ids}" for s in sigs)

class Judge:
    def __init__(self, client: OpenAI, model: str, cache: LlmCache):
        self.client = client
        self.model = model
        self.cache = cache

    def _build_payload(self, turn: Turn, rule_signals: list[RuleSignal]) -> str:
        return USER_PROMPT_TEMPLATE.format(
            turn_id=turn.user.turn_id,
            user_msg=_trunc(turn.user.content, 2000),
            agent_run_id=turn.run.agent_run_id,
            step_count=len(turn.run.steps),
            tool_calls_count=sum(1 for s in turn.run.steps if s.action.tool_name != "respond_to_user"),
            compacted_steps=compact_turn(turn),
            rule_signals_summary=_summarize_signals(rule_signals),
        )

    def judge_turn(self, turn: Turn, rule_signals: list[RuleSignal]) -> list[LlmFinding]:
        payload = self._build_payload(turn, rule_signals)
        key = self.cache.key(payload, PROMPT_VERSION, TAXONOMY_VERSION, self.model)
        hit = self.cache.get(key)
        if hit is not None:
            return self._parse(hit)

        try:
            raw = self._call(payload)
        except Exception as e:
            return []  # log+skip on API failure

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # one retry with stricter instruction appended
            try:
                raw = self._call(payload + "\n\nReturn ONLY valid JSON.")
                parsed = json.loads(raw)
            except Exception:
                return []

        self.cache.put(key, parsed)
        return self._parse(parsed)

    def _call(self, payload: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload},
            ],
            extra_body={"enable_thinking": False},
            temperature=0.1,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or "{}"

    def _parse(self, raw: dict[str, Any]) -> list[LlmFinding]:
        out: list[LlmFinding] = []
        for f in raw.get("findings", []):
            try:
                out.append(LlmFinding.model_validate(f))
            except Exception:
                continue
        return out
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/llm/test_judge.py -v
git add src/agent_error_process/llm/judge.py tests/llm/test_judge.py
git commit -m "feat(llm): Qwen judge with payload compaction + cache"
```

---

## Phase 5 — Pipeline & aggregator

### Task 5.1: Merge rule signals + LLM findings → Finding

**Files:**
- Create: `src/agent_error_process/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Test**

```python
# tests/test_pipeline.py
from agent_error_process.pipeline import merge_findings
from agent_error_process.models import RuleSignal, LlmFinding, Severity, Source
from agent_error_process.taxonomy import Category, Subtype

def test_merge_yields_rule_and_llm_findings():
    rule = [RuleSignal(category=Category.TOOL_FAILURE, subtype=Subtype.TOOL_EXIT_NONZERO,
                       severity=Severity.MED, step_ids=[1], evidence={}, rule_id="r1")]
    llm = [LlmFinding(subtype=Subtype.LAZY_FIX, severity=Severity.HIGH,
                      step_ids=[2], confidence=0.8, evidence_text="x",
                      root_cause_hypothesis="y")]
    out = merge_findings("wzp", "abc", 1, rule, llm, model="qwen3.6-plus", prompt_version="v1")
    assert len(out) == 2
    assert any(f.source == Source.RULE for f in out)
    assert any(f.source == Source.LLM for f in out)

def test_finding_id_is_unique():
    rule = [RuleSignal(category=Category.TOOL_FAILURE, subtype=Subtype.TOOL_EXIT_NONZERO,
                       severity=Severity.MED, step_ids=[1], evidence={}, rule_id="r1")] * 3
    out = merge_findings("wzp", "abc", 1, rule, [], model="m", prompt_version="v1")
    assert len({f.finding_id for f in out}) == 3
```

- [ ] **Step 2: Implement**

```python
# src/agent_error_process/pipeline.py
"""Pipeline orchestrator: rules + LLM → ErrorReport per turn → SessionReport."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .loader import Turn, load_trajectory, iter_turns, session_hash_from_path
from .models import (
    Finding, RuleSignal, LlmFinding, Severity, Source,
    ErrorReport, SessionReport, OUTPUT_SCHEMA_VERSION,
)
from .taxonomy import Category, category_of
from .rules import run_all as run_all_rules
from .llm.judge import Judge

def merge_findings(
    project: str, session_hash: str, turn_id: int,
    rule_signals: list[RuleSignal], llm_findings: list[LlmFinding],
    model: str, prompt_version: str,
) -> list[Finding]:
    out: list[Finding] = []
    counter = 0
    for s in rule_signals:
        counter += 1
        out.append(Finding(
            finding_id=f"{project}_{session_hash}_t{turn_id}_f{counter}",
            category=s.category, subtype=s.subtype, severity=s.severity,
            source=Source.RULE, step_ids=s.step_ids,
            evidence=s.evidence, rule_id=s.rule_id,
        ))
    for lf in llm_findings:
        counter += 1
        out.append(Finding(
            finding_id=f"{project}_{session_hash}_t{turn_id}_f{counter}",
            category=category_of(lf.subtype), subtype=lf.subtype, severity=lf.severity,
            source=Source.LLM, step_ids=lf.step_ids,
            evidence_text=lf.evidence_text, confidence=lf.confidence,
            root_cause_hypothesis=lf.root_cause_hypothesis,
            judge_prompt_version=prompt_version, judge_model=model,
        ))
    return out

def _metrics(turn: Turn, rule_signals: list[RuleSignal]) -> dict[str, int]:
    from .rules._common import is_read_step, is_write_step, is_verify_step, file_path_from_args
    from collections import Counter
    rc = Counter(); wc = Counter()
    for s in turn.run.steps:
        p = file_path_from_args(s.action.args)
        if not p:
            continue
        if is_read_step(s):
            rc[p] += 1
        elif is_write_step(s):
            wc[p] += 1
    streak = best = 0
    for s in turn.run.steps:
        if is_write_step(s):
            streak += 1; best = max(best, streak)
        elif is_verify_step(s):
            streak = 0
    return {
        "redundant_reads_max": max(rc.values(), default=0),
        "redundant_writes_max": max(wc.values(), default=0),
        "edits_without_verify_run": best,
        "tool_failure_count": sum(1 for s in rule_signals if s.category == Category.TOOL_FAILURE),
    }

def process_turn(turn: Turn, project: str, session_hash: str, judge: Optional[Judge]) -> ErrorReport:
    rule_sigs = run_all_rules(turn)
    llm_findings: list[LlmFinding] = []
    if judge is not None:
        llm_findings = judge.judge_turn(turn, rule_sigs)
    findings = merge_findings(
        project, session_hash, turn.user.turn_id,
        rule_sigs, llm_findings,
        model=(judge.model if judge else "n/a"),
        prompt_version=("v1" if judge else "n/a"),
    )
    return ErrorReport(
        turn_id=turn.user.turn_id,
        agent_run_id=turn.run.agent_run_id,
        user_message_excerpt=(turn.user.content or "")[:400],
        step_count=len(turn.run.steps),
        tool_calls_count=sum(1 for s in turn.run.steps if s.action.tool_name != "respond_to_user"),
        findings=findings,
        metrics=_metrics(turn, rule_sigs),
    )

def process_trajectory(traj_path: Path, judge: Optional[Judge]) -> SessionReport:
    traj = load_trajectory(traj_path)
    session_hash = session_hash_from_path(traj_path)
    project = traj.session_metadata.project
    reports = [process_turn(t, project, session_hash, judge) for t in iter_turns(traj)]
    return SessionReport(
        schema_version=OUTPUT_SCHEMA_VERSION,
        project=project,
        session_hash=session_hash,
        session_id=traj.session_metadata.session_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        turns=reports,
    )
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/test_pipeline.py -v
git add src/agent_error_process/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): rule+LLM merge into ErrorReport"
```

---

### Task 5.2: Aggregator

**Files:**
- Create: `src/agent_error_process/aggregator.py`
- Create: `tests/test_aggregator.py`

- [ ] **Step 1: Test**

```python
# tests/test_aggregator.py
from agent_error_process.aggregator import build_aggregate
from agent_error_process.models import (
    SessionReport, ErrorReport, Finding, Severity, Source, OUTPUT_SCHEMA_VERSION,
)
from agent_error_process.taxonomy import Category, Subtype

def _f(sub, sev=Severity.MED, src=Source.RULE, fid="f1", steps=None):
    return Finding(finding_id=fid, category=Category.TOOL_FAILURE if "tool_failure" in sub.value else Category.CONTEXT_HYGIENE,
                   subtype=sub, severity=sev, source=src, step_ids=steps or [1])

def test_aggregate_counts():
    sr = SessionReport(
        schema_version=OUTPUT_SCHEMA_VERSION, project="wzp",
        session_hash="abc", session_id="x", generated_at="t",
        turns=[ErrorReport(turn_id=1, agent_run_id="r", user_message_excerpt="u",
                           step_count=1, tool_calls_count=1,
                           findings=[_f(Subtype.TOOL_EXIT_NONZERO),
                                     _f(Subtype.WRITE_WITHOUT_READ, sev=Severity.HIGH, fid="f2")],
                           metrics={})])
    agg = build_aggregate("wzp", [sr])
    assert agg.session_count == 1
    assert agg.turn_count == 1
    assert agg.totals_by_category["tool_failure"] == 1
    assert agg.totals_by_category["context_hygiene"] == 1
    assert agg.severity_breakdown["high"] == 1
```

- [ ] **Step 2: Implement**

```python
# src/agent_error_process/aggregator.py
"""Roll session reports up into ProjectAggregate."""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
from .models import (
    SessionReport, ProjectAggregate, FindingExample, TopOffendingSession,
    OUTPUT_SCHEMA_VERSION, Severity,
)

def build_aggregate(project: str, sessions: list[SessionReport]) -> ProjectAggregate:
    by_cat: Counter = Counter()
    by_sub: Counter = Counter()
    by_sev: Counter = Counter()
    by_tool: dict[str, dict] = defaultdict(lambda: {"total": 0, "categories": Counter()})
    by_phase: dict[str, dict] = defaultdict(lambda: {"total": 0, "categories": Counter()})
    examples: dict[str, list[FindingExample]] = defaultdict(list)
    top: list[TopOffendingSession] = []
    turn_count = 0

    for sr in sessions:
        high = sum(1 for tr in sr.turns for f in tr.findings if f.severity == Severity.HIGH)
        total = sum(len(tr.findings) for tr in sr.turns)
        top.append(TopOffendingSession(session_hash=sr.session_hash,
                                       high_severity_count=high, total_findings=total))
        for tr in sr.turns:
            turn_count += 1
            for f in tr.findings:
                by_cat[f.category.value if hasattr(f.category, "value") else f.category] += 1
                by_sub[f.subtype.value if hasattr(f.subtype, "value") else f.subtype] += 1
                by_sev[f.severity.value if hasattr(f.severity, "value") else f.severity] += 1
                tool = (f.evidence or {}).get("tool_name") if f.evidence else None
                if tool:
                    by_tool[tool]["total"] += 1
                    by_tool[tool]["categories"][f.category if isinstance(f.category, str) else f.category.value] += 1
                if len(examples[f.subtype if isinstance(f.subtype, str) else f.subtype.value]) < 5:
                    examples[f.subtype if isinstance(f.subtype, str) else f.subtype.value].append(
                        FindingExample(session_hash=sr.session_hash, turn_id=tr.turn_id, finding_id=f.finding_id))

    top.sort(key=lambda x: x.high_severity_count, reverse=True)

    return ProjectAggregate(
        schema_version=OUTPUT_SCHEMA_VERSION, project=project,
        generated_at=datetime.now(timezone.utc).isoformat(),
        session_count=len(sessions), turn_count=turn_count,
        totals_by_category=dict(by_cat),
        totals_by_subtype=dict(by_sub),
        severity_breakdown=dict(by_sev),
        by_tool={k: {"total": v["total"], "categories": dict(v["categories"])} for k, v in by_tool.items()},
        by_phase={k: {"total": v["total"], "categories": dict(v["categories"])} for k, v in by_phase.items()},
        top_offending_sessions=top[:20],
        examples_per_subtype=dict(examples),
    )
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/test_aggregator.py -v
git add src/agent_error_process/aggregator.py tests/test_aggregator.py
git commit -m "feat(aggregator): project rollup of session reports"
```

---

### Task 5.3: CLI

**Files:**
- Create: `src/agent_error_process/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Implement**

```python
# src/agent_error_process/cli.py
"""CLI entry point: agent-error-process analyze | aggregate"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Optional
import click
from tqdm import tqdm
from .loader import iter_traj_files, load_trajectory, session_hash_from_path
from .pipeline import process_trajectory
from .aggregator import build_aggregate
from .models import SessionReport
from .llm.cache import LlmCache
from .llm.judge import Judge, make_default_client

REPO_ROOT = Path(__file__).resolve().parents[3].parent  # traj-error-pattern parent
TRAJ_ROOT = REPO_ROOT / "traj-data-new"
DATA_ROOT = Path(__file__).resolve().parents[3] / "data"

def _resolve_projects(project: str) -> list[str]:
    if project == "all":
        return sorted(p.name for p in TRAJ_ROOT.iterdir() if p.is_dir() and not p.name.startswith("_"))
    return [project]

def _build_judge(no_llm: bool, refresh: bool, model: str) -> Optional[Judge]:
    if no_llm:
        return None
    cache_root = DATA_ROOT / "llm_cache"
    if refresh:
        for f in cache_root.glob("*.json"):
            f.unlink()
    cache = LlmCache(cache_root)
    return Judge(client=make_default_client(), model=model, cache=cache)

@click.group()
def main() -> None:
    """traj-error-pattern analyzer."""

@main.command()
@click.option("--project", required=True, help="wzp | zzj | all")
@click.option("--no-llm", is_flag=True, help="Skip LLM judge layer")
@click.option("--refresh-llm", is_flag=True, help="Bypass LLM cache")
@click.option("--model", default="qwen3.6-plus")
@click.option("--max-llm-calls", type=int, default=None)
def analyze(project: str, no_llm: bool, refresh_llm: bool, model: str, max_llm_calls: Optional[int]) -> None:
    judge = _build_judge(no_llm, refresh_llm, model)
    for proj in _resolve_projects(project):
        out_dir = DATA_ROOT / "per_turn" / proj
        out_dir.mkdir(parents=True, exist_ok=True)
        sessions: list[SessionReport] = []
        files = list(iter_traj_files(TRAJ_ROOT, proj))
        for traj_path in tqdm(files, desc=f"analyze {proj}"):
            try:
                report = process_trajectory(traj_path, judge)
            except Exception as e:
                click.echo(f"FAILED {traj_path}: {e}", err=True)
                continue
            (out_dir / f"{report.session_hash}.json").write_text(
                report.model_dump_json(indent=2), encoding="utf-8")
            sessions.append(report)
        agg = build_aggregate(proj, sessions)
        agg_dir = DATA_ROOT / "aggregates"
        agg_dir.mkdir(parents=True, exist_ok=True)
        (agg_dir / f"{proj}.summary.json").write_text(agg.model_dump_json(indent=2), encoding="utf-8")
        click.echo(f"[{proj}] sessions={len(sessions)} cache_hits={getattr(judge.cache, 'hits', 0) if judge else 0}")

@main.command()
@click.option("--project", required=True)
def aggregate(project: str) -> None:
    for proj in _resolve_projects(project):
        per_turn = DATA_ROOT / "per_turn" / proj
        sessions = [SessionReport.model_validate_json((p).read_text(encoding="utf-8"))
                    for p in sorted(per_turn.glob("*.json"))]
        agg = build_aggregate(proj, sessions)
        out = DATA_ROOT / "aggregates" / f"{proj}.summary.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(agg.model_dump_json(indent=2), encoding="utf-8")
        click.echo(f"[{proj}] aggregate -> {out}")
```

- [ ] **Step 2: Smoke test (no-LLM, real wzp data)**

Run:

```bash
cd traj-error-pattern/agent-error-process
.venv/bin/agent-error-process analyze --project wzp --no-llm
```

Expected: progress bar, completes without error, writes JSONs into `data/per_turn/wzp/` and `data/aggregates/wzp.summary.json`.

- [ ] **Step 3: Inspect output**

Run: `python3 -c "import json; print(list(json.load(open('data/aggregates/wzp.summary.json')).keys()))"`
Expected: contains `totals_by_category`, `totals_by_subtype`, `severity_breakdown`, etc.

- [ ] **Step 4: Commit**

```bash
git add src/agent_error_process/cli.py
git commit -m "feat(cli): analyze + aggregate commands"
```

---

### Task 5.4: End-to-end fixture test

**Files:**
- Create: `tests/test_e2e_pipeline.py`

- [ ] **Step 1: Test**

```python
# tests/test_e2e_pipeline.py
"""Run the rule-only pipeline against a real wzp .traj file end-to-end."""
from pathlib import Path
from agent_error_process.pipeline import process_trajectory

WZP = Path("/Users/xd/Desktop/work/project-logs/traj-data-new/wzp/014354fc.traj")

def test_e2e_no_llm_completes_and_emits_findings():
    report = process_trajectory(WZP, judge=None)
    assert report.project == "wzp"
    assert report.session_hash == "014354fc"
    assert len(report.turns) >= 1
    # very loose sanity: at least one turn parses cleanly
    assert all(t.step_count >= 0 for t in report.turns)
```

- [ ] **Step 2: Run + commit**

```bash
.venv/bin/pytest tests/test_e2e_pipeline.py -v
git add tests/test_e2e_pipeline.py
git commit -m "test: e2e rule-only pipeline against real wzp fixture"
```

---

## Phase 6 — Backend (FastAPI)

### Task 6.1: Backend skeleton

**Files:**
- Create: `traj-error-pattern/backend/pyproject.toml`
- Create: `traj-error-pattern/backend/main.py`
- Create: `traj-error-pattern/backend/__init__.py`

- [ ] **Step 1: pyproject.toml**

```toml
[project]
name = "traj-error-pattern-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.110", "uvicorn[standard]>=0.29", "pydantic>=2.7"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Install**

```bash
cd traj-error-pattern/backend
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Expected: `Successfully installed traj-error-pattern-backend-0.1.0`

- [ ] **Step 3: Stub main.py**

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="traj-error-pattern backend", version="0.1.0")

@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
```

- [ ] **Step 4: Smoke test**

```bash
.venv/bin/uvicorn main:app --port 8001 &
sleep 1
curl -s http://localhost:8001/healthz
kill %1
```

Expected: `{"status":"ok"}`

- [ ] **Step 5: Commit**

```bash
git add traj-error-pattern/backend/pyproject.toml traj-error-pattern/backend/main.py traj-error-pattern/backend/__init__.py
git commit -m "feat(backend): FastAPI skeleton with healthz"
```

---

### Task 6.2: Backend models (mirror analyzer JSON)

**Files:**
- Create: `traj-error-pattern/backend/models.py`
- Create: `traj-error-pattern/backend/tests/__init__.py` (empty)
- Create: `traj-error-pattern/backend/tests/test_models_contract.py`

- [ ] **Step 1: Write models.py (hand-mirror of analyzer output models)**

```python
# backend/models.py
"""Pydantic models mirroring agent-error-process JSON output.

NOTE: kept separate from the analyzer to enforce JSON-only boundary.
Schema drift is caught by tests/test_models_contract.py.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

OUTPUT_SCHEMA_VERSION = "1.0"

class Severity(str, Enum):
    LOW = "low"; MED = "med"; HIGH = "high"

class Source(str, Enum):
    RULE = "rule"; LLM = "llm"

class Finding(BaseModel):
    finding_id: str
    category: str
    subtype: str
    severity: Severity
    source: Source
    step_ids: list[int] = Field(default_factory=list)
    evidence: Optional[dict[str, Any]] = None
    rule_id: Optional[str] = None
    evidence_text: Optional[str] = None
    confidence: Optional[float] = None
    root_cause_hypothesis: Optional[str] = None
    judge_prompt_version: Optional[str] = None
    judge_model: Optional[str] = None

class ErrorReport(BaseModel):
    turn_id: int
    agent_run_id: str
    user_message_excerpt: str
    step_count: int
    tool_calls_count: int
    findings: list[Finding]
    metrics: dict[str, int] = Field(default_factory=dict)

class SessionReport(BaseModel):
    schema_version: str
    project: str
    session_hash: str
    session_id: str
    generated_at: str
    turns: list[ErrorReport]

class FindingExample(BaseModel):
    session_hash: str
    turn_id: int
    finding_id: str

class TopOffendingSession(BaseModel):
    session_hash: str
    high_severity_count: int
    total_findings: int

class ProjectAggregate(BaseModel):
    schema_version: str
    project: str
    generated_at: str
    session_count: int
    turn_count: int
    totals_by_category: dict[str, int]
    totals_by_subtype: dict[str, int]
    severity_breakdown: dict[str, int]
    by_tool: dict[str, dict[str, Any]]
    by_phase: dict[str, dict[str, Any]]
    top_offending_sessions: list[TopOffendingSession]
    examples_per_subtype: dict[str, list[FindingExample]]

class ProjectInfo(BaseModel):
    name: str
    session_count: int
    turn_count: int
    last_analyzed_at: Optional[str] = None
```

- [ ] **Step 2: Write contract test**

```python
# backend/tests/test_models_contract.py
"""Schema-drift guard: load real analyzer JSON and validate via backend models."""
from pathlib import Path
from backend.models import SessionReport, ProjectAggregate

DATA = Path(__file__).resolve().parents[2] / "agent-error-process" / "data"

def test_session_report_validates_real_outputs():
    files = list((DATA / "per_turn" / "wzp").glob("*.json")) if (DATA / "per_turn" / "wzp").exists() else []
    if not files:
        # produced only after analyzer ran; skip when missing
        import pytest; pytest.skip("no analyzer output yet")
    for p in files[:3]:
        SessionReport.model_validate_json(p.read_text("utf-8"))

def test_aggregate_validates_real_outputs():
    p = DATA / "aggregates" / "wzp.summary.json"
    if not p.exists():
        import pytest; pytest.skip("no aggregate yet")
    ProjectAggregate.model_validate_json(p.read_text("utf-8"))
```

- [ ] **Step 3: Run + commit**

```bash
.venv/bin/pytest tests/test_models_contract.py -v
git add backend/models.py backend/tests/__init__.py backend/tests/test_models_contract.py
git commit -m "feat(backend): mirror models + contract test against analyzer JSON"
```

---

### Task 6.3: Backend loader (in-memory index)

**Files:**
- Create: `traj-error-pattern/backend/loader.py`
- Create: `traj-error-pattern/backend/tests/test_loader.py`

- [ ] **Step 1: Implement**

```python
# backend/loader.py
"""Scan analyzer output directory; build in-memory index with mtime-based detail cache."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from .models import SessionReport, ProjectAggregate, ProjectInfo

class DataIndex:
    def __init__(self, data_root: Path):
        self.data_root = data_root
        self._sessions: dict[tuple[str, str], tuple[float, SessionReport]] = {}
        self._aggregates: dict[str, tuple[float, ProjectAggregate]] = {}

    def projects(self) -> list[ProjectInfo]:
        out: list[ProjectInfo] = []
        per_turn_root = self.data_root / "per_turn"
        if not per_turn_root.exists():
            return out
        for proj_dir in sorted(per_turn_root.iterdir()):
            if not proj_dir.is_dir():
                continue
            files = list(proj_dir.glob("*.json"))
            agg = self.aggregate(proj_dir.name)
            out.append(ProjectInfo(
                name=proj_dir.name,
                session_count=len(files),
                turn_count=agg.turn_count if agg else 0,
                last_analyzed_at=(agg.generated_at if agg else None),
            ))
        return out

    def aggregate(self, project: str) -> Optional[ProjectAggregate]:
        p = self.data_root / "aggregates" / f"{project}.summary.json"
        if not p.exists():
            return None
        mt = p.stat().st_mtime
        cached = self._aggregates.get(project)
        if cached and cached[0] == mt:
            return cached[1]
        agg = ProjectAggregate.model_validate_json(p.read_text("utf-8"))
        self._aggregates[project] = (mt, agg)
        return agg

    def session(self, project: str, session_hash: str) -> Optional[SessionReport]:
        p = self.data_root / "per_turn" / project / f"{session_hash}.json"
        if not p.exists():
            return None
        mt = p.stat().st_mtime
        key = (project, session_hash)
        cached = self._sessions.get(key)
        if cached and cached[0] == mt:
            return cached[1]
        sr = SessionReport.model_validate_json(p.read_text("utf-8"))
        self._sessions[key] = (mt, sr)
        return sr

    def list_sessions(self, project: str,
                      category: Optional[str] = None,
                      subtype: Optional[str] = None,
                      severity: Optional[str] = None,
                      min_findings: int = 0) -> list[dict]:
        out = []
        proj_dir = self.data_root / "per_turn" / project
        if not proj_dir.exists():
            return out
        for p in sorted(proj_dir.glob("*.json")):
            sr = self.session(project, p.stem)
            if not sr:
                continue
            findings = [f for tr in sr.turns for f in tr.findings]
            if category:
                findings = [f for f in findings if f.category == category]
            if subtype:
                findings = [f for f in findings if f.subtype == subtype]
            if severity:
                findings = [f for f in findings if f.severity.value == severity]
            if len(findings) < min_findings:
                continue
            out.append({
                "session_hash": sr.session_hash,
                "session_id": sr.session_id,
                "turn_count": len(sr.turns),
                "finding_count": len(findings),
                "high_severity_count": sum(1 for f in findings if f.severity.value == "high"),
            })
        return out

    def list_findings(self, project: str, subtype: Optional[str] = None, limit: int = 200) -> list[dict]:
        out: list[dict] = []
        proj_dir = self.data_root / "per_turn" / project
        if not proj_dir.exists():
            return out
        for p in sorted(proj_dir.glob("*.json")):
            sr = self.session(project, p.stem)
            if not sr:
                continue
            for tr in sr.turns:
                for f in tr.findings:
                    if subtype and f.subtype != subtype:
                        continue
                    out.append({
                        "session_hash": sr.session_hash,
                        "turn_id": tr.turn_id,
                        "finding": json.loads(f.model_dump_json()),
                    })
                    if len(out) >= limit:
                        return out
        return out

    def comparison(self, projects: list[str]) -> dict:
        result = {}
        for proj in projects:
            agg = self.aggregate(proj)
            if not agg or agg.turn_count == 0:
                continue
            denom = agg.turn_count / 100.0
            result[proj] = {
                "turn_count": agg.turn_count,
                "rates_by_category": {k: v / denom for k, v in agg.totals_by_category.items()},
                "rates_by_subtype": {k: v / denom for k, v in agg.totals_by_subtype.items()},
            }
        return result
```

- [ ] **Step 2: Test**

```python
# backend/tests/test_loader.py
from pathlib import Path
from backend.loader import DataIndex

ROOT = Path(__file__).resolve().parents[2] / "agent-error-process" / "data"

def test_projects_listing():
    if not (ROOT / "per_turn").exists():
        import pytest; pytest.skip("analyzer has not run yet")
    idx = DataIndex(ROOT)
    projs = idx.projects()
    names = {p.name for p in projs}
    assert "wzp" in names or "zzj" in names
```

- [ ] **Step 3: Pass + commit**

```bash
.venv/bin/pytest tests/test_loader.py -v
git add backend/loader.py backend/tests/test_loader.py
git commit -m "feat(backend): in-memory data index with mtime cache"
```

---

### Task 6.4: Backend API endpoints

**Files:**
- Modify: `traj-error-pattern/backend/main.py` (replace stub)
- Create: `traj-error-pattern/backend/tests/test_api.py`

- [ ] **Step 1: Replace main.py**

```python
# main.py
from __future__ import annotations
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .loader import DataIndex
from .models import ProjectInfo, SessionReport, ProjectAggregate

DATA_ROOT = Path(os.environ.get(
    "TRAJ_ERROR_DATA_ROOT",
    str(Path(__file__).resolve().parent.parent / "agent-error-process" / "data"),
))

app = FastAPI(title="traj-error-pattern backend", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

index = DataIndex(DATA_ROOT)

@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "data_root": str(DATA_ROOT), "exists": DATA_ROOT.exists()}

@app.get("/api/projects", response_model=list[ProjectInfo])
def projects() -> list[ProjectInfo]:
    return index.projects()

@app.get("/api/aggregates/{project}", response_model=ProjectAggregate)
def aggregate(project: str) -> ProjectAggregate:
    agg = index.aggregate(project)
    if not agg:
        raise HTTPException(404, f"no aggregate for {project}")
    return agg

@app.get("/api/sessions")
def list_sessions(project: str = Query(...), category: str | None = None,
                  subtype: str | None = None, severity: str | None = None,
                  min_findings: int = 0) -> list[dict]:
    return index.list_sessions(project, category, subtype, severity, min_findings)

@app.get("/api/sessions/{project}/{session_hash}", response_model=SessionReport)
def session(project: str, session_hash: str) -> SessionReport:
    sr = index.session(project, session_hash)
    if not sr:
        raise HTTPException(404, "session not found")
    return sr

@app.get("/api/findings")
def list_findings(project: str = Query(...), subtype: str | None = None, limit: int = 200) -> list[dict]:
    return index.list_findings(project, subtype, limit)

@app.get("/api/comparison")
def comparison(projects: str = Query(..., description="comma-separated")) -> dict:
    return index.comparison([p.strip() for p in projects.split(",") if p.strip()])
```

- [ ] **Step 2: API tests**

```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_projects_returns_list():
    r = client.get("/api/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_aggregate_404_for_unknown():
    r = client.get("/api/aggregates/__nope__")
    assert r.status_code == 404
```

- [ ] **Step 3: Run + commit**

```bash
.venv/bin/pytest tests/test_api.py -v
git add backend/main.py backend/tests/test_api.py
git commit -m "feat(backend): full API surface (projects/aggregates/sessions/findings/comparison)"
```

- [ ] **Step 4: Manual smoke test**

```bash
.venv/bin/uvicorn backend.main:app --port 8001 --reload &
sleep 1
curl -s http://localhost:8001/api/projects | head -c 200
curl -s http://localhost:8001/api/aggregates/wzp | head -c 200
kill %1
```

Expected: JSON responses (or `[]` if analyzer hasn't run).

---

## Phase 7 — Frontend (Vue 3 + Vite)

### Task 7.1: Scaffold Vue 3 project

**Files:**
- Create: `traj-error-pattern/frontend/package.json`
- Create: `traj-error-pattern/frontend/vite.config.ts`
- Create: `traj-error-pattern/frontend/tsconfig.json`
- Create: `traj-error-pattern/frontend/index.html`
- Create: `traj-error-pattern/frontend/src/main.ts`
- Create: `traj-error-pattern/frontend/src/App.vue`
- Create: `traj-error-pattern/frontend/src/router.ts`

- [ ] **Step 1: package.json**

```json
{
  "name": "traj-error-pattern-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "chart.js": "^4.4.0",
    "vue-chartjs": "^5.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vue-tsc": "^2.0.0"
  }
}
```

- [ ] **Step 2: vite.config.ts**

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: { '/api': 'http://localhost:8001', '/healthz': 'http://localhost:8001' }
  }
})
```

- [ ] **Step 3: tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020", "module": "ESNext", "moduleResolution": "bundler",
    "strict": true, "jsx": "preserve", "isolatedModules": true,
    "esModuleInterop": true, "skipLibCheck": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "types": ["vite/client"]
  },
  "include": ["src/**/*.ts", "src/**/*.vue"]
}
```

- [ ] **Step 4: index.html**

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>traj-error-pattern</title>
</head>
<body>
<div id="app"></div>
<script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 5: src/main.ts**

```ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
```

- [ ] **Step 6: src/router.ts**

```ts
import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import FindingsTable from './views/FindingsTable.vue'
import TurnDetailView from './views/TurnDetailView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: DashboardView },
    { path: '/findings', component: FindingsTable },
    { path: '/sessions/:project/:hash', component: TurnDetailView, props: true },
  ],
})
```

- [ ] **Step 7: src/App.vue (placeholder shell)**

```vue
<script setup lang="ts">
</script>
<template>
  <div class="app-shell">
    <header><router-link to="/">traj-error-pattern</router-link></header>
    <main><router-view /></main>
  </div>
</template>
```

- [ ] **Step 8: Install + dev server smoke test**

```bash
cd traj-error-pattern/frontend
npm install
npm run dev &
sleep 2
curl -s http://localhost:5174 | head -c 200
kill %1
```

Expected: HTML with `<div id="app">` is returned.

- [ ] **Step 9: Commit**

```bash
git add traj-error-pattern/frontend/{package.json,vite.config.ts,tsconfig.json,index.html} \
        traj-error-pattern/frontend/src/{main.ts,App.vue,router.ts}
git commit -m "feat(frontend): Vue 3 + Vite + router scaffold"
```

---

### Task 7.2: API client + shared types

**Files:**
- Create: `traj-error-pattern/frontend/src/types.ts`
- Create: `traj-error-pattern/frontend/src/api.ts`

- [ ] **Step 1: src/types.ts (mirror backend models)**

```ts
export type Severity = 'low' | 'med' | 'high'
export type Source = 'rule' | 'llm'

export interface Finding {
  finding_id: string
  category: string
  subtype: string
  severity: Severity
  source: Source
  step_ids: number[]
  evidence?: Record<string, unknown> | null
  rule_id?: string | null
  evidence_text?: string | null
  confidence?: number | null
  root_cause_hypothesis?: string | null
  judge_prompt_version?: string | null
  judge_model?: string | null
}

export interface ErrorReport {
  turn_id: number
  agent_run_id: string
  user_message_excerpt: string
  step_count: number
  tool_calls_count: number
  findings: Finding[]
  metrics: Record<string, number>
}

export interface SessionReport {
  schema_version: string
  project: string
  session_hash: string
  session_id: string
  generated_at: string
  turns: ErrorReport[]
}

export interface ProjectAggregate {
  schema_version: string
  project: string
  generated_at: string
  session_count: number
  turn_count: number
  totals_by_category: Record<string, number>
  totals_by_subtype: Record<string, number>
  severity_breakdown: Record<string, number>
  by_tool: Record<string, { total: number; categories: Record<string, number> }>
  by_phase: Record<string, { total: number; categories: Record<string, number> }>
  top_offending_sessions: Array<{ session_hash: string; high_severity_count: number; total_findings: number }>
  examples_per_subtype: Record<string, Array<{ session_hash: string; turn_id: number; finding_id: string }>>
}

export interface ProjectInfo {
  name: string
  session_count: number
  turn_count: number
  last_analyzed_at?: string | null
}
```

- [ ] **Step 2: src/api.ts**

```ts
import type { ProjectInfo, ProjectAggregate, SessionReport, Finding } from './types'

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${path}: ${r.status}`)
  return r.json() as Promise<T>
}

export const api = {
  projects: () => get<ProjectInfo[]>('/api/projects'),
  aggregate: (project: string) => get<ProjectAggregate>(`/api/aggregates/${project}`),
  sessions: (q: { project: string; category?: string; subtype?: string; severity?: string; min_findings?: number }) => {
    const p = new URLSearchParams({ project: q.project })
    if (q.category) p.set('category', q.category)
    if (q.subtype) p.set('subtype', q.subtype)
    if (q.severity) p.set('severity', q.severity)
    if (q.min_findings) p.set('min_findings', String(q.min_findings))
    return get<Array<{ session_hash: string; session_id: string; turn_count: number; finding_count: number; high_severity_count: number }>>(`/api/sessions?${p}`)
  },
  session: (project: string, hash: string) => get<SessionReport>(`/api/sessions/${project}/${hash}`),
  findings: (project: string, subtype?: string, limit = 200) => {
    const p = new URLSearchParams({ project, limit: String(limit) })
    if (subtype) p.set('subtype', subtype)
    return get<Array<{ session_hash: string; turn_id: number; finding: Finding }>>(`/api/findings?${p}`)
  },
  comparison: (projects: string[]) => get<Record<string, { turn_count: number; rates_by_category: Record<string, number>; rates_by_subtype: Record<string, number> }>>(`/api/comparison?projects=${projects.join(',')}`),
}
```

- [ ] **Step 3: Commit**

```bash
git add traj-error-pattern/frontend/src/types.ts traj-error-pattern/frontend/src/api.ts
git commit -m "feat(frontend): typed API client"
```

---

### Task 7.3: Frontend visual design (use frontend-design skill)

**Files:**
- Create: `traj-error-pattern/frontend/src/styles/tokens.css`
- Create: `traj-error-pattern/frontend/src/styles/base.css`

- [ ] **Step 1: Invoke the frontend-design skill**

Invoke the `frontend-design:frontend-design` skill with this brief:

> Build the visual layer for `traj-error-pattern/frontend`. The app has three views — an aggregate dashboard (project picker, summary tiles, category histogram, severity heatmap, project comparison, top-offending sessions table, by-tool breakdown), a flat findings table, and a per-turn drill-down with steps annotated by inline error badges.
>
> Required visual conventions (do not invent alternatives):
> - Severity colors: high=red, med=amber, low=slate
> - Source distinction: rule findings = solid border, llm findings = dashed border
> - Phase colors must match traj-viz: blue=localization, violet=editing, green=verification, gold=submission
>
> Produce `src/styles/tokens.css` (CSS custom properties for the colors above plus typography/spacing scale) and `src/styles/base.css` (reset + app-shell layout). The skill should also propose component class names and HTML structures for `CategoryHistogram`, `SeverityHeatmap`, `ProjectComparison`, `FindingsTable`, `ErrorAnnotatedStep`, `FindingBadge`, `SubtypeFilter` so subsequent tasks can implement them.

- [ ] **Step 2: Wire styles into src/main.ts**

Add at top of `src/main.ts`:

```ts
import './styles/tokens.css'
import './styles/base.css'
```

- [ ] **Step 3: Verify dev server still renders**

```bash
cd traj-error-pattern/frontend
npm run dev &
sleep 2
curl -s http://localhost:5174 > /dev/null && echo OK
kill %1
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add traj-error-pattern/frontend/src/styles/ traj-error-pattern/frontend/src/main.ts
git commit -m "feat(frontend): design tokens + base styles via frontend-design skill"
```

---

### Task 7.4: Reusable components (FindingBadge, ErrorAnnotatedStep, SubtypeFilter)

**Files:**
- Create: `traj-error-pattern/frontend/src/components/FindingBadge.vue`
- Create: `traj-error-pattern/frontend/src/components/ErrorAnnotatedStep.vue`
- Create: `traj-error-pattern/frontend/src/components/SubtypeFilter.vue`

- [ ] **Step 1: FindingBadge.vue**

```vue
<script setup lang="ts">
import type { Finding } from '../types'
defineProps<{ finding: Finding }>()
</script>
<template>
  <span :class="['finding-badge', `sev-${finding.severity}`, `src-${finding.source}`]">
    {{ finding.subtype }}
    <em v-if="finding.confidence != null">{{ (finding.confidence * 100).toFixed(0) }}%</em>
  </span>
</template>
<style scoped>
.finding-badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:12px; margin:2px 4px 2px 0; }
.sev-high { background: var(--c-sev-high-bg); color: var(--c-sev-high-fg); }
.sev-med  { background: var(--c-sev-med-bg);  color: var(--c-sev-med-fg);  }
.sev-low  { background: var(--c-sev-low-bg);  color: var(--c-sev-low-fg);  }
.src-rule { border: 1px solid currentColor; }
.src-llm  { border: 1px dashed currentColor; }
.finding-badge em { font-style: normal; opacity: .7; margin-left: 4px; }
</style>
```

- [ ] **Step 2: ErrorAnnotatedStep.vue**

```vue
<script setup lang="ts">
import type { Finding } from '../types'
import FindingBadge from './FindingBadge.vue'
const props = defineProps<{ stepId: number; phase?: string | null; toolName: string;
  argsBrief: string; observationExcerpt: string; status: string; findings: Finding[] }>()
</script>
<template>
  <div :class="['step', `phase-${phase || 'unknown'}`, `status-${status}`]">
    <div class="step-header">
      <span class="step-id">#{{ stepId }}</span>
      <span class="tool">{{ toolName }}</span>
      <span class="phase-tag" v-if="phase">{{ phase }}</span>
    </div>
    <div class="step-args">{{ argsBrief }}</div>
    <div class="step-obs" v-if="observationExcerpt">{{ observationExcerpt }}</div>
    <div class="step-findings" v-if="findings.length">
      <FindingBadge v-for="f in findings" :key="f.finding_id" :finding="f" />
    </div>
  </div>
</template>
<style scoped>
.step { border-left: 4px solid var(--c-border); padding: 8px 12px; margin: 6px 0; background: var(--c-surface); }
.phase-localization { border-left-color: var(--c-phase-localization); }
.phase-editing      { border-left-color: var(--c-phase-editing);      }
.phase-verification { border-left-color: var(--c-phase-verification); }
.phase-submission   { border-left-color: var(--c-phase-submission);   }
.status-error { background: var(--c-error-tint); }
.step-header { display:flex; gap:8px; align-items:center; font-weight:600; }
.tool { color: var(--c-accent); }
.step-args, .step-obs { font-family: var(--font-mono); font-size: 12px; white-space: pre-wrap; }
</style>
```

- [ ] **Step 3: SubtypeFilter.vue**

```vue
<script setup lang="ts">
defineProps<{ modelValue: string; subtypes: string[] }>()
defineEmits<{ (e: 'update:modelValue', v: string): void }>()
</script>
<template>
  <select :value="modelValue" @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)">
    <option value="">all subtypes</option>
    <option v-for="s in subtypes" :key="s" :value="s">{{ s }}</option>
  </select>
</template>
```

- [ ] **Step 4: Commit**

```bash
git add traj-error-pattern/frontend/src/components/
git commit -m "feat(frontend): FindingBadge / ErrorAnnotatedStep / SubtypeFilter components"
```

---

### Task 7.5: Chart components (CategoryHistogram, SeverityHeatmap, ProjectComparison)

**Files:**
- Create: `traj-error-pattern/frontend/src/components/CategoryHistogram.vue`
- Create: `traj-error-pattern/frontend/src/components/SeverityHeatmap.vue`
- Create: `traj-error-pattern/frontend/src/components/ProjectComparison.vue`

- [ ] **Step 1: CategoryHistogram.vue**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Title } from 'chart.js'
ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Title)

const props = defineProps<{ counts: Record<string, number> }>()
const emit = defineEmits<{ (e: 'select', category: string): void }>()

const data = computed(() => ({
  labels: Object.keys(props.counts),
  datasets: [{ label: 'findings', data: Object.values(props.counts), backgroundColor: '#6366f1' }],
}))
const options = {
  responsive: true,
  onClick: (_e: any, els: any[]) => {
    if (els.length) emit('select', Object.keys(props.counts)[els[0].index])
  },
}
</script>
<template>
  <Bar :data="data" :options="options" />
</template>
```

- [ ] **Step 2: SeverityHeatmap.vue**

```vue
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ totalsBySubtype: Record<string, number>; totalsByCategory: Record<string, number> }>()

const rows = computed(() => Object.entries(props.totalsBySubtype).sort((a,b) => b[1]-a[1]))
const max = computed(() => Math.max(1, ...Object.values(props.totalsBySubtype)))
function shade(v: number) {
  const t = v / max.value
  return `rgba(220,38,38,${0.15 + 0.85 * t})`
}
</script>
<template>
  <div class="heatmap">
    <div v-for="[sub, n] in rows" :key="sub" class="row">
      <span class="label">{{ sub }}</span>
      <span class="cell" :style="{ background: shade(n) }">{{ n }}</span>
    </div>
  </div>
</template>
<style scoped>
.heatmap { display:grid; gap:4px; }
.row { display:grid; grid-template-columns: 280px 1fr; gap: 8px; align-items:center; font-size: 12px; }
.cell { padding: 4px 8px; border-radius: 4px; color: white; text-align: center; min-width: 30px; }
</style>
```

- [ ] **Step 3: ProjectComparison.vue**

```vue
<script setup lang="ts">
defineProps<{ data: Record<string, { turn_count: number; rates_by_category: Record<string, number> }> }>()
</script>
<template>
  <table class="comparison">
    <thead><tr><th>category</th><th v-for="(_, p) in data" :key="p">{{ p }} (per 100 turns)</th></tr></thead>
    <tbody>
      <tr v-for="cat in [...new Set(Object.values(data).flatMap(v => Object.keys(v.rates_by_category)))]" :key="cat">
        <td>{{ cat }}</td>
        <td v-for="(v, p) in data" :key="p">{{ v.rates_by_category[cat]?.toFixed(1) ?? '-' }}</td>
      </tr>
    </tbody>
  </table>
</template>
<style scoped>
.comparison { width:100%; font-size: 13px; border-collapse: collapse; }
.comparison th, .comparison td { border-bottom: 1px solid var(--c-border); padding: 6px 10px; text-align: left; }
</style>
```

- [ ] **Step 4: Commit**

```bash
git add traj-error-pattern/frontend/src/components/{CategoryHistogram,SeverityHeatmap,ProjectComparison}.vue
git commit -m "feat(frontend): aggregate chart components"
```

---

### Task 7.6: DashboardView

**Files:**
- Create: `traj-error-pattern/frontend/src/views/DashboardView.vue`

- [ ] **Step 1: Implement**

```vue
<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import type { ProjectInfo, ProjectAggregate } from '../types'
import CategoryHistogram from '../components/CategoryHistogram.vue'
import SeverityHeatmap from '../components/SeverityHeatmap.vue'
import ProjectComparison from '../components/ProjectComparison.vue'

const projects = ref<ProjectInfo[]>([])
const selected = ref<string>('')
const agg = ref<ProjectAggregate | null>(null)
const comparison = ref<Record<string, any> | null>(null)
const router = useRouter()

onMounted(async () => {
  projects.value = await api.projects()
  if (projects.value.length) selected.value = projects.value[0].name
  if (projects.value.length >= 2) {
    comparison.value = await api.comparison(projects.value.map(p => p.name))
  }
})

watch(selected, async (p) => {
  if (!p) return
  agg.value = await api.aggregate(p)
})

function onSelectCategory(cat: string) {
  router.push({ path: '/findings', query: { project: selected.value, category: cat }})
}
</script>

<template>
  <section class="dashboard">
    <header class="picker">
      <label>Project:
        <select v-model="selected">
          <option v-for="p in projects" :key="p.name" :value="p.name">
            {{ p.name }} ({{ p.session_count }} sessions)
          </option>
        </select>
      </label>
    </header>

    <div v-if="agg" class="tiles">
      <div class="tile"><b>{{ agg.session_count }}</b><span>sessions</span></div>
      <div class="tile"><b>{{ agg.turn_count }}</b><span>turns</span></div>
      <div class="tile"><b>{{ Object.values(agg.totals_by_subtype).reduce((a,b)=>a+b,0) }}</b><span>findings</span></div>
      <div class="tile"><b>{{ agg.severity_breakdown.high || 0 }}</b><span>high severity</span></div>
    </div>

    <section v-if="agg" class="card">
      <h2>By category</h2>
      <CategoryHistogram :counts="agg.totals_by_category" @select="onSelectCategory" />
    </section>

    <section v-if="agg" class="card">
      <h2>Severity heatmap (subtype)</h2>
      <SeverityHeatmap :totals-by-subtype="agg.totals_by_subtype" :totals-by-category="agg.totals_by_category" />
    </section>

    <section v-if="comparison" class="card">
      <h2>Project comparison</h2>
      <ProjectComparison :data="comparison" />
    </section>

    <section v-if="agg" class="card">
      <h2>Top offending sessions</h2>
      <ul>
        <li v-for="s in agg.top_offending_sessions" :key="s.session_hash">
          <router-link :to="`/sessions/${selected}/${s.session_hash}`">{{ s.session_hash }}</router-link>
          — {{ s.high_severity_count }} high / {{ s.total_findings }} total
        </li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.tiles { display:grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin: 16px 0; }
.tile { padding: 16px; background: var(--c-surface); border-radius: 8px; display:flex; flex-direction:column; }
.tile b { font-size: 28px; }
.tile span { color: var(--c-muted); font-size: 12px; }
.card { background: var(--c-surface); border-radius: 8px; padding: 16px; margin: 16px 0; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add traj-error-pattern/frontend/src/views/DashboardView.vue
git commit -m "feat(frontend): DashboardView with tiles/histogram/heatmap/comparison/top-sessions"
```

---

### Task 7.7: FindingsTable view

**Files:**
- Create: `traj-error-pattern/frontend/src/views/FindingsTable.vue`

- [ ] **Step 1: Implement**

```vue
<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import FindingBadge from '../components/FindingBadge.vue'

const route = useRoute()
const rows = ref<Array<any>>([])

async function load() {
  const project = (route.query.project as string) || 'wzp'
  const subtype = (route.query.subtype as string) || undefined
  rows.value = await api.findings(project, subtype, 500)
}

onMounted(load)
watch(() => route.query, load)
</script>
<template>
  <section>
    <h2>Findings — {{ route.query.project }} <small v-if="route.query.subtype">/ {{ route.query.subtype }}</small></h2>
    <table class="findings">
      <thead><tr><th>session</th><th>turn</th><th>finding</th><th>evidence</th></tr></thead>
      <tbody>
        <tr v-for="r in rows" :key="r.finding.finding_id">
          <td><router-link :to="`/sessions/${route.query.project}/${r.session_hash}`">{{ r.session_hash }}</router-link></td>
          <td>#{{ r.turn_id }}</td>
          <td><FindingBadge :finding="r.finding" /></td>
          <td><code>{{ r.finding.evidence_text || JSON.stringify(r.finding.evidence) }}</code></td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
<style scoped>
.findings { width: 100%; font-size: 13px; border-collapse: collapse; }
.findings th, .findings td { border-bottom: 1px solid var(--c-border); padding: 6px 10px; text-align: left; vertical-align: top; }
code { white-space: pre-wrap; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add traj-error-pattern/frontend/src/views/FindingsTable.vue
git commit -m "feat(frontend): FindingsTable view"
```

---

### Task 7.8: TurnDetailView with annotated steps

**Files:**
- Create: `traj-error-pattern/frontend/src/views/TurnDetailView.vue`

- [ ] **Step 1: Implement**

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import type { SessionReport, Finding } from '../types'
import ErrorAnnotatedStep from '../components/ErrorAnnotatedStep.vue'
import FindingBadge from '../components/FindingBadge.vue'

const props = defineProps<{ project: string; hash: string }>()
const report = ref<SessionReport | null>(null)

onMounted(async () => {
  report.value = await api.session(props.project, props.hash)
})

function findingsForStep(turnFindings: Finding[], stepId: number) {
  return turnFindings.filter(f => f.step_ids.includes(stepId))
}
</script>
<template>
  <section v-if="report">
    <h2>{{ report.project }} / {{ report.session_hash }}</h2>
    <p class="meta">session_id: <code>{{ report.session_id }}</code> · {{ report.turns.length }} turns</p>

    <article v-for="tr in report.turns" :key="tr.agent_run_id" class="turn">
      <header>
        <h3>Turn #{{ tr.turn_id }} — {{ tr.step_count }} steps · {{ tr.tool_calls_count }} tool calls</h3>
        <p class="user-msg">{{ tr.user_message_excerpt }}</p>
        <div class="badges">
          <FindingBadge v-for="f in tr.findings" :key="f.finding_id" :finding="f" />
        </div>
      </header>
      <!-- Step list — synthesized: backend gives us metric counts only, full step text lives in .traj.
           For now we render finding-anchored placeholders showing the steps each finding cites. -->
      <div class="steps">
        <ErrorAnnotatedStep
          v-for="f in tr.findings" :key="f.finding_id"
          :step-id="f.step_ids[0] || 0"
          :phase="null"
          :tool-name="(f.evidence?.tool_name as string) || '(see evidence)'"
          :args-brief="JSON.stringify(f.evidence || {})"
          :observation-excerpt="f.evidence_text || (f.evidence?.text as string) || ''"
          :status="f.severity === 'high' ? 'error' : 'ok'"
          :findings="[f]"
        />
      </div>
    </article>
  </section>
  <section v-else>Loading…</section>
</template>
<style scoped>
.turn { background: var(--c-surface); border-radius: 8px; padding: 16px; margin: 16px 0; }
.user-msg { color: var(--c-muted); font-style: italic; }
.meta code { font-size: 11px; color: var(--c-muted); }
.badges { margin: 8px 0; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add traj-error-pattern/frontend/src/views/TurnDetailView.vue
git commit -m "feat(frontend): TurnDetailView with annotated steps"
```

---

### Task 7.9: End-to-end smoke test (analyzer → backend → frontend)

- [ ] **Step 1: Run analyzer with rules only (cheap)**

```bash
cd traj-error-pattern/agent-error-process
.venv/bin/agent-error-process analyze --project wzp --no-llm
.venv/bin/agent-error-process analyze --project zzj --no-llm
```

Expected: per-turn JSONs + aggregate JSON written for both projects.

- [ ] **Step 2: Start backend**

```bash
cd ../backend
.venv/bin/uvicorn backend.main:app --port 8001 --reload &
sleep 1
curl -s http://localhost:8001/api/projects | python3 -m json.tool | head -30
```

Expected: list contains both `wzp` and `zzj`.

- [ ] **Step 3: Start frontend dev server**

```bash
cd ../frontend
npm run dev
```

Expected: open `http://localhost:5174` in a browser, see the dashboard, switch projects, click a category bar → lands on FindingsTable, click a top-offending session → lands on TurnDetailView.

- [ ] **Step 4: Smoke test the LLM pipeline (small slice)**

```bash
cd ../agent-error-process
ls traj-data-new/zzj/ | head -1   # use only 1 small session
DASHSCOPE_API_KEY=$DASHSCOPE_API_KEY .venv/bin/agent-error-process analyze --project zzj --max-llm-calls 5
```

Expected: completes; LLM cache directory `data/llm_cache/` populated; second invocation reports `cache_hits > 0`.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: complete end-to-end smoke test of traj-error-pattern"
```

---

## Phase 8 — Project hygiene

### Task 8.1: Top-level README + run instructions

**Files:**
- Modify: `traj-error-pattern/README.md`

- [ ] **Step 1: Expand README with runbook**

Append to existing `traj-error-pattern/README.md`:

```markdown

## Running

### 1. Analyzer (write JSON outputs)

```bash
cd agent-error-process
python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"
export DASHSCOPE_API_KEY=...
.venv/bin/agent-error-process analyze --project all                # rules + LLM
.venv/bin/agent-error-process analyze --project all --no-llm       # rules only
.venv/bin/agent-error-process analyze --project wzp --refresh-llm  # bypass cache
```

Output: `agent-error-process/data/per_turn/{project}/*.json` + `aggregates/{project}.summary.json`

### 2. Backend

```bash
cd backend
python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn backend.main:app --port 8001 --reload
```

API: <http://localhost:8001/api/projects>

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: <http://localhost:5174>

## Tests

```bash
cd agent-error-process && .venv/bin/pytest -v
cd backend && .venv/bin/pytest -v
```

## Spec

See `docs/superpowers/specs/2026-04-20-traj-error-pattern-design.md`.
```

- [ ] **Step 2: Commit**

```bash
git add traj-error-pattern/README.md
git commit -m "docs: README runbook for analyzer/backend/frontend"
```

---

## Spec coverage map

| Spec section | Covered by |
|---|---|
| §3.1 Analyzer pipeline | Phases 1–5 |
| §3.2 Backend endpoints | Phase 6 (Tasks 6.1–6.4) |
| §3.3 Frontend routes/views/components | Phase 7 (Tasks 7.1–7.8) |
| §4 Taxonomy (2-level) | Task 1.2 + per-detector tasks 3.2–3.7 |
| §5 Per-turn / aggregate JSON contract | Task 1.3 + Task 5.2 |
| §6 LLM judge (qwen3.6-plus, cache, prompts) | Tasks 4.1–4.3 |
| §7 CLI surface | Task 5.3 |
| §8 Testing strategy | Test steps in every task + Tasks 5.4, 6.2, 7.9 |
| §10 Success criteria | Task 7.9 (end-to-end smoke) |


