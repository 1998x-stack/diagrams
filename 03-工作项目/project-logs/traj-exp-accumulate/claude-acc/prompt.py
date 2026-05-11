"""
Build the prompt for gene generation via `claude -p`.

Usage:
    python3 prompt.py --session 9dc56f96 --project wzp
    # Prints the prompt to stdout; pipe to `claude -p`
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = Path(__file__).resolve().parent / "plugins"
SCHEMA_PATH = ROOT / "plugins" / "_schema.json"

INTENT_TAXONOMY = {
    "new_feature": "First-time request for a new capability, system, screen, or game mechanic that does not yet exist.",
    "feature_modification": "Tweak / adjust / extend an existing feature the user already accepted.",
    "bug_report": "User observed broken behavior in the running product; expects diagnosis + fix.",
    "ai_output_correction": "User is correcting the AI's most-recent or recent delivery.",
    "inquiry": "Question seeking information, status, or judgment. Does not request code change.",
    "inspection_review": "Ask the AI to inspect / audit / review existing code, docs, or designs.",
    "planning_design": "Request to design / draft / spec something before implementation.",
    "documentation": "Update, create, or refresh documentation specifically.",
    "content_creation": "Generate non-code assets — images, text/copy, audio specs, character bios, dialogue.",
    "refactor_redesign": "Re-architect or redo something already built (not a small tweak).",
    "error_log_paste": "User pastes raw error logs / crash reports / stack traces.",
    "configuration": "Change a config value, environment variable, build flag, or registry entry.",
    "meta_workflow": "Operational request not about the product itself — saving sessions, switching tools, summarizing progress.",
    "other": "Use only if none of the above clearly fits.",
}


def load_existing_index(plugins_dir: Path) -> str:
    """Load all existing index.md files as a single string for overlap detection."""
    parts = []
    for idx in sorted(plugins_dir.rglob("index.md")):
        rel = idx.relative_to(plugins_dir)
        content = idx.read_text(encoding="utf-8")
        parts.append(f"=== {rel} ===\n{content}")
    if not parts:
        return "(No existing genes yet — this is a fresh run.)"
    return "\n\n".join(parts)


def load_schema() -> str:
    if SCHEMA_PATH.exists():
        return SCHEMA_PATH.read_text(encoding="utf-8")
    return "(Schema not found — use the example gene format below.)"


def load_example_gene() -> str:
    """Load one example gene from the reference plugins/ for the LLM to follow."""
    ref_dir = ROOT / "plugins" / "feature_modification" / "genes.json"
    if ref_dir.exists():
        genes = json.loads(ref_dir.read_text(encoding="utf-8"))
        if genes:
            return json.dumps(genes[0], ensure_ascii=False, indent=2)
    return "(No example available.)"


def build_prompt(session: str, project: str) -> str:
    json_path = ROOT / "examples" / project / f"{session}.json"
    traj_path = ROOT.parent / "traj-data-new" / project / f"{session}.traj"
    existing_index = load_existing_index(PLUGINS_DIR)
    schema = load_schema()
    example_gene = load_example_gene()
    taxonomy_str = "\n".join(f'  - {k}: {v}' for k, v in INTENT_TAXONOMY.items())
    plugins_abs = str(PLUGINS_DIR)

    return f"""You are a trajectory analysis expert. Your task is to analyze a game-development AI agent session and extract reusable behavioral patterns ("genes") from it.

## GOAL
Analyze session `{session}` (project: `{project}`) and generate Gene objects organized by intent category. Write them to the plugins directory.

## INPUT FILES (use Read/Bash tools to access these)
1. **Intent classifications**: `{json_path}`
   - Contains classified user prompts with intent_primary, target_artifact, summaries
2. **Full trajectory**: `{traj_path}`
   - Contains the full agent trajectory (may be very large — use Bash with python/jq to extract summaries, don't try to read the whole file at once)

## ANALYSIS STEPS
1. Read the .json file to understand intent distribution and prompt sequences
2. Use Bash to extract per-turn summary from the .traj file:
   - Per turn: step count, tool distribution, phase, edit count, build count, error count
   - Session-level: total duration, total steps, tool frequency, phase distribution
3. Identify reusable behavioral patterns:
   - Consecutive same-intent sequences (e.g., 5+ visual tweaks in a row)
   - Workflow chains (e.g., design doc → implement → polish → doc checkpoint)
   - Failure patterns (repeated bug reports, escalation sequences)
   - Session rhythm (doc checkpoint cadence, phase boundaries)
   - Content creation workflows (generate → preview → apply)
4. Check existing genes (below) for overlaps
5. Generate new genes or enhance existing ones

## INTENT TAXONOMY
{taxonomy_str}

## GENE SCHEMA
{schema}

## EXAMPLE GENE
{example_gene}

## EXISTING GENES INDEX (for overlap detection)
{existing_index}

## OUTPUT INSTRUCTIONS — DEDUP-FIRST WORKFLOW

**BEFORE creating any new gene, you MUST check for similar existing genes using this exact workflow:**

### Step A: Grep for overlap
For each pattern you want to create a gene for, run:
```bash
grep -r "intent:{{category}}" {plugins_abs}/*/genes.json
grep -r "{{key_signal}}" {plugins_abs}/*/genes.json
```
where `{{key_signal}}` is the most distinctive signal tag (e.g., `consecutive_same_intent`, `sfx_name_in_prompt`, `stacktrace_in_prompt`).

### Step B: If grep finds a match — ENHANCE, don't create
1. Read the matching `{plugins_abs}/{{category}}/genes.json`
2. Find the specific gene object with overlapping signals
3. Use Edit to update ONLY the `_provenance` section:
   - Append `"{session}"` to `session_hashes` array
   - Append new turn/prompt references to `evidence`
   - Set or increment `session_count`
   - Update `turn_range` to include the new session's turns (format: `"prev_hash:T01-T03, {session}:T05-T08"`)
4. If the new session reveals additional signals or preconditions not in the existing gene, you MAY also add them to `signals_match` and `preconditions` — but do NOT remove existing ones.

### Step C: If grep finds no match — CREATE new gene
1. If `{plugins_abs}/{{category}}/genes.json` exists, Read it, then append your new gene to the JSON array.
2. If the file does not exist, create it as a JSON array containing your new gene: `[ {{gene}} ]`
3. Also create the category directory if needed: `mkdir -p {plugins_abs}/{{category}}`

### Step D: After all writes
Run: `python3 {ROOT}/gen_index.py --plugins-dir {plugins_abs}`

## GENE ID CONVENTION
- Format: `gene_{{intent_prefix}}_{{pattern_name}}`
- Intent prefixes: fm=feature_modification, nf=new_feature, br=bug_report, aoc=ai_output_correction, inq=inquiry, pd=planning_design, doc=documentation, cc=content_creation, cfg=configuration, mw=meta_workflow, elp=error_log_paste, meta=session_meta

## IMPORTANT RULES
- Every gene must have all required fields from the schema
- Preconditions and strategy should be in Chinese (matching the user's language)
- title_zh in Chinese, title_en in English
- _provenance must include session_hashes, turn_range, prompt_indices, and evidence
- Do NOT create genes for sessions with very few prompts (< 3) unless the pattern is highly distinctive
- Quality over quantity: 3-5 high-quality genes per session is better than 10 weak ones
- The plugins directory to write to is: `{plugins_abs}`

Now analyze the session and generate genes. Start by reading the .json file."""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    print(build_prompt(args.session, args.project))


if __name__ == "__main__":
    main()
