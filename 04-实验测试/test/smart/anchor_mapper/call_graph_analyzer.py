"""
SMART Framework - Stage 4: Structural Anchor Mapper
Phase 1: AST-based call graph analysis.
Produces a list[CandidateSet] — one per subgoal, each containing candidate anchors.
"""
from __future__ import annotations

import ast
import sys
import os
from collections import deque

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
from models import FunctionInfo, CandidateSet


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_function_map(source_code: str) -> dict[str, FunctionInfo]:
    """Parse source_code and return a map of qualified name → FunctionInfo.

    Limitation: Only top-level functions and one-level-deep class methods are
    indexed. Nested classes (a ClassDef inside another ClassDef) are NOT
    recursed into, so methods defined inside a nested class will not appear in
    the function map. Anchors that fall inside such methods will therefore find
    no containing function and will be treated as orphans by analyze_call_graph,
    causing them to be added to every subgoal's candidate set via the
    conservative fallback.
    """
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
    queue: deque[str] = deque(entry_names)
    while queue:
        current = queue.popleft()
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
    if hasattr(anchor, "control_stmt_line"):
        return anchor.control_stmt_line
    raise TypeError(
        f"Unrecognized anchor type {type(anchor).__name__!r}: "
        "expected ModifiedLine (has .line_number) or ModifiedBranch (has .control_stmt_line)"
    )


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
