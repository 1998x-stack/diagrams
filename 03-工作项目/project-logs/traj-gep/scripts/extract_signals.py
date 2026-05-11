"""Stage 2 — Python orchestrator that calls the Node wrapper for each session."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import yaml

from scripts.load_trajectories import SessionRecord


def extract_signals_for_session(
    record: SessionRecord,
    wrapper_path: Path,
    *,
    user_max: int,
    err_max: int,
    timeout: int,
    node_bin: str = "node",
) -> list[str]:
    payload = json.dumps({
        "userSnippet": (record.user_corpus or "")[:user_max],
        "todayLog":    (record.error_corpus or "")[:err_max],
        "recentSessionTranscript": "",
        "memorySnippet": "",
    }, ensure_ascii=False)
    try:
        proc = subprocess.run(
            [node_bin, str(wrapper_path)],
            input=payload, capture_output=True, text=True,
            timeout=timeout, check=True,
        )
    except subprocess.TimeoutExpired:
        print(f"WARN: extract_signals timeout for {record.session_hash}", file=sys.stderr)
        return []
    except subprocess.CalledProcessError as e:
        print(f"WARN: extract_signals failed for {record.session_hash}: {e.stderr.strip()}",
              file=sys.stderr)
        return []
    try:
        return list(json.loads(proc.stdout).get("signals") or [])
    except json.JSONDecodeError:
        print(f"WARN: extract_signals bad JSON for {record.session_hash}", file=sys.stderr)
        return []


def _load_config(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sessions-file", required=True, type=Path)
    p.add_argument("--wrapper", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--config", default=Path("config.yaml"), type=Path)
    args = p.parse_args(argv)

    cfg = _load_config(args.config)
    e_cfg = cfg.get("extractor", {})
    user_max = int(e_cfg.get("user_corpus_max_chars", 50000))
    err_max = int(e_cfg.get("error_corpus_max_chars", 30000))
    timeout = int(e_cfg.get("timeout_seconds", 15))
    node_bin = e_cfg.get("node_bin", "node")

    if not args.wrapper.exists():
        print(f"wrapper not found: {args.wrapper}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with args.sessions_file.open(encoding="utf-8") as fh, \
         args.output.open("w", encoding="utf-8") as out:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            rec = SessionRecord(**data)
            sigs = extract_signals_for_session(
                rec, args.wrapper,
                user_max=user_max, err_max=err_max, timeout=timeout, node_bin=node_bin,
            )
            row = asdict(rec) | {"signals": sigs}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote signals for {n} sessions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
