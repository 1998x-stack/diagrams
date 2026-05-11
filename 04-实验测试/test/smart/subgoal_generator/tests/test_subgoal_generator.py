"""Phase 4 tests: subgoal generator with mock Anthropic client."""
import os, sys
import pytest
from unittest.mock import MagicMock, patch

# Stage 1 imports FIRST — load DiffResult without polluting sys.modules["models"] for Stage 2
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch

# Stage 2 imports LAST — so sys.modules["models"] = Stage2 at call time (needed for lazy import)
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Subgoal, SubgoalSequence, SubgoalGenerationError
from subgoal_generator import generate_subgoals


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_diff_result() -> DiffResult:
    return DiffResult(
        file_path="test.py",
        modified_lines=[ModifiedLine("test.py", 10, "added", "class Foo: pass")],
        modified_branches=[ModifiedBranch("test.py", 20, "if_true", "x > 0")],
    )


def make_subgoal_sequence() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Test Task",
        summary="A test task with two steps.",
        subgoals=[
            Subgoal(index=1, description="Do the first thing", rationale="line 10",
                    anchor_hints=["10"]),
            Subgoal(index=2, description="Do the second thing", rationale="line 20",
                    anchor_hints=["20/if_true"]),
        ],
    )


def make_mock_client(seq: SubgoalSequence, stop_reason: str = "end_turn") -> MagicMock:
    mock_response = MagicMock()
    mock_response.parsed_output = seq
    mock_response.stop_reason = stop_reason
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client


# ── Tests ────────────────────────────────────────────────────────────────────

class TestGenerateSubgoalsHappyPath:
    def test_returns_subgoal_sequence(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        result = generate_subgoals(make_diff_result(), client=client)
        assert isinstance(result, SubgoalSequence)

    def test_subgoals_preserved(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        result = generate_subgoals(make_diff_result(), client=client)
        assert len(result.subgoals) == 2
        assert result.subgoals[0].index == 1

    def test_calls_messages_parse(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client)
        assert client.messages.parse.called

    def test_passes_model_to_api(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client, model="claude-opus-4-6")
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("model") == "claude-opus-4-6"

    def test_passes_output_format(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("output_format") is SubgoalSequence

    def test_uses_thinking_when_requested(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client, use_thinking=True)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("thinking") == {"type": "adaptive"}

    def test_no_thinking_by_default(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        generate_subgoals(make_diff_result(), client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert "thinking" not in call_kwargs

    def test_to_dict_on_result(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq)
        result = generate_subgoals(make_diff_result(), client=client)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert len(d["subgoals"]) == 2


class TestGenerateSubgoalsErrorHandling:
    def test_refusal_raises_error(self):
        seq = make_subgoal_sequence()
        client = make_mock_client(seq, stop_reason="refusal")
        with pytest.raises(SubgoalGenerationError) as exc_info:
            generate_subgoals(make_diff_result(), client=client)
        assert exc_info.value.stop_reason == "refusal"

    def test_none_parsed_output_raises_error(self):
        mock_response = MagicMock()
        mock_response.parsed_output = None
        mock_response.stop_reason = "end_turn"
        mock_client = MagicMock()
        mock_client.messages.parse.return_value = mock_response
        with pytest.raises(SubgoalGenerationError):
            generate_subgoals(make_diff_result(), client=mock_client)

    def test_api_error_propagates(self):
        import anthropic
        mock_client = MagicMock()
        mock_client.messages.parse.side_effect = anthropic.APIStatusError(
            message="server error",
            response=MagicMock(status_code=500),
            body={},
        )
        with pytest.raises(anthropic.APIStatusError):
            generate_subgoals(make_diff_result(), client=mock_client)


class TestGenerateSubgoalsClientFactory:
    def test_no_client_raises_env_error_when_no_key(self):
        """When client=None and no API key set, EnvironmentError from factory."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError):
                generate_subgoals(make_diff_result())
