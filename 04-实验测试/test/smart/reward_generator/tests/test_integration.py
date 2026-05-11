"""
Phase 5: Integration test — real Claude API call.
Skipped automatically when ANTHROPIC_API_KEY is not set.
Run with: pytest tests/test_integration.py -v -s
"""
import os, sys
import pytest

# ── Stage 2 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator"))
from models import Subgoal, SubgoalSequence

# ── Stage 3 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import ObservableVariable, ObservationSchema, RewardRuleSet
from reward_generator import generate_reward_rules

needs_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API integration test",
)


def make_math_calc_subgoal_sequence() -> SubgoalSequence:
    """Synthetic subgoal sequence based on math calculator additions."""
    return SubgoalSequence(
        task_name="Math Calculator Extended",
        summary="Player uses the calculator to perform matrix operations and complex arithmetic.",
        subgoals=[
            Subgoal(
                index=1,
                description="Open the matrix calculator interface",
                rationale="MatrixCalculator class added in v2",
                anchor_hints=["MatrixCalculator"],
            ),
            Subgoal(
                index=2,
                description="Perform a determinant calculation on a 2x2 matrix",
                rationale="determinant method handles singular check",
                anchor_hints=["determinant/if_true"],
            ),
            Subgoal(
                index=3,
                description="Apply Taylor series expansion to a function",
                rationale="taylor_series function added in v2",
                anchor_hints=["taylor_series"],
            ),
        ],
    )


def make_math_calc_schema() -> ObservationSchema:
    """Observable variables for the math calculator game environment."""
    return ObservationSchema(variables=[
        ObservableVariable(
            name="calculator_mode",
            type="'basic'|'matrix'|'complex'|'calculus'",
            description="Current mode of the calculator",
        ),
        ObservableVariable(
            name="last_result",
            type="float",
            description="Result of the most recent calculation",
        ),
        ObservableVariable(
            name="operations_count",
            type="int",
            description="Number of operations performed so far",
        ),
        ObservableVariable(
            name="error_state",
            type="bool",
            description="True if the last operation raised an error",
        ),
    ])


@needs_key
def test_math_calc_produces_valid_reward_rules():
    """End-to-end: synthetic SubgoalSequence + ObservationSchema → RewardRuleSet."""
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    assert isinstance(result, RewardRuleSet)
    assert len(result.rules) == len(seq.subgoals)
    assert all(len(r.events) >= 1 for r in result.rules)


@needs_key
def test_math_calc_subgoal_indices_match():
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    expected_indices = {sg.index for sg in seq.subgoals}
    actual_indices = {r.subgoal_index for r in result.rules}
    assert actual_indices == expected_indices


@needs_key
def test_math_calc_conditions_reference_schema_variables():
    """Conditions should reference variables from the observation schema."""
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    variable_names = {v.name for v in schema.variables}
    all_conditions = " ".join(
        ev.condition for rule in result.rules for ev in rule.events
    )
    assert any(v in all_conditions for v in variable_names), (
        f"No schema variable found in conditions. Conditions: {all_conditions[:300]}"
    )


@needs_key
def test_math_calc_to_dict_serializable():
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "rules" in d
    assert len(d["rules"]) == len(seq.subgoals)


@needs_key
def test_math_calc_prints_readable_report(capsys):
    seq = make_math_calc_subgoal_sequence()
    schema = make_math_calc_schema()
    result = generate_reward_rules(seq, schema)
    print(f"\n{'='*60}")
    print(f"SMART Stage 3 — Reward Rule Report")
    print(f"Task: {result.task_name}")
    print(f"{'='*60}")
    for rule in result.rules:
        print(f"  [{rule.subgoal_index}] {rule.subgoal_description}")
        for ev in rule.events:
            print(f"       event: {ev.event} | reward: {ev.reward}")
            print(f"       cond:  {ev.condition}")
    print(f"{'='*60}")
    captured = capsys.readouterr()
    assert "Stage 3" in captured.out
