# traj-error-pattern — Design Spec

**Date:** 2026-04-20
**Status:** Approved (brainstorming complete, awaiting implementation plan)
**Owner:** Agent-eval team

## 1. Purpose

Discover, classify, and visualize error patterns produced by Claude Code agents in real production trajectories. Output is consumed by **two equally-weighted audiences**:

1. **Humans** (agent-eval researchers) — drill into per-trajectory errors, spot systemic patterns, decide where to invest agent / tool / prompt improvements.
2. **Automated agent-improvement loop** — stable JSON feed for tooling that derives training data, prompt patches, and tool-design changes.

This is industrial-production tooling, not a one-off analysis script. The JSON contract must be stable enough to integrate into Agent-eval pipelines.

## 2. Inputs & scope

- **Inputs:** v2 `.traj` files in `traj-data-new/wzp/` and `traj-data-new/zzj/`. Schema and structure documented in the existing repo's `CLAUDE.md` and `traj-data-new/swe-agent-traj-*.md`.
- **Unit of analysis:** a **turn** = one user message + the agent run that responds to it (matches v2 multi-turn grouping).
- **Error scope:** all three layers
  - Hard failures (exit codes, edit errors, LSP/tool errors)
  - Behavioral anti-patterns (redundant reads/writes, edit churn, write-without-read, search loops, missing verification)
  - LLM-judged subtle errors (intent mismatch, premature submission, lazy fixes, ignored corrections)
- **Out of scope (initial release):** real-time analysis, raw JSONL ingestion (we read the converted `.traj` only), authentication.

## 3. Architecture

Three top-level folders under `traj-error-pattern/`:

```
traj-error-pattern/
├── agent-error-process/   # Python analyzer (CLI-first, batch, writes JSON)
├── backend/               # FastAPI read-only server over the JSON
└── frontend/              # Vue 3 SPA dashboard + drill-down
```

**Boundary rule:** the analyzer is the only writer; the backend is read-only and consumes the analyzer's JSON output. The backend never imports analyzer source — it duplicates Pydantic models with a contract test that fails on schema drift.

### 3.1 Analyzer pipeline (`agent-error-process/`)

Two-stage pipeline (rule layer → LLM-judge layer) chosen because:
- Cheap rules and expensive LLM calls cache independently.
- The 2-level taxonomy maps cleanly onto the layers (mechanical = rules, semantic = LLM).
- Either layer can iterate without invalidating the other.

```
*.traj → loader.iter_turns
       → rules/* detectors → list[RuleSignal]
       → llm/judge.judge_turn(turn, rule_signals) → list[LlmFinding]
       → pipeline.merge → ErrorReport (per turn)
       → write data/per_turn/{project}/{session_hash}.json
       → aggregator.build_summary → data/aggregates/{project}.summary.json
```

**Modules:**

```
src/agent_error_process/
├── loader.py         # reads traj-data-new/{wzp,zzj}/*.traj
├── models.py         # Pydantic: Trajectory, Turn, ErrorReport, RuleSignal, LlmFinding
├── taxonomy.py       # 2-level enum + descriptions (single source of truth)
├── rules/
│   ├── tool_failure.py
│   ├── context_hygiene.py    # write-without-read, redundant reads/writes, stale_read
│   ├── edit_churn.py
│   ├── verification_gap.py
│   ├── lsp_error.py
│   └── user_correction.py
├── llm/
│   ├── judge.py      # qwen-plus client, enable_thinking=False
│   ├── prompts.py    # versioned prompt templates
│   └── cache.py      # SHA-256 content-hash cache
├── pipeline.py       # orchestrator
├── aggregator.py     # turn → run → session → project rollups
└── cli.py            # `agent-error-process analyze ...`
```

**Output layout:**

```
agent-error-process/data/
├── per_turn/{project}/{session_hash}.json   # one file per session, all turns inside
├── aggregates/{project}.summary.json
└── llm_cache/{sha256}.json
```

**Stand-alone:** does not import from `traj-viz`. Loader logic and Pydantic models are copied (minimal surface) to keep clean boundaries.

### 3.2 Backend (`backend/`)

FastAPI + Pydantic v2 + uvicorn. Mirrors the traj-viz pattern: scan-on-startup, in-memory index, mtime-based detail cache.

| Method | Path | Returns |
|---|---|---|
| GET | `/api/projects` | `[{name, session_count, turn_count, last_analyzed_at}]` |
| GET | `/api/aggregates/{project}` | full project summary JSON |
| GET | `/api/sessions?project=&category=&subtype=&severity=&min_findings=` | filtered session list |
| GET | `/api/sessions/{project}/{session_hash}` | per-turn report for one session |
| GET | `/api/findings?project=&subtype=&limit=` | flat finding list (table view) |
| GET | `/api/comparison?projects=wzp,zzj` | rates per 100 turns side-by-side |
| GET | `/healthz` | index status, file count, cache hit rate |

### 3.3 Frontend (`frontend/`)

Vue 3 + vue-router + TypeScript + Vite (matches traj-viz so engineers can move between them). Styling and component design built via the **`frontend-design:frontend-design`** skill at implementation time, not improvised.

**Routes:**
- `/` → DashboardView (project picker → aggregate charts)
- `/findings?subtype=...` → FindingsTable
- `/sessions/:project/:hash` → TurnDetailView (per-turn drill-down with inline error annotations)

**DashboardView:**
1. Project selector + summary tiles (sessions, turns, findings, high-severity count)
2. Category histogram (bar chart, clickable → findings table)
3. Severity heatmap (rows = subtype, cols = phase)
4. Project comparison panel (rates per 100 turns when ≥2 projects)
5. Top offending sessions table (clickable → TurnDetailView)
6. By-tool breakdown (which tools accumulate which categories — surfaces tool-design problems)

**TurnDetailView:**
- Header: user message excerpt, run summary, finding badges
- Step timeline (preserving traj-viz phase colors: blue=localization, violet=editing, green=verification, gold=submission)
- Each step rendered as `ErrorAnnotatedStep`: phase stripe, action + observation excerpt, finding overlay (subtype badge, severity color, evidence, hover → LLM root_cause_hypothesis)
- Right panel: full finding list for the turn, click → scroll to step

**Components:** `CategoryHistogram.vue`, `SeverityHeatmap.vue`, `ProjectComparison.vue`, `FindingsTable.vue`, `ErrorAnnotatedStep.vue`, `FindingBadge.vue`, `SubtypeFilter.vue`. Plus `useApi.ts` composable.

**Visual conventions:**
- Severity colors: high=red, med=amber, low=slate
- Source-of-finding distinction: rule = solid border, LLM = dashed border (so the user sees at a glance which findings are deterministic vs probabilistic)
- Phase colors preserved from traj-viz to keep the visual language consistent across tools

## 4. Error taxonomy (2-level)

Defined in `taxonomy.py` as the single source of truth. Categories 1–4 are mechanical (rule-detected). Categories 5–6 are semantic (LLM-judged).

| Category | Subtype | Detection | Signal |
|---|---|---|---|
| **1. tool_failure** | `tool_exit_nonzero` | rule | `observation.exit_code != 0` |
| | `edit_rejected` | rule | `observation.type == "edit_error"` |
| | `lsp_diagnostic` | rule | error_kind ∈ {syntax, type, name} from observation text |
| | `mcp_call_error` | rule | tool_name starts with `mcp__` AND status=error |
| **2. context_hygiene** | `write_without_read` | rule | Edit/Write to path not previously Read in same agent_run |
| | `redundant_read` | rule | Same path Read ≥3× in one agent_run |
| | `redundant_write` | rule | Same path Edit/Write ≥4× in one agent_run |
| | `stale_read` | rule | Read → many steps elapse → Edit without re-Read |
| **3. verification_gap** | `edit_without_verify` | rule | ≥4 consecutive edits with no test/lint/run step |
| | `submission_without_test` | rule | run_summary.result=submitted AND zero verification steps |
| | `ignored_test_failure` | rule | test_result exit_code=1 → next step is submission, not fix |
| **4. control_flow** | `search_loop` | rule | ≥3 grep/glob steps with no Read between them |
| | `tool_thrash` | rule | Same tool_name ≥6× consecutively in one run |
| | `phase_oscillation` | rule | edit→verify→edit→verify ≥3 cycles without convergence |
| **5. intent_alignment** *(LLM)* | `misread_intent` | LLM | Agent solved a different problem than user asked |
| | `partial_completion` | LLM | Submitted while parts of request remain unaddressed |
| | `over_scope` | LLM | Did extra work user didn't request (refactor/cleanup) |
| | `lazy_fix` | LLM | Patched symptom not root cause |
| **6. user_correction** *(LLM)* | `repeated_correction` | LLM | Same user complaint surfaces ≥2 turns |
| | `instruction_drift` | LLM | Agent abandons earlier user instruction within session |
| | `confused_response` | LLM | Agent asks user a question already answered above |

**Severity rule of thumb:** `high` = blocks task completion; `med` = wastes turns / extra cost; `low` = stylistic / efficiency.

## 5. Data contracts (durable JSON)

### Per-turn report

```json
{
  "turn_id": 3,
  "agent_run_id": "run_t3",
  "user_message_excerpt": "...",
  "step_count": 17,
  "tool_calls_count": 12,
  "findings": [
    {
      "finding_id": "wzp_<sha>_t3_f1",
      "category": "context_hygiene",
      "subtype": "write_without_read",
      "severity": "med",
      "source": "rule",
      "step_ids": [4, 7],
      "evidence": {
        "tool_name": "Edit",
        "path": "src/foo.lua",
        "observation_excerpt": "..."
      },
      "rule_id": "context_hygiene.write_without_read.v1"
    },
    {
      "finding_id": "wzp_<sha>_t3_f2",
      "category": "intent_alignment",
      "subtype": "lazy_fix",
      "severity": "high",
      "source": "llm",
      "step_ids": [12, 14],
      "confidence": 0.82,
      "root_cause_hypothesis": "Agent suppressed warning instead of fixing nil reference.",
      "evidence_text": "wrapped call in pcall without addressing why object was nil",
      "judge_prompt_version": "v1",
      "judge_model": "qwen3.6-plus"
    }
  ],
  "metrics": {
    "redundant_reads_max": 2,
    "redundant_writes_max": 1,
    "edits_without_verify_run": 0,
    "tool_failure_count": 1
  }
}
```

### Aggregate summary

```json
{
  "project": "wzp",
  "generated_at": "...",
  "schema_version": "1.0",
  "session_count": 42,
  "turn_count": 612,
  "totals_by_category": {"tool_failure": 88, "context_hygiene": 134},
  "totals_by_subtype": {"context_hygiene.write_without_read": 41},
  "severity_breakdown": {"high": 73, "med": 410, "low": 220},
  "by_tool": {"Edit": {"total": 240, "categories": {}}},
  "by_phase": {"editing": {}, "verification": {}},
  "top_offending_sessions": [{"session_hash": "...", "high_severity_count": 12}],
  "examples_per_subtype": {"context_hygiene.write_without_read": [{"session_hash":"...","turn_id":3,"finding_id":"..."}]}
}
```

## 6. LLM judge

- **Model:** `qwen3.6-plus` (per user spec; concrete Dashscope model ID to be confirmed against the live catalog at implementation time — fall back to `qwen-plus` if the requested ID is not available). `enable_thinking=False`.
- **Auth:** `DASHSCOPE_API_KEY` from environment.
- **Unit:** one call per turn. Input includes user message + compacted agent run + rule signals already detected for the turn.
- **Compaction rules:** strip base64; truncate observations >2KB to head + tail; keep tool args verbatim.
- **Token budget:** target 8k input / 1k output per turn. Hard cap configurable via `--max-llm-calls`.
- **Output schema:** strict JSON validated against `LlmFinding` Pydantic model. On parse failure, retry once with stricter prompt; on second failure, log + skip (no findings emitted) and surface in CLI report.
- **Prompt versioning:** `prompts.py` exposes `PROMPT_VERSION = "v1"`. Bumping the version invalidates the cache for the affected calls.

### LLM cache

- **Location:** `agent-error-process/data/llm_cache/<sha256>.json`
- **Key:** `sha256(turn_normalized_json + prompt_version + taxonomy_version + model_id)`
- **On hit:** read JSON, skip API call.
- **On miss:** call API → validate → write cache.
- **Refresh:** `--refresh-llm` flag bypasses cache for one CLI invocation.

## 7. CLI

```bash
agent-error-process analyze --project wzp                   # full batch
agent-error-process analyze --project wzp --no-llm          # rules only
agent-error-process analyze --project all --refresh-llm     # bypass cache
agent-error-process aggregate --project wzp                 # rebuild summary only
```

CLI is the only writer. Backend never triggers LLM calls. This keeps cost predictable and makes runs reproducible.

## 8. Testing

- **Analyzer:** unit tests per rule detector with crafted fixture turns; LLM judge tested with a mocked client; pipeline integration test with a small fixture `.traj`.
- **Backend:** pytest, fixture JSONs in `tests/fixtures/`. Contract test asserts backend Pydantic models match the per-turn / aggregate JSON shapes by validating real fixture files against both analyzer and backend models.
- **Frontend:** light component tests for the data-shape-sensitive components (`CategoryHistogram`, `ErrorAnnotatedStep`, `FindingBadge`); manual QA for full dashboard.

## 9. Out of scope (explicitly)

- Real-time / streaming analysis.
- Raw JSONL ingestion (consume converted `.traj` only).
- Authentication / multi-tenant access control.
- Direct integration into traj-viz (kept as a separate project).
- Auto-remediation suggestions (beyond `root_cause_hypothesis` text from the LLM).

## 10. Success criteria

1. Running `agent-error-process analyze --project all` produces complete `per_turn/` and `aggregates/` JSON for both wzp and zzj without manual intervention.
2. The aggregate JSON exposes — at minimum — counts per category, per subtype, per severity, per tool, per phase, and a list of top offending sessions.
3. The dashboard renders the histogram, heatmap, and project comparison; clicking through to a session lands on the TurnDetailView with findings annotated inline at the correct steps.
4. The LLM cache reduces re-run cost: a second `analyze --project wzp` with no taxonomy/prompt change makes zero Qwen calls.
5. All findings include enough evidence (`step_ids`, `evidence` / `evidence_text`) for a researcher to verify the call from the trajectory alone.
