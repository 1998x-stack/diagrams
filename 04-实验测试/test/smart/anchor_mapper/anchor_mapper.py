"""
SMART Framework - Stage 4: Structural Anchor Mapper
Main entry point: orchestrates Phase 1 (call graph) + Phase 2 (LLM filter)
and returns a validated StructuralAnchorMap.
"""
from __future__ import annotations

import importlib.util
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

# Load the Stage 4 models module exactly once at anchor_mapper import time and pin it
# under a private stable key.  Use whatever is already in sys.modules["models"] if it
# is the Stage 4 models (has AnchorMappingError), so that callers who imported the
# Stage 4 models just before importing anchor_mapper share the same class objects.
# This guarantees class identity regardless of what other modules do to
# sys.modules["models"] between pytest collection and test execution.
_ANCHOR_MAPPER_MODELS_KEY = "_anchor_mapper_stage4_models"
if _ANCHOR_MAPPER_MODELS_KEY not in sys.modules:
    _existing = sys.modules.get("models")
    if _existing is not None and hasattr(_existing, "AnchorMappingError"):
        # Re-use the already-loaded Stage 4 models — same object the caller imported.
        _mod = _existing
    else:
        _spec = importlib.util.spec_from_file_location(
            _ANCHOR_MAPPER_MODELS_KEY,
            os.path.join(_S4_PATH, "models.py"),
        )
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
    sys.modules[_ANCHOR_MAPPER_MODELS_KEY] = _mod
_STAGE4_MODELS = sys.modules[_ANCHOR_MAPPER_MODELS_KEY]


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
    # Use the Stage 4 models module loaded once at anchor_mapper import time.
    # This guarantees class identity regardless of what other modules do to
    # sys.modules["models"] between collection and test execution.
    _m = _STAGE4_MODELS
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
