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


CYCLIC_SOURCE = """\
def alpha():
    return beta()

def beta():
    return alpha()

def gamma():
    return 99
"""

CHAIN_SOURCE = """\
def a():
    return b()

def b():
    return c()

def c():
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
        with pytest.raises(ValueError):
            analyze_call_graph(diff, seq, "")

    def test_bfs_terminates_on_mutual_recursion(self):
        """alpha calls beta, beta calls alpha — BFS must terminate without infinite loop."""
        diff = make_diff(lines=[
            ModifiedLine("test.py", 2, "added", "return beta()"),   # in alpha
            ModifiedLine("test.py", 5, "added", "return alpha()"),  # in beta
            ModifiedLine("test.py", 8, "added", "return 99"),       # in gamma (unreachable)
        ])
        seq = make_seq(["1"])  # hint '1' → alpha's line
        result = analyze_call_graph(diff, seq, CYCLIC_SOURCE)
        assert len(result) == 1
        line_nums = {getattr(c, 'line_number', None) for c in result[0].candidates}
        assert 2 in line_nums  # alpha's line is a candidate
        assert 5 in line_nums  # beta's line reachable via alpha→beta
        # gamma (line 8) may appear via the conservative orphan fallback; the key
        # assertion is that BFS terminates and alpha+beta lines ARE present.

    def test_bfs_follows_multi_hop_chain(self):
        """a calls b calls c — anchors in c are reachable from a via two hops."""
        diff = make_diff(lines=[
            ModifiedLine("test.py", 8, "added", "return 42"),  # in c
        ])
        seq = make_seq(["1"])  # hint '1' → a's line
        result = analyze_call_graph(diff, seq, CHAIN_SOURCE)
        assert len(result) == 1
        line_nums = {getattr(c, 'line_number', None) for c in result[0].candidates}
        assert 8 in line_nums  # c is reachable from a via a→b→c

    def test_returns_one_candidate_set_per_subgoal(self):
        diff = make_diff(lines=[ModifiedLine("test.py", 2, "added", "x")])
        seq = make_seq(["1"], ["4"], ["10"])
        result = analyze_call_graph(diff, seq, SIMPLE_SOURCE)
        assert len(result) == 3
        indices = [cs.subgoal_index for cs in result]
        assert indices == [1, 2, 3]

    def test_nested_class_method_falls_through_to_orphan_fallback(self):
        """
        _build_function_map only indexes top-level and one-level-deep class methods.
        A method inside a nested class (Outer.Inner.inner_method) is NOT indexed,
        so an anchor on its body line has no containing function and becomes an orphan.
        The conservative fallback must add it to every subgoal's candidate set.
        """
        NESTED_CLASS_SOURCE = """\
class Outer:
    class Inner:
        def inner_method(self):
            x = 1
"""
        # Anchor at line 4 — inside Inner.inner_method (not indexed by _build_function_map)
        diff = make_diff(lines=[ModifiedLine("test.py", 4, "added", "x = 1")])
        # One subgoal with no anchor_hints — so no BFS entry points at all
        seq = make_seq([])
        result = analyze_call_graph(diff, seq, NESTED_CLASS_SOURCE)
        assert len(result) == 1
        line_nums = {getattr(c, "line_number", None) for c in result[0].candidates}
        assert 4 in line_nums, (
            "Anchor inside a nested class method must appear via orphan fallback"
        )
