"""
Statistical Analysis — Phase 3
Pearson correlation between LLM difficulty scores and human data.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from analysis.runner import ExperimentResult


@dataclass
class CorrelationResult:
    """Result of a Pearson correlation test."""
    r: float           # Pearson correlation coefficient
    p_value: float     # Two-tailed p-value
    n: int             # Sample size
    significant: bool  # True if p < 0.05

    def __str__(self) -> str:
        sig = "✅ significant" if self.significant else "❌ not significant"
        strength = self._strength()
        return f"r={self.r:.3f}, p={self.p_value:.4f}, n={self.n} ({strength}, {sig})"

    def _strength(self) -> str:
        a = abs(self.r)
        if a < 0.2:
            return "very weak"
        if a < 0.4:
            return "weak"
        if a < 0.6:
            return "moderate"
        if a < 0.8:
            return "strong"
        return "very strong"


def pearson_correlation(x: List[float], y: List[float]) -> CorrelationResult:
    """
    Compute Pearson correlation coefficient and two-tailed p-value.
    Pure Python implementation (no scipy dependency for core logic).

    Args:
        x: LLM difficulty scores (avg guesses per puzzle)
        y: Human difficulty scores (avg guesses or win rate from public data)

    Returns:
        CorrelationResult with r, p_value, n
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have equal length: {len(x)} vs {len(y)}")
    n = len(x)
    if n < 3:
        raise ValueError(f"Need at least 3 data points for correlation, got {n}")

    # Means
    mx = sum(x) / n
    my = sum(y) / n

    # Numerator and denominators
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    denom_x = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    denom_y = math.sqrt(sum((yi - my) ** 2 for yi in y))

    if denom_x == 0 or denom_y == 0:
        return CorrelationResult(r=0.0, p_value=1.0, n=n, significant=False)

    r = num / (denom_x * denom_y)
    r = max(-1.0, min(1.0, r))  # Clamp to [-1, 1] due to floating point

    # Two-tailed p-value via t-distribution approximation
    if abs(r) == 1.0:
        p_value = 0.0
    else:
        t_stat = r * math.sqrt(n - 2) / math.sqrt(1 - r ** 2)
        p_value = _t_pvalue(t_stat, df=n - 2)

    return CorrelationResult(r=r, p_value=p_value, n=n, significant=p_value < 0.05)


def _t_pvalue(t: float, df: int) -> float:
    """
    Approximate two-tailed p-value for a t-distribution.
    Uses a numerical approximation of the regularized incomplete beta function.
    Accurate to ~4 decimal places for df >= 2.
    """
    # Use the relationship between t-dist CDF and incomplete beta function
    x = df / (df + t * t)
    p_one_tail = 0.5 * _regularized_incomplete_beta(df / 2, 0.5, x)
    return min(1.0, 2 * p_one_tail)


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """
    Regularized incomplete beta function I_x(a, b) via continued fraction.
    Lentz's method approximation.
    """
    if x < 0 or x > 1:
        raise ValueError(f"x must be in [0, 1], got {x}")
    if x == 0:
        return 0.0
    if x == 1:
        return 1.0

    # Use the symmetry relation if needed for numerical stability
    if x > (a + 1) / (a + b + 2):
        return 1.0 - _regularized_incomplete_beta(b, a, 1.0 - x)

    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a

    # Lentz's continued fraction
    def cf():
        MAX_ITER = 200
        EPSILON = 1e-8
        f = 1.0
        C = f
        D = 1.0 - (a + b) * x / (a + 1)
        if abs(D) < 1e-30:
            D = 1e-30
        D = 1.0 / D
        C = 1.0 + 0.0
        f = D

        for m in range(1, MAX_ITER + 1):
            # Even step
            nm = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
            D = 1.0 + nm * D
            C = 1.0 + nm / C
            if abs(D) < 1e-30:
                D = 1e-30
            if abs(C) < 1e-30:
                C = 1e-30
            D = 1.0 / D
            delta = C * D
            f *= delta

            # Odd step
            nm = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
            D = 1.0 + nm * D
            C = 1.0 + nm / C
            if abs(D) < 1e-30:
                D = 1e-30
            if abs(C) < 1e-30:
                C = 1e-30
            D = 1.0 / D
            delta = C * D
            f *= delta

            if abs(delta - 1.0) < EPSILON:
                break
        return f

    return front * cf()


@dataclass
class ComparisonReport:
    """Report comparing LLM difficulty scores to human data."""
    strategy_name: str
    words: List[str]
    llm_scores: List[float]
    human_scores: List[float]
    correlation: CorrelationResult
    avg_llm_guesses: float
    avg_human_guesses: float

    def summary(self) -> str:
        lines = [
            f"=== Difficulty Correlation Report ===",
            f"Strategy:         {self.strategy_name}",
            f"Puzzles analyzed: {len(self.words)}",
            f"",
            f"LLM avg guesses:   {self.avg_llm_guesses:.2f}",
            f"Human avg guesses: {self.avg_human_guesses:.2f}",
            f"",
            f"Pearson Correlation: {self.correlation}",
        ]
        return "\n".join(lines)


class DifficultyAnalyzer:
    """Compares LLM experiment results to human benchmark data."""

    def analyze(
        self,
        experiment: ExperimentResult,
        human_data: Dict[str, float],  # {word: human_avg_guesses}
    ) -> ComparisonReport:
        """
        Compute correlation between LLM scores and human scores
        for the words that exist in both datasets.
        """
        words, llm_scores, human_scores = [], [], []
        for puzzle in experiment.puzzle_results:
            word = puzzle.word
            if word in human_data:
                words.append(word)
                llm_scores.append(puzzle.avg_guesses_all)
                human_scores.append(human_data[word])

        if len(words) < 3:
            raise ValueError(
                f"Not enough overlapping words for correlation: found {len(words)}, need ≥3"
            )

        corr = pearson_correlation(llm_scores, human_scores)
        return ComparisonReport(
            strategy_name=experiment.strategy.value,
            words=words,
            llm_scores=llm_scores,
            human_scores=human_scores,
            correlation=corr,
            avg_llm_guesses=sum(llm_scores) / len(llm_scores),
            avg_human_guesses=sum(human_scores) / len(human_scores),
        )

    def rank_by_difficulty(
        self, experiment: ExperimentResult
    ) -> List[Tuple[str, float]]:
        """Return words sorted from hardest to easiest (highest avg_guesses first)."""
        pairs = [(r.word, r.avg_guesses_all) for r in experiment.puzzle_results]
        return sorted(pairs, key=lambda x: x[1], reverse=True)
