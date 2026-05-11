import json
from pathlib import Path

import pytest

from scripts.cluster_patterns import (
    Cluster,
    ClusterConfig,
    cluster_signals,
    normalize_signal,
    augment_with_llm,
    sample_excerpts,
)


@pytest.fixture
def base_cfg() -> ClusterConfig:
    return ClusterConfig(
        min_sessions=3, min_frequency=5, min_distinctness=0.0,
        top_k_per_family=30, dedupe_jaccard=0.99,
    )


def _mkrec(h, signals, tools, phases=None):
    return {
        "session_hash": h, "project": "wzp", "signals": signals,
        "tool_sequence": tools,
        "phase_sequence": phases or ["editing"] * len(tools),
        "correction_signals": [], "file_targets": [], "n_steps": len(tools),
        "user_corpus": "test corpus",
    }


def test_f1_signal_x_bigram_clusters(base_cfg):
    sessions = [
        _mkrec("a", ["log_error"], ["Read", "Edit", "Read", "Edit"]),
        _mkrec("b", ["log_error"], ["Read", "Edit", "Bash"]),
        _mkrec("c", ["log_error"], ["Read", "Edit"]),
    ]
    out = cluster_signals(sessions, base_cfg)
    f1 = [c for c in out if c.family == "F1"]
    assert any(c.key.get("signal") == "log_error"
               and c.key.get("tools") == ["Read", "Edit"] for c in f1)


def test_f2_trigram_clusters(base_cfg):
    sessions = [_mkrec(h, ["x"], ["Read", "Edit", "Bash", "Read", "Edit", "Bash"])
                for h in ("a", "b", "c", "d", "e")]
    out = cluster_signals(sessions, base_cfg)
    f2 = [c for c in out if c.family == "F2"]
    assert any(c.key.get("tools") == ["Read", "Edit", "Bash"] for c in f2)


def test_f3_phase_transition_clusters(base_cfg):
    sessions = [
        _mkrec("a", ["log_error"], ["Read", "Edit"], phases=["localization", "editing"]),
        _mkrec("b", ["log_error"], ["Read", "Edit"], phases=["localization", "editing"]),
        _mkrec("c", ["log_error"], ["Read", "Edit"], phases=["localization", "editing"]),
    ]
    out = cluster_signals(sessions, base_cfg)
    f3 = [c for c in out if c.family == "F3"]
    assert any(c.key.get("from_phase") == "localization"
               and c.key.get("to_phase") == "editing" for c in f3)


def test_min_sessions_threshold_excludes(base_cfg):
    sessions = [
        _mkrec("a", ["log_error"], ["Read", "Edit"]),
        _mkrec("b", ["log_error"], ["Read", "Edit"]),
    ]
    out = cluster_signals(sessions, base_cfg)
    assert all(c.session_count >= 3 for c in out)


def test_min_distinctness_excludes_concentrated():
    cfg = ClusterConfig(min_sessions=3, min_frequency=5, min_distinctness=0.5,
                        top_k_per_family=30, dedupe_jaccard=0.99)
    sessions = [
        _mkrec("a", ["log_error"], ["Read", "Edit"] * 10),
        _mkrec("b", ["log_error"], ["Read", "Edit"]),
        _mkrec("c", ["log_error"], ["Read", "Edit"]),
    ]
    out = cluster_signals(sessions, cfg)
    f1_log = [c for c in out if c.family == "F1" and c.key.get("signal") == "log_error"]
    if f1_log:
        for c in f1_log:
            assert c.session_count / c.frequency >= 0.5


def test_signal_normalize_strips_detail_suffix():
    assert normalize_signal("user_feature_request:add inventory") == "user_feature_request"
    assert normalize_signal("log_error") == "log_error"


def test_dedupe_by_jaccard():
    cfg = ClusterConfig(min_sessions=3, min_frequency=5, min_distinctness=0.0,
                        top_k_per_family=30, dedupe_jaccard=0.5)
    sessions = [
        _mkrec("a", ["log_error", "x_other"], ["Read", "Edit"]),
        _mkrec("b", ["log_error", "x_other"], ["Read", "Edit"]),
        _mkrec("c", ["log_error", "x_other"], ["Read", "Edit"]),
    ]
    out = cluster_signals(sessions, cfg)
    f1 = [c for c in out if c.family == "F1"]
    keys = [(c.key.get("signal"), tuple(c.key.get("tools", []))) for c in f1]
    assert len(set(keys)) == len(keys)


def test_top_k_per_family_caps_output():
    cfg = ClusterConfig(min_sessions=2, min_frequency=2, min_distinctness=0.0,
                        top_k_per_family=2, dedupe_jaccard=0.99)
    sessions = []
    for i in range(5):
        sessions.append(_mkrec(f"s{i}", [f"sig{i}"], ["Read", "Edit"]))
    sessions += [_mkrec("z1", ["sig0"], ["Read", "Edit"]),
                 _mkrec("z2", ["sig1"], ["Read", "Edit"])]
    out = cluster_signals(sessions, cfg)
    by_fam = {}
    for c in out:
        by_fam.setdefault(c.family, []).append(c)
    for fam, items in by_fam.items():
        assert len(items) <= 2


def test_signal_details_preserved_for_field_filling(base_cfg):
    sessions = [
        _mkrec("a", ["log_error", "recurring_errsig:lua nil"], ["Read", "Edit"]),
        _mkrec("b", ["log_error", "recurring_errsig:lua nil"], ["Read", "Edit"]),
        _mkrec("c", ["log_error"], ["Read", "Edit"]),
    ]
    out = cluster_signals(sessions, base_cfg)
    f1 = [c for c in out if c.family == "F1" and c.key.get("signal") == "log_error"]
    assert f1, "expected at least one F1 log_error cluster"
    assert any("recurring_errsig:lua nil" in c.signal_details for c in f1)


class _StubLLM:
    """Stand-in for LLMClient used in augmentation tests."""
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def call(self, *, system, user):
        self.calls += 1
        return dict(self.payload)


def test_llm_summary_attached_to_each_cluster(base_cfg):
    sessions = [
        _mkrec("a", ["log_error"], ["Read", "Edit"]),
        _mkrec("b", ["log_error"], ["Read", "Edit"]),
        _mkrec("c", ["log_error"], ["Read", "Edit"]),
    ]
    clusters = cluster_signals(sessions, base_cfg)
    llm = _StubLLM({
        "title_zh": "测试标题", "title_en": "test title",
        "summary_zh": "测试摘要", "extra_signals": ["cn_test_signal"],
    })
    augmented = augment_with_llm(clusters, sessions, llm,
                                 system_prompt="sys",
                                 excerpt_count=2, excerpt_max_chars=80)
    assert llm.calls == len(clusters)
    for c in augmented:
        assert c.llm["title_zh"] == "测试标题"
        assert "cn_test_signal" in c.llm["extra_signals"]


def test_llm_excerpt_sampling_is_deterministic_per_cluster_id():
    pool = [f"snippet number {i} with some words" for i in range(20)]
    a1 = sample_excerpts("cluster_X", pool, count=5, max_chars=30)
    a2 = sample_excerpts("cluster_X", pool, count=5, max_chars=30)
    b = sample_excerpts("cluster_Y", pool, count=5, max_chars=30)
    assert a1 == a2
    assert a1 != b


from scripts.cluster_patterns import main as cluster_main


def test_cluster_cli_accepts_arbitrary_project(tmp_path, monkeypatch):
    """A non-{wzp,zzj} project name must be accepted."""
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    sigs = tmp_path / "signals.jsonl"
    sigs.write_text("")  # empty, no clusters
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "paths:\n  output_dir: " + str(tmp_path) + "\n"
        "clustering: {min_sessions: 3, min_frequency: 5, min_distinctness: 0.4, "
        "top_k_per_family: 30, dedupe_jaccard: 0.8}\n"
        "llm: {model: qwen3.6-plus, temperature: 0, seed: 42, enable_thinking: false, "
        "timeout_seconds: 10, max_retries: 1, retry_backoff_seconds: [0]}\n"
    )
    prompt = tmp_path / "p.txt"; prompt.write_text("dummy")
    out = tmp_path / "clusters.json"
    rc = cluster_main([
        "--signals-file", str(sigs),
        "--project", "anything-goes",
        "--config", str(cfg),
        "--output", str(out),
        "--prompt-file", str(prompt),
    ])
    # We expect rc=0 (no clusters → no LLM calls → ok);
    # critically NOT argparse SystemExit due to choices restriction.
    assert rc == 0


def test_cluster_cli_accepts_model_override(tmp_path, monkeypatch, capsys):
    """--model on the CLI overrides config.yaml."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    sigs = tmp_path / "signals.jsonl"
    sigs.write_text("")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "paths:\n  output_dir: " + str(tmp_path) + "\n"
        "clustering: {min_sessions: 3, min_frequency: 5, min_distinctness: 0.4, "
        "top_k_per_family: 30, dedupe_jaccard: 0.8}\n"
        "llm: {model: qwen3.6-plus, temperature: 0, seed: 42, enable_thinking: false, "
        "timeout_seconds: 10, max_retries: 1, retry_backoff_seconds: [0]}\n"
    )
    prompt = tmp_path / "p.txt"; prompt.write_text("dummy")
    out = tmp_path / "clusters.json"
    rc = cluster_main([
        "--signals-file", str(sigs),
        "--project", "p",
        "--config", str(cfg),
        "--output", str(out),
        "--prompt-file", str(prompt),
        "--model", "claude-sonnet-4-6",
    ])
    assert rc == 0
    # If the LLMConfig was built with claude provider it will have read ANTHROPIC_API_KEY,
    # which is set above. Smoke check: no DASHSCOPE_API_KEY error on stderr.
    err = capsys.readouterr().err
    assert "DASHSCOPE_API_KEY" not in err
