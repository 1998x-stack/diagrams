# traj-gep

Independent parallel experiment: mine `*.traj` corpora into evolver-schema GEP
**Genes** with the 7 canonical fields
`id / category / signals_match / preconditions / strategy / constraints / validation`,
then de-duplicate semantically-equivalent Genes via Stage 5.

Pipeline: load → extract signals → cluster patterns → build Genes → clean Genes.
Stages 3, 4, and 5 are LLM-augmented (default `qwen3.6-plus`; switch to
`claude-sonnet-4-6` via `--model`).

## Setup

```bash
cd traj-gep
python3 -m pip install -r requirements.txt
export DASHSCOPE_API_KEY=sk-...        # default Qwen backend
# or
export ANTHROPIC_API_KEY=sk-ant-...    # required when using --model claude-*
make verify-wrapper                    # smoke-test the Node bridge
```

## Run — built-in projects

```bash
make pipeline-wzp                # ~5 minutes (cold LLM cache)
make pipeline-zzj
# Output: output/{wzp,zzj}/cleaned_genes.json (and genes.json, clusters.json, ...)
```

## Run — arbitrary corpus

```bash
make pipeline TRAJ=/path/to/your/traj-dir
# PROJECT inferred from basename; outputs land in output/<basename>/
```

## Run — switch to Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
make pipeline TRAJ=../traj-data-new/wzp \
  PROJECT=wzp-claude          # avoid colliding with the qwen output dir

# Or set per stage:
python3 -m scripts.cluster_patterns ... --model claude-sonnet-4-6
python3 -m scripts.build_genes      ... --model claude-sonnet-4-6
python3 -m scripts.clean_genes      ... --model claude-sonnet-4-6
```

Cached re-runs (after first complete pass) take ~10 seconds — the LLM cache at
`output/<project>/llm_cache.jsonl` is consulted before any API call. Cache keys
include the model, so qwen and claude runs do not collide.

## Test

```bash
make test                            # ~50 tests, none touch live LLM APIs
```

## Stage 5: cleaned_genes.json

Stage 5 (`scripts/clean_genes.py`) groups duplicate Genes within each category
via one LLM call per category and produces `output/<project>/cleaned_genes.json`.
The original `genes.json` is preserved unchanged for diffing. Tunables in
`config.yaml` under `cleaning:`.

## Troubleshooting

- `extract_signals.js` errors: confirm `../evolver/src/gep/signals.js` exists.
- `DASHSCOPE_API_KEY` missing: required for default Qwen backend.
- `ANTHROPIC_API_KEY` missing: required when `llm.model` resolves to `claude-*`.
- Want to wipe and re-run from scratch: `make clean PROJECT=wzp`.

## Output schema (genes.json / cleaned_genes.json)

See `docs/superpowers/specs/2026-04-20-traj-gep-design.md` §Stage 4 for the
canonical Gene schema and `2026-04-20-traj-gep-v2-design.md` §Stage 5 for the
merge rules and `_merged_from` provenance field.
