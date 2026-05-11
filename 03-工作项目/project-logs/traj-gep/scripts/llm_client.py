"""Shared Qwen LLM client with prompt-hash cache for reproducibility."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

@dataclass(frozen=True)
class LLMConfig:
    provider: Literal["qwen", "claude"]
    model: str
    base_url: str
    api_key: str
    temperature: float
    seed: int
    enable_thinking: bool
    timeout_seconds: int
    max_retries: int
    retry_backoff_seconds: list[int] = field(default_factory=lambda: [1, 4, 16])

    def replace(self, **kwargs) -> "LLMConfig":
        return dataclasses.replace(self, **kwargs)


def _detect_provider(model: str) -> Literal["qwen", "claude"]:
    return "claude" if model.lower().startswith("claude") else "qwen"


def load_llm_config(cfg: dict, *, model_override: str | None = None) -> LLMConfig:
    """Build LLMConfig from parsed config.yaml `llm` section + env.
    `model_override` (from CLI --model) wins over config.yaml.
    """
    section = cfg.get("llm", {})
    model = model_override or section.get("model", "qwen3.6-plus")
    provider = section.get("provider") or _detect_provider(model)

    if provider == "claude":
        api_key_env = section.get("api_key_env_claude", "ANTHROPIC_API_KEY")
        base_url = section.get("base_url_claude", "https://api.anthropic.com")
    else:
        api_key_env = section.get("api_key_env", "DASHSCOPE_API_KEY")
        base_url = section.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    api_key = os.environ.get(api_key_env, "")
    if not api_key:
        raise RuntimeError(
            f"environment variable {api_key_env!r} is not set; required for LLM calls"
        )
    return LLMConfig(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=float(section.get("temperature", 0)),
        seed=int(section.get("seed", 42)),
        enable_thinking=bool(section.get("enable_thinking", False)),
        timeout_seconds=int(section.get("timeout_seconds", 60)),
        max_retries=int(section.get("max_retries", 3)),
        retry_backoff_seconds=list(section.get("retry_backoff_seconds", [1, 4, 16])),
    )


class LLMClient:
    """Caches by SHA256(model + system + user). Always-deterministic."""

    def __init__(self, cfg: LLMConfig, *, cache_path: Path):
        self.cfg = cfg
        self.cache_path = Path(cache_path)
        self._openai = None
        self._anthropic = None
        if cfg.provider == "qwen":
            from openai import OpenAI
            self._openai = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url,
                                  timeout=cfg.timeout_seconds)
        else:
            from anthropic import Anthropic
            self._anthropic = Anthropic(api_key=cfg.api_key, base_url=cfg.base_url,
                                        timeout=cfg.timeout_seconds)

    # ------------------------------------------------------------------ cache

    def compute_key(self, system: str, user: str) -> str:
        body = f"{self.cfg.model}\n{system}\n---\n{user}"
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def _lookup_cache(self, key: str) -> dict | None:
        if not self.cache_path.exists():
            return None
        with self.cache_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("key") == key and row.get("model") == self.cfg.model:
                    return row.get("payload")
        return None

    def _append_cache(self, key: str, payload: dict) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"key": key, "model": self.cfg.model, "payload": payload},
                                ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ backends

    _ANTH_JSON_INSTRUCTION = (
        "\n\nRespond with a single JSON object only. No prose, no Markdown fences."
    )

    def _openai_create(self, system: str, user: str) -> dict:
        resp = self._openai.chat.completions.create(
            model=self.cfg.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=self.cfg.temperature,
            seed=self.cfg.seed,
            extra_body={"enable_thinking": self.cfg.enable_thinking},
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)

    def _anthropic_raw_text(self, system: str, user: str) -> str:
        resp = self._anthropic.messages.create(
            model=self.cfg.model,
            system=system + self._ANTH_JSON_INSTRUCTION,
            messages=[{"role": "user", "content": user}],
            max_tokens=4096,
            temperature=self.cfg.temperature,
        )
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "".join(parts).strip()

    @staticmethod
    def _strip_fences(text: str) -> str:
        t = text.strip()
        if t.startswith("```"):
            # remove leading ```lang and trailing ```
            t = t.split("\n", 1)[1] if "\n" in t else t[3:]
            if t.endswith("```"):
                t = t[: -3]
        return t.strip()

    def _anthropic_create(self, system: str, user: str) -> dict:
        text = self._anthropic_raw_text(system, user)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                return json.loads(self._strip_fences(text))
            except json.JSONDecodeError:
                return {"_fallback": True, "_reason": "json_parse"}

    def _create_chat_completion(self, system: str, user: str) -> dict:
        if self.cfg.provider == "claude":
            return self._anthropic_create(system, user)
        return self._openai_create(system, user)

    # ------------------------------------------------------------------ public

    def call(self, *, system: str, user: str) -> dict:
        key = self.compute_key(system, user)
        cached = self._lookup_cache(key)
        if cached is not None:
            return cached

        last_err: Exception | None = None
        for attempt in range(self.cfg.max_retries):
            try:
                payload = self._create_chat_completion(system, user)
                # cache only successful (non-fallback) and non-error payloads
                if payload.get("_fallback"):
                    return payload
                self._append_cache(key, payload)
                return payload
            except Exception as e:
                last_err = e
                if attempt + 1 < self.cfg.max_retries:
                    delay = self.cfg.retry_backoff_seconds[
                        min(attempt, len(self.cfg.retry_backoff_seconds) - 1)
                    ]
                    if delay > 0:
                        time.sleep(delay)
        return {"_fallback": True, "_reason": "max_retries"}
