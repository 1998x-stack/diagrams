"""
SMART Framework - Stage 2: Subgoal Generator
Client factory: creates an Anthropic SDK client from env var or explicit key.
"""
import os
from typing import Optional
import anthropic


def create_client(api_key: Optional[str] = None) -> anthropic.Anthropic:
    """
    Create an Anthropic client.

    Args:
        api_key: Explicit API key. If None, reads ANTHROPIC_API_KEY env var.

    Returns:
        anthropic.Anthropic instance.
        SDK default: max_retries=2 (handles 429 and 5xx automatically).

    Raises:
        EnvironmentError: If no API key is available from either source.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Pass api_key= explicitly or export ANTHROPIC_API_KEY before running."
        )
    return anthropic.Anthropic(api_key=key)
