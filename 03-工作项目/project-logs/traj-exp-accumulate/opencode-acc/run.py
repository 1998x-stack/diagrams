"""
Gene accumulation runner — OpenCode / Qwen 3.6 Plus pipeline.

Iterates unprocessed sessions, invokes `opencode run` for each,
and records completion in _processed.json.

Usage:
    python3 run.py                     # Process all unprocessed sessions
    python3 run.py --only 9dc56f96     # Process a specific session
    python3 run.py --dry-run           # Show what would be processed
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from prompt import build_prompt

ROOT = Path(__file__).resolve().parent.parent
ACC_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = ACC_DIR / "plugins"
PROCESSED_PATH = ACC_DIR / "_processed.json"
LOGS_DIR = ACC_DIR / "logs"
EXAMPLES_DIR = ROOT / "examples"
TRAJ_DIR = ROOT.parent / "traj-data-new"
PROJECTS = ("wzp", "zzj")

log = logging.getLogger("opencode-acc")


def setup_logging():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        LOGS_DIR / f"run_{ts}.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    log.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.addHandler(console_handler)

    return LOGS_DIR / f"run_{ts}.log"


def load_processed() -> dict:
    if PROCESSED_PATH.exists():
        return json.loads(PROCESSED_PATH.read_text(encoding="utf-8"))
    return {"processed_sessions": {}}


def save_processed(data: dict):
    tmp = PROCESSED_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(PROCESSED_PATH)


def discover_sessions() -> list[tuple[str, str]]:
    sessions = []
    for project in PROJECTS:
        proj_dir = EXAMPLES_DIR / project
        if not proj_dir.exists():
            continue
        for jf in sorted(proj_dir.glob("*.json")):
            session = jf.stem
            traj = TRAJ_DIR / project / f"{session}.traj"
            if traj.exists():
                sessions.append((project, session))
    return sessions


def count_genes_in_plugins() -> int:
    total = 0
    for gf in PLUGINS_DIR.rglob("genes.json"):
        try:
            genes = json.loads(gf.read_text(encoding="utf-8"))
            total += len(genes)
        except Exception:
            pass
    return total


def save_session_log(session: str, prompt: str, result: subprocess.CompletedProcess):
    """Save per-session prompt + stdout + stderr for debugging."""
    session_log_dir = LOGS_DIR / "sessions"
    session_log_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = session_log_dir / f"{session}.prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    stdout_file = session_log_dir / f"{session}.stdout.txt"
    stdout_file.write_text(result.stdout or "", encoding="utf-8")

    if result.stderr:
        stderr_file = session_log_dir / f"{session}.stderr.txt"
        stderr_file.write_text(result.stderr, encoding="utf-8")


def process_session(project: str, session: str) -> tuple[bool, str]:
    """Run opencode run for a single session. Returns (success, message)."""
    prompt = build_prompt(session, project)
    log.debug(f"prompt length: {len(prompt)} chars")
    genes_before = count_genes_in_plugins()

    log.info(f"  invoking opencode run ...")
    t0 = time.time()

    try:
        result = subprocess.run(
            ["opencode", "run", prompt],
            capture_output=True,
            text=True,
            timeout=1600,
            cwd=str(ROOT),
        )
    except FileNotFoundError:
        return (False, "opencode CLI not found — is it installed and on PATH?")

    dt = time.time() - t0
    save_session_log(session, prompt, result)

    log.debug(f"opencode exit code: {result.returncode}")
    log.debug(f"stdout length: {len(result.stdout or '')} chars")
    if result.stderr:
        log.debug(f"stderr: {result.stderr[:500]}")

    genes_after = count_genes_in_plugins()
    genes_created = genes_after - genes_before

    if result.returncode != 0:
        stderr_preview = (result.stderr or "").strip()[:300]
        stdout_preview = (result.stdout or "").strip()[:300]
        detail = stderr_preview or stdout_preview or "(no output)"
        return (False, f"exit {result.returncode} after {dt:.0f}s — {detail}")

    if genes_created > 0:
        rebuild_indexes()

    return (True, f"done in {dt:.0f}s, genes delta: +{genes_created}")


def rebuild_indexes():
    """Regenerate index.md for all plugin categories."""
    log.debug("rebuilding index.md ...")
    try:
        subprocess.run(
            ["python3", str(ROOT / "gen_index.py"), "--plugins-dir", str(PLUGINS_DIR)],
            capture_output=True, text=True, timeout=30,
        )
    except Exception as e:
        log.warning(f"index rebuild failed: {e}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", help="Process only these session hashes")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--limit", type=int, default=0, help="Max sessions to process (0=all)")
    args = parser.parse_args()

    log_path = setup_logging()
    log.info(f"=== opencode-acc runner ===")
    log.info(f"log file: {log_path}")

    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    processed = load_processed()
    all_sessions = discover_sessions()

    if args.only:
        targets = [(p, s) for p, s in all_sessions if s in args.only]
    else:
        done = set(processed["processed_sessions"].keys())
        targets = [(p, s) for p, s in all_sessions if s not in done]

    if args.limit > 0:
        targets = targets[:args.limit]

    log.info(f"Total sessions available: {len(all_sessions)}")
    log.info(f"Already processed: {len(processed['processed_sessions'])}")
    log.info(f"To process: {len(targets)}")

    if args.dry_run:
        for project, session in targets:
            log.info(f"  would process: {project}/{session}")
        return 0

    ok_count = 0
    fail_count = 0

    for i, (project, session) in enumerate(targets, 1):
        log.info(f"\n[{i}/{len(targets)}] {project}/{session}")
        try:
            success, msg = process_session(project, session)
        except subprocess.TimeoutExpired:
            success, msg = False, "timeout (1600s)"
        except Exception as e:
            log.debug(f"exception: {e}", exc_info=True)
            success, msg = False, f"crash: {e}"

        if success:
            ok_count += 1
            processed["processed_sessions"][session] = {
                "project": project,
                "processed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "genes_delta": msg.split("+")[-1] if "+" in msg else "0",
                "message": msg,
            }
            save_processed(processed)
            log.info(f"  OK {msg}")
        else:
            fail_count += 1
            log.error(f"  FAIL {msg}")

    log.info(f"\n=== summary: {ok_count} ok, {fail_count} failed ===")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
