"""Phase 5 tests: anchor mapper orchestrator with mock Anthropic client."""
import os, sys
import pytest
from unittest.mock import MagicMock

# Stage 1 imports FIRST
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ast_diff_parser"))
from models import DiffResult, ModifiedLine, ModifiedBranch

# Stage 2 imports SECOND (loaded via importlib to avoid clobbering sys.modules["models"])
import importlib.util as _ilu
_s2_spec = _ilu.spec_from_file_location(
    "_s2_models",
    os.path.join(os.path.dirname(__file__), "..", "..", "subgoal_generator", "models.py"),
)
_s2 = _ilu.module_from_spec(_s2_spec)
_s2_spec.loader.exec_module(_s2)
Subgoal = _s2.Subgoal
SubgoalSequence = _s2.SubgoalSequence

# Stage 4 imports LAST — sys.modules["models"] = Stage 4 at call time
if "models" in sys.modules:
    del sys.modules["models"]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import AnchorMapping, StructuralAnchorMap, AnchorMappingError
from anchor_mapper import generate_anchor_map
from prompt_builder import FilterResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

# Inline source matching the anchors below
# Line 1: def compute(x):
# Line 2:     if x > 0:
# Line 3:         return x
# Line 4:     return -x
COMPUTE_SOURCE = """\
def compute(x):
    if x > 0:
        return x
    return -x
"""


def make_diff() -> DiffResult:
    return DiffResult(
        file_path="compute.py",
        modified_lines=[ModifiedLine("compute.py", 3, "added", "return x")],
        modified_branches=[ModifiedBranch("compute.py", 2, "if_true", "x > 0")],
    )


def make_seq() -> SubgoalSequence:
    return SubgoalSequence(
        task_name="Compute Task",
        summary="Test compute function with if branch.",
        subgoals=[
            Subgoal(index=1, description="Trigger positive branch", rationale="line 2",
                    anchor_hints=["2"]),
        ],
    )


def make_mock_client(relevant_keys=None, stop_reason="end_turn") -> MagicMock:
    mock_response = MagicMock()
    mock_response.stop_reason = stop_reason
    if stop_reason == "refusal":
        mock_response.parsed_output = None
    else:
        mock_response.parsed_output = FilterResult(
            relevant_keys=relevant_keys if relevant_keys is not None else ["L:3", "B:2:if_true"],
            rationale="Both relevant to subgoal 1",
        )
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client


def make_two_subgoal_seq() -> SubgoalSequence:
    """Two subgoals, both pointing to the same function (line 1 = compute's def line)."""
    return SubgoalSequence(
        task_name="Compute Task",
        summary="Two subgoals for the same function.",
        subgoals=[
            Subgoal(index=1, description="Check positive path", rationale="line 2",
                    anchor_hints=["2"]),
            Subgoal(index=2, description="Check negative path", rationale="line 2",
                    anchor_hints=["2"]),
        ],
    )


def make_two_call_mock_client() -> MagicMock:
    """Returns L:3 as relevant for both calls (simulates shared anchor across subgoals)."""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.parsed_output = FilterResult(
        relevant_keys=["L:3"],
        rationale="Relevant to this subgoal",
    )
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = mock_response
    return mock_client


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestGenerateAnchorMapHappyPath:
    def test_returns_structural_anchor_map(self):
        client = make_mock_client()
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert isinstance(result, StructuralAnchorMap)

    def test_task_name_and_file_path_set(self):
        client = make_mock_client()
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert result.task_name == "Compute Task"
        assert result.file_path == "compute.py"

    def test_mappings_contain_relevant_anchors(self):
        client = make_mock_client(relevant_keys=["L:3"])
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        keys = {m.anchor_key for m in result.mappings}
        assert "L:3" in keys

    def test_for_subgoal_returns_relevant_anchors(self):
        client = make_mock_client(relevant_keys=["L:3"])
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        sg1_anchors = result.for_subgoal(1)
        assert len(sg1_anchors) >= 1
        assert all(1 in a.subgoal_indices for a in sg1_anchors)

    def test_calls_messages_parse_once_per_nonempty_candidate_set(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert client.messages.parse.call_count == 1

    def test_passes_model_to_api(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE,
                            client=client, model="claude-opus-4-6")
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("model") == "claude-opus-4-6"

    def test_passes_output_format(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("output_format") is FilterResult

    def test_use_thinking_adds_kwargs(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE,
                            client=client, use_thinking=True)
        call_kwargs = client.messages.parse.call_args[1]
        assert call_kwargs.get("thinking") == {"type": "adaptive"}

    def test_no_thinking_by_default(self):
        client = make_mock_client()
        generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        call_kwargs = client.messages.parse.call_args[1]
        assert "thinking" not in call_kwargs

    def test_to_dict_on_result(self):
        client = make_mock_client()
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "mappings" in d

    def test_hallucinated_key_discarded(self):
        client = make_mock_client(relevant_keys=["L:3", "L:999"])  # L:999 not in diff
        result = generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        keys = {m.anchor_key for m in result.mappings}
        assert "L:999" not in keys

    def test_empty_candidate_sets_returns_empty_mappings(self):
        """Empty diff → no candidates → no LLM calls → empty mappings."""
        empty_diff = DiffResult(file_path="compute.py", modified_lines=[], modified_branches=[])
        client = make_mock_client()
        result = generate_anchor_map(empty_diff, make_seq(), COMPUTE_SOURCE, client=client)
        assert result.mappings == []
        assert client.messages.parse.call_count == 0

    def test_shared_anchor_accumulates_across_subgoals(self):
        """An anchor relevant to both subgoals gets subgoal_indices=[1, 2]."""
        client = make_two_call_mock_client()
        result = generate_anchor_map(make_diff(), make_two_subgoal_seq(), COMPUTE_SOURCE, client=client)
        # L:3 should appear in subgoals 1 AND 2
        l3_mappings = [m for m in result.mappings if m.anchor_key == "L:3"]
        assert len(l3_mappings) == 1, "L:3 should appear exactly once as a mapping"
        assert 1 in l3_mappings[0].subgoal_indices
        assert 2 in l3_mappings[0].subgoal_indices
        assert client.messages.parse.call_count == 2  # one call per subgoal


class TestGenerateAnchorMapErrorHandling:
    def test_refusal_raises_anchor_mapping_error(self):
        client = make_mock_client(stop_reason="refusal")
        with pytest.raises(AnchorMappingError) as exc_info:
            generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=client)
        assert exc_info.value.stop_reason == "refusal"

    def test_none_parsed_output_raises_error(self):
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.parsed_output = None
        mock_client = MagicMock()
        mock_client.messages.parse.return_value = mock_response
        with pytest.raises(AnchorMappingError):
            generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=mock_client)

    def test_phase1_value_error_raises_anchor_mapping_error(self):
        """ValueError from analyze_call_graph is wrapped in AnchorMappingError."""
        from unittest.mock import patch
        with patch("anchor_mapper.analyze_call_graph", side_effect=ValueError("empty source")):
            with pytest.raises(AnchorMappingError, match="empty source"):
                generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=make_mock_client())

    def test_api_error_propagates(self):
        import anthropic
        mock_client = MagicMock()
        mock_client.messages.parse.side_effect = anthropic.APIStatusError(
            message="server error",
            response=MagicMock(status_code=500),
            body={},
        )
        with pytest.raises(anthropic.APIStatusError):
            generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE, client=mock_client)


class TestGenerateAnchorMapClientFactory:
    def test_no_client_raises_env_error_when_no_key(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError):
                generate_anchor_map(make_diff(), make_seq(), COMPUTE_SOURCE)
