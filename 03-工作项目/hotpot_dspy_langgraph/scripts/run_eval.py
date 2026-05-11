"""Evaluate the standalone DSPy program and LangGraph pipeline.

Usage:
    python scripts/run_eval.py \
      --split-path data/processed/test.jsonl \
      --artifact-dir artifacts/mipro_run
"""

from __future__ import annotations

from pathlib import Path

import dataclasses

import dspy
import orjson
import typer
from rich import print

from hotpot_dspy_langgraph.config import Settings
from hotpot_dspy_langgraph.data import load_prepared_examples
from hotpot_dspy_langgraph.dspy_program import HotPotQAModule
from hotpot_dspy_langgraph.evaluation import evaluate_graph, evaluate_program
from hotpot_dspy_langgraph.graph_pipeline import build_hotpot_graph


def main(
    split_path: str,
    artifact_dir: str = "artifacts/mipro_run",
) -> None:
    """Evaluate both the raw DSPy program and the LangGraph wrapper."""

    settings = Settings.from_env()
    dspy.configure(lm=settings.build_lm())

    artifact_dir = Path(artifact_dir)
    compiled_state_path = artifact_dir / "compiled_program.json"

    program = HotPotQAModule(top_k=settings.retriever_top_k)
    if compiled_state_path.exists():
        # State-only loading is preferred over pickle-based whole-program loading.
        program.load(str(compiled_state_path))

    examples = load_prepared_examples(split_path)
    graph = build_hotpot_graph(program)

    program_agg, _ = evaluate_program(program, examples)
    graph_agg, _ = evaluate_graph(graph, examples)

    payload = {
        "program": dataclasses.asdict(program_agg),
        "graph": dataclasses.asdict(graph_agg),
    }
    (artifact_dir / "evaluation_summary.json").write_bytes(
        orjson.dumps(payload, option=orjson.OPT_INDENT_2)
    )
    print(payload)


if __name__ == "__main__":
    typer.run(main)
