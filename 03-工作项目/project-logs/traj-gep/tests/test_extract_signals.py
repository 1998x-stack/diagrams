import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]      # project-logs/
WRAPPER = REPO / "traj-gep" / "scripts" / "extract_signals.js"


def _node_available() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


@pytest.mark.skipif(not _node_available(), reason="node not installed")
def test_node_wrapper_executable():
    payload = json.dumps({"userSnippet": "ping", "todayLog": ""})
    proc = subprocess.run(
        ["node", str(WRAPPER)],
        input=payload, capture_output=True, text=True, check=True, timeout=15,
    )
    out = json.loads(proc.stdout)
    assert "signals" in out
    assert isinstance(out["signals"], list)


def test_user_feature_request_signal_detected(monkeypatch, sample_session_record):
    from scripts import extract_signals as es
    rec = sample_session_record(user_corpus="please add a new button to the inventory menu")

    def fake_run(cmd, input, capture_output, text, timeout, check):
        class P:
            stdout = json.dumps({"signals": ["user_feature_request:add a new button"]})
            stderr = ""
        return P()

    monkeypatch.setattr(es.subprocess, "run", fake_run)
    sigs = es.extract_signals_for_session(
        rec, WRAPPER, user_max=1000, err_max=1000, timeout=5,
    )
    assert any(s.startswith("user_feature_request") for s in sigs)


def test_log_error_signal_detected(monkeypatch, sample_session_record):
    from scripts import extract_signals as es
    rec = sample_session_record(error_corpus="Traceback (most recent call last):\n  File 'x'")

    def fake_run(*a, **kw):
        class P:
            stdout = json.dumps({"signals": ["log_error"]})
            stderr = ""
        return P()

    monkeypatch.setattr(es.subprocess, "run", fake_run)
    sigs = es.extract_signals_for_session(rec, WRAPPER, user_max=1000, err_max=1000, timeout=5)
    assert "log_error" in sigs


def test_timeout_returns_empty_signals_with_warning(monkeypatch, sample_session_record, capsys):
    from scripts import extract_signals as es
    rec = sample_session_record()

    def fake_run(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="node", timeout=5)

    monkeypatch.setattr(es.subprocess, "run", fake_run)
    sigs = es.extract_signals_for_session(rec, WRAPPER, user_max=1000, err_max=1000, timeout=5)
    assert sigs == []
    captured = capsys.readouterr()
    assert "timeout" in captured.err.lower()


def test_signals_jsonl_output_shape(tmp_path, monkeypatch, sample_session_record):
    """End-to-end through main() with one session."""
    from scripts import extract_signals as es
    sessions = tmp_path / "sessions.jsonl"
    output = tmp_path / "signals.jsonl"
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "extractor:\n  user_corpus_max_chars: 1000\n  error_corpus_max_chars: 1000\n"
        "  timeout_seconds: 5\n  node_bin: node\n"
    )
    rec = sample_session_record()
    sessions.write_text(
        json.dumps({
            "project": rec.project, "session_hash": rec.session_hash,
            "user_corpus": rec.user_corpus, "error_corpus": rec.error_corpus,
            "tool_sequence": rec.tool_sequence, "phase_sequence": rec.phase_sequence,
            "correction_signals": rec.correction_signals,
            "file_targets": rec.file_targets, "n_steps": rec.n_steps,
        }, ensure_ascii=False) + "\n"
    )

    def fake_run(*a, **kw):
        class P:
            stdout = json.dumps({"signals": ["fake_signal"]}); stderr = ""
        return P()

    monkeypatch.setattr(es.subprocess, "run", fake_run)
    rc = es.main([
        "--sessions-file", str(sessions),
        "--wrapper", str(WRAPPER),
        "--output", str(output),
        "--config", str(cfg_file),
    ])
    assert rc == 0
    rows = [json.loads(l) for l in output.read_text().strip().split("\n")]
    assert rows[0]["signals"] == ["fake_signal"]
    assert rows[0]["session_hash"] == "abc12345"
