"""DSPy modules for multi-hop HotPotQA.

This module keeps all LM-facing logic inside DSPy:

- first-hop query planning
- follow-up query generation
- answer synthesis
- answer verification

The `HotPotQAModule` can run standalone and is also the core engine used by the
LangGraph pipeline in `graph_pipeline.py`.
"""

from __future__ import annotations

from typing import Any

import dspy

from .config import Settings
from .data_models import Passage
from .retrieval import LocalBM25Retriever


def _coerce_passages(candidate_passages: list[dict[str, Any]] | list[Passage]) -> list[Passage]:
    """Normalize raw passage payloads into `Passage` instances."""

    result: list[Passage] = []
    for item in candidate_passages:
        if isinstance(item, Passage):
            result.append(item)
        else:
            result.append(Passage.from_dict(item))
    return result


def format_passages(passages: list[Passage]) -> str:
    """Render passages into a compact prompt-friendly string."""

    if not passages:
        return "<no_passages>"

    chunks: list[str] = []
    for idx, passage in enumerate(passages, start=1):
        score_str = "" if passage.score is None else f" score={passage.score:.3f}"
        chunks.append(
            f"[Passage {idx}{score_str}]\n"
            f"Title: {passage.title}\n"
            f"Text: {passage.text}"
        )
    return "\n\n".join(chunks)


class FirstHopQuery(dspy.Signature):
    """Write a focused first retrieval query for a multi-hop question."""

    question: str = dspy.InputField(desc="Original HotPotQA question.")
    first_query: str = dspy.OutputField(desc="Short first-hop retrieval query.")


class FollowupQuery(dspy.Signature):
    """Write the next retrieval query using the current evidence."""

    question: str = dspy.InputField(desc="Original question.")
    gathered_evidence: str = dspy.InputField(desc="Already retrieved evidence.")
    followup_query: str = dspy.OutputField(desc="Short second-hop retrieval query.")


class SynthesizeAnswer(dspy.Signature):
    """Answer a multi-hop question from retrieved evidence.

    The model is also asked to surface supporting titles because HotPotQA is not
    just about final answers; evidence selection matters too.
    """

    question: str = dspy.InputField(desc="Original question.")
    gathered_evidence: str = dspy.InputField(desc="Retrieved evidence from one or more hops.")
    answer: str = dspy.OutputField(desc="Final short answer.")
    supporting_titles_csv: str = dspy.OutputField(
        desc="Comma-separated titles used to answer the question."
    )
    confidence: float = dspy.OutputField(desc="Confidence from 0 to 1.")


class VerifyAnswer(dspy.Signature):
    """Verify whether the candidate answer is supported by the evidence."""

    question: str = dspy.InputField(desc="Original question.")
    gathered_evidence: str = dspy.InputField(desc="Evidence used by the answerer.")
    answer: str = dspy.InputField(desc="Candidate answer to verify.")
    supported: bool = dspy.OutputField(desc="True if the answer is supported.")
    revised_answer: str = dspy.OutputField(desc="Improved answer if a revision is needed.")
    verifier_feedback: str = dspy.OutputField(desc="One short sentence of feedback.")


class HotPotQAModule(dspy.Module):
    """A DSPy multi-hop QA program with local retrieval.

    The module is intentionally compact so it can be optimized by DSPy
    optimizers and reused inside LangGraph nodes.
    """

    def __init__(self, top_k: int = 3) -> None:
        super().__init__()
        self.top_k = top_k

        # Separate DSPy predictors keep the program decomposed and optimizable.
        self.first_hop = dspy.Predict(FirstHopQuery)
        self.followup = dspy.ChainOfThought(FollowupQuery)
        self.answerer = dspy.ChainOfThought(SynthesizeAnswer)
        self.verifier = dspy.Predict(VerifyAnswer)

    @classmethod
    def from_settings(cls, settings: Settings) -> "HotPotQAModule":
        """Create and globally configure a program from project settings."""

        dspy.configure(lm=settings.build_lm())
        return cls(top_k=settings.retriever_top_k)

    def retrieve_first_hop(self, question: str, passages: list[Passage]) -> tuple[str, list[Passage]]:
        """Generate the first query and retrieve passages."""

        prediction = self.first_hop(question=question)
        query_1 = (prediction.first_query or "").strip() or question
        first_passages = LocalBM25Retriever().retrieve(query_1, passages, top_k=self.top_k)
        return query_1, first_passages

    def retrieve_second_hop(
        self,
        question: str,
        passages: list[Passage],
        first_passages: list[Passage],
    ) -> tuple[str, list[Passage]]:
        """Use first-hop evidence to plan and execute the follow-up retrieval."""

        first_evidence = format_passages(first_passages)
        prediction = self.followup(question=question, gathered_evidence=first_evidence)
        query_2 = (prediction.followup_query or "").strip() or question
        excluded = {p.title for p in first_passages}
        second_passages = LocalBM25Retriever().retrieve(
            query_2,
            passages,
            top_k=self.top_k,
            exclude_titles=excluded,
        )
        return query_2, second_passages

    def forward(self, question: str, candidate_passages: list[dict[str, Any]] | list[Passage]) -> dspy.Prediction:
        """Run retrieval -> reasoning -> answer verification.

        Args:
            question: Original HotPotQA question.
            candidate_passages: Candidate passage pool extracted from the sample.

        Returns:
            A `dspy.Prediction` with the answer, evidence titles, confidence, and
            intermediate retrieval queries.
        """

        passages = _coerce_passages(candidate_passages)
        query_1, first_passages = self.retrieve_first_hop(question, passages)
        query_2, second_passages = self.retrieve_second_hop(question, passages, first_passages)

        merged_passages = first_passages + second_passages
        evidence_text = format_passages(merged_passages)

        answer_prediction = self.answerer(
            question=question,
            gathered_evidence=evidence_text,
        )
        verify_prediction = self.verifier(
            question=question,
            gathered_evidence=evidence_text,
            answer=answer_prediction.answer,
        )

        final_answer = answer_prediction.answer
        if not getattr(verify_prediction, "supported", False):
            revised = (getattr(verify_prediction, "revised_answer", "") or "").strip()
            if revised:
                final_answer = revised

        return dspy.Prediction(
            answer=final_answer,
            supporting_titles_csv=answer_prediction.supporting_titles_csv,
            confidence=float(answer_prediction.confidence),
            verifier_feedback=getattr(verify_prediction, "verifier_feedback", ""),
            supported=bool(getattr(verify_prediction, "supported", False)),
            query_1=query_1,
            query_2=query_2,
            evidence_text=evidence_text,
        )
