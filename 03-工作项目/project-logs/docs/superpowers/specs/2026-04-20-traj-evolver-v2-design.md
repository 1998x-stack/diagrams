# Traj-Evolver V2 Design

**Date:** 2026-04-20
**Status:** Design — awaiting user review

## Goal

Replace the LLM-enrichment and instinct-cli stages of the traj-evolver v1 pipeline with the `evolver/` GEP engine. Trajectory patterns are formatted as evolver-native Gene and Capsule assets, injected via `a2a_ingest.js`, and then exported as ECC skill folders by a new Python builder.

## Non-Goals

- No changes to Stage 1 (`traj_miner.py`) — it is reused as-is from `traj-evolver/`
- No changes to `evolver/` source code
- No support for continuous / live ingestion — this remains a batch pipeline
- No cross-project gene merging (wzp and zzj run independently)

## Architecture

```
traj-evolver-v2/
├── config.yaml                   # evolver_path, thresholds, project config
├── Makefile                      # mine/format/ingest/distill/pipeline/test targets
├── README.md
├── scripts/
│   ├── format_patterns.py        # Stage 2: patterns.json → A2A Gene/Capsule JSONL
│   └── build_ecc_skills.py       # Stage 4: evolver store → ECC skill folders
└── tests/
    ├── conftest.py               # shared fixtures
    ├── test_format_patterns.py   # TDD for pattern → Gene/Capsule mapping
    └── test_build_ecc.py         # TDD for evolver store → ECC output
```

## Pipeline

```
traj-data-new/{wzp,zzj}/*.traj
  ↓ [Stage 1] traj-evolver/scripts/traj_miner.py  (Python, reused from v1)
traj-evolver-v2/patterns/{wzp,zzj}/patterns.json
  ↓ [Stage 2] traj-evolver-v2/scripts/format_patterns.py  (Python)
traj-evolver-v2/formatted/{wzp,zzj}/genes.jsonl + capsules.jsonl
  ↓ [Stage 3] node evolver/scripts/a2a_ingest.js  (existing Node.js, called as subprocess)
evolver/assets/gep/external_candidates.jsonl  (evolver's persistent store)
  ↓ [Stage 4] traj-evolver-v2/scripts/build_ecc_skills.py  (Python)
project-logs/evolved/{wzp,zzj}/
  ├── skills/<gene_id>/SKILL.md
  ├── commands/<capsule_id>.md
  ├── agents/<intent>-agent.md
  └── README.md
```

Each stage writes to disk for resumability. wzp and zzj run as independent parallel pipelines.

## Stage 2: format_patterns.py

**Input:** `patterns.json` (output of traj_miner.py)
**Output:** `formatted/{project}/genes.jsonl` + `formatted/{project}/capsules.jsonl`

### CLI

```bash
python3 traj-evolver-v2/scripts/format_patterns.py \
  --patterns-file traj-evolver-v2/patterns/wzp/patterns.json \
  --output-dir    traj-evolver-v2/formatted/wzp \
  --project       wzp \
  --project-name  "wzp-脑力大冒险" \
  --evolver-dir   evolver
```

### Pattern → Gene/Capsule Mapping

**Genes** — behavioral rules for evolver's gene selector. Written to `genes.jsonl`.

| Pattern family | Gene `category` | `signals_match` derivation | `strategy` |
|---|---|---|---|
| `tool_sequence` | `workflow` | pattern `keywords` array | `"When {keywords}, apply {sequence} tool flow"` |
| `phase_transition` | `workflow` | from-phase name (e.g., `"localization"`) | `"Follow {from}→{to} phase transition"` |
| `tool_fingerprint` | `platform` | tool name fragments (e.g., `"sce-urhox"`, `"build"`) | `"Use project-specific tool {tool}"` |

Every Gene includes:
- `type`: `"Gene"`
- `id`: derived from pattern id, truncated to 60 chars, `[a-z0-9_-]+`
- `schema_version`: imported from evolver's `contentHash.SCHEMA_VERSION` (read from `evolver/src/gep/contentHash.js` — use the string constant `"2"` as fallback if obfuscated)
- `asset_id`: `sha256(canonical_json)[:16]` (replicate evolver's `computeAssetId` in Python)
- `a2a.status`: `"external_candidate"`
- `a2a.source`: `"traj-{project}"` (e.g., `"traj-wzp"`)
- `a2a.received_at`: ISO timestamp
- `constraints`: `{"max_files": 10, "forbidden_paths": [".git", "node_modules"]}`
- `validation`: `[]`

**Capsules** — successful execution records. Written to `capsules.jsonl`.

| Pattern family | Capsule `intent` | `confidence` | `strategy` |
|---|---|---|---|
| `task_shape` | `workflow` | frequency-based (same table as v1) | describes the tool cluster |
| `correction_signal` | `repair` | min(frequency-based, 0.45) | `"Undo {file} edit when user corrects"` |

Confidence table (before 0.6 A2A factor):

| Frequency | Raw confidence |
|---|---|
| ≥ 20 | 0.85 |
| 10–19 | 0.75 |
| 5–9 | 0.65 |
| 3–4 | 0.55 |

Every Capsule includes:
- `type`: `"Capsule"`
- `id`: derived from pattern id
- `schema_version`, `asset_id`, `a2a.*`: same as Gene
- `blast_radius`: `{"files": 0, "lines": 0}` (trajectory patterns are read-only)

### asset_id Computation (Python)

Evolver computes `asset_id` as `sha256` of a canonical JSON string with certain fields excluded. Replicate in Python:

```python
import hashlib, json

EXCLUDED_KEYS = {"asset_id", "a2a", "schema_version"}

def compute_asset_id(asset: dict) -> str:
    filtered = {k: v for k, v in asset.items() if k not in EXCLUDED_KEYS}
    canonical = json.dumps(filtered, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
```

## Stage 3: a2a_ingest.js (existing)

Called as a subprocess from the Makefile:

```bash
A2A_SOURCE=traj-wzp A2A_EXTERNAL_CONFIDENCE_FACTOR=0.6 \
  node evolver/scripts/a2a_ingest.js traj-evolver-v2/formatted/wzp/genes.jsonl

A2A_SOURCE=traj-wzp A2A_EXTERNAL_CONFIDENCE_FACTOR=0.6 \
  node evolver/scripts/a2a_ingest.js traj-evolver-v2/formatted/wzp/capsules.jsonl
```

After ingestion, assets appear in `evolver/assets/gep/external_candidates.jsonl` tagged with `a2a.source = "traj-wzp"` and confidence reduced by 0.6×.

**Note:** `a2a_ingest.js` requires `A2A_NODE_ID` to be set (evolver requirement). Set it in config.yaml or `.env` as `A2A_NODE_ID=traj-evolver-v2`.

## Stage 4: build_ecc_skills.py

**Input:** `evolver/assets/gep/external_candidates.jsonl`
**Filter:** only assets where `a2a.source == "traj-{project}"`
**Output:** `evolved/{project}/` ECC skill folders

### CLI

```bash
python3 traj-evolver-v2/scripts/build_ecc_skills.py \
  --evolver-dir   evolver \
  --project       wzp \
  --project-name  "wzp-脑力大冒险" \
  --output-dir    evolved/wzp
```

### Output Rules

**Gene → `skills/<gene_id>/SKILL.md`**

```markdown
---
name: {gene_id}
description: {first strategy sentence}
trigger: when {signals_match joined with " or "}
domain: {category}
source: trajectory-import
project: {project}
---

# {human-readable gene title}

## When to use
When {signals_match conditions}.

## Action
{strategy steps as numbered list}
```

**High-confidence Capsule** (post-factor confidence ≥ 0.4) → `commands/<capsule_id>.md`

```markdown
---
name: {capsule_id}
intent: {intent}
confidence: {confidence}
source: trajectory-import
project: {project}
---

# {human-readable capsule title}

## Action
{strategy}
```

**Capsule cluster** (≥ 3 capsules with same `intent`) → `agents/<intent>-agent.md`

```markdown
---
name: {intent}-agent
intent: {intent}
capsule_count: {N}
source: trajectory-import
project: {project}
---

# {intent} Agent

Covers {N} behavioral patterns extracted from real sessions.

## Patterns
{bulleted list of capsule ids}
```

**README.md** in `evolved/{project}/`:

```markdown
# Evolved Skills — {project_name}

Generated: {timestamp}
Source: trajectory patterns via traj-evolver-v2 + evolver GEP

## Provenance
- Sessions analyzed: {from patterns.json stats}
- Genes ingested: {count}
- Capsules ingested: {count}
- ECC skills written: {count}
```

## config.yaml

```yaml
pipeline:
  evolver_dir: evolver                       # relative to project root
  a2a_node_id: traj-evolver-v2              # A2A_NODE_ID for a2a_ingest.js
  a2a_confidence_factor: 0.6               # applied to all ingested assets

miner:                                       # passed through to traj_miner.py
  min_frequency: 3
  top_k_per_family: 20
  distinctness_weight: 0.5
  min_sessions: 2
```

## Makefile Targets

```makefile
mine:      # Stage 1 — calls traj-evolver/scripts/traj_miner.py
format:    # Stage 2 — format_patterns.py
ingest:    # Stage 3 — a2a_ingest.js (genes then capsules)
distill:   # Stage 4 — build_ecc_skills.py
pipeline:  # all four, per PROJECT={wzp,zzj}
test:      # pytest traj-evolver-v2/tests/
clean:     # rm patterns/ formatted/ and reset evolved/ for this PROJECT
```

## Testing

### test_format_patterns.py (8 tests, TDD)

Uses the same `traj_a`/`traj_b`/`traj_c` fixtures from `traj-evolver/tests/conftest.py`. Import via `sys.path.insert(0, "../traj-evolver/tests")` in `traj-evolver-v2/tests/conftest.py` — do not copy the fixture definitions.

1. `test_tool_sequence_pattern_becomes_gene` — Gene type, category=workflow, signals_match contains keywords
2. `test_phase_transition_becomes_gene` — Gene category=workflow, signals_match has from-phase
3. `test_fingerprint_becomes_gene` — Gene category=platform, signals_match has tool fragments
4. `test_task_shape_becomes_capsule` — Capsule type, intent=workflow, confidence mapping
5. `test_correction_signal_becomes_capsule` — Capsule intent=repair, confidence ≤ 0.45
6. `test_asset_id_computed` — every output object has non-empty `asset_id` field (16-char hex)
7. `test_a2a_fields_present` — every output has `a2a.status="external_candidate"`, `a2a.source="traj-wzp"`
8. `test_format_patterns_cli_end_to_end` — writes genes.jsonl + capsules.jsonl to tmp_path, both non-empty

### test_build_ecc.py (4 tests, TDD)

Uses in-memory fixture JSONL (no subprocess needed).

1. `test_gene_produces_skill_md` — Gene fixture → `skills/<id>/SKILL.md` with frontmatter
2. `test_high_conf_capsule_produces_command_md` — Capsule confidence ≥ 0.4 → `commands/<id>.md`
3. `test_low_conf_capsule_skipped` — Capsule confidence < 0.4 → no file written
4. `test_capsule_cluster_produces_agent_md` — 3 capsules same intent → `agents/<intent>-agent.md`

### End-to-end smoke test

Run Stages 1–4 against 3 real wzp files (same 3 as v1 smoke test). Assert:
- `formatted/wzp/genes.jsonl` and `capsules.jsonl` non-empty
- `evolver/assets/gep/external_candidates.jsonl` gains new entries with `a2a.source = "traj-wzp"`
- `evolved/wzp/` exists with at least 1 skill and a README

## Open Questions

None — all major decisions resolved during brainstorm.

## Next Step

Invoke `superpowers:writing-plans` to produce a detailed implementation plan.
