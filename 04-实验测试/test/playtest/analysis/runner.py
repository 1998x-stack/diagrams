"""
Experiment Runner — Phase 3
Runs multi-trial experiments across a word list and aggregates results.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from wordle.engine import WordleEngine
from agent.llm_client import WordleAgent
from agent.prompts import PromptStrategy

logger = logging.getLogger(__name__)


@dataclass
class PuzzleResult:
    """Statistics for a single Wordle puzzle across N trials."""
    word: str
    trials: List[int]          # Guess counts; -1 means failed (lost)
    num_trials: int = 0
    avg_guesses: float = 0.0   # Average over successful trials only
    avg_guesses_all: float = 0.0  # Average counting failures as max_guesses+1
    win_rate: float = 0.0

    def __post_init__(self):
        if self.trials:
            self.num_trials = len(self.trials)
            wins = [t for t in self.trials if t > 0]
            losses = len(self.trials) - len(wins)
            self.win_rate = len(wins) / len(self.trials) if self.trials else 0.0
            self.avg_guesses = sum(wins) / len(wins) if wins else float("inf")
            # For difficulty ranking: failed games count as max_guesses + 1
            penalized = wins + [13] * losses  # 13 = 12 max + 1 penalty
            self.avg_guesses_all = sum(penalized) / len(penalized) if penalized else 0.0


@dataclass
class ExperimentResult:
    """Aggregated results for an experiment across all puzzles."""
    strategy: PromptStrategy
    puzzle_results: List[PuzzleResult] = field(default_factory=list)
    num_trials_per_puzzle: int = 0

    @property
    def avg_guesses_overall(self) -> float:
        """Mean of per-puzzle avg_guesses_all — matches Table 1 metric."""
        vals = [r.avg_guesses_all for r in self.puzzle_results if r.num_trials > 0]
        return sum(vals) / len(vals) if vals else 0.0

    @property
    def llm_difficulty_scores(self) -> List[float]:
        """Per-puzzle difficulty score (avg_guesses_all) in puzzle_results order."""
        return [r.avg_guesses_all for r in self.puzzle_results]

    @property
    def words(self) -> List[str]:
        return [r.word for r in self.puzzle_results]


class ExperimentRunner:
    """
    Orchestrates multi-trial Wordle experiments.
    Each puzzle is attempted num_trials times; results are averaged.
    """

    def __init__(
        self,
        agent: WordleAgent,
        max_guesses: int = 12,
    ) -> None:
        self._agent = agent
        self._max_guesses = max_guesses

    def run_single_puzzle(
        self,
        word: str,
        num_trials: int = 20,
    ) -> PuzzleResult:
        """Run num_trials games on a single target word."""
        trials: List[int] = []
        for trial_idx in range(num_trials):
            engine = WordleEngine(word.upper(), max_guesses=self._max_guesses)
            try:
                result = self._agent.play_game(engine)
                trials.append(result)
                logger.debug(f"  [{word}] Trial {trial_idx+1}: {result} guesses")
            except Exception as e:
                logger.error(f"  [{word}] Trial {trial_idx+1} error: {e}")
                trials.append(-1)
        return PuzzleResult(word=word.upper(), trials=trials)

    def run_experiment(
        self,
        word_list: List[str],
        num_trials: int = 20,
    ) -> ExperimentResult:
        """Run the full experiment across all words in word_list."""
        result = ExperimentResult(
            strategy=self._agent.strategy,
            num_trials_per_puzzle=num_trials,
        )
        total = len(word_list)
        for i, word in enumerate(word_list):
            logger.info(f"[{i+1}/{total}] Testing word: {word.upper()}")
            puzzle_result = self.run_single_puzzle(word, num_trials=num_trials)
            result.puzzle_results.append(puzzle_result)
            logger.info(
                f"  → avg_guesses={puzzle_result.avg_guesses_all:.2f}, "
                f"win_rate={puzzle_result.win_rate:.1%}"
            )
        return result
