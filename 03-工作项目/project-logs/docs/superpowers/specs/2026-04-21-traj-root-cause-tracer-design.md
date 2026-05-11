# traj-root-cause-tracer — Design Spec

**Date:** 2026-04-21
**Status:** Approved (brainstorming complete, awaiting implementation plan)
**Owner:** traj-err-trace
**Predecessors:** `2026-04-20-traj-error-pattern-design.md` (this spec consumes its classified prompt JSONs)

---

## 1. Purpose

For each user prompt classified as `ai_output_correction` or `bug_report`, trace back through the trajectory to find the agent step that introduced the defect — and, where the defect was inherited from earlier sessions, the cross-session **genesis** step where the wrong code was first written.

Output is a stable JSON evidence chain per traced case, plus a confidence score derived from the agent's own subsequent fix. Downstream consumers:

1. **Per-case forensic case files** (HTML render like `viz/index.html`, one per high-confidence trace).
2. **Aggregated failure-mode catalog** — counts and exemplars per failure mode across all sessions.
3. **Future automated improvement loop** — feed of `(failure_mode, counter_pattern)` pairs for agent prompt/tool tuning.

## 2. Scope

### In scope
- v2 `.traj` files under `traj-data-new/{wzp,zzj}/`.
- Classified prompt JSONs under `examples/{wzp,zzj}/<session>.json` (produced by the existing `extraction/` pipeline).
- Tracing prompts where `is_correction_of_ai_work == true` OR `intent_primary == "bug_report"`.
- Two-tier trace per case: **proximate root** within the same session, plus **genesis root** cross-session when the proximate root only extends pre-existing wrong code.

### Out of scope
- Realtime tracing inside an active Claude Code session.
- Tracing `feature_modification`, `inquiry`, etc. (configurable later but not in v1).
- Auto-applying fixes or generating PRs.
- Defects that originated from non-AI code (i.e. code present before any AI session) — we will surface "no genesis found in trajectory corpus" as a terminal state, not search outside the corpus.

## 3. Trace model — two tiers

### 3.1 Proximate root (within-session)
For a correction at turn N in session S, the proximate root is the prior agent step in S that **introduced or extended** the broken state. Most cases stop here.

### 3.2 Genesis root (cross-session)
Run only when the proximate-root attribution declares the agent **inherited** pre-existing wrong code (e.g. extended an already-wrong field, edited an already-broken function). The tracer then searches the global step corpus for the **first** step (any session) that wrote the offending symbol. If the offending symbol exists in the corpus origin (i.e. earliest write is itself an extension of older state we can't see), output `"genesis": "outside_corpus"`.

## 4. Pipeline

Each traced case runs through 7 stages. Model assignment:

- `qwen-flash` (small, fast): stages **1, 3, 4, 6a, 7**
- `qwen-plus-latest` (thinking-disabled, heavy reasoning): stages **5, 6b**
- Deterministic (no LLM): stage **2**

```
correction prompt (turn N in session S)
        │
        ▼
[1] glossary    qwen-flash · build session-local glossary (cached per S)
[2] context     deterministic · load prior steps + last 3 user turns
        │
        ▼
[3] entities    qwen-flash · resolve complaint → {artifacts, symbols, surface}
[4] candidates  qwen-flash · score step summaries (batched 50/call) → top-K within S
        │
        ▼
[5] attribute   qwen-plus-latest · evidence chain + proximate root + failure mode
        │
        ├─ if attribute.genesis_check.needs_cross_session_trace ──┐
        │                                                         ▼
        │                                          [6a] qwen-flash · score global step summaries
        │                                          [6b] qwen-plus-latest · genesis confirm
        │                                                         │
        │◄────────────────────────────────────────────────────────┘
        ▼
[7] validate    qwen-flash · compare predicted_fix_target vs agent's actual post-correction fix
                            → confidence ∈ {high, medium, low}
        │
        ▼
   trace.json  (atomic write; existence = snapshot)
```

### Stage details

**Step filter — action-only.** Stage 4's step-summary cache and stage 5's candidate set EXCLUDE `respond_to_user` steps (they dominate (~40% of all steps in the corpus) and contain no code mutation). Code-touching tools kept: `mcp__mkr__Edit`, `mcp__mkr__Write`, `mcp__mkr__Read`, `Grep`, `Glob`, `mcp__mkr__Bash`, `mcp__sce-urhox__build`, `Task`. `TodoWrite` kept as weak signal but de-prioritised. The thinking content from `respond_to_user` is folded into the *next* action step's context as `prior_thought`.

**[1] Glossary build (qwen-flash, ~1 call per session, cached).**
Input: list of all file paths the agent read/wrote during S, plus any `title` / `name` / `levelId` / `nodeId` / dialogue speaker fields that appear in observations.
Output: JSON list of typed glossary entries (per-entry `kind` is required so stage 3 can disambiguate, e.g. an NPC name vs. a level title that contains that NPC's name):
```json
[
  {"name":"冰火花园",   "kind":"level",      "canonical":"scripts/config/storyline-levels/story-27.lua", "evidence":"observed_names"},
  {"name":"糖糖",       "kind":"npc",        "canonical":"characters/rabbit",                            "evidence":"observed_names"},
  {"name":"火火",       "kind":"npc",        "canonical":"characters/protagonist",                        "evidence":"observed_names"},
  {"name":"debug 按钮", "kind":"ui_element", "canonical":"scripts/ui/debug-button.lua",                  "evidence":"file_paths_touched"},
  {"name":"主线关卡总览","kind":"document",   "canonical":"docs/主线关卡总览.md",                          "evidence":"file_paths_touched"}
]
```
`kind` ∈ {`level`, `npc`, `ui_element`, `document`, `system`, `feature`, `unknown`}. Two in-context examples included in the prompt (one level/NPC-heavy session, one UI-heavy session) so qwen-flash converges on the schema. Cached at `extraction/cache/<dataset>/<project>/glossary/<session>.json`. Built lazily on first use.

**[2] Context load (deterministic).**
Read all steps in S that occur strictly before turn N. Read user turns N-3..N for anaphora resolution. Trim oversized observation text to first 2 KB.

**[3] Entity resolution (qwen-flash).**
Input: complaint text, glossary, user turns N-3..N.
Output:
```json
{
  "artifacts": ["scripts/config/storyline-levels/story-27.lua", "scripts/games/p3-match-3/board.lua"],
  "symbols":   ["frozenCells", "icePositions", "ice_block_render"],
  "surface":   "in-game runtime",
  "user_intent_restated": "ice obstacles declared in story-27 are not appearing in the running game"
}
```
The `symbols` field may include both **observed** identifiers (from glossary) and **plausible** identifiers (LLM hypothesis) — both are useful as retrieval keys.

**[4] Candidate retrieval (qwen-flash, batched).**
A **step summary cache** is pre-built once per session at `extraction/cache/step-summary/<project>/<session>.jsonl`, one line per step:
```json
{ "step":112, "tool":"Edit", "file":"story-27.lua", "summary":"append 4 entries to frozenCells field" }
```
Generated by qwen-flash from the raw step JSON (one batch call per session, cached).

For retrieval: send batches of 50 step summaries + the resolved entities to qwen-flash, ask "score 0–3 how likely each step is the introducer". Keep `score >= 2`, hard-cap top-8 candidates.

**[5] Attribution (qwen-plus-latest).**
Input: complaint, entities, top-8 candidate steps with **full** action+observation content.
Output: the evidence chain JSON (schema in §5).
Model is asked to commit to one `proximate_root` step, write the chain, classify failure mode from the v1 taxonomy (§6), produce a counter-pattern, and decide whether genesis check is needed.

**[6] Genesis trace (conditional, qwen-flash + qwen-plus-latest).**
Triggered when `genesis_check.needs_cross_session_trace == true`.

A **global step summary corpus** at `extraction/cache/step-summary/global/<project>.jsonl` is pre-built across all sessions in a project. Filter by mention of the offending file or symbol (cheap string match). Send filtered summaries (sorted by timestamp) to qwen-flash for relevance scoring. Take earliest-timestamp candidate with `score >= 2`. Confirm with qwen-plus-latest by sending complaint + proximate root + candidate step content.

If no candidates exist or none score ≥ 2: emit `"genesis": "outside_corpus"`.

**[7] Validation (qwen-flash, deterministic comparison).**
Scan steps after turn N in session S. Identify the agent's diagnostic + fix steps (Edit / Write actions following the user's correction).

Send (predicted_fix_target, actual_fix_target_list) to qwen-flash with the question: "did the predicted target match what the agent actually fixed?" Output:
- `high` — predicted file AND symbol both present in actual fix targets
- `medium` — predicted file present but symbol absent (or vice versa)
- `low` — neither matches; flag for human review

If no fix steps exist (the user's correction never got addressed): `"confidence": "unverified"`.

## 5. Output schema

One file per trace at `traces/<project>/<session>__turn-<N>.json`:

```json
{
  "trace_id": "wzp__6b8566ea__turn-12",
  "project": "wzp",
  "session_id": "6b8566ea",
  "turn_id": 12,
  "complaint": {
    "raw": "糖糖的冰火花园关卡，游戏内没有看到冰块",
    "intent_primary": "bug_report",
    "is_correction_of_ai_work": true
  },
  "entities": { /* §4 stage 3 */ },
  "evidence_chain": [
    { "id": "complaint",  "kind": "user_observation", "ref": { "session":"6b8566ea","turn":12 } },
    { "id": "symptom",    "kind": "claim", "text": "ice obstacles not rendering at runtime" },
    { "id": "broken_state","kind": "claim",
      "text": "story-27.lua declares ice obstacles under field `frozenCells` but board.lua reads `icePositions`",
      "evidence": [ { "session":"6b8566ea","step":110,"why":"Read shows frozenCells field" } ]
    },
    { "id": "introducing","kind": "agent_step",
      "ref": { "session":"6b8566ea","step":112 },
      "why": "first step in S that mutated obstacle config; appended to frozenCells without verifying consumer field name"
    },
    { "id": "missing_check","kind": "absence",
      "text": "no Read/Grep step in S touched board.lua or 'icePositions' before step 112"
    }
  ],
  "proximate_root": {
    "session":"6b8566ea","step":112,
    "file":"scripts/config/storyline-levels/story-27.lua",
    "symbol":"frozenCells"
  },
  "genesis_root": {
    "session":"<earlier>", "step": 47,
    "file": "scripts/config/storyline-levels/story-27.lua",
    "symbol":"frozenCells",
    "note":"first session that introduced the wrong field name"
  },
  "failure_mode": "verification_gap_via_lexical_familiarity",
  "counter_pattern": "Before mutating an existing config field, locate at least one reader of that exact name in consumer code (e.g. grep <field> in scripts/games/).",
  "predicted_fix_target": { "file":"story-27.lua", "symbol":"frozenCells→icePositions" },
  "validation": {
    "actual_fix_targets": [
      { "session":"6b8566ea","step":134,"file":"story-27.lua","symbol_diff":"frozenCells → icePositions" }
    ],
    "confidence":"high"
  },
  "model": { "thinking":"qwen-plus-latest", "small":"qwen-flash" },
  "extracted_at": "2026-04-21T..."
}
```

Atomic write via `<file>.tmp → rename`. File existence at the canonical path = snapshot (resume skips it).

## 6. Failure-mode taxonomy (v1)

Initial closed-vocabulary set. Stage 5 must pick exactly one. New modes are added by manual review of `low`-confidence traces, not invented by the LLM at runtime.

| key | description |
|---|---|
| `verification_gap_via_lexical_familiarity` | Treated an existing identifier as a contract; never read the consumer. (Canonical: frozenCells case.) |
| `hallucinated_symbol` | Wrote a call to an API/symbol that does not exist. |
| `inherited_broken_state` | Extended pre-existing wrong code without questioning it. |
| `silent_acceptor_fooled_by_build` | Treated a clean compile / typecheck as proof of behaviour. |
| `premature_completion` | Declared task done without runtime verification when verification was warranted. |
| `wrong_mental_model` | Operated on a fundamentally wrong understanding of the system. |
| `misread_spec` | Misinterpreted the user's instruction. |
| `ambiguous_spec_picked_wrong` | Spec was genuinely ambiguous; agent picked an interpretation the user didn't intend. |
| `racy_or_order_dependent` | Timing/order/state-ordering defect. |
| `regression_from_unrelated_edit` | Broke X while changing Y; no awareness of coupling. |
| `incomplete_refactor` | Renamed/moved partially; left stragglers. |
| `other` | Use only when none above fit; trace is then queued for taxonomy review. |

## 7. Storage layout

Concrete defaults below — all paths overridable via the CLI flags in §13.

```
traj-err-trace/
├── extraction/
│   ├── prompts.py, extract.py, run.sh           # existing
│   └── cache/                                   # NEW (see §11/§13 for full path schema)
│       └── <dataset>/<project>/
│           ├── glossary/<session>.json
│           └── step-summary/
│               ├── <session>.jsonl
│               └── _global.jsonl                # cross-session corpus
├── tracing/                                     # NEW
│   ├── prompts.py                               # all stage prompts (1, 3, 4, 5, 6, 7)
│   ├── pipeline.py                              # 7-stage orchestrator
│   ├── trace.py                                 # CLI entry (argparse — see §13)
│   ├── render.py                                # optional case-file HTML renderer
│   ├── run.sh                                   # nohup launcher (passes flags through)
│   └── logs/                                    # see §14 for streams
│       ├── trace-<ts>.log, latest.log
│       ├── events-<ts>.jsonl
│       └── failures/<trace_id>.json
└── traces/                                      # NEW — output
    └── <dataset>/<project>/
        ├── <session>__turn-<N>.json             # published traces
        └── _review/<session>__turn-<N>.json     # low-confidence quarantine
```

## 8. Concurrency, cost, runtime

- Same model: DashScope OpenAI-compatible endpoint, `extra_body={"enable_thinking": False}` for both models.
- `asyncio.Semaphore(3)` global cap, matching the existing extractor convention.
- Per case: 4–6 LLM calls (mostly flash). Across ~85 expected cases (13% trigger rate × ~660 prompts): 350–500 calls total. Estimated minutes-scale runtime.
- Per-session caches (glossary, step-summary) are built lazily on first need and reused across all traces in that session — amortised cheaply.

## 9. Edge cases & decisions

| Case | Handling |
|---|---|
| Correction prompt has no clear entities | Stage 3 returns empty `artifacts`/`symbols`. Pipeline emits `"trace": "abandoned", "reason": "no_entities"`. Skipped without error. |
| No prior agent steps in session (correction is the first user turn) | Pipeline emits `"trace": "abandoned", "reason": "no_prior_steps"`. |
| LLM at stage 5 returns a step ID not in the candidate set | Reject and re-prompt once, flagging the constraint. If second attempt also drifts, set `confidence: low` and record raw LLM output for audit. |
| Multiple correction prompts in one session reference the same defect | Each is traced independently. Aggregator (future work) can deduplicate by `(file, symbol)` of proximate_root. |
| Agent never fixes the bug after the user complaint | `validation.confidence = "unverified"`. Still emit the trace; downstream can decide whether to use it. |
| Cross-project genesis (wzp defect originating in zzj or vice versa) | Out of scope. Genesis search is per-project. |
| Same-session duplicate retries | Snapshot check is by canonical output path; duplicate runs no-op. |

## 10. Validation as a first-class signal

The validator (stage 7) is not just a post-hoc score — it gates **publication**:

- `high` → trace is published as-is.
- `medium` → trace is published with a visible warning banner in the rendered case file; aggregator counts but does not promote to "exemplar".
- `low` → trace is written under `traces/<project>/_review/` instead of the main directory; not picked up by aggregator.
- `unverified` → trace published with neutral note.

Aggregate accuracy is computed nightly: `% of traces with confidence ∈ {high, medium}`. Track in `traces/_metrics.json`.

## 11. Context construction — per-stage detail

The single biggest correctness risk in this system is feeding the LLM either too little (forces it to guess) or too much (drowns the signal and invites hallucination). This section pins down exactly what each LLM call sees, where each field is sourced from in the raw `.traj` data, the token budget, and the hallucination defenses.

Source paths are relative to the repo root unless noted. Token estimates assume `~4 chars/token` for mixed CJK + English.

### 11.0 Cross-stage invariants (self-review distillation)

These principles were extracted from a critical pass over the canonical 6b8566ea/turn-12 case. Every stage MUST satisfy them.

1. **Surface negative evidence, not just positive.** "What the agent did NOT do" is half the diagnosis. Verification-gap failures are invisible to the LLM unless we explicitly tell it which checks were absent. → enforced in §11.4 step-summary schema (`introduces_symbols`/`removes_symbols`) and §11.5 attribution prompt (`negative_findings` block).
2. **Preserve agent reasoning even when the action step is filtered.** `respond_to_user` is dropped from candidate sets, but its `thought`/`thinking` text is the smoking gun. → folded as `prior_thought` into the next action step at both summary and full-content levels.
3. **Use upstream classifier signal.** `target_artifact`, `summary_zh`, `intent_primary`, `is_correction_of_ai_work` already paid for. → injected into stages 3 and 5 with explicit role labels.
4. **Give the LLM permission to say "not sure."** Stages 3, 5 expose an `insufficient_evidence` escape that triggers retrieval expansion + one retry instead of forcing a wrong answer.
5. **Slot, don't free-form.** All structured outputs use named slots (not arrays of free-form objects) so downstream aggregation works.
6. **Anchor every numeric scale.** No score has meaning without per-value definitions in the prompt.
7. **Never assume edit semantics.** Symbol introduction/removal is parsed deterministically from `old_string`/`new_string`, not inferred. Validation inspects BOTH sides of the diff.

### 11.1 Stage 1 — Glossary build (qwen-flash)

**Goal.** Build a map of natural-language names → canonical file/symbol identifiers, scoped to one session. Cached at `extraction/cache/<dataset>/<project>/glossary/<session>.json` and reused by every trace in S.

**Inputs (constructed deterministically from `traj-data-new/<project>/<session>.traj`):**

| field | source path in .traj | shape | dedup |
|---|---|---|---|
| `file_paths_touched` | `messages[].steps[].action.args.file_path` for tools in {Edit, Write, Read} | sorted unique list | yes |
| `grep_patterns_seen` | `messages[].steps[].action.args.pattern` for tool=Grep | sorted unique list | yes |
| `observed_names` | regex extract `title = "..."`, `name = "..."`, `levelId = "..."`, `nodeId = "..."` from `messages[].steps[].observation.text` | sorted unique list | yes |
| `session_meta` | `session_metadata.{project, project_name, started_at}` | object | — |

**Token budget.** ~1.5 KB input, ~1 KB output. Cap `file_paths_touched` at 200; cap `observed_names` at 100 by frequency.

**Hallucination risks + mitigations:**

| risk | mitigation |
|---|---|
| LLM invents a name that isn't in `observed_names` | Prompt instructs: "every output key must appear verbatim in `observed_names` OR `grep_patterns_seen`." Reject + retry once if violated. |
| LLM maps a name to a file that wasn't touched | Prompt instructs: "every output value must be a path from `file_paths_touched` OR a sub-symbol thereof." Validator scans output post-hoc. |

### 11.2 Stage 2 — Context load (deterministic, no LLM)

Loads the bundle that stages 3–5 will consume. No LLM call. Output is an in-memory object:

| field | source | notes |
|---|---|---|
| `complaint` | classified prompts JSON: `examples/<project>/<session>.json → prompts[k]` where `k` matches turn N | includes `raw`, `index`, `classification` (intent + is_correction_of_ai_work + summary_zh) |
| `complaint_turn_id` | `messages[]` indexed by `turn_id == N` | int |
| `prior_user_turns` | last 3 `messages[]` with `role=user` and `turn_id < N`, ordered chronologically | for anaphora ("还是不对", "这个问题") |
| `prior_steps` | flat list of `messages[].steps[]` from agent runs with `turn_id <= N`, action-only filter (see §4 step filter), sorted by `step_id` ascending | typically 30–500 entries |
| `posterior_steps` | same but `turn_id > N`, capped at 30 (the agent's diagnosis + fix window) | for stage 7 validation |

### 11.3 Stage 3 — Entity resolution (qwen-flash)

**Goal.** Turn the complaint's natural language into the artifacts/symbols/surface the trace will search for.

**Constructed input (single chat message, sections explicitly labelled — the LLM is told what each block IS so it doesn't conflate the classifier's `summary_zh` with the user's actual words):**

```
<COMPLAINT — verbatim user text at turn {N}>
{complaint.raw}

<PRIOR USER TURNS (N-3..N-1) — for anaphora resolution only; NOT to be answered>
[turn N-3] ...
[turn N-2] ...
[turn N-1] ...

<AGENT'S LAST RESPONSE TO USER — the turn the user is reacting to>
{from messages[]: last respond_to_user step in agent run for turn N-1, with thought + final answer}

<UPSTREAM CLASSIFIER OUTPUT — independent prior labelling of this complaint, treat as HINT not ground truth>
intent_primary: bug_report | ai_output_correction
is_correction_of_ai_work: true|false
target_artifact: game_logic | ui_layout | visual_style | audio | narrative | documentation | build_config | tooling | asset_resource | unknown
summary_zh: <classifier's 1-line restatement; NOT verbatim user text>

<SESSION GLOSSARY (from stage 1)>
{glossary JSON list}

<TASK>
Resolve the complaint into the artifacts/symbols/surface the trace will search for.
You may propose hypothesis symbols (names not in glossary) — these are useful for cross-contract discovery (e.g. proposing `icePositions` even when only `frozenCells` is in evidence). Mark them as hypothesis.
If you cannot identify any plausible artifact from the complaint + prior turns + agent's last response, return `insufficient_evidence: true` instead of guessing. The pipeline will retry with an expanded user-turn window.
```

**Token budget.** Glossary capped at ~1 KB; total input ≤ 3 KB. Output ≤ 500 tokens.

**Output schema (strict JSON, all keys required):**

```json
{
  "artifacts": [
    {"path":"scripts/config/storyline-levels/story-27.lua","source":"glossary","confidence":"high"},
    {"path":"scripts/games/p3-match-3/board.lua",          "source":"hypothesis","confidence":"medium"}
  ],
  "symbols": [
    {"name":"frozenCells",  "source":"observed",  "confidence":"high"},
    {"name":"icePositions", "source":"hypothesis","confidence":"medium"},
    {"name":"ice_block_render","source":"hypothesis","confidence":"low"}
  ],
  "surface":   "in-game runtime" | "build" | "documentation" | "ui" | "unknown",
  "user_intent_restated": "ice obstacles declared in story-27 are not appearing in the running game",
  "insufficient_evidence": false
}
```

`source ∈ {glossary, observed, hypothesis}` lets stage 4 weight retrieval (glossary/observed entries get higher candidate scoring weight than hypotheses).

**Hallucination risks + mitigations:**

| risk | mitigation |
|---|---|
| LLM invents file paths not in glossary or actually-touched set | Validator: every entry in `artifacts` must be either in glossary values OR a path that appears in `prior_steps[].action.args.file_path`. Drop violators silently and log. |
| LLM invents symbol names plausible-looking but not present in any prior observation/edit | Symbols are kept as **hypotheses** (we *want* the model to propose `icePositions` even though only `frozenCells` is in current evidence — this is what allows cross-contract discovery). They are filtered later by stage 4 retrieval evidence. |
| Empty / vague complaint ("没生效") | If `confidence == "low"` AND `artifacts == []`, abort the trace with `reason: "no_entities_resolved"`. |

### 11.4 Stage 4 — Candidate retrieval (qwen-flash, batched)

**Step-summary cache.** Built once per session at `extraction/cache/<dataset>/<project>/step-summary/<session>.jsonl`. One line per action-only step. Symbol-level fields are parsed **deterministically** (regex over identifier-shaped tokens in `old_string`/`new_string`); only the natural-language `summary` is generated by qwen-flash:

```json
{
  "step":112,
  "turn":9,
  "tool":"Edit",
  "file":"scripts/config/storyline-levels/story-27.lua",
  "summary":"appended 4 entries to frozenCells field of story-27 level config",
  "introduces_symbols":[],
  "removes_symbols":[],
  "preserves_symbols":["frozenCells"],
  "prior_thought":"当前有 3 个冰冻格 {4,4},{2,6},{6,6}，无石块。需要新增 4 个冰冻格。",
  "obs_excerpt":"+++ story-27.lua @@ frozenCells +4 lines, build_status=ok",
  "timestamp":"2026-04-03T09:57:04Z"
}
```

`introduces_symbols` = identifier tokens present in `new_string` but NOT `old_string`. `removes_symbols` = the inverse. `preserves_symbols` = present in both (extension/mutation, not introduction). For `Write` actions (no `old_string`), all identifier tokens are `introduces_symbols` and `preserves_symbols=[]`. This is what lets §11.6 detect "agent is extending pre-existing wrong code."

`prior_thought` is the `thought` (and `thinking` if present) from the immediately-preceding `respond_to_user` step, folded in. Without this, the FAULT step (e.g. step 111 in 6b8566ea where the agent reasoned "需要新增 4 个冰冻格") becomes invisible to attribution.

Generated by qwen-flash from the raw step JSON in batches of 50 for the natural-language `summary` field; deterministic for the rest. Each summary entry ≤ 400 chars (~100 tokens). Median session = 83 action-only steps × 100 tokens ≈ 8 KB cache.

**Retrieval call.** Send entities + batches of 50 step summaries, ask flash to score each step 0–3 for likelihood of being the introducer. Batch protocol:

```
<ENTITIES from stage 3>
artifacts: [...]
symbols: [...]
surface: ...
user_intent_restated: ...

<STEP SUMMARIES — batch m of M>
[step=108] Grep   pattern="冰火花园"
[step=110] Read   story-27.lua  → 38 lines
[step=112] Edit   story-27.lua  · field=frozenCells · +4 entries
[step=116] Edit   主线关卡总览.md · "冰冻格 3→7"
[step=117] build  exit=0  · 0 errors
... (50 per batch)

<TASK>
Score each step on this anchored 0..3 scale:
  0 — irrelevant: does not touch the artifacts/symbols in entities
  1 — adjacent: touches a related file or area but not the specific artifact/symbol
  2 — touches: reads/edits the artifact in question or a sibling artifact
  3 — likely introducer: mutates the specific symbol implicated, OR introduces a symbol the user complaint refers to, OR is the latest pre-complaint Edit/Write to the named artifact
Higher-confidence sources from <ENTITIES> (source=glossary/observed) outweigh source=hypothesis when both could match.
Be selective: typically ≤ 20% of steps in a batch should score ≥ 2.
Output JSON only: [{"step":108,"score":0,"reason":"grep, no mutation"},{"step":110,"score":2,"reason":"read of named artifact"},{"step":112,"score":3,"reason":"edit mutates frozenCells in story-27"},...]
```

Aggregate across batches; keep `score >= 2`; hard-cap top-8 by score (ties broken by recency, latest first). Each candidate's `reason` is preserved into stage 5 input for traceability.

If after aggregation NO step scores ≥ 2 in any batch: loosen threshold to ≥1 for one retry; if still empty, abort with `reason: "no_candidates"`.

**Token budget.** For p90 session of 487 action-only steps ≈ 10 batches × ~4 KB each = ~40 KB total flash spend per case. ~$0.001 per case at flash pricing.

**Hallucination risks + mitigations:**

| risk | mitigation |
|---|---|
| LLM fabricates a step ID not in the batch | Validator drops any step ID not present in the batch's input. |
| All steps score 0 (no candidates) | Loosen threshold to `>= 1` for one retry; if still empty, abort with `reason: "no_candidates"`. |
| Score inflation (everything gets 3) | If >50% of steps in a batch score ≥2, re-prompt with explicit "be selective; ≤20% of steps should score ≥2." |

### 11.5 Stage 5 — Attribution (qwen-plus-latest)

This is the only "thinking" call. Everything before it is preparation; everything after is verification.

**Constructed input.** Six explicitly labelled blocks. The LLM is told exactly what each block IS and is NOT, to prevent confusion between user voice / agent voice / classifier voice / system voice.

```
<COMPLAINT — verbatim user text at turn {N}>
{complaint.raw}

<UPSTREAM CLASSIFIER OUTPUT — independent prior labelling, treat as HINT not ground truth>
intent_primary: {bug_report | ai_output_correction}
is_correction_of_ai_work: {bool}
target_artifact: {enum}
summary_zh: {classifier's restatement}

<PROJECT META>
project: {wzp | zzj | …}
project_name: {脑力大冒险 | 超时空要塞 | …}
runtime: lua  (relevant for failure-mode reasoning — Lua silently accepts unknown table keys)

<RESOLVED ENTITIES (stage 3 output)>
artifacts: [{path,source,confidence}, …]
symbols:   [{name,source,confidence}, …]
surface: …
user_intent_restated: …

<CANDIDATE STEPS (top-{K}, ordered by step_id ASC) — these are the ONLY steps you may cite>
─── step 110 ─── (turn 9 · tool=Read · score=2 · reason="read of named artifact")
prior_thought: (none)
action.args.file_path: scripts/config/storyline-levels/story-27.lua
observation (1141 chars):
  return { ... frozenCells = { {4,4}, {2,6}, {6,6} }, ...

─── step 111 ─── (turn 9 · tool=respond_to_user · KEPT because thought is implicated)
thought: 当前有 3 个冰冻格 {4,4},{2,6},{6,6}，无石块。需要新增 4 个冰冻格。
(no action; included for reasoning context only — cannot be proximate_root)

─── step 112 ─── (turn 9 · tool=Edit · score=3 · reason="mutates frozenCells in story-27")
prior_thought: (none)
introduces_symbols: []
removes_symbols: []
preserves_symbols: ["frozenCells"]
action.args.file_path: scripts/config/storyline-levels/story-27.lua
action.args.old_string: "    frozenCells = {\n        { 4, 4 }, { 2, 6 }, { 6, 6 },\n    },"
action.args.new_string: "    frozenCells = {\n        { 4, 4 }, { 2, 6 }, { 6, 6 },\n        { 3, 2 }, { 7, 2 }, { 5, 8 }, { 8, 5 },\n    },"
observation (551 chars):
  +++ story-27.lua @@ -15,8 +15,9 @@ ...

… (up to 8 candidate action steps; respond_to_user steps included only when their thought is implicated by entities)

<NEGATIVE FINDINGS — facts about what was NOT done in S before the complaint>
no_step_read: ["scripts/games/p3-match-3/board.lua"]   # consumer of the field
no_step_grepped: ["icePositions", "ice_block"]
no_step_searched_for_field_consumers: true
no_step_executed_runtime_test: true                    # only build, never play
(constructed deterministically by checking whether any prior_step matches each pattern)

<FAILURE-MODE TAXONOMY — closed vocabulary, pick exactly one>
{key}: {one-line definition}  e.g.:
verification_gap_via_lexical_familiarity: agent extends an existing identifier without verifying the consumer reads that exact name (e.g. extends frozenCells without checking board.lua reads icePositions)
hallucinated_symbol: agent calls an API/function/key that does not exist in the codebase
inherited_broken_state: agent extends pre-existing wrong code without questioning it
silent_acceptor_fooled_by_build: agent treats green build/typecheck as proof of behaviour in a runtime that silently accepts wrong inputs (Lua tables, JS objects, env vars)
premature_completion: agent declares done without runtime verification when the task required it
wrong_mental_model: agent operates on a fundamentally wrong understanding of the system
misread_spec: agent misinterprets the user's instruction
ambiguous_spec_picked_wrong: spec was ambiguous; agent picked an interpretation the user didn't intend
racy_or_order_dependent: timing/order/state-ordering defect
regression_from_unrelated_edit: broke X while changing Y; no awareness of coupling
incomplete_refactor: renamed/moved partially; left stragglers
other: none of the above; trace queued for taxonomy review

<TASK>
Produce the evidence chain JSON. Use ONLY the named slots below — do NOT emit free-form chain entries.

Constraints (HARD):
  1. proximate_root.{session,step} MUST be a candidate step ID above with tool ≠ respond_to_user.
  2. Every evidence_chain.*.ref.step MUST be a candidate step ID above.
  3. failure_mode MUST be one of the taxonomy keys above.
  4. predicted_fix_target[].file MUST appear in <RESOLVED ENTITIES.artifacts> OR in some candidate step's action.args.file_path.
  5. counter_pattern: ≤ 200 chars, MUST start with an imperative verb (e.g. "Before mutating…", "Verify that…", "Read the consumer…").
  6. evidence_chain has at most 5 named slots; OMIT slots that don't apply rather than padding with weak claims.

If candidates do not contain a step that plausibly introduced the defect, set `attribution_confidence: "candidates_insufficient"` and the pipeline will retry with K=16. Do NOT pick the highest-scoring candidate just to fill the slot.

Return ONLY this JSON shape:
{
  "evidence_chain": {
    "complaint":     {ref: {turn: N},                         text: "..."},
    "symptom":       {                                        text: "...what observable behavior is wrong"},
    "broken_state":  {refs: [{step: ...}, ...],               text: "...what the code currently does wrong"},
    "introducing":   {ref:  {step: ...},                      text: "...what this step did + why it caused the symptom"},
    "missing_check": {                                        text: "...derived from <NEGATIVE FINDINGS>; the verification absence that allowed the defect"}
  },
  "proximate_root": {session: "...", step: ..., file: "...", symbol: "..."},
  "genesis_check":  {needs_cross_session_trace: bool, reason: "..."},
  "failure_mode":   "<one taxonomy key>",
  "counter_pattern":"<verb-led, ≤200 chars>",
  "predicted_fix_target": [{file: "...", symbol: "..."}],
  "attribution_confidence": "high" | "medium" | "low" | "candidates_insufficient"
}
```

**Token budget.** Empirical: for the 6b8566ea/turn-12 case, 11 nearby steps total ~1.1 K tokens of evidence; 8-candidate cap → ~3 KB of evidence + 1.5 KB of scaffolding + 1 KB taxonomy = ~5–6 KB input. Output ~1.5 KB JSON. Comfortably under 32 K context.

**Hallucination risks + mitigations:**

| risk | mitigation |
|---|---|
| LLM cites a step not in candidate set | Post-hoc validator rejects; one retry with explicit constraint reminder; if still violates, mark `confidence: low` and persist to `_review/`. |
| LLM picks a failure mode outside taxonomy | Same — reject + retry; second failure → coerce to `other` and tag `taxonomy_violation: true`. |
| LLM invents `predicted_fix_target.symbol` not seen anywhere | Symbol field is **allowed** to be a hypothesis (e.g., the model may correctly predict `frozenCells → icePositions` even if `icePositions` never appears in candidate steps — that's the whole point). Validator does NOT enforce on symbol; only on file. |
| LLM padding (long evidence chains with weak claims) | Schema constraint: `evidence_chain.length ≤ 6`. Enforce in prompt + reject if violated. |

### 11.6 Stage 6 — Genesis trace (cross-session, conditional)

**Pre-built global step-summary corpus.** `extraction/cache/<dataset>/<project>/step-summary/_global.jsonl`. Same shape as per-session summaries, prefixed with `session` field. Built once per project; rebuilt incrementally on `--rebuild-cache`.

**[6a] Filter + score (qwen-flash).** First a deterministic prefilter: keep only summaries whose `file` or `key_args` mentions the offending file or symbol from `proximate_root`. This is grep-grade filtering, not retrieval — purely to bound the LLM payload.

Then sort filtered summaries by `timestamp ASC` (earliest first) and score with qwen-flash, asking specifically: "is this step the FIRST appearance of the wrong identifier?"

**[6b] Confirm (qwen-plus-latest).** Send the earliest high-scoring candidate's full step content + the proximate root + the complaint to qwen-plus. Ask: "is this the genesis, or is it itself an extension of even earlier wrong code (in which case mark `outside_corpus`)?"

**Hallucination risks + mitigations:**

| risk | mitigation |
|---|---|
| LLM picks a recent step instead of the earliest candidate | Prompt constraint: "the genesis MUST be the earliest-timestamp candidate unless you can name a strictly-earlier one in the input." Validator enforces timestamp monotonicity. |
| LLM declares genesis when proximate_root was actually the genesis | Deterministic precheck before stage 6 runs: derive the `pre_state` of `proximate_root.file` by finding the earliest Read of that file in S (or in the `_global` corpus if S never read it). If the offending symbol IS present in `pre_state` — gate opens, stage 6 runs. If `pre_state` is empty (file didn't exist before S) OR symbol is absent from `pre_state` — proximate_root IS the genesis; stage 6 skipped, output `genesis: null` with `note: "originated_in_proximate_session"`. For Write actions on previously-non-existent files, `pre_state = null` ⇒ gate stays closed. |
| Project corpus has no earlier writes of the symbol | Emit `genesis: "outside_corpus"` and persist; do not call qwen-plus. |

### 11.7 Stage 7 — Validation (qwen-flash + deterministic)

Mostly deterministic; flash only for ambiguity.

**Inputs:** `predicted_fix_target` (from stage 5) + `posterior_steps` (from stage 2) filtered to Edit/Write actions.

**Deterministic comparison first.** Aggregate ALL posterior Edit/Write steps into a single `actual_fix_set`:
- `actual_files = union of file_path across posterior Edit/Write`
- `actual_symbols_changed = union of identifier-shaped tokens that appear in EITHER old_string OR new_string but not both` (this captures rename diffs like `frozenCells → icePositions`, where the predicted symbol may live on the removed side)

For each entry in `predicted_fix_target` (a list — fixes can span files):
- `file_match` = predicted file ∈ `actual_files`
- `symbol_match` = predicted symbol parts (split on `→` for renames) ∩ `actual_symbols_changed` non-empty

Aggregate to a single confidence using the strongest predicted_fix_target match:
- ANY predicted target has both file+symbol match → `high`. No LLM call.
- ANY predicted target has file match only → `medium`. No LLM call.
- No predicted target has file or symbol match BUT posterior Edit/Write exists → call qwen-flash with `(predicted_fix_targets, actual_fix_set)` and the original complaint, ask "did the agent's actual fix address the same root cause as predicted?" — yes → `medium`, no → `low`.
- No posterior Edit/Write within 30 steps → `unverified`.

**No hallucination risk in the deterministic path.** The flash escape hatch is bounded: it can only flip `low` → `medium`, never to `high`.

## 12. Hallucination defense — cross-cutting

| defense | applies to | mechanism |
|---|---|---|
| Closed-vocabulary failure modes | Stage 5 | Reject + retry on out-of-vocab; coerce to `other` + flag on second failure |
| Step-ID grounding | Stages 4, 5 | Every step ID in LLM output must exist in the input candidate/batch set |
| File-path grounding | Stages 3, 5 | Files must come from glossary/touched-files set |
| Evidence-chain length cap | Stage 5 | `≤6 nodes` enforced in prompt; rejected on violation |
| One-retry policy | All LLM stages | Soft constraint violation → 1 retry with explicit "you violated constraint X" reminder; second violation → degrade gracefully (mark low confidence, route to `_review/`) |
| Validator publication gate (§10) | End of pipeline | `low`-confidence traces never enter the published corpus |
| Self-consistency NOT used | All stages | Explicitly out of scope: too expensive, and the validator gate is the better signal |

## 13. Dataset extensibility

`wzp` and `zzj` are the v1 datasets but the system MUST support arbitrary additional projects without code changes.

**CLI shape (matching the existing `extraction/extract.py` style):**

```
tracing/trace.py
  --dataset-root    PATH    default: traj-data-new
  --classified-root PATH    default: examples
  --output-root     PATH    default: traces
  --cache-root      PATH    default: extraction/cache
  --projects        LIST    comma-separated; default: discover all dirs under --dataset-root
  --only            LIST    optional: trace only specific session ids (file stems)
  --concurrency     INT     default: 3   (matches DASHSCOPE rate budget)
  --thinking-model  STR     default: qwen-plus-latest
  --small-model     STR     default: qwen-flash
  --rebuild-cache           flag: ignore existing glossary/step-summary caches
  --dry-run                 flag: load + plan + cost estimate, no LLM calls
  --log-level       STR     default: INFO
```

**Path conventions** become dataset-aware:

```
{cache-root}/{dataset_name}/{project}/glossary/{session}.json
{cache-root}/{dataset_name}/{project}/step-summary/{session}.jsonl
{cache-root}/{dataset_name}/{project}/step-summary/_global.jsonl
{output-root}/{dataset_name}/{project}/{session}__turn-{N}.json
{output-root}/{dataset_name}/{project}/_review/{session}__turn-{N}.json   # low-confidence
```

`{dataset_name}` is the basename of `--dataset-root` (e.g. `traj-data-new`). This means swapping in a new dataset is a one-flag change and never collides with existing outputs.

`run.sh` accepts and passes through all flags so nohup launches stay parameterised.

## 14. Logging

Three independent log streams, all under `tracing/logs/`:

**14.1 Run log** — `tracing/logs/trace-{ts}.log` (with `latest.log` symlink). Mirrors `extraction/run.sh`. One line per stage transition per case, plain text.

**14.2 Structured trace events** — `tracing/logs/events-{ts}.jsonl`. One JSON line per stage call. Each event:

```json
{
  "ts": "2026-04-21T...",
  "trace_id": "wzp__6b8566ea__turn-12",
  "stage": 5,
  "model": "qwen-plus-latest",
  "duration_ms": 4123,
  "input_tokens_est": 5800,
  "output_tokens_est": 1450,
  "outcome": "ok" | "retry" | "violation" | "error",
  "violation": null | "step_id_not_in_candidates" | "out_of_vocab_failure_mode" | ...,
  "extra": {}
}
```

This is the canonical signal for cost monitoring and quality regression detection. Append-only.

**14.3 Failure dumps** — `tracing/logs/failures/{trace_id}.json`. Written ONLY on hard failures (exception, validator gave up after retry). Contains: full constructed prompt, raw model response, validator decision, last-good intermediate state. For post-mortem; never read at runtime.

**Defaults.** Logging level controlled by `--log-level`. Stage events always emitted regardless of level (they're the metric stream, not chatter). Default tail-friendly format for the run log: `<ts> <level> <trace_id> <stage> <message>`.

## 15. Out of scope / future work

- **Realtime mode** — reuse the pipeline against an in-progress session; out of v1.
- **Cross-project genesis search.**
- **Failure-mode auto-discovery** — letting the LLM propose new failure modes from `low`-confidence traces, then human-review-promote into the taxonomy.
- **Aggregated dashboard** — separate spec, will consume `traces/` directory.
- **Auto-fix suggestion** — generate proposed code patches from `counter_pattern`. Not now.

## 16. Acceptance criteria for v1

1. `tracing/run.sh` processes all corrections + bug_reports across `wzp` + `zzj` end-to-end, writes one `trace.json` per case, atomically.
2. Snapshot resume works: re-running skips already-traced cases.
3. The canonical 6b8566ea/turn-12 case produces a trace that:
   - identifies step 112 as proximate root,
   - declares genesis check needed,
   - finds the genesis step in an earlier session (or `outside_corpus` if not found),
   - classifies failure mode as `verification_gap_via_lexical_familiarity`,
   - validates `high` against the agent's actual fix at step ~134.
4. `traces/_metrics.json` reports aggregate confidence distribution.
5. At least 80% of traces are published (i.e., not `low`-confidence).
