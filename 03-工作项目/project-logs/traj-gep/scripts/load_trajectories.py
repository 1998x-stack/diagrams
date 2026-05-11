"""Stage 1 — load v2 .traj files into SessionRecord objects."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

ERROR_LINE_RE = re.compile(
    r"^\s*(Error|Traceback|Exception|TypeError|ReferenceError|SyntaxError|失败|错误|报错)",
    re.MULTILINE,
)
# Lookbehind alternation instead of \b: Python's \b is ASCII-only and
# treats CJK characters as non-word, so it false-positives on
# ASCII-to-Chinese transitions (e.g. "fix撤销" would match). The lookbehind
# anchors only at line start, whitespace, or punctuation — correctly
# rejecting matches embedded mid-word in ASCII-Chinese mixed text.
CORRECTION_RE = re.compile(
    r"(?i)(?:^|(?<=\s)|(?<=\W))(no|stop|wrong|undo|actually|nope|don'?t|不对|别|停|撤销|不要|错了|有问题)[^.\n]{0,80}",
    re.MULTILINE,
)
CORRECTION_MAX = 20
ERROR_OBS_MAX_CHARS = 800


@dataclass
class SessionRecord:
    project: str
    session_hash: str
    user_corpus: str
    error_corpus: str
    tool_sequence: list[str]
    phase_sequence: list[str]
    correction_signals: list[str]
    file_targets: list[str]
    n_steps: int


def _is_error_observation(obs: dict) -> bool:
    if obs is None:
        return False
    exit_code = obs.get("exit_code")
    if exit_code is not None and exit_code != 0:
        return True
    text = obs.get("text") or ""
    return bool(ERROR_LINE_RE.search(text))


def extract_correction_signals(text: str) -> list[str]:
    return [m.group(0).strip() for m in CORRECTION_RE.finditer(text)][:CORRECTION_MAX]


def _tool_name_for_step(step: dict) -> str | None:
    action = step.get("action") or {}
    tool = action.get("tool_name")
    if not tool or tool == "respond_to_user":
        return None
    if tool == "Agent":
        sub = (action.get("args") or {}).get("subagent_type")
        if sub:
            return f"@{sub}"
    return tool


def load_traj_file(path: Path, project: str) -> SessionRecord:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    # Prefer filename stem (8-hex) over UUID for short-hash compatibility with downstream code
    session_hash = Path(path).stem

    user_texts: list[str] = []
    error_chunks: list[str] = []
    tool_sequence: list[str] = []
    phase_sequence: list[str] = []
    file_targets: list[str] = []

    for msg in data.get("messages", []):
        if msg.get("role") == "user":
            t = msg.get("content") or ""
            if t:
                user_texts.append(t)
        elif "agent_run_id" in msg or "steps" in msg:
            for step in msg.get("steps", []) or []:
                tool = _tool_name_for_step(step)
                if tool is None:
                    continue
                tool_sequence.append(tool)
                phase_sequence.append(step.get("phase") or "")
                obs = step.get("observation") or {}
                if _is_error_observation(obs):
                    error_chunks.append((obs.get("text") or "")[:ERROR_OBS_MAX_CHARS])
                args = (step.get("action") or {}).get("args") or {}
                fp = args.get("file_path")
                if fp and tool in {"Edit", "Write"} and fp not in file_targets:
                    file_targets.append(fp)
        # else: unknown message shape — skip silently

    user_corpus = "\n---\n".join(user_texts)
    error_corpus = "\n---\n".join(error_chunks)
    correction_signals = extract_correction_signals(user_corpus)

    return SessionRecord(
        project=project,
        session_hash=session_hash,
        user_corpus=user_corpus,
        error_corpus=error_corpus,
        tool_sequence=tool_sequence,
        phase_sequence=phase_sequence,
        correction_signals=correction_signals,
        file_targets=file_targets,
        n_steps=len(tool_sequence),
    )


def iter_traj_files(traj_dir: Path) -> Iterable[Path]:
    return sorted(Path(traj_dir).glob("*.traj"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    # `--traj` is the canonical flag; `--traj-dir` retained as alias for back-compat.
    p.add_argument("--traj", "--traj-dir", dest="traj", required=True, type=Path)
    p.add_argument("--project", required=False, default=None,
                   help="If omitted, derived from basename(--traj).")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)

    if not args.traj.exists():
        print(f"--traj does not exist: {args.traj}", file=sys.stderr)
        return 1

    project = args.project or args.traj.resolve().name
    if not project:
        print("could not derive --project from --traj basename; pass --project explicitly",
              file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with args.output.open("w", encoding="utf-8") as out:
        for f in iter_traj_files(args.traj):
            try:
                rec = load_traj_file(f, project=project)
            except Exception as e:
                print(f"failed to parse {f}: {e}", file=sys.stderr)
                return 2
            out.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} sessions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
