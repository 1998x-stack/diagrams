"""Evaluation helpers for the DSPy program and LangGraph pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

from .data import prepared_to_dspy_example
from .data_models import PreparedHotPotExample
from .graph_pipeline import invoke_graph
from .metrics import summarize_metrics


@dataclass(slots=True)
class ExampleResult:
    """Evaluation record for a single example."""

    qid: str
    question: str
    gold_answer: str
    pred_answer: str
    supporting_titles_csv: str
    exact_match: float
    token_f1: float
    supporting_title_recall: float


@dataclass(slots=True)
class AggregateResult:
    """Aggregate metrics for a split."""

    count: int
    exact_match: float
    token_f1: float
    supporting_title_recall: float


def _aggregate(records: list[ExampleResult]) -> AggregateResult:
    """Average metrics across evaluated records."""

    if not records:
        return AggregateResult(count=0, exact_match=0.0, token_f1=0.0, supporting_title_recall=0.0)

    return AggregateResult(
        count=len(records),
        exact_match=mean(r.exact_match for r in records),
        token_f1=mean(r.token_f1 for r in records),
        supporting_title_recall=mean(r.supporting_title_recall for r in records),
    )


def evaluate_program(program: Any, examples: list[PreparedHotPotExample]) -> tuple[AggregateResult, list[ExampleResult]]:
    """Evaluate the standalone DSPy module."""

    records: list[ExampleResult] = []
    for example in examples:
        pred = program(
            question=example.question,
            candidate_passages=[p.to_dict() for p in example.candidate_passages],
        )
        scores = summarize_metrics(
            gold_answer=example.answer,
            pred_answer=pred.answer,
            gold_titles=example.supporting_titles,
            pred_titles_csv=getattr(pred, "supporting_titles_csv", ""),
        )
        records.append(
            ExampleResult(
                qid=example.qid,
                question=example.question,
                gold_answer=example.answer,
                pred_answer=pred.answer,
                supporting_titles_csv=getattr(pred, "supporting_titles_csv", ""),
                exact_match=scores["exact_match"],
                token_f1=scores["token_f1"],
                supporting_title_recall=scores["supporting_title_recall"],
            )
        )
    return _aggregate(records), records


def evaluate_graph(graph: Any, examples: list[PreparedHotPotExample]) -> tuple[AggregateResult, list[ExampleResult]]:
    """Evaluate the LangGraph pipeline."""

    records: list[ExampleResult] = []
    for example in examples:
        state = invoke_graph(graph, example)
        pred_answer = state.get("final_answer", "")
        pred_titles_csv = state.get("supporting_titles_csv", "")
        scores = summarize_metrics(
            gold_answer=example.answer,
            pred_answer=pred_answer,
            gold_titles=example.supporting_titles,
            pred_titles_csv=pred_titles_csv,
        )
        records.append(
            ExampleResult(
                qid=example.qid,
                question=example.question,
                gold_answer=example.answer,
                pred_answer=pred_answer,
                supporting_titles_csv=pred_titles_csv,
                exact_match=scores["exact_match"],
                token_f1=scores["token_f1"],
                supporting_title_recall=scores["supporting_title_recall"],
            )
        )
    return _aggregate(records), records
