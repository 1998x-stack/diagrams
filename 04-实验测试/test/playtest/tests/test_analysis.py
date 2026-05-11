"""
Phase 3 Test Suite — Difficulty Analysis & Correlation
All tests pass before declaring project complete.
Integration test (last one) calls real Claude API.
"""
from __future__ import annotations

import math
from unittest.mock import MagicMock

import pytest

from analysis.runner import ExperimentResult, ExperimentRunner, PuzzleResult
from analysis.stats import (
    ComparisonReport,
    CorrelationResult,
    DifficultyAnalyzer,
    pearson_correlation,
)
from analysis.report import generate_markdown_report
from agent.llm_client import LLMClient, WordleAgent
from agent.prompts import PromptStrategy


# ─── test_pearson_calculation ───────────────────────────────────────────────────

class TestPearsonCalculation:
    """test_pearson_calculation: Verify against known values."""

    def test_perfect_positive_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        result = pearson_correlation(x, y)
        assert abs(result.r - 1.0) < 1e-9
        assert result.p_value < 0.001

    def test_perfect_negative_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        result = pearson_correlation(x, y)
        assert abs(result.r - (-1.0)) < 1e-9

    def test_known_moderate_correlation(self):
        # Hand-computed: r should be ~0.9
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.1, 1.9, 3.2, 3.8, 5.1]
        result = pearson_correlation(x, y)
        assert 0.99 < result.r <= 1.0

    def test_significance_flag(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        y = [1.1, 2.2, 2.9, 4.1, 5.0, 5.8, 7.2, 8.1, 8.9, 10.1]
        result = pearson_correlation(x, y)
        assert result.significant

    def test_equal_length_required(self):
        with pytest.raises(ValueError, match="equal length"):
            pearson_correlation([1, 2, 3], [1, 2])

    def test_minimum_3_points(self):
        with pytest.raises(ValueError, match="at least 3"):
            pearson_correlation([1.0, 2.0], [1.0, 2.0])


class TestPerfectCorrelation:
    """test_perfect_correlation: r==1.0 for perfectly correlated data."""

    def test_r_is_one(self):
        x = [3.5, 5.0, 7.0, 8.5, 9.0]
        y = [7.0, 10.0, 14.0, 17.0, 18.0]  # y = 2*x
        result = pearson_correlation(x, y)
        assert abs(result.r - 1.0) < 1e-6

    def test_p_is_zero_for_perfect(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [3.0, 6.0, 9.0, 12.0, 15.0]
        result = pearson_correlation(x, y)
        assert result.p_value < 0.001


class TestNoCorrelation:
    """test_no_correlation: Random-ish data has r≈0."""

    def test_constant_y_returns_zero(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 5.0, 5.0, 5.0, 5.0]
        result = pearson_correlation(x, y)
        assert result.r == 0.0
        assert not result.significant

    def test_alternating_pattern(self):
        # x increasing, y alternating → low correlation
        x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        y = [1.0, 8.0, 2.0, 7.0, 3.0, 6.0, 4.0, 5.0]
        result = pearson_correlation(x, y)
        assert abs(result.r) < 0.3


# ─── test_experiment_runner_mock ────────────────────────────────────────────────

class TestExperimentRunnerMock:
    """test_experiment_runner_mock: Verify aggregation with mocked agent."""

    def _make_runner(self, guess_sequence: list[str]) -> ExperimentRunner:
        """Create runner with a mock agent that cycles through guess_sequence."""
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete_with_retry.side_effect = guess_sequence * 100  # plenty of responses
        agent = WordleAgent(strategy=PromptStrategy.ZERO_SHOT, llm_client=mock_client)
        return ExperimentRunner(agent=agent, max_guesses=12)

    def test_single_puzzle_wins(self):
        # Target CRANE, agent always guesses CRANE immediately
        runner = self._make_runner(["CRANE"])
        result = runner.run_single_puzzle("CRANE", num_trials=3)
        assert result.word == "CRANE"
        assert result.num_trials == 3
        assert result.win_rate == 1.0
        assert result.avg_guesses == 1.0  # Always wins in 1 guess

    def test_single_puzzle_loses(self):
        # Target CRANE, agent always guesses SLATE (never wins)
        runner = self._make_runner(["SLATE"])
        result = runner.run_single_puzzle("CRANE", num_trials=3)
        assert result.win_rate == 0.0
        assert result.avg_guesses == float("inf")

    def test_experiment_collects_all_puzzles(self):
        runner = self._make_runner(["CRANE"])
        words = ["CRANE", "SLATE", "ARISE"]
        exp = runner.run_experiment(words, num_trials=2)
        assert len(exp.puzzle_results) == 3
        assert exp.words == ["CRANE", "SLATE", "ARISE"]

    def test_difficulty_scores_length_matches_words(self):
        runner = self._make_runner(["CRANE", "SLATE"])
        words = ["CRANE", "SLATE"]
        exp = runner.run_experiment(words, num_trials=2)
        assert len(exp.llm_difficulty_scores) == 2


# ─── test_report_generation ─────────────────────────────────────────────────────

class TestReportGeneration:
    """test_report_generation: Markdown report generates without error."""

    def _make_comparison(self) -> tuple[ComparisonReport, ExperimentResult]:
        words = ["CRANE", "SLATE", "ARISE", "STARE", "SNARE"]
        llm_scores = [5.5, 7.2, 6.1, 8.0, 9.3]
        human_scores = [4.1, 5.5, 4.8, 6.0, 7.2]

        corr = pearson_correlation(llm_scores, human_scores)
        comparison = ComparisonReport(
            strategy_name="cot_plus",
            words=words,
            llm_scores=llm_scores,
            human_scores=human_scores,
            correlation=corr,
            avg_llm_guesses=sum(llm_scores) / len(llm_scores),
            avg_human_guesses=sum(human_scores) / len(human_scores),
        )

        puzzle_results = [
            PuzzleResult(word=w, trials=[int(s)] * 3)
            for w, s in zip(words, llm_scores)
        ]
        experiment = ExperimentResult(
            strategy=PromptStrategy.COT_PLUS,
            puzzle_results=puzzle_results,
            num_trials_per_puzzle=3,
        )
        return comparison, experiment

    def test_report_is_string(self):
        comp, exp = self._make_comparison()
        report = generate_markdown_report(comp, exp)
        assert isinstance(report, str)

    def test_report_contains_strategy(self):
        comp, exp = self._make_comparison()
        report = generate_markdown_report(comp, exp)
        assert "cot_plus" in report

    def test_report_contains_pearson(self):
        comp, exp = self._make_comparison()
        report = generate_markdown_report(comp, exp)
        assert "Pearson" in report or "r=" in report

    def test_report_contains_all_words(self):
        comp, exp = self._make_comparison()
        report = generate_markdown_report(comp, exp)
        for word in ["CRANE", "SLATE", "ARISE", "STARE", "SNARE"]:
            assert word in report

    def test_difficulty_analyzer_ranks_correctly(self):
        comp, exp = self._make_comparison()
        analyzer = DifficultyAnalyzer()
        ranked = analyzer.rank_by_difficulty(exp)
        # SNARE has highest avg_guesses (9.3) → should be first (hardest)
        assert ranked[0][0] == "SNARE"

    def test_analyzer_computes_correlation(self):
        comp, exp = self._make_comparison()
        human_data = {w: s for w, s in zip(comp.words, comp.human_scores)}
        analyzer = DifficultyAnalyzer()
        report = analyzer.analyze(exp, human_data)
        assert isinstance(report.correlation.r, float)
        assert -1.0 <= report.correlation.r <= 1.0


# ─── Integration Test (calls real Claude API) ────────────────────────────────────

class TestIntegration5Words:
    """
    integration_test_5_words: End-to-end test with real Claude API.

    Runs 3 trials on 5 words with Zero-Shot strategy.
    Verifies the pipeline produces valid correlation output.
    This test WILL make real API calls — requires ANTHROPIC_API_KEY.
    """

    WORDS = ["CRANE", "SLATE", "ARISE", "JAZZY", "QUEEN"]
    # Simulated human difficulty scores (avg guesses from WordleBot-like data)
    HUMAN_DATA = {
        "CRANE": 3.8,
        "SLATE": 3.9,
        "ARISE": 4.0,
        "JAZZY": 5.4,
        "QUEEN": 5.1,
    }

    @pytest.mark.integration
    def test_full_pipeline_5_words(self):
        """Full end-to-end: engine → agent → runner → stats → report."""
        client = LLMClient(model="claude-haiku-4-5-20251001")  # Haiku for cost efficiency
        agent = WordleAgent(strategy=PromptStrategy.ZERO_SHOT, llm_client=client)
        runner = ExperimentRunner(agent=agent, max_guesses=12)

        experiment = runner.run_experiment(self.WORDS, num_trials=3)

        # Basic sanity checks
        assert len(experiment.puzzle_results) == 5
        for pr in experiment.puzzle_results:
            assert pr.num_trials == 3
            assert 0.0 <= pr.win_rate <= 1.0
            assert pr.avg_guesses_all >= 1.0

        # Correlation analysis
        analyzer = DifficultyAnalyzer()
        report = analyzer.analyze(experiment, self.HUMAN_DATA)

        assert -1.0 <= report.correlation.r <= 1.0
        assert 0.0 <= report.correlation.p_value <= 1.0
        assert report.correlation.n == 5

        # Generate report
        md_report = generate_markdown_report(report, experiment)
        assert "CRANE" in md_report
        assert "Pearson" in md_report

        print("\n" + "=" * 60)
        print(report.summary())
        print("=" * 60)
        print(f"\nFull Markdown Report Preview (first 500 chars):")
        print(md_report[:500])
