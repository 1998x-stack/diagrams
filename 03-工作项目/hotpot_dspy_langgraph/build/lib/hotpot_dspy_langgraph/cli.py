"""Small Typer CLI for dataset prep, optimization, and evaluation."""

from __future__ import annotations

from pathlib import Path

import dspy
import orjson
import typer
from rich import print

from .config import Settings
from .data import load_prepared_examples, load_dspy_examples, prepare_hotpotqa_splits
from .dspy_program import HotPotQAModule
from .evaluation import evaluate_graph, evaluate_program
from .graph_pipeline import build_hotpot_graph
from .metrics import hotpot_metric

app = typer.Typer(no_args_is_help=True)


@app.command()
def prepare(
    output_dir: str = typer.Option("data/processed", help="Directory for processed JSONL splits."),
    seed: int = typer.Option(42, help="Random seed for deterministic sampling."),
) -> None:
    """Prepare the requested HotPotQA hard splits."""

    paths = prepare_hotpotqa_splits(output_dir=output_dir, seed=seed)
    print({name: str(path) for name, path in paths.items()})


@app.command()
def optimize(
    train_path: str = typer.Option(..., help="Path to processed train.jsonl."),
    val_path: str = typer.Option(..., help="Path to processed val.jsonl."),
    artifact_dir: str = typer.Option("artifacts/mipro_run", help="Where to save optimizer artifacts."),
    auto: str = typer.Option("light", help="DSPy MIPROv2 auto budget: light/medium/heavy."),
) -> None:
    """Optimize the DSPy program with MIPROv2."""

    settings = Settings.from_env()
    dspy.configure(lm=settings.build_lm())

    program = HotPotQAModule(top_k=settings.retriever_top_k)
    optimizer = dspy.MIPROv2(metric=hotpot_metric, auto=auto)

    trainset = load_dspy_examples(train_path)
    valset = load_dspy_examples(val_path)

    compiled = optimizer.compile(program, trainset=trainset, valset=valset)

    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    compiled_path = artifact_dir / "compiled_program.json"
    compiled.save(str(compiled_path), save_program=False)

    summary = {
        "artifact_dir": str(artifact_dir),
        "compiled_program": str(compiled_path),
        "optimizer": "MIPROv2",
        "auto": auto,
        "train_size": len(trainset),
        "val_size": len(valset),
    }
    (artifact_dir / "optimization_summary.json").write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
    print(summary)


@app.command()
def evaluate(
    split_path: str = typer.Option(..., help="Path to processed split JSONL."),
    compiled_program_path: str = typer.Option("", help="Optional path to a saved DSPy state JSON file."),
) -> None:
    """Evaluate the DSPy module and LangGraph pipeline on a processed split."""

    settings = Settings.from_env()
    dspy.configure(lm=settings.build_lm())

    program = HotPotQAModule(top_k=settings.retriever_top_k)
    if compiled_program_path:
        program.load(compiled_program_path)

    examples = load_prepared_examples(split_path)
    graph = build_hotpot_graph(program)

    program_agg, _ = evaluate_program(program, examples)
    graph_agg, _ = evaluate_graph(graph, examples)

    print({
        "program": program_agg.__dict__,
        "graph": graph_agg.__dict__,
    })
