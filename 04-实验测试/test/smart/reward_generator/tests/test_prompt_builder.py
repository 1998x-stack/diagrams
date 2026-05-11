"""Phase 3 tests: SubgoalSequence + ObservationSchema → prompt string."""
import os, sys
import pytest

# ── Stage 2 imports ──────────────────────────────────────────────────────────
# Clear any cached 'models' from Stage 1 first
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator"))
from models import Subgoal, SubgoalSequence

# ── Stage 3 imports ──────────────────────────────────────────────────────────
# Clear Stage 2 'models' cache before loading Stage 3 models
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import ObservableVariable, ObservationSchema
from prompt_builder import build_prompt


def make_subgoal_sequence() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Pizza Quest",
        summary="Player assembles and delivers an onion pizza.",
        subgoals=[
            Subgoal(index=1, description="Obtain and chop a tomato", rationale="line 45"),
            Subgoal(index=2, description="Place pizza in the oven", rationale="line 52",
                    anchor_hints=["52/if_true"]),
        ],
    )


def make_observation_schema() -> ObservationSchema:
    return ObservationSchema(variables=[
        ObservableVariable(name="inventory", type="list[str]", description="Items the player carries"),
        ObservableVariable(name="oven_state", type="'raw'|'baking'|'done'", description="State of the oven"),
        ObservableVariable(name="score", type="int", description="Current score"),
    ])


class TestBuildPromptStructure:
    def test_returns_string(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert isinstance(prompt, str)

    def test_contains_task_name(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Pizza Quest" in prompt

    def test_contains_subgoal_description(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Obtain and chop a tomato" in prompt

    def test_contains_subgoal_index(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "1" in prompt

    def test_contains_rationale(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "line 45" in prompt

    def test_contains_anchor_hints(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "52/if_true" in prompt

    def test_contains_observation_variable_names(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "inventory" in prompt
        assert "oven_state" in prompt
        assert "score" in prompt

    def test_contains_variable_types(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "list[str]" in prompt

    def test_contains_variable_descriptions(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Items the player carries" in prompt

    def test_contains_reward_rules_instructions(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "RewardRuleSet" in prompt or "reward" in prompt.lower()

    def test_contains_subgoal_section_header(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "SUBGOAL" in prompt.upper()

    def test_contains_observation_section_header(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "OBSERVATION" in prompt.upper() or "SCHEMA" in prompt.upper()

    def test_prompt_non_empty(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert len(prompt) > 100

    def test_subgoal_index_match_instruction(self):
        """Prompt must tell the LLM that subgoal_index must match the subgoal index."""
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "subgoal_index" in prompt or "index" in prompt

    def test_both_subgoals_present(self):
        prompt = build_prompt(make_subgoal_sequence(), make_observation_schema())
        assert "Place pizza in the oven" in prompt
