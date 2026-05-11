"""
SMART Framework - Stage 2: Subgoal Generator
Main entry point: calls Claude API and returns a validated SubgoalSequence.
"""
from __future__ import annotations

import os, sys
from typing import TYPE_CHECKING, Optional
import anthropic

_S2_PATH = os.path.dirname(os.path.abspath(__file__))
if _S2_PATH not in sys.path:
    sys.path.insert(0, _S2_PATH)
from client_factory import create_client
from prompt_builder import build_prompt

if TYPE_CHECKING:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ast_diff_parser"))
    from models import DiffResult


def generate_subgoals(
    diff_result: "DiffResult",
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    use_thinking: bool = False,
) -> "SubgoalSequence":  # type: ignore[name-defined]
    """
    Generate an ordered subgoal sequence from a Stage 1 DiffResult.

    Stage2 model classes (SubgoalSequence, SubgoalGenerationError) are resolved
    lazily from sys.modules["models"] at call time. This ensures class identity
    matches when tests manipulate sys.modules.

    Args:
        diff_result: Structural anchors (C_L, C_B) from ast_diff_parser.
        client: Anthropic client. If None, created via create_client().
        model: Claude model ID to use.
        max_tokens: Maximum output tokens.
        use_thinking: If True, enable adaptive thinking for deeper reasoning.

    Returns:
        SubgoalSequence — validated Pydantic object.

    Raises:
        EnvironmentError: If client is None and ANTHROPIC_API_KEY is not set.
        SubgoalGenerationError: If Claude refuses or output fails to parse.
        anthropic.APIStatusError: On API-level errors (caller handles retry).
    """
    # Lazy import: use whatever Stage2 models is current in sys.modules["models"].
    _cached = sys.modules.get("models")
    if _cached and hasattr(_cached, "SubgoalSequence"):
        _m = _cached
    else:
        if "models" in sys.modules:
            del sys.modules["models"]
        if _S2_PATH not in sys.path:
            sys.path.insert(0, _S2_PATH)
        import models as _m  # type: ignore[import]

    SubgoalSequence = _m.SubgoalSequence
    SubgoalGenerationError = _m.SubgoalGenerationError

    if client is None:
        client = create_client()

    prompt = build_prompt(diff_result)

    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_format=SubgoalSequence,
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    response = client.messages.parse(**kwargs)

    if response.stop_reason == "refusal":
        raise SubgoalGenerationError(
            "Claude refused to generate subgoals for this diff.",
            stop_reason="refusal",
        )
    if response.parsed_output is None:
        raise SubgoalGenerationError(
            "Claude response did not parse to a valid SubgoalSequence.",
            stop_reason=response.stop_reason,
        )
    return response.parsed_output
