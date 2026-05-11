# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable)
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/test_metrics.py::test_name

# Prepare dataset
python scripts/prepare_hotpotqa.py --output-dir data/processed --seed 42

# Optimize DSPy program (requires prepared data)
python scripts/optimize_hotpotqa.py \
  --train-path data/processed/train.jsonl \
  --val-path data/processed/val.jsonl \
  --artifact-dir artifacts/mipro_run

# Evaluate
python scripts/run_eval.py \
  --split-path data/processed/test.jsonl \
  --artifact-dir artifacts/mipro_run
```

## Environment

```bash
export DASHSCOPE_API_KEY="<key>"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export OPENAI_MODEL="qwen3.6-plus"
```

All LM calls must use `qwen3.6-plus` with `enable_thinking=False` (set in `Settings.build_lm()`). This is enforced via `extra_body={"enable_thinking": False}` in the DSPy LM constructor.

## Architecture

**Separation of concerns:** DSPy owns LM logic; LangGraph owns orchestration.

- `config.py` — `Settings` dataclass, reads env vars, builds the `dspy.LM` instance
- `data_models.py` — `Passage` and `PreparedHotPotExample` dataclasses
- `retrieval.py` — `LocalBM25Retriever`: retrieves from in-example passage pool (stand-in for full Wikipedia retrieval)
- `dspy_program.py` — `HotPotQAModule`: 4 DSPy predictors (first-hop query, follow-up query, synthesize answer, verify answer); can run standalone
- `graph_pipeline.py` — `build_hotpot_graph()`: wraps the same predictors as explicit LangGraph nodes with retry routing via `route_after_verification`
- `data.py` — dataset loading from HuggingFace; 70/30 train split, 300/300/500 sample sizes
- `evaluation.py` — batch evaluation over splits
- `metrics.py` — answer scoring (exact match, F1)

**Graph flow:** `plan_first_hop → retrieve_first_hop → plan_second_hop → retrieve_second_hop → draft_answer → verify_answer →` (retry loop or `finalize`)

DSPy predictors in `HotPotQAModule` and the LangGraph nodes in `graph_pipeline.py` share the same underlying `program.first_hop`, `program.followup`, `program.answerer`, and `program.verifier` instances — the graph delegates directly to the module's predictors, not a separate implementation.
