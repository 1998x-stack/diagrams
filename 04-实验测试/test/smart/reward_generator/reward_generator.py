from __future__ import annotations
import os, sys
from typing import Optional
import anthropic

# client_factory and prompt_builder have no Stage3 model class identity concerns
_S3_PATH = os.path.dirname(os.path.abspath(__file__))
if _S3_PATH not in sys.path:
    sys.path.insert(0, _S3_PATH)
from client_factory import create_client
from prompt_builder import build_prompt


def generate_reward_rules(
    subgoal_sequence,
    observation_schema,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
):
    """
    Generate reward rules for a subgoal sequence using the Claude API.

    Stage3 model classes (RewardRuleSet, RewardGenerationError) are resolved
    lazily from sys.modules["models"] at call time. This ensures the class
    objects match the caller's imports when tests manipulate sys.modules.

    Args:
        subgoal_sequence: SubgoalSequence from Stage 2 (duck-typed).
        observation_schema: ObservationSchema describing game state variables.
        client: Anthropic client. If None, creates one using ANTHROPIC_API_KEY.
        model: Claude model to use.
        max_tokens: Maximum tokens for the response.
        use_thinking: If True, enables adaptive thinking.

    Returns:
        Validated RewardRuleSet Pydantic object.

    Raises:
        RewardGenerationError: If Claude refuses or returns an invalid response.
        EnvironmentError: If no API key is available and client is None.
    """
    # Lazy import: use whatever Stage3 models is current in sys.modules["models"].
    # This guarantees class identity with the caller — critical for isinstance/pytest.raises.
    _cached = sys.modules.get("models")
    if _cached and hasattr(_cached, "RewardRuleSet"):
        _m = _cached
    else:
        if "models" in sys.modules:
            del sys.modules["models"]
        if _S3_PATH not in sys.path:
            sys.path.insert(0, _S3_PATH)
        import models as _m  # type: ignore[import]

    RewardRuleSet = _m.RewardRuleSet
    RewardGenerationError = _m.RewardGenerationError

    if client is None:
        client = create_client()

    prompt = build_prompt(subgoal_sequence, observation_schema)

    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_format=RewardRuleSet,
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    response = client.messages.parse(**kwargs)

    if response.stop_reason == "refusal":
        raise RewardGenerationError(
            "Claude refused to generate reward rules.",
            stop_reason="refusal",
        )
    if response.parsed_output is None:
        raise RewardGenerationError(
            "Claude response did not parse to a valid RewardRuleSet.",
            stop_reason=response.stop_reason,
        )
    return response.parsed_output
