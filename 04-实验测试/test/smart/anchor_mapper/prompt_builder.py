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

# Stage 4 sys.modules collision guard:
# Three stages (ast_diff_parser, subgoal_generator, anchor_mapper) each have a `models.py`.
# This block fires once at import time and ensures `from models import ...` below
# loads Stage 4's models.py (anchor_mapper/models.py), not a previously-loaded stage's copy.
# NOTE: This approach relies on import ordering — anchor_mapper's tests load Stage 4 last.
# The orchestrator (anchor_mapper.py) uses the cleaner pinned-key strategy instead.
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
