"""Phase 4 tests: reward_generator with mock Anthropic client."""
import os, sys
import pytest
from unittest.mock import MagicMock

# ── Stage 2 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator"))
from models import Subgoal, SubgoalSequence

# ── Stage 3 imports ──────────────────────────────────────────────────────────
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import (
    ObservableVariable, ObservationSchema,
    RewardEvent, RewardRule, RewardRuleSet,
    RewardGenerationError,
)
from reward_generator import generate_reward_rules


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_subgoal_sequence() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Test Task",
        summary="A test task with two steps.",
        subgoals=[
            Subgoal(index=1, description="Do the first thing", rationale="line 10"),
            Subgoal(index=2, description="Do the second thing", rationale="line 20"),
        ],
    )


def make_observation_schema() -> ObservationSchema:
    return ObservationSchema(variables=[
        ObservableVariable(name="score", type="int", description="Player score"),
    ])


def make_reward_rule_set() -> RewardRuleSet:
    return RewardRuleSet(
        task_name="Test Task",
        rules=[
            RewardRule(
                subgoal_index=1,
                subgoal_description="Do the first thing",
                events=[RewardEvent(event="step1", condition="score > 0", reward=1.0,
                                    description="First step done")],
            ),
            RewardRule(
                subgoal_index=2,
                subgoal_description="Do the second thing",
                events=[RewardEvent(event="step2", condition="score > 10", reward=10.0,
                                    description="Second step done")],
            ),
        ],
    )


def make_mock_client(reward_rule_set: RewardRuleSet, stop_reason: str = "end_turn") -> MagicMock:
    mock_response = MagicMock()
    mock_response.parsed_output = reward_rule_set
    mock_response.stop_reason = stop_reason
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client


# ── Tests ────────────────────────────────────────────────────────────────────

class TestGenerateRewardRulesHappyPath:
    def test_returns_reward_rule_set(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        result = generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert isinstance(result, RewardRuleSet)

    def test_rules_preserved(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        result = generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert len(result.rules) == 2

    def test_calls_messages_parse(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert client.messages.parse.called

    def test_passes_model_to_api(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(),
                               client=client, model="claude-opus-4-6")
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("model") == "claude-opus-4-6"

    def test_passes_output_format(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("output_format") is RewardRuleSet

    def test_uses_thinking_when_requested(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(),
                               client=client, use_thinking=True)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("thinking") == {"type": "adaptive"}

    def test_no_thinking_by_default(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert "thinking" not in call_kwargs

    def test_to_dict_on_result(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs)
        result = generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert len(d["rules"]) == 2


class TestGenerateRewardRulesErrorHandling:
    def test_refusal_raises_error(self):
        rs = make_reward_rule_set()
        client = make_mock_client(rs, stop_reason="refusal")
        with pytest.raises(RewardGenerationError) as exc_info:
            generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=client)
        assert exc_info.value.stop_reason == "refusal"

    def test_none_parsed_output_raises_error(self):
        mock_response = MagicMock()
        mock_response.parsed_output = None
        mock_response.stop_reason = "end_turn"
        mock_client = MagicMock()
        mock_client.messages.parse.return_value = mock_response
        with pytest.raises(RewardGenerationError):
            generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=mock_client)

    def test_api_error_propagates(self):
        import anthropic
        mock_client = MagicMock()
        mock_client.messages.parse.side_effect = anthropic.APIStatusError(
            message="server error",
            response=MagicMock(status_code=500),
            body={},
        )
        with pytest.raises(anthropic.APIStatusError):
            generate_reward_rules(make_subgoal_sequence(), make_observation_schema(), client=mock_client)


class TestGenerateRewardRulesClientFactory:
    def test_no_client_raises_env_error_when_no_key(self):
        """When client=None and no API key set, EnvironmentError from factory."""
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError):
                generate_reward_rules(make_subgoal_sequence(), make_observation_schema())
