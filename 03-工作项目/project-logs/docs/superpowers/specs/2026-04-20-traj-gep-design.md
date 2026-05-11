# Traj-GEP Design

**Date:** 2026-04-20
**Status:** Design — revised after first review (LLM integration)
**Position:** Independent parallel experiment alongside `traj-evolver-v2`

## Goal

Build a standalone Python+Node pipeline (`traj-gep/`) that mines `traj-data-new/{wzp,zzj}/*.traj` files into evolver-schema GEP **Genes** (with the 7 canonical fields `id / category / signals_match / preconditions / strategy / constraints / validation`). The output is a pair of independent `genes.json` files for offline review and side-by-side comparison with `traj-evolver-v2`'s output.

### Three pillars

1. **Signal vocabulary reuse** — call evolver's official `extractSignals()` from `evolver/src/gep/signals.js` via a thin Node wrapper. Vocabulary stays 100% aligned with evolver upstream.
2. **LLM augmentation in Stage 3 & 4** — `qwen3.6-plus` (Dashscope, `enable_thinking=False`, `temperature=0`) generates cluster summaries (Stage 3) and Gene `preconditions` / `strategy` text (Stage 4). Reproducibility is enforced via prompt-hash caching.
3. **Language bridge** — `signals.js` is English-regex-dominant; `.traj` user prompts are heavily Chinese. The LLM compensates: it reads original Chinese cluster evidence, emits Chinese-aware human-readable cluster summaries, and writes Gene strategy text that captures intent the English regex missed.

## Non-Goals

- Not a replacement for `traj-evolver-v2` — runs in parallel as a comparison baseline.
- Not modifying `evolver/` source (only reads `signals.js` as a library).
- Not generating Capsules — Gene only.
- Not invoking `a2a_ingest.js` — output stays as standalone files.
- Not using LLM in Stage 1 or Stage 2 — `signals.js` remains the sole signal-extraction logic (the language gap is bridged in Stage 3, not Stage 2).
- Not merging cross-project (wzp and zzj independent).
- Not continuous / live — batch only.

## Confirmed Constraints

| Item | Decision |
|---|---|
| Project relation | Completely independent parallel experiment |
| Granularity | 1 Gene = 1 cross-session recurring pattern |
| Data scope | wzp + zzj, independent outputs |
| Algorithm | Stage 1-2 rule-based + evolver `signals.js`; Stage 3-4 LLM-augmented (qwen3.6-plus) |
| Output location | `traj-gep/` (new dir at repo root) |
| Consumption | Standalone `genes.json` files; no a2a ingest |

## Architecture

### Directory Structure

```
project-logs/
├── traj-data-new/{wzp,zzj}/*.traj      # Input (v2 schema, existing)
├── evolver/                             # Library, not modified
│   ├── src/gep/signals.js               # require()'d by Stage 2 wrapper
│   └── assets/gep/genes.json            # Schema reference sample
└── traj-gep/                            # NEW
    ├── README.md
    ├── Makefile                         # mine / cluster / build / pipeline / test
    ├── config.yaml                      # Thresholds, paths, project map
    ├── requirements.txt                 # pyyaml, pytest
    ├── .gitignore                       # output/, __pycache__/
    ├── scripts/
    │   ├── load_trajectories.py         # Stage 1
    │   ├── extract_signals.js           # Stage 2 — Node wrapper
    │   ├── extract_signals.py           # Stage 2 — Python orchestrator
    │   ├── cluster_patterns.py          # Stage 3 (LLM-augmented)
    │   ├── build_genes.py               # Stage 4 (LLM-augmented)
    │   └── llm_client.py                # Shared Qwen client + prompt-hash cache
    ├── prompts/
    │   ├── cluster_summary.txt          # Stage 3 prompt template
    │   └── gene_strategy.txt            # Stage 4 prompt template
    ├── tests/
    │   ├── conftest.py
    │   ├── test_load_trajectories.py    # 8 tests
    │   ├── test_extract_signals.py      # 5 tests
    │   ├── test_cluster_patterns.py     # 11 tests (+2 LLM)
    │   ├── test_build_genes.py          # 12 tests (+2 LLM)
    │   ├── test_llm_client.py           # 5 tests
    │   └── test_smoke_e2e.py            # 1 test
    └── output/                          # gitignored
        ├── wzp/
        │   ├── {sessions,signals}.jsonl
        │   ├── {clusters,genes}.json
        │   └── llm_cache.jsonl          # Prompt-hash → response cache
        └── zzj/...
```

### Pipeline (per project, independent)

```
traj-data-new/{P}/*.traj
  ↓ Stage 1 — load_trajectories.py
output/{P}/sessions.jsonl     (one SessionRecord per line)
  ↓ Stage 2 — extract_signals.py (calls Node wrapper per session)
output/{P}/signals.jsonl      (adds signals[] to each session)
  ↓ Stage 3 — cluster_patterns.py
output/{P}/clusters.json      (recurring (signal, tool, phase) patterns)
  ↓ Stage 4 — build_genes.py
output/{P}/genes.json         (final Gene array)
```

Each stage writes to disk for resumability. wzp and zzj run as independent parallel pipelines.

## Stage 1 — Load Trajectories

**Input:** `traj-data-new/{project}/*.traj` (v2 schema)
**Output:** `output/{project}/sessions.jsonl`

### SessionRecord

```python
@dataclass
class SessionRecord:
    project: str                  # "wzp" / "zzj"
    session_hash: str             # 8-hex from filename
    user_corpus: str              # All user_message text concatenated with "\n---\n"
    error_corpus: str             # observation chunks where exit_code != 0 or text matches error regex
    tool_sequence: list[str]      # action.tool_name in temporal order, no dedup
    phase_sequence: list[str]     # phase tag per step, same length as tool_sequence
    correction_signals: list[str] # User correction phrases (max 20)
    file_targets: list[str]       # Edit/Write file_path, deduped
    n_steps: int                  # Agent step count
```

### Parsing rules

1. Walk every `.traj`, json.load, iterate `messages[]`.
2. **`user_corpus`**: concatenate all `type=="user_message"` `text` fields (v2 already filters system messages); separator `\n---\n`.
3. **`error_corpus`**: scan each step's `observation`; include first 800 chars when `exit_code` is non-null and non-zero, OR `text` matches `^Error|Traceback|Exception|TypeError|失败|错误|报错`.
4. **`tool_sequence`**: collect `step.action.tool_name` in order; skip `respond_to_user`; subagent steps recorded as `"@<subagent_type>"`.
5. **`phase_sequence`**: same length as tool_sequence, taken from each step's phase tag.
6. **`correction_signals`**: regex extract from `user_corpus`:
   ```
   r'(?i)\b(no|stop|wrong|undo|actually|nope|don\'?t|不对|别|停|撤销|不要|错了|有问题)\b[^.\n]{0,80}'
   ```
   Cap at 20 matches per session.
7. **`file_targets`**: from `Edit/Write` step `args.file_path`, deduped.

### CLI

```bash
python3 traj-gep/scripts/load_trajectories.py \
  --traj-dir ../traj-data-new/wzp \
  --project wzp \
  --output  output/wzp/sessions.jsonl
```

### Tradeoffs

- Don't parse thinking content (low signal value, high token cost).
- Subagents flattened to `"@<subagent_type>"` (preserve structural info, no recursion).
- Don't dedup tool_sequence (`Read,Read,Read` is a meaningful signal).

## Stage 2 — Signal Extraction

**Input:** `output/{project}/sessions.jsonl`
**Output:** `output/{project}/signals.jsonl`

### Node wrapper — `scripts/extract_signals.js`

```javascript
const path = require('path');
const { extractSignals } = require(
  path.resolve(__dirname, '../../evolver/src/gep/signals.js')
);

let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => { buf += c; });
process.stdin.on('end', () => {
  const input = JSON.parse(buf);
  const signals = extractSignals({
    userSnippet: input.userSnippet || '',
    todayLog: input.todayLog || '',
    recentSessionTranscript: input.recentSessionTranscript || '',
    memorySnippet: input.memorySnippet || '',
    recentEvents: [],
  });
  process.stdout.write(JSON.stringify({ signals }));
});
```

Input via stdin (corpus may exceed CLI arg limits).

### Python orchestrator — `scripts/extract_signals.py`

```python
def extract_signals_for_session(record: SessionRecord, wrapper_path: Path,
                                 max_user: int, max_err: int, timeout: int) -> list[str]:
    payload = json.dumps({
        "userSnippet": record.user_corpus[:max_user],
        "todayLog":    record.error_corpus[:max_err],
        "recentSessionTranscript": "",
        "memorySnippet": "",
    }, ensure_ascii=False)
    proc = subprocess.run(
        ["node", str(wrapper_path)],
        input=payload, capture_output=True, text=True, timeout=timeout, check=True,
    )
    return json.loads(proc.stdout)["signals"]
```

Maps the 4-channel corpus structure of `signals.js` deliberately:
- `userSnippet` ← `user_corpus` (intent signals like `user_feature_request`)
- `todayLog` ← `error_corpus` (error signals like `log_error`, `recurring_errsig`)
- `recentSessionTranscript`, `memorySnippet` ← `""` (no history concept in offline analysis)

### Output schema

```json
{
  "session_hash": "014354fc",
  "project": "wzp",
  "signals": ["log_error", "recurring_errsig:lua nil", "user_feature_request:add inventory UI"],
  "tool_sequence": ["Read","Edit","Bash","Read","Edit","Bash"],
  "phase_sequence": ["localization","editing","verification","localization","editing","verification"],
  "correction_signals": ["no don't add validation"],
  "file_targets": ["src/inventory.lua"],
  "n_steps": 6
}
```

### Failure handling

| Case | Handling |
|---|---|
| Node timeout (>15s) | warning to stderr; `signals=[]`; record still written |
| Node non-zero exit | same; stderr appended to `output/{P}/extract_errors.log` |
| `signals` field missing in stdout | empty array |
| `signals.js` path not found | fail-fast at startup; suggest `--evolver-dir` |

### Performance

Serial execution: 73 (wzp) + 168 (zzj) ≈ 241 sessions × ~150ms node cold-start ≈ 36s total. **No concurrency** — added complexity not justified for 36s.

### Smoke test target — `make verify-wrapper`

```bash
echo '{"userSnippet":"please add a button to the menu","todayLog":""}' \
  | node traj-gep/scripts/extract_signals.js
# Expect: signals contain user_feature_request*
```

## LLM Client (shared by Stage 3 & 4)

**Module:** `scripts/llm_client.py`
**Model:** `qwen3.6-plus` via Dashscope OpenAI-compatible endpoint.

### Configuration

```python
client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

resp = client.chat.completions.create(
    model="qwen3.6-plus",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ],
    temperature=0,
    seed=42,
    extra_body={"enable_thinking": False},
    response_format={"type": "json_object"},   # Stage 3 & 4 both expect JSON
)
```

`enable_thinking=False` is a Qwen3-family parameter; passed via `extra_body` (the OpenAI client does not know about it natively).

### Reproducibility — prompt-hash cache

```python
def call_llm(system: str, user: str, cache_path: Path) -> dict:
    key = hashlib.sha256(
        f"{MODEL}\n{system}\n---\n{user}".encode("utf-8")
    ).hexdigest()
    cached = lookup_cache(cache_path, key)
    if cached is not None:
        return cached
    resp = client.chat.completions.create(...)   # as above
    payload = json.loads(resp.choices[0].message.content)
    append_cache(cache_path, key, payload)
    return payload
```

- Cache file `output/{P}/llm_cache.jsonl` — one line per call: `{"key": "<sha256>", "model": "qwen3.6-plus", "payload": {...}}`.
- Cache key includes model name → bumping model invalidates cleanly.
- Same input always returns the same output (cache hit) regardless of API non-determinism.
- Cache is per-project (`{P}` in path), so wzp and zzj do not share cache pollution.

### Failure handling

| Case | Handling |
|---|---|
| `DASHSCOPE_API_KEY` not set | fail-fast at startup with clear error |
| HTTP error (429 / 5xx) | retry up to 3× with exponential backoff (1s, 4s, 16s) |
| JSON parse error | retry once with stricter system prompt; on second failure → return `{"_fallback": true, ...template defaults}` |
| Timeout (>60s per call) | log warning, fall back to template |

### Cost & runtime estimate

- Stage 3: ≤ 60 cluster calls per project × ~600 tokens each ≈ 36k tokens
- Stage 4: same 60 calls × ~800 tokens ≈ 48k tokens
- Per project total ~84k tokens. wzp+zzj together ~170k. With qwen3.6-plus pricing this is sub-dollar.
- First run ~5 min (network bound); cached re-runs ~10s.

### Tradeoffs

- **`temperature=0` + `seed=42` + cache** combine to make output reproducible enough to commit `llm_cache.jsonl` for review.
- **JSON response format** removes string-parsing fragility.
- **Cache committed to git for review purposes**: opt-in via `git add -f output/{P}/llm_cache.jsonl` (otherwise gitignored). Lets reviewers see what the LLM actually said without re-running.

## Stage 3 — Pattern Clustering

**Input:** `output/{project}/signals.jsonl`
**Output:** `output/{project}/clusters.json`

### Three cluster families

| Family | Key | Meaning | Gene category |
|---|---|---|---|
| **F1: signal × tool-bigram** | `(normalized_signal, tool_a, tool_b)` | "On signal X, use A→B sequence" | `repair / optimize / innovate` (by signal type) |
| **F2: tool-trigram** | `(tool_a, tool_b, tool_c)` | "Pure workflow A→B→C, signal-agnostic" | `workflow` |
| **F3: phase-transition × signal** | `(from_phase, to_phase, normalized_signal)` | "On signal X, transition from P1 to P2" | `workflow` |

### Algorithm (pseudocode)

```python
def cluster(sessions: list[SignalRecord], cfg) -> list[Cluster]:
    f1, f2, f3 = defaultdict(list), defaultdict(list), defaultdict(list)
    for s in sessions:
        norm_signals = {normalize(sig) for sig in s.signals}
        for sig in norm_signals:
            for a, b in bigrams(s.tool_sequence):
                f1[(sig, a, b)].append(s.session_hash)
        for a, b, c in trigrams(s.tool_sequence):
            f2[(a, b, c)].append(s.session_hash)
        for (p1, p2) in unique_phase_transitions(s.phase_sequence):
            for sig in norm_signals:
                f3[(p1, p2, sig)].append(s.session_hash)

    candidates = []
    for key, hashes in chain(f1.items(), f2.items(), f3.items()):
        sessions_count = len(set(hashes))
        frequency = len(hashes)
        if sessions_count < cfg.min_sessions: continue
        if frequency < cfg.min_frequency: continue
        if sessions_count / frequency < cfg.min_distinctness: continue
        candidates.append(Cluster(family=family_of(key), key=key,
                                  frequency=frequency, session_count=sessions_count,
                                  sessions=sorted(set(hashes))))
    candidates = take_top_k_per_family(candidates, cfg.top_k_per_family)
    return dedupe_overlapping(candidates, cfg.dedupe_jaccard)
```

### Thresholds (config.yaml)

| Param | Default | Purpose |
|---|---|---|
| `min_sessions` | 3 | Minimum distinct sessions for a recurring pattern |
| `min_frequency` | 5 | Minimum total occurrences (same session counts multiple times) |
| `min_distinctness` | 0.4 | `session_count / frequency` floor (rejects single-session repetition) |
| `top_k_per_family` | 30 | Keep top-K per family by `session_count` |
| `dedupe_jaccard` | 0.8 | Drop overlapping candidates with same signal |

### Signal normalization

```python
def normalize(sig: str) -> str:
    return sig.split(':', 1)[0]
```

`signals.js` produces `user_feature_request:add inventory UI`. Cluster key uses prefix; full strings preserved in `cluster.signal_details` for downstream `signals_match` filling.

### Dedupe (avoid Gene candidate cannibalism)

```python
def dedupe_overlapping(cands, threshold):
    cands.sort(key=lambda c: -c.session_count)
    kept = []
    for c in cands:
        if not any(jaccard(c.sessions, k.sessions) > threshold
                   and shares_signal(c.key, k.key) for k in kept):
            kept.append(c)
    return kept
```

### Category derivation

| Normalized signal | category |
|---|---|
| `log_error / recurring_errsig / errsig` | `repair` |
| `perf_bottleneck / capability_gap / unsupported_input_type` | `optimize` |
| `user_feature_request / user_improvement_suggestion / external_opportunity` | `innovate` |
| F2 (no signal dim) | `workflow` |
| F3 phase transitions | `workflow` |
| Other | `optimize` (fallback) |

### LLM augmentation step (Chinese-aware cluster summary)

After rule-based clusters are computed, each cluster goes through `llm_client.call_llm()` to produce a Chinese-aware summary that bridges the language gap left by `signals.js` (English-regex-dominant) vs `.traj` user prompts (heavily Chinese).

**Per-cluster LLM input** (assembled in Python, sent as JSON in the user message):

```json
{
  "family": "F1",
  "key": {"signal": "log_error", "tools": ["Read", "Edit"]},
  "session_count": 14,
  "frequency": 38,
  "signal_details": ["log_error", "recurring_errsig:lua nil"],
  "user_corpus_excerpts": [
    "脑力大冒险关卡跳转报错 nil...",
    "Edit 后又出现 lua 报错...",
    "..."
  ],
  "representative_files": ["src/menu.lua", "src/inventory.lua"],
  "correction_evidence": ["no actually undo that"]
}
```

`user_corpus_excerpts` = up to 5 random snippets (each ≤ 400 chars) drawn from the cluster's sessions' `user_corpus`, providing original-language context.

**Prompt template** (`prompts/cluster_summary.txt`):

```
你是 GEP 协议的模式分析师。给定一组复现轨迹模式的证据，输出严格 JSON：

{
  "title_zh": "<8-20 字中文标题，描述这个模式>",
  "title_en": "<8-15 word English title, mirroring zh>",
  "summary_zh": "<1-2 句中文摘要，说明何时该应用此模式>",
  "extra_signals": ["<至多 3 条原始 signals.js 未捕获的、源于中文 user prompt 的信号短语，用 ascii 短下划线词，例如 cn_level_jump_bug>"]
}

不要输出 JSON 以外内容。不要使用 markdown 代码块。
```

**LLM output merged into cluster object**:

```json
{
  "cluster_id": "f1_log_error_Read_Edit",
  "family": "F1",
  "category": "repair",
  "key": {"signal": "log_error", "tools": ["Read", "Edit"]},
  "session_count": 14,
  "frequency": 38,
  "sessions": ["014354fc", "019cf9e3", "..."],
  "signal_details": ["log_error", "recurring_errsig:lua nil"],
  "representative_files": ["src/menu.lua", "src/inventory.lua"],
  "correction_evidence": ["no actually undo that"],
  "llm": {
    "title_zh": "Lua 关卡跳转 nil 报错的读改循环",
    "title_en": "Read-edit loop for Lua level-jump nil errors",
    "summary_zh": "当 Lua 报 nil 错时，先 Read 现场再 Edit 修补，往往需要多轮才稳定。",
    "extra_signals": ["cn_level_jump_bug", "lua_nil_recurring"]
  }
}
```

`extra_signals` from LLM are recorded but **do not** retroactively change rule-based cluster keys — they feed Stage 4's `signals_match` field.

### Tradeoffs

- No ML clustering (k-means / embeddings) — interpretability and reproducibility prioritized.
- bigram + trigram chosen — bigram alone too short, 4-gram too sparse.
- No temporal weighting — all sessions equal weight ("project final experience" not "recent trend").
- F1 and F2 overlap allowed — different granularity, both useful.
- LLM only enriches metadata, never changes cluster membership — reproducibility of rule-based clustering preserved.
- `user_corpus_excerpts` random sample uses `random.Random(cluster_id)` — same cluster always picks same excerpts → cache stable.

## Stage 4 — Build Genes

**Input:** `output/{project}/clusters.json`
**Output:** `output/{project}/genes.json`

### Field filling rules — the 7 required fields

#### `type`
Fixed: `"Gene"` (schema requirement, not in user's 7-field list but evolver expects it).

#### `id`
```
gene_traj_<project>_<family>_<slug>
```
- `<family>` ∈ `{f1sig, f2flow, f3phase}`
- `<slug>` lowercase, alphanumeric+underscore, ≤ 40 chars
- Total ≤ 60 chars
- Collision: append `_2`, `_3`, ...
- Examples:
  - `gene_traj_wzp_f1sig_log_error_read_edit`
  - `gene_traj_wzp_f2flow_read_edit_bash`
  - `gene_traj_zzj_f3phase_localization_to_editing_log_error`

#### `category`
Per Stage 3 derivation table.

#### `signals_match`

**F1:**
```python
[normalize(cluster.key.signal)]              # primary signal
+ cluster.signal_details[:3]                 # up to 3 detailed signals
+ [tool.lower() for tool in cluster.key.tools]
```

**F2:**
```python
[tool.lower() for tool in cluster.key.tools]
+ ["workflow", f"phase:{dominant_phase}"]
```

**F3:**
```python
["phase_transition", f"from:{from_phase}", f"to:{to_phase}",
 normalize(cluster.key.signal)]
```

Dedupe, preserve order, cap at 8.

#### `signals_match` — extension

In addition to the rules above, append `cluster.llm.extra_signals` (up to 3 entries) to the array, then dedupe and cap at `max_signals_match` (default 8). This is the only way LLM-derived signals enter the Gene contract.

#### `preconditions` (LLM-generated)

`llm_client.call_llm()` is invoked with the cluster (including `cluster.llm` metadata from Stage 3) and the prompt template `prompts/gene_strategy.txt`. The LLM emits a strict JSON object with the `preconditions` and `strategy` arrays — see prompt below.

Templates remain as a **fallback** when the LLM call fails (returns `_fallback: true` per LLM client failure handling).

**F1 fallback template:**
```
[
  "signals contains '{signal}' indicator",
  "task involves {tool_a} followed by {tool_b}",
  "evidence: pattern observed in {session_count} sessions ({frequency} occurrences)"
]
```

**F2 fallback template:**
```
[
  "task is in {dominant_phase} phase",
  "{tool_a} → {tool_b} → {tool_c} sequence is appropriate",
  "no critical errors blocking baseline workflow"
]
```

**F3 fallback template:**
```
[
  "current phase is '{from_phase}'",
  "signals indicate transition trigger '{signal}'",
  "next phase '{to_phase}' has not yet started"
]
```

#### `strategy` (LLM-generated)

Same LLM call as `preconditions` — both fields produced in one round-trip per cluster.

**F1 fallback template:**
```
[
  "Detect '{signal}' signal in incoming task or recent log",
  "Apply {tool_a} → {tool_b} sequence as primary action path",
  "If {tool_a} reveals additional context, repeat before applying {tool_b}",
  "Record outcome via EvolutionEvent for selector feedback"
]
```

If `cluster.correction_evidence` non-empty, append:
```
"Watch for user corrections like {top_correction_phrase!r}; rollback {tool_b} if triggered"
```

**F2 fallback template:**
```
[
  "When entering {dominant_phase} phase, follow {a} → {b} → {c} as canonical flow",
  "Validate intermediate state after each tool before proceeding",
  "Do not skip {b} even if {a} appears successful"
]
```

**F3 fallback template:**
```
[
  "Recognize transition trigger from '{from_phase}' to '{to_phase}' on '{signal}'",
  "Complete pending {from_phase} actions before transitioning",
  "Initialize {to_phase} with the file targets from {from_phase}"
]
```

Cap at `max_strategy_steps` (default 6).

#### Gene-fields LLM prompt — `prompts/gene_strategy.txt`

```
你是 GEP 协议的 Gene 编写专家。基于聚类证据，写出该 Gene 的 preconditions 与 strategy。

约束：
- 输出严格 JSON，无 markdown，无注释。
- preconditions: 2-4 条，每条 ≤ 80 字，描述【何时该应用此 Gene】。
- strategy: 3-6 条命令式步骤，每条 ≤ 100 字，动词开头。
- 语言：preconditions / strategy 用中文（与 .traj 项目原文一致），便于人工 review。
- 必须引用聚类证据中的具体 tool 名（保持英文，如 Read/Edit/Bash）。
- 若 correction_evidence 非空，最后一条 strategy 必须涉及"监听用户撤销/纠正"。

输出 schema:
{
  "preconditions": ["...", "..."],
  "strategy":      ["...", "...", "..."]
}
```

LLM input includes the entire cluster object plus its `cluster.llm` metadata.

#### `constraints`
Fixed:
```json
{"max_files": 10, "forbidden_paths": [".git", "node_modules"]}
```

Trajectory-mined genes are behavioral guidance, not large-scale refactor; 10-file ceiling conservative.

#### `validation`
Fixed: `[]`

Trajectory data is read-only analysis output. There is no executable command to bind. Hard-coding `node scripts/validate-suite.js` would point to a non-existent script and selector would reject. Empty array is the honest representation.

Activating these genes inside evolver later would require a separate "validation harness" project — out of scope.

### `_provenance` (optional, default ON)

```json
{
  "_provenance": {
    "source": "traj-gep",
    "project": "wzp",
    "session_count": 14,
    "frequency": 38,
    "session_hashes_sample": ["014354fc", "019cf9e3", "0428882b"]
  }
}
```

Underscore prefix isolates from evolver-recognized fields. Configurable via `gene_builder.include_provenance`.

### Final output sample (LLM-augmented)

```json
[
  {
    "type": "Gene",
    "id": "gene_traj_wzp_f1sig_log_error_read_edit",
    "category": "repair",
    "title_zh": "Lua 关卡跳转 nil 报错的读改循环",
    "title_en": "Read-edit loop for Lua level-jump nil errors",
    "signals_match": [
      "log_error", "recurring_errsig:lua nil",
      "read", "edit",
      "cn_level_jump_bug", "lua_nil_recurring"
    ],
    "preconditions": [
      "task 中包含 Lua 报 nil 或类似运行时报错",
      "需要先 Read 现场再 Edit 修补的迭代场景",
      "证据：14 个 session 中复现 38 次"
    ],
    "strategy": [
      "在收到 log_error / lua nil 信号时，先 Read 报错位置周边代码",
      "若上下文不足，重复 Read 相邻文件直到掌握状态",
      "对最小可疑行 Edit 一次，避免大范围改动",
      "Edit 后立刻让用户/脚本验证；监听用户撤销或'no/undo/不对'的纠正"
    ],
    "constraints": {"max_files": 10, "forbidden_paths": [".git", "node_modules"]},
    "validation": [],
    "_provenance": {
      "source": "traj-gep",
      "model": "qwen3.6-plus",
      "project": "wzp",
      "session_count": 14, "frequency": 38,
      "session_hashes_sample": ["014354fc", "019cf9e3", "0428882b", "056c0fdf", "06335c24"]
    }
  }
]
```

`title_zh` / `title_en` are LLM-derived (Stage 3) and added at gene-build time as additional fields outside the canonical 7. evolver selector ignores unknown fields; they exist for human review.

### CLI

```bash
python3 traj-gep/scripts/build_genes.py \
  --clusters output/wzp/clusters.json \
  --project  wzp \
  --config   config.yaml \
  --output   output/wzp/genes.json
```

### Tradeoffs

- No LLM calls — preconditions/strategy fully templated. Lower fluency, higher reproducibility.
- `constraints` not personalized — avoids unjustified per-Gene tuning.
- `_provenance` underscore prefix — isolates from evolver schema validation.

## Configuration & CLI

### `config.yaml`

```yaml
paths:
  evolver_dir:    ../evolver
  traj_data_dir:  ../traj-data-new
  output_dir:     ./output

projects:
  - id: wzp
    name: "wzp-脑力大冒险"
  - id: zzj
    name: "zzj-超时空要塞"

extractor:
  node_bin: node
  timeout_seconds: 15
  user_corpus_max_chars:  50000
  error_corpus_max_chars: 30000

clustering:
  min_sessions:        3
  min_frequency:       5
  min_distinctness:    0.4
  top_k_per_family:    30
  dedupe_jaccard:      0.8

gene_builder:
  max_signals_match:   8
  max_strategy_steps:  6
  include_provenance:  true
  provenance_session_sample: 5

llm:
  model:               qwen3.6-plus
  base_url:            https://dashscope.aliyuncs.com/compatible-mode/v1
  api_key_env:         DASHSCOPE_API_KEY
  temperature:         0
  seed:                42
  enable_thinking:     false
  timeout_seconds:     60
  max_retries:         3
  retry_backoff_seconds: [1, 4, 16]
  cluster_excerpt_count: 5
  cluster_excerpt_max_chars: 400
```

### Makefile targets

```
verify-wrapper        Smoke test the Node bridge (run once at setup)
load                  Stage 1 (per PROJECT)
extract               Stage 2 (depends on load)
cluster               Stage 3 (depends on extract)
build                 Stage 4 (depends on cluster)
pipeline-wzp          Full pipeline for wzp
pipeline-zzj          Full pipeline for zzj
pipeline-all          Both
test                  pytest tests/
clean                 Remove output/<PROJECT>
```

### CLI conventions

- `--config <path>` — all scripts; defaults to `config.yaml`. Flags override config values.
- `--project <id>` — required. Rejects values outside `wzp/zzj`.
- `--output <path>` — required. Parent dirs auto-created.
- Exit codes: 0 success; 1 user error; 2 data error; 3 external process error.

### Dependencies

- Python ≥ 3.10
- Node ≥ 18 (matches evolver)
- Python packages: `pyyaml`, `pytest`, `openai` (≥ 1.0, used as Dashscope-compatible client). **No** pandas/sklearn/pydantic.
- Env: `DASHSCOPE_API_KEY` required for live LLM calls. Tests run without it via `monkeypatch`.

## Testing (TDD)

42 tests total across 6 files. Coverage target ≥ 80%.

### Shared fixtures — `tests/conftest.py`

- `tmp_traj_file` — builds minimal v2-schema .traj on demand
- `sample_user_msg`, `sample_step` — message/step factories
- `sample_session_record` — in-memory SessionRecord for downstream tests

### `tests/test_load_trajectories.py` (8 tests)

1. `test_loads_basic_traj`
2. `test_user_corpus_concatenates_with_separator`
3. `test_error_corpus_filters_by_exit_code`
4. `test_error_corpus_matches_error_keywords`
5. `test_tool_sequence_skips_respond_to_user`
6. `test_subagent_recorded_as_at_prefix`
7. `test_correction_signals_extract_chinese_and_english`
8. `test_cli_writes_jsonl`

### `tests/test_extract_signals.py` (5 tests)

1. `test_node_wrapper_executable` (the only test that actually spawns Node)
2. `test_user_feature_request_signal_detected`
3. `test_log_error_signal_detected`
4. `test_timeout_returns_empty_signals_with_warning`
5. `test_signals_jsonl_output_shape`

Tests 2-5 monkeypatch `extract_signals_for_session` to avoid 73 Node spawns.

### `tests/test_cluster_patterns.py` (11 tests)

1. `test_f1_signal_x_bigram_clusters`
2. `test_f2_trigram_clusters`
3. `test_f3_phase_transition_clusters`
4. `test_min_sessions_threshold_excludes`
5. `test_min_distinctness_excludes_concentrated`
6. `test_signal_normalize_strips_detail_suffix`
7. `test_dedupe_by_jaccard`
8. `test_top_k_per_family_caps_output`
9. `test_signal_details_preserved_for_field_filling`
10. `test_llm_summary_attached_to_each_cluster` (LLM mocked via monkeypatch returning fixed payload)
11. `test_llm_excerpt_sampling_is_deterministic_per_cluster_id`

### `tests/test_build_genes.py` (12 tests)

1. `test_required_seven_fields_present`
2. `test_id_format_and_length`
3. `test_category_derivation_log_error_to_repair`
4. `test_category_derivation_user_feature_request_to_innovate`
5. `test_signals_match_includes_tools_lowercase`
6. `test_signals_match_capped_at_8`
7. `test_signals_match_includes_llm_extra_signals`
8. `test_correction_evidence_appends_strategy_step` (fallback template path)
9. `test_validation_is_empty_array`
10. `test_provenance_emitted_when_enabled`
11. `test_llm_preconditions_and_strategy_used_when_present`
12. `test_template_fallback_when_llm_returns_fallback_marker`

### `tests/test_llm_client.py` (5 tests)

1. `test_cache_hit_avoids_api_call` (monkeypatch `client.chat.completions.create` to raise — pre-seeded cache returns)
2. `test_cache_key_includes_model` (different model → different key → cache miss)
3. `test_retry_on_429_then_success`
4. `test_returns_fallback_marker_after_max_retries`
5. `test_response_format_json_object_parsed`

### `tests/test_smoke_e2e.py` (1 test)

1. `test_full_pipeline_on_3_real_traj_files` — runs `make pipeline PROJECT=wzp` against 3 real wzp .traj files in tmp dir; asserts `genes.json` is valid JSON array (size unconstrained — 3 sessions may not reach `min_sessions=3` cluster).

### TDD order

```
test_load_trajectories.py   → load_trajectories.py
test_extract_signals.py     → extract_signals.{js,py}
test_llm_client.py          → llm_client.py            (NEW — needed before clusters & genes)
test_cluster_patterns.py    → cluster_patterns.py
test_build_genes.py         → build_genes.py
test_smoke_e2e.py           → end-to-end verification
```

### Test conventions

- All non-smoke tests ≤ 1s; smoke ≤ 60s.
- No network; no real `output/` writes (use `tmp_path`).
- `monkeypatch` isolates Node subprocess (CI does not need Node for unit tests).
- `monkeypatch` replaces `OpenAI` client; tests never touch Dashscope. The smoke test sets `DASHSCOPE_API_KEY`, but the cluster_summary / gene_strategy responses are **pre-seeded into `llm_cache.jsonl`** for the 3 sample sessions, so the smoke test never makes a live LLM call either.

## Comparison with traj-evolver-v2

After both pipelines complete, optionally implement `scripts/compare_with_v2.py` producing `output/comparison-{project}.md` with:

1. **Count comparison** — v2 Gene count vs traj-gep Gene count; v2 Capsule count (traj-gep N/A).
2. **Coverage comparison** — signal sets in v2 only, traj-gep only, intersection.
3. **Example comparison** — for `log_error`, list top-3 Gene from each side with strategy text.
4. **Granularity distribution** — v2 (fingerprint/phase) vs traj-gep (signal × bigram).
5. **Session overlap** — `_provenance.session_hashes` if both retain.

### Manual rubric (1-5 scale, filled in after experiments)

| Dimension | v2 | traj-gep | Notes |
|---|---|---|---|
| Signal accuracy | | | Real evolver vocab? |
| Strategy readability | | | Template vs LLM-augmented |
| Granularity appropriateness | | | Too fine / too coarse |
| Reproducibility | | | Same input → same output |
| Implementation complexity | | | LOC, deps, runtime |

### Out of scope

- LLM-as-judge comparison (we use LLM as field generator, not arbiter)
- Merging products into evolver store
- Performance benchmarks (both < 5 min including LLM)

### Language-bridge note

`evolver/src/gep/signals.js` regex coverage is mostly English (`error|exception|TypeError|...`) with a small Chinese set (`错误|异常|报错|失败`). Real `.traj` user prompts are heavily Chinese and contain domain terms (关卡, 角色, 道具, etc.) the regex never catches. Without LLM augmentation, traj-gep would underrepresent Chinese-only signal modes. The Stage 3 `extra_signals` field and the Chinese-language `preconditions/strategy` (Stage 4) are how this gap is closed without rewriting the upstream regex.

## Followup Comparison

(To be filled in after the experiment runs.)

## Open Questions

None — all major decisions resolved during brainstorm.

## Next Step

Invoke `superpowers:writing-plans` to produce a detailed implementation plan after user approves this spec.
