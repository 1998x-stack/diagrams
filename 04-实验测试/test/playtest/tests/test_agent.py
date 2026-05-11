"""
Phase 2 Test Suite — LLM Agent Interface
All tests use Mock LLM (no real API calls).
Must all pass before proceeding to Phase 3.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent.prompts import (
    COT_INSTRUCTIONS,
    COT_PLUS_STRATEGIES,
    GAME_RULE,
    PromptBuilder,
    PromptStrategy,
    parse_action,
    serialize_state,
)
from agent.llm_client import LLMClient, WordleAgent
from wordle.engine import GameState, GameStatus, LetterStatus, GuessResult, WordleEngine


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_state_after_guesses(target: str, guesses: list[str]) -> GameState:
    """Run guesses against engine and return resulting state."""
    engine = WordleEngine(target, max_guesses=12)
    for g in guesses:
        engine.guess(g)
    return engine.get_state()


# ─── test_state_serialization ───────────────────────────────────────────────────

class TestStateSerialization:
    """test_state_serialization: GameState serializes to LLM-readable text."""

    def test_no_guesses_yet(self):
        state = GameState()
        text = serialize_state(state)
        assert "first guess" in text.lower() or "no guesses" in text.lower()

    def test_letters_formatted_as_list(self):
        # After guessing CRANE on target STARE
        state = make_state_after_guesses("STARE", ["CRANE"])
        text = serialize_state(state)
        # Letters should appear as [C, R, A, N, E], not "CRANE"
        assert "[C, R, A, N, E]" in text

    def test_correct_position_shown(self):
        # Target: CRANE, Guess: CRANE → E at position 4 is correct
        state = make_state_after_guesses("CRANE", ["CRANE"])
        text = serialize_state(state)
        assert "E" in text

    def test_wrong_position_shown(self):
        # Target: STARE, Guess: CRANE → A at pos 2 is in STARE (wrong pos)
        state = make_state_after_guesses("STARE", ["CRANE"])
        text = serialize_state(state)
        assert "wrong position" in text.lower() or "wrong" in text.lower()

    def test_incorrect_letters_shown(self):
        # Target: STARE, Guess: FILMS → F,I,L,M,S not in STARE (well, S is)
        state = make_state_after_guesses("STARE", ["FILMS"])
        text = serialize_state(state)
        assert "Incorrect letters" in text

    def test_guesses_count_shown(self):
        state = make_state_after_guesses("CRANE", ["SLATE", "ABOVE"])
        text = serialize_state(state)
        assert "2" in text


# ─── test_action_parsing ────────────────────────────────────────────────────────

class TestActionParsing:
    """test_action_parsing: Extract 5-letter word from LLM responses."""

    def test_plain_word(self):
        assert parse_action("CRANE") == "CRANE"

    def test_lowercase(self):
        assert parse_action("crane") == "CRANE"

    def test_word_with_explanation(self):
        response = "Based on my analysis, my next guess is CRANE."
        assert parse_action(response) == "CRANE"

    def test_word_in_quotes(self):
        assert parse_action("'CRANE'") == "CRANE"
        assert parse_action('"CRANE"') == "CRANE"

    def test_word_on_last_line(self):
        response = "Let me think...\nI'll try SLATE\nCRANE"
        assert parse_action(response) == "CRANE"

    def test_cot_style_response(self):
        response = """
Step 1: Known letters - none
Step 2: Try a word with common letters
Step 3: My best guess is SLATE

SLATE
"""
        assert parse_action(response) == "SLATE"


class TestActionParsingEdgeCases:
    """test_action_parsing_edge_cases: Handle tricky formats."""

    def test_mixed_case(self):
        assert parse_action("Crane") == "CRANE"

    def test_with_trailing_newline(self):
        assert parse_action("CRANE\n") == "CRANE"

    def test_with_period(self):
        assert parse_action("CRANE.") == "CRANE"

    def test_multiple_words_picks_last(self):
        # Should pick last 5-letter word (the conclusion)
        response = "From SLATE to CRANE is my answer"
        result = parse_action(response)
        assert result in ("SLATE", "CRANE")

    def test_no_valid_word_returns_none(self):
        # No 5-letter word present — only short words
        assert parse_action("I do not know.") is None

    def test_too_long_word_ignored(self):
        result = parse_action("CRANES")
        # CRANES is 6 letters, should be ignored
        assert result != "CRANES"

    def test_all_numbers_returns_none(self):
        assert parse_action("12345") is None


# ─── test_prompt_building ───────────────────────────────────────────────────────

class TestPromptBuildingZeroShot:
    """test_prompt_building_zs: Zero-Shot prompt contains Game Rule and state."""

    def setup_method(self):
        self.builder = PromptBuilder()
        self.state = GameState()

    def test_contains_game_rule(self):
        prompt = self.builder.build(self.state, PromptStrategy.ZERO_SHOT)
        assert "word guessing" in prompt.lower() or "wordle" in prompt.lower()

    def test_no_cot_instructions(self):
        prompt = self.builder.build(self.state, PromptStrategy.ZERO_SHOT)
        assert COT_INSTRUCTIONS not in prompt

    def test_no_strategies(self):
        prompt = self.builder.build(self.state, PromptStrategy.ZERO_SHOT)
        assert COT_PLUS_STRATEGIES not in prompt

    def test_contains_output_format(self):
        prompt = self.builder.build(self.state, PromptStrategy.ZERO_SHOT)
        assert "guess" in prompt.lower()


class TestPromptBuildingCoT:
    """test_prompt_building_cot: CoT prompt includes reasoning steps."""

    def setup_method(self):
        self.builder = PromptBuilder()
        self.state = GameState()

    def test_contains_cot_instructions(self):
        prompt = self.builder.build(self.state, PromptStrategy.COT)
        assert "step" in prompt.lower()

    def test_no_strategies(self):
        prompt = self.builder.build(self.state, PromptStrategy.COT)
        assert COT_PLUS_STRATEGIES not in prompt

    def test_contains_game_rule(self):
        prompt = self.builder.build(self.state, PromptStrategy.COT)
        assert "wordle" in prompt.lower() or "word guessing" in prompt.lower()


class TestPromptBuildingCoTPlus:
    """test_prompt_building_cot_plus: CoT+ includes strategies."""

    def setup_method(self):
        self.builder = PromptBuilder()
        self.state = GameState()

    def test_contains_strategies(self):
        prompt = self.builder.build(self.state, PromptStrategy.COT_PLUS)
        assert "strateg" in prompt.lower()

    def test_contains_cot_instructions(self):
        prompt = self.builder.build(self.state, PromptStrategy.COT_PLUS)
        assert "step" in prompt.lower()

    def test_contains_game_rule(self):
        prompt = self.builder.build(self.state, PromptStrategy.COT_PLUS)
        assert "wordle" in prompt.lower() or "word guessing" in prompt.lower()


# ─── test_llm_client_mock ───────────────────────────────────────────────────────

class TestLLMClientMock:
    """test_llm_client_mock: Verify agent flow with mocked LLM."""

    def _make_agent(self, responses: list[str], strategy=PromptStrategy.ZERO_SHOT) -> WordleAgent:
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete_with_retry.side_effect = responses
        return WordleAgent(strategy=strategy, llm_client=mock_client)

    def test_agent_makes_guess(self):
        agent = self._make_agent(["CRANE"])
        state = GameState()
        result = agent.make_guess(state)
        assert result == "CRANE"

    def test_agent_retries_on_invalid_response(self):
        # First response is unparseable, second is valid
        agent = self._make_agent(["I have no idea", "SLATE"])
        state = GameState()
        result = agent.make_guess(state)
        assert result == "SLATE"

    def test_agent_uses_fallback_after_all_retries(self):
        # All responses are unparseable
        agent = self._make_agent(["??", "??", "??"])
        state = GameState()
        result = agent.make_guess(state)
        assert len(result) == 5
        assert result.isalpha()


class TestFullGameSessionMock:
    """test_full_game_session_mock: Complete game session with mock LLM."""

    def test_agent_wins_game(self):
        mock_client = MagicMock(spec=LLMClient)
        # Sequence: wrong guess, then correct
        mock_client.complete_with_retry.side_effect = ["SLATE", "CRANE"]

        agent = WordleAgent(strategy=PromptStrategy.ZERO_SHOT, llm_client=mock_client)
        engine = WordleEngine("CRANE", max_guesses=12)
        guesses = agent.play_game(engine)
        assert guesses == 2
        assert engine.is_won()

    def test_agent_returns_minus_one_on_loss(self):
        mock_client = MagicMock(spec=LLMClient)
        # Always guess wrong word
        mock_client.complete_with_retry.return_value = "SLATE"

        agent = WordleAgent(strategy=PromptStrategy.ZERO_SHOT, llm_client=mock_client)
        engine = WordleEngine("CRANE", max_guesses=3)
        result = agent.play_game(engine)
        assert result == -1
        assert not engine.is_won()

    def test_one_guess_win(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete_with_retry.return_value = "CRANE"

        agent = WordleAgent(strategy=PromptStrategy.ZERO_SHOT, llm_client=mock_client)
        engine = WordleEngine("CRANE", max_guesses=12)
        result = agent.play_game(engine)
        assert result == 1


class TestInvalidWordRetry:
    """test_invalid_word_retry: Agent handles LLM returning non-word gracefully."""

    def test_agent_does_not_crash_on_bad_response(self):
        mock_client = MagicMock(spec=LLMClient)
        # First 2 bad, third good
        mock_client.complete_with_retry.side_effect = [
            "NOTAVALIDWORDXYZ",
            "123AB",
            "CRANE",
        ]
        agent = WordleAgent(strategy=PromptStrategy.ZERO_SHOT, llm_client=mock_client)
        state = GameState()
        result = agent.make_guess(state, max_retries=3)
        assert result == "CRANE"
