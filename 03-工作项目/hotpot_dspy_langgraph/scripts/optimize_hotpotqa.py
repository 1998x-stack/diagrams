"""Optimize the HotPotQA DSPy program with MIPROv2.

Usage:
    python scripts/optimize_hotpotqa.py \
      --train-path data/processed/train.jsonl \
      --val-path data/processed/val.jsonl \
      --artifact-dir artifacts/mipro_run
"""

from __future__ import annotations

from pathlib import Path

import dspy
import orjson
import typer
from rich import print

from hotpot_dspy_langgraph.config import Settings
from hotpot_dspy_langgraph.data import load_dspy_examples
from hotpot_dspy_langgraph.dspy_program import HotPotQAModule
from hotpot_dspy_langgraph.metrics import hotpot_metric


def main(
    train_path: str = typer.Option(..., help="Path to processed train.jsonl."),
    val_path: str = typer.Option(..., help="Path to processed val.jsonl."),
    artifact_dir: str = typer.Option("artifacts/mipro_run", help="Where to save optimizer artifacts."),
    auto: str = typer.Option("light", help="DSPy MIPROv2 auto budget: light/medium/heavy."),
) -> None:
    """Compile the DSPy program and save the resulting state."""

    settings = Settings.from_env()
    dspy.configure(lm=settings.build_lm())

    trainset = load_dspy_examples(train_path)
    valset = load_dspy_examples(val_path)

    program = HotPotQAModule(top_k=settings.retriever_top_k)
    optimizer = dspy.MIPROv2(metric=hotpot_metric, auto=auto)
    compiled = optimizer.compile(program, trainset=trainset, valset=valset)

    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    compiled_path = artifact_dir / "compiled_program.json"
    compiled.save(str(compiled_path), save_program=False)

    summary = {
        "optimizer": "MIPROv2",
        "auto": auto,
        "train_size": len(trainset),
        "val_size": len(valset),
        "compiled_program": str(compiled_path),
    }
    (artifact_dir / "optimization_summary.json").write_bytes(
        orjson.dumps(summary, option=orjson.OPT_INDENT_2)
    )
    print(summary)


if __name__ == "__main__":
    typer.run(main)
