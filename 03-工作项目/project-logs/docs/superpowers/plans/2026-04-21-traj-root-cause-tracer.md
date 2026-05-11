# traj-root-cause-tracer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 7-stage LLM pipeline that traces every `ai_output_correction` / `bug_report` user prompt back to the agent step that introduced the defect, with cross-session genesis tracing and validation against the agent's own subsequent fix.

**Architecture:** Two-tier model routing (`qwen-flash` + `qwen-plus-latest`) over precomputed glossary and step-summary caches. Deterministic gates wrap LLM calls (entity grounding, step-ID grounding, closed-vocab failure modes, both-sides diff symbol matching for validation). Snapshot-by-output-file resume. Output: per-case JSON evidence chains under `traces/<dataset>/<project>/`.

**Tech Stack:** Python 3.10+, asyncio, openai SDK against DashScope OpenAI-compatible endpoint, pytest + pytest-asyncio, dataclasses (no pydantic).

**Spec:** `docs/superpowers/specs/2026-04-21-traj-root-cause-tracer-design.md` — keep open while executing.

**Working dir:** `/Users/xd/Desktop/work/project-logs/traj-err-trace/` — all paths below relative to this unless absolute.

---

## File map

```
traj-err-trace/
├── tracing/
│   ├── __init__.py
│   ├── settings.py              # paths, model names, constants
│   ├── models.py                # dataclasses: TraceCase, StepSummary, EvidenceChain, ...
│   ├── logging_setup.py         # 3 log streams (run / events / failures)
│   ├── data_io.py               # load .traj + classified JSON; iter trigger prompts
│   ├── llm.py                   # LLM client Protocol + DashScope impl + Fake impl
│   ├── prompts.py               # all stage prompts (literal text from spec §11)
│   ├── step_summary.py          # build per-session step-summary cache
│   ├── glossary.py              # build per-session glossary cache
│   ├── corpus.py                # build _global.jsonl cross-session corpus
│   ├── stage2_context.py        # deterministic context loader
│   ├── stage3_entities.py       # qwen-flash entity resolution
│   ├── stage4_candidates.py     # qwen-flash batched scoring
│   ├── stage5_attribution.py    # qwen-plus attribution
│   ├── stage6_genesis.py        # genesis trace (gate + retrieval + confirm)
│   ├── stage7_validation.py     # deterministic validator + flash escape
│   ├── pipeline.py              # 7-stage orchestrator per case
│   ├── trace.py                 # CLI entry (argparse, asyncio main)
│   ├── run.sh                   # nohup launcher
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py          # fixtures
│       ├── fixtures/
│       │   ├── mini.traj        # tiny synthetic .traj for unit tests
│       │   └── mini.classified.json
│       ├── test_data_io.py
│       ├── test_step_summary.py
│       ├── test_glossary.py
│       ├── test_corpus.py
│       ├── test_stage2_context.py
│       ├── test_stage3_entities.py
│       ├── test_stage4_candidates.py
│       ├── test_stage5_attribution.py
│       ├── test_stage6_genesis.py
│       ├── test_stage7_validation.py
│       ├── test_pipeline.py
│       └── test_e2e_canonical.py    # uses real wzp/6b8566ea data + fake LLM
└── extraction/cache/<dataset>/<project>/   # NEW (consumed by tracing)
    ├── glossary/<session>.json
    └── step-summary/
        ├── <session>.jsonl
        └── _global.jsonl
```

---

## Phase A · Foundations

### Task 1: Project skeleton, deps, settings, models, logging

**Files:**
- Create: `tracing/__init__.py`, `tracing/settings.py`, `tracing/models.py`, `tracing/logging_setup.py`, `tracing/tests/__init__.py`, `tracing/tests/conftest.py`, `pyproject.toml` (or update existing `extraction/requirements.txt`)
- Create: `tracing/tests/test_logging_setup.py`

- [ ] **Step 1: Verify Python and create venv**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-err-trace
python3 --version    # expect 3.10+ ; if 3.9 install python@3.10 first
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install 'openai>=1.40.0' 'pytest>=8.0' 'pytest-asyncio>=0.23'
pip freeze > tracing/requirements.txt
```

Expected: `tracing/requirements.txt` lists openai, pytest, pytest-asyncio with concrete versions.

- [ ] **Step 2: Create `tracing/settings.py`**

```python
"""Central paths and constants. Override via CLI flags in trace.py."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DATASET_ROOT    = ROOT / "traj-data-new"
DEFAULT_CLASSIFIED_ROOT = ROOT / "examples"
DEFAULT_OUTPUT_ROOT     = ROOT / "traces"
DEFAULT_CACHE_ROOT      = ROOT / "extraction" / "cache"

DEFAULT_THINKING_MODEL = "qwen-plus-latest"
DEFAULT_SMALL_MODEL    = "qwen-flash"
DASHSCOPE_BASE_URL     = "https://dashscope.aliyuncs.com/compatible-mode/v1"

MAX_CONCURRENCY    = 3
PER_CALL_TIMEOUT_S = 60.0
MAX_RETRIES        = 2          # one soft retry on validator violation; one hard retry on transient error

# Step filtering — the action-only set (§4 of spec)
ACTION_TOOLS = frozenset({
    "mcp__mkr__Edit", "mcp__mkr__Write", "mcp__mkr__Read",
    "Grep", "Glob", "mcp__mkr__Bash", "mcp__sce-urhox__build", "Task",
    "TodoWrite",   # weak signal — kept but de-prioritised
})
THINKING_TOOL = "respond_to_user"  # filtered from candidates but its thought folded into prior_thought

# Trigger filter — which classified prompts get traced (§2 of spec)
TRIGGER_INTENTS = frozenset({"ai_output_correction", "bug_report"})

# Stage 4 score thresholds
CANDIDATE_SCORE_KEEP = 2
CANDIDATE_TOP_K      = 8
CANDIDATE_BATCH      = 50

# Stage 7 validation
POSTERIOR_WINDOW = 30  # max steps after correction to consider as fix
```

- [ ] **Step 3: Create `tracing/models.py`**

```python
"""Shared dataclasses. Plain stdlib — no pydantic dependency."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class GlossaryEntry:
    name: str
    kind: Literal["level", "npc", "ui_element", "document", "system", "feature", "unknown"]
    canonical: str
    evidence: Literal["observed_names", "file_paths_touched", "grep_patterns_seen"]


@dataclass
class StepSummary:
    step: int
    turn: int
    tool: str
    file: Optional[str]
    summary: str
    introduces_symbols: list[str]
    removes_symbols: list[str]
    preserves_symbols: list[str]
    prior_thought: Optional[str]
    obs_excerpt: str
    timestamp: str
    session: Optional[str] = None  # filled only in _global corpus


@dataclass
class EntityRef:
    path_or_name: str
    source: Literal["glossary", "observed", "hypothesis"]
    confidence: Literal["high", "medium", "low"]


@dataclass
class ResolvedEntities:
    artifacts: list[EntityRef]
    symbols: list[EntityRef]
    surface: str
    user_intent_restated: str
    insufficient_evidence: bool


@dataclass
class CandidateScore:
    step: int
    score: int  # 0..3
    reason: str


@dataclass
class EvidenceSlot:
    text: str
    ref: dict[str, Any] = field(default_factory=dict)
    refs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class EvidenceChain:
    complaint: EvidenceSlot
    symptom: EvidenceSlot
    broken_state: Optional[EvidenceSlot]
    introducing: EvidenceSlot
    missing_check: Optional[EvidenceSlot]


@dataclass
class FixTarget:
    file: str
    symbol: str


@dataclass
class AttributionResult:
    evidence_chain: EvidenceChain
    proximate_root: dict[str, Any]
    genesis_check: dict[str, Any]
    failure_mode: str
    counter_pattern: str
    predicted_fix_target: list[FixTarget]
    attribution_confidence: Literal["high", "medium", "low", "candidates_insufficient"]


@dataclass
class GenesisResult:
    found: bool
    session: Optional[str] = None
    step: Optional[int] = None
    file: Optional[str] = None
    symbol: Optional[str] = None
    note: str = ""


@dataclass
class ValidationResult:
    confidence: Literal["high", "medium", "low", "unverified"]
    actual_fix_targets: list[dict[str, Any]]


@dataclass
class TraceCase:
    """One unit of work — flows through the entire pipeline."""
    dataset: str
    project: str
    session_id: str
    turn_id: int
    complaint_raw: str
    complaint_index_in_classified: int
    classification: dict[str, Any]
```

- [ ] **Step 4: Create `tracing/__init__.py`**

```python
"""traj-root-cause-tracer — see docs/superpowers/specs/2026-04-21-traj-root-cause-tracer-design.md"""
__version__ = "0.1.0"
```

- [ ] **Step 5: Write the failing test for logging setup**

`tracing/tests/test_logging_setup.py`:

```python
import json
from pathlib import Path
import pytest
from tracing.logging_setup import setup_logging, log_event


def test_setup_logging_creates_three_streams(tmp_path):
    paths = setup_logging(log_dir=tmp_path, level="INFO")
    assert paths["run_log"].exists()
    assert paths["events_log"].exists()
    assert paths["failures_dir"].exists() and paths["failures_dir"].is_dir()
    assert (tmp_path / "latest.log").is_symlink()


def test_log_event_writes_jsonl(tmp_path):
    paths = setup_logging(log_dir=tmp_path, level="INFO")
    log_event(events_path=paths["events_log"], trace_id="t1", stage=3,
              model="qwen-flash", duration_ms=120, input_tokens_est=400,
              output_tokens_est=80, outcome="ok")
    lines = paths["events_log"].read_text().strip().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["trace_id"] == "t1" and obj["stage"] == 3 and obj["outcome"] == "ok"
```

- [ ] **Step 6: Run test, expect ImportError**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-err-trace
.venv/bin/pytest tracing/tests/test_logging_setup.py -v
```

Expected: FAIL — `ModuleNotFoundError: tracing.logging_setup`

- [ ] **Step 7: Implement `tracing/logging_setup.py`**

```python
"""Three log streams: run log, structured events JSONL, failure dumps."""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def setup_logging(log_dir: Path, level: str = "INFO") -> dict[str, Path]:
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    failures_dir = log_dir / "failures"
    failures_dir.mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    run_log    = log_dir / f"trace-{ts}.log"
    events_log = log_dir / f"events-{ts}.jsonl"

    # touch both so symlink + jsonl writes succeed without race
    run_log.touch()
    events_log.touch()

    latest = log_dir / "latest.log"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    os.symlink(run_log.name, latest)

    handlers: list[logging.Handler] = [logging.FileHandler(run_log), logging.StreamHandler()]
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)sZ %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )
    return {"run_log": run_log, "events_log": events_log, "failures_dir": failures_dir}


def log_event(events_path: Path, trace_id: str, stage: int, model: str,
              duration_ms: int, input_tokens_est: int, output_tokens_est: int,
              outcome: str, violation: str | None = None, extra: dict[str, Any] | None = None) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "trace_id": trace_id, "stage": stage, "model": model,
        "duration_ms": duration_ms,
        "input_tokens_est": input_tokens_est, "output_tokens_est": output_tokens_est,
        "outcome": outcome, "violation": violation, "extra": extra or {},
    }
    with events_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def dump_failure(failures_dir: Path, trace_id: str, payload: dict[str, Any]) -> Path:
    out = failures_dir / f"{trace_id}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
```

- [ ] **Step 8: Run test, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_logging_setup.py -v
```

Expected: 2 passed.

- [ ] **Step 9: Create `tracing/tests/conftest.py` with shared fixtures**

```python
import json
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def mini_traj_path(tmp_path: Path) -> Path:
    """A minimal valid v2 .traj file used by many tests."""
    data = {
        "schema_version": "2.0",
        "conversation_id": "test-conv",
        "agent": {"name": "claude-code", "model": "test", "environment": "test", "tool_protocol": "claude_tool_use"},
        "session_metadata": {
            "project": "wzp", "project_name": "脑力大冒险",
            "session_id": "minisess", "started_at": "2026-04-01T00:00:00Z",
            "ended_at": "2026-04-01T00:10:00Z", "duration_sec": 600.0,
            "cwd": "/workspace", "version": "test", "git_branch": "",
        },
        "messages": [
            {"turn_id": 1, "role": "user", "content": "在糖糖的冰火花园，增加4个冰块",
             "timestamp": "2026-04-01T00:00:00Z"},
            {"turn_id": 1, "agent_run_id": "r1", "steps": [
                {"step_id": 10, "phase": "editing", "thinking": None,
                 "thought": "需要新增 4 个冰冻格。",
                 "action": {"tool_name": "respond_to_user", "tool_use_id": "", "args": {}},
                 "observation": {"type": "text", "text": "", "exit_code": None},
                 "state": None, "status": "ok",
                 "timestamp": "2026-04-01T00:00:05Z", "execution_time": 1.0,
                 "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0, "cache_creation_tokens": 0}},
                {"step_id": 11, "phase": "editing", "thinking": None, "thought": None,
                 "action": {"tool_name": "mcp__mkr__Edit", "tool_use_id": "u1",
                            "args": {"file_path": "/workspace/story-27.lua",
                                     "old_string": "frozenCells = { {4,4} }",
                                     "new_string": "frozenCells = { {4,4}, {3,2}, {7,2}, {5,8}, {8,5} }"}},
                 "observation": {"type": "tool_result", "text": "+++ story-27.lua @@ frozenCells +4 lines",
                                 "exit_code": None},
                 "state": None, "status": "ok",
                 "timestamp": "2026-04-01T00:00:10Z", "execution_time": 0.3,
                 "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0, "cache_creation_tokens": 0}},
            ]},
            {"turn_id": 2, "role": "user", "content": "游戏内没有看到冰块",
             "timestamp": "2026-04-01T00:00:20Z"},
            {"turn_id": 2, "agent_run_id": "r2", "steps": [
                {"step_id": 20, "phase": "editing", "thinking": None, "thought": None,
                 "action": {"tool_name": "mcp__mkr__Edit", "tool_use_id": "u2",
                            "args": {"file_path": "/workspace/story-27.lua",
                                     "old_string": "frozenCells = { {4,4}, {3,2}, {7,2}, {5,8}, {8,5} }",
                                     "new_string": "icePositions = { {4,4}, {3,2}, {7,2}, {5,8}, {8,5} }"}},
                 "observation": {"type": "tool_result", "text": "rename ok", "exit_code": None},
                 "state": None, "status": "ok",
                 "timestamp": "2026-04-01T00:00:30Z", "execution_time": 0.3,
                 "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0, "cache_creation_tokens": 0}},
            ]},
        ],
        "phases": [], "markers": [], "subagents": [], "summary": {},
    }
    p = tmp_path / "minisess.traj"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


@pytest.fixture
def mini_classified_path(tmp_path: Path) -> Path:
    data = {
        "session_id": "minisess", "project": "wzp", "model": "test",
        "prompt_count": 2, "extracted_at": "2026-04-01T00:00:00Z",
        "prompts": [
            {"index": 0, "raw": "在糖糖的冰火花园，增加4个冰块",
             "classification": {
                 "intent_primary": "new_feature", "intent_secondary": [],
                 "target_artifact": "game_logic", "is_correction_of_ai_work": False,
                 "urgency": "normal", "has_attached_doc": False, "mentions_specific_file": False,
                 "summary_zh": "在冰火花园增加4个冰块", "summary_en": "Add 4 ice blocks",
                 "reasoning": ""}, "error": None},
            {"index": 1, "raw": "游戏内没有看到冰块",
             "classification": {
                 "intent_primary": "bug_report", "intent_secondary": [],
                 "target_artifact": "game_logic", "is_correction_of_ai_work": True,
                 "urgency": "high", "has_attached_doc": False, "mentions_specific_file": False,
                 "summary_zh": "冰块在游戏内未显示", "summary_en": "Ice blocks not visible in game",
                 "reasoning": ""}, "error": None},
        ],
    }
    p = tmp_path / "minisess.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p
```

- [ ] **Step 10: Commit**

```bash
git add -A tracing/ pyproject.toml tracing/requirements.txt 2>/dev/null || true
git status   # if not a git repo, skip git commit
# If a git repo:
# git commit -m "feat(tracing): scaffolding, settings, models, logging"
```

---

### Task 2: Data IO — load .traj + classified JSON, iterate trigger prompts

**Files:**
- Create: `tracing/data_io.py`
- Create: `tracing/tests/test_data_io.py`

- [ ] **Step 1: Write the failing test**

```python
import json
from pathlib import Path
from tracing.data_io import load_traj, load_classified, iter_trigger_cases
from tracing.settings import TRIGGER_INTENTS


def test_load_traj_returns_messages(mini_traj_path: Path):
    t = load_traj(mini_traj_path)
    assert t["session_metadata"]["session_id"] == "minisess"
    assert len(t["messages"]) == 4


def test_load_classified_returns_prompts(mini_classified_path: Path):
    c = load_classified(mini_classified_path)
    assert c["prompt_count"] == 2 and len(c["prompts"]) == 2


def test_iter_trigger_cases_yields_only_triggers(mini_traj_path: Path, mini_classified_path: Path):
    cases = list(iter_trigger_cases(
        dataset="traj-data-new", project="wzp",
        traj_path=mini_traj_path, classified_path=mini_classified_path))
    assert len(cases) == 1
    c = cases[0]
    assert c.session_id == "minisess"
    assert c.turn_id == 2
    assert c.complaint_raw == "游戏内没有看到冰块"
    assert c.classification["intent_primary"] == "bug_report"
```

- [ ] **Step 2: Run test, expect ImportError**

```bash
.venv/bin/pytest tracing/tests/test_data_io.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `tracing/data_io.py`**

```python
"""Load v2 .traj and classified prompt JSON; emit one TraceCase per trigger prompt."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Iterator

from tracing.models import TraceCase
from tracing.settings import TRIGGER_INTENTS


def load_traj(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_classified(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _user_turn_index(traj: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Map turn_id -> the user message dict for that turn."""
    return {m["turn_id"]: m for m in traj.get("messages", [])
            if m.get("role") == "user"}


def iter_trigger_cases(
    dataset: str, project: str, traj_path: Path, classified_path: Path,
) -> Iterator[TraceCase]:
    """Yield one TraceCase per classified prompt that matches a trigger intent.

    Matching: classified prompts are stored in original ordering. Pair them with user
    turns by index — the i-th user turn corresponds to prompts[i] (this matches how
    extraction/extract.py split user prompts on "\\n\\n---\\n\\n").
    """
    traj = load_traj(traj_path)
    cls  = load_classified(classified_path)
    user_turns = sorted([m for m in traj["messages"] if m.get("role") == "user"],
                        key=lambda m: m["turn_id"])

    for i, prompt in enumerate(cls["prompts"]):
        if prompt.get("error") is not None:
            continue
        clf = prompt.get("classification") or {}
        is_trigger = (
            clf.get("intent_primary") in TRIGGER_INTENTS
            or clf.get("is_correction_of_ai_work") is True
        )
        if not is_trigger:
            continue
        if i >= len(user_turns):
            continue   # mismatch — silently skip; warn upstream if needed
        turn = user_turns[i]
        yield TraceCase(
            dataset=dataset, project=project,
            session_id=cls["session_id"],
            turn_id=turn["turn_id"],
            complaint_raw=turn["content"],
            complaint_index_in_classified=i,
            classification=clf,
        )
```

- [ ] **Step 4: Run test, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_data_io.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add -A tracing/data_io.py tracing/tests/test_data_io.py
git commit -m "feat(tracing): load .traj + classified JSON, iter trigger cases" || true
```

---

### Task 3: LLM client — Protocol + DashScope impl + Fake impl

**Files:**
- Create: `tracing/llm.py`
- Create: `tracing/tests/test_llm.py`

- [ ] **Step 1: Write the failing test**

```python
import asyncio
import pytest
from tracing.llm import FakeLLMClient, LLMResponse


@pytest.mark.asyncio
async def test_fake_returns_canned_json():
    client = FakeLLMClient(canned={
        ("qwen-flash", "ENT"): LLMResponse(content='{"k":"v"}', input_tokens=10, output_tokens=2),
    })
    r = await client.chat_json(model="qwen-flash", system="sys", user="ENT please")
    assert r.content == '{"k":"v"}'
    assert client.call_count == 1


@pytest.mark.asyncio
async def test_fake_default_response_when_no_match():
    client = FakeLLMClient(canned={}, default=LLMResponse(content="{}", input_tokens=0, output_tokens=0))
    r = await client.chat_json(model="qwen-flash", system="x", user="y")
    assert r.content == "{}"


@pytest.mark.asyncio
async def test_fake_raises_when_no_match_and_no_default():
    client = FakeLLMClient(canned={})
    with pytest.raises(KeyError):
        await client.chat_json(model="qwen-flash", system="x", user="y")
```

- [ ] **Step 2: Run, expect FAIL**

```bash
.venv/bin/pytest tracing/tests/test_llm.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `tracing/llm.py`**

```python
"""LLM client abstraction. Real impl uses DashScope OpenAI-compatible endpoint;
Fake impl is keyed on (model, substring) for deterministic tests."""
from __future__ import annotations
import asyncio
import os
from dataclasses import dataclass
from typing import Optional, Protocol

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

from tracing.settings import DASHSCOPE_BASE_URL, PER_CALL_TIMEOUT_S, MAX_RETRIES


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int


class LLMClient(Protocol):
    async def chat_json(self, *, model: str, system: str, user: str,
                        temperature: float = 0.1) -> LLMResponse: ...


class DashScopeClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not key:
            raise RuntimeError("DASHSCOPE_API_KEY not set")
        self._client = AsyncOpenAI(api_key=key, base_url=DASHSCOPE_BASE_URL)

    async def chat_json(self, *, model: str, system: str, user: str,
                        temperature: float = 0.1) -> LLMResponse:
        last_err: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES
            try:
                resp = await self._client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user",   "content": user}],
                    temperature=temperature, top_p=0.9,
                    timeout=PER_CALL_TIMEOUT_S,
                    response_format={"type": "json_object"},
                    extra_body={"enable_thinking": False},
                )
                u = resp.usage
                return LLMResponse(
                    content=resp.choices[0].message.content or "",
                    input_tokens=getattr(u, "prompt_tokens", 0),
                    output_tokens=getattr(u, "completion_tokens", 0),
                )
            except (RateLimitError, APITimeoutError, APIError) as e:
                last_err = e
                if attempt > MAX_RETRIES:
                    raise
                await asyncio.sleep(min(2 ** attempt, 20))
        assert last_err is not None
        raise last_err


class FakeLLMClient:
    """Deterministic LLM stand-in for tests. Match by (model, substring of user prompt)."""
    def __init__(self, canned: dict[tuple[str, str], LLMResponse],
                 default: Optional[LLMResponse] = None) -> None:
        self._canned = canned
        self._default = default
        self.call_count = 0
        self.calls: list[dict] = []

    async def chat_json(self, *, model: str, system: str, user: str,
                        temperature: float = 0.1) -> LLMResponse:
        self.call_count += 1
        self.calls.append({"model": model, "system": system, "user": user})
        for (m, needle), resp in self._canned.items():
            if m == model and needle in user:
                return resp
        if self._default is not None:
            return self._default
        raise KeyError(f"FakeLLMClient: no match for model={model}, needle in user prompt")
```

- [ ] **Step 4: Configure pytest-asyncio. Edit `tracing/tests/conftest.py` — add at the top:**

```python
import pytest_asyncio  # noqa: F401
```

And create `pytest.ini` at repo root with:

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 5: Run, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_llm.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add -A tracing/llm.py tracing/tests/test_llm.py tracing/tests/conftest.py pytest.ini
git commit -m "feat(tracing): LLM client Protocol + DashScope + Fake" || true
```

---

## Phase B · Caches (deterministic + LLM)

### Task 4: Step-summary cache — deterministic part (symbols + prior_thought)

**Files:**
- Create: `tracing/step_summary.py`
- Create: `tracing/tests/test_step_summary.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import json
from tracing.data_io import load_traj
from tracing.step_summary import (
    iter_action_steps_with_prior_thought,
    parse_symbol_diff,
    deterministic_summary_record,
)


def test_parse_symbol_diff_introduces_and_preserves():
    res = parse_symbol_diff(
        old_string="frozenCells = { {4,4} }",
        new_string="frozenCells = { {4,4}, {3,2} }",
    )
    assert "frozenCells" in res["preserves"]
    assert res["introduces"] == [] and res["removes"] == []


def test_parse_symbol_diff_rename():
    res = parse_symbol_diff(
        old_string="frozenCells = { {4,4} }",
        new_string="icePositions = { {4,4} }",
    )
    assert "icePositions" in res["introduces"]
    assert "frozenCells" in res["removes"]


def test_parse_symbol_diff_write_first_creation():
    res = parse_symbol_diff(old_string=None,
                            new_string="local M = {}\nM.icePositions = {}")
    assert "icePositions" in res["introduces"]
    assert res["removes"] == []
    assert res["preserves"] == []


def test_iter_action_steps_folds_prior_thought(mini_traj_path):
    traj = load_traj(mini_traj_path)
    out = list(iter_action_steps_with_prior_thought(traj))
    # mini_traj has step 10 (respond_to_user with thought) then step 11 (Edit)
    edits = [s for s in out if s["step"]["step_id"] == 11]
    assert len(edits) == 1
    assert "需要新增 4 个冰冻格" in (edits[0]["prior_thought"] or "")


def test_deterministic_summary_record_shape(mini_traj_path):
    traj = load_traj(mini_traj_path)
    enriched = list(iter_action_steps_with_prior_thought(traj))
    edit = next(e for e in enriched if e["step"]["step_id"] == 11)
    rec = deterministic_summary_record(edit)
    assert rec["step"] == 11 and rec["tool"] == "mcp__mkr__Edit"
    assert rec["file"].endswith("story-27.lua")
    assert "frozenCells" in rec["preserves_symbols"]
    assert rec["timestamp"] == "2026-04-01T00:00:10Z"
```

- [ ] **Step 2: Run, expect FAIL**

```bash
.venv/bin/pytest tracing/tests/test_step_summary.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `tracing/step_summary.py`** (deterministic functions only — LLM summary added in Task 5)

```python
"""Per-session step-summary cache. Deterministic core + LLM natural-language summary.

This module owns the *deterministic* fields. The natural-language `summary` field
is filled by `add_llm_summaries` (next task) using qwen-flash."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Iterator, Optional

from tracing.settings import ACTION_TOOLS, THINKING_TOOL


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")  # 3+ chars to skip noise like 'a','i'


def parse_symbol_diff(*, old_string: Optional[str], new_string: Optional[str]) -> dict[str, list[str]]:
    """Identifier-shaped tokens introduced / removed / preserved between two diff sides.

    For Write actions (no old_string): everything in new_string is introduces.
    """
    new = set(_IDENT.findall(new_string or ""))
    if old_string is None:
        return {"introduces": sorted(new), "removes": [], "preserves": []}
    old = set(_IDENT.findall(old_string or ""))
    return {
        "introduces": sorted(new - old),
        "removes":    sorted(old - new),
        "preserves":  sorted(new & old),
    }


def iter_action_steps_with_prior_thought(traj: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Walk all agent steps in chronological order. Filter to ACTION_TOOLS.
    Fold the immediately-preceding respond_to_user.thought into prior_thought."""
    last_thought: Optional[str] = None
    for msg in traj.get("messages", []):
        if "agent_run_id" not in msg:
            continue
        for step in msg.get("steps", []):
            tool = step["action"]["tool_name"]
            if tool == THINKING_TOOL:
                t = step.get("thought") or step.get("thinking") or ""
                if t:
                    last_thought = str(t).strip()
                continue
            if tool not in ACTION_TOOLS:
                continue
            yield {"step": step, "turn": msg["turn_id"], "prior_thought": last_thought}
            last_thought = None  # consumed by the next action


def _short_obs(text: str, n: int = 220) -> str:
    if not text:
        return ""
    s = text.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def deterministic_summary_record(enriched: dict[str, Any]) -> dict[str, Any]:
    step = enriched["step"]
    args = step["action"].get("args") or {}
    file_path = args.get("file_path")
    diff = parse_symbol_diff(
        old_string=args.get("old_string"),
        new_string=args.get("new_string") if step["action"]["tool_name"] != "mcp__mkr__Read" else None,
    )
    obs_text = (step.get("observation") or {}).get("text") or ""
    return {
        "step": step["step_id"],
        "turn": enriched["turn"],
        "tool": step["action"]["tool_name"],
        "file": file_path,
        "summary": "",  # filled by LLM in next task
        "introduces_symbols": diff["introduces"],
        "removes_symbols":    diff["removes"],
        "preserves_symbols":  diff["preserves"],
        "prior_thought":      enriched["prior_thought"],
        "obs_excerpt":        _short_obs(obs_text),
        "timestamp":          step.get("timestamp", ""),
    }


def write_summary_jsonl(records: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(out_path)
```

- [ ] **Step 4: Run test, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_step_summary.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add -A tracing/step_summary.py tracing/tests/test_step_summary.py
git commit -m "feat(tracing): step-summary deterministic core" || true
```

---

### Task 5: Step-summary cache — LLM natural-language `summary` field

**Files:**
- Modify: `tracing/step_summary.py` (add `add_llm_summaries`)
- Modify: `tracing/tests/test_step_summary.py` (add async test)
- Create: `tracing/prompts.py` (start the file; one prompt added here, more added per stage later)

- [ ] **Step 1: Add the failing test**

Append to `tracing/tests/test_step_summary.py`:

```python
import pytest
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.step_summary import add_llm_summaries


@pytest.mark.asyncio
async def test_add_llm_summaries_fills_summary_field(mini_traj_path):
    from tracing.data_io import load_traj
    traj = load_traj(mini_traj_path)
    enriched = list(iter_action_steps_with_prior_thought(traj))
    records = [deterministic_summary_record(e) for e in enriched]

    fake = FakeLLMClient(canned={}, default=LLMResponse(
        content='[{"step":11,"summary":"Edit story-27 frozenCells +4"}]',
        input_tokens=100, output_tokens=20))
    out = await add_llm_summaries(records, llm=fake, model="qwen-flash", batch_size=50)
    by_id = {r["step"]: r for r in out}
    assert by_id[11]["summary"] == "Edit story-27 frozenCells +4"
```

- [ ] **Step 2: Create `tracing/prompts.py` with the step-summary prompt**

```python
"""All LLM prompts. Each prompt is a function returning (system, user) strings.

Prompt text mirrors spec docs/superpowers/specs/2026-04-21-traj-root-cause-tracer-design.md §11.
When updating a prompt, update both the spec and this module."""
from __future__ import annotations
import json
from typing import Any


def step_summary_batch(records: list[dict[str, Any]]) -> tuple[str, str]:
    """qwen-flash: enrich a batch of step records with a natural-language `summary`.
    The deterministic fields are passed in for context but only `summary` is generated."""
    system = (
        "You enrich agent trajectory steps with concise natural-language summaries. "
        "For each input step, produce a single 'summary' field (≤ 200 chars) that names "
        "the file touched, the operation, and the key identifier(s) involved. Do NOT "
        "invent fields. Output JSON only."
    )
    inputs = [
        {k: r[k] for k in ("step", "tool", "file", "introduces_symbols",
                           "removes_symbols", "preserves_symbols", "obs_excerpt")}
        for r in records
    ]
    user = (
        "Input steps:\n"
        f"{json.dumps(inputs, ensure_ascii=False)}\n\n"
        "Output JSON array, one entry per input step, in the SAME order:\n"
        '[{"step": <int>, "summary": "<≤200 chars>"}, ...]'
    )
    return system, user
```

- [ ] **Step 3: Add `add_llm_summaries` to `tracing/step_summary.py`** (append):

```python
import json as _json  # avoid clobbering top-level json import in this file

from tracing.llm import LLMClient
from tracing.prompts import step_summary_batch


async def add_llm_summaries(records: list[dict[str, Any]], *, llm: LLMClient,
                            model: str, batch_size: int = 50) -> list[dict[str, Any]]:
    """Mutates and returns records with `summary` filled in. Batched."""
    by_id = {r["step"]: r for r in records}
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        system, user = step_summary_batch(batch)
        resp = await llm.chat_json(model=model, system=system, user=user)
        try:
            parsed = _json.loads(resp.content)
        except _json.JSONDecodeError:
            # Tolerate code fences / leading prose
            txt = resp.content.strip().lstrip("`").rstrip("`")
            start = txt.find("[")
            end = txt.rfind("]")
            parsed = _json.loads(txt[start : end + 1])
        for entry in parsed:
            sid = int(entry.get("step", -1))
            if sid in by_id:
                by_id[sid]["summary"] = str(entry.get("summary", ""))[:400]
    return records
```

- [ ] **Step 4: Run test, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_step_summary.py -v
```

Expected: 6 passed (5 from before + new async one).

- [ ] **Step 5: Commit**

```bash
git add -A tracing/step_summary.py tracing/prompts.py tracing/tests/test_step_summary.py
git commit -m "feat(tracing): LLM-generated natural-language summary field" || true
```

---

### Task 6: Glossary cache builder

**Files:**
- Create: `tracing/glossary.py`
- Create: `tracing/tests/test_glossary.py`
- Modify: `tracing/prompts.py` (add `glossary_build`)

- [ ] **Step 1: Failing test**

```python
import pytest
from tracing.data_io import load_traj
from tracing.glossary import collect_glossary_inputs, build_glossary
from tracing.llm import FakeLLMClient, LLMResponse


def test_collect_glossary_inputs_gathers_files_and_names(mini_traj_path):
    traj = load_traj(mini_traj_path)
    inp = collect_glossary_inputs(traj)
    assert any("story-27.lua" in p for p in inp["file_paths_touched"])
    assert isinstance(inp["observed_names"], list)


@pytest.mark.asyncio
async def test_build_glossary_returns_typed_entries(mini_traj_path):
    traj = load_traj(mini_traj_path)
    fake = FakeLLMClient(canned={}, default=LLMResponse(
        content=('[{"name":"冰火花园","kind":"level","canonical":"story-27.lua",'
                 '"evidence":"file_paths_touched"}]'),
        input_tokens=80, output_tokens=20))
    entries = await build_glossary(traj, llm=fake, model="qwen-flash")
    assert len(entries) == 1
    assert entries[0]["name"] == "冰火花园" and entries[0]["kind"] == "level"
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Add `glossary_build` to `tracing/prompts.py`**

```python
def glossary_build(file_paths: list[str], observed_names: list[str],
                   grep_patterns: list[str], session_meta: dict[str, Any]) -> tuple[str, str]:
    system = (
        "You build a glossary of natural-language names found in an agent's "
        "trajectory and their canonical code identifiers. "
        "Every output 'name' must appear verbatim in observed_names OR grep_patterns. "
        "Every 'canonical' must be a path from file_paths_touched OR a sub-symbol of one. "
        "Each entry MUST have a 'kind' from: level, npc, ui_element, document, system, feature, unknown. "
        "Output JSON ARRAY only."
    )
    inputs = {
        "file_paths_touched": file_paths[:200],
        "observed_names":     observed_names[:100],
        "grep_patterns_seen": grep_patterns[:100],
        "session_meta":       session_meta,
    }
    user = (
        "Inputs:\n"
        f"{json.dumps(inputs, ensure_ascii=False)}\n\n"
        "Examples of good output (DO NOT include in your output):\n"
        '[{"name":"冰火花园","kind":"level","canonical":"scripts/config/storyline-levels/story-27.lua","evidence":"observed_names"},\n'
        ' {"name":"debug 按钮","kind":"ui_element","canonical":"scripts/ui/debug-button.lua","evidence":"file_paths_touched"}]\n\n'
        "Now produce the glossary for the inputs above. Output JSON array only."
    )
    return system, user
```

- [ ] **Step 4: Implement `tracing/glossary.py`**

```python
"""Per-session glossary builder. One LLM call per session, cached."""
from __future__ import annotations
import json as _json
import re
from pathlib import Path
from typing import Any

from tracing.llm import LLMClient
from tracing.prompts import glossary_build
from tracing.settings import ACTION_TOOLS

_NAME_REGEXES = [
    re.compile(r'\btitle\s*=\s*"([^"]+)"'),
    re.compile(r'\bname\s*=\s*"([^"]+)"'),
    re.compile(r'\blevelId\s*=\s*"([^"]+)"'),
    re.compile(r'\bnodeId\s*=\s*"([^"]+)"'),
    re.compile(r'\bspeaker\s*=\s*"([^"]+)"'),
]


def collect_glossary_inputs(traj: dict[str, Any]) -> dict[str, Any]:
    file_paths: set[str] = set()
    grep_patterns: set[str] = set()
    observed: set[str] = set()
    for msg in traj.get("messages", []):
        if "agent_run_id" not in msg:
            continue
        for step in msg.get("steps", []):
            tool = step["action"]["tool_name"]
            if tool not in ACTION_TOOLS:
                continue
            args = step["action"].get("args") or {}
            if isinstance(args.get("file_path"), str):
                file_paths.add(args["file_path"])
            if tool == "Grep" and isinstance(args.get("pattern"), str):
                grep_patterns.add(args["pattern"])
            obs = (step.get("observation") or {}).get("text") or ""
            for rx in _NAME_REGEXES:
                for m in rx.findall(obs):
                    observed.add(m)
    return {
        "file_paths_touched": sorted(file_paths),
        "grep_patterns_seen": sorted(grep_patterns),
        "observed_names":     sorted(observed),
        "session_meta":       traj.get("session_metadata", {}),
    }


async def build_glossary(traj: dict[str, Any], *, llm: LLMClient, model: str) -> list[dict[str, Any]]:
    inp = collect_glossary_inputs(traj)
    system, user = glossary_build(
        file_paths=inp["file_paths_touched"],
        observed_names=inp["observed_names"],
        grep_patterns=inp["grep_patterns_seen"],
        session_meta=inp["session_meta"],
    )
    resp = await llm.chat_json(model=model, system=system, user=user)
    txt = resp.content.strip()
    start = txt.find("[")
    end = txt.rfind("]")
    return _json.loads(txt[start : end + 1])


def write_glossary(entries: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(_json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out_path)


def read_cached_glossary(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        return _json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
```

- [ ] **Step 5: Run, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_glossary.py -v
```

- [ ] **Step 6: Commit**

```bash
git add -A tracing/glossary.py tracing/tests/test_glossary.py tracing/prompts.py
git commit -m "feat(tracing): per-session glossary cache" || true
```

---

### Task 7: Global step-summary corpus builder

**Files:**
- Create: `tracing/corpus.py`
- Create: `tracing/tests/test_corpus.py`

- [ ] **Step 1: Failing test**

```python
import json
import pytest
from pathlib import Path
from tracing.corpus import build_global_corpus, filter_corpus_by_symbol
from tracing.llm import FakeLLMClient, LLMResponse


@pytest.mark.asyncio
async def test_build_global_corpus_concatenates_per_session_summaries(
    mini_traj_path: Path, tmp_path: Path):
    # Stage two .traj files and call the builder
    traj_dir = tmp_path / "ds" / "wzp"
    traj_dir.mkdir(parents=True)
    p1 = traj_dir / "minisess.traj"
    p1.write_text(mini_traj_path.read_text(encoding="utf-8"), encoding="utf-8")

    cache_dir = tmp_path / "cache"
    fake = FakeLLMClient(canned={}, default=LLMResponse(
        content='[{"step":11,"summary":"edit"},{"step":20,"summary":"edit"}]',
        input_tokens=10, output_tokens=10))
    out_path = await build_global_corpus(
        dataset_root=tmp_path, dataset="ds", project="wzp",
        cache_root=cache_dir, llm=fake, model="qwen-flash")
    text = out_path.read_text(encoding="utf-8").strip()
    lines = [json.loads(line) for line in text.splitlines()]
    assert all("session" in r for r in lines)
    sessions = {r["session"] for r in lines}
    assert sessions == {"minisess"}


def test_filter_corpus_by_symbol_returns_matches(tmp_path):
    corpus = tmp_path / "g.jsonl"
    corpus.write_text(
        '{"session":"a","step":1,"file":"foo.lua","preserves_symbols":["frozenCells"],"introduces_symbols":[],"removes_symbols":[],"timestamp":"2026-01-01T00:00:00Z"}\n'
        '{"session":"b","step":2,"file":"bar.lua","preserves_symbols":["other"],"introduces_symbols":[],"removes_symbols":[],"timestamp":"2026-01-02T00:00:00Z"}\n',
        encoding="utf-8")
    hits = filter_corpus_by_symbol(corpus, file_path="foo.lua", symbol="frozenCells")
    assert len(hits) == 1 and hits[0]["session"] == "a"
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Implement `tracing/corpus.py`**

```python
"""Cross-session step-summary corpus. Built once per (dataset, project)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from tracing.data_io import load_traj
from tracing.llm import LLMClient
from tracing.step_summary import (
    iter_action_steps_with_prior_thought,
    deterministic_summary_record,
    add_llm_summaries,
)


async def build_global_corpus(*, dataset_root: Path, dataset: str, project: str,
                              cache_root: Path, llm: LLMClient, model: str,
                              rebuild: bool = False) -> Path:
    out_dir = cache_root / dataset / project / "step-summary"
    out_path = out_dir / "_global.jsonl"
    if out_path.exists() and not rebuild:
        return out_path
    out_dir.mkdir(parents=True, exist_ok=True)
    project_dir = dataset_root / project
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")

    with tmp.open("w", encoding="utf-8") as f:
        for traj_path in sorted(project_dir.glob("*.traj")):
            traj = load_traj(traj_path)
            sid = traj["session_metadata"]["session_id"]
            short_sid = sid.split("-")[0] if "-" in sid else sid
            enriched = list(iter_action_steps_with_prior_thought(traj))
            records = [deterministic_summary_record(e) for e in enriched]
            records = await add_llm_summaries(records, llm=llm, model=model)
            for r in records:
                r2 = dict(r); r2["session"] = short_sid
                f.write(json.dumps(r2, ensure_ascii=False) + "\n")
    tmp.replace(out_path)
    return out_path


def filter_corpus_by_symbol(corpus_path: Path, *, file_path: str | None,
                            symbol: str | None) -> list[dict[str, Any]]:
    """Cheap deterministic prefilter: lines whose file or any *_symbols list
    mentions the file or symbol of interest. Used by stage 6 before LLM scoring."""
    out: list[dict[str, Any]] = []
    if not corpus_path.exists():
        return out
    f_needle = (file_path or "").rsplit("/", 1)[-1] if file_path else None
    with corpus_path.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            file_match = bool(f_needle) and bool(rec.get("file")) and f_needle in rec["file"]
            sym_match = False
            if symbol:
                for k in ("introduces_symbols", "removes_symbols", "preserves_symbols"):
                    if symbol in (rec.get(k) or []):
                        sym_match = True; break
            if file_match or sym_match:
                out.append(rec)
    out.sort(key=lambda r: r.get("timestamp", ""))
    return out
```

- [ ] **Step 4: Run, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_corpus.py -v
```

- [ ] **Step 5: Commit**

```bash
git add -A tracing/corpus.py tracing/tests/test_corpus.py
git commit -m "feat(tracing): cross-session step-summary corpus" || true
```

---

## Phase C · Pipeline stages

### Task 8: Stage 2 — context loader (deterministic)

**Files:**
- Create: `tracing/stage2_context.py`
- Create: `tracing/tests/test_stage2_context.py`

- [ ] **Step 1: Failing test**

```python
from pathlib import Path
from tracing.data_io import load_traj, load_classified
from tracing.stage2_context import load_case_context


def test_load_case_context_separates_prior_and_posterior(mini_traj_path, mini_classified_path):
    traj = load_traj(mini_traj_path)
    cls  = load_classified(mini_classified_path)
    ctx = load_case_context(traj=traj, classified=cls,
                            complaint_index=1, complaint_turn_id=2)
    # prior_steps must be only step 10 + 11 (turn 1)
    assert {s["step_id"] for s in ctx["prior_steps"]} == {11}    # step 10 was respond_to_user, filtered
    # posterior_steps must be step 20 (turn 2)
    assert {s["step_id"] for s in ctx["posterior_steps"]} == {20}
    # complaint loaded from classified
    assert ctx["complaint"]["raw"] == "游戏内没有看到冰块"
    assert ctx["complaint"]["classification"]["intent_primary"] == "bug_report"
    # last agent response captured
    assert ctx["agent_last_response"] is not None
    assert "需要新增 4 个冰冻格" in ctx["agent_last_response"]
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Implement `tracing/stage2_context.py`**

```python
"""Stage 2 — deterministic context loader. No LLM. Builds the bundle
that stages 3-5 will consume."""
from __future__ import annotations
from typing import Any

from tracing.settings import ACTION_TOOLS, THINKING_TOOL, POSTERIOR_WINDOW


def _all_steps_with_turn(traj: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    """Yield (turn_id, step) tuples preserving chronological order."""
    out = []
    for msg in traj.get("messages", []):
        if "agent_run_id" not in msg:
            continue
        for s in msg.get("steps", []):
            out.append((msg["turn_id"], s))
    return out


def load_case_context(*, traj: dict[str, Any], classified: dict[str, Any],
                      complaint_index: int, complaint_turn_id: int) -> dict[str, Any]:
    user_msgs = [m for m in traj.get("messages", []) if m.get("role") == "user"]
    user_by_turn = {m["turn_id"]: m for m in user_msgs}
    prior_user_turns = [m for m in user_msgs
                        if m["turn_id"] < complaint_turn_id][-3:]

    all_steps = _all_steps_with_turn(traj)

    prior_action_steps = [s for (t, s) in all_steps
                          if t < complaint_turn_id and s["action"]["tool_name"] in ACTION_TOOLS]
    posterior_action_steps = [s for (t, s) in all_steps
                              if t > complaint_turn_id and s["action"]["tool_name"] in ACTION_TOOLS][:POSTERIOR_WINDOW]

    # The agent's last respond_to_user message before the complaint — what user reacted to.
    agent_last_response: str | None = None
    for (t, s) in reversed(all_steps):
        if t < complaint_turn_id and s["action"]["tool_name"] == THINKING_TOOL:
            txt = s.get("thought") or s.get("thinking") or ""
            if txt:
                agent_last_response = str(txt).strip()
                break

    complaint = classified["prompts"][complaint_index]

    return {
        "complaint": complaint,
        "complaint_turn": user_by_turn.get(complaint_turn_id),
        "prior_user_turns": prior_user_turns,
        "agent_last_response": agent_last_response,
        "prior_steps": prior_action_steps,
        "posterior_steps": posterior_action_steps,
        "session_meta": traj.get("session_metadata", {}),
    }
```

- [ ] **Step 4: Run, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add -A tracing/stage2_context.py tracing/tests/test_stage2_context.py
git commit -m "feat(tracing): stage 2 context loader" || true
```

---

### Task 9: Stage 3 — entity resolution (qwen-flash)

**Files:**
- Create: `tracing/stage3_entities.py`
- Create: `tracing/tests/test_stage3_entities.py`
- Modify: `tracing/prompts.py` (add `entity_resolution`)

- [ ] **Step 1: Failing test**

```python
import pytest
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.stage3_entities import resolve_entities


@pytest.mark.asyncio
async def test_resolve_entities_returns_typed_lists():
    fake = FakeLLMClient(canned={}, default=LLMResponse(content=(
        '{"artifacts":[{"path":"story-27.lua","source":"glossary","confidence":"high"}],'
        '"symbols":[{"name":"frozenCells","source":"observed","confidence":"high"},'
        '{"name":"icePositions","source":"hypothesis","confidence":"medium"}],'
        '"surface":"in-game runtime",'
        '"user_intent_restated":"ice obstacles missing",'
        '"insufficient_evidence":false}'
    ), input_tokens=200, output_tokens=80))

    result = await resolve_entities(
        complaint_raw="冰块没看到",
        prior_user_turns=[],
        agent_last_response="已新增 4 冰冻格",
        glossary=[{"name":"冰火花园","kind":"level","canonical":"story-27.lua","evidence":"observed_names"}],
        classification={"intent_primary":"bug_report","is_correction_of_ai_work":True,
                        "target_artifact":"game_logic","summary_zh":"冰块未显示"},
        llm=fake, model="qwen-flash")

    assert result["insufficient_evidence"] is False
    assert result["artifacts"][0]["path"] == "story-27.lua"
    assert any(s["name"] == "icePositions" for s in result["symbols"])
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Add prompt to `tracing/prompts.py`**

```python
def entity_resolution(complaint_raw: str, prior_user_turns: list[dict[str, Any]],
                      agent_last_response: str | None,
                      glossary: list[dict[str, Any]],
                      classification: dict[str, Any]) -> tuple[str, str]:
    system = (
        "You resolve a user complaint into the artifacts/symbols/surface a forensic "
        "tracer should search for. Distinguish strictly: USER text vs CLASSIFIER hint "
        "vs AGENT response — the user is the only ground truth.\n\n"
        "Output rules:\n"
        " - artifacts[].path MUST be from glossary canonicals OR a path that obviously "
        "   appears in agent_last_response. Mark source accordingly.\n"
        " - symbols MAY be HYPOTHESES (names not in evidence) — mark source=hypothesis. "
        "   This is desired, e.g. proposing 'icePositions' even when only 'frozenCells' is in evidence.\n"
        " - If you cannot identify any plausible artifact, set insufficient_evidence=true.\n"
        " - Output JSON object only, schema fixed."
    )
    user = (
        f"<COMPLAINT — verbatim user text>\n{complaint_raw}\n\n"
        f"<PRIOR USER TURNS — for anaphora only, NOT to be answered>\n"
        + "\n".join(f"[turn {t.get('turn_id')}] {t.get('content','')}" for t in prior_user_turns)
        + "\n\n"
        f"<AGENT'S LAST RESPONSE TO USER — what user is reacting to>\n"
        f"{agent_last_response or '(none)'}\n\n"
        f"<UPSTREAM CLASSIFIER OUTPUT — HINT not ground truth>\n"
        f"intent_primary: {classification.get('intent_primary')}\n"
        f"is_correction_of_ai_work: {classification.get('is_correction_of_ai_work')}\n"
        f"target_artifact: {classification.get('target_artifact')}\n"
        f"summary_zh: {classification.get('summary_zh')}\n\n"
        f"<SESSION GLOSSARY>\n{json.dumps(glossary, ensure_ascii=False)}\n\n"
        "<TASK>\nResolve and return JSON with keys: artifacts[], symbols[], surface, "
        "user_intent_restated, insufficient_evidence."
    )
    return system, user
```

- [ ] **Step 4: Implement `tracing/stage3_entities.py`**

```python
"""Stage 3 — qwen-flash entity resolution + grounding validators."""
from __future__ import annotations
import json as _json
from typing import Any

from tracing.llm import LLMClient
from tracing.prompts import entity_resolution


def _coerce_json_obj(text: str) -> dict[str, Any]:
    s = text.strip()
    if s.startswith("```"):
        s = s.lstrip("`")
        if s.lower().startswith("json"):
            s = s[4:]
        s = s.rstrip("`").strip()
    start = s.find("{"); end = s.rfind("}")
    return _json.loads(s[start : end + 1])


def _validate_artifacts(artifacts: list[dict[str, Any]],
                        glossary_paths: set[str], touched_files: set[str]) -> list[dict[str, Any]]:
    """Drop any artifact whose path is not in glossary OR touched files."""
    keep = []
    for a in artifacts:
        path = str(a.get("path", ""))
        if path in glossary_paths or path in touched_files or any(
            path in tf or tf.endswith("/" + path) for tf in touched_files
        ):
            keep.append(a)
    return keep


async def resolve_entities(*, complaint_raw: str,
                           prior_user_turns: list[dict[str, Any]],
                           agent_last_response: str | None,
                           glossary: list[dict[str, Any]],
                           classification: dict[str, Any],
                           touched_files: set[str] | None = None,
                           llm: LLMClient, model: str) -> dict[str, Any]:
    system, user = entity_resolution(
        complaint_raw=complaint_raw,
        prior_user_turns=prior_user_turns,
        agent_last_response=agent_last_response,
        glossary=glossary,
        classification=classification,
    )
    resp = await llm.chat_json(model=model, system=system, user=user)
    obj = _coerce_json_obj(resp.content)

    glossary_paths = {str(g.get("canonical", "")) for g in glossary}
    if touched_files is not None:
        obj["artifacts"] = _validate_artifacts(obj.get("artifacts", []),
                                               glossary_paths, touched_files)
    return obj
```

- [ ] **Step 5: Run, expect PASS** then commit

```bash
.venv/bin/pytest tracing/tests/test_stage3_entities.py -v
git add -A tracing/stage3_entities.py tracing/tests/test_stage3_entities.py tracing/prompts.py
git commit -m "feat(tracing): stage 3 entity resolution" || true
```

---

### Task 10: Stage 4 — candidate retrieval (qwen-flash, batched)

**Files:**
- Create: `tracing/stage4_candidates.py`
- Create: `tracing/tests/test_stage4_candidates.py`
- Modify: `tracing/prompts.py` (add `candidate_scoring`)

- [ ] **Step 1: Failing test**

```python
import pytest
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.stage4_candidates import score_and_select_candidates


@pytest.mark.asyncio
async def test_score_and_select_returns_top_k_with_threshold():
    summaries = [
        {"step": s, "tool": "Edit", "file": "f.lua",
         "summary": f"edit step {s}", "introduces_symbols": [],
         "removes_symbols": [], "preserves_symbols": ["frozenCells"],
         "prior_thought": None, "obs_excerpt": "", "timestamp": ""}
        for s in range(1, 11)
    ]
    fake = FakeLLMClient(canned={}, default=LLMResponse(
        content=("[" + ",".join(f'{{"step":{s},"score":{(s % 4)},"reason":"r"}}'
                                  for s in range(1, 11)) + "]"),
        input_tokens=300, output_tokens=80))
    entities = {"artifacts":[{"path":"f.lua","source":"glossary","confidence":"high"}],
                "symbols":[{"name":"frozenCells","source":"observed","confidence":"high"}],
                "surface":"runtime","user_intent_restated":"x","insufficient_evidence":False}

    chosen = await score_and_select_candidates(
        summaries=summaries, entities=entities, llm=fake, model="qwen-flash",
        batch_size=50, keep_threshold=2, top_k=8)
    # steps with s%4 in {2,3} pass threshold -> 1,2,3,5,6,7,9,10 score >=2
    kept_steps = {c["step"] for c in chosen}
    assert all(s % 4 in (2, 3) for s in kept_steps)
    assert len(chosen) <= 8
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Add prompt to `tracing/prompts.py`**

```python
def candidate_scoring(entities: dict[str, Any],
                      step_summaries: list[dict[str, Any]]) -> tuple[str, str]:
    system = (
        "You score agent steps for likelihood of having introduced a defect.\n"
        "Anchored 0..3 scale:\n"
        "  0 = irrelevant: does not touch the artifacts/symbols in entities.\n"
        "  1 = adjacent: touches a related file or area but not the specific artifact/symbol.\n"
        "  2 = touches: reads/edits the artifact in question or a sibling artifact.\n"
        "  3 = likely introducer: mutates the specific symbol implicated, OR introduces a "
        "      symbol the user complaint refers to, OR is the latest pre-complaint Edit/Write "
        "      to the named artifact.\n"
        "Be selective — typically ≤ 20% of steps score ≥ 2. Higher-confidence sources "
        "(source=glossary/observed) outweigh source=hypothesis when both could match. "
        "Output JSON ARRAY only."
    )
    user = (
        f"<ENTITIES>\n{json.dumps(entities, ensure_ascii=False)}\n\n"
        f"<STEP SUMMARIES — score each by step id>\n"
        + "\n".join(
            f"[step={r['step']} tool={r['tool']} file={r.get('file')}] "
            f"{r['summary']} | introduces={r['introduces_symbols']} "
            f"removes={r['removes_symbols']} preserves={r['preserves_symbols']}"
            for r in step_summaries
        )
        + "\n\n"
        '<TASK>\nOutput JSON array: [{"step":<int>,"score":0..3,"reason":"<short>"},...]'
    )
    return system, user
```

- [ ] **Step 4: Implement `tracing/stage4_candidates.py`**

```python
"""Stage 4 — batched candidate scoring + threshold + top-K selection."""
from __future__ import annotations
import json as _json
from typing import Any

from tracing.llm import LLMClient
from tracing.prompts import candidate_scoring


def _coerce_json_array(text: str) -> list[dict[str, Any]]:
    s = text.strip()
    if s.startswith("```"):
        s = s.lstrip("`")
        if s.lower().startswith("json"):
            s = s[4:]
        s = s.rstrip("`").strip()
    start = s.find("["); end = s.rfind("]")
    return _json.loads(s[start : end + 1])


async def score_and_select_candidates(
    *, summaries: list[dict[str, Any]], entities: dict[str, Any],
    llm: LLMClient, model: str,
    batch_size: int = 50, keep_threshold: int = 2, top_k: int = 8,
) -> list[dict[str, Any]]:
    """Returns selected candidate dicts: {step, score, reason} sorted by (score desc, step desc).
    Steps not in summaries are silently dropped from the LLM output."""
    valid_steps = {r["step"] for r in summaries}
    scored: dict[int, dict[str, Any]] = {}
    for i in range(0, len(summaries), batch_size):
        batch = summaries[i : i + batch_size]
        system, user = candidate_scoring(entities, batch)
        resp = await llm.chat_json(model=model, system=system, user=user)
        for entry in _coerce_json_array(resp.content):
            sid = int(entry.get("step", -1))
            if sid not in valid_steps:
                continue   # ground rejection
            sc = max(0, min(3, int(entry.get("score", 0))))
            scored[sid] = {"step": sid, "score": sc,
                           "reason": str(entry.get("reason", ""))[:200]}
    kept = [c for c in scored.values() if c["score"] >= keep_threshold]
    kept.sort(key=lambda c: (-c["score"], -c["step"]))   # higher score, then more recent
    return kept[:top_k]
```

- [ ] **Step 5: Run, expect PASS** then commit

```bash
.venv/bin/pytest tracing/tests/test_stage4_candidates.py -v
git add -A tracing/stage4_candidates.py tracing/tests/test_stage4_candidates.py tracing/prompts.py
git commit -m "feat(tracing): stage 4 batched candidate retrieval" || true
```

---

### Task 11: Stage 5 — attribution (qwen-plus-latest)

**Files:**
- Create: `tracing/stage5_attribution.py`
- Create: `tracing/tests/test_stage5_attribution.py`
- Modify: `tracing/prompts.py` (add `attribution` and `negative_findings_compute`)

- [ ] **Step 1: Failing test**

```python
import pytest
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.stage5_attribution import (
    compute_negative_findings, attribute_root_cause,
)


def test_compute_negative_findings_detects_missing_consumer_read():
    prior = [
        {"step_id":11,"action":{"tool_name":"mcp__mkr__Edit",
            "args":{"file_path":"story-27.lua","old_string":"frozenCells = {}",
                    "new_string":"frozenCells = {{1,2}}"}},
         "observation":{"text":"ok"}}
    ]
    nf = compute_negative_findings(
        prior_steps=prior,
        consumer_files_to_check=["board.lua"],
        symbols_to_grep=["icePositions"])
    assert "board.lua" in nf["no_step_read"]
    assert "icePositions" in nf["no_step_grepped"]
    assert nf["no_step_executed_runtime_test"] is True


@pytest.mark.asyncio
async def test_attribute_returns_evidence_chain_with_grounded_step_id():
    candidates = [
        {"step":11,"score":3,"reason":"mutates frozenCells",
         "detail":{"step":11,"turn":1,"tool":"mcp__mkr__Edit",
                   "file":"story-27.lua","summary":"+4 entries",
                   "introduces_symbols":[],"removes_symbols":[],
                   "preserves_symbols":["frozenCells"],"prior_thought":"需要新增","obs_excerpt":"+4 lines",
                   "timestamp":"2026-04-01T00:00:10Z"}},
    ]
    entities = {"artifacts":[{"path":"story-27.lua","source":"glossary","confidence":"high"}],
                "symbols":[{"name":"frozenCells","source":"observed","confidence":"high"}],
                "surface":"runtime","user_intent_restated":"ice missing",
                "insufficient_evidence":False}
    nf = {"no_step_read":["board.lua"],"no_step_grepped":["icePositions"],
          "no_step_searched_for_field_consumers":True,"no_step_executed_runtime_test":True}

    fake = FakeLLMClient(canned={}, default=LLMResponse(content=(
        '{"evidence_chain":{'
        '"complaint":{"ref":{"turn":2},"text":"ice missing"},'
        '"symptom":{"text":"no ice"},'
        '"broken_state":{"refs":[{"step":11}],"text":"wrong field"},'
        '"introducing":{"ref":{"step":11},"text":"appended to frozenCells"},'
        '"missing_check":{"text":"never read board.lua"}},'
        '"proximate_root":{"session":"s","step":11,"file":"story-27.lua","symbol":"frozenCells"},'
        '"genesis_check":{"needs_cross_session_trace":true,"reason":"extends pre-existing"},'
        '"failure_mode":"verification_gap_via_lexical_familiarity",'
        '"counter_pattern":"Read consumer code before mutating an existing config field.",'
        '"predicted_fix_target":[{"file":"story-27.lua","symbol":"frozenCells->icePositions"}],'
        '"attribution_confidence":"high"}'
    ), input_tokens=2000, output_tokens=400))

    result = await attribute_root_cause(
        complaint_raw="冰块没看到", complaint_turn_id=2,
        classification={"intent_primary":"bug_report","is_correction_of_ai_work":True,
                        "target_artifact":"game_logic","summary_zh":"冰块未显示"},
        project="wzp", project_name="脑力大冒险", session_id="s",
        entities=entities, candidates=candidates, negative_findings=nf,
        llm=fake, model="qwen-plus-latest")
    assert result["proximate_root"]["step"] == 11
    assert result["failure_mode"] == "verification_gap_via_lexical_familiarity"
    assert result["attribution_confidence"] == "high"
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Add `attribution` and `FAILURE_MODE_TAXONOMY` to `tracing/prompts.py`**

```python
FAILURE_MODE_TAXONOMY: dict[str, str] = {
    "verification_gap_via_lexical_familiarity":
        "agent extends an existing identifier without verifying the consumer reads that exact name "
        "(e.g. extends frozenCells without checking board.lua reads icePositions)",
    "hallucinated_symbol":
        "agent calls an API/function/key that does not exist in the codebase",
    "inherited_broken_state":
        "agent extends pre-existing wrong code without questioning it",
    "silent_acceptor_fooled_by_build":
        "agent treats green build/typecheck as proof of behaviour in a runtime that silently "
        "accepts wrong inputs (Lua tables, JS objects, env vars)",
    "premature_completion":
        "agent declares done without runtime verification when the task required it",
    "wrong_mental_model":
        "agent operates on a fundamentally wrong understanding of the system",
    "misread_spec":
        "agent misinterprets the user's instruction",
    "ambiguous_spec_picked_wrong":
        "spec was ambiguous; agent picked an interpretation the user didn't intend",
    "racy_or_order_dependent":
        "timing/order/state-ordering defect",
    "regression_from_unrelated_edit":
        "broke X while changing Y; no awareness of coupling",
    "incomplete_refactor":
        "renamed/moved partially; left stragglers",
    "other":
        "none of the above; trace queued for taxonomy review",
}


def attribution(*, complaint_raw: str, complaint_turn_id: int,
                classification: dict[str, Any], project: str, project_name: str,
                entities: dict[str, Any], candidates: list[dict[str, Any]],
                negative_findings: dict[str, Any]) -> tuple[str, str]:
    system = (
        "You are a forensic root-cause analyst for AI coding agent trajectories. "
        "Identify the agent step that introduced the defect described in the user complaint, "
        "classify the failure mode, write a counter-pattern, and predict the fix target. "
        "HARD constraints:\n"
        " 1. proximate_root.step MUST be one of the candidate step IDs below with tool ≠ respond_to_user.\n"
        " 2. Every evidence_chain.*.ref.step MUST be a candidate step ID.\n"
        " 3. failure_mode MUST be one of the taxonomy keys below.\n"
        " 4. predicted_fix_target[].file MUST be in entities.artifacts OR a candidate step's file.\n"
        " 5. counter_pattern: ≤200 chars, MUST start with an imperative verb.\n"
        " 6. evidence_chain has at most 5 named slots (complaint/symptom/broken_state/introducing/missing_check); "
        "OMIT slots that don't apply rather than padding with weak claims.\n"
        " 7. If candidates do not contain a step that plausibly introduced the defect, set "
        "    attribution_confidence='candidates_insufficient'. Do NOT pick the highest-scoring "
        "    candidate just to fill the slot.\n"
        "Output ONLY the JSON object — no prose, no fences."
    )

    cand_blocks = []
    for c in candidates:
        d = c.get("detail") or {}
        cand_blocks.append(
            f"─── step {d.get('step')} ─── (turn {d.get('turn')} · tool={d.get('tool')} · "
            f"score={c.get('score')} · reason={c.get('reason')!r})\n"
            f"prior_thought: {d.get('prior_thought') or '(none)'}\n"
            f"introduces_symbols: {d.get('introduces_symbols')}\n"
            f"removes_symbols: {d.get('removes_symbols')}\n"
            f"preserves_symbols: {d.get('preserves_symbols')}\n"
            f"file: {d.get('file')}\n"
            f"obs_excerpt: {d.get('obs_excerpt')}\n"
        )
    cand_text = "\n".join(cand_blocks) if cand_blocks else "(none)"

    taxonomy_text = "\n".join(f"  {k}: {v}" for k, v in FAILURE_MODE_TAXONOMY.items())

    user = (
        f"<COMPLAINT — verbatim user text at turn {complaint_turn_id}>\n{complaint_raw}\n\n"
        f"<UPSTREAM CLASSIFIER OUTPUT — HINT not ground truth>\n"
        f"intent_primary: {classification.get('intent_primary')}\n"
        f"is_correction_of_ai_work: {classification.get('is_correction_of_ai_work')}\n"
        f"target_artifact: {classification.get('target_artifact')}\n"
        f"summary_zh: {classification.get('summary_zh')}\n\n"
        f"<PROJECT META>\nproject: {project}\nproject_name: {project_name}\nruntime: lua\n\n"
        f"<RESOLVED ENTITIES>\n{json.dumps(entities, ensure_ascii=False)}\n\n"
        f"<CANDIDATE STEPS — these are the ONLY steps you may cite>\n{cand_text}\n\n"
        f"<NEGATIVE FINDINGS — facts about what was NOT done before the complaint>\n"
        f"{json.dumps(negative_findings, ensure_ascii=False)}\n\n"
        f"<FAILURE-MODE TAXONOMY — closed vocabulary, pick exactly one>\n{taxonomy_text}\n\n"
        "<TASK>\nReturn JSON only with keys: evidence_chain, proximate_root, genesis_check, "
        "failure_mode, counter_pattern, predicted_fix_target, attribution_confidence."
    )
    return system, user
```

- [ ] **Step 4: Implement `tracing/stage5_attribution.py`**

```python
"""Stage 5 — qwen-plus attribution. Constructs negative findings deterministically,
calls the LLM once, validates step-ID grounding + taxonomy + fix target file."""
from __future__ import annotations
import json as _json
from typing import Any

from tracing.llm import LLMClient
from tracing.prompts import attribution, FAILURE_MODE_TAXONOMY


def compute_negative_findings(*, prior_steps: list[dict[str, Any]],
                              consumer_files_to_check: list[str],
                              symbols_to_grep: list[str]) -> dict[str, Any]:
    files_read = set()
    grep_patterns = set()
    ran_runtime_test = False
    for s in prior_steps:
        tool = s["action"]["tool_name"]
        args = s["action"].get("args") or {}
        if tool in ("mcp__mkr__Read", "mcp__mkr__Edit", "mcp__mkr__Write") and isinstance(args.get("file_path"), str):
            files_read.add(args["file_path"].rsplit("/", 1)[-1])
        if tool == "Grep" and isinstance(args.get("pattern"), str):
            grep_patterns.add(args["pattern"])
        if tool in ("mcp__sce-urhox__build", "Task"):
            pass   # build is not a runtime test
        if tool == "mcp__mkr__Bash":
            ran_runtime_test = True
    no_read = [f for f in consumer_files_to_check if f.rsplit("/", 1)[-1] not in files_read]
    no_grep = [sym for sym in symbols_to_grep if not any(sym in p for p in grep_patterns)]
    return {
        "no_step_read": no_read,
        "no_step_grepped": no_grep,
        "no_step_searched_for_field_consumers": bool(no_read),
        "no_step_executed_runtime_test": not ran_runtime_test,
    }


def _coerce_obj(text: str) -> dict[str, Any]:
    s = text.strip()
    if s.startswith("```"):
        s = s.lstrip("`")
        if s.lower().startswith("json"):
            s = s[4:]
        s = s.rstrip("`").strip()
    start = s.find("{"); end = s.rfind("}")
    return _json.loads(s[start : end + 1])


def _validate(result: dict[str, Any], candidates: list[dict[str, Any]],
              entities: dict[str, Any]) -> list[str]:
    """Return list of violation messages; empty list = clean."""
    cand_steps = {c["step"] for c in candidates}
    artifact_paths = {a.get("path") for a in entities.get("artifacts", [])}
    cand_files = {(c.get("detail") or {}).get("file") for c in candidates}
    violations: list[str] = []

    pr = result.get("proximate_root", {})
    if pr.get("step") not in cand_steps:
        violations.append(f"proximate_root.step {pr.get('step')} not in candidates")

    chain = result.get("evidence_chain", {}) or {}
    for slot_name, slot in chain.items():
        if not isinstance(slot, dict):
            continue
        ref = slot.get("ref") or {}
        if "step" in ref and ref["step"] not in cand_steps:
            violations.append(f"evidence_chain.{slot_name}.ref.step not in candidates")
        for r in (slot.get("refs") or []):
            if isinstance(r, dict) and "step" in r and r["step"] not in cand_steps:
                violations.append(f"evidence_chain.{slot_name}.refs.step not in candidates")

    fm = result.get("failure_mode")
    if fm not in FAILURE_MODE_TAXONOMY:
        violations.append(f"failure_mode '{fm}' not in taxonomy")

    for ft in (result.get("predicted_fix_target") or []):
        f = ft.get("file") if isinstance(ft, dict) else None
        if f and f not in artifact_paths and f not in cand_files:
            violations.append(f"predicted_fix_target.file '{f}' not in artifacts or candidate files")

    cp = result.get("counter_pattern") or ""
    if not cp or len(cp) > 200:
        violations.append("counter_pattern missing or > 200 chars")

    return violations


async def attribute_root_cause(*, complaint_raw: str, complaint_turn_id: int,
                               classification: dict[str, Any],
                               project: str, project_name: str, session_id: str,
                               entities: dict[str, Any],
                               candidates: list[dict[str, Any]],
                               negative_findings: dict[str, Any],
                               llm: LLMClient, model: str,
                               max_retries: int = 1) -> dict[str, Any]:
    system, user = attribution(
        complaint_raw=complaint_raw, complaint_turn_id=complaint_turn_id,
        classification=classification, project=project, project_name=project_name,
        entities=entities, candidates=candidates, negative_findings=negative_findings,
    )
    last_violations: list[str] = []
    for attempt in range(max_retries + 1):
        resp = await llm.chat_json(model=model, system=system, user=user)
        result = _coerce_obj(resp.content)
        violations = _validate(result, candidates, entities)
        if not violations:
            return result
        last_violations = violations
        # one retry with explicit reminder
        user = (user + "\n\n<RETRY — your previous output had violations>\n"
                + "\n".join(f"- {v}" for v in violations) + "\nFix and re-emit JSON.")
    # Degrade gracefully: mark low confidence and pass through (caller routes to _review/)
    result["attribution_confidence"] = "low"
    result["_violations"] = last_violations
    return result
```

- [ ] **Step 5: Run, expect PASS** then commit

```bash
.venv/bin/pytest tracing/tests/test_stage5_attribution.py -v
git add -A tracing/stage5_attribution.py tracing/tests/test_stage5_attribution.py tracing/prompts.py
git commit -m "feat(tracing): stage 5 attribution with grounding validators" || true
```

---

### Task 12: Stage 6 — genesis trace (deterministic gate + qwen-flash + qwen-plus)

**Files:**
- Create: `tracing/stage6_genesis.py`
- Create: `tracing/tests/test_stage6_genesis.py`
- Modify: `tracing/prompts.py` (add `genesis_score` and `genesis_confirm`)

- [ ] **Step 1: Failing test**

```python
import pytest
from pathlib import Path
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.stage6_genesis import (
    pre_state_contains_symbol,
    select_genesis_candidate,
    confirm_genesis,
)
from tracing.models import GenesisResult


def test_pre_state_contains_symbol_via_earliest_read(tmp_path):
    # Build a fake prior_steps list: a Read of file f returns text containing the symbol
    prior_steps = [
        {"step_id":5,"action":{"tool_name":"mcp__mkr__Read","args":{"file_path":"/x/foo.lua"}},
         "observation":{"text":"frozenCells = { {1,1} }"}},
        {"step_id":6,"action":{"tool_name":"mcp__mkr__Edit","args":{"file_path":"/x/foo.lua",
            "old_string":"frozenCells = { {1,1} }", "new_string":"frozenCells = { {1,1},{2,2} }"}},
         "observation":{"text":"ok"}},
    ]
    has = pre_state_contains_symbol(prior_steps=prior_steps, file_path="/x/foo.lua",
                                    symbol="frozenCells")
    assert has is True


def test_pre_state_returns_false_when_write_creates_file():
    prior_steps = [
        {"step_id":1,"action":{"tool_name":"mcp__mkr__Write","args":{"file_path":"/x/new.lua",
            "new_string":"frozenCells = {}"}}, "observation":{"text":"created"}},
    ]
    has = pre_state_contains_symbol(prior_steps=prior_steps, file_path="/x/new.lua",
                                    symbol="frozenCells")
    assert has is False


def test_select_genesis_candidate_returns_earliest_high_score(tmp_path):
    # Three filtered corpus entries; LLM scores them
    corpus_hits = [
        {"session":"a","step":3,"file":"f.lua","summary":"early intro",
         "introduces_symbols":["frozenCells"],"removes_symbols":[],
         "preserves_symbols":[],"timestamp":"2026-01-01T00:00:00Z"},
        {"session":"b","step":7,"file":"f.lua","summary":"later edit",
         "introduces_symbols":[],"removes_symbols":[],
         "preserves_symbols":["frozenCells"],"timestamp":"2026-02-01T00:00:00Z"},
    ]

    @pytest.mark.asyncio
    async def _run():
        fake = FakeLLMClient(canned={}, default=LLMResponse(content=(
            '[{"step":3,"score":3,"reason":"introduces"},'
            '{"step":7,"score":1,"reason":"only preserves"}]'),
            input_tokens=80, output_tokens=20))
        chosen = await select_genesis_candidate(
            corpus_hits=corpus_hits, symbol="frozenCells",
            llm=fake, model="qwen-flash")
        assert chosen is not None and chosen["step"] == 3 and chosen["session"] == "a"

    import asyncio; asyncio.run(_run())
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Add prompts to `tracing/prompts.py`**

```python
def genesis_score(symbol: str, file_path: str | None,
                  corpus_hits: list[dict[str, Any]]) -> tuple[str, str]:
    system = (
        f"You score cross-session steps for whether they FIRST introduced the wrong identifier '{symbol}' "
        f"into the codebase. Anchored 0..3 scale where 3 = clearly introduces this symbol. "
        "Output JSON ARRAY only."
    )
    user = (
        f"<TARGET SYMBOL>\n{symbol}\n\n<TARGET FILE>\n{file_path or '(any)'}\n\n"
        f"<CORPUS HITS — sorted by timestamp ASC>\n"
        + "\n".join(
            f"[session={h['session']} step={h['step']} ts={h.get('timestamp')}] "
            f"{h.get('summary','')} | introduces={h.get('introduces_symbols')} "
            f"preserves={h.get('preserves_symbols')}"
            for h in corpus_hits
        )
        + "\n\n"
        '<TASK>\nOutput JSON: [{"step":<int>,"session":"<id>","score":0..3,"reason":"<short>"},...]'
    )
    return system, user


def genesis_confirm(complaint_raw: str, proximate_root: dict[str, Any],
                    candidate: dict[str, Any]) -> tuple[str, str]:
    system = (
        "You confirm whether a candidate step is the GENESIS of a defect, or whether it is "
        "itself an extension of even-earlier wrong code (in which case mark outside_corpus). "
        "Output JSON object only."
    )
    user = (
        f"<COMPLAINT>\n{complaint_raw}\n\n"
        f"<PROXIMATE ROOT (within session)>\n{json.dumps(proximate_root, ensure_ascii=False)}\n\n"
        f"<GENESIS CANDIDATE>\n{json.dumps(candidate, ensure_ascii=False)}\n\n"
        '<TASK>\nReturn JSON: {"is_genesis": true|false, "outside_corpus": true|false, '
        '"note": "<short>"}.'
    )
    return system, user
```

- [ ] **Step 4: Implement `tracing/stage6_genesis.py`**

```python
"""Stage 6 — cross-session genesis trace.

Order: deterministic pre-state gate -> qwen-flash retrieval scoring -> qwen-plus confirm."""
from __future__ import annotations
import json as _json
from pathlib import Path
from typing import Any

from tracing.corpus import filter_corpus_by_symbol
from tracing.llm import LLMClient
from tracing.models import GenesisResult
from tracing.prompts import genesis_score, genesis_confirm


def pre_state_contains_symbol(*, prior_steps: list[dict[str, Any]],
                              file_path: str, symbol: str) -> bool:
    """Reconstruct the pre-state of file_path: find the earliest Read of file_path in S
    (or earliest Edit's old_string). Return True if symbol appears in that pre-state.

    For Write actions on previously-non-existent files: return False (no pre-state).
    """
    fname = (file_path or "").rsplit("/", 1)[-1]
    earliest_read_text: str | None = None
    earliest_edit_old: str | None = None
    saw_write_create = False
    for s in prior_steps:
        args = s["action"].get("args") or {}
        fp = (args.get("file_path") or "").rsplit("/", 1)[-1]
        if fp != fname:
            continue
        tool = s["action"]["tool_name"]
        if tool == "mcp__mkr__Read" and earliest_read_text is None:
            earliest_read_text = (s.get("observation") or {}).get("text") or ""
        if tool == "mcp__mkr__Edit" and earliest_edit_old is None:
            earliest_edit_old = args.get("old_string") or ""
        if tool == "mcp__mkr__Write":
            saw_write_create = True
    if earliest_read_text and symbol in earliest_read_text:
        return True
    if earliest_edit_old and symbol in earliest_edit_old:
        return True
    if saw_write_create and not earliest_read_text and not earliest_edit_old:
        return False
    return False


async def select_genesis_candidate(*, corpus_hits: list[dict[str, Any]],
                                   symbol: str, file_path: str | None = None,
                                   llm: LLMClient, model: str) -> dict[str, Any] | None:
    if not corpus_hits:
        return None
    system, user = genesis_score(symbol=symbol, file_path=file_path, corpus_hits=corpus_hits)
    resp = await llm.chat_json(model=model, system=system, user=user)
    txt = resp.content.strip()
    start = txt.find("["); end = txt.rfind("]")
    arr = _json.loads(txt[start : end + 1])
    by_id = {(h.get("session"), h["step"]): h for h in corpus_hits}
    scored = []
    for entry in arr:
        sid = int(entry.get("step", -1))
        sess = entry.get("session")
        key = (sess, sid)
        if key not in by_id:
            continue
        sc = max(0, min(3, int(entry.get("score", 0))))
        if sc >= 2:
            scored.append((by_id[key], sc))
    if not scored:
        return None
    # earliest timestamp wins among scored>=2
    scored.sort(key=lambda t: t[0].get("timestamp", ""))
    return scored[0][0]


async def confirm_genesis(*, complaint_raw: str, proximate_root: dict[str, Any],
                          candidate: dict[str, Any], llm: LLMClient, model: str) -> dict[str, Any]:
    system, user = genesis_confirm(complaint_raw, proximate_root, candidate)
    resp = await llm.chat_json(model=model, system=system, user=user)
    s = resp.content.strip()
    start = s.find("{"); end = s.rfind("}")
    return _json.loads(s[start : end + 1])


async def trace_genesis(*, prior_steps: list[dict[str, Any]],
                        proximate_root: dict[str, Any],
                        complaint_raw: str,
                        global_corpus_path: Path,
                        small_llm: LLMClient, small_model: str,
                        thinking_llm: LLMClient, thinking_model: str) -> GenesisResult:
    """Returns a GenesisResult. Caller decides how to record it."""
    file_path = proximate_root.get("file") or ""
    symbol    = proximate_root.get("symbol") or ""
    if not symbol or not file_path:
        return GenesisResult(found=False, note="missing_proximate_file_or_symbol")

    # Deterministic gate: if symbol is NOT in pre-state, proximate IS genesis
    if not pre_state_contains_symbol(prior_steps=prior_steps, file_path=file_path, symbol=symbol):
        return GenesisResult(found=False, note="originated_in_proximate_session")

    hits = filter_corpus_by_symbol(global_corpus_path, file_path=file_path, symbol=symbol)
    candidate = await select_genesis_candidate(
        corpus_hits=hits, symbol=symbol, file_path=file_path,
        llm=small_llm, model=small_model)
    if candidate is None:
        return GenesisResult(found=False, note="outside_corpus")

    confirm = await confirm_genesis(
        complaint_raw=complaint_raw, proximate_root=proximate_root,
        candidate=candidate, llm=thinking_llm, model=thinking_model)

    if confirm.get("outside_corpus"):
        return GenesisResult(found=False, note="outside_corpus")
    if not confirm.get("is_genesis"):
        return GenesisResult(found=False, note=str(confirm.get("note", "")))

    return GenesisResult(
        found=True,
        session=str(candidate.get("session", "")),
        step=int(candidate.get("step", -1)),
        file=str(candidate.get("file", "")),
        symbol=symbol,
        note=str(confirm.get("note", "")),
    )
```

- [ ] **Step 5: Run, expect PASS** then commit

```bash
.venv/bin/pytest tracing/tests/test_stage6_genesis.py -v
git add -A tracing/stage6_genesis.py tracing/tests/test_stage6_genesis.py tracing/prompts.py
git commit -m "feat(tracing): stage 6 genesis trace with deterministic gate" || true
```

---

### Task 13: Stage 7 — validation (deterministic + flash escape)

**Files:**
- Create: `tracing/stage7_validation.py`
- Create: `tracing/tests/test_stage7_validation.py`
- Modify: `tracing/prompts.py` (add `validation_compare`)

- [ ] **Step 1: Failing test**

```python
import pytest
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.stage7_validation import (
    extract_actual_fix_set, deterministic_compare, validate,
)


def test_extract_actual_fix_set_captures_rename_diff():
    posterior = [
        {"step_id":20,"action":{"tool_name":"mcp__mkr__Edit","args":{
            "file_path":"/x/story-27.lua",
            "old_string":"frozenCells = { {1,1} }",
            "new_string":"icePositions = { {1,1} }"}},
         "observation":{"text":"ok"}}
    ]
    fix_set = extract_actual_fix_set(posterior)
    assert "/x/story-27.lua" in fix_set["files"]
    # rename: both names changed-on-only-one-side -> in actual_symbols_changed
    assert "frozenCells" in fix_set["symbols_changed"]
    assert "icePositions" in fix_set["symbols_changed"]


def test_deterministic_compare_high_when_both_match():
    fix_set = {"files":{"/x/story-27.lua"}, "symbols_changed":{"frozenCells","icePositions"}}
    targets = [{"file":"/x/story-27.lua","symbol":"frozenCells->icePositions"}]
    res = deterministic_compare(targets, fix_set)
    assert res["confidence"] == "high"


def test_deterministic_compare_medium_file_only():
    fix_set = {"files":{"/x/story-27.lua"}, "symbols_changed":{"otherThing"}}
    targets = [{"file":"/x/story-27.lua","symbol":"frozenCells"}]
    res = deterministic_compare(targets, fix_set)
    assert res["confidence"] == "medium"


def test_deterministic_compare_unverified_when_no_posterior_edits():
    res = deterministic_compare([{"file":"x","symbol":"y"}],
                                {"files":set(),"symbols_changed":set()},
                                posterior_edit_count=0)
    assert res["confidence"] == "unverified"
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Add prompt to `tracing/prompts.py`**

```python
def validation_compare(predicted: list[dict[str, Any]], actual: dict[str, Any],
                       complaint: str) -> tuple[str, str]:
    system = (
        "You compare a predicted fix target against the agent's ACTUAL post-correction edits "
        "to decide whether they address the same root cause. Output JSON only."
    )
    user = (
        f"<COMPLAINT>\n{complaint}\n\n"
        f"<PREDICTED FIX TARGETS>\n{json.dumps(predicted, ensure_ascii=False)}\n\n"
        f"<ACTUAL FIX SET>\nfiles: {sorted(actual.get('files', []))}\n"
        f"symbols_changed: {sorted(actual.get('symbols_changed', []))}\n\n"
        '<TASK>\nReturn JSON: {"same_root_cause": true|false, "rationale":"<short>"}'
    )
    return system, user
```

- [ ] **Step 4: Implement `tracing/stage7_validation.py`**

```python
"""Stage 7 — validation. Deterministic compare first; flash only when neither
file nor symbol matches AND the agent did make posterior edits."""
from __future__ import annotations
import json as _json
import re
from typing import Any

from tracing.llm import LLMClient
from tracing.prompts import validation_compare

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def extract_actual_fix_set(posterior_steps: list[dict[str, Any]]) -> dict[str, Any]:
    files: set[str] = set()
    symbols_changed: set[str] = set()
    edit_count = 0
    for s in posterior_steps:
        if s["action"]["tool_name"] not in ("mcp__mkr__Edit", "mcp__mkr__Write"):
            continue
        edit_count += 1
        args = s["action"].get("args") or {}
        if isinstance(args.get("file_path"), str):
            files.add(args["file_path"])
        old = set(_IDENT.findall(args.get("old_string") or ""))
        new = set(_IDENT.findall(args.get("new_string") or ""))
        # tokens that appear on EXACTLY ONE side of the diff
        symbols_changed.update(old.symmetric_difference(new))
    return {"files": files, "symbols_changed": symbols_changed, "edit_count": edit_count}


def _norm_file(f: str) -> str:
    return (f or "").rsplit("/", 1)[-1]


def deterministic_compare(predicted_targets: list[dict[str, Any]],
                          fix_set: dict[str, Any],
                          posterior_edit_count: int | None = None) -> dict[str, Any]:
    edit_count = posterior_edit_count if posterior_edit_count is not None else fix_set.get("edit_count", 0)
    actual_files_basenames = {_norm_file(f) for f in fix_set.get("files", set())}
    actual_symbols = set(fix_set.get("symbols_changed", set()))
    actual_targets = [{"file": f} for f in fix_set.get("files", set())]

    if edit_count == 0:
        return {"confidence": "unverified", "actual_fix_targets": actual_targets}

    high = False
    medium = False
    for t in predicted_targets:
        if not isinstance(t, dict):
            continue
        f_basename = _norm_file(t.get("file", ""))
        sym_str = str(t.get("symbol", ""))
        sym_parts = {p.strip() for p in re.split(r"->|→", sym_str) if p.strip()}
        f_match = f_basename in actual_files_basenames
        s_match = bool(sym_parts & actual_symbols)
        if f_match and s_match:
            high = True; break
        if f_match:
            medium = True

    if high:
        return {"confidence": "high", "actual_fix_targets": actual_targets}
    if medium:
        return {"confidence": "medium", "actual_fix_targets": actual_targets}
    return {"confidence": "_neither", "actual_fix_targets": actual_targets}


async def validate(*, predicted_targets: list[dict[str, Any]],
                   posterior_steps: list[dict[str, Any]], complaint_raw: str,
                   llm: LLMClient, model: str) -> dict[str, Any]:
    fix_set = extract_actual_fix_set(posterior_steps)
    det = deterministic_compare(predicted_targets, fix_set)
    if det["confidence"] != "_neither":
        return det
    # flash escape — only flips low->medium, never to high
    system, user = validation_compare(predicted_targets, fix_set, complaint_raw)
    resp = await llm.chat_json(model=model, system=system, user=user)
    s = resp.content.strip()
    start = s.find("{"); end = s.rfind("}")
    obj = _json.loads(s[start : end + 1])
    confidence = "medium" if obj.get("same_root_cause") else "low"
    det["confidence"] = confidence
    return det
```

- [ ] **Step 5: Run, expect PASS** then commit

```bash
.venv/bin/pytest tracing/tests/test_stage7_validation.py -v
git add -A tracing/stage7_validation.py tracing/tests/test_stage7_validation.py tracing/prompts.py
git commit -m "feat(tracing): stage 7 validation with both-sides diff matching" || true
```

---

## Phase D · Orchestration & end-to-end

### Task 14: Pipeline orchestrator (one case → one trace.json)

**Files:**
- Create: `tracing/pipeline.py`
- Create: `tracing/tests/test_pipeline.py`

- [ ] **Step 1: Failing test** — synthetic `mini` fixture end-to-end with a fake LLM:

```python
import json
import pytest
from pathlib import Path
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.data_io import load_traj, load_classified
from tracing.pipeline import run_one_case
from tracing.models import TraceCase


@pytest.mark.asyncio
async def test_run_one_case_produces_trace_json(mini_traj_path, mini_classified_path, tmp_path):
    cache_root = tmp_path / "cache"
    output_root = tmp_path / "traces"

    fake = FakeLLMClient(canned={
        ("qwen-flash", "Output JSON array, one entry per input step"): LLMResponse(
            content='[{"step":11,"summary":"Edit story-27 frozenCells +4"}]',
            input_tokens=50, output_tokens=20),
        ("qwen-flash", "produce the glossary"): LLMResponse(
            content='[{"name":"\u51b0\u706b\u82b1\u56ed","kind":"level","canonical":"/workspace/story-27.lua","evidence":"file_paths_touched"}]',
            input_tokens=50, output_tokens=20),
        ("qwen-flash", "Resolve and return JSON"): LLMResponse(
            content=('{"artifacts":[{"path":"/workspace/story-27.lua","source":"glossary","confidence":"high"}],'
                     '"symbols":[{"name":"frozenCells","source":"observed","confidence":"high"}],'
                     '"surface":"in-game runtime","user_intent_restated":"ice missing","insufficient_evidence":false}'),
            input_tokens=200, output_tokens=80),
        ("qwen-flash", "score each by step id"): LLMResponse(
            content='[{"step":11,"score":3,"reason":"mutates frozenCells"}]',
            input_tokens=200, output_tokens=80),
        ("qwen-plus-latest", "Return JSON only with keys: evidence_chain"): LLMResponse(
            content=('{"evidence_chain":{'
                     '"complaint":{"ref":{"turn":2},"text":"ice missing"},'
                     '"symptom":{"text":"no ice rendered"},'
                     '"introducing":{"ref":{"step":11},"text":"appended to frozenCells"},'
                     '"missing_check":{"text":"never read board.lua"}},'
                     '"proximate_root":{"session":"minisess","step":11,"file":"/workspace/story-27.lua","symbol":"frozenCells"},'
                     '"genesis_check":{"needs_cross_session_trace":false,"reason":"originated_here"},'
                     '"failure_mode":"verification_gap_via_lexical_familiarity",'
                     '"counter_pattern":"Read consumer code before mutating an existing config field.",'
                     '"predicted_fix_target":[{"file":"/workspace/story-27.lua","symbol":"frozenCells->icePositions"}],'
                     '"attribution_confidence":"high"}'),
            input_tokens=2000, output_tokens=400),
    }, default=LLMResponse(content="{}", input_tokens=0, output_tokens=0))

    case = TraceCase(
        dataset="ds", project="wzp", session_id="minisess", turn_id=2,
        complaint_raw="\u6e38\u620f\u5185\u6ca1\u6709\u770b\u5230\u51b0\u5757",
        complaint_index_in_classified=1,
        classification={"intent_primary":"bug_report","is_correction_of_ai_work":True,
                        "target_artifact":"game_logic","summary_zh":"ice not shown"},
    )
    out_path = await run_one_case(
        case=case, traj=load_traj(mini_traj_path),
        classified=load_classified(mini_classified_path),
        cache_root=cache_root, output_root=output_root,
        global_corpus_path=None,
        small_llm=fake, small_model="qwen-flash",
        thinking_llm=fake, thinking_model="qwen-plus-latest",
    )
    assert out_path.exists()
    trace = json.loads(out_path.read_text(encoding="utf-8"))
    assert trace["proximate_root"]["step"] == 11
    assert trace["failure_mode"] == "verification_gap_via_lexical_familiarity"
    assert trace["validation"]["confidence"] == "high"
```

- [ ] **Step 2: Run, expect FAIL**


- [ ] **Step 3: Implement `tracing/pipeline.py`**

```python
"""Per-case 7-stage orchestrator."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from tracing.glossary import build_glossary, read_cached_glossary, write_glossary
from tracing.llm import LLMClient
from tracing.models import TraceCase, GenesisResult
from tracing.stage2_context import load_case_context
from tracing.stage3_entities import resolve_entities
from tracing.stage4_candidates import score_and_select_candidates
from tracing.stage5_attribution import attribute_root_cause, compute_negative_findings
from tracing.stage6_genesis import trace_genesis
from tracing.stage7_validation import validate
from tracing.step_summary import (
    iter_action_steps_with_prior_thought, deterministic_summary_record,
    add_llm_summaries, write_summary_jsonl,
)


def _trace_id(case: TraceCase) -> str:
    return f"{case.project}__{case.session_id}__turn-{case.turn_id}"


def _output_path(*, output_root: Path, case: TraceCase, low_confidence: bool) -> Path:
    base = output_root / case.dataset / case.project
    if low_confidence:
        base = base / "_review"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{case.session_id}__turn-{case.turn_id}.json"


async def _ensure_summaries(*, traj, cache_root, dataset, project, session_id, llm, model):
    out_path = cache_root / dataset / project / "step-summary" / f"{session_id}.jsonl"
    if out_path.exists():
        return [json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    enriched = list(iter_action_steps_with_prior_thought(traj))
    records = [deterministic_summary_record(e) for e in enriched]
    records = await add_llm_summaries(records, llm=llm, model=model)
    write_summary_jsonl(records, out_path)
    return records


async def _ensure_glossary(*, traj, cache_root, dataset, project, session_id, llm, model):
    out_path = cache_root / dataset / project / "glossary" / f"{session_id}.json"
    cached = read_cached_glossary(out_path)
    if cached is not None:
        return cached
    entries = await build_glossary(traj, llm=llm, model=model)
    write_glossary(entries, out_path)
    return entries


async def run_one_case(*, case: TraceCase, traj: dict[str, Any], classified: dict[str, Any],
                       cache_root: Path, output_root: Path,
                       global_corpus_path: Optional[Path],
                       small_llm: LLMClient, small_model: str,
                       thinking_llm: LLMClient, thinking_model: str) -> Path:
    pub_path  = _output_path(output_root=output_root, case=case, low_confidence=False)
    rev_path  = _output_path(output_root=output_root, case=case, low_confidence=True)
    if pub_path.exists():
        return pub_path
    if rev_path.exists():
        return rev_path

    summaries = await _ensure_summaries(
        traj=traj, cache_root=cache_root,
        dataset=case.dataset, project=case.project, session_id=case.session_id,
        llm=small_llm, model=small_model,
    )
    glossary = await _ensure_glossary(
        traj=traj, cache_root=cache_root,
        dataset=case.dataset, project=case.project, session_id=case.session_id,
        llm=small_llm, model=small_model,
    )

    ctx = load_case_context(traj=traj, classified=classified,
                            complaint_index=case.complaint_index_in_classified,
                            complaint_turn_id=case.turn_id)

    touched_files = {((s["action"].get("args") or {}).get("file_path") or "")
                     for s in ctx["prior_steps"]
                     if (s["action"].get("args") or {}).get("file_path")}

    entities = await resolve_entities(
        complaint_raw=case.complaint_raw,
        prior_user_turns=ctx["prior_user_turns"],
        agent_last_response=ctx["agent_last_response"],
        glossary=glossary, classification=case.classification,
        touched_files=touched_files,
        llm=small_llm, model=small_model,
    )
    if entities.get("insufficient_evidence"):
        abandoned = {"trace_id": _trace_id(case), "abandoned": "no_entities_resolved",
                     "entities": entities, "complaint": case.complaint_raw}
        rev_path.write_text(json.dumps(abandoned, ensure_ascii=False, indent=2), encoding="utf-8")
        return rev_path

    prior_step_ids = {s["step_id"] for s in ctx["prior_steps"]}
    prior_summaries = [r for r in summaries if r["step"] in prior_step_ids]

    selected = await score_and_select_candidates(
        summaries=prior_summaries, entities=entities,
        llm=small_llm, model=small_model,
    )
    if not selected:
        abandoned = {"trace_id": _trace_id(case), "abandoned": "no_candidates",
                     "entities": entities, "complaint": case.complaint_raw}
        rev_path.write_text(json.dumps(abandoned, ensure_ascii=False, indent=2), encoding="utf-8")
        return rev_path

    by_id = {r["step"]: r for r in summaries}
    for c in selected:
        c["detail"] = by_id.get(c["step"], {})

    consumer_files = [a["path"] for a in entities.get("artifacts", [])
                      if a.get("source") in ("hypothesis", "observed")]
    hypothesis_symbols = [s["name"] for s in entities.get("symbols", [])
                          if s.get("source") == "hypothesis"]
    nf = compute_negative_findings(
        prior_steps=ctx["prior_steps"],
        consumer_files_to_check=consumer_files,
        symbols_to_grep=hypothesis_symbols,
    )

    attribution = await attribute_root_cause(
        complaint_raw=case.complaint_raw, complaint_turn_id=case.turn_id,
        classification=case.classification,
        project=case.project, project_name=ctx["session_meta"].get("project_name", ""),
        session_id=case.session_id,
        entities=entities, candidates=selected, negative_findings=nf,
        llm=thinking_llm, model=thinking_model,
    )

    genesis = GenesisResult(found=False, note="not_run")
    needs_g = (attribution.get("genesis_check") or {}).get("needs_cross_session_trace") is True
    if needs_g and global_corpus_path is not None:
        genesis = await trace_genesis(
            prior_steps=ctx["prior_steps"], proximate_root=attribution["proximate_root"],
            complaint_raw=case.complaint_raw, global_corpus_path=global_corpus_path,
            small_llm=small_llm, small_model=small_model,
            thinking_llm=thinking_llm, thinking_model=thinking_model,
        )

    val = await validate(
        predicted_targets=attribution.get("predicted_fix_target", []),
        posterior_steps=ctx["posterior_steps"],
        complaint_raw=case.complaint_raw,
        llm=small_llm, model=small_model,
    )

    confidence = (val.get("confidence") or "unverified")
    is_low = (confidence == "low") or (attribution.get("attribution_confidence") == "candidates_insufficient")

    payload = {
        "trace_id": _trace_id(case),
        "dataset": case.dataset, "project": case.project,
        "session_id": case.session_id, "turn_id": case.turn_id,
        "complaint": {
            "raw": case.complaint_raw,
            "intent_primary": case.classification.get("intent_primary"),
            "is_correction_of_ai_work": case.classification.get("is_correction_of_ai_work"),
        },
        "entities": entities,
        "negative_findings": nf,
        "evidence_chain": attribution.get("evidence_chain", {}),
        "proximate_root": attribution.get("proximate_root"),
        "genesis_root":   {"found": genesis.found, "session": genesis.session,
                            "step": genesis.step, "file": genesis.file,
                            "symbol": genesis.symbol, "note": genesis.note},
        "failure_mode":    attribution.get("failure_mode"),
        "counter_pattern": attribution.get("counter_pattern"),
        "predicted_fix_target": attribution.get("predicted_fix_target", []),
        "validation": val,
        "model": {"thinking": thinking_model, "small": small_model},
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    out_path = rev_path if is_low else pub_path
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out_path)
    return out_path
```

- [ ] **Step 4: Run, expect PASS** then commit

```bash
.venv/bin/pytest tracing/tests/test_pipeline.py -v
git add tracing/pipeline.py tracing/tests/test_pipeline.py
git commit -m "feat(tracing): per-case 7-stage orchestrator" || true
```

---

### Task 15: CLI entry (argparse) + nohup launcher

**Files:**
- Create: `tracing/trace.py`
- Create: `tracing/run.sh`

- [ ] **Step 1: Implement `tracing/trace.py`**

```python
"""CLI entry point. Discovers triggers across (dataset, projects), runs cases
through the pipeline with bounded concurrency. Snapshot resume by output file."""
from __future__ import annotations
import argparse
import asyncio
import sys
import time
from pathlib import Path

from tracing.data_io import load_traj, load_classified, iter_trigger_cases
from tracing.llm import DashScopeClient
from tracing.logging_setup import setup_logging
from tracing.pipeline import run_one_case
from tracing.corpus import build_global_corpus
from tracing.settings import (
    DEFAULT_DATASET_ROOT, DEFAULT_CLASSIFIED_ROOT, DEFAULT_OUTPUT_ROOT,
    DEFAULT_CACHE_ROOT, DEFAULT_THINKING_MODEL, DEFAULT_SMALL_MODEL, MAX_CONCURRENCY,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="traj-root-cause-tracer CLI")
    p.add_argument("--dataset-root",    type=Path, default=DEFAULT_DATASET_ROOT)
    p.add_argument("--classified-root", type=Path, default=DEFAULT_CLASSIFIED_ROOT)
    p.add_argument("--output-root",     type=Path, default=DEFAULT_OUTPUT_ROOT)
    p.add_argument("--cache-root",      type=Path, default=DEFAULT_CACHE_ROOT)
    p.add_argument("--projects",        type=str, default="",
                   help="comma-separated project names; default = discover all dirs under --dataset-root")
    p.add_argument("--only", nargs="*", default=None,
                   help="optional list of session ids (file stems) to trace")
    p.add_argument("--concurrency",     type=int, default=MAX_CONCURRENCY)
    p.add_argument("--thinking-model",  default=DEFAULT_THINKING_MODEL)
    p.add_argument("--small-model",     default=DEFAULT_SMALL_MODEL)
    p.add_argument("--rebuild-cache",   action="store_true",
                   help="force-rebuild glossary, step-summary, and global corpus caches")
    p.add_argument("--dry-run",         action="store_true",
                   help="discover work, print plan, no LLM calls")
    p.add_argument("--log-level",       default="INFO")
    p.add_argument("--log-dir",         type=Path, default=Path(__file__).resolve().parent / "logs")
    p.add_argument("--skip-genesis",    action="store_true",
                   help="skip cross-session genesis trace stage 6")
    return p.parse_args()


def discover_projects(dataset_root: Path, projects_arg: str) -> list[str]:
    if projects_arg:
        return [p for p in projects_arg.split(",") if p.strip()]
    return sorted([p.name for p in dataset_root.iterdir() if p.is_dir()])


async def _bound(sem: asyncio.Semaphore, coro):
    async with sem:
        return await coro


async def main_async(args: argparse.Namespace) -> int:
    setup_logging(log_dir=args.log_dir, level=args.log_level)
    dataset_name = args.dataset_root.name

    projects = discover_projects(args.dataset_root, args.projects)
    print(f"[traj-trace] dataset={dataset_name} projects={projects} concurrency={args.concurrency}",
          flush=True)

    if args.dry_run:
        for proj in projects:
            n = sum(1 for _ in (args.dataset_root / proj).glob("*.traj"))
            print(f"  {proj}: {n} sessions")
        return 0

    small = DashScopeClient()
    thinking = small  # same connection; different models per call
    sem = asyncio.Semaphore(args.concurrency)

    corpora: dict[str, Path | None] = {}
    if not args.skip_genesis:
        for proj in projects:
            cp = await build_global_corpus(
                dataset_root=args.dataset_root, dataset=dataset_name, project=proj,
                cache_root=args.cache_root, llm=small, model=args.small_model,
                rebuild=args.rebuild_cache,
            )
            corpora[proj] = cp
            print(f"  global corpus ready: {proj} -> {cp}", flush=True)
    else:
        for proj in projects:
            corpora[proj] = None

    summary = {"ok": 0, "abandoned": 0, "error": 0}
    for proj in projects:
        proj_dataset_dir    = args.dataset_root    / proj
        proj_classified_dir = args.classified_root / proj
        for traj_path in sorted(proj_dataset_dir.glob("*.traj")):
            sid = traj_path.stem
            if args.only and sid not in args.only:
                continue
            classified_path = proj_classified_dir / f"{sid}.json"
            if not classified_path.exists():
                continue
            traj = load_traj(traj_path)
            classified = load_classified(classified_path)
            cases = list(iter_trigger_cases(
                dataset=dataset_name, project=proj,
                traj_path=traj_path, classified_path=classified_path))
            if not cases:
                continue
            print(f"  {proj}/{sid}: {len(cases)} trigger case(s)", flush=True)

            tasks = []
            for case in cases:
                async def _run(case=case, traj=traj, classified=classified, proj=proj):
                    t0 = time.time()
                    try:
                        out = await run_one_case(
                            case=case, traj=traj, classified=classified,
                            cache_root=args.cache_root, output_root=args.output_root,
                            global_corpus_path=corpora[proj],
                            small_llm=small, small_model=args.small_model,
                            thinking_llm=thinking, thinking_model=args.thinking_model,
                        )
                        dt = time.time() - t0
                        kind = "abandoned" if "_review" in str(out) else "ok"
                        print(f"    [{dt:.1f}s] {kind:9s} {out.relative_to(args.output_root)}", flush=True)
                        return kind
                    except Exception as e:
                        print(f"    ERROR {case.session_id}__turn-{case.turn_id}: {e!r}", flush=True)
                        return "error"
                tasks.append(_bound(sem, _run()))

            for r in await asyncio.gather(*tasks, return_exceptions=False):
                summary[r] = summary.get(r, 0) + 1

    print(f"\n[traj-trace] summary: {summary}", flush=True)
    return 0 if summary["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main_async(parse_args())))
```

- [ ] **Step 2: Implement `tracing/run.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -z "${DASHSCOPE_API_KEY:-}" ]]; then
  echo "ERROR: DASHSCOPE_API_KEY not exported" >&2
  exit 2
fi

PY=""
for c in ../.venv/bin/python .venv/bin/python python3 python; do
  if command -v "$c" >/dev/null 2>&1 || [[ -x "$c" ]]; then
    PY="$c"; break
  fi
done
[[ -n "$PY" ]] || { echo "interpreter not found" >&2; exit 2; }

mkdir -p logs
ts=$(date +%Y%m%d-%H%M%S)
log="logs/trace-${ts}.log"
ln -sfn "trace-${ts}.log" logs/latest.log

echo "launching tracer -> $log"
nohup "$PY" -u -m tracing.trace "$@" >"$log" 2>&1 &
pid=$!
echo "$pid" >logs/trace.pid
echo "pid=$pid    tail -f $(pwd)/$log"
```

- [ ] **Step 3: Make executable, smoke-test dry-run**

```bash
chmod +x tracing/run.sh
cd /Users/xd/Desktop/work/project-logs/traj-err-trace
.venv/bin/python -m tracing.trace --dry-run
```

Expected: prints discovered projects (`wzp`, `zzj`) and session counts; zero LLM calls.

- [ ] **Step 4: Commit**

Use git add then git commit with message "feat(tracing): CLI entry + nohup launcher".

---

### Task 16: End-to-end test on canonical wzp/6b8566ea/turn-12 case

**Files:**
- Create: `tracing/tests/test_e2e_canonical.py`

This test exercises the entire pipeline against REAL fixture data (the actual `.traj` and classified JSON for `wzp/6b8566ea`) using a `FakeLLMClient` whose responses are scripted to mimic what we expect qwen-flash + qwen-plus to produce. Catches regressions in the pipeline glue without spending API credits.

- [ ] **Step 1: Write the test**

```python
"""End-to-end regression on the canonical 6b8566ea/turn-12 case.

Spec §16 acceptance criterion #3 — must:
  - identify step 112 as proximate_root,
  - declare genesis_check needs_cross_session_trace=true,
  - classify failure_mode = verification_gap_via_lexical_familiarity,
  - validate `high` against the agent's actual fix at step ~134 in the same session.
"""
import json
import pytest
from pathlib import Path
from tracing.data_io import load_traj, load_classified, iter_trigger_cases
from tracing.llm import FakeLLMClient, LLMResponse
from tracing.pipeline import run_one_case

REPO = Path(__file__).resolve().parents[3]
TRAJ = REPO / "traj-data-new" / "wzp" / "6b8566ea.traj"
CLF  = REPO / "examples"      / "wzp" / "6b8566ea.json"


@pytest.mark.skipif(not TRAJ.exists() or not CLF.exists(),
                    reason="canonical fixtures not present in this checkout")
@pytest.mark.asyncio
async def test_canonical_proximate_root_is_step_112(tmp_path):
    traj = load_traj(TRAJ)
    classified = load_classified(CLF)
    cases = list(iter_trigger_cases(
        dataset="traj-data-new", project="wzp",
        traj_path=TRAJ, classified_path=CLF))
    target = next(
        c for c in cases
        if c.complaint_raw.strip() == "糖糖的冰火花园关卡，游戏内没有看到冰块"
    )

    fake = FakeLLMClient(canned={
        ("qwen-flash", "Output JSON array, one entry per input step"):
            LLMResponse(content="[]", input_tokens=10, output_tokens=10),
        ("qwen-flash", "produce the glossary"):
            LLMResponse(content=(
                '[{"name":"冰火花园","kind":"level",'
                '"canonical":"/workspace/scripts/config/storyline-levels/story-27.lua",'
                '"evidence":"file_paths_touched"}]'),
                input_tokens=400, output_tokens=80),
        ("qwen-flash", "Resolve and return JSON"):
            LLMResponse(content=(
                '{"artifacts":[{"path":"/workspace/scripts/config/storyline-levels/story-27.lua","source":"glossary","confidence":"high"}],'
                '"symbols":[{"name":"frozenCells","source":"observed","confidence":"high"},'
                '{"name":"icePositions","source":"hypothesis","confidence":"medium"}],'
                '"surface":"in-game runtime","user_intent_restated":"ice obstacles missing in story-27",'
                '"insufficient_evidence":false}'),
                input_tokens=400, output_tokens=200),
        ("qwen-flash", "score each by step id"):
            LLMResponse(content='[{"step":112,"score":3,"reason":"mutates frozenCells in story-27"}]',
                        input_tokens=400, output_tokens=80),
        ("qwen-plus-latest", "Return JSON only with keys: evidence_chain"):
            LLMResponse(content=(
                '{"evidence_chain":{'
                '"complaint":{"ref":{"turn":12},"text":"ice missing"},'
                '"symptom":{"text":"no ice rendered in story-27"},'
                '"introducing":{"ref":{"step":112},"text":"appended to frozenCells without verifying consumer"},'
                '"missing_check":{"text":"never read board.lua, never grepped icePositions"}},'
                '"proximate_root":{"session":"6b8566ea","step":112,'
                '"file":"/workspace/scripts/config/storyline-levels/story-27.lua","symbol":"frozenCells"},'
                '"genesis_check":{"needs_cross_session_trace":true,"reason":"extends pre-existing frozenCells"},'
                '"failure_mode":"verification_gap_via_lexical_familiarity",'
                '"counter_pattern":"Read consumer code before mutating an existing config field.",'
                '"predicted_fix_target":[{"file":"/workspace/scripts/config/storyline-levels/story-27.lua","symbol":"frozenCells->icePositions"}],'
                '"attribution_confidence":"high"}'),
                input_tokens=4000, output_tokens=600),
    }, default=LLMResponse(content="{}", input_tokens=0, output_tokens=0))

    out = await run_one_case(
        case=target, traj=traj, classified=classified,
        cache_root=tmp_path / "cache", output_root=tmp_path / "traces",
        global_corpus_path=None,
        small_llm=fake, small_model="qwen-flash",
        thinking_llm=fake, thinking_model="qwen-plus-latest",
    )
    trace = json.loads(out.read_text(encoding="utf-8"))
    assert trace["proximate_root"]["step"] == 112
    assert trace["failure_mode"] == "verification_gap_via_lexical_familiarity"
    assert trace["validation"]["confidence"] in ("high", "medium")
    assert "_review" not in str(out)
```

- [ ] **Step 2: Run, expect PASS**

```bash
.venv/bin/pytest tracing/tests/test_e2e_canonical.py -v
```

If the canonical fixtures exist (default) the test runs; if not it's skipped.

- [ ] **Step 3: Final smoke run on real data — ONE session, real LLM**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-err-trace
.venv/bin/python -m tracing.trace --only 6b8566ea --skip-genesis 2>&1 | tee /tmp/trace-smoke.log

# Expected ending:
#   [traj-trace] summary: {'ok': 1, 'abandoned': 0, 'error': 0}
cat traces/traj-data-new/wzp/6b8566ea__turn-12.json | python3 -m json.tool | head -40
```

Expected: `proximate_root.step == 112`, `failure_mode == "verification_gap_via_lexical_familiarity"`, `validation.confidence in {high, medium}`.

- [ ] **Step 4: Final commit**

git add the new test file, then commit with message "test(tracing): canonical 6b8566ea regression".

---

## Final verification checklist

- [ ] All 16 tasks committed
- [ ] `.venv/bin/pytest tracing/tests/ -v` — full suite green
- [ ] Smoke run on `--only 6b8566ea` produces a `high` or `medium` confidence trace
- [ ] `tracing/logs/latest.log` and `tracing/logs/events-*.jsonl` exist after a run
- [ ] Re-running the same `--only 6b8566ea` is a no-op (snapshot resume works)
- [ ] `--dry-run` correctly enumerates work without LLM calls
- [ ] `--projects wzp` and `--projects zzj` both work; default discovers both

## Spec coverage map

| Spec section | Implemented in task |
|---|---|
| §3 two-tier trace model | Tasks 11 (proximate) + 12 (genesis) |
| §4 7-stage pipeline | Tasks 8 + 9 + 10 + 11 + 12 + 13; orchestrated in Task 14 |
| §5 output schema | Task 14 (`payload` dict) |
| §6 failure-mode taxonomy | Task 11 (`FAILURE_MODE_TAXONOMY` in prompts.py) |
| §7 storage layout | Task 14 (`_output_path`) + Task 15 (CLI defaults) |
| §10 validation as publication gate | Task 14 (`is_low` routing to `_review/`) |
| §11.1 Stage 1 glossary with `kind` | Task 6 |
| §11.2 Stage 2 context loader | Task 8 |
| §11.3 Stage 3 entities + classifier signal + insufficient_evidence | Task 9 |
| §11.4 Stage 4 step-summary fields + score anchors | Tasks 4, 5, 10 |
| §11.5 Stage 5 negative findings + slotted chain + grounding validators | Task 11 |
| §11.6 Stage 6 deterministic gate (pre_state) + retrieval + confirm | Task 12 |
| §11.7 Stage 7 both-sides diff + flash escape | Task 13 |
| §12 cross-cutting hallucination defenses | Tasks 9, 10, 11 (step-ID grounding + closed vocab + retry + low-confidence routing) |
| §13 dataset extensibility (argparse) | Task 15 |
| §14 logging streams | Tasks 1 (logging_setup), 15 (CLI wiring) |
| §16 acceptance criteria #3 (canonical case) | Task 16 |

## Out-of-scope confirmations (per spec §15)

- Realtime tracing — not implemented
- Cross-project genesis search — not implemented (per-project only)
- Auto-fix suggestion / aggregated dashboard / failure-mode auto-discovery — separate future work
