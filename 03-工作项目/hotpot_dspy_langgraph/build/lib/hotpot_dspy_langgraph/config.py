"""Configuration helpers for the HotPotQA DSPy + LangGraph project.

The central concern in this file is model setup. The user asked for:

- `DASHSCOPE_API_KEY` as the credential source
- `OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `OPENAI_MODEL=qwen3.6-plus`
- `enable_thinking=false`

We therefore expose a single `Settings` object that reads these values
from the environment and can build a ready-to-use DSPy LM instance.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import dspy
from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    """Project configuration loaded from environment variables.

    Attributes:
        dashscope_api_key: API key used against DashScope.
        openai_base_url: OpenAI-compatible base URL exposed by DashScope.
        openai_model: Default model name used by this project.
        model_temperature: Default generation temperature.
        model_max_tokens: Default max generation tokens.
        retriever_top_k: Number of passages returned per retrieval hop.
        data_dir: Default location for processed dataset files.
        artifact_dir: Default location for optimizer artifacts.
    """

    dashscope_api_key: str
    openai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    openai_model: str = "qwen3.6-plus"
    model_temperature: float = 0.0
    model_max_tokens: int = 768
    retriever_top_k: int = 3
    data_dir: Path = Path("data/processed")
    artifact_dir: Path = Path("artifacts")

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables.

        The function intentionally supports `.env` files for convenience.
        In CI or production, regular exported environment variables work too.
        """

        load_dotenv(override=False)

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "DASHSCOPE_API_KEY is not set. Export it before running the project."
            )

        return cls(
            dashscope_api_key=api_key,
            openai_base_url=os.getenv(
                "OPENAI_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            openai_model=os.getenv("OPENAI_MODEL", "qwen3.6-plus"),
            model_temperature=float(os.getenv("MODEL_TEMPERATURE", "0.0")),
            model_max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "768")),
            retriever_top_k=int(os.getenv("RETRIEVER_TOP_K", "3")),
            data_dir=Path(os.getenv("DATA_DIR", "data/processed")),
            artifact_dir=Path(os.getenv("ARTIFACT_DIR", "artifacts")),
        )

    def build_lm(self) -> dspy.LM:
        """Construct the DSPy LM configured for DashScope.

        DSPy supports OpenAI-compatible providers via the `openai/` model prefix.
        The DashScope `enable_thinking` toggle is passed through `extra_body`
        because it is a provider-specific parameter.
        """

        model_name = f"openai/{self.openai_model}"
        return dspy.LM(
            model=model_name,
            api_key=self.dashscope_api_key,
            api_base=self.openai_base_url,
            temperature=self.model_temperature,
            max_tokens=self.model_max_tokens,
            cache=True,
            extra_body={"enable_thinking": False},
        )

    def ensure_dirs(self) -> None:
        """Create default artifact and data directories if missing."""

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
