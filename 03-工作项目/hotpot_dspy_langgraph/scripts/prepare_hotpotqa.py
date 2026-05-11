"""Prepare the user-requested HotPotQA hard splits.

Usage:
    python scripts/prepare_hotpotqa.py --output-dir data/processed --seed 42
"""

from __future__ import annotations

import typer
from rich import print

from hotpot_dspy_langgraph.data import prepare_hotpotqa_splits


def main(output_dir: str = "data/processed", seed: int = 42) -> None:
    """Prepare train/val/test JSONL files in the requested format."""

    paths = prepare_hotpotqa_splits(output_dir=output_dir, seed=seed)
    print({name: str(path) for name, path in paths.items()})


if __name__ == "__main__":
    typer.run(main)
