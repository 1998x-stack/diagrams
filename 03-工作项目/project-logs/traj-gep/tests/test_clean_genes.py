import json
from pathlib import Path

import pytest

from scripts.clean_genes import (
    build_user_payload,
    cluster_genes,
    merge_cluster,
    main as clean_main,
)


# -------------------------------------------------------------------- fixtures


def _gene(gid: str, *, category: str, freq: int,
          title_zh: str = "标题", title_en: str = "Title",
          signals=("a", "b"), preconds=("p1",), strategy=("s1",),
          sessions=("ha", "hb")) -> dict:
    return {
        "type": "Gene",
        "id": gid,
        "category": category,
        "signals_match": list(signals),
        "preconditions": list(preconds),
        "strategy": list(strategy),
        "constraints": {"max_files": 10, "forbidden_paths": [".git"]},
        "validation": [],
        "title_zh": title_zh,
        "title_en": title_en,
        "_provenance": {
            "source": "traj-gep",
            "project": "p",
            "session_count": len(sessions),
            "frequency": freq,
            "session_hashes_sample": list(sessions),
        },
    }


class FakeLLM:
    """Returns a deterministic clusters payload keyed by category."""

    def __init__(self, payload_by_category: dict[str, dict]):
        self.payload_by_category = payload_by_category
        self.calls = []

    def call(self, *, system, user):
        self.calls.append({"system": system, "user": user})
        # User payload starts with `category=...\n` per build_user_payload.
        first_line = user.splitlines()[0]
        cat = first_line.split("=", 1)[1].strip()
        return self.payload_by_category.get(cat, {"clusters": []})


# -------------------------------------------------------------------- tests


def test_two_genes_merge_into_one(tmp_path):
    g1 = _gene("gene_a", category="workflow", freq=10, title_zh="A", title_en="A title",
               sessions=("h1", "h2"))
    g2 = _gene("gene_b", category="workflow", freq=4, title_zh="B", title_en="B title",
               sessions=("h2", "h3"))
    fake = FakeLLM({"workflow": {"clusters": [
        {"new_title_zh": "合并标题", "new_title_en": "Merged Title",
         "ids": ["gene_a", "gene_b"]},
    ]}})
    cleaned = cluster_genes([g1, g2], llm=fake, system_prompt="x",
                            min_titles_for_llm=2, prompt_max_genes_per_call=80)
    assert len(cleaned) == 1
    g = cleaned[0]
    assert g["title_zh"] == "合并标题"
    assert g["title_en"] == "Merged Title"
    assert g["_provenance"]["frequency"] == 14
    assert sorted(g["_provenance"]["session_hashes_sample"]) == ["h1", "h2", "h3"]
    assert g["_provenance"]["_merged_from"] == ["gene_a", "gene_b"]
    assert g["id"].startswith("gene_a_merged_2")  # highest-freq member wins id base


def test_categories_isolated_in_llm_calls(tmp_path):
    g_workflow = _gene("g_w", category="workflow", freq=5)
    g_repair = _gene("g_r", category="repair", freq=3)
    fake = FakeLLM({
        "workflow": {"clusters": [{"new_title_zh": "w", "new_title_en": "w", "ids": ["g_w"]}]},
        "repair":   {"clusters": [{"new_title_zh": "r", "new_title_en": "r", "ids": ["g_r"]}]},
    })
    cleaned = cluster_genes([g_workflow, g_repair], llm=fake, system_prompt="x",
                            min_titles_for_llm=2, prompt_max_genes_per_call=80)
    # The min_titles_for_llm=2 means single-gene categories skip LLM and become singletons.
    # That means NO calls should be made for single-element groups.
    # Verify: zero LLM calls because each category has only 1 gene.
    assert len(fake.calls) == 0
    assert len(cleaned) == 2


def test_missing_id_recovered_as_singleton(capsys):
    g1 = _gene("gene_a", category="workflow", freq=5)
    g2 = _gene("gene_b", category="workflow", freq=4)
    fake = FakeLLM({"workflow": {"clusters": [
        # LLM forgot gene_b
        {"new_title_zh": "T", "new_title_en": "T", "ids": ["gene_a"]},
    ]}})
    cleaned = cluster_genes([g1, g2], llm=fake, system_prompt="x",
                            min_titles_for_llm=2, prompt_max_genes_per_call=80)
    assert len(cleaned) == 2
    ids = sorted(g["id"] for g in cleaned)
    assert ids == ["gene_a", "gene_b"]
    assert "missing" in capsys.readouterr().err.lower()


def test_llm_fallback_keeps_all_genes_as_singletons():
    g1 = _gene("gene_a", category="workflow", freq=5)
    g2 = _gene("gene_b", category="workflow", freq=4)

    class FallbackLLM:
        def call(self, *, system, user):
            return {"_fallback": True, "_reason": "max_retries"}

    cleaned = cluster_genes([g1, g2], llm=FallbackLLM(), system_prompt="x",
                            min_titles_for_llm=2, prompt_max_genes_per_call=80)
    assert len(cleaned) == 2
    assert {g["id"] for g in cleaned} == {"gene_a", "gene_b"}


def test_singleton_keeps_original_titles_when_llm_omits():
    g = _gene("gene_a", category="workflow", freq=5,
              title_zh="原始标题", title_en="Original Title")
    fake = FakeLLM({"workflow": {"clusters": [
        {"new_title_zh": "", "new_title_en": "", "ids": ["gene_a"]},
    ]}})
    cleaned = cluster_genes([g], llm=fake, system_prompt="x",
                            min_titles_for_llm=1, prompt_max_genes_per_call=80)
    assert len(cleaned) == 1
    assert cleaned[0]["title_zh"] == "原始标题"
    assert cleaned[0]["title_en"] == "Original Title"


def test_main_writes_cleaned_genes_json(tmp_path, monkeypatch):
    """End-to-end: main() reads genes.json, calls a fake LLM, writes cleaned_genes.json."""
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    genes = [_gene(f"gene_{i}", category="workflow", freq=10 - i) for i in range(3)]
    genes_path = tmp_path / "genes.json"
    genes_path.write_text(json.dumps(genes, ensure_ascii=False))
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "paths:\n  output_dir: " + str(tmp_path) + "\n"
        "gene_builder: {max_signals_match: 8, max_strategy_steps: 6, "
        "include_provenance: true, provenance_session_sample: 5}\n"
        "cleaning: {prompt_max_genes_per_call: 80, min_titles_for_llm: 2}\n"
        "llm: {model: qwen3.6-plus, temperature: 0, seed: 42, enable_thinking: false, "
        "timeout_seconds: 10, max_retries: 1, retry_backoff_seconds: [0]}\n"
    )
    prompt_path = tmp_path / "clean.txt"
    prompt_path.write_text("dummy prompt")
    out = tmp_path / "cleaned.json"

    # Patch LLMClient.call to merge all three into one cluster
    def fake_call(self, *, system, user):
        return {"clusters": [{
            "new_title_zh": "三合一",
            "new_title_en": "Three Into One",
            "ids": ["gene_0", "gene_1", "gene_2"],
        }]}

    monkeypatch.setattr("scripts.llm_client.LLMClient.call", fake_call)
    rc = clean_main([
        "--genes", str(genes_path),
        "--project", "p",
        "--config", str(cfg_path),
        "--output", str(out),
        "--prompt-file", str(prompt_path),
    ])
    assert rc == 0
    cleaned = json.loads(out.read_text())
    assert len(cleaned) == 1
    assert cleaned[0]["title_zh"] == "三合一"
    assert cleaned[0]["_provenance"]["frequency"] == 10 + 9 + 8
