"""Convert Claude Code JSONL sessions to v2 .traj format.

Usage:
    python converter_v2.py --wzp-workspace <path> --zzj-workspace <path> --output-dir .
    python converter_v2.py --session <path.jsonl> --project <name> --output-dir .
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from phase_tagger import tag_phases_v2, detect_markers_v2


PROJECT_NAMES = {"wzp": "脑力大冒险", "zzj": "超时空要塞"}

SYSTEM_PREFIXES = [
    "This session is being continued",
    "<image-caption>",
    "[Image: original",
    "[Image: ",
    "[Request interrupted by user]",
    "Base directory for this skill:",
    "<system-reminder>",
    "<command-name>",
    "<local-command",
]


def is_system_message(text: str) -> bool:
    """Check if a user message is a system-injected message."""
    stripped = text.strip()
    return any(stripped.startswith(p) for p in SYSTEM_PREFIXES)


def extract_text_content(content: Any) -> Optional[str]:
    """Extract text from content (string or list of content blocks)."""
    if content is None:
        return None
    if isinstance(content, str):
        return content.strip() if content.strip() else None
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        combined = "".join(parts)
        return combined if combined else None
    return None


def extract_thinking_content(content: Any) -> Optional[str]:
    """Extract thinking blocks from assistant content. Ignores signature."""
    if content is None or isinstance(content, str):
        return None
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "thinking":
                parts.append(block.get("thinking", ""))
        combined = " ".join(p for p in parts if p)
        return combined if combined else None
    return None


def extract_tool_calls(content: Any) -> list[dict]:
    """Extract tool_use blocks from assistant content."""
    if content is None or isinstance(content, str):
        return []
    if isinstance(content, list):
        return [
            block for block in content
            if isinstance(block, dict) and block.get("type") == "tool_use"
        ]
    return []


def is_tool_result_content(content: Any) -> bool:
    """Check if user message content is a tool result."""
    if not isinstance(content, list):
        return False
    return any(
        isinstance(b, dict) and b.get("type") == "tool_result"
        for b in content
    )


def extract_tool_result_text(content: Any) -> str:
    """Extract text from tool_result content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif "content" in block:
                    parts.append(str(block["content"])[:500])
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(p for p in parts if p)
    return str(content)[:500] if content else ""


def _parse_ts(ts_str: str) -> Optional[datetime]:
    if not ts_str:
        return None
    ts_str = ts_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return None


def _delta_seconds(ts1: str, ts2: str) -> float:
    dt1 = _parse_ts(ts1)
    dt2 = _parse_ts(ts2)
    if dt1 and dt2:
        return abs((dt2 - dt1).total_seconds())
    return 0.0


def parse_jsonl(filepath: str) -> list[dict]:
    """Parse a JSONL file, keeping only user and assistant entries."""
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") in ("user", "assistant"):
                entries.append(entry)
    return entries


def build_messages(entries: list[dict]) -> list[dict]:
    """Convert raw JSONL entries into v2 messages structure.

    Returns a list of message dicts:
    - User messages: {"turn_id": N, "role": "user", "content": "...", "timestamp": "..."}
    - Agent runs: {"turn_id": N, "agent_run_id": "run_tN", "steps": [...], "run_summary": {...}}
    """
    if not entries:
        return []

    # Pre-scan: collect all tool results by tool_use_id
    tool_result_map: dict[str, str] = {}
    for entry in entries:
        if entry.get("type") == "user":
            content = entry.get("message", {}).get("content", "")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tid = block.get("tool_use_id", "")
                        result_text = extract_tool_result_text(block.get("content", ""))
                        if tid:
                            tool_result_map[tid] = result_text

    messages: list[dict] = []
    turn_id = 0
    step_counter = 0
    current_steps: list[dict] = []
    prev_ts = ""

    def _flush_run():
        """Flush accumulated steps into an agent_run message."""
        nonlocal current_steps
        if not current_steps and turn_id == 0:
            return
        if not current_steps:
            return
        tool_calls_in_run = sum(
            1 for s in current_steps if s["action"]["tool_name"] != "respond_to_user"
        )
        messages.append({
            "turn_id": turn_id,
            "agent_run_id": f"run_t{turn_id}",
            "steps": current_steps,
            "run_summary": {
                "steps_count": len(current_steps),
                "tool_calls_count": tool_calls_in_run,
            },
        })
        current_steps = []

    for entry in entries:
        msg_type = entry.get("type")
        content = entry.get("message", {}).get("content", "")
        timestamp = entry.get("timestamp", "")

        if msg_type == "user":
            # Skip tool result entries — they don't start new turns
            if is_tool_result_content(content):
                continue

            # Extract text
            text = extract_text_content(content)
            if not text:
                continue

            # Skip system messages
            if is_system_message(text):
                continue

            # Flush previous turn's run
            _flush_run()

            # New turn
            turn_id += 1
            messages.append({
                "turn_id": turn_id,
                "role": "user",
                "content": text,
                "timestamp": timestamp,
            })
            prev_ts = timestamp

        elif msg_type == "assistant":
            if turn_id == 0:
                # Assistant message before any user turn — skip
                continue

            thinking = extract_thinking_content(content)
            text = extract_text_content(content)
            tool_calls = extract_tool_calls(content)
            usage = entry.get("message", {}).get("usage", {})

            usage_dict = {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0),
            }

            if tool_calls:
                for tc in tool_calls:
                    step_counter += 1
                    tool_id = tc.get("id", "")
                    observation_text = tool_result_map.pop(tool_id, "")

                    exec_time = _delta_seconds(prev_ts, timestamp)

                    current_steps.append({
                        "step_id": step_counter,
                        "phase": "",  # Filled later by phase tagger
                        "thinking": thinking,
                        "thought": text,
                        "action": {
                            "tool_name": tc.get("name", "unknown"),
                            "tool_use_id": tool_id,
                            "args": tc.get("input", {}),
                        },
                        "observation": {
                            "type": "tool_result",
                            "text": observation_text[:2000],
                            "exit_code": None,
                        },
                        "state": None,
                        "status": "ok",
                        "timestamp": timestamp,
                        "execution_time": round(exec_time, 1),
                        "usage": usage_dict,
                    })
                    prev_ts = timestamp
                    # Only attach thinking to the first tool call in a batch
                    thinking = None

            elif text:
                step_counter += 1
                exec_time = _delta_seconds(prev_ts, timestamp)
                current_steps.append({
                    "step_id": step_counter,
                    "phase": "",
                    "thinking": thinking,
                    "thought": text,
                    "action": {
                        "tool_name": "respond_to_user",
                        "tool_use_id": "",
                        "args": {},
                    },
                    "observation": {
                        "type": "text",
                        "text": "",
                        "exit_code": None,
                    },
                    "state": None,
                    "status": "ok",
                    "timestamp": timestamp,
                    "execution_time": round(exec_time, 1),
                    "usage": usage_dict,
                })
                prev_ts = timestamp

    # Flush last turn's run
    _flush_run()

    return messages


def _collect_all_steps(messages: list[dict]) -> list[dict]:
    """Collect all steps from all agent runs in messages."""
    steps = []
    for m in messages:
        if "steps" in m:
            steps.extend(m["steps"])
    return steps


def _apply_phases(messages: list[dict], phases: list[dict]):
    """Write phase labels back into step dicts."""
    # Build step_id -> phase label mapping
    label_map: dict[int, str] = {}
    for phase in phases:
        for sid in range(phase["start_step"], phase["end_step"] + 1):
            label_map[sid] = phase["label"]

    for m in messages:
        if "steps" in m:
            for step in m["steps"]:
                step["phase"] = label_map.get(step["step_id"], "editing")


def convert_session_v2(jsonl_path: str, project: str) -> dict:
    """Convert a single JSONL session file to v2 .traj format."""
    session_id = Path(jsonl_path).stem

    entries = parse_jsonl(jsonl_path)
    if not entries:
        return _empty_traj(project, session_id)

    messages = build_messages(entries)
    all_steps = _collect_all_steps(messages)

    # Phase tagging
    if all_steps:
        phases = tag_phases_v2(all_steps)
        markers = detect_markers_v2(all_steps)
        _apply_phases(messages, phases)
    else:
        phases = []
        markers = []

    # Subagent processing
    subagents = []
    subagent_dir = Path(jsonl_path).parent / session_id / "subagents"
    if subagent_dir.is_dir():
        for agent_file in sorted(subagent_dir.glob("agent-*.jsonl")):
            agent_id = agent_file.stem[len("agent-"):]
            agent_entries = parse_jsonl(str(agent_file))
            if agent_entries:
                agent_messages = build_messages(agent_entries)
                subagents.append({
                    "agent_id": agent_id,
                    "messages": agent_messages,
                })

    # Metadata extraction
    timestamps = [e.get("timestamp", "") for e in entries if e.get("timestamp")]
    start_time = timestamps[0] if timestamps else ""
    end_time = timestamps[-1] if timestamps else ""
    duration = _delta_seconds(start_time, end_time)

    model = ""
    cwd = ""
    version = ""
    git_branch = ""
    for e in entries:
        if not model:
            m = e.get("message", {}).get("model")
            if m:
                model = m
        if not cwd and e.get("cwd"):
            cwd = e["cwd"]
        if not version and e.get("version"):
            version = e["version"]
        if not git_branch and e.get("gitBranch"):
            git_branch = e["gitBranch"]

    # Summary computation
    user_msgs = [m for m in messages if m.get("role") == "user"]
    total_turns = len(user_msgs)
    total_steps = len(all_steps)
    total_tool_calls = sum(
        1 for s in all_steps if s["action"]["tool_name"] != "respond_to_user"
    )
    total_input = sum(s["usage"]["input_tokens"] for s in all_steps)
    total_output = sum(s["usage"]["output_tokens"] for s in all_steps)
    total_cache_read = sum(s["usage"]["cache_read_tokens"] for s in all_steps)
    total_cache_create = sum(s["usage"]["cache_creation_tokens"] for s in all_steps)

    first_prompt = user_msgs[0]["content"] if user_msgs else ""
    phase_labels = list(dict.fromkeys(p["label"] for p in phases))

    return {
        "schema_version": "2.0",
        "conversation_id": session_id,
        "agent": {
            "name": "claude-code",
            "model": model,
            "environment": "taptap-maker",
            "tool_protocol": "claude_tool_use",
        },
        "session_metadata": {
            "project": project,
            "project_name": PROJECT_NAMES.get(project, project),
            "session_id": session_id,
            "started_at": start_time,
            "ended_at": end_time,
            "duration_sec": round(duration, 1),
            "cwd": cwd,
            "version": version,
            "git_branch": git_branch,
        },
        "messages": messages,
        "phases": phases,
        "markers": markers,
        "subagents": subagents,
        "summary": {
            "total_turns": total_turns,
            "total_steps": total_steps,
            "total_tool_calls": total_tool_calls,
            "total_subagents": len(subagents),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cache_read_tokens": total_cache_read,
            "total_cache_creation_tokens": total_cache_create,
            "exit_reason": "end_of_conversation",
            "status": "completed" if messages else "empty",
            "first_user_prompt": first_prompt[:500],
            "phase_labels": phase_labels,
            "marker_count": len(markers),
        },
    }


def _empty_traj(project: str, session_id: str) -> dict:
    return {
        "schema_version": "2.0",
        "conversation_id": session_id,
        "agent": {
            "name": "claude-code",
            "model": "",
            "environment": "taptap-maker",
            "tool_protocol": "claude_tool_use",
        },
        "session_metadata": {
            "project": project,
            "project_name": PROJECT_NAMES.get(project, project),
            "session_id": session_id,
            "started_at": "",
            "ended_at": "",
            "duration_sec": 0,
            "cwd": "",
            "version": "",
            "git_branch": "",
        },
        "messages": [],
        "phases": [],
        "markers": [],
        "subagents": [],
        "summary": {
            "total_turns": 0,
            "total_steps": 0,
            "total_tool_calls": 0,
            "total_subagents": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cache_read_tokens": 0,
            "total_cache_creation_tokens": 0,
            "exit_reason": "no_messages",
            "status": "empty",
            "first_user_prompt": "",
            "phase_labels": [],
            "marker_count": 0,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Convert Claude Code sessions to v2 .traj format")
    parser.add_argument("--wzp-workspace", help="Path to wzp workspace directory")
    parser.add_argument("--zzj-workspace", help="Path to zzj workspace directory")
    parser.add_argument("--session", help="Path to a single session JSONL file")
    parser.add_argument("--project", help="Project name (used with --session)")
    parser.add_argument("--output-dir", default=".", help="Output directory (default: .)")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    total_sessions = 0
    total_turns = 0
    total_tools = 0

    if args.session:
        if not args.project:
            print("Error: --project is required with --session")
            sys.exit(1)
        proj_dir = output_dir / args.project
        proj_dir.mkdir(parents=True, exist_ok=True)
        traj = convert_session_v2(args.session, args.project)
        session_hash = traj["session_metadata"]["session_id"][:8]
        out_path = proj_dir / f"{session_hash}.traj"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(traj, f, ensure_ascii=False, indent=2)
        print(f"  -> {out_path} ({traj['summary']['total_turns']} turns)")
        total_sessions = 1
        total_turns = traj["summary"]["total_turns"]
        total_tools = traj["summary"]["total_tool_calls"]
    else:
        workspaces = {}
        if args.wzp_workspace:
            workspaces["wzp"] = args.wzp_workspace
        if args.zzj_workspace:
            workspaces["zzj"] = args.zzj_workspace

        if not workspaces:
            print("Error: provide --wzp-workspace and/or --zzj-workspace, or --session")
            sys.exit(1)

        for project, ws_path in workspaces.items():
            proj_dir = output_dir / project
            proj_dir.mkdir(parents=True, exist_ok=True)
            ws = Path(ws_path)
            jsonl_files = sorted(ws.glob("*.jsonl"))
            print(f"\n[{project}] Converting {len(jsonl_files)} sessions...")

            for jsonl_file in jsonl_files:
                traj = convert_session_v2(str(jsonl_file), project)
                if traj["summary"]["status"] == "empty":
                    continue
                session_hash = traj["session_metadata"]["session_id"][:8]
                out_path = proj_dir / f"{session_hash}.traj"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(traj, f, ensure_ascii=False, indent=2)
                total_sessions += 1
                total_turns += traj["summary"]["total_turns"]
                total_tools += traj["summary"]["total_tool_calls"]
                marker_count = len(traj["markers"])
                phase_count = len(traj["phases"])
                print(f"  {session_hash} -> {traj['summary']['total_turns']} turns, {phase_count} phases, {marker_count} markers")

    print(f"\nDone: {total_sessions} sessions, {total_turns} turns, {total_tools} tool calls")


if __name__ == "__main__":
    main()
