"""
LLM Client and Wordle Agent.
Wraps the Anthropic Claude API with retry logic.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import anthropic

from wordle.engine import GameState, GameStatus, WordleEngine
from agent.prompts import PromptBuilder, PromptStrategy, parse_action

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Thin wrapper around Claude API.
    Handles retries and basic error logging.
    """

    def __init__(
        self,
        model: str = "claude-opus-4-6",
        max_tokens: int = 1024,
        temperature: float = 1.0,
    ) -> None:
        self._client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def complete(self, prompt: str) -> str:
        """Single API call. Raises on failure."""
        message = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def complete_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        """Retry on transient errors with exponential backoff."""
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return self.complete(prompt)
            except anthropic.RateLimitError as e:
                last_error = e
                wait = retry_delay * (2 ** attempt)
                logger.warning(f"Rate limit hit, retrying in {wait:.1f}s (attempt {attempt+1})")
                time.sleep(wait)
            except anthropic.APIError as e:
                last_error = e
                logger.error(f"API error on attempt {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        raise RuntimeError(f"LLM call failed after {max_retries} attempts") from last_error


class WordleAgent:
    """
    Complete LLM Agent that plays Wordle.
    Combines: PromptBuilder + LLMClient + action parsing.
    """

    # Fallback words if LLM produces unparseable output
    _FALLBACK_WORDS = ["CRANE", "SLATE", "ARISE", "STARE", "SNARE"]

    def __init__(
        self,
        strategy: PromptStrategy,
        llm_client: LLMClient,
    ) -> None:
        self.strategy = strategy
        self._llm = llm_client
        self._prompt_builder = PromptBuilder()

    def make_guess(self, state: GameState, max_retries: int = 3) -> str:
        """
        Ask the LLM for a 5-letter word guess given current game state.
        Retries if LLM produces invalid output.
        Returns an uppercase 5-letter word.
        """
        for attempt in range(max_retries):
            prompt = self._prompt_builder.build(state, self.strategy)
            try:
                response = self._llm.complete_with_retry(prompt)
                word = parse_action(response)
                if word and len(word) == 5 and word.isalpha():
                    logger.debug(f"[{self.strategy.value}] Guess: {word} (attempt {attempt+1})")
                    return word
                logger.warning(f"Could not parse word from response (attempt {attempt+1}): {response[:100]}")
            except Exception as e:
                logger.error(f"LLM error on attempt {attempt+1}: {e}")

        # Last resort fallback
        for word in self._FALLBACK_WORDS:
            if word not in state.guesses_made:
                logger.warning(f"Using fallback word: {word}")
                return word
        return "CRANE"

    def play_game(self, engine: WordleEngine) -> int:
        """
        Play a complete game. Returns number of guesses used.
        Returns -1 if the game was lost (exceeded max guesses).
        """
        while not engine.is_finished():
            state = engine.get_state()
            word = self.make_guess(state)
            try:
                engine.guess(word)
            except ValueError as e:
                # Word was rejected by engine (invalid), try fallback
                logger.warning(f"Invalid guess '{word}': {e}. Trying fallback.")
                for fallback in self._FALLBACK_WORDS:
                    if fallback not in engine.get_state().guesses_made:
                        engine.guess(fallback)
                        break

        state = engine.get_state()
        if engine.is_won():
            return state.num_guesses
        return -1  # Lost
