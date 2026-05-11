"""
Entry point for LLM Game Difficulty Framework.

Usage:
    python3 main.py                        # Full run (ZS+CoT+CoT+, 20 trials, 10 words)
    python3 main.py --quick-test           # 5 words, 3 trials, ZS only
    python3 main.py --strategy cot_plus    # Specify strategy
    python3 main.py --words CRANE SLATE    # Specific words
"""
from __future__ import annotations

import argparse
import logging
import sys

from agent.llm_client import LLMClient, WordleAgent
from agent.prompts import PromptStrategy
from analysis.report import generate_markdown_report
from analysis.runner import ExperimentRunner
from analysis.stats import DifficultyAnalyzer
from wordle.word_list import WordList

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
# Suppress noisy HTTP request logs from the anthropic SDK
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Simulated human difficulty data (replace with real WordleBot data in production)
HUMAN_DIFFICULTY = {
    "CRANE": 3.8, "SLATE": 3.9, "ARISE": 4.0, "STARE": 3.7, "SNARE": 4.2,
    "JAZZY": 5.4, "QUEEN": 5.1, "TRYST": 5.3, "GLYPH": 5.5, "NYMPH": 5.6,
    "ABOVE": 4.1, "BLOWN": 4.3, "CIVIC": 4.6, "DEPOT": 4.4, "EMPTY": 4.2,
}

STRATEGY_MAP = {
    "zero_shot": PromptStrategy.ZERO_SHOT,
    "cot": PromptStrategy.COT,
    "cot_plus": PromptStrategy.COT_PLUS,
}


def main():
    parser = argparse.ArgumentParser(description="LLM Game Difficulty Framework")
    parser.add_argument("--quick-test", action="store_true", help="5 words, 3 trials")
    parser.add_argument("--strategy", choices=list(STRATEGY_MAP), default="zero_shot")
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--words", nargs="+", help="Specific target words")
    parser.add_argument("--output", default="difficulty_report.md")
    args = parser.parse_args()

    # Configure experiment
    if args.quick_test:
        words = ["CRANE", "SLATE", "JAZZY", "QUEEN", "ARISE"]
        num_trials = 3
        strategy = PromptStrategy.ZERO_SHOT
        print("=== Quick Test Mode (5 words, 3 trials, Zero-Shot) ===")
    else:
        wl = WordList.builtin()
        words = args.words or list(HUMAN_DIFFICULTY.keys())[:10]
        num_trials = args.trials
        strategy = STRATEGY_MAP[args.strategy]
        print(f"=== Full Run: {len(words)} words, {num_trials} trials, {args.strategy} ===")

    # Build agent
    client = LLMClient(model=args.model)
    agent = WordleAgent(strategy=strategy, llm_client=client)
    runner = ExperimentRunner(agent=agent, max_guesses=12)

    # Run experiment
    print(f"Running experiment on {len(words)} words × {num_trials} trials...")
    experiment = runner.run_experiment(words, num_trials=num_trials)

    # Filter to words with human data
    human_data = {w: HUMAN_DIFFICULTY[w] for w in words if w in HUMAN_DIFFICULTY}

    if len(human_data) < 3:
        print(f"Warning: Only {len(human_data)} words have human data. Skipping correlation.")
        print("\nRaw difficulty ranking:")
        analyzer = DifficultyAnalyzer()
        ranked = analyzer.rank_by_difficulty(experiment)
        for rank, (word, score) in enumerate(ranked, 1):
            print(f"  {rank}. {word}: {score:.2f} avg guesses")
        return

    # Analyze
    analyzer = DifficultyAnalyzer()
    comparison = analyzer.analyze(experiment, human_data)

    print("\n" + "=" * 60)
    print(comparison.summary())
    print("=" * 60)

    # Generate report
    report_md = generate_markdown_report(comparison, experiment)
    with open(args.output, "w") as f:
        f.write(report_md)
    print(f"\nMarkdown report saved to: {args.output}")


if __name__ == "__main__":
    main()
