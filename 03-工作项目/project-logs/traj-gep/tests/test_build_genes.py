import json
import re
from pathlib import Path

import pytest

from scripts.build_genes import (
    GeneBuilderConfig,
    build_gene_from_cluster,
    fallback_preconditions,
    fallback_strategy,
)


@pytest.fixture
def cfg() -> GeneBuilderConfig:
    return GeneBuilderConfig(
        max_signals_match=8, max_strategy_steps=6,
        include_provenance=True, provenance_session_sample=5,
    )


def _mkcluster(**overrides) -> dict:
    base = dict(
        cluster_id="f1_log_error_read_edit",
        family="F1", category="repair",
        key={"signal": "log_error", "tools": ["Read", "Edit"]},
        session_count=14, frequency=38,
        sessions=["aaaa", "bbbb", "cccc", "dddd", "eeee", "ffff"],
        signal_details=["log_error", "recurring_errsig:lua nil"],
        representative_files=["src/menu.lua"],
        correction_evidence=[],
        user_corpus_pool=[],
        llm={"title_zh": "T", "title_en": "T", "summary_zh": "S",
             "extra_signals": ["cn_extra_a", "cn_extra_b"]},
    )
    base.update(overrides)
    return base


def test_required_seven_fields_present(cfg):
    g = build_gene_from_cluster(_mkcluster(), project="wzp", cfg=cfg)
    for k in ("id", "category", "signals_match", "preconditions",
              "strategy", "constraints", "validation"):
        assert k in g, f"missing {k}"


def test_id_format_and_length(cfg):
    g = build_gene_from_cluster(_mkcluster(), project="wzp", cfg=cfg)
    assert re.match(r"^gene_traj_(wzp|zzj)_(f1sig|f2flow|f3phase)_[a-z0-9_]+$", g["id"])
    assert len(g["id"]) <= 60


def test_category_derivation_log_error_to_repair(cfg):
    g = build_gene_from_cluster(_mkcluster(category="repair"), project="wzp", cfg=cfg)
    assert g["category"] == "repair"


def test_category_derivation_user_feature_request_to_innovate(cfg):
    cluster = _mkcluster(
        category="innovate",
        key={"signal": "user_feature_request", "tools": ["Read", "Edit"]},
    )
    g = build_gene_from_cluster(cluster, project="wzp", cfg=cfg)
    assert g["category"] == "innovate"


def test_signals_match_includes_tools_lowercase(cfg):
    g = build_gene_from_cluster(_mkcluster(), project="wzp", cfg=cfg)
    assert "read" in g["signals_match"]
    assert "edit" in g["signals_match"]


def test_signals_match_capped_at_8(cfg):
    cluster = _mkcluster(
        signal_details=[f"log_error:detail{i}" for i in range(10)],
        llm={"title_zh": "", "title_en": "", "summary_zh": "",
             "extra_signals": [f"cn_x{i}" for i in range(5)]},
    )
    g = build_gene_from_cluster(cluster, project="wzp", cfg=cfg)
    assert len(g["signals_match"]) <= 8


def test_signals_match_includes_llm_extra_signals(cfg):
    g = build_gene_from_cluster(_mkcluster(), project="wzp", cfg=cfg)
    assert "cn_extra_a" in g["signals_match"]


def test_correction_evidence_appends_strategy_step(cfg):
    cluster = _mkcluster(
        correction_evidence=["no actually undo that"],
        llm={"title_zh": "", "title_en": "", "summary_zh": "",
             "extra_signals": [], "_fallback": True},   # forces fallback path
    )
    g = build_gene_from_cluster(cluster, project="wzp", cfg=cfg)
    assert any("撤销" in s or "纠正" in s or "rollback" in s.lower()
               or "user correction" in s.lower() for s in g["strategy"])


def test_validation_is_empty_array(cfg):
    g = build_gene_from_cluster(_mkcluster(), project="wzp", cfg=cfg)
    assert g["validation"] == []


def test_provenance_emitted_when_enabled(cfg):
    g = build_gene_from_cluster(_mkcluster(), project="wzp", cfg=cfg)
    assert "_provenance" in g
    assert g["_provenance"]["project"] == "wzp"
    cfg2 = GeneBuilderConfig(max_signals_match=8, max_strategy_steps=6,
                             include_provenance=False, provenance_session_sample=5)
    g2 = build_gene_from_cluster(_mkcluster(), project="wzp", cfg=cfg2)
    assert "_provenance" not in g2


def test_llm_preconditions_and_strategy_used_when_present(cfg, monkeypatch):
    """When LLM payload (non-fallback) is supplied, gene fields use LLM text."""
    cluster = _mkcluster()
    # The build function calls an LLM via a 'gene_llm' callback on the cluster.
    cluster["_gene_llm"] = {
        "preconditions": ["A中文条件1", "A中文条件2"],
        "strategy":      ["B步骤1：先 Read", "B步骤2：再 Edit", "B步骤3：监听用户撤销"],
    }
    g = build_gene_from_cluster(cluster, project="wzp", cfg=cfg)
    assert g["preconditions"] == ["A中文条件1", "A中文条件2"]
    assert g["strategy"][0].startswith("B步骤1")


def test_template_fallback_when_llm_returns_fallback_marker(cfg):
    cluster = _mkcluster()
    cluster["_gene_llm"] = {"_fallback": True}
    g = build_gene_from_cluster(cluster, project="wzp", cfg=cfg)
    assert g["preconditions"] == fallback_preconditions(cluster)
    assert g["strategy"] == fallback_strategy(cluster, cfg)


from scripts.build_genes import main as build_main


def test_build_cli_accepts_arbitrary_project(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    clusters = tmp_path / "clusters.json"
    clusters.write_text("[]")  # no clusters → no LLM calls
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "paths:\n  output_dir: " + str(tmp_path) + "\n"
        "gene_builder: {max_signals_match: 8, max_strategy_steps: 6, "
        "include_provenance: true, provenance_session_sample: 5}\n"
        "llm: {model: qwen3.6-plus, temperature: 0, seed: 42, enable_thinking: false, "
        "timeout_seconds: 10, max_retries: 1, retry_backoff_seconds: [0]}\n"
    )
    out = tmp_path / "genes.json"
    rc = build_main([
        "--clusters", str(clusters),
        "--project", "my-corpus",
        "--config", str(cfg),
        "--output", str(out),
    ])
    assert rc == 0
    assert out.read_text().strip() == "[]"


def test_build_cli_accepts_model_override(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    clusters = tmp_path / "clusters.json"
    clusters.write_text("[]")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "paths:\n  output_dir: " + str(tmp_path) + "\n"
        "gene_builder: {max_signals_match: 8, max_strategy_steps: 6, "
        "include_provenance: true, provenance_session_sample: 5}\n"
        "llm: {model: qwen3.6-plus, temperature: 0, seed: 42, enable_thinking: false, "
        "timeout_seconds: 10, max_retries: 1, retry_backoff_seconds: [0]}\n"
    )
    out = tmp_path / "genes.json"
    rc = build_main([
        "--clusters", str(clusters),
        "--project", "p",
        "--config", str(cfg),
        "--output", str(out),
        "--model", "claude-sonnet-4-6",
    ])
    assert rc == 0
    err = capsys.readouterr().err
    assert "DASHSCOPE_API_KEY" not in err
