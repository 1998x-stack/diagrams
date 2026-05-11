"""LangGraph orchestration for the HotPotQA DSPy program.

The graph makes the execution steps explicit, which helps with debugging and
future expansion. DSPy handles the LM-facing parts; LangGraph handles routing.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .data_models import Passage, PreparedHotPotExample
from .dspy_program import HotPotQAModule, format_passages
from .retrieval import LocalBM25Retriever


class HotPotGraphState(TypedDict, total=False):
    """Shared graph state for one HotPotQA execution."""

    question: str
    candidate_passages: list[dict[str, Any]]
    query_1: str
    passages_1: list[dict[str, Any]]
    query_2: str
    passages_2: list[dict[str, Any]]
    evidence_text: str
    draft_answer: str
    supporting_titles_csv: str
    confidence: float
    verifier_feedback: str
    supported: bool
    retries: int
    max_retries: int
    final_answer: str


def _coerce_dict_passages(passages: list[Passage]) -> list[dict[str, Any]]:
    """Serialize passages for safe transport inside graph state."""

    return [p.to_dict() for p in passages]


def build_hotpot_graph(program: HotPotQAModule):
    """Build a LangGraph pipeline around the DSPy program."""

    graph = StateGraph(HotPotGraphState)

    def plan_first_hop(state: HotPotGraphState) -> HotPotGraphState:
        prediction = program.first_hop(question=state["question"])
        query_1 = (prediction.first_query or "").strip() or state["question"]
        return {"query_1": query_1}

    def retrieve_first_hop(state: HotPotGraphState) -> HotPotGraphState:
        candidate_passages = [Passage.from_dict(p) for p in state["candidate_passages"]]
        passages_1 = LocalBM25Retriever().retrieve(
            state["query_1"],
            candidate_passages,
            top_k=program.top_k,
        )
        return {"passages_1": _coerce_dict_passages(passages_1)}

    def plan_second_hop(state: HotPotGraphState) -> HotPotGraphState:
        first_passages = [Passage.from_dict(p) for p in state.get("passages_1", [])]
        first_evidence = format_passages(first_passages)
        prediction = program.followup(
            question=state["question"],
            gathered_evidence=first_evidence,
        )
        query_2 = (prediction.followup_query or "").strip() or state["question"]
        return {"query_2": query_2}

    def retrieve_second_hop(state: HotPotGraphState) -> HotPotGraphState:
        candidate_passages = [Passage.from_dict(p) for p in state["candidate_passages"]]
        first_passages = [Passage.from_dict(p) for p in state.get("passages_1", [])]
        passages_2 = LocalBM25Retriever().retrieve(
            state["query_2"],
            candidate_passages,
            top_k=program.top_k,
            exclude_titles={p.title for p in first_passages},
        )
        return {"passages_2": _coerce_dict_passages(passages_2)}

    def draft_answer(state: HotPotGraphState) -> HotPotGraphState:
        merged = [Passage.from_dict(p) for p in state.get("passages_1", [])] + [
            Passage.from_dict(p) for p in state.get("passages_2", [])
        ]
        evidence_text = format_passages(merged)
        if state.get("verifier_feedback"):
            evidence_text = (
                f"{evidence_text}\n\n"
                f"[Verifier feedback]\n{state['verifier_feedback']}"
            )
        prediction = program.answerer(
            question=state["question"],
            gathered_evidence=evidence_text,
        )
        return {
            "evidence_text": evidence_text,
            "draft_answer": prediction.answer,
            "supporting_titles_csv": prediction.supporting_titles_csv,
            "confidence": float(prediction.confidence),
        }

    def verify_answer(state: HotPotGraphState) -> HotPotGraphState:
        prediction = program.verifier(
            question=state["question"],
            gathered_evidence=state["evidence_text"],
            answer=state["draft_answer"],
        )
        final_answer = state["draft_answer"]
        if not bool(prediction.supported):
            revised = (prediction.revised_answer or "").strip()
            if revised:
                final_answer = revised
        return {
            "supported": bool(prediction.supported),
            "verifier_feedback": prediction.verifier_feedback,
            "final_answer": final_answer,
            "retries": state.get("retries", 0) + 1,
        }

    def route_after_verification(state: HotPotGraphState) -> str:
        if state.get("supported", False):
            return "finalize"
        if state.get("retries", 0) > state.get("max_retries", 1):
            return "finalize"
        return "draft_answer"

    def finalize(state: HotPotGraphState) -> HotPotGraphState:
        return {"final_answer": state.get("final_answer", state.get("draft_answer", ""))}

    graph.add_node("plan_first_hop", plan_first_hop)
    graph.add_node("retrieve_first_hop", retrieve_first_hop)
    graph.add_node("plan_second_hop", plan_second_hop)
    graph.add_node("retrieve_second_hop", retrieve_second_hop)
    graph.add_node("draft_answer", draft_answer)
    graph.add_node("verify_answer", verify_answer)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "plan_first_hop")
    graph.add_edge("plan_first_hop", "retrieve_first_hop")
    graph.add_edge("retrieve_first_hop", "plan_second_hop")
    graph.add_edge("plan_second_hop", "retrieve_second_hop")
    graph.add_edge("retrieve_second_hop", "draft_answer")
    graph.add_edge("draft_answer", "verify_answer")
    graph.add_conditional_edges("verify_answer", route_after_verification)
    graph.add_edge("finalize", END)

    return graph.compile()


def invoke_graph(graph, example: PreparedHotPotExample, max_retries: int = 1) -> HotPotGraphState:
    """Run the compiled graph on one processed example."""

    initial_state: HotPotGraphState = {
        "question": example.question,
        "candidate_passages": [p.to_dict() for p in example.candidate_passages],
        "retries": 0,
        "max_retries": max_retries,
    }
    return graph.invoke(initial_state)
