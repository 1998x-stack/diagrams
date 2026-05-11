"""Dataset preparation and I/O utilities.

This module covers two jobs:

1. Convert the raw Hugging Face HotPotQA examples into a simpler JSONL format.
2. Convert processed examples into `dspy.Example` objects for optimization.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable

import dspy
import orjson
from datasets import Dataset, DatasetDict, load_dataset

from .data_models import Passage, PreparedHotPotExample


def _jsonl_write(path: Path, rows: Iterable[dict]) -> None:
    """Write dictionaries to a JSONL file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for row in rows:
            f.write(orjson.dumps(row))
            f.write(b"\n")


def _jsonl_read(path: Path) -> list[dict]:
    """Read a JSONL file into a list of dictionaries."""

    rows: list[dict] = []
    with path.open("rb") as f:
        for line in f:
            if line.strip():
                rows.append(orjson.loads(line))
    return rows


def flatten_context_to_passages(example: dict) -> list[Passage]:
    """Convert the nested HotPotQA context structure into passages.

    The dataset stores context as parallel arrays:
    - `context["title"]`
    - `context["sentences"]`

    We flatten each title's sentence list into one retrievable passage.
    """

    titles = example["context"]["title"]
    sentence_groups = example["context"]["sentences"]

    passages: list[Passage] = []
    for idx, (title, sentences) in enumerate(zip(titles, sentence_groups, strict=False)):
        clean_sentences = [s.strip() for s in sentences if s and s.strip()]
        if not clean_sentences:
            continue
        passages.append(
            Passage(
                title=title,
                text=" ".join(clean_sentences),
                sentence_ids=list(range(len(clean_sentences))),
            )
        )
    return passages


def raw_to_prepared(example: dict) -> PreparedHotPotExample:
    """Convert one raw HotPotQA sample to the project's simpler format."""

    return PreparedHotPotExample(
        qid=example["id"],
        question=example["question"],
        answer=example["answer"],
        question_type=example["type"],
        level=example["level"],
        supporting_titles=list(example["supporting_facts"]["title"]),
        supporting_sentence_ids=list(example["supporting_facts"]["sent_id"]),
        candidate_passages=flatten_context_to_passages(example),
    )


def save_prepared_examples(path: str | Path, examples: list[PreparedHotPotExample]) -> None:
    """Persist processed examples to JSONL."""

    _jsonl_write(Path(path), [item.to_dict() for item in examples])


def load_prepared_examples(path: str | Path) -> list[PreparedHotPotExample]:
    """Load processed examples from JSONL."""

    return [PreparedHotPotExample.from_dict(row) for row in _jsonl_read(Path(path))]


def prepared_to_dspy_example(example: PreparedHotPotExample) -> dspy.Example:
    """Convert a processed example into `dspy.Example`.

    The `candidate_passages` field is intentionally preserved as a list of
    dictionaries so the program can run local retrieval inside `forward()`.
    """

    payload = dspy.Example(
        qid=example.qid,
        question=example.question,
        answer=example.answer,
        supporting_titles=list(example.supporting_titles),
        candidate_passages=[p.to_dict() for p in example.candidate_passages],
    )
    return payload.with_inputs("question", "candidate_passages")


def load_dspy_examples(path: str | Path) -> list[dspy.Example]:
    """Load processed examples and convert them to DSPy examples."""

    return [prepared_to_dspy_example(item) for item in load_prepared_examples(path)]


def _filter_hard(dataset: Dataset) -> list[dict]:
    """Extract only `hard` items from a Hugging Face dataset split."""

    return [row for row in dataset if row.get("level") == "hard"]


def _deterministic_sample(items: list[dict], n: int, seed: int) -> list[dict]:
    """Sample `n` items deterministically from a list."""

    if n > len(items):
        raise ValueError(f"Requested {n} items, but only {len(items)} are available.")
    rng = random.Random(seed)
    copied = list(items)
    rng.shuffle(copied)
    return copied[:n]


def _train_val_split(items: list[dict], train_ratio: float, seed: int) -> tuple[list[dict], list[dict]]:
    """Create a deterministic train/validation split from a list of items."""

    rng = random.Random(seed)
    copied = list(items)
    rng.shuffle(copied)
    cutoff = int(len(copied) * train_ratio)
    return copied[:cutoff], copied[cutoff:]


def prepare_hotpotqa_splits(
    output_dir: str | Path,
    dataset_name: str = "hotpotqa/hotpot_qa",
    subset: str = "fullwiki",
    seed: int = 42,
    train_size: int = 300,
    val_size: int = 300,
    test_size: int = 500,
) -> dict[str, Path]:
    """Prepare the requested HotPotQA splits.

    The user's requested sampling recipe is implemented exactly as follows:

    - use `fullwiki`
    - keep only `hard` examples
    - official `train` -> deterministic 70/30 split -> sample 300/300
    - official `test` -> sample 500
    """

    dataset: DatasetDict = load_dataset(dataset_name, subset)

    hard_train = _filter_hard(dataset["train"])
    train_pool, val_pool = _train_val_split(hard_train, train_ratio=0.7, seed=seed)

    sampled_train = _deterministic_sample(train_pool, train_size, seed=seed + 1)
    sampled_val = _deterministic_sample(val_pool, val_size, seed=seed + 2)

    hard_test = _filter_hard(dataset["test"])
    sampled_test = _deterministic_sample(hard_test, test_size, seed=seed + 3)

    prepared_train = [raw_to_prepared(item) for item in sampled_train]
    prepared_val = [raw_to_prepared(item) for item in sampled_val]
    prepared_test = [raw_to_prepared(item) for item in sampled_test]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.jsonl"
    val_path = output_dir / "val.jsonl"
    test_path = output_dir / "test.jsonl"

    save_prepared_examples(train_path, prepared_train)
    save_prepared_examples(val_path, prepared_val)
    save_prepared_examples(test_path, prepared_test)

    return {
        "train": train_path,
        "val": val_path,
        "test": test_path,
    }
