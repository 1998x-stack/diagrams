# Traj-Evolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-stage pipeline that mines real Claude Code session trajectories into ECC-format skill folders for two game projects (wzp, zzj).

**Architecture:** Stage 1 (`traj_miner.py`) is pure-Python deterministic pattern mining producing `patterns.json`. Stage 2 (`traj_enricher.py`) calls an LLM (Qwen preferred, Anthropic fallback) to turn each pattern into a YAML-frontmatter instinct file. Stage 3 (`evolve_skills.py`) stages instincts into a synthetic homunculus project and runs `instinct-cli.py evolve --generate`, then copies the output to `project-logs/evolved/{wzp,zzj}/`.

**Tech Stack:** Python 3.11+, `openai` SDK (Qwen via OpenAI-compatible API), `anthropic` SDK, `asyncio`, `pytest`, `pyyaml`

---

## File Map

```
traj-evolver/
├── config.yaml                    # provider + threshold config
├── Makefile                       # mine / enrich / evolve / pipeline / test targets
├── README.md                      # quick-start + troubleshooting
├── prompts/
│   └── enrich.md                  # cached LLM prompt prefix
├── scripts/
│   ├── traj_miner.py              # Stage 1: scan + select → patterns.json
│   ├── traj_enricher.py           # Stage 2: LLM enrichment → instinct .md files
│   └── evolve_skills.py           # Stage 3: stage instincts + run instinct-cli + copy output
└── tests/
    ├── conftest.py                # shared fixtures (in-memory traj dicts)
    ├── test_miner.py
    ├── test_enricher.py
    └── test_evolve.py
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `traj-evolver/config.yaml`
- Create: `traj-evolver/tests/conftest.py`
- Create: `traj-evolver/prompts/enrich.md` (placeholder, filled in Task 9)

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p traj-evolver/{scripts,prompts,tests}
touch traj-evolver/scripts/__init__.py traj-evolver/tests/__init__.py
```

- [ ] **Step 2: Write `traj-evolver/config.yaml`**

```yaml
enricher:
  providers:
    - name: qwen
      enabled: true
      api_key_env: DASHSCOPE_API_KEY
      base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
      model: qwen3.6-plus
      extra_body:
        enable_thinking: false
      sdk: openai

    - name: anthropic
      enabled: true
      api_key_env: ANTHROPIC_API_KEY
      model: claude-sonnet-4-6
      sdk: anthropic
      prompt_caching: true

  temperature: 0
  concurrency: 5
  max_retries: 3
  retry_backoff_sec: 2

miner:
  min_frequency: 3
  top_k_per_family: 20
  distinctness_weight: 0.5
  min_sessions: 2

evolve:
  instinct_cli_path: ~/.claude/plugins/cache/everything-claude-code/everything-claude-code/1.9.0/skills/continuous-learning-v2/scripts/instinct-cli.py
```

- [ ] **Step 3: Write `traj-evolver/tests/conftest.py`**

This builds two minimal synthetic traj dicts (A and B) used by all unit tests. Three turns each. The Read→Grep→Edit n-gram appears in both, creating the cross-session frequency needed for selection.

```python
import pytest

def _make_step(step_id, tool_name, phase, file_path=None):
    args = {"file_path": file_path} if file_path else {}
    return {
        "step_id": step_id,
        "phase": phase,
        "thinking": None,
        "thought": None,
        "action": {"tool_name": tool_name, "tool_use_id": f"id{step_id}", "args": args},
        "observation": {"type": "tool_result", "text": "ok", "exit_code": None},
        "status": "ok",
        "timestamp": "2026-01-01T00:00:00Z",
        "execution_time": 1.0,
        "usage": {"input_tokens": 10, "output_tokens": 5,
                  "cache_read_tokens": 0, "cache_creation_tokens": 0},
    }

def _make_user_msg(turn_id, content):
    return {"turn_id": turn_id, "role": "user", "content": content,
            "timestamp": "2026-01-01T00:00:00Z"}

def _make_agent_run(turn_id, steps):
    return {"turn_id": turn_id, "agent_run_id": f"run_t{turn_id}",
            "steps": steps, "run_summary": {}}

@pytest.fixture
def traj_a():
    """Session A: 3 turns. Turn 1: Read→Grep→Edit(game.lua).
    Turn 2: user says 'wrong'. Turn 3: Edit(game.lua) — correction signal."""
    return {
        "schema_version": "2.0",
        "conversation_id": "session-aaaa",
        "session_metadata": {"project": "wzp", "project_name": "脑力大冒险"},
        "messages": [
            _make_user_msg(1, "fix the bug"),
            _make_agent_run(1, [
                _make_step(1, "mcp__mkr__Read", "localization", "scripts/game.lua"),
                _make_step(2, "Grep", "localization"),
                _make_step(3, "mcp__mkr__Edit", "editing", "scripts/game.lua"),
            ]),
            _make_user_msg(2, "wrong, revert that"),
            _make_agent_run(2, []),
            _make_user_msg(3, "ok try again"),
            _make_agent_run(3, [
                _make_step(4, "mcp__mkr__Edit", "editing", "scripts/game.lua"),
            ]),
        ],
        "phases": [], "markers": [], "subagents": [], "summary": {},
    }

@pytest.fixture
def traj_b():
    """Session B: 2 turns. Turn 1: Read→Grep→Edit(game.lua).
    Turn 2: mcp__sce-urhox__build — platform fingerprint tool."""
    return {
        "schema_version": "2.0",
        "conversation_id": "session-bbbb",
        "session_metadata": {"project": "wzp", "project_name": "脑力大冒险"},
        "messages": [
            _make_user_msg(1, "fix the crash bug"),
            _make_agent_run(1, [
                _make_step(1, "mcp__mkr__Read", "localization", "scripts/game.lua"),
                _make_step(2, "Grep", "localization"),
                _make_step(3, "mcp__mkr__Edit", "editing", "scripts/game.lua"),
            ]),
            _make_user_msg(2, "build it"),
            _make_agent_run(2, [
                _make_step(4, "mcp__sce-urhox__build", "verification"),
            ]),
        ],
        "phases": [], "markers": [], "subagents": [], "summary": {},
    }

@pytest.fixture
def traj_c():
    """Session C: 1 turn. Read→Grep→Edit (third occurrence of the n-gram)."""
    return {
        "schema_version": "2.0",
        "conversation_id": "session-cccc",
        "session_metadata": {"project": "wzp", "project_name": "脑力大冒险"},
        "messages": [
            _make_user_msg(1, "fix this bug please"),
            _make_agent_run(1, [
                _make_step(1, "mcp__mkr__Read", "localization"),
                _make_step(2, "Grep", "localization"),
                _make_step(3, "mcp__mkr__Edit", "editing"),
            ]),
        ],
        "phases": [], "markers": [], "subagents": [], "summary": {},
    }
```

- [ ] **Step 4: Create placeholder prompt file and verify pytest can collect**

```bash
echo "# Enricher prompt — filled in Task 9" > traj-evolver/prompts/enrich.md
cd traj-evolver && python -m pytest tests/ --collect-only -q
```

Expected: `no tests ran` with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add traj-evolver/
git commit -m "feat(traj-evolver): project scaffold, config, test fixtures"
```

---

## Task 2: traj_miner.py — Data Loading + N-gram Mining

**Files:**
- Create: `traj-evolver/scripts/traj_miner.py`
- Create: `traj-evolver/tests/test_miner.py` (partial — n-gram section)

- [ ] **Step 1: Write the failing n-gram tests**

Create `traj-evolver/tests/test_miner.py`:

```python
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "scripts"))

import pytest
from traj_miner import extract_turns, tool_names, mine_ngrams


def test_extract_turns_user_agent_interleave(traj_a):
    turns = extract_turns(traj_a)
    assert len(turns) == 3
    assert turns[0]["user_content"] == "fix the bug"
    assert turns[0]["session_id"] == "session-aaaa"
    assert len(turns[0]["steps"]) == 3


def test_extract_turns_skips_empty_agent_runs(traj_a):
    turns = extract_turns(traj_a)
    # Turn 2 has an empty agent run — still included but steps=[]
    assert turns[1]["user_content"] == "wrong, revert that"
    assert turns[1]["steps"] == []


def test_tool_names_extracts_action_tool_name(traj_a):
    turns = extract_turns(traj_a)
    assert tool_names(turns[0]["steps"]) == [
        "mcp__mkr__Read", "Grep", "mcp__mkr__Edit"
    ]


def test_mine_ngrams_bigram_counts_across_sessions(traj_a, traj_b, traj_c):
    all_session_turns = [
        extract_turns(traj_a),
        extract_turns(traj_b),
        extract_turns(traj_c),
    ]
    patterns = mine_ngrams(all_session_turns, n=2)
    # Read→Grep appears in turns 0 of sessions A, B, C
    read_grep = next(
        p for p in patterns
        if p["sequence"] == ["mcp__mkr__Read", "Grep"]
    )
    assert read_grep["frequency"] == 3
    assert read_grep["session_count"] == 3


def test_mine_ngrams_trigram(traj_a, traj_b, traj_c):
    all_session_turns = [
        extract_turns(traj_a),
        extract_turns(traj_b),
        extract_turns(traj_c),
    ]
    patterns = mine_ngrams(all_session_turns, n=3)
    rge = next(
        p for p in patterns
        if p["sequence"] == ["mcp__mkr__Read", "Grep", "mcp__mkr__Edit"]
    )
    assert rge["frequency"] == 3
    assert rge["family"] == "tool_sequence"


def test_mine_ngrams_co_indexes_keywords(traj_a, traj_b, traj_c):
    all_session_turns = [
        extract_turns(traj_a),
        extract_turns(traj_b),
        extract_turns(traj_c),
    ]
    patterns = mine_ngrams(all_session_turns, n=3)
    rge = next(p for p in patterns if p["sequence"] == ["mcp__mkr__Read", "Grep", "mcp__mkr__Edit"])
    assert "fix" in rge["keywords"]
    assert "bug" in rge["keywords"]
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd traj-evolver && python -m pytest tests/test_miner.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'traj_miner'`

- [ ] **Step 3: Implement data loading + n-gram mining in `traj-evolver/scripts/traj_miner.py`**

```python
#!/usr/bin/env python3
"""Stage 1: deterministic pattern mining from .traj files."""

import argparse
import json
import re
import yaml
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


CORRECTION_KEYWORDS = {"不对", "wrong", "revert", "undo", "应该", "actually"}


# ── Data loading ──────────────────────────────────────────────────────────────

def load_traj_files(input_dir: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(input_dir.glob("*.traj"))]


def extract_turns(traj: dict) -> list[dict]:
    """Return list of {user_content, steps, session_id, turn_id}."""
    turns = []
    session_id = traj.get("conversation_id", "")
    pending_user = ""
    for msg in traj.get("messages", []):
        if msg.get("role") == "user":
            pending_user = msg.get("content", "")
        elif "agent_run_id" in msg:
            turns.append({
                "user_content": pending_user,
                "steps": msg.get("steps", []),
                "session_id": session_id,
                "turn_id": msg.get("turn_id"),
            })
            pending_user = ""
    return turns


def tool_names(steps: list[dict]) -> list[str]:
    return [s["action"]["tool_name"] for s in steps if s.get("action", {}).get("tool_name")]


def extract_keywords(text: str) -> list[str]:
    """Lowercase word tokens, length >= 2, de-duped."""
    return list(set(re.findall(r"[\w\u4e00-\u9fff]{2,}", text.lower())))


# ── Pattern family 1: tool-sequence n-grams ──────────────────────────────────

def mine_ngrams(all_session_turns: list[list[dict]], n: int) -> list[dict]:
    """Mine n-gram patterns from multiple sessions.

    all_session_turns: one list[dict] per session (output of extract_turns).
    Returns list of pattern dicts.
    """
    # freq[ngram] = total count; sessions[ngram] = set of session_ids
    # keywords[ngram] = Counter of keywords co-occurring with this ngram
    freq: Counter = Counter()
    sessions: dict[tuple, set] = defaultdict(set)
    keywords: dict[tuple, Counter] = defaultdict(Counter)
    examples: dict[tuple, list] = defaultdict(list)

    for session_turns in all_session_turns:
        for turn in session_turns:
            tools = tool_names(turn["steps"])
            kws = extract_keywords(turn["user_content"])
            for i in range(len(tools) - n + 1):
                ngram = tuple(tools[i : i + n])
                freq[ngram] += 1
                sessions[ngram].add(turn["session_id"])
                keywords[ngram].update(kws)
                if len(examples[ngram]) < 3:
                    examples[ngram].append({
                        "session": turn["session_id"],
                        "turn": turn["turn_id"],
                        "step_range": [i + 1, i + n],
                    })

    patterns = []
    for ngram, count in freq.items():
        top_kws = [kw for kw, _ in keywords[ngram].most_common(5)]
        ngram_id = "ngram_" + "_".join(
            t.replace("mcp__mkr__", "").replace("mcp__sce-urhox__", "sce_").lower()
            for t in ngram
        )
        patterns.append({
            "id": ngram_id[:60],
            "family": "tool_sequence",
            "sequence": list(ngram),
            "frequency": count,
            "session_count": len(sessions[ngram]),
            "distinctness": 1.0,  # updated by caller when compare data available
            "keywords": top_kws,
            "examples": examples[ngram],
        })
    return patterns
```

- [ ] **Step 4: Run tests — n-gram tests should pass**

```bash
cd traj-evolver && python -m pytest tests/test_miner.py -v -k "ngram or extract or tool_names"
```

Expected: all 5 n-gram/extract tests PASS.

- [ ] **Step 5: Commit**

```bash
git add traj-evolver/scripts/traj_miner.py traj-evolver/tests/test_miner.py
git commit -m "feat(traj-evolver): traj_miner data loading + n-gram mining"
```

---

## Task 3: traj_miner.py — Phase Transitions + Task Shapes

**Files:**
- Modify: `traj-evolver/scripts/traj_miner.py`
- Modify: `traj-evolver/tests/test_miner.py`

- [ ] **Step 1: Add failing tests for phase transitions and task shapes**

Append to `traj-evolver/tests/test_miner.py`:

```python
from traj_miner import mine_phase_transitions, mine_task_shapes


def test_mine_phase_transitions_detects_localization_to_editing(traj_a, traj_b, traj_c):
    all_turns = [
        extract_turns(traj_a),
        extract_turns(traj_b),
        extract_turns(traj_c),
    ]
    patterns = mine_phase_transitions(all_turns)
    loc_edit = next(
        p for p in patterns
        if p["sequence"] == ["localization", "editing"]
    )
    assert loc_edit["frequency"] >= 3
    assert loc_edit["family"] == "phase_transition"
    assert loc_edit["session_count"] >= 3


def test_mine_phase_transitions_no_self_transitions(traj_a):
    all_turns = [extract_turns(traj_a)]
    patterns = mine_phase_transitions(all_turns)
    for p in patterns:
        seq = p["sequence"]
        assert seq[0] != seq[1], "Self-transitions must be excluded"


def test_mine_task_shapes_clusters_similar_turns(traj_a, traj_b, traj_c):
    all_turns = [
        extract_turns(traj_a),
        extract_turns(traj_b),
        extract_turns(traj_c),
    ]
    patterns = mine_task_shapes(all_turns)
    # All three sessions have turn 1 with {Read, Grep, Edit} tools + "fix"/"bug" keywords
    # They should cluster together (min_size=3 → exactly 1 cluster)
    assert len(patterns) >= 1
    cluster = patterns[0]
    assert cluster["family"] == "task_shape"
    assert cluster["size"] >= 3
    assert "fix" in cluster["keywords"] or "bug" in cluster["keywords"]


def test_mine_task_shapes_min_cluster_size_3(traj_a, traj_b):
    # Only 2 sessions → no cluster of size >= 3
    all_turns = [extract_turns(traj_a), extract_turns(traj_b)]
    patterns = mine_task_shapes(all_turns)
    assert all(p["size"] >= 3 for p in patterns)
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd traj-evolver && python -m pytest tests/test_miner.py -v -k "phase or shape" 2>&1 | head -15
```

Expected: `ImportError` or `AttributeError` — functions not yet defined.

- [ ] **Step 3: Implement phase transitions in `traj_miner.py`**

Add after the n-gram section:

```python
# ── Pattern family 2: phase-transition patterns ───────────────────────────────

def mine_phase_transitions(all_session_turns: list[list[dict]]) -> list[dict]:
    freq: Counter = Counter()
    sessions: dict[tuple, set] = defaultdict(set)
    examples: dict[tuple, list] = defaultdict(list)

    for session_turns in all_session_turns:
        for turn in session_turns:
            phases = [s.get("phase") for s in turn["steps"] if s.get("phase")]
            for i in range(len(phases) - 1):
                if phases[i] != phases[i + 1]:
                    pair = (phases[i], phases[i + 1])
                    freq[pair] += 1
                    sessions[pair].add(turn["session_id"])
                    if len(examples[pair]) < 3:
                        examples[pair].append({
                            "session": turn["session_id"],
                            "turn": turn["turn_id"],
                            "step": i + 1,
                        })

    return [
        {
            "id": f"phase_{a}_to_{b}",
            "family": "phase_transition",
            "sequence": [a, b],
            "frequency": count,
            "session_count": len(sessions[(a, b)]),
            "distinctness": 1.0,
            "keywords": [],
            "examples": examples[(a, b)],
        }
        for (a, b), count in freq.items()
    ]
```

- [ ] **Step 4: Implement task shapes in `traj_miner.py`**

Add after phase transitions:

```python
# ── Pattern family 3: task-shape patterns ────────────────────────────────────

def _jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    return len(set_a & set_b) / len(union) if union else 0.0


def mine_task_shapes(all_session_turns: list[list[dict]], threshold: float = 0.5, min_size: int = 3) -> list[dict]:
    """Cluster turns by Jaccard similarity of tool sets + keyword overlap."""
    # Represent each turn as a shape
    shapes = []
    for session_turns in all_session_turns:
        for turn in session_turns:
            tools = set(tool_names(turn["steps"]))
            kws = set(extract_keywords(turn["user_content"]))
            if not tools:
                continue
            shapes.append({
                "tools": tools,
                "keywords": kws,
                "session_id": turn["session_id"],
                "turn_id": turn["turn_id"],
            })

    # Greedy clustering: assign each shape to first compatible cluster
    clusters: list[list[dict]] = []
    for shape in shapes:
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            tool_sim = _jaccard(shape["tools"], rep["tools"])
            kw_sim = _jaccard(shape["keywords"], rep["keywords"])
            if (tool_sim + kw_sim) / 2 >= threshold:
                cluster.append(shape)
                placed = True
                break
        if not placed:
            clusters.append([shape])

    patterns = []
    for i, cluster in enumerate(clusters):
        if len(cluster) < min_size:
            continue
        all_tools = set()
        all_kws: Counter = Counter()
        for s in cluster:
            all_tools |= s["tools"]
            all_kws.update(s["keywords"])
        cluster_id = "shape_" + "_".join(sorted(all_tools)[:3]).replace("mcp__mkr__", "").lower()
        patterns.append({
            "id": cluster_id[:60],
            "family": "task_shape",
            "tools": sorted(all_tools),
            "size": len(cluster),
            "session_count": len({s["session_id"] for s in cluster}),
            "frequency": len(cluster),
            "distinctness": 1.0,
            "keywords": [kw for kw, _ in all_kws.most_common(5)],
            "examples": [
                {"session": s["session_id"], "turn": s["turn_id"]}
                for s in cluster[:3]
            ],
        })
    return patterns
```

- [ ] **Step 5: Run all miner tests so far**

```bash
cd traj-evolver && python -m pytest tests/test_miner.py -v
```

Expected: all tests PASS (including n-gram tests from Task 2).

- [ ] **Step 6: Commit**

```bash
git add traj-evolver/scripts/traj_miner.py traj-evolver/tests/test_miner.py
git commit -m "feat(traj-evolver): phase transition + task shape mining"
```

---

## Task 4: traj_miner.py — Corrections + Fingerprints + Selection + CLI

**Files:**
- Modify: `traj-evolver/scripts/traj_miner.py`
- Modify: `traj-evolver/tests/test_miner.py`

- [ ] **Step 1: Add failing tests for corrections, fingerprints, and selection**

Append to `traj-evolver/tests/test_miner.py`:

```python
from traj_miner import mine_corrections, mine_tool_fingerprints, apply_selection, run_miner


def test_mine_corrections_detects_revert_pattern(traj_a):
    # traj_a: turn1=Edit(game.lua), turn2=user:"wrong,revert", turn3=Edit(game.lua)
    all_turns = [extract_turns(traj_a)]
    patterns = mine_corrections(all_turns)
    assert len(patterns) >= 1
    corr = patterns[0]
    assert corr["family"] == "correction_signal"
    assert "game.lua" in corr["file"]
    assert corr["frequency"] >= 1


def test_mine_corrections_no_false_positive(traj_b):
    # traj_b has no correction keyword in user messages
    all_turns = [extract_turns(traj_b)]
    patterns = mine_corrections(all_turns)
    assert patterns == []


def test_mine_tool_fingerprints_wzp_specific(traj_a, traj_b):
    # mcp__sce-urhox__build appears in wzp sessions but not other_project_turns=[]
    wzp_turns = [extract_turns(traj_a), extract_turns(traj_b)]
    other_turns = []
    patterns = mine_tool_fingerprints(wzp_turns, other_turns)
    sce_build = next(
        (p for p in patterns if "sce-urhox__build" in p["id"]),
        None,
    )
    assert sce_build is not None
    assert sce_build["distinctness"] == 1.0  # 0 in other project


def test_mine_tool_fingerprints_distinctness_ratio(traj_b):
    # Simulate a tool that appears 4× in wzp and 2× in other → distinctness=4/(4+2)=0.67
    other_turns = [
        [{"user_content": "", "session_id": "other-1", "turn_id": 1,
          "steps": [{"action": {"tool_name": "mcp__sce-urhox__build"}, "phase": "verification"}] * 2}]
    ]
    wzp_turns = [extract_turns(traj_b)]  # has 1 build call
    patterns = mine_tool_fingerprints(wzp_turns, other_turns)
    sce = next(p for p in patterns if "sce-urhox__build" in p["id"])
    # wzp=1, other=2 → distinctness=1/(1+2)=0.33 (approximately)
    assert 0.2 < sce["distinctness"] < 0.5


def test_apply_selection_drops_below_min_frequency():
    patterns = [
        {"id": "a", "family": "tool_sequence", "frequency": 2, "session_count": 2, "distinctness": 0.9, "keywords": []},
        {"id": "b", "family": "tool_sequence", "frequency": 5, "session_count": 3, "distinctness": 0.7, "keywords": []},
    ]
    config = {"min_frequency": 3, "top_k_per_family": 20, "distinctness_weight": 0.5, "min_sessions": 2}
    result = apply_selection(patterns, config)
    assert all(p["frequency"] >= 3 for p in result)
    assert not any(p["id"] == "a" for p in result)


def test_apply_selection_top_k_per_family():
    patterns = [
        {"id": f"p{i}", "family": "tool_sequence", "frequency": 10 - i,
         "session_count": 3, "distinctness": 0.5, "keywords": []}
        for i in range(25)
    ]
    config = {"min_frequency": 1, "top_k_per_family": 5, "distinctness_weight": 0.5, "min_sessions": 1}
    result = apply_selection(patterns, config)
    assert len(result) <= 5


def test_run_miner_end_to_end(tmp_path, traj_a, traj_b, traj_c):
    import json
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    for name, traj in [("a.traj", traj_a), ("b.traj", traj_b), ("c.traj", traj_c)]:
        (input_dir / name).write_text(json.dumps(traj))

    config = {"min_frequency": 3, "top_k_per_family": 20, "distinctness_weight": 0.5, "min_sessions": 2}
    result = run_miner(input_dir, output_dir, config, project="wzp")

    assert result["stats"]["sessions"] == 3
    assert len(result["patterns"]) > 0
    patterns_file = output_dir / "patterns.json"
    assert patterns_file.exists()
    data = json.loads(patterns_file.read_text())
    assert data["project"] == "wzp"
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd traj-evolver && python -m pytest tests/test_miner.py -v -k "correction or fingerprint or selection or end_to_end" 2>&1 | head -20
```

Expected: `ImportError` for `mine_corrections`, `mine_tool_fingerprints`, `apply_selection`, `run_miner`.

- [ ] **Step 3: Implement correction signal mining in `traj_miner.py`**

Add after task shapes:

```python
# ── Pattern family 4: user-correction signals ─────────────────────────────────

def _edited_files(steps: list[dict]) -> set[str]:
    files = set()
    for step in steps:
        tool = step.get("action", {}).get("tool_name", "")
        if "Edit" in tool or "Write" in tool:
            fp = step.get("action", {}).get("args", {}).get("file_path", "")
            if fp:
                files.add(fp)
    return files


def mine_corrections(all_session_turns: list[list[dict]]) -> list[dict]:
    found: dict[str, dict] = {}  # file → pattern dict

    for session_turns in all_session_turns:
        for i in range(len(session_turns) - 2):
            turn_n, turn_n1, turn_n2 = session_turns[i], session_turns[i + 1], session_turns[i + 2]
            edited = _edited_files(turn_n["steps"])
            if not edited:
                continue
            kws = set(extract_keywords(turn_n1["user_content"]))
            if not kws & CORRECTION_KEYWORDS:
                continue
            re_edited = _edited_files(turn_n2["steps"])
            overlap = edited & re_edited
            if not overlap:
                continue
            for file in overlap:
                if file not in found:
                    found[file] = {
                        "id": f"correction_{file.replace('/', '_').replace('.', '_')}",
                        "family": "correction_signal",
                        "file": file,
                        "frequency": 0,
                        "session_count": 0,
                        "distinctness": 1.0,
                        "keywords": list(kws & CORRECTION_KEYWORDS),
                        "examples": [],
                    }
                found[file]["frequency"] += 1
                found[file]["session_count"] += 1
                if len(found[file]["examples"]) < 3:
                    found[file]["examples"].append({
                        "session": turn_n["session_id"],
                        "turn": turn_n["turn_id"],
                    })
    return list(found.values())
```

- [ ] **Step 4: Implement tool fingerprints in `traj_miner.py`**

Add after corrections:

```python
# ── Pattern family 5: project-specific tool fingerprints ─────────────────────

def mine_tool_fingerprints(
    this_project_turns: list[list[dict]],
    other_project_turns: list[list[dict]],
) -> list[dict]:
    this_freq: Counter = Counter()
    other_freq: Counter = Counter()

    for session_turns in this_project_turns:
        for turn in session_turns:
            for tool in tool_names(turn["steps"]):
                if tool.startswith("mcp__"):
                    this_freq[tool] += 1

    for session_turns in other_project_turns:
        for turn in session_turns:
            for tool in tool_names(turn["steps"]):
                if tool.startswith("mcp__"):
                    other_freq[tool] += 1

    patterns = []
    for tool, count in this_freq.items():
        other_count = other_freq.get(tool, 0)
        total = count + other_count
        distinctness = count / total if total > 0 else 1.0
        safe_name = tool.replace("mcp__", "").replace("__", "_").replace("-", "_")
        patterns.append({
            "id": f"fingerprint_{safe_name}"[:60],
            "family": "tool_fingerprint",
            "tool": tool,
            "frequency": count,
            "session_count": 1,  # approximation — refine if needed
            "distinctness": round(distinctness, 4),
            "keywords": [],
            "examples": [],
        })
    return patterns
```

- [ ] **Step 5: Implement `apply_selection` and `run_miner` in `traj_miner.py`**

Add after fingerprints:

```python
# ── Selection ─────────────────────────────────────────────────────────────────

def apply_selection(patterns: list[dict], config: dict) -> list[dict]:
    min_freq = config.get("min_frequency", 3)
    top_k = config.get("top_k_per_family", 20)
    dw = config.get("distinctness_weight", 0.5)
    min_sessions = config.get("min_sessions", 2)

    filtered = [
        p for p in patterns
        if p["frequency"] >= min_freq and p["session_count"] >= min_sessions
    ]

    # Score: blend normalized frequency with distinctness
    max_freq = max((p["frequency"] for p in filtered), default=1)
    for p in filtered:
        norm_freq = p["frequency"] / max_freq
        p["_score"] = (1 - dw) * norm_freq + dw * p["distinctness"]

    # Group by family, take top-k each
    by_family: dict[str, list] = defaultdict(list)
    for p in filtered:
        by_family[p["family"]].append(p)

    selected = []
    for family_patterns in by_family.values():
        family_patterns.sort(key=lambda x: x["_score"], reverse=True)
        selected.extend(family_patterns[:top_k])

    # Remove internal score key
    for p in selected:
        p.pop("_score", None)
    return selected


# ── CLI orchestration ─────────────────────────────────────────────────────────

def run_miner(
    input_dir: Path,
    output_dir: Path,
    config: dict,
    project: str = "unknown",
    compare_dir: Path | None = None,
) -> dict:
    trajs = load_traj_files(input_dir)
    all_session_turns = [extract_turns(t) for t in trajs]

    other_session_turns: list[list[dict]] = []
    if compare_dir and compare_dir.exists():
        other_trajs = load_traj_files(compare_dir)
        other_session_turns = [extract_turns(t) for t in other_trajs]

    total_steps = sum(
        len(turn["steps"])
        for session in all_session_turns
        for turn in session
    )
    total_tool_calls = sum(
        len(tool_names(turn["steps"]))
        for session in all_session_turns
        for turn in session
    )

    raw_patterns: list[dict] = []
    for n in (2, 3, 4):
        raw_patterns.extend(mine_ngrams(all_session_turns, n))
    raw_patterns.extend(mine_phase_transitions(all_session_turns))
    raw_patterns.extend(mine_task_shapes(all_session_turns))
    raw_patterns.extend(mine_corrections(all_session_turns))
    raw_patterns.extend(mine_tool_fingerprints(all_session_turns, other_session_turns))

    selected = apply_selection(raw_patterns, config)

    output = {
        "project": project,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "sessions": len(trajs),
            "steps": total_steps,
            "tool_calls": total_tool_calls,
        },
        "patterns": selected,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "patterns.json").write_text(json.dumps(output, indent=2, ensure_ascii=False))
    return output


def main():
    parser = argparse.ArgumentParser(description="Mine patterns from .traj files")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--project", default="unknown")
    parser.add_argument("--compare-dir", type=Path, default=None,
                        help="Other project dir for distinctness calculation")
    parser.add_argument("--config", type=Path, default=Path("traj-evolver/config.yaml"))
    args = parser.parse_args()

    config = {}
    if args.config.exists():
        with open(args.config) as f:
            data = yaml.safe_load(f)
        config = data.get("miner", {})

    result = run_miner(args.input_dir, args.output_dir, config,
                       project=args.project, compare_dir=args.compare_dir)
    print(f"Mined {len(result['patterns'])} patterns from {result['stats']['sessions']} sessions")
    print(f"Output: {args.output_dir / 'patterns.json'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run all miner tests**

```bash
cd traj-evolver && python -m pytest tests/test_miner.py -v
```

Expected: all tests PASS.

- [ ] **Step 7: Smoke-run the CLI against real wzp data**

```bash
cd /Users/xd/Desktop/work/project-logs
python3 traj-evolver/scripts/traj_miner.py \
  --input-dir traj-data-new/wzp \
  --output-dir traj-evolver/patterns/wzp \
  --project wzp \
  --compare-dir traj-data-new/zzj \
  --config traj-evolver/config.yaml
```

Expected: prints `Mined N patterns from 73 sessions`, file created at `traj-evolver/patterns/wzp/patterns.json`.

- [ ] **Step 8: Commit**

```bash
git add traj-evolver/scripts/traj_miner.py traj-evolver/tests/test_miner.py traj-evolver/patterns/
git commit -m "feat(traj-evolver): correction + fingerprint mining, selection, CLI"
```

---

## Task 5: traj_enricher.py — Provider Clients

**Files:**
- Create: `traj-evolver/scripts/traj_enricher.py`
- Create: `traj-evolver/tests/test_enricher.py` (provider section)

- [ ] **Step 1: Write failing provider client tests**

Create `traj-evolver/tests/test_enricher.py`:

```python
import sys, asyncio
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "scripts"))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from traj_enricher import QwenClient, AnthropicClient, build_client, EnricherConfig


@pytest.fixture
def qwen_config():
    return EnricherConfig(
        providers=[{
            "name": "qwen", "enabled": True,
            "api_key_env": "DASHSCOPE_API_KEY",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen3.6-plus",
            "extra_body": {"enable_thinking": False},
            "sdk": "openai",
        }],
        temperature=0, concurrency=5, max_retries=1, retry_backoff_sec=0,
    )


@pytest.fixture
def anthropic_config():
    return EnricherConfig(
        providers=[{
            "name": "anthropic", "enabled": True,
            "api_key_env": "ANTHROPIC_API_KEY",
            "model": "claude-sonnet-4-6",
            "sdk": "anthropic",
            "prompt_caching": True,
        }],
        temperature=0, concurrency=5, max_retries=1, retry_backoff_sec=0,
    )


def test_build_client_selects_qwen_first_when_both_available(qwen_config, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = build_client(qwen_config)
    assert isinstance(client, QwenClient)


def test_build_client_falls_back_to_anthropic(anthropic_config, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = build_client(anthropic_config)
    assert isinstance(client, AnthropicClient)


def test_build_client_raises_when_no_keys_available(qwen_config, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DASHSCOPE_API_KEY"):
        build_client(qwen_config)


def test_qwen_client_sends_enable_thinking_false(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="result text"))]

    captured = {}

    async def fake_create(**kwargs):
        captured["extra_body"] = kwargs.get("extra_body")
        return mock_response

    with patch("openai.AsyncOpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        mock_cls.return_value = mock_client

        client = QwenClient(
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen3.6-plus",
            extra_body={"enable_thinking": False},
            temperature=0,
        )
        result = asyncio.get_event_loop().run_until_complete(
            client.complete("sys", "user")
        )

    assert captured["extra_body"] == {"enable_thinking": False}
    assert result == "result text"


def test_anthropic_client_sets_cache_control(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    captured = {}

    async def fake_create(**kwargs):
        captured["system"] = kwargs.get("system")
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="instinct text")]
        return mock_msg

    with patch("anthropic.AsyncAnthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create = fake_create
        mock_cls.return_value = mock_client

        client = AnthropicClient(
            api_key="test-key",
            model="claude-sonnet-4-6",
            temperature=0,
        )
        asyncio.get_event_loop().run_until_complete(
            client.complete("cached prefix", "dynamic user part")
        )

    system_block = captured["system"]
    assert isinstance(system_block, list)
    cache_types = [b.get("cache_control", {}).get("type") for b in system_block]
    assert "ephemeral" in cache_types
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd traj-evolver && python -m pytest tests/test_enricher.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'traj_enricher'`

- [ ] **Step 3: Implement provider clients in `traj-evolver/scripts/traj_enricher.py`**

```python
#!/usr/bin/env python3
"""Stage 2: LLM enrichment — patterns → instinct .md files."""

import argparse
import asyncio
import json
import os
import re
import time
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class EnricherConfig:
    providers: list[dict] = field(default_factory=list)
    temperature: float = 0
    concurrency: int = 5
    max_retries: int = 3
    retry_backoff_sec: float = 2.0

    @classmethod
    def from_yaml(cls, path: Path) -> "EnricherConfig":
        with open(path) as f:
            data = yaml.safe_load(f)
        cfg = data.get("enricher", {})
        return cls(
            providers=cfg.get("providers", []),
            temperature=cfg.get("temperature", 0),
            concurrency=cfg.get("concurrency", 5),
            max_retries=cfg.get("max_retries", 3),
            retry_backoff_sec=cfg.get("retry_backoff_sec", 2.0),
        )


# ── Provider abstraction ──────────────────────────────────────────────────────

class EnricherClient:
    async def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class QwenClient(EnricherClient):
    def __init__(self, api_key: str, base_url: str, model: str,
                 extra_body: dict, temperature: float):
        import openai
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._extra_body = extra_body
        self._temperature = temperature

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            extra_body=self._extra_body,
        )
        return response.choices[0].message.content


class AnthropicClient(EnricherClient):
    def __init__(self, api_key: str, model: str, temperature: float):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._temperature = temperature

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=self._temperature,
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


def build_client(config: EnricherConfig, force_provider: Optional[str] = None) -> EnricherClient:
    providers = config.providers
    if force_provider:
        providers = [p for p in providers if p["name"] == force_provider]

    missing_keys = []
    for p in providers:
        if not p.get("enabled", True):
            continue
        key_env = p["api_key_env"]
        api_key = os.environ.get(key_env, "")
        if not api_key:
            missing_keys.append(key_env)
            continue
        if p["sdk"] == "openai":
            return QwenClient(
                api_key=api_key,
                base_url=p["base_url"],
                model=p["model"],
                extra_body=p.get("extra_body", {}),
                temperature=config.temperature,
            )
        elif p["sdk"] == "anthropic":
            return AnthropicClient(
                api_key=api_key,
                model=p["model"],
                temperature=config.temperature,
            )

    env_list = ", ".join(missing_keys) if missing_keys else "none configured"
    raise RuntimeError(
        f"No LLM provider available. Set one of: {env_list}"
    )
```

- [ ] **Step 4: Run provider tests**

```bash
cd traj-evolver && python -m pytest tests/test_enricher.py -v -k "client or provider or qwen or anthropic"
```

Expected: all 5 provider tests PASS.

- [ ] **Step 5: Commit**

```bash
git add traj-evolver/scripts/traj_enricher.py traj-evolver/tests/test_enricher.py
git commit -m "feat(traj-evolver): enricher provider clients (Qwen + Anthropic)"
```

---

## Task 6: traj_enricher.py — Prompt Construction + YAML Validation + Rejection

**Files:**
- Modify: `traj-evolver/scripts/traj_enricher.py`
- Modify: `traj-evolver/tests/test_enricher.py`

- [ ] **Step 1: Add failing tests for prompt construction and YAML validation**

Append to `traj-evolver/tests/test_enricher.py`:

```python
from traj_enricher import (
    build_system_prompt, build_user_prompt,
    validate_instinct, write_instinct, CONFIDENCE_TABLE,
)


SAMPLE_PATTERN = {
    "id": "ngram_read_grep_edit",
    "family": "tool_sequence",
    "sequence": ["mcp__mkr__Read", "Grep", "mcp__mkr__Edit"],
    "frequency": 47,
    "session_count": 23,
    "distinctness": 0.62,
    "keywords": ["fix", "bug"],
    "examples": [{"session": "aaaa", "turn": 3, "step_range": [1, 3]}],
}

VALID_INSTINCT = """---
id: wzp-read-grep-edit-debug-flow
trigger: "when fixing bugs in wzp lua scripts"
confidence: 0.75
domain: debugging
source: trajectory-import
scope: project
project_name: wzp-脑力大冒险
evolved_from_pattern: ngram_read_grep_edit
---

# Read → Grep → Edit Debug Flow

## Action
Start bug investigation by reading the reported file, then grep for related symbols before editing.

## Evidence
- Pattern occurred 47 times across 23 sessions
- Consistently precedes successful edits when user message contains fix or bug
"""


def test_build_system_prompt_contains_schema_docs():
    prompt_prefix = "# Project overview\nThis is wzp."
    system = build_system_prompt(prompt_prefix)
    assert "wzp" in system
    assert "trigger" in system
    assert "confidence" in system


def test_build_user_prompt_contains_pattern_json():
    traj_examples = [{"session": "aaaa", "content": "fix the bug → Read → Grep → Edit"}]
    user = build_user_prompt(SAMPLE_PATTERN, traj_examples, project_name="wzp-脑力大冒险")
    assert "ngram_read_grep_edit" in user
    assert "wzp-脑力大冒险" in user
    assert "fix the bug" in user


def test_validate_instinct_passes_valid():
    errors = validate_instinct(VALID_INSTINCT)
    assert errors == []


def test_validate_instinct_fails_missing_id():
    bad = VALID_INSTINCT.replace("id: wzp-read-grep-edit-debug-flow\n", "")
    errors = validate_instinct(bad)
    assert any("id" in e for e in errors)


def test_validate_instinct_fails_bad_id_format():
    bad = VALID_INSTINCT.replace("id: wzp-read-grep-edit-debug-flow", "id: INVALID ID!")
    errors = validate_instinct(bad)
    assert any("id" in e.lower() for e in errors)


def test_validate_instinct_fails_id_too_long():
    long_id = "a" * 61
    bad = VALID_INSTINCT.replace("id: wzp-read-grep-edit-debug-flow", f"id: {long_id}")
    errors = validate_instinct(bad)
    assert any("60" in e or "id" in e.lower() for e in errors)


def test_validate_instinct_fails_missing_evidence_bullets():
    bad = VALID_INSTINCT.replace("- Pattern occurred 47 times across 23 sessions\n", "")
    bad = bad.replace("- Consistently precedes successful edits when user message contains fix or bug\n", "")
    errors = validate_instinct(bad)
    assert any("evidence" in e.lower() or "bullet" in e.lower() for e in errors)


def test_confidence_table_maps_frequency():
    assert CONFIDENCE_TABLE(20) == 0.85
    assert CONFIDENCE_TABLE(15) == 0.75
    assert CONFIDENCE_TABLE(7) == 0.65
    assert CONFIDENCE_TABLE(3) == 0.55


def test_write_instinct_rejects_to_rejected_dir(tmp_path):
    invalid = "not yaml frontmatter at all"
    rejected_dir = tmp_path / "_rejected"
    write_instinct(invalid, "bad_pattern", tmp_path, rejected_dir, errors=["no frontmatter"])
    assert (rejected_dir / "bad_pattern.md").exists()
    assert not (tmp_path / "bad_pattern.md").exists()
    error_log = rejected_dir / "error_log.txt"
    assert error_log.exists()
    assert "bad_pattern" in error_log.read_text()


def test_write_instinct_writes_valid(tmp_path):
    rejected_dir = tmp_path / "_rejected"
    write_instinct(VALID_INSTINCT, "ngram_read_grep_edit", tmp_path, rejected_dir, errors=[])
    out_file = tmp_path / "ngram_read_grep_edit.md"
    assert out_file.exists()
    assert not (rejected_dir / "ngram_read_grep_edit.md").exists()
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd traj-evolver && python -m pytest tests/test_enricher.py -v -k "prompt or validate or confidence or write_instinct" 2>&1 | head -20
```

Expected: `ImportError` for `build_system_prompt`, `validate_instinct`, etc.

- [ ] **Step 3: Add prompt construction + validation to `traj_enricher.py`**

Append to `traj-evolver/scripts/traj_enricher.py`:

```python
# ── Confidence calibration ────────────────────────────────────────────────────

def CONFIDENCE_TABLE(frequency: int) -> float:
    if frequency >= 20:
        return 0.85
    if frequency >= 10:
        return 0.75
    if frequency >= 5:
        return 0.65
    return 0.55


# ── Prompt construction ───────────────────────────────────────────────────────

INSTINCT_SCHEMA_DOCS = """
## Instinct YAML Frontmatter Schema

Required fields:
- id: lowercase alphanumeric + hyphens, max 60 chars
- trigger: one-sentence description of when this instinct applies (quoted string)
- confidence: float 0.0–1.0 (will be set by pipeline — include a placeholder)
- domain: one of: debugging, editing, localization, verification, workflow, platform
- source: trajectory-import
- scope: project

Optional fields:
- project_name: human-readable project name
- evolved_from_pattern: source pattern id

## Sections

### Action
1–2 sentences describing what to do when the trigger fires.

### Evidence
Minimum 2 bullet points with quantitative evidence from the trajectory data.

## Example

---
id: wzp-read-grep-edit-debug-flow
trigger: "when fixing bugs in wzp lua scripts"
confidence: 0.75
domain: debugging
source: trajectory-import
scope: project
project_name: wzp-脑力大冒険
evolved_from_pattern: ngram_read_grep_edit
---

# Read → Grep → Edit Debug Flow

## Action
Start by reading the affected file, grep for related symbols, then edit.

## Evidence
- Appeared 47 times across 23 sessions
- Co-occurs with "fix" and "bug" keywords in the preceding user message
"""


def build_system_prompt(prompt_prefix: str) -> str:
    return prompt_prefix + "\n\n" + INSTINCT_SCHEMA_DOCS


def build_user_prompt(pattern: dict, traj_examples: list[dict], project_name: str) -> str:
    parts = [
        f"Project: {project_name}",
        f"\nPattern JSON:\n```json\n{json.dumps(pattern, indent=2, ensure_ascii=False)}\n```",
    ]
    if traj_examples:
        parts.append("\nConversation examples (truncated to 500 chars each):")
        for ex in traj_examples[:3]:
            content = str(ex.get("content", ""))[:500]
            parts.append(f"  - Session {ex.get('session', '?')}: {content}")
    parts.append(
        "\nEmit a single YAML-frontmatter instinct document. "
        "Do not add any text before or after the document."
    )
    return "\n".join(parts)


# ── YAML validation ───────────────────────────────────────────────────────────

REQUIRED_FIELDS = {"id", "trigger", "confidence", "domain", "scope"}
ID_PATTERN = re.compile(r"^[a-z0-9-]+$")


def validate_instinct(text: str) -> list[str]:
    errors = []

    # Must have YAML frontmatter
    if not text.strip().startswith("---"):
        errors.append("Missing YAML frontmatter (must start with ---)")
        return errors

    try:
        parts = text.split("---", 2)
        if len(parts) < 3:
            errors.append("Malformed frontmatter: missing closing ---")
            return errors
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return errors

    if not isinstance(fm, dict):
        errors.append("Frontmatter is not a YAML mapping")
        return errors

    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"Missing required field: {field}")

    instinct_id = str(fm.get("id", ""))
    if instinct_id:
        if not ID_PATTERN.match(instinct_id):
            errors.append(f"id '{instinct_id}' must match ^[a-z0-9-]+$")
        if len(instinct_id) > 60:
            errors.append(f"id exceeds 60 chars (got {len(instinct_id)})")

    body = parts[2] if len(parts) >= 3 else ""
    bullets = re.findall(r"^\s*-\s+.+", body, re.MULTILINE)
    if len(bullets) < 2:
        errors.append("Evidence section must have >= 2 bullet points")

    return errors


# ── Write / reject ────────────────────────────────────────────────────────────

def write_instinct(
    text: str,
    pattern_id: str,
    output_dir: Path,
    rejected_dir: Path,
    errors: list[str],
) -> None:
    if errors:
        rejected_dir.mkdir(parents=True, exist_ok=True)
        (rejected_dir / f"{pattern_id}.md").write_text(text, encoding="utf-8")
        error_log = rejected_dir / "error_log.txt"
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"\n=== {pattern_id} ===\n")
            for e in errors:
                f.write(f"  {e}\n")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{pattern_id}.md").write_text(text, encoding="utf-8")
```

- [ ] **Step 4: Run validation tests**

```bash
cd traj-evolver && python -m pytest tests/test_enricher.py -v -k "prompt or validate or confidence or write"
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add traj-evolver/scripts/traj_enricher.py traj-evolver/tests/test_enricher.py
git commit -m "feat(traj-evolver): prompt construction, YAML validation, rejection path"
```

---

## Task 7: traj_enricher.py — Async Orchestration + CLI

**Files:**
- Modify: `traj-evolver/scripts/traj_enricher.py`
- Modify: `traj-evolver/tests/test_enricher.py`

- [ ] **Step 1: Add failing tests for the full enricher orchestration**

Append to `traj-evolver/tests/test_enricher.py`:

```python
from traj_enricher import enrich_patterns, load_traj_examples


def test_load_traj_examples_returns_truncated_content(tmp_path):
    import json
    traj = {
        "conversation_id": "aaaa",
        "messages": [
            {"turn_id": 1, "role": "user", "content": "fix the bug", "timestamp": "2026-01-01T00:00:00Z"},
            {"turn_id": 1, "agent_run_id": "run_t1",
             "steps": [{"step_id": 1, "phase": "editing",
                        "action": {"tool_name": "mcp__mkr__Read", "tool_use_id": "x", "args": {}},
                        "observation": {"type": "tool_result", "text": "A" * 600, "exit_code": None},
                        "status": "ok"}],
             "run_summary": {}},
        ],
    }
    (tmp_path / "a.traj").write_text(json.dumps(traj))
    examples = load_traj_examples(
        pattern={"examples": [{"session": "aaaa", "turn": 1}]},
        traj_dir=tmp_path,
    )
    assert len(examples) == 1
    assert len(examples[0]["content"]) <= 520  # truncated to ~500 chars


def test_enrich_patterns_processes_all_patterns(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")

    patterns = [
        {**SAMPLE_PATTERN, "id": f"pattern_{i}", "frequency": 5 + i}
        for i in range(3)
    ]
    output_dir = tmp_path / "instincts"
    rejected_dir = output_dir / "_rejected"

    call_count = 0

    async def fake_complete(system, user):
        nonlocal call_count
        call_count += 1
        pid = f"pattern_{call_count - 1}"
        return VALID_INSTINCT.replace("ngram_read_grep_edit", pid).replace(
            "id: wzp-read-grep-edit-debug-flow",
            f"id: wzp-{pid}-flow",
        )

    client = MagicMock()
    client.complete = fake_complete

    with patch("traj_enricher.build_client", return_value=client):
        asyncio.get_event_loop().run_until_complete(
            enrich_patterns(
                patterns=patterns,
                traj_dir=tmp_path,
                output_dir=output_dir,
                rejected_dir=rejected_dir,
                prompt_prefix="# wzp project",
                project_name="wzp-脑力大冒险",
                client=client,
                concurrency=2,
                max_retries=1,
                retry_backoff_sec=0,
            )
        )

    assert call_count == 3
    md_files = list(output_dir.glob("*.md"))
    assert len(md_files) == 3


def test_enrich_patterns_retries_on_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    call_count = 0

    async def flaky_complete(system, user):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("transient error")
        return VALID_INSTINCT

    client = MagicMock()
    client.complete = flaky_complete

    asyncio.get_event_loop().run_until_complete(
        enrich_patterns(
            patterns=[SAMPLE_PATTERN],
            traj_dir=tmp_path,
            output_dir=tmp_path / "out",
            rejected_dir=tmp_path / "rejected",
            prompt_prefix="# prefix",
            project_name="wzp-脑力大冒险",
            client=client,
            concurrency=1,
            max_retries=3,
            retry_backoff_sec=0,
        )
    )
    assert call_count == 2  # failed once, succeeded on retry
    assert (tmp_path / "out" / "ngram_read_grep_edit.md").exists()
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd traj-evolver && python -m pytest tests/test_enricher.py -v -k "enrich or load_traj" 2>&1 | head -15
```

Expected: `ImportError` for `enrich_patterns`, `load_traj_examples`.

- [ ] **Step 3: Implement orchestration in `traj_enricher.py`**

Append to `traj-evolver/scripts/traj_enricher.py`:

```python
# ── Traj example extraction ───────────────────────────────────────────────────

def load_traj_examples(pattern: dict, traj_dir: Path) -> list[dict]:
    """Pull up to 3 conversation snippets matching pattern examples."""
    results = []
    seen = {}
    for ex in pattern.get("examples", [])[:3]:
        session_id = ex.get("session", "")
        if session_id in seen:
            traj_data = seen[session_id]
        else:
            matches = list(traj_dir.glob("*.traj"))
            traj_data = None
            for path in matches:
                raw = json.loads(path.read_text())
                if raw.get("conversation_id", "") == session_id or path.stem == session_id[:8]:
                    traj_data = raw
                    break
            seen[session_id] = traj_data

        if not traj_data:
            continue

        turn_id = ex.get("turn")
        snippet = f"Session {session_id[:8]}"
        for msg in traj_data.get("messages", []):
            if msg.get("role") == "user" and msg.get("turn_id") == turn_id:
                snippet += f": {msg.get('content', '')[:500]}"
                break
        results.append({"session": session_id[:8], "content": snippet[:520]})
    return results


# ── Async orchestration ───────────────────────────────────────────────────────

async def _process_one(
    pattern: dict,
    traj_dir: Path,
    output_dir: Path,
    rejected_dir: Path,
    prompt_prefix: str,
    project_name: str,
    client: EnricherClient,
    max_retries: int,
    retry_backoff_sec: float,
    semaphore: asyncio.Semaphore,
) -> None:
    pattern_id = pattern["id"]
    system = build_system_prompt(prompt_prefix)
    traj_examples = load_traj_examples(pattern, traj_dir)
    user = build_user_prompt(pattern, traj_examples, project_name)

    text = ""
    last_exc = None
    async with semaphore:
        for attempt in range(max_retries):
            try:
                text = await client.complete(system, user)
                break
            except Exception as e:
                last_exc = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_backoff_sec * (attempt + 1))
        else:
            write_instinct("", pattern_id, output_dir, rejected_dir,
                           errors=[f"LLM call failed after {max_retries} retries: {last_exc}"])
            return

    # Inject deterministic confidence
    confidence = CONFIDENCE_TABLE(pattern.get("frequency", 0))
    text = re.sub(r"(confidence:\s*)[\d.]+", f"confidence: {confidence}", text)

    errors = validate_instinct(text)
    write_instinct(text, pattern_id, output_dir, rejected_dir, errors=errors)


async def enrich_patterns(
    patterns: list[dict],
    traj_dir: Path,
    output_dir: Path,
    rejected_dir: Path,
    prompt_prefix: str,
    project_name: str,
    client: EnricherClient,
    concurrency: int,
    max_retries: int,
    retry_backoff_sec: float,
) -> None:
    sem = asyncio.Semaphore(concurrency)
    tasks = [
        _process_one(
            pattern=p,
            traj_dir=traj_dir,
            output_dir=output_dir,
            rejected_dir=rejected_dir,
            prompt_prefix=prompt_prefix,
            project_name=project_name,
            client=client,
            max_retries=max_retries,
            retry_backoff_sec=retry_backoff_sec,
            semaphore=sem,
        )
        for p in patterns
    ]
    await asyncio.gather(*tasks)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Enrich patterns with LLM")
    parser.add_argument("--patterns-file", required=True, type=Path)
    parser.add_argument("--traj-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=Path("traj-evolver/config.yaml"))
    parser.add_argument("--provider", default=None, help="Force specific provider (qwen|anthropic)")
    args = parser.parse_args()

    cfg = EnricherConfig.from_yaml(args.config)
    client = build_client(cfg, force_provider=args.provider)

    data = json.loads(args.patterns_file.read_text())
    patterns = data["patterns"]
    project_name = data.get("project", "unknown")

    prompt_prefix_path = Path("traj-evolver/prompts/enrich.md")
    prompt_prefix = prompt_prefix_path.read_text() if prompt_prefix_path.exists() else ""

    output_dir = args.output_dir
    rejected_dir = output_dir / "_rejected"

    print(f"Enriching {len(patterns)} patterns for project '{project_name}'")
    print(f"Provider: {client.__class__.__name__}")

    asyncio.run(enrich_patterns(
        patterns=patterns,
        traj_dir=args.traj_dir,
        output_dir=output_dir,
        rejected_dir=rejected_dir,
        prompt_prefix=prompt_prefix,
        project_name=project_name,
        client=client,
        concurrency=cfg.concurrency,
        max_retries=cfg.max_retries,
        retry_backoff_sec=cfg.retry_backoff_sec,
    ))

    accepted = len(list(output_dir.glob("*.md")))
    rejected = len(list(rejected_dir.glob("*.md"))) if rejected_dir.exists() else 0
    print(f"Done: {accepted} accepted, {rejected} rejected")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all enricher tests**

```bash
cd traj-evolver && python -m pytest tests/test_enricher.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add traj-evolver/scripts/traj_enricher.py traj-evolver/tests/test_enricher.py
git commit -m "feat(traj-evolver): enricher async orchestration + CLI"
```

---

## Task 8: evolve_skills.py — Staging + Invocation + Copy

**Files:**
- Create: `traj-evolver/scripts/evolve_skills.py`
- Create: `traj-evolver/tests/test_evolve.py`

- [ ] **Step 1: Write failing tests**

Create `traj-evolver/tests/test_evolve.py`:

```python
import sys, json, shutil
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "scripts"))

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from evolve_skills import stage_instincts, copy_evolved_output, run_evolve


SAMPLE_INSTINCT = """---
id: wzp-read-grep-edit-debug-flow
trigger: "when fixing bugs in wzp lua scripts"
confidence: 0.75
domain: debugging
source: trajectory-import
scope: project
project_name: wzp-脑力大冒険
---

# Read → Grep → Edit Debug Flow

## Action
Start by reading the affected file.

## Evidence
- Appeared 47 times
- Co-occurs with fix keywords
"""


def _make_instincts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "instincts"
    d.mkdir()
    (d / "pattern_a.md").write_text(SAMPLE_INSTINCT)
    (d / "pattern_b.md").write_text(SAMPLE_INSTINCT.replace("debug-flow", "grep-flow"))
    (d / "pattern_c.md").write_text(SAMPLE_INSTINCT.replace("debug-flow", "edit-flow"))
    return d


def test_stage_instincts_creates_inherited_dir(tmp_path):
    instincts_dir = _make_instincts_dir(tmp_path)
    project_dir = tmp_path / "homunculus" / "projects" / "test-project-id"

    stage_instincts(instincts_dir, project_dir)

    inherited = project_dir / "instincts" / "inherited"
    assert inherited.exists()
    md_files = list(inherited.glob("*.md"))
    assert len(md_files) == 3


def test_stage_instincts_skips_rejected(tmp_path):
    instincts_dir = _make_instincts_dir(tmp_path)
    rejected = instincts_dir / "_rejected"
    rejected.mkdir()
    (rejected / "bad.md").write_text("bad instinct")

    project_dir = tmp_path / "homunculus" / "projects" / "test-id"
    stage_instincts(instincts_dir, project_dir)

    inherited = project_dir / "instincts" / "inherited"
    assert not (inherited / "bad.md").exists()
    assert not (inherited / "_rejected").exists()


def test_copy_evolved_output_copies_skills_commands_agents(tmp_path):
    evolved = tmp_path / "evolved"
    (evolved / "skills" / "wzp-debug").mkdir(parents=True)
    (evolved / "skills" / "wzp-debug" / "SKILL.md").write_text("# Skill")
    (evolved / "commands").mkdir()
    (evolved / "commands" / "wzp-fix.md").write_text("# Command")
    (evolved / "agents").mkdir()

    output_dir = tmp_path / "output"
    copy_evolved_output(evolved, output_dir, project_name="wzp-脑力大冒险",
                        stats={"sessions": 73, "patterns": 12})

    assert (output_dir / "skills" / "wzp-debug" / "SKILL.md").exists()
    assert (output_dir / "commands" / "wzp-fix.md").exists()
    assert (output_dir / "README.md").exists()
    readme = (output_dir / "README.md").read_text()
    assert "73" in readme
    assert "wzp" in readme


def test_run_evolve_calls_instinct_cli_with_generate(tmp_path):
    instincts_dir = _make_instincts_dir(tmp_path)
    output_dir = tmp_path / "out"
    cli_path = Path("/fake/instinct-cli.py")

    # Simulate instinct-cli creating evolved output
    def fake_run(cmd, env, check, capture_output):
        project_dir_path = Path(env["CLAUDE_PROJECT_DIR"])
        import hashlib
        pid = hashlib.sha256(str(project_dir_path).encode()).hexdigest()[:12]
        homunculus = tmp_path / "homunculus"
        evolved_dir = homunculus / "projects" / pid / "evolved"
        (evolved_dir / "skills" / "wzp-debug").mkdir(parents=True)
        (evolved_dir / "skills" / "wzp-debug" / "SKILL.md").write_text("# Skill")
        (evolved_dir / "commands").mkdir(exist_ok=True)
        (evolved_dir / "agents").mkdir(exist_ok=True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        return mock_result

    with patch("subprocess.run", side_effect=fake_run):
        with patch("evolve_skills.HOMUNCULUS_DIR", tmp_path / "homunculus"):
            run_evolve(
                instincts_dir=instincts_dir,
                output_dir=output_dir,
                project_name="wzp-脑力大冒险",
                instinct_cli_path=cli_path,
            )

    assert (output_dir / "skills" / "wzp-debug" / "SKILL.md").exists()
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd traj-evolver && python -m pytest tests/test_evolve.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'evolve_skills'`

- [ ] **Step 3: Implement `traj-evolver/scripts/evolve_skills.py`**

```python
#!/usr/bin/env python3
"""Stage 3: Stage instincts into homunculus, run instinct-cli evolve, copy output."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import yaml
from datetime import datetime, timezone
from pathlib import Path

HOMUNCULUS_DIR = Path.home() / ".claude" / "homunculus"


def stage_instincts(instincts_dir: Path, project_dir: Path) -> None:
    """Copy instinct .md files (excluding _rejected/) to project_dir/instincts/inherited/."""
    inherited = project_dir / "instincts" / "inherited"
    inherited.mkdir(parents=True, exist_ok=True)

    for md_file in instincts_dir.glob("*.md"):
        shutil.copy(md_file, inherited / md_file.name)


def copy_evolved_output(evolved_dir: Path, output_dir: Path, project_name: str, stats: dict) -> None:
    """Copy evolved/{skills,commands,agents}/ to output_dir and write README.md."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for subdir in ("skills", "commands", "agents"):
        src = evolved_dir / subdir
        dst = output_dir / subdir
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            dst.mkdir(exist_ok=True)

    readme = f"""# Evolved Skills — {project_name}

Generated: {datetime.now(timezone.utc).isoformat()}

## Provenance

- Sessions analyzed: {stats.get('sessions', '?')}
- Patterns mined: {stats.get('patterns', '?')}
- Project: {project_name}

## Contents

- `skills/` — Auto-triggered patterns extracted from real session trajectories
- `commands/` — User-invoked workflow shortcuts
- `agents/` — Multi-step process agents

## Usage

Install skills by copying to your Claude Code project's `.claude/skills/` directory,
or reference them via the ECC plugin system.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def run_evolve(
    instincts_dir: Path,
    output_dir: Path,
    project_name: str,
    instinct_cli_path: Path,
) -> None:
    """Create synthetic homunculus project, run evolve, copy output."""
    with tempfile.TemporaryDirectory(prefix="traj-evolver-") as tmp_root:
        # Compute the project_id instinct-cli will derive from this path
        project_id = hashlib.sha256(tmp_root.encode()).hexdigest()[:12]
        project_dir = HOMUNCULUS_DIR / "projects" / project_id

        # Stage instincts before invoking CLI
        stage_instincts(instincts_dir, project_dir)

        # Ensure evolved dirs exist (instinct-cli may expect them)
        for subdir in ("skills", "commands", "agents"):
            (project_dir / "evolved" / subdir).mkdir(parents=True, exist_ok=True)

        env = {**os.environ, "CLAUDE_PROJECT_DIR": tmp_root}
        result = subprocess.run(
            [sys.executable, str(instinct_cli_path), "evolve", "--generate"],
            env=env,
            check=True,
            capture_output=True,
        )

        evolved_dir = project_dir / "evolved"
        patterns_count = len(list(instincts_dir.glob("*.md")))
        copy_evolved_output(
            evolved_dir=evolved_dir,
            output_dir=output_dir,
            project_name=project_name,
            stats={"patterns": patterns_count},
        )


def main():
    parser = argparse.ArgumentParser(description="Stage instincts and run instinct-cli evolve")
    parser.add_argument("--instincts-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--config", type=Path, default=Path("traj-evolver/config.yaml"))
    args = parser.parse_args()

    cli_path = Path("~/.claude/plugins/cache/everything-claude-code/everything-claude-code"
                    "/1.9.0/skills/continuous-learning-v2/scripts/instinct-cli.py").expanduser()
    if args.config.exists():
        with open(args.config) as f:
            data = yaml.safe_load(f)
        cli_str = data.get("evolve", {}).get("instinct_cli_path", "")
        if cli_str:
            cli_path = Path(cli_str).expanduser()

    if not cli_path.exists():
        print(f"ERROR: instinct-cli.py not found at {cli_path}", file=sys.stderr)
        print("Set evolve.instinct_cli_path in config.yaml", file=sys.stderr)
        sys.exit(1)

    run_evolve(
        instincts_dir=args.instincts_dir,
        output_dir=args.output_dir,
        project_name=args.project_name,
        instinct_cli_path=cli_path,
    )
    print(f"Done. Output at: {args.output_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all evolve tests**

```bash
cd traj-evolver && python -m pytest tests/test_evolve.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Run the full test suite**

```bash
cd traj-evolver && python -m pytest tests/ -v
```

Expected: all tests PASS (miner + enricher + evolve).

- [ ] **Step 6: Commit**

```bash
git add traj-evolver/scripts/evolve_skills.py traj-evolver/tests/test_evolve.py
git commit -m "feat(traj-evolver): evolve_skills staging + instinct-cli invocation"
```

---

## Task 9: prompts/enrich.md + Makefile + README.md

**Files:**
- Modify: `traj-evolver/prompts/enrich.md`
- Create: `traj-evolver/Makefile`
- Create: `traj-evolver/README.md`

- [ ] **Step 1: Write `traj-evolver/prompts/enrich.md`**

```markdown
# Trajectory Instinct Enricher — System Context

You are analyzing real Claude Code session trajectories from two game development projects
built on the UrhoX Lua engine via TapTap Maker:

- **wzp** (脑力大冒险): casual puzzle game collection, content-production heavy.
  Typical tools: mcp__mkr__Read, Grep, mcp__mkr__Edit, mcp__sce-urhox__build
- **zzj** (超时空要塞): TapTap platform integration, search-heavy with long marathon sessions.
  Typical tools: Grep, mcp__mkr__Read, mcp__mkr__Edit, mcp__sce-urhox__* platform tools

## Your Task

Given a pattern JSON object extracted from trajectory data, produce a single
YAML-frontmatter instinct document. The instinct should:

1. Name the pattern concisely (e.g. "Read → Grep → Edit Debug Flow")
2. Write a trigger clause that fires when this pattern is most useful
3. Write 1-2 action sentences (imperative, specific)
4. List 2+ evidence bullets with quantitative data from the pattern

## Quality Bar

- **Trigger**: starts with "when", describes a concrete situation, not vague
  - Good: "when fixing a bug reported in a specific Lua file"
  - Bad: "when editing code"
- **Action**: tells the reader exactly what to do first
  - Good: "Read the reported file first, then Grep for related function names before editing"
  - Bad: "Handle the bug appropriately"
- **Evidence**: numbers, ratios, and session counts from the pattern JSON
  - Good: "- Appeared 47 times across 23 sessions (distinctness: 0.62)"
  - Bad: "- Commonly observed pattern"

## Style

- Tone: practical, direct, no fluff
- Avoid: "this instinct", "you should", marketing language
- Domain values: debugging, editing, localization, verification, workflow, platform
- Leave confidence as a placeholder (0.75) — the pipeline overwrites it deterministically

## Output Format

Emit only the YAML-frontmatter markdown document. No preamble, no explanation.
The document must start with `---` on the first line.
```

- [ ] **Step 2: Write `traj-evolver/Makefile`**

```makefile
SHELL := /bin/bash
PROJECT ?= wzp
ROOT    := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
CONFIG  := $(ROOT)/traj-evolver/config.yaml

.PHONY: mine enrich evolve pipeline test clean

mine:
	python3 $(ROOT)/traj-evolver/scripts/traj_miner.py \
	  --input-dir  $(ROOT)/traj-data-new/$(PROJECT) \
	  --output-dir $(ROOT)/traj-evolver/patterns/$(PROJECT) \
	  --project    $(PROJECT) \
	  --compare-dir $(ROOT)/traj-data-new/$(if $(filter wzp,$(PROJECT)),zzj,wzp) \
	  --config $(CONFIG)

enrich:
	python3 $(ROOT)/traj-evolver/scripts/traj_enricher.py \
	  --patterns-file $(ROOT)/traj-evolver/patterns/$(PROJECT)/patterns.json \
	  --traj-dir      $(ROOT)/traj-data-new/$(PROJECT) \
	  --output-dir    $(ROOT)/traj-evolver/instincts/$(PROJECT) \
	  --config $(CONFIG)

evolve:
	python3 $(ROOT)/traj-evolver/scripts/evolve_skills.py \
	  --instincts-dir $(ROOT)/traj-evolver/instincts/$(PROJECT) \
	  --output-dir    $(ROOT)/evolved/$(PROJECT) \
	  --project-name  "$(PROJECT)" \
	  --config $(CONFIG)

pipeline: mine enrich evolve

test:
	cd $(ROOT)/traj-evolver && python -m pytest tests/ -v

clean:
	rm -rf $(ROOT)/traj-evolver/patterns/$(PROJECT) \
	       $(ROOT)/traj-evolver/instincts/$(PROJECT) \
	       $(ROOT)/evolved/$(PROJECT)
```

- [ ] **Step 3: Write `traj-evolver/README.md`**

```markdown
# traj-evolver

Converts real Claude Code session trajectories (`.traj` files) into ECC-format skill folders.

## Quick Start

```bash
# Set at least one provider key
export DASHSCOPE_API_KEY=sk-...    # Qwen (default, cheaper)
# OR
export ANTHROPIC_API_KEY=sk-ant-... # Anthropic Sonnet (fallback)

# Run the full pipeline for one project
cd /path/to/project-logs
make -f traj-evolver/Makefile pipeline PROJECT=wzp
```

Output: `evolved/wzp/{skills,commands,agents}/`

## Pipeline Stages

| Stage | Script | Input | Output |
|---|---|---|---|
| Scan+Select | `traj_miner.py` | `traj-data-new/{project}/*.traj` | `patterns/{project}/patterns.json` |
| Prompt/Mutate | `traj_enricher.py` | `patterns.json` | `instincts/{project}/*.md` |
| Event | `evolve_skills.py` | `instincts/{project}/*.md` | `evolved/{project}/` |

Each stage writes to disk. You can inspect and resume from any stage.

## Configuration

Edit `config.yaml`:
- `miner.min_frequency`: drop patterns seen fewer than N times (default: 3)
- `miner.top_k_per_family`: keep top K patterns per family (default: 20)
- `enricher.providers`: provider order; first with a valid API key wins
- `evolve.instinct_cli_path`: path to `instinct-cli.py`

## Troubleshooting

**No API key**: `RuntimeError: No LLM provider available. Set one of: DASHSCOPE_API_KEY`
→ Export at least one of the provider keys listed.

**`enable_thinking` error from Qwen**: The config already sets `enable_thinking: false`.
If you see this error, verify your `config.yaml` has `extra_body.enable_thinking: false` under the qwen provider.

**No patterns mined**: Lower `miner.min_frequency` to 1 and rerun Stage 1.
If still empty, check that `--input-dir` points to a directory containing `.traj` files.

**Rejection failures**: Check `instincts/{project}/_rejected/error_log.txt` for per-pattern error details.

**instinct-cli not found**: Update `evolve.instinct_cli_path` in `config.yaml` to the
absolute path of your `instinct-cli.py`. Find it with:
`find ~/.claude -name instinct-cli.py 2>/dev/null`

## Running Tests

```bash
cd traj-evolver && python -m pytest tests/ -v
```

47 tests, no API keys required (all LLM calls mocked).
```

- [ ] **Step 4: Run the full test suite one final time**

```bash
cd traj-evolver && python -m pytest tests/ -v --tb=short
```

Expected: all tests PASS. Count the test total and confirm it's ≥ 15.

- [ ] **Step 5: Commit**

```bash
git add traj-evolver/prompts/enrich.md traj-evolver/Makefile traj-evolver/README.md
git commit -m "feat(traj-evolver): prompt prefix, Makefile, README"
```

---

## Task 10: End-to-End Smoke Test

**Files:**
- No new files — runs against real data, verifies output

This task has no mocked LLM calls. It uses real Qwen API calls on the 3 smallest wzp `.traj` files.

- [ ] **Step 1: Find the 3 smallest wzp .traj files**

```bash
ls -lS traj-data-new/wzp/*.traj | head -4
```

Note the 3 filenames with the smallest sizes. Example output:
```
  12345 traj-data-new/wzp/cc1dd130.traj
  23456 traj-data-new/wzp/08e306a0.traj
  34567 traj-data-new/wzp/4d80bab3.traj
```

- [ ] **Step 2: Create a smoke-test input dir with those 3 files**

```bash
mkdir -p traj-evolver/smoke-test/input
cp traj-data-new/wzp/cc1dd130.traj traj-data-new/wzp/08e306a0.traj traj-data-new/wzp/4d80bab3.traj \
   traj-evolver/smoke-test/input/
```

(Use the actual 3 filenames from Step 1.)

- [ ] **Step 3: Run Stage 1 on smoke-test input**

```bash
python3 traj-evolver/scripts/traj_miner.py \
  --input-dir traj-evolver/smoke-test/input \
  --output-dir traj-evolver/smoke-test/patterns \
  --project wzp \
  --config traj-evolver/config.yaml
```

Expected: prints `Mined N patterns from 3 sessions`. Check the output:

```bash
python3 -c "
import json
d = json.load(open('traj-evolver/smoke-test/patterns/patterns.json'))
print('sessions:', d['stats']['sessions'])
print('patterns:', len(d['patterns']))
assert d['stats']['sessions'] == 3
assert len(d['patterns']) > 0, 'No patterns — lower min_frequency in config.yaml'
print('Stage 1 OK')
"
```

- [ ] **Step 4: Run Stage 2 (requires DASHSCOPE_API_KEY or ANTHROPIC_API_KEY)**

```bash
python3 traj-evolver/scripts/traj_enricher.py \
  --patterns-file traj-evolver/smoke-test/patterns/patterns.json \
  --traj-dir traj-evolver/smoke-test/input \
  --output-dir traj-evolver/smoke-test/instincts \
  --config traj-evolver/config.yaml
```

Expected: prints `Done: N accepted, M rejected`. Verify:

```bash
python3 -c "
from pathlib import Path
instincts = list(Path('traj-evolver/smoke-test/instincts').glob('*.md'))
assert len(instincts) >= 3, f'Expected >= 3 instincts, got {len(instincts)}'
print(f'Stage 2 OK: {len(instincts)} instincts generated')
for p in instincts[:2]:
    print(' ', p.name)
"
```

- [ ] **Step 5: Run Stage 3**

```bash
python3 traj-evolver/scripts/evolve_skills.py \
  --instincts-dir traj-evolver/smoke-test/instincts \
  --output-dir traj-evolver/smoke-test/evolved \
  --project-name "wzp-脑力大冒险" \
  --config traj-evolver/config.yaml
```

Expected: prints `Done. Output at: traj-evolver/smoke-test/evolved`. Verify:

```bash
python3 -c "
from pathlib import Path
evolved = Path('traj-evolver/smoke-test/evolved')
skills = list(evolved.glob('skills/**/*.md'))
assert evolved.exists(), 'evolved/ dir missing'
assert (evolved / 'README.md').exists(), 'README.md missing'
print(f'Stage 3 OK: {len(skills)} skill files in evolved/skills/')
"
```

- [ ] **Step 6: Commit smoke-test results (patterns and instincts only, not evolved)**

```bash
git add traj-evolver/smoke-test/patterns/ traj-evolver/smoke-test/instincts/
git commit -m "test(traj-evolver): smoke-test output from 3 wzp sessions"
```

---

## Self-Review

### Spec Coverage

| Spec Section | Covered By |
|---|---|
| Stage 1: traj_miner.py (5 pattern families) | Tasks 2–4 |
| Stage 1: selection thresholds + output schema | Task 4 |
| Stage 1: CLI with --input-dir / --output-dir | Task 4 |
| Stage 2: dual-provider (Qwen/Anthropic) | Task 5 |
| Stage 2: prompt caching on Anthropic | Task 5 |
| Stage 2: enable_thinking=false on Qwen | Task 5 |
| Stage 2: prompt structure (cached prefix + dynamic suffix) | Tasks 6–7, 9 |
| Stage 2: YAML validation + rejection path | Task 6 |
| Stage 2: confidence calibration (deterministic) | Task 6 |
| Stage 2: async concurrency + retry | Task 7 |
| Stage 2: CLI with --provider flag | Task 7 |
| Stage 3: synthetic homunculus project staging | Task 8 |
| Stage 3: instinct-cli evolve --generate invocation | Task 8 |
| Stage 3: copy output to evolved/ | Task 8 |
| Stage 3: README.md in evolved/{project}/ | Task 8 |
| Makefile targets: mine/enrich/evolve/pipeline/test | Task 9 |
| traj-evolver/README.md | Task 9 |
| End-to-end smoke test | Task 10 |
| config.yaml with all settings | Task 1 |

No gaps identified.

### Placeholder Check

No TBDs, TODOs, or "add appropriate" language in any step. All code blocks are complete.

### Type Consistency

- `extract_turns()` → `list[dict]` used consistently in `mine_ngrams`, `mine_phase_transitions`, `mine_task_shapes`, `mine_corrections`, `mine_tool_fingerprints`
- `tool_names()` → `list[str]` used in all mining functions
- `EnricherClient.complete(system: str, user: str) -> str` implemented identically in `QwenClient` and `AnthropicClient`
- `write_instinct(text, pattern_id, output_dir, rejected_dir, errors)` called consistently in `_process_one` and tests
- `run_evolve(instincts_dir, output_dir, project_name, instinct_cli_path)` matches test calls
