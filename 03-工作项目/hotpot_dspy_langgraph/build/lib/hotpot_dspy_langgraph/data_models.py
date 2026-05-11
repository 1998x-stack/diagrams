"""Data models used across preparation, retrieval, and evaluation.

The models are intentionally plain dataclasses so the project stays light and
serializes cleanly to JSONL.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Passage:
    """A single candidate passage associated with a HotPotQA example.

    Attributes:
        title: Wikipedia page title associated with the passage.
        text: Flattened passage text.
        sentence_ids: Sentence ids retained from the original example.
        score: Optional retrieval score attached at runtime.
    """

    title: str
    text: str
    sentence_ids: list[int] = field(default_factory=list)
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the passage to a JSON-friendly dictionary."""

        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Passage":
        """Deserialize a passage from a dictionary."""

        return cls(
            title=payload["title"],
            text=payload["text"],
            sentence_ids=list(payload.get("sentence_ids", [])),
            score=payload.get("score"),
        )


@dataclass(slots=True)
class PreparedHotPotExample:
    """A processed HotPotQA example used by this project.

    The original dataset carries nested lists for titles and sentences.
    This project flattens them into `Passage` objects so retrieval and graph
    execution are easier to read.
    """

    qid: str
    question: str
    answer: str
    question_type: str
    level: str
    supporting_titles: list[str]
    supporting_sentence_ids: list[int]
    candidate_passages: list[Passage]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the example to a JSON-friendly dictionary."""

        return {
            "qid": self.qid,
            "question": self.question,
            "answer": self.answer,
            "question_type": self.question_type,
            "level": self.level,
            "supporting_titles": list(self.supporting_titles),
            "supporting_sentence_ids": list(self.supporting_sentence_ids),
            "candidate_passages": [p.to_dict() for p in self.candidate_passages],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PreparedHotPotExample":
        """Deserialize a processed example from a dictionary."""

        return cls(
            qid=payload["qid"],
            question=payload["question"],
            answer=payload["answer"],
            question_type=payload["question_type"],
            level=payload["level"],
            supporting_titles=list(payload.get("supporting_titles", [])),
            supporting_sentence_ids=list(payload.get("supporting_sentence_ids", [])),
            candidate_passages=[
                Passage.from_dict(item) for item in payload.get("candidate_passages", [])
            ],
        )
