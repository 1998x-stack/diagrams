# traj-gep v2 — Extensible CLI, Multi-Provider LLM, Stage 5 Dedupe

**Date:** 2026-04-20
**Status:** Approved (pending implementation plan)
**Supersedes (partially):** `2026-04-20-traj-gep-design.md` — adds Stage 5 and provider abstraction; does not change Stages 1–4 schemas.

## Goal

Three additive improvements to traj-gep, no schema or breaking pipeline changes:

1. **Extensible corpus input.** Run the pipeline against any directory of `.traj` files, not just `wzp` and `zzj`.
2. **Multi-provider LLM client.** Support both Qwen (Dashscope OpenAI-compat) and Claude (Anthropic SDK) selectable via `--model`.
3. **Stage 5 — gene deduplication.** Cluster near-duplicate genes from `genes.json` into `cleaned_genes.json`. Motivated by observed duplication: `output/zzj/genes.json` contains 11 genes with the title *"High Frequency Visual Feedback Iteration And Logic Correction Pattern"*.

## Non-goals

- No changes to `.traj` schema, `extract_signals.js`, or the v2 viewer.
- No embedding-based dedupe in Stage 5.
- No multi-corpus merging into a single output.

## Design

### 1. Extensible `--traj` input

**Flag.** All pipeline scripts accept `--traj <dir>` pointing at a directory of `.traj` files. `load_trajectories.py` keeps the existing `--traj-dir` flag as an alias for back-compat.

**Project derivation.** `--project` becomes optional. If omitted, derive from `basename(--traj)`:
```
--traj /foo/bar/wzp        → project = "wzp"
--traj /foo/bar/my-corpus  → project = "my-corpus"
```

**Output layout.** Unchanged: `output/<project>/{sessions.jsonl, signals.jsonl, clusters.json, genes.json, cleaned_genes.json, llm_cache.jsonl}`.

**Makefile.** New generic variables and target:
```
TRAJ    ?= ../traj-data-new/$(PROJECT)
PROJECT ?= $(notdir $(patsubst %/,%,$(TRAJ)))

make pipeline TRAJ=../traj-data-new/wzp        # PROJECT inferred from basename
make pipeline TRAJ=/abs/path PROJECT=custom    # explicit override
```
All sub-targets (`load`, `extract`, `cluster`, `build`, `clean-genes`) pass `--traj $(TRAJ) --project $(PROJECT)` to their scripts. Existing `pipeline-wzp` and `pipeline-zzj` become thin wrappers: `$(MAKE) pipeline TRAJ=../traj-data-new/wzp`.

### 2. LLM client — provider abstraction

**Refactor `scripts/llm_client.py` into:**

| Component | Responsibility |
|---|---|
| `LLMConfig` | Adds `provider: Literal["qwen", "claude"]`. Other fields unchanged. |
| `_OpenAIBackend` | Current behavior. Used for Qwen (Dashscope `compatible-mode`). |
| `_AnthropicBackend` | New. Wraps `anthropic.Anthropic().messages.create(...)`. |
| `LLMClient` | Public surface unchanged (`call(system=..., user=...) -> dict`). Dispatches to the chosen backend. |

**Provider auto-detection.** From the model name string at config-load time:
- `claude*` → `claude` provider
- everything else → `qwen` provider
- Override via `llm.provider` in `config.yaml` (explicit wins).

**API key env per provider.**
| Provider | Env var |
|---|---|
| qwen | `DASHSCOPE_API_KEY` |
| claude | `ANTHROPIC_API_KEY` |

`load_llm_config()` reads the env appropriate to the resolved provider; raises if missing.

**JSON output for Anthropic.** Anthropic has no `response_format=json_object`. We:
1. Append a fixed instruction to the system prompt: *"Respond with a single JSON object only. No prose, no Markdown fences."*
2. After the call, attempt `json.loads(content)`.
3. On failure, strip surrounding ```json ... ``` fences once and retry the parse.
4. If still failing, return `{"_fallback": True, "_reason": "json_parse"}` (matches existing fallback shape).

**CLI `--model` flag.** Added to `cluster_patterns.py` and `build_genes.py`. Overrides `llm.model` from `config.yaml` for that run. Default unchanged: `qwen3.6-plus`.

**Cache compatibility.** The current cache key is `SHA256(model + "\n" + system + "\n---\n" + user)`. Because `model` is part of the key, qwen runs and claude runs naturally don't collide — no migration needed. Cache file path stays per-project.

**Dependencies.** Add `anthropic>=0.40` to `requirements.txt`.

### 3. Stage 5 — `clean_genes.py` (LLM-based clustering)

**Script.** New `scripts/clean_genes.py`:

```
Input:  output/<project>/genes.json    (Stage 4 output, untouched)
Output: output/<project>/cleaned_genes.json
```

**Why LLM, not Jaccard.** Set-overlap on `signals_match` is brittle: two genes describing the same workflow can use partially-overlapping signal vocabularies, and two genes with high signal overlap can describe genuinely different patterns. A small LLM call comparing semantic content (titles + preconditions) is more reliable than a vocabulary-overlap heuristic.

**Algorithm:**

1. Load all genes from `genes.json`. Group by `category` (currently `workflow`, `optimize`, `repair`, `innovate`).
2. **Per category, one LLM call** (so prompts stay focused and a `repair` gene can never silently merge with a `workflow` gene):
   - Build a compact summary list. For each gene: `{id, title_zh, title_en, frequency, preconditions[]}`. Strategy/signals omitted to keep the prompt small.
   - System prompt: instruct the LLM to cluster genes that describe **the same operational pattern** (same trigger conditions and same intent), assign each cluster a single canonical `new_title_zh` and `new_title_en` (prefer the highest-frequency member's wording when reasonable), and list the member `id`s. Single-member clusters are valid.
   - Response JSON schema:
     ```json
     {"clusters": [
       {"new_title_zh": "...", "new_title_en": "...", "ids": ["gene_a", "gene_b", ...]},
       ...
     ]}
     ```
3. **Validation of LLM output:**
   - Every input `id` must appear in exactly one cluster. Missing ids → assign each to its own singleton cluster (deterministic recovery, log a warning). Duplicated ids → drop the second occurrence (warn).
   - Unknown ids → drop (warn).
   - On `_fallback` (LLM unavailable / unparseable after retries): fall back to one cluster per gene (no merging, never crashes the pipeline).
4. For each cluster, build one merged gene using these deterministic rules:

| Field | Merge rule |
|---|---|
| `id` | If cluster size = 1: keep original. Else: `<highest_frequency_member_id>_merged_<N>` where N = cluster size. |
| `category` | All members share one (enforced by per-category clustering). |
| `signals_match` | Set-union of member `signals_match`, sorted, capped at `gene_builder.max_signals_match`. |
| `preconditions` | Concatenate member lists, dedupe by exact string, preserve first-occurrence order. |
| `strategy` | Concatenate, dedupe, cap at `gene_builder.max_strategy_steps`. |
| `validation` | Concatenate, dedupe. |
| `constraints.max_files` | `max(...)` across members. |
| `constraints.forbidden_paths` | Set-union, sorted. |
| `title_zh`, `title_en` | From the LLM (`new_title_zh`, `new_title_en`). For singleton clusters, fall back to the original gene's titles if LLM omits them. |
| `_provenance.frequency` | `sum(...)` |
| `_provenance.session_count` | `sum(...)` (we accept slight over-counting if a session appears in multiple members) |
| `_provenance.session_hashes_sample` | Set-union, sorted, capped at `gene_builder.provenance_session_sample`. |
| `_provenance._merged_from` | List of member `id`s, sorted. Omitted when cluster size = 1. |
| `_provenance.source` | `"traj-gep"` (unchanged). |
| `_provenance.project` | unchanged. |

5. Sort merged genes by `_provenance.frequency` descending, then `id` ascending. Write to `cleaned_genes.json`.

**Config additions (`config.yaml`):**
```yaml
cleaning:
  prompt_max_genes_per_call: 80    # safety cap; if a category exceeds this, split into chunks
  min_titles_for_llm: 2            # categories with <2 genes skip the LLM call entirely
```

**Prompt template lives at:** `prompts/clean_genes.txt`. Loaded at runtime, identical pattern to `prompts/cluster_summary.txt` and `prompts/gene_strategy.txt`.

**CLI:**
```
python -m scripts.clean_genes \
  --genes  output/<project>/genes.json \
  --config config.yaml \
  --output output/<project>/cleaned_genes.json
```

**Makefile:**
```
clean-genes: build
    $(PYTHON) -m scripts.clean_genes \
      --genes  output/$(PROJECT)/genes.json \
      --config config.yaml \
      --output output/$(PROJECT)/cleaned_genes.json

pipeline: clean-genes        # default pipeline now ends at Stage 5
```

## Testing

Tests live in `tests/`. Mirror the existing fake-LLM pattern (no live API calls).

**`test_llm_client_anthropic.py`** (new, ~5 tests):
- Provider auto-detect: `claude-sonnet-4-6` → `claude`, `qwen3.6-plus` → `qwen`, override via config wins.
- Anthropic backend returns parsed JSON when content is clean.
- Anthropic backend strips ```json fences and parses successfully.
- Anthropic backend returns `{"_fallback": True}` when JSON unparseable after fence-strip.
- Cache key includes model — same prompt under different models yields different keys.

**`test_clean_genes.py`** (new, ~5 tests, all use a fake LLM via monkeypatch — no live API):
- LLM clusters two genes into one merged gene with summed frequency, unioned session hashes, `_merged_from` list, and titles from LLM output.
- Genes are sent to the LLM grouped by category — `repair` and `workflow` never appear in the same prompt.
- LLM output that omits an input id is recovered: missing ids become singleton clusters; warning emitted on stderr.
- LLM `_fallback` response leaves every gene as a singleton (no merging, exit code 0).
- Singleton cluster from LLM keeps the original gene's titles when LLM provides empty `new_title_zh/en`.

**`test_load_trajectories_cli.py`** (extend existing):
- `--traj` accepted; `--traj-dir` still works.
- `--project` derived from `basename(--traj)` when omitted.
- `--project` explicit override wins.

Run via existing `make test`.

## Migration & back-compat

- `genes.json` format unchanged. Existing `output/{wzp,zzj}/genes.json` files remain valid.
- `make pipeline-wzp` / `pipeline-zzj` keep working.
- `--traj-dir` keeps working.
- Default model and provider unchanged (Qwen).
- Existing `output/{wzp,zzj}/llm_cache.jsonl` remains valid (key format unchanged).

## Files touched

| File | Change |
|---|---|
| `scripts/llm_client.py` | Refactor to provider-abstracted backends. |
| `scripts/load_trajectories.py` | Add `--traj` flag (alias of `--traj-dir`); derive `--project`. |
| `scripts/extract_signals.py` | Same. |
| `scripts/cluster_patterns.py` | Same + `--model`. |
| `scripts/build_genes.py` | Same + `--model`. |
| `scripts/clean_genes.py` | **New.** Stage 5 (LLM-clustered dedupe). |
| `prompts/clean_genes.txt` | **New.** System prompt for Stage 5 LLM call. |
| `config.yaml` | Add `cleaning:` block. Optional `llm.provider:`. |
| `requirements.txt` | Add `anthropic>=0.40`. |
| `Makefile` | New `pipeline` and `clean-genes` targets; existing `pipeline-{wzp,zzj}` rewritten as wrappers. |
| `tests/test_llm_client_anthropic.py` | New. |
| `tests/test_clean_genes.py` | New. |
| `tests/test_load_trajectories.py` (or conftest) | Extend for `--traj`. |
| `README.md` | Document `--traj`, `--model`, Stage 5. |

## Open thresholds (defaults chosen, easy to tune)

| Knob | Default | Rationale |
|---|---|---|
| `cleaning.prompt_max_genes_per_call` | `80` | wzp has 59 and zzj has 31 today, so all categories fit in one call. Cap protects against future corpora. |
| `cleaning.min_titles_for_llm` | `2` | A category with 0 or 1 genes has nothing to cluster. |
| `prompts/clean_genes.txt` | LLM is told: cluster genes describing the same operational pattern; one canonical title per cluster; preserve all input ids exactly once. |
