"""
Phase 1 Test Suite — Wordle Game Engine
All 8 tests must pass before proceeding to Phase 2.
"""
import pytest
from wordle.engine import (
    GameStatus,
    GuessResult,
    LetterStatus,
    WordleEngine,
)
from wordle.word_list import WordList


# ─── Engine Tests ──────────────────────────────────────────────────────────────

class TestCorrectGuess:
    """test_correct_guess: All letters green when guess equals target."""

    def test_exact_match_all_green(self):
        engine = WordleEngine("CRANE")
        result = engine.guess("CRANE")
        assert result.is_correct is True
        assert all(s == LetterStatus.GREEN for s in result.feedback)
        assert engine.is_won()
        assert engine.get_state().status == GameStatus.WON

    def test_case_insensitive(self):
        engine = WordleEngine("CRANE")
        result = engine.guess("crane")
        assert result.is_correct is True


class TestWrongPosition:
    """test_wrong_position: Letters in word but wrong position → YELLOW."""

    def test_single_wrong_position(self):
        # Target: CRANE, Guess: ACORN → A is in CRANE but not at pos 0
        engine = WordleEngine("CRANE")
        result = engine.guess("ACORN")
        # A at pos 0: in CRANE, wrong position → YELLOW
        assert result.feedback[0] == LetterStatus.YELLOW
        # C at pos 1: in CRANE, wrong position → YELLOW
        assert result.feedback[1] == LetterStatus.YELLOW
        # R at pos 3: in CRANE, wrong position → YELLOW
        assert result.feedback[3] == LetterStatus.YELLOW
        # N at pos 4: in CRANE, wrong position → YELLOW
        assert result.feedback[4] == LetterStatus.YELLOW

    def test_correct_position_beats_yellow(self):
        # Target: CRANE, Guess: CRANE → all GREEN, none YELLOW
        engine = WordleEngine("CRANE")
        result = engine.guess("CRANE")
        assert all(s == LetterStatus.GREEN for s in result.feedback)


class TestIncorrectLetter:
    """test_incorrect_letter: Letters not in word → GRAY."""

    def test_all_wrong_letters(self):
        # Target: CRANE, Guess: FILMS → F,I,L,M,S not in CRANE
        engine = WordleEngine("CRANE")
        result = engine.guess("FILMS")
        assert all(s == LetterStatus.GRAY for s in result.feedback)

    def test_state_tracks_incorrect(self):
        engine = WordleEngine("CRANE")
        engine.guess("FILMS")
        state = engine.get_state()
        assert "F" in state.incorrect_letters
        assert "I" in state.incorrect_letters
        assert "L" in state.incorrect_letters
        assert "M" in state.incorrect_letters
        assert "S" in state.incorrect_letters


class TestDuplicateLetters:
    """test_duplicate_letters: Duplicate letters handled correctly."""

    def test_guess_has_duplicate_not_in_target(self):
        # Target: CRANE, Guess: AACME → A appears twice in guess but once in target
        # pos 0: A → YELLOW (A is in CRANE at pos 2, wrong position)
        # pos 1: A → GRAY (only 1 A in target, already "used" by pos 0)
        engine = WordleEngine("CRANE")
        result = engine.guess("AACME")
        assert result.feedback[0] == LetterStatus.YELLOW  # first A → YELLOW
        assert result.feedback[1] == LetterStatus.GRAY    # second A → GRAY (exhausted)

    def test_target_has_duplicate_letters(self):
        # Target: APPLE, Guess: APPLY
        # A→GREEN, P→GREEN, P→GREEN, L→GREEN, Y→GRAY
        engine = WordleEngine("APPLE")
        result = engine.guess("APPLY")
        assert result.feedback[0] == LetterStatus.GREEN   # A
        assert result.feedback[1] == LetterStatus.GREEN   # P
        assert result.feedback[2] == LetterStatus.GREEN   # P
        assert result.feedback[3] == LetterStatus.GREEN   # L
        assert result.feedback[4] == LetterStatus.GRAY    # Y

    def test_paper_example_apple_alert(self):
        # Paper example: target=APPLE, guess=ALERT
        # A→GREEN, L→YELLOW, E→YELLOW, R→GRAY, T→GRAY
        engine = WordleEngine("APPLE")
        result = engine.guess("ALERT")
        assert result.feedback[0] == LetterStatus.GREEN   # A correct position
        assert result.feedback[1] == LetterStatus.YELLOW  # L in APPLE, wrong pos
        assert result.feedback[2] == LetterStatus.YELLOW  # E in APPLE, wrong pos
        assert result.feedback[3] == LetterStatus.GRAY    # R not in APPLE
        assert result.feedback[4] == LetterStatus.GRAY    # T not in APPLE


class TestMaxGuessesExceeded:
    """test_max_guesses_exceeded: Game ends after max guesses."""

    def test_game_lost_after_max_guesses(self):
        engine = WordleEngine("CRANE", max_guesses=3)
        engine.guess("SLATE")
        engine.guess("FILMS")
        engine.guess("DEPOT")
        assert engine.is_finished()
        assert not engine.is_won()
        assert engine.get_state().status == GameStatus.LOST

    def test_cannot_guess_after_game_over(self):
        engine = WordleEngine("CRANE", max_guesses=1)
        engine.guess("SLATE")
        with pytest.raises(ValueError, match="Game is already over"):
            engine.guess("CRANE")

    def test_remaining_guesses_counts_down(self):
        engine = WordleEngine("CRANE", max_guesses=5)
        assert engine.get_state().remaining_guesses == 5
        engine.guess("SLATE")
        assert engine.get_state().remaining_guesses == 4
        engine.guess("FILMS")
        assert engine.get_state().remaining_guesses == 3


class TestInvalidWord:
    """test_invalid_word: Non-5-letter or non-alpha guesses are rejected."""

    def test_too_short(self):
        engine = WordleEngine("CRANE")
        with pytest.raises(ValueError):
            engine.guess("CAT")

    def test_too_long(self):
        engine = WordleEngine("CRANE")
        with pytest.raises(ValueError):
            engine.guess("CRANES")

    def test_contains_number(self):
        engine = WordleEngine("CRANE")
        with pytest.raises(ValueError):
            engine.guess("CR4NE")

    def test_empty_string(self):
        engine = WordleEngine("CRANE")
        with pytest.raises(ValueError):
            engine.guess("")

    def test_invalid_target(self):
        with pytest.raises(ValueError):
            WordleEngine("TOOLONG")

    def test_invalid_target_non_alpha(self):
        with pytest.raises(ValueError):
            WordleEngine("CR4NE")


class TestGameStateTracking:
    """test_game_state_tracking: State correctly accumulates across guesses."""

    def test_guesses_accumulate(self):
        engine = WordleEngine("CRANE")
        engine.guess("SLATE")
        engine.guess("ABOVE")
        state = engine.get_state()
        assert state.guesses_made == ["SLATE", "ABOVE"]
        assert len(state.feedbacks) == 2
        assert state.num_guesses == 2

    def test_correct_positions_tracked(self):
        # Target: CRANE, Guess: CRANE → all positions correct
        engine = WordleEngine("CRANE")
        engine.guess("FRAME")  # E at pos 4 is correct
        state = engine.get_state()
        assert state.correct_positions.get(4) == "E"

    def test_wrong_positions_tracked(self):
        # Target: CRANE, Guess: ACORN
        # A at pos 0 is in word but wrong position
        engine = WordleEngine("CRANE")
        engine.guess("ACORN")
        state = engine.get_state()
        assert "A" in state.wrong_positions
        assert 0 in state.wrong_positions["A"]

    def test_state_is_copy(self):
        """Modifying returned state should not affect engine's internal state."""
        engine = WordleEngine("CRANE")
        engine.guess("SLATE")
        state = engine.get_state()
        state.guesses_made.append("TAMPER")
        assert engine.get_state().num_guesses == 1


class TestWinDetection:
    """test_win_detection: Win correctly detected, further guesses blocked."""

    def test_win_on_first_guess(self):
        engine = WordleEngine("CRANE")
        engine.guess("CRANE")
        assert engine.is_won()
        assert engine.is_finished()

    def test_win_on_last_guess(self):
        engine = WordleEngine("CRANE", max_guesses=3)
        engine.guess("SLATE")
        engine.guess("FILMS")
        engine.guess("CRANE")
        assert engine.is_won()

    def test_no_more_guesses_after_win(self):
        engine = WordleEngine("CRANE")
        engine.guess("CRANE")
        with pytest.raises(ValueError, match="Game is already over"):
            engine.guess("SLATE")

    def test_num_guesses_on_win(self):
        engine = WordleEngine("CRANE", max_guesses=12)
        engine.guess("SLATE")
        engine.guess("CRANE")
        state = engine.get_state()
        assert state.num_guesses == 2
        assert state.remaining_guesses == 10


# ─── WordList Tests ─────────────────────────────────────────────────────────────

class TestWordList:
    def test_builtin_list_loads(self):
        wl = WordList.builtin()
        assert len(wl) > 0

    def test_valid_word_check(self):
        wl = WordList.builtin()
        assert wl.is_valid_word("CRANE")
        assert not wl.is_valid_word("ZZZZZ")

    def test_case_insensitive_validation(self):
        wl = WordList.builtin()
        assert wl.is_valid_word("crane")

    def test_random_word_is_5_letters(self):
        wl = WordList.builtin()
        word = wl.get_random_word()
        assert len(word) == 5
        assert word.isalpha()

    def test_deterministic_with_seed(self):
        wl = WordList.builtin()
        w1 = wl.get_random_word(seed=42)
        w2 = wl.get_random_word(seed=42)
        assert w1 == w2
