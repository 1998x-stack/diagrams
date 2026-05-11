# Traj-Evolver V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 4-stage pipeline that converts trajectory patterns into evolver-native Gene/Capsule assets (via `a2a_ingest.js`) and exports them as ECC skill folders — replacing v1's LLM enrichment and instinct-cli stages.

**Architecture:** Stage 2 (`format_patterns.py`) converts `patterns.json` → Gene/Capsule JSONL without computing `asset_id` (letting evolver compute it at ingest to avoid integrity check failures). Stage 3 calls `node evolver/scripts/a2a_ingest.js` as a subprocess. Stage 4 (`build_ecc_skills.py`) reads `external_candidates.jsonl` filtered by `a2a.source`, writes ECC skill folders. Stage 1 reuses `traj-evolver/scripts/traj_miner.py` unchanged.

**Tech Stack:** Python 3.11+, `pyyaml`, `pytest`, Node.js (existing evolver scripts only)

---

## File Map

```
traj-evolver-v2/
├── config.yaml                        # evolver_dir, a2a settings, miner thresholds
├── Makefile                           # mine/format/ingest/distill/pipeline/test/clean targets
├── README.md                          # quick-start + troubleshooting
├── scripts/
│   ├── __init__.py
│   ├── format_patterns.py             # Stage 2: patterns.json → genes.jsonl + capsules.jsonl
│   └── build_ecc_skills.py            # Stage 4: external_candidates.jsonl → ECC skill folders
└── tests/
    ├── __init__.py
    ├── conftest.py                    # sample pattern fixtures (no raw traj data needed)
    ├── test_format_patterns.py        # 8 tests for Stage 2
    └── test_build_ecc.py              # 4 tests for Stage 4
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `traj-evolver-v2/config.yaml`
- Create: `traj-evolver-v2/scripts/__init__.py`
- Create: `traj-evolver-v2/tests/__init__.py`
- Create: `traj-evolver-v2/tests/conftest.py`

- [ ] **Step 1: Create directories**

```bash
mkdir -p /Users/xd/Desktop/work/project-logs/traj-evolver-v2/{scripts,tests}
touch /Users/xd/Desktop/work/project-logs/traj-evolver-v2/scripts/__init__.py
touch /Users/xd/Desktop/work/project-logs/traj-evolver-v2/tests/__init__.py
```

- [ ] **Step 2: Write `traj-evolver-v2/config.yaml`**

```yaml
pipeline:
  evolver_dir: evolver
  a2a_node_id: traj-evolver-v2
  a2a_confidence_factor: 0.6

miner:
  min_frequency: 3
  top_k_per_family: 20
  distinctness_weight: 0.5
  min_sessions: 2
```

- [ ] **Step 3: Write `traj-evolver-v2/tests/conftest.py`**

These fixtures represent the output of `traj_miner.py` — pattern dicts ready to be formatted. No raw traj data needed.

```python
import pytest


@pytest.fixture
def tool_sequence_pattern():
    return {
        "id": "ngram_read_grep_edit",
        "family": "tool_sequence",
        "sequence": ["mcp__mkr__Read", "Grep", "mcp__mkr__Edit"],
        "frequency": 15,
        "session_count": 8,
        "distinctness": 0.62,
        "keywords": ["fix", "bug"],
        "examples": [{"session": "aaaa", "turn": 1, "step_range": [1, 3]}],
    }


@pytest.fixture
def phase_transition_pattern():
    return {
        "id": "phase_localization_to_editing",
        "family": "phase_transition",
        "sequence": ["localization", "editing"],
        "frequency": 12,
        "session_count": 7,
        "distinctness": 0.8,
        "keywords": [],
        "examples": [{"session": "aaaa", "turn": 1, "step": 2}],
    }


@pytest.fixture
def fingerprint_pattern():
    return {
        "id": "fingerprint_sce-urhox_build",
        "family": "tool_fingerprint",
        "tool": "mcp__sce-urhox__build",
        "frequency": 20,
        "session_count": 15,
        "distinctness": 0.9,
        "keywords": [],
        "examples": [],
    }


@pytest.fixture
def task_shape_pattern():
    return {
        "id": "shape_edit_grep_read",
        "family": "task_shape",
        "tools": ["Grep", "mcp__mkr__Edit", "mcp__mkr__Read"],
        "size": 12,
        "frequency": 12,
        "session_count": 6,
        "distinctness": 0.7,
        "keywords": ["fix", "bug"],
        "examples": [{"session": "aaaa", "turn": 1}],
    }


@pytest.fixture
def correction_signal_pattern():
    return {
        "id": "correction_scripts_game_lua",
        "family": "correction_signal",
        "file": "scripts/game.lua",
        "frequency": 5,
        "session_count": 3,
        "distinctness": 1.0,
        "keywords": ["wrong", "revert"],
        "examples": [{"session": "aaaa", "turn": 2}],
    }
```

- [ ] **Step 4: Verify pytest collects with zero errors**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2 && python -m pytest tests/ --collect-only -q
```

Expected: `no tests collected` with 0 errors.

---

## Task 2: format_patterns.py — TDD + Implementation

**Files:**
- Create: `traj-evolver-v2/tests/test_format_patterns.py`
- Create: `traj-evolver-v2/scripts/format_patterns.py`

- [ ] **Step 1: Write failing tests in `traj-evolver-v2/tests/test_format_patterns.py`**

```python
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from format_patterns import (
    tool_sequence_to_gene,
    phase_transition_to_gene,
    fingerprint_to_gene,
    task_shape_to_capsule,
    correction_to_capsule,
    format_patterns,
    confidence_from_frequency,
)


def test_tool_sequence_pattern_becomes_gene(tool_sequence_pattern):
    gene = tool_sequence_to_gene(tool_sequence_pattern, "wzp", "wzp-脑力大冒险")
    assert gene["type"] == "Gene"
    assert gene["category"] == "workflow"
    assert "fix" in gene["signals_match"] or "bug" in gene["signals_match"]
    assert any("Read" in s or "Grep" in s or "Edit" in s for s in gene["strategy"])


def test_phase_transition_becomes_gene(phase_transition_pattern):
    gene = phase_transition_to_gene(phase_transition_pattern, "wzp", "wzp-脑力大冒险")
    assert gene["type"] == "Gene"
    assert gene["category"] == "workflow"
    assert "localization" in gene["signals_match"]
    assert any("localization" in s and "editing" in s for s in gene["strategy"])


def test_fingerprint_becomes_gene(fingerprint_pattern):
    gene = fingerprint_to_gene(fingerprint_pattern, "wzp", "wzp-脑力大冒险")
    assert gene["type"] == "Gene"
    assert gene["category"] == "platform"
    assert any("sce-urhox" in frag or "build" in frag for frag in gene["signals_match"])


def test_task_shape_becomes_capsule(task_shape_pattern):
    cap = task_shape_to_capsule(task_shape_pattern, "wzp", "wzp-脑力大冒险")
    assert cap["type"] == "Capsule"
    assert cap["intent"] == "workflow"
    assert cap["confidence"] == confidence_from_frequency(task_shape_pattern["frequency"])
    assert cap["blast_radius"] == {"files": 0, "lines": 0}


def test_correction_signal_becomes_capsule(correction_signal_pattern):
    cap = correction_to_capsule(correction_signal_pattern, "wzp", "wzp-脑力大冒险")
    assert cap["type"] == "Capsule"
    assert cap["intent"] == "repair"
    assert cap["confidence"] <= 0.45
    assert "game.lua" in cap["strategy"][0]


def test_no_asset_id_in_output(tool_sequence_pattern):
    # We intentionally omit asset_id so a2a_ingest.js computes it correctly
    # (if we include a wrong asset_id, a2a_ingest rejects the asset)
    gene = tool_sequence_to_gene(tool_sequence_pattern, "wzp", "wzp-脑力大冒险")
    assert "asset_id" not in gene


def test_a2a_fields_present(tool_sequence_pattern, task_shape_pattern):
    gene = tool_sequence_to_gene(tool_sequence_pattern, "wzp", "wzp-脑力大冒险")
    cap = task_shape_to_capsule(task_shape_pattern, "wzp", "wzp-脑力大冒险")
    for asset in [gene, cap]:
        assert asset["a2a"]["status"] == "external_candidate"
        assert asset["a2a"]["source"] == "traj-wzp"
        assert "received_at" in asset["a2a"]


def test_format_patterns_end_to_end(
    tmp_path, tool_sequence_pattern, task_shape_pattern
):
    patterns_data = {
        "project": "wzp",
        "stats": {"sessions": 3},
        "patterns": [tool_sequence_pattern, task_shape_pattern],
    }
    genes, capsules = format_patterns(patterns_data, "wzp", "wzp-脑力大冒险")
    assert len(genes) == 1
    assert len(capsules) == 1
    output_dir = tmp_path / "formatted"
    output_dir.mkdir()
    (output_dir / "genes.jsonl").write_text(
        "\n".join(json.dumps(g, ensure_ascii=False) for g in genes)
    )
    (output_dir / "capsules.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in capsules)
    )
    assert (output_dir / "genes.jsonl").stat().st_size > 0
    assert (output_dir / "capsules.jsonl").stat().st_size > 0
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2 && python -m pytest tests/test_format_patterns.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'format_patterns'`

- [ ] **Step 3: Write `traj-evolver-v2/scripts/format_patterns.py`**

```python
#!/usr/bin/env python3
"""Stage 2: Convert patterns.json to A2A Gene/Capsule JSONL for evolver ingestion."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "2"


def confidence_from_frequency(freq: int) -> float:
    if freq >= 20:
        return 0.85
    if freq >= 10:
        return 0.75
    if freq >= 5:
        return 0.65
    return 0.55


def safe_id(s: str) -> str:
    """Normalize to [a-z0-9_-], max 60 chars."""
    return re.sub(r"[^a-z0-9_\-]", "_", s.lower())[:60]


def _make_a2a(project: str) -> dict:
    return {
        "status": "external_candidate",
        "source": f"traj-{project}",
        "received_at": datetime.now(timezone.utc).isoformat(),
    }


def tool_sequence_to_gene(pattern: dict, project: str, project_name: str) -> dict:
    seq = pattern.get("sequence", [])
    keywords = pattern.get("keywords", [])
    seq_label = "→".join(
        t.replace("mcp__mkr__", "").replace("mcp__sce-urhox__", "sce-") for t in seq
    )
    return {
        "type": "Gene",
        "id": safe_id(f"traj-{project}-{pattern['id']}"),
        "schema_version": SCHEMA_VERSION,
        "category": "workflow",
        "signals_match": keywords if keywords else [seq_label.lower()],
        "preconditions": [f"user message matches: {', '.join(keywords)}"] if keywords else [],
        "strategy": [
            f"When '{', '.join(keywords) if keywords else seq_label}', apply {seq_label} tool flow.",
            f"Sequence: {' → '.join(seq)}",
            f"Observed {pattern.get('frequency', 0)} times across {pattern.get('session_count', 0)} sessions.",
        ],
        "constraints": {"max_files": 10, "forbidden_paths": [".git", "node_modules"]},
        "validation": [],
        "a2a": _make_a2a(project),
        "project": project,
        "project_name": project_name,
    }


def phase_transition_to_gene(pattern: dict, project: str, project_name: str) -> dict:
    seq = pattern.get("sequence", ["?", "?"])
    from_phase, to_phase = seq[0], seq[1]
    return {
        "type": "Gene",
        "id": safe_id(f"traj-{project}-{pattern['id']}"),
        "schema_version": SCHEMA_VERSION,
        "category": "workflow",
        "signals_match": [from_phase],
        "preconditions": [f"currently in {from_phase} phase"],
        "strategy": [
            f"Follow {from_phase}→{to_phase} phase transition.",
            f"After {from_phase} work, move to {to_phase} steps.",
            f"Observed {pattern.get('frequency', 0)} transitions across {pattern.get('session_count', 0)} sessions.",
        ],
        "constraints": {"max_files": 10, "forbidden_paths": [".git", "node_modules"]},
        "validation": [],
        "a2a": _make_a2a(project),
        "project": project,
        "project_name": project_name,
    }


def fingerprint_to_gene(pattern: dict, project: str, project_name: str) -> dict:
    tool = pattern.get("tool", "")
    fragments = [f for f in re.split(r"[_\-]+", tool.replace("mcp__", "")) if f and len(f) > 2]
    return {
        "type": "Gene",
        "id": safe_id(f"traj-{project}-{pattern['id']}"),
        "schema_version": SCHEMA_VERSION,
        "category": "platform",
        "signals_match": fragments if fragments else [tool],
        "preconditions": [f"using {project} platform tools"],
        "strategy": [
            f"Use project-specific tool {tool}.",
            f"This tool appears {pattern.get('frequency', 0)} times in {project} sessions.",
            f"Distinctness score: {pattern.get('distinctness', 1.0):.2f} (project-specific).",
        ],
        "constraints": {"max_files": 5, "forbidden_paths": [".git", "node_modules"]},
        "validation": [],
        "a2a": _make_a2a(project),
        "project": project,
        "project_name": project_name,
    }


def task_shape_to_capsule(pattern: dict, project: str, project_name: str) -> dict:
    tools = pattern.get("tools", [])
    freq = pattern.get("frequency", 0)
    tool_label = ", ".join(
        t.replace("mcp__mkr__", "") for t in tools[:3]
    )
    return {
        "type": "Capsule",
        "id": safe_id(f"traj-{project}-{pattern['id']}"),
        "schema_version": SCHEMA_VERSION,
        "intent": "workflow",
        "confidence": confidence_from_frequency(freq),
        "strategy": [
            f"Task cluster using tools: {tool_label}.",
            f"Cluster size: {pattern.get('size', freq)} turns across {pattern.get('session_count', 0)} sessions.",
            f"Common keywords: {', '.join(pattern.get('keywords', [])[:5])}.",
        ],
        "blast_radius": {"files": 0, "lines": 0},
        "a2a": _make_a2a(project),
        "project": project,
        "project_name": project_name,
    }


def correction_to_capsule(pattern: dict, project: str, project_name: str) -> dict:
    freq = pattern.get("frequency", 0)
    confidence = min(confidence_from_frequency(freq), 0.45)
    file_path = pattern.get("file", "unknown")
    kws = pattern.get("keywords", [])
    return {
        "type": "Capsule",
        "id": safe_id(f"traj-{project}-{pattern['id']}"),
        "schema_version": SCHEMA_VERSION,
        "intent": "repair",
        "confidence": confidence,
        "strategy": [
            f"Undo edit to {file_path} when user corrects (keywords: {', '.join(kws)}).",
            f"Re-approach the edit after understanding the correction.",
            f"Observed {freq} correction cycles in {pattern.get('session_count', 0)} sessions.",
        ],
        "blast_radius": {"files": 0, "lines": 0},
        "a2a": _make_a2a(project),
        "project": project,
        "project_name": project_name,
    }


_FAMILY_TO_GENE = {
    "tool_sequence": tool_sequence_to_gene,
    "phase_transition": phase_transition_to_gene,
    "tool_fingerprint": fingerprint_to_gene,
}

_FAMILY_TO_CAPSULE = {
    "task_shape": task_shape_to_capsule,
    "correction_signal": correction_to_capsule,
}


def format_patterns(
    patterns_data: dict, project: str, project_name: str
) -> tuple[list[dict], list[dict]]:
    """Convert patterns.json data to (genes, capsules) lists."""
    genes: list[dict] = []
    capsules: list[dict] = []
    for pattern in patterns_data.get("patterns", []):
        family = pattern.get("family")
        if family in _FAMILY_TO_GENE:
            genes.append(_FAMILY_TO_GENE[family](pattern, project, project_name))
        elif family in _FAMILY_TO_CAPSULE:
            capsules.append(_FAMILY_TO_CAPSULE[family](pattern, project, project_name))
    return genes, capsules


def main() -> None:
    parser = argparse.ArgumentParser(description="Format patterns.json as A2A Gene/Capsule JSONL")
    parser.add_argument("--patterns-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--project-name", default="")
    args = parser.parse_args()

    data = json.loads(args.patterns_file.read_text(encoding="utf-8"))
    genes, capsules = format_patterns(data, args.project, args.project_name or args.project)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "genes.jsonl").write_text(
        "\n".join(json.dumps(g, ensure_ascii=False) for g in genes),
        encoding="utf-8",
    )
    (args.output_dir / "capsules.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in capsules),
        encoding="utf-8",
    )
    print(f"Formatted {len(genes)} genes + {len(capsules)} capsules → {args.output_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all 8 tests**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2 && python -m pytest tests/test_format_patterns.py -v
```

Expected: `8 passed`.

---

## Task 3: build_ecc_skills.py — TDD + Implementation

**Files:**
- Create: `traj-evolver-v2/tests/test_build_ecc.py`
- Create: `traj-evolver-v2/scripts/build_ecc_skills.py`

- [ ] **Step 1: Write failing tests in `traj-evolver-v2/tests/test_build_ecc.py`**

```python
import sys, json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from build_ecc_skills import build_ecc_skills, gene_to_skill_md, capsule_to_command_md, cluster_to_agent_md


def _make_gene(gid="traj-wzp-ngram_read_grep_edit", signals=None, strategy=None):
    return {
        "type": "Gene",
        "id": gid,
        "category": "workflow",
        "signals_match": signals or ["fix", "bug"],
        "strategy": strategy or [
            "When fix, apply Read→Grep→Edit flow.",
            "Sequence: mcp__mkr__Read → Grep → mcp__mkr__Edit",
            "Observed 15 times across 8 sessions.",
        ],
        "a2a": {"status": "external_candidate", "source": "traj-wzp"},
        "project": "wzp",
    }


def _make_capsule(cid="traj-wzp-shape_edit_grep_read", intent="workflow", confidence=0.75):
    return {
        "type": "Capsule",
        "id": cid,
        "intent": intent,
        "confidence": confidence,
        "strategy": ["Task cluster using tools: Edit, Grep, Read.", "Cluster of 12 turns."],
        "blast_radius": {"files": 0, "lines": 0},
        "a2a": {"status": "external_candidate", "source": "traj-wzp"},
        "project": "wzp",
    }


def _write_candidates(evolver_dir: Path, assets: list) -> None:
    gep = evolver_dir / "assets" / "gep"
    gep.mkdir(parents=True, exist_ok=True)
    (gep / "external_candidates.jsonl").write_text(
        "\n".join(json.dumps(a, ensure_ascii=False) for a in assets),
        encoding="utf-8",
    )


def test_gene_produces_skill_md(tmp_path):
    evolver_dir = tmp_path / "evolver"
    _write_candidates(evolver_dir, [_make_gene()])
    output_dir = tmp_path / "evolved" / "wzp"

    build_ecc_skills(evolver_dir, "wzp", "wzp-脑力大冒险", output_dir, {})

    skill_file = output_dir / "skills" / "traj_wzp_ngram_read_grep_edit" / "SKILL.md"
    assert skill_file.exists()
    content = skill_file.read_text()
    assert "name:" in content
    assert "trigger:" in content
    assert "fix" in content or "bug" in content


def test_high_conf_capsule_produces_command_md(tmp_path):
    evolver_dir = tmp_path / "evolver"
    _write_candidates(evolver_dir, [_make_capsule(confidence=0.75)])
    output_dir = tmp_path / "evolved" / "wzp"

    build_ecc_skills(evolver_dir, "wzp", "wzp-脑力大冒险", output_dir, {})

    cmd_file = output_dir / "commands" / "traj_wzp_shape_edit_grep_read.md"
    assert cmd_file.exists()
    content = cmd_file.read_text()
    assert "confidence:" in content
    assert "0.75" in content


def test_low_conf_capsule_skipped(tmp_path):
    evolver_dir = tmp_path / "evolver"
    _write_candidates(evolver_dir, [_make_capsule(confidence=0.30)])
    output_dir = tmp_path / "evolved" / "wzp"

    build_ecc_skills(evolver_dir, "wzp", "wzp-脑力大冒险", output_dir, {})

    assert not list((output_dir / "commands").glob("*.md"))


def test_capsule_cluster_produces_agent_md(tmp_path):
    caps = [_make_capsule(cid=f"traj-wzp-cap_{i}", intent="workflow") for i in range(3)]
    evolver_dir = tmp_path / "evolver"
    _write_candidates(evolver_dir, caps)
    output_dir = tmp_path / "evolved" / "wzp"

    build_ecc_skills(evolver_dir, "wzp", "wzp-脑力大冒险", output_dir, {})

    agent_file = output_dir / "agents" / "workflow-agent.md"
    assert agent_file.exists()
    content = agent_file.read_text()
    assert "capsule_count: 3" in content
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2 && python -m pytest tests/test_build_ecc.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'build_ecc_skills'`

- [ ] **Step 3: Write `traj-evolver-v2/scripts/build_ecc_skills.py`**

```python
#!/usr/bin/env python3
"""Stage 4: Build ECC skill folders from evolver external_candidates.jsonl."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def _safe_filename(s: str) -> str:
    return re.sub(r"[^a-z0-9_\-]", "_", s.lower())[:60]


def load_candidates(evolver_dir: Path, project: str) -> tuple[list[dict], list[dict]]:
    """Return (genes, capsules) filtered to traj-{project} source."""
    path = evolver_dir / "assets" / "gep" / "external_candidates.jsonl"
    if not path.exists():
        return [], []
    source_tag = f"traj-{project}"
    genes: list[dict] = []
    capsules: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("a2a", {}).get("source") != source_tag:
            continue
        t = obj.get("type")
        if t == "Gene":
            genes.append(obj)
        elif t == "Capsule":
            capsules.append(obj)
    return genes, capsules


def gene_to_skill_md(gene: dict, project: str) -> str:
    gid = gene.get("id", "unknown")
    signals = gene.get("signals_match", [])
    category = gene.get("category", "workflow")
    strategy = gene.get("strategy", [])
    trigger = " or ".join(signals) if signals else "relevant workflow"
    title = gid.replace(f"traj-{project}-", "").replace("_", " ").replace("-", " ").title()
    description = strategy[0] if strategy else f"Apply {gid} pattern"
    action_steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(strategy))
    return f"""---
name: {gid}
description: {description}
trigger: when {trigger}
domain: {category}
source: trajectory-import
project: {project}
---

# {title}

## When to use
When {trigger}.

## Action
{action_steps}
"""


def capsule_to_command_md(capsule: dict, project: str) -> str:
    cid = capsule.get("id", "unknown")
    intent = capsule.get("intent", "workflow")
    confidence = capsule.get("confidence", 0.0)
    strategy = capsule.get("strategy", [])
    title = cid.replace(f"traj-{project}-", "").replace("_", " ").replace("-", " ").title()
    action = "\n".join(f"- {s}" for s in strategy)
    return f"""---
name: {cid}
intent: {intent}
confidence: {confidence:.2f}
source: trajectory-import
project: {project}
---

# {title}

## Action
{action}
"""


def cluster_to_agent_md(intent: str, capsules: list[dict], project: str) -> str:
    count = len(capsules)
    bullets = "\n".join(f"- {c.get('id', '?')}" for c in capsules)
    return f"""---
name: {intent}-agent
intent: {intent}
capsule_count: {count}
source: trajectory-import
project: {project}
---

# {intent.title()} Agent

Covers {count} behavioral patterns extracted from real {project} sessions.

## Patterns
{bullets}
"""


def build_ecc_skills(
    evolver_dir: Path,
    project: str,
    project_name: str,
    output_dir: Path,
    patterns_stats: dict,
) -> dict:
    """Write ECC folders from evolver store. Returns summary counts."""
    genes, capsules = load_candidates(evolver_dir, project)
    output_dir.mkdir(parents=True, exist_ok=True)
    skills_dir = output_dir / "skills"
    commands_dir = output_dir / "commands"
    agents_dir = output_dir / "agents"
    for d in [skills_dir, commands_dir, agents_dir]:
        d.mkdir(exist_ok=True)

    skill_count = 0
    for gene in genes:
        gid = _safe_filename(gene.get("id", "unknown"))
        skill_subdir = skills_dir / gid
        skill_subdir.mkdir(exist_ok=True)
        (skill_subdir / "SKILL.md").write_text(
            gene_to_skill_md(gene, project), encoding="utf-8"
        )
        skill_count += 1

    command_count = 0
    for cap in capsules:
        if cap.get("confidence", 0) >= 0.4:
            cid = _safe_filename(cap.get("id", "unknown"))
            (commands_dir / f"{cid}.md").write_text(
                capsule_to_command_md(cap, project), encoding="utf-8"
            )
            command_count += 1

    agent_count = 0
    by_intent: dict[str, list] = defaultdict(list)
    for cap in capsules:
        by_intent[cap.get("intent", "workflow")].append(cap)
    for intent, cluster in by_intent.items():
        if len(cluster) >= 3:
            (agents_dir / f"{intent}-agent.md").write_text(
                cluster_to_agent_md(intent, cluster, project), encoding="utf-8"
            )
            agent_count += 1

    readme = (
        f"# Evolved Skills — {project_name}\n\n"
        f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
        f"Source: trajectory patterns via traj-evolver-v2 + evolver GEP\n\n"
        f"## Provenance\n"
        f"- Sessions analyzed: {patterns_stats.get('sessions', '?')}\n"
        f"- Genes ingested: {len(genes)}\n"
        f"- Capsules ingested: {len(capsules)}\n"
        f"- ECC skills written: {skill_count}\n"
        f"- Commands written: {command_count}\n"
        f"- Agents written: {agent_count}\n"
    )
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    return {
        "skills": skill_count,
        "commands": command_count,
        "agents": agent_count,
        "genes": len(genes),
        "capsules": len(capsules),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ECC skills from evolver store")
    parser.add_argument("--evolver-dir", required=True, type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--project-name", default="")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--patterns-file",
        type=Path,
        default=None,
        help="Optional patterns.json to read session stats from",
    )
    args = parser.parse_args()

    stats: dict = {}
    if args.patterns_file and args.patterns_file.exists():
        stats = json.loads(args.patterns_file.read_text()).get("stats", {})

    counts = build_ecc_skills(
        evolver_dir=args.evolver_dir,
        project=args.project,
        project_name=args.project_name or args.project,
        output_dir=args.output_dir,
        patterns_stats=stats,
    )
    print(
        f"Built: {counts['skills']} skills, {counts['commands']} commands, "
        f"{counts['agents']} agents"
    )
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all 12 tests**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2 && python -m pytest tests/ -v
```

Expected: `12 passed`.

---

## Task 4: Makefile + README + Smoke Test

**Files:**
- Create: `traj-evolver-v2/Makefile`
- Create: `traj-evolver-v2/README.md`

- [ ] **Step 1: Write `traj-evolver-v2/Makefile`**

Note: Makefile recipe lines require actual TAB characters, not spaces.

```makefile
SHELL   := /bin/bash
PROJECT ?= wzp
ROOT    := $(shell cd .. && pwd)
CONFIG  := $(ROOT)/traj-evolver-v2/config.yaml

# Read config values
EVOLVER_DIR  := $(ROOT)/evolver
A2A_NODE_ID  := traj-evolver-v2
A2A_FACTOR   := 0.6

.PHONY: mine format ingest distill pipeline test clean

mine:
	python3 $(ROOT)/traj-evolver/scripts/traj_miner.py \
	  --input-dir   $(ROOT)/traj-data-new/$(PROJECT) \
	  --output-dir  $(ROOT)/traj-evolver-v2/patterns/$(PROJECT) \
	  --project     $(PROJECT) \
	  --compare-dir $(ROOT)/traj-data-new/$(if $(filter wzp,$(PROJECT)),zzj,wzp) \
	  --config      $(ROOT)/traj-evolver/config.yaml

format:
	python3 $(ROOT)/traj-evolver-v2/scripts/format_patterns.py \
	  --patterns-file $(ROOT)/traj-evolver-v2/patterns/$(PROJECT)/patterns.json \
	  --output-dir    $(ROOT)/traj-evolver-v2/formatted/$(PROJECT) \
	  --project       $(PROJECT)

ingest:
	cd $(ROOT) && \
	A2A_NODE_ID=$(A2A_NODE_ID) \
	A2A_SOURCE=traj-$(PROJECT) \
	A2A_EXTERNAL_CONFIDENCE_FACTOR=$(A2A_FACTOR) \
	  node $(EVOLVER_DIR)/scripts/a2a_ingest.js \
	    traj-evolver-v2/formatted/$(PROJECT)/genes.jsonl && \
	A2A_NODE_ID=$(A2A_NODE_ID) \
	A2A_SOURCE=traj-$(PROJECT) \
	A2A_EXTERNAL_CONFIDENCE_FACTOR=$(A2A_FACTOR) \
	  node $(EVOLVER_DIR)/scripts/a2a_ingest.js \
	    traj-evolver-v2/formatted/$(PROJECT)/capsules.jsonl

distill:
	python3 $(ROOT)/traj-evolver-v2/scripts/build_ecc_skills.py \
	  --evolver-dir   $(EVOLVER_DIR) \
	  --project       $(PROJECT) \
	  --output-dir    $(ROOT)/evolved/$(PROJECT) \
	  --patterns-file $(ROOT)/traj-evolver-v2/patterns/$(PROJECT)/patterns.json

pipeline: mine format ingest distill

test:
	cd $(ROOT)/traj-evolver-v2 && python -m pytest tests/ -v

clean:
	rm -rf $(ROOT)/traj-evolver-v2/patterns/$(PROJECT) \
	       $(ROOT)/traj-evolver-v2/formatted/$(PROJECT) \
	       $(ROOT)/evolved/$(PROJECT)
```

- [ ] **Step 2: Write `traj-evolver-v2/README.md`**

```markdown
# traj-evolver-v2

Converts `.traj` session trajectories into evolver-native Gene/Capsule assets and ECC skill folders — using `evolver/`'s GEP engine instead of LLM enrichment.

## Quick Start

```bash
# From project-logs root
cd traj-evolver-v2
make pipeline PROJECT=wzp
```

Output: `evolved/wzp/{skills,commands,agents}/`

## Pipeline Stages

| Stage | What runs | Input | Output |
|---|---|---|---|
| 1 mine | `traj_miner.py` (v1, reused) | `traj-data-new/{project}/*.traj` | `patterns/{project}/patterns.json` |
| 2 format | `format_patterns.py` | `patterns.json` | `formatted/{project}/genes.jsonl` + `capsules.jsonl` |
| 3 ingest | `node evolver/scripts/a2a_ingest.js` | `genes.jsonl`, `capsules.jsonl` | `evolver/assets/gep/external_candidates.jsonl` |
| 4 distill | `build_ecc_skills.py` | `external_candidates.jsonl` | `evolved/{project}/` |

Each stage writes to disk. Inspect and resume from any stage.

## Requirements

- Node.js (for Stage 3 only — calls existing `evolver/scripts/a2a_ingest.js`)
- Python 3.11+
- `evolver/` directory present at repo root with `npm install` run

## Troubleshooting

**Stage 3 rejected=N, accepted=0**: Your JSONL has malformed JSON. Check `formatted/{project}/genes.jsonl` with `python3 -c "import json; [json.loads(l) for l in open('...').readlines() if l.strip()]"`.

**No skills in evolved/**: `build_ecc_skills.py` filters candidates by `a2a.source == "traj-{project}"`. If ingest ran with a different `A2A_SOURCE`, the filter won't match. Re-run ingest with the correct `A2A_SOURCE=traj-{project}`.

**No capsule commands generated**: Capsules need `confidence >= 0.4` post-factor (0.6×). Raw confidence ≥ 0.67 required. Only `task_shape` patterns with frequency ≥ 10 meet this bar (raw 0.75 × 0.6 = 0.45 ≥ 0.4). Lower-frequency patterns produce agents only.

## Running Tests

```bash
cd traj-evolver-v2 && python -m pytest tests/ -v
```

12 tests, no Node.js or API keys required.
```

- [ ] **Step 3: Run full test suite**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2 && python -m pytest tests/ -v --tb=short
```

Expected: `12 passed`.

- [ ] **Step 4: Run end-to-end smoke test — Stage 1 + 2**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2
make mine PROJECT=wzp
make format PROJECT=wzp
```

Verify:

```bash
python3 -c "
import json
from pathlib import Path
g = list(Path('formatted/wzp/genes.jsonl').open())
c = list(Path('formatted/wzp/capsules.jsonl').open())
assert len(g) > 0, 'No genes'
assert len(c) > 0, 'No capsules'
gene = json.loads(g[0])
assert gene['type'] == 'Gene', f'Expected Gene, got {gene[\"type\"]}'
assert 'asset_id' not in gene, 'asset_id should not be in output'
assert gene['a2a']['source'] == 'traj-wzp'
print(f'Stage 1+2 OK: {len(g)} genes, {len(c)} capsules')
"
```

Expected output: `Stage 1+2 OK: N genes, M capsules`

- [ ] **Step 5: Run Stage 3 (a2a_ingest)**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2
make ingest PROJECT=wzp
```

Verify:

```bash
python3 -c "
import json
from pathlib import Path
path = Path('../evolver/assets/gep/external_candidates.jsonl')
assert path.exists(), 'external_candidates.jsonl not found'
lines = [l for l in path.read_text().splitlines() if l.strip()]
wzp_lines = [l for l in lines if '\"traj-wzp\"' in l]
assert len(wzp_lines) > 0, 'No traj-wzp candidates found'
# Verify asset_id was computed by evolver
sample = json.loads(wzp_lines[0])
assert 'asset_id' in sample, 'evolver should have computed asset_id'
print(f'Stage 3 OK: {len(wzp_lines)} wzp candidates ingested')
"
```

Expected output: `Stage 3 OK: N wzp candidates ingested`

- [ ] **Step 6: Run Stage 4 (build ECC skills)**

```bash
cd /Users/xd/Desktop/work/project-logs/traj-evolver-v2
make distill PROJECT=wzp
```

Verify:

```bash
python3 -c "
from pathlib import Path
evolved = Path('../evolved/wzp')
assert evolved.exists()
assert (evolved / 'README.md').exists()
skills = list((evolved / 'skills').glob('*/SKILL.md'))
assert len(skills) > 0, f'No skills generated. Check ../evolver/assets/gep/external_candidates.jsonl for traj-wzp entries.'
print(f'Stage 4 OK: {len(skills)} skills in evolved/wzp/')
"
```

Expected output: `Stage 4 OK: N skills in evolved/wzp/`

---

## Self-Review

### Spec Coverage

| Spec Requirement | Covered By |
|---|---|
| Stage 2: format_patterns.py CLI | Task 2 |
| tool_sequence → Gene (workflow, signals_match from keywords) | Task 2 |
| phase_transition → Gene (workflow, signals_match from from-phase) | Task 2 |
| tool_fingerprint → Gene (platform, signals_match from fragments) | Task 2 |
| task_shape → Capsule (workflow, confidence from freq table) | Task 2 |
| correction_signal → Capsule (repair, confidence ≤ 0.45) | Task 2 |
| No asset_id in output (let evolver compute) | Task 2, test_no_asset_id_in_output |
| a2a.status + a2a.source + a2a.received_at present | Task 2 |
| Stage 3: a2a_ingest.js subprocess with A2A_SOURCE env | Task 4 Makefile |
| Stage 4: build_ecc_skills.py CLI | Task 3 |
| Gene → skills/<id>/SKILL.md with frontmatter | Task 3 |
| Capsule confidence ≥ 0.4 → commands/<id>.md | Task 3 |
| Capsule confidence < 0.4 → skipped from commands | Task 3 |
| Capsule cluster ≥ 3 same intent → agents/<intent>-agent.md | Task 3 |
| README.md in evolved/{project}/ | Task 3 |
| config.yaml | Task 1 |
| Makefile with mine/format/ingest/distill/pipeline/test/clean | Task 4 |
| README.md for traj-evolver-v2 | Task 4 |
| End-to-end smoke test | Task 4 |

### Placeholder Check

No TBDs, no "add appropriate handling", no "similar to" references. All code blocks are complete.

### Type Consistency

- `format_patterns(data, project, project_name) -> tuple[list[dict], list[dict]]` defined in Task 2, used in test Task 2 ✓
- `tool_sequence_to_gene(pattern, project, project_name) -> dict` consistent across test and implementation ✓
- `build_ecc_skills(evolver_dir, project, project_name, output_dir, patterns_stats) -> dict` defined in Task 3, tested in Task 3 ✓
- `load_candidates(evolver_dir, project) -> tuple[list[dict], list[dict]]` defined and used within Task 3 ✓
- `_safe_filename` vs `safe_id`: `format_patterns.py` uses `safe_id`; `build_ecc_skills.py` uses `_safe_filename` (private, same logic). No cross-file dependency. ✓
- `_make_gene` / `_make_capsule` / `_write_candidates` are test helpers defined only in `test_build_ecc.py` and only used there ✓
