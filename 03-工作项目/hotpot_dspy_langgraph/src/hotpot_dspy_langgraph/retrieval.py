"""Retrieval utilities for the HotPotQA graph.

The default retriever is intentionally simple: a per-example BM25 ranker over
candidate passages extracted from the dataset's `context` field.

This is a good educational default because it keeps the project runnable with no
external infrastructure. In a real fullwiki reproduction, swap this retriever
for a corpus-scale system.
"""

from __future__ import annotations

import math
import re
from dataclasses import replace
from typing import Protocol

from rank_bm25 import BM25Okapi

from .data_models import Passage

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class Retriever(Protocol):
    """Protocol for pluggable retrievers."""

    def retrieve(
        self,
        query: str,
        passages: list[Passage],
        top_k: int = 3,
        exclude_titles: set[str] | None = None,
    ) -> list[Passage]:
        """Return the best matching passages for a query."""


def simple_tokenize(text: str) -> list[str]:
    """A compact tokenizer suitable for local BM25 ranking."""

    return _TOKEN_RE.findall(text.lower())


class LocalBM25Retriever:
    """A small BM25 retriever over the current example's passage set.

    The retriever is rebuilt per example because each HotPotQA item already
    ships with a small local passage universe in the processed JSONL.
    """

    def retrieve(
        self,
        query: str,
        passages: list[Passage],
        top_k: int = 3,
        exclude_titles: set[str] | None = None,
    ) -> list[Passage]:
        """Rank passages using BM25 and return the top matches."""

        exclude_titles = exclude_titles or set()
        usable = [p for p in passages if p.title not in exclude_titles]
        if not usable:
            return []

        tokenized_corpus = [simple_tokenize(f"{p.title} {p.text}") for p in usable]
        # BM25 works poorly on empty token lists, so we guard against that.
        tokenized_corpus = [tokens if tokens else ["<empty>"] for tokens in tokenized_corpus]
        bm25 = BM25Okapi(tokenized_corpus)

        tokenized_query = simple_tokenize(query) or ["<empty>"]
        scores = bm25.get_scores(tokenized_query)

        ranked_pairs = sorted(
            zip(usable, scores, strict=False),
            key=lambda item: item[1],
            reverse=True,
        )

        selected: list[Passage] = []
        for passage, score in ranked_pairs[:top_k]:
            clean_score = float(score)
            if math.isnan(clean_score):
                clean_score = 0.0
            selected.append(replace(passage, score=clean_score))
        return selected
