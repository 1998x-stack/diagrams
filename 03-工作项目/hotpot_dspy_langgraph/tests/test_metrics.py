"""Minimal regression tests for core metrics."""

from hotpot_dspy_langgraph.metrics import exact_match, normalize_answer, token_f1


def test_normalize_answer() -> None:
    assert normalize_answer("The Eiffel Tower!") == "eiffel tower"


def test_exact_match() -> None:
    assert exact_match("The Beatles", "beatles") == 1.0


def test_token_f1_partial_overlap() -> None:
    score = token_f1("Barack Obama", "Obama")
    assert 0.0 < score < 1.0
