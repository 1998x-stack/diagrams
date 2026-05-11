"""
Phase 5: Integration test — real Claude API call.
Skipped automatically when ANTHROPIC_API_KEY is not set.
Run with: pytest tests/test_integration.py -v -s
"""
import os, sys
import pytest

# Stage 2 imports FIRST (before 'models' is cached as stage1)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import SubgoalSequence, Subgoal
from subgoal_generator import generate_subgoals

# Clear 'models' cache so stage1 modules load correctly
if "models" in sys.modules:
    del sys.modules["models"]

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from diff_parser import parse_diff_files

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser", "tests", "fixtures")
V1_PATH = os.path.join(FIXTURES, "math_calc_v1.py")
V2_PATH = os.path.join(FIXTURES, "math_calc_v2.py")

needs_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API integration test"
)


@needs_key
def test_real_api_returns_subgoal_sequence():
    """Full pipeline: math_calc v1→v2 diff → Claude API → SubgoalSequence."""
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    assert isinstance(seq, SubgoalSequence)


@needs_key
def test_real_api_subgoals_nonempty():
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    assert len(seq.subgoals) >= 2


@needs_key
def test_real_api_subgoals_reference_diff_content():
    """Subgoal descriptions must mention new components from v2."""
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    all_text = " ".join(s.description + " " + s.rationale for s in seq.subgoals).lower()
    keywords = ["matrix", "complex", "taylor", "integrate", "derivative"]
    assert any(kw in all_text for kw in keywords), (
        f"No expected keyword found in subgoals. Got: {all_text[:200]}"
    )


@needs_key
def test_real_api_subgoals_have_anchor_hints():
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    hints = [s for s in seq.subgoals if s.anchor_hints]
    assert len(hints) >= 1


@needs_key
def test_real_api_to_dict_serializable():
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    d = seq.to_dict()
    assert isinstance(d, dict)
    assert len(d["subgoals"]) >= 1


@needs_key
def test_real_api_prints_readable_report(capsys):
    diff_result = parse_diff_files(V1_PATH, V2_PATH)
    seq = generate_subgoals(diff_result)
    print(f"\n{'='*60}")
    print(f"SMART Stage 2 — Subgoal Report")
    print(f"Task: {seq.task_name}")
    print(f"Summary: {seq.summary}")
    print(f"{'='*60}")
    for sg in seq.subgoals:
        print(f"  [{sg.index}] {sg.description}")
        if sg.anchor_hints:
            print(f"       anchors: {', '.join(sg.anchor_hints)}")
    print(f"{'='*60}")
    captured = capsys.readouterr()
    assert "Stage 2" in captured.out
