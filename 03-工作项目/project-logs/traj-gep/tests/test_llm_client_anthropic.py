import json
from pathlib import Path

import pytest

from scripts.llm_client import LLMClient, LLMConfig, load_llm_config


def _claude_cfg() -> LLMConfig:
    return LLMConfig(
        provider="claude",
        model="claude-sonnet-4-6",
        base_url="https://api.anthropic.com",
        api_key="dummy",
        temperature=0,
        seed=42,
        enable_thinking=False,
        timeout_seconds=10,
        max_retries=2,
        retry_backoff_seconds=[0, 0],
    )


def test_provider_autodetect_claude_from_model_name(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    cfg = load_llm_config({"llm": {"model": "claude-sonnet-4-6"}})
    assert cfg.provider == "claude"
    assert cfg.api_key == "k"


def test_provider_autodetect_qwen_from_model_name(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    cfg = load_llm_config({"llm": {"model": "qwen3.6-plus"}})
    assert cfg.provider == "qwen"


def test_provider_explicit_override_in_config(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    cfg = load_llm_config({"llm": {"model": "qwen3.6-plus", "provider": "claude"}})
    assert cfg.provider == "claude"


def test_model_override_from_cli_arg(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    cfg = load_llm_config({"llm": {"model": "qwen3.6-plus"}}, model_override="claude-sonnet-4-6")
    assert cfg.provider == "claude"
    assert cfg.model == "claude-sonnet-4-6"


def test_anthropic_backend_returns_parsed_json(tmp_path, monkeypatch):
    cache = tmp_path / "llm_cache.jsonl"
    client = LLMClient(_claude_cfg(), cache_path=cache)

    def fake_anth(system, user):
        return '{"hello":"world"}'

    monkeypatch.setattr(client, "_anthropic_raw_text", fake_anth)
    out = client.call(system="s", user="u")
    assert out == {"hello": "world"}


def test_anthropic_backend_strips_json_fences(tmp_path, monkeypatch):
    cache = tmp_path / "llm_cache.jsonl"
    client = LLMClient(_claude_cfg(), cache_path=cache)

    def fake_anth(system, user):
        return "```json\n{\"a\":1}\n```"

    monkeypatch.setattr(client, "_anthropic_raw_text", fake_anth)
    out = client.call(system="s", user="u")
    assert out == {"a": 1}


def test_anthropic_backend_returns_fallback_on_unparseable(tmp_path, monkeypatch):
    cache = tmp_path / "llm_cache.jsonl"
    client = LLMClient(_claude_cfg(), cache_path=cache)

    def fake_anth(system, user):
        return "not json at all"

    monkeypatch.setattr(client, "_anthropic_raw_text", fake_anth)
    out = client.call(system="s", user="u")
    assert out == {"_fallback": True, "_reason": "json_parse"}


def test_cache_key_differs_across_models(tmp_path):
    cache = tmp_path / "llm_cache.jsonl"
    qwen = LLMClient(LLMConfig(
        provider="qwen", model="qwen3.6-plus", base_url="x", api_key="k",
        temperature=0, seed=42, enable_thinking=False, timeout_seconds=10,
        max_retries=1, retry_backoff_seconds=[0],
    ), cache_path=cache)
    claude = LLMClient(_claude_cfg(), cache_path=cache)
    assert qwen.compute_key("s", "u") != claude.compute_key("s", "u")
