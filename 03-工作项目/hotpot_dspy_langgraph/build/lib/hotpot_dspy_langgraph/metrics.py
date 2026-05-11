"""Evaluation metrics for HotPotQA-style answer checking.

The metrics here intentionally focus on answer quality first. Supporting title
matching is reported as an auxiliary signal.
"""

from __future__ import annotations

import re
import string
from collections import Counter
from typing import Any

_ARTICLES = re.compile(r"\b(a|an|the)\b")
_WHITESPACE = re.compile(r"\s+")


def normalize_answer(text: str) -> str:
    """Normalize answers using the standard QA cleanup recipe.

    This mirrors the common exact-match / token-F1 normalization strategy used
    in reading-comprehension benchmarks.
    """

    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = _ARTICLES.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text


def exact_match(gold: str, pred: str) -> float:
    """Return 1.0 when normalized answers match exactly, else 0.0."""

    return float(normalize_answer(gold) == normalize_answer(pred))


def token_f1(gold: str, pred: str) -> float:
    """Compute token-level F1 after normalization."""

    gold_tokens = normalize_answer(gold).split()
    pred_tokens = normalize_answer(pred).split()

    if not gold_tokens and not pred_tokens:
        return 1.0
    if not gold_tokens or not pred_tokens:
        return 0.0

    common = Counter(gold_tokens) & Counter(pred_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0

    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def supporting_title_recall(gold_titles: list[str], pred_titles_csv: str) -> float:
    """Measure how many gold supporting titles were surfaced by the model."""

    gold_set = {normalize_answer(title) for title in gold_titles if title}
    pred_set = {
        normalize_answer(part)
        for part in pred_titles_csv.split(",")
        if part and normalize_answer(part)
    }

    if not gold_set:
        return 1.0
    if not pred_set:
        return 0.0
    return len(gold_set & pred_set) / len(gold_set)


def hotpot_metric(example: Any, pred: Any, trace: Any | None = None) -> float:
    """DSPy-compatible optimization metric.

    The score emphasizes answer correctness while giving a small bonus for
    surfacing the right supporting titles.
    """

    gold_answer = getattr(example, "answer", "")
    pred_answer = getattr(pred, "answer", "")
    gold_titles = getattr(example, "supporting_titles", [])
    pred_titles_csv = getattr(pred, "supporting_titles_csv", "")

    answer_score = token_f1(gold_answer, pred_answer)
    title_score = supporting_title_recall(gold_titles, pred_titles_csv)
    return 0.9 * answer_score + 0.1 * title_score


def summarize_metrics(gold_answer: str, pred_answer: str, gold_titles: list[str], pred_titles_csv: str) -> dict[str, float]:
    """Return a compact dictionary of evaluation metrics for reporting."""

    return {
        "exact_match": exact_match(gold_answer, pred_answer),
        "token_f1": token_f1(gold_answer, pred_answer),
        "supporting_title_recall": supporting_title_recall(gold_titles, pred_titles_csv),
    }
