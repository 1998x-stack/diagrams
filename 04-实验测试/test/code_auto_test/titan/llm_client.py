"""
LLM Client for TITAN-Snake
Wraps Claude API with Mock mode support for unit testing.
"""
from __future__ import annotations

import os
from typing import Optional


class LLMClient:
    """
    Claude API client with Mock mode.
    Set TITAN_MOCK_LLM=1 environment variable or pass mock=True to use mock mode.
    In mock mode, responses are returned from a preset queue (no API calls).
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        mock: Optional[bool] = None,
    ):
        self.model = model
        # Auto-detect mock mode from environment
        if mock is None:
            mock = os.environ.get("TITAN_MOCK_LLM", "0") == "1"
        self.mock = mock
        self._mock_responses: list[str] = []
        self._default_mock_response: str = "RIGHT"
        self._client = None

        if not self.mock:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize the Anthropic client (only in real mode)."""
        try:
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )
        except ImportError:
            raise ImportError(
                "anthropic package is required for real LLM mode. "
                "Run: pip install anthropic"
            )

    def set_mock_response(self, response: str) -> None:
        """Set a single mock response (used in tests)."""
        self._mock_responses = [response]

    def set_mock_responses(self, responses: list[str]) -> None:
        """Set a queue of mock responses (consumed in order, last one repeats)."""
        self._mock_responses = list(responses)

    def set_default_mock_response(self, response: str) -> None:
        """Set the fallback mock response when queue is empty."""
        self._default_mock_response = response

    def chat(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 512,
    ) -> str:
        """
        Send a chat message and return the response text.

        Args:
            system: System prompt
            messages: List of {"role": "user"|"assistant", "content": str}
            max_tokens: Max tokens in response

        Returns:
            Response text as string
        """
        if self.mock:
            return self._mock_chat()

        return self._real_chat(system, messages, max_tokens)

    def _mock_chat(self) -> str:
        """Return next mock response from queue, or default."""
        if self._mock_responses:
            response = self._mock_responses[0]
            if len(self._mock_responses) > 1:
                self._mock_responses.pop(0)
            return response
        return self._default_mock_response

    def _real_chat(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int,
    ) -> str:
        """Call the real Claude API."""
        if self._client is None:
            self._init_client()

        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            temperature=0,
        )
        return response.content[0].text

    def decide_action(
        self,
        abstract_state: dict,
        recommended_actions: list[str],
        system_context: str = "",
    ) -> str:
        """
        Ask LLM to choose the best action from recommended list.
        Returns a direction string: UP/DOWN/LEFT/RIGHT.
        Falls back to first recommended action on parse failure.
        """
        if not recommended_actions:
            return "RIGHT"  # fallback

        # Fast path: if only one option, no need to call LLM
        if len(recommended_actions) == 1:
            return recommended_actions[0]

        system = (
            "You are a snake game testing agent. "
            "Choose the best action to maximize coverage and find bugs. "
            "Reply with ONLY the action name, nothing else. "
            f"Valid actions: {', '.join(recommended_actions)}"
        )

        state_summary = (
            f"Direction: {abstract_state.get('direction', 'RIGHT')}, "
            f"Food: {abstract_state.get('food_direction', 'unknown')}, "
            f"Danger ahead: {abstract_state.get('danger_ahead', False)}, "
            f"Snake length: {abstract_state.get('snake_length', 'short')}"
        )

        if system_context:
            system = system_context + "\n\n" + system

        messages = [{"role": "user", "content": (
            f"Current state: {state_summary}\n"
            f"Recommended actions (in priority order): {recommended_actions}\n"
            f"Choose the best action."
        )}]

        response = self.chat(system, messages, max_tokens=10)
        # Parse the response: extract first valid direction
        response_upper = response.strip().upper()
        for action in ["UP", "DOWN", "LEFT", "RIGHT"]:
            if action in response_upper:
                if action in recommended_actions:
                    return action

        # Fallback to first recommended
        return recommended_actions[0]

    def reflect(
        self,
        abstract_state: dict,
        action_history: list[tuple],
        stall_count: int,
    ) -> dict:
        """
        Perform reflection on stalled state.
        Returns dict with 'suggested_actions' and 'is_bug' flag.
        """
        system = (
            "You are a TITAN testing agent for a snake game. "
            "Analyze why the agent is stuck and suggest what to do next. "
            "Format your response as:\n"
            "ACTIONS: UP,RIGHT,DOWN (comma-separated direction sequence)\n"
            "IS_BUG: yes/no\n"
            "REASON: brief explanation"
        )

        recent = action_history[-10:] if len(action_history) > 10 else action_history
        history_str = " → ".join(
            f"{a[1]}(score={a[2]})" for a in recent if len(a) >= 3
        )

        messages = [{"role": "user", "content": (
            f"State: {abstract_state}\n"
            f"Stalled for {stall_count} steps. Recent actions: {history_str}\n"
            "Analyze and suggest next actions."
        )}]

        response = self.chat(system, messages, max_tokens=100)
        return self._parse_reflection(response)

    def _parse_reflection(self, response: str) -> dict:
        """Parse reflection response into structured dict."""
        result = {
            "suggested_actions": [],
            "is_bug": False,
            "reason": response,
        }

        lines = response.strip().split('\n')
        for line in lines:
            if line.startswith("ACTIONS:"):
                raw = line.replace("ACTIONS:", "").strip()
                actions = [a.strip().upper() for a in raw.split(',')]
                valid = [a for a in actions if a in ("UP", "DOWN", "LEFT", "RIGHT")]
                result["suggested_actions"] = valid
            elif line.startswith("IS_BUG:"):
                val = line.replace("IS_BUG:", "").strip().lower()
                result["is_bug"] = val in ("yes", "true", "1")
            elif line.startswith("REASON:"):
                result["reason"] = line.replace("REASON:", "").strip()

        return result

    def generate_bug_report(
        self,
        bug_type: str,
        abstract_state: dict,
        evidence: dict,
    ) -> str:
        """Generate a human-readable bug report using LLM."""
        system = (
            "You are a QA engineer for a snake game. "
            "Write a concise bug report in Chinese and English. "
            "Be specific about what was observed vs expected."
        )

        messages = [{"role": "user", "content": (
            f"Bug type: {bug_type}\n"
            f"Game state: {abstract_state}\n"
            f"Evidence: {evidence}\n"
            "Write a bug report."
        )}]

        return self.chat(system, messages, max_tokens=200)
