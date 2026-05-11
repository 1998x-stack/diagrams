from __future__ import annotations
import sys, os

# Ensure Stage 3 models.py (this package) is resolved correctly.
_S3_PATH = os.path.dirname(os.path.abspath(__file__))
if _S3_PATH not in sys.path:
    sys.path.insert(0, _S3_PATH)

# Only reload if the cached 'models' isn't Stage3 (missing ObservationSchema).
if not (sys.modules.get("models") and hasattr(sys.modules["models"], "ObservationSchema")):
    if "models" in sys.modules:
        del sys.modules["models"]
from models import ObservationSchema


def build_prompt(subgoal_sequence, observation_schema: ObservationSchema) -> str:
    """
    Build the prompt for the LLM to generate a RewardRuleSet.

    Args:
        subgoal_sequence: SubgoalSequence from Stage 2 (duck-typed).
        observation_schema: ObservationSchema describing game state variables.

    Returns:
        Formatted prompt string.
    """
    lines = [
        "You are a reinforcement learning reward engineer for a game testing system.",
        "Given the subgoal sequence and observable state variables below, generate",
        "a RewardRuleSet with one RewardRule per subgoal.",
        "",
        "Rules:",
        "1. Each RewardRule must have at least one RewardEvent.",
        "2. Conditions must only reference variables listed in the ObservationSchema.",
        "3. Use progressive rewards: small rewards for intermediate events,",
        "   large rewards for subgoal completion (typically 10x the intermediate reward).",
        "4. Conditions must be expressed as readable predicate strings (not code).",
        "5. subgoal_index must match the index field from the subgoal list exactly.",
        "",
        "=== SUBGOAL SEQUENCE ===",
        f"Task: {subgoal_sequence.task_name}",
        f"Summary: {subgoal_sequence.summary}",
    ]

    for sg in subgoal_sequence.subgoals:
        anchors = ", ".join(sg.anchor_hints) if sg.anchor_hints else "none"
        lines.append(f"{sg.index:>3}. {sg.description}")
        lines.append(f"     rationale: {sg.rationale}")
        lines.append(f"     anchors: {anchors}")

    lines.append("")
    lines.append("=== OBSERVATION SCHEMA ===")

    for var in observation_schema.variables:
        lines.append(f"{var.name}: {var.type} — {var.description}")

    lines.append("=== END ===")
    lines.append("")
    lines.append("Respond with a valid RewardRuleSet JSON object.")

    return "\n".join(lines)
