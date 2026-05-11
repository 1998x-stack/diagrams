"""Phase 2 tests: Anthropic client factory."""
import os, sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client_factory import create_client


class TestCreateClient:
    def test_raises_env_error_when_no_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
            create_client()

    def test_accepts_explicit_key(self):
        import anthropic
        client = create_client(api_key="sk-ant-test-key")
        assert isinstance(client, anthropic.Anthropic)

    def test_reads_env_var(self, monkeypatch):
        import anthropic
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
        client = create_client()
        assert isinstance(client, anthropic.Anthropic)

    def test_explicit_key_overrides_env(self, monkeypatch):
        import anthropic
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
        client = create_client(api_key="sk-ant-explicit-key")
        assert isinstance(client, anthropic.Anthropic)

    def test_returns_anthropic_instance(self):
        import anthropic
        client = create_client(api_key="sk-ant-any-key")
        assert isinstance(client, anthropic.Anthropic)
