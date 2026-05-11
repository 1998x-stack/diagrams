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
