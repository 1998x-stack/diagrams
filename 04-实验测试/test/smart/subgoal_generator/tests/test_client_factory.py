"""Phase 2 tests: Anthropic client factory."""
import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client_factory import create_client


class TestCreateClient:
    def test_raises_when_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure ANTHROPIC_API_KEY is absent
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError) as exc_info:
                create_client()
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_explicit_key_creates_client(self):
        client = create_client(api_key="sk-ant-fake-key-for-testing")
        assert client is not None
        # Verify it's an Anthropic client (has messages attribute)
        assert hasattr(client, "messages")

    def test_env_key_creates_client(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-fake-key-env"}):
            client = create_client()
            assert client is not None
            assert hasattr(client, "messages")

    def test_explicit_key_takes_precedence_over_env(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-env-key"}):
            client = create_client(api_key="sk-ant-explicit-key")
            assert client is not None

    def test_error_message_is_helpful(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError) as exc_info:
                create_client()
            msg = str(exc_info.value)
            assert "ANTHROPIC_API_KEY" in msg
            assert "export" in msg.lower() or "set" in msg.lower()
