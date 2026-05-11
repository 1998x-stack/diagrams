import json
from pathlib import Path

import pytest

from scripts.llm_client import LLMClient, LLMConfig


@pytest.fixture
def cfg() -> LLMConfig:
    return LLMConfig(
        provider="qwen",
        model="qwen3.6-plus",
        base_url="https://example.invalid/v1",
        api_key="dummy",
        temperature=0,
        seed=42,
        enable_thinking=False,
        timeout_seconds=10,
        max_retries=3,
        retry_backoff_seconds=[0, 0, 0],
    )


def _seed_cache(path: Path, key: str, payload: dict, model: str = "qwen3.6-plus"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"key": key, "model": model, "payload": payload},
                            ensure_ascii=False) + "\n")


def test_cache_hit_avoids_api_call(tmp_path, cfg, monkeypatch):
    cache = tmp_path / "llm_cache.jsonl"
    client = LLMClient(cfg, cache_path=cache)
    key = client.compute_key("sys", "user")
    _seed_cache(cache, key, {"hello": "world"})

    def boom(*a, **kw):
        raise AssertionError("API should not be called on cache hit")

    monkeypatch.setattr(client, "_create_chat_completion", boom)
    out = client.call(system="sys", user="user")
    assert out == {"hello": "world"}


def test_cache_key_includes_model(tmp_path, cfg):
    cache = tmp_path / "llm_cache.jsonl"
    client_a = LLMClient(cfg, cache_path=cache)
    client_b = LLMClient(cfg.replace(model="qwen-other"), cache_path=cache)
    assert client_a.compute_key("s", "u") != client_b.compute_key("s", "u")


def test_retry_on_429_then_success(tmp_path, cfg, monkeypatch):
    cache = tmp_path / "llm_cache.jsonl"
    client = LLMClient(cfg, cache_path=cache)
    calls = {"n": 0}

    def fake_create(system, user):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("HTTP 429 rate limit")
        return {"ok": True}

    monkeypatch.setattr(client, "_create_chat_completion", fake_create)
    out = client.call(system="s", user="u")
    assert out == {"ok": True}
    assert calls["n"] == 2


def test_returns_fallback_marker_after_max_retries(tmp_path, cfg, monkeypatch):
    cache = tmp_path / "llm_cache.jsonl"
    client = LLMClient(cfg, cache_path=cache)

    def always_fail(system, user):
        raise RuntimeError("HTTP 500")

    monkeypatch.setattr(client, "_create_chat_completion", always_fail)
    out = client.call(system="s", user="u")
    assert out == {"_fallback": True, "_reason": "max_retries"}


def test_response_format_json_object_parsed(tmp_path, cfg, monkeypatch):
    cache = tmp_path / "llm_cache.jsonl"
    client = LLMClient(cfg, cache_path=cache)

    def fake_create(system, user):
        return {"title_zh": "标题", "extra_signals": ["a"]}

    monkeypatch.setattr(client, "_create_chat_completion", fake_create)
    out = client.call(system="s", user="u")
    assert out["title_zh"] == "标题"
    # cache should now be populated
    cached = [json.loads(l) for l in (tmp_path / "llm_cache.jsonl").read_text().splitlines()]
    assert len(cached) == 1
