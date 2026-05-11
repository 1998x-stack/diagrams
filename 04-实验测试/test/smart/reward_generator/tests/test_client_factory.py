"""Phase 2 tests: Anthropic client factory."""
import os
import pytest
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client_factory import create_client


class TestCreateClient:
    def test_raises_env_error_when_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
                create_client()

    def test_raises_env_error_explicit_message(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError) as exc_info:
                create_client()
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_accepts_explicit_api_key(self):
        import anthropic
        client = create_client(api_key="sk-test-key")
        assert isinstance(client, anthropic.Anthropic)

    def test_reads_env_var(self):
        import anthropic
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
            client = create_client()
            assert isinstance(client, anthropic.Anthropic)

    def test_explicit_key_takes_precedence(self):
        import anthropic
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
            client = create_client(api_key="sk-explicit-key")
            assert isinstance(client, anthropic.Anthropic)
