import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.load_trajectories import (
    SessionRecord,
    load_traj_file,
    extract_correction_signals,
    main as load_main,
)


def test_loads_basic_traj(tmp_traj_file, sample_user_msg, sample_step):
    f = tmp_traj_file("abc12345", [
        sample_user_msg("hello"),
        sample_step("Read", args={"file_path": "src/x.lua"}),
    ])
    rec = load_traj_file(f, project="wzp")
    assert isinstance(rec, SessionRecord)
    assert rec.project == "wzp"
    assert rec.session_hash == "abc12345"
    assert "hello" in rec.user_corpus
    assert rec.tool_sequence == ["Read"]
    assert rec.n_steps == 1


def test_user_corpus_concatenates_with_separator(tmp_traj_file, sample_user_msg):
    f = tmp_traj_file("abc12345", [
        sample_user_msg("first"),
        sample_user_msg("second"),
        sample_user_msg("third"),
    ])
    rec = load_traj_file(f, project="wzp")
    assert "\n---\n" in rec.user_corpus
    assert rec.user_corpus.count("\n---\n") == 2


def test_error_corpus_filters_by_exit_code(tmp_traj_file, sample_step):
    f = tmp_traj_file("abc12345", [
        sample_step("Bash", obs_text="ok output", exit_code=0),
        sample_step("Bash", obs_text="boom", exit_code=1),
    ])
    rec = load_traj_file(f, project="wzp")
    assert "boom" in rec.error_corpus
    assert "ok output" not in rec.error_corpus


def test_error_corpus_matches_error_keywords(tmp_traj_file, sample_step):
    f = tmp_traj_file("abc12345", [
        sample_step("Bash", obs_text="Traceback (most recent call last):\n  File ...", exit_code=None),
    ])
    rec = load_traj_file(f, project="wzp")
    assert "Traceback" in rec.error_corpus


def test_tool_sequence_skips_respond_to_user(tmp_traj_file, sample_step):
    f = tmp_traj_file("abc12345", [
        sample_step("Read"),
        sample_step("respond_to_user"),
        sample_step("Edit"),
    ])
    rec = load_traj_file(f, project="wzp")
    assert rec.tool_sequence == ["Read", "Edit"]


def test_subagent_recorded_as_at_prefix(tmp_traj_file, sample_step):
    step = sample_step("Agent")
    step["action"]["args"] = {"subagent_type": "code-reviewer"}
    f = tmp_traj_file("abc12345", [step])
    rec = load_traj_file(f, project="wzp")
    assert rec.tool_sequence == ["@code-reviewer"]


def test_correction_signals_extract_chinese_and_english():
    text = "no don't add validation\n撤销那个改动\n实际上 actually wait"
    matches = extract_correction_signals(text)
    joined = " | ".join(matches)
    assert "no" in joined.lower() or "don" in joined.lower()
    assert "撤销" in joined
    assert "actually" in joined.lower()


def test_cli_writes_jsonl(tmp_path, tmp_traj_file, sample_user_msg, sample_step):
    f1 = tmp_traj_file("aaaa1111", [sample_user_msg("hi"), sample_step("Read")])
    f2 = tmp_traj_file("bbbb2222", [sample_user_msg("yo"), sample_step("Edit")])
    out = tmp_path / "sessions.jsonl"
    repo_root = Path(__file__).resolve().parents[2]   # project-logs/
    script = repo_root / "traj-gep" / "scripts" / "load_trajectories.py"
    proc = subprocess.run(
        [sys.executable, str(script),
         "--traj-dir", str(f1.parent),
         "--project", "wzp",
         "--output", str(out)],
        capture_output=True, text=True, check=True,
    )
    assert out.exists()
    lines = out.read_text().strip().split("\n")
    assert len(lines) == 2
    parsed = [json.loads(l) for l in lines]
    hashes = {p["session_hash"] for p in parsed}
    assert hashes == {"aaaa1111", "bbbb2222"}


def _write_minimal_traj(path: Path):
    path.write_text(json.dumps({
        "session_id": "abc",
        "messages": [
            {"role": "user", "content": "hello"},
            {"agent_run_id": "r1", "steps": []},
        ],
    }), encoding="utf-8")


def test_cli_accepts_traj_flag(tmp_path):
    traj_dir = tmp_path / "wzp"
    traj_dir.mkdir()
    _write_minimal_traj(traj_dir / "00000001.traj")
    out = tmp_path / "out.jsonl"
    rc = load_main(["--traj", str(traj_dir), "--output", str(out)])
    assert rc == 0
    line = json.loads(out.read_text().strip())
    assert line["project"] == "wzp"   # derived from basename


def test_cli_explicit_project_overrides_basename(tmp_path):
    traj_dir = tmp_path / "wzp"
    traj_dir.mkdir()
    _write_minimal_traj(traj_dir / "00000001.traj")
    out = tmp_path / "out.jsonl"
    rc = load_main(["--traj", str(traj_dir), "--project", "custom", "--output", str(out)])
    assert rc == 0
    line = json.loads(out.read_text().strip())
    assert line["project"] == "custom"


def test_cli_traj_dir_alias_still_works(tmp_path):
    traj_dir = tmp_path / "zzj"
    traj_dir.mkdir()
    _write_minimal_traj(traj_dir / "00000001.traj")
    out = tmp_path / "out.jsonl"
    rc = load_main(["--traj-dir", str(traj_dir), "--output", str(out)])
    assert rc == 0
    line = json.loads(out.read_text().strip())
    assert line["project"] == "zzj"
