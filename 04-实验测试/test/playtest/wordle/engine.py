"""
Wordle Game Engine
Phase 1: Core game logic — no external dependencies.

Key design decisions aligned with the paper:
- Letters represented as lists (not strings) to avoid LLM tokenization issues (Guideline G1)
- Default max_guesses=12 to give LLMs sufficient room to distinguish difficulty (Guideline G2)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class LetterStatus(Enum):
    GREEN = "GREEN"    # Correct letter, correct position
    YELLOW = "YELLOW"  # Correct letter, wrong position
    GRAY = "GRAY"      # Letter not in word


class GameStatus(Enum):
    ONGOING = "ONGOING"
    WON = "WON"
    LOST = "LOST"


@dataclass
class GuessResult:
    """Result of a single guess attempt."""
    word: str
    feedback: List[LetterStatus]  # One status per letter, length == 5
    is_correct: bool

    def __repr__(self) -> str:
        icons = {LetterStatus.GREEN: "🟩", LetterStatus.YELLOW: "🟨", LetterStatus.GRAY: "⬜"}
        row = "".join(icons[s] for s in self.feedback)
        return f"{self.word.upper()} {row}"


@dataclass
class GameState:
    """
    Complete snapshot of the current game state.
    Passed to the LLM agent for decision making.
    Note: target_word is NOT exposed to the agent.
    """
    guesses_made: List[str] = field(default_factory=list)
    feedbacks: List[GuessResult] = field(default_factory=list)
    correct_positions: Dict[int, str] = field(default_factory=dict)   # {0: 'A', 4: 'E'}
    wrong_positions: Dict[str, List[int]] = field(default_factory=dict)  # {'A': [2, 3]}
    incorrect_letters: Set[str] = field(default_factory=set)
    remaining_guesses: int = 12
    status: GameStatus = GameStatus.ONGOING

    @property
    def num_guesses(self) -> int:
        return len(self.guesses_made)


class WordleEngine:
    """
    Manages a single Wordle game session.

    Usage:
        engine = WordleEngine("CRANE", max_guesses=12)
        result = engine.guess("SLATE")
        state = engine.get_state()
    """

    WORD_LENGTH = 5

    def __init__(self, target_word: str, max_guesses: int = 12) -> None:
        target = target_word.upper().strip()
        if len(target) != self.WORD_LENGTH:
            raise ValueError(f"Target word must be {self.WORD_LENGTH} letters, got '{target}'")
        if not target.isalpha():
            raise ValueError(f"Target word must contain only letters, got '{target}'")

        self._target = target
        self._max_guesses = max_guesses
        self._state = GameState(remaining_guesses=max_guesses)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def guess(self, word: str) -> GuessResult:
        """
        Submit a guess. Returns GuessResult with per-letter feedback.

        Raises:
            ValueError: if word is invalid length, non-alpha, or game is already over
        """
        if self._state.status != GameStatus.ONGOING:
            raise ValueError(f"Game is already over (status={self._state.status.value})")

        word = word.upper().strip()
        if len(word) != self.WORD_LENGTH:
            raise ValueError(f"Guess must be {self.WORD_LENGTH} letters, got '{word}'")
        if not word.isalpha():
            raise ValueError(f"Guess must contain only letters, got '{word}'")

        feedback = self._evaluate_guess(word)
        is_correct = all(s == LetterStatus.GREEN for s in feedback)
        result = GuessResult(word=word, feedback=feedback, is_correct=is_correct)

        self._update_state(result)
        return result

    def get_state(self) -> GameState:
        """Return a copy of current game state (safe to share with agent)."""
        return GameState(
            guesses_made=list(self._state.guesses_made),
            feedbacks=list(self._state.feedbacks),
            correct_positions=dict(self._state.correct_positions),
            wrong_positions={k: list(v) for k, v in self._state.wrong_positions.items()},
            incorrect_letters=set(self._state.incorrect_letters),
            remaining_guesses=self._state.remaining_guesses,
            status=self._state.status,
        )

    def is_finished(self) -> bool:
        return self._state.status != GameStatus.ONGOING

    def is_won(self) -> bool:
        return self._state.status == GameStatus.WON

    @property
    def target_word(self) -> str:
        """Expose target word for result tracking (NOT passed to LLM)."""
        return self._target

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------

    def _evaluate_guess(self, word: str) -> List[LetterStatus]:
        """
        Core Wordle evaluation algorithm.
        Handles duplicate letters correctly:
        - GREEN takes priority over YELLOW
        - A letter can only be marked YELLOW as many times as it appears in the target
        """
        feedback = [LetterStatus.GRAY] * self.WORD_LENGTH

        # Count available target letters (for duplicate handling)
        target_letter_counts: Dict[str, int] = {}
        for ch in self._target:
            target_letter_counts[ch] = target_letter_counts.get(ch, 0) + 1

        # Pass 1: Mark GREEN (exact matches consume a count)
        for i, (g_ch, t_ch) in enumerate(zip(word, self._target)):
            if g_ch == t_ch:
                feedback[i] = LetterStatus.GREEN
                target_letter_counts[t_ch] -= 1

        # Pass 2: Mark YELLOW (in-word but wrong position)
        for i, g_ch in enumerate(word):
            if feedback[i] == LetterStatus.GREEN:
                continue
            if target_letter_counts.get(g_ch, 0) > 0:
                feedback[i] = LetterStatus.YELLOW
                target_letter_counts[g_ch] -= 1

        return feedback

    def _update_state(self, result: GuessResult) -> None:
        """Update internal state based on a guess result."""
        s = self._state
        s.guesses_made.append(result.word)
        s.feedbacks.append(result)
        s.remaining_guesses -= 1

        # Update knowledge derived from feedback
        for i, (letter, status) in enumerate(zip(result.word, result.feedback)):
            if status == LetterStatus.GREEN:
                s.correct_positions[i] = letter
                # Remove from wrong_positions if it was there
                if letter in s.wrong_positions and i in s.wrong_positions[letter]:
                    s.wrong_positions[letter].remove(i)
            elif status == LetterStatus.YELLOW:
                if letter not in s.wrong_positions:
                    s.wrong_positions[letter] = []
                if i not in s.wrong_positions[letter]:
                    s.wrong_positions[letter].append(i)
            elif status == LetterStatus.GRAY:
                # Only add to incorrect if letter doesn't appear in target at all
                # (it could be gray due to duplicate exhaustion)
                if letter not in s.correct_positions.values() and letter not in s.wrong_positions:
                    s.incorrect_letters.add(letter)

        # Update game status
        if result.is_correct:
            s.status = GameStatus.WON
        elif s.remaining_guesses == 0:
            s.status = GameStatus.LOST
